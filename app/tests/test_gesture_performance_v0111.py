"""Regression contracts: navigation must not recomposite or replay every layer."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class GestureRegression(unittest.TestCase):
 def test_static_document_compositing(self):
  self.assertIn('if(compositeDirty)composeLayers()',HTML)
  self.assertIn('vec2 uv=local/uDocument+.5',HTML)
  self.assertIn('layerCtx.drawImage(getLayerRenderCanvas(l),0,0)',HTML)
  self.assertIn('fallback.drawImage(layer,0,0,baseW,baseH)',HTML)
  self.assertNotIn('composedViewKey',HTML)
 def test_touch_navigation_lightweight(self):
  self.assertIn('navigationFast=true;',HTML)
  self.assertIn('finishDrawingForGesture();',HTML)
  self.assertIn('function finishDrawingForGesture()',HTML)
  self.assertIn('if(navigationFast||gesture)return;',HTML)
  self.assertIn('if(!navigationFast)renderPreview();',HTML)
  self.assertIn('gl.uniform1f(loc.fast,navigationFast?1:(isMobileWorkspace()?.25:0))',HTML)
 def test_contextual_mobile_transforms(self):
  self.assertIn("name==='transform'?!transformMode||!mobileOptions.transform",HTML)
  for label in ('move','rotate','scale'):
   self.assertIn(f'data-transform="{label}" aria-label="{label.title()} layer"',HTML)
  self.assertIn("$('transformDone').onclick",HTML)
if __name__=='__main__':unittest.main()
