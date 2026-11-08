#!/usr/bin/env python3
"""Offline idempotent normalized source importer; never invokes old release builders."""
import os,subprocess,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent
batches=['m2_reviewed_batch1','m2_reviewed_archive59','m2_reviewed_explicit_events','m2_reviewed_archive_batch1','m2_reviewed_visual','m2_reviewed_archive_batch2','m2_reviewed_site_batch3a','m2_reviewed_site_batch3b','m2_reviewed_site_batch4','m2_reviewed_site_batch5','m2_reviewed_site_batch6']
commands=[[D/'review_local_backlog.py'],[D/'sync_archive_queue.py'],[P/'review_cached.py']]+[[P/'import_reviewed.py',b] for b in batches]
for args in commands:
 r=subprocess.run([sys.executable,*map(str,args)],capture_output=True,text=True)
 print(Path(args[0]).name, str(args[1:]),r.returncode,flush=True)
 if r.returncode:print(r.stdout,r.stderr);sys.exit(r.returncode)
print('COMPLETE',os.environ.get('DUBLIN_ADMISSIONS_DB',str(D/'admissions.sqlite3')),flush=True)
