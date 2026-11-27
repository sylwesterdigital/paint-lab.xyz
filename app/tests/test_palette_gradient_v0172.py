"""Regression: active pigment is distinct from first/last palette gradient stops."""
from pathlib import Path
import json,unittest
APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
class PaletteGradientRegression(unittest.TestCase):
 def test_palette_selection_does_not_edit_first_stop(self):
  self.assertIn('function updateColor(c,updateFirstSwatch=true)',HTML)
  self.assertIn('selectPaletteSwatch(index);updateColor(c,false)',HTML)
  self.assertIn('selectPaletteSwatch(index);updateColor(hex,false)',HTML)
  self.assertIn('updateColor(editingActive?hex:previousPaintColor,false)',HTML)
 def test_gradient_uses_stored_endpoints(self):
  self.assertIn('gradientAnchors=normalizeGradientAnchors([{position:0,color:source[0]}',HTML)
  self.assertIn("$('currentColor').style.background=firstSwatch",HTML)
  self.assertIn("$('colorPicker').value=firstSwatch",HTML)
  self.assertIn("updateColor(data.color,false)",HTML)
 def test_release_metadata(self):
  j=json.loads((APP/'changelog.json').read_text())
  self.assertEqual(j['version'],'0.1.79')
  self.assertEqual(j['history'][0]['version'],'0.1.78')
  self.assertEqual(j,json.loads((APP/'frontend/changelog.json').read_text()))
if __name__=='__main__':unittest.main()
