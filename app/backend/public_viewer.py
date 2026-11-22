"""Accessible, CSP-restricted public artwork viewer with full-height image fitting.

The viewer operates on published PNGs only. Slide data contains public titles,
publication tokens and same-origin routes, never private projects or credentials.
"""
from __future__ import annotations

import html
import json

BASE_CSS = '''
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:#15191a;color:#f1f3ef;font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:#b5d7cc;text-decoration:none}a:hover{text-decoration:underline}
button{font:inherit}button:focus-visible,a:focus-visible{outline:3px solid #b4d3ac;outline-offset:3px}
nav{display:flex;align-items:center;gap:18px;min-height:54px;padding:11px max(18px,env(safe-area-inset-right)) 11px max(18px,env(safe-area-inset-left));background:#202727;border-bottom:1px solid #34403f}
nav a{font-weight:700}nav span{color:#a1aba8;font-size:13px}
main{max-width:1120px;margin:26px auto;padding:0 20px 32px}
main h1{font-size:clamp(20px,3vw,29px);line-height:1.25;overflow-wrap:anywhere}
/* A fluid, column-based masonry wall: real PNG proportions determine each tile's height.
   Unlike fixed thumbnail boxes, no artwork is cropped, stretched, or letterboxed. */
.gallery-page main{max-width:none;width:100%;margin:0 auto;padding:clamp(20px,2.6vw,42px) clamp(12px,2.1vw,38px) 56px}
.gallery-page main h1{font-size:clamp(24px,2.8vw,38px);margin:0 0 clamp(18px,2.2vw,30px)}
.gallery{columns:280px;column-gap:clamp(12px,1.3vw,20px)}
.gallery .card{display:inline-block;vertical-align:top;width:100%;margin:0 0 clamp(12px,1.3vw,20px);break-inside:avoid;page-break-inside:avoid}
.card{min-width:0;border:1px solid #33403f;background:#222b2b;border-radius:13px;overflow:hidden}
.card a{display:block;color:#f1f3ef}
.card img{display:block;width:100%;height:auto;max-width:100%;aspect-ratio:auto;object-fit:contain;background:#303939}
.card h2{font-size:14px;font-weight:620;margin:11px 13px 13px;overflow-wrap:anywhere}
.card:hover{border-color:#698880}
.gallery-lead{color:#b9c4bf;margin-bottom:22px}
@media(max-width:480px){.gallery{columns:1}.gallery-page main{padding:18px 12px 40px}.gallery-page main h1{margin-bottom:16px}.gallery .card{margin-bottom:14px}}
'''

# The cross-artist discovery wall is public, server-rendered and works without JS.
DISCOVER_CSS = r'''
.discover-page nav{gap:18px;flex-wrap:wrap}
.discover-page main.discover-main,.gallery-page main.discover-main{max-width:none;width:100%;margin:0;padding:clamp(18px,3vw,44px) clamp(12px,3vw,48px) 70px}
.discovery-hero{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:18px;margin-bottom:25px}
.discovery-kicker{font-size:11px;color:#a7cab7;font-weight:780;letter-spacing:.14em;text-transform:uppercase}
.discover-page main h1,.gallery-page main.discover-main h1{font-size:clamp(30px,5vw,56px);letter-spacing:-.045em;line-height:1.05;margin:6px 0 9px}
.discovery-subtitle{color:#b2c0bb;margin:0;max-width:550px}
.community-invite{display:flex;align-items:center;gap:12px;justify-content:space-between;max-width:420px;border:1px solid #52655b;background:linear-gradient(135deg,#293c35,#202a28);border-radius:18px;padding:15px 18px}
.community-invite strong{display:block;font-size:15px}
.community-invite span{display:block;font-size:12px;color:#bacbc0;margin-top:2px}
.community-invite a{flex:none;white-space:nowrap;border-radius:11px;background:#b2d7a5;color:#17251b;padding:10px 13px;font-weight:750;font-size:13px}
.discovery-filters{border:1px solid #354440;background:#202726;border-radius:18px;padding:15px;margin:0 0 18px}
.discovery-quick{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:14px}
.discovery-chip{border:1px solid #475951;border-radius:100px;padding:7px 14px;font-size:13px;color:#d1ddd5}
.discovery-chip[aria-current=page]{color:#112419;background:#add4a3;border-color:#add4a3;font-weight:700}
.discovery-form{display:grid;grid-template-columns:minmax(170px,2fr) minmax(120px,1fr) repeat(2,minmax(120px,.75fr)) auto;align-items:end;gap:10px}
.discovery-form label{display:flex;flex-direction:column;gap:5px;font-size:12px;color:#aebbb5;font-weight:600}
.discovery-form input,.discovery-form select{width:100%;min-width:0;padding:11px 12px;min-height:43px;border-radius:10px;border:1px solid #52605c;background:#151b1a;color:#f0f6f1;font:inherit;font-size:14px;color-scheme:dark}
.discovery-form button{border:0;background:#add4a3;color:#102118;border-radius:10px;min-height:43px;padding:0 19px;font-weight:740;cursor:pointer}
.discovery-form button:hover,.community-invite a:hover{background:#c9e8c1;text-decoration:none}
.discovery-meta{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px;color:#aab7b0;font-size:13px;margin:15px 0}
.discovery-meta a{color:#bbd9c9}
.discovery-wall{columns:270px;column-gap:clamp(11px,1.5vw,22px)}
.discovery-tile{break-inside:avoid;display:inline-block;width:100%;margin-bottom:clamp(11px,1.5vw,22px);overflow:hidden;border-radius:14px;border:1px solid #31423b;background:#202a26;vertical-align:top}
.discovery-tile .artwork-link{display:block;position:relative;color:#fff}
.discovery-tile img{display:block;width:100%;height:auto;object-fit:contain;max-width:100%;background:#28302d}
.discovery-tile .discovery-caption{display:block;position:relative;padding:10px 12px 4px;font-weight:680;font-size:14px;overflow-wrap:anywhere}
.discovery-tile:hover{border-color:#94bc9f;transform:translateY(-2px);transition:transform .15s,border-color .15s}
.discovery-artist{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:0 12px 10px;font-size:12px;color:#b7c5bc}
.discovery-artist a{color:#b6d6bb;font-weight:650}
.discovery-artist time{color:#879a90;font-variant-numeric:tabular-nums}
.discovery-empty{text-align:center;margin:7vh auto;padding:34px;max-width:460px;border:1px solid #39473e;border-radius:16px;color:#b8c7ba}
.discovery-pager{display:flex;justify-content:center;align-items:center;gap:15px;margin:24px auto}
.discovery-pager a{padding:10px 17px;border:1px solid #52645a;border-radius:11px}
@media(max-width:850px){.discovery-form{grid-template-columns:repeat(2,minmax(0,1fr))}.discovery-form .discovery-search{grid-column:1/-1}}
@media(max-width:500px){.discovery-form{grid-template-columns:repeat(2,minmax(0,1fr))}.discovery-form button{grid-column:1/-1}.discovery-wall{columns:1}.community-invite{width:100%;max-width:none}.discovery-hero{gap:18px}}
@media(prefers-reduced-motion:reduce){.discovery-tile:hover{transform:none}}
'''


def discover_markup(items, filters, total, page, urls, *, artist=None, edit=False, is_owner=False, csrf="", gallery_url=None):
    """One public discovery page. All untrusted text is HTML-escaped."""
    escape=lambda value: html.escape(str(value),quote=True)
    chips=''.join('<a class="discovery-chip" href="'+escape(urls['period'][name])+'"'+
       (' aria-current="page"' if filters.period==name else '')+'>'+label+'</a>'
       for name,label in [('all','All art'),('today','Today'),('week','Past 7 days'),('month','Past 30 days')])
    sorts=[('recent','Newest first'),('oldest','Oldest first'),('az','Title A–Z'),
           ('za','Title Z–A'),('artist','Artist A–Z')]
    options=''.join('<option value="'+key+'"'+(' selected' if filters.sort==key else '')+'>'+escape(label)+'</option>' for key,label in sorts)
    def card(item):
        visible=item.get('visible',True)
        token=escape(item.get('token',''))
        title=escape(item['title'])
        img='<img src="'+escape(item['image'])+'" loading="lazy" decoding="async" alt="'+title+'">'
        main=('<a class="artwork-link" href="'+escape(item['url'])+'">'+img+
              '<span class="discovery-caption">'+title+'</span></a>') if visible else (
              '<div class="artwork-link">'+img+'<span class="discovery-caption">'+title+'</span></div>')
        controls=''
        if edit:
            controls=('<div class="owner-controls"><span class="visibility-label">'+('Public' if visible else 'Hidden from public')+'</span>'
                '<button type="button" data-visibility="'+token+'" data-next="'+('0' if visible else '1')+'">'+('Hide' if visible else 'Show')+'</button>'
                '<button type="button" class="danger" data-remove="'+token+'">Remove</button></div>')
        return ('<article class="discovery-tile'+(' owner-hidden' if not visible else '')+'" data-publication="'+token+'">'
            +main+'<div class="discovery-artist"><a href="'+escape(item['artist_url'])+'">@'+escape(item['username'])+'</a>'
            '<time datetime="'+escape(str(item['created_at'])[:10])+'">'+escape(str(item['created_at'])[:10])+'</time></div>'
            +controls+'</article>')
    cards=''.join(card(item) for item in items)
    pager = ''
    if total > 48:
        pager = '<div class="discovery-pager" aria-label="Art page navigation">'
        if urls.get('prev'):
            pager += '<a href="'+escape(urls['prev'])+'">← Previous</a>'
        pager += '<span>Page '+str(page)+' / '+str(max(1,(total+47)//48))+'</span>'
        if urls.get('next'):
            pager += '<a href="'+escape(urls['next'])+'">Next →</a>'
        pager += '</div>'
    heading = ('<div class="discovery-kicker">Artist gallery · Paint Lab</div><h1>@'+escape(artist)+'</h1>'
        '<p class="discovery-subtitle">'+('Manage public and hidden artworks. Hide is reversible; Remove deletes permanently.' if edit else 'Published artworks by this artist.')+'</p>') if artist else (
        '<div class="discovery-kicker">Discover · Paint Lab</div><h1>Art from everyone.</h1>'
        '<p class="discovery-subtitle">A public gallery of paintings shared by the community. Explore, find artists, and start creating.</p>')
    owner_link=('<a class="owner-edit-link" href="'+escape(gallery_url)+('?edit=1' if not edit else '')+'">'+
        ('View public gallery' if edit else 'Edit my gallery')+'</a>') if is_owner and gallery_url else ''
    invite=('' if artist else '<aside class="community-invite"><div><strong>Make art together</strong><span>Talk about ideas, share a link and find collaborators on Rantlist.</span></div>'
        '<a href="https://rantlist.me/" target="_blank" rel="noopener noreferrer">Join the conversation</a></aside>')
    action='/u/'+escape(artist) if artist else '/explore'
    edit_field='<input type="hidden" name="edit" value="1">' if edit else ''
    return ('<main class="discover-main" id="publicDiscovery"'+(' data-csrf="'+escape(csrf)+'"' if edit else '')+'>' +
      '<header class="discovery-hero"><div>'+heading+owner_link+'</div>'+invite+'</header>'
      '<section class="discovery-filters" aria-label="Find public artworks"><div class="discovery-quick">'+chips+'</div>'
      '<form class="discovery-form" action="'+action+'" method="get">'+edit_field+
      '<input type="hidden" name="period" value="'+escape(filters.period)+'">'
      '<label class="discovery-search" for="discoverQuery">Search title or artist<input id="discoverQuery" type="search" name="q" maxlength="100" placeholder="Search art or artist…" value="'+escape(filters.q)+'"></label>'
      '<label for="discoverSort">Sort by<select id="discoverSort" name="sort">'+options+'</select></label>'
      '<label for="discoverFrom">From date<input id="discoverFrom" type="date" name="from" value="'+escape(filters.date_from)+'"></label>'
      '<label for="discoverTo">To date<input id="discoverTo" type="date" name="to" value="'+escape(filters.date_to)+'"></label>'
      '<button type="submit">Show artworks</button></form></section>'
      '<div class="discovery-meta"><span><strong>'+str(total)+'</strong> '+('artworks including hidden' if edit else 'published '+('artwork' if total==1 else 'artworks'))+' · Page '+str(page)+'</span>'
      '<a href="'+action+('?edit=1' if edit else '')+'">Clear filters</a></div>'
      +('<div class="discovery-wall">'+cards+'</div>' if items else '<div class="discovery-empty"><strong>No matching artwork yet.</strong><p>Try a different search or date range, or create something new.</p><a href="/">Open Paint Lab</a></div>')+
      pager+'</main>')

VIEWER_CSS = '''
body.viewer-page{height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
.viewer-page nav{flex:none}
.viewer-page main{flex:1;min-height:0;min-width:0;width:100%;max-width:none;margin:0;padding:12px clamp(10px,2.4vw,32px) max(12px,env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:10px}
.art-head{flex:none;display:flex;justify-content:space-between;align-items:center;gap:12px;min-height:54px}
.art-head h1{font-size:clamp(17px,2.7vw,23px);margin:0 0 3px;line-height:1.3;max-width:70vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.art-head p{color:#b4c1bb;font-size:12px;margin:0}
.gallery-link{flex:none;display:inline-flex;align-items:center;padding:8px 12px;border:1px solid #495755;border-radius:9px;font-size:13px}
.art-stage{position:relative;flex:1;min-height:0;min-width:0;display:flex;align-items:center;justify-content:center;background:#0b0f10;border:1px solid #2f3b39;border-radius:10px;overflow:hidden;touch-action:pan-y;overscroll-behavior:contain}
.art-stage img{display:block;max-width:100%;max-height:100%;width:100%;height:100%;object-fit:contain;object-position:center;background:transparent;border-radius:0;user-select:none;-webkit-user-drag:none;pointer-events:none}
.art-arrow{position:absolute;top:50%;transform:translateY(-50%);display:flex;align-items:center;justify-content:center;width:52px;height:60px;padding:0;border:1px solid #ffffff44;border-radius:12px;background:#182120cf;color:#fff;font-size:30px;line-height:1;cursor:pointer;z-index:2;backdrop-filter:blur(6px)}
.art-arrow:hover{background:#324640f0}.art-arrow.prev{left:12px}.art-arrow.next{right:12px}
.art-arrow[hidden]{display:none}
.art-foot{flex:none;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px;min-height:34px;font-size:12px;color:#a9b8b1}
.art-foot .art-counter{font-variant-numeric:tabular-nums;min-width:54px}
.art-foot .art-hint{flex:1;text-align:center}
.art-foot .community-link{flex:none;color:#b5d7cc;padding:8px;font-weight:650}
.art-foot .download{flex:none;display:inline-flex;align-items:center;justify-content:center;padding:8px 12px;border:1px solid #566966;border-radius:9px;font-weight:650}
@media(max-width:620px){
  .viewer-page nav{min-height:48px;padding-top:8px;padding-bottom:8px}
  .viewer-page main{gap:8px;padding:8px 7px max(9px,env(safe-area-inset-bottom))}
  .art-head{min-height:47px;padding:0 7px}
  .art-head h1{max-width:58vw;font-size:16px}
  .art-head p{font-size:11px}
  .gallery-link{padding:7px 9px;font-size:11px}
  .art-stage{border-radius:4px}
  .art-arrow{width:44px;height:54px;font-size:26px;border-radius:10px}
  .art-arrow.prev{left:5px}.art-arrow.next{right:5px}
  .art-foot{padding:0 5px;gap:8px}
  .art-foot .art-hint{font-size:11px}
  .art-foot .download{font-size:11px;padding:7px 9px}
}
@media(max-height:500px){.viewer-page main{gap:4px;padding-top:4px;padding-bottom:4px}.art-head{min-height:34px}.viewer-page nav{min-height:40px;padding-top:5px;padding-bottom:5px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important}}
'''

# Code is static and invoked using a one-time CSP nonce; no executable user data.
VIEWER_JS = r'''(() => {
  'use strict';
  const root = document.getElementById('publicViewer');
  if (!root) return;
  const slides = JSON.parse(root.dataset.slides || '[]');
  if (!slides.length) return;
  const image = document.getElementById('artImage');
  const title = document.getElementById('artTitle');
  const creator = document.getElementById('artCreator');
  const counter = document.getElementById('artCounter');
  const download = document.getElementById('artDownload');
  const stage = document.getElementById('artStage');
  const prev = document.getElementById('artPrev');
  const next = document.getElementById('artNext');
  const total = slides.length;
  let index = Math.min(total - 1, Math.max(0, Number(root.dataset.index) || 0));
  const at = i => (i + total) % total;
  const currentPath = () => window.location.pathname;
  const indexForPath = () => slides.findIndex(slide => slide.url.split('?')[0] === currentPath());
  function show(i, push = true) {
    index = at(i);
    const item = slides[index];
    image.src = item.image;
    image.alt = item.title;
    title.textContent = item.title;
    if (creator && item.username && item.artist_url) { creator.textContent = item.username; creator.href = item.artist_url; }
    counter.textContent = (index + 1) + ' / ' + total;
    download.href = item.image;
    download.setAttribute('download', 'paint-lab-artwork.png');
    document.title = item.title + ' · Paint Lab';
    if (push && currentPath() !== item.url.split('?')[0]) history.pushState({paintLabPublicSlide: true}, '', item.url);
    if (total > 1) {
      const adjacent = new Image();
      adjacent.src = slides[at(index + 1)].image;
    }
  }
  const move = step => { if (total > 1) show(index + step); };
  prev.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  window.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.defaultPrevented) return;
    if (['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)) return;
    if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
  });
  window.addEventListener('popstate', () => {
    const target = indexForPath();
    if (target >= 0) show(target, false);
    else window.location.reload();
  });
  // Use passive touch events for iOS/Android; normal vertical scrolling is not blocked.
  let start = null;
  stage.addEventListener('touchstart', event => {
    start = event.touches.length === 1 && !event.target.closest('button,a')
      ? {x: event.touches[0].clientX, y: event.touches[0].clientY}
      : null;
  }, {passive: true});
  stage.addEventListener('touchcancel', () => { start = null; }, {passive: true});
  stage.addEventListener('touchend', event => {
    if (!start || !event.changedTouches.length || event.touches.length) { start = null; return; }
    const dx = event.changedTouches[0].clientX - start.x;
    const dy = event.changedTouches[0].clientY - start.y;
    start = null;
    if (Math.abs(dx) >= Math.max(45, Math.min(90, stage.clientWidth * .12)) && Math.abs(dx) > Math.abs(dy) * 1.3) {
      move(dx < 0 ? 1 : -1);
    }
  }, {passive: true});
  show(index, false);
})();'''



def gallery_markup(items: list[dict], username: str) -> str:
    """An uncropped public gallery: original PNG dimensions determine tile height.

    Only public URLs and titles are exposed; escaped attributes and text prevent
    stored artwork titles and account names from becoming HTML.
    """
    escape = lambda val: html.escape(str(val), quote=True)
    heading = f'<h1>{escape(username)} · Public artworks</h1>'
    if not items:
        return '<main class="gallery-main" id="publicGallery">' + heading + '<p>No artworks have been published yet.</p></main>'
    cards = ''.join(
        '<article class="card"><a href="' + escape(item['url']) + '">'
        '<img loading="lazy" decoding="async" src="' + escape(item['image']) +
        '" alt="' + escape(item['title']) + '">'
        '<h2>' + escape(item['title']) + '</h2></a></article>'
        for item in items
    )
    return '<main class="gallery-main" id="publicGallery">' + heading + '<div class="gallery">' + cards + '</div></main>'


def viewer_markup(slides: list[dict], active: int, username: str, space_path: str, *, gallery_url: str | None = None) -> str:
    """Build the page for public paintings by one artist, newest first."""
    if not slides or not 0 <= active < len(slides):
        raise ValueError('Viewer requires a published active artwork')
    item = slides[active]
    escape = lambda val: html.escape(str(val), quote=True)
    # HTML attribute escaping prevents titles/URLs from escaping into arbitrary markup.
    slide_data = escape(json.dumps(slides, ensure_ascii=True, separators=(',', ':')))
    controls = '' if len(slides) > 1 else ' hidden'
    hint = 'Swipe or use ← → to browse' if len(slides) > 1 else 'Published artwork'
    return (
        f'<main class="artwork-viewer" id="publicViewer" data-slides="{slide_data}" data-index="{active}">'
        '<header class="art-head"><div>'
        f'<h1 id="artTitle">{escape(item["title"])}</h1>'
        f'<p>By <a id="artCreator" href="{escape(space_path)}">{escape(username)}</a> · Public artwork</p>'
        '</div>'
        f'<a class="gallery-link" href="{escape(gallery_url or space_path)}">All artworks</a>'
        '</header>'
        '<section class="art-stage" id="artStage" aria-label="Published artwork preview">'
        f'<img id="artImage" src="{escape(item["image"])}" alt="{escape(item["title"])}" draggable="false">'
        f'<button type="button" class="art-arrow prev" id="artPrev" aria-label="Previous artwork"{controls}>‹</button>'
        f'<button type="button" class="art-arrow next" id="artNext" aria-label="Next artwork"{controls}>›</button>'
        '</section>'
        '<footer class="art-foot">'
        f'<span class="art-counter" id="artCounter" aria-live="polite">{active+1} / {len(slides)}</span>'
        f'<span class="art-hint">{hint}</span>'
        '<a class="community-link" href="https://rantlist.me/" target="_blank" rel="noopener noreferrer">Discuss art</a>'
        f'<a class="download" id="artDownload" href="{escape(item["image"])}" download="paint-lab-artwork.png">Download PNG</a>'
        '</footer></main>'
    )


MANAGE_CSS = r'''
.owner-edit-link{display:inline-block;margin-top:14px;background:#b0d7a7;color:#183023;padding:10px 17px;border-radius:10px;font-weight:750}
.owner-hidden{opacity:.82;border-style:dashed}
.owner-hidden img{filter:grayscale(.55)}
.owner-controls{display:flex;align-items:center;gap:7px;padding:7px 11px 12px;flex-wrap:wrap}
.owner-controls .visibility-label{flex:1;font-size:12px;color:#b9c8be;min-width:65px}
.owner-controls button{border:1px solid #627c6a;background:#2c4036;border-radius:8px;color:#eff6ed;padding:8px 10px;font-weight:700;cursor:pointer}
.owner-controls button:hover{background:#41604d}
.owner-controls button.danger{border-color:#8b5f5f;background:#422f30}
.owner-controls button.danger:hover{background:#623c3c}
.owner-controls button:disabled{opacity:.5;cursor:wait}
.gallery-page main.discover-main{max-width:none;padding:clamp(18px,3vw,44px) clamp(12px,3vw,48px) 70px}
.gallery-page .discovery-hero h1{font-size:clamp(27px,4.2vw,50px);letter-spacing:-.03em;margin:5px 0 9px}
'''

MANAGE_JS = r'''
(()=>{
 const gallery=document.getElementById('publicDiscovery');
 if(!gallery)return;
 const csrf=gallery.dataset.csrf;
 gallery.addEventListener('click',async event=>{
   const button=event.target.closest('button[data-visibility],button[data-remove]');
   if(!button)return;
   const token=button.dataset.visibility||button.dataset.remove;
   if(!/^[A-Za-z0-9_-]{20,80}$/.test(token))return;
   const remove=button.hasAttribute('data-remove');
   const visible=button.dataset.next==='1';
   if(remove&&!confirm('Permanently remove this publication? Its public link will stop working.'))return;
   const card=button.closest('[data-publication]');
   card.querySelectorAll('button').forEach(b=>b.disabled=true);
   try{
     const response=await fetch('/api/publications/'+encodeURIComponent(token),{
       method:remove?'DELETE':'PATCH',credentials:'same-origin',
       headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},
       body:JSON.stringify(remove?{}:{visible})
     });
     if(!response.ok){const problem=await response.json().catch(()=>({}));throw Error(problem.error||'Could not update artwork');}
     // Refresh filtered result counts, dates, sort order and the visibility badge.
     window.location.reload();
   }catch(error){alert(error.message);card.querySelectorAll('button').forEach(b=>b.disabled=false);}
 });
})();
'''
