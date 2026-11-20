"""Mandatory SQLite and key vault tests, independent of Flask install availability."""
import tempfile,unittest,json,os
from pathlib import Path
from backend import db,keyvault

class StorageAndVault(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='paint-lab-storage-')
  self.addCleanup(self.temp.cleanup)
  self.folder=Path(self.temp.name)
  self.db=self.folder/'projects.sqlite3'
  self.old=os.environ.get('PAINT_LAB_VAULT_KEY_FILE')
  os.environ['PAINT_LAB_VAULT_KEY_FILE']=str(self.folder/'vault.key')
  self.addCleanup(self.restore_env)
  db.init(self.db)
 def restore_env(self):
  if self.old is None:os.environ.pop('PAINT_LAB_VAULT_KEY_FILE',None)
  else:os.environ['PAINT_LAB_VAULT_KEY_FILE']=self.old
 def test_schema_and_owned_projects(self):
  with db.connect(self.db) as con:
   owner=con.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',('owner','hash')).lastrowid
   rival=con.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',('rival','hash')).lastrowid
   content=json.dumps({'format':'paint-lab-webgl','version':3,'actions':[]})
   con.execute('INSERT INTO projects(id,owner_id,title,document) VALUES(?,?,?,?)',('a',owner,'My painting',content))
  with db.connect(self.db) as con:
   self.assertEqual(con.execute('SELECT count(*) FROM projects WHERE owner_id=?',(owner,)).fetchone()[0],1)
   self.assertEqual(con.execute('SELECT count(*) FROM projects WHERE owner_id=?',(rival,)).fetchone()[0],0)
   self.assertEqual(json.loads(con.execute('SELECT document FROM projects WHERE id=?',('a',)).fetchone()[0])['format'],'paint-lab-webgl')
 def test_key_is_encrypted_and_scoped(self):
  with db.connect(self.db) as con:
   owner=con.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',('owner','hash')).lastrowid
   rival=con.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',('rival','hash')).lastrowid
   keyvault.save(con,owner,'openai','sk-user-unshared-secret-99',self.folder)
  with db.connect(self.db) as con:
   self.assertEqual(keyvault.get(con,owner,'openai',self.folder),'sk-user-unshared-secret-99')
   self.assertIsNone(keyvault.get(con,rival,'openai',self.folder))
   self.assertNotIn('sk-user-unshared-secret-99',str(con.execute('SELECT ciphertext FROM provider_keys').fetchone()[0]))
  self.assertEqual(self.folder.joinpath('vault.key').stat().st_mode & 0o777,0o600)
