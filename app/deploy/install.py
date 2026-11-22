#!/usr/bin/env python3
"""Paint Lab Ubuntu installer. Isolated service, versioned releases, nginx/TLS gates and rollback.

Run ONLY by the ZIP watcher over an authenticated SSH connection; never silently
replace existing vhosts or unrelated services. Artwork and secrets live outside releases.
"""
from __future__ import annotations
import argparse,hashlib,http.client,ipaddress,json,os,pwd,re,secrets,shutil,socket,ssl,subprocess,sys,time,urllib.request
from pathlib import Path

DOMAIN='paint-lab.xyz';SERVICE='paint-lab';PORT=18766;MANAGED='# PAINT_LAB_MANAGED_V1'
BASE=Path('/var/www/paint-lab.xyz');RELEASES=BASE/'releases';CURRENT=BASE/'current'
DATA=Path('/var/lib/paint-lab');BACKUPS=DATA/'deploy-backups';VENV=Path('/opt/paint-lab/venv')
SITE=Path('/etc/nginx/sites-available/paint-lab.xyz');ENABLED=Path('/etc/nginx/sites-enabled/paint-lab.xyz')
UNIT=Path('/etc/systemd/system/paint-lab.service');ENV=Path('/etc/paint-lab.env');VAULT=Path('/etc/paint-lab-vault.key')
CERT=Path('/etc/letsencrypt/live/paint-lab.xyz/fullchain.pem');PRIVKEY=Path('/etc/letsencrypt/live/paint-lab.xyz/privkey.pem')
CERTBOT_ACCOUNTS=Path('/etc/letsencrypt/accounts/acme-v02.api.letsencrypt.org/directory')

HTTP='''# PAINT_LAB_MANAGED_V1
server {
 listen 80;
 listen [::]:80;
 server_name paint-lab.xyz;
 location ^~ /.well-known/acme-challenge/ { root /var/www/paint-lab.xyz/acme; try_files $uri =404; }
 location / { return 503 'Paint Lab TLS setup in progress'; }
}
'''
NGINX='''# PAINT_LAB_MANAGED_V1
server {
 listen 80;
 listen [::]:80;
 server_name paint-lab.xyz;
 location ^~ /.well-known/acme-challenge/ { root /var/www/paint-lab.xyz/acme; try_files $uri =404; }
 location / { return 301 https://$host$request_uri; }
}
server {
 listen 443 ssl;
 listen [::]:443 ssl;
 server_name paint-lab.xyz;
 ssl_certificate /etc/letsencrypt/live/paint-lab.xyz/fullchain.pem;
 ssl_certificate_key /etc/letsencrypt/live/paint-lab.xyz/privkey.pem;
 ssl_protocols TLSv1.2 TLSv1.3;
 ssl_session_cache shared:PaintLabSSL:10m;
 root /var/www/paint-lab.xyz/current/frontend;
 index index.html;
 access_log /var/log/nginx/paint-lab.xyz.access.log;
 error_log /var/log/nginx/paint-lab.xyz.error.log;
 add_header X-Content-Type-Options nosniff always;
 add_header Referrer-Policy strict-origin-when-cross-origin always;
 client_max_body_size 22m;
 location /api/ {
  proxy_pass http://127.0.0.1:18766;
  proxy_http_version 1.1;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_read_timeout 40s;
 }
 location = /ws {
  proxy_pass http://127.0.0.1:18766/ws;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_read_timeout 90s;
 }
 # Public artwork pages and profile galleries are Flask routes, not static SPA assets.
 # Keep the original URI intact (no trailing slash on proxy_pass), including
 # /p/<token>/image.png, so shared links open art rather than index.html.
 location ^~ /p/ {
  proxy_pass http://127.0.0.1:18766;
  proxy_http_version 1.1;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_read_timeout 40s;
 }
 location ^~ /u/ {
  proxy_pass http://127.0.0.1:18766;
  proxy_http_version 1.1;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_read_timeout 40s;
 }
 location /assets/ { try_files $uri =404; }
 location = /version.json { add_header Cache-Control "no-store" always; try_files $uri =404; }
 location / { try_files $uri $uri/ /index.html; }
 location ~ /\\. { deny all; }
}
'''
UNIT_TEXT='''# PAINT_LAB_MANAGED_V1
[Unit]
Description=Paint Lab Flask, WebSocket and SQLite service
Wants=network-online.target
After=network-online.target
[Service]
Type=simple
User=paint-lab
Group=paint-lab
WorkingDirectory=/var/www/paint-lab.xyz/current
EnvironmentFile=/etc/paint-lab.env
ExecStart=/opt/paint-lab/venv/bin/gunicorn --workers 1 --threads 8 --timeout 55 --bind 127.0.0.1:18766 backend.app:app
Restart=on-failure
RestartSec=3
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/var/lib/paint-lab
[Install]
WantedBy=multi-user.target
'''

class DeployError(Exception):pass

def run(*args,timeout=120,check=True,**kw):
    return subprocess.run([str(a) for a in args],check=check,timeout=timeout,**kw)

def atomic(path:Path, content:str, mode:int=0o644):
    temporary=path.with_name('.'+path.name+'.paint-lab-new')
    temporary.write_text(content);temporary.chmod(mode);os.replace(temporary,path)

def switch(release:Path|None):
    temp=CURRENT.with_name('.current-paint-lab-next')
    temp.unlink(missing_ok=True)
    if release is None:
        CURRENT.unlink(missing_ok=True)
    else:
        temp.symlink_to(release,target_is_directory=True)
        os.replace(temp,CURRENT)

def hashes_ok(stage,version):
    info=json.loads((stage/'manifest.json').read_text())
    if info.get('project')!='paint-lab' or info.get('version')!=version:raise DeployError('Invalid manifest')
    for name,digest in info.get('sha256',{}).items():
        if not name.startswith('app/') or '..' in Path(name).parts:raise DeployError('Unsafe release path')
        candidate=stage/name
        if not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest()!=digest:
            raise DeployError('SHA256 mismatch '+name)

def active_nginx_conf():
    output=run('nginx','-T',capture_output=True,text=True,timeout=25).stdout
    chunks=re.split(r'(?m)^# configuration file (.+?):\s*$',output)
    found=[]
    for i in range(1,len(chunks),2):
        lines='\n'.join(line.split('#',1)[0] for line in chunks[i+1].splitlines())
        for entry in re.findall(r'(?m)^\s*server_name\s+([^;]+);',lines):
            if DOMAIN in entry.split():found.append(Path(chunks[i]).resolve());break
    return list(dict.fromkeys(found))

def check_no_collisions():
    run('nginx','-t',timeout=20,capture_output=True)
    found=active_nginx_conf()
    if len(found)>1:raise DeployError('Multiple nginx vhosts advertise '+DOMAIN+'; manual review required')
    target=SITE.resolve()
    if found and found[0]!=target:raise DeployError('Domain already served by another nginx configuration: '+str(found[0]))
    if SITE.is_symlink():raise DeployError('Site configuration is a symlink; manual review required')
    if SITE.exists() and MANAGED not in SITE.read_text():raise DeployError('Existing unrecognized Paint Lab nginx site; refusing overwrite')
    if ENABLED.exists() and not ENABLED.is_symlink():raise DeployError('Enabled site is not a symlink')
    if ENABLED.is_symlink() and ENABLED.resolve()!=SITE.resolve():raise DeployError('Enabled nginx site points elsewhere; refusing overwrite')
    if UNIT.exists() and MANAGED not in UNIT.read_text():raise DeployError('Existing unrecognized paint-lab service; refusing overwrite')
    if CURRENT.exists() and not CURRENT.is_symlink():raise DeployError('Expected current release symlink; found another path')
    with socket.socket() as sock:
        sock.settimeout(1)
        listening=sock.connect_ex(('127.0.0.1',PORT))==0
    if listening:
        try:
            req=urllib.request.Request(f'http://127.0.0.1:{PORT}/api/health')
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=2) as response:
                health=json.load(response)
            good=health.get('storage')=='sqlite' and health.get('ok') is True and CURRENT.is_symlink()
        except Exception:good=False
        if not good:raise DeployError(f'Port {PORT} is occupied by another application')

def check_dns():
    # The reference deployment host is 46.62.232.64, overridable for migrations.
    expected=os.environ.get('PAINT_LAB_EXPECTED_IP','46.62.232.64').strip()
    addresses={a[4][0] for a in socket.getaddrinfo(DOMAIN,80,type=socket.SOCK_STREAM)}
    if expected and expected not in addresses:
        raise DeployError(f'DNS for {DOMAIN} resolves to {sorted(addresses)}, not expected server {expected}. No changes made.')
    print('DNS_OK',', '.join(sorted(addresses)))

def ensure_packages():
    # Install missing components only; never upgrade unrelated services/packages.
    needed=[]
    commands={'nginx':'nginx','python3':'python3','systemctl':None,'runuser':'util-linux','certbot':'certbot'}
    for command,package in commands.items():
        if not shutil.which(command):
            if not package:raise DeployError('Required system program missing: '+command)
            needed.append(package)
    check=run('python3','-m','venv','--help',capture_output=True,check=False)
    if check.returncode:needed.append('python3-venv')
    if needed:
        if not shutil.which('apt-get'):raise DeployError('Missing required packages: '+', '.join(needed))
        if os.getenv('PAINT_LAB_INSTALL_PACKAGES','1')!='1':raise DeployError('Missing packages; set PAINT_LAB_INSTALL_PACKAGES=1 to install: '+', '.join(needed))
        run('apt-get','update',timeout=200)
        run('apt-get','install','-y','--no-install-recommends',*sorted(set(needed)),timeout=240)

def ensure_user_and_data():
    try:account=pwd.getpwnam('paint-lab')
    except KeyError:
        run('useradd','--system','--home-dir',str(DATA),'--shell','/usr/sbin/nologin','paint-lab');account=pwd.getpwnam('paint-lab')
    for folder in (BASE,RELEASES,DATA,BACKUPS):folder.mkdir(parents=True,exist_ok=True)
    DATA.chmod(0o750);BACKUPS.chmod(0o700)
    os.chown(DATA,account.pw_uid,account.pw_gid)
    return account

def ensure_env(account):
    if not ENV.exists():
        content=('PAINT_LAB_DATA_DIR=/var/lib/paint-lab\nPAINT_LAB_DB=/var/lib/paint-lab/paint-lab.sqlite3\n'
                 'PAINT_LAB_HTTPS=1\nPAINT_LAB_SESSION_KEY='+secrets.token_hex(48)+'\n'
                 'PAINT_LAB_VAULT_KEY_FILE=/etc/paint-lab-vault.key\n')
        fd=os.open(str(ENV),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o640)
        with os.fdopen(fd,'w') as out:out.write(content)
    else:
        content=ENV.read_text()
        if 'PAINT_LAB_SESSION_KEY=' not in content:raise DeployError('Existing environment file lacks the session key; manual review required')
    run('chown','root:paint-lab',str(ENV));ENV.chmod(0o640)
    if not VAULT.exists():
        from cryptography.fernet import Fernet
        fd=os.open(str(VAULT),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o640)
        with os.fdopen(fd,'wb') as out:out.write(Fernet.generate_key()+b'\n')
    run('chown','root:paint-lab',str(VAULT));VAULT.chmod(0o640)

def user_environment():
    # Tests and health need only data paths; systemd owns sensitive env loading.
    return {**os.environ,'PAINT_LAB_DATA_DIR':str(DATA),'PAINT_LAB_DB':str(DATA/'paint-lab.sqlite3'),
            'PAINT_LAB_SESSION_KEY':'server-test-session-only','PAINT_LAB_VAULT_KEY_FILE':str(VAULT)}

def wait_health(version):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));last='no response'
    for _ in range(40):
        try:
            with opener.open('http://127.0.0.1:18766/api/health',timeout=2) as response:result=json.load(response)
            if result.get('ok') and result.get('version')==version and result.get('storage')=='sqlite' and result.get('websocket'):
                return
            last=repr(result)[:200]
        except Exception as e:last=str(e)[:200]
        time.sleep(1)
    raise DeployError('Local service health check failed: '+last)

def reload_nginx():
    run('nginx','-t',timeout=20)
    run('systemctl','reload','nginx',timeout=20)

# Public nginx route readiness is eventually consistent after `systemctl reload nginx`:
# the command can return after signalling a graceful reload while a previous
# worker still accepts a few new connections with the SPA fallback config.
# Probe the Flask upstream separately to distinguish an upstream 404 from an
# nginx location-routing bug, then retry the HTTPS front door before rolling back.
PUBLIC_ROUTE_PROBES=(
    '/p/paintlabunknownpublication9999',
    '/p/paintlabunknownpublication9999/image.png',
    '/u/PaintLabUnknownPublicUser9999',
)

def probe_backend_public_route(route):
    """Return upstream response status, using a direct socket without proxies."""
    connection=http.client.HTTPConnection('127.0.0.1',PORT,timeout=4)
    try:
        connection.request('GET',route,headers={'Host':DOMAIN,'Cache-Control':'no-store'})
        response=connection.getresponse()
        response.read(256)
        return response.status
    finally:
        connection.close()

def probe_https_public_route(route):
    """Return local nginx response status and type via verified production TLS.

    Send the actual hostname as SNI and Host while connecting directly to
    localhost. That excludes external DNS and third-party proxy caching.
    """
    with socket.create_connection(('127.0.0.1',443),timeout=5) as raw:
        with ssl.create_default_context().wrap_socket(raw,server_hostname=DOMAIN) as connection:
            connection.settimeout(5)
            connection.sendall(('GET '+route+' HTTP/1.1\r\nHost: '+DOMAIN+
                '\r\nConnection: close\r\nCache-Control: no-store\r\nAccept: text/html\r\n\r\n').encode('ascii'))
            response=b''
            while b'\r\n\r\n' not in response and len(response)<8192:
                chunk=connection.recv(1024)
                if not chunk:break
                response+=chunk
    head,_,_=response.partition(b'\r\n\r\n')
    lines=head.split(b'\r\n')
    status=lines[0].decode('ascii','replace') if lines else ''
    match=re.match(r'^HTTP/1\.[01] (\d{3})(?: |$)',status)
    if not match:raise DeployError('Invalid nginx HTTP response for '+route+': '+repr(status[:100]))
    content_type=next((line.split(b':',1)[1].decode('latin1').strip() for line in lines[1:]
        if line.lower().startswith(b'content-type:')),'unknown')
    return int(match.group(1)),content_type

def check_public_routes(max_attempts=45,pause_seconds=.5):
    """Wait for public Flask routes to be active after graceful nginx reload.

    Known-absent publication/gallery URLs must return 404, not the editor SPA's
    HTTP 200. Probe Flask itself first; only nginx can cause a 200/404 mismatch.
    A bounded retry tolerates workers retiring asynchronously without hiding a
    persistently wrong nginx vhost, a bad certificate or a broken Flask route.
    """
    for route in PUBLIC_ROUTE_PROBES:
        upstream=probe_backend_public_route(route)
        if upstream!=404:
            raise DeployError('Flask public-route contract failed: '+route+
                ' returned '+str(upstream)+' directly from 127.0.0.1:'+str(PORT))
    last_error='no response'
    for attempt in range(1,max_attempts+1):
        failures=[]
        for route in PUBLIC_ROUTE_PROBES:
            try:
                status,content_type=probe_https_public_route(route)
                if status!=404:
                    failures.append(route+' HTTP '+str(status)+' ('+content_type+')')
            except (OSError,ssl.SSLError,DeployError) as exc:
                failures.append(route+' '+str(exc))
        if not failures:
            print('PUBLIC ROUTES OK /p/, /p/<token>/image.png, /u/ after '+str(attempt)+' nginx probe(s)',flush=True)
            return
        last_error='; '.join(failures)
        if attempt==1:
            print('PUBLIC ROUTES: waiting for nginx reload to take effect; '+last_error,flush=True)
        if attempt<max_attempts:time.sleep(pause_seconds)
    raise DeployError('Public share URL not routed to Flask after '+str(max_attempts)+
        ' HTTPS checks (Flask upstream returned 404): '+last_error+
        '. Verify the live 443 vhost, enabled site symlink and nginx reload on the server.')

def certificate_ready():return CERT.is_file() and PRIVKEY.is_file()

def certbot_identity():
    """Reuse the server's existing Let's Encrypt production account, if available.

    Never borrow certificates issued for other domains. The account is reused to
    request a new, domain-specific certificate for paint-lab.xyz. Noninteractive
    issuance without a registered account requires an explicitly provided email.
    """
    accounts=[]
    if CERTBOT_ACCOUNTS.is_dir():
        for directory in CERTBOT_ACCOUNTS.iterdir():
            if (directory/'regr.json').is_file() and re.fullmatch(r'[A-Za-z0-9_-]+',directory.name):
                accounts.append(directory)
    explicit=os.getenv('PAINT_LAB_CERTBOT_ACCOUNT','').strip()
    if explicit:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',explicit):
            raise DeployError('Invalid PAINT_LAB_CERTBOT_ACCOUNT identifier')
        if explicit not in [directory.name for directory in accounts]:
            raise DeployError('Requested Certbot account not found on server: '+explicit)
        return ['--account',explicit], 'Reusing selected existing Let\'s Encrypt account '+explicit
    if accounts:
        # An existing Certbot installation normally already has an ACME account.
        # Prefer the most recently used registration; never expose its private key.
        account=max(accounts,key=lambda path:(path.stat().st_mtime,path.name))
        return ['--account',account.name], 'Reusing existing Let\'s Encrypt account '+account.name
    email=os.getenv('PAINT_LAB_CERTBOT_EMAIL','').strip()
    if email:
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
            raise DeployError('Invalid PAINT_LAB_CERTBOT_EMAIL')
        return ['--email',email], 'Registering a new Let\'s Encrypt account'
    raise DeployError('No existing production Certbot account found. Supply PAINT_LAB_CERTBOT_EMAIL for the first registration; no nginx or service changes made.')

def install(stage:Path,version:str):
    if os.geteuid()!=0:raise DeployError('Deployment must run as root')
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise DeployError('Invalid version')
    hashes_ok(stage,version);check_dns();ensure_packages();check_no_collisions()
    # Resolve the certificate account before touching nginx, systemd or data.
    certbot_options,certbot_message=(certbot_identity() if not certificate_ready() else ([], 'Domain certificate already installed'))
    print('CERTBOT '+certbot_message,flush=True)
    account=ensure_user_and_data();dest=RELEASES/('v'+version)
    if dest.exists():
        for name,digest in json.loads((stage/'manifest.json').read_text())['sha256'].items():
            p=dest/Path(name).relative_to('app')
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
                raise DeployError('Existing release version collision: '+name)
    else:
        temp=RELEASES/('.stage-'+version+'-'+secrets.token_hex(4))
        shutil.copytree(stage/'app',temp)
        os.replace(temp,dest)
    for path in dest.rglob('*'):
        if path.is_file():path.chmod(0o644)
    VENV.parent.mkdir(parents=True,exist_ok=True)
    if not (VENV/'bin/python').is_file():run('python3','-m','venv',str(VENV),timeout=75)
    run(str(VENV/'bin/python'),'-m','pip','install','--disable-pip-version-check','-r',str(dest/'requirements.txt'),timeout=260)
    ensure_env(account)
    run('runuser','-u','paint-lab','--',str(VENV/'bin/python'),'-m','unittest','discover','-s','tests','-v',cwd=dest,env=user_environment(),timeout=105)
    previous=CURRENT.resolve() if CURRENT.is_symlink() else None
    stamp=time.strftime('%Y%m%d-%H%M%S')+'-'+version
    backup=BACKUPS/stamp;backup.mkdir(mode=0o700)
    prior_site=SITE.read_text() if SITE.exists() else None
    prior_unit=UNIT.read_text() if UNIT.exists() else None
    prior_enabled=ENABLED.is_symlink()
    (backup/'metadata.json').write_text(json.dumps({'previous':str(previous) if previous else None,
      'site_existed':prior_site is not None,'unit_existed':prior_unit is not None,
      'enabled_existed':prior_enabled,'version':version},indent=2))
    if prior_site is not None:(backup/'site.conf').write_text(prior_site)
    if prior_unit is not None:(backup/'service.unit').write_text(prior_unit)
    changed=False
    try:
        (BASE/'acme'/'.well-known'/'acme-challenge').mkdir(parents=True,exist_ok=True)
        if not certificate_ready():
            atomic(SITE,HTTP)
            if not ENABLED.is_symlink():ENABLED.symlink_to(SITE)
            changed=True;reload_nginx()
            run('certbot','certonly','--webroot','--non-interactive','--agree-tos',
                *certbot_options,'-w',str(BASE/'acme'),'-d',DOMAIN,timeout=240)
            if not certificate_ready():raise DeployError('Certbot did not create certificate')
        atomic(UNIT,UNIT_TEXT)
        atomic(SITE,NGINX)
        if not ENABLED.is_symlink():ENABLED.symlink_to(SITE)
        changed=True;run('systemctl','daemon-reload');run('nginx','-t')
        switch(dest)
        run('systemctl','enable','paint-lab',timeout=25)
        run('systemctl','restart','paint-lab',timeout=35)
        wait_health(version)
        reload_nginx()
        check_public_routes()
        print('DEPLOYED v'+version)
        print('SERVER UNIT '+str(UNIT))
        print('PUBLIC URL https://'+DOMAIN+'/')
    except Exception:
        if changed:
            try:
                switch(previous)
                if prior_unit is None:UNIT.unlink(missing_ok=True)
                else:atomic(UNIT,prior_unit)
                if prior_site is None:SITE.unlink(missing_ok=True)
                else:atomic(SITE,prior_site)
                if not prior_enabled:ENABLED.unlink(missing_ok=True)
                run('systemctl','daemon-reload')
                if previous:run('systemctl','restart','paint-lab',timeout=35)
                else:run('systemctl','disable','--now','paint-lab',timeout=25,check=False)
                reload_nginx()
                print('ROLLED BACK failed release; SQLite and vault were preserved')
            except Exception as rollback_error:
                print('ROLLBACK NEEDS ADMIN REVIEW: '+str(rollback_error),file=sys.stderr)
        raise

def rollback():
    if os.geteuid()!=0:raise DeployError('Root required')
    choices=sorted(BACKUPS.iterdir(),reverse=True) if BACKUPS.exists() else []
    for path in choices:
        marker=path/'metadata.json'
        if marker.is_file():
            entry=json.loads(marker.read_text());prev=Path(entry['previous']) if entry.get('previous') else None
            if prev is None or not prev.is_dir():continue
            if not CURRENT.is_symlink() or CURRENT.resolve()==prev:continue
            if MANAGED not in UNIT.read_text() or MANAGED not in SITE.read_text():
                raise DeployError('Unmanaged live configuration; refusing rollback')
            current=CURRENT.resolve();switch(prev)
            try:
                run('systemctl','restart','paint-lab',timeout=40)
                version=json.loads((prev/'version.json').read_text())['version'];wait_health(version)
            except Exception:
                switch(current);run('systemctl','restart','paint-lab',timeout=40);raise
            print('ROLLED BACK to '+str(prev)+' (SQLite data unchanged)');return
    raise DeployError('No previous release available for rollback')

if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('--stage');args.add_argument('--version');args.add_argument('--rollback',action='store_true');opt=args.parse_args()
    try:
        if opt.rollback:rollback()
        else:
            if not opt.stage or not opt.version:raise DeployError('--stage and --version required')
            install(Path(opt.stage).resolve(),opt.version)
    except Exception as e:print('DEPLOY ERROR: '+str(e),file=sys.stderr);sys.exit(1)
