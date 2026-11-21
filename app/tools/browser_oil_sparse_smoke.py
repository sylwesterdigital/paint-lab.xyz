#!/usr/bin/env python3
"""Chromium pixel QA for the v0.1.30 sparse-sample oil engine.

Proves new oil strokes have continuous pigment despite a single long pointer
jump, and verifies legacy project strokes retain their old rendering path.
No Flask, internet, network services or third-party brush code needed.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
HOOK="""
window.__oilSparseQA={
 run:(tip='rigger',legacy=false)=>{
  baseW=3700;baseH=480;resize();ensureLayer();clearLayer();
  const cfg={...snapshot(),material:'oil',mode:0,strokeStyle:'none',tip,
    naturalWidth:true,initialWidth:.18,growthDistance:1.3,speedWidth:.08,
    size:85,color:'#ac4c38',strength:1,flow:1,viscosity:.7,
    paintLoad:1,wetness:.4,density:.9,scatter:0,bristleCount:70};
  if(legacy)delete cfg.oilSamplingEngine;
  const pts=[{x:110,y:220,pressure:.4,t:0},{x:3310,y:220,pressure:1,t:600}];
  replayStroke({kind:'stroke',cfg,points:pts,seed:23});
  const l=activeLayer(),w=l.canvas.width,h=l.canvas.height,d=l.ctx.getImageData(0,0,w,h).data;
  let hit=0,n=0,maxGap=0,gap=0;
  for(let x=125;x<3290;x+=4){n++;
   let present=false;
   const center=Math.round(220*dpr),column=Math.round(x*dpr);
   for(let oy=-Math.round(35*dpr);oy<=Math.round(35*dpr);oy++){
    const y=center+oy;
    if(y>=0&&y<h&&d[(y*w+column)*4+3]>60){present=true;break;}
   }
   if(present){hit++;maxGap=Math.max(maxGap,gap);gap=0;}else gap++;
  }
  return {hit,n,maxGap,dpr,version:cfg.oilSamplingEngine||'legacy'};
 }
};
"""
needle="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert needle in HTML
HTML=HTML.replace(needle,HOOK+'\n'+needle,1)

def main():
  errors=[]
  with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    results=[]
    for dpr in (1,1.5):
      page=browser.new_page(viewport={'width':1250,'height':800},device_scale_factor=dpr)
      page.on('pageerror',lambda error:errors.append(str(error)))
      page.set_content(HTML,wait_until='domcontentloaded',timeout=35000)
      for tip in ('rigger','round','flat'):
        result=page.evaluate('(t)=>__oilSparseQA.run(t)',tip)
        assert result['hit']/result['n']>.98,(dpr,tip,result)
        assert result['maxGap']==0,(dpr,tip,result)
        results.append((tip,dpr,result['hit'],result['n']))
      if dpr==1:
        legacy=page.evaluate('()=>__oilSparseQA.run("rigger",true)')
        assert legacy['hit']/legacy['n']<.72,legacy
      page.close()
    assert not errors,errors
    browser.close()
  print('PASS: sparse oil strokes continuous across sample jumps at 1× and 1.5× DPR, legacy history preserved, no JS exceptions')
  print(results)

if __name__=='__main__':main()
