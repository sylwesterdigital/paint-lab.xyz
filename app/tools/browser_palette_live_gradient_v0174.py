#!/usr/bin/env python3
"""Chromium: edited intermediate stops immediately rebuild the palette; no reset on Gradients re-click."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
MARKER='})();\n</script></body></html>'
assert HTML.count(MARKER)==1
HOOK=r'''
window.__liveGradient174={run(){
 paletteSize=24;
 const original=Array.from({length:24},(_,i)=>'#'+((i*310001+0x151515)&0xffffff).toString(16).padStart(6,'0'));
 original[0]='#ff0000';original[23]='#101010';
 setPalette(original,'Custom');
 modifyPalette('Gradients');
 if(paletteName!=='Gradients'||gradientAnchors.length!==2||palette[0]!=='#ff0000'||palette.at(-1)!=='#101010')throw Error('gradient activation failed');
 const baseline=palette.slice();
 selectPaletteSwatch(9);editSelectedPaletteSwatch('#00ccff');
 if(paletteName!=='Gradients'||gradientAnchors.length!==3||palette[9]!=='#00ccff')throw Error('first live middle stop failed');
 if(palette[8]===baseline[8]||palette[10]===baseline[10])throw Error('neighbours did not update immediately');
 const cyanNeighbours=[palette[8],palette[10]];
 selectPaletteSwatch(17);editSelectedPaletteSwatch('#ffe100');
 if(gradientAnchors.length!==4||palette[9]!=='#00ccff'||palette[17]!=='#ffe100'||palette[0]!=='#ff0000'||palette[23]!=='#101010')throw Error('second stop reset another anchor');
 if(palette[10]===cyanNeighbours[1]&&palette[16]===baseline[16])throw Error('segments did not update');
 const multi=palette.slice(),anchors=JSON.stringify(gradientAnchors);
 modifyPalette('Gradients');
 if(JSON.stringify(palette)!==JSON.stringify(multi)||JSON.stringify(gradientAnchors)!==anchors)throw Error('clicking Gradients resets manual stops');
 // Recolour the first endpoint without affecting intermediate anchors.
 selectPaletteSwatch(0);editSelectedPaletteSwatch('#8800ff');
 if(palette[0]!=='#8800ff'||palette[9]!=='#00ccff'||palette[17]!=='#ffe100')throw Error('editing first stop damaged middle stops');
 // The custom picker must use the same live gradient behaviour.
 selectPaletteSwatch(0);updateColor('#5511aa');
 if(palette[0]!=='#5511aa'||palette[9]!=='#00ccff')throw Error('native first picker did not live update');
 selectPaletteSwatch(23);editSelectedPaletteSwatch('#ffffff');
 if(palette[23]!=='#ffffff'||palette[9]!=='#00ccff'||palette[17]!=='#ffe100')throw Error('editing last stop reset middle');
 // Preserve anchors when changing the number of displayed swatches.
 const beforeResize=JSON.stringify(gradientAnchors);
 setPaletteSize(8);
 if(palette.length!==8||JSON.stringify(gradientAnchors)!==beforeResize||palette[0]!=='#5511aa'||palette.at(-1)!=='#ffffff')throw Error('XL discarded anchors');
 setPaletteSize(48);
 if(palette.length!==48||JSON.stringify(gradientAnchors)!==beforeResize)throw Error('S discarded anchors');
 setPaletteSize(24);
 if(palette[9]!=='#00ccff'||palette[17]!=='#ffe100')throw Error('M did not recover edited colours');
 // A simple selection is not an edit and must not change stop positions or colours.
 const savedStops=JSON.stringify(gradientAnchors),selected=palette[10];
 document.querySelector('#swatches .swatch[data-index="10"]').click();
 if(JSON.stringify(gradientAnchors)!==savedStops||color!==selected)throw Error('select mutated gradient stops');
 // Restore the actual saved workspace state, including stop metadata.
 const saved=currentSettings();
 if(saved.gradientAnchors.length!==4)throw Error('settings do not serialize stops');
 setPalette(PALETTES.Studio,'Studio');
 applySettings(saved);
 if(paletteName!=='Gradients'||palette[9]!=='#00ccff'||palette[17]!=='#ffe100'||palette[23]!=='#ffffff'||JSON.stringify(gradientAnchors)!==savedStops)throw Error('workspace restore lost gradient stops');
 // Removing a middle stop must update intermediate colours and keep other anchors.
 const left=palette[9];toggleGradientAnchor(9);
 if(gradientAnchors.length!==3||palette[9]===left||palette[17]!=='#ffe100')throw Error('remove stop failed');
 toggleGradientAnchor(9);
 if(gradientAnchors.length!==4)throw Error('add stop failed');
 return {version:'0.1.74',stops:gradientAnchors.length,selected:color,recolour:true,resizing:true,restored:true};
}};
'''
HTML=HTML.replace(MARKER,HOOK+MARKER)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--disable-gpu','--use-gl=angle','--use-angle=swiftshader'])
 for mobile in (False,True):
  page=browser.new_page(viewport={'width':390 if mobile else 1160,'height':780},is_mobile=mobile,has_touch=mobile)
  page.route('**/*',lambda route: route.abort() if route.request.url.startswith('http') else route.continue_())
  errors=[];page.on('pageerror',lambda error: errors.append(str(error)))
  page.set_content(HTML,wait_until='domcontentloaded',timeout=50000)
  page.wait_for_function('!!window.__liveGradient174',timeout=20000)
  result=page.evaluate('()=>window.__liveGradient174.run()')
  assert result['restored'] and result['resizing'] and not errors,(result,errors)
  print(('Mobile' if mobile else 'Desktop')+' live multistop gradient PASS '+str(result))
  page.close()
 browser.close()
