"""Static guards for adaptive palette and supplied panel control artwork."""
from pathlib import Path
import unittest
import json
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class PaletteContracts(unittest.TestCase):
 def test_palette_first_swatch_replaces_original_colour(self):
  self.assertIn("sw.append(picker);",HTML)
  self.assertIn("for(let index=1;index<palette.length;index++)",HTML)
  self.assertIn('const PALETTE_MODIFIERS=',HTML)
  self.assertIn('function updatePaletteGrid()',HTML)
  self.assertIn('paletteObserver.observe($(\'palettePanel\'))',HTML)
 def test_gradient_is_not_static_colour_bank(self):
  self.assertIn("if(name==='Gradients')",HTML)
  self.assertIn("source.at(-1)",HTML)
  self.assertIn('function interpolateGradient(stops,count)',HTML)
  self.assertIn('function colourToLab(hex)',HTML)
  self.assertIn('if(e.shiftKey)',HTML)
 def test_modifiers_reuse_current_palette(self):
  self.assertIn('const original=palette.slice(),source=',HTML)
  for name in ['Sepias','Pastels','Sharp','Chromatics','Warm','Cool','Earth','Neon','Muted','Vintage','Monochrome','Invert']:
   self.assertIn(name,HTML)
 def test_supplied_fit_collapse_distinct(self):
  self.assertIn('id="pl-panel-fit"',HTML)
  self.assertIn('id="pl-panel-collapse"',HTML)
  self.assertIn("fit.innerHTML=plIcon('panel-fit')",HTML)
  self.assertIn("plIcon(expanded?'panel-collapse':'panel-expand')",HTML)
 def test_release_histories(self):
  a=json.loads((ROOT/'changelog.json').read_text())
  b=json.loads((ROOT/'frontend/changelog.json').read_text())
  self.assertEqual(a,b)
  self.assertEqual(a['version'],'0.1.20')
  self.assertEqual(a['history'][0]['version'],'0.1.19')
if __name__=='__main__':unittest.main()
