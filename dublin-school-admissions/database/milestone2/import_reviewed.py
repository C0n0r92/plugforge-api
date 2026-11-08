#!/usr/bin/env python3
"""Import one frozen manually reviewed discovery batch; offline and idempotent."""
import sys,json,gzip,re,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from import_database import *
P=D/'milestone2';batch=sys.argv[1];path=P/(batch+'.json');data=json.loads(path.read_text());I=Importer();I.release='database_'+batch
I.put('dataset_release',dict(release_id=I.release,label='Milestone2 source-reviewed historical recovery: '+batch,imported_at=now(),source_manifest_sha256=sha(path.read_bytes()),notes='Actual retrieved historical source bodies manually reviewed. Same source/year/cohort groups only; no aggregate sums or inferred waiting movement.'))
data=I.input(batch,data=data);I.school_records={r['roll_number']:r for r in json.loads(gzip.decompress((D/'inputs/v4_primary.json.gz').read_bytes()))}
for i,b in enumerate(data):
 rid=I.raw(batch,i,b,'normalized' if b.get('groups') else 'excluded',b.get('exclusion_reason'))
 did=I.doc(b['roll'],b['url'],b.get('sha256'),b.get('format'));sid=I.source(b['url']);ts=b.get('capture_timestamp');parsed=bool(b.get('text_file'))
 if b.get('retrieval_url'):
  dt=datetime.datetime.strptime(ts,'%Y%m%d%H%M%S').replace(tzinfo=datetime.timezone.utc).astimezone(ZoneInfo('Europe/Dublin')).isoformat() if ts else None
  I.put('retrieval',dict(retrieval_id=key(did,b['retrieval_url'],ts),document_id=did,source_id=sid,retrieval_url=b['retrieval_url'],retrieval_kind='archive_capture' if ts else 'official_school_public',retrieved_at=b.get('retrieved_at'),http_status=b.get('http_status',200),payload_sha256=b.get('sha256'),local_payload_path=b.get('source_file'),archive_capture_timestamp=ts,archive_capture_time_dublin=dt,memento_datetime_header=b.get('memento_datetime_header'),body_verified=int(parsed),notes='Capture time is not publication time or academic year. Original URL retained separately.'))
 if not b.get('groups'):continue
 text=(ROOT/b['text_file']).read_text();lines=text.splitlines()
 for g in b['groups']:
  lo=g.get('lo',1);hi=min(g.get('hi',len(lines)),len(lines));excerpt='\n'.join(lines[lo-1:hi]);assert excerpt.strip(),(i,g)
  q={'roll_number':b['roll'],'notice_url':b['url'],'school_year':g.get('title') or b.get('title'),'notes':[g.get('notes','')],'evidence':[{'source_url':b['url'],'source_sha256':b.get('sha256')}]}
  gid,_=I.group(q,rid,g['phase'],g['cohort'],g.get('year'),g.get('year_status') or ('explicit_source_year' if g.get('year') else 'ambiguous_conflicting_printed_years'),g.get('scope','whole_table'),did,g.get('quality','high'))
  I.c.execute('UPDATE observation_group SET year_status=? WHERE group_id=?',(g.get('year_status') or ('explicit_source_year' if g.get('year') else 'ambiguous_or_unprinted_year_not_inferred'),gid))
  if g.get('as_of'):I.c.execute('UPDATE observation_group SET as_of=? WHERE group_id=?',(g['as_of'],gid))
  for metric,detail in g['metrics'].items():
   v=detail.get('value') if isinstance(detail,dict) else detail;word=detail.get('word') if isinstance(detail,dict) else None
   definition=g.get('metric_definitions',{}).get(metric)
   if definition:I.put('metric_definition',dict(metric_code=metric,label=metric.replace('_',' '),definition=definition))
   ev=dict(field=metric,value=v,source_url=b['url'],source_sha256=b.get('sha256'),excerpt=excerpt,text_file=b['text_file'],line_start=lo,line_end=hi,page=g.get('page',''.join(text.splitlines(keepends=True)[:lo-1]).count('\f')+1),method='manual_explicit_written_count' if word else 'manual_retrieved_historical_table_review',source_written_word=word)
   eid=I.evidence(ev,did,rid);assert I.c.execute('select verified_excerpt from evidence where evidence_id=?',(eid,)).fetchone()[0]==1,(i,metric,v,lo,hi)
   I.obs(gid,did,rid,metric,metric,v,[ev],qualifier=g.get('notes',''),status=detail.get('status','not_published') if isinstance(detail,dict) else 'not_published',asof=g.get('as_of'))
I.reconcile();I.c.commit();print(batch,'raw',len(data),'source groups',sum(len(b.get('groups',[])) for b in data),'metrics',sum(len(g['metrics']) for b in data for g in b.get('groups',[])));I.c.close()
