"""Regression: startup progress, instant release notes, and admin-gated logs."""
import importlib.util,json,os,sqlite3,tempfile,unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
API=(APP/'backend/app.py').read_text()

class DiagnosticsContracts(unittest.TestCase):
    def test_recovery_and_news_nonblocking(self):
        self.assertIn('async function replayDraftIncrementally()',HTML)
        self.assertIn('function openDevLog(force=false)',HTML)
        self.assertIn("devLogRender(data);showModal('devLogOverlay')",HTML)
        self.assertIn("if(loadProject(draft.data,draft.artId||null,true))",HTML)
        self.assertIn('id="bootProgress"',HTML)
    def test_terminal_controls_and_security(self):
        for label in ('adminLogsOverlay','adminLogFont','adminLogOutput','adminLogPause','adminLogCopy'):
            self.assertIn('id="'+label+'"',HTML)
        self.assertIn("cloudUser.role==='admin'",HTML)
        self.assertIn('@admin_only',API)
        self.assertIn("request.url_rule.rule",API)
        self.assertIn("maxBytes=2_000_000",API)
        self.assertIn("logger.info('Paint Lab v%s service initialized",API)
        self.assertIn('def admin_logs():',API)
        self.assertNotIn('journalctl',API)
    def test_sqlite_existing_users_migrate(self):
        from backend import db
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'old.sqlite3'
            with sqlite3.connect(path) as con:
                con.execute('CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,password_hash TEXT)')
                con.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',('old_artist','hash'))
            db.init(path)
            with db.connect(path) as con:
                row=con.execute('SELECT role FROM users WHERE username=?',('old_artist',)).fetchone()
                self.assertEqual(row[0],'user')
                con.execute("UPDATE users SET role='admin' WHERE username='old_artist'")
                self.assertEqual(con.execute("SELECT role FROM users WHERE username='old_artist'").fetchone()[0],'admin')

AVAILABLE=all(importlib.util.find_spec(n) for n in ('flask','flask_sock','cryptography'))
@unittest.skipUnless(AVAILABLE,'Flask + flask-sock required; server tests enforce this')
class AdminAPITests(unittest.TestCase):
    def test_admin_endpoint_permissions(self):
        import subprocess,sys
        with tempfile.TemporaryDirectory(prefix='paint-lab-admin-') as folder:
            env={**os.environ,'PAINT_LAB_DATA_DIR':folder,'PAINT_LAB_DB':str(Path(folder)/'admin.sqlite3'),'PAINT_LAB_SESSION_KEY':'isolated-admin-test-key'}
            program=r"""
import json,sqlite3
from backend.app import app,DATABASE
app.config.update(TESTING=True,SESSION_COOKIE_SECURE=False)
unauth=app.test_client()
assert unauth.get('/api/admin/logs').status_code==401
cli=app.test_client();token=cli.get('/api/auth/me').json['csrf']
reg=cli.post('/api/auth/register',json={'username':'admin_diag_test','password':'a-very-long-password'},headers={'X-CSRF-Token':token})
assert reg.status_code==201,reg.json
assert cli.get('/api/admin/logs').status_code==403
with sqlite3.connect(DATABASE) as conn:conn.execute("UPDATE users SET role='admin' WHERE username=?",('admin_diag_test',))
assert cli.get('/api/auth/me').json['user']['role']=='admin'
data=cli.get('/api/admin/logs?limit=15')
assert data.status_code==200,data.json
assert len(data.json['lines'])<=15
assert 'a-very-long-password' not in json.dumps(data.json)
assert cli.get('/api/admin/logs?limit=foo').status_code==400
print('ADMIN_API_OK')
"""
            test=subprocess.run([sys.executable,'-c',program],cwd=APP,env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(test.returncode,0,test.stdout+'\n'+test.stderr)
            self.assertIn('ADMIN_API_OK',test.stdout)
