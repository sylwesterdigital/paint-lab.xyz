"""Core behavioural contracts for the canvas/document and the compact brush workspace."""
import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'frontend/index.html').read_text()
class ViewAndBrushContracts(unittest.TestCase):
 def test_camera_does_not_invalidate_artwork_composite(self):
  self.assertNotIn("if(composedViewKey!==viewKey){composedViewKey=viewKey;compositeDirty=true;}",s)
  self.assertIn("if(compositeDirty)composeLayers();",s)
  self.assertIn("vec2 uv=local/uDocument+.5",s)
  self.assertIn("function applyViewAnchor",s)
 def test_document_mask_and_outside_checkerboard(self):
  for fragment in ['uniform vec2 uDocument','uniform vec2 uPan','uniform float uAngle','min(edge.x,edge.y)<0.','mix(.92,.975,shade)','pctx.strokeRect(0,0,baseW,baseH)']:
   self.assertIn(fragment,s)
 def test_minimized_palette_and_tip_resize(self):
  for fragment in ['id="compactPalette"','syncCompactPalette();','function updateTipLayout()','queueTipLayout();',"tipObserver.observe($('tipPanel'))"]:
   self.assertIn(fragment,s)
 def test_password_inputs_belong_to_forms(self):
  for fragment in ['<form id="cloudAuth"','<form id="providerSettings"']:
   self.assertIn(fragment,s)
if __name__=='__main__':unittest.main()
