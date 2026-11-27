"""v0.1.81: gradient tiles are safe selection targets; deletion is a separate action."""
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text(encoding='utf-8')

class GradientPresetSelectionContract(unittest.TestCase):
 def test_only_one_delete_button_not_inside_tile(self):
  self.assertIn('id="deleteGradientPreset"',SOURCE)
  self.assertIn('disabled>Delete</button>',SOURCE)
  self.assertIn('function deleteSelectedGradientPreset()',SOURCE)
  self.assertIn("$('deleteGradientPreset').onclick=deleteSelectedGradientPreset",SOURCE)
  self.assertNotIn('palette-gradient-delete',SOURCE)
  self.assertNotIn('tile.append(use,remove)',SOURCE)
  self.assertIn('tile.append(use);root.append(tile);',SOURCE)
 def test_selected_border_is_same_as_deletion_target(self):
  self.assertIn('let customGradientPresets=[],selectedGradientPresetId=null;',SOURCE)
  self.assertIn("use.setAttribute('aria-pressed',String(selectedGradientPresetId===preset.id))",SOURCE)
  self.assertIn("const selected=customGradientPresets.find(p=>p.id===selectedGradientPresetId)",SOURCE)
  self.assertIn('if(!selected)return;',SOURCE)
  self.assertIn("confirmAction('Delete this saved gradient?','Delete gradient','Delete')",SOURCE)
  self.assertIn('selectedGradientPresetId=null;',SOURCE)
  self.assertIn('remove.disabled=!selected;',SOURCE)
 def test_browser_compatibility_and_edit_safety(self):
  self.assertIn("const GRADIENT_PRESETS_KEY='paint-lab-gradient-presets-v1'",SOURCE)
  self.assertIn('selectedGradientPresetId=preset.id;',SOURCE)
  self.assertIn('if(selectedGradientPresetId!==null){selectedGradientPresetId=null;renderGradientPresets();}',SOURCE)
  self.assertIn("preview.style.background='linear-gradient(90deg,'",SOURCE)

if __name__=='__main__':unittest.main()
