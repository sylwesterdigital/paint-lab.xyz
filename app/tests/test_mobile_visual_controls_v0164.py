"""Release contracts: centred closers, theme-safe brush tips, and all mobile sliders."""
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/'frontend/index.html'
SRC=P.read_text()
class MobileVisualControls164(unittest.TestCase):
 def test_close_button_centring(self):
  self.assertIn('button:has(> .svg-icon use[href="#pl-close"])',SRC)
  self.assertIn('place-items:center!important',SRC)
  for element in ('closeSettings','mobileTipGalleryClose','mobileDynamicsClose','mobileLayerOpacityClose'):
   self.assertIn(f'id="{element}"',SRC)
 def test_contrast_tip_gallery_previews(self):
  self.assertIn('luminance>.67',SRC)
  self.assertIn("canvas.style.backgroundColor=luminance>.67?'#27312e':'#fafaf5'",SRC)
  self.assertIn('ctx.fillStyle=color;ctx.strokeStyle=color',SRC)
 def test_mobile_slider_heads_everywhere(self):
  self.assertIn(':root.mobile-workspace input[type="range"]::-webkit-slider-thumb',SRC)
  self.assertIn('width:34px;height:34px',SRC)
  self.assertIn('width:38px;height:38px',SRC)
  self.assertIn(':root[data-pl-shadows="off"].mobile-workspace input[type="range"]::-webkit-slider-thumb',SRC)
if __name__=='__main__':unittest.main()
