"""Static deployment checks that do not require nginx, certificates or SSH."""
import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class DeployContracts(unittest.TestCase):
 def test_domain_and_service_are_isolated(self):
  import deploy.install as installer
  self.assertEqual(installer.DOMAIN,'paint-lab.xyz')
  self.assertEqual(installer.PORT,18766)
  self.assertNotIn('free-lab.cam',installer.NGINX)
  self.assertIn('PAINT_LAB_MANAGED_V1',installer.NGINX)
  self.assertIn('location = /ws',installer.NGINX)
  self.assertIn('proxy_set_header Upgrade $http_upgrade',installer.NGINX)
  self.assertIn('try_files $uri =404;',installer.NGINX)
 def test_version_markers_match(self):
  manifest=json.loads((ROOT/'version.json').read_text())
  frontend=json.loads((ROOT/'frontend/version.json').read_text())
  html=(ROOT/'frontend/index.html').read_text()
  self.assertEqual(manifest['version'],frontend['version'])
  self.assertIn('name="paint-lab-version" content="'+manifest['version']+'"',html)
 def test_editor_and_cloud_workflows_exist(self):
  doc=(ROOT/'frontend/index.html').read_text()
  for marker in ('id="layersPanel"','id="toolRail"','id="materialQuick"','id="cloudOverlay"','id="cloudTop"','id="apiProvider"'):
   self.assertIn(marker,doc)
  self.assertNotIn('window.alert(',doc)
  self.assertNotIn('window.prompt(',doc)
 def test_typed_artwork_schema(self):
  source=(ROOT/'backend/app.py').read_text()
  for item in ('validate_document','/api/projects','/api/providers','/ws','/api/health'):
   self.assertIn(item,source)


class CertbotIdentityTests(unittest.TestCase):
 def test_reuses_existing_certbot_account_without_email(self):
  import tempfile
  from unittest.mock import patch
  import deploy.install as installer
  with tempfile.TemporaryDirectory() as tmp:
   from pathlib import Path
   root=Path(tmp);account=root/'existing-id';account.mkdir();(account/'regr.json').write_text('{}')
   with patch.object(installer,'CERTBOT_ACCOUNTS',root),patch.dict('os.environ',{},clear=True):
    options,message=installer.certbot_identity()
   self.assertEqual(options,['--account','existing-id'])
   self.assertIn('Reusing',message)
 def test_existing_email_is_optional_but_required_for_new_account(self):
  import tempfile
  from unittest.mock import patch
  import deploy.install as installer
  with tempfile.TemporaryDirectory() as tmp:
   with patch.object(installer,'CERTBOT_ACCOUNTS',Path(tmp)),patch.dict('os.environ',{},clear=True):
    with self.assertRaisesRegex(installer.DeployError,'PAINT_LAB_CERTBOT_EMAIL'):
     installer.certbot_identity()
   with patch.object(installer,'CERTBOT_ACCOUNTS',Path(tmp)),patch.dict('os.environ',{'PAINT_LAB_CERTBOT_EMAIL':'admin@example.org'},clear=True):
    options,_=installer.certbot_identity()
    self.assertEqual(options,['--email','admin@example.org'])
 def test_rejects_unknown_explicit_account(self):
  import tempfile
  from unittest.mock import patch
  import deploy.install as installer
  with tempfile.TemporaryDirectory() as tmp:
   with patch.object(installer,'CERTBOT_ACCOUNTS',Path(tmp)),patch.dict('os.environ',{'PAINT_LAB_CERTBOT_ACCOUNT':'missing'},clear=True):
    with self.assertRaisesRegex(installer.DeployError,'not found'):
     installer.certbot_identity()
