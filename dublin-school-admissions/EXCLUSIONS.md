# Exclusions and privacy check

No snapshot file listed in `MANIFEST_SHA256.json` was edited. Hashes for those 3,027 files still match. Nothing was force-pushed, and this branch is not merged to `main`.

## Not copied

- The 13 evidence ZIP containers. The 796 PDFs were extracted to the relative paths in `EVIDENCE_RESTORE.md`. Keeping the ZIPs as well would duplicate that bulk.
- Machine paths from the delivery note (`/workspace/dublin-admissions/...` and upload directories). Those paths are not on this checkout. Use the relative paths in this directory.
- Earlier full payloads named in `MANIFEST_SHA256.json` under `immutable_prior_archives` (expanded v4, wayback pilot ZIP, milestone 1 ZIP). They were not part of this delivery. Their recorded hashes stay in the manifest only.
- `wayback-pilot/raw/05600C_2020.html` and `wayback-pilot/raw/05600C_2021.html`. The database still points at them (`retrieval.local_payload_path`), and their payload hashes are stored, but neither file was among the 796 PDF parts. Archive HTML was not universally retained. The two wayback PDFs that were supplied are present: `wayback-pilot/raw/19032R_notice.pdf` and `wayback-pilot/raw/20223I_older_notice.pdf`.
- No DOCX files were in the 13 parts. All 796 originals are PDFs.

## Privacy scan

Checked SQLite text columns, evidence text, JSON, CSV, and scripts for credentials, cookies, bearer tokens, PPS numbers, and email addresses.

- No API keys, passwords, bearer tokens, or cookie headers.
- No PPS numbers. Mentions of PPSN or date of birth in evidence text are blank policy wording (a field the school asks for, or age order on a waiting list), not a pupil record.
- Seven email addresses appear, all public school or NCSE office addresses already present in source URLs or notice text: `info@saintbrigids.ie`, `registration@saintbrigids.ie`, `admissions@ballinteeretns.ie`, `info@ballinteeretns.ie`, `burrowprincipal@gmail.com`, `burrowsecretary@gmail.com`, `d15acat@ncse.ie`. They were left in place. They are not pupil or parent mailboxes.
- One recorded school URL is a broken public link, `http://file:///C:/Users/1kerr/Downloads/doc00532220251014134651%20(1).pdf`, in `database/milestone2/checkpoints/19817H.json` and the retrieval table. It is the URL the school site published. It is not a credential and not a pupil record, so the snapshot was not redacted.
- No pupil or parent tables. `development_inspection`, `external_dataset`, `geographic_area`, and `geographic_time_observation` are empty.

No redaction was applied. PlugForge files outside `dublin-school-admissions/` were left in place.
