"""Source-level contracts for versioned, adaptive oil samples and tiled endpoints.

The pixel outcome is separately tested by tools/browser_oil_sparse_smoke.py.
"""
import unittest
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
SOURCE=(APP/'frontend/index.html').read_text()

class OilSparseV130(unittest.TestCase):
 def test_new_strokes_record_sampling_engine(self):
  self.assertIn("pencilEngine:'continuous-v1',oilSamplingEngine:'adaptive-v2'",SOURCE)
  self.assertIn("const oilEngine=s.cfg.oilSamplingEngine||'adaptive-v1';",SOURCE)
  self.assertIn("if(oilEngine==='adaptive-v1'){oilContactStroke(s,a,b);return;}",SOURCE)
 def test_interpolates_sparse_input_and_preserves_saved_legacy(self):
  for marker in ('const turnSegments=Math.ceil(turnDelta/(Math.PI/18));',
                 'const segments=Math.max(1,Math.ceil(dist/maxTravel),turnSegments);',
                 'oilContactStroke(s,previous,next);previous=next;',
                 'pressure:(a.pressure??1)+((b.pressure??1)-(a.pressure??1))*f',
                 't:Number(a.t??0)+(Number(b.t??0)-Number(a.t??0))*f'):
   self.assertIn(marker,SOURCE)
 def test_endpoint_tiles_are_bounded_and_legacy_is_guarded(self):
  body=SOURCE[SOURCE.index('function sculptOilEnvelope('):SOURCE.index('function finishOilStroke(')]
  self.assertIn("if(cfg.oilSamplingEngine!=='adaptive-v1'&&(x1-x0)*(y1-y0)>850000)return;",body)
  self.assertIn('const TILE=256,antialias=',body)
  self.assertIn('const image=paint.getImageData(tileX,tileY,w,h)',body)
  self.assertIn('paint.putImageData(image,tileX,tileY)',body)
  self.assertNotIn('if(w*h>850000)return;',body)

 def test_adaptive_v2_finishes_live_without_posthoc_recut(self):
  self.assertIn("}else if((s.cfg.oilSamplingEngine||'adaptive-v1')!=='adaptive-v2')finishOilStroke(s);",SOURCE)
  self.assertIn("Adaptive v2 keeps the stroke shape live while drawing",SOURCE)
 def test_browser_pixel_regression_present(self):
  smoke=(APP/'tools/browser_oil_sparse_smoke.py').read_text()
  for key in ("for dpr in (1,1.5):", "('rigger','round','flat')", "legacy=page.evaluate(", 'result[\'maxGap\']==0'):
   self.assertIn(key,smoke)

if __name__=='__main__':unittest.main()
