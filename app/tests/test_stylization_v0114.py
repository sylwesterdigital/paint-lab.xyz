"""Rendering contracts for v0.1.35 stroke-image stylization and legacy compatibility."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'frontend/index.html').read_text()
class StylizeTests(unittest.TestCase):
 def test_style_choices_are_stroke_presets_not_layer_actions(self):
  for style in ("'halftone'","'ascii'","'invert'","'pixelate'","'mosaic'","'symbols'","'mono'","'desaturate'","'solarize'","'edge'"):
   self.assertIn(style,SRC)
  self.assertIn('Stroke stylization · converts painted pixels',SRC)
  self.assertIn("styleEngine:'stroke-fx-v2'",SRC)
  self.assertIn("strokeEffect:strokeStyle==='none'?null",SRC)
  part=SRC[SRC.index('function selectStrokeStyle(name){'):SRC.index('function chooseMaterial(next){')]
  self.assertNotIn('setLayerFilters(',part)
  self.assertNotIn('addSelectedLayerFilter(',part)
  self.assertIn('b.onclick=()=>selectStrokeStyle(id)',part)
 def test_raw_stroke_to_image_filter_to_layer(self):
  for token in ('function initStrokeImageFX(', 'function paintIntoStrokeImage(', 'function strokeImageBounds(',
   'function renderStrokeImageFX(', 'function commitStrokeImageFX(', 'applyCompositeFilterStep(input,s.cfg.strokeEffect)',
   'target.ctx.drawImage(result.canvas,result.x,result.y)', 'paintIntoStrokeImage(s,()=>rawDrawStrokeStart(s))',
   'paintIntoStrokeImage(s,()=>rawDrawStrokeStep(s,b))', 'paintIntoStrokeImage(s,()=>rawFinishStrokeRender(s))',
   'if(hasStrokeImageFX(s))commitStrokeImageFX(s)', 'pctx.drawImage(result.canvas,result.x/dpr,result.y/dpr',
   "if(e.type!=='pointercancel'){finishStrokeRender(a);if(hasStrokeImageFX(a))commitStrokeImageFX(a);"):
   self.assertIn(token,SRC,token)
 def test_legacy_compatibility(self):
  self.assertIn("c?.styleEngine==='stroke-fx-v2'",SRC)
  self.assertIn("(conf.styleEngine&&conf.styleEngine!=='stroke-v1')?'none'",SRC)
  self.assertIn('stylizedStampTexture(baseStamp,strokeStylization,mat,t,col,conf)',SRC)
  self.assertIn('function updateLayerFilterCache(',SRC)
  self.assertIn("else if(a.kind==='layer-filter')",SRC)
 def test_release_integrity(self):
  v=json.loads((ROOT/'version.json').read_text())['version'];self.assertEqual(v,'0.1.35')
  log=json.loads((ROOT/'changelog.json').read_text());self.assertEqual(log['version'],v)
  self.assertEqual(log['history'][0]['version'],'0.1.34')
  self.assertIn('Painted-Stroke Image Filters',log['title'])
if __name__=='__main__':unittest.main()
