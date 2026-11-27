"""New mobile brush dynamics and right-aligned eraser regression contracts."""
import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class MobileDynamics161(unittest.TestCase):
 def test_release_markers(self):
  self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.78')
  self.assertEqual(json.loads((ROOT/'frontend/changelog.json').read_text())['version'],'0.1.78')
  self.assertIn('<meta name="paint-lab-version" content="0.1.78">',HTML)
 def test_eraser_is_grouped_immediately_before_history(self):
  m=re.search(r'<div id="mobileUndoRedo".*?</div>',HTML,re.S)
  self.assertIsNotNone(m)
  group=m.group(0)
  self.assertLess(group.index('id="mobileErase"'),group.index('id="mobileUndo"'))
  self.assertLess(group.index('id="mobileUndo"'),group.index('id="mobileRedo"'))
  self.assertEqual(HTML.count('id="mobileErase"'),1)
  self.assertIn('function toggleMobileEraser()',HTML)
  self.assertIn('setMode(mobilePreEraserMode===1?0:mobilePreEraserMode)',HTML)
  self.assertIn('pigment:true,eraser:true,history:true',HTML)
  self.assertIn('eraserPlacementV61',HTML)
 def test_long_hold_opens_specific_editor_without_duplicating_tip_controls(self):
  self.assertIn("initMobileModePress('mobileMaterial',mobileCycleMaterial,()=>openMobileTuning('brush'))",HTML)
  self.assertIn("initMobileModePress('mobileEffects',mobileCycleEffects,()=>openMobileTuning('effects'))",HTML)
  self.assertIn("initMobileModePress('mobileStylize',mobileCycleStylize,()=>openMobileTuning('stylize'))",HTML)
  self.assertIn('id="mobileDynamicsSheet"',HTML)
  self.assertIn('id="mobileDynamicsBody"',HTML)
  self.assertNotIn('id="mobileDynamicsTabs"',HTML)
  self.assertNotIn('data-mobile-tuning-tab',HTML)
  self.assertIn("['Bristles & texture'",HTML)
  self.assertEqual(HTML.count('id="mobileBrush"'),1)
  self.assertNotIn('id="mobileTipCycle"',HTML)
 def test_existing_desktop_values_are_canonical(self):
  self.assertIn('const source=$(id);if(!source)continue;',HTML)
  self.assertIn("source.dispatchEvent(new Event('input',{bubbles:true}))",HTML)
  self.assertIn("source.dispatchEvent(new Event('change',{bubbles:true}))",HTML)
  for key in ('strength','flow','wetness','density','scatter','stiffness','paintLoad','bristleCount','bristleLength','spacing','viscosity','initialWidth','growthDistance','speedWidth','pencilHardness','pencilPressureSpan','styleAmount','styleCell'):
   self.assertIn(f'id="{key}"',HTML)
  self.assertIn('mobile-tuning-control input[type="range"]',HTML)
if __name__=='__main__':unittest.main()
