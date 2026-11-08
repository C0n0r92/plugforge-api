# Original evidence restore

The 796 original source files are already extracted in this directory. They are public school admission PDFs. The 13 transport ZIP parts are not stored again, so the PDFs are not duplicated as both loose files and archives.

Read `CLAUDE_HANDOFF.md`, then `RESUME_PROMPT.txt`. Paths below are relative to this directory (`dublin-school-admissions/`).

## What was verified

Each supplied part matched `original-evidence/PART_SHA256SUMS.txt` before extraction. Every extracted file begins with the PDF header `%PDF-`. 796 of 798 recorded `retrieval.payload_sha256` values match the file at `retrieval.local_payload_path`. The other two paths are HTML and were not in these parts. See `EXCLUSIONS.md`.

| Part | Files | Extracted under |
| --- | ---: | --- |
| `dublin-admissions-milestone2-evidence-01-of-13.zip` | 88 | `cache/` |
| `dublin-admissions-milestone2-evidence-02-of-13.zip` | 80 | `cache/` |
| `dublin-admissions-milestone2-evidence-03-of-13.zip` | 69 | `cache/` |
| `dublin-admissions-milestone2-evidence-04-of-13.zip` | 79 | `cache/` |
| `dublin-admissions-milestone2-evidence-05-of-13.zip` | 75 | `cache/` |
| `dublin-admissions-milestone2-evidence-06-of-13.zip` | 56 | `cache/` |
| `dublin-admissions-milestone2-evidence-07-of-13.zip` | 73 | `cache/` |
| `dublin-admissions-milestone2-evidence-08-of-13.zip` | 78 | `cache/` |
| `dublin-admissions-milestone2-evidence-09-of-13.zip` | 67 | `cache/` (51) and `database/milestone2/cache/` (16) |
| `dublin-admissions-milestone2-evidence-10-of-13.zip` | 50 | `database/milestone2/cache/` |
| `dublin-admissions-milestone2-evidence-11-of-13.zip` | 34 | `database/milestone2/cache/` |
| `dublin-admissions-milestone2-evidence-12-of-13.zip` | 40 | `database/milestone2/cache/` (27) and `database/milestone2/unparsed_notice_followup/cache/` (13) |
| `dublin-admissions-milestone2-evidence-13-of-13.zip` | 7 | `database/milestone2/unparsed_notice_followup/cache/` (5) and `wayback-pilot/raw/` (2) |

File-to-part membership is `original-evidence/part-membership.tsv` (part filename, tab, relative path).

## ZIP layout

Each part member is stored as `dublin-admissions-milestone2/<relative-path>`. Extraction strips that prefix so `<relative-path>` lands in this directory. That is the layout the SQLite `local_payload_path` values and the handoff scripts already use.

To extract the parts again from a folder that contains the 13 ZIPs:

```bash
python3 - << 'PY'
import shutil, zipfile
from pathlib import Path
root = Path("dublin-school-admissions")  # this directory
prefix = "dublin-admissions-milestone2/"
for part in sorted(Path("path-to-zips").glob("dublin-admissions-milestone2-evidence-*-of-13.zip")):
    with zipfile.ZipFile(part) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.endswith("/") or name.startswith("/") or ".." in Path(name).parts:
                raise SystemExit(name)
            if not name.startswith(prefix):
                raise SystemExit(name)
            target = root / name[len(prefix):]
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
PY
```

To rebuild one part from this tree, read its rows in `original-evidence/part-membership.tsv` and write those files back under the `dublin-admissions-milestone2/` prefix. Compare the result with `original-evidence/PART_SHA256SUMS.txt`.

Core snapshot hashes for the non-PDF files are in `MANIFEST_SHA256.json`. Those hashes were checked after extraction and matched, including `database/admissions.sqlite3`.
