import re,sys
sys.path.insert(0,'scripts')
import collect as c
out=[]
h=c.fetch("/bid/bidList.do")
out.append("FORM FIELDS: "+", ".join(sorted(set(re.findall(r'name="([A-Za-z_]+)"',h)))))
out.append("LINKS: "+"\n".join(sorted(set(re.findall(r'href="(/[a-zA-Z/]+\.do[^"]*)"',h)))[:200]))
for kw in ("kaptName","searchKaptName","aptName","kaptCode"):
  try:
    h2=c.fetch("/bid/bidList.do",{"pageSelect":100,"searchBidGb":"bid_gb_1","bidTitle":"","searchDateGb":"reg","dateStart":"2025-06-01","dateEnd":"2026-10-21","pageNo":1,"type":"3","bidArea":"11",kw:"잠실래미안아이파크"})
    rows=c.ROW_RE.findall(h2); names=[c.text_of(x) for x in re.findall(r"<td[^>]*>(.*?)</td>",rows[0][1],re.S)] if rows else []
    out.append(f"{kw}: rows={len(rows)} first={names}")
  except Exception as e: out.append(f"{kw}: ERR {e}")
for path in ("/bid/privateContractList.do","/bid/pContractList.do","/bid/contractList.do","/bid/bidList.do?searchBidGb=bid_gb_2"):
  try:
    h3=c.fetch(path); out.append(f"{path}: len={len(h3)} title={re.findall(r'<title>(.*?)</title>',h3)} rows={len(c.ROW_RE.findall(h3))} fields={sorted(set(re.findall(r'name=\"([A-Za-z_]+)\"',h3)))[:40]}")
  except Exception as e: out.append(f"{path}: ERR {e}")
open('probe/out.txt','w').write("\n".join(out))
