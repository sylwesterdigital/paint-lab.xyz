"""Mobile acceptance tests for appearance sliders, theme generation and interrupted gestures."""
from pathlib import Path
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
src=(APP/'frontend/index.html').read_text()
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert src.count(anchor)==1
src=src.replace('initUI();initDevLog();','initUI();',1).replace(anchor,"""window.__qa158={
 appearance:(state)=>applyAppearance(state),
 view:()=>({...view}),
 mobile:()=>({...mobileOptions,rotationUserSet:mobileRotationExplicit}),
 screen:(x,y)=>pointToScreen(x,y),
 center:()=>({x:baseW/2,y:baseH/2}),
 point:(x,y)=>pointFromScreen(x,y),
 mapped:(x,y)=>getPoint({clientX:x,clientY:y,pointerType:'touch'}),
 prepareDrawing:()=>{chooseMaterial('pencil');size=8;setMode(0);},
 recentStroke:()=>actions[head-1]?.points?.slice(-1)[0]||null,
 regenerate:()=>generateAlternativeTheme(),
 palette:()=>({accent:getComputedStyle(document.documentElement).getPropertyValue('--accent'),theme})
};"""+anchor,1)

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width,height in [(320,720),(390,844),(430,900)]:
  context=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=1)
  page=context.new_page();page.set_default_timeout(9000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  page.set_content(src,wait_until='domcontentloaded');page.wait_for_function('!!window.__qa158')
  assert page.evaluate('__qa158.mobile().rotateCanvas'),page.evaluate('__qa158.mobile()')
  # A zero should be an actual zero, not a residual hardcoded border or shadow.
  page.evaluate('__qa158.appearance({border:0,background:96,shadows:true,shadowStrength:0,blur:0})')
  for selector in ['#mobileMaterial','#mobileBrush','#mobileEffects','#mobileStylize','#mobileSwatch','#mobileUndo']:
   o=page.locator(selector).evaluate('(el)=>{let c=getComputedStyle(el);return {border:c.borderColor,shadow:c.boxShadow}}')
   assert o['border'] in ['rgba(255, 255, 255, 0)','rgba(255, 255, 255, 0.0)','transparent','rgba(0, 0, 0, 0)','color(srgb 0 0 0 / 0)'],(width,selector,o)
   assert o['shadow']=='none',(width,selector,o)
  assert page.evaluate('document.documentElement.dataset.plShadows')=='off'
  assert page.evaluate('document.documentElement.dataset.plBorders')=='off'
  page.evaluate('__qa158.appearance({border:50,shadows:true,shadowStrength:35})')
  o=page.locator('#mobileMaterial').evaluate('el=>getComputedStyle(el).borderColor')
  assert '0.5' in o or '0.502' in o,(width,o)
  # Visible star button produces *different* themes on successive clicks.
  page.locator('#mobileSettings').tap()
  assert page.locator('#generateTheme').is_visible()
  page.locator('#generateTheme').tap();color1=page.evaluate('__qa158.palette()')
  page.locator('#generateTheme').tap();color2=page.evaluate('__qa158.palette()')
  assert color1['theme']=='generated' and color2['theme']=='generated'
  assert color1['accent']!=color2['accent'],(color1,color2)
  page.locator('#doneSettings').tap()
  # Canvas matrices remain invertible even after browser chrome adjustments.
  pos=page.evaluate('({p:__qa158.screen(500,400),v:__qa158.view()})')
  xy=page.evaluate('p=>__qa158.point(p.x,p.y)',pos['p'])
  assert abs(xy['x']-500)<1e-4 and abs(xy['y']-400)<1e-4,(pos,xy)
  # Two-finger rotation is enabled by default; no accidental disable.
  initial=page.evaluate('__qa158.view()')
  cdp=context.new_cdp_session(page)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':1,'x':width//2-54,'y':height//2-34},{'id':2,'x':width//2+54,'y':height//2+34}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'id':1,'x':width//2-45,'y':height//2+80},{'id':2,'x':width//2+52,'y':height//2-82}]})
  after=page.evaluate('__qa158.view()')
  assert abs(after['angle'])>.2,(width,after)
  # Simulate switching to another app before contacts are released.
  page.evaluate("window.dispatchEvent(new Event('pagehide'))")
  page.evaluate("window.dispatchEvent(new Event('pageshow'))")
  restored=page.evaluate('__qa158.view()')
  assert abs(restored['angle']-initial['angle'])<1e-7 and abs(restored['zoom']-initial['zoom'])<1e-7,(initial,restored)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  # Changing CSS box dimensions before a resize event must preserve coordinates.
  page.evaluate("document.getElementById('preview').style.width='90vw'")
  m=page.evaluate('''() => {const rect=preview.getBoundingClientRect(),x=rect.left+rect.width*.5,y=rect.top+rect.height*.5;return {p:__qa158.mapped(x,y),canvas:__qa158.center(),view:__qa158.view()};}''')
  assert abs(m['p']['x']-m['canvas']['x'])<.01 and abs(m['p']['y']-m['canvas']['y'])<.01,(width,m)
  page.evaluate("document.getElementById('preview').style.removeProperty('width')")
  # After a suspended gesture, the next real finger stroke must land beneath it.
  page.evaluate('__qa158.prepareDrawing()')
  paintx=round(width*.54);painty=round(height*.47)
  expected=page.evaluate('([x,y])=>__qa158.mapped(x,y)',[paintx+12,painty+8])
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':3,'x':paintx,'y':painty}]})
  page.wait_for_timeout(145)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'id':3,'x':paintx+12,'y':painty+8}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  page.wait_for_timeout(70)
  actual=page.evaluate('__qa158.recentStroke()')
  assert actual and abs(actual['x']-expected['x'])<2 and abs(actual['y']-expected['y'])<2,(width,expected,actual)

  if width==390:
   page.evaluate('__qa158.appearance({border:0,background:96,shadows:true,shadowStrength:0,blur:0})')
   page.screenshot(path='/mnt/data/paintlab_mobile_theme_v0158_no_chrome.png')
  assert not errors,errors
  print('PASS',width,'theme star + mobile 0 borders/shadows + interruption & canvas-to-touch mapping',flush=True)
  context.close()
 browser.close()
