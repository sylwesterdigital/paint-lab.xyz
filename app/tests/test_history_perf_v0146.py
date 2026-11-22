"""Undo/Redo cache and non-blocking historical replay regression contracts."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()

class HistoryPerformanceV146(unittest.TestCase):
    def test_release_and_project_compatibility(self):
        version=json.loads((ROOT/'version.json').read_text())['version']
        self.assertEqual(version,'0.1.57')
        self.assertIn('content="0.1.57"',HTML)
        self.assertIn("format:'paint-lab-webgl'",HTML)

    def test_undo_uses_bounded_checkpoints(self):
        self.assertIn('HISTORY_CACHE_LIMIT=6,HISTORY_CACHE_BYTES=80*1024*1024',HTML)
        self.assertIn('function rememberHistoryCheckpoint()',HTML)
        self.assertIn('function restoreHistoryCheckpoint(s)',HTML)
        self.assertIn('function historyCheckpointValid(s,target)',HTML)
        self.assertIn('clearHistoryCheckpoints();}',HTML)

    def test_older_history_yields_between_actions(self):
        self.assertIn('function rebuildHistoryWithoutBlocking({opening=false,onProgress=null,onComplete=null}={})',HTML)
        self.assertIn('const start=performance.now(),budget=isMobileWorkspace()?5:9;',HTML)
        self.assertIn('requestAnimationFrame(replaySlice);',HTML)
        self.assertIn('const epoch=++historyReplayEpoch,target=head;',HTML)
        self.assertIn('if(epoch!==historyReplayEpoch)return;',HTML)
        self.assertIn('head--;historyPage=null;selectionId=null;rebuildHistoryWithoutBlocking();',HTML)

    def test_cache_invalidation_is_non_destructive_and_layer_aware(self):
        self.assertIn('layerItem.filterDirty=true;',HTML)
        mark=HTML.split('function invalidateLayerFilterCache(layerItem){',1)[1].split('\n}',1)[0]
        self.assertNotIn('filterCache.width=',mark)
        self.assertIn('layers.find(l=>l.ctx===paint)||activeLayer()',HTML)

    def test_autosave_waits_for_complete_reconstruction(self):
        self.assertIn('if(rendering){scheduleDraft();return Promise.resolve(false);}',HTML)
        self.assertIn('if(restoringDraft||rendering)return;',HTML)

if __name__=='__main__':unittest.main()
