import sys,re,tempfile,time
from pathlib import Path
sys.path.insert(0,'scripts')
import openapt as oa
oa.DEADLINE=time.monotonic()+2500
T0=time.monotonic()
out=[];hits=[]
s=oa.Session("A13824006")
rows=[]
for page in range(1,80):
  h=s.post("/boardForm/selectBoardList.do",{"aptCode":"A13824006","returnUrl":"/openApt/aMenu/aptLeaderMeeting/leaderMeetingList.open","query":"openAptMngCommonBoard.openAptMngBoardList","bbsCommCode":"02","pageIndex":str(page)})
  r=oa.parse_list(h)
  if not r: break
  rows+=r
old=[r for r in rows if r["date"]<"2024-03-01"]
out.append(f"total {len(rows)} old {len(old)} oldest {min((r['date'] for r in rows),default='')}")
P=re.compile(r"(피트니스|헬스|사우나|수영|독서실|골프|GX|주민공동시설|커뮤니티|휘트니스|스포츠센터).{0,60}([\d,]{3,}\s*원|\d+\s*회|\d{1,2}\s*:\s*\d\d)|이용료|운영\s*시간|운영세칙")
for r in old:
  if time.monotonic()-T0>2300: out.append("TIME");break
  try:
    d=s.post("/boardForm/boardDetail.do",{"aptCode":"A13824006","searchValue":f"aptCode:A13824006|bbsCommCode:02|nttId:{r['nttId']}","query":"openAptMngCommonBoard.openAptMngBoardDetail","returnUrl":"/openApt/aMenu/aptLeaderMeeting/leaderMeetingDetail.open"})
    files,body=oa.parse_detail(d)
    texts=[(body or "","본문",None)]
    for f in files[:4]:
      if f.get("inline"): continue
      url=f"{oa.B}/open/FileDown.do?atchFileId={f['atchFileId']}&fileSn={f['fileSn']}"
      data=s._open(url,timeout=90)
      with tempfile.TemporaryDirectory() as td:
        p=Path(td)/("f"+Path(f["name"]).suffix[:6]); p.write_bytes(data)
        txt,kind=oa.extract(p,f["name"],max_pages=6)
      texts.append((txt,f["name"],url))
    for txt,nm,url in texts:
      ls=[ln.strip()[:170] for ln in txt.splitlines() if P.search(ln)]
      if ls: hits.append(f"### {r['date']} {r['title']} | {nm} | {url}\n"+"\n".join(ls[:12]))
  except Exception as e: out.append(f"{r['nttId']} ERR {str(e)[:80]}")
open('probe/out.txt','w').write("\n".join(out+hits)[:300000])
# 1792768163
