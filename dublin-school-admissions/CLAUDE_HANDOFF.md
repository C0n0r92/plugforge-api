# Dublin admissions — milestone2 handoff
Snapshot: 2026-11-08T13:45:32.752497+00:00 Europe/Dublin. Local SQLite, NOT hosted/shared online. No new research was performed after the wrap-up instruction.

## Actual coverage — do not substitute notice counts
- 520 school identities (516 scope +4 predecessors).
- **826 school/year pairs with at least one supported core admissions figure**, versus 671 at milestone1 (+155).
- **780 explicitly dated/cohort-matched core pairs** (+148); stricter comparable-ratio and per-metric conflict checks still apply.
- 366 retrospective core pairs (+84); 337 strict retrospective pairs.
- 198 schools have >=2 supported numeric years; 184 have >=2 strict core years.
- 51 distinct school/year pairs have a complete comparable five-count source table (59 source groups). NOT all other pairs are full funnels.
- 834 broader supported numeric pairs includes qualified, conditional or auxiliary-only observations; do not label this strict funnel coverage.
- Actual admission years **2020/21–2027/28**,8academic years, uneven school coverage. Archive captures older than2020 do NOT establish older intake statistics.
- 975 notices, 5447 observations, 6244 field-evidence rows. Notices/captures/URLs are NOT distinct school-years.

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
- 5827 pending public links, mostly NOT necessarily notices. Exact links and per-school observed-year gaps in exports/progress.json. Gaps only within observed range do not establish earlier years absent.
- Prefix index route:208 source-derived prefixes;6complete,4checkpointed transient failures,1interrupted inferred scope(11873A),197truly unattempted. Old broad-domain pending queue is a DIFFERENT method; do not call all those schools wholly unsearched.
-26 original source-ambiguity tasks retained. Conflicting years/combined cohorts/Citywest20398U2024/25ASD narrative0versustable1 are not resolved by a different-year notice.
- Original74 local editions all triaged;119 additional cached editions and all current reviewed batches imported.19 previously successful-but-unparsed documents at14schools were rechecked; all19 reviewed, including complete visual scan checks. No OCR backlog hidden for this unit.
- 368 unimported distinct-payload archive body checkpoints, of which 194 admission-bearing candidate TEXT bodies are in core. Many are changing page chrome or repeat years, NOT new notices or years. See exports/unreviewed_cached_bodies.json; metadata for nonnotice homepage bodies retained without duplicating irrelevant full homepage content.

## Archive stop and method audit — do NOT bypass
HTTP429 TooManyRequests at **13:24:34Europe/Dublin8Nov2026**, archive.org/wayback/available for AllSaints10494K. All archive.org AND web.archive.org automated requests stopped; no alternate network/browser/host route. Do not retry until a later user instruction and ordinary rate-limit-respecting access/backoff, never aggressive retries. Two overlapping archive processes were terminated(PIDs77241 and69891); all other collectors completed. No lingering collectors at snapshot.

Actual audit: database/milestone2/method_audit/audit.json. Original pilot recovered real notice bodies for3/4source-informed schools, NOT a general75%yield. Broad domain CDX requests timed out at40seconds; narrower exact queries returned200. In next outcome-independent ten-school sample,4schools actually requested,3completed before429,6unattempted after stop. Two schools yielded readable archivedHTML, but **ZERO recovered numeric notice bodies/new years** in that sample: navigation/form pages or embeddedOffice document, not original archived notice PDF. Exact-CDX header latency2.09–4.59seconds in three successful requests. Cause of broad timeouts not established. PDF body proof requires real archived body and Memento header; archivedHTML with livePDF is not archivedPDF proof.

Concrete parser gaps: ordinaryDOCX and Officeiframe encoded src were not fully followed; replay now supports actualDOCX parsing, but ordinaryDOCX outgoing discovery/Officeembedded-source extraction still needs correction. Opaque Wix file names do not match admissions-name filters; an empty such index is not evidence no notice exists. Official-site title matching rejected valid notices omittingANNUAL or insertingAUTISMCLASS and discarded scans: bounded recovery/import batch6 corrected that recovered unit. Prefer cached older PDFs and known exact historical pages/outgoing official document links to broad slow domain enumeration. Respect source robots, challenges, denies, low host rate and request caching.

## Validation and preservation
Integrity/FKs/raw-import conservation/null-zero/cross-payload gates and Dominican/GSer/Stewarts fixtures passed. Full source rebuild was compared with current numeric source groups: identical. All importers re-run with identical32table counts. New explicit StAnne/BishopGalvin fixtures passed.798original payload hashes verified locally; optional files supplied separately. CSV/JSON parity validated at packaging. Standalone core-only offline rebuild also passed: all32table counts and all source-group numeric funnels exactly match, without optional original payload archives. Existing v4, pilot and milestone1ZIPs preserved unchanged on original box; hashes recorded in release manifest. No credentials, cookies, user login material or applicant-level pupil/parent records are included; sources are public school aggregates and school metadata.

Main all-school site pass began12:31:26Europe/Dublin; this snapshot is2026-11-08T13:45:32.752497+00:00. That is elapsed collection/review work, NOT an estimated completion time. No defensible ETA for all historical years; unfinished queues are real.
