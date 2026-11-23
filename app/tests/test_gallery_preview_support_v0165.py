"""v0.1.65: public thumbnails, lazy-load contracts, view analytics and Stripe safeguards."""
import hashlib,hmac,io,json,tempfile,time,unittest
from pathlib import Path
from PIL import Image
from backend import public_previews,public_viewer,support_checkout,db
from backend.public_discovery import normalized,search

ROOT=Path(__file__).resolve().parents[1]

class GalleryPreviewAndSupport(unittest.TestCase):
 def test_thumbnail_is_bounded_aspect_correct_and_cached(self):
  with tempfile.TemporaryDirectory() as root:
   src=Path(root)/'art.png';target=public_previews.preview_path(Path(root),'a'*26)
   img=Image.new('RGB',(1600,900),'#b841c3');img.save(src)
   self.assertEqual(public_previews.png_dimensions(src),(1600,900))
   self.assertEqual(public_previews.make_preview(src,target),target)
   with Image.open(target) as thumb:
    self.assertEqual(thumb.format,'WEBP')
    self.assertEqual(thumb.size,(720,405))
   self.assertLess(target.stat().st_size,src.stat().st_size)
   first=target.stat().st_mtime_ns
   public_previews.make_preview(src,target)
   self.assertEqual(target.stat().st_mtime_ns,first)
   with Image.open(src) as original:self.assertEqual(original.size,(1600,900))

 def test_public_markup_keeps_full_image_as_fallback_and_defers_later_tiles(self):
  from html.parser import HTMLParser
  class Images(HTMLParser):
   def __init__(self):super().__init__();self.images=[]
   def handle_starttag(self,tag,attrs):
    if tag=='img':self.images.append(dict(attrs))
  items=[{'title':f'Art {i}','token':'x'*24+str(i),'image':f'/p/{i}/image.png',
          'preview':f'/p/{i}/preview.webp','dimensions':(1200,800),
          'url':f'/p/{i}','artist_url':'/u/Aaartist','username':'Aaartist',
          'created_at':'2026-11-23T00:00:00Z'} for i in range(9)]
  urls={'period':{a:'/explore' for a in ('all','today','week','month')},'prev':None,'next':None}
  markup=public_viewer.discover_markup(items,normalized({}),9,1,urls)
  parser=Images();parser.feed(markup)
  pictures=[img for img in parser.images if 'data-fallback-src' in img]
  self.assertEqual(len(pictures),9)
  self.assertEqual([p['src'] for p in pictures[:4]],[i['preview'] for i in items[:4]])
  for img in pictures[4:]:
   self.assertNotIn('src',img)
   self.assertIn('data-preview-src',img)
   self.assertEqual((img['width'],img['height']),('1200','800'))
  self.assertIn('IntersectionObserver',public_viewer.DISCOVERY_JS)
  self.assertIn('rootMargin:\'450px 0px\'',public_viewer.DISCOVERY_JS)

 def test_download_and_support_does_not_sell_free_download(self):
  slide={'token':'a'*24,'title':'Acrylic','url':'/p/'+'a'*24,'image':'/p/'+'a'*24+'/image.png'}
  markup=public_viewer.viewer_markup([slide],0,'Artist','/u/Artist',csrf='csrf-token')
  self.assertIn('id="artDownloadFile"',markup)
  self.assertIn('download="paint-lab-artwork.png"',markup)
  self.assertIn('Download original PNG',markup)
  self.assertIn('not directly to the artist',markup)
  self.assertIn('data-stripe-dialog-trigger="supportDialog"',markup)
  self.assertIn('data-stripe-dialog',markup)
  self.assertIn('buy-button-id="buy_btn_1UemYTC7wxoTGQU3bmUqn2Yl"',markup)
  self.assertIn('https://donate.stripe.com/4gM6oGbw61Wf5nJa1wcZa0c',markup)
  self.assertIn('data-stripe-status',markup)
  self.assertNotIn('data-support-amount',markup)
  self.assertIn('data-csrf="csrf-token"',markup)
  enabled=public_viewer.viewer_markup([slide],0,'Artist','/u/Artist',support_enabled=True)
  self.assertIn('stripe-buy-button',enabled)
  self.assertIn('Download original PNG',enabled)
  self.assertIn("umami.track('artwork_view'",public_viewer.VIEWER_JS)
  self.assertIn("(window.paintLabArtworkViews||(window.paintLabArtworkViews=[])).push",public_viewer.VIEWER_JS)

 def test_stripe_does_not_accept_client_price_or_return_url(self):
  token='a'*28
  with self.assertRaises(ValueError):support_checkout.checkout_form(token,9999,'https://paint-lab.xyz')
  with self.assertRaises(ValueError):support_checkout.checkout_form(token,'300','https://paint-lab.xyz')
  form=support_checkout.checkout_form(token,500,'https://paint-lab.xyz')
  self.assertEqual(form['line_items[0][price_data][unit_amount]'],'500')
  self.assertEqual(form['line_items[0][price_data][currency]'],'gbp')
  self.assertEqual(form['metadata[publication_token]'],token)
  self.assertEqual(form['success_url'],f'https://paint-lab.xyz/p/{token}?support=returned')

 def test_stripe_hmac_validation_rejects_forgery_and_stale_timestamp(self):
  raw=json.dumps({'data':{'object':{'id':'cs_test_foobar'}},'type':'checkout.session.completed'}).encode()
  now=int(time.time());secret='whsec_just-a-test'
  sig=hmac.new(secret.encode(),str(now).encode()+b'.'+raw,hashlib.sha256).hexdigest()
  self.assertEqual(support_checkout.signed_event(raw,f't={now},v1={sig}',secret,now=now)['type'],'checkout.session.completed')
  with self.assertRaises(ValueError):support_checkout.signed_event(raw+b'garbage',f't={now},v1={sig}',secret,now=now)
  with self.assertRaises(ValueError):support_checkout.signed_event(raw,f't={now},v1={sig}',secret,now=now+400)
  with self.assertRaises(ValueError):support_checkout.signed_event(raw,'t=bad,v1=xx',secret,now=now)

 def test_sqlite_receipts_idempotent_and_visibility_query_unchanged(self):
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/'db.sqlite';db.init(path)
   with db.connect(path) as con:
    uid=con.execute("INSERT INTO users(username,password_hash) VALUES('ArtistOne','x')").lastrowid
    con.execute("INSERT INTO publications(token,owner_id,title,file_name,is_visible) VALUES(?,?,?,?,0)",('x'*28,uid,'Hidden','hidden.png'))
    con.execute("INSERT OR IGNORE INTO support_payments(session_id,publication_token,amount_pence,currency) VALUES('cs_test_token','xxxxx',500,'gbp')")
    con.execute("INSERT OR IGNORE INTO support_payments(session_id,publication_token,amount_pence,currency) VALUES('cs_test_token','xxxxx',500,'gbp')")
    self.assertEqual(con.execute('SELECT COUNT(*) FROM support_payments').fetchone()[0],1)
    self.assertEqual(search(con,normalized({}))[1],0)

 def test_app_routes_keep_visibility_and_signed_webhook_guards(self):
  s=(ROOT/'backend/app.py').read_text()
  for marker in ("@app.get('/p/<token>/preview.webp')","@app.get('/api/publications/<token>/preview.webp')",
    "WHERE token=? AND is_visible=1","WHERE token=? AND owner_id=?",
    "@app.post('/api/support/checkout')","@app.post('/api/stripe/webhook')",
    'require_csrf()','support_checkout.signed_event','INSERT OR IGNORE INTO support_payments'):
   self.assertIn(marker,s)

if __name__=='__main__':unittest.main()
