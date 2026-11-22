import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class AppearanceAndBrushDynamics(unittest.TestCase):
 def test_ui_controls(self):
  for name in ('appearanceBorder','appearanceBackground','appearanceShadows','appearanceShadowStrength','appearanceBlur','resetAppearance','naturalWidth','initialWidth','growthDistance','speedWidth'):
   self.assertIn('id="'+name+'"',HTML)
 def test_appearance_preset_restore(self):
  for s in ('uiAppearance:{...uiAppearance}','function applyAppearance(','applyAppearance(data.uiAppearance,false)','--pl-panel-alpha','--pl-border-alpha','data-pl-blur="off"'):
   self.assertIn(s,HTML)
 def test_tapered_replay_and_oil_contact(self):
  for s in ('function strokeWidthFactor(cfg,distance,speed=0)','naturalWidth,initialWidth,growthDistance,speedWidth','strokeWidthFactor(c,progress,speed)','strokeWidthFactor(c,distanceAlong','run.pathLength+=dist'):
   self.assertIn(s,HTML)
  self.assertIn('if(cfg.naturalWidth!==true)return 1;',HTML)
 def test_version_and_log(self):
  self.assertEqual(json.loads((ROOT/'changelog.json').read_text())['version'],'0.1.59')
  self.assertIn('content="0.1.59"',HTML)
  self.assertEqual(json.loads((ROOT/'changelog.json').read_text())['history'][0]['version'],'0.1.58')
if __name__=='__main__':unittest.main()
