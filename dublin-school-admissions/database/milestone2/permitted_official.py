"""Reuse verified origin robots and host denial state; never retry actual controls."""
import json
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import collect_sites as X
P=X.P
robots={};denied=set()
for line in (P/'requests.jsonl').read_text().splitlines():
 try:r=json.loads(line)
 except:continue
 u=r.get('url','');z=urlsplit(u);st=r.get('status','')
 if st in ['network_proxy_block','anti_bot_challenge','http_access_denied_401','http_access_denied_403','http_access_denied_429']:denied.add(z.hostname)
 if z.path=='/robots.txt':robots[z.scheme+'://'+z.netloc]=r
for origin,r in robots.items():
 st=r.get('status','');f=P/'cache'/('robots_'+X.sha(origin.encode())[:20]+'.txt')
 if st in ['robots_rules_loaded','reused_verified_robots_rules'] and f.exists():
  rp=RobotFileParser();rp.parse(f.read_text().splitlines());X.F.rules[origin]=(rp,max(2.8,rp.crawl_delay(X.BOT) or rp.crawl_delay('*') or 0),'reused_milestone2_verified_robots_rules')
 elif st in ['robots_absent','reused_robots_absent']:X.F.rules[origin]=(None,2.8,st)
 else:X.F.rules[origin]=(False,2.8,st)
X.F.blocked.update({h:'prior_milestone2_host_access_or_network_control_not_retried' for h in denied if h})
