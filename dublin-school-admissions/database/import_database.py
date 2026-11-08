#!/usr/bin/env python3
"""Idempotent normalized import of local validated school-admission evidence. No network."""
import sqlite3,json,gzip,hashlib,re,csv,datetime,sys,os
from pathlib import Path
from urllib.parse import urlsplit
D=Path(__file__).resolve().parent;ROOT=D.parent;DB=Path(os.environ.get('DUBLIN_ADMISSIONS_DB',str(D/'admissions.sqlite3')))
def js(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def key(*x):return sha(js(x))[:32]
def now():return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
def norm(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def year(y):
 m=re.search(r'\b((?:19|20)\d{2})\s*[/–-]\s*(\d{2,4})\b',str(y or ''))
 if not m:return None
 a=int(m[1]);b=int(m[2]);b=b if b>99 else a//100*100+b
 return f'{a}/{b}' if b==a+1 else None
class Importer:
 def __init__(self):
  self.c=sqlite3.connect(DB);self.c.execute('PRAGMA foreign_keys=ON');self.c.execute('PRAGMA busy_timeout=15000')
  self.c.execute('CREATE TABLE IF NOT EXISTS schema_migration(version INTEGER PRIMARY KEY,name TEXT NOT NULL,sha256 TEXT NOT NULL)')
  for p in sorted((D/'migrations').glob('*.sql')):
   version=int(p.name.split('_')[0]);digest=sha(p.read_bytes());prior=self.c.execute('SELECT sha256 FROM schema_migration WHERE version=?',(version,)).fetchone()
   if prior:
    if prior[0]!=digest:raise RuntimeError('Applied migration checksum changed: '+p.name)
    continue
   self.c.executescript(p.read_text());self.put('schema_migration',{'version':version,'name':p.name,'sha256':digest});self.c.commit()
  # Upgrade task identities from the prototype URL-only key to source-edition keys.
  for row in self.c.execute("SELECT task_id,roll,stage,source_url,document_id FROM work_queue WHERE stage IN ('local_notice_review','source_ambiguity_resolution')").fetchall():
   old_id,roll,stage,url,did=row;new_id=key(roll,stage,url,did)
   if old_id!=new_id:
    if self.c.execute('SELECT 1 FROM work_queue WHERE task_id=?',(new_id,)).fetchone():self.c.execute('DELETE FROM work_queue WHERE task_id=?',(old_id,))
    else:self.c.execute('UPDATE work_queue SET task_id=? WHERE task_id=?',(new_id,old_id))
  self.school_records={};self.doc_index={};self.datasets={};self.evidence_cache={}
 def put(self,t,r):
  self.c.execute(f"INSERT OR IGNORE INTO {t} ({','.join(r)}) VALUES ({','.join('?' for _ in r)})",tuple(r.values()))
  if t=='evidence':self.c.execute('UPDATE evidence SET verified_excerpt=?,text_file_sha256=? WHERE evidence_id=?',(r['verified_excerpt'],r.get('text_file_sha256'),r['evidence_id']))
  if t=='cohort':self.c.execute('UPDATE cohort SET intake_kind=?,special_needs_label=?,scope_confirmed=? WHERE cohort_id=?',(r['intake_kind'],r.get('special_needs_label'),r['scope_confirmed'],r['cohort_id']))
  if t=='observation_group':
   if r.get('year_status')=='explicit_source_year':self.c.execute("UPDATE observation_group SET year_status='explicit_source_year' WHERE group_id=?",(r['group_id'],))
   self.c.execute('UPDATE observation_group SET preferred_source_rank=MAX(preferred_source_rank,?) WHERE group_id=?',(r.get('preferred_source_rank',0),r['group_id']))
  return next(iter(r.values()))
 def source(self,u,kind='official_school_public'):
  if not u:return None
  sid=key('source',u,kind);self.put('source',dict(source_id=sid,original_url=u,domain=urlsplit(u).hostname,source_kind=kind));return sid
 def raw(self,ds,idx,r,status='normalized',reason=None):
  rid=key(self.release,ds,str(idx));self.put('raw_record',dict(raw_id=rid,release_id=self.release,dataset=ds,record_key=str(idx),payload_json=js(r),payload_sha256=sha(js(r)),normalization_status=status,exclusion_reason=reason));return rid
 def input(self,ds,path=None,data=None):
  if data is None:
   packed=D/'inputs'/f'{ds}.json.gz'
   if packed.exists():data=json.loads(gzip.decompress(packed.read_bytes()))
   else:
    p=ROOT/path
    data=list(csv.DictReader(p.open())) if p.suffix=='.csv' else json.loads(p.read_text())
  if isinstance(data,dict):data=[{'input_key':k,**v} for k,v in data.items()]
  packed=D/'inputs'/f'{ds}.json.gz'
  if not packed.exists():packed.write_bytes(gzip.compress(js(data).encode(),mtime=0))
  self.datasets[ds]=len(data);return data
 def school(self,r,rid=None):
  roll=r.get('roll_number') or r.get('roll');name=r.get('school_name') or roll
  self.put('school',dict(roll=roll,name=name,roster_status=r.get('roster_status'),geographic_scope=r.get('geographic_scope_classification'),website_url=r.get('website_url') or r.get('website_candidate')))
  if rid:
   sid=self.source(r.get('official_gis_metadata_source_url'),'official_department_roster')
   for field,typ in [('school_name','roster_name'),('official_gis_school_name','official_gis_name')]:
    if r.get(field):self.put('school_identity',dict(identity_id=key(roll,typ,r[field]),roll=roll,name=r[field],identity_type=typ,source_id=sid,raw_id=rid,quality='sourced_roster_label',valid_from=None,valid_to=None))
   if any(r.get(x) for x in ['address','latitude','longitude']):
    self.put('school_location',dict(location_id=key(roll,'location',r.get('latitude'),r.get('longitude'),r.get('address')),roll=roll,address=r.get('address'),eircode=r.get('eircode'),latitude=r.get('latitude'),longitude=r.get('longitude'),as_of=str(r.get('official_gis_source_year') or '') or None,as_of_precision='year' if r.get('official_gis_source_year') else None,source_id=sid,raw_id=rid,boundary_caveat='School point, not a catchment. Source geography/version may differ from current administrative boundaries; school address does not establish eligibility.'))
   for field in ['school_type','official_gis_primary_level','official_gis_primary_type','county','local_authority','intake_applicability','junior_infants_applicability']:
    if r.get(field):self.put('school_metadata',dict(metadata_id=key(roll,field,r[field]),roll=roll,attribute=field,value_text=str(r[field]),as_of=str(r.get('official_gis_source_year') or '') or None,source_id=sid,raw_id=rid,quality='official_gis_sourced' if field.startswith('official_gis') else 'baseline_roster_or_review_classification'))
  return roll
 def doc(self,roll,url,h=None,fmt=None,raw=None,kind='official_school_public'):
  if not roll:return None
  self.school({'roll_number':roll})
  sid=self.source(url,kind);identity=h or 'unhashed:'+str(url)
  did=key('document',roll,identity)
  self.put('document',dict(document_id=did,roll=roll,payload_sha256=h,identity_key=identity,media_type=fmt,identity_quality='payload_hash_and_school_identity' if h else 'unhashed_source_identity_only'))
  if sid:self.put('document_source',dict(document_id=did,source_id=sid))
  return did
 def evidence(self,ev,did,raw=None):
  if not isinstance(ev,dict):return None
  sid=self.source(ev.get('source_url'));textpath=ev.get('text_file');text='';th=None
  if textpath:
   p=ROOT/textpath
   if not p.exists():p=D/textpath.removeprefix('database/')
   if p.exists():
    text=p.read_text(errors='replace');th=sha(p.read_bytes())
  excerpt=str(ev.get('excerpt') or '');verified=int(bool(excerpt) and (norm(excerpt) in norm(text) or ev.get('pilot_verified') is True))
  if textpath and not text and ev.get('verified_existing_review'):verified=0
  if isinstance(ev.get('value'),int) and not re.search(r'(?<![0-9])'+str(ev['value'])+r'(?![0-9])',excerpt.replace(',','')):
   # A reviewed explicit written count is source evidence, not an arithmetic inference.
   words={'one':1,'two':2,'three':3,'beirt':2,'cúigear':5,'none':0}
   word=str(ev.get('source_written_word') or '').lower()
   if not (ev.get('method')=='manual_explicit_written_count' and words.get(word)==ev['value'] and re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)',excerpt,re.I)):verified=0
  if any(w in str(ev.get('method','')).lower() for w in ['sum_','derived','inferred']):verified=0
  eid=key('evidence',did,ev.get('field'),ev.get('page'),ev.get('line_start'),excerpt,ev.get('source_sha256'))
  self.put('evidence',dict(evidence_id=eid,document_id=did,source_id=sid,source_field=ev.get('field'),source_value_json=js(ev.get('value')),page=ev.get('page'),line_start=ev.get('line_start'),line_end=ev.get('line_end'),excerpt=excerpt,source_payload_sha256=ev.get('source_sha256'),text_file=textpath,text_file_sha256=th,method=ev.get('method'),verified_excerpt=verified,year_evidence=int('year' in str(ev.get('field')))))
  return eid
 def cohort(self,roll,label):
  label=norm(label) or 'Unspecified intake (not inferred)';low=label.lower()
  special=any(x in low for x in ['autism','asd','as class','special','disabil','dld','speech','language class','reading-school']) or self.school_records.get(roll,{}).get('school_type')=='special_school'
  ambiguous=any(x in low for x in ['ambiguous','unseparated','not distinguished','combined','all listed','joint ','dual enrolment','including asd','other year group','preceding']) or label.startswith('Unspecified')
  k='special' if special else 'junior_infants' if any(x in low for x in ['junior infant','naíonáin shóisearacha']) else 'senior' if any(x in low for x in ['third','second','fourth','fifth','sixth','senior','first class']) else 'other_or_unspecified'
  needs=label if any(x in low for x in ['autism','asd','disabil','dld','speech','language class','reading-school']) else None;cid=key(roll,label)
  self.put('cohort',dict(cohort_id=cid,roll=roll,source_label=label,intake_kind=k,special_needs_label=needs,scope_confirmed=int(not ambiguous and k!='other_or_unspecified')));return cid,int(not ambiguous and k!='other_or_unspecified')
 def group(self,r,rid,phase,cohort,yr,yearstatus,scope='whole_table',did=None,quality=None):
  roll=r['roll_number'];url=r.get('notice_url');evs=r.get('evidence',[])
  if isinstance(evs,dict):evs=[evs]
  hs={e.get('source_sha256') for e in evs if e.get('source_sha256') and (not url or e.get('source_url')==url)}
  h=next(iter(hs)) if len(hs)==1 else next((e.get('source_sha256') for e in evs if e.get('source_sha256')),None)
  did=did or self.doc(roll,url,h,r.get('source_format'));title=year(r.get('school_year') or r.get('notice_school_year'));nid=key(did,'annual_notice')
  self.put('notice',dict(notice_id=nid,document_id=did,title_school_year=title,publication_time=r.get('publication_date'),publication_precision='day' if r.get('publication_date') else None,identity_verified=int(r.get('validation_status')!='automated_candidates_only')))
  if title:self.put('notice_title_assertion',dict(assertion_id=key(nid,title,rid),notice_id=nid,title_school_year=title,raw_id=rid))
  self.c.execute('UPDATE notice SET title_school_year=(SELECT CASE WHEN COUNT(DISTINCT title_school_year)=1 THEN MIN(title_school_year) END FROM notice_title_assertion WHERE notice_id=?) WHERE notice_id=?',(nid,nid))
  cid,matched=self.cohort(roll,cohort);yr=year(yr);pid=key(roll,yr,cid)
  self.put('school_period',dict(period_id=pid,roll=roll,academic_year=yr,year_start=int(yr[:4]) if yr else None,cohort_id=cid))
  quality=quality or r.get('quality_override') or r.get('quality') or 'medium';asof=r.get('previous_waiting_list_snapshot_date') if phase=='retrospective' else None
  if asof:scope+=' | snapshot:'+str(asof)
  gid=key(nid,pid,phase,scope);era='pre_2020_definitions_require_review' if yr and int(yr[:4])<2020 else 'annual_notice_2020_onward' if yr else 'undated'
  self.put('observation_group',dict(group_id=gid,notice_id=nid,period_id=pid,phase=phase,table_scope=scope,as_of=asof,year_status=yearstatus if yr else 'ambiguous_or_unprinted_year_not_inferred',cohort_matched=matched,quality=quality,preferred_source_rank=int(bool(r.get('selected_for_main_record') or r.get('selected_notice_for_main_record') or r.get('used_in_selected_historical_funnel'))),review_notes=js(r.get('notes',[])),definition_era=era))
  self.put('group_lineage',dict(group_id=gid,raw_id=rid))
  for ev in evs:self.evidence(ev,did,rid)
  return gid,did
 def obs(self,gid,did,rid,field,metric,value,evs,status=None,qualifier='',asof=None,quality='source_review'):
  if isinstance(value,bool):value=None
  if not isinstance(value,int):value=None
  evs=[ev for ev in evs if isinstance(ev,dict) and ev.get('field')==field]
  state='observed' if value is not None else status or 'not_recorded'
  if state=='observed' and value is None:state='ambiguous'
  oid=key(gid,metric,value,state,qualifier,asof)
  self.put('observation',dict(observation_id=oid,group_id=gid,metric_code=metric,value_integer=value,value_status=state,definition_qualifier=qualifier,as_of=asof,quality=quality))
  self.put('observation_lineage',dict(observation_id=oid,raw_id=rid,source_field=field))
  for ev in evs:
   eid=self.evidence(ev,did,rid);self.put('observation_evidence',dict(observation_id=oid,evidence_id=eid))
  return oid
 def import_record(self,r,rid,only_history=False,_source_partitioned=False):
  roll=r.get('roll_number');evs=r.get('evidence') or []
  if isinstance(evs,dict):evs=[evs]
  if not r.get('notice_url'):
   return
  # A selected school record may borrow history from a DIFFERENT notice. Partition before
  # grouping: raw values from different payloads/revisions must never form one funnel.
  if not _source_partitioned:
   partitions={}
   for e in evs:
    h=e.get('source_sha256')
    if h:partitions.setdefault(h,[]).append(e)
   if len(partitions)>1:
    numeric_fields=[k for k,v in r.items() if isinstance(v,int) and not isinstance(v,bool) and (k.startswith('previous_') or k.startswith('waiting_list_') or k in ['junior_infants_places','upcoming_intake_places','special_class_places','vacated_places_reoffered_to_waiting_list'])]
    covered=set()
    for h,ee in partitions.items():
     q=dict(r);q['evidence']=ee;q['notice_url']=next((e.get('source_url') for e in ee if e.get('source_url')),r['notice_url'])
     own_fields={e.get('field') for e in ee};covered.update(own_fields)
     for field in numeric_fields:
      if field not in own_fields:q[field]=None
     q['school_year']=next((e.get('value') for e in ee if e.get('field')=='school_year'),None)
     q['special_class_details']=[]
     if not any(e.get('field')=='previous_school_year' for e in ee):q['historical_table_year_status']='unconfirmed_year_requires_evidence'
     self.import_record(q,rid,only_history,_source_partitioned=True)
    # Values lacking a field-level payload link survive as unsupported observations,
    # never as eligible comparable numbers. Full original records also survive raw.
    missing=[f for f in numeric_fields if f not in covered]
    if missing:
     q=dict(r);q['evidence']=[];q['quality']='unattributed_source_counts';q['special_class_details']=[];q['historical_table_year_status']='unconfirmed_year_requires_evidence'
     for field in numeric_fields:
      if field not in missing:q[field]=None
     self.import_record(q,rid,only_history,_source_partitioned=True)
    return
  def dated(field,y):
   y=year(y)
   if not y:return 'ambiguous_or_unprinted_year_not_inferred'
   for ev in evs:
    if ev.get('field')==field and year(ev.get('value'))==y and year(ev.get('excerpt'))==y and 'infer' not in str(ev.get('method','')):return 'explicit_source_year'
   return 'unconfirmed_year_requires_evidence'
  historyfields={'previous_places_available':'places','previous_junior_infants_places':'places','previous_applications_received':'applications','previous_offers_made':'offers','previous_offers_accepted':'acceptances','previous_waiting_list':'waiting_list_names_placed','previous_registration_interest_forms_received':'registrations_of_interest'}
  if not only_history and any(r.get(f) is not None for f in ['junior_infants_places','upcoming_intake_places','special_class_places']):
   y=r.get('school_year');yc=dated('school_year',y)
   for fields,cohort in [(['junior_infants_places'],'Junior Infants'),(['upcoming_intake_places'],r.get('upcoming_intake_class')),(['special_class_places'],'Special class (type unspecified in aggregate field)')]:
    for f in fields:
     if r.get(f) is not None:
      g,d=self.group(r,rid,'upcoming',cohort,y,yc);self.obs(g,d,rid,f,'places',r[f],evs)
  has_history=any(r.get(f) is not None for f in historyfields) or only_history
  if has_history:
   cohort=r.get('previous_intake_class');y=r.get('previous_school_year');yc=r.get('historical_table_year_status') or dated('previous_school_year',y)
   scope=r.get('previous_waiting_list_snapshot_label') or 'whole_table'
   g,d=self.group(r,rid,'retrospective',cohort,y,yc,scope)
   for f,m in historyfields.items():
    if f=='previous_junior_infants_places' and r.get(f) is None:continue
    if f=='previous_registration_interest_forms_received' and r.get(f) is None:continue
    met=m
    qualifier=''
    if f=='previous_applications_received' and 'registration' in str(r.get('previous_applications_metric','')).lower():met='registrations_of_interest'
    if f=='previous_waiting_list':
     label=str(r.get('previous_waiting_list_metric') or '')
     if any(t in label.lower() for t in ['remaining','snapshot','current','final']):met='waiting_list_remaining'
     elif label and 'names_placed' not in label and 'names placed' not in label:met='waiting_list_unspecified'
     qualifier=label
    st=str((r.get('historical_field_status') or {}).get(f,''));status='not_published' if st.startswith('not_published') else 'not_applicable' if 'not_applicable' in st else 'ambiguous' if 'ambiguous' in st else 'not_recorded'
    self.obs(g,d,rid,f,met,r.get(f),evs,status=status,qualifier=qualifier,asof=r.get('previous_waiting_list_snapshot_date') if f=='previous_waiting_list' else None)
  eventmap={'waiting_list_offers_made':'waiting_list_offers','waiting_list_offers_accepted':'waiting_list_acceptances','waiting_list_admissions':'waiting_list_actual_admissions','vacated_places_reoffered_to_waiting_list':'vacated_places_reoffered','waiting_list_removed_other_school_offers':'waiting_list_removed_other_school_offer'}
  for f,m in eventmap.items():
   if r.get(f) is not None:
    y=r.get('waiting_list_movement_school_year') or r.get('previous_school_year');yc=dated('previous_school_year',y)
    g,d=self.group(r,rid,'waiting_event',r.get('previous_intake_class'),y,yc,r.get('waiting_list_movement_scope') or 'exact_waiting_event_scope')
    self.obs(g,d,rid,f,m,r[f],evs,qualifier=str(r.get('waiting_list_movement_scope') or ''),asof=r.get('waiting_list_movement_snapshot_date'))
  # Structured special-class detail is kept separately, not collapsed into mainstream capacity.
  for i,detail in enumerate(r.get('special_class_details') or []):
   if not isinstance(detail,dict):continue
   y=detail.get('school_year');g,d=self.group(r,rid,'upcoming' if year(y)==year(r.get('school_year')) else 'retrospective',detail.get('class'),y,'unconfirmed_year_requires_evidence','structured_special_detail')
   for f,m in [('places','places'),('applications','applications'),('offers_made','offers'),('waiting_list','waiting_list_unspecified'),('removed_after_accepting_other_schools','waiting_list_removed_other_school_offer')]:
    if detail.get(f) is not None:self.obs(g,d,rid,'special_class_details.'+str(i)+'.'+f,m,detail[f],[],quality='structured_detail_without_field_evidence_link')
 def attempts(self,r,rid):
  roll=r['roll_number']
  for a in r.get('v4_deep_attempts',[]):
   sid=self.source(a.get('url'));exact=str(a.get('status','not_recorded'));stat='blocked' if any(t in exact for t in ['robots_disallow','antibot','captcha','access_denied','403']) else 'attempted_success' if exact in ['ok','http_200'] else 'retrieval_failed'
   self.put('collection_attempt',dict(attempt_id=key(roll,'v4_deep',a),roll=roll,source_id=sid,method='v4_own_site_discovery',attempted_at=r.get('collected_date'),status=stat,exact_status=exact,coverage_limit='Bounded prior own-site discovery; not exhaustive publication coverage',raw_id=rid,details_json=js(a)))
  outcome=r.get('individual_research_outcome') or r.get('v4_website_notice_outcome') or 'not_attempted'
  self.put('coverage',dict(coverage_id=key(roll,'v4_notice_coverage'),roll=roll,academic_year=None,coverage_dimension='v4_notice_discovery',status=str(outcome),source_id=self.source(r.get('website_url')),as_of=r.get('collected_date'),scope_limit=str(r.get('individual_research_bound') or 'bounded v4 own-site research; no claim all historical years searched'),raw_id=rid))
 def reconcile(self):
  for ds,count in self.datasets.items():
   rr=self.c.execute('SELECT COUNT(*),SUM(normalization_status<>\'excluded\'),SUM(normalization_status=\'excluded\') FROM raw_record WHERE release_id=? AND dataset=?',(self.release,ds)).fetchone()
   self.c.execute('INSERT OR REPLACE INTO import_reconciliation VALUES(?,?,?,?,?,?)',(self.release,ds,count,rr[0],rr[1] or 0,rr[2] or 0));assert count==rr[0] and count==(rr[1] or 0)+(rr[2] or 0),(ds,count,rr)
 def baseline(self):
  self.release='v4_plus_wayback_pilot_baseline';self.put('dataset_release',dict(release_id=self.release,label='Immutable v4 validated baseline and separate verified Wayback pilot',imported_at=now(),source_manifest_sha256='627b3b0d6a3332f65f44fd113e838d5a73b76d535932ae0fd41385ec044391de',notes='Original v4/pilot preserved. Raw inputs retained and reconciled. Capture dates do not imply publication dates.'))
  definitions={'places':'Places available in this exact source table, cohort, period and revision; upcoming/retrospective separated at group level.','applications':'Applications received; excludes registrations of interest. Qualifiers retained.','offers':'Offers made, not pupils admitted.','acceptances':'Accepted offers; NOT actual observed admissions.','actual_admissions':'Explicitly observed admissions/enrolment only. Never inferred from acceptances.','waiting_list_names_placed':'Names placed on list during the stated process; not necessarily remaining at a snapshot.','waiting_list_remaining':'Names remaining/current/final at explicitly qualified snapshot.','waiting_list_unspecified':'Printed waiting-list quantity without sufficiently established names-ever-placed vs remaining definition.','registrations_of_interest':'Registrations/expressions of interest, NOT applications.','waiting_list_offers':'Explicit offers to waiting-list applicants.','waiting_list_acceptances':'Explicit acceptance of waiting-list offers; NOT actual admissions.','waiting_list_actual_admissions':'Explicit admissions from waiting list; not inferred.','vacated_places_reoffered':'Vacated places explicitly reoffered, not necessarily admissions.','waiting_list_removed_other_school_offer':'Explicit removals after accepting other-school offers; not inferred as a difference.'}
  for m,d in definitions.items():self.put('metric_definition',dict(metric_code=m,label=m.replace('_',' '),definition=d))
  data=self.input('v4_primary','data/admissions.json')
  for i,r in enumerate(data):
   rid=self.raw('v4_primary',r['roll_number'],r);self.school_records[r['roll_number']]=r;self.school(r,rid)
  for r in data:
   rid=key(self.release,'v4_primary',r['roll_number']);self.import_record(r,rid);self.attempts(r,rid)
  for ds,path in [('v4_reviewed_editions','data/reviewed_notice_editions_v4.json'),('v4_historical_tables','data/historical_funnel_by_notice_v4.json')]:
   for i,r in enumerate(self.input(ds,path)):
    rid=self.raw(ds,i,r);self.import_record(r,rid,only_history=ds=='v4_historical_tables')
  for i,r in enumerate(self.input('v4_review_archive','sources/v4_notice_reviews.json')):
   rid=self.raw('v4_review_archive',r['input_key'],r);q=dict(r.get('review_record') or {});q['roll_number']=r['roll_number'];q['selected_for_main_record']=r.get('selected_for_main_record');self.import_record(q,rid)
  inventory=self.input('v4_notice_inventory','data/notice_inventory.json')
  for i,r in enumerate(inventory):
   rid=self.raw('v4_notice_inventory',i,r);roll=r.get('roll_number') or r.get('roll');did=self.doc(roll,r.get('url'),r.get('sha256'),r.get('format'),rid)
   if r.get('source_file'):
    sid=self.source(r.get('url'));self.put('retrieval',dict(retrieval_id=key(sid,r.get('sha256'),'prior_local_payload'),document_id=did,source_id=sid,retrieval_url=r.get('url'),retrieval_kind='prior_local_school_retrieval',http_status=200,payload_sha256=r.get('sha256'),local_payload_path=r.get('source_file'),body_verified=int((ROOT/r['source_file']).exists()),notes='Payload captured in prior collection; exact retrieval timestamp not available in this inventory.'))
  for i,r in enumerate(self.input('v4_waiting_events','data/waiting_list_events_v4.json')):
   rid=self.raw('v4_waiting_events',i,r);f=r.get('metric');q={'roll_number':r['roll_number'],'notice_url':r.get('source_url'),'school_year':r.get('notice_school_year'),'previous_school_year':r.get('event_school_year'),'waiting_list_movement_school_year':r.get('event_school_year'),'previous_intake_class':r.get('intake_class'),'waiting_list_movement_scope':r.get('scope'),'evidence':[r.get('evidence')],f:r.get('value')};self.import_record(q,rid)
  for i,r in enumerate(self.input('v4_screenshot_reference','data/user_provided_screenshot_funnels.json')):self.raw('v4_screenshot_reference',i,r,'excluded','User-reported screenshot expectations, not original-source/visual verified. Preserved as reference, never in comparable observations.')
  for i,r in enumerate(self.input('v4_predecessors','data/historical_predecessors.csv')):
   rid=self.raw('v4_predecessors',i,r);self.school(r)
   # Exact predecessor->successor links require explicit proof; do not infer by shared website.
   self.put('school_metadata',dict(metadata_id=key(r['roll_number'],'predecessor_status'),roll=r['roll_number'],attribute='historical_predecessor_status',value_text=r.get('roster_status'),raw_id=rid,source_id=self.source(r.get('website_discovery_source'),'public_directory'),quality='baseline_predecessor_flag_relationship_requires_explicit_link'))
  for i,r in enumerate(self.input('v4_local_review_backlog','data/retrieved_notice_edition_review_backlog_v4.json')):
   rid=self.raw('v4_local_review_backlog',i,r);did=self.doc(r['roll'],r['url'],r.get('sha256'),r.get('format'));self.put('work_queue',dict(task_id=key(r['roll'],'local_notice_review',r['url'],did),roll=r['roll'],stage='local_notice_review',source_url=r['url'],document_id=did,status='pending',priority=1,checkpoint_json=js(r),updated_at=now()))
  for i,r in enumerate(self.input('wayback_pilot','wayback-pilot/historical_test_table.json')):self.pilot(r,self.raw('wayback_pilot',i,r))
  self.pilot_captures()
  for roll,r in self.school_records.items():
   u=r.get('website_url') or r.get('website_candidate')
   self.put('work_queue',dict(task_id=key(roll,'historical_archive_domain',u or ''),roll=roll,stage='historical_archive_domain',source_url=u,document_id=None,status='pending' if u else 'no_domain',priority=2,checkpoint_json=js({'earliest_year_cutoff':None,'scope':'All available indexed public admission notices; domain search not yet executed in this database expansion','not_exhaustive':True}),updated_at=now()))
  # Historical predecessor domains also receive their own all-available-years task.
  for roll,u in self.c.execute('SELECT roll,website_url FROM school').fetchall():
   self.put('work_queue',dict(task_id=key(roll,'historical_archive_domain',u or ''),roll=roll,stage='historical_archive_domain',source_url=u,document_id=None,status='pending' if u else 'no_domain',priority=2,checkpoint_json=js({'earliest_year_cutoff':None,'scope':'All available dates including predecessor identity'}),updated_at=now()))
  # Separate original-site historical archive navigation from archive-index research.
  for roll,u in self.c.execute('SELECT roll,website_url FROM school').fetchall():
   self.put('work_queue',dict(task_id=key(roll,'historical_school_site_archive_navigation',u or ''),roll=roll,stage='historical_school_site_archive_navigation',source_url=u,document_id=None,status='pending_historical_archive_navigation' if u else 'no_domain',priority=3,checkpoint_json=js({'scope':'Public original-school historical admissions links/navigation across all available years; prior v4 own-site attempts retained separately','earliest_year_cutoff':None,'robots_recheck_required':True}),updated_at=now()))
  # Existing source-reviewed amalgamations: historical identities remain separate schools.
  for idx,rel in enumerate(self.input('v4_amalgamation_evidence','sources/roster_reconciliation_evidence.json')):
   rid=self.raw('v4_amalgamation_evidence',rel['input_key'],rel)
   if not rel.get('successor'):continue
   for predecessor in rel.get('predecessors',[]):
    self.put('school_relation',dict(relation_id=key(predecessor,rel['successor'],'amalgamation'),predecessor_roll=predecessor,successor_roll=rel['successor'],relationship='amalgamated_into',effective_date=rel.get('effective_date') or str(rel.get('year') or '') or None,date_precision='day' if rel.get('effective_date') else 'year',source_id=self.source(rel.get('source_url'),'public_amalgamation_announcement'),evidence_excerpt=rel.get('excerpt') or rel.get('school_announcement_excerpt') or 'See source-reviewed roster reconciliation',raw_id=rid))
  self.reconcile();self.c.commit()
 def pilot(self,r,rid):
  roll=r['roll_number'];did=self.doc(roll,r['original_url'],r['payload_sha256'],'application/pdf' if '.pdf' in r['original_url'] else 'text/html')
  q={'roll_number':roll,'notice_url':r['original_url'],'school_year':r['notice_admission_year'],'notes':[r['notes']]};phase='upcoming' if r['table_type']=='part_1_places' else 'retrospective' if 'criterion' not in r['table_type'] else 'waiting_event'
  # Pilot's criterion is a separate cohort; never attach whole-intake places to it.
  g,d=self.group(q,rid,phase,r['cohort'],r['table_school_year'],'explicit_source_year',r['table_type'],did,'high')
  fields={'places':'places','applications':'applications','offers':'offers','acceptances':'acceptances','names_on_waiting_list':'waiting_list_names_placed','actual_admissions':'actual_admissions'}
  for f,m in fields.items():
   if 'Historic Waitlist' in r['cohort'] and f=='offers':m='waiting_list_offers'
   if 'Historic Waitlist' in r['cohort'] and f=='acceptances':m='waiting_list_acceptances'
   ev={'field':f,'value':r.get(f),'source_url':r['original_url'],'source_sha256':r['payload_sha256'],'excerpt':r['exact_evidence_excerpt'],'method':'pilot_archive_body_direct_read','pilot_verified':True}
   self.obs(g,d,rid,f,m,r.get(f),[ev],status='not_recorded')
  for f,value in r.get('additional_explicit_metrics',{}).items():
   # Different counts/definitions are retained raw, not silently used as a second applications value.
   pass
 def pilot_captures(self):
  packed=D/'inputs'/'wayback_pilot_sources.json.gz'
  if packed.exists():ss=json.loads(gzip.decompress(packed.read_bytes()))
  else:
   ss=json.loads((ROOT/'wayback-pilot/sources.json').read_text());packed.write_bytes(gzip.compress(js(ss).encode(),mtime=0))
  for name,s in ss.items():
   r=s['request'];cap=s['capture'];roll=name.split('_')[0];sid=self.source(cap['original']);did=self.doc(roll,cap['original'],r['payload_sha256'],cap.get('mimetype'))
   rawpath=next((str(p.relative_to(ROOT)) for p in (ROOT/'wayback-pilot/raw').glob(name+'.*') if p.suffix in ['.html','.pdf']),None)
   dt=datetime.datetime.strptime(cap['timestamp'],'%Y%m%d%H%M%S').replace(tzinfo=datetime.timezone.utc).astimezone()
   self.put('retrieval',dict(retrieval_id=key(sid,r['payload_sha256'],cap['timestamp']),document_id=did,source_id=sid,retrieval_url=r['url'],retrieval_kind='wayback_archived_body',retrieved_at=r.get('requested_at'),http_status=r['status_code'],payload_sha256=r['payload_sha256'],local_payload_path=rawpath,archive_capture_timestamp=cap['timestamp'],archive_capture_time_dublin=dt.isoformat(),memento_datetime_header=r.get('headers',{}).get('memento-datetime'),body_verified=1,notes='Actual replay body; capture time distinct from publication and academic year.'))
if __name__=='__main__':
 i=Importer();i.baseline();print(json.dumps({'database':str(DB),'schools':i.c.execute('select count(*) from school').fetchone()[0],'raw_records':i.c.execute('select count(*) from raw_record').fetchone()[0],'observations':i.c.execute('select count(*) from observation').fetchone()[0],'reconciliation':i.c.execute('select dataset,expected_rows,raw_rows,excluded_rows from import_reconciliation').fetchall()},indent=2));i.c.close()
