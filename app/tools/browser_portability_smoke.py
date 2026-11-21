from playwright.sync_api import sync_playwright
from pathlib import Path
import zipfile,io,json,shutil,time
errors=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page(viewport={'width':1280,'height':820},accept_downloads=True)
 page.on('pageerror',lambda exc: errors.append(str(exc)))
 html=(Path(__file__).resolve().parents[1] / 'frontend' / 'index.html').read_text()
 hook='''window.__paintQA={state:()=>({w:baseW,h:baseH,title:artName,head,actions:actions.length,layers:layers.length}),ensureGallery:()=>{galleryDb={transaction:()=>({})}},selectPencil:()=>{chooseMaterial('pencil');size=20;strength=1;flow=1;},docToScreen:(x,y)=>pointToScreen(x,y)};'''
 html=html.replace("window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});",hook+"\nwindow.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});",1)
 page.set_content(html,wait_until='domcontentloaded',timeout=25000)
 page.evaluate('__paintQA.ensureGallery()')
 page.wait_for_timeout(1400)
 print('title',page.title(),'errors',errors)
 if page.locator('#devLogOverlay').evaluate('(x)=>x.classList.contains("visible")'):
  page.locator('#devLogDone').click(force=True)
 page.locator('#newWork').click(force=True)
 assert page.locator('#newCanvasOverlay').evaluate('(x)=>x.classList.contains("visible")')
 page.locator('[data-ratio="16:9"]').click()
 w=int(page.locator('#newCanvasWidth').input_value());h=int(page.locator('#newCanvasHeight').input_value())
 print('preset ratio',w,h)
 assert abs(w/h-16/9)<.01
 page.locator('#newCanvasWidth').fill('2048')
 page.locator('#newCanvasHeight').fill('1024')
 page.locator('#newCanvasName').fill('My portable painting')
 page.locator('#confirmNewCanvas').click()
 page.wait_for_timeout(500)
 dims=page.evaluate('__paintQA.state()')
 print('created',dims,'errors',errors)
 assert all(dims[k]==v for k,v in {'w':2048,'h':1024,'title':'My portable painting','layers':1}.items())
 # Paint a small pencil stroke, confirm editable action.
 page.evaluate('__paintQA.selectPencil()')
 start=page.evaluate('__paintQA.docToScreen(700,460)');end=page.evaluate('__paintQA.docToScreen(950,460)')
 page.mouse.move(start['x'],start['y']);page.mouse.down();page.mouse.move(end['x'],end['y'],steps=12);page.mouse.up()
 page.wait_for_timeout(350)
 print('history',page.evaluate('__paintQA.state()'))
 assert page.evaluate('__paintQA.state().head')>=1
 page.locator('#saveTop').click(force=True)
 print('save prefilled',page.locator('#artName').input_value())
 assert page.locator('#artName').input_value()=='My portable painting'
 with page.expect_download(timeout=35000) as info:
  page.locator('#saveZIP').click(force=True)
 artifact=info.value
 print('download',artifact.suggested_filename)
 out=Path('/tmp/paint_v0123_roundtrip.zip');artifact.save_as(str(out))
 with zipfile.ZipFile(out) as z:
  print('zip names',z.namelist());desc=json.loads(z.read('project.json'))
  assert desc['document']['baseW']==2048 and desc['document']['title']=='My portable painting'
  assert any(p.startswith('assets/layers/') for p in z.namelist())
  assert len(desc['document']['actions'])>=1
 page.locator('[data-close="saveOverlay"]').first.click(force=True)
 # export transparent PNG
 page.locator('#saveTop').click(force=True)
 with page.expect_download(timeout=35000) as pnginfo:page.locator('#savePNGWithout').click(force=True)
 print('png',pnginfo.value.suggested_filename)
 page.locator('[data-close="saveOverlay"]').first.click(force=True)
 # fresh canvas with no history
 page.locator('#newWork').click(force=True)
 page.locator('#confirmNewCanvas').click(force=True)
 if page.locator('#askOverlay').evaluate('(x)=>x.classList.contains("visible")'):
  page.locator('#askAccept').click(force=True)
 page.wait_for_timeout(250)
 print('blank',page.evaluate('__paintQA.state()'))
 page.locator('#exportTop').click(force=True)
 page.locator('#importProjectFile').set_input_files(str(out))
 page.wait_for_timeout(1100)
 if page.locator('#askOverlay').evaluate('(x)=>x.classList.contains("visible")'):
  page.locator('#askAccept').click(force=True)
 page.wait_for_timeout(450)
 restored=page.evaluate('__paintQA.state()')
 print('restored',restored,'errors',errors)
 assert restored['w']==2048 and restored['h']==1024 and restored['head']>=1 and restored['layers']==1
 page.locator('#shareTop').click(force=True)
 print('share dialog',page.locator('#shareOverlay').evaluate('(x)=>x.classList.contains("visible")'))
 assert page.locator('#shareOverlay').evaluate('(x)=>x.classList.contains("visible")')
 assert not errors,errors
 browser.close()
print('browser workflow PASS')
