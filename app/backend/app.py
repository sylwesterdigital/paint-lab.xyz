"""Paint Lab: browser painting frontend, private SQLite canvases, provider vault and WebSocket events."""
from __future__ import annotations
import json,os,re,secrets,sqlite3,threading,time,urllib.error,urllib.request,uuid,logging,collections
from datetime import timedelta,datetime,timezone
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask,abort,g,jsonify,request,session,send_from_directory
from flask_sock import Sock
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash,check_password_hash
from . import db,keyvault

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('PAINT_LAB_DATA_DIR',str(ROOT/'var'))).resolve()
DATABASE=Path(os.environ.get('PAINT_LAB_DB',str(DATA/'paint-lab.sqlite3'))).resolve()
VERSION=json.loads((ROOT/'version.json').read_text())['version']
app=Flask(__name__,static_folder=str(ROOT/'frontend'),static_url_path='')
app.config.update(SECRET_KEY=os.environ.get('PAINT_LAB_SESSION_KEY',secrets.token_hex(48)),
 SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',
 SESSION_COOKIE_SECURE=os.environ.get('PAINT_LAB_HTTPS','0')=='1',
 PERMANENT_SESSION_LIFETIME=timedelta(days=14),MAX_CONTENT_LENGTH=22*1024*1024,
 JSON_SORT_KEYS=False)
app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1,x_host=0)
sock=Sock(app)
db.init(DATABASE)
clients={};client_lock=threading.RLock()
login_attempts={};attempt_lock=threading.Lock()

# Dedicated application log only: never expose OS journal, credentials, headers or bodies.
LOG_DIR=DATA/'logs'
LOG_DIR.mkdir(parents=True,exist_ok=True)
LOG_FILE=LOG_DIR/'application.log'
logger=logging.getLogger('paint_lab.operations')
logger.setLevel(logging.INFO)
logger.propagate=False
if not logger.handlers:
    log_handler=RotatingFileHandler(LOG_FILE,maxBytes=2_000_000,backupCount=3,encoding='utf-8')
    log_handler.setFormatter(logging.Formatter('%(asctime)sZ [%(levelname)-7s] %(message)s',datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(log_handler)
BOOT_TIME=time.monotonic()
operations={'requests':0,'errors':0,'slow':0}
ops_lock=threading.Lock()
logger.info('Paint Lab v%s service initialized, SQLite storage configured',VERSION)

@app.before_request
def timing_start():
    g.start_time=time.monotonic()

@app.after_request
def timing_end(response):
    elapsed=1000*(time.monotonic()-getattr(g,'start_time',time.monotonic()))
    # Drop query strings, username, cookies, request payloads and auth headers from logs.
    # No request body or provider credentials are ever emitted.
    route=request.url_rule.rule if request.url_rule else '[unmatched]'
    level=logging.WARNING if response.status_code>=500 or elapsed>=1000 else logging.INFO
    if request.path!='/api/admin/logs':
        logger.log(level,'%s %s -> %s %.0fms',request.method,route,response.status_code,elapsed)
    with ops_lock:
        operations['requests']+=1
        operations['errors']+=int(response.status_code>=500)
        operations['slow']+=int(elapsed>=1000)
    return response

@app.errorhandler(Exception)
def unexpected_error(error):
    from werkzeug.exceptions import HTTPException
    if isinstance(error,HTTPException):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description),error.code
        return error
    # Exception class only: never log stack variables, submitted keys or password content.
    logger.error('Unhandled server failure: %s on %s',type(error).__name__,request.url_rule.rule if request.url_rule else '[unmatched]')
    if request.path.startswith('/api/'):
        return jsonify(error='Internal application error'),500
    return 'Internal application error',500



@app.before_request
def verify_origin():
    if request.method in ('POST','PUT','PATCH','DELETE'):
        origin=request.headers.get('Origin','')
        if origin and (urlsplit(origin).netloc!=request.host or urlsplit(origin).scheme!=request.scheme):
            return jsonify(error='Cross-origin request blocked'),403

@app.teardown_appcontext
def cleanup(_):
    con=g.pop('sqlite',None)
    if con is not None:con.close()

def con():
    if 'sqlite' not in g:g.sqlite=db.connect(DATABASE)
    return g.sqlite

def csrf():
    if not session.get('_csrf'):session['_csrf']=secrets.token_urlsafe(32)
    return session['_csrf']

def require_csrf():
    if not secrets.compare_digest(str(request.headers.get('X-CSRF-Token','')),csrf()):abort(403,'Invalid CSRF token')

def auth(f):
    @wraps(f)
    def guarded(*args,**kwargs):
        if not isinstance(session.get('user_id'),int):return jsonify(error='Please sign in'),401
        return f(*args,**kwargs)
    return guarded

def user():return session['user_id']

def payload():
    if not request.is_json:abort(415,'JSON body required')
    data=request.get_json(silent=True)
    if not isinstance(data,dict):abort(400,'JSON object required')
    return data

def serialize_project(row,include_document=False):
    item={k:row[k] for k in ('id','title','thumbnail','created_at','updated_at')}
    if include_document:item['document']=json.loads(row['document'])
    return item

def validate_document(obj):
    if not isinstance(obj,dict) or obj.get('format')!='paint-lab-webgl' or obj.get('version') not in (2,3):
        raise ValueError('Invalid Paint Lab project format')
    actions=obj.get('actions')
    if not isinstance(actions,list) or len(actions)>20000:raise ValueError('Invalid project actions')
    if not isinstance(obj.get('baseW'),(int,float)) or not 32<=obj['baseW']<=8192:raise ValueError('Invalid canvas width')
    if not isinstance(obj.get('baseH'),(int,float)) or not 32<=obj['baseH']<=8192:raise ValueError('Invalid canvas height')
    raw=json.dumps(obj,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    if len(raw.encode('utf-8'))>16*1024*1024:raise ValueError('Project exceeds 16 MB')
    return raw

def title(v):
    if not isinstance(v,str) or not v.strip():raise ValueError('Give this painting a name')
    return v.strip()[:100]

def broadcast(uid,kind,pid):
    with client_lock:
        sockets=list(clients.get(uid,()))
    for ws in sockets:
        try:ws.send(json.dumps({'event':kind,'project_id':pid,'version':VERSION}))
        except Exception:
            with client_lock:clients.get(uid,set()).discard(ws)

@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(413)
@app.errorhandler(415)
def bad_http(e):
    if request.path.startswith('/api/'):
        return jsonify(error=getattr(e,'description',str(e))),e.code
    return e

@app.get('/')
def home():return send_from_directory(str(ROOT/'frontend'),'index.html')

@app.get('/api/health')
def health():
    try:
        ok=con().execute('SELECT 1').fetchone()[0]==1
    except sqlite3.Error:ok=False
    return jsonify(ok=ok,version=VERSION,storage='sqlite',websocket=True),200 if ok else 503

@app.get('/api/auth/me')
def me():
    token=csrf();uid=session.get('user_id')
    row=con().execute('SELECT id,username,role FROM users WHERE id=?',(uid,)).fetchone() if uid else None
    return jsonify(authenticated=bool(row),user=dict(row) if row else None,csrf=token)

def admin_only(f):
    @wraps(f)
    def gated(*args,**kwargs):
        uid=session.get('user_id')
        if not isinstance(uid,int):return jsonify(error='Sign in required'),401
        row=con().execute('SELECT role FROM users WHERE id=?',(uid,)).fetchone()
        if not row or row['role']!='admin':return jsonify(error='Administrator permission required'),403
        return f(*args,**kwargs)
    return gated

@app.get('/api/admin/logs')
@admin_only
def admin_logs():
    # Read only the application-owned rotating log, not systemd, gunicorn journal or nginx logs.
    try:limit=min(250,max(1,int(request.args.get('limit','150'))))
    except ValueError:return jsonify(error='Invalid log limit'),400
    try:
        # A bounded tail means no unbounded file reads even on a busy deployment.
        with LOG_FILE.open('rb') as stream:
            stream.seek(0,2);size=stream.tell();stream.seek(max(0,size-160_000))
            last=stream.read().decode('utf-8','replace')
        lines=last.splitlines()[-limit:]
    except OSError:
        lines=['[WARN] Application log file unavailable']
    with ops_lock:stats=dict(operations)
    response=jsonify(version=VERSION,uptime_seconds=int(time.monotonic()-BOOT_TIME),
        requests_total=stats['requests'],errors_total=stats['errors'],slow_total=stats['slow'],
        lines=lines,source='application',server_time=datetime.now(timezone.utc).isoformat())
    response.headers['Cache-Control']='no-store'
    return response

@app.post('/api/auth/register')
def register():
    require_csrf();data=payload()
    username=str(data.get('username','')).strip()
    password=data.get('password','')
    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,40}',username):return jsonify(error='Username: 3–40 letters, numbers, . _ or -'),400
    if not isinstance(password,str) or not 12<=len(password)<=256:return jsonify(error='Password must be 12–256 characters'),400
    try:
        with con():
            cur=con().execute('INSERT INTO users(username,password_hash) VALUES(?,?)',(username,generate_password_hash(password)))
            uid=cur.lastrowid
    except sqlite3.IntegrityError:return jsonify(error='Username already exists'),409
    session.clear();session.permanent=True;session['user_id']=uid;csrf()
    return jsonify(ok=True,user={'id':uid,'username':username,'role':'user'},csrf=csrf()),201

@app.post('/api/auth/login')
def login():
    require_csrf();data=payload();username=str(data.get('username','')).strip();password=data.get('password','')
    if not isinstance(password,str):return jsonify(error='Invalid credentials'),401
    key=(request.remote_addr or '?',username.casefold());now=time.monotonic()
    with attempt_lock:
        attempts=[t for t in login_attempts.get(key,[]) if now-t<300]
        if len(attempts)>=12:return jsonify(error='Too many attempts. Try later.'),429
        login_attempts[key]=attempts
    row=con().execute('SELECT id,username,password_hash,role FROM users WHERE username=?',(username,)).fetchone()
    if not row or not check_password_hash(row['password_hash'],password):
        with attempt_lock:login_attempts.setdefault(key,[]).append(now)
        return jsonify(error='Invalid credentials'),401
    with attempt_lock:login_attempts.pop(key,None)
    session.clear();session.permanent=True;session['user_id']=row['id'];csrf()
    return jsonify(ok=True,user={'id':row['id'],'username':row['username'],'role':row['role']},csrf=csrf())

@app.post('/api/auth/logout')
def logout():
    require_csrf();session.clear();return jsonify(ok=True,csrf=csrf())

@app.get('/api/projects')
@auth
def list_projects():
    rows=con().execute('SELECT id,title,thumbnail,created_at,updated_at FROM projects WHERE owner_id=? ORDER BY updated_at DESC LIMIT 100',(user(),)).fetchall()
    return jsonify(projects=[serialize_project(r) for r in rows])

@app.post('/api/projects')
@auth
def create_project():
    require_csrf();data=payload()
    try:raw=validate_document(data.get('document'));name=title(data.get('title'))
    except (ValueError,TypeError,OverflowError) as e:return jsonify(error=str(e)),400
    if con().execute('SELECT count(*) FROM projects WHERE owner_id=?',(user(),)).fetchone()[0]>=100:
        return jsonify(error='Maximum 100 cloud canvases per account'),409
    thumb=data.get('thumbnail')
    if not isinstance(thumb,str) or len(thumb)>150000 or not thumb.startswith('data:image/jpeg;base64,'):thumb=None
    key=str(uuid.uuid4())
    with con():con().execute('INSERT INTO projects(id,owner_id,title,document,thumbnail) VALUES(?,?,?,?,?)',(key,user(),name,raw,thumb))
    broadcast(user(),'project_saved',key)
    return jsonify(ok=True,id=key),201

@app.get('/api/projects/<uuid:project_id>')
@auth
def get_project(project_id):
    row=con().execute('SELECT * FROM projects WHERE id=? AND owner_id=?',(str(project_id),user())).fetchone()
    if not row:return jsonify(error='Project not found'),404
    return jsonify(project=serialize_project(row,True))

@app.put('/api/projects/<uuid:project_id>')
@auth
def update_project(project_id):
    require_csrf();data=payload()
    try:raw=validate_document(data.get('document'));name=title(data.get('title'))
    except (ValueError,TypeError,OverflowError) as e:return jsonify(error=str(e)),400
    thumb=data.get('thumbnail')
    if not isinstance(thumb,str) or len(thumb)>150000 or not thumb.startswith('data:image/jpeg;base64,'):thumb=None
    with con():result=con().execute("UPDATE projects SET title=?,document=?,thumbnail=?,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND owner_id=?",(name,raw,thumb,str(project_id),user()))
    if not result.rowcount:return jsonify(error='Project not found'),404
    broadcast(user(),'project_saved',str(project_id))
    return jsonify(ok=True,id=str(project_id))

@app.delete('/api/projects/<uuid:project_id>')
@auth
def delete_project(project_id):
    require_csrf()
    with con():result=con().execute('DELETE FROM projects WHERE id=? AND owner_id=?',(str(project_id),user()))
    if not result.rowcount:return jsonify(error='Project not found'),404
    broadcast(user(),'project_deleted',str(project_id))
    return jsonify(ok=True)

@app.get('/api/providers')
@auth
def providers():return jsonify(providers=keyvault.status(con(),user()))

@app.put('/api/providers/<provider>')
@auth
def put_provider(provider):
    require_csrf();data=payload();key=data.get('key','')
    try:
        with con():keyvault.save(con(),user(),provider,key,DATA)
    except (ValueError,UnicodeEncodeError) as e:return jsonify(error=str(e)),400
    return jsonify(ok=True,provider=provider)

@app.delete('/api/providers/<provider>')
@auth
def delete_provider(provider):
    require_csrf()
    if provider not in keyvault.PROVIDERS:return jsonify(error='Unknown provider'),404
    with con():con().execute('DELETE FROM provider_keys WHERE owner_id=? AND provider=?',(user(),provider))
    return jsonify(ok=True)

@app.post('/api/providers/<provider>/test')
@auth
def test_provider(provider):
    require_csrf()
    if provider not in keyvault.PROVIDERS:return jsonify(error='Unknown provider'),404
    key=keyvault.get(con(),user(),provider,DATA)
    if not key:return jsonify(error='No API key saved'),404
    probes={
      'openai':('https://api.openai.com/v1/models',{'Authorization':'Bearer '+key}),
      'anthropic':('https://api.anthropic.com/v1/models',{'x-api-key':key,'anthropic-version':'2023-06-01'}),
      'google':('https://generativelanguage.googleapis.com/v1beta/models',{'x-goog-api-key':key}),
      'xai':('https://api.x.ai/v1/models',{'Authorization':'Bearer '+key}),
      'replicate':('https://api.replicate.com/v1/models',{'Authorization':'Bearer '+key}),
    }
    if provider not in probes:return jsonify(ok=False,status='not_available',message='This provider has no read-only verification endpoint configured')
    url,headers=probes[provider];headers['User-Agent']='PaintLab/0.1'
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=8) as response:
            return jsonify(ok=True,status='verified',http_status=response.status)
    except urllib.error.HTTPError as e:
        return jsonify(ok=False,status='rejected' if e.code in (401,403) else 'unknown',http_status=e.code,
                       message='Provider rejected credentials' if e.code in (401,403) else 'Provider returned an error')
    except (urllib.error.URLError,TimeoutError) as e:
        return jsonify(ok=False,status='unavailable',message='Provider could not be reached')

@app.get('/api/ai/capabilities')
def ai_capabilities():
    return jsonify(layer_edit=False,message='API-key vault is ready; AI layer editing is not enabled in this release')

@sock.route('/ws')
def websocket(ws):
    origin=request.headers.get('Origin','')
    if not origin or urlsplit(origin).netloc!=request.host or urlsplit(origin).scheme!=request.scheme:
        ws.close();return
    uid=session.get('user_id')
    if not isinstance(uid,int):ws.close();return
    with client_lock:clients.setdefault(uid,set()).add(ws)
    try:
        ws.send(json.dumps({'event':'connected','version':VERSION}))
        while True:
            try:raw=ws.receive(timeout=35)
            except Exception:break
            if raw is None:continue
            if len(raw)>512:ws.close();break
            try:message=json.loads(raw)
            except (ValueError,TypeError):continue
            if isinstance(message,dict) and message.get('type')=='ping':
                ws.send(json.dumps({'event':'pong'}))
    finally:
        with client_lock:clients.get(uid,set()).discard(ws)

if __name__=='__main__':
    app.run(host='127.0.0.1',port=int(os.environ.get('PAINT_LAB_PORT','18766')),debug=False)
