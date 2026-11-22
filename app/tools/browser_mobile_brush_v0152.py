#!/usr/bin/env python3
"""Chromium smoke test: v0.1.52 left-edge size rail, live tip and real touch long-hold browser."""
from pathlib import Path
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
page_html=(APP/'frontend/index.html').read_text().replace('initUI();initDevLog();','initUI();')
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in page_html
page_html=page_html.replace(anchor,"window.__mobileBrushQA={state(){return {tip,size,color};},colour(){updateColor('#f4257c');}};"+anchor,1)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    for width,height in [(390,760),(320,710)]:
        context=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True)
        page=context.new_page();page.set_default_timeout(9000)
        errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
        page.set_content(page_html,wait_until='domcontentloaded')
        page.wait_for_function('!!window.__mobileBrushQA')
        page.evaluate('window.__mobileBrushQA.colour()')
        page.locator('#mobileBrush').tap()
        assert page.locator('#mobileBrushPopover').is_visible()
        assert page.locator('#mobileBrushSizePreview').is_visible()
        rail=page.locator('#mobileBrushPopover').evaluate('e=>getComputedStyle(e).backgroundColor')
        assert rail=='rgba(0, 0, 0, 0)',rail
        slider=page.locator('#mobileSizeSlider')
        assert slider.evaluate('e=>getComputedStyle(e).getPropertyValue("--brush-color").trim()')=='#f4257c'
        assert page.locator('#mobileBrushNext').inner_text().strip()==''
        assert page.locator('#mobileBrushActualTip').evaluate('e=>e.getContext("2d").getImageData(160,160,1,1).data[0]')>200
        box=slider.bounding_box();x=box['x']+box['width']/2
        cdp=context.new_cdp_session(page)
        cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':round(x),'y':round(box['y']+box['height']*.8),'id':1}]})
        cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':round(x),'y':round(box['y']+box['height']*.2),'id':1}]})
        cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        assert page.evaluate('__mobileBrushQA.state().size')>150,page.evaluate('__mobileBrushQA.state()')
        old=page.evaluate('__mobileBrushQA.state().tip')
        page.locator('#mobileBrushNext').tap()
        assert page.evaluate('__mobileBrushQA.state().tip')!=old
        selected=page.evaluate('__mobileBrushQA.state().tip')
        box=page.locator('#mobileBrushNext').bounding_box();x=round(box['x']+box['width']/2);y=round(box['y']+box['height']/2)
        cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
        page.wait_for_timeout(620)
        cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        page.wait_for_function("document.getElementById('mobileTipGallery').classList.contains('open')")
        assert page.evaluate('__mobileBrushQA.state().tip')==selected,'Hold must not silently select a tip'
        assert page.locator('#mobileTipGalleryCategories button').count()>=12
        assert page.locator('#mobileTipGalleryGrid button').count()>=30
        page.get_by_role('button',name='Dry Media',exact=True).tap()
        assert page.locator('#mobileTipGalleryGrid button').count()==3
        page.locator('#mobileTipGalleryGrid button').first.tap()
        assert not page.locator('#mobileTipGallery').is_visible()
        assert page.evaluate('__mobileBrushQA.state().tip')=='pointed'
        page.locator('#mobileLayers').tap()
        sheet=page.locator('#layersPanel.mobile-sheet-active');r=sheet.bounding_box()
        assert r['y']<5 and r['height']>=height-5,r
        assert not errors,(width,errors)
        print(f'PASS {width}px: coloured edge rail, live preview, touch slider, tap cycle, long press, category library, full-height layers')
        context.close()
    browser.close()
