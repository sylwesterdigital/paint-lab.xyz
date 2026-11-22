"""Regression: selected oil tip affects its real bristle contact pattern."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class OilTipShapeContract(unittest.TestCase):
    def test_physical_tip_contact(self):
        for marker in ('function oilContactProfile(t,density)','function oilContactAt(profile,u)',
                       'function oilHeadBristles(t,requested)','const tipProfile=oilContactProfile(c.tip,density)',
                       'const shape=oilContactAt(tipProfile.profile,u)','contact:shape>.035',
                       '(.62+.38*br.shape)',"if(['stippler','splat','grain','drycomb'].includes(c.tip)"):
            self.assertIn(marker,HTML)
        self.assertIn('const custom=customTips.get(t)',HTML)
    def test_restore_never_starts_sync_rebuild(self):
        self.assertIn('resize(false);if(!deferReplay)rebuild()',HTML)
        self.assertIn('if(!restoringDraft&&!rendering)requestFrame()',HTML)
        self.assertIn('j<a.points.length',HTML)
if __name__=='__main__':unittest.main()
