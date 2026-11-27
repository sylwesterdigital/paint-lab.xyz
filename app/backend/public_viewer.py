"""Accessible, CSP-restricted public artwork viewer with full-height image fitting.

The viewer operates on published PNGs only. Slide data contains public titles,
publication tokens and same-origin routes, never private projects or credentials.
"""
from __future__ import annotations

import html
import json
from urllib.parse import urlencode

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
/* Desktop keeps every filter visible. Mobile has one intentional reveal control. */
.discovery-mobile-controls{display:none}
.discovery-desktop-controls{display:block}
.discovery-mobile-invite,.discovery-more-label{display:none}
.discovery-mobile-invite{border:1px solid #40584b;border-radius:12px;background:#24352d;padding:12px 14px;align-items:center;justify-content:space-between;gap:10px}
.discovery-mobile-invite span{font-size:12px;color:#bbcec0}
.discovery-mobile-invite a{font-size:12px;font-weight:750;color:#bce1b5;white-space:nowrap}
@media(max-width:850px){.discovery-form{grid-template-columns:repeat(2,minmax(0,1fr))}.discovery-form .discovery-search{grid-column:1/-1}}
@media(max-width:500px){
 .discover-page nav{min-height:48px;gap:12px;padding:8px 14px}.discover-page nav span{display:none}
 .discover-page main.discover-main{padding:11px 10px 32px}
 .discover-page .discovery-hero{margin:0 0 11px;gap:0}
 .discover-page .discovery-kicker,.discover-page .discovery-subtitle,.discover-page .discovery-hero .community-invite{display:none}
 .discover-page main.discover-main h1{font-size:clamp(23px,7vw,28px);letter-spacing:-.035em;margin:0;line-height:1.18}
 .discover-page .discovery-filters{border:0;background:transparent;padding:0;margin:0 0 8px}
 .discover-page .discovery-desktop-controls{display:none}
 .discover-page .discovery-mobile-controls{display:block;margin:0}
 .discover-page .discovery-mobile-controls>summary{display:flex;align-items:center;gap:9px;min-height:44px;padding:9px 13px;background:#242f2b;border:1px solid #4c6155;border-radius:12px;color:#e2f0e7;font-weight:680;font-size:13px;cursor:pointer;list-style:none;user-select:none}
 .discover-page .discovery-mobile-controls>summary::-webkit-details-marker{display:none}
 .discover-page .discovery-mobile-controls>summary svg{flex:none;width:19px;height:19px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
 .discover-page .discovery-mobile-controls>summary .discovery-filter-arrow{margin-left:auto;transition:transform .18s}
 .discover-page .discovery-mobile-controls[open]>summary .discovery-filter-arrow{transform:rotate(180deg)}
 .discover-page .discovery-mobile-controls:not([open])>.discovery-search-body{display:none}
 .discover-page .discovery-search-body{padding:12px 2px 3px}
 .discover-page .discovery-quick{flex-wrap:nowrap;overflow-x:auto;padding-bottom:5px;margin-bottom:11px;scrollbar-width:thin}
 .discover-page .discovery-chip{white-space:nowrap;flex:none;padding:6px 12px;font-size:12px}
 .discover-page .discovery-form{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
 .discover-page .discovery-form button{grid-column:1/-1}
 .discover-page .discovery-meta{font-size:12px;margin:9px 2px 12px;gap:6px}
 .discover-page .discovery-meta .discovery-page-number{display:none}
 .discover-page .discovery-wall{columns:1}
 .discover-page .discovery-wall.discovery-featured-mode{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;align-items:start}
 .discover-page .discovery-featured-mode>.discovery-tile{margin:0;display:block}
 .discover-page .discovery-featured-mode>.discovery-tile:nth-of-type(-n+4) img{aspect-ratio:1/1;object-fit:contain;max-height:none}
 .discover-page .discovery-featured-mode>.discovery-tile:nth-of-type(-n+4) .artwork-link{position:relative}
 .discover-page .discovery-featured-mode>.discovery-tile:nth-of-type(-n+4) .discovery-caption{position:absolute;bottom:0;left:0;right:0;padding:26px 9px 8px;color:white;background:linear-gradient(transparent,#121b17dc);font-size:12px;line-height:1.2;white-space:nowrap;text-overflow:ellipsis;overflow:hidden}
 .discover-page .discovery-featured-mode>.discovery-tile:nth-of-type(-n+4) .discovery-artist{padding:5px 9px 7px;font-size:11px}
 .discover-page .discovery-featured-mode>.discovery-tile:nth-of-type(-n+4) time{display:none}
 .discover-page .discovery-featured-mode>.discovery-tile:nth-of-type(n+5){grid-column:1/-1}
 .discover-page .discovery-featured-mode>.discovery-more-label{grid-column:1/-1;display:block;margin:8px 0 0;color:#d6e4d9;font-weight:750;font-size:17px}
 .discover-page .discovery-wall>.discovery-mobile-invite{display:flex}
 .discover-page .discovery-featured-mode>.discovery-mobile-invite{grid-column:1/-1}
 .discover-page .discovery-wall:not(.discovery-featured-mode)>.discovery-tile{margin-bottom:11px}
}
@media(max-width:360px){.discover-page .discovery-featured-mode>.discovery-tile:nth-of-type(-n+4) .discovery-artist{padding:4px 6px 6px}}

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
    featured=(not artist and page==1 and filters.sort=='recent' and filters.period=='all' and not filters.q and not filters.date_from and not filters.date_to)
    def card(item,index):
        visible=item.get('visible',True)
        token=escape(item.get('token',''))
        title=escape(item['title'])
        # First four tiles paint immediately; the rest request compressed previews
        # only as they approach the viewport. Width/height reserve the correct
        # uncropped height while the image is deferred.
        eager=index<4
        src=escape(item.get('preview',item['image']))
        fallback=escape(item['image'])
        dims=item.get('dimensions',(1,1))
        try: width,height=int(dims[0]),int(dims[1])
        except (TypeError,ValueError,IndexError):width,height=1,1
        sizes=' width="'+str(max(1,width))+'" height="'+str(max(1,height))+'"'
        priority=' loading="eager" fetchpriority="high"' if eager else ' loading="lazy"'
        img=('<img'+(' src="'+src+'"' if eager else ' data-preview-src="'+src+'"')+
             ' data-fallback-src="'+fallback+'"'+priority+' decoding="async"'+sizes+' alt="'+title+'">')
        if not eager: img+='<noscript><img src="'+src+'" loading="lazy" alt="'+title+'"></noscript>'
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
    cards=''
    for i,item in enumerate(items):
        if featured and i==4:
            cards+=('<aside class="discovery-mobile-invite"><span>Make art together</span>'
                    '<a href="https://rantlist.me/" target="_blank" rel="noopener noreferrer">Discuss & collaborate ↗</a></aside>'
                    '<h2 class="discovery-more-label">More artwork</h2>')
        cards+=card(item,i)
    if not artist and (not featured or len(items)<=4):
        cards+=('<aside class="discovery-mobile-invite"><span>Make art together</span>'
                '<a href="https://rantlist.me/" target="_blank" rel="noopener noreferrer">Discuss & collaborate ↗</a></aside>')
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
    filters_body=('<div class="discovery-search-body"><div class="discovery-quick">'+chips+'</div>'
      '<form class="discovery-form" action="'+action+'" method="get">'+edit_field+
      '<input type="hidden" name="period" value="'+escape(filters.period)+'">'
      '<label class="discovery-search" for="discoverQuery">Search title or artist<input id="discoverQuery" type="search" name="q" maxlength="100" placeholder="Search art or artist…" value="'+escape(filters.q)+'"></label>'
      '<label for="discoverSort">Sort by<select id="discoverSort" name="sort">'+options+'</select></label>'
      '<label for="discoverFrom">From date<input id="discoverFrom" type="date" name="from" value="'+escape(filters.date_from)+'"></label>'
      '<label for="discoverTo">To date<input id="discoverTo" type="date" name="to" value="'+escape(filters.date_to)+'"></label>'
      '<button type="submit">Show artworks</button></form></div>')
    active_filters=bool(filters.q or filters.period!='all' or filters.sort!='recent' or filters.date_from or filters.date_to)
    filter_title=('Search & filters · Active' if active_filters else 'Search art & filters')
    filter_summary=('<summary aria-label="Search and filter artworks">'
      '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.7" cy="10.7" r="6.7"/><path d="m16 16 5 5"/></svg>'
      '<span>'+filter_title+'</span>'
      '<svg class="discovery-filter-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
      '</summary>')
    # Two *presentation-only* responsive forms preserve a no-JavaScript mobile disclosure
    # without collapsing desktop layout or hiding owner-gallery editing controls.
    # Both forms submit the same validated GET arguments to the same public endpoint.
    def mobile_ids(fragment):
        for base in ('discoverQuery','discoverSort','discoverFrom','discoverTo'):
            fragment=fragment.replace('id="'+base+'"','id="'+base+'Mobile"')
            fragment=fragment.replace('for="'+base+'"','for="'+base+'Mobile"')
        return fragment
    filters_panel=(('<div class="discovery-desktop-controls">'+filters_body+'</div>'
         '<details class="discovery-mobile-controls">'+filter_summary+mobile_ids(filters_body)+'</details>')
        if not artist else filters_body)
    meta=('<div class="discovery-meta"><span><strong>'+str(total)+'</strong> '+
      ('artworks including hidden' if edit else 'published '+('artwork' if total==1 else 'artworks'))+
      ' <span class="discovery-page-number">· Page '+str(page)+'</span></span>'+
      ('<a href="'+action+('?edit=1' if edit else '')+'">Clear filters</a>' if active_filters or page>1 else '')+'</div>')
    return ('<main class="discover-main" id="publicDiscovery"'+(' data-csrf="'+escape(csrf)+'"' if edit else '')+'>' +
      '<header class="discovery-hero"><div>'+heading+owner_link+'</div>'+invite+'</header>'
      '<section class="discovery-filters" aria-label="Find public artworks">'+filters_panel+'</section>'+meta+
      ('<div class="discovery-wall'+(' discovery-featured-mode' if featured else '')+'">'+cards+'</div>' if items else '<div class="discovery-empty"><strong>No matching artwork yet.</strong><p>Try a different search or date range, or create something new.</p><a href="/">Open Paint Lab</a></div>')+
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
.art-discuss-status{flex:0 0 100%;font-size:11px;color:#b7cbc2;line-height:1.4;padding:0 6px 3px}
.art-discuss-status[hidden]{display:none}
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
.support-dialog{border:1px solid #52665c;border-radius:18px;background:#202925;color:#f2f5f1;padding:0;width:min(460px,calc(100vw - 28px));max-height:calc(100dvh - 28px);box-shadow:0 20px 80px #0008}
.support-dialog::backdrop{background:#060b09c9}
.support-content{padding:23px;display:flex;flex-direction:column;gap:16px}
.support-top{display:flex;align-items:center;justify-content:space-between;gap:14px}
.support-top h2{margin:0;font-size:22px}
.support-close{width:38px;height:38px;border:1px solid #587367;background:#2b3a33;border-radius:10px;color:white;display:grid;place-items:center;font-size:23px;cursor:pointer}
.support-description{margin:0;color:#b9cbc1;font-size:14px}
.support-download{display:flex;align-items:center;justify-content:center;padding:13px;border-radius:10px;background:#b0d6a7;color:#142419;font-weight:750}
.support-divider{height:1px;background:#44594e}
.support-dialog .stripe-donation-embed{display:flex;justify-content:center;min-height:55px;max-width:100%}
.support-dialog .stripe-donation-status{font-size:12px;color:#b9cbc1;line-height:1.45;margin:0}
.support-dialog .stripe-donation-fallback{font-size:13px;color:#b5d7cc;text-decoration:underline;text-underline-offset:3px;text-align:center}
.support-dialog .stripe-donation-embed stripe-buy-button{display:block;max-width:100%}
@media(max-width:620px){.support-content{padding:18px}}
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
  const download = document.getElementById('artDownloadFile');
  const supportDialog=document.getElementById('supportDialog');
  const supportOpen=document.getElementById('artDownload');
  const discuss=document.getElementById('artDiscuss');
  const discussStatus=document.getElementById('artDiscussStatus');
  const rantlistIntent=item=>{
    const url=new URL('https://rantlist.me/');
    url.searchParams.set('room','lobby');
    url.searchParams.set('paintLabPublication',item.token);
    return url.href;
  };
  const stage = document.getElementById('artStage');
  const prev = document.getElementById('artPrev');
  const next = document.getElementById('artNext');
  const total = slides.length;
  let index = Math.min(total - 1, Math.max(0, Number(root.dataset.index) || 0));
  const at = i => (i + total) % total;
  const currentPath = () => window.location.pathname;
  const indexForPath = () => slides.findIndex(slide => slide.url.split('?')[0] === currentPath());
  let lastViewed='';
  let viewsSent=0;
  function recordView(item){
    if(item.token===lastViewed || viewsSent>=24)return;
    lastViewed=item.token; viewsSent++;
    if(window.umami && typeof window.umami.track==='function'){
      try{window.umami.track('artwork_view',{publication:item.token});}catch(e){}
    }else{(window.paintLabArtworkViews||(window.paintLabArtworkViews=[])).push(item.token);}
  }
  function show(i, push = true) {
    index = at(i);
    const item = slides[index];
    image.src = item.preview || item.image;
    image.alt = item.title;
    title.textContent = item.title;
    if (creator && item.username && item.artist_url) { creator.textContent = item.username; creator.href = item.artist_url; }
    counter.textContent = (index + 1) + ' / ' + total;
    download.href = item.image;
    download.setAttribute('download', 'paint-lab-artwork.png');
    supportOpen.dataset.publication=item.token;
    // Context follows arrows, swipes and browser back/forward, not the entry artwork.
    discuss.href=rantlistIntent(item);
    discuss.setAttribute('aria-label','Discuss '+item.title+' in Rantlist #lobby');
    if(discussStatus){discussStatus.hidden=true;discussStatus.textContent='';}
    recordView(item);
    document.title = item.title + ' · Paint Lab';
    if (push && currentPath() !== item.url.split('?')[0]) history.pushState({paintLabPublicSlide: true}, '', item.url);
    if (total > 1) {
      const adjacent = new Image();
      adjacent.src = slides[at(index + 1)].preview || slides[at(index + 1)].image;
    }
  }
  const move = step => { if (total > 1) show(index + step); };
  prev.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  window.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.defaultPrevented) return;
    if(supportDialog?.open || ['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)) return;
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
  // Until Rantlist supports paintLabPublication share intents, copy the exact
  // public artwork link for a manual #lobby post. Do not silently publish.
  discuss.addEventListener('click',()=>{
    const item=slides[index];
    const publicUrl='https://paint-lab.xyz/p/'+item.token;
    const text='Discuss this Paint Lab artwork: '+item.title+'\n'+publicUrl;
    const status=copied=>{
      if(!discussStatus)return;
      discussStatus.textContent=copied
        ? 'Artwork link copied. If Rantlist does not show a draft, paste it into #lobby. No message was posted.'
        : 'Rantlist needs the image-draft integration. Copy this artwork URL to post it manually in #lobby.';
      discussStatus.hidden=false;
    };
    if(navigator.clipboard?.writeText){
      navigator.clipboard.writeText(text).then(()=>status(true)).catch(()=>status(false));
    }else status(false);
    // Allow the native target=_blank anchor navigation to proceed synchronously.
  });
  download.addEventListener('click',()=>{
    const item=slides[index];
    if(window.umami&&typeof window.umami.track==='function')try{window.umami.track('artwork_download',{publication:item.token})}catch(e){}
  });
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
        '<img loading="lazy" decoding="async" src="' + escape(item.get('preview',item['image'])) +
        '" data-fallback-src="' + escape(item['image']) + '" alt="' + escape(item['title']) + '">'
        '<h2>' + escape(item['title']) + '</h2></a></article>'
        for item in items
    )
    return '<main class="gallery-main" id="publicGallery">' + heading + '<div class="gallery">' + cards + '</div></main>'


def viewer_markup(slides: list[dict], active: int, username: str, space_path: str, *, gallery_url: str | None = None, support_enabled=False, csrf="") -> str:
    """Build the page for public paintings by one artist, newest first."""
    if not slides or not 0 <= active < len(slides):
        raise ValueError('Viewer requires a published active artwork')
    item = slides[active]
    # The no-JS link also identifies the exact active publication. Rantlist
    # currently needs a compatible share-intent receiver to use the parameter.
    discuss_url='https://rantlist.me/?'+urlencode({'room':'lobby','paintLabPublication':item['token']})
    escape = lambda val: html.escape(str(val), quote=True)
    # HTML attribute escaping prevents titles/URLs from escaping into arbitrary markup.
    slide_data = escape(json.dumps(slides, ensure_ascii=True, separators=(',', ':')))
    controls = '' if len(slides) > 1 else ' hidden'
    hint = 'Swipe or use ← → to browse' if len(slides) > 1 else 'Published artwork'
    return (
        f'<main class="artwork-viewer" id="publicViewer" data-slides="{slide_data}" data-index="{active}" data-csrf="{escape(csrf)}" data-support-enabled="{1 if support_enabled else 0}">'
        '<header class="art-head"><div>'
        f'<h1 id="artTitle">{escape(item["title"])}</h1>'
        f'<p>By <a id="artCreator" href="{escape(space_path)}">{escape(username)}</a> · Public artwork</p>'
        '</div>'
        f'<a class="gallery-link" href="{escape(gallery_url or space_path)}">All artworks</a>'
        '</header>'
        '<section class="art-stage" id="artStage" aria-label="Published artwork preview">'
        f'<img id="artImage" src="{escape(item.get("preview",item["image"]))}" alt="{escape(item["title"])}" draggable="false">'
        f'<button type="button" class="art-arrow prev" id="artPrev" aria-label="Previous artwork"{controls}>‹</button>'
        f'<button type="button" class="art-arrow next" id="artNext" aria-label="Next artwork"{controls}>›</button>'
        '</section>'
        '<footer class="art-foot">'
        f'<span class="art-counter" id="artCounter" aria-live="polite">{active+1} / {len(slides)}</span>'
        f'<span class="art-hint">{hint}</span>'
        f'<a class="community-link" id="artDiscuss" href="{escape(discuss_url)}" target="_blank" rel="noopener noreferrer" aria-label="Discuss this artwork in Rantlist #lobby">Discuss art</a>'
        '<span class="art-discuss-status" id="artDiscussStatus" role="status" aria-live="polite" hidden></span>' 
        '<button type="button" class="download" id="artDownload" data-stripe-dialog-trigger="supportDialog" aria-haspopup="dialog">Download &amp; support</button>'
        '</footer>'
        '<dialog class="support-dialog" id="supportDialog" data-stripe-dialog aria-labelledby="supportTitle"><div class="support-content">'
        '<div class="support-top"><h2 id="supportTitle">Download &amp; support</h2><button type="button" class="support-close" id="supportClose" data-stripe-dialog-close aria-label="Close">×</button></div>'
        '<p class="support-description">Download the original artwork for free, or optionally support Paint Lab.</p>'
        f'<a class="support-download" id="artDownloadFile" href="{escape(item["image"])}" download="paint-lab-artwork.png">Download original PNG</a>'
        '<div class="support-divider"></div>'
        '<strong>Support the Paint Lab project</strong>'
        '<p class="support-description">Contributions go to Paint Lab, not directly to the artist. Artist payouts would require a separate Stripe Connect programme.</p>'
        '<div class="stripe-donation-embed" aria-label="Stripe donation button">'
        '<stripe-buy-button buy-button-id="buy_btn_1UemYTC7wxoTGQU3bmUqn2Yl" publishable-key="pk_live_51OS1fPC7wxoTGQU3jLPCJmKrEOZ03kLdBpCyRKcE1DRj9xKHNdIWNbAAwMFLsi0s9cyUGw9BdYQzYDmFbsNacsrx00KDuQKgna"></stripe-buy-button>'
        '</div>'
        '<p class="stripe-donation-status" data-stripe-status role="status">Donations are optional. Stripe checkout may open a separate secure page.</p>'
        '<a class="stripe-donation-fallback" href="https://donate.stripe.com/4gM6oGbw61Wf5nJa1wcZa0c" target="_blank" rel="noopener noreferrer">Open secure Stripe donation page</a>'
        '</div></dialog></main>'
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


# Avoid downloading full-resolution PNGs in masonry feeds. The first four previews
# are eagerly requested; remaining WebPs begin at most 450px before entering view.
DISCOVERY_JS = r"""(()=>{
  'use strict';
  const root=document.getElementById('publicDiscovery');
  if(!root)return;
  const images=[...root.querySelectorAll('img[data-preview-src]')];
  const load=img=>{if(img.dataset.previewSrc){img.src=img.dataset.previewSrc;delete img.dataset.previewSrc;}};
  const missing=img=>{
    const fallback=img.dataset.fallbackSrc;
    if(fallback&&img.src!==new URL(fallback,location.href).href){img.src=fallback;}
  };
  for(const img of root.querySelectorAll('img[data-fallback-src]')){
    img.addEventListener('error',()=>missing(img),{once:true});
  }
  if(!('IntersectionObserver' in window)){images.forEach(load);return;}
  const observer=new IntersectionObserver(entries=>{
    entries.forEach(entry=>{if(entry.isIntersecting){load(entry.target);observer.unobserve(entry.target);}});
  },{rootMargin:'450px 0px',threshold:0});
  images.forEach(img=>observer.observe(img));
})();"""
