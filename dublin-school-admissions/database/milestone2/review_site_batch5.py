#!/usr/bin/env python3
import json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];A=json.loads((P/'discovery_batch5_inventory.json').read_text());out=[];by={}
def b(i):
 if i not in by:
  x=A[i].copy();x.update(groups=[],url=x.get('url',x.get('original_url')),sha256=x.get('sha256',x.get('payload_sha256')),retrieval_url=x.get('archived_url',x.get('url')),capture_timestamp=x.get('capture',{}).get('timestamp'),retrieved_at=x.get('attempted_at'),memento_datetime_header=x.get('headers',{}).get('memento-datetime'));by[i]=x;out.append(x)
 return by[i]
def g(i,t,y,c,metrics,lo,hi,notes='',phase='upcoming',scope='whole_table',ys=None):
 x=dict(title=t,year=y,cohort=c,metrics=metrics,lo=lo,hi=hi,notes=notes,phase=phase,scope=scope,quality='high' if y else 'medium')
 if ys:x['year_status']=ys
 b(i)['groups'].append(x);return x
def h(i,t,y,c,m,lo,hi,n='',ys=None):return g(i,t,y,c,m,lo,hi,n,'retrospective',ys=ys)
# Archived HTML explicitly dates ASD intake and six NEW places in2022/23, not current enrolled six in2023/24.
g(30,'2022/2023','2022/2023','ASD special class',{'places':6},147,167,'Explicit current-year ASD annual notice in archived homepage. Capture calendar year is not used to infer intake year.')
# Bishop Galvin is a senior school: never relabel ThirdClass as JuniorInfants.
for i,t,p,asd in [(299,'2025/2026',110,1),(300,'2026/2027',112,2)]:
 g(i,t,t,'Third Class',{'places':p},15,31)
 g(i,t,t,'Autism class (Third to Sixth Class)',{'places':asd},15,31)
h(299,'2025/2026','2024/2025','Third Class',{'places':110,'applications':113,'offers':110,'acceptances':None,'waiting_list_names_placed':3},54,76,'Part2 generic title repeatsnotice2025/26; detailed intake,intro and table all explicitly2024/25. Criterion acceptance110 is not reclassified as an aggregate.')
g(299,'2025/2026','2024/2025','Third Class',{'offers':110,'acceptances':110},63,70,'Explicit first criterion only, not aggregate.','retrospective','criterion_1_Bishop_Shanahan')
h(299,'2025/2026','2024/2025','Autism class',{'places':2,'applications':2,'offers':2,'waiting_list_names_placed':0},79,100,'Detailed breakdown explicitly2024/25; introductory2024 is a start-year shorthand, not an invented different academic period.')
h(299,'2025/2026','2024/2025','Fourth / Fifth / Sixth Class combined',{'places':7,'applications':17,'offers_made_and_accepted_joint_count':7,'waiting_list_names_placed':10},102,130,'Total row is joint made-and-accepted count; not silently substituted for distinct aggregate acceptance field.')
h(300,'2026/2027','2025/2026','Third Class',{'places':116,'applications':121,'offers':116,'acceptances':None,'waiting_list_names_placed':3},55,76,'Explicit completed applications and ThirdClass retrospective group; criterion accepted114 not summed with other rows.')
g(300,'2026/2027','2025/2026','Third Class',{'offers':116,'acceptances':114},63,70,'Printed first criterion only; not whole-intake accepted total.','retrospective','criterion_1_Bishop_Shanahan')
h(300,'2026/2027','2025/2026','Autism class',{'places':1,'applications':2,'offers':1,'acceptances':1,'waiting_list_names_placed':1},80,101,'Aggregate total explicitly says1offered,1accepted. Acceptance is NOT actual enrolment/admission.')
h(300,'2026/2027','2025/2026','Fourth / Fifth / Sixth Class combined',{'places':2,'applications':11,'offers':2,'acceptances':None,'waiting_list_names_placed':9},102,130)
# Newly accessible own-site source proves actual senior and autism quota; existing primary year is not a new pair.
lines=(R/A[303]['text_file']).read_text().splitlines()
def span(a,z):
 lo=next(i+1 for i,x in enumerate(lines) if a in x);hi=next(i+1 for i,x in enumerate(lines[lo-1:],lo-1) if z==x.strip());return lo,hi
g(303,'2027/2028','2027/2028','Third Class',{'places':17},*span('Number of places being made available in 2027/28','17'))
g(303,'2027/2028','2027/2028','Autism special class',{'places':1},*span('Number of places being made available in 2027/28','1'))
for i in [301,302]:b(i)['exclusion_reason']='Blank application forms, not annual notices; hosted subject is Dundalk CoLouth roll18504E, not discovery identity18968A. No pupil/parent values present or extracted.'
(P/'m2_reviewed_site_batch5.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(len(out),sum(len(x['groups']) for x in out))
