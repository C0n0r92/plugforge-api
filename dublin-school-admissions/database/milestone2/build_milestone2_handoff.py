#!/usr/bin/env python3
"""Build a NEW portable handoff; never touches milestone1/v4/pilot archives."""
from pathlib import Path
import sqlite3,json,csv,gzip,shutil,hashlib,zipfile,datetime,re,subprocess,sys,collections
P=Path(__file__).resolve().parent;D=P.parent;R=D.parent;S=P/'release_work'/'dublin-admissions-milestone2';S.mkdir(parents=True,exist_ok=True);SD=S/'database';SD.mkdir(exist_ok=True)
def cp(p):
 if not p.is_file():return
 target=S/p.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
# Exact current SQLite, copied through backup API after all workers and imports stopped.
src=sqlite3.connect(D/'admissions.sqlite3');dst=sqlite3.connect(SD/'admissions.sqlite3');src.backup(dst);src.close();dst.close()
for p in D.glob('*.py'):
 if p.name not in ['build_release.py','test_reproduction.py']:cp(p)
for p in D.glob('*.md'):cp(p)
cp(D/'schema.sql');cp(D/'queries.sql')
for folder in [D/'inputs',D/'migrations',D/'checkpoints',P]:
 for p in folder.rglob('*'):
  if not p.is_file() or any(x in p.parts for x in ['release_work','cache','__pycache__','evidence','errata']):continue
  if p.suffix in ['.json','.jsonl','.py','.gz','.sql'] and not p.name.endswith('.sqlite3'):cp(p)
for p in [D/'exports/validation.json',D/'exports/milestone2_idempotency.json',D/'exports/progress.json',P/'clean_rebuild_comparison.json',P/'method_audit/audit.json',P/'errata/review_spec_corrections.json']:cp(p)
c=sqlite3.connect(SD/'admissions.sqlite3');c.row_factory=sqlite3.Row
# Required evidence texts plus every cached review input text; no original home-page binaries in core.
texts={r[0] for r in c.execute('select distinct text_file from evidence where text_file is not null')}
for name in ['m2_cached_editions','v4_local_review_backlog']:
 f=D/'inputs'/(name+'.json.gz')
 if f.exists():texts.update(x['text_file'] for x in json.loads(gzip.decompress(f.read_bytes())) if x.get('text_file'))
for rel in sorted(texts):
 p=Path(rel);p=p if p.is_absolute() else R/p
 if p.exists() and p.is_relative_to(R):cp(p)
# Preserve downloaded unreviewed body text, stripping clearly unrelated homepage material where no notice title exists.
# Admission-bearing body texts are copied in full; these are public aggregate school-source extracts, not pupil records.
unreviewed=[];known={(r[0],r[1]) for r in c.execute('select roll,payload_sha256 from document where payload_sha256 is not null')}
for folder in ['exact_archive','archive_replays']:
 for f in (P/folder).glob('*.json'):
  try:b=json.loads(f.read_text())
  except:continue
  if not isinstance(b,dict) or not b.get('text_file') or not b.get('roll'):continue
  h=b.get('payload_sha256',b.get('sha256'));rel=b['text_file'];text=R/rel
  if (b['roll'],h) in known or not text.exists():continue
  t=text.read_text();isnotice=bool(re.search(r'annual.{0,40}admission|admission.{0,30}notice|f[oó]gra.{0,30}(?:iontr|bliant)|number of places.{0,20}available',t,re.I))
  if isnotice:cp(text)
  unreviewed.append({'roll':b['roll'],'payload_sha256':h,'original_url':b.get('original_url'),'capture_timestamp':b.get('capture',{}).get('timestamp'),'text_file':rel,'body_text_in_core':isnotice,'body_kind':'admissions_candidate_not_reviewed' if isnotice else 'homepage_navigation_no_notice_title_detected_metadata_retained','checkpoint_file':str(f.relative_to(R))})
(SD/'exports').mkdir(exist_ok=True);(SD/'exports/unreviewed_cached_bodies.json').write_text(json.dumps(unreviewed,indent=2))
def export(name,query):
 rows=[dict(r) for r in c.execute(query)];path=SD/'exports'/name
 path.with_suffix('.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 if rows:
  with path.with_suffix('.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 return len(rows)
exports={}
for name,q in [('schools','select * from school order by roll'),('admissions_funnels_by_source','select * from v_group_funnel order by roll,academic_year,cohort,phase,group_id'),('comparison_ratios','select * from v_comparison_ratios order by roll,academic_year,cohort,phase,group_id'),('observations','select o.*,p.roll,p.academic_year,p.cohort_id,g.phase,g.table_scope,g.year_status,g.as_of group_as_of from observation o join observation_group g using(group_id) join school_period p using(period_id) order by p.roll,p.academic_year,o.observation_id'),('evidence','select * from evidence order by evidence_id'),('work_queue','select * from work_queue order by stage,roll,task_id'),('import_reconciliation','select * from import_reconciliation order by release_id,dataset')]:exports[name]=export(name,q)
progress=json.loads((P/'progress.json').read_text());cur=progress['current'];baseline=progress['milestone1_exact_baseline'];at=datetime.datetime.now().astimezone().isoformat();prefixq=json.loads((P/'prefix_archive/source_queue.json').read_text());prefixi=[json.loads(f.read_text()) for f in (P/'prefix_archive').glob('index_*.json')]
queue={'as_of':at,'timezone':'Europe/Dublin','own_sites':progress['own_site_school_statuses'],'pending_public_links_not_assumed_notices':progress['pending_public_links_not_assumed_notices'],'source_derived_prefixes_queued':len(prefixq),'prefixes_checkpointed':len(prefixi),'prefixes_index_complete':sum(x['status']=='index_complete' for x in prefixi),'prefixes_failed_checkpointed':sum(x['status']!='index_complete' for x in prefixi),'additional_prefix_attempt_interrupted_without_own_checkpoint':{'roll':'11873A','prefix':'https://rathmichaelschool.com/wp-content/uploads/','basis':'Serial worker queue after10saved prefixes and third consecutive timeout; scope reconstructed from saved source_queue and loop order.'},'prefixes_truly_unattempted':len(prefixq)-len(prefixi)-1,'retained_source_ambiguity_tasks':26,'unreviewed_distinct_payload_body_checkpoints':len(unreviewed),'unreviewed_admissions_candidate_texts_in_core':sum(x['body_text_in_core'] for x in unreviewed),'archive429':'All archive requests stopped after13:24:34Europe/Dublin; no retry until later user instruction, normal documented access and service limits respected.','collectors_running':False,'stopped_archive_pids':[77241,69891],'other_collection_workers':'All own-site/media/link/seed/unparsed workers completed; no live collectors at snapshot.'}
(SD/'exports/remaining_queues.json').write_text(json.dumps(queue,indent=2))
# Relative-path requirements and folder map, no hosted service or account credentials.
(S/'requirements.txt').write_text('requests\nbeautifulsoup4\n')
(S/'CLAUDE_HANDOFF.md').write_text(f'''# Dublin admissions — milestone2 handoff
Snapshot: {at} Europe/Dublin. Local SQLite, NOT hosted/shared online. No new research was performed after the wrap-up instruction.

## Actual coverage — do not substitute notice counts
- {cur['counts']['school']} school identities (516 scope +4 predecessors).
- **{cur['core_admissions_school_year_pairs']} school/year pairs with at least one supported core admissions figure**, versus {baseline['core_admissions_school_year_pairs']} at milestone1 (+{cur['core_admissions_school_year_pairs']-baseline['core_admissions_school_year_pairs']}).
- **{cur['explicitly_dated_cohort_matched_core_pairs']} explicitly dated/cohort-matched core pairs** (+{cur['explicitly_dated_cohort_matched_core_pairs']-baseline['explicitly_dated_cohort_matched_core_pairs']}); stricter comparable-ratio and per-metric conflict checks still apply.
- {cur['retrospective_core_school_year_pairs']} retrospective core pairs (+{cur['retrospective_core_school_year_pairs']-baseline['retrospective_core_school_year_pairs']}); {cur['strict_retrospective_core_pairs']} strict retrospective pairs.
- {cur['schools_with_at_least_two_supported_numeric_years']} schools have >=2 supported numeric years; {cur['schools_with_at_least_two_strict_core_years']} have >=2 strict core years.
- {cur['distinct_full_five_metric_school_year_pairs']} distinct school/year pairs have a complete comparable five-count source table ({cur['full_five_metric_source_groups']} source groups). NOT all other pairs are full funnels.
- {cur['supported_numeric_school_year_pairs_including_qualified_or_noncore']} broader supported numeric pairs includes qualified, conditional or auxiliary-only observations; do not label this strict funnel coverage.
- Actual admission years **2020/21–2027/28**,8academic years, uneven school coverage. Archive captures older than2020 do NOT establish older intake statistics.
- {cur['counts']['notice']} notices, {cur['counts']['observation']} observations, {cur['counts']['evidence']} field-evidence rows. Notices/captures/URLs are NOT distinct school-years.

## Goal and scope
Recover as much publicly available historical admissions data as possible for ALL Dublin schools and ALL recoverable years. No earliest-year cutoff. Priority actual school/year/cohort figures and provenance, not dashboards, demographics, housing/property enrichment or repeated documentation. No school contacts, forms submissions or outgoing messages. Do not treat unfinished research as unavailable data. The user paused collection for this handoff because of usage, not because the project is complete.

## Files and start
```
CLAUDE_HANDOFF.md  RESUME_PROMPT.txt  README.md  requirements.txt
database/admissions.sqlite3        actual populated latest database
database/schema.sql, migrations/   DDL and migration history
database/DATA_DICTIONARY.md, POSTGRESQL.md, queries.sql
database/inputs/*.json.gz          frozen raw inputs and reviewed specifications
database/exports/                  matched CSV/JSON, evidence, progress, remaining queues
(database/milestone2/)             import/rebuild scripts, public discovery scripts, checkpoints, method_audit/
(evidence/... and cached text paths) referenced school-source evidence texts
```
Unzip into one directory and run commands from THAT root, preserving paths. Python3.11+ and SQLite with window functions; pip install -r requirements.txt. Poppler tools(pdftotext,pdfinfo,pdftoppm) for new PDFs. Local tesseract optional; not installed in collection box and package repository returnedHTTP500, so scans were directly visually reviewed. No API key/service signup required to read SQLite.

```
python3 database/milestone2/validate_handoff.py
python3 -c "import sqlite3; c=sqlite3.connect('database/admissions.sqlite3'); print(c.execute('select count(*) from observation').fetchone())"
# Offline normalized reimport: deterministic IDs; DO NOT use legacy milestone1 builders.
python3 database/milestone2/rebuild_verified.py
python3 database/milestone2/sync_research_snapshot.py
python3 database/milestone2/refresh_progress.py
```
To rebuild into a NEW file without overwriting the snapshot:
```
DUBLIN_ADMISSIONS_DB="$PWD/rebuilt.sqlite3" python3 database/milestone2/rebuild_verified.py
DUBLIN_ADMISSIONS_DB="$PWD/rebuilt.sqlite3" python3 database/milestone2/sync_research_snapshot.py
```
`refresh_progress.py` operates on database/admissions.sqlite3; omit it for an alternate-path test. It uses bundled exact baseline statistics when the immutable milestone1ZIP is absent. `validate_database.py` is the full-box validator and expects original v4/pilotZIPs; use portable validate_handoff.py here. Original full payloads are optional separate evidence archives; core has referenced evidence TEXT. Extraction of evidence parts into the same root restores original PDF paths. Missing payload paths without those parts do not imply missing numeric evidence.

## Schema and definitions
school roll is TEXT PK; identity/predecessor links and sourced locations/metadata separate. school_period = school+academic-year+cohort. Documents dedup by school+payloadSHA256; originals/source aliases, retrievals and archive captures separate. Notice editions -> observation_group (one exact source, year, cohort, phase, scope/asof) -> observations -> field evidence and raw lineage. Upcoming capacity and retrospective places are separate. Never stitch different payloads/years/cohorts/revisions into a false complete funnel. Explicit-year conflicts remain flagged or yearNULL. Capture time, publication date and academic year are different.

JuniorInfants != senior intake, special-school intake, ASD class, combined grades or preschool. Accepted offers != actual enrolment/admission. Interest/registrations != applications. Names ever placed != list remaining/snapshot or opt-in lists. Offer rounds are NOT automatically waiting-list movement. Only explicitly labelled waiting-list offers/acceptances are such events; never sum criterion acceptances to manufacture totals. Numeric0 only explicit; not published/not found/not applicable/ambiguous/blocked/unattempted remain distinct. Unknown metadataNULL; geographic points are not catchments. Views preserve all source groups; preferred ranking is deterministic, not a claim the chosen edition is chronologically latest.

Ratios in v_comparison_ratios use same group/cohort/year, conflict/explicitness gates and denominator>0. Use phase='retrospective' and suitable table_scope; never rank demand from incompatible definitions. v_year_over_year comparisons need adjacent years and same cohort/definition. Future geographic/housing/property structures remain EMPTY; do not populate invented values.

## Source fixtures and genuine new waiting evidence
- Dominican05600C2021/22 JI36.
- GSer20223I2024/25 places60/apps70/list0; offers/acceptedNULL. Not2023/24. User screenshot remains separate excluded-reference evidence, not original-school payload proof.
- Stewarts19032R2021/22 places16/apps109/offers21/list56; accepted totalNULL. Explicit historic-waitlist offers13/accepted8; not actual admissions.
- StAnneShankill19888H2023/24 supplementary waitinglist: asof2023-06-22 **8offers,3accepted**; asof2023-08-29 **9offers,4accepted**. These are directly labelled source snapshots, NOT differences between editions, and not admissions. URLs/evidence are in DB and batch4 specs.
- BishopGalvin19494J2025/26 autism:1place,2applications,1offer,1accepted,1waitingname. Other senior ThirdClass cohorts stay separate.

## Actual attempted/pending work
- Own-site stages:434 accessible attempted,84 permission/retrieval failures,2 no-domain identities; no wholly unattempted school left in this bounded own-site pass. This is NOT exhaustive school history.
- {queue['pending_public_links_not_assumed_notices']} pending public links, mostly NOT necessarily notices. Exact links and per-school observed-year gaps in exports/progress.json. Gaps only within observed range do not establish earlier years absent.
- Prefix index route:208 source-derived prefixes;6complete,4checkpointed transient failures,1interrupted inferred scope(11873A),197truly unattempted. Old broad-domain pending queue is a DIFFERENT method; do not call all those schools wholly unsearched.
-26 original source-ambiguity tasks retained. Conflicting years/combined cohorts/Citywest20398U2024/25ASD narrative0versustable1 are not resolved by a different-year notice.
- Original74 local editions all triaged;119 additional cached editions and all current reviewed batches imported.19 previously successful-but-unparsed documents at14schools were rechecked; all19 reviewed, including complete visual scan checks. No OCR backlog hidden for this unit.
- {len(unreviewed)} unimported distinct-payload archive body checkpoints, of which {sum(x['body_text_in_core'] for x in unreviewed)} admission-bearing candidate TEXT bodies are in core. Many are changing page chrome or repeat years, NOT new notices or years. See exports/unreviewed_cached_bodies.json; metadata for nonnotice homepage bodies retained without duplicating irrelevant full homepage content.

## Archive stop and method audit — do NOT bypass
HTTP429 TooManyRequests at **13:24:34Europe/Dublin8Nov2026**, archive.org/wayback/available for AllSaints10494K. All archive.org AND web.archive.org automated requests stopped; no alternate network/browser/host route. Do not retry until a later user instruction and ordinary rate-limit-respecting access/backoff, never aggressive retries. Two overlapping archive processes were terminated(PIDs77241 and69891); all other collectors completed. No lingering collectors at snapshot.

Actual audit: database/milestone2/method_audit/audit.json. Original pilot recovered real notice bodies for3/4source-informed schools, NOT a general75%yield. Broad domain CDX requests timed out at40seconds; narrower exact queries returned200. In next outcome-independent ten-school sample,4schools actually requested,3completed before429,6unattempted after stop. Two schools yielded readable archivedHTML, but **ZERO recovered numeric notice bodies/new years** in that sample: navigation/form pages or embeddedOffice document, not original archived notice PDF. Exact-CDX header latency2.09–4.59seconds in three successful requests. Cause of broad timeouts not established. PDF body proof requires real archived body and Memento header; archivedHTML with livePDF is not archivedPDF proof.

Concrete parser gaps: ordinaryDOCX and Officeiframe encoded src were not fully followed; replay now supports actualDOCX parsing, but ordinaryDOCX outgoing discovery/Officeembedded-source extraction still needs correction. Opaque Wix file names do not match admissions-name filters; an empty such index is not evidence no notice exists. Official-site title matching rejected valid notices omittingANNUAL or insertingAUTISMCLASS and discarded scans: bounded recovery/import batch6 corrected that recovered unit. Prefer cached older PDFs and known exact historical pages/outgoing official document links to broad slow domain enumeration. Respect source robots, challenges, denies, low host rate and request caching.

## Validation and preservation
Integrity/FKs/raw-import conservation/null-zero/cross-payload gates and Dominican/GSer/Stewarts fixtures passed. Full source rebuild was compared with current numeric source groups: identical. All importers re-run with identical32table counts. New explicit StAnne/BishopGalvin fixtures passed.798original payload hashes verified locally; optional files supplied separately. CSV/JSON parity validated at packaging. Existing v4, pilot and milestone1ZIPs preserved unchanged on original box; hashes recorded in release manifest. No credentials, cookies, user login material or applicant-level pupil/parent records are included; sources are public school aggregates and school metadata.

Main all-school site pass began12:31:26Europe/Dublin; this snapshot is{at}. That is elapsed collection/review work, NOT an estimated completion time. No defensible ETA for all historical years; unfinished queues are real.
''')
(S/'RESUME_PROMPT.txt').write_text('Continue this Dublin primary-school admissions research from the enclosed ACTUAL milestone2 SQLite database, not from scratch. First read CLAUDE_HANDOFF.md and validate database/milestone2/validate_handoff.py. Goal: all recoverable historical years for all Dublin schools, maximum actual verified numeric school/year/cohort evidence, not dashboards or more infrastructure. Current coverage and remaining queues are in database/exports/progress.json and remaining_queues.json; notices/captures are not school-years. Prioritise cached unreviewed admission-bearing bodies/older PDFs, exact historical official-page/document links and missing school-year gaps. Preserve all source editions/conflicts; no cross-payload/year/cohort funnels, no invented accepted totals or waiting-list movement. Acceptances are not actual admissions. Internet Archive hitHTTP429 and all archive requests are stopped: do not retry without later user instruction and service-respecting backoff; no bypass, alternate network, aggressive retry, or robots evasion. No contacts/outbound messages, pupil/parent records, invented demographics/property data or arbitrary school-count pilot cap. Official sources may be researched only when the user authorises resumption after this handoff; do not begin a new crawl merely to inspect the bundle. Use relative paths and existing idempotent importers; never invoke legacy milestone1 release builders. Keep progress strict, attempted versus unattempted and residual blockers explicit. The user prioritises data and reduced usage; do not spend runtime rewriting docs before real evidence gains.\n')
(S/'README.md').write_text('# Dublin admissions milestone2\n\nStart with CLAUDE_HANDOFF.md, then RESUME_PROMPT.txt. Actual local SQLite: database/admissions.sqlite3. All paths relative to this extracted directory. Core contains current database, frozen inputs, reviewed field-source text, scripts and saved queues; optional evidence ZIPs restore original PDF/DOCX paths. No service signup, hosted database or dashboard.\n')
(SD/'exports/export_statistics.json').write_text(json.dumps({'at':at,'timezone':'Europe/Dublin','row_counts':exports,'csv_json_same_rows_and_columns':True},indent=2))
c.close()
# Portable validator must work from the actual extracted root, without original box ZIPs.
z=subprocess.run([sys.executable,str(SD/'milestone2/validate_handoff.py')],cwd=S,capture_output=True,text=True);print(z.stdout,z.stderr);assert z.returncode==0
# Actual CSV/JSON parity after filesystem serialization, not just one in-memory list.
for name,n in exports.items():
 a=json.loads((SD/'exports'/(name+'.json')).read_text());b=list(csv.DictReader((SD/'exports'/(name+'.csv')).open()));assert len(a)==len(b)==n
 if a:assert list(a[0])==list(b[0])
 for x,y in zip(a,b):assert all(('' if v is None else str(v))==y[k] for k,v in x.items()),name
manifest={'created_at':at,'timezone':'Europe/Dublin','coverage':cur,'remaining_queues':queue,'files':{},'immutable_prior_archives':{}}
for rel in ['dublin-admissions-expanded-v4-2026-11-08.zip','wayback-pilot/wayback-feasibility-pilot-2026-11-08.zip','database/dublin-admissions-database-milestone1-2026-11-08.zip']:
 f=R/rel;manifest['immutable_prior_archives'][rel]=hashlib.sha256(f.read_bytes()).hexdigest()
for f in sorted(S.rglob('*')):
 if f.is_file():manifest['files'][str(f.relative_to(S))]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(S/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2))
out=D/'dublin-admissions-database-milestone2-claude-handoff-2026-11-08.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as zz:
 for f in sorted(S.rglob('*')):
  if f.is_file():zz.write(f,Path(S.name)/f.relative_to(S))
assert out.stat().st_size<25000000,('Core handoff too large',out.stat().st_size)
(out.with_suffix('.sha256')).write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n');print('CORE',str(out),out.stat().st_size,flush=True)
# Independently extractable optional original payload packs, <=24MB each; no HTML homepage binaries.
payloads=[];cc=sqlite3.connect(D/'admissions.sqlite3')
for rel,h,fmt in cc.execute("select distinct r.local_payload_path,r.payload_sha256,d.media_type from retrieval r join document d using(document_id) where r.local_payload_path is not null and r.payload_sha256 is not null"):
 f=R/rel
 if f.is_file() and f.suffix.lower() in ['.pdf','.docx'] and hashlib.sha256(f.read_bytes()).hexdigest()==h:payloads.append(f)
cc.close();payloads=sorted(set(payloads));chunks=[];chunk=[];size=0
for f in payloads:
 if chunk and size+f.stat().st_size>22500000:chunks.append(chunk);chunk=[];size=0
 chunk.append(f);size+=f.stat().st_size
if chunk:chunks.append(chunk)
parts=[]
for i,files in enumerate(chunks,1):
 dest=D/f'dublin-admissions-milestone2-evidence-{i:02d}-of-{len(chunks):02d}.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as zz:
  for f in files:zz.write(f,Path(S.name)/f.relative_to(R))
 assert dest.stat().st_size<=24000000
 parts.append({'path':str(dest),'bytes':dest.stat().st_size,'files':len(files),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()});print('EVIDENCE',dest.name,dest.stat().st_size,flush=True)
(D/'milestone2_handoff_delivery.json').write_text(json.dumps({'core_zip':str(out),'core_bytes':out.stat().st_size,'core_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'working_sqlite':str(D/'admissions.sqlite3'),'portable_root':str(S),'optional_evidence_parts':parts,'original_payload_files_packaged':len(payloads)},indent=2))
print('FINISHED',flush=True)
