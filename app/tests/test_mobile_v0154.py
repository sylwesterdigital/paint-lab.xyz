"""v0.1.55 mobile control and pre-stroke fast-history regression contracts."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()

class Mobile154(unittest.TestCase):
    def test_version_and_devlog(self):
        self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.58')
        self.assertEqual(json.loads((ROOT/'frontend/changelog.json').read_text())['version'],'0.1.58')

    def test_tip_tap_accessibility_and_gallery(self):
        self.assertNotIn('id="mobileTipCycle"',HTML)
        self.assertIn('id="mobileBrushLauncherImage"',HTML)
        self.assertIn('function handleMobileBrushTap()',HTML)
        self.assertIn('function mobileNextTip()',HTML)
        self.assertIn('function openMobileTipGallery()',HTML)
        self.assertIn('id="mobileSizeSlider"',HTML)

    def test_colour_and_history_are_pinned_to_opposite_edges(self):
        self.assertIn('right:calc(8px + env(safe-area-inset-right,0px))!important;',HTML)
        self.assertIn('justify-content:flex-start!important;',HTML)
        self.assertIn('margin-left:auto!important;position:static!important;flex:none;',HTML)
        self.assertIn('id="mobileUndo"',HTML)
        self.assertIn('id="mobileRedo"',HTML)

    def test_pigment_name_and_central_feedback(self):
        self.assertIn("setMobileModeTile('mobileMaterial',materialNames[material]||'Oil'",HTML)
        self.assertIn('id="mobileChoiceNotice"',HTML)
        self.assertIn('function announceMobileChoice(kind,value)',HTML)
        self.assertIn("announceMobileChoice('Effect',next===0?'None':MODE_NAMES[next])",HTML)
        self.assertIn("announceMobileChoice('Stylize'",HTML)
        self.assertIn("mobileChoiceNoticeTimer=setTimeout(()=>notice.classList.remove('visible'),850)",HTML)
        self.assertNotIn('id="mobileEffectsNone"',HTML)
        self.assertNotIn('id="mobileStylizeNone"',HTML)

    def test_mobile_undo_pre_stroke_snapshot_and_less_replay_ui(self):
        self.assertIn('if(isMobileWorkspace()&&!historyCheckpoints.some(s=>s.head===head&&historyCheckpointValid(s,head)))rememberHistoryCheckpoint();',HTML)
        self.assertIn('timeout:isMobileWorkspace()?180:700',HTML)
        self.assertIn('const start=performance.now(),budget=isMobileWorkspace()?5:9;',HTML)
        self.assertIn("if(!isMobileWorkspace()||mobileSheetId==='layersPanel')renderLayers();",HTML)

if __name__=='__main__': unittest.main()
