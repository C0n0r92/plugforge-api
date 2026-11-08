#!/usr/bin/env python3
"""Explicit manual numeric review of formerly unparsed annual notices; policy scans fully visually checked."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];A=json.loads((P/'discovery_batch6_inventory.json').read_text());by={};out=[]
def b(i):
 if i not in by:x={**A[i],'groups':[],'retrieval_url':A[i]['url']};by[i]=x;out.append(x)
 return by[i]
def span(i,start,end=None):
 lines=(R/b(i)['text_file']).read_text().splitlines();lo=next(j+1 for j,l in enumerate(lines) if re.search(start,l,re.I));hi=next((j+1 for j,l in enumerate(lines[lo:],lo) if re.search(end,l,re.I)),len(lines)) if end else len(lines);return lo,hi
def g(i,t,y,c,v,rg,notes='',phase='upcoming',scope='whole_table',ys=None):
 x=dict(title=t,year=y,cohort=c,metrics=v,lo=rg[0],hi=rg[1],notes=notes,phase=phase,scope=scope,quality='high' if y else 'medium')
 if ys:x['year_status']=ys
 b(i)['groups'].append(x);return x
def h(i,t,y,c,v,rg,n='',ys=None):return g(i,t,y,c,v,rg,n,'retrospective',ys=ys)
# No ANNUAL ADMISSION NOTICE title, but source is an actual filled FirstClass/Autism annual notice.
g(2,'2026/2027','2026/2027','First Class',{'places':50},span(2,'Number of places being made available in 2026','PART 2'))
g(2,'2026/2027','2026/2027','Autism special class',{'places':3},span(2,'Number of places being made available in 2026','PART 2'))
h(2,'2026/2027','2025/2026','Autism special class',{'places':4,'applications':5,'offers':4,'acceptances':None,'waiting_list_names_placed':1},span(2,'PART 2'),'Only criterion2 explicitly accepted4; not manufactured aggregate acceptance.')
g(2,'2026/2027','2025/2026','Autism special class',{'offers':4,'acceptances':4},span(2,'Number of Offers made','Total number of offers made'),'Explicit feeder-school criterion only.','retrospective','criterion_2_feeder_school')
g(3,'2027/2028','2027/2028','ASD special class',{'places':0},span(3,'Number of places being made available in 2027'),'Direct printed0, not an inference from prose currently full.')
# Phoenix's historical printed periods conflict. Do NOT force a dated full funnel.
g(4,'2026/2027 (Part1)','2026/2027','All primary special-school classes: Severe EBD',{'places':5},span(4,'Number of places available in 2026'), 'Capacity and Part1 agree2026/27, introductory policy-copy availability says2025/26. Preserve conflict flag.',ys='explicit_quota_year_conflicting_intro')
g(7,'2027/2028','2027/2028','All primary special-school classes: Severe EBD',{'places':4},span(7,'Number of places available in 2027'))
for i,title,p,ap,ac,wl in [(4,'2026/2027 (Part1)',5,12,5,5),(7,'2027/2028',3,10,3,2)]:
 x=h(i,title,None,'All primary special-school classes: Severe EBD',{'places':p,'applications':ap,'offers':None,'acceptances':ac,'waiting_list_eligible_names':wl},span(i,'PART 2'),'Historical wrapper/intake and detailedintro/table give conflicting academic years. Total-offers row VALUE explicitly says places accepted; retain accepted count but do not silently turn it into offers. Waitinglist explicitly restricted to those meeting criteria, not all names ever placed.')
 x['metric_definitions']={'waiting_list_eligible_names':'Source count on waiting list explicitly meeting criteria; not all applications or all names ever placed.'}
# Baldoyle mixed-year edition retains undated observations, no stitching to2026/27 or2025/26.
for cohort,val in [('Junior school (special school)',7),('Senior school (special school)',0)]:g(5,'2027/2028',None,cohort,{'places':val},span(5,'Number of places being made available in 2026','PART 2'),'Part1/title2027/28 versus quota heading2026/27; not resolved by upload date.')
h(5,'2027/2028',None,'All special-school classes (intake not separated)',{'places':4,'applications':63,'offers':4,'acceptances':None,'waiting_list_names_placed':4},span(5,'PART 2'),'Historical section/intake/intro2026/27 versus detailedcaption2025/26; exact period unresolved. Six criterion cells4 are not aggregate accepted24.')
for cohort,val in [('Junior Infants',30),('Autism special class',4)]:g(6,'2027/2028','2027/2028',cohort,{'places':val},span(6,'Number of places being made available in 2027'))
# Body explicitly2023/24 despite stale2022_2023 filenames; aliases share identical payload, not extra years.
for i in [8,17]:
 for cohort,val in [('Junior Infants',104),('Autism special class',0)]:g(i,'2023/2024','2023/2024',cohort,{'places':val},span(i,'Number of places being made available in 2023'),'Academic-year quota heading, not filename, anchors the year.')
g(12,'2023/2024','2023/2024','Autism special class',{'places':6},span(12,'Number of places being made available in the 2023'))
for cohort,val in [('Junior Infants to Second Class combined',80),('Autism special class',1),('Early Start preschool',30)]:g(13,'2024/2025','2024/2025',cohort,{'places':val},span(13,'Number of places being made available in 2024'),'80 explicitly covers JuniorInfants THROUGH SecondClass combined; not a JI-only quota.')
# StKevin upcoming is clear; retrospective and offer-round periods are genuinely contradictory.
for cohort,val in [('Junior Infants',26),('Autism special class',1)]:g(15,'2027/2028','2027/2028',cohort,{'places':val},span(15,'Number of places being made available in St','Part 2'))
h(15,'2027/2028',None,'Junior Infants',{'places':26,'applications':44},span(15,'History of Admissions','Number of Places available in the Special'),'History says previousyear, tablecaption2027/28, special waitingrow2025/26. Do not guess retrospective year.')
h(15,'2027/2028',None,'Autism special class',{'places':2,'applications':14,'offers':2,'acceptances':2},span(15,'Number of Places available in the Special'),'Historical period not independently resolved. Explicit offers2/accepted2 only, not actual admission.')
h(15,'2027/2028','2025/2026','Autism special class',{'waiting_list_names_placed':12},span(15,'Number of Names placed on waiting list'),'ONLY this waiting-list row explicitly names2025/26; other table metrics remain undated. No cross-year full funnel.')
rg=span(15,'Number of Offers made and accepted','Number of Places available in the Special')
g(15,'2027/2028',None,'Junior Infants',{'offers':26,'offer_rejections':2,'waiting_list_round_count':18},rg,'Printed round1 offers26 and two declined; round1 waitingcount18. No derived24accepted.','offer_round','round_1')
g(15,'2027/2028',None,'Junior Infants',{'offers':6,'acceptances':6,'waiting_list_round_count':12},rg,'Printed round2 offers6/accepted6 and list12. Source does NOT explicitly identify these as waiting-list offers; do not infer movement.','offer_round','round_2')
g(15,'2027/2028',None,'Junior Infants',{'additional_offers':6,'acceptances':6,'source_stated_cumulative_offers':30},rg,'Literal later6additionaloffers,total30,6accepted retained without reconciling contradictory arithmetic. Not labelled waiting-list movement or actual admission.','offer_round','later_class_expansion')
# Fully visually reviewed two-page scanned Clonburris notice, not filename-derived2026.
i=9;x=b(i);tf=P/'unparsed_notice_followup/evidence/clonburris_visual_transcript.txt';tf.write_text('Page1 visual transcription from retained PDF SHA256 '+x['sha256']+'\nOur Lady Queen of the Apostles N.S. ANNUAL ADMISSION NOTICE in respect of admissions to the2027/2028schoolyear.\nPART1 Admissions to the2027-2028schoolyear.\n\f\nPage2 visual transcription\nNumber of places being made available in2027/2028\nThe number of places being made available in junior infants/first year is 70\nPART2 Admissions to the2025-2026schoolyear\nSection not applicable since school intake group/special class in the previous school year was not oversubscribed.\nIntakeGroup for JuniorInfants for2027-2028schoolyear; intro2023/2024; breakdown2026-2027; all historical numeric cells blank.\n');x['text_file']=str(tf.relative_to(R));g(9,'2027/2028','2027/2028','Junior Infants',{'places':70},(2,10),'Direct visual scan review page2; filename sept2026 is not academic year. Historical multiple-year headings conflict and numeric cells are blank.')['page']=2
h(9,'2027/2028',None,'Unspecified prior-year intake',{'places':None,'applications':None,'offers':None,'acceptances':None,'waiting_list_names_placed':{'value':None,'status':'not_applicable'}},(9,12),'Explicit notoversubscribed/sectionnotapplicable statement, but historical year genuinely unresolved. Not numeric zero.')['page']=2
for i in [0,11,16]:b(i)['exclusion_reason']='Special-class policy appendix only; six is general full-class size, not a dated annual new-place quota. No annual historical table.'
for i in [1,10]:b(i)['exclusion_reason']='All8rendered scanned policy pages visually reviewed; general policy, no completed annual intake notice/table. Not inaccessible and not blank OCR assumed.'
b(14)['exclusion_reason']='Public poster for another school: StVincentCastleknockCollege SECONDARY firstyear; not Powerstown primary intake.'
b(18)['exclusion_reason']='Blank enrolment application form, not annual notice or numeric funnel; no pupil/parent entries collected.'

for source in out:
 for group in source['groups']:
  for code,definition in {'waiting_list_round_count':'Count printed for the named offer round; not inferred cumulative-ever or remaining names.','additional_offers':'Explicit additional offers in a named source round; not assumed to be made from waiting list.','source_stated_cumulative_offers':'Literal cumulative offers printed by source; arithmetic discrepancies with other rounds retained without correction.'}.items():
   if code in group['metrics']:group.setdefault('metric_definitions',{})[code]=definition
(P/'m2_reviewed_site_batch6.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print('sources',len(out),'groups',sum(len(b['groups']) for b in out))
