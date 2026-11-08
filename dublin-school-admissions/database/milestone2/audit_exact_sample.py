#!/usr/bin/env python3
import sys,time,json,sqlite3,datetime,hashlib
from pathlib import Path
import collect_exact_archive as X
P=Path(__file__).resolve().parent;O=P/'method_audit';O.mkdir(exist_ok=True)
selection=json.loads((O/'sample_selection.json').read_text());original_get=X.get;route='';calls=[]
c=sqlite3.connect(P.parent/'admissions.sqlite3');baseline=[list(r) for r in c.execute('select distinct roll,academic_year from v_group_funnel where academic_year is not null and supported_metric_count>0')];c.close();X.save(O/'before_school_year_pairs.json',baseline)
def get(u,params=None):
 start=time.monotonic();r=None;err=None
 try:r,err=original_get(u,params);return r,err
 finally:
  rec={'at':X.stamp(),'school_roll':active,'stage':route,'url':r.url if r is not None else u,'params':params,'elapsed_total_seconds':round(time.monotonic()-start,3),'response_elapsed_seconds':r.elapsed.total_seconds() if r is not None else None,'http_status':r.status_code if r is not None else None,'error':err}
  calls.append(rec)
  with (O/'requests.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
X.get=get;cdxfail=0;results=[]
try:
 for row in selection['sample']:
  active=row['roll'];fp=O/(active+'.json')
  if fp.exists():results.append(json.loads(fp.read_text()));continue
  start=time.monotonic();target=row['landing_url'] or row['original_url'];rec={**row,'target_url':target,'started_at':X.stamp(),'captures_replayed':[]}
  route='availability_exact_URL';r,err=X.get('https://archive.org/wayback/available',{'url':target,'timestamp':'20220101'})
  if r is not None and r.status_code==200:
   try:
    a=r.json();rec['availability']=a;cap=a.get('archived_snapshots',{}).get('closest',{})
    if cap.get('available') and cap.get('status')=='200':
     route='actual_archived_body';body=X.replay(active,{'original':target,'timestamp':cap['timestamp'],'availability_url':cap['url']});rec['captures_replayed'].append(body)
   except (ValueError,KeyError) as e:rec['availability_parse_error']=str(e)
  else:rec['availability_failure']={'http':r.status_code if r is not None else None,'error':err}
  if cdxfail<3:
   route='CDX_exact_URL_all_available_dates';idx=X.index(active,target);rec['index']=idx
   cdxfail=cdxfail+1 if idx['status']!='index_complete' else 0
   seen={(x.get('capture',{}).get('timestamp'),x.get('original_url')) for x in rec['captures_replayed'] if x}
   # Method test only: verify earliest and latest distinct payload capture; full remaining index retained.
   caps=idx.get('captures',[]);pick=[caps[0],caps[-1]] if caps else []
   for cap in pick:
    key=(cap['timestamp'],cap['original'])
    if key not in seen:
     route='actual_archived_body';rec['captures_replayed'].append(X.replay(active,cap));seen.add(key)
   rec['indexed_captures_unreplayed_by_sample']=max(0,len(caps)-len(seen))
  else:rec['index_status']='not_attempted_after_three_index_failures_backoff'
  rec['elapsed_seconds']=round(time.monotonic()-start,3);rec['finished_at']=X.stamp();X.save(fp,rec);results.append(rec);print(active,'bodies',len(rec['captures_replayed']),'index',rec.get('index',{}).get('status',rec.get('index_status')),rec['elapsed_seconds'],flush=True)
except X.Stop as e:X.save(O/'STOP.json',{'at':X.stamp(),'school_roll':active,'reason':str(e)});print('STOP',str(e),flush=True)
X.save(O/'sample_results.json',{'at':X.stamp(),'selection':selection,'attempted_schools':len(results),'results':results,'requests':calls});print('FINISHED',len(results),flush=True)
