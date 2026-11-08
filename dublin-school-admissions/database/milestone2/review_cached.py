#!/usr/bin/env python3
"""Second evidence review: 119 frozen cached source editions, manual specifications.
Never equates acceptance with enrolment, derives totals, or guesses conflicting years.
"""
import sys,json,gzip,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from import_database import *
P=D/'milestone2';I=Importer();I.release='database_milestone2_cached_2026_11_08'
I.put('dataset_release',dict(release_id=I.release,label='Milestone2: manually reviewed remaining cached editions',imported_at=now(),source_manifest_sha256=sha((D/'checkpoints/m2_local_unreviewed_inventory.json').read_bytes()),notes='All 119 unique cached editions triaged; conditional capacity, conflicting years, unseparated cohorts and actual enrolment retained distinctly.'))
a=I.input('m2_cached_editions',data=json.loads((D/'checkpoints/m2_local_unreviewed_inventory.json').read_text()))
I.school_records={r['roll_number']:r for r in json.loads(gzip.decompress((D/'inputs/v4_primary.json.gz').read_bytes()))}
S={};T={};N={};amb=set()
def add(i,title,phase,y,c,lo,hi,m,n='',scope='whole_table',status=None):
 T[i]=title;S.setdefault(i,[]).append(dict(title=title,phase=phase,year=y,cohort=c,lo=lo,hi=hi,metrics=m,notes=n,scope=scope,status=status))
 if y is None:amb.add(i)
def cap(i,title,y,c,v,lo=1,hi=99999,n='',metric='places'):add(i,title,'upcoming',y,c,lo,hi,{metric:v},n)
def ji(i,y,v,n=''):cap(i,y,y,'Junior Infants',v,n=n)
def sp(i,y,v,c='Special class (type not specified in aggregate)',n=''):cap(i,y,y,c,v,n=n)
def hist(i,title,y,c,m,lo=1,hi=99999,n='',scope='whole_table'):add(i,title,'retrospective',y,c,lo,hi,m,n,scope)
cap(0,'2026/2027','2026/2027','Second Class',None,n='Capacity cell blank, not zero. Senior intake, not Junior Infants.')
cap(1,'2026/2027','2026/2027','First Class',None,n='Places depend on feeder school senior-infant cohort; no fixed number published.')
ji(2,'2026/2027',54);sp(2,'2026/2027',0,c='Autism special classes')
hist(2,'2026/2027','2025/2026','Junior Infants',{'places':54,'applications':60,'offers':54,'waiting_list_names_placed':6},55,74,n='Detailed table and narrative explicitly2025/26; Part2 heading2026/27 conflicts, retained as year-qualified detailed table.')
hist(2,'2026/2027','2025/2026','Autism special classes',{'places':12,'applications':32,'waiting_list_names_placed':20},75,84,n='Only criterion-level offers-and-accepted printed; no aggregate offers or acceptances inferred.')
ji(3,'2026/2027',40);sp(3,'2026/2027',0,c='Autism special classes')
hist(3,'2026/2027','2025/2026','Junior Infants',{'places':40,'applications':51,'offers':51,'waiting_list_names_placed':0},45,85)
hist(3,'2026/2027','2025/2026','Autism special classes',{'places':0,'applications':5,'offers':0,'waiting_list_names_placed':5},70,120)
ji(6,'2023/2024',12)
hist(6,'2023/2024',None,'Junior Infants',{'places':14,'applications':23,'offers':14,'waiting_list_names_placed':0},35,95,n='Part2 heading/narrative2022/23 vs detailed breakdown2021/22; year unresolved.')
cap(7,'2025/2026','2025/2026','Second Class',26,22,52,n='Explicit application/decision heading names admission to Second Class2025; identical archived PDF independently confirms intake.')
hist(7,'2025/2026','2024/2025','Second Class',{'places':26,'applications':20,'offers':20,'waiting_list_names_placed':0},25,48)
ji(8,'2026/2027',26)
hist(8,'2026/2027','2025/2026','Junior Infants',{'places':28,'applications':70,'offers':30,'waiting_list_names_placed':40},45,105,n='Introductory narrative66 vs detailed applications70, unresolved source conflict; both retained in same group.')
hist(8,'2026/2027','2025/2026','Junior Infants',{'applications':66},40,70,n='Introductory66 versus detailed70; consensus applications must remain NULL.')
for i,title in [(9,'2023/2024'),(10,'2024/2025')]:cap(i,title,None,'Junior Infants',72,n='Title and capacity/Part1 give conflicting2023/24 and2024/25 labels. No guessed year.')
cap(12,'2027/2028',None,'Junior Infants',19,n='Title2027/28 vs capacity2026/27.');cap(12,'2027/2028',None,'Autism special classes',1,n='Title2027/28 vs capacity2026/27.')
ji(14,'2026/2027',21);sp(14,'2026/2027',1,'Autism Le Cheile class')
hist(14,'2026/2027','2025/2026','Special class (type not distinguished in historical table)',{'places':1,'applications':17,'offers':2,'waiting_list_names_placed':15},60,110,n='Unlabelled historical table not forced into Junior Infants; aggregate acceptances not printed.')
cap(15,'2024/2025',None,'Junior Infants',50,n='Title2024/25 vs capacity heading2023. Explicit conflict retained.')
for i,y,v in [(16,'2026/2027',78),(17,'2025/2026',75),(18,'2024/2025',75),(19,'2023/2024',75),(20,'2022/2023',78),(21,'2022/2023',78),(22,'2021/2022',78)]:cap(i,y,y,'Second Class',v,n='Conditional: printed number OR number of girls from Belgrove Infant Girls first classes seeking admission. Not a fixed available-place denominator.',metric='places_conditional_reference')
cap(23,'2022/2023',None,'Junior Infants',30,n='Title2022/23 vs Part1/capacity2021/22.');cap(23,'2022/2023',None,'Special class (type unspecified)',6,n='Conflicting printed years.')
cap(24,'2021/2022','2021/2022','Junior Infants',None,n='Genuine dated notice but no numeric capacity published in retrieved PDF.')
cap(25,'2026/2027',None,'Second Class',22,n='Capacity2023/24 conflicts with title2026/27.');cap(25,'2026/2027',None,'Autism special classes',2,n='Conflicting capacity/title years.')
ji(26,'2027/2028',100);sp(26,'2027/2028',1,'Autism special classes');hist(26,'2027/2028','2026/2027','Autism special classes',{'places':5,'applications':43},68,80)
for i,y,v in [(27,'2025/2026',25),(28,'2025/2026',25),(29,'2022/2023',16)]:ji(i,y,v,n='Source body year, not filename/upload year.')
for i,title in [(30,'2026/2027'),(31,'2023/2024')]:cap(i,title,None,'Junior Infants',24,n='Capacity heading2025 conflicts with title/Part1; no inferred academic year.')
cap(32,'2026/2027',None,'Second Class',40,n='Title2026/27 vs capacity2025/26.');cap(32,'2026/2027',None,'Autism special classes',1,n='Conflicting title/capacity years.')
cap(33,'2027/2028',None,'Junior Infants',54,n='Title2027/28 vs capacity2026/27.');cap(33,'2027/2028',None,'Autism special classes',0,n='Conflicting title/capacity years.')
cap(34,'2026/2027','2026/2027','Junior Infants',None,n='Genuine annual notice, capacity not printed in retrieved text.')
ji(35,'2027/2028',56);sp(35,'2027/2028',0)
hist(35,'2027/2028','2026/2027','Junior Infants',{'places':60,'applications':128,'offers':106,'waiting_list_names_placed':22},45,110,n='Irish original reviewed; criterion acceptances not summed.')
hist(35,'2027/2028','2026/2027','Special class (type unspecified)',{'places':6,'applications':10,'offers':10,'waiting_list_names_placed':0},105,180,n='CUID3 separate special-class intake; not merged with Junior Infants.')
ji(36,'2023/2024',22);sp(36,'2023/2024',0,'ASD special class');hist(36,'2023/2024','2022/2023','ASD special class',{'places':0,'applications':6,'offers':0,'waiting_list_names_placed':6},35,110)
cap(37,'2026/2027',None,'Second Class',50,n='Title2026/27 vs narrative2025/26; source publication05/01/2026 does not resolve academic-year conflict.');cap(37,'2026/2027',None,'Special class (type unspecified)',0,n='Conflicting title/narrative years.')
ji(38,'2025/2026',84)
# The entire cached HTML is a single source line; no hidden page/year interpolation.
cap(39,'2027/2028','2027/2028','Junior Infants',None,n='Notice numeric capacity requires separate HTML review; not inferred from existing enrolled pupil count.')
for i,y in [(40,'2027/2028'),(41,'2023/2024')]:
 cap(i,y,y,'Early Start',30,n='30 Early Start slots, not Junior Infant capacity.')
 cap(i,y,y,'Autism special class',0,n='Explicit zero available in existing class; not zero applications.')
cap(42,'2027/2028',None,'Junior Infants',20,n='Title2027/28 vs capacity2025/26 and Part12024/25.');cap(42,'2027/2028',None,'Special class (type unspecified)',3,n='Conflicting printed years.')
hist(42,'2027/2028','2026/2027','Junior Infants',{'places':19,'applications':20,'offers':19,'acceptances':19,'waiting_list_names_placed':1},45,120,n='Explicitly printed aggregate offers19/accepted19, not actual admissions.')
hist(42,'2027/2028','2026/2027','Special class (scope not distinguished in second historical table)',{'places':6,'applications':7,'offers':6,'acceptances':6,'waiting_list_names_placed':1},100,180,n='Second table source does not uniquely distinguish cohort; comparative cohort matching disabled.')
ji(44,'2021/2022',48,n='Source capacity heading malformed2021/20200; overall notice/Part1 explicitly2021/22.')
cap(45,'2025/2026','2025/2026','Third Class',127);cap(45,'2025/2026','2025/2026','Mild General Learning Disability special class',2)
cap(46,'2027/2028','2027/2028','Early Intervention ASD class',5)
cap(47,'2027/2028',None,'ASD special class',1,n='Bilingual capacity headers conflicting2026/27 vs2027/28.')
hist(47,'2027/2028',None,'ASD special class',{'places':0,'applications':9,'offers':0,'waiting_list_names_placed':9},35,130,n='Irish table2026/27, English Part2 header2025/26 and breakdown2026/27. Preserve unresolved bilingual year conflict.')
cap(49,'2023/2024',None,'Third Class',70,n='Title2023/24 vs capacity/Part12021/22.')
ji(50,'2026/2027',130)
cap(52,'2026/2027','2026/2027','Third Class',None,n='Genuine senior-school notice; numeric capacity absent in retrieved source.')
for c,v in [('Junior Infants',34),('Early Start',60),('ASD Den special class',3)]:cap(54,'2027/2028',None,c,v,n='Title2027/28 vs capacity2026/27; unknown exact year.')
cap(55,'2020/2021','2020/2021','Third Class',None,n='24:1 is class/pupil-teacher ratio, not24 total intake places. No fixed total capacity published.')
for c,v in [('Third Class',96),('Mild General Learning Disability special class',0),('Speech and Language Disorder special class',0)]:cap(57,'2026/2027',None,c,v,n='Title2026/27 vs capacity2025/26.')
cap(58,'2027/2028',None,'Junior Infants',51,n='Title2027/28 vs capacity2026/27.');cap(58,'2027/2028',None,'ASD special class',2,n='Conflicting title/capacity years.')
hist(58,'2027/2028',None,'ASD special class',{'places':7,'applications':30,'offers':7,'waiting_list_names_placed':20},50,120,n='Part2 heading2026/27 vs detailed2024/25; year unresolved.')
cap(59,'2026/2027','2026/2027','Third Class',42);cap(59,'2026/2027','2026/2027','ASD special classes',2)
hist(59,'2026/2027',None,'ASD special classes',{'places':1,'applications':4,'offers':1,'waiting_list_names_placed':3},55,140,n='Part2 heading2025/26 vs detailed2024/25.')
cap(60,'2025/2026','2025/2026','Third Class',54);cap(60,'2025/2026','2025/2026','ASD special classes',1)
hist(60,'2025/2026','2024/2025','ASD special classes',{'places':12,'applications':16,'offers':14,'waiting_list_names_placed':2},63,115,n='Detailed applications16 conflicts with introductory15; both retained; footnote list wording is not converted into inferred movement.')
hist(60,'2025/2026','2024/2025','ASD special classes',{'applications':15},63,66,n='Explicit introductory15 conflicts with detailed16; consensus applications suppressed.')
for i,y in [(61,'2025/2026'),(62,'2025/2026'),(63,'2023/2024')]:cap(i,y,y,'Second Class',None,n='Genuine dated annual notice; retrieved edition publishes dates only, not capacity.')
for c,v in [('Junior Infants',19),('Early Start',19),('Horizons Junior Autism class',1),('Horizons Senior Autism class',0)]:cap(64,'2027/2028',None,c,v,n='Title2027/28 vs capacity2026/27.')
cap(65,'2023/2024',None,'Junior Infants',68,n='Title2023/24 vs capacity2024/25; no calendar-year inference.')
cap(66,'2027/2028',None,'Junior Infants',None,n='Bilingual dates/section headings conflict with2027/28 title; numeric capacity absent.')
cap(67,'2026/2027','2026/2027','Third Class',150);cap(67,'2026/2027','2026/2027','Reading Classes',12)
hist(67,'2026/2027','2025/2026','Third Class',{'places':157,'applications':162,'waiting_list_initial_snapshot':162},100,113,n='Original Waiting List162 is exact source as printed, not names ever placed; no total offers or acceptances printed.')
add(67,'2026/2027','criterion_detail','2025/2026','Third Class: Category1 feeder-school transfer',100,107,{'offers':150},'Only original Category1 offers; not all offers.')
add(67,'2026/2027','waiting_event','2025/2026','Third Class',109,113,{'vacated_places_reoffered_to_waiting_list':3},'Explicit3 originally accepted places vacated/change of mind/moved and offered to waiting list. Not3 acceptances or actual admissions.',scope='explicit_vacated_place_reoffers')
ji(68,'2027/2028',30)
for i,title,y in [(72,'2023/2024',None),(73,'2022/2023','2022/2023'),(74,'2021/2022','2021/2022')]:cap(i,title,y,'Junior Infants',None,n='Genuine annual notice dates only; capacity not published. Conflicting Part1 year retained where applicable.')
ji(76,'2026/2027',68);sp(76,'2026/2027',3,'ASD special classes')
hist(76,'2026/2027',None,'ASD special classes',{'places':4,'applications':29,'offers':4,'waiting_list_names_placed':22},45,110,n='Part2 heading2025/26 vs detailed2024/25.')
ji(77,'2026/2027',28);ji(78,'2026/2027',26);sp(78,'2026/2027',0,'ASD special classes')
cap(79,'2026/2027',None,'Junior Infants',26,n='Title2026/27 vs capacity2025/26.')
for i,title,y in [(80,'2024/2025',None),(81,'2024/2025','2024/2025'),(82,'2023/2024',None),(83,'2021/2022','2021/2022'),(84,'2021/2022','2021/2022'),(85,'2021/2022','2021/2022')]:
 cap(i,title,y,'Junior Infants',None,n='Capacity TBC/Le Dearbhu, not numeric zero. Stale English capacity heading2021/22 retained as ambiguity where present.')
 add(i,title,'upcoming',y,'Special class (type unspecified)',1,99999,{'places':None},'Source special-class field N/A/none, not zero applications.',status='not_applicable')
cap(87,'2027/2028',None,'Junior Infants',50,n='Title2027/28 vs capacity2026/27.');cap(87,'2027/2028',None,'Special class (type unspecified)',1,n='Conflicting title/capacity years.')
cap(88,'2021/2022','2021/2022','Third Class',None,n='Senior-school notice says capacity varies by other class; no fixed numeric total.')
# Scanned GSer/Josephs source bodies pending OCR, not treated as reviewed numeric.
cap(90,'2026/2027',None,'Autism special classes',None,n='Title2026/27 vs Part12027/28; upcoming quota needs source conflict review.')
hist(90,'2026/2027',None,'Autism special classes',{'places':2,'applications':92,'offers':3,'waiting_list_names_placed':85},117,126,n='Part2 header2025/26 vs detailed2026/27; exact year unresolved.')
ji(91,'2025/2026',48);sp(91,'2025/2026',0)
hist(91,'2025/2026','2024/2025','Junior Infants',{'places':50,'applications':60,'offers':48},65,71)
hist(91,'2025/2026','2024/2025','Autism special classes',{'places':1,'applications':30,'offers':2},74,79)
ji(94,'2026/2027',40);sp(94,'2026/2027',0,'Autism special classes',n='Zero expected at publication; not a guarantee of no later vacancies.')
hist(94,'2026/2027','2025/2026','Junior Infants',{'places':38,'applications':73,'offers':71,'waiting_list_names_placed':2},125,142,n='Criteria16+22 not summed into aggregate acceptances.')
ji(95,'2022/2023',75)
hist(95,'2022/2023','2021/2022','Unseparated Junior Infants / Special Class / other year groups',{'places':110,'applications':353,'offers':276,'acceptances':110,'waiting_list_names_placed':77},136,149,n='Explicit aggregate offers276 accepted110; combined source scope, not asserted as JI-only.')
ji(98,'2026/2027',72)
hist(98,'2026/2027','2025/2026','Junior Infants',{'places':72,'applications_excluding_late':203,'offers':203,'waiting_list_names_placed':0},123,143,n='Footnote excludes later applications;203 not unqualified total applications. Criteria27+115+1+3+55+2 not summed as acceptances.',scope='October_2024_application_window_only')
for i,title,v in [(99,'2027/2028',75),(100,'2023/2024',28),(101,'2023/2024',28)]:
 cap(i,title,None,'Junior Infants',v,n='Title/Part1 academic year conflicts with capacity heading/September reference year.')
 for c in ['Autism Special Class A','Autism Special Class B']:cap(i,title,None,c,0,n='Conflicting capacity/title years; explicit class full zero, not no demand.')
ji(102,'2026/2027',24)
cap(105,'2026/2027',None,'Junior Infants',23,n='Public-reader transcript, original PDF payload hash unavailable. Title/capacity2026/27 vs Part12027/28; no guessed year.')
hist(105,'2026/2027','2026/2027','Junior Infants',{'places':46,'applications':148,'offers':75,'actual_admissions':47},13,22,n='Exact historical table2026/27;47 explicitly children enrolled, not an inferred acceptance sum. Public-reader transcription; binary hash not available.')
for i,y in [(106,'2025/2026'),(107,'2023/2024')]:cap(i,y,y,'Preschool Year1: special-school intake',9,18,39)
for c,v in [('Early Intervention Classes',5),('Primary classes: special-school intake',9)]:cap(109,'2027/2028','2027/2028',c,v,44,49)
hist(109,'2027/2028','2026/2027','Early Intervention Classes',{'places':7,'applications':12,'offers':7,'waiting_list_names_placed':0},51,70)
hist(109,'2027/2028','2026/2027','Primary classes: special-school intake',{'places':9,'applications':45,'offers':11,'waiting_list_names_placed':6},73,82,n='Criteria diagnoses may overlap; no aggregate acceptance sum.')
cap(110,'2021/2022',None,'Special-school intake (class unspecified)',20,n='Main title2021/22 vs Part1/capacity2023/24.')
cap(111,'2026/2027','2026/2027','Severe and Profound Learning Disabilities',0)
hist(111,'2026/2027','2025/2026','Severe and Profound Learning Disabilities',{'places':2,'eligible_applications':8,'offers':4},47,60,n='Eligible applications explicitly, not all applications.')
cap(112,'2025/2026','2025/2026','All classes and ages: special-school intake',4)
hist(112,'2025/2026','2024/2025','All classes and ages: special-school intake',{'places':4,'applications':49,'offers':4,'waiting_list_names_placed':45},49,61)
for i in [113,115,116]:
 for n in range(1,5):cap(i,'2025/2026','2025/2026',f'Group {n}: special-school intake',6,n=f'Exact printed Group{n} quota; no inferred JI equivalent.')
# Lucan2026 document heading is checked below; unknown year is not replaced with URL date.
for c,v in [('Destination Class1 age5-8',12),('Destination Class2 age9-12',6),('Destination Class3 age13-15',0),('Destination Class4 age16-18',0)]:cap(114,None,None,c,v,1,24,n='Retrieved source fragment has no explicit academic year; URL/retrieval year not used.')
false={4:'procedure_not_annual_notice',5:'download_navigation_not_notice',11:'homepage_navigation_not_notice',13:'admissions_landing_not_notice',43:'homepage_navigation_not_notice',48:'admission_policy_not_notice',51:'admissions_navigation_not_notice',53:'enrolment_navigation_not_notice',56:'homepage_navigation_not_notice',69:'policy_or_navigation_not_verified_notice',70:'policy_or_navigation_not_verified_notice',71:'policy_or_navigation_not_verified_notice',75:'admissions_navigation_not_notice',86:'admissions_navigation_not_notice',92:'policy_not_notice',93:'homepage_notice_link_not_notice_body',96:'search_results_not_notice',97:'admission_policy_not_notice',103:'admission_policy_not_notice',104:'draft_policy_not_notice',117:'admission_policy_not_notice',118:'admission_policy_not_notice'}
newdefs={'places_conditional_reference':'Conditional quota reference followed by OR feeder-school cohort; not fixed available places.','waiting_list_initial_snapshot':'Explicit initial/original waiting-list snapshot, not names ever placed.','actual_admissions':'Explicit number of children enrolled in the stated intake/year; not accepted offers.','vacated_places_reoffered_to_waiting_list':'Explicit count of vacated originally accepted places subsequently offered to waiting list; not resulting acceptances/admissions.'}
for m,definition in newdefs.items():I.put('metric_definition',dict(metric_code=m,label=m.replace('_',' '),definition=definition))
# Final source-boundary audit: each field excerpt must actually include its row, not merely the same number elsewhere.
for i,phase,cohort,lo,hi in [(3,'retrospective','Junior Infants',73,106),(3,'retrospective','Autism special classes',109,129),(8,'retrospective','Junior Infants',64,104),(35,'retrospective','Junior Infants',48,87),(35,'retrospective','Special class (type unspecified)',88,145),(36,'retrospective','ASD special class',114,134),(42,'retrospective','Junior Infants',52,68),(42,'retrospective','Special class (scope not distinguished in second historical table)',71,78)]:
 for g in S[i]:
  if g['phase']==phase and g['cohort']==cohort:g['lo']=lo;g['hi']=hi
for g in S[8]:
 if g['metrics']=={'applications':66}:g['lo']=71;g['hi']=72
for g in S[14]:
 if g['phase']=='retrospective':g['cohort']='Unspecified historical intake (not inferred)';g['lo']=86;g['hi']=103
for g in S[2]:
 if g['phase']=='retrospective':g['year_status']='explicit_table_year_conflicting_section_header'
S[39]=[];ji(39,'2027/2028',50);sp(39,'2027/2028',2,'Autism special classes',n='Source explicitly says2 available places, not the12 currently enrolled.')
for i,y in [(40,'2027/2028'),(41,'2023/2024')]:
 ji(i,y,20)
 for g in S[i]:
  if g['cohort']=='Autism special class' and i==40:g['cohort']='Senior Autism class'
 if i==40:cap(i,y,y,'Junior Autism class',0,n='Distinct junior class available places0; not6 already enrolled.')
res=[];extract=[]
for idx,b in enumerate(a):
 status='rejected_not_notice' if idx in false else 'payload_unavailable_prior_failure_requires_permitted_source_retrieval' if idx==89 else 'reviewed_visual_no_published_numeric' if idx==108 else 'reviewed_with_source_ambiguity' if idx in amb else 'reviewed_numeric' if any(any(v is not None for v in g['metrics'].values()) for g in S.get(idx,[])) else 'reviewed_no_published_numeric' if idx in S else 'pending'
 reason=false.get(idx);rid=I.raw('m2_cached_editions',idx,b,'excluded' if idx in false else 'normalized' if idx in S else 'pending',reason);did=I.doc(b['roll'],b['url'],b['sha256'],b.get('format'))
 text=(ROOT/b['text_file']).read_text() if b.get('text_file') else '';lines=text.splitlines()
 for g in S.get(idx,[]):
  lo,hi=g['lo'],min(g['hi'],len(lines));ex='\n'.join(lines[lo-1:hi]);assert ex.strip(),(idx,g)
  q={'roll_number':b['roll'],'notice_url':b['url'],'school_year':g['title'],'notes':[g['notes']],'evidence':[{'source_sha256':b['sha256'],'source_url':b['url']}]}
  gid,_=I.group(q,rid,g['phase'],g['cohort'],g['year'],g.get('year_status') or ('explicit_source_year' if g['year'] else 'ambiguous_conflicting_printed_years'),g['scope'],did,'medium' if idx in amb or b['sha256'] is None else 'high')
  for m,v in g['metrics'].items():
   if v is not None:assert re.search(r'(?<![0-9])'+str(v)+r'(?![0-9])',ex.replace(',','')),(idx,m,v,lo,hi)
   ev=dict(field=m,value=v,source_url=b['url'],source_sha256=b['sha256'],excerpt=ex,text_file=b['text_file'],line_start=lo,line_end=hi,page='\n'.join(lines[:lo-1]).count('\f')+1,method='manual_cached_source_table_review')
   I.obs(gid,did,rid,m,m,v,[ev],status=g['status'] or ('ambiguous' if not g['year'] else 'not_published'),qualifier=g['notes'])
  extract.append(dict(roll=b['roll'],document_id=did,source_url=b['url'],group_id=gid,**g))
 task=key(b['roll'],'m2_cached_edition_review',b['url'],did);I.put('work_queue',dict(task_id=task,roll=b['roll'],stage='m2_cached_edition_review',source_url=b['url'],document_id=did,status=status,priority=2,checkpoint_json=js({'index':idx,'reason':reason,'groups_extracted':len(S.get(idx,[]))}),updated_at=now()))
 I.c.execute('UPDATE work_queue SET status=?,checkpoint_json=?,updated_at=? WHERE task_id=?',(status,js({'index':idx,'reason':reason,'groups_extracted':len(S.get(idx,[]))}),now(),task))
 res.append(dict(index=idx,roll=b['roll'],url=b['url'],document_id=did,status=status,reason=reason,groups_extracted=len(S.get(idx,[]))))
I.reconcile();I.c.commit();I.c.close()
(P/'cached_review_results.json').write_text(json.dumps(res,indent=2)+'\n');(P/'cached_review_groups.json').write_text(json.dumps(extract,indent=2)+'\n');(P/'cached_review_specs.json').write_text(json.dumps(S,indent=2)+'\n')
from collections import Counter
print(dict(Counter(r['status'] for r in res)),'groups',len(extract),'metric assertions',sum(len(g['metrics']) for g in extract))
