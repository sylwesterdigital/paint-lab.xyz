"""v0.1.77 release contract: optional stroke history, lossless raster snapshots."""
import json
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
HTML = (APP / 'frontend/index.html').read_text()


class FastLayeredGallery(unittest.TestCase):
    def test_public_link_and_saved_history_choice(self):
        self.assertIn('href="/explore">Public gallery</a>', HTML)
        self.assertIn('type="checkbox" id="saveStrokeHistory"', HTML)
        self.assertIn('let flatHistoryBase=null,preserveSavedStrokeHistory=false;', HTML)
        self.assertIn("$('saveStrokeHistory').checked=preserveSavedStrokeHistory", HTML)
        self.assertIn("const keepStrokeHistory=$('saveStrokeHistory').checked", HTML)
        self.assertIn('if(!keepStrokeHistory){data.actions=[];data.head=0;}', HTML)
        self.assertIn('keepStrokeHistory,rasterLayers,baseRasterLayers', HTML)

    def test_raster_snapshots_and_baseline_survive_changes(self):
        self.assertIn('const rasterLayers=await captureLayerSnapshot(revision)', HTML)
        self.assertIn('const baseRasterLayers=keepStrokeHistory?await captureBaselineSnapshot(revision):null', HTML)
        self.assertIn('const snapshot=await decodeSavedLayers(item.rasterLayers', HTML)
        self.assertIn('if(!restoreFlatBase()){layers=[createLayer(', HTML)
        self.assertIn('}else if(!restoreFlatBase()){layers=[createLayer(', HTML)
        self.assertIn('if(item.keepStrokeHistory===false)flatHistoryBase=cloneLayersAsBaseline()', HTML)
        self.assertIn('if(item.keepStrokeHistory===false)throw Error(', HTML)
        self.assertIn('if(doc.flatBaseline?.length)await decodeEmbeddedBaseline(doc.flatBaseline)', HTML)
        self.assertIn('const doc=exportEmbeddedBaseline(projectData())', HTML)
        self.assertIn('const record={id:\'active\',savedAt:Date.now(),artId,data,rasterLayers,baseRasterLayers}', HTML)

    def test_version_and_notes_match(self):
        version = json.loads((APP / 'version.json').read_text())['version']
        self.assertEqual(version, '0.1.78')
        self.assertIn('content="0.1.78"', HTML)
        canonical = json.loads((APP / 'changelog.json').read_text())
        self.assertEqual(canonical, json.loads((APP / 'frontend/changelog.json').read_text()))
        self.assertEqual(canonical['history'][0]['version'], '0.1.77')
        self.assertIn('Keep brush stroke history', ' '.join(canonical['history'][8]['changes']))


if __name__ == '__main__':
    unittest.main()
