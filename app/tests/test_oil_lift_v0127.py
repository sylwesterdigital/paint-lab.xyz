"""v0.1.27 oil release: no separate cap; family-specific, motion-dependent final contact."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'frontend/index.html').read_text()

class OilLiftTests(unittest.TestCase):
 def test_version(self):
  self.assertEqual(json.loads((ROOT/'changelog.json').read_text())['version'],'0.1.27')
  self.assertIn('<title>Paint Lab v0.1.27</title>',SRC)
 def test_model(self):
  body=SRC[SRC.index('function oilReleaseBehaviour('):SRC.index('function finishStrokeRender(')]
  for key in ['function oilReleaseMetrics(', 'function finishOilStroke(', 'slowing', 'endPressure', 'tipWidth', 'originalOilPigment(', 'const segments=[]', 'release.length', 'const antialias=', 'const excess=', 'paint.putImageData(image,x0,y0)']:
   self.assertIn(key,body)
  self.assertNotIn('ctx.arc(',body)
  self.assertNotIn('paint.arc(',body)
 def test_tip_families(self):
  body=SRC[SRC.index('function oilReleaseBehaviour('):SRC.index('function oilReleaseMetrics(')]
  for key in ['rigger','needler','pointed','sword','round','filbert','mop','flat','bright','chisel','rake','haircomb','fan']:
   self.assertIn("'"+key+"'",body)
 def test_replay_and_live_finish(self):
  self.assertIn('finishStrokeRender(a);delete a._run;',SRC)
  self.assertIn('finishStrokeRender(s);s._run=null;',SRC)
  self.assertIn('oilContactStroke(s,a,b);return;',SRC)
  self.assertIn('if(w*h>850000)return;',SRC)
if __name__=='__main__':unittest.main()
