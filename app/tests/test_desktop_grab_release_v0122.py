"""Desktop transforms: pointer anchor and click-to-confirm must not regress."""
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()

class DesktopGrabRelease0122(unittest.TestCase):
    def test_keyboard_modal_transform_initializes_from_actual_mouse(self):
        start=SOURCE.index('function beginDesktopTransform(mode,duplicate=false)')
        end=SOURCE.index('function moveDesktopTransform(e)', start)
        body=SOURCE[start:end]
        self.assertIn('desktopTransformMouse',body)
        self.assertIn("const pivot=mode==='move'&&start?{x:start.x,y:start.y}:target.pivot;",body)
        self.assertIn('spec:neutralTransform(pivot)',body)
        self.assertIn('start,',body)

    def test_pointer_follows_without_viewport_recomposition(self):
        body=SOURCE[SOURCE.index('function moveDesktopTransform(e)'):SOURCE.index('function confirmDesktopTransform()')]
        self.assertIn('active.start=point',body)
        self.assertIn('transformAtPointer(active.mode,active.start,point,active.pivot)',body)
        self.assertIn('requestFrame()',body)
        self.assertNotIn('markPaint()',body)

    def test_click_confirmation_is_intercepted_before_regular_canvas_click(self):
        body=SOURCE[SOURCE.index('function desktopTransformClick(e)'):SOURCE.index('function activeTransformFromPointer(e)')]
        self.assertIn("window.addEventListener('pointerdown',desktopTransformClick,true)",body)
        self.assertIn('e.stopImmediatePropagation()',body)
        self.assertIn('if(e.button===0)confirmDesktopTransform();else cancelDesktopTransform()',body)
        self.assertIn("window.addEventListener('mousedown',e=>",body)

if __name__=='__main__':unittest.main()
