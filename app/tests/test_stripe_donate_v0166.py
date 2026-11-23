"""v0.1.66: public and studio donations share Stripe's public Payment Link."""
import json,unittest
from pathlib import Path
from backend import public_viewer

ROOT=Path(__file__).resolve().parents[1]
FRONT=(ROOT/'frontend/index.html').read_text()
LOADER=(ROOT/'frontend/assets/stripe_donate.js').read_text()
APP=(ROOT/'backend/app.py').read_text()
URL='https://donate.stripe.com/4gM6oGbw61Wf5nJa1wcZa0c'
KEY='pk_live_51OS1fPC7wxoTGQU3jLPCJmKrEOZ03kLdBpCyRKcE1DRj9xKHNdIWNbAAwMFLsi0s9cyUGw9BdYQzYDmFbsNacsrx00KDuQKgna'
BUTTON='buy_btn_1UemYTC7wxoTGQU3bmUqn2Yl'

class StripeDonationAndIdentity166(unittest.TestCase):
 def test_identity_has_no_container_decoration_and_version_is_synchronised(self):
  self.assertIn('class="paint-lab-brand"',FRONT)
  self.assertIn('class="paint-lab-wordmark"',FRONT)
  self.assertIn('background:linear-gradient(100deg',FRONT)
  self.assertIn('color:transparent;-webkit-text-fill-color:transparent',FRONT)
  self.assertIn('>Paint-lab</a>',FRONT)
  self.assertIn('v0.1.68</span>',FRONT)
  self.assertIn('href="https://github.com/sylwesterdigital/paint-lab.xyz"',FRONT)
  self.assertIn('data-stripe-dialog-trigger="paintLabDonateDialog"',FRONT)
  self.assertIn("classList.toggle('mobile-focused',mobileFocusMode)",FRONT)
  self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.68')

 def test_both_support_panels_use_the_supplied_public_stripe_widget(self):
  slide={'token':'a'*26,'title':'Art','url':'/p/'+'a'*26,'image':'/p/'+'a'*26+'/image.png'}
  viewer=public_viewer.viewer_markup([slide],0,'Artist','/u/Artist')
  for source in (FRONT,viewer):
   self.assertIn(URL,source)
   self.assertIn('buy-button-id="'+BUTTON+'"',source)
   self.assertIn('publishable-key="'+KEY+'"',source)
   self.assertIn('stripe-buy-button',source)
   self.assertIn('data-stripe-status',source)
  self.assertIn('Download original PNG',viewer)
  self.assertIn('download="paint-lab-artwork.png"',viewer)
  self.assertIn('data-stripe-dialog-trigger="supportDialog"',viewer)
  self.assertNotIn('data-support-amount',viewer)
  self.assertIn('not directly to the artist',viewer)

 def test_widget_is_lazy_and_payment_link_is_the_fallback(self):
  self.assertIn('https://js.stripe.com/v3/buy-button.js',LOADER)
  self.assertIn('trigger.addEventListener(\'click\'',LOADER)
  self.assertIn('loadStripe().then',LOADER)
  self.assertIn('script.onerror=',LOADER)
  self.assertIn('src="assets/stripe_donate.js"',FRONT)
  self.assertIn('src="/assets/stripe_donate.js"',APP)
  self.assertIn('if viewer:',APP)
  self.assertIn('frame-src https://js.stripe.com https://*.stripe.com',APP)
  self.assertIn("if viewer else \"\"",APP)

 def test_no_payment_secret_embedded_in_browser_files(self):
  for source in (FRONT,LOADER,public_viewer.VIEWER_JS):
   self.assertNotIn('sk_live_',source)
   self.assertNotIn('whsec_',source)
  self.assertIn("@app.post('/api/stripe/webhook')",APP)
  self.assertIn("@app.post('/api/support/checkout')",APP)

if __name__=='__main__':unittest.main()
