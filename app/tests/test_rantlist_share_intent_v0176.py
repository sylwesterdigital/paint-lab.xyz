"""v0.1.77: publishing must give Rantlist the same public token as viewer Discuss art."""
import json,re,unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from backend import public_viewer

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()

class Tags(HTMLParser):
 def __init__(self):super().__init__();self.by_id={}
 def handle_starttag(self,tag,attrs):
  fields=dict(attrs)
  if fields.get('id'):self.by_id[fields['id']]=(tag,fields)

class RantlistShareIntent(unittest.TestCase):
 def test_new_tab_link_in_both_publish_dialogs(self):
  tags=Tags();tags.feed(HTML)
  for field in ('saveRantlistShare','shareRantlistShare'):
   tag,attrs=tags.by_id[field]
   self.assertEqual(tag,'a')
   self.assertEqual(attrs['target'],'_blank')
   self.assertIn('noopener',attrs['rel'])
   self.assertIn('noreferrer',attrs['rel'])
   self.assertIn('btn',attrs['class'])
  self.assertIn("$('saveRantlistShare').href=intent;",HTML)
  self.assertIn("$('shareRantlistShare').href=intent;",HTML)
  self.assertIn('const intent=rantlistDiscussionURL(link)',HTML)
  self.assertIn('function prepareRantlistHandoff(',HTML)
  self.assertNotIn('window.open(RANTLIST_HOME',HTML)
  self.assertNotIn('sharePublishedToRantlist',HTML)

 def test_safe_url_uses_publication_id_not_working_title_or_image_url(self):
  self.assertIn("intent.searchParams.set('room','lobby');",HTML)
  self.assertIn("intent.searchParams.set('paintLabPublication',token);",HTML)
  self.assertIn("/^\\/p\\/[A-Za-z0-9_-]{20,80}$/",HTML)
  self.assertIn("String(result.token||'')!==new URL(link).pathname.slice(3)",HTML)
  slides=[dict(token='ylXJE8AVgDG25bf6ubJKZxL78hI',title='Test',url='/p/ylXJE8AVgDG25bf6ubJKZxL78hI',image='/p/ylXJE8AVgDG25bf6ubJKZxL78hI/image.png')]
  page=public_viewer.viewer_markup(slides,0,'artist','/u/artist')
  tags=Tags();tags.feed(page)
  query=parse_qs(urlsplit(tags.by_id['artDiscuss'][1]['href']).query)
  self.assertEqual(query,{'room':['lobby'],'paintLabPublication':['ylXJE8AVgDG25bf6ubJKZxL78hI']})

 def test_no_automatic_post_and_bot_remains_separate(self):
  self.assertIn('no message was posted.',HTML)
  self.assertIn('const RANTLIST_HOME=',HTML)
  self.assertIn("@app.post('/api/publications/<token>/share/rantlist')",(APP/'backend/app.py').read_text())
  self.assertEqual(json.loads((APP/'version.json').read_text())['version'],'0.1.77')
  self.assertTrue((APP/'docs/RANTLIST_DISCUSS_ART_ACTION_v3.md').is_file())

if __name__=='__main__':unittest.main()
