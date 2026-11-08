#!/usr/bin/env python3
"""Lightweight current DB and collection reconciliation; no retrieval and no coverage inflation."""
import json,sqlite3,datetime,collections,zipfile,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent;R=D.parent;at=datetime.datetime.now().astimezone().isoformat();c=sqlite3.connect(D/'admissions.sqlite3');c.row_factory=sqlite3.Row
base=sqlite3.connect(':memory:');base.row_factory=sqlite3.Row
baseline_zip_exists=(D/'dublin-admissions-database-milestone1-2026-11-08.zip').exists()
if baseline_zip_exists:
 with zipfile.ZipFile(D/'dublin-admissions-database-milestone1-2026-11-08.zip') as z:base.deserialize(z.read('database/admissions.sqlite3'))
else:baseline_exact=json.loads((D/'exports/progress.json').read_text())['milestone1_exact_baseline']
core=['places','applications','offers','acceptances','waiting_list_names_placed','waiting_list_remaining','actual_admissions']
def summary(conn):
 rows=[dict(r) for r in conn.execute('select * from v_group_funnel')];num=[r for r in rows if r['academic_year'] and r['supported_metric_count']>0];co=[r for r in num if any(r[k] is not None for k in core)];strict=[r for r in co if r['explicitly_dated'] and r['cohort_matched'] and r['quality']!='user_report_unverified'];retro=[r for r in co if r['phase']=='retrospective'];full=[dict(r) for r in conn.execute('select * from v_comparison_ratios where complete_five_metric_funnel=1')]
 pair=lambda rr:{(r['roll'],r['academic_year']) for r in rr};years=collections.defaultdict(set);sy=collections.defaultdict(set)
 for r in num:years[r['roll']].add(r['academic_year'])
 for r in strict:sy[r['roll']].add(r['academic_year'])
 result={'supported_numeric_school_year_pairs_including_qualified_or_noncore':len(pair(num)),'core_admissions_school_year_pairs':len(pair(co)),'explicitly_dated_cohort_matched_core_pairs':len(pair(strict)),'retrospective_core_school_year_pairs':len(pair(retro)),'strict_retrospective_core_pairs':len(pair([r for r in strict if r['phase']=='retrospective'])),'schools_with_core_admissions_year':len({r['roll'] for r in co}),'schools_with_strict_core_year':len({r['roll'] for r in strict}),'schools_with_supported_numeric_year':len(years),'schools_with_at_least_two_supported_numeric_years':sum(len(v)>=2 for v in years.values()),'schools_with_at_least_two_strict_core_years':sum(len(v)>=2 for v in sy.values()),'full_five_metric_source_groups':len(full),'distinct_full_five_metric_school_year_pairs':len(pair(full)),'oldest_supported_academic_year':min((r['academic_year'] for r in co),default=None),'latest_supported_academic_year':max((r['academic_year'] for r in co),default=None),'academic_years':sorted({r['academic_year'] for r in co}),'counts':{t:conn.execute('select count(*) from '+t).fetchone()[0] for t in ['school','document','notice','observation_group','observation','evidence','raw_record']}}
 return result,rows,num,co,strict,retro,full
now,rows,num,co,strict,retro,full=summary(c);before=summary(base)[0] if baseline_zip_exists else baseline_exact;base.close();gain={k:now[k]-before[k] for k in now if isinstance(now[k],int) and k in before}
# Load actual school records only: FINISHED/source_queue/summary JSON are not schools.
cp=collections.defaultdict(list)
for folder in ['checkpoints','media_followup','pending_notice_followup','seed_followup/checkpoints','unparsed_notice_followup/checkpoints']:
 for f in (P/folder).glob('*.json'):
  r=json.loads(f.read_text())
  if isinstance(r,dict) and r.get('roll') and ('attempts' in r or 'documents' in r):cp[r['roll']].append({'checkpoint_file':str(f.relative_to(R)),**r})
per=[];statuscounts=collections.Counter();removed=[]
for school in c.execute('select roll,name,website_url from school order by roll').fetchall():
 roll=school['roll'];rr=cp[roll];aa=[a for x in rr for a in x.get('attempts',[])];attempted={a['url'] for a in aa};pending={a['url']:a for x in rr for a in x.get('pending_links',[]) if a['url'] not in attempted};sts=collections.Counter(a.get('status','unknown') for a in aa)
 status='attempted_accessible' if any(k in sts for k in ['ok','reused_local_verified_payload']) else 'attempted_permission_or_retrieval_failed' if aa else 'no_domain' if not school['website_url'] else 'not_attempted'
 statuscounts[status]+=1
 def yy(src):return sorted({r['academic_year'] for r in src if r['roll']==roll})
 cy=yy(co);gaps=[]
 if cy:
  y={int(x[:4]) for x in cy};gaps=[str(x)+'/'+str(x+1) for x in range(min(y),max(y)+1) if x not in y]
 item={'roll':roll,'name':school['name'],'website_url':school['website_url'],'supported_numeric_years':yy(num),'core_admissions_years':cy,'strict_dated_cohort_matched_core_years':yy(strict),'retrospective_core_years':yy(retro),'full_five_years':yy(full),'gaps_within_observed_core_year_range_only':gaps,'own_site_status':status,'actual_attempt_status_counts':dict(sts),'attempt_records':len(aa),'pending_link_count_not_assumed_notices':len(pending),'pending_links':list(pending.values()),'checkpoint_files':[x['checkpoint_file'] for x in rr]};per.append(item)
 # Initial task and temporary checkpoint task were duplicate queue entries, not two schools.
 qq=c.execute("select task_id from work_queue where roll=? and stage='historical_school_site_archive_navigation' order by length(task_id) desc,task_id",(roll,)).fetchall()
 if qq:
  keep=qq[0][0]
  for q in qq[1:]:removed.append(q[0]);c.execute('delete from work_queue where task_id=?',(q[0],))
  c.execute('update work_queue set status=?,checkpoint_json=?,updated_at=? where task_id=?',(status,json.dumps(item),at,keep))
# Correct generic importer's previous form-feed page-counter bug. Raw source spans/values unchanged.
pagefix=0
for e in c.execute("select evidence_id,page,text_file,line_start from evidence where method in ('manual_retrieved_historical_table_review','manual_explicit_written_count') and text_file is not null and line_start is not null").fetchall():
 f=R/e['text_file']
 if not f.exists() or 'visual_transcript' in e['text_file']:continue
 page=''.join(f.read_text().splitlines(keepends=True)[:e['line_start']-1]).count('\f')+1
 if page!=e['page']:c.execute('update evidence set page=? where evidence_id=?',(page,e['evidence_id']));pagefix+=1
c.commit()
archive={}
for folder in ['exact_archive','prefix_archive','archive_replays']:
 records=[]
 for f in (P/folder).glob('*.json'):
  r=json.loads(f.read_text())
  if isinstance(r,dict) and r.get('roll') and (r.get('status') or r.get('capture')):records.append(r)
 archive[folder]={'school_rolls_actually_checkpointed':len({r['roll'] for r in records}),'index_attempt_checkpoint_count':sum('index_' in f.name for f in (P/folder).glob('index_*.json')),'body_attempt_checkpoint_count':sum(bool(r.get('capture')) for r in records),'status_counts':dict(collections.Counter(r.get('status','unknown') for r in records))}
stop=P/'exact_archive/STOP_ACCESS.json'
obj={'generated_at':at,'timezone':'Europe/Dublin','definitions':{'supported_numeric':'Any source-evidenced numeric metric, including qualified years, criterion groups, conditional quotas or auxiliary metrics; NOT a complete funnel.','core_admissions':'At least one non-null field among places,applications,offers,acceptances,names placed,list remaining,actual admissions. Unknown-year rows excluded. Accepted is not actual admission.','strict':'Explicitly dated and cohort matched core evidence; no user-report-unverified quality. Further per-metric conflicts/denominator tests apply to comparable ratios.','gaps':'Only absent years between this school oldest/latest observed core year. Earlier/later historical coverage remains unresolved, not implicitly absent.','site_attempted':'Bounded public own-site navigation or permission/retrieval attempts, NOT exhaustive historical search. No-new-found is not proof a notice does not exist.','source_omission':'Missing observation status applies to the reviewed source edition only, not all years for a school.'},'current':now,'milestone1_exact_baseline':before,'gain_vs_milestone1':gain,'own_site_school_statuses':dict(statuscounts),'school_identities':len(per),'pending_public_links_not_assumed_notices':sum(r['pending_link_count_not_assumed_notices'] for r in per),'archive_method_checkpoints':archive,'archive_host_stop':json.loads(stop.read_text()) if stop.exists() else None,'queue_stage_statuses':[dict(r) for r in c.execute('select stage,status,count(*) task_count from work_queue group by stage,status')],'per_school':per,'reconciliation':{'duplicate_school_site_queue_tasks_removed_this_refresh':len(removed),'evidence_page_numbers_corrected_this_refresh':pagefix}}
for f in [P/'progress.json',D/'exports/progress.json']:f.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
if removed or pagefix:(P/('checkpoint_reconciliation_'+at.replace(':','').replace('+','_')+'.json')).write_text(json.dumps({'at':at,'removed_duplicate_task_ids':removed,'page_numbers_corrected':pagefix},indent=2))
print(json.dumps({k:obj[k] for k in ['generated_at','current','gain_vs_milestone1','own_site_school_statuses','pending_public_links_not_assumed_notices','reconciliation']},indent=2));c.close()
