"""Release v0.1.77 contract: reference uses normal layer selector/transform pipeline."""
import json
import unittest
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
class ReferenceUnified173(unittest.TestCase):
 def test_reference_is_same_layer_list_and_no_separate_transform_panel(self):
  self.assertIn('addReferenceRow(root)',HTML)
  self.assertIn("row.className='layer-row reference-layer'",HTML)
  self.assertIn("root.append(row);",HTML)
  self.assertIn('referenceSelected=true;selectionId=null;',HTML)
  self.assertNotIn('id="referenceSlot"',HTML)
  self.assertNotIn('referenceMoveMode',HTML)
  self.assertNotIn('referenceDrag',HTML)
  self.assertNotIn('reference-adjustments',HTML)
  self.assertNotIn('Move on canvas',HTML)
 def test_native_resolution_transform_and_non_exporting(self):
  self.assertIn("targetKind:'reference'",HTML)
  self.assertIn('function selectTransformTarget(){',HTML)
  self.assertIn("if(tr.targetKind==='reference'&&referenceRecord)",HTML)
  self.assertIn("if(active.targetKind==='reference'){compositeDirty=true;textureDirty=true;}",HTML)
  self.assertIn('ctx.drawImage(img,-r.width/2,-r.height/2,r.width,r.height)',HTML)
  self.assertIn('reference:referenceRecord?{...referenceRecord}:null',HTML)
  self.assertIn('loadReferenceFromData(data.reference)',HTML)
  self.assertIn('if(mobileLayerOpacityId===\'reference\')referenceChanged();',HTML)
  self.assertNotIn('drawReferenceGuide',HTML.split('function createExportCanvas(withBg){',1)[1].split('function exportPNG()',1)[0])
 def test_release(self):
  log=json.loads((APP/'changelog.json').read_text())
  self.assertEqual(log['version'],'0.1.81')
  self.assertEqual(log['history'][0]['version'],'0.1.80')
  self.assertEqual(log,json.loads((APP/'frontend/changelog.json').read_text()))
if __name__=='__main__':unittest.main()
