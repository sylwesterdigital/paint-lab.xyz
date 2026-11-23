#!/usr/bin/env python3
"""Offline Chromium smoke: live identifiers, lazy Stripe, editor and public modal.

Requires Playwright + locally installed Chromium; no live payment is made.
Mocks the Stripe script response, not the payment endpoint.
"""
from __future__ import annotations
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend import public_viewer

TOKEN='a'*26
MOCK_STRIPE="""customElements.define('stripe-buy-button',class extends HTMLElement{
 connectedCallback(){this.innerHTML='<button type="button" data-test-stripe-button>Stripe support (mock)</button>'}
});"""

def check_page(browser, mobile=False):
 context=browser.new_context(viewport={'width':375 if mobile else 1440,'height':812 if mobile else 900},is_mobile=mobile,has_touch=mobile)
 page=context.new_page();requested=[];errors=[]
 page.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None)
 def stripe_route(route):requested.append(route.request.url);route.fulfill(status=200,content_type='text/javascript',body=MOCK_STRIPE)
 page.route('https://js.stripe.com/v3/buy-button.js',stripe_route)
 page.route('https://analytics.mielniczuk.com/**',lambda route:route.abort())
 page.set_content((ROOT/'frontend/index.html').read_text().replace('<script defer src="assets/stripe_donate.js"></script>', '<script>'+(ROOT/'frontend/assets/stripe_donate.js').read_text()+'</script>'),wait_until='domcontentloaded')
 page.wait_for_selector('.paint-lab-wordmark')
 if mobile:
  page.wait_for_function("document.documentElement.classList.contains('mobile-workspace')")
 assert page.locator('.paint-lab-wordmark').inner_text()=='Paint-lab'
 assert page.locator('.paint-lab-version').inner_text()=='v0.1.67'
 assert page.locator('a.paint-lab-brand-link').get_attribute('href').endswith('/paint-lab.xyz')
 assert not requested, 'Stripe must be lazy on studio startup'
 page.locator('[data-stripe-dialog-trigger="paintLabDonateDialog"]').click()
 assert page.locator('#paintLabDonateDialog').evaluate('(el)=>el.open')
 page.locator('#paintLabDonateDialog [data-test-stripe-button]').wait_for(timeout=10000)
 assert len(requested)==1
 assert page.locator('#paintLabDonateDialog .stripe-donation-fallback').get_attribute('href')=='https://donate.stripe.com/4gM6oGbw61Wf5nJa1wcZa0c'
 page.locator('#paintLabDonateDialog [data-stripe-dialog-close]').click()
 assert not page.locator('#paintLabDonateDialog').evaluate('(el)=>el.open')
 if mobile:
  page.locator('#mobileFocus').click()
  assert not page.locator('.paint-lab-brand').is_visible(),'Mobile canvas focus must hide branding'
  page.locator('#mobileFocus').click()
  assert page.locator('.paint-lab-brand').is_visible()
 rect=page.locator('.paint-lab-brand').bounding_box()
 assert rect and rect['x']>=0 and rect['x']+rect['width']<= (375 if mobile else 1440)+2,rect
 print(('mobile' if mobile else 'desktop')+' studio: PASS (dialog, close, lazy widget, link, wordmark, placement)')
 if errors:print('Studio console errors (usually blocked analytics):',errors[:2])
 context.close()

def check_viewer(browser):
 page=browser.new_page(viewport={'width':400,'height':800});requested=[];errors=[]
 page.route('https://js.stripe.com/v3/buy-button.js',lambda r:(requested.append(1),r.fulfill(status=200,content_type='text/javascript',body=MOCK_STRIPE)))
 page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 slide={'token':TOKEN,'title':'Sample painting','url':'/p/'+TOKEN,'image':'/p/'+TOKEN+'/image.png'}
 html=('<!doctype html><html><head><style>'+public_viewer.BASE_CSS+public_viewer.VIEWER_CSS+'</style></head><body>'
       +public_viewer.viewer_markup([slide],0,'Artist','/u/Artist')
       +'<script>'+public_viewer.VIEWER_JS+'</script>'
       +'<script>'+(ROOT/'frontend/assets/stripe_donate.js').read_text()+'</script></body></html>')
 page.set_content(html,wait_until='domcontentloaded')
 assert not requested
 assert 'Download original PNG' in page.content()
 page.locator('#artDownload').click()
 page.locator('#supportDialog [data-test-stripe-button]').wait_for(timeout=10000)
 assert len(requested)==1
 assert page.locator('#artDownloadFile').get_attribute('href')=='/p/'+TOKEN+'/image.png'
 assert page.locator('#supportDialog .stripe-donation-fallback').get_attribute('target')=='_blank'
 page.locator('#supportDialog [data-stripe-dialog-close]').click()
 assert not page.locator('#supportDialog').evaluate('(el)=>el.open')
 print('public viewer: PASS (free download, lazy widget, secure link, close)')
 unexpected=[m for m in errors if 'Content Security Policy' in m or 'Refused to' in m]
 assert not unexpected,unexpected
 page.close()

if __name__=='__main__':
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  try:
   check_page(browser)
   check_page(browser,mobile=True)
   check_viewer(browser)
  finally:browser.close()
 print('ALL STRIPE / IDENTITY BROWSER CHECKS PASSED')
