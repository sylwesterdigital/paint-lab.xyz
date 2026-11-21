"""Versioned regression contracts for composite layer stylization and legacy stroke compatibility."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'frontend/index.html').read_text()
class StylizeTests(unittest.TestCase):
 def test_composite_filter_catalog_and_ui(self):
  self.assertIn("const STROKE_STYLES=",JS)
  for style in ("'halftone'","'ascii'","'invert'","'pixelate'","'mosaic'","'symbols'","'mono'","'desaturate'","'solarize'","'edge'"):
   self.assertIn(style,JS)
  self.assertIn('Composite layer stylization · transforms existing pixels',JS)
  self.assertIn('id="addLayerFilter"',JS)
  self.assertIn('id="replaceLayerFilters"',JS)
  self.assertIn('id="layerFilterStack"',JS)
 def test_filter_stack_renderer_and_layer_action(self):
  self.assertIn('function applyCompositeFilterStep(',JS)
  self.assertIn('function updateLayerFilterCache(',JS)
  self.assertIn('function setLayerFilters(layerId,filters)',JS)
  self.assertIn("else if(a.kind==='layer-filter')",JS)
  self.assertIn("'layer-filter'",JS)
  self.assertIn('drawImage(getLayerRenderCanvas(l),0,0)',JS)
 def test_legacy_stroke_stylization_compatibility(self):
  self.assertIn("styleEngine:'layer-fx-v1'",JS)
  self.assertIn("(conf.styleEngine&&conf.styleEngine!=='stroke-v1')?'none'",JS)
  self.assertIn('stylizedStampTexture(baseStamp,strokeStylization,mat,t,col,conf)',JS)
  self.assertIn('function invertPaintStamp(',JS)
 def test_history_and_docs(self):
  v=json.loads((ROOT/'version.json').read_text())['version']
  self.assertEqual(v,'0.1.33')
  log=json.loads((ROOT/'changelog.json').read_text());self.assertEqual(log['version'],v)
  self.assertEqual(log['history'][0]['version'],'0.1.32')
  self.assertIn('Composite Layer Stylization',log['title'])
 if __name__=='__main__':
  unittest.main()
