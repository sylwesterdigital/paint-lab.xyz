#!/usr/bin/env python3
"""Real Chromium checks for curated, editable and personal brush collection workflows."""
from pathlib import Path
from playwright.sync_api import sync_playwright
APP=Path(__file__).resolve().parents[1]
MARKER='})();\n</script></body></html>'
HOOK=r'''
window.__brushTest={
 inspect(){return {name:activeBrushRecipe?.name,tip,material,size,strength,flow,spacing,scatter,category:currentTipCategory,personal:personalBrushes.map(x=>({...x}))};},
 enter(){const panel=$('tipPanel');if(innerWidth<=650){openMobileSheet('tipPanel');}else{panel.style.display='flex';panel.classList.remove('collapsed');panel.style.height='min(730px,calc(100dvh - 28px))';panel.style.width='350px';panel.style.left='10px';panel.style.top='10px';$('toolRail').style.display='none';}renderTipLibrary();updateBrushEditor();},
 setPrompt(value){window.__promptValue=value;},
 signin(){cloudUser={username:'SampleArtist'};cloudCSRF='ok';loadPublications();},
 openShare(){openShareArtwork();},
 removeAll(){personalBrushes=[];persistPersonalBrushes();}
};
'''
html=(APP/'frontend/index.html').read_text();assert html.count(MARKER)==1
html=html.replace('initUI();initDevLog();','initUI();').replace(MARKER,HOOK+MARKER)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name,w,h in [('desktop',1280,900),('mobile',430,900)]:
  context=browser.new_context(viewport={'width':w,'height':h},is_mobile=name=='mobile',has_touch=name=='mobile')
  page=context.new_page();page.set_default_timeout(7000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded',timeout=30000)
  page.wait_for_function('!!window.__brushTest',timeout=16000)
  page.evaluate('window.__brushTest.enter()')
  assert page.locator('#tipCategories button').count()>=13
  page.get_by_role('button',name='Dry Media',exact=True).click()
  assert page.locator('#tipGrid .recipe').count()==3
  page.get_by_role('button',name='Soft graphite brush').evaluate('e=>e.click()')
  state=page.evaluate('window.__brushTest.inspect()')
  assert state['tip']=='pointed' and state['material']=='pencil' and state['size']==13,state
  assert page.locator('#brushEditorName').inner_text()=='Soft graphite'
  page.locator('#brushEdit_size').fill('49')
  page.locator('#brushEdit_strength').fill('66')
  state=page.evaluate('window.__brushTest.inspect()')
  assert state['size']==49 and abs(state['strength']-.66)<.001,state
  page.locator('#brushSaveNew').evaluate('e=>e.click()')
  page.locator('#askText').fill('My pencil')
  page.locator('#askAccept').click()
  page.wait_for_function('window.__brushTest.inspect().personal.length===1')
  state=page.evaluate('window.__brushTest.inspect()')
  assert state['category']=='My Brushes' and state['personal'][0]['name']=='My pencil',state
  assert not page.locator('#brushUpdate').is_hidden()
  page.locator('#brushEdit_flow').fill('48')
  page.locator('#brushUpdate').evaluate('e=>e.click()')
  state=page.evaluate('window.__brushTest.inspect()')
  assert state['personal'][0]['flow']==48,state
  page.locator('#brushRename').evaluate('e=>e.click()')
  page.locator('#askText').fill('Revised pencil')
  page.locator('#askAccept').click()
  assert page.locator('#tipGrid .recipe').first.locator('span').inner_text()=='Revised pencil'
  page.evaluate('window.__brushTest.signin()')
  page.evaluate('window.__brushTest.openShare()')
  assert page.locator('#sharePublicSpace').is_visible()
  assert page.locator('#sharePublicSpace').get_attribute('href')=='/u/SampleArtist?edit=1'
  assert page.locator('#sharePublications').count()==0
  assert page.locator('#shareOverlay .dialogFooter').count()==0
  page.screenshot(path=f'/mnt/data/paintlab_brush_library_v0148_{name}.png')
  page.locator('#shareOverlay [data-close="shareOverlay"]').first.click()
  page.locator('#brushDelete').evaluate('e=>e.click()')
  page.locator('#askAccept').click()
  page.wait_for_function('window.__brushTest.inspect().personal.length===0')
  assert not errors,errors
  print('PASS',name,'brush recipe/edit/personal save/update/rename/delete/share link')
  context.close()
 browser.close()
