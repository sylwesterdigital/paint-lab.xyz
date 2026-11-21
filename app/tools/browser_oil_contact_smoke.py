#!/usr/bin/env python3
"""Optional Chromium pixel regression for Paint Lab live oil contact behaviour.
Run locally after installing playwright and Chromium. Does not require Flask.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
HOOK="""
window.__oilQA={
 points:(tip='round',length=650,lowPressure=false,times=null)=>{
   const cfg={...snapshot(),material:'oil',mode:0,strokeStyle:'none',tip,
      naturalWidth:true,initialWidth:.18,growthDistance:1.3,speedWidth:.08,
      size:85,color:'#ac4c38',strength:1,flow:1,viscosity:.7,
      paintLoad:1,wetness:.4,density:.9,scatter:0,bristleCount:70};
   const points=[];
   for(let i=0;i<=90;i++){
     const q=i/90;
     points.push({x:110+length*q,y:200+Math.sin(q*2.3*Math.PI)*33,
       pressure:lowPressure?(.25+.72*Math.sin(q*Math.PI)):1,
       t:times&&times.length?times[i]:i*5});
   }
   return {cfg,points};
 },
 run:(tip='round',length=650,lowPressure=false,times=null)=>{
   ensureLayer();clearLayer();
   const stroke=window.__oilQA.points(tip,length,lowPressure,times);
   replayStroke({kind:'stroke',cfg:stroke.cfg,points:stroke.points,seed:23});
   return {start:stroke.points[0],end:stroke.points.at(-1)};
 },
 runLive:(tip='round',length=650)=>{
   ensureLayer();clearLayer();
   const stroke=window.__oilQA.points(tip,length,false,null);
   const s={kind:'stroke',cfg:stroke.cfg,points:stroke.points,seed:23};
   s._run=null;s.loadedColor=null;s._invertVisited=null;
   drawStrokeStart(s);
   for(let i=1;i<s.points.length;i++)drawStrokeStep(s,s.points[i]);
   const before=window.__oilQA.widths();
   finishStrokeRender(s);
   const after=window.__oilQA.widths();
   return {before,after};
 },
 widths:()=>{
  const l=activeLayer(),w=l.canvas.width,h=l.canvas.height,d=l.ctx.getImageData(0,0,w,h).data;
  return Array.from({length:68},(_,i)=>{
    const x=110+i*10;let width=0;
    for(let y=0;y<h;y++)if(d[(y*w+x)*4+3]>100)width++;
    return width;
  });
 },
 components:()=>{
  const ctx=activeLayer().ctx,img=ctx.getImageData(90,100,780,280),w=img.width,h=img.height;
  const d=img.data,seen=new Uint8Array(w*h),queue=new Int32Array(w*h);
  let count=0,total=0;
  for(let i=0;i<w*h;i++){
   if(seen[i]||d[i*4+3]<=100)continue;
   count++;let head=0,tail=0;seen[i]=1;queue[tail++]=i;
   while(head<tail){const index=queue[head++];total++;
    const x=index%w,y=(index/w)|0;
    const near=[x>0?index-1:-1,x<w-1?index+1:-1,
       y>0?index-w:-1,y<h-1?index+w:-1];
    for(const n of near)if(n>=0&&!seen[n]&&d[n*4+3]>100){seen[n]=1;queue[tail++]=n;}
   }
  }
  return {count,total};
 }
};
"""
HTML=HTML.replace(
    "window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});",
    HOOK+"\nwindow.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});",
    1,
)

def main():
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
        page=browser.new_page(viewport={'width':1300,'height':840})
        page.on('pageerror',lambda exc:errors.append(str(exc)))
        page.set_content(HTML,wait_until='domcontentloaded',timeout=35000)
        page.wait_for_timeout(450)
        profiles={}
        for tip in ['round','flat','rigger','fan']:
            page.evaluate('(tip)=>__oilQA.run(tip)',tip)
            widths=page.evaluate('__oilQA.widths()')
            components=page.evaluate('__oilQA.components()')
            start=max(widths[:3]);body=max(widths[24:40]);end=max(widths[64:67])
            assert body>0 and start<body*.58,(tip,start,body)
            assert components['count']==1,(tip,components)
            assert components['total']>50,(tip,components)
            profiles[tip]={'touchdown':start,'body':body,'release':end,'connected':components['count']}
        # New live-contact contract: touchdown is tapered, the body stays connected,
        # and finishStrokeRender must not rewrite the beginning after drawing.
        stable=page.evaluate('__oilQA.runLive("round",650)')
        before=max(stable['before'][:3]);after=max(stable['after'][:3])
        assert abs(after-before)<=1,(before,after)
        assert profiles['flat']['release']>=profiles['round']['release']*.8,profiles
        assert profiles['rigger']['body']<profiles['round']['body']*.55,profiles
        page.evaluate('()=>__oilQA.run("round",650,true)')
        pen=page.evaluate('__oilQA.widths()')
        assert max(pen[:3])<profiles['round']['touchdown'],(pen[:3],profiles['round'])
        for length in [3,10,30,60,100,200]:
            page.evaluate('(length)=>__oilQA.run("round",length)',length)
            connected=page.evaluate('__oilQA.components()')
            assert connected['count']==1,(length,connected)
        assert not errors,errors
        browser.close()
        print('PASS: live oil touchdown, stable start after finish, connected body, tip families, pen pressure, short strokes, JS errors')
        print(profiles)

if __name__=='__main__':
    main()
