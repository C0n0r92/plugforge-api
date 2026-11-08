#!/usr/bin/env python3
"""All remaining explicit linked notice targets, not guessed paths or unrelated policies."""
import collect_sites as X
import json,re,sqlite3,time,threading,concurrent.futures as cf
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
P=X.P;O=P/'pending_notice_followup';O.mkdir(exist_ok=True)
logs=[]
for f in [P/'requests.jsonl',P/'media_followup/requests.jsonl']:
 if f.exists():
  for l in f.read_text().splitlines():
   try:logs.append(json.loads(l))
   except:pass
attempted={r.get('url') for r in logs if r.get('kind')!='robots'};denied=set();robots={}
for r in logs:
 u=r.get('url','');z=urlsplit(u);st=r.get('status','')
 if st in ['network_proxy_block','anti_bot_challenge','http_access_denied_401','http_access_denied_403','http_access_denied_429']:denied.add(z.hostname)
 if z.path=='/robots.txt':robots[z.scheme+'://'+z.netloc]=r
for origin,r in robots.items():
 st=r.get('status','');f=P/'cache'/('robots_'+X.sha(origin.encode())[:20]+'.txt')
 if st in ['robots_rules_loaded','reused_verified_robots_rules'] and f.exists():
  rp=RobotFileParser();rp.parse(f.read_text().splitlines());X.F.rules[origin]=(rp,max(2.8,rp.crawl_delay(X.BOT) or rp.crawl_delay('*') or 0),'reused_milestone2_verified_robots_rules')
 elif st in ['robots_absent','reused_robots_absent']:X.F.rules[origin]=(None,2.8,st)
 else:X.F.rules[origin]=(False,2.8,st)
X.F.blocked.update({h:'prior_milestone2_host_access_or_network_control_not_retried' for h in denied if h})
c=sqlite3.connect(X.D/'admissions.sqlite3');homes=dict(c.execute('select roll,website_url from school'));known=set(c.execute('select roll,payload_sha256 from document'));c.close();todo={}
for f in (P/'checkpoints').glob('*.json'):
 r=json.loads(f.read_text());roll=r['roll'];home=homes.get(roll);host=(urlsplit(home or '').hostname or '').removeprefix('www.')
 for a in r.get('pending_links',[]):
  u=a['url'];lab=a.get('label','');s=u+' '+lab;uh=(urlsplit(u).hostname or '').removeprefix('www.')
  if u in attempted or X.BAD.search(u):continue
  if re.search(r'policy|polasa|application.?form|foirm|template|privacy|secondary|post.primary',s,re.I):continue
  if not re.search(r'annual.{0,35}(?:admi|enrol|notice)|admi.{0,30}notice|f[oó]gra|bliant|(?:admission|enrolment)[-_ ]20\d\d|20\d\d.{0,15}(?:admission|enrolment)',s,re.I):continue
  # Patron and other-school homepages are not broad discovery targets. Public storage must be explicitly linked.
  if uh!=host and uh not in ['static.wixstatic.com','storage.googleapis.com','drive.google.com','docs.google.com','www.dropbox.com','dropbox.com']:continue
  todo.setdefault(roll,[]).append(a)
for rr in todo:todo[rr]=list({z['url']:z for z in todo[rr]}.values());todo[rr].sort(key=lambda z:(-X.score(z['url'],z.get('label','')),z['url']))
X.save(O/'source_queue.json',[{'roll':r,'url':v['url'],'label':v.get('label','')} for r,vv in sorted(todo.items()) for v in vv]);print('QUEUED',len(todo),'schools',sum(map(len,todo.values())),'explicit notice links',flush=True)
def one(item):
 roll,aa=item;fp=O/(roll+'.json')
 if fp.exists():return
 start=time.monotonic();out={'roll':roll,'started_at':X.now(),'method':'previously_linked_explicit_annual_notice_gap_followup','attempts':[],'documents':[],'pending_links':[],'earliest_year_cutoff':None}
 for j,a in enumerate(aa):
  if j>=24 or time.monotonic()-start>=150:out['pending_links']+=aa[j:];break
  body,st,end=X.F.get(a['url'],roll,'remaining_explicit_notice_link');out['attempts'].append({'url':a['url'],'final_url':end,'status':st,'label':a.get('label','')})
  if not body:continue
  z=X.parse(body,end,roll,a.get('label',''))
  if z and (roll,z['sha256']) not in known:out['documents'].append(z)
 out['status']='attempted_notice_candidates_found' if out['documents'] else 'attempted_no_new_numeric_notice_established';out['elapsed_seconds']=round(time.monotonic()-start,2);X.save(fp,out);print('SCHOOL',roll,len(out['attempts']),len(out['documents']),len(out['pending_links']),flush=True)
with cf.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(one,sorted(todo.items())))
X.save(O/'FINISHED.json',{'at':X.now(),'schools':len(todo),'links':sum(map(len,todo.values()))});print('FINISHED',X.now(),flush=True)
