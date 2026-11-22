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
.art-foot{flex:none;display:flex;align-items:center;justify-content:space-between;gap:14px;min-height:34px;font-size:12px;color:#a9b8b1}
.art-foot .art-counter{font-variant-numeric:tabular-nums;min-width:54px}
.art-foot .art-hint{flex:1;text-align:center}
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
  const counter = document.getElementById('artCounter');
  const download = document.getElementById('artDownload');
  const stage = document.getElementById('artStage');
  const prev = document.getElementById('artPrev');
  const next = document.getElementById('artNext');
  const total = slides.length;
  let index = Math.min(total - 1, Math.max(0, Number(root.dataset.index) || 0));
  const at = i => (i + total) % total;
  const currentPath = () => window.location.pathname;
  const indexForPath = () => slides.findIndex(slide => slide.url === currentPath());
  function show(i, push = true) {
    index = at(i);
    const item = slides[index];
    image.src = item.image;
    image.alt = item.title;
    title.textContent = item.title;
    counter.textContent = (index + 1) + ' / ' + total;
    download.href = item.image;
    download.setAttribute('download', 'paint-lab-artwork.png');
    document.title = item.title + ' · Paint Lab';
    if (push && currentPath() !== item.url) history.pushState({paintLabPublicSlide: true}, '', item.url);
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


def viewer_markup(slides: list[dict], active: int, username: str, space_path: str) -> str:
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
        f'<p>By <a href="{escape(space_path)}">{escape(username)}</a> · Public artwork</p>'
        '</div>'
        f'<a class="gallery-link" href="{escape(space_path)}">All artworks</a>'
        '</header>'
        '<section class="art-stage" id="artStage" aria-label="Published artwork preview">'
        f'<img id="artImage" src="{escape(item["image"])}" alt="{escape(item["title"])}" draggable="false">'
        f'<button type="button" class="art-arrow prev" id="artPrev" aria-label="Previous artwork"{controls}>‹</button>'
        f'<button type="button" class="art-arrow next" id="artNext" aria-label="Next artwork"{controls}>›</button>'
        '</section>'
        '<footer class="art-foot">'
        f'<span class="art-counter" id="artCounter" aria-live="polite">{active+1} / {len(slides)}</span>'
        f'<span class="art-hint">{hint}</span>'
        f'<a class="download" id="artDownload" href="{escape(item["image"])}" download="paint-lab-artwork.png">Download PNG</a>'
        '</footer></main>'
    )
