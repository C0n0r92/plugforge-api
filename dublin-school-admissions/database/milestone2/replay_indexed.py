#!/usr/bin/env python3
"""Replay existing indexed captures, no CDX bulk query. Stops on archive denial or consecutive timeouts."""
import sqlite3,json,time,requests,datetime,hashlib,subprocess
from pathlib import Path
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent;D=P.parent
UA='DublinAdmissionsHistoricalReplay/1.0 (small public admission aggregate research; read-only; low rate)'
R=P/'archive_replays';R.mkdir(exist_ok=True)
c=sqlite3.connect(D/'admissions.sqlite3');todo=[(a,b,json.loads(z)) for a,b,z in c.execute("select task_id,roll,checkpoint_json from work_queue where stage='archive_capture_body_review'")];c.close()
todo.sort(key=lambda x:(0 if x[2]['mimetype']=='application/pdf' else 2 if x[2]['mimetype'].startswith('image/') else 1,x[2]['timestamp']))
consecutive=0;last=0
for task,roll,cap in todo:
 out=R/(task+'.json')
 if out.exists():continue
 rec={'task_id':task,'roll':roll,'capture':cap,'original_url':cap['original'],'archived_url':'https://web.archive.org/web/'+cap['timestamp']+'/'+cap['original'],'attempted_at':datetime.datetime.now().astimezone().isoformat()}
 if cap['mimetype'].startswith('image/'):
  rec['status']='image_variant_pending_visual_review_not_numeric_notice_proof';out.write_text(json.dumps(rec,indent=2)+'\n');continue
 time.sleep(max(0,3.5-(time.monotonic()-last)))
 try:
  r=requests.get(rec['archived_url'],headers={'User-Agent':UA},timeout=(10,20),allow_redirects=False);last=time.monotonic();rec.update(http_status=r.status_code,headers={k:v for k,v in r.headers.items() if k.lower() in ['memento-datetime','content-type','location','x-mitmproxy-blocked-reason']},payload_sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content))
  if r.status_code in [401,403,429] or 'x-mitmproxy-blocked-reason' in {k.lower() for k in r.headers}:
   rec.update(status='archive_access_blocked_stop',error=r.text[:400]);out.write_text(json.dumps(rec,indent=2)+'\n');(R/'STOP_ACCESS.json').write_text(json.dumps(rec,indent=2));print('STOP access',flush=True);break
  if r.status_code==200 and rec['headers'].get('memento-datetime'):
   h=rec['payload_sha256']
   if r.content.startswith(b'%PDF'):
    raw=P/'cache'/(h+'.pdf');raw.write_bytes(r.content);t=subprocess.run(['pdftotext','-layout',str(raw),'-'],capture_output=True,timeout=20).stdout.decode('utf8','replace');rec['source_file']=str(raw.relative_to(D.parent));rec['format']='pdf'
   else:
    soup=BeautifulSoup(r.content,'html.parser');node=soup.select_one('article') or soup.select_one('main') or soup
    for e in node.select('script,style,nav,footer,header'):e.decompose()
    t=node.get_text('\n',strip=True);rec['format']='html';rec['archive_link_candidates']=[{'url':a.get('href'),'label':a.get_text(' ',strip=True)} for a in soup.select('a[href]') if any(w in (a.get('href','')+' '+a.get_text(' ',strip=True)).lower() for w in ['admission','iontr','fogra','notice'])]
   fp=P/'evidence'/f'archive_{roll}_{h[:20]}.txt';fp.write_text(t);rec.update(status='archived_body_retrieved_requires_notice_evidence_review',text_file=str(fp.relative_to(D.parent)));consecutive=0
  else:rec['status']='archive_replay_http_'+str(r.status_code);consecutive=consecutive+1 if r.status_code>=500 else 0
 except requests.exceptions.ProxyError as e:
  rec.update(status='archive_network_proxy_block_stop',error=str(e));(R/'STOP_ACCESS.json').write_text(json.dumps(rec,indent=2));out.write_text(json.dumps(rec,indent=2)+'\n');break
 except requests.RequestException as e:
  last=time.monotonic();rec.update(status='archive_transient_'+type(e).__name__,error=str(e));consecutive+=1
 out.write_text(json.dumps(rec,indent=2)+'\n');print(roll,cap['timestamp'],rec['status'],flush=True)
 if consecutive>=3:(R/'STOP_TRANSIENT.json').write_text(json.dumps(rec,indent=2));print('STOP consecutive transient failures',flush=True);break
