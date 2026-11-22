"""Release contracts; physical opacity/brush variation also checked in Chromium."""
from pathlib import Path
import json, unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'frontend/index.html').read_text()

class OilBodyAndStartup(unittest.TestCase):
    def test_oil_body_is_overlapping_and_loaded(self):
        self.assertIn("const stepLength=engine==='adaptive-v2'?Math.max(.45,Math.min(1.65,width*.018)):Math.max(.7,Math.min(3.1,width*.030)),steps=clamp(Math.ceil(travel/stepLength),1,engine==='adaptive-v2'?240:120);",SOURCE)
        self.assertIn("engine==='adaptive-v2'?1.38+visc*.41:1.24+visc*.34",SOURCE)
        self.assertIn("const weight=Math.pow(Math.max(0,1-distSq),engine==='adaptive-v2' ? .38 : .45)",SOURCE)
        self.assertIn('(.62+.38*br.shape)',SOURCE)
        self.assertIn('const broken=',SOURCE)
        self.assertIn('br.load=Math.max(.24+load*.23',SOURCE)
    def test_version_title_and_startup_brand(self):
        self.assertIn('<title>Paint Lab v0.1.41</title>',SOURCE)
        self.assertIn('id="startupBrand"',SOURCE)
        self.assertIn('function showBrandIntro()',SOURCE)
        self.assertIn('pointer-events:none;opacity:0',SOURCE)
        self.assertIn('showBrandIntro();',SOURCE)
    def test_untitled_is_fallback_not_input_value(self):
        self.assertIn("$('artName').value=saveAsNew&&['Untitled painting','Untitled'].includes(artName)?'':artName",SOURCE)
        self.assertIn("$('artName').value.trim()||'Untitled'",SOURCE)
    def test_metadata(self):
        log=json.loads((ROOT/'changelog.json').read_text())
        self.assertEqual(log['version'],'0.1.41')
        self.assertEqual(log['history'][0]['version'],'0.1.40')

if __name__=='__main__':unittest.main()
