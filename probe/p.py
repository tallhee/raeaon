import sys,re,tempfile
from pathlib import Path
sys.path.insert(0,'scripts')
import openapt as oa
oa.DEADLINE=oa.time.monotonic()+2400
out=[]
s=oa.Session("A13824006")
for ntt in ("2350296","2328351","201425","2102819","42236"):
  try:
    d=s.post("/boardForm/boardDetail.do",{"aptCode":"A13824006","searchValue":f"aptCode:A13824006|bbsCommCode:09|nttId:{ntt}","query":"openAptMngCommonBoard.openAptMngBoardDetail","returnUrl":"/openApt/aMenu/mngAgree/mngAgreeDetail.open"})
    files,_=oa.parse_detail(d)
    for f in files:
      if f.get("inline"): continue
      url=f"{oa.B}/open/FileDown.do?atchFileId={f['atchFileId']}&fileSn={f['fileSn']}"
      data=s._open(url,timeout=120)
      with tempfile.TemporaryDirectory() as td:
        p=Path(td)/("f"+Path(f["name"]).suffix[:6]); p.write_bytes(data)
        txt,kind=oa.extract(p,f["name"],max_pages=60)
      out.append(f"=== {ntt} {f['name']} {kind} {len(txt)} {url}")
      for i,ln in enumerate(txt.splitlines()):
        if re.search(r"(피트니스|헬스|사우나|수영|독서실|골프|주민공동시설|커뮤니티).{0,40}([\d,]{3,}\s*원|\d+\s*회|\d{1,2}\s*:\s*\d\d|\d+\s*시)",ln) or re.search(r"이용료|운영시간|별표.{0,10}(주민공동|커뮤니티|복리)",ln):
          out.append(f"{i}: {ln.strip()[:170]}")
  except Exception as e: out.append(f"{ntt} ERR {e}")
open('probe/out.txt','w').write("\n".join(out)[:200000])
# 1792768039
