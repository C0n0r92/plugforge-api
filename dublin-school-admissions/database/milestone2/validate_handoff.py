#!/usr/bin/env python3
"""Portable offline validation; original optional PDF archives need not be installed."""
import sqlite3,json,gzip,hashlib,datetime
from pathlib import Path
D=Path(__file__).resolve().parents[1];R=D.parent;c=sqlite3.connect(D/'admissions.sqlite3');c.row_factory=sqlite3.Row
assert c.execute('pragma integrity_check').fetchone()[0]=='ok';assert not c.execute('pragma foreign_key_check').fetchall()
assert not c.execute('select roll,payload_sha256 from document where payload_sha256 is not null group by roll,payload_sha256 having count(*)>1').fetchall()
assert not c.execute('select * from import_reconciliation where expected_rows<>raw_rows or normalized_rows+excluded_rows<>raw_rows').fetchall()
assert not c.execute("select * from observation where value_integer<0 or (value_integer is null and value_status='observed') or (value_integer is not null and value_status<>'observed')").fetchall()
assert c.execute("select count(*) from v_group_funnel where roll='05600C' and academic_year='2021/2022' and places=36").fetchone()[0]
assert c.execute("select count(*) from v_group_funnel where roll='20223I' and academic_year='2024/2025' and places=60 and applications=70 and offers is null and acceptances is null and waiting_list_names_placed=0").fetchone()[0]
assert c.execute("select count(*) from v_group_funnel where roll='19032R' and academic_year='2021/2022' and places=16 and applications=109 and offers=21 and acceptances is null and waiting_list_names_placed=56").fetchone()[0]
for ds,n in [('v4_primary',516),('v4_historical_tables',398),('v4_reviewed_editions',835),('v4_review_archive',561),('v4_waiting_events',21),('wayback_pilot',8)]:assert c.execute('select count(*) from raw_record where dataset=?',(ds,)).fetchone()[0]==n
missing=[];bad=[]
for r in c.execute('select distinct text_file,text_file_sha256 from evidence where text_file is not null'):
 p=R/r['text_file']
 if not p.exists():missing.append(r['text_file'])
 elif r['text_file_sha256'] and hashlib.sha256(p.read_bytes()).hexdigest()!=r['text_file_sha256']:bad.append(r['text_file'])
assert not missing,missing[:5];assert not bad,bad[:5]
report={'passed':True,'validated_at':datetime.datetime.now().astimezone().isoformat(),'timezone':'Europe/Dublin','integrity_check':'ok','foreign_key_violations':0,'duplicate_school_payloads':0,'raw_conservation':'passed','core_fixtures':'Dominican,GSer,Stewarts passed','evidence_text_files_missing':len(missing),'evidence_text_hash_mismatches':len(bad),'optional_original_payloads':'Install optional evidence archives to resolve original payload paths; archiveHTML not universally retained.'};(D/'exports/handoff_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
