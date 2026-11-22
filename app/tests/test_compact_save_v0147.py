"""Compact direct-action Save & Share interface contracts for v0.1.47."""
import re,unittest
from pathlib import Path
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
SAVE=HTML.split('<div class="overlay" id="saveOverlay"')[1].split('<div class="overlay" id="exportOverlay"')[0]
class CompactSaveTests(unittest.TestCase):
 def test_direct_actions_one_row(self):
  self.assertIn('class="save-hub-actions"',SAVE)
  for x in ['saveNew','saveOverwrite','savePublish','saveNativeShare']:
   self.assertIn('id="'+x+'"',SAVE)
  self.assertIn('grid-template-columns:repeat(4,minmax(0,1fr))',HTML)
 def test_four_direct_exports(self):
  self.assertIn('class="save-hub-exports"',SAVE)
  for x in ['savePNGWith','savePNGWithout','saveZIP','saveJSON']:
   self.assertIn('id="'+x+'"',SAVE)
 def test_no_loud_sections_or_extra_footer(self):
  for old in ['save-hub-section-head','save-hub-section','save-hub-footer','>Done</button>','saveOverwriteHint','savePublishHelp']:
   self.assertNotIn(old,SAVE)
  self.assertNotIn('class="dialogFooter"',SAVE)
  self.assertIn('data-close="saveOverlay"',SAVE)
 def test_hidden_idle_status_and_existing_publish_link(self):
  self.assertIn('id="saveStatus" role="status" aria-live="polite"></div>',SAVE)
  self.assertIn('id="savePublicLinkWrap" hidden',SAVE)
  self.assertIn('id="savePublishBackground"',SAVE)
  self.assertIn('id="saveSignIn"',SAVE)
if __name__=='__main__':unittest.main()
