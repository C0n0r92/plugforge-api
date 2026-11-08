#!/usr/bin/env python3
"""Evidence-reviewed bounded local backlog expansion. Manual table specifications, not generic numerical scraping.
All 74 candidates are triaged; unresolved combined cohorts/year conflicts explicitly retain a follow-up task.
"""
from import_database import *
def read_source(relative):
 p=ROOT/relative
 if not p.exists():p=D/relative.removeprefix('database/')
 return p.read_text()
I=Importer();I.baseline();I.release='database_local_editions_2026_11_08';I.datasets={}
I.put('dataset_release',dict(release_id=I.release,label='First database historical expansion: complete local backlog triage and source-table extracts',imported_at=now(),source_manifest_sha256=sha((D/'inputs/v4_local_review_backlog.json.gz').read_bytes()),notes='Manual source-text review. Numeric source conflicts and unresolved cohort/year scopes preserved; no inferred aggregate acceptances.'))
backlog=I.input('local_review_inputs',data=json.loads(gzip.decompress((D/'inputs/v4_local_review_backlog.json.gz').read_bytes())))
# Group specification: phase, exact table year (null if conflicting), cohort, source lines, explicit metrics, notes.
S={}
def add(idx,title,phase,y,cohort,lo,hi,metrics,notes=''):
 S.setdefault(idx,{'title':title,'groups':[]})['groups'].append(dict(phase=phase,year=y,cohort=cohort,line_start=lo,line_end=hi,metrics=metrics,notes=notes))
def cur(i,y,ji=None,special=None,lo=1,hi=9999,notes=''):
 if ji is not None:add(i,y,'upcoming',y,'Junior Infants',lo,hi,{'places':ji},notes)
 if special is not None:add(i,y,'upcoming',y,'Special class (type unspecified in aggregate field)',lo,hi,{'places':special},notes)
def hist(i,title,y,cohort,lo,hi,metrics,notes=''):add(i,title,'retrospective',y,cohort,lo,hi,metrics,notes)
cur(0,'2025/2026',60,lo=40,hi=42)
hist(0,'2025/2026','2024/2025','Junior Infants',47,85,{'places':60,'applications':123,'offers':100,'waiting_list_unspecified':0},'Printed list zero is qualified by footnotes about contacting remaining 23 and withdrawals; do not call zero names ever placed. Aggregate acceptances are not printed.')
cur(1,'2022/2023',28,lo=44,hi=48)
hist(1,'2022/2023','2021/2022','Junior Infants',59,100,{'places':28,'applications':43,'offers':28,'waiting_list_names_placed':15},'First-round table: 28 offers. Narrative separately reports cumulative 39 at 31/07/21; never substitute that snapshot into this funnel. Introductory 63 is expressions of interest labelled 2020/21, not this applications total.')
add(1,'2022/2023','snapshot','2021/2022','Junior Infants',78,90,{'offers':39},'Explicit cumulative offers as of 31/07/2021; separate from first-round table. No waiting-list movement calculated.')
add(2,'2025/2026','upcoming','2025/2026','Severe and Profound Learning Disabilities',41,43,{'places':2})
hist(2,'2025/2026','2024/2025','Severe and Profound Learning Disabilities',47,63,{'places':0,'eligible_applications':9,'offers':1},'Applications are explicitly eligible applications; separate definition, not automatically all applications. Zero capacity coexists with one offer; preserve source, no correction.')
cur(3,'2026/2027',72,1,89,94,'ALC special-class aggregate; other year groups separately six, not merged.')
for i,y,ji,sp,lo,hi in [(4,'2025/2026',66,0,93,95),(5,'2024/2025',72,0,94,96),(6,'2023/2024',75,7,89,92),(7,'2022/2023',70,0,92,94),(8,'2021/2022',57,0,116,118)]:cur(i,y,ji,sp,lo,hi,'Historical combined Junior Infant/ALC/other-year-group table needs separate cohort extraction; not fused to these upcoming capacities.')
cur(9,'2027/2028',52,0,104,110,'Header year explicitly 2027/28 despite 2026/2027 footer; retain this source-year qualification.')
for i in [10,15,16,17,18]:
 cur(i,'2026/2027',112,2,18,30,'JI total may reduce for dual special-class placements. Do not treat capacity as realized admissions.')
 # Locate historical ETB tables from reviewed structure instead of guessing a single combined cohort.
 t=read_source(backlog[i]['text_file']);ln=t.splitlines();starts=[j+1 for j,l in enumerate(ln) if 'Number of places available' in l]
 app=106 if i==17 else 102
 if len(starts)>=2:
  hist(i,'2026/2027','2025/2026','Junior Infants',starts[0]-3,starts[0]+3,{'places':112,'applications':108,'offers':108})
  hist(i,'2026/2027','2025/2026','Autism special classes',starts[1]-3,starts[1]+4,{'places':3,'applications':app,'offers':3},'Other editions report 102 vs 106 applications; retain edition conflict without averaging.')
for i in [11,12,13,19]:
 lo=126 if i in [11,12] else 127 if i==13 else 128
 add(i,'2026/2027','upcoming','2026/2027','Autism special classes: Sonas & Bród Junior Classes',lo,lo+5,{'places':2})
 # Do not guess which of mutually conflicting table labels is correct.
 hist(i,'2026/2027',None,'Autism special classes',lo+7,lo+20,{'places':3,'applications':106,'offers':3,'waiting_list_names_placed':97},'Part Two/information header says 2025/26; breakdown caption says 2024/25. Exact year unresolved. Offers made-and-accepted under criteria is not an explicit aggregate acceptance count.')
cur(14,'2026/2027',112,2,74,81)
hist(14,'2026/2027','2025/2026','Autism special classes',106,123,{'places':3,'applications':102,'offers':3,'waiting_list_names_placed':94},'102 includes five not eligible. Other editions show revised 106 applications and 97 list names; retain source revisions.')
cur(20,'2025/2026',112,3,71,78)
hist(20,'2025/2026','2023/2024','Autism special classes',105,121,{'places':0,'applications':28,'offers':0,'waiting_list_names_placed':25},'28 includes three incomplete applications. Printed table 2023/24 retained; do not infer 2024/25 from notice title.')
for i in [21,22]:
 lo=75 if i==21 else 66
 cur(i,'2025/2026',50,0,lo,lo+18,'Two columns: school 50 vs LCES four-school aggregate 225; 225 not imported as school capacity.')
 hist(i,'2025/2026','2023/2024','Autism special class',92 if i==21 else 85,111 if i==21 else 104,{'places':3,'applications_excluding_late':15,'offers':3,'waiting_list_names_placed':12},'Printed row: 15 + 1 late application. Introductory narrative separately says 10. No inferred total 16 and no unqualified applications ratio.')
cur(23,'2024/2025',52,3,57,69,'School capacity 52; adjacent LCES aggregate 208 excluded.')
hist(23,'2024/2025','2022/2023','Autism special class',72,87,{'places':1,'applications':19,'offers':1,'waiting_list_names_placed':13})
for i,y,ji,sp,lo,hi,hy,hm,hs,la,lb in [(24,'2024/2025',50,0,10,22,'2023/2024',(50,50,50),(6,35,6),77,91),(25,'2023/2024',48,6,10,22,'2022/2023',(50,75,50),(7,50,7),67,80),(26,'2021/2022',78,0,9,17,'2020/2021',(60,130,60),(6,30,6),56,69),(27,'2021/2022',78,0,9,17,'2020/2021',(60,130,60),(6,30,6),56,69)]:
 cur(i,y,ji,sp,lo,hi)
 hist(i,y,hy,'Junior Infants',la,lb,dict(zip(['places','applications','offers'],hm)))
 hist(i,y,hy,'Autism special classes',la,lb,dict(zip(['places','applications','offers'],hs)),'Special-class narrative capacity differs from detailed table in 2020/21: narrative 12, detailed six; six is exact table value, conflict preserved in evidence.')
# Conflicting header years are quarantined rather than silently normalized.
for i,y,hy,vals,lo,hi in [(30,'2027/2028',None,(1,56,1,55),87,102),(31,'2026/2027','2025/2026',(2,80,2,66),82,97),(32,'2026/2027','2025/2026',(2,80,2,66),82,97),(33,'2026/2027','2025/2026',(2,80,2,66),82,97)]:
 hist(i,y,hy,'Autism special classes',lo,hi,dict(zip(['places','applications','offers','waiting_list_names_placed'],vals)),'2027/28 edition has conflicting Part Two2026/27 vs detailed2025/26 labels; not assigned an inferred year.' if i==30 else 'Exact 2025/26 table; other editions differ, retained separately.')
cur(34,'2026/2027',50,lo=44,hi=46,notes='Source qualifies capacity by pupil-teacher ratio and staffing schedule.')
hist(34,'2026/2027','2025/2026','Junior Infants',48,62,{'places':100,'applications':106,'offers':106,'waiting_list_names_placed':0})
for i,lo,hi in [(35,55,57),(36,54,56),(37,54,56)]:
 cur(i,'2025/2026',100,lo=lo,hi=hi)
 hist(i,'2025/2026','2024/2025','Junior Infants',lo+5,hi+21,{'places':100,'applications':111,'offers':109,'waiting_list_names_placed':0})
add(39,'2022/2023','upcoming','2022/2023','Autism special class',1,1,{'places':6},'Public school post, not the search-results page. Footer unrelated content excluded from subsequent comparisons.')
for i,y,hy,ji,sp,lo,hi in [(41,'2025/2026','2023/2024',(50,140,61),(0,40,0),62,79),(42,'2026/2027','2024/2025',(48,140,48),(1,71,1),73,89)]:
 cur(i,y,48,lo=23,hi=26)
 hist(i,y,hy,'Junior Infants',lo,hi,dict(zip(['places','applications','offers'],ji)))
 hist(i,y,hy,'Autism special classes',lo,hi,dict(zip(['places','applications','offers'],sp)),'2024/25 narrative says zero places but detailed ASD table says one; table one preserved as distinct source assertion.' if i==42 else '')
for i,y,ji,lo,hi in [(43,'2026/2027',52,99,109),(44,'2025/2026',48,118,128)]:cur(i,y,ji,0,lo,hi,'Exact capacity section year; earlier application-date headers may carry stale prior-year captions.')
for i,y,lo,hi in [(45,'2027/2028',27,29),(46,'2026/2027',39,41),(47,'2025/2026',39,41)]:cur(i,y,34,lo=lo,hi=hi)
cur(49,'2025/2026',46,lo=16,hi=18)
add(49,'2025/2026','upcoming','2025/2026','Autism special classes',22,24,{'places':4},'Source separately prints total12, alreadyallocated8, placesleft4. Four available new places, not total classroom capacity12.')
hist(49,'2025/2026','2024/2025','Junior Infants',78,82,{'places':46,'applications':76,'offers':46})
hist(49,'2025/2026','2023/2024','Autism special classes',91,96,{'places':2,'applications':30,'offers':2},'Special-class table year2023/24 differs from mainstream2024/25. Not combined.')
for i,y,ji,lo,hi in [(50,'2027/2028',50,67,78),(51,'2026/2027',50,68,79),(52,'2026/2027',50,46,53),(53,'2025/2026',50,73,86),(54,'2023/2024',54,61,69),(55,'2021/2022',56,65,73)]:cur(i,y,ji,lo=lo,hi=hi,notes='Combined other-year-group historical tables retained for field-level follow-up, not used to fabricate a Junior Infants funnel.')
for i,y,ji,lo,hi in [(56,None,28,8,19),(57,'2024/2025',28,1,10),(58,'2023/2024',28,10,21),(59,'2022/2023',26,8,19),(60,'2021/2022',26,8,19),(61,'2021/2022',26,1,10)]:
 cur(i,y or '2025/2026',ji,lo=lo,hi=hi,notes='Title2025/26 conflicts with narrative2024/25; year not resolved.' if i==56 else '')
 if i==56:S[i]['groups'][0]['year']=None
for i,lo in [(62,98),(63,98)]:cur(i,'2026/2027',30,0,lo,lo+13)
cur(64,'2025/2026',30,0,96,109,'Capacity section2025/26 vs title2024/25 conflict retained; year unresolved.')
for g in S[64]['groups']:g['year']=None
for i in [65,66]:
 cur(i,'2023/2024',30,lo=91,hi=95,notes='Special-class header says2022/23; Max6 is a ceiling, not confirmed available intake.')
 add(i,'2023/2024','upcoming','2022/2023','Junior Infants',110,114,{'places':30},'Separate second capacity block explicitly2022/23; not another capture-year observation.')
cur(67,'2022/2023',30,lo=90,hi=94,notes='Max6 special-class capacity is not confirmed available places. Prior special class explicitly did not exist in2021/22; not applicable, not zero demand.')
cur(71,'2027/2028',30,0,170,185,'Bilingual historical field uses léirithe spéise (expressions of interest) versus English applications. Do not silently equate86 with applications. Waiting-list row labels2024/25 while section2026/27; pending definition/year review.')
for i in [72,73]:
 for group in range(1,5):add(i,'2025/2026','upcoming','2025/2026',f'Group {group}: special-school intake',2*group+3,2*group+4,{'places':6},'Group-specific capacity; no invented age band or Junior Infant equivalence.')
cur(70,'2027/2028',30,0,1,3,'Physical PDF page2 directly visually reviewed; manual aggregate-only transcript; source header and capacity section explicitly2027/28.')
# Remaining combined tables: retain printed assertions while explicitly preventing a fake grade-specific funnel.
for i,title,hy,lo,hi,counts,lists in [(4,'2025/2026','2024/2025',108,121,(80,261,205),(27,29)),(5,'2024/2025','2023/2024',109,122,(83,223,152),(0,0)),(6,'2023/2024','2022/2023',113,128,(65,196,147),(10,27)),(7,'2022/2023','2021/2022',120,142,(57,255,81),(37,37)),(8,'2021/2022','2020/2021',143,154,(56,405,56),(92,56))]:
 hist(i,title,hy,'Unseparated Junior Infants / ALC / other year groups',lo,hi,dict(zip(['places','applications','offers'],counts)),'Source combined heading does not establish that all these counts have Junior Infant-only scope; cohort unmatched and ratios disabled. Separate list subgroups are not stitched into this aggregate.')
 hist(i,title,hy,'Junior Infants: separately printed waiting-list row',lo,hi,{'waiting_list_names_placed':lists[0]},'List subgroup only; no incompatible aggregate places/applications attached.')
 hist(i,title,hy,'Other year groups: separately printed waiting-list row',lo,hi,{'waiting_list_names_placed':lists[1]})
# Canal Way: distinguish explicit JI and non-JI application scopes from unseparated total offers.
for i,title,hy,lo,hi,apps,other,total,wait in [(50,'2027/2028',None,85,102,135,44,161,2),(51,'2026/2027','2025/2026',86,104,161,46,207,0),(52,'2026/2027','2025/2026',56,72,161,46,207,0),(53,'2025/2026',None,102,118,175,40,175,0)]:
 hist(i,title,hy,'Junior Infants',lo,hi,{'places':50,'applications':apps},'Part Two vs breakdown year conflicts quarantined where present. Printed total offers are not assumed to be Junior Infant-only.')
 hist(i,title,hy,'Other year groups: Non Junior Infants',lo,hi,{'applications':other})
 hist(i,title,hy,'Unseparated Junior Infants / other year groups',lo,hi,{'offers':total,'waiting_list_names_placed':wait},'Scope not clearly a single intake; do not attach JI-only capacity or applications.')
for i,title,hy,lo,hi,places,apps,offersbase,wait in [(54,'2023/2024','2022/2023',85,101,56,193,125,35),(55,'2021/2022','2020/2021',89,104,56,250,194,31)]:
 hist(i,title,hy,'Unseparated Junior Infants / other year groups',lo,hi,{'places':places,'applications':apps,'offers_excluding_siblings':offersbase,'waiting_list_names_placed':wait},'Offers explicitly exclude additional sibling offers:125 plus33, or194 plus25. No inferred total.2020/21 introductory applications225 conflict with detailed250; retain source assertion/quality, not guessed reconciliation.')
# The bilingual source explicitly uses expressions-of-interest wording; English application gloss remains in evidence.
hist(71,'2027/2028','2026/2027','All listed year groups combined: Junior Infants, Autism and other years',136,164,{'places':37,'registrations_of_interest':86,'offers':81},'Irish léirithe spéise means expressions of interest despite English applications gloss. Registration-interest quantity is NOT in the applications metric. Combined grade scope prevents grade-specific ratios.')
hist(71,'2027/2028',None,'All listed year groups combined: Junior Infants, Autism and other years',166,168,{'waiting_list_unspecified':5},'Waiting-list row says2024/25, surrounding section2026/27. Unresolved exact year; do not attach5 to2026/27 funnel.')
for grade,places in [('Senior Infants',7),('First Class',1),('Second Class',0),('Third Class',2),('Fourth Class',12),('Fifth Class',2),('Sixth Class',2)]:add(71,'2027/2028','upcoming','2027/2028',grade,176,182,{'places':places},'Exact per-grade capacity, not an inferred total.')
# Explicit criterion-level acceptances are retained; no summing them into whole-intake totals.
for i,title,hy,lo,hi,siblings,alc,other in [(4,'2025/2026','2024/2025',108,121,23,(1,1),(41,14)),(5,'2024/2025','2023/2024',109,122,22,(26,6),(104,55)),(6,'2023/2024','2022/2023',113,128,29,(None,0),(4,4)),(7,'2022/2023','2021/2022',120,142,45,(None,1),(0,0)),(8,'2021/2022','2020/2021',143,154,43,(None,1),(12,12))]:
 add(i,title,'criterion_detail',hy,'Sibling criterion within combined intake',lo,hi,{'acceptances':siblings},'Explicit accepted criterion count only; never aggregated or equated with actual enrolment.')
 add(i,title,'criterion_detail',hy,'ALC special class criterion within combined intake',lo,hi,dict(acceptances=alc[1],**({'offers':alc[0]} if alc[0] is not None else {})))
 add(i,title,'criterion_detail',hy,'All other places criterion within combined intake',lo,hi,dict(zip(['offers','acceptances'],other)))
# Additional semantic metric definitions; not folded into unqualified application counts.
for code,definition in [('eligible_applications','Only eligible applications, as printed; not all applications.'),('applications_excluding_late','Printed base count followed by an additional late-application quantity; not inferred total.'),('places_capacity_ceiling','Maximum class capacity; not confirmed available new intake.'),('offers_excluding_siblings','Printed offers quantity with additional sibling offers stated separately; not the total offers metric.')]:I.put('metric_definition',dict(metric_code=code,label=code.replace('_',' '),definition=definition))
complex_indices={1,4,5,6,7,8,11,12,13,19,21,22,30,42,50,51,52,53,54,55,56,64,65,66,67,71}
false_indices={28:'admission_policy_not_annual_notice',29:'navigation_excerpt_not_genuine_notice',38:'search_results_page_multiple_notice_excerpts',40:'admission_policy_not_annual_notice',68:'draft_policy_not_annual_notice',69:'policy_not_annual_notice'}
results=[];extracted=[]
for idx,b in enumerate(backlog):
 b=dict(b)
 if idx==70:b['text_file']='database/evidence/broadmeadow_2027_visual_transcript.txt'
 status='reviewed_with_source_ambiguity' if idx in complex_indices else 'reviewed_numeric' if idx in S else 'reviewed_no_numeric' if idx==48 else 'rejected_not_notice' if idx in false_indices else 'requires_ocr_review' if idx==70 else 'pending'
 reason=false_indices.get(idx) or 'Scanned PDF has no parsed text; OCR/visual evidence review required.' if idx==70 else false_indices.get(idx)
 rid=I.raw('local_review_inputs',idx,b,'excluded' if idx in false_indices else 'normalized',reason)
 did=I.doc(b['roll'],b['url'],b['sha256'],b.get('format'))
 task=key(b['roll'],'local_notice_review',b['url'],did);I.c.execute('UPDATE work_queue SET status=?,checkpoint_json=?,updated_at=? WHERE task_id=?',(status,js({'input':b,'review_status':status,'reason':reason,'groups_extracted':len(S.get(idx,{}).get('groups',[])),'reviewed_at':now()}),now(),task))
 if idx in complex_indices:
  I.put('work_queue',dict(task_id=key(b['roll'],'source_ambiguity_resolution',b['url'],did),roll=b['roll'],stage='source_ambiguity_resolution',source_url=b['url'],document_id=did,status='needs_scope_year_or_definition_resolution',priority=4,checkpoint_json=js({'review_index':idx,'reason':'Printed year, cohort scope, metric definition, snapshot, or edition conflicts; exact evidence retained and incompatible ratios suppressed.'}),updated_at=now()))
 if idx in S:
  text=read_source(b['text_file']);lines=text.splitlines();s=S[idx]
  for j,g in enumerate(s['groups']):
   excerpt='\n'.join(lines[g['line_start']-1:g['line_end']]);assert excerpt.strip(),(idx,j,'empty source range')
   for m,v in g['metrics'].items():assert re.search(r'(?<![0-9])'+str(v)+r'(?![0-9])',excerpt.replace(',','')),(idx,m,v,'expected number absent',excerpt)
   q={'roll_number':b['roll'],'notice_url':b['url'],'school_year':s['title'],'notes':[g['notes']],'evidence':[{'source_sha256':b['sha256'],'source_url':b['url']}]}
   # Only explicitly labelled publication dates; never filesystem, URL-upload or archive dates.
   pm=re.search(r'(?:This notice was )?published on\s+([^\n]+)',text,re.I)
   if pm:
    printed=pm.group(1).strip().rstrip('.');clean=re.sub(r'(\d)(?:st|nd|rd|th)',r'\1',printed);clean=re.sub(r'\s*/\s*','/',clean)
    for fmt in ['%d/%m/%Y','%d/%m/%y','%d %B %Y']:
     try:q['publication_date']=datetime.datetime.strptime(clean,fmt).date().isoformat();break
     except ValueError:pass
   yrstatus='explicit_source_year' if g['year'] else 'ambiguous_conflicting_printed_years'
   scope='first_round_table' if idx==1 and g['phase']=='retrospective' else 'cumulative_2021_07_31' if idx==1 and g['phase']=='snapshot' else 'whole_table'
   groupid,d=I.group(q,rid,g['phase'],g['cohort'],g['year'],yrstatus,scope,did,'medium' if idx in complex_indices else 'high')
   if idx==1 and g['phase']=='snapshot':I.c.execute('UPDATE observation_group SET as_of=? WHERE group_id=?',('2021-07-31',groupid))
   if q.get('publication_date') and pm:
    pe={'field':'publication_date','value':q['publication_date'],'source_url':b['url'],'source_sha256':b['sha256'],'text_file':b['text_file'],'excerpt':pm.group(0),'method':'explicit_publication_label_date_parse_Irish_day_month_year'}
    eid=I.evidence(pe,d,rid);nid=I.c.execute('SELECT notice_id FROM observation_group WHERE group_id=?',(groupid,)).fetchone()[0]
    I.put('notice_publication_assertion',dict(assertion_id=key(nid,q['publication_date'],rid),notice_id=nid,publication_date=q['publication_date'],date_precision='day',source_printed_text=pm.group(0),evidence_id=eid,raw_id=rid))
    I.c.execute('UPDATE notice SET publication_time=(SELECT CASE WHEN COUNT(DISTINCT publication_date)=1 THEN MIN(publication_date) END FROM notice_publication_assertion WHERE notice_id=?),publication_precision=? WHERE notice_id=?',(nid,'day',nid))
   for m,v in g['metrics'].items():
    ev={'field':m,'value':v,'source_url':b['url'],'source_sha256':b['sha256'],'excerpt':excerpt,'text_file':b['text_file'],'line_start':g['line_start'],'line_end':g['line_end'],'page':2 if idx==70 else text[:sum(len(x)+1 for x in lines[:g['line_start']-1])].count('\f')+1,'method':'manual_visual_PDF_page2_transcript' if idx==70 else 'manual_local_notice_table_review'}
    I.obs(groupid,d,rid,m,m,v,[ev],qualifier=g['notes'] if m in ['applications_excluding_late','eligible_applications','waiting_list_unspecified'] else '')
   extracted.append({'roll':b['roll'],'document_id':did,'source_url':b['url'],'group_id':groupid,**g})
 elif idx==48:
  I.put('notice',dict(notice_id=key(did,'2024/2025'),document_id=did,title_school_year='2024/2025',identity_verified=1))
 results.append({'index':idx,'roll':b['roll'],'url':b['url'],'status':status,'reason':reason,'groups_extracted':len(S.get(idx,{}).get('groups',[]))})
I.datasets['local_review_inputs']=len(backlog);I.reconcile();I.c.commit()
(D/'checkpoints/local_backlog_review.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n');(D/'checkpoints/new_local_observation_groups.json').write_text(json.dumps(extracted,indent=2,ensure_ascii=False)+'\n');(D/'checkpoints/local_review_specs.json').write_text(json.dumps(S,indent=2,ensure_ascii=False)+'\n')
from collections import Counter
print('RESULT',dict(Counter(r['status'] for r in results)),'groups',len(extracted),'metrics',sum(len(g['metrics']) for g in extracted));I.c.close()
