"""Real-touch acceptance for mobile v0.1.62: one contextual editor, compact handles and fixed header."""
from pathlib import Path
from playwright.sync_api import sync_playwright
APP=Path(__file__).resolve().parents[1]
html=(APP/'frontend/index.html').read_text()
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in html
hook="""window.__qa161={state(){return {mode,material,strength,flow,wetness,density,scatter,styleAmount,styleCell,naturalWidth,mobileEraser:mobileOptions.eraser,pre:mobilePreEraserMode,tip,size};},setEffect(){setMode(2);return this.state()},reset(){setMode(0)},setStylize(){setMode(0);selectStrokeStyle('halftone');return this.state()}};"""
html=html.replace('initUI();initDevLog();','initUI();').replace(anchor,hook+anchor,1)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width,height in [(320,740),(390,844),(430,930)]:
  ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=1)
  page=ctx.new_page();page.set_default_timeout(11000)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded');page.wait_for_function('!!window.__qa161')
  assert page.evaluate('__qa161.state().mobileEraser'), 'eraser should default to visible'
  assert page.locator('#mobileErase').is_visible()
  eraser=page.locator('#mobileErase').bounding_box();undo=page.locator('#mobileUndo').bounding_box();redo=page.locator('#mobileRedo').bounding_box()
  assert eraser['x']<undo['x']<redo['x'],(eraser,undo,redo)
  assert max(abs(eraser['y']-undo['y']),abs(eraser['height']-undo['height']))<2
  assert eraser['x']>=0 and redo['x']+redo['width']<=width+1
  assert abs(eraser['width']-undo['width'])<2, (eraser,undo)
  page.evaluate('__qa161.setEffect()')
  page.locator('#mobileErase').tap();assert page.evaluate('__qa161.state().mode')==1
  page.locator('#mobileErase').tap();assert page.evaluate('__qa161.state().mode')==2, 'eraser restores active effect mode'
  # Material long-hold activates the mobile brush editor, short tap still cycles material.
  cdp=ctx.new_cdp_session(page)
  def hold(selector,tid):
   box=page.locator(selector).bounding_box()
   assert box,(selector,'not visible')
   x=round(box['x']+box['width']/2);y=round(box['y']+box['height']/2)
   cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':tid}]})
   page.wait_for_timeout(650)
   cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  page.evaluate('__qa161.reset()')
  hold('#mobileMaterial',1)
  assert page.locator('#mobileDynamicsSheet').is_visible(),(width,'sheet did not open')
  assert page.locator('#mobileDynamicsSheet').get_attribute('role')=='dialog'
  assert page.locator('#mobileTune_strength').is_visible()
  assert page.locator('#mobileTune_flow').is_visible()
  assert page.locator('#mobileTune_wetness').is_visible()
  assert page.locator('#mobileTune_strength').evaluate('e=>e.getBoundingClientRect().width')>=width-60
  before=page.evaluate('__qa161.state()')
  page.locator('#mobileTune_strength').fill('39')
  after=page.evaluate('__qa161.state()')
  assert abs(after['strength']-.39)<.001,(before,after)
  assert page.locator('#strength').input_value()=='39'
  assert not page.locator('#mobileDynamicsTabs').count()
  assert not page.locator('[data-mobile-tuning-tab]').count()
  assert not page.locator('.mobile-tuning-choice').count()
  assert page.locator('#mobileTune_density').is_visible()
  assert page.locator('#mobileTune_pencilHardness').is_visible()
  page.locator('#mobileTune_density').fill('28')
  assert abs(page.evaluate('__qa161.state().density')-.28)<.001
  assert page.locator('#density').input_value()=='28'
  # Natural-height sheet stays within the visual viewport; header stays visible when the long brush editor scrolls.
  brush_sheet=page.locator('#mobileDynamicsSheet').bounding_box()
  assert brush_sheet['y']>=0 and brush_sheet['y']+brush_sheet['height']<=height+1,brush_sheet
  assert brush_sheet['height']>height*.65,brush_sheet
  assert page.locator('#mobileTune_strength').evaluate('e=>getComputedStyle(e).height')=='45px'
  title_y=page.locator('#mobileDynamicsTitle').bounding_box()['y']
  page.locator('#mobileDynamicsBody').evaluate('e=>e.scrollTop=e.scrollHeight')
  assert abs(page.locator('#mobileDynamicsTitle').bounding_box()['y']-title_y)<2
  assert page.locator('#mobileDynamicsBody').evaluate('e=>e.scrollTop')>0
  if width==390:
   page.locator('#mobileDynamicsBody').evaluate('e=>e.scrollTop=0')
   page.screenshot(path='/mnt/data/paintlab_v0162_mobile_brush.png')
  # Desktop natural-width checkbox is the same state in the sheet.
  checkbox=page.locator('#mobileDynamicsBody .mobile-tuning-check input').first
  was=page.evaluate('__qa161.state().naturalWidth')
  checkbox.set_checked(not was)
  assert page.evaluate('__qa161.state().naturalWidth') != was

  page.locator('#mobileDynamicsClose').tap()
  assert not page.locator('#mobileDynamicsSheet').is_visible()
  assert page.evaluate('__qa161.state().material')=='oil','holding material must not cycle'
  page.locator('#mobileMaterial').tap()
  assert page.evaluate('__qa161.state().material')=='pencil','short press cycles'
  # Effects long-hold and stylization long-hold open the appropriate live controls.
  hold('#mobileEffects',2)
  effect_sheet=page.locator('#mobileDynamicsSheet').bounding_box()
  assert effect_sheet['height']<=brush_sheet['height']+1,(brush_sheet,effect_sheet)
  assert effect_sheet['y']>=0 and effect_sheet['y']+effect_sheet['height']<=height+1
  assert page.locator('#mobileTune_strength').is_visible()
  assert page.locator('#mobileTune_scatter').is_visible()
  page.locator('#mobileDynamicsClose').tap()
  page.evaluate('__qa161.setStylize()')
  hold('#mobileStylize',3)
  assert page.locator('#mobileTune_styleAmount').is_visible()
  assert page.locator('#mobileTune_styleCell').is_visible()
  page.locator('#mobileTune_styleAmount').fill('45')
  assert abs(page.evaluate('__qa161.state().styleAmount')-.45)<.001
  assert page.locator('#styleAmount').input_value()=='45'
  if width==390:
   page.screenshot(path='/mnt/data/paintlab_v0162_mobile_stylize.png')
  page.locator('#mobileDynamicsClose').tap()
  assert not errors,(width,errors)
  print('PASS',width,'context-only mobile editor, thumb size, scrolling header, short effects sheet, real long press and canonical values',flush=True)
  ctx.close()
 browser.close()
