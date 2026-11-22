"""v0.1.58: one unchanged brush button handles rail, tip cycle and gallery."""
from pathlib import Path
import json
import unittest
APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()

class SingleBrushLauncherV157(unittest.TestCase):
 def test_release(self):
  self.assertEqual(json.loads((APP/'version.json').read_text())['version'],'0.1.62')
 def test_one_fixed_size_control_above_swatch(self):
  section=HTML.split('id="mobileBrushTop" class="mobile-brush-top"',1)[1].split('</div>',1)[0]
  self.assertEqual(section.count('<button'),1)
  self.assertIn('id="mobileBrush"',section)
  self.assertIn('id="mobileBrushLauncherImage"',section)
  self.assertNotIn('mobileBrushNumber',section)
 def test_popup_has_slider_not_another_tip_button(self):
  popup=HTML.split('<div id="mobileBrushPopover"',1)[1].split('<div id="mobileBrushSizePreview"',1)[0]
  self.assertIn('id="mobileSizeSlider"',popup)
  self.assertNotIn('<button',popup)
  self.assertNotIn('id="mobileTipCycle"',HTML)
  self.assertNotIn('id="mobileBrushImage"',HTML)
 def test_same_button_cycles_once_open_and_hold_opens_gallery(self):
  body=HTML.split('function handleMobileBrushTap(){',1)[1].split('\nfunction initMobileBrushController(){',1)[0]
  self.assertIn("$('mobileBrushPopover').classList.contains('open')",body)
  self.assertIn('mobileNextTip();showMobileBrushSizePreview()',body)
  self.assertIn("toggleMobilePopover('mobileBrushPopover')",body)
  self.assertIn("const button=$('mobileBrush')",HTML)
  self.assertIn('holdTimer=setTimeout(()=>{holdTimer=null;held=true;},500)',HTML)
  self.assertIn('setTimeout(()=>openMobileTipGallery(),130)',HTML)
  self.assertIn('function openMobileTipGallery()',HTML)
 def test_gallery_and_preview_persist(self):
  self.assertIn('function drawMobileActualTip()',HTML)
  self.assertIn("for(const id of ['mobileBrushLauncherImage'])",HTML)
  self.assertIn("if(entry.recipe)applyBrushRecipe(entry.recipe)",HTML)
  self.assertIn('function showMobileBrushSizePreview()',HTML)
  self.assertNotIn('id="mobileBrushNumber"',HTML)
if __name__=='__main__':unittest.main()
