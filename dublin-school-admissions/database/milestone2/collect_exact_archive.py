#!/usr/bin/env python3
"""Healthy narrow documented CDX queries + actual archived bodies, all available dates.
Finite source-derived queue. Global low rate, durable checkpoints, denial/timeout circuit.
"""
import requests,json,time,re,sqlite3,hashlib,datetime,subprocess,fcntl,zipfile,io
from xml.etree import ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit,urljoin,urldefrag
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent;D=P.parent;ROOT=D.parent;OUT=P/'exact_archive';OUT.mkdir(exist_ok=True)
UA='DublinAdmissionsHistoricalResearch/1.0 (public aggregate admissions; read-only; low rate; no contacts)'
last=0;failures=0
class Stop(Exception):pass
def save(p,r):tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def stamp():return datetime.datetime.now().astimezone().isoformat()
def h(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def get(u,params=None):
 # Shared host lock: exact replays and prefix metadata remain polite together.
 if (OUT/'STOP_ACCESS.json').exists():raise Stop('existing_archive_access_denial_no_retry')
 with (P/'wayback_request.lock').open('a+') as lock:
  fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
  state=P/'wayback_last_request.txt'
  try:prior=float(state.read_text())
  except (FileNotFoundError,ValueError):prior=0
  time.sleep(max(0,3.8-(time.time()-prior)))
  try:return _get_unlocked(u,params)
  finally:state.write_text(str(time.time()))
def _get_unlocked(u,params=None):
 global last,failures
 time.sleep(max(0,3.8-(time.monotonic()-last)));last=time.monotonic()
 try:
  r=requests.get(u,params=params,headers={'User-Agent':UA},timeout=(8,25),allow_redirects=False);last=time.monotonic()
  if r.status_code in [401,403,429] or any(k.lower()=='x-mitmproxy-blocked-reason' for k in r.headers):save(OUT/'STOP_ACCESS.json',{'at':stamp(),'url':r.url,'http_status':r.status_code,'error':r.text[:400]});raise Stop('archive_access_or_network_denial')
  failures=failures+1 if r.status_code>=500 else 0
  if failures>=3:save(OUT/'STOP_TRANSIENT.json',{'at':stamp(),'url':r.url,'http_status':r.status_code});raise Stop('three_consecutive_transient_failures')
  return r,None
 except requests.exceptions.ProxyError as e:save(OUT/'STOP_ACCESS.json',{'at':stamp(),'url':u,'error':str(e)});raise Stop('network_proxy_block')
 except requests.RequestException as e:
  last=time.monotonic();failures+=1
  if failures>=3:save(OUT/'STOP_TRANSIENT.json',{'at':stamp(),'url':u,'error':str(e)});raise Stop('three_consecutive_transient_failures')
  return None,dict(error_class=type(e).__name__,error=str(e))
def index(roll,u):
 fp=OUT/('index_'+h(roll+' '+u)[:24]+'.json')
 if fp.exists():return json.loads(fp.read_text())
 params={'url':u,'matchType':'exact','output':'json','fl':'timestamp,original,mimetype,statuscode,digest','filter':'statuscode:200','collapse':'digest','limit':'200','showResumeKey':'true'}
 rec={'roll':roll,'original_url':u,'method':'documented_CDX_exact_URL_all_available_dates','attempted_at':stamp(),'params':params,'earliest_year_cutoff':None,'captures':[],'pages':[]}
 # Reuse successful health-check query; do not request it a second time.
 cached=P/'narrow_cdx_dominican.json';cached=json.loads(cached.read_text()) if cached.exists() else {}
 while True:
  if not rec['pages'] and cached.get('status')=='success' and cached['params']['url']==u:body=cached['body'];code=200;err=None
  else:
   r,err=get('https://web.archive.org/cdx/search/cdx',params);body=r.text if r is not None else '';code=r.status_code if r is not None else None
  page={'at':stamp(),'http_status':code,'params':dict(params)};rec['pages'].append(page)
  if err:rec.update(status='index_transient_failure_pending',**err);save(fp,rec);return rec
  if code!=200:rec.update(status='index_http_'+str(code));save(fp,rec);return rec
  try:
   data,end=json.JSONDecoder().raw_decode(body.lstrip());tail=body.lstrip()[end:].strip();header=data[0] if data else [];rec['captures']+= [dict(zip(header,row)) for row in data[1:] if len(row)==len(header)]
  except Exception as e:rec.update(status='index_parse_failure',error=str(e));save(fp,rec);return rec
  if not tail:break
  params['resumeKey']=tail;rec['resume_key']=tail;save(fp,{**rec,'status':'pagination_in_progress'})
 rec.update(status='index_complete',capture_count=len(rec['captures']));save(fp,rec);print('INDEX',roll,len(rec['captures']),u,flush=True);return rec
def original_link(u):
 m=re.search(r'(?:(?:https?://web\.archive\.org)?/web/[^/]+/)(https?://.*)',u)
 return m[1] if m else u
seen=set()
def replay(roll,cap,depth=0):
 u=cap['original'];ts=cap['timestamp'];fp=OUT/('body_'+h(roll+' '+ts+' '+u)[:24]+'.json')
 if fp.exists():return json.loads(fp.read_text())
 if (roll,ts,u) in seen:return None
 seen.add((roll,ts,u));url='https://web.archive.org/web/'+ts+'/'+u;rec={'roll':roll,'capture':cap,'original_url':u,'archived_url':url,'attempted_at':stamp(),'linked_from_capture':cap.get('linked_from_capture')}
 r,err=get(url)
 if err:rec.update(status='replay_transient_failure_pending',**err);save(fp,rec);return rec
 rec.update(http_status=r.status_code,headers={k:v for k,v in r.headers.items() if k.lower() in ['memento-datetime','content-type','location']},bytes=len(r.content))
 if r.is_redirect:
  target=urljoin(url,r.headers.get('Location',''));rec.update(status='archive_redirect_pending',redirect_url=target)
  save(fp,rec)
  m=re.match(r'https://web\.archive\.org/web/(\d{14})[^/]*/(https?://.*)',target)
  if m and depth<3:return replay(roll,{'timestamp':m[1],'original':m[2],'linked_from_capture':url},depth+1)
  return rec
 if r.status_code!=200 or not r.headers.get('memento-datetime'):rec['status']='replay_http_'+str(r.status_code)+'_or_missing_capture_header';save(fp,rec);return rec
 payload=r.content;digest=h(payload);rec['payload_sha256']=digest
 if payload.startswith(b'%PDF'):
  src=P/'cache'/(digest+'.pdf');src.write_bytes(payload);z=subprocess.run(['pdftotext','-layout',str(src),'-'],capture_output=True,timeout=25);t=z.stdout.decode('utf8','replace');rec.update(format='pdf',source_file=str(src.relative_to(ROOT)),parse_stderr=z.stderr.decode('utf8','replace')[:500]);links=[]
 elif payload.startswith(b'PK'):
  src=P/'cache'/(digest+'.docx');src.write_bytes(payload);links=[]
  try:
   with zipfile.ZipFile(io.BytesIO(payload)) as z:
    doc=ET.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};t='\n'.join(' | '.join(''.join(q.itertext()) for q in para.findall('.//w:t',ns)) for para in doc.findall('.//w:p',ns))
   rec.update(format='docx',source_file=str(src.relative_to(ROOT)))
  except Exception as e:t='';rec.update(format='unsupported_zip',parse_error=str(e))
 elif 'html' in r.headers.get('Content-Type',''):
  src=P/'cache'/(digest+'.html');src.write_bytes(payload);rec['source_file']=str(src.relative_to(ROOT))
  soup=BeautifulSoup(payload,'html.parser');links=[]
  for a in soup.select('a[href],iframe[src],embed[src]'):
   v=original_link(urljoin(url,a.get('href') or a.get('src','')));label=a.get_text(' ',strip=True) or a.get('title','')
   if re.search(r'annual.{0,25}notice|admiss.{0,20}notice|f[oó]gra|bliant',v+' '+label,re.I) and re.search(r'\.pdf(?:\?|$)|drive.google.com/file/|_files/ugd/',v,re.I) and not re.search(r'policy|application.?form|mailto:|tel:',v+' '+label,re.I):links.append({'url':v,'label':label})
  node=soup.select_one('article') or soup.select_one('main') or soup
  for e in node.select('script,style,nav,footer,header'):e.decompose()
  t=node.get_text('\n',strip=True);rec['format']='html'
 else:t='';links=[];rec['format']='unsupported_media_pending'
 text=P/'evidence'/('exact_'+roll+'_'+digest[:20]+'.txt');text.write_text(re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[school email omitted]',t));rec.update(status='archived_body_retrieved_requires_manual_evidence_review' if t.strip() else 'archive_body_invalid_or_no_text_pending',text_file=str(text.relative_to(ROOT)),linked_document_candidates=links);save(fp,rec);print('BODY',roll,ts,rec['format'],len(t),flush=True)
 for item in links:
  if depth<2 and urlsplit(item['url']).scheme in ['http','https'] and not re.match(r'^\d+\.\d+\.\d+\.\d+$',urlsplit(item['url']).hostname or ''):replay(roll,{'original':item['url'],'timestamp':ts,'linked_from_capture':url,'link_label':item['label']},depth+1)
 return rec
if __name__=='__main__':
 try:
  c=sqlite3.connect(D/'admissions.sqlite3');rows=c.execute("select distinct d.roll,s.original_url from document d join notice n using(document_id) join document_source ds using(document_id) join source s using(source_id) where d.media_type like '%html%' order by d.roll,s.original_url").fetchall();c.close();todo=[];canon=set()
  for roll,u in rows:
   if 'googletranslate=' in u:continue
   k=(roll,u.rstrip('/'))
   if k in canon:continue
   canon.add(k);todo.append((roll,u))
  save(OUT/'source_queue.json',[{'roll':roll,'url':u} for roll,u in todo]);indices=[]
  for roll,u in todo:indices.append(index(roll,u))
  tasks=[]
  for r in indices:
   yearly={}
   for cap in r['captures']:yearly.setdefault(cap['timestamp'][:4],[]).append(cap)
   for y,cc in yearly.items():
    cc.sort(key=lambda x:x['timestamp'])
    for j,cap in enumerate(cc):tasks.append((0 if j==0 else 1,r['roll'],cap['timestamp'],cap))
  # Actual body verification for one oldest capture per CALENDAR YEAR first, then all remaining captures.
  # Calendar year is retrieval priority ONLY, NEVER the admission-year assignment.
  tasks.sort(key=lambda x:(x[0],x[1],x[2]));save(OUT/'capture_queue.json',[{'priority':pr,'roll':roll,**cap} for pr,roll,ts,cap in tasks])
  for pr,roll,ts,cap in tasks:replay(roll,cap)
  save(OUT/'FINISHED.json',{'at':stamp(),'sources_indexed':len(indices),'captures_queued':len(tasks)});print('FINISHED',stamp(),flush=True)
 except Stop as e:print('STOP',str(e),stamp(),flush=True)
