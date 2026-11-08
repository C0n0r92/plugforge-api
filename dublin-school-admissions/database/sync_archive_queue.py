#!/usr/bin/env python3
"""Merge immutable current checkpoint snapshots into the database; does not make network calls."""
from import_database import *
I=Importer();I.release='historical_archive_index_progress';I.datasets={}
I.put('dataset_release',dict(release_id=I.release,label='Incremental all-school public Wayback index discovery; not verified notice bodies',imported_at=now(),source_manifest_sha256=sha(''.join(p.name+sha(p.read_bytes()) for p in sorted((D/'checkpoints/archive_index').glob('*.json')))),notes='All available archive dates, no earliest-year cutoff; capture metadata is candidate discovery only.'))
history=D/'inputs/archive_import_history.json.gz'
if history.exists():
 for raw in json.loads(gzip.decompress(history.read_bytes())):I.put('raw_record',raw)
P=D/'checkpoints/archive_index';snapshots=[]
for fp in sorted(P.glob('*.json')):
 if fp.name.startswith('STOP_'):continue
 state=json.loads(fp.read_text());snapshots.append(state);domain=state['domain'];status=state['status']
 rid=I.raw('archive_domain_checkpoints',domain,state)
 # Preserve each checkpoint revision instead of rewriting raw evidence.
 if I.c.execute('SELECT payload_sha256 FROM raw_record WHERE raw_id=?',(rid,)).fetchone()[0]!=sha(js(state)):
  rid=I.raw('archive_domain_checkpoint_revisions',domain+':'+sha(js(state))[:16],state)
 for roll in state['rolls']:
  u=I.c.execute('SELECT website_url FROM school WHERE roll=?',(roll,)).fetchone()[0]
  task=key(roll,'historical_archive_domain',u or '')
  I.put('work_queue',dict(task_id=task,roll=roll,stage='historical_archive_domain',source_url=u,document_id=None,status=status,priority=2,checkpoint_json=js(state),updated_at=state['updated_at']))
  I.c.execute('UPDATE work_queue SET status=?,checkpoint_json=?,updated_at=? WHERE task_id=?',(status,js(state),state['updated_at'],task))
  sid=I.source('https://'+domain,'school_domain_for_archive_discovery')
  I.put('coverage',dict(coverage_id=key(roll,'archive_index',sha(js(state))),roll=roll,academic_year=None,coverage_dimension='all_available_dates_archive_index',status=status,source_id=sid,as_of=state['updated_at'],scope_limit=state.get('scope') or state.get('reason') or 'Index request did not complete; exact failure in checkpoint',raw_id=rid))
  for capture in state.get('captures',[]):
   url=capture['original'];tid=key(roll,'archive_capture_body_review',capture['timestamp'],url)
   I.put('work_queue',dict(task_id=tid,roll=roll,stage='archive_capture_body_review',source_url=url,document_id=None,status='candidate_index_only',priority=3,checkpoint_json=js(capture),updated_at=state['updated_at']))
 if state.get('last_request'):
  e=state['last_request']
  for roll in state['rolls']:I.put('collection_attempt',dict(attempt_id=key(roll,e),roll=roll,source_id=I.source(e.get('url'),'official_archive_CDX_API'),method=e.get('method','Wayback_CDX'),attempted_at=e.get('attempted_at'),status=status,exact_status=str(e.get('http_status')),query_text=js(e.get('params')),requested_from=None,requested_to=None,coverage_limit='All available dates; index is not exhaustive and captures are not verified notices; paginated200',raw_id=rid,details_json=js(e)))
for ds in ['archive_domain_checkpoints','archive_domain_checkpoint_revisions']:
 count=I.c.execute('SELECT COUNT(*) FROM raw_record WHERE release_id=? AND dataset=?',(I.release,ds)).fetchone()[0]
 if count:I.datasets[ds]=count
I.reconcile();I.c.commit()
from collections import Counter
summary={'as_of':now(),'timezone':'Europe/Dublin','domains_checkpointed':len(snapshots),'domain_statuses':dict(Counter(s['status'] for s in snapshots)),'schools_checkpointed':len(set(r for s in snapshots for r in s['rolls'])),'indexed_candidate_captures':sum(len(s.get('captures',[])) for s in snapshots),'new_archive_bodies_verified_in_this_expansion':0,'ongoing_worker_log':'checkpoints/archive_worker.log','note':'Pilot actual bodies are already imported separately. Index-only candidates require replay, document identity/year/cohort and numeric evidence review.'}
(D/'exports/archive_progress.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));I.c.close()
