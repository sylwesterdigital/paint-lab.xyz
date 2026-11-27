"""Release v0.1.77: guide images, non-destructive transforms, palette editing and link UI."""
import json
import re
import subprocess
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
HTML = (APP / 'frontend/index.html').read_text()

class ReferencePaletteContract(unittest.TestCase):
    def test_reference_is_pinned_and_excluded_from_png(self):
        self.assertIn('id="addReferenceImage"', HTML)
        self.assertNotIn('id="referenceSlot"', HTML)
        self.assertIn('addReferenceRow(root);const add=', HTML)
        self.assertIn('drawReferenceGuide(layerCtx)', HTML)
        export = HTML.split('function createExportCanvas(withBg){', 1)[1].split('function exportPNG()', 1)[0]
        self.assertNotIn('drawReferenceGuide', export)
        self.assertIn('reference:referenceRecord?{...referenceRecord}:null', HTML)
        self.assertIn('loadReferenceFromData(data.reference)', HTML)
        self.assertIn("ctx.drawImage(img,-r.width/2,-r.height/2,r.width,r.height)", HTML)
        self.assertIn('loadReferenceFromData(null);artId=null', HTML)

    def test_palette_flow_and_swatch_edit(self):
        for marker in ('id="palettePingPong"', 'id="editPaletteSwatch"',
                       'function paletteBounceIndex(step,count)',
                       'colorTravelPingPong,travelPalette:',
                       'function editSelectedPaletteSwatch(hex)',
                       'colorTravel,colorTravelPingPong,color,reference:'):
            self.assertIn(marker, HTML)

    def test_open_link_behaves_as_button_but_opens_new_tab(self):
        self.assertRegex(HTML, r'<a class="btn save-open-link" id="saveOpenLink" href="#" target="_blank" rel="noopener noreferrer"')
        self.assertIn('#saveOpenLink.save-open-link{display:inline-flex', HTML)
        self.assertIn('text-decoration:none!important', HTML)

    def test_devlog_and_version(self):
        data = json.loads((APP / 'changelog.json').read_text())
        self.assertEqual(data['version'], '0.1.79')
        self.assertEqual(data, json.loads((APP / 'frontend/changelog.json').read_text()))
        self.assertEqual(data['history'][0]['version'], '0.1.78')

    def test_triangle_wave(self):
        match = re.search(r'function paletteBounceIndex\(step,count\)\{.*?\n\}', HTML, re.S)
        self.assertIsNotNone(match)
        code = 'const values=Array.from({length:10},(_,i)=>paletteBounceIndex(i,4));if(JSON.stringify(values)!==JSON.stringify([0,1,2,3,2,1,0,1,2,3]))throw Error(JSON.stringify(values));'
        result = subprocess.run(['node', '-e', match.group() + '\n' + code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == '__main__':
    unittest.main()
