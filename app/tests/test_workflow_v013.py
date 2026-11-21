"""Regression contracts for Paint Lab 0.1.3 artist controls and layer performance."""
from pathlib import Path
import re
import unittest
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text(encoding='utf-8')
class ArtistWorkflowTests(unittest.TestCase):
 def test_quick_pigments_and_status(self):
  for material in ('pencil','chalk','watercolor','oil'):
   self.assertIn('data-material-choice="'+material+'"',HTML)
  for name in ('hudMode','hudEffect','hudMaterial','hudTip','hudPigment','hudSize','hudZoom'):
   self.assertIn('id="'+name+'"',HTML)
  self.assertIn("if(['1','2','3','4'].includes(key))",HTML)
 def test_palette_first_swatch_is_picker(self):
  self.assertRegex(HTML,r'id="swatches"[^>]*><div id="currentColor"')
  self.assertNotIn('class="color-strip"',HTML)
  self.assertNotIn('id="paletteStrip"',HTML)
  self.assertIn('id="importImage"',HTML)
  self.assertIn('id="generatePalette"',HTML)
 def test_visual_tip_library_and_serialized_imports(self):
  for item in ('tipCategories','tipGrid','importBrushTip','captureBrushTip'):
   self.assertIn('id="'+item+'"',HTML)
  self.assertIn('function normalizeTipImage(',HTML)
  self.assertIn('function restoreCustomTips(',HTML)
  self.assertIn("customTips:serializeCustomTips()",HTML)
  self.assertIn("const custom=tintCustomTip(t,col)",HTML)
 def test_layer_operations_incremental(self):
  line=HTML.split('function layerAction(a){',1)[1].split('\nfunction addPaintLayer(',1)[0]
  self.assertIn('applyLayerAction(action)',line)
  self.assertNotIn('rebuild()',line)
  self.assertNotIn('toDataURL',HTML.split('function renderLayers(){',1)[1].split('function undo(){',1)[0])
  self.assertIn("document.createElement('canvas');thumb.width=80",HTML)
if __name__=='__main__':unittest.main()
