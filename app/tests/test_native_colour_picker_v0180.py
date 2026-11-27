"""The native picker must remain attached during every live gradient input tick."""
import unittest
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()

class NativeColourPicker180(unittest.TestCase):
 def test_live_gradient_keeps_colour_input_mounted(self):
  self.assertIn("if(picker.parentElement!==sw)sw.prepend(picker);",HTML)
  self.assertNotIn("sw.replaceChildren();sw.append(picker);",HTML)
  self.assertIn("const existing=Array.from(sw.querySelectorAll(':scope > button.swatch'));",HTML)
  self.assertIn("const clickedIndex=Number(b.dataset.index),clickedColor=palette[clickedIndex];",HTML)
  self.assertIn("if($('colorPicker').value!==firstSwatch)$('colorPicker').value=firstSwatch;",HTML)
 def test_mobile_palette_reuses_buttons_during_picker_drag(self):
  self.assertIn("for(const button of buttons.slice(palette.length))button.remove();",HTML)
  self.assertIn("const n=Number(button.dataset.index)",HTML)
  self.assertNotIn("function renderMobilePalette(){const grid=$('mobilePaletteGrid');if(!grid)return;grid.replaceChildren();",HTML)
 def test_browser_qa_shipped(self):
  self.assertTrue((APP/'tools/browser_native_colour_picker_v0180.py').is_file())

if __name__=='__main__':unittest.main()
