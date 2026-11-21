"""Oil-contact painting and shared brush preview atlas regression contract."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'frontend/index.html').read_text()
class OilAtlasTests(unittest.TestCase):
 def test_no_individual_brush_preview_canvases(self):
  self.assertIn('let tipAtlas=null;',JS)
  self.assertIn('const atlas=document.createElement(\'canvas\')',JS)
  self.assertIn('b.innerHTML=\'<div class="tip-art"',JS)
  self.assertNotIn('<canvas width="180" height="112"',JS)
  self.assertIn('if(!tipAtlas||tipAtlas.signature!==signature)',JS)
 def test_oil_uses_bounded_contact_patches(self):
  self.assertIn('function oilContactStroke(s,a,b)',JS)
  self.assertIn('const patch=paint.getImageData(x0,y0,patchW,patchH)',JS)
  self.assertIn('paint.putImageData(patch,x0,y0)',JS)
  self.assertIn('if(area>2100000)return',JS)
  self.assertIn('oilContactStroke(s,a,b);return;',JS)
  self.assertIn('const reflectance=',JS)
 def test_no_invert_canvas_allocation_per_dab(self):
  self.assertIn('const invertMaskCanvas=document.createElement(\'canvas\')',JS)
  self.assertIn('const c=invertMaskContext;c.setTransform(1,0,0,1,0,0)',JS)
if __name__=='__main__':unittest.main()
