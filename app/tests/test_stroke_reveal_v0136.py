"""v0.1.36: a stylization stroke reveals converted EXISTING imagery via alpha mask."""
from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'frontend/index.html').read_text()
class StrokeRevealV136(unittest.TestCase):
 def test_versioned_new_stroke_engine(self):
  self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.64')
  self.assertIn("styleEngine:'existing-image-fx-v3'",SOURCE)
  self.assertIn('Stroke-masked filters · reveal existing artwork',SOURCE)
 def test_source_pixels_not_own_pigment(self):
  for token in ('function captureExistingCanvasImage()',
                "ctx.drawImage(getLayerRenderCanvas(art),0,0);",
                "const source=isExistingImageFX(s)?captureExistingCanvasImage():null;",
                "ctx.drawImage(isExistingImageFX(s)?fx.source:fx.raw",
                "output.globalCompositeOperation='destination-in';",
                'output.drawImage(fx.raw,bounds.x,bounds.y,bounds.w,bounds.h,0,0,bounds.w,bounds.h);',
                'output.drawImage(input,0,0);'):
   self.assertIn(token,SOURCE,token)
 def test_replay_and_old_engine_support(self):
  self.assertIn("['stroke-fx-v2','existing-image-fx-v3'].includes(c?.styleEngine)",SOURCE)
  self.assertIn('if(hasStrokeImageFX(s))commitStrokeImageFX(s)',SOURCE)
  self.assertIn('if(hasStrokeImageFX(a))commitStrokeImageFX(a)',SOURCE)
  self.assertIn('const spacing=Math.max(3,Math.round(cell*dpr));',SOURCE)
 def test_acceptance_browser_script_is_shipped(self):
  test=(ROOT/'tools/browser_stroke_reveal_v0136.py').read_text()
  self.assertIn('blank image stays blank',test)
  self.assertIn('lower layer not sampled',test)
if __name__=='__main__':unittest.main()
