"""Multi-layer select/merge regression contracts (run in full browser too)."""
from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'frontend/index.html').read_text()
class LayerV0117Contracts(unittest.TestCase):
 def test_multiselection_and_bulk_buttons(self):
  for token in ('selectedLayerIds=new Set()','event.metaKey||event.ctrlKey','event?.shiftKey',
                'layerSelectionAnchorId','id="mergeSelectedLayers"','id="mergeAllLayers"',
                'id="toggleSelectedLayers"','layer-clone-many','layer-remove-many','layer-props-many'):
   self.assertIn(token,SOURCE)
 def test_merging_and_history(self):
  for token in ("a.kind==='layer-merge'","for(const part of source){if(!part.visible)continue;",
                'ctx.globalAlpha=part.opacity','ctx.globalCompositeOperation=part.blend',
                'ctx.drawImage(getLayerRenderCanvas(part),0,0)',"layerAction({kind:'layer-merge'",'a.ids.length<2'):
   self.assertIn(token,SOURCE)
 def test_hidden_icon(self):
  self.assertIn('id="pl-eye-hidden"',SOURCE)
  self.assertIn("l.visible?'eye':'eye-hidden'",SOURCE)
 def test_version(self):
  self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.47')
  self.assertIn('content="0.1.47"',SOURCE)
