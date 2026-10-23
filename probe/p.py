import sys,re,tempfile,time,urllib.request
from pathlib import Path
sys.path.insert(0,'scripts')
import openapt as oa
oa.DEADLINE=time.monotonic()+2500
s=oa.Session("A13824006")
out=[]
U=["FILE_000000001192788&fileSn=1","FILE_000000001192788&fileSn=2","FILE_000000001172076&fileSn=0","FILE_000000001012849&fileSn=0","FILE_000000000998758&fileSn=0","FILE_000000001004650&fileSn=0"]
for u in U:
  url=f"{oa.B}/open/FileDown.do?atchFileId={u}"
  try:
    data=s._open(url,timeout=120)
    with tempfile.TemporaryDirectory() as td:
      p=Path(td)/"f.pdf"; p.write_bytes(data)
      txt,kind=oa.extract(p,"f.pdf",max_pages=30)
    out.append(f"=== {u} {kind} {len(txt)}")
    L=txt.splitlines()
    keep=set()
    for i,ln in enumerate(L):
      if re.search(r"피트니스|휘트니스|헬스|사우나|수영|독서실|도서실|골프|GX|주민공동|커뮤니티|이용료|운영시간|아이두레",ln):
        keep.update(range(max(0,i-2),min(len(L),i+6)))
    out+= [L[i].rstrip()[:180] for i in sorted(keep)]
  except Exception as e: out.append(f"{u} ERR {e}")
open('probe/out.txt','w').write("\n".join(out)[:250000])
# 1792770545
