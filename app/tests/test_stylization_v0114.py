"""Versioned regression contracts for stylized brush effects and directional oil flow."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'frontend/index.html').read_text()
class StylizeTests(unittest.TestCase):
 def test_styles_independent_of_material_and_tool(self):
  self.assertIn("const STROKE_STYLES=",JS)
  for style in ("'halftone'","'ascii'","'invert'","'pixelate'","'mosaic'","'symbols'"):
   self.assertIn(style,JS)
  self.assertIn('function snapshot(){return {color,mode,tip,material,naturalWidth,initialWidth,growthDistance,speedWidth,strokeStyle,styleCell,styleAmount,size,',JS)
  self.assertIn('stylizedStampTexture(baseStamp,strokeStylization,mat,t,col,conf)',JS)
 def test_bounded_cache_and_oil_bristles(self):
  self.assertIn('STYLE_STAMP_CACHE.size>=64',JS)
  self.assertIn('function oilRibbonSegment(',JS)
  self.assertIn('paint.quadraticCurveTo(',JS)
  self.assertIn('underColor',JS)
  self.assertIn('function invertPaintStamp(',JS)
  self.assertIn('seen.has(index)',JS)
 def test_ui_and_project_settings(self):
  self.assertIn('id="brushTabStyle"',JS)
  self.assertIn('data-focus-tab="style"',JS)
  self.assertIn('data-mobile-tab="style"',JS)
  self.assertIn('strokeStyle,styleCell,styleAmount,customTips:',JS)
 def test_history_and_docs(self):
  v=json.loads((ROOT/'version.json').read_text())['version']
  self.assertEqual(v,'0.1.31')
  log=json.loads((ROOT/'changelog.json').read_text());self.assertEqual(log['version'],v)
  self.assertEqual(log['history'][0]['version'],'0.1.30')
  self.assertIn('David Li',(ROOT/'CHANGELOG.md').read_text())
if __name__=='__main__':unittest.main()
