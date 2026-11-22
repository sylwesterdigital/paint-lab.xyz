"""Release v0.1.29: mobile gesture cancellation, oil endpoint and chosen-tool markers.

These contracts run on Ubuntu with no browser; local Chromium interaction tests
exercise actual multi-touch state and canvas painting paths.
"""
import json
import re
import unittest
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
SRC=(APP/'frontend/index.html').read_text()


class MobileTouchAndOilEnds(unittest.TestCase):
    def test_release_number_and_changelog(self):
        self.assertEqual(json.loads((APP/'changelog.json').read_text())['version'],'0.1.38')
        self.assertIn('<title>Paint Lab v0.1.38</title>',SRC)

    def test_two_live_fingers_required(self):
        self.assertIn('if(touchPointers.size<2||gesture||gestureBlockedUntilAllUp)return;',SRC)
        self.assertIn('gestureBlockedUntilAllUp=true',SRC)
        self.assertIn('if(touchPointers.size===0){gestureBlockedUntilAllUp=false',SRC)
        self.assertIn('if(gesture.pair.every(pid=>touchPointers.has(pid)))gestureMove()',SRC)
        self.assertIn('touchPointers.delete(id)',SRC)
        self.assertIn("lostpointercapture",SRC)
        self.assertIn("visibilitychange",SRC)
        self.assertIn("touchend","touchend" if "touchend" in SRC else "")
        self.assertIn("e.touches.length===0",SRC)
        self.assertIn('window.addEventListener(\'pagehide\'',SRC)
        self.assertIn('if(!safariGesture||touchPointers.size<2||gesture)return;',SRC)

    def test_provisional_touch_and_fast_cancellation(self):
        self.assertIn('TOUCH_STROKE_GRACE_MS=105',SRC)
        self.assertIn('function flushPendingTouch(',SRC)
        self.assertIn('function cancelPendingTouch()',SRC)
        self.assertIn('function captureTouchStrokeTiles(',SRC)
        self.assertIn('function restoreUncommittedTouchStroke(',SRC)
        self.assertIn('else if(!restoreUncommittedTouchStroke(action))rebuild()',SRC)
        self.assertIn('delete a.touchRollback',SRC)

    def test_pigment_and_tip_exit_transform(self):
        self.assertIn('if(transformMode)setTransformMode(null);',SRC[SRC.index('function chooseMaterial(next){'):SRC.index('function initMaterialQuick(){')])
        self.assertIn('function setTip(s){if(!TIPS.some(x=>x[0]===s)&&!customTips.has(s))return;if(transformMode)setTransformMode(null);',SRC)

    def test_oil_endpoints_and_replay(self):
        self.assertIn('function finishOilStroke(',SRC)
        self.assertIn('function finishStrokeRender(',SRC)
        self.assertIn('oilFirstAngle',SRC)
        self.assertIn('const rawAngle=travel>.03?',SRC)
        self.assertIn('finishStrokeRender(s);if(hasStrokeImageFX(s))commitStrokeImageFX(s);s._run=null;',SRC)
        self.assertIn("if(e.type!=='pointercancel'){finishStrokeRender(a);if(hasStrokeImageFX(a))commitStrokeImageFX(a);}",SRC)
        self.assertIn('Wait for a real tangent;',SRC)

    def test_selection_visibility(self):
        self.assertIn('#tipGrid .tip-btn.active::after',SRC)
        self.assertIn('#swatches .swatch.active::after',SRC)
        self.assertIn('#currentColor.is-active',SRC)
        self.assertIn("b.setAttribute('aria-pressed',String(tip===key))",SRC)

if __name__=='__main__':unittest.main()
