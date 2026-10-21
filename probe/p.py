import re,sys,traceback
sys.path.insert(0,'scripts')
import collect as c
out=[]
for how in ("get","post"):
  try:
    if how=="get": h=c.fetch("/bid/privateContractDetail.do",{"pcNum":"20260928181740077"},timeout=60)
    else: h=c.fetch("/bid/privateContractDetail.do",data={"pcNum":"20260928181740077"},timeout=60)
    t=c.text_of(h); out.append(f"{how}: len={len(h)} has={'KT 임대차' in t} {t[t.find('계약명'):t.find('계약명')+300] if '계약명' in t else t[:300]}")
  except Exception as e: out.append(f"{how}: ERR {e}")
try:
  h2=c.fetch("/bid/privateContractList.do",{"aptName":"잠실래미안아이파크"},timeout=60)
  m=re.search(r"goView\s*\(.{0,10}\)\s*\{.{0,800}",h2,re.S) or re.search(r"function goView.{0,800}",h2,re.S)
  out.append("GOVIEW:"+(m.group(0) if m else "none"))
except Exception as e: out.append(f"list ERR {e}")
open('probe/out.txt','w').write("\n".join(out)+"\n#"+str(__import__('time').time()))
# 1792591195
