#!/usr/bin/env python3
"""Real Chromium regression: mobile controls, layers, clear+reset, desktop continuity."""
from pathlib import Path
from playwright.sync_api import sync_playwright
APP=Path(__file__).resolve().parents[1]
HOOK=r'''
window.__mobileQA={
 state(){return {mode,style:strokeStyle,size,tip,material,head,layerCount:layers.length,options:{...mobileOptions},rendering};},
 setBrush(){setMode(0);selectStrokeStyle('pixelate');setTip('fan');chooseMaterial('pencil');setStyleValue('styleCell',88);$('size').value=123;$('size').dispatchEvent(new Event('input',{bubbles:true}));return this.state()},
 reset(){resetPaintingTools();return this.state();},
 setCanvas(){baseW=460;baseH=300;resize(false);actions=[];head=0;rebuild();},
 getSelection(){return {active:mobileSheetId,layers:layers.length};},
 enableLocalSaving(){galleryDb={};window.__savedInTest=[];storeRecord=async record=>window.__savedInTest.push({id:record.id,document:record.data});thumbnail=()=>"data:image/jpeg;base64,T0s=";}
};
'''
html=(APP/'frontend/index.html').read_text();anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in html
html=html.replace('initUI();initDevLog();','initUI();').replace(anchor,HOOK+anchor,1)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width,height in [(390,844),(320,720)]:
  context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,is_mobile=True,has_touch=True)
  page=context.new_page();page.set_default_timeout(12000);errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
  page.set_content(html,wait_until='domcontentloaded',timeout=30000)
  page.wait_for_function("!!window.__mobileQA&&document.documentElement.classList.contains('mobile-workspace')")
  assert page.locator('#mobileShare').count()==0
  assert page.locator('#mobileSizeButton').count()==0
  assert page.locator('#mobileBrush').is_visible()
  assert page.locator('#mobileLayers').is_visible()
  assert page.locator('#mobileEffects').is_visible()
  assert page.locator('#mobileStylize').is_visible()
  assert page.locator('#mobileEffects').inner_text()=='FX: None'
  assert page.locator('#mobileStylize').inner_text()=='Style: None'
  page.locator('#mobileEffects').click()
  assert page.evaluate('__mobileQA.state().mode')==2
  assert page.locator('#mobileEffects').inner_text()=='FX: Smear'
  assert page.locator('#mobileEffectsNone').is_visible()
  page.locator('#mobileStylize').click()
  assert page.evaluate('__mobileQA.state().mode')==0
  assert page.evaluate('__mobileQA.state().style')=='halftone'
  assert page.locator('#mobileEffects').inner_text()=='FX: None'
  assert page.locator('#mobileStylize').inner_text()=='Style: Halftone'
  page.locator('#mobileStylizeNone').click()
  assert page.evaluate('__mobileQA.state().style')=='none'
  page.locator('#mobileEffects').click()
  page.locator('#mobileEffectsNone').click()
  assert page.evaluate('__mobileQA.state().mode')==0
  page.locator('#mobileBrush').click()
  assert page.locator('#mobileBrushPopover').is_visible()
  page.locator('#mobileBrushNext').click()
  assert page.evaluate('__mobileQA.state().tip')!='round'
  page.locator('#mobileSizeSlider').focus();page.keyboard.press('ArrowUp')
  assert page.evaluate('__mobileQA.state().size')!=38
  page.locator('#mobileLayers').click()
  assert page.locator('#layersPanel.mobile-sheet-active').is_visible()
  sheet=page.locator('#layersPanel');thumb=page.locator('#layersList .layer-thumb').first
  sh=sheet.evaluate('e=>e.getBoundingClientRect().height');tw=thumb.evaluate('e=>e.getBoundingClientRect().width')
  assert sh<=500,(width,sh)
  assert tw>=69,(width,tw)
  page.locator('#addLayer').click()
  assert page.evaluate('__mobileQA.state().layerCount')==2
  assert page.locator('#layersList .layer-thumb').count()==2
  page.locator('#mobileLayers').click() # toggle Layers closed
  assert not page.locator('#layersPanel').evaluate("e=>e.classList.contains('mobile-sheet-active')")
  # Clear WITHOUT reset: tool choice remains.
  page.evaluate('__mobileQA.setBrush()')
  current=page.evaluate('__mobileQA.state()')
  page.locator('#mobileClear').click()
  assert not page.locator('#clearResetTools').is_checked()
  page.locator('#confirmCanvasClear').click()
  after=page.evaluate('__mobileQA.state()')
  assert (after['style'],after['size'],after['tip'])==(current['style'],current['size'],current['tip']),after
  # Clear WITH reset: style, effect, material, tip, size and other brush dynamics reset.
  page.locator('#mobileEffects').click() # picks effect mode, clears current style
  page.locator('#mobileClear').click()
  page.locator('#clearResetTools').check()
  page.locator('#confirmCanvasClear').click()
  after=page.evaluate('__mobileQA.state()')
  assert after['mode']==0 and after['style']=='none' and after['size']==38 and after['material']=='oil' and after['tip']=='round',after
  assert not page.locator('#clearResetTools').is_checked() or not page.locator('#clearCanvasOverlay').is_visible()
  # Save before clearing also carries the reset choice until the IndexedDB write completes.
  page.evaluate('__mobileQA.enableLocalSaving();__mobileQA.setBrush()')
  page.locator('#mobileClear').click()
  page.locator('#clearResetTools').check()
  page.locator('#saveBeforeCanvasClear').click()
  assert page.locator('#saveOverlay').is_visible()
  assert page.locator('#saveOverwrite').is_disabled()
  page.locator('#artName').fill('Preserved painting')
  page.locator('#saveNew').click()
  page.wait_for_function('window.__savedInTest.length===1')
  state=page.evaluate('__mobileQA.state()')
  assert state['size']==38 and state['style']=='none' and state['tip']=='round',state
  assert page.evaluate('window.__savedInTest[0].document.version')==4
  assert not page.locator('#saveOverlay').is_visible()
  assert not errors,(width,errors)
  page.screenshot(path=f'/mnt/data/paintlab_mobile_controls_v0149_{width}.png')
  print('PASS mobile',width,'effects stylize None, combined brush+size, layer sheet',sh,'px thumbnail',tw,'px, clear/reset, errors none')
  context.close()
 # Desktop controls still visible
 context=browser.new_context(viewport={'width':1300,'height':850});page=context.new_page();errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
 page.set_content(html,wait_until='domcontentloaded',timeout=30000);page.wait_for_function('!!window.__mobileQA')
 assert not page.evaluate("document.documentElement.classList.contains('mobile-workspace')")
 assert page.locator('#saveTop').is_visible()
 assert page.locator('#layersPanel').is_visible()
 assert not errors,errors
 print('PASS desktop original UI intact')
 browser.close()
