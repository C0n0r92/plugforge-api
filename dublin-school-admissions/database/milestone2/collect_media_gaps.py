#!/usr/bin/env python3
"""Fill prior notice-name/Irish-title gaps via verified public WordPress media endpoints.
Independent completed unique-host schools only; don't race active school navigation or retry blocks.
"""
import sys,json,time,re,collections,os
from pathlib import Path
from urllib.parse import urlsplit,urlencode
sys.path.insert(0,str(Path(__file__).resolve().parent))
import collect_sites as C
P=C.P;O=P/'media_followup';O.mkdir(exist_ok=True)
rows=C.sqlite3.connect(C.D/'admissions.sqlite3').execute('select roll,website_url from school').fetchall();hostcounts=collections.Counter((urlsplit(u).hostname or '').removeprefix('www.') for _,u in rows if u);site={r:u for r,u in rows};blocked=set()
def save(p,x):C.save(p,x)
def blocked_hosts():
 global blocked
 for line in (P/'requests.jsonl').read_text().splitlines():
  try:r=json.loads(line)
  except:continue
  st=r.get('status','')
  if re.search(r'access_denied|anti_bot|challenge|network_proxy_block|prior_robots_access|robots_permission_unestablished_http_(?:401|403|429)',st):blocked.add((urlsplit(r.get('url','')).hostname or '').removeprefix('www.'))
known=set(C.known_urls)
for path in (P/'checkpoints').glob('*.json'):
 for d in json.loads(path.read_text()).get('documents',[]):known.add(d['url']);C.known_hash.add((d['roll'],d['sha256']))
checked=set()
while True:
 blocked_hosts();fresh=[p for p in sorted((P/'checkpoints').glob('*.json')) if p.stem not in checked]
 for p in fresh:
  r=json.loads(p.read_text());roll=r['roll'];checked.add(roll);fp=O/(roll+'.json')
  if fp.exists():continue
  u=site.get(roll);host=(urlsplit(u or '').hostname or '').removeprefix('www.');out={'roll':roll,'attempted_at':C.now(),'method':'documented_public_WordPress_media_notice_and_Irish_title_gap_search','attempts':[],'documents':[],'pending_links':[],'earliest_year_cutoff':None}
  api=next((v['url'].split('?')[0] for v in r.get('attempts',[]) if v.get('via')=='wordpress_media' and v.get('status')=='ok'),None)
  if not api or hostcounts[host]!=1 or host in blocked:
   out['status']='skipped_prior_access_control' if host in blocked else 'not_applicable_no_verified_public_WP_endpoint' if not api else 'shared_host_deferred_to_avoid_parallel_host_requests';save(fp,out);continue
  start=time.monotonic();links=[]
  for term in ['notice','fógra']:
   q=api+'?'+urlencode({'search':term,'per_page':100,'orderby':'date','order':'asc','_fields':'source_url,title,mime_type,date'});b,st,end=C.F.get(q,roll,'m2_additional_documented_media_search');out['attempts'].append({'url':q,'status':st})
   if not b:continue
   try:items=json.loads(b)
   except:continue
   if not isinstance(items,list):continue
   if len(items)==100:out['pending_links'].append({'url':q+'&page=2','reason':'public_media_pagination_remains'})
   for a in items:
    v=a.get('source_url');label=a.get('title',{}).get('rendered','')
    if v and v not in known and re.search(r'annual.{0,30}notice|admiss.{0,25}notice|f[oó]gra|bliant',v+' '+label,re.I) and not re.search(r'privacy|application.?form|policy|polas[aá][ií]',v+' '+label,re.I):links.append({'url':v,'label':label,'cms_media_date_as_printed_not_publication':a.get('date')})
  uniq={a['url']:a for a in links};links=sorted(uniq.values(),key=lambda a:C.score(a['url'],a['label']),reverse=True)
  for a in links:
   if len(out['attempts'])>=24 or time.monotonic()-start>=150:out['pending_links'].append(a);continue
   known.add(a['url']);b,st,end=C.F.get(a['url'],roll,'m2_publicly_indexed_older_notice_media');out['attempts'].append({'url':a['url'],'status':st,'label':a['label']})
   if not b:continue
   d=C.parse(b,end,roll,a['label'])
   if d:d['discovery_method']='documented_WP_notice_or_Irish_title_media_query';d['cms_media_date_as_printed_not_publication']=a.get('cms_media_date_as_printed_not_publication');out['documents'].append(d);C.known_hash.add((roll,d['sha256']))
  out['status']='attempted_new_historical_notice_candidates' if out['documents'] else 'attempted_no_new_notice_payload';out['elapsed_seconds']=round(time.monotonic()-start,1);save(fp,out);print(roll,out['status'],'new',len(out['documents']),flush=True)
 # This is a finite pass through an upstream finite school queue, not a schedule or ongoing monitor.
 log=(P/'collection.log').read_text();finished='FINISHED' in log or 'Traceback (most recent call last)' in log
 if finished and all(p.stem in checked for p in (P/'checkpoints').glob('*.json')):break
 time.sleep(5)
save(O/'FINISHED.json',{'at':C.now(),'checked_school_checkpoints':len(checked)});print('FINISHED',C.now(),flush=True)
