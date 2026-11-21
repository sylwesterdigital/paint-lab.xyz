"""v0.1.24 portable project and account-controlled publication contracts."""
import importlib.util,os,sqlite3,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
API=(ROOT/'backend/app.py').read_text()

class PortableProjectTests(unittest.TestCase):
 def test_public_png_fixture_uses_only_standard_library(self):
  # The Ubuntu release venv intentionally installs only app/requirements.txt;
  # a test-only PIL import caused the v0.1.23 release to fail after staging.
  own=Path(__file__).read_text()
  self.assertNotIn('from '+'PIL import',own)
  self.assertNotIn('import '+'PIL',own)
  self.assertIn("zlib.compress(scanline*4)",own)
 def test_canvas_dialog_ratio_and_limits(self):
  for item in ('window','1:1','3:2','2:3','16:9','3:4','4:3','2:1','custom'):
   self.assertIn(f'data-ratio="{item}"',HTML)
  for item in ('newCanvasName','newCanvasWidth','newCanvasHeight','confirmNewCanvas'):
   self.assertIn('id="'+item+'"',HTML)
  self.assertIn('MAX_CANVAS_PIXELS=16000000',HTML)
  self.assertIn('async function createNewCanvas()',HTML)
 def test_zip_assets_and_image_exports(self):
  for item in ('savePNGWith','savePNGWithout','saveZIP','exportZIP','importProjectFile'):
   self.assertIn('id="'+item+'"',HTML)
  for code in ('function createPortableZIP(entries)','function readPortableZIP(bytes)',
    "name:'project.json'",'assets/layers/','assets/brushes/','assets/previews/artwork.png',
    'async function importProjectZIP(file)','function zipCRC(bytes)'):
   self.assertIn(code,HTML)
  self.assertIn('l.ctx.drawImage(img,0,0,l.canvas.width,l.canvas.height)',HTML)
  self.assertIn('validateData(doc)',HTML)
 def test_sharing_is_explicit_and_uses_uploaded_icon(self):
  for item in ('pl-share','shareOverlay','shareNative','publishArtwork','copyShareLink','sharePublications','mobileShare'):
   self.assertIn('id="'+item+'"',HTML)
  self.assertIn('navigator.canShare',HTML)
  self.assertIn("apiCall('/publications','POST'",HTML)
  self.assertIn("cloudUser",HTML)
 def test_sqlite_publication_schema(self):
  from backend import db
  with tempfile.TemporaryDirectory() as folder:
   database=Path(folder)/'project.sqlite3';db.init(database)
   with db.connect(database) as con:
    owner=con.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',('test','hash')).lastrowid
    con.execute('INSERT INTO publications(token,owner_id,title,file_name) VALUES(?,?,?,?)',('sampletoken',owner,'Public art','sampletoken.png'))
    self.assertEqual(con.execute('SELECT count(*) FROM publications WHERE owner_id=?',(owner,)).fetchone()[0],1)
    con.execute('DELETE FROM users WHERE id=?',(owner,))
    self.assertEqual(con.execute('SELECT count(*) FROM publications').fetchone()[0],0)
 def test_server_no_document_or_key_publication(self):
  for code in ('@app.post(\'/api/publications\')',"@app.get('/p/<token>')", "@app.get('/u/<username>')",'@app.delete(\'/api/publications/<token>\')','PUBLIC_IMAGE_LIMIT=7*1024*1024','with image_path.open(\'xb\')','@auth','require_csrf()'):
   self.assertIn(code,API)
  self.assertIn('Only PNG images and public username/title are exposed',API)
  self.assertIn("default-src 'none'",API)

AVAILABLE=bool(importlib.util.find_spec('flask') and importlib.util.find_spec('flask_sock'))
@unittest.skipUnless(AVAILABLE,'Flask dependencies required to exercise endpoints')
class PublicShareEndpoints(unittest.TestCase):
 def test_owner_isolation_and_revocation(self):
  import subprocess,sys
  with tempfile.TemporaryDirectory() as folder:
   env={**os.environ,'PAINT_LAB_DATA_DIR':folder,'PAINT_LAB_DB':str(Path(folder)/'paintlab.sqlite3'),'PAINT_LAB_SESSION_KEY':'unit-test-session-secret'}
   script=r'''
import base64,struct,zlib
from backend.app import app
app.config.update(TESTING=True,SESSION_COOKIE_SECURE=False)
a=app.test_client();b=app.test_client();anon=app.test_client()
tok=a.get('/api/auth/me').json['csrf'];csrf=b.get('/api/auth/me').json['csrf']
r=a.post('/api/auth/register',json={'username':'share_owner','password':'sufficiently-long-password'},headers={'X-CSRF-Token':tok});assert r.status_code==201,r.json
tok=r.json['csrf']
r=b.post('/api/auth/register',json={'username':'share_other','password':'sufficiently-long-password'},headers={'X-CSRF-Token':csrf});assert r.status_code==201,r.json
csrf=r.json['csrf']
# Fully valid 4x4 RGBA PNG generated with only the Python standard library.
# This production-environment test must not depend on Pillow/PIL: the Paint Lab
# runtime deliberately does not install image libraries for public PNG sharing.
def chunk(kind,payload):
    return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
rgba=bytes((255,24,8,255))
scanline=b'\x00'+rgba*4
png=(b'\x89PNG\r\n\x1a\n'
     +chunk(b'IHDR',struct.pack('>IIBBBBB',4,4,8,6,0,0,0))
     +chunk(b'IDAT',zlib.compress(scanline*4))
     +chunk(b'IEND',b''))
encoded='data:image/png;base64,'+base64.b64encode(png).decode()
assert anon.post('/api/publications',json={'title':'Test','image':encoded}).status_code==401
assert a.post('/api/publications',json={'title':'Test','image':encoded}).status_code==403
res=a.post('/api/publications',json={'title':'Test','image':encoded},headers={'X-CSRF-Token':tok});assert res.status_code==201,res.json
item=res.json;token=item['token'];assert '/p/'+token in item['url']
assert b.get('/api/publications').json['publications']==[]
assert anon.get('/p/'+token).status_code==200
assert b.get('/u/share_owner').status_code==200
image=anon.get('/p/'+token+'/image.png');assert image.status_code==200 and image.data==png
assert b.delete('/api/publications/'+token,headers={'X-CSRF-Token':csrf}).status_code==404
assert a.delete('/api/publications/'+token,headers={'X-CSRF-Token':tok}).status_code==200
assert anon.get('/p/'+token).status_code==404
assert anon.get('/p/'+token+'/image.png').status_code==404
print('PUBLIC_SHARE_OK')
'''
   proc=subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=35)
   self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)
   self.assertIn('PUBLIC_SHARE_OK',proc.stdout)
