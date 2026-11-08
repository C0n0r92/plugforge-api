#!/usr/bin/env python3
"""Finite all-source-derived school upload prefix CDX queue. No earliest year cutoff.
Discover only admissions-related PDFs; actual bodies use archived replay/Memento proof.
Shared archive-host request lock, durable checkpoints, transient/access stop circuits.
"""
import json,sqlite3,re
from pathlib import Path
from urllib.parse import urlsplit
import collect_exact_archive as X
P=X.P; O=P/'prefix_archive';O.mkdir(exist_ok=True)
def prefix(u,home):
 p=urlsplit(u); hp=(urlsplit(home or '').hostname or '').removeprefix('www.')
 owner=(p.hostname or '').removeprefix('www.')
 # Never broaden a school's link to a shared provider's unrelated files.
 if '/wp-content/uploads/' in p.path and owner==hp:return u.split('/wp-content/uploads/')[0]+'/wp-content/uploads/'
 if '/_files/ugd/' in p.path and owner==hp:return u.split('/_files/ugd/')[0]+'/_files/ugd/'
 if owner=='storage.googleapis.com':
  m=re.match(r'(/iclasscrm_files/\d+/)',p.path)
  if m:return p.scheme+'://'+p.netloc+m[1]
 if owner=='static.wixstatic.com':
  m=re.match(r'(/ugd/[0-9a-fA-F]+_)',p.path)
  if m:return p.scheme+'://'+p.netloc+m[1]
 if '/uploads/' in p.path and owner==hp:return u.split('/uploads/')[0]+'/uploads/'
 if '/images/' in p.path and owner==hp:return u.split('/images/')[0]+'/images/'
 return None
def idx(roll,u):
 fp=O/('index_'+X.h(roll+' '+u)[:24]+'.json')
 if fp.exists():return json.loads(fp.read_text())
 q={'url':u,'matchType':'prefix','output':'json','fl':'timestamp,original,mimetype,statuscode,digest','filter':['statuscode:200','mimetype:application/pdf','original:(?i).*(admi|fogra|fógra|iontr|bliant|enrol).*'],'collapse':'urlkey','limit':'200','showResumeKey':'true'}
 r={'roll':roll,'original_prefix':u,'method':'documented_CDX_source_derived_upload_prefix_all_available_dates','earliest_year_cutoff':None,'attempted_at':X.stamp(),'pages':[],'captures':[]}
 # The successful narrow health-check is already cached. Do not refetch it.
 f=P/'prefix_cdx_healthcheck.json';old=json.loads(f.read_text()) if f.exists() else {}
 while True:
  if not r['pages'] and old.get('http_status')==200 and old['params']['url']==u:body=old['body'];code=200;err=None
  else:
   z,err=X.get('https://web.archive.org/cdx/search/cdx',q);body=z.text if z is not None else '';code=z.status_code if z is not None else None
  r['pages'].append({'at':X.stamp(),'params':dict(q),'http_status':code})
  if err:r.update(status='index_transient_failure_pending',**err);X.save(fp,r);return r
  if code!=200:r.update(status='index_http_'+str(code));X.save(fp,r);return r
  try:data,n=json.JSONDecoder().raw_decode(body.lstrip());tail=body.lstrip()[n:].strip();h=data[0] if data else [];r['captures'] += [dict(zip(h,v)) for v in data[1:] if len(v)==len(h)]
  except Exception as e:r.update(status='index_parse_failure_pending',error=str(e));X.save(fp,r);return r
  if not tail:break
  q['resumeKey']=tail;X.save(fp,{**r,'status':'pagination_in_progress'})
 r.update(status='index_complete',capture_count=len(r['captures']));X.save(fp,r);print('INDEX',roll,len(r['captures']),u,flush=True);return r
def main():
 c=sqlite3.connect(X.D/'admissions.sqlite3');rows=c.execute("select distinct d.roll,s.original_url,sc.website_url from document d join document_source ds using(document_id) join source s using(source_id) join school sc on sc.roll=d.roll where d.payload_sha256 is not null").fetchall()
 todo=set();known={(r,u) for r,u,w in rows}
 for r,u,w in rows:
  p=prefix(u,w)
  if p:todo.add((r,p))
 todo=sorted(todo,key=lambda v:(v[0]!='20043G',v));X.save(O/'source_queue.json',[{'roll':r,'prefix':u} for r,u in todo]);print('QUEUED',len(todo),'derived-prefixes',flush=True)
 for roll,u in todo:
  a=idx(roll,u);tasks=[]
  for z in a['captures']:
   original=z['original']
   if not re.search(r'admi|f[oó]gra|iontr|bliant|enrol',original,re.I):continue
   if re.search(r'policy|polasa|form|foirm|privacy|rse|code.of|data.protect',original,re.I):continue
   # Known versions remain valuable, but recover unknown older URL gaps first.
   tasks.append((int((roll,original) in known),z['timestamp'],z))
  tasks.sort(key=lambda v:(v[0],v[1]));X.save(O/('candidates_'+X.h(roll+' '+u)[:24]+'.json'),{'roll':roll,'prefix':u,'tasks':[v[2] for v in tasks]})
  for _,_,z in tasks:X.replay(roll,z)
 X.save(O/'FINISHED.json',{'at':X.stamp(),'source_prefixes':len(todo)})
if __name__=='__main__':
 try:main()
 except X.Stop as e:print('STOP',str(e),X.stamp(),flush=True)
