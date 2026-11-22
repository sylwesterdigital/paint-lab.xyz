"""Browser acceptance: two-finger zoom/rotation and undistorted touch-to-canvas after resize/resume."""
from pathlib import Path
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
src=(APP/'frontend/index.html').read_text()
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert src.count(anchor)==1
src=src.replace('initUI();initDevLog();','initUI();',1).replace(anchor,"""window.__qa160={
 view:()=>({...view}),
 screen:(x,y)=>pointToScreen(x,y),
 point:(x,y)=>pointFromScreen(x,y),
 dims:()=>({vW,vH,baseW,baseH,dpr,css:{width:preview.getBoundingClientRect().width,height:preview.getBoundingClientRect().height},buffer:{width:display.width,height:display.height}}),
 mobile:()=>({...mobileOptions}),
 center:()=>({x:baseW/2,y:baseH/2}),
 mapped:(x,y)=>getPoint({clientX:x,clientY:y,pointerType:'touch'}),
};"""+anchor,1)

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width,height in [(320,720),(390,844),(430,900)]:
  context=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=1)
  page=context.new_page();page.on('pageerror',lambda e:print('JS ERROR',e))
  page.set_content(src,wait_until='domcontentloaded');page.wait_for_function('!!window.__qa160')
  assert page.evaluate('__qa160.mobile().rotateCanvas'),page.evaluate('__qa160.mobile()')
  before=page.evaluate('__qa160.view()')
  x,y=width/2,height/2
  cdp=context.new_cdp_session(page)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':1,'x':x-44,'y':y-35},{'id':2,'x':x+44,'y':y+35}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'id':1,'x':x-84,'y':y+15},{'id':2,'x':x+84,'y':y-15}]})
  during=page.evaluate('__qa160.view()')
  assert abs(during['angle']-before['angle'])>.35,(width,before,during)
  assert during['zoom']>before['zoom']*1.2,(width,before,during)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  # The canvas must be an orthogonal, uniformly scaled rectangle even when rotated.
  def assert_uniform():
   geo=page.evaluate('''() => {const c=__qa160.center();return [__qa160.screen(c.x,c.y),__qa160.screen(c.x+100,c.y),__qa160.screen(c.x,c.y+100)];}''')
   o,a,b=geo;u=(a['x']-o['x'],a['y']-o['y']);v=(b['x']-o['x'],b['y']-o['y'])
   normu=(u[0]**2+u[1]**2)**.5;normv=(v[0]**2+v[1]**2)**.5
   assert abs(normu-normv)<1e-4,(width,'nonuniform',normu,normv)
   assert abs(u[0]*v[0]+u[1]*v[1])<1e-3,(width,'skew',u,v)
   dst=page.evaluate('p=>__qa160.point(p.x,p.y)',a)
   cen=page.evaluate('__qa160.center()')
   assert abs(dst['x']-(cen['x']+100))<.01 and abs(dst['y']-cen['y'])<.01,(width,dst,cen)
  assert_uniform()
  # Actual viewport change triggers a canvas resolution update without resetting angle.
  page.set_viewport_size({'width':width+24,'height':height-120});page.wait_for_timeout(80)
  after=page.evaluate('__qa160.view()')
  assert abs(after['angle']-during['angle'])<1e-5,(width,during,after)
  dims=page.evaluate('__qa160.dims()')
  assert abs(dims['vW']-dims['css']['width'])<.51 and abs(dims['vH']-dims['css']['height'])<.51,(width,dims)
  assert abs(dims['buffer']['width']/dims['buffer']['height']-dims['css']['width']/dims['css']['height'])<.004,(width,dims)
  assert_uniform()
  # iOS app switching should not straighten an already completed rotation.
  page.evaluate("window.dispatchEvent(new Event('pagehide'));window.dispatchEvent(new Event('pageshow'))")
  page.wait_for_timeout(80)
  resumed=page.evaluate('__qa160.view()')
  assert abs(resumed['angle']-during['angle'])<1e-5,(width,during,resumed)
  assert_uniform()
  print(f'PASS {width}px rotated zoom, uniform aspect, resize and resumed coordinate mapping')
  context.close()
 browser.close()
