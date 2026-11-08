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
# St Francis gives24:1 per class, not an exact intake capacity.
x=g(110,'2020/2021','2020/2021','Third Class',None,20,36,'Source says number per ThirdClass24:1: a ratio, not total new places. Exact intake total not published.');x['metrics']['pupil_teacher_ratio_numerator']=24;x['metrics']['pupil_teacher_ratio_denominator']=1;x['metric_definitions']={'pupil_teacher_ratio_numerator':'Literal pupil-to-teacher ratio numerator, not available intake places.','pupil_teacher_ratio_denominator':'Literal pupil-to-teacher ratio denominator, not intake places.'}
# St Attracta senior: ThirdClass and autism remain separate; criterion acceptance counts never summed.
for i,t,y,ap,of,wl,cl,ch,hl,hh in [(112,'2022/2023','2021/2022',83,83,0,58,61,63,99),(113,'2023/2024','2022/2023',87,87,0,58,61,63,99),(116,'2024/2025','2023/2024',89,89,0,58,61,63,99),(119,'2025/2026','2024/2025',90,90,0,56,58,66,100),(117,'2026/2027','2025/2026',95,92,3,58,60,68,102),(118,'2026/2027','2025/2026',95,92,3,58,60,68,102)]:
 g(i,t,t,'Third Class',90,cl,ch)
 h(i,t,y,'Third Class',{'places':90,'applications':ap,'offers':of,'waiting_list_names_placed':wl},hl,hh,'Exact senior intake, not Junior Infants. No total accepted offers is printed; criteria not summed.')
 if i in [112,113,116]:rows=[(78,85,of,of,'1'),(87,89,0,0,'2'),(91,93,0,0,'3')]
 elif i==119:rows=[(79,86,90,90,'1'),(88,90,0,0,'2'),(92,94,0,0,'3')]
 else:rows=[(81,88,91,91,'1'),(90,92,0,0,'2'),(94,96,1,1,'3')]
 for a,z,off,ac,k in rows:cr(i,t,y,'Third Class',a,z,off,ac,k)
for i in [114,115]:g(i,'2024/2025','2024/2025','ASD special class' if i==114 else 'Ambiguous ASD versus Third Class intake',6,52,54,'April edition explicitly ASD6; March edition ASD section title conflicts with capacity row naming ThirdClass. Distinct editions; March scope stays unmatched.')
for i in [117,118]:
 g(i,'2026/2027','2026/2027','Autism special class',0,64,66)
 h(i,'2026/2027','2025/2026','Autism special class',{'places':2,'applications':4,'offers':2,'waiting_list_names_placed':0},110,152,'Explicit special-class historical table, not ThirdClass totals.')
 for a,z,of,ac,k in [(124,126,2,2,'1'),(128,130,0,0,'2'),(132,136,0,0,'3'),(138,140,0,0,'4'),(142,143,0,0,'5'),(145,146,0,0,'6')]:cr(i,'2026/2027','2025/2026','Autism special class',a,z,of,ac,k)
g(119,'2025/2026','2025/2026','ASD special class',2,62,64)
h(119,'2025/2026','2024/2025','ASD special class',{'places':6,'applications':4,'offers':4,'waiting_list_names_placed':0},108,149)
for a,z,of,ac,k in [(121,123,1,1,'1'),(125,127,3,3,'2'),(129,133,0,0,'3'),(135,137,0,0,'4'),(139,140,0,0,'5'),(142,143,0,0,'6')]:cr(119,'2025/2026','2024/2025','ASD special class',a,z,of,ac,k)
# Mutable Irish DOCX filename2023/24 actually prints2027/28; use body years only.
g(140,'2027/2028','2027/2028','Junior Infants',28,26,35,'Irish source NaíonáinShóisearacha=JuniorInfants; filename is not the academic year.')
h(140,'2027/2028','2026/2027','Junior Infants',{'places':28,'applications':56,'offers':29,'waiting_list_names_placed':27},41,63,'Irish iarratas means applications, tairiscintí offers, glactha accepted. Aggregate acceptance not printed.')
for line,of,ac,k in [(54,18,17,'1_siblings'),(55,1,1,'2_irish_level3'),(56,6,6,'3_irish_level2'),(58,3,3,'5_past_pupil'),(59,1,1,'6_age')]:cr(140,'2027/2028','2026/2027','Junior Infants',line,line,of,ac,k)
# Donabate Portrane combined tables must never be presented as Junior Infant-only demand.
combined='All listed intake groups combined: Junior Infants, Autism and other grades'
for i,t,y,cl,ch,hl,hh,p,ap,of,wl in [(146,'2021/2022','2020/2021',64,72,85,113,52,178,99,15),(148,'2023/2024','2022/2023',85,97,115,142,53,157,157,0),(149,'2023/2024','2022/2023',85,97,115,142,53,157,157,0),(150,'2024/2025','2023/2024',98,109,127,154,57,196,107,139),(151,'2024/2025','2023/2024',98,109,127,154,57,196,107,139),(152,'2024/2025','2023/2024',98,109,127,154,57,196,107,139)]:
 g(i,t,None if i==146 else t,'Junior Infants',52 if i==146 else 50,cl,ch,'2021/22 title vs available places2020 conflict.' if i==146 else '')
 g(i,t,None if i==146 else t,'Autism special class',2 if i==146 else None,cl,ch,'Source unknown dependent on vacancies, not0.' if i!=146 else 'Title/capacity year conflict.')
 x=h(i,t,y,combined,{'places':p,'applications':ap,'offers':of,'waiting_list_post_allocation_opt_in':wl},hl,hh,'Source heading explicitly includes JuniorInfants, SpecialClasses and other grades. Waiting-list figure is after remaining families were contacted following allocation; not names ever placed throughout the process. No cross-cohort applications/places ratio.');x['metric_definitions']={'waiting_list_post_allocation_opt_in':'Names explicitly opting onto list after allocation and subsequent contact with remaining families; not initial or cumulative-ever names.'}
 if i==146:rows=[(99,102,28,22,6,None,'1_siblings'),(104,108,69,30,12,27,'2_first_come')]
 elif i in [148,149]:rows=[(127,130,28,26,2,None,'1_siblings'),(132,136,129,27,6,96,'2_first_come')]
 else:rows=[(141,144,21,14,None,7,'1_siblings'),(146,149,86,36,None,50,'2_first_come')]
 for a,z,off,ac,deferred,rej,k in rows:
  q=cr(i,t,y,combined,a,z,off,ac,k)
  if deferred is not None:q['metrics']['offers_deferred_to_next_entry_year']=deferred;q.setdefault('metric_definitions',{})['offers_deferred_to_next_entry_year']='Source-explicit offered places deferred to the named following intake calendar year; not this-year acceptance or admission.'
  if rej is not None:q['metrics']['offer_rejections']=rej
 if i in [148,149]:splits=[('Junior Infants',50,123),('Autism special class',2,124),('Fourth Class',1,125)]
 elif i in [150,151,152]:splits=[('Junior Infants',50,136),('Autism special class',3,137),('Second Class',3,138),('Fifth Class',1,139)]
 else:splits=[]
 for co,v,line in splits:h(i,t,y,co,{'places':v},line,line,'Explicit retrospective place subgroup only; combined applications/offers never attached.')
 if i in [150,151,152]:
  for co,v,line in [('Junior Infants',50,121),('Autism special class',3,122)]:
   q=g(i,t,'2023/2024',co,{'pre_act_places_offered_and_accepted':v},116,line,'Explicit pre-Section62 offered-and-accepted places for2023/24; not current2024/25 quota or all-intake acceptance total.','pre_commencement','pre_section_62_commencement');q['metric_definitions']={'pre_act_places_offered_and_accepted':'Places explicitly offered and accepted before Section62 commencement for this printed intake year; not all-intake offers/acceptance totals.'}
# Bilingual year/definition conflict: retain both descriptions without guessing2021/22 or equating registrations with offers.
g(161,'2021/2022',None,'Junior Infants',52,50,67,'Irish title2021/22 versus English2020/21. Available-entryyear2021 does not remove conflicting language-edition year labels.')
x=g(161,'2021/2022',None,'Junior Infants',{'pre_act_places_offered_and_accepted':47},55,63,'Irish text explicitly says places offered and accepted before commencement; bilingual English says registrations. Do not silently merge definitions.','pre_commencement','Irish_source_wording');x['metric_definitions']={'pre_act_places_offered_and_accepted':'Explicit places offered and accepted before Section62 commencement, with source/year qualifiers retained.'}
x=g(161,'2021/2022',None,'Junior Infants',{'pre_act_registered_children':47},121,124,'English source says children registered forJuniorInfants2021; not applications or necessarily accepted school-place offers.','pre_commencement','English_source_wording');x['metric_definitions']={'pre_act_registered_children':'Children explicitly registered on pre-commencement enrolment list; not applications or school-place offers/acceptances.'}
g(166,'2026/2027','2026/2027','All classes and ages: special-school intake',2,9,36)
h(166,'2026/2027','2025/2026','All classes and ages: special-school intake',{'places':4,'applications':75,'offers':4,'waiting_list_names_placed':71,'offers_made_and_accepted_joint_count':4},45,60,'Criteria1 joint cell4 is not a separately printed aggregate acceptance-only total.')
# Gaelscoil Shliabh Rua explicitly prints accepted totals in parentheses: source counts, not criterion sums.
for i,t,y,ap,ac,lo,hi in [(168,'2025/2026','2024/2025',87,47,49,72),(169,'2024/2025','2023/2024',87,47,49,72),(170,'2024/2025','2022/2023',102,50,49,72),(171,'2026/2027','2025/2026',93,44,47,75)]:
 g(i,t,None if i==171 else t,'Junior Infants',62,42,45,'2026/27 title conflicts with capacity2025/26.' if i==171 else '')
 h(i,t,y,'Junior Infants',{'places':62,'applications':ap,'offers':ap,'acceptances':ac,'waiting_list_names_placed':0},lo,hi,'Accepted total is explicitly parenthesized beside totaloffers, not summed from criteria.2022/23 edition conflicts with Part2header2023/24.',ys='explicit_table_year_conflicting_section_header' if i==170 else None)
# Broombridge distinguishes future quota revisions, exact autism cohorts and genuinely unlabelled drafts.
for i,t,ji,sp,lo,hi in [(172,'2021/2022',60,0,108,125),(173,'2022/2023',60,0,96,105),(174,'2021/2022',60,6,96,105),(175,'2023/2024',60,0,96,105),(176,'2024/2025',60,1,109,120),(177,'2024/2025',60,1,96,105),(178,'2025/2026',60,0,112,123),(179,'2026/2027',60,1,127,131)]:
 g(i,t,t,'Junior Infants',ji,lo,hi);g(i,t,t,'Autism special class',sp,lo,hi,'Source revisions0 versus6 available2021/22 retained; no inferred transfer or list movement.')
for i,t,y,c,p,ap,of,joint,wl,lo,hi in [(172,'2021/2022','2020/2021','Autism special class',0,1,0,0,1,132,148),(173,'2022/2023','2021/2022','Autism special class',6,16,7,6,2,112,128),(174,'2021/2022','2020/2021','Autism special class',0,1,0,0,1,112,128),(175,'2023/2024','2022/2023','Autism special class',0,6,0,0,6,112,128),(176,'2024/2025','2023/2024','Unspecified historical intake (not inferred)',0,2,0,0,2,128,140),(177,'2024/2025','2023/2024','Autism special class',0,2,0,0,2,112,128),(178,'2025/2026','2024/2025','Unspecified historical intake (not inferred)',1,7,1,1,5,131,143)]:
 h(i,t,y,c,{'places':p,'applications':ap,'offers':of,'offers_made_and_accepted_joint_count':joint,'waiting_list_names_placed':wl},lo,hi,'Joint made-and-accepted count kept distinct from acceptance-only total; no conversion to admissions.',ys='explicit_table_year_conflicting_intake_or_section_header' if i in [175,178] else None)
h(179,'2026/2027','2025/2026','Junior Infants',{'places':60,'applications':177,'offers':60,'waiting_list_names_placed':0},151,173,'Printed totaloffers60 retained despite criterion18+42+2; no arithmetic correction or inferred acceptance total.')
for a,z,off,ac,k in [(163,165,18,18,'1_sibling'),(166,168,42,22,'2_catchment'),(169,171,2,2,'3_outside')]:cr(179,'2026/2027','2025/2026','Junior Infants',a,z,off,ac,k)
h(179,'2026/2027','2025/2026','Autism special class',{'places':2,'applications':6,'offers':2,'waiting_list_names_placed':4},175,195)
x=g(179,'2026/2027','2025/2026','Autism special class',{'offers_made_and_accepted_joint_count':2},185,186,'Current-student CriterionOne joint row only; no aggregate acceptance-only claim.','retrospective','criterion_1_current_students')
# These two patron-hosted notices name/print Cherrywood20535E, not the discovery-page school20525B.
for i,t in [(186,'2021/2022'),(187,'2020/2021')]:
 x=b(i);x['discovered_under_roll']=x['roll'];x['roll']='20535E';x['identity_review']='Printed Cherrywood ETNS name/address and roll20535E in2020 original; source subject independently matches roster. Patron-host discovery owner is not subject school.'
 g(i,t,t,'Junior Infants',26,56 if i==186 else 1,60 if i==186 else 25,'Identity corrected to subject Cherrywood20535E; no admissions metrics attributed to discovery context20525B.')
 if i==186:g(i,t,t,'Senior Infants',20,36,60,'Explicit separate Senior Infant quota, not additional Junior Infant places.')
for i,reason in [(122,'Landing-page excerpt/ReadMore, not notice body.'),(129,'Notice announced for future publication; navigation only, not a numerical notice.'),(138,'Admission policy, not an annual numerical notice.'),(142,'Google-published admission policy, not a notice.'),(147,'Explicit DRAFT notice; numeric claims duplicate non-draft source146. Retained as excluded draft source, not silently treated as final.'),(181,'Annual-notice download links, not numerical body.'),(183,'Annual-notice reference/navigation, not actual notice body.')]:b(i)['exclusion_reason']=reason
(P/'m2_reviewed_site_batch3b.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print('sources',len(out),'groups',sum(len(x['groups']) for x in out))
