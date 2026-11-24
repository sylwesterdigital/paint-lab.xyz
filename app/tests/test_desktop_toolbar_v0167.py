"""v0.1.69 desktop toolbar, wordmark placement and zoom-HUD contracts."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONT = (ROOT / 'frontend/index.html').read_text(encoding='utf-8')


class DesktopToolbar167(unittest.TestCase):
    def test_release_markers_and_history(self):
        for file in ('version.json', 'frontend/version.json', 'changelog.json', 'frontend/changelog.json'):
            self.assertEqual(json.loads((ROOT / file).read_text())['version'], '0.1.69')
        self.assertIn('<meta name="paint-lab-version" content="0.1.69">', FRONT)
        changelog = json.loads((ROOT / 'changelog.json').read_text())
        self.assertEqual(changelog['history'][0]['version'], '0.1.68')

    def test_brand_is_unboxed_and_header_reserves_panel_space(self):
        self.assertIn('id="paintLabBrand"', FRONT)
        self.assertIn('font-size:28px;font-weight:850', FRONT)
        self.assertIn('z-index:9;top:10px;left:10px', FRONT)
        self.assertIn('.paint-lab-brand-link{border:0;background:transparent', FRONT)
        self.assertIn('.paint-lab-brand-link{border:0;background:transparent', FRONT)
        self.assertIn('color:#000;text-decoration:none', FRONT)
        self.assertIn('text-shadow:none', FRONT)
        self.assertIn('function desktopHeaderFloor()', FRONT)
        self.assertIn('headerFloor=panelTopFloor(panel)', FRONT)
        self.assertIn('clamp(e.clientY-drag.dy,panelTopFloor(panel)', FRONT)

    def test_desktop_toolbar_preserves_single_original_button_per_action(self):
        self.assertIn('id="desktopMore"', FRONT)
        self.assertIn('id="desktopOverflowMenu"', FRONT)
        self.assertIn('id="desktopQuickActions"', FRONT)
        self.assertIn('id="settingsTop"', FRONT)
        self.assertIn("const DEFAULT_DESKTOP_QUICK=['trashTop','saveTop','undoTop','redoTop']", FRONT)
        self.assertIn('(desktopQuickActions.includes(id)?quick:menu).append(b)', FRONT)
        self.assertIn('function initDesktopToolbar()', FRONT)
        self.assertIn('initDesktopToolbar();', FRONT)
        self.assertIn('id="desktopToolbarChoices"', FRONT)
        self.assertIn('class="desktop-toolbar-settings"', FRONT)
        for action in ('trashTop', 'saveTop', 'undoTop', 'redoTop', 'themeTop', 'galleryTop'):
            self.assertEqual(len(re.findall(rf'id="{action}"', FRONT)), 1, action)

    def test_toolbar_setting_is_validated_and_persisted_with_presets(self):
        self.assertIn('function sanitizeDesktopQuick(value)', FRONT)
        self.assertIn('desktopQuickActions:[...desktopQuickActions]', FRONT)
        self.assertIn('if(Array.isArray(data.desktopQuickActions))', FRONT)
        self.assertIn('syncDesktopToolbar();schedulePersist();', FRONT)
        self.assertIn("root.replaceChildren();for(const [id,label] of DESKTOP_ACTIONS)", FRONT)

    def test_live_zoom_and_fit_reside_inside_canvas_hud(self):
        hud = FRONT.split('<div class="canvas-hud"', 1)[-1].split('<div class="paint-lab-brand"', 1)[0]
        self.assertIn('id="zoomValue"', hud)
        self.assertIn('id="resetView"', hud)
        self.assertEqual(len(re.findall(r'id="zoomValue"', FRONT)), 1)
        self.assertEqual(len(re.findall(r'id="resetView"', FRONT)), 1)
        self.assertIn("$('resetView').onclick=resetCanvasView", FRONT)
        self.assertIn("function updateZoomUI(){const zoom=Math.round(view.zoom*100)+'%',chip=$('zoomValue')", FRONT)
        self.assertNotIn("$('hudZoom').textContent", FRONT)

    def test_shortcut_square_close_buttons_and_preserved_stripe(self):
        self.assertIn("e.shiftKey&&key==='s'&&!e.repeat", FRONT)
        self.assertIn('openSave(false);return;', FRONT)
        self.assertIn("if(['g','r','s'].includes(key)&&!e.shiftKey)", FRONT)
        self.assertIn('button:has(> .svg-icon use[href="#pl-close"])', FRONT)
        self.assertIn('aspect-ratio:1!important', FRONT)
        self.assertIn('place-items:center!important', FRONT)
        self.assertIn('buy_btn_1UemYTC7wxoTGQU3bmUqn2Yl', FRONT)
        self.assertIn('https://donate.stripe.com/4gM6oGbw61Wf5nJa1wcZa0c', FRONT)


if __name__ == '__main__':
    unittest.main()
