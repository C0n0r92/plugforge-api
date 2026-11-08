#!/usr/bin/env python3
"""All-school bounded historical school-site discovery; cached evidence reused, no date cutoff.
Read-only public navigation, robots sitemaps and documented public WordPress media. No contacts.
"""
import requests,json,time,re,hashlib,threading,concurrent.futures as cf,sqlite3,subprocess,zipfile,io,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit,urljoin,urldefrag,urlencode
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent;D=P.parent;ROOT=D.parent
UA='DublinPrimaryAdmissionsResearch/0.2 (public school admission aggregates; read-only; low-rate historical research; no contacts)'
BOT='DublinPrimaryAdmissionsResearch'
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return time.strftime('%Y-%m-%dT%H:%M:%S%z')
def save(p,x):tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
TOPIC=re.compile(r'admiss|enrol|iontr|f[oó]gra|bliant|annual.?notice',re.I);NAV=re.compile(r'polic|parent|download|documents|school.info',re.I);BAD=re.compile(r'mailto:|tel:|facebook|instagram|twitter\.com|x\.com/|wp-admin|wp-login|aladdin|forms\.gle|docs.google.com/forms|\.xlsx?(?:\?|$)',re.I)
class Fetch:
 def __init__(self):
  self.mu=threading.Lock();self.locks={};self.last={};self.rules={};self.cache={};self.blocked={};self.denied=set();self.prior={}
  for line in (ROOT/'logs/requests.jsonl').read_text().splitlines():
   try:r=json.loads(line)
   except:continue
   u=r.get('url','');z=urlsplit(u)
   if z.path=='/robots.txt' and 'robots' in str(r.get('kind','')):self.prior[z.scheme+'://'+z.netloc]=r
   if r.get('status') in [401,403,429] or r.get('reason') in ['http_401','http_403','http_429']:self.denied.add(u)
 def log(self,e):
  with self.mu:
   with (P/'requests.jsonl').open('a') as f:f.write(json.dumps({'attempted_at':now(),**e})+'\n')
 def get(self,url,roll,kind,redirect=0):
  z=urlsplit(url);host=z.hostname or '';origin=z.scheme+'://'+z.netloc
  if z.scheme not in ['http','https'] or not host or host=='localhost' or host.endswith('.local') or re.match(r'^\d+\.\d+\.\d+\.\d+$',host):return None,'invalid_nonpublic_url',url
  with self.mu:lock=self.locks.setdefault(host,threading.Lock())
  with lock:
   if host in self.blocked:return None,self.blocked[host],url
   if url in self.denied:return None,'prior_exact_URL_access_denial_not_retried',url
   if url in self.cache:return self.cache[url]
   if origin not in self.rules:
    old=self.prior.get(origin,{});fp=ROOT/'cache'/('robots_'+sha(origin.encode())[:20]+'.txt');rp=None
    if old.get('status')==200 and fp.exists() and not re.search(r'<html|cf-chl',fp.read_text()[:2000],re.I):
     rp=RobotFileParser();rp.parse(fp.read_text().splitlines());self.rules[origin]=(rp,max(2.8,rp.crawl_delay(BOT) or rp.crawl_delay('*') or 0),'reused_verified_robots_rules')
    elif old.get('status') in [404,410]:self.rules[origin]=(None,2.8,'reused_robots_absent')
    elif old.get('status') in [401,403,429,202]:self.rules[origin]=(False,2.8,'prior_robots_access_or_challenge_not_retried')
    else:
     try:
      rr=requests.get(origin+'/robots.txt',headers={'User-Agent':UA},timeout=(7,12),allow_redirects=False);self.last[host]=time.monotonic();reason=''
      if rr.status_code==200 and not re.search(r'<html|cf-chl|challenge-platform',rr.text[:4000],re.I):
       rp=RobotFileParser();rp.parse(rr.text.splitlines());self.rules[origin]=(rp,max(2.8,rp.crawl_delay(BOT) or rp.crawl_delay('*') or 0),'robots_rules_loaded');(P/'cache'/('robots_'+sha(origin.encode())[:20]+'.txt')).write_text(rr.text)
      elif rr.status_code in [404,410]:self.rules[origin]=(None,2.8,'robots_absent')
      else:self.rules[origin]=(False,2.8,'robots_permission_unestablished_http_'+str(rr.status_code))
      self.log(dict(roll=roll,url=origin+'/robots.txt',kind='robots',http_status=rr.status_code,status=self.rules[origin][2]))
     except requests.RequestException as e:
      reason='network_proxy_block' if isinstance(e,requests.exceptions.ProxyError) else 'robots_transient_'+type(e).__name__;self.rules[origin]=(False,2.8,reason);self.log(dict(roll=roll,url=origin+'/robots.txt',kind='robots',status=reason,error=str(e)))
      if reason=='network_proxy_block':self.blocked[host]=reason
   rp,delay,reason=self.rules[origin]
   if rp is False or (rp is not None and not rp.can_fetch(UA,url)):return None,reason if rp is False else 'robots_disallow',url
   time.sleep(max(0,delay-(time.monotonic()-self.last.get(host,0))))
   try:
    r=requests.get(url,headers={'User-Agent':UA},timeout=(7,18),allow_redirects=False,stream=True);self.last[host]=time.monotonic()
    if r.status_code in [401,403,429] or any(k.lower()=='x-mitmproxy-blocked-reason' for k in r.headers):
     reason='network_proxy_block' if any(k.lower()=='x-mitmproxy-blocked-reason' for k in r.headers) else 'http_access_denied_'+str(r.status_code);self.blocked[host]=reason;r.close();self.log(dict(roll=roll,url=url,kind=kind,status=reason));return None,reason,url
    if r.is_redirect:
     target=urljoin(url,r.headers.get('Location',''));r.close();result=None;st='redirect'
    elif r.status_code!=200:
     st='http_'+str(r.status_code);r.close();self.log(dict(roll=roll,url=url,kind=kind,status=st));return None,st,url
    else:
     chunks=[];n=0
     for b in r.iter_content(65536):
      n+=len(b)
      if n>10000000:r.close();return None,'public_document_size_bound',url
      chunks.append(b)
     body=b''.join(chunks);ct=r.headers.get('Content-Type','');r.close()
     if re.search(rb'<title>[^<]*(Just a moment|Access Denied|Verify)|cf-chl-|challenge-platform',body[:12000],re.I):self.blocked[host]='anti_bot_challenge';return None,'anti_bot_challenge',url
     self.log(dict(roll=roll,url=url,kind=kind,status='ok',sha256=sha(body),bytes=n,content_type=ct));self.cache[url]=(body,'ok',url);return body,'ok',url
   except requests.RequestException as e:
    st='network_proxy_block' if isinstance(e,requests.exceptions.ProxyError) else 'transient_'+type(e).__name__
    if st=='network_proxy_block':self.blocked[host]=st
    self.last[host]=time.monotonic();self.log(dict(roll=roll,url=url,kind=kind,status=st,error=str(e)));return None,st,url
  if redirect>=4:return None,'redirect_bound',url
  return self.get(target,roll,kind,redirect+1)
F=Fetch();known_urls=set();known_hash=set();records=json.loads((ROOT/'data/admissions.json').read_text());rec={r['roll_number']:r for r in records}
for r in json.loads((ROOT/'data/notice_inventory.json').read_text()):known_urls.add(r['url']);known_hash.add((r['roll_number'],r.get('sha256')))
def parse(body,url,roll,label):
 h=sha(body)
 if (roll,h) in known_hash:return None
 fmt='pdf' if body.startswith(b'%PDF') else 'docx' if body.startswith(b'PK') else 'html';source=None
 if fmt=='pdf':
  source=P/'cache'/(h+'.pdf');source.write_bytes(body)
  try:text=subprocess.run(['pdftotext','-layout',str(source),'-'],capture_output=True,timeout=20).stdout.decode('utf8','replace')
  except Exception:text=''
 elif fmt=='docx':
  try:
   z=zipfile.ZipFile(io.BytesIO(body));text='\n'.join(''.join(x.itertext()) for x in ET.fromstring(z.read('word/document.xml')).findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
  except Exception:return None
 else:
  soup=BeautifulSoup(body,'html.parser');a=soup.select_one('article') or soup.select_one('main') or soup
  for x in a.select('script,style,nav,footer,header'):x.decompose()
  text=a.get_text('\n',strip=True)
  m=re.search(r'annual\s+admissions?\s+notice|f[oó]gra\s+(?:bliant|iontr)',text,re.I)
  if not m:return None
  text=text[max(0,m.start()-100):m.start()+18000]
 annual=bool(re.search(r'annual\s+admissions?\s+notice|f[oó]gra\s+(?:bliant|iontr)|f[oó]gra\s+um\s+ligean',text,re.I))
 if not annual:
  if source:source.unlink(missing_ok=True)
  return None
 # Remove contact headers; no pupil/parent data fields are extracted.
 text=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[school email omitted]',text)
 fp=P/'evidence'/f'{roll}_{h[:20]}.txt';fp.write_text(text)
 return {'roll':roll,'url':url,'label':label,'sha256':h,'format':fmt,'text_file':str(fp.relative_to(ROOT)),'source_file':str(source.relative_to(ROOT)) if source else None,'candidate_status':'notice_body_candidate_requires_evidence_review','text_length':len(text)}
def score(url,label):
 s=url+' '+label;years=[int(y) for y in re.findall(r'(?:19|20)\d\d',s)];old=min(years) if years else 2100
 return 50*bool(re.search(r'annual|notice|f[oó]gra|bliant',s,re.I))+20*bool(TOPIC.search(s))+10*bool(re.search(r'\.pdf|\.docx?',url,re.I))+max(0,2030-old)-20*bool(re.search(r'policy|application.form',s,re.I))
def one(row):
 roll,url=row;fp=P/'checkpoints'/f'{roll}.json'
 if fp.exists():return
 start=time.monotonic();attempts=[];docs=[];seen=set();queue=[];queued=set();maps=set();wp=False
 if not url:save(fp,dict(roll=roll,status='no_domain',attempts=[],documents=[],pending_links=[],started_at=now()));return
 host=(urlsplit(url).hostname or '').removeprefix('www.')
 def put(u,label,via):
  u=urldefrag(u)[0]
  if not u.startswith(('http://','https://')) or BAD.search(u) or u in seen or u in queued or u in known_urls:return
  queued.add(u);queue.append((score(u,label),u,label,via))
 # Current home is one discovery seed, not evidence that historical notices are absent.
 put(url,'School homepage','home')
 old=ROOT/'checkpoints/v4_deep'/f'{roll}.json'
 if old.exists():
  rr=json.loads(old.read_text())
  for a in rr.get('attempted_urls',[]):
   u=a.get('url','')
   if a.get('status')=='ok' and TOPIC.search(u) and not re.search(r'\.pdf|\.docx?|wp-json',u,re.I):put(u,a.get('label',''),'prior_public_admissions_landing')
 r=rec.get(roll,{})
 for u in r.get('admissions_landing_urls',[]):put(u,'Prior school admissions section','prior_link')
 while queue and len(attempts)<24 and time.monotonic()-start<150:
  queue.sort(reverse=True);_,u,label,via=queue.pop(0);seen.add(u);b,st,end=F.get(u,roll,via);attempts.append(dict(url=u,final_url=end,status=st,via=via,label=label))
  if not b:continue
  d=parse(b,end,roll,label)
  if d and d['sha256'] not in {v['sha256'] for v in docs}:docs.append(d)
  if b.startswith(b'%PDF') or b.startswith(b'PK'):continue
  if 'wordpress_media' in via:
   try:
    for item in json.loads(b):
     v=item.get('source_url');lab=item.get('title',{}).get('rendered','')
     if v and TOPIC.search(v+' '+lab):put(v,lab,'public_wordpress_media_link')
   except Exception:pass
   continue
  if 'sitemap' in via:
   try:
    root=ET.fromstring(b)
    for x in root.iter():
     if x.tag.split('}')[-1]!='loc' or not x.text:continue
     v=x.text.strip()
     if root.tag.split('}')[-1]=='sitemapindex':
      if len(maps)<4 and not re.search(r'image|tag|author|category',v):maps.add(v);put(v,'Public sitemap index child','sitemap_child')
     elif TOPIC.search(v):put(v,'Admission URL from sitemap','sitemap_link')
   except Exception:pass
   continue
  soup=BeautifulSoup(b,'html.parser')
  for a in soup.select('a[href],iframe[src],embed[src],object[data]'):
   v=urljoin(end,a.get('href') or a.get('src') or a.get('data'));lab=a.get_text(' ',strip=True) or a.get('title','');same=(urlsplit(v).hostname or '').removeprefix('www.')==host
   if TOPIC.search(v+' '+lab) or (same and NAV.search(v+' '+lab)) or (TOPIC.search(end) and re.search(r'\.pdf(?:\?|$)|\.docx?(?:\?|$)',v,re.I)):put(v,lab,'school_public_link')
  origin=urlsplit(end).scheme+'://'+urlsplit(end).netloc
  if origin not in maps:
   maps.add(origin);rf=ROOT/'cache'/('robots_'+sha(origin.encode())[:20]+'.txt');rt=rf.read_text() if rf.exists() else '';sm=re.findall(r'^Sitemap:\s*(\S+)',rt,re.I|re.M)
   for v in sm or [origin+'/sitemap.xml']:put(v,'Public sitemap','sitemap_root')
  if not wp and (b'wp-content/' in b or soup.find('link',rel='https://api.w.org/')):
   wp=True;put(origin+'/wp-json/wp/v2/media?'+urlencode({'search':'admission','per_page':100,'orderby':'date','order':'asc','_fields':'source_url,title,mime_type,date'}),'Oldest public admission media (all dates)','wordpress_media')
 pending=[{'url':u,'label':l,'via':v} for _,u,l,v in sorted(queue,reverse=True)]
 status='attempted_historical_discovery_candidates_found' if docs else 'bounded_search_no_new_notice_found' if any(a['status']=='ok' for a in attempts) else 'access_or_infrastructure_deferred'
 save(fp,dict(roll=roll,status=status,attempts=attempts,documents=docs,pending_links=pending,elapsed_seconds=round(time.monotonic()-start,2),bound='24 public linked requests or150seconds per school; robots/public sitemap/one documented oldest-media page; pending links retained; no school count cap; no date cutoff',started_at=now()));print(roll,status,'attempts',len(attempts),'newdocs',len(docs),'pending',len(pending),flush=True)
if __name__=='__main__':
 c=sqlite3.connect(D/'admissions.sqlite3');rows=c.execute('select roll,website_url from school').fetchall();c.close();counts={}
 for r in json.loads((ROOT/'data/notice_inventory.json').read_text()):counts[r['roll_number']]=counts.get(r['roll_number'],0)+1
 rows.sort(key=lambda r:(-counts.get(r[0],0),r[0]));print('START all-school historical navigation',now(),'schools',len(rows),'workers12',flush=True)
 with cf.ThreadPoolExecutor(max_workers=12) as pool:list(pool.map(one,rows))
 print('FINISHED',now(),flush=True)
