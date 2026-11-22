"""Compact single-row mobile control and badge-free mode reset contracts."""
import unittest
from pathlib import Path

PAGE=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()

class CompactMobileDockV153(unittest.TestCase):
    def test_fx_style_have_no_floating_clear_badges(self):
        self.assertNotIn('id="mobileEffectsNone"',PAGE)
        self.assertNotIn('id="mobileStylizeNone"',PAGE)
        self.assertNotIn('.mobile-mode-clear{',PAGE)
        self.assertIn("initMobileModePress('mobileEffects',mobileCycleEffects,()=>setMode(0))",PAGE)
        self.assertIn("initMobileModePress('mobileStylize',mobileCycleStylize,()=>{selectStrokeStyle('none')",PAGE)
        self.assertIn('timer=setTimeout(()=>{timer=null;held=true;reset();},520)',PAGE)
    def test_reset_and_cycle_remain_accessible_in_same_button(self):
        self.assertIn('const MOBILE_EFFECT_MODES=[0,',PAGE)
        self.assertIn('function mobileCycleStylize()',PAGE)
        self.assertIn("const choices=STROKE_STYLES.map(([key])=>key)",PAGE)
        self.assertIn("button.addEventListener('click',e=>{if(held){e.preventDefault();held=false;return;}cycle();});",PAGE)
        self.assertIn("$('mobileEffects').classList.toggle('active',activeEffect)",PAGE)
        self.assertIn("$('mobileStylize').classList.toggle('active',strokeStyle!=='none')",PAGE)
    def test_compact_square_dock_no_duplicate_tip_control(self):
        self.assertIn('--dock-size:clamp(',PAGE)
        self.assertIn('height:var(--dock-size)!important',PAGE)
        self.assertIn('width:max-content!important',PAGE)
        self.assertNotIn('id="mobileBrushNext"',PAGE)
        self.assertIn('id="mobileTipCycle"',PAGE)
        self.assertIn('id="mobileSizeSlider"',PAGE)

if __name__=='__main__':unittest.main()
