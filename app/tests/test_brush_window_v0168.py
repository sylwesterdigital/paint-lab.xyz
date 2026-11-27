"""v0.1.77: brush previews remain usable and minimized desktop panels may reach top edge."""
import json
import re
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
HTML = (APP / 'frontend/index.html').read_text()

class BrushWindow168(unittest.TestCase):
    def test_brush_tip_gallery_has_room_and_controls_are_closed(self):
        self.assertIn('height:clamp(205px,36dvh,330px)!important', HTML)
        self.assertIn('overflow-y:auto!important;overflow-x:hidden!important', HTML)
        self.assertIn('<details class="brush-edit" id="brushEditor">', HTML)
        self.assertIn('<details class="tip-extra" id="textBrushAdvanced">', HTML)
        self.assertIn('const tileHeight=clamp(Math.round(perCell*.86),72,94)', HTML)
        self.assertLess(HTML.index("if(currentTipCategory==='All'||!showRecipes)for", HTML.index('function renderTipLibrary(){')),HTML.index('if(showRecipes)for(const recipe of recipes)', HTML.index('function renderTipLibrary(){')))
        for item in ('id="tipGrid"','id="brushEdit_size"','id="brushExport"','id="textBrushInput"'):
            self.assertIn(item,HTML)

    def test_collapsed_panels_get_top_edge_dragging(self):
        self.assertIn("function panelTopFloor(panel){return panel?.classList.contains('collapsed')?6:desktopHeaderFloor();}",HTML)
        self.assertIn('headerFloor=panelTopFloor(panel)',HTML)
        self.assertIn('clamp(e.clientY-drag.dy,panelTopFloor(panel)',HTML)
        self.assertIn('fitPanelVisible(panel);if(panel.id=',HTML)

    def test_plain_links_and_current_history(self):
        self.assertIn('color:#000;text-decoration:none',HTML)
        self.assertIn('cursor:pointer;text-shadow:none',HTML)
        self.assertIn('paint-lab-wordmark',HTML)
        log=json.loads((APP/'changelog.json').read_text())
        self.assertEqual(log['version'],'0.1.79')
        self.assertEqual(log['history'][0]['version'],'0.1.78')

if __name__=='__main__':unittest.main()
