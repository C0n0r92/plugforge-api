#!/usr/bin/env python3
"""Follow explicit public robots redirects for two redirect-only failures, plus one zero-seed school."""
import collect_sites as X
import json,re,time,requests,sqlite3,concurrent.futures as cf
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
P=X.P;O=P/'seed_followup';O.mkdir(exist_ok=True)
for sub in ['cache','evidence','checkpoints']:(O/sub).mkdir(exist_ok=True)
logs=[]
for l in (P/'requests.jsonl').read_text().splitlines():
 try:logs.append(json.loads(l))
 except:pass
denied={urlsplit(r.get('url','')).hostname for r in logs if r.get('status') in ['network_proxy_block','anti_bot_challenge','http_access_denied_401','http_access_denied_403','http_access_denied_429']}
X.P=O;X.F.blocked.update({h:'prior_milestone2_host_access_or_network_control_not_retried' for h in denied if h})
c=sqlite3.connect(X.D/'admissions.sqlite3');todo=c.execute("select roll,website_url from school where roll in ('19314E','19676P','20495S') order by roll").fetchall();c.close()
def run(item):
 roll,home=item
 if (O/'checkpoints'/(roll+'.json')).exists():return
 origin=urlsplit(home).scheme+'://'+urlsplit(home).netloc;u=origin+'/robots.txt';hops=[];finalorigin=origin
 if urlsplit(home).hostname in denied:X.save(O/(roll+'_robots_resolution.json'),{'roll':roll,'status':'prior_actual_access_control_not_retried','hops':hops});return
 if roll!='19314E':
  rp=False;reason='robots_redirect_resolution_pending'
  for _ in range(5):
   z=urlsplit(u)
   if z.scheme not in ['http','https'] or not z.hostname or z.hostname in denied or z.hostname=='localhost' or re.match(r'^\d+\.\d+\.\d+\.\d+$',z.hostname) or re.search(r'login|captcha|challenge|sign.in',u,re.I):reason='redirect_target_not_sanctioned_public_robots';break
   time.sleep(3)
   try:r=requests.get(u,headers={'User-Agent':X.UA},timeout=(7,12),allow_redirects=False)
   except requests.RequestException as e:reason='robots_transient_'+type(e).__name__;hops.append({'url':u,'error':str(e)});break
   hops.append({'url':u,'status':r.status_code,'location':r.headers.get('Location')})
   if r.status_code in [401,403,429] or any(k.lower()=='x-mitmproxy-blocked-reason' for k in r.headers):reason='robots_access_or_network_denial';break
   if r.is_redirect:u=urljoin(u,r.headers.get('Location',''));continue
   finalorigin=z.scheme+'://'+z.netloc
   if r.status_code in [404,410]:rp=None;reason='robots_absent_after_explicit_redirect';break
   if r.status_code==200 and not re.search(r'<html|cf-chl|challenge-platform',r.text[:4000],re.I):rp=RobotFileParser();rp.parse(r.text.splitlines());(O/'cache'/('robots_'+X.sha(origin.encode())[:20]+'.txt')).write_text(r.text);reason='robots_rules_after_explicit_redirect';break
   reason='robots_permission_unestablished_http_'+str(r.status_code);break
  X.save(O/(roll+'_robots_resolution.json'),{'roll':roll,'status':reason,'hops':hops,'started_at':X.now()})
  X.F.rules[origin]=(rp,max(2.8,rp.crawl_delay(X.BOT) or rp.crawl_delay('*') or 0) if rp else 2.8,reason)
  if finalorigin!=origin:X.F.rules[finalorigin]=X.F.rules[origin]
 X.known_urls.discard(home)
 for u in X.rec.get(roll,{}).get('admissions_landing_urls',[]):
  if not re.search(r'\.pdf|\.docx?',u,re.I):X.known_urls.discard(u)
 X.one(item)
with cf.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,todo))
X.save(O/'FINISHED.json',{'at':X.now(),'source_schools':3});print('FINISHED',X.now(),flush=True)
