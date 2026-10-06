"""Offline fixtures; do not represent live feedback or adapter approval."""
import copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import heard as h

class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.plan={'product':'Fixture product','confirmed':True,'sources':[{'id':'a','family':'portal','adapter':'manual','path':'a.json','permission':'approved','permission_evidence':'Fixture only'},{'id':'b','family':'reviews','adapter':'manual','path':'b.json','permission':'approved','permission_evidence':'Fixture only'}]}
        h.save(self.root/'a.json',[{'text':'Export blocks my work </script><script>alert(1)</script>','url':'https://example.com/1','date':'2026-01-01','author':'Do not store'}]);h.save(self.root/'b.json',[{'text':'Please add export','url':'https://example.org/2'},{'text':'Please add export','url':'https://example.org/3'}]);h.save(self.root/'plan.json',self.plan)
        self.c=h.collect(self.root/'plan.json');ids=[r['id'] for r in self.c['records']]
        self.a={'brief':'Fixture strategy','blind_spots':['Synthetic data'], 'assignments':[{'record_id':i,'theme_ids':['t1'],'intensity':2,'rationale':'Stated friction'} for i in ids], 'themes':[{'id':'t1','title':'Export','verdict':'Watch','review_status':'proposed','reasoning':'Validate','beneficiary':'Unknown','cost':'Unknown','displaces':'Unknown','counterevidence':'None in fixture','next_test':'Interview','quotes':[{'record_id':ids[0],'text':'Export blocks my work'}]}]}
    def tearDown(self): self.tmp.cleanup()
    def test_pipeline(self):
        self.assertEqual(len(self.c['records']),2); self.assertEqual(len(self.c['duplicates']),1)
        self.assertNotIn('author',self.c['records'][0]);r=h.build(self.c,self.a,self.root/'report.html');self.assertEqual(r['themes'][0]['count'],2);self.assertEqual(r['family_count'],2)
        self.assertNotIn('</script><script>alert(1)</script>',(self.root/'report.html').read_text());self.assertTrue((self.root/'report.csv').exists())
    def test_fabricated_quote(self):
        self.a['themes'][0]['quotes'][0]['text']='Fabricated';self.assertRaises(ValueError,h.compute,self.c,self.a)
    def test_missing_record(self): self.a['assignments'].pop();self.assertRaises(ValueError,h.compute,self.c,self.a)
    def test_duplicate_assignment(self): self.a['assignments'][0]['theme_ids']=['t1','t1'];self.assertRaises(ValueError,h.compute,self.c,self.a)
    def test_text_tampering(self): self.c['records'][0]['text']='changed';self.assertRaises(ValueError,h.compute,self.c,self.a)
    def test_unconfirmed(self): self.plan['confirmed']=False;h.save(self.root/'plan.json',self.plan);self.assertRaises(ValueError,h.collect,self.root/'plan.json')
    def test_human_decision(self):
        r=h.build(self.c,self.a,self.root/'r.html',[{'id':'t1','verdict':'Ignore','review_status':'edited','reviewer':'PM','decision_reason':'Outside strategy'}]);self.assertEqual(r['themes'][0]['model_verdict'],'Watch');self.assertEqual(r['themes'][0]['verdict'],'Ignore')
    def test_overlap(self):
        t=copy.deepcopy(self.a['themes'][0]);t['id']='t2';self.a['themes'].append(t)
        for a in self.a['assignments']:a['theme_ids'].append('t2')
        r=h.compute(self.c,self.a);self.assertEqual([t['count'] for t in r['themes']],[2,2])
    def test_feed(self):
        rss=b'<rss><channel><item><description>Need &lt;b&gt;export&lt;/b&gt;</description><link>https://example.com/r</link><pubDate>Mon, 05 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'
        self.assertEqual(h.parse_feed(rss)[0]['text'],'Need export')
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><content>Need export</content><link href="https://example.com/a"/><updated>2026-01-01T12:00:00Z</updated></entry></feed>'
        self.assertEqual(h.parse_feed(atom)[0]['url'],'https://example.com/a')
        self.assertRaises(ValueError,h.parse_feed,b'<!DOCTYPE rss><rss/>')
    def test_appstore(self):
        data=json.dumps({'feed':{'entry':[{'content':{'label':'Need export'},'im:rating':{'label':'2'},'updated':{'label':'2026-01-01'}}]}}).encode()
        r=h.parse_appstore(data,'https://apps.apple.com/app/id123');self.assertEqual(r[0]['url_scope'],'product-fallback');self.assertEqual(r[0]['rating'],2)
    def test_remote_adapters(self):
        self.plan['sources'][0].update(adapter='json',url='https://example.com/reviews')
        h.save(self.root/'plan.json',self.plan)
        with patch.object(h,'permitted_fetch',return_value=json.dumps([{'text':'Remote fixture','url':'https://example.com/r'}]).encode()):
            r=h.collect(self.root/'plan.json');self.assertIn('Remote fixture',[x['text'] for x in r['records']])
    def test_partial_failure(self):
        self.plan['sources'][0]['permission']='unverified';h.save(self.root/'plan.json',self.plan);r=h.collect(self.root/'plan.json');self.assertEqual(len(r['failures']),1);self.assertEqual(len(r['records']),1)
    def test_nonpublic_url(self):
        for url in ['http://example.com','https://127.0.0.1','https://localhost','javascript:alert(1)','https://user:pass@example.com']: self.assertRaises(ValueError,h.url_ok,url)
    def test_network_guard(self):
        with patch.object(h.socket,'getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',443))]):self.assertRaises(ValueError,h.fetch,'https://example.com')
    def test_excluded_audit(self):
        self.a['assignments'][1]['theme_ids']=[]
        r=h.compute(self.c,self.a);self.assertEqual(len(r['assignments']),2);self.assertEqual(r['themes'][0]['count'],1)
    def test_review_types(self):
        self.a['themes'][0].update(review_status='accepted',reviewer={'name':'PM'},decision_reason=['Yes']);self.assertRaises(ValueError,h.compute,self.c,self.a)
    def test_atom_alternate(self):
        feed=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><summary>Issue</summary><link rel="self" href="https://example.com/api"/><link rel="alternate" href="https://example.com/review"/></entry></feed>'
        self.assertEqual(h.parse_feed(feed)[0]['url'],'https://example.com/review')
    def test_excluded_future_date(self):
        self.a['assignments'][1]['theme_ids']=[];self.c['records'][1]['date']='2999-01-01';self.assertRaises(ValueError,h.compute,self.c,self.a)
    def test_xhtml_blocks(self):
        feed=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><content type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml"><p>Need export.</p><p>Work blocked.</p></div></content><link href="https://example.com/review"/></entry></feed>'
        self.assertIn('export.\n',h.parse_feed(feed)[0]['text'])
    def test_future_date(self): self.assertRaises(ValueError,h.normalize,[{'text':'x','url':'https://example.com','date':'2999-01-01'}],self.plan['sources'][0],h.now())
if __name__=='__main__': unittest.main()
