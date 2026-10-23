import sys,re,json
sys.path.insert(0,'scripts')
import openapt as oa
oa.DEADLINE=oa.time.monotonic()+1500
out=[]
s=oa.Session("A13824006")
for bbs,ret in (("09","/openApt/aMenu/mngAgree/mngAgreeList.open"),("17","/openApt/eMenu/etc/mngEtcList.open"),("02","/openApt/aMenu/aptLeaderMeeting/leaderMeetingList.open")):
  for page in range(1,40):
    try:
      h=s.post("/boardForm/selectBoardList.do",{"aptCode":"A13824006","returnUrl":ret,"query":"openAptMngCommonBoard.openAptMngBoardList","bbsCommCode":bbs,"pageIndex":str(page)})
    except Exception as e:
      out.append(f"{bbs} p{page} ERR {e}");break
    rows=oa.parse_list(h)
    if not rows: break
    for r in rows:
      if bbs!="02" or re.search(r"커뮤니티|주민공동|피트니스|헬스|운영규정|운영세칙|이용료|사우나|수영|독서실",r["title"]):
        out.append(f"{bbs}|{r['date']}|{r['nttId']}|{r['title']}")
open('probe/out.txt','w').write("\n".join(out))
# 1792767911
