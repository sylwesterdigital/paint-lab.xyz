"""Static regression tests for independent, inline SVG controls and help shortcuts."""
from pathlib import Path
import re, unittest
import xml.etree.ElementTree as ET

HTML = Path(__file__).resolve().parents[1] / 'frontend' / 'index.html'

class SvgEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding='utf-8')

    def test_all_svg_use_refs_exist(self):
        ids = set(re.findall(r'<symbol id="(pl-[\w-]+)"', self.html))
        refs = re.findall(r'<use href="#(pl-[\w-]+)"', self.html)
        self.assertGreaterEqual(len(ids), 70)
        self.assertGreaterEqual(len(refs), 35)
        self.assertEqual(set(refs) - ids, set())
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn('<script', self.html.split('id="paintLabIconSprite"',1)[1].split('</svg>',1)[0])

    def test_desktop_help_accepts_unshifted_slash(self):
        code = self.html.split('<script>',1)[1]
        start = code.index('function handleKey(e)')
        condition = code[start:start+430]
        self.assertIn("e.code==='Slash'", condition)
        self.assertIn("e.key==='/'", condition)
        self.assertIn('e.preventDefault()', condition)
        self.assertNotIn('e.shiftKey&&', condition)
        self.assertIn("window.addEventListener('keydown',handleKey,true)", code)

    def test_critical_toolbar_buttons_have_inline_svg(self):
        for control in ('helpTop','undoTop','redoTop','galleryTop','saveTop','exportTop','settingsTop','cloudTop','resetView'):
            self.assertRegex(self.html, rf'<button[^>]*id="{control}"[^>]*>\s*<svg class="svg-icon"')

    def test_shape_selection_not_replaced_by_characters(self):
        self.assertIn('PL_SHAPE_ICONS[key]', self.html)
        self.assertIn("eye.innerHTML=plIcon(l.visible?'eye':'eye-hidden')",self.html)

if __name__=='__main__':unittest.main()
