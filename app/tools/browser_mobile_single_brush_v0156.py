from pathlib import Path
from playwright.sync_api import sync_playwright
APP=Path(__file__).resolve().parents[1]
html=(APP/'frontend/index.html').read_text()
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in html
html=html.replace('initUI();initDevLog();','initUI();').replace(anchor,"window.__qa156={state(){return {tip,size,color};},setColor(){updateColor('#ef3981')}};"+anchor,1)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width,height in [(320,720),(390,844),(430,900)]:
  context=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=1)
  page=context.new_page();page.set_default_timeout(9000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  page.set_content(html,wait_until='domcontentloaded');page.wait_for_function('!!window.__qa156')
  page.evaluate('__qa156.setColor()')
  assert page.locator('#mobileBrushTop button').count()==1,'two buttons remain'
  assert page.locator('#mobileBrushPopover #mobileTipCycle').count()==1
  assert not page.locator('#mobileTipCycle').is_visible()
  assert page.locator('#mobileBrushLauncherImage').evaluate('c=>c.getContext("2d").getImageData(c.width/2,c.height/2,1,1).data[3]')>0,'launcher needs tip image'
  page.locator('#mobileBrush').tap()
  assert page.locator('#mobileBrushPopover').is_visible()
  assert page.locator('#mobileTipCycle').is_visible()
  assert page.locator('#mobileBrushSizePreview').is_visible()
  assert page.locator('#mobileBrushNumber').count()==0
  launch=page.locator('#mobileBrush').bounding_box();sw=page.locator('#mobileSwatch').bounding_box();tipbox=page.locator('#mobileTipCycle').bounding_box()
  assert launch['y']+launch['height']<sw['y'],'launcher must be above swatch'
  assert tipbox['y']+tipbox['height']<launch['y'],'tip must be in rail, not a dock control'
  old=page.evaluate('__qa156.state()')
  page.locator('#mobileTipCycle').tap();page.wait_for_timeout(100)
  changed=page.evaluate('__qa156.state()')
  assert changed['tip']!=old['tip'],('tap should cycle tip',old,changed)
  assert page.locator('#mobileBrushPopover').is_visible(), 'rail should stay open'
  slider=page.locator('#mobileSizeSlider');box=slider.bounding_box();x=round(box['x']+box['width']/2)
  cdp=context.new_cdp_session(page)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':round(box['y']+box['height']*.78),'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':round(box['y']+box['height']*.21),'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  assert page.evaluate('__qa156.state().size')>135,page.evaluate('__qa156.state()')
  assert page.locator('#mobileBrushSizePreview').is_visible()
  # real finger holds in-rail tip swatch
  box=page.locator('#mobileTipCycle').bounding_box();x=round(box['x']+box['width']/2);y=round(box['y']+box['height']/2)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
  page.wait_for_timeout(610)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  page.wait_for_function("document.getElementById('mobileTipGallery').classList.contains('open')")
  assert page.locator('#mobileTipGalleryCategories button').count()>=10
  page.locator('#mobileTipGalleryCategories button').filter(has_text='Dry Media').first.tap()
  page.locator('#mobileTipGalleryGrid button').first.tap()
  assert not page.locator('#mobileTipGallery').is_visible()
  assert page.locator('#mobileBrushPopover').is_visible(),'rail should remain after gallery selection'
  page.locator('#mobileBrush').tap()
  assert not page.locator('#mobileBrushPopover').is_visible()
  assert page.locator('#mobileTipCycle').is_hidden()
  assert not errors,errors
  print('PASS',width,'single launcher + size slider + tap tip + long hold gallery + return to rail',flush=True)
  context.close()
 browser.close()
