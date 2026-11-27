#!/usr/bin/env python3
"""Desktop/mobile Chromium regression: live gradient picker never gets detached.

Native OS colour panels cannot be automated in headless Chromium; the observable
failure mode is precisely the transient removal of input[type=color].
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

html=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
marker='})();\n</script></body></html>'
assert html.count(marker)==1
hook=r'''
window.__testNativeColourPicker180={async run(isMobile=false){
 setPaletteSize(24);
 const start=Array.from({length:24},(_,i)=>i===0?'#ff0000':i===23?'#111111':'#'+((i*333333)&0xffffff).toString(16).padStart(6,'0'));
 setPalette(start,'Custom');modifyPalette('Gradients');
 if(paletteName!=='Gradients'||gradientAnchors.length!==2)throw Error('gradient setup failed');
 const picker=$('colorPicker'),container=$('currentColor'),sw=$('swatches');
 const firstButton=sw.querySelector('button.swatch[data-index="1"]');
 const mobileButton=$('mobilePaletteGrid').firstElementChild;
 let detached=0,buttonRemoved=0,mobileRebuilt=0;
 const contains=(removed,target)=>removed===target||(removed.nodeType===1&&removed.contains(target));
 const observer=new MutationObserver(records=>{
  for(const entry of records)for(const removed of entry.removedNodes){
   if(contains(removed,picker)||contains(removed,container))detached++;
   if(contains(removed,firstButton))buttonRemoved++;
   if(contains(removed,mobileButton))mobileRebuilt++;
  }
 });
 observer.observe(document.documentElement,{childList:true,subtree:true});
 picker.focus();
 for(const value of ['#e00000','#dd3300','#c55500','#99aa11','#22bbee','#5511ee']){
  picker.value=value;
  picker.dispatchEvent(new Event('input',{bubbles:true}));
  if(palette[0]!==value||color!==value||gradientAnchors[0].color!==value)throw Error('native picker did not change the active live endpoint: '+value);
  if(!picker.isConnected||container.parentElement!==sw||(!isMobile&&document.activeElement!==picker))throw Error('native colour picker lost focus or was disconnected');
  if(sw.querySelector('button.swatch[data-index="1"]')!==firstButton)throw Error('palette swatches were regenerated');
  if($('mobilePaletteGrid').firstElementChild!==mobileButton)throw Error('mobile palette was regenerated');
 }
 await Promise.resolve();observer.disconnect();
 if(detached||buttonRemoved||mobileRebuilt)throw Error('native picker or swatches detached: '+JSON.stringify({detached,buttonRemoved,mobileRebuilt}));
 // Editing an intermediate stop while its own native picker is open must also
 // retain the input and existing gradient buttons.
 const edit=$('editPaletteSwatch');selectPaletteSwatch(9);edit.focus();
 for(const value of ['#0099ee','#00bbdd','#22ddcc']){
  edit.value=value;edit.dispatchEvent(new Event('input',{bubbles:true}));
  if(palette[9]!==value||gradientAnchors.length!==3)throw Error('live intermediate stop did not update');
  if(!edit.isConnected||(!isMobile&&document.activeElement!==edit)||sw.querySelector('button.swatch[data-index="1"]')!==firstButton)throw Error('edit-stop picker was interrupted');
 }
 // Reuse event handlers correctly after palette-size changes and stop edits.
 setPaletteSize(8);setPaletteSize(48);setPaletteSize(24);
 if(sw.children.length!==24||picker!==$('colorPicker'))throw Error('palette-size change broke picker identity');
 const before=color, target=palette[5];sw.querySelector('button.swatch[data-index="5"]').click();
 if(color!==target||color===before)throw Error('reused swatch click captured stale colour');
 if(!picker.isConnected)throw Error('picker detached on resizing palette');
 return {pickerAttached:true,dragSteps:6,intermediateSteps:3,desktopAndMobileNodesStable:true,paletteSizes:true};
}};
'''
html=html.replace(marker,hook+marker)
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--disable-gpu','--use-gl=angle','--use-angle=swiftshader'])
    for is_mobile in (False,True):
        page=browser.new_page(viewport={'width':390 if is_mobile else 1150,'height':790},is_mobile=is_mobile,has_touch=is_mobile)
        page.route('**/*',lambda route: route.abort() if route.request.url.startswith('http') else route.continue_())
        errors=[]
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        page.set_content(html,wait_until='domcontentloaded',timeout=50000)
        page.wait_for_function('!!window.__testNativeColourPicker180',timeout=20000)
        result=page.evaluate('(mobile)=>window.__testNativeColourPicker180.run(mobile)',is_mobile)
        assert not errors,(result,errors)
        print(('Mobile' if is_mobile else 'Desktop')+' native colour picker PASS '+str(result))
        page.close()
    browser.close()
