#!/usr/bin/env python3
"""Local-only desktop/mobile UI smoke for v0.1.67; Stripe is mocked and payments are never made."""
from __future__ import annotations
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def test_desktop(browser,width=1180):
 context=browser.new_context(viewport={'width':width,'height':900})
 page=context.new_page();page.set_default_timeout(5000);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('https://analytics.mielniczuk.com/**',lambda r:r.abort())
 page.route('https://js.stripe.com/**',lambda r:r.abort())
 page.set_content((ROOT/'frontend/index.html').read_text(),wait_until='domcontentloaded')
 page.wait_for_selector('#desktopQuickActions #trashTop')
 page.wait_for_timeout(950)
 if page.locator('#devLogOverlay').is_visible():page.locator('#devLogClose').click()
 assert page.locator('.paint-lab-brand').is_visible()
 brand=page.locator('#paintLabBrand').bounding_box()
 assert abs(brand['x']-10)<2 and abs(brand['y']-10)<2,brand
 assert page.locator('.paint-lab-wordmark').evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)')==28
 assert page.locator('#desktopQuickActions>button').count()==4,page.locator('#desktopQuickActions').inner_html()
 assert page.locator('#desktopMore').get_attribute('aria-expanded')=='false'
 # Simulate last release's stored overlapping panel coordinates and trigger resize reconciliation.
 page.evaluate("""() => { for (const [id,x,y,w] of [['toolRail',10,31,115],['tipPanel',135,31,600],['shapePanel',735,31,400]]) {const el=document.getElementById(id);el.style.display='flex';el.style.left=x+'px';el.style.top=y+'px';el.style.right='auto';el.style.width=w+'px';} window.dispatchEvent(new Event('resize'));}""")
 page.wait_for_timeout(200)
 for id in ('toolRail','tipPanel','shapePanel'):
  r=page.locator('#'+id).bounding_box()
  assert not r or r['y']>=brand['y']+brand['height']+7,(id,r,brand)
 # menu button actions are original IDs and retain handlers
 page.locator('#desktopMore').click()
 assert page.locator('#desktopOverflowMenu').is_visible()
 assert page.locator('#desktopOverflowMenu #helpTop').is_visible()
 page.locator('#desktopOverflowMenu #helpTop').click()
 assert page.locator('#helpOverlay').is_visible(),'Menu help action must work'
 assert not page.locator('#desktopOverflowMenu').is_visible()
 page.locator('#helpOverlay [data-close="helpOverlay"]').first.click()
 # settings checkboxes pin/unpin existing gallery action
 page.locator('#settingsTop').click()
 assert page.locator('#settingsShade').is_visible()
 section=page.locator('.desktop-toolbar-settings')
 section.locator('summary').click()
 gallery_option=page.locator('#desktopToolbarChoices input[value="galleryTop"]')
 gallery_option.check()
 assert page.locator('#desktopQuickActions #galleryTop').count()==1
 page.locator('#doneSettings').click()
 assert not page.locator('#settingsShade').is_visible()
 # Existing DOM action persists when re-parented; localStorage persistence is
 # asserted by the static contract test (opaque browser origin in offline smoke).
 assert page.locator('#desktopQuickActions #galleryTop').count()==1
 # HUD Zoom and clickable Fit: apply Zoom via keyboard then Fit via HUD
 page.keyboard.press('+')
 page.wait_for_timeout(110)
 previous=page.locator('#zoomValue').inner_text()
 page.locator('#resetView').click()
 page.wait_for_timeout(100)
 following=page.locator('#zoomValue').inner_text()
 assert following.endswith('%') and previous!=following,(previous,following)
 # Shift+S; plain S continues transform and does not launch save
 page.keyboard.press('Shift+s')
 assert page.locator('#saveOverlay').is_visible(),'Shift+S should open Save & share'
 for el in page.locator('.dialogHead button:has(> .svg-icon use[href="#pl-close"])').all()[:4]:
  box=el.bounding_box()
  if box and box['width']>0:assert abs(box['width']-box['height'])<=1,box
 page.locator('#saveOverlay [data-close="saveOverlay"]').click()
 assert not page.locator('#saveOverlay').is_visible()
 page.keyboard.press('s')
 assert not page.locator('#saveOverlay').is_visible(),'Plain S should not open save'
 if errors:raise AssertionError('JS errors: '+repr(errors[:6]))
 print('desktop '+str(width)+' PASS: branding, header clearance, menu, pin selection, fit, Shift+S, square close')
 context.close()

def test_mobile(browser):
 context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 page=context.new_page();page.set_default_timeout(5000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('https://analytics.mielniczuk.com/**',lambda r:r.abort())
 page.set_content((ROOT/'frontend/index.html').read_text(),wait_until='domcontentloaded')
 page.wait_for_function("document.documentElement.classList.contains('mobile-workspace')")
 page.wait_for_timeout(950)
 if page.locator('#devLogOverlay').is_visible():page.locator('#devLogClose').click()
 assert not page.locator('.appbar').is_visible()
 assert page.locator('.paint-lab-brand').is_visible()
 page.locator('#mobileFocus').click()
 assert not page.locator('.paint-lab-brand').is_visible()
 page.locator('#mobileFocus').click()
 assert page.locator('.paint-lab-brand').is_visible()
 if errors:raise AssertionError(errors[:5])
 print('mobile PASS: original toolbar hidden, branded mobile focus preserved')
 context.close()

if __name__=='__main__':
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  try:
   test_desktop(browser,1180)
   test_desktop(browser,750)
   test_mobile(browser)
  finally:browser.close()
