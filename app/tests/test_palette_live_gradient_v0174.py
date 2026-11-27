"""Regression contracts for v0.1.77 live position-based multi-stop gradient editor."""
import json,unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
class PaletteLiveGradient(unittest.TestCase):
 def test_intermediate_edit_creates_live_stop(self):
  for snippet in ('let gradientAnchors=[];',"if(paletteName==='Gradients'&&gradientAnchors.length>=2){",'setGradientAnchorAt(index/Math.max(1,palette.length-1),hex);','regenerateGradientPalette();','function interpolateAnchoredGradient(anchors,count)','function refreshGradientStopMarkers()'):
   self.assertIn(snippet,HTML)
 def test_stops_survive_size_and_settings(self):
  self.assertIn("if(paletteName==='Gradients'&&gradientAnchors.length>=2)regenerateGradientPalette();",HTML)
  self.assertIn('gradientAnchors:gradientAnchors.map(a=>({...a}))',HTML)
  self.assertIn('gradientAnchors=restored.length?restored:',HTML)
  self.assertIn("if(paletteName==='Gradients'&&gradientAnchors.length>=2){",HTML)
 def test_history(self):
  log=json.loads((APP/'changelog.json').read_text())
  self.assertEqual(log['version'],'0.1.78')
  self.assertEqual(log['history'][0]['version'],'0.1.77')
  self.assertEqual(log,json.loads((APP/'frontend/changelog.json').read_text()))
if __name__=='__main__':unittest.main()
