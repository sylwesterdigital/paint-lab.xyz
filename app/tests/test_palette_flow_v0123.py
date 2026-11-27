"""Palette size, movement-only colour cycling and persistence contracts."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
HTML = (APP / 'frontend/index.html').read_text()


class PaletteFlowTests(unittest.TestCase):
    def test_size_selector_and_compact_flow_toggle(self):
        for n in (8, 24, 48):
            self.assertIn(f'data-palette-size="{n}"', HTML)
        self.assertIn('id="paletteTravel"', HTML)
        self.assertIn('function resizePaletteColours(source,count)', HTML)
        self.assertIn('function setPaletteSize(next,persist=true)', HTML)

    def test_colour_is_snapshotted_and_shared_across_pigment_engines(self):
        self.assertIn('travelPalette:colorTravel?palette.slice():undefined', HTML)
        self.assertIn('const travelledColor=strokeTravelColour(c,progress);', HTML)
        self.assertIn('const colour=hexToRgb(strokeTravelColour(c,0))', HTML)
        self.assertIn('const nextColour=strokeTravelColour(c,(run.pathLength||0)+travel*q)', HTML)
        self.assertIn('paintTextStamp(s,x,y,radius,angle,rng,opacity,travelledColor)', HTML)
        self.assertIn('paletteSource:[...paletteSource],paletteSize,paletteName,colorTravel,colorTravelPingPong,color', HTML)
        self.assertIn('paletteSource:paletteSource.slice(),paletteSize,paletteName,gradientAnchors:gradientAnchors.map(a=>({...a}))', HTML)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for standalone colour-function tests')
    def test_actual_colour_algorithms(self):
        # Evaluate the same pure functions shipped in the release. Do not test
        # separately reimplemented Python algorithms.
        segments = [
            HTML[HTML.index('function colourToLab('):HTML.index('function interpolateGradient(')],
            HTML[HTML.index('function resizePaletteColours('):HTML.index('function setPalette(colors,name,options={})')],
        ]
        script = r'''
        const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
        const hexToRgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
        const rgbHex=rgb=>'#'+rgb.map(v=>clamp(Math.round(v),0,255).toString(16).padStart(2,'0')).join('');
        ''' + '\n'.join(segments) + r'''
        const original=Array.from({length:24},(_,i)=>rgbHex([(i*43)%256,(i*91)%256,(i*13)%256]));
        const medium=resizePaletteColours(original,24);
        const big=resizePaletteColours(original,8);
        const small=resizePaletteColours(original,48);
        if(medium.length!==24||big.length!==8||small.length!==48)throw Error('wrong palette size');
        if(JSON.stringify(medium)!==JSON.stringify(original))throw Error('24 colours mutated');
        if(big[0]!==original[0]||big[7]!==original[23])throw Error('endpoints moved');
        if(!small.every(x=>/^#[0-9a-f]{6}$/.test(x)))throw Error('bad generated hex');
        const cfg={color:'#112233',colorTravel:true,size:50,travelPalette:['#112233','#445566','#778899']};
        if(strokeTravelColour(cfg,0)!=='#112233')throw Error('wrong start');
        if(strokeTravelColour(cfg,14.99)!=='#112233')throw Error('changed without enough travel');
        if(strokeTravelColour(cfg,15)!=='#445566')throw Error('failed to change after moving');
        if(strokeTravelColour(cfg,30)!=='#778899')throw Error('failed second movement step');
        if(strokeTravelColour(cfg,45)!=='#112233')throw Error('failed to cycle');
        cfg.colorTravel=false;
        if(strokeTravelColour(cfg,200)!=='#112233')throw Error('toggle disabled but colour changed');
        console.log('PALETTE_FLOW_ALGORITHMS_OK');
        '''
        proc = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=12)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('PALETTE_FLOW_ALGORITHMS_OK', proc.stdout)

    def test_project_version_consistency(self):
        for name in ('version.json', 'frontend/version.json', 'changelog.json', 'frontend/changelog.json'):
            self.assertEqual(json.loads((APP / name).read_text())['version'], '0.1.81')
