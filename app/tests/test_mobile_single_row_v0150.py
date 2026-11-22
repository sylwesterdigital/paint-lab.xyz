"""Contracts for a single-row mobile toolbar and non-obstructed Layers sheet."""
from pathlib import Path
import unittest

PAGE=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()


class MobileSingleRowV150(unittest.TestCase):
 def test_modes_history_and_paint_tools_share_one_dock(self):
  a=PAGE.index('<div class="mobile-bottom mobile-optional" id="mobileBottom"')
  palette=PAGE.index('id="mobilePalettePopover"',a)
  dock=PAGE[a:palette]
  for key in ('mobileBrush','mobileSwatch','mobileMaterial','mobileEffects','mobileStylize','mobileUndoRedo','mobileUndo','mobileRedo'):
   self.assertIn(f'id="{key}"',dock)
  self.assertIn('mobile-primary-stack',dock)
  self.assertIn('mobile-mode-shortcuts',dock)
  self.assertEqual(PAGE.count('id="mobileModeShortcuts"'),1)
  self.assertEqual(PAGE.count('id="mobileUndoRedo"'),1)
 def test_dock_has_no_above_row_or_wrap(self):
  self.assertIn('.mobile-workspace .mobile-primary-stack,.mobile-workspace .mobile-mode-shortcuts,.mobile-workspace .mobile-undo-redo{display:contents',PAGE)
  self.assertIn('flex-wrap:nowrap;align-items:center;gap:4px;overflow:visible',PAGE)
  self.assertIn('.mobile-workspace #mobileBrush,.mobile-workspace #mobileSwatch,.mobile-workspace #mobileMaterial',PAGE)
  self.assertIn('min-width:0!important',PAGE)
 def test_layer_panel_is_above_toolbar_and_has_correct_depth(self):
  self.assertIn('#layersPanel.mobile-sheet-active{bottom:calc(70px + env(safe-area-inset-bottom,0px))!important',PAGE)
  self.assertIn('.mobile-workspace.mobile-sheet-open .mobile-studio{z-index:80}',PAGE)
  self.assertIn('.mobile-workspace .mobile-sheet-shade.visible{z-index:83}',PAGE)
  self.assertIn('.mobile-workspace.mobile-sheet-open .surface{z-index:103}',PAGE)
  self.assertIn("document.documentElement.classList.toggle('mobile-sheet-open',!!mobileSheetId)",PAGE)
 def test_stylize_and_effects_remain_resettable(self):
  self.assertIn("$('mobileEffectsNone').onclick=()=>setMode(0)",PAGE)
  self.assertIn("$('mobileStylizeNone').onclick=()=>{selectStrokeStyle('none')",PAGE)
  self.assertIn("$('mobileEffects').textContent=activeEffect?'FX·'",PAGE)
  self.assertIn("$('mobileStylize').textContent=strokeStyle!=='none'?'ST·'",PAGE)

if __name__=='__main__':unittest.main()
