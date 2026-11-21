"""Regression contracts for functional paint retouch and accessibility."""
import unittest
from pathlib import Path
S=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
class RetouchContracts(unittest.TestCase):
 def test_effects_are_pixel_based(self):
  a=S.index('function effectStamp(');b=S.index('function paintTextStamp(',a);piece=S[a:b]
  for key in ('target.canvas','target.blend','retouchCarry','destination-in','mode===2','mode===3','mode===4','blur(','sctx.drawImage','destination-out'):
   self.assertIn(key,piece)
  self.assertNotIn('baseCol',piece)
 def test_paint_tab_resets_retouch(self):
  self.assertIn("switchBrushTab(b.dataset.brushtab,true)",S)
  self.assertIn("activateTool&&name==='paint'&&brushTabForMode(mode)==='effects'",S)
  self.assertIn("if(mode!==0)setMode(0)",S)
  self.assertIn("b.setAttribute('aria-pressed',String(selected))",S)
 def test_no_retoucher_dab_on_down(self):
  self.assertIn("if([2,3,4].includes(s.cfg.mode))return",S)
  self.assertIn("if([2,3,4].includes(s.cfg.mode)){",S)
 def test_readback_hint_and_settings_accessibility(self):
  self.assertIn("result.getContext('2d',{willReadFrequently:true})",S)
  self.assertIn("el.contains(document.activeElement)",S)
  self.assertIn("el.setAttribute('inert','')",S)
  self.assertIn("$('settingsShade').removeAttribute('inert')",S)
if __name__=='__main__':unittest.main()
