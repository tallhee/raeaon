import re,sys
sys.path.insert(0,'scripts')
import collect as c
out=[]
for nm in ("잠실래미안아이파크","올림픽파크포레온"):
  h=c.fetch("/bid/privateContractList.do",{"pageSelect":100,"aptName":nm,"searchDateGb":"reg","dateStart":"2025-01-01","dateEnd":"2026-10-21","pageNo":1,"bidArea":"11","area":"11"})
  trs=re.findall(r'<tr[^>]*>(.*?)</tr>',h,re.S)
  out.append(f"== {nm} trs={len(trs)}")
  heads=re.findall(r'<th[^>]*>(.*?)</th>',h,re.S); out.append("TH: "+" | ".join(c.text_of(x) for x in heads[:20]))
  for t in trs[:4]: out.append("ROWRAW: "+re.sub(r'\s+',' ',t)[:900])
h=c.fetch("/bid/bidList.do",{"pageSelect":100,"searchBidGb":"bid_gb_1","bidTitle":"","searchDateGb":"reg","dateStart":"2024-01-01","dateEnd":"2026-10-21","pageNo":1,"type":"3","bidArea":"11","aptName":"잠실래미안아이파크"})
for b,inner in c.ROW_RE.findall(h): out.append("BID: "+b+" "+" | ".join(c.text_of(x) for x in re.findall(r"<td[^>]*>(.*?)</td>",inner,re.S)))
open('probe/out.txt','w').write("\n".join(out))
