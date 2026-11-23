#!/usr/bin/env python3
"""Offline Chromium smoke for visible brush shapes, clean identity links and minimized-window dragging.

Does not contact Paint Lab or Stripe backends.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
    try:
        page = browser.new_page(viewport={'width':1180,'height':900})
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('https://analytics.mielniczuk.com/**',lambda r:r.abort())
        page.route('https://js.stripe.com/**',lambda r:r.abort())
        page.set_content((ROOT/'frontend/index.html').read_text(), wait_until='domcontentloaded')
        page.wait_for_timeout(1050)
        if page.locator('#devLogOverlay').is_visible():page.locator('#devLogClose').click()
        for selector in ('.paint-lab-version','.paint-lab-brand-link'):
            for item in page.locator(selector).all():
                assert item.evaluate('(e)=>getComputedStyle(e).textShadow') == 'none',selector
                assert item.evaluate('(e)=>getComputedStyle(e).color') == 'rgb(0, 0, 0)',selector
        print('PASS: version and links plain black, no shadow')
        # Isolate the panel to measure the default visible brush gallery.
        page.evaluate('''() => {
           for(const id of ['palettePanel','modePanel','shapePanel','surfacePanel','historyPanel','layersPanel']) { const other=document.getElementById(id);if(other)other.style.display='none'; }
           const p=document.getElementById('tipPanel');
           p.style.display='flex';p.classList.remove('collapsed');
           p.style.width='510px';p.style.height='620px';p.style.left='150px';
           p.style.top='80px';p.style.right='auto';p.style.bottom='auto';
           window.dispatchEvent(new Event("resize"));
        }''')
        page.wait_for_timeout(300)
        gallery=page.locator('#tipGrid')
        assert page.locator('#tipGrid .tip-btn').count()>=25
        assert gallery.evaluate('(e)=>e.clientHeight')>=200
        assert gallery.evaluate('(e)=>e.scrollHeight > e.clientHeight')
        assert not page.locator('#brushEditor').evaluate('(e)=>e.open')
        assert not page.locator('#textBrushAdvanced').evaluate('(e)=>e.open')
        assert page.locator('#tipGrid .tip-btn').first.bounding_box()['height'] >= 70
        assert page.locator('#tipGrid .tip-btn .tip-art').first.evaluate('(e)=>getComputedStyle(e).backgroundImage') != 'none'
        print('PASS: scrollable silhouettes visible; advanced sections collapsed')
        # Keep panel visible but explicitly minimize and drag its header to the upper-left edge.
        page.locator('#tipPanel .panel-head .collapse').click()
        assert page.locator('#tipPanel').evaluate('(e)=>e.classList.contains("collapsed")')
        before=page.locator('#tipPanel').bounding_box()
        head=page.locator('#tipPanel .panel-head').bounding_box()
        x=head['x']+110;y=head['y']+head['height']/2
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(120,2,steps=12);page.mouse.up()
        after=page.locator('#tipPanel').bounding_box()
        assert 5 <= after['y'] <= 8,(before,after)
        assert page.locator('#tipPanel').evaluate('(e)=>parseInt(getComputedStyle(e).zIndex)')>=151
        print('PASS: minimized brush window dragged to top edge',round(after['y']))
        # Expanded panel gets different floor, and header never traps it beneath the brand.
        page.locator('#tipPanel .panel-head .collapse').click()
        after_expand=page.locator('#tipPanel').bounding_box()
        brand=page.locator('#paintLabBrand').bounding_box()
        assert after_expand['y'] >= brand['y']+brand['height']+7 - 1,(after_expand,brand)
        print('PASS: expanded window clears branding strip')
        assert not errors, errors[:4]
    finally:browser.close()
