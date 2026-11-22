"""Published artwork owner management, privacy, filtering and backward compatible migration."""
import sqlite3,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from backend import db, public_discovery, public_viewer

class PublicManagement(unittest.TestCase):
 def setup_db(self,path):
  db.init(path)
  con=db.connect(path)
  first=con.execute("INSERT INTO users(username,password_hash) VALUES('FirstArtist','hash')").lastrowid
  second=con.execute("INSERT INTO users(username,password_hash) VALUES('SecondArtist','hash')").lastrowid
  tokens=['publication'+'a'*18,'publication'+'b'*18,'publication'+'c'*18]
  for i,(owner,token,name) in enumerate(zip([first,first,second],tokens,['Blue portrait','Hidden study','Other artist'])):
   con.execute('INSERT INTO publications(token,owner_id,title,file_name,created_at) VALUES(?,?,?,?,?)',
    (token,owner,name,token+'.png',f'2026-11-22T12:0{i}:00Z'))
  con.commit()
  return con,first,second,tokens

 def test_search_only_public_in_explore_and_owner_preview(self):
  with tempfile.TemporaryDirectory() as tmp:
   con,first,second,tokens=self.setup_db(Path(tmp)/'database.sqlite')
   con.execute('UPDATE publications SET is_visible=0 WHERE token=?',(tokens[1],));con.commit()
   f=public_discovery.normalized({'sort':'recent'})
   now=datetime(2026,11,22,tzinfo=timezone.utc)
   rows,total,_=public_discovery.search(con,f,now)
   self.assertEqual(total,2)
   self.assertNotIn(tokens[1],[row['token'] for row in rows])
   rows,total,_=public_discovery.search(con,f,now,owner_id=first)
   self.assertEqual(total,1)
   rows,total,_=public_discovery.search(con,f,now,owner_id=first,include_hidden=True)
   self.assertEqual(total,2)
   self.assertEqual([r['is_visible'] for r in rows],[0,1])
   rows,total,_=public_discovery.search(con,public_discovery.normalized({'q':'Hidden'}),now,owner_id=first,include_hidden=True)
   self.assertEqual(total,1)
   self.assertEqual(rows[0]['token'],tokens[1])
   con.close()

 def test_migration_preserves_all_existing_publications(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'legacy.sqlite';con=sqlite3.connect(path)
   con.execute('CREATE TABLE publications(token TEXT PRIMARY KEY,owner_id INTEGER,title TEXT,file_name TEXT,created_at TEXT)')
   con.execute("INSERT INTO publications VALUES ('oldtoken',1,'Legacy','old.png','2025-01-01T00:00:00Z')")
   con.commit();con.close()
   db.init(path)
   with db.connect(path) as upgraded:
    row=upgraded.execute('SELECT is_visible FROM publications WHERE token=?',('oldtoken',)).fetchone()
    self.assertEqual(row[0],1)

 def test_owner_gallery_filters_safe_markup_and_controls(self):
  f=public_discovery.normalized({'q':'blue','sort':'az','period':'today'})
  urls={'period':{p:'/u/FirstArtist?period='+p+'&edit=1' for p in public_discovery.PERIODS},'prev':None,'next':None}
  item={'token':'publication'+'x'*18,'title':'<img onerror=alert(1)>','image':'/api/publications/token/image.png',
   'url':'/p/publicationxxxxxxxx','artist_url':'/u/FirstArtist','username':'FirstArtist','created_at':'2026-11-22T12:00:00Z','visible':False}
  html=public_viewer.discover_markup([item],f,1,1,urls,artist='FirstArtist',edit=True,is_owner=True,csrf='fake-csrf',gallery_url='/u/FirstArtist')
  self.assertNotIn('<img onerror',html)
  self.assertIn('name="edit" value="1"',html)
  self.assertIn('action="/u/FirstArtist"',html)
  self.assertIn('data-visibility=',html)
  self.assertIn('data-remove=',html)
  self.assertIn('Hidden from public',html)
  self.assertNotIn('href="/p/publicationxxxxxxxx"',html)
  self.assertIn('data-csrf="fake-csrf"',html)
  self.assertIn('name="sort"',html)
  self.assertIn('name="from"',html)
  self.assertIn('name="to"',html)

 def test_endpoints_require_owner_csrf_and_hide_public_image(self):
  app=(Path(__file__).resolve().parents[1]/'backend/app.py').read_text()
  for marker in ["@app.patch('/api/publications/<token>')","@app.get('/api/publications/<token>/image.png')",
    'require_csrf()',"AND owner_id=?",'AND p.is_visible=1',"WHERE token=? AND is_visible=1"]:
   self.assertIn(marker,app)
  self.assertIn("if type(data.get('visible')) is not bool",app)
  self.assertIn('public_discovery.search(con(),filters,owner_id=row[\'id\'],include_hidden=edit)',app)

if __name__=='__main__':unittest.main()
