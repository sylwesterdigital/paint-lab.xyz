"""Run with the release-installed Flask, flask-sock and cryptography packages."""
import importlib.util,json,os,sqlite3,tempfile,unittest
from pathlib import Path

AVAILABLE=all(importlib.util.find_spec(n) for n in ('flask','flask_sock','cryptography'))

@unittest.skipUnless(AVAILABLE,'Flask/flask-sock not installed in local validator (required on Ubuntu)')
class PaintLabAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='paint-lab-test-')
        data=Path(cls.temp.name)
        os.environ['PAINT_LAB_DATA_DIR']=str(data)
        os.environ['PAINT_LAB_DB']=str(data/'test.sqlite3')
        os.environ['PAINT_LAB_VAULT_KEY_FILE']=str(data/'vault.key')
        os.environ['PAINT_LAB_SESSION_KEY']='test-key-for-isolated-unit-tests'
        from backend.app import app,DATABASE
        cls.app=app;cls.database=DATABASE
        app.config.update(TESTING=True,SESSION_COOKIE_SECURE=False)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.c=self.app.test_client()
        self.token=self.c.get('/api/auth/me').json['csrf']

    def post(self,route,payload):return self.c.post(route,json=payload,headers={'X-CSRF-Token':self.token})
    def register(self,name,password='correct-horse-battery-staple'):
        response=self.post('/api/auth/register',{'username':name,'password':password})
        self.assertEqual(response.status_code,201,response.json)
        self.token=response.json['csrf'];return response

    def sample(self):return {'format':'paint-lab-webgl','version':4,'baseW':900,'baseH':700,'actions':[],'title':'Canvas'}

    def test_v4_document_and_format_contract(self):
        self.register('artist_v4_formats')
        doc=self.sample()
        doc['actions']=[{'kind':'stroke','layerId':'base-layer','seed':53,
            'cfg':{'styleEngine':'existing-image-fx-v3','strokeEffect':{'kind':'ascii','cell':16,'amount':1}},
            'points':[{'x':20,'y':40},{'x':35,'y':41}]},
            {'kind':'layer-filter','layerId':'base-layer','filters':[]}] 
        saved=self.post('/api/projects',{'title':'Version 4 — stylized','document':doc})
        self.assertEqual(saved.status_code,201,saved.json)
        loaded=self.c.get('/api/projects/'+saved.json['id'])
        self.assertEqual(loaded.status_code,200,loaded.json)
        self.assertEqual(loaded.json['project']['document'],doc)
        changed=self.c.put('/api/projects/'+saved.json['id'],json={
            'title':'v4 overwritten','document':doc},headers={'X-CSRF-Token':self.token})
        self.assertEqual(changed.status_code,200,changed.json)
        report=self.c.get('/api/health').json
        self.assertEqual(report['current_editable_format'],4)
        self.assertEqual(report['editable_formats'],[2,3,4])
        self.assertEqual(report['public_share_format'],'image/png')
        doc['version']=5
        rejected=self.post('/api/projects',{'title':'Not supported','document':doc})
        self.assertEqual(rejected.status_code,400,rejected.json)

    def test_health_and_version(self):
        r=self.c.get('/api/health');self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['websocket']);self.assertEqual(r.json['storage'],'sqlite')

    def test_auth_and_csrf(self):
        self.assertEqual(self.c.post('/api/auth/register',json={'username':'no-csrf','password':'long-enough-password'}).status_code,403)
        self.register('user_auth')
        self.assertTrue(self.c.get('/api/auth/me').json['authenticated'])
        self.assertEqual(self.post('/api/auth/logout',{}).status_code,200)
        self.token=self.c.get('/api/auth/me').json['csrf']
        self.assertEqual(self.post('/api/auth/login',{'username':'user_auth','password':'wrong'}).status_code,401)
        login=self.post('/api/auth/login',{'username':'user_auth','password':'correct-horse-battery-staple'})
        self.assertEqual(login.status_code,200);self.token=login.json['csrf']

    def test_project_crud_and_owner_isolation(self):
        self.register('artist_projects')
        made=self.post('/api/projects',{'title':'Test canvas','document':self.sample()})
        self.assertEqual(made.status_code,201,made.json);pid=made.json['id']
        get=self.c.get('/api/projects/'+pid)
        self.assertEqual(get.json['project']['document']['format'],'paint-lab-webgl')
        self.assertEqual(len(self.c.get('/api/projects').json['projects']),1)
        updated=self.c.put('/api/projects/'+pid,json={'title':'Renamed','document':self.sample()},headers={'X-CSRF-Token':self.token})
        self.assertEqual(updated.status_code,200)
        other=self.app.test_client();key=other.get('/api/auth/me').json['csrf']
        res=other.post('/api/auth/register',json={'username':'other_artist','password':'correct-horse-battery-staple'},headers={'X-CSRF-Token':key})
        self.assertEqual(res.status_code,201)
        self.assertEqual(other.get('/api/projects/'+pid).status_code,404)
        self.assertEqual(self.c.delete('/api/projects/'+pid,headers={'X-CSRF-Token':self.token}).status_code,200)
        self.assertEqual(self.c.get('/api/projects/'+pid).status_code,404)

    def test_provider_secret_not_returned(self):
        self.register('artist_api_keys')
        key='sk-user-private-1234567890'
        res=self.c.put('/api/providers/openai',json={'key':key},headers={'X-CSRF-Token':self.token})
        self.assertEqual(res.status_code,200,res.json)
        status=self.c.get('/api/providers').get_json()
        self.assertNotIn(key,json.dumps(status));self.assertTrue(next(x for x in status['providers'] if x['id']=='openai')['configured'])
        with sqlite3.connect(self.database) as con:
            record=con.execute("SELECT ciphertext FROM provider_keys WHERE provider='openai'").fetchone()[0]
            self.assertNotIn(key.encode(),record)
        self.assertEqual(self.c.delete('/api/providers/openai',headers={'X-CSRF-Token':self.token}).status_code,200)

    def test_reject_bad_project_and_cross_origin(self):
        self.register('artist_validation')
        self.assertEqual(self.post('/api/projects',{'title':'Bad','document':{'a':1}}).status_code,400)
        invalid=self.c.post('/api/projects',json={'title':'Bad','document':self.sample()},headers={'X-CSRF-Token':self.token,'Origin':'https://untrusted.invalid'})
        self.assertEqual(invalid.status_code,403)
