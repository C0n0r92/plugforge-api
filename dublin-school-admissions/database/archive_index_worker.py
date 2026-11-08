#!/usr/bin/env python3
"""Resumable, bounded-per-request all-school CDX enumeration. Index-only discovery, not verified numbers.
No earliest-year limit; pagination preserved. Refusal/network block stops the archive host, never routes around it.
"""
import sqlite3,json,requests,time,datetime,hashlib,re,sys,os
from pathlib import Path
from urllib.parse import urlsplit
D=Path(__file__).resolve().parent;P=D/'checkpoints/archive_index';P.mkdir(parents=True,exist_ok=True)
UA='DublinAdmissionsHistoricalResearch/1.0 (public aggregate school admissions; read-only; low-rate archive discovery)'
def now():return datetime.datetime.now().astimezone().isoformat()
def save(p,x):tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def main():
 if (P/'STOP_ARCHIVE_ACCESS.json').exists():print('Prior access stop; no requests',flush=True);return
 c=sqlite3.connect(D/'admissions.sqlite3');tasks=c.execute("SELECT roll,website_url FROM school WHERE website_url IS NOT NULL ORDER BY roll").fetchall();c.close()
 domains={};last=0;consecutive_errors=0
 for roll,u in tasks:
  host=(urlsplit(u).hostname or '').lower().removeprefix('www.')
  if not host:continue
  domains.setdefault(host,[]).append(roll)
 print('START',now(),'schools',len(tasks),'distinct_domains',len(domains),'all available years; no year cutoff',flush=True)
 # Reuse prior explicit robots 404 preflight from this session; no school-host crawling.
 # If not available, stop rather than assume permission.
 robots=D.parent/'wayback-pilot/archive_preflight.json'
 if not robots.exists() or json.loads(robots.read_text()).get('status_code')!=404:raise RuntimeError('Expected archive-host robots 404 preflight unavailable; recheck robots before running')
 for host,rolls in domains.items():
  fp=P/(hashlib.sha256(host.encode()).hexdigest()[:20]+'.json')
  previous=json.loads(fp.read_text()) if fp.exists() else {}
  if previous.get('status') in ['index_search_complete','archive_access_blocked','domain_scope_requires_manual_review']:continue
  if host.endswith(('wordpress.com','wixsite.com','weebly.com','google.com','facebook.com')):
   save(fp,dict(domain=host,rolls=rolls,status='domain_scope_requires_manual_review',reason='Shared host requires path-scoped exact original school URL; no whole-host crawl',updated_at=now()));continue
  resume=previous.get('resume_key');page=previous.get('pages',0);captures=previous.get('captures',[])
  while True:
   delay=max(0,3.5-(time.monotonic()-last))
   if delay:time.sleep(delay)
   params={'url':host,'matchType':'domain','output':'json','fl':'timestamp,original,mimetype,statuscode,digest','filter':['statuscode:200','original:(?i).*(admission|annual.{0,20}notice|iontr|fogra|f%C3%B3gra).*'],'collapse':'digest','limit':'200','showResumeKey':'true'}
   if resume:params['resumeKey']=resume
   e={'domain':host,'rolls':rolls,'attempted_at':now(),'method':'official_Wayback_CDX_domain_all_available_dates','params':params,'earliest_year_cutoff':None,'no_retry':True}
   try:
    r=requests.get('https://web.archive.org/cdx/search/cdx',params=params,headers={'User-Agent':UA},timeout=(12,40),allow_redirects=False);last=time.monotonic();e.update(url=r.url,http_status=r.status_code,headers={k:v for k,v in r.headers.items() if k.lower() in ['content-type','location','x-mitmproxy-blocked-reason','server']},body_sha256=hashlib.sha256(r.content).hexdigest())
    if r.status_code in [401,403,429] or 'x-mitmproxy-blocked-reason' in {k.lower() for k in r.headers}:
     e.update(status='archive_access_blocked',error_excerpt=r.text[:600]);save(P/'STOP_ARCHIVE_ACCESS.json',e);save(fp,{**e,'captures':captures,'pages':page,'updated_at':now()});print('STOP',json.dumps(e),flush=True);return
    if r.status_code!=200:raise RuntimeError(f'Archive HTTP {r.status_code}: {r.text[:300]}')
    text=r.text.strip();decoder=json.JSONDecoder();a,pos=decoder.raw_decode(text);trailing=text[pos:].strip();resume=trailing.splitlines()[-1].strip() if trailing else None
    if not isinstance(a,list):raise ValueError('Unexpected CDX result')
    if a:
     header=a[0]
     for row in a[1:]:
      if isinstance(row,list) and len(row)==len(header):captures.append(dict(zip(header,row)))
    page+=1;consecutive_errors=0;e['status']='index_page_retrieved';e['page']=page
    state={'domain':host,'rolls':rolls,'status':'index_pagination_pending' if resume else 'index_search_complete','pages':page,'resume_key':resume,'captures':captures,'updated_at':now(),'scope':'Domain indexed admission-related original URLs, all available dates; bounded 200 per page; follows resume keys; index not exhaustive school archive or notice proof','last_request':e}
    save(fp,state);print('DOMAIN',host,'schools',','.join(rolls),'captures',len(captures),'pages',page,'resume',bool(resume),flush=True)
    with (P/'attempts.jsonl').open('a') as f:f.write(json.dumps(e)+'\n')
    if not resume:break
   except requests.exceptions.ProxyError as x:
    e.update(status='archive_network_proxy_block',error=str(x));save(P/'STOP_ARCHIVE_ACCESS.json',e);save(fp,{**e,'captures':captures,'pages':page,'updated_at':now()});print('STOP proxy',str(x),flush=True);return
   except Exception as x:
    e.update(status='transient_or_unclassified_failure',error_class=type(x).__name__,error=str(x));save(fp,{**e,'captures':captures,'pages':page,'resume_key':resume,'updated_at':now()})
    with (P/'attempts.jsonl').open('a') as f:f.write(json.dumps(e)+'\n')
    consecutive_errors+=1;print('DEFER',host,str(x),flush=True)
    if consecutive_errors>=3:save(P/'STOP_TRANSIENT_CIRCUIT.json',e);print('STOP transient circuit; resume only after diagnosis/cooldown',flush=True);return
    time.sleep(15);break
 print('FINISHED',now(),flush=True)
if __name__=='__main__':main()
