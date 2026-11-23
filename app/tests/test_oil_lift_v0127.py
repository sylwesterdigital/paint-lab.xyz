"""v0.1.29 oil release: contact envelopes replace separate endpoint caps."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'frontend/index.html').read_text()

class OilLiftTests(unittest.TestCase):
 def test_version(self):
  self.assertEqual(json.loads((ROOT/'changelog.json').read_text())['version'],'0.1.64')
  self.assertIn('<title>Paint Lab v0.1.64</title>',SRC)
 def test_model(self):
  body=SRC[SRC.index('function oilReleaseBehaviour('):SRC.index('// v0.1.29: A graphite pencil')]
  for key in ['function oilReleaseMetrics(', 'function finishOilStroke(', 'slowing', 'endPressure', 'tipWidth', 'originalOilPigment(', 'const segments=[]', 'profile.length', 'antialias=Math.max(', 'const excess=', 'paint.putImageData(image,tileX,tileY)']:
   self.assertIn(key,body)
  self.assertNotIn('ctx.arc(',body)
  self.assertNotIn('paint.arc(',body)
 def test_tip_families(self):
  body=SRC[SRC.index('function oilReleaseBehaviour('):SRC.index('function oilReleaseMetrics(')]
  for key in ['rigger','needler','pointed','sword','round','filbert','mop','flat','bright','chisel','rake','haircomb','fan']:
   self.assertIn("'"+key+"'",body)
 def test_replay_and_live_finish(self):
  self.assertIn("if(e.type!=='pointercancel'){finishStrokeRender(a);if(hasStrokeImageFX(a))commitStrokeImageFX(a);}",SRC)
  self.assertIn('finishStrokeRender(s);if(hasStrokeImageFX(s))commitStrokeImageFX(s);s._run=null;',SRC)
  self.assertIn('oilContactStroke(s,previous,next);previous=next;',SRC)
  self.assertIn('const TILE=256,antialias=',SRC)
if __name__=='__main__':unittest.main()
