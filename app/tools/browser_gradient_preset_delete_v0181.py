#!/usr/bin/env python3
"""v0.1.81 desktop/mobile: select gradient tile, then explicitly delete with confirmation."""
from pathlib import Path
from playwright.sync_api import sync_playwright

html=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text(encoding='utf-8')
marker='})();\n</script></body></html>'
assert html.count(marker)==1
hook=r'''
window.__gradientDelete181={
 setup(){
  const make=(first,middle,last)=>[
   {position:0,color:first}, {position:.5,color:middle}, {position:1,color:last}
  ];
  customGradientPresets=[
   {id:'gradient-one',name:'First',anchors:make('#ff0000','#00ff00','#0000ff')},
   {id:'gradient-two',name:'Second',anchors:make('#ffff00','#ff00ff','#ffeeaa')}
  ];
  selectedGradientPresetId=null;
  persistGradientPresets();
 },
 state(){return {
  names:customGradientPresets.map(p=>p.id), selected:selectedGradientPresetId,
  paletteName, anchors:JSON.parse(JSON.stringify(gradientAnchors)),
  saved:JSON.parse(localStorage.getItem(GRADIENT_PRESETS_KEY)||'[]').map(p=>p.id)
 };},
 editSelected(){selectPaletteSwatch(8);editSelectedPaletteSwatch('#778899');}
};
'''
html=html.replace(marker,hook+marker)
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--disable-gpu','--use-gl=angle','--use-angle=swiftshader'])
    for mobile in (False,True):
        page=browser.new_page(viewport={'width':390 if mobile else 1180,'height':780},is_mobile=mobile,has_touch=mobile)
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.evaluate("""() => {const map={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem(k){return map[k]??null},setItem(k,v){map[k]=String(v)},removeItem(k){delete map[k]}}});}""")
        page.set_content(html,wait_until='domcontentloaded',timeout=50000)
        page.wait_for_function('!!window.__gradientDelete181')
        page.evaluate('window.__gradientDelete181.setup()')
        tiles=page.locator('#gradientPresets .palette-gradient-load')
        delete=page.locator('#deleteGradientPreset')
        assert tiles.count()==2
        assert page.locator('#gradientPresets .palette-gradient-delete').count()==0
        assert delete.is_disabled()
        assert tiles.nth(0).get_attribute('aria-pressed')=='false'
        # Every pixel of the preset can be clicked safely without a delete overlay.
        page.evaluate("document.querySelectorAll('#gradientPresets .palette-gradient-load')[1].click()")
        assert tiles.nth(1).get_attribute('aria-pressed')=='true'
        assert tiles.nth(0).get_attribute('aria-pressed')=='false'
        assert delete.is_enabled()
        before=page.evaluate('window.__gradientDelete181.state()')
        assert before['selected']=='gradient-two'
        # Cancel never deletes the selection.
        page.evaluate("document.querySelector('#deleteGradientPreset').click()")
        page.locator('#askOverlay.visible').wait_for()
        page.locator('#askCancel').click()
        assert page.evaluate('window.__gradientDelete181.state()')['saved']==['gradient-one','gradient-two']
        assert tiles.nth(1).get_attribute('aria-pressed')=='true'
        assert delete.is_enabled()
        # Delete precisely the selected preset, leaving applied gradient intact.
        page.evaluate("document.querySelector('#deleteGradientPreset').click()")
        page.locator('#askOverlay.visible').wait_for()
        page.locator('#askAccept').click()
        page.wait_for_function("JSON.parse(localStorage.getItem('paint-lab-gradient-presets-v1')||'[]').length===1")
        after=page.evaluate('window.__gradientDelete181.state()')
        assert after['saved']==['gradient-one'],after
        assert after['anchors']==before['anchors'],after
        assert delete.is_disabled()
        assert tiles.count()==1
        # Edits make the preset unselected; old saved data does not change.
        page.evaluate("document.querySelector('#gradientPresets .palette-gradient-load').click()")
        assert delete.is_enabled()
        page.evaluate('window.__gradientDelete181.editSelected()')
        assert delete.is_disabled()
        assert tiles.nth(0).get_attribute('aria-pressed')=='false'
        assert page.evaluate('window.__gradientDelete181.state()')['saved']==['gradient-one']
        assert not errors,errors
        print(('Mobile' if mobile else 'Desktop')+' safe selected-gradient delete PASS')
        page.close()
    browser.close()
