import re,sys
sys.path.insert(0,'scripts')
import collect as c
h=c.fetch("/bid/privateContractDetail.do",{"pcNum":"20260928181740077"},timeout=60)
t=c.text_of(h)
i=t.find("KT")
open('probe/out.txt','w').write(f"len={len(h)} title={re.findall(r'<title>(.*?)</title>',h)} has_KT={'KT 임대차' in t}\n"+t[max(0,i-300):i+600])
h2=c.fetch("/bid/privateContractList.do",{"aptName":"잠실래미안아이파크"},timeout=60)
m=re.search(r"function\s+goView\s*\([^)]*\)\s*\{(.{0,800}?)\}",h2,re.S)
open('probe/out.txt','a').write("\nGOVIEW:"+(m.group(0) if m else "none"))
