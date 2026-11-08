#!/usr/bin/env python3
"""Recover source-identified, previously successful notice downloads with OCR as needed.
No archive requests, guessed paths, forms or pupil records. All eligible queue items attempted.
"""
import json,re,subprocess,concurrent.futures as cf,time,zipfile,io,shutil
from pathlib import Path
from xml.etree import ElementTree as ET
import permitted_official as F
X=F.X;P=X.P;O=P/'unparsed_notice_followup'
for folder in ['checkpoints','cache','evidence']: (O/folder).mkdir(parents=True,exist_ok=True)
raw=json.loads((P/'unparsed_notice_candidate_queue.json').read_text());todo=[]
for a in raw:
 u=a['url']
 if re.search(r'(?:^|[-_/])(?:form|forms|privacy|priobha|príobhá)|Application.*Form|for-Admissions-Form|enrolment.*form|enrollment.*form|pre.?enrolment|data.protection|safeguard|cumhdach|frith|hathbhreith|athbhreith|information|infographic|catchment|poster|enrolment.*steps|challenges|FAQ|booklet',u,re.I):continue
 if re.search(r'notice|notificat|Annual|Signed-and-Approved-Admissions|Admission-p\.pdf|Appendix.*Admission.to.Special|Autism-Class-Enrolment',u,re.I):todo.append(a)
X.save(O/'source_queue.json',todo);print('QUEUED',len(todo),'documents',len({r['roll'] for r in todo}),'schools',flush=True)
def one(a):
 fp=O/'checkpoints'/(X.sha((a['roll']+' '+a['url']).encode())[:24]+'.json')
 if fp.exists():return
 start=time.monotonic();r={**a,'started_at':X.now(),'method':'recheck_prior_success_unparsed_notice_with_actual_OCR_if_needed','documents':[],'attempts':[]}
 # Reuse existing actual payload where retained; otherwise request the known public original exactly once.
 cached=next((p for p in [O/'cache'/(a['prior_sha256']+'.pdf'),P/'cache'/(a['prior_sha256']+'.pdf'),X.ROOT/'cache'/(a['prior_sha256']+'.pdf')] if p.exists()),None)
 if cached:b=cached.read_bytes();st='reused_local_verified_payload';end=a['url']
 else:b,st,end=X.F.get(a['url'],a['roll'],'unparsed_notice_evidence_recovery')
 r['attempts'].append({'url':a['url'],'final_url':end,'status':st});r['status']=st
 if b:
  h=X.sha(b);r['sha256']=h;r['same_payload_as_prior_success']=(h==a['prior_sha256']);fmt='pdf' if b.startswith(b'%PDF') else 'docx' if b.startswith(b'PK') else 'html';r['format']=fmt;text='';ocr=False
  if fmt=='pdf':
   src=O/'cache'/(h+'.pdf');src.write_bytes(b);z=subprocess.run(['pdftotext','-layout',str(src),'-'],capture_output=True,timeout=30);text=z.stdout.decode('utf8','replace');r['parse_stderr']=z.stderr.decode('utf8','replace')[:400]
   if len(text.strip())<300:
    info=subprocess.run(['pdfinfo',str(src)],capture_output=True,timeout=15).stdout.decode('utf8','replace');m=re.search(r'^Pages:\s*(\d+)',info,re.M);n=int(m[1]) if m else 0
    if 0<n<=20:
     ocr=True;parts=[]
     for page in range(1,n+1):
      img=O/'cache'/(h+'_p'+str(page));subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-scale-to','2200','-gray','-png','-singlefile',str(src),str(img)],capture_output=True,timeout=40,check=True)
      
      if shutil.which('tesseract'):
       z=subprocess.run(['tesseract',str(img)+'.png','stdout','--psm','6'],capture_output=True,timeout=50,check=True);parts.append(z.stdout.decode('utf8','replace'))
      else:r['ocr_pending_reason']='tesseract_unavailable_and_package_repository_HTTP500; rendered_pages_available_for_manual_visual_review'
     text='\f\n'.join(parts)
    else:r['ocr_pending_reason']='invalid_pdf_or_more_than20pages_requires_review'
  elif fmt=='docx':
   src=O/'cache'/(h+'.docx');src.write_bytes(b)
   with zipfile.ZipFile(io.BytesIO(b)) as z:
    root=ET.fromstring(z.read('word/document.xml'));text='\n'.join(''.join(t.itertext()) for t in root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
  else:
   src=None;soup=X.BeautifulSoup(b,'html.parser');text=soup.get_text('\n',strip=True)
  text=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[school email omitted]',text);tf=O/'evidence'/(a['roll']+'_'+h[:20]+'.txt');tf.write_text(text)
  d={'roll':a['roll'],'url':end,'sha256':h,'format':fmt,'source_file':str(src.relative_to(X.ROOT)) if src else None,'text_file':str(tf.relative_to(X.ROOT)),'candidate_status':'actual_body_OCR_requires_manual_review' if ocr else 'actual_body_requires_manual_review','ocr':ocr,'retrieved_at':X.now()};r.update(documents=[d],status='body_retrieved_requires_manual_review',text_length=len(text))
 r['elapsed_seconds']=round(time.monotonic()-start,2);X.save(fp,r);print(a['roll'],r['status'],r.get('text_length'),r.get('documents',[{}])[0].get('ocr') if r['documents'] else '',flush=True)
with cf.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(one,todo))
X.save(O/'FINISHED.json',{'at':X.now(),'documents_queued':len(todo)});print('FINISHED',flush=True)
