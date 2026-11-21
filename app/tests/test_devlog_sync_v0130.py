"""Fail-closed release generator refuses stale changelog bundles."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools import sync_devlog

APP=Path(__file__).resolve().parents[1]
class DevlogBuildV130(unittest.TestCase):
 def test_stale_fallback_rejected_then_repaired_only_by_explicit_sync(self):
  canonical=json.loads((APP/'changelog.json').read_text())
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'frontend').mkdir()
   for name in ('changelog.json','version.json','frontend/changelog.json','frontend/version.json'):
    file=root/name;file.parent.mkdir(exist_ok=True)
    file.write_bytes((APP/name).read_bytes())
   version=canonical['version']
   html=f'<meta name="paint-lab-version" content="{version}"><title>Paint Lab v{version}</title>\nconst DEVLOG_FALLBACK={{"project":"paint-lab","version":"0.1.26"}};\n'
   page=root/'frontend/index.html';page.write_text(html)
   with patch.object(sync_devlog,'APP',root):
    with self.assertRaisesRegex(ValueError,'Stale embedded development log'):
     sync_devlog.validate_or_sync(write=False)
    sync_devlog.validate_or_sync(write=True)
    self.assertEqual(sync_devlog.validate_or_sync(write=False),canonical)
 def test_disagreement_between_canonical_and_public_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'frontend').mkdir()
   for name in ('changelog.json','version.json','frontend/changelog.json','frontend/version.json'):
    file=root/name;file.write_bytes((APP/name).read_bytes())
   data=json.loads((root/'frontend/changelog.json').read_text());data['version']='0.1.26'
   (root/'frontend/changelog.json').write_text(json.dumps(data))
   with patch.object(sync_devlog,'APP',root):
    with self.assertRaisesRegex(ValueError,'disagree'):
     sync_devlog.validate_or_sync(write=False)

if __name__=='__main__':unittest.main()
