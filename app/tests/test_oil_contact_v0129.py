"""Oil stroke continuity and entry/release contact model regression contracts.
Browser pixel behaviour is checked separately through tools/browser_oil_contact_smoke.py.
"""
from pathlib import Path
import json, unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'frontend/index.html').read_text()

class OilContactV29(unittest.TestCase):
    def test_release_version(self):
        self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.60')
        self.assertIn('<title>Paint Lab v0.1.60</title>',SOURCE)
    def test_entry_and_exit_contact_profiles(self):
        for marker in ('function oilEntryBehaviour(', 'function oilEntryMetrics(',
                       'function oilReleaseMetrics(', 'function oilEnvelopeSegments(',
                       'function sculptOilEnvelope(', "sculptOilEnvelope(s,'start')",
                       "sculptOilEnvelope(s,'end')", 'startPressure','endPressure',
                       'acceleration', 'slowing', 'antialias=Math.max(',
                       'originalOilPigment(run,tileX+px,tileY+py)'):
            self.assertIn(marker,SOURCE)
    def test_contact_is_narrow_at_both_ends(self):
        body=SOURCE[SOURCE.index('function sculptOilEnvelope('):SOURCE.index('function finishOilStroke(')]
        self.assertIn('const phase=smoothing(clamp(dist/Math.max(1,length),0,1))',body)
        self.assertIn('const radiusFraction=profile.tipWidth+(1-profile.tipWidth)*Math.pow(phase,profile.curve)',body)
        self.assertNotIn('Math.pow(1-phase,profile.curve)',body)
        self.assertIn('const excess=radial-allowed',body)
        self.assertNotIn('paint.arc(',body)
    def test_short_stroke_envelopes_do_not_overlap(self):
        body=SOURCE[SOURCE.index('function oilReleaseMetrics('):SOURCE.index('function oilEnvelopeHalfWidth(')]
        self.assertEqual(body.count('Math.min(total*.47,'),2)
    def test_adaptive_v2_live_contact_path(self):
        for marker in ("oilSamplingEngine:'adaptive-v2'",
                       "run.oilEntryLive",
                       "const turnSegments=Math.ceil(turnDelta/(Math.PI/18));",
                       "const tangentRadius=engine==='adaptive-v2'?",
                       "const distSq=engine==='adaptive-v2'?",
                       "}else if((s.cfg.oilSamplingEngine||'adaptive-v1')!=='adaptive-v2')finishOilStroke(s);"):
            self.assertIn(marker,SOURCE)

    def test_watcher_compiles_in_one_invocation(self):
        # Ubuntu installs app/ by itself: the source watcher need not be
        # present beside the deployed application's test directory.
        watcher_path=ROOT.parent/'watch-paint-lab.sh'
        if watcher_path.is_file():
            watcher=watcher_path.read_text()
            self.assertIn("VERSION='0.1.6'",watcher)
            self.assertIn("'-m','compileall','-q'",watcher)
        else:
            self.assertTrue((ROOT/'version.json').is_file())
    def test_reference_architecture_distinguished_from_actual_implementation(self):
        research=(ROOT/'docs/PAINT_SIMULATION_RESEARCH.md').read_text()
        for term in ('GPU', 'height', 'pickup', 'reservoir', 'raster oil approximation'):
            self.assertIn(term,research)
if __name__=='__main__':unittest.main()
