#!/usr/bin/env python3
"""Manual cell-level specs read from own-site batch3 sources. No network, no arithmetic totals."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];A=json.loads((P/'discovery_batch3_inventory.json').read_text());out=[];by={};times={}
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
g(2,'2027/2028','2027/2028','Junior Infants',12,3,20)
# Howth Road: preserve introductory vs detailed application conflicts and table-year caveats.
g(11,'2021/2020','2021/2022','Junior Infants',11,19,56,'Title is invalid2021/2020; Part1 and quota explicitly2021/22.')
h(11,'2021/2020','2020/2021','Junior Infants',{'places':15,'applications':54,'offers':20,'waiting_list_names_placed':34},71,95,'Part2 headline2021/22 vs specific table/intake2020/21. Intro15 applications conflicts with detailed54; no aggregate accepted sum.',ys='explicit_table_year_conflicting_section_header')
h(11,'2021/2020','2020/2021','Junior Infants',{'applications':15},75,78,'Introductory count conflicts with detailed54.',ys='explicit_table_year_conflicting_section_header')
for lo,hi,of,ac,s in [(86,88,5,4,'1_presbyterian'),(89,89,6,5,'2_sibling'),(91,91,9,6,'4_others')]:cr(11,'2021/2020','2020/2021','Junior Infants',lo,hi,of,ac,s)
g(12,'2022/2023','2022/2023','Junior Infants',13,51,54)
h(12,'2022/2023','2021/2022','Junior Infants',{'places':11,'applications':54,'offers':22,'waiting_list_remaining':32},64,94,'Section/intake and detailed caption2021/22; one invalid2021/2021 caption noted. Intro53 applications conflicts with detailed54. List32 explicitly qualified43 less11 offered, so not names ever placed.')
h(12,'2022/2023','2021/2022','Junior Infants',{'applications':53},72,73,'Intro53 vs detailed54 applications retained as conflict.')
for lo,hi,of,ac,s in [(78,79,4,4,'1_presbyterian'),(80,81,4,4,'2_sibling'),(82,83,1,1,'3_former_sibling'),(84,85,0,0,'4_staff'),(86,87,1,1,'5_past_pupil'),(88,89,11,1,'6_others')]:cr(12,'2022/2023','2021/2022','Junior Infants',lo,hi,of,ac,s)
x=g(12,'2022/2023','2021/2022','Junior Infants',{'waiting_list_prior_snapshot':43,'waiting_list_offers':11,'waiting_list_remaining':32},93,94,'Exact source list-row wording:32 (43 less11 offered). Movement counts are printed, not calculated differences. No waiting-list acceptance/admission count stated.','waiting_event','explicit_waiting_list_formula');x['metric_definitions']={'waiting_list_prior_snapshot':'Explicit earlier list count within a source waiting-list formula; not necessarily initial names ever placed.'}
g(13,'2023/2024','2023/2024','Junior Infants',11,51,54)
h(13,'2023/2024','2022/2023','Junior Infants',{'places':13,'applications':43,'offers':21,'offer_rejections':8,'waiting_list_remaining':19},64,94,'Source aggregate21offered8declined, list19(27less5offered3declined). Preserve exact list semantics; not an inferred acceptance13.')
for lo,hi,of,ac,s in [(78,79,1,None,'1_presbyterian'),(80,81,6,5,'2_sibling'),(82,83,0,0,'3_former_sibling'),(84,85,0,0,'4_staff'),(86,87,3,3,'5_past_pupil'),(88,89,11,5,'6_others')]:cr(13,'2023/2024','2022/2023','Junior Infants',lo,hi,of,ac,s)
x=g(13,'2023/2024','2022/2023','Junior Infants',{'waiting_list_prior_snapshot':27,'waiting_list_offers':5,'waiting_list_declined_unspecified':3,'waiting_list_remaining':19},93,94,'Exact source list-row wording19(27less5offered3declined). Declined3 is not classified as acceptance, admission, or necessarily rejection of an offered place. No arithmetic used.','waiting_event','explicit_waiting_list_formula');x['metric_definitions']={'waiting_list_declined_unspecified':'Explicit declined count in a waiting-list row; source does not establish whether a place or continuation on the list was declined.'}
g(14,'2024/2025','2024/2025','Junior Infants',12,54,56)
h(14,'2024/2025',None,'Junior Infants',{'places':12,'applications':31,'offers':12,'waiting_list_unspecified':0},71,94,'Historical section/table say2024/25(last year) inside2024/25 notice; intro2021/22 says12. Conflicting valid years, no guessed historical assignment. Criterion offers not summed.')
h(14,'2024/2025',None,'Junior Infants',{'applications':12},77,78,'Introductory count/year conflict retained.')
for lo,hi,of,ac,s in [(83,84,3,2,'1_presbyterian'),(85,85,1,1,'2_sibling'),(86,87,0,0,'3_past_sibling'),(88,88,1,0,'4_staff'),(89,89,1,0,'5_past_pupil'),(90,90,25,9,'6_others')]:cr(14,'2024/2025',None,'Junior Infants',lo,hi,of,ac,s)
g(15,'2026/2027','2026/2027','Junior Infants',11,54,56)
h(15,'2026/2027','2025/2026','Junior Infants',{'places':12,'applications':45,'offers':30,'waiting_list_unspecified':15},71,93,'Cell says15 on waiting list; no explicit source snapshot date, so not asserted names ever placed or dated remaining snapshot. No aggregate accepted sum.')
for lo,hi,of,ac,s in [(83,84,2,2,'1_presbyterian'),(85,85,6,6,'2_sibling'),(86,87,0,0,'3_past_sibling'),(88,88,0,0,'4_staff'),(89,89,3,1,'5_past_pupil'),(90,90,19,3,'6_others')]:cr(15,'2026/2027','2025/2026','Junior Infants',lo,hi,of,ac,s)
# Star of the Sea: exact separate mainstream and autism tables, including source errors.
for i,t,y,ji,sp,lo,hi in [(20,'2021/2022','2021/2022',45,None,106,109),(21,'2022/2023','2022/2023',45,0,118,134),(22,'2022/2023','2022/2023',45,0,118,134),(23,'2021/2022','2021/2022',45,None,141,144),(24,'2023/2024',None,45,2,118,130),(25,'2024/2025','2024/2025',30,0,119,130),(26,'2025/2026',None,30,0,118,129),(27,'2026/2027','2026/2027',30,0,116,127)]:
 g(i,t,y,'Junior Infants',ji,lo,hi,'Notice/Part1 year conflicts with capacity year; not resolved from URL.' if y is None else '')
 if sp is not None:g(i,t,y,'Autism special class',sp,lo,hi,'Conditional on construction of facilities by April2024.' if i==24 else 'Zero new availability is conditional on no transfer; no later movement inferred.')
for i,t,y,lo,hi,p,ap,of,wl,crit in [(20,'2021/2022','2020/2021',113,139,45,57,57,0,[(130,131,34,28,'A'),(132,133,0,0,'B'),(134,135,23,10,'C')]),(21,'2022/2023','2021/2022',136,163,45,62,62,0,[(154,155,29,21,'A'),(156,157,0,0,'B'),(158,159,33,14,'C')]),(22,'2022/2023','2021/2022',136,163,45,62,62,0,[(154,155,29,21,'A'),(156,157,0,0,'B'),(158,159,33,14,'C')]),(23,'2021/2022','2020/2021',151,178,45,57,57,0,[(169,170,34,28,'A'),(171,172,0,0,'B'),(173,174,23,10,'C')]),(24,'2023/2024',None,132,159,45,54,54,0,[(150,151,33,26,'A'),(152,153,0,0,'B'),(154,155,22,9,'C')]),(25,'2024/2025','2023/2024',132,158,45,59,59,0,[(149,150,35,23,'A'),(151,152,0,0,'B'),(153,154,24,6,'C')]),(26,'2025/2026',None,131,157,30,52,52,0,[(148,149,32,23,'A'),(150,151,0,0,'B'),(152,153,20,2,'C')]),(27,'2026/2027','2025/2026',129,154,30,50,50,0,[(145,146,23,19,'A'),(147,148,0,0,'B'),(149,150,27,6,'C')])]:
 h(i,t,y,'Junior Infants',{'places':p,'applications':ap,'offers':of,'waiting_list_names_placed':wl},lo,hi,'Exact printed totals; no sum of criterion acceptances. Conflicting historical intake/caption years retained.' if y is None else 'No sum of criterion acceptances.')
 if i==26:h(i,t,y,'Junior Infants',{'applications':59},140,141,'Introduction59 vs detailed52, within already year-conflicting historical section.')
 for a,z,ofr,ac,s in crit:cr(i,t,y,'Junior Infants',a,z,ofr,ac,s)
for i,t,y,lo,hi,p,ap,of,wl,crit in [(21,'2022/2023','2021/2022',166,183,3,14,4,10,[(174,175,4,3,'A'),(176,177,0,0,'B'),(178,179,0,10,'C')]),(22,'2022/2023','2021/2022',166,183,3,14,4,10,[(174,175,4,3,'A'),(176,177,0,0,'B'),(178,179,0,10,'C')]),(24,'2023/2024','2022/2023',162,179,1,12,1,11,[(170,171,1,1,'A'),(172,173,0,0,'B'),(174,175,0,10,'C')]),(25,'2024/2025','2023/2024',161,178,2,9,2,6,[(169,170,2,2,'A'),(171,172,0,0,'B'),(173,174,0,0,'C')]),(26,'2025/2026','2024/2025',160,177,1,11,1,10,[(168,169,0,0,'A'),(170,171,0,0,'B'),(172,173,1,1,'C')]),(27,'2026/2027','2025/2026',157,174,0,8,0,8,[(165,166,0,0,'A'),(167,168,0,0,'B'),(169,170,0,0,'C')])]:
 h(i,t,y,'Autism special class',{'places':p,'applications':ap,'offers':of,'waiting_list_names_placed':wl},lo,hi,'Source figures preserved even when criterion C inexplicably says0offers10accepted; no aggregate acceptance fabricated.')
 for a,z,ofr,ac,s in crit:cr(i,t,y,'Autism special class',a,z,ofr,ac,s,'Criterion-only source claim;0offered10accepted is preserved as source anomaly, not corrected or combined.' if ac>ofr else 'Criterion-only acceptance, not aggregate or observed admission.')
h(23,'2021/2022','2020/2021','Special class (type unspecified)',{'places':0},165,180,'Retrospective SpecialClass row separately prints0; no invented application/offer counts.')
g(32,'2027/2028','2027/2028','Junior Infants',75,6,17,'Full2027/28 application header anchors abbreviated27/28 academic year; CMS timestamp not a publication assertion.')
g(33,'2021/2022',None,'Junior Infants',60,17,35,'Notice/application2021/22 conflicts with capacity2020/21.');g(33,'2021/2022',None,'Special class (type unspecified)',0,31,35)
g(34,'2026/2027','2026/2027','Junior Infants',60,16,54);g(34,'2026/2027','2026/2027','Special class (type unspecified)',12,50,56)
h(34,'2026/2027','2025/2026','Junior Infants',{'places':60,'applications':77,'offers':74,'waiting_list_names_placed':3},58,84,'Total offers74 printed; criterion counts not substituted or summed; no aggregate accepted count.')
for a,z,of,ac,s in [(61,67,4,4,'1'),(69,74,0,0,'2'),(76,81,64,33,'3')]:cr(34,'2026/2027','2025/2026','Junior Infants',a,z,of,ac,s)
# Springdale explicitly states including second-round offers, not solely first-round.
for i,t,y,lo,hi,p,ap,of,wl,crit in [(46,'2023/2024','2022/2023',42,69,26,60,34,1,[(56,56,7,6,'1'),(58,58,2,2,'2'),(60,60,4,4,'3'),(62,62,11,10,'4'),(64,64,10,4,'5')]),(47,'2024/2025','2023/2024',43,83,24,68,34,20,[(57,64,13,11,'1'),(66,67,0,None,'2'),(69,70,8,7,'3'),(72,75,13,6,'4'),(77,79,0,None,'5')]),(48,'2025/2026','2024/2025',43,83,24,61,28,11,[(57,64,9,9,'1'),(66,67,1,1,'2'),(69,70,11,11,'3'),(72,75,7,3,'4'),(77,79,0,None,'5')]),(49,'2026/2027','2025/2026',45,82,24,54,33,5,[(57,66,10,9,'1'),(67,68,1,1,'2'),(69,70,7,6,'3'),(71,74,6,3,'4'),(75,78,9,5,'5')]),(50,'2026/2027','2025/2026',45,81,24,54,33,5,[(57,65,10,9,'1'),(66,67,1,1,'2'),(68,69,7,6,'3'),(70,73,6,3,'4'),(74,77,9,5,'5')])]:
 cl,ch=(36,39) if i==46 else (38,41) if i in [47,48] else (39,43);g(i,t,t,'Junior Infants',24,cl,ch)
 h(i,t,y,'Junior Infants',{'places':p,'applications':ap,'offers':of,'waiting_list_names_placed':wl},lo,hi,'Source includes second-round offers. All criterion acceptances stay scoped; no aggregate sum.')
 for a,z,ofr,ac,s in crit:cr(i,t,y,'Junior Infants',a,z,ofr,ac,s)
g(51,'2025/2026',None,'All classes: special-school intake',7,16,36,'Part1/title2025/26 conflicts with capacity2024/25.')
h(51,'2025/2026','2024/2025','All classes: special-school intake',{'places':3,'applications':38,'eligible_applications':28,'offers':3,'waiting_list_names_placed':35},38,59,'Introduction explicitly valid applications28; detailed all applications38. Different definitions, not a silently selected count.')['metric_definitions']={'eligible_applications':'Source-explicit valid/eligible applications, excluding ineligible submissions; not all applications.'}
cr(51,'2025/2026','2024/2025','All classes: special-school intake',53,54,1,1,'catchment');cr(51,'2025/2026','2024/2025','All classes: special-school intake',55,56,2,2,'outside_catchment')
# St Kevin GNS: 2022/23 explicitly all categories accepted24. Other joint-count cells stay distinct.
for i,t,ji,sp,lo,hi in [(72,'2021/2022',29,0,66,71),(73,'2022/2023',60,0,57,62),(74,'2022/2023',60,0,72,77),(75,'2024/2025',28,None,57,61),(76,'2025/2026',28,1,64,68)]:
 g(i,t,t,'Junior Infants',ji,lo,hi,'Capacity paragraph erroneously names Boys School while notice header and printed roll19466E identify GNS; identity caveat retained.' if i==75 else '')
 g(i,t,t,'Autism special class',sp,lo,hi,'Source explicitly unknown, not0.' if sp is None else '')
for i,lo,hi,sl,sh in [(73,69,82,84,96),(74,78,91,93,105)]:
 h(i,'2022/2023','2021/2022','Junior Infants',{'places':29,'applications':36,'offers':30,'waiting_list_names_placed':6},lo,hi,'Category1&2 ambiguous parenthesized29 is not asserted an aggregate acceptance count.')
 h(i,'2022/2023','2020/2021','Autism special class',{'places':0,'applications':12,'offers':0,'waiting_list_names_placed':12},sl,sh,'Intro says7e applications versus detailed12; malformed intro retained verbatim, not forced to an integer7. Academic year explicitly2020/21, not previous2021/22.')
h(75,'2024/2025','2022/2023','Junior Infants',{'places':28,'applications':28,'offers':28,'acceptances':24,'waiting_list_names_placed':0},64,77,'Source says all categories offered28 places and24 accepted. Explicit aggregate, not summed or actual admissions.')
h(75,'2024/2025','2022/2023','Autism special class',{'places':1,'applications':12,'offers':2,'waiting_list_names_placed':11},79,90,'Intro11 vs detailed12 applications conflicts. Two places offered and accepted belongs Category1 only, not aggregate.')
h(75,'2024/2025','2022/2023','Autism special class',{'applications':11},79,79,'Explicit introduction11 vs detailed12 applications conflict.')
cr(75,'2024/2025','2022/2023','Autism special class',85,86,2,2,'1')
x=h(76,'2025/2026','2024/2025','Junior Infants',{'places':56,'applications':41,'offers':41,'offers_made_and_accepted_joint_count':34,'waiting_list_names_placed':41},72,84,'Joint made-and-accepted row34 is not unambiguously an acceptance-only aggregate; preserve separate metric. Source list41 is retained, not calculated as applications minus offers.');x['metric_definitions']={'offers_made_and_accepted_joint_count':'Literal numeric cell for offers made and accepted under each criterion with no separately identifiable acceptance-only aggregate; not silently relabelled acceptances.'}
h(76,'2025/2026','2024/2025','Autism special class',{'places':0,'applications':12,'offers':0,'offers_made_and_accepted_joint_count':0,'waiting_list_names_placed':12},87,96,'Joint offers-made-and-accepted row retained without inference.')
# Divine Word live edition has fully separated JI/autism historical tables; no aggregate acceptance sums.
for i in [89,90]:
 g(i,'2027/2028','2027/2028','Junior Infants',56,22,43);g(i,'2027/2028','2027/2028','Autism special class',0,44,62)
 h(i,'2027/2028','2026/2027','Junior Infants',{'places':56,'applications':164,'offers':122,'waiting_list_names_placed':42},69,94)
 h(i,'2027/2028','2026/2027','Autism special class',{'places':6,'applications':18,'offers':8,'waiting_list_names_placed':10},95,120)
 for c,rows in [('Junior Infants',[(78,80,60,48,'1'),(81,83,1,0,'2'),(84,87,61,8,'3'),(88,90,0,0,'4')]),('Autism special class',[(104,106,3,2,'1'),(107,109,0,0,'2'),(110,113,5,4,'3'),(114,116,None,0,'4')])]:
  for a,z,of,ac,s in rows:cr(i,'2027/2028','2026/2027',c,a,z,of,ac,s)
# Dalkey School Project: exact table years remain distinguishable from Part2 wrapper headings.
for i,t,v,lo,hi,hy,p,ap,of,wl,hl,hh,crit in [(95,'2021/2022',29,46,49,'2020/2021',29,183,85,96,64,91,[(78,79,13,10,'1'),(81,82,72,19,'2')]),(96,'2023/2024',28,65,68,'2022/2023',29,219,74,134,83,106,[(95,97,14,11,'1'),(99,101,60,18,'2')]),(97,'2022/2023',29,59,62,'2021/2022',29,219,51,167,77,100,[(89,91,16,15,'1'),(93,95,35,14,'2')]),(98,'2024/2025',28,62,65,'2023/2024',28,173,96,161,77,105,[(94,96,18,14,'1'),(98,100,78,14,'2')]),(99,'2025/2026',28,60,63,'2024/2025',28,172,172,0,75,105,[(88,90,37,4,'1'),(92,93,8,6,'2'),(95,98,125,16,'3')]),(100,'2026/2027',28,61,64,'2025/2026',28,156,132,0,71,101,[(87,88,13,12,'1'),(90,91,120,16,'2')])]:
 g(i,t,t,'Junior Infants',v,lo,hi)
 h(i,t,hy,'Junior Infants',{'places':p,'applications':ap,'offers':of,'waiting_list_names_placed':wl},hl,hh,'Detailed caption/introduction identify this table year; Part2 wrapper carries current notice year in some editions. No criterion acceptance totals calculated.',ys='explicit_table_year_conflicting_section_header' if i in [96,97,98] else None)
 for a,z,ofr,ac,s in crit:cr(i,t,hy,'Junior Infants',a,z,ofr,ac,s)
 if i in [98,100]:h(i,t,hy,'Junior Infants',{'applications':219 if i==98 else 172},85 if i==98 else 74,86 if i==98 else 76,'Introductory count conflicts with detailed table, retained rather than chosen.',ys='explicit_table_year_conflicting_section_header' if i==98 else None)
g(108,'2026/2027','2026/2027','Junior Infants',50,44,51);g(108,'2026/2027','2026/2027','Autism special classes',0,44,51)
h(108,'2026/2027','2025/2026','Autism special classes',{'places':1,'applications':17,'offers':1,'waiting_list_names_placed':13},54,73)
cr(108,'2026/2027','2025/2026','Autism special classes',67,67,1,1,'2_existing_mainstream')
for i in [6,10,70,92,93,94,104,105,106]:b(i)['exclusion_reason']='Navigation or annual-notice reference, not an actual numerical notice body.'
(P/'m2_reviewed_site_batch3a.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print('sources',len(out),'groups',sum(len(x['groups']) for x in out))
