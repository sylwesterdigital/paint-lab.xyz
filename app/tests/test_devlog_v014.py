"""Development log, GitHub documentation and versioned on-load behavior contracts."""
from pathlib import Path
import unittest,json,re
APP=Path(__file__).resolve().parents[1]
class ReleaseLogTests(unittest.TestCase):
 def test_canonical_public_log_match(self):
  latest=json.loads((APP/'changelog.json').read_text())
  public=json.loads((APP/'frontend/changelog.json').read_text())
  version=json.loads((APP/'version.json').read_text())['version']
  self.assertEqual(latest,public)
  self.assertEqual(latest['version'],version)
  self.assertEqual(latest['version'],json.loads((APP/'frontend/version.json').read_text())['version'])
  self.assertGreaterEqual(len(latest['history']),4)
  self.assertEqual([entry['version'] for entry in latest['history']][:5],['0.1.49','0.1.48','0.1.47','0.1.46','0.1.45'])
  self.assertEqual(latest['history'][-1]['version'],'0.1.0')
  for entry in [latest,*latest['history']]:self.assertTrue(entry.get('changes'))
 def test_modal_and_toolbar_exist(self):
  html=(APP/'frontend/index.html').read_text()
  for item in ('devLogTop','devLogOverlay','devLogLatest','devLogHistory','devLogArchive','devLogCurrent','devLogDone'):
   self.assertIn('id="'+item+'"',html)
  self.assertIn("const DEVLOG_SEEN_KEY='paint-lab-devlog-seen-v1'",html)
  self.assertIn('window.setTimeout(()=>{if(safeLocalGet(DEVLOG_SEEN_KEY)',html)
  self.assertIn("fetch(`./changelog.json?v=",html)
  self.assertIn('return devLogValid(data)?data:null',html)
  self.assertIn('https://github.com/sylwesterdigital/paint-lab.xyz/blob/main/CHANGELOG.md',html)
 def test_canonical_docs(self):
  for name in ('ABOUT.md','CHANGELOG.md','docs/GITHUB_README.md'):
   text=(APP/name).read_text()
   self.assertIn('https://paint-lab.xyz/',text)
   self.assertIn('https://github.com/sylwesterdigital/paint-lab.xyz',text)
   self.assertTrue(text.startswith('# '))
  self.assertIn('0.1.4',(APP/'CHANGELOG.md').read_text())
if __name__=='__main__':unittest.main()
