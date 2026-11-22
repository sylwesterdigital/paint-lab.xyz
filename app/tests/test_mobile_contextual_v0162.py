"""Mobile settings sheet is contextual, compact, and entirely driven by existing brush settings."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class MobileContextualTuning162(unittest.TestCase):
 def test_no_internal_mode_or_none_switches(self):
  self.assertIn('id="mobileDynamicsSheet"',HTML)
  self.assertNotIn('id="mobileDynamicsTabs"',HTML)
  self.assertNotIn('data-mobile-tuning-tab',HTML)
  self.assertNotIn('Tap to set None',HTML)
  self.assertIn("$('mobileDynamicsSheet').dataset.editor=tab;",HTML)
  self.assertIn("const MOBILE_TUNING_GROUPS={",HTML)
  for key in ('brush','effects','stylize'):
   self.assertIn(f"{key}:[",HTML)
 def test_mobile_slider_is_touch_sized_and_sheet_fits_height(self):
  for fragment in ('height:auto;', 'max-height:calc(100dvh', 'overflow-y:auto', '-webkit-overflow-scrolling:touch', 'width:38px;height:38px', 'height:45px', 'min-height:45px'):
   self.assertIn(fragment,HTML)
  self.assertIn("source.dispatchEvent(new Event('input',{bubbles:true}))",HTML)
 def test_long_press_opens_only_corresponding_editor(self):
  self.assertIn("initMobileModePress('mobileMaterial',mobileCycleMaterial,()=>openMobileTuning('brush'))",HTML)
  self.assertIn("initMobileModePress('mobileEffects',mobileCycleEffects,()=>openMobileTuning('effects'))",HTML)
  self.assertIn("initMobileModePress('mobileStylize',mobileCycleStylize,()=>openMobileTuning('stylize'))",HTML)
  self.assertIn("['Bristles & texture'",HTML)
  self.assertIn("['Natural stroke width'",HTML)
if __name__=='__main__':unittest.main()
