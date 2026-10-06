#!/usr/bin/env python3
"""Heard batch collection and deterministic evidence/report pipeline (stdlib only)."""
import argparse, csv, hashlib, html, ipaddress, json, math, re, socket, sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

UA = 'Heard/0.1'
MAX_BYTES = 5_000_000
BLOCKED = ('g2.com', 'reddit.com', 'redd.it', 'capterra.com', 'trustradius.com', 'trustpilot.com', 'play.google.com')

def now(): return datetime.now(timezone.utc).isoformat()
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
def require(ok, message):
    if not ok: raise ValueError(message)
def url_ok(url):
    p = urlparse(url)
    require(p.scheme == 'https' and p.hostname and not p.username and not p.password and p.port in (None,443), 'Public HTTPS URL required')
    require(p.hostname != 'localhost', 'Local URL disallowed')
    try: require(ipaddress.ip_address(p.hostname).is_global, 'Non-public URL disallowed')
    except ValueError as e:
        if str(e) == 'Non-public URL disallowed': raise
    return p

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): raise ValueError('Redirect requires separately approved URL')

def fetch(url, method='GET'):
    p = url_ok(url)
    addresses = socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM)
    require(addresses and all(ipaddress.ip_address(x[4][0]).is_global for x in addresses), 'Non-public DNS target')
    with build_opener(NoRedirect()).open(Request(url, headers={'User-Agent':UA}, method=method), timeout=20) as response:
        data = response.read(MAX_BYTES+1) if method == 'GET' else b''
        require(len(data) <= MAX_BYTES, 'Response exceeds size limit')
        return data

def permitted_fetch(url):
    p = url_ok(url)
    require(not any(p.hostname == d or p.hostname.endswith('.'+d) for d in BLOCKED), 'Automatic collection disabled for this source')
    robot_url = f'https://{p.netloc}/robots.txt'
    try: robots = fetch(robot_url).decode('utf-8')
    except Exception as e: raise ValueError('Robots unavailable; use manual import') from e
    rp = RobotFileParser(); rp.parse(robots.splitlines())
    require(rp.can_fetch(UA,url), 'Robots disallows endpoint')
    delay = rp.crawl_delay(UA)
    require(delay is None, 'Feed has crawl delay; use approved external collection/import')
    return fetch(url)

class Plain(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,data): self.parts.append(data)
    def handle_starttag(self,tag,attrs):
        if tag.split(':')[-1] in ('p','div','br','li','h1','h2','h3'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag.split(':')[-1] in ('p','div','li','h1','h2','h3'): self.parts.append('\n')
def plain(text):
    p=Plain(); p.feed(text); return ''.join(p.parts).strip()
def tag(node,name): return next((x for x in node if x.tag.split('}')[-1] == name),None)
def val(node,name):
    x=tag(node,name)
    if x is None: return ''
    if len(x): return (x.text or '')+''.join(ET.tostring(child,encoding='unicode') for child in x)
    return x.text or ''
def parse_feed(data):
    require(b'<!DOCTYPE' not in data.upper() and b'<!ENTITY' not in data.upper(), 'DTD/entity declarations disallowed')
    root=ET.fromstring(data); records=[]
    for x in root.iter():
        name=x.tag.split('}')[-1]
        if name not in ('item','entry'): continue
        links=[child for child in x if child.tag.split('}')[-1]=='link']
        link=next((child for child in links if child.get('rel','alternate')=='alternate'),None)
        url=(link.get('href') or (link.text or '')) if link is not None else ''
        text=plain(val(x,'description') or val(x,'content') or val(x,'summary') or val(x,'title'))
        date=val(x,'pubDate') or val(x,'updated') or val(x,'published')
        if date:
            try: date=parsedate_to_datetime(date).date().isoformat()
            except (ValueError,TypeError): date=date[:10]
        records.append({'text':text,'url':url,'date':date or None})
    return records

def parse_appstore(data, fallback):
    entries=json.loads(data).get('feed',{}).get('entry',[])
    if isinstance(entries,dict): entries=[entries]
    result=[]
    for e in entries:
        if 'im:rating' not in e: continue
        links=e.get('link',[]); links=[links] if isinstance(links,dict) else links
        url=next((l.get('attributes',{}).get('href') for l in links if l.get('attributes',{}).get('href')),None)
        result.append({'text':e.get('content',{}).get('label',''), 'url':url or fallback,
            'url_scope':'review' if url else 'product-fallback', 'date':e.get('updated',{}).get('label','')[:10] or None,
            'rating':float(e['im:rating']['label'])})
    return result

def normalize(rows, source, collected):
    require(isinstance(rows,list), 'Source must contain a JSON record array')
    output=[]
    for row in rows:
        require(isinstance(row,dict) and isinstance(row.get('text'),str) and row['text'].strip(), 'Empty/invalid record text')
        url_ok(row.get('url',''))
        require(len(row['text']) <= 100000, 'Record too large')
        date=row.get('date') or None
        if date:
            require(isinstance(date,str), 'Invalid date')
            day=datetime.fromisoformat(date[:10]).date()
            require(day <= datetime.fromisoformat(collected).date(), 'Future date')
            date=day.isoformat()
        identity=source['id']+'\0'+row['url']+'\0'+row['text']
        r={'id':'r_'+hashlib.sha256(identity.encode()).hexdigest()[:20], 'source':source['id'], 'family':source['family'],
            'text':row['text'],'url':row['url'],'date':date,'collected_at':collected,
            'content_hash':hashlib.sha256(row['text'].encode()).hexdigest(), 'url_scope':row.get('url_scope','record')}
        for key in ('rating','role'):
            if row.get(key) is not None:
                if key=='rating': require(isinstance(row[key],(int,float)) and not isinstance(row[key],bool) and math.isfinite(row[key]), 'Invalid rating')
                else: require(isinstance(row[key],str), 'Invalid role')
                r[key]=row[key]
        output.append(r)
    return output

def collect(plan_path):
    plan=load(plan_path); require(plan.get('confirmed') is True,'Source plan is not confirmed')
    require(isinstance(plan.get('product'),str) and plan['product'].strip(), 'Product required')
    sources=plan['sources']; require(sources and len({s['id'] for s in sources})==len(sources), 'Unique source IDs required')
    collected=now(); result={'product':plan['product'],'collected_at':collected,'sources':[],'failures':[],'duplicates':[],'records':[]}; seen={}
    for s in sources:
        try:
            require(s.get('permission')=='approved' and s.get('permission_evidence'), 'Permission evidence required')
            require(s.get('family') and s.get('id'), 'Source identity required')
            limit=s.get('limit',200); require(type(limit)==int and 1<=limit<=1000,'Limit must be 1–1000')
            adapter=s['adapter']
            if adapter=='manual':
                rows=load(Path(plan_path).parent / s['path'])
                require(not any(urlparse(r.get('url','')).hostname and (urlparse(r['url']).hostname=='g2.com' or urlparse(r['url']).hostname.endswith('.g2.com')) for r in rows),'G2 excluded')
            else:
                data=permitted_fetch(s['url'])
                if adapter=='rss': rows=parse_feed(data)
                elif adapter=='json': rows=json.loads(data)
                elif adapter=='appstore': rows=parse_appstore(data,s.get('product_url',''))
                else: raise ValueError('Unknown adapter')
            records=normalize(rows[:limit],s,collected)
            for r in records:
                fingerprint=re.sub(r'\s+',' ',r['text']).strip().casefold()
                if fingerprint in seen: result['duplicates'].append({'retained_id':seen[fingerprint],'source':s['id'],'url':r['url']}); continue
                seen[fingerprint]=r['id']; result['records'].append(r)
            result['sources'].append({k:s.get(k) for k in ('id','family','adapter','url','permission_evidence')} | {'retrieved':len(rows),'limit':limit,'processed':len(records)})
        except Exception as e: result['failures'].append({'source':s.get('id','unknown'),'error':str(e)})
    require(result['records'],'No records collected: '+json.dumps(result['failures']))
    return result

def validate_corpus(corpus):
    records=corpus['records']; require(records,'Empty corpus')
    require(len({r['id'] for r in records})==len(records),'Duplicate record ID')
    for r in records:
        if r.get('date'):
            require(isinstance(r['date'],str), 'Invalid date')
            require(datetime.fromisoformat(r['date']).date() <= datetime.fromisoformat(corpus['collected_at']).date(), 'Future date')
        url_ok(r['url']); require(r['content_hash']==hashlib.sha256(r['text'].encode()).hexdigest(),'Record text changed after collection')
    return {r['id']:r for r in records}

def compute(corpus, analysis):
    records=validate_corpus(corpus); themes=analysis['themes']; assignments=analysis['assignments']
    require(isinstance(analysis.get('brief'),str) and isinstance(analysis.get('blind_spots'),list), 'Brief/blind spots required')
    tids=[t['id'] for t in themes]; require(len(set(tids))==len(tids),'Duplicate theme ID')
    require(len(assignments)==len(records) and {a['record_id'] for a in assignments}==set(records),'Every record requires exactly one assignment')
    counts={t:[] for t in tids}
    for a in assignments:
        require(a.get('rationale'),'Assignment rationale required')
        require(type(a.get('intensity'))==int and 0<=a['intensity']<=3,'Intensity must be integer 0–3')
        ids=a['theme_ids']; require(len(ids)==len(set(ids)), 'Duplicate theme assignment')
        for t in ids:
            require(t in counts,'Unknown theme ID'); counts[t].append(a)
    families={r['family'] for r in records.values()}; day=datetime.fromisoformat(corpus['collected_at']).date(); output=[]
    for t in themes:
        require(t['verdict'] in ('Build','Watch','Ignore'),'Invalid verdict')
        status=t.get('review_status'); require(status in ('proposed','accepted','edited'),'Review status required')
        if status!='proposed': require(all(isinstance(t.get(k),str) and t[k].strip() for k in ('reviewer','decision_reason')),'Human review evidence required')
        for key in ('title','reasoning','beneficiary','cost','displaces','next_test','counterevidence'): require(isinstance(t.get(key),str) and t[key].strip(), 'Missing theme field: '+key)
        members=counts[t['id']]; require(members,'Empty theme'); ids={a['record_id'] for a in members}; quotes=t['quotes']; require(quotes,'Theme quote required')
        for q in quotes: require(q['record_id'] in ids and isinstance(q['text'],str) and q['text'] and q['text'] in records[q['record_id']]['text'],'Quote is not a verbatim substring of an assigned record')
        recency=[]; unknown=0
        for a in members:
            date=records[a['record_id']].get('date')
            if not date: recency.append(0); unknown+=1
            else:
                age=(day-datetime.fromisoformat(date).date()).days; require(age>=0,'Future date'); recency.append(max(0,1-age/365))
        dist={f:sum(records[a['record_id']]['family']==f for a in members) for f in sorted(families)}
        components=[len(ids)/len(records),sum(a['intensity'] for a in members)/len(members)/3,sum(recency)/len(recency),sum(v>0 for v in dist.values())/len(families)]
        output.append(dict(t,record_ids=sorted(ids),count=len(ids),source_counts=dist,missing_dates=unknown,components=components,score=sum(w*v for w,v in zip((45,25,20,10),components))))
    output.sort(key=lambda t:(-t['score'],t['id']))
    return {'product':corpus['product'],'brief':analysis['brief'],'blind_spots':analysis['blind_spots'], 'collected_at':corpus['collected_at'],'failures':corpus.get('failures',[]),'sources':corpus['sources'],'duplicates':len(corpus.get('duplicates',[])), 'record_count':len(records),'family_count':len(families),'themes':output,'records':list(records.values()),'assignments':assignments,'scoring_version':'1'}

def build(corpus,analysis,out,decisions=None):
    if decisions:
        require(isinstance(decisions,list),'Decisions must be an array')
        require(len({d['id'] for d in decisions})==len(decisions),'Duplicate human decision')
        mapping={t['id']:t for t in analysis['themes']}
        for d in decisions:
            require(d['id'] in mapping,'Unknown decision theme')
            t=mapping[d['id']]; t['model_verdict']=t.get('model_verdict',t['verdict']); t['model_reasoning']=t.get('model_reasoning',t['reasoning'])
            for k in ('verdict','review_status','reviewer','decision_reason'): t[k]=d.get(k)
    report=compute(corpus,analysis); out=Path(out); out.parent.mkdir(parents=True,exist_ok=True)
    template=(Path(__file__).parent.parent/'assets/report.html').read_text()
    payload=json.dumps(report,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    out.write_text(template.replace('__DATA__',payload),encoding='utf-8'); save(out.with_suffix('.json'),report)
    with out.with_suffix('.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['Theme','Verdict','Review status','Mentions','Score','Reasoning','Next validation'])
        for t in report['themes']:
            values=[t['title'],t['verdict'],t['review_status'],t['count'],round(t['score'],2),t['reasoning'],t['next_test']]
            writer.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    return report

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('collect'); c.add_argument('plan'); c.add_argument('--out',required=True)
    c=sub.add_parser('prepare'); c.add_argument('records'); c.add_argument('--out',required=True); c.add_argument('--batch-size',type=int,default=40)
    c=sub.add_parser('build'); c.add_argument('records'); c.add_argument('analysis'); c.add_argument('--out',required=True); c.add_argument('--decisions')
    c=sub.add_parser('links'); c.add_argument('records'); c.add_argument('--out',required=True)
    args=p.parse_args()
    try:
        if args.cmd=='collect':
            result=collect(args.plan); save(args.out,result); print(json.dumps({'records':len(result['records']),'failures':result['failures']}))
        elif args.cmd=='prepare':
            corpus=load(args.records); validate_corpus(corpus); require(1<=args.batch_size<=100,'Batch size must be 1–100'); out=Path(args.out); files=[]
            for start in range(0,len(corpus['records']),args.batch_size):
                name=f'batch-{start//args.batch_size+1:03}.json'; save(out/name,corpus['records'][start:start+args.batch_size]); files.append(name)
            save(out/'manifest.json',{'total_records':len(corpus['records']),'files':files,'product':corpus['product']}); print(json.dumps({'batches':len(files)}))
        elif args.cmd=='build':
            r=build(load(args.records),load(args.analysis),args.out,load(args.decisions) if args.decisions else None); print(json.dumps({'verified_records':r['record_count'],'themes':len(r['themes']),'out':args.out}))
        else:
            corpus=load(args.records); validate_corpus(corpus); checks=[]
            for url in sorted({r['url'] for r in corpus['records']}):
                try: fetch(url,method='HEAD'); checks.append({'url':url,'status':'resolves','checked_at':now()})
                except Exception as e: checks.append({'url':url,'status':'unknown','detail':str(e),'checked_at':now()})
            save(args.out,{'checks':checks,'confirmed_share':sum(c['status']=='resolves' for c in checks)/len(checks),'note':'Resolution is not source authenticity; redirects remain unknown.'}); print(json.dumps({'checked':len(checks)}))
    except (ValueError,KeyError,TypeError,OSError) as e: print('ERROR: '+str(e),file=sys.stderr); return 1
    return 0
if __name__=='__main__': sys.exit(main())
