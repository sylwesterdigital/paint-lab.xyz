"""Chromium touch acceptance: the SAME square brush button controls size, tip and gallery."""
from pathlib import Path
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
html=(APP/'frontend/index.html').read_text()
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in html
html=html.replace('initUI();initDevLog();','initUI();').replace(anchor,"window.__qa157={state(){return {tip,size,color};},setColor(){updateColor('#1c82fc')}};"+anchor,1)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width,height in [(320,720),(390,844),(430,900)]:
  context=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=1)
  page=context.new_page();page.set_default_timeout(9000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  page.set_content(html,wait_until='domcontentloaded');page.wait_for_function('!!window.__qa157')
  page.evaluate('__qa157.setColor()')
  assert page.locator('#mobileBrushTop button').count()==1
  assert page.locator('#mobileBrushPopover button').count()==0
  assert page.locator('#mobileTipCycle').count()==0
  assert not page.locator('#mobileBrushPopover').is_visible()
  launcher=page.locator('#mobileBrush').bounding_box();swatch=page.locator('#mobileSwatch').bounding_box()
  assert abs(launcher['width']-swatch['width'])<=1,(launcher,swatch)
  assert abs(launcher['height']-swatch['height'])<=1,(launcher,swatch)
  assert abs(launcher['x']-swatch['x'])<=2,(launcher,swatch)
  assert launcher['y']+launcher['height'] < swatch['y'],(launcher,swatch)
  initial=page.evaluate('__qa157.state()')
  page.locator('#mobileBrush').tap()
  assert page.locator('#mobileBrushPopover').is_visible()
  assert page.locator('#mobileSizeSlider').is_visible()
  assert page.locator('#mobileBrushSizePreview').is_visible()
  assert page.evaluate('__qa157.state().tip')==initial['tip'],'opening should not change tip'
  assert page.locator('#mobileBrush').get_attribute('aria-expanded')=='true'
  # Repeated tapping the SAME launcher cycles tips; rail stays open.
  page.locator('#mobileBrush').tap()
  second=page.evaluate('__qa157.state()')
  assert second['tip']!=initial['tip'],('second tap should cycle tip',initial,second)
  assert page.locator('#mobileBrushPopover').is_visible(),'second tap must not close rail'
  assert page.locator('#mobileBrush').bounding_box()==launcher,'button must not move or resize'
  # Slider drag still adjusts diameter and uses the same selected paint color.
  rail=page.locator('#mobileSizeSlider');box=rail.bounding_box();x=round(box['x']+box['width']/2)
  cdp=context.new_cdp_session(page)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':round(box['y']+box['height']*.78),'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':round(box['y']+box['height']*.21),'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  assert page.evaluate('__qa157.state().size')>135,page.evaluate('__qa157.state()')
  assert page.locator('#mobileBrushPopover').is_visible()
  if width==390:
   page.screenshot(path='/mnt/data/paintlab_mobile_one_brush_v0157_open.png')
  # Real long touch on the SAME launcher opens the categorized tip gallery.
  box=page.locator('#mobileBrush').bounding_box();x=round(box['x']+box['width']/2);y=round(box['y']+box['height']/2)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':2}]})
  page.wait_for_timeout(640)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  page.wait_for_function("document.getElementById('mobileTipGallery').classList.contains('open')")
  assert page.locator('#mobileTipGalleryCategories button').count()>=10
  assert page.locator('#mobileBrushPopover button').count()==0
  if width==390:
   page.screenshot(path='/mnt/data/paintlab_mobile_one_brush_v0157_gallery.png')
  page.locator('#mobileTipGalleryCategories button').filter(has_text='Dry Media').first.tap()
  page.locator('#mobileTipGalleryGrid button').first.tap()
  assert not page.locator('#mobileTipGallery').is_visible()
  assert page.locator('#mobileBrushPopover').is_visible(),'return to open slider'
  assert page.locator('#mobileBrushTop button').count()==1
  assert not errors,errors
  print('PASS',width,'one stationary button + open slider + same-button tip cycle + gallery hold + return to slider',flush=True)
  context.close()
 browser.close()
