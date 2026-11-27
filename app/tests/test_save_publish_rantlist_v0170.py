"""Release v0.1.77: combined save/publish, safe public-link UI and scoped Rantlist bridge."""
import hashlib,hmac,json,os,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from backend import db,rantlist_bridge

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
BACKEND=(APP/'backend/app.py').read_text()

class SaveAndRantlist(unittest.TestCase):
 def test_ui_controls_and_no_implicit_overwrite(self):
  for item in ['id="saveAndPublish"','id="saveOpenLink"','id="saveRantlistShare"',
               'function setPublishedSaveLink(result)',"$('saveAndPublish').onclick=saveAndPublish",
               "await saveGallery(true,{keepOpen:true})",'function rantlistDiscussionURL(publicLink)',
               "Nothing is posted automatically.","prepareRantlistHandoff"]:
   self.assertIn(item,HTML)
  self.assertIn('if(!keepOpen)hideModal(\'saveOverlay\')',HTML)
  self.assertIn('rel="noopener noreferrer"',HTML)
  self.assertIn('if(pendingClearAfterSave){saveHubStatus(',HTML)
  self.assertIn('No local save has been made.',HTML)

 def test_server_requires_owner_visible_csrf_and_explicit_action(self):
  self.assertIn("@app.post('/api/publications/<token>/share/rantlist')",BACKEND)
  self.assertIn('@auth\ndef share_publication_rantlist(token):\n    require_csrf()',BACKEND)
  self.assertIn('AND owner_id=? AND is_visible=1',BACKEND)
  self.assertIn('rantlist_bridge.send_publication(token,row[\'title\'])',BACKEND)
  self.assertIn('already_shared=True',BACKEND)
  self.assertIn("recent>=5",BACKEND)

 def test_db_migration_is_additive_and_idempotent(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'data.sqlite';db.init(path)
   with db.connect(path) as con:
    owner=con.execute("INSERT INTO users(username,password_hash) VALUES('artist','hash')").lastrowid
    token='A'*27
    con.execute('INSERT INTO publications(token,owner_id,title,file_name) VALUES(?,?,?,?)',(token,owner,'Public','public.png'))
    con.execute('INSERT INTO rantlist_publication_shares(publication_token,owner_id,message_id) VALUES(?,?,?)',(token,owner,'message-1234'))
   db.init(path)
   with db.connect(path) as con:
    row=con.execute('SELECT message_id FROM rantlist_publication_shares WHERE publication_token=?',(token,)).fetchone()
    self.assertEqual(row['message_id'],'message-1234')
    with self.assertRaises(sqlite3.IntegrityError):
     con.execute('INSERT INTO rantlist_publication_shares(publication_token,owner_id,message_id) VALUES(?,?,?)',(token,owner,'message-5678'))
    con.execute('DELETE FROM publications WHERE token=?',(token,))
    self.assertEqual(con.execute('SELECT count(*) FROM rantlist_publication_shares').fetchone()[0],0)

 def test_unconfigured_and_non_rantlist_hosts_rejected(self):
  with patch.dict(os.environ,{'PAINT_LAB_RANTLIST_BRIDGE_SECRET':'','PAINT_LAB_RANTLIST_BRIDGE_URL':rantlist_bridge.DEFAULT_URL}):
   self.assertFalse(rantlist_bridge.enabled())
   with self.assertRaises(rantlist_bridge.BridgeError):rantlist_bridge.send_publication('A'*28,'hello')
  with patch.dict(os.environ,{'PAINT_LAB_RANTLIST_BRIDGE_SECRET':'a'*40,'PAINT_LAB_RANTLIST_BRIDGE_URL':'http://127.0.0.1:1234/internal'}):
   self.assertFalse(rantlist_bridge.enabled())

 def test_signed_payload_pinned_target_and_ack(self):
  token='A'*28;secret='x'*40;captured=[]
  class Response:
   status=201
   def __enter__(self):return self
   def __exit__(self,*_):return None
   def read(self,size):return b'{"ok":true,"channel":"lobby","message_id":"test-message-123456"}'
  class Opener:
   def open(self,req,timeout):
    captured.append((req,timeout));return Response()
  with patch.dict(os.environ,{'PAINT_LAB_RANTLIST_BRIDGE_SECRET':secret,'PAINT_LAB_RANTLIST_BRIDGE_URL':rantlist_bridge.DEFAULT_URL}),patch.object(rantlist_bridge.urllib.request,'build_opener',return_value=Opener()),patch.object(rantlist_bridge.time,'time',return_value=1764000000):
   self.assertEqual(rantlist_bridge.send_publication(token,'Tree'),'test-message-123456')
  req,timeout=captured[0];self.assertEqual(req.full_url,rantlist_bridge.DEFAULT_URL)
  self.assertEqual(timeout,8)
  self.assertEqual(req.get_header('X-paint-lab-idempotency-key'),token)
  self.assertEqual(json.loads(req.data),{'version':1,'destination':'lobby','publication_id':token,'title':'Tree','url':'https://paint-lab.xyz/p/'+token})
  expected=hmac.new(secret.encode(),b'1764000000\n'+req.data,hashlib.sha256).hexdigest()
  self.assertEqual(req.get_header('X-paint-lab-signature'),'sha256='+expected)

 def test_bridge_documentation_and_version(self):
  self.assertTrue((APP/'docs/RANTLIST_INTEGRATION.md').is_file())
  self.assertIn('server-to-server', (APP/'docs/RANTLIST_INTEGRATION.md').read_text())
  self.assertEqual(json.loads((APP/'version.json').read_text())['version'],'0.1.78')

if __name__=='__main__':unittest.main()
