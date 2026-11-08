#!/usr/bin/env python3
"""Integrity, lineage, conservation, fixture and safe-comparison checks; offline only."""
import sqlite3,json,hashlib,subprocess,sys,re,gzip,datetime
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parent
C=sqlite3.connect(D/'admissions.sqlite3');C.row_factory=sqlite3.Row
q=lambda s,p=():C.execute(s,p).fetchall()
assert q('PRAGMA integrity_check')[0][0]=='ok'
assert not q('PRAGMA foreign_key_check')
assert not q("select roll from school where typeof(roll)<>'text'")
assert q("select count(*) from raw_record where dataset='v4_primary'")[0][0]==516
assert q("select count(*) from raw_record where dataset='v4_historical_tables'")[0][0]==398
assert q("select count(*) from raw_record where dataset='v4_reviewed_editions'")[0][0]==835
assert q("select count(*) from raw_record where dataset='v4_review_archive'")[0][0]==561
assert q("select count(*) from raw_record where dataset='v4_waiting_events'")[0][0]==21
assert q("select count(*) from raw_record where dataset='wayback_pilot'")[0][0]==8
assert q("select count(*) from raw_record where dataset='v4_screenshot_reference' and normalization_status='excluded'")[0][0]==1
assert not q('select * from import_reconciliation where expected_rows<>raw_rows or normalized_rows+excluded_rows<>raw_rows')
assert not q('select roll,payload_sha256,count(*) from document where payload_sha256 is not null group by roll,payload_sha256 having count(*)>1')
assert not q("select * from observation where (value_integer is not null and value_status<>'observed') or (value_status='observed' and value_integer is null) or value_integer<0")
assert not q('select e.evidence_id from evidence e join document d on d.document_id=e.document_id where e.source_payload_sha256 is not null and d.payload_sha256 is not null and e.source_payload_sha256<>d.payload_sha256'), 'Cross-payload evidence association'
assert not q('select o.observation_id from observation o join observation_group g on g.group_id=o.group_id join notice n on n.notice_id=g.notice_id join observation_evidence oe on oe.observation_id=o.observation_id join evidence e on e.evidence_id=oe.evidence_id where e.document_id<>n.document_id')
assert not q('select * from v_comparison_ratios where applications_per_place is not null and (places<=0 or comparable<>1)')
assert not q('select * from v_comparison_ratios where acceptances_per_offer is not null and (offers<=0 or comparable<>1)')
assert q("select count(*) from v_group_funnel where roll='05600C' and academic_year='2021/2022' and cohort='Junior Infants' and places=36")[0][0]>0
assert q("select count(*) from v_group_funnel where roll='20223I' and academic_year='2024/2025' and places=60 and applications=70 and offers is null and acceptances is null and waiting_list_names_placed=0")[0][0]>0
assert q("select count(*) from v_group_funnel where roll='19032R' and academic_year='2021/2022' and places=16 and applications=109 and offers=21 and acceptances is null and waiting_list_names_placed=56")[0][0]>0
assert q("select count(*) from observation o join observation_group g on g.group_id=o.group_id join school_period p on p.period_id=g.period_id where p.roll='19032R' and p.academic_year='2021/2022' and o.metric_code='waiting_list_offers' and o.value_integer=13")[0][0]>0
assert q("select count(*) from observation o join observation_group g on g.group_id=o.group_id join school_period p on p.period_id=g.period_id where p.roll='19032R' and p.academic_year='2021/2022' and o.metric_code='waiting_list_acceptances' and o.value_integer=8")[0][0]>0
assert q("select count(*) from school_relation")[0][0]==4
for t in ['geographic_area','external_dataset','geographic_time_observation','development_inspection']:assert q('select count(*) from '+t)[0][0]==0
# Input parity: each frozen input record accounted for, exclusions explicit.
for r in q('select * from import_reconciliation'):
 packed=D/'inputs'/(r['dataset']+'.json.gz')
 if packed.exists():assert len(json.loads(gzip.decompress(packed.read_bytes())))==r['expected_rows'],r['dataset']
# Payload verification is separate from minimized/extracted-text hash verification.
cache_checked=0;missing_payload=0;bad=[]
for r in q("select distinct local_payload_path,payload_sha256 from retrieval where local_payload_path is not null and payload_sha256 is not null"):
 p=ROOT/r['local_payload_path']
 if p.exists():
  cache_checked+=1
  if hashlib.sha256(p.read_bytes()).hexdigest()!=r['payload_sha256']:bad.append(r['local_payload_path'])
 else:missing_payload+=1
assert not bad,('Payload hash mismatch',bad)
for p,h in [('dublin-admissions-expanded-v4-2026-11-08.zip','627b3b0d6a3332f65f44fd113e838d5a73b76d535932ae0fd41385ec044391de'),('wayback-pilot/wayback-feasibility-pilot-2026-11-08.zip','cfd384c6a3dda9ce329e04e0979941c9e5d2023bea06a46573eff648950ee50a')]:assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
report={'validated_at':datetime.datetime.now().astimezone().isoformat(),'timezone':'Europe/Dublin','integrity_check':'ok','foreign_key_violations':0,'cross_payload_evidence_mismatches':0,'duplicate_school_payload_editions':0,'raw_import_conservation':'passed all releases/datasets','fixture_tests':['Dominican2021/22 capacity36','GSer2024/25 60places70applications0list; no invented offers','Stewarts2021/22 16places109applications21offers56list; aggregateacceptancesnull','Stewarts historic-waitlist explicit13offers8acceptances','four sourced amalgamation links'],'known_payload_hashes_checked':cache_checked,'local_payloads_not_present':missing_payload,'production_v4_and_pilot_unchanged':True,'future_geographic_enrichment_tables_empty':True,'zero_vs_null_constraints':'passed','denominator_and_comparable_gates':'passed','passed':True}
(D/'exports/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
