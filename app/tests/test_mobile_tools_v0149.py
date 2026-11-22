"""Contracts for visible mobile effects/stylize, combined brush control and reset-clear safety."""
import unittest
from pathlib import Path

PAGE=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
class MobileControlV149(unittest.TestCase):
 def test_toolbar_no_duplicate_share_or_size(self):
  for key in ['mobileBrush','mobileBrushNumber','mobileSwatch','mobileLayers','mobileEffects','mobileStylize','mobileEffectsNone','mobileStylizeNone']:
   self.assertIn('id="'+key+'"',PAGE)
  self.assertNotIn('id="mobileShare"',PAGE)
  self.assertNotIn('id="mobileSizeButton"',PAGE)
  self.assertIn("$('mobileBrush').onclick=()=>toggleMobilePopover('mobileBrushPopover')",PAGE)
  self.assertIn("$('mobileLayers').onclick=()=>",PAGE)
 def test_mobile_none_states_and_routed_effects(self):
  self.assertIn('const MOBILE_EFFECT_MODES=[0,',PAGE)
  self.assertIn('function mobileCycleEffects()',PAGE)
  self.assertIn('function mobileCycleStylize()',PAGE)
  self.assertIn("$('mobileEffectsNone').onclick=()=>setMode(0)",PAGE)
  self.assertIn("$('mobileStylizeNone').onclick=()=>{selectStrokeStyle('none')",PAGE)
  self.assertIn("if(next!==0&&strokeStyle!=='none')selectStrokeStyle('none')",PAGE)
  self.assertIn("if(next!=='none'&&mode!==0)setMode(0)",PAGE)
 def test_optional_clear_reset_is_guarded(self):
  self.assertIn('id="clearResetTools"',PAGE)
  self.assertIn('function resetPaintingTools()',PAGE)
  self.assertIn('function clearCanvasPaint(resetTools=false)',PAGE)
  self.assertIn('if(resetTools)resetPaintingTools()',PAGE)
  self.assertIn('pendingClearResetTools',PAGE)
  self.assertIn('const clearAfterSave=pendingClearAfterSave,resetAfterSave=pendingClearResetTools',PAGE)
 def test_layers_bigger_and_mobile_sheet_smaller(self):
  self.assertIn('id="layersPanel"',PAGE)
  self.assertIn('#layersPanel.mobile-sheet-active{height:min(60dvh,490px)!important',PAGE)
  self.assertIn('.layer-thumb{width:76px!important;height:76px!important}',PAGE)
  self.assertIn('id="mobileLayers"',PAGE)
if __name__=='__main__':unittest.main()
