"""The viewer handoff must always identify the active public artwork, never post it."""
from __future__ import annotations
import json,unittest
from html.parser import HTMLParser
from urllib.parse import parse_qs,urlsplit
from backend import public_viewer

class Tags(HTMLParser):
 def __init__(self):super().__init__();self.by_id={}
 def handle_starttag(self,tag,attrs):
  fields=dict(attrs)
  if 'id' in fields:self.by_id[fields['id']]=(tag,fields)

class DiscussArtHandoffTests(unittest.TestCase):
 def slides(self):
  return [dict(token=token,title=title,url='/p/'+token+'?browse=explore&page=1',image='/p/'+token+'/image.png',preview='/p/'+token+'/preview.webp')
          for token,title in [('A'*28,'First "<Paint>" & more'),('B'*28,'Second painting'),('C'*28,'Third')]]
 def test_initial_handoff_is_only_a_published_token_and_a_new_tab(self):
  markup=public_viewer.viewer_markup(self.slides(),1,'Sample Artist','/u/artist')
  tags=Tags();tags.feed(markup)
  tag,attr=tags.by_id['artDiscuss']
  self.assertEqual(tag,'a')
  parsed=urlsplit(attr['href']);query=parse_qs(parsed.query)
  self.assertEqual((parsed.scheme,parsed.netloc,parsed.path),('https','rantlist.me','/'))
  self.assertEqual(query,{'room':['lobby'],'paintLabPublication':['B'*28]})
  self.assertEqual(attr['target'],'_blank')
  self.assertIn('noopener',attr['rel'])
  self.assertNotIn('Second painting',attr['href'])
  self.assertNotIn('image.png',attr['href'])
  self.assertEqual(tags.by_id['artDiscussStatus'][1].get('hidden'),None)
  self.assertEqual(tags.by_id['artImage'][1]['src'],'/p/'+'B'*28+'/preview.webp')
  self.assertEqual(json.loads(tags.by_id['publicViewer'][1]['data-slides']),self.slides())
 def test_dynamic_navigation_links_to_shown_item_and_manual_fallback(self):
  js=public_viewer.VIEWER_JS
  for text in ("url.searchParams.set('paintLabPublication',item.token)",
               "url.searchParams.set('room','lobby')",'discuss.href=rantlistIntent(item);',
               "const item=slides[index];", "navigator.clipboard.writeText(text)",
               "image.src = item.preview || item.image;","adjacent.src = slides[at(index + 1)].preview || slides[at(index + 1)].image;",
               "No message was posted.","show(target, false)","move(dx < 0 ? 1 : -1)",
               "history.pushState", "discuss.addEventListener('click'", "status(false)"):
   self.assertIn(text,js)
  self.assertNotIn('fetch(',js)
  self.assertNotIn('innerHTML',js)
 def test_spec_explicitly_requires_confirmation_and_real_image_bubble(self):
  from pathlib import Path
  spec=(Path(__file__).resolve().parents[1]/'docs/RANTLIST_DISCUSS_ART_SPEC_v2.md').read_text()
  for text in ('medium-sized native image bubble','Nothing is posted on opening the link',
               'image.png','paintLabPublication','authenticated Rantlist user',
               'same* native medium-image pipeline'):
   self.assertIn(text,spec)
if __name__=='__main__':unittest.main()
