"""Regression guard for v0.1.29 continuous pencil route and historical compatibility."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'frontend/index.html').read_text()

class ContinuousPencilTests(unittest.TestCase):
 def test_metadata(self):
  self.assertEqual(json.loads((ROOT/'changelog.json').read_text())['version'],'0.1.67')
  self.assertIn('<title>Paint Lab v0.1.67</title>',SRC)
 def test_new_strokes_record_engine(self):
  self.assertIn("pencilEngine:'continuous-v1'",SRC[SRC.index('function snapshot()'):SRC.index('function snapshot()')+750])
 def test_continuous_path_and_legacy_fallback(self):
  body=SRC[SRC.index('function continuousPencil('):SRC.index('function finishStrokeRender(')]
  self.assertIn("c.pencilEngine==='continuous-v1'",body)
  for symbol in ['function pencilContactWidth(','function pencilContactAlpha(','function pencilDrawPath(','quadraticCurveTo','function pencilStrokeStep(','function pencilStrokeFinish(']:
   self.assertIn(symbol,body)
  self.assertIn('if(continuousPencil(s)){pencilStrokeStart(s);return;}',SRC)
  self.assertIn('if(continuousPencil(s)){pencilStrokeStep(s,b);return;}',SRC)
  self.assertIn('if(continuousPencil(s)){pencilStrokeFinish(s);return;}',SRC)
  self.assertIn('return c.pencilEngine===',body)
 def test_no_repeated_tip_stamps(self):
  body=SRC[SRC.index('function pencilDrawPath('):SRC.index('function pencilStrokeFinish(')]
  self.assertNotIn('paintTip(',body)
  self.assertNotIn('materialStampTexture(',body)
  self.assertNotIn('pigmentStamp(',body)
  self.assertIn('strokeTravelColour(c,pathDistance)',body)

if __name__=='__main__':unittest.main()
