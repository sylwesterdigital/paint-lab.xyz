#!/usr/bin/env python3
"""Chromium desktop/mobile: visible Bounce switch and named, persisted multi-stop gradient presets."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text(encoding='utf-8')
MARKER='})();\n</script></body></html>'
assert HTML.count(MARKER)==1
HOOK=r'''
window.__customGradient178={
 build(){
  const colours=Array.from({length:24},()=> '#607080');
  colours[0]='#ff1100';colours[23]='#101010';
  setPalette(colours,'Custom');modifyPalette('Gradients');
  selectPaletteSwatch(8);editSelectedPaletteSwatch('#00ddff');
  selectPaletteSwatch(16);editSelectedPaletteSwatch('#ffee00');
  return {anchors:JSON.parse(JSON.stringify(gradientAnchors)),palette:palette.slice()};
 },
 state(){return {name:paletteName,anchors:JSON.parse(JSON.stringify(gradientAnchors)),palette:palette.slice(),flow:colorTravel,bounce:colorTravelPingPong,presets:customGradientPresets.map(p=>({...p})),stored:localStorage.getItem(GRADIENT_PRESETS_KEY)};},
 resize(count){setPaletteSize(count);return {count:palette.length,anchors:JSON.stringify(gradientAnchors)}},
 reset(){setPalette(PALETTES.Studio,'Studio')},
 restoreSaved(){customGradientPresets=[];customGradientPresets=readGradientPresets();renderGradientPresets();return customGradientPresets.length},
 edit(){selectPaletteSwatch(8);editSelectedPaletteSwatch('#cc0088')}
};
'''
HTML=HTML.replace(MARKER,HOOK+MARKER)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--disable-gpu','--use-gl=angle','--use-angle=swiftshader'])
 for mobile in (False,True):
  page=browser.new_page(viewport={'width':390 if mobile else 1160,'height':800},is_mobile=mobile,has_touch=mobile)
  errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  # about:blank is intentionally offline; emulate browser localStorage between DOM loads.
  page.evaluate("""() => {window.__gradientStore={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem(k){return Object.prototype.hasOwnProperty.call(window.__gradientStore,k)?window.__gradientStore[k]:null},setItem(k,v){window.__gradientStore[k]=String(v)},removeItem(k){delete window.__gradientStore[k]}}});}""")
  page.set_content(HTML,wait_until='domcontentloaded',timeout=50000)
  page.wait_for_function('!!window.__customGradient178')
  created=page.evaluate('window.__customGradient178.build()')
  assert len(created['anchors'])==4
  bounce=page.locator('#palettePingPong'); flow=page.locator('#paletteTravel')
  assert not bounce.is_checked() and not flow.is_checked()
  # DOM click works on both desktop and mobile, including when mobile palette is collapsed.
  page.evaluate("document.querySelector('#paletteTravel').click()")
  page.evaluate("document.querySelector('#palettePingPong').click()")
  assert bounce.is_checked() and flow.is_checked()
  state=page.evaluate('window.__customGradient178.state()')
  assert state['bounce'] and state['flow']
  page.evaluate("document.querySelector('#saveGradientPreset').click()")
  page.locator('#askText').fill('Coastal Dawn')
  page.locator('#askAccept').click()
  page.wait_for_function("JSON.parse(localStorage.getItem('paint-lab-gradient-presets-v1')||'[]').length===1")
  saved=page.evaluate('window.__customGradient178.state()')
  assert len(saved['presets'])==1 and len(saved['presets'][0]['anchors'])==4
  page.evaluate('window.__customGradient178.reset()')
  page.evaluate("document.querySelector('#gradientPresets .palette-gradient-load').click()")
  restored=page.evaluate('window.__customGradient178.state()')
  assert restored['anchors']==created['anchors'] and restored['name']=='Gradients'
  for size in (8,48,24):
   assert page.evaluate('count => window.__customGradient178.resize(count)',size)['anchors']==__import__('json').dumps(created['anchors'],separators=(',',':'))
  # Editing after loading must not mutate the saved preset.
  page.evaluate('window.__customGradient178.edit()')
  assert page.evaluate('window.__customGradient178.state()')['anchors']!=created['anchors']
  assert page.evaluate('window.__customGradient178.state()')['presets'][0]['anchors']==created['anchors']
  assert page.evaluate('window.__customGradient178.restoreSaved()')==1
  assert page.locator('#gradientPresets .palette-gradient-load').count()==1
  page.evaluate("document.querySelector('#gradientPresets .palette-gradient-load').click()")
  assert page.evaluate('window.__customGradient178.state()')['anchors']==created['anchors']
  page.evaluate("document.querySelector('#gradientPresets .palette-gradient-delete').click()")
  page.locator('#askAccept').click()
  page.wait_for_function("JSON.parse(localStorage.getItem('paint-lab-gradient-presets-v1')||'[]').length===0")
  assert page.locator('#gradientPresets .palette-gradient-load').count()==0
  assert not errors,errors
  print(('Mobile' if mobile else 'Desktop')+' gradient custom presets + Bounce PASS')
  page.close()
 browser.close()
