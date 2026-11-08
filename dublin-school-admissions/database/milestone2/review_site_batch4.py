#!/usr/bin/env python3
"""Manual cell-level specs read from own-site batch3 sources. No network, no arithmetic totals."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];A=json.loads((P/'discovery_batch4_inventory.json').read_text());out=[];by={};times={}
for l in (P/'requests.jsonl').read_text().splitlines():
 try:r=json.loads(l);times[(r.get('roll'),r.get('sha256'))]=r.get('attempted_at')
 except:pass
def b(i):
 if i not in by:
  x=A[i].copy();x.update(groups=[],retrieval_url=x['url'],retrieved_at=times.get((x['roll'],x['sha256'])));by[i]=x;out.append(x)
 return by[i]
def g(i,t,y,c,v,lo,hi,n='',phase='upcoming',scope='whole_table',ys=None):
 x=dict(title=t,year=y,cohort=c,metrics=v if isinstance(v,dict) else {'places':v},lo=lo,hi=hi,notes=n,phase=phase,scope=scope,quality='high' if y else 'medium');b(i)['groups'].append(x)
 if ys:x['year_status']=ys
 return x
def h(i,t,y,c,v,lo,hi,n='',ys=None):return g(i,t,y,c,v,lo,hi,n,'retrospective',ys=ys)
def cr(i,t,y,c,lo,hi,of,ac,scope,n='Only this explicitly printed criterion; not whole-intake accepted offers.'):
 v={}
 if of is not None:v['offers']=of
 if ac is not None:v['acceptances']=ac
 x=g(i,t,y,c,v,lo,hi,n,'retrospective','criterion_'+scope)
 parent=next((z for z in by[i]['groups'] if z['cohort']==c and z['year']==y and z['phase']=='retrospective' and z['scope']=='whole_table' and z.get('year_status')),None)
 if parent:x['year_status']=parent['year_status']
 return x
# Balscadden genuine JI historical table; accepted criterion cells not summed.
g(1,'2027/2028','2027/2028','Junior Infants',25,28,31)
h(1,'2027/2028','2026/2027','Junior Infants',{'places':25,'applications':32,'offers':32,'waiting_list_names_placed':0},37,59)
for line,of,ac,k in [(50,18,18,'1_local_siblings'),(51,0,0,'2_staff'),(52,1,1,'3'),(53,6,3,'4'),(54,7,3,'5')]:cr(1,'2027/2028','2026/2027','Junior Infants',line,line,of,ac,k)
# St Vincent's has contradictory valid/malformed year headings. Exact table year retained with conflict flag, not strict comparability.
t='2027-2027 (invalid printed heading)'
g(11,t,None,'Junior Infants',38,4,48,'Title2027-2027, Part1 2025/26, application2024/25 and form2026/27 conflict. Filename is not evidence resolving the year.')
g(11,t,None,'ASD special class',0,29,56,'Conflicting year headings; no guessed future year.')
x=h(11,t,'2024/2025','Unspecified historical intake (first table, not inferred)',{'places':38,'applications':26,'offers':21,'offers_made_and_accepted_joint_count':21,'waiting_list_names_placed':{'value':0,'word':'none'}},59,74,'Specific table/intro2024/25 conflicts with Part2 2025/26. Count cell says none; direct written zero, not inferred from undersubscription.',ys='explicit_table_year_conflicting_section_header')
h(11,t,'2024/2025','Special class (type not explicitly repeated)',{'places':8,'applications':10,'offers':8,'offers_made_and_accepted_joint_count':8,'waiting_list_names_placed':1},77,93,'Specific special-class table explicitly2024/25; section wrapper2025/26 conflict retained. Joint count not aggregate acceptance-only.',ys='explicit_table_year_conflicting_section_header')
# Saint Finian's unusual retrospective/current numbers for SAME printed year stay in different phases.
g(13,'2022/2023','2022/2023','Junior Infants',20,18,45)
h(13,'2022/2023','2022/2023','Unspecified historical intake (not independently labelled)',{'places':42,'applications':42,'offers':42,'waiting_list_names_placed':0},54,88,'Source itself repeats2022/23 in Part2 and table. Do not silently relabel2021/22 or force an intake type. EarlyStart is a criterion, not necessarily an intake cohort.')
for lo,hi,n,k in [(74,75,27,'early_start'),(76,77,7,'siblings'),(78,78,8,'local')]:g(13,'2022/2023','2022/2023','Unspecified historical intake (not independently labelled)',{'offers_made_and_accepted_joint_count':n},lo,hi,'Joint criterion cell only, not separate offers/acceptance totals.','retrospective','criterion_'+k)
# North Dublin Project explicitly counts applications still VALID AT THE DRAW, not all applications.
for i,t,y,p,ap,wl,lo,hi in [(14,'2023/2024','2022/2023',28,149,121,56,86),(15,'2024/2025','2023/2024',26,135,107,54,85),(16,'2025/2026','2024/2025',27,116,87,54,85),(17,'2026/2027','2025/2026',28,114,None,54,88),(18,'2027/2028','2026/2027',27,119,None,57,92)]:
 g(i,t,t,'Junior Infants',None,1,26,'No upcoming quota is printed in this notice body; not zero.')
 x=h(i,t,y,'Junior Infants',{'places':p,'eligible_applications':ap,'offers':None,'acceptances':None,'waiting_list_names_placed':wl},lo,hi,'Source applications are explicitly still-valid-at-draw applications. No aggregate offer/accepted/list total is constructed from criterion rows.');x['metric_definitions']={'eligible_applications':'Source-explicit valid/eligible applications, excluding ineligible or no-longer-valid submissions; not all applications.'}
 if i==14:
  g(i,t,y,'Junior Infants',{'offers_made_and_accepted_joint_count':13},81,81,'Sibling joint cell13, not separate aggregate acceptance count.','retrospective','criterion_siblings');cr(i,t,y,'Junior Infants',82,82,15,None,'2_lottery')
 else:
  for a,z,of,ac,k in ([(79,79,11,11,'siblings'),(80,81,15,15,'2_lottery')] if i==15 else [(79,79,14,14,'siblings'),(80,81,13,13,'2_lottery')] if i==16 else [(79,79,13,12,'siblings'),(80,81,27,16,'2_lottery')] if i==17 else [(83,83,14,13,'siblings'),(84,85,72,14,'2_lottery')]):cr(i,t,y,'Junior Infants',a,z,of,ac,k)
 if i in [17,18]:
  for line,n,k in ([(84,61,'2'),(85,0,'3'),(86,4,'4'),(87,1,'5'),(88,6,'6')] if i==17 else [(88,19,'2'),(89,0,'3'),(90,2,'4'),(91,1,'5'),(92,8,'6')]):g(i,t,y,'Junior Infants',{'waiting_list_names_placed':n},line,line,'Printed per-category waiting-list names; not summed into a whole-intake total.','retrospective','criterion_'+k)
# St Anne's provides valuable dated historical revisions plus explicitly labelled supplementary waiting-list offers/acceptances.
for i,t,ji,lo,hi in [(19,'2024/2025',54,28,31),(20,'2024/2025',54,28,31),(21,'2025/2026',56,28,31),(22,'2025/2026',56,28,31),(23,'2026/2027',52,34,36),(24,'2027/2028',54,22,23)]:g(i,t,t,'Junior Infants',ji,lo,hi)
for i,t,y,p,ap,of,wl,lo,hi,asof in [(19,'2024/2025','2023/2024',69,103,103,0,33,64,'2023-06-22'),(20,'2024/2025','2023/2024',69,104,103,0,33,64,'2023-08-29'),(21,'2025/2026','2024/2025',56,114,114,0,33,66,'2024-08-30'),(22,'2025/2026','2024/2025',56,114,114,0,33,66,'2024-08-30'),(23,'2026/2027','2025/2026',48,96,90,0,38,79,'2025-08-30'),(24,'2027/2028','2026/2027',54,111,66,46,26,69,'2026-08-30')]:
 x=h(i,t,y,'Junior Infants',{'places':p,'applications':ap,'offers':of,'waiting_list_names_placed':wl},lo,hi,'Source-explicit asof retained. Criterion acceptances not summed; conflicting intro/detail application counts remain conflicts.');x['as_of']=asof
 if i==21:h(i,t,y,'Junior Infants',{'applications':113},39,40,'Intro113 conflicts with detailed114; no value silently selected.')['as_of']=asof
 if i==24:h(i,t,y,'Junior Infants',{'applications':116},31,32,'Intro116 conflicts with detailed111; no value silently selected.')['as_of']=asof
 if i in [19,20]:rows=[(48,53,57,46 if i==19 else 45,'1_sibling_catchment'),(54,54,1,1,'2_staff'),(55,58,15,8,'3_parish'),(59,60,22,6,'4_outside'),(61,61,8 if i==19 else 9,3 if i==19 else 4,'supplementary_waiting_list')]
 elif i in [21,22]:rows=[(50,55,63,45,'1'),(56,56,0,0,'2'),(57,60,19,8,'3'),(61,63,22,2,'4'),(64,64,10,1,'late')]
 elif i==23:rows=[(60,64,59,38,'1'),(66,66,1,0,'2'),(68,70,9,3,'3'),(72,73,13,2,'4'),(75,75,8,4,'late')]
 else:rows=[(46,50,64,52,'1'),(56,56,1,1,'2'),(58,60,1,1,'3'),(62,63,0,0,'4'),(65,65,0,0,'late')]
 for a,z,off,ac,k in rows:cr(i,t,y,'Junior Infants',a,z,off,ac,k)['as_of']=asof
 if i in [19,20]:
  x=g(i,t,y,'Junior Infants',{'waiting_list_offers':8 if i==19 else 9,'waiting_list_acceptances':3 if i==19 else 4},47,61,'Row explicitly Supplementary WaitingList, columns OffersMade and OffersAccepted. Counts are source totals at stated asof, NOT delta between editions. Acceptance is not actual admission/enrolment.','waiting_event','supplementary_waiting_list_source_snapshot');x['as_of']=asof
for i in [21,22]:
 g(i,'2025/2026','2025/2026','Autism special class',3,68,85)
 h(i,'2025/2026','2024/2025','Autism special class',{'places':4,'applications':11,'offers':4,'waiting_list_names_placed':7},87,120)['as_of']='2024-08-30'
 for a,z,of,ac,k in [(106,107,3,3,'1_current'),(108,110,1,1,'2_sibling')]:cr(i,'2025/2026','2024/2025','Autism special class',a,z,of,ac,k)['as_of']='2024-08-30'
g(23,'2026/2027','2026/2027','Autism special class',0,100,103)
h(23,'2026/2027',None,'Autism special class',{'places':3,'applications':14,'offers':4,'waiting_list_names_placed':10},105,136,'Part4header2026/27, detailed intro2025/26, tablecaption2024/25: year is genuinely unresolved, not relabelled by asof.')['as_of']='2025-08-30'
for a,z,of,ac,k in [(123,124,1,1,'1_current'),(125,126,1,1,'2_sibling'),(129,131,2,1,'4_parish')]:cr(23,'2026/2027',None,'Autism special class',a,z,of,ac,k)['as_of']='2025-08-30'
g(24,'2027/2028',None,'Autism special class',0,72,94,'Part3 title2027/28 versus special application and capacity2026/27. Future year unresolved.')
h(24,'2027/2028','2026/2027','Autism special class',{'places':0,'applications':10,'offers':0,'waiting_list_names_placed':10},96,129)['as_of']='2026-08-30'
# Donabate's combined-grade tables and explicit grade place breakdowns; no false JuniorInfant demand.
co='All listed intake groups combined: Junior Infants, Autism and other grades'
for i,t,y,places,ap,of,wl,hl,hh,ji in [(28,'2025/2026','2024/2025',56,258,64,194,117,146,46),(29,'2026/2027','2025/2026',54,246,89,157,117,149,46)]:
 g(i,t,t,'Junior Infants',ji,99,100,'Capacity title explicitly matches notice year; 2025/26 edition has one stale application-date heading2024/25, not used as quota year.')
 g(i,t,t,'Autism special class',None,99,105,'Unknown dependent on vacancies, not zero.')
 x=h(i,t,y,co,{'places':places,'applications':ap,'offers':of,'waiting_list_post_allocation_opt_in':wl},hl,hh,'Explicit combined JuniorInfants, SpecialClasses and other grades. List count follows family contact after allocation; no sum or JI-only ratios.');x['metric_definitions']={'waiting_list_post_allocation_opt_in':'Names explicitly opting onto list after allocation and subsequent contact with remaining families; not initial or cumulative-ever names.'}
 rows=[(134,136,31,30,1,'1_sibling'),(138,141,33,22,11,'2_lottery')] if i==28 else [(137,139,33,27,6,'1_sibling'),(141,144,56,27,29,'2_lottery')]
 for a,z,off,ac,decl,k in rows:cr(i,t,y,co,a,z,off,ac,k)['metrics']['offer_rejections']=decl
 splits=[('Junior Infants',50,125),('Autism special class',2,126),('First Class',1,127),('Fourth Class',1,128),('Fifth Class',1,129),('Sixth Class',1,130)] if i==28 else [('Junior Infants',46,125),('Autism special class',1,126),('Senior Infants',1,127),('First Class',1,128),('Second Class',2,129),('Third Class',1,130),('Fourth Class',1,131),('Fifth Class',1,132)]
 for cc,n,line in splits:h(i,t,y,cc,{'places':n},line,line,'Explicit grade-level retrospective places only; combined applications not attached.')
# Irish originals corroborate one year and expose a conflicting-year translation in the other edition.
for i,t,y in [(30,'2024/2025','2023/2024'),(31,'2025/2026',None)]:
 g(i,t,t,'Junior Infants',62,51,55)
 h(i,t,y,'Junior Infants',{'places':62,'applications':87,'offers':87,'acceptances':47,'waiting_list_names_placed':0},60,83,'Literal87(47glactha): explicit aggregate accepted47, not criterion sum.2025/26 Irish edition Part2/intake2024/25 conflicts with detailedcaption2023/24.' if i==31 else 'Irish source explicitly prints87offers,47accepted. Application timeline appears one calendar year late; academic quota/table headings retained.')
# St John's own-site years; the40/38 and20/20 rows are EXAMPLES, and2024/2025 in application-count blanks is a year, not thousands of applications.
for i,t,ji,sp,lo,hi in [(37,'2026/2027',25,2,31,37),(38,'2025/2026',25,2,23,28),(39,'2021/2022',25,0,25,42)]:
 g(i,t,t,'Junior Infants',ji,3,hi,'Body title anchors year where capacity heading remains an unfilled placeholder. Historical Part2 is blank/template, not numerical evidence.')
 g(i,t,None if i==38 else t,'Autism special class',sp,16 if i==38 else lo,hi,'Special application header2024/25 conflicts with overall2025/26; no guessed year.' if i==38 else 'Autism identified in same edition special-class application section. Historical template examples excluded.')
# Embedded notices in files named policies really can contain genuine historical tables.
g(0,'2026/2027','2026/2027','Junior Infants',19,266,297,'Completed annual-notice appendix within policy DOCX, not the blank application-form fields.')
g(0,'2026/2027','2026/2027','Autism special class',0,295,301)
h(0,'2026/2027','2025/2026','Special class (type not explicitly repeated)',{'places':0,'applications':9,'offers':1,'waiting_list_names_placed':8},305,323,'Historical intake explicitly specialclass; generic type retained rather than inventing grade or summing criteria.')
for line,n,k in [(316,1,'1_current'),(317,0,'2_sibling'),(318,0,'3_parish'),(319,0,'4_to_6_other')]:cr(0,'2026/2027','2025/2026','Special class (type not explicitly repeated)',line,line,n,None,k)
g(12,'2027/2028','2027/2028','Junior Infants',56,668,670,'Completed annual-notice appendix within policy PDF, not policy capacity guidance.')
g(12,'2027/2028','2027/2028','Autism special class',2,693,695)
h(12,'2027/2028','2026/2027','Autism special class',{'places':9,'applications':21,'offers':9,'offers_made_and_accepted_joint_count':9,'waiting_list_names_placed':12},699,730,'Intro18 versus detailed21 applications conflict. Literal total9offeredandaccepted preserved as a joint definition, not silently converted to an acceptance-only column.')
h(12,'2027/2028','2026/2027','Autism special class',{'applications':18},708,709,'Intro18 versus detailed21 application conflict.')
# Griffith Barracks cannot be turned into a JI funnel: source explicitly says JI/other-year-groups.
co='Unseparated Junior Infants and other year groups'
for i,t,y,p,ap,of,wl,lo,hi in [(25,'2026/2027',None,52,265,120,123,524,544),(26,'2027/2028','2026/2027',53,233,127,88,622,641)]:
 g(i,t,t,'Junior Infants',51 if i==25 else 50,501 if i==25 else 607,504 if i==25 else 610)
 h(i,t,y,co,{'places':p,'applications':ap,'offers':of,'waiting_list_names_placed':wl},lo,hi,'2025/26 table caption and intake versus2024/25 introduction conflict.' if i==25 else 'Unseparated grades; intro265 vs detailed233 applications conflict; totaloffers127 retained despite criteria25+99.')
 if i==26:h(i,t,y,co,{'applications':265},629,630,'Intro265 versus detailed233 application conflict.')
 for a,z,off,ac,k in ([(537,539,20,20,'sibling_staff'),(540,541,100,31,'other')] if i==25 else [(634,635,25,23,'sibling_staff'),(637,638,99,30,'other')]):cr(i,t,y,co,a,z,off,ac,k)
# Stratford appendix: multi-grade caveat retained; all criterion cells are joint-only, not invented offer totals.
g(40,'2023/2024','2023/2024','Junior Infants',12,496,531,'Announced12 places may be reduced if SeniorInfants admitted; combined infant ceiling26 is NOT JI-only capacity. One deadline footnote is stale2021.')
h(40,'2023/2024','2022/2023','Junior Infants',{'places':14,'applications':84,'offers':None,'acceptances':None,'waiting_list_names_placed':70},551,568,'No aggregate offers or accepted total printed. Criterion13+1 not summed.')
for line,n,k in [(560,13,'1'),(561,0,'2'),(562,1,'3'),(563,0,'4'),(564,0,'5'),(565,0,'6')]:g(40,'2023/2024','2022/2023','Junior Infants',{'offers_made_and_accepted_joint_count':n},line,line,'Literal joint-criterion cell, not an aggregate acceptance-only count.','retrospective','criterion_'+k)
# Year-specific inline quota in a policy, distinct from generic class-size ceilings elsewhere.
g(57,'2026/2027','2026/2027','Unspecified entry class (grade not named in inline quota)',29,136,141,'Irish explicitly says In26/27therewillbe29spacesintheclassoffered. No grade silently inferred from school age policy; generic class-size ceilings are not quota observations.')
for i,t,y,ji,sp,lo,hi,hl,hh in [(66,'2023/2024','2022/2023',21,6,605,612,616,619),(67,'2025/2026','2024/2025',21,2,603,610,614,616)]:
 g(i,t,t,'Junior Infants',ji,lo,hi,'Embedded actual notice, not inferred from file date.')
 g(i,t,t,'ASD and complex educational needs special class',sp,lo,hi,'Available new places differ from the maximum total class enrolment6; do not substitute ceiling6 for edition67quota2.')
 h(i,t,y,'All school intake groups (unseparated qualitative statement)',{'places':None,'applications':None,'offers':None,'acceptances':None,'waiting_list_names_placed':{'value':None,'status':'not_applicable'}},hl,hh,'Explicitly not oversubscribed/no waitinglistapplies. No numeric zero is manufactured for names ever placed, and no JI-only cohort is guessed.')
g(68,'2027/2028','2027/2028','Junior Infants',50,18,44);g(68,'2027/2028','2027/2028','Autism special class',0,46,71)
g(70,'2027/2028','2027/2028','Junior Infants',46,287,347);g(70,'2027/2028','2027/2028','Autism special class',1,322,351)
h(70,'2027/2028',None,'Unspecified historical intake (not independently labelled)',{'places':1,'applications':36,'offers':0,'waiting_list_names_placed':35},352,368,'Part2header26/27 versus table25/26 conflicts. Criterion1joint1 is not substituted for printed totaloffers0. URLending2020 is mutable and not admission year.')
# Audited exclusions: blank templates/example counts, other-county subjects, rule-only policies and navigation.
for i in range(len(A)):
 if i in by:continue
 x=b(i)
 if i in [32,33]:x['exclusion_reason']='Unfilled patron template naming[SCHOOLNAME];40/38and20/20 are explicit examples, not school data.'
 elif i in [34,35,36]:x['exclusion_reason']='Patron hosts MullingarETNS, Rathgowan, CountyWestmeath. Different school outside Dublin roster; no admissions metrics attributed to discovery roll20525B.'
 elif i in [69,71]:x['exclusion_reason']='Navigation/cookie-policy text, not numerical annual-notice body.'
 elif i in [2,3,4,5,6,7,8,9,10,27]:x['exclusion_reason']='Policy with unfilled annual-notice template and/or example counts. No actual dated numeric intake table; example counts excluded.'
 else:x['exclusion_reason']='Admission policy/rules/terms only. Bounded appendix/table-signal review found no completed dated school admissions table; generic class-size ceilings not treated as actual intake places.'
(P/'m2_reviewed_site_batch4.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print('sources',len(out),'groups',sum(len(x['groups']) for x in out))
