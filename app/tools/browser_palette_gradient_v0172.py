#!/usr/bin/env python3
"""Chromium regression: palette swatch editing must not overwrite gradient start."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML = (Path(__file__).resolve().parents[1] / 'frontend/index.html').read_text()
MARKER = '})();\n</script></body></html>'
assert HTML.count(MARKER) == 1
HOOK = r'''
window.__palette172={run(){
 paletteSize=24;
 const colors=Array.from({length:24},(_,i)=>rgbHex([24+i*2,60+i*3,82+i*4]));
 colors[0]='#123456';colors[10]='#bb2211';colors[23]='#1234dd';
 setPalette(colors,'Custom');
 const start=palette[0],before=palette.slice();
 const select=document.querySelector('#swatches .swatch[data-index="10"]');
 select.click();
 if(selectedPaletteIndex!==10||color!==before[10])throw Error('swatch selection failed');
 if(palette[0]!==start||paletteSource[0]!==start)throw Error('clicking swatch overwrote first gradient stop');
 editSelectedPaletteSwatch('#27aabb');
 if(palette[0]!==start||paletteSource[0]!==start)throw Error('editing middle swatch overwrote first gradient stop');
 if(palette[10]!=='#27aabb'||paletteSource[10]!=='#27aabb'||color!=='#27aabb')throw Error('middle swatch edit failed');
 if(palette[23]!==before[23])throw Error('editing middle changed last stop');
 document.querySelector('#swatches .swatch[data-index="23"]').click();
 editSelectedPaletteSwatch('#ff7722');
 if(palette[0]!==start||palette[23]!=='#ff7722'||color!=='#ff7722')throw Error('last stop edit changed first stop or active paint');
 if($('currentColor').style.background!== 'rgb(18, 52, 86)' || $('colorPicker').value!==start)throw Error('first custom swatch UI was overwritten');
 const prior=palette.slice();
 modifyPalette('Gradients');
 if(palette[0]!==start||palette.at(-1)!=='#ff7722')throw Error('gradient ignored independent selected endpoints');
 if(palette[1]===prior[1]&&palette[2]===prior[2])throw Error('gradient not generated');
 const paletteAfter=palette.slice();
 selectPaletteSwatch(0);editSelectedPaletteSwatch('#993322');
 if(palette[0]!=='#993322'||palette[23]!==paletteAfter[23])throw Error('first stop edit changed other stops');
 // The paint colour and the first saved gradient stop are distinct when restoring settings.
 const state=currentSettings();
 if(state.paletteSource[0]!=='#993322')throw Error('wrong saved first swatch');
 selectPaletteSwatch(8);updateColor(palette[8],false);
 const stored=currentSettings();
 if(stored.paletteSource[0]!=='#993322'||stored.color!==palette[8])throw Error('save incorrectly synchronised active colour and first stop');
 setPalette(['#abcdef',...stored.paletteSource.slice(1)],'Temp');
 applySettings(stored);
 if(palette[0]!=='#993322'||color!==stored.color)throw Error('restoring settings modified independent palette colours');
 return {start:palette[0],end:palette.at(-1),active:color,middle:palette[8],preserved:true};
}};
'''
HTML = HTML.replace(MARKER, HOOK + MARKER)
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--disable-gpu', '--use-gl=angle', '--use-angle=swiftshader'])
    for mobile in (False, True):
        page = browser.new_page(viewport={'width':390 if mobile else 1160,'height':780},is_mobile=mobile,has_touch=mobile)
        page.route('**/*', lambda route: route.abort() if route.request.url.startswith('http') else route.continue_())
        errors=[]
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(HTML, wait_until='domcontentloaded', timeout=50000)
        page.wait_for_function('!!window.__palette172', timeout=20000)
        result = page.evaluate('()=>window.__palette172.run()')
        assert result['preserved'] and result['start']=='#993322' and not errors,(result, errors)
        print(('Mobile' if mobile else 'Desktop')+' Palette v0.1.72 regression PASS '+str(result))
        page.close()
    browser.close()
