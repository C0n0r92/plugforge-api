#!/usr/bin/env python3
"""Freeze/replay collection metadata and remaining work, offline and idempotently."""
import sys,json,gzip,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from import_database import *
P=D/'milestone2';ds='m2_research_snapshot';packed=D/'inputs'/(ds+'.json.gz')
if not packed.exists():
 data=[];by=collections.defaultdict(list)
 for folder in ['checkpoints','media_followup','pending_notice_followup','seed_followup/checkpoints','unparsed_notice_followup/checkpoints']:
  for f in sorted((P/folder).glob('*.json')):
   r=json.loads(f.read_text())
   if isinstance(r,dict) and r.get('roll') and ('attempts' in r or 'documents' in r):by[r['roll']].append({'checkpoint_path':str(f.relative_to(ROOT)),**r})
 for roll,records in sorted(by.items()):data.append({'record_type':'school_site_checkpoints','roll':roll,'checkpoints':records})
 for folder,pattern in [('exact_archive','index_*.json'),('exact_archive','body_*.json'),('prefix_archive','index_*.json'),('archive_replays','*.json')]:
  for f in sorted((P/folder).glob(pattern)):
   r=json.loads(f.read_text())
   if isinstance(r,dict) and r.get('roll'):data.append({'record_type':'archive_checkpoint','checkpoint_path':str(f.relative_to(ROOT)),'route':folder,'data':r})
 for f in [P/'exact_archive/source_queue.json',P/'exact_archive/capture_queue.json',P/'prefix_archive/source_queue.json',P/'method_audit/sample_status.json',P/'exact_archive/STOP_ACCESS.json',P/'exact_archive/STOP_TRANSIENT.json']:
  if f.exists():data.append({'record_type':'remaining_queue_or_stop','checkpoint_path':str(f.relative_to(ROOT)),'data':json.loads(f.read_text())})
 packed.write_bytes(gzip.compress(js(data).encode(),mtime=0))
I=Importer();I.release='database_m2_research_checkpoint_2026_11_08';I.put('dataset_release',dict(release_id=I.release,label='Milestone2 frozen actual collection attempts, captures and remaining queues',imported_at=now(),source_manifest_sha256=sha(packed.read_bytes()),notes='Operational metadata only, not numeric notice coverage. Archive429stop retained; no retries.'))
data=I.input(ds);known={r[0] for r in I.c.execute('select distinct document_id from observation_group join notice using(notice_id)')}
for idx,r in enumerate(data):
 rid=I.raw(ds,idx,r)
 if r['record_type']=='school_site_checkpoints':
  roll=r['roll'];cp=r['checkpoints'];aa=[a for x in cp for a in x.get('attempts',[])];home=I.c.execute('select website_url from school where roll=?',(roll,)).fetchone()[0];status='attempted_accessible' if any(a['status'] in ['ok','reused_local_verified_payload'] for a in aa) else 'attempted_permission_or_retrieval_failed' if aa else 'no_domain' if not home else 'not_attempted'
  qq=I.c.execute("select task_id from work_queue where roll=? and stage='historical_school_site_archive_navigation'",(roll,)).fetchall()
  for q in qq:I.c.execute('update work_queue set status=?,checkpoint_json=?,updated_at=? where task_id=?',(status,js(r),now(),q[0]))
  for cpidx,x in enumerate(cp):
   for j,a in enumerate(x.get('attempts',[])):
    I.put('collection_attempt',dict(attempt_id=key('m2_official_site',roll,x['checkpoint_path'],j,a['url']),roll=roll,source_id=I.source(a['url']),method=x.get('method') or a.get('via') or 'public_school_site_permission_or_retrieval',attempted_at=None,status=a['status'],exact_status=a['status'],query_text=None,requested_from=None,requested_to=None,coverage_limit='Bounded public linked navigation,robots and confirmed public media; checkpoint stage start retained, per-request timestamp not invented',raw_id=rid,details_json=js({'checkpoint_path':x['checkpoint_path'],'stage_started_at':x.get('started_at'),'attempt':a})))
 elif r['record_type']=='archive_checkpoint':
  x=r['data'];roll=x['roll'];isindex='index_' in Path(r['checkpoint_path']).name;stage='archive_exact_URL_index' if isindex and r['route']=='exact_archive' else 'archive_source_prefix_index' if isindex else 'archive_capture_body_review';u=x.get('original_url') or x.get('original_prefix') or x.get('capture',{}).get('original');cap=x.get('capture',{});ts=cap.get('timestamp');status=x.get('status','unknown')
  h=x.get('payload_sha256',x.get('sha256'));did=key('document',roll,h) if h else None
  if did in known:status='body_reviewed_imported_numeric_or_notice_evidence'
  tid=x.get('task_id') or key(roll,stage,ts,u)
  I.put('work_queue',dict(task_id=tid,roll=roll,stage=stage,source_url=u,document_id=did if did in known else None,status=status,priority=3,checkpoint_json=js(x),updated_at=x.get('attempted_at')))
  I.c.execute('update work_queue set status=?,checkpoint_json=?,updated_at=? where task_id=?',(status,js(x),x.get('attempted_at'),tid))
  I.put('collection_attempt',dict(attempt_id=key('m2_archive_checkpoint',r['checkpoint_path']),roll=roll,source_id=I.source(x.get('archived_url') or u,'public_archive_research'),method=x.get('method') or stage,attempted_at=x.get('attempted_at'),status=x.get('status','unknown'),exact_status=str(x.get('http_status','not_recorded')),query_text=js(x.get('params')) if x.get('params') else None,requested_from=None,requested_to=None,coverage_limit='All available dates for indexed scope; capture timestamp is not academic year. Body is not numeric until reviewed.',raw_id=rid,details_json=js(x)))
I.reconcile();I.c.commit();print('frozen research records',len(data));I.c.close()
