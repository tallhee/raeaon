mkdir -p probe/out4; cd probe/out4
python3 - <<'PY'
import re,urllib.request,urllib.parse,http.cookiejar
B="https://openapt.seoul.go.kr"; code="A10023043"
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",f"{B}/openApt/index.do?aptCode={code}")]
idx=op.open(f"{B}/openApt/index.do?aptCode={code}").read().decode()
tok=re.search(r'name="csrf-token" content="([^"]+)"',idx).group(1)
def post(p,d): return op.open(B+p,urllib.parse.urlencode({**d,"csrfToken":tok}).encode()).read().decode("utf-8","replace")
l=post("/boardForm/selectBoardList.do",{"aptCode":code,"returnUrl":"/openApt/aMenu/aptLeaderMeeting/leaderMeetingList.open","query":"openAptMngCommonBoard.openAptMngBoardList","bbsCommCode":"02"})
open("list.html","w").write(l)
ntt=re.search(r"onDetail\(\s*'?(\d+)",l).group(1)
d=post("/boardForm/boardDetail.do",{"aptCode":code,"searchValue":f"aptCode:{code}|bbsCommCode:02|nttId:{ntt}","query":"openAptMngCommonBoard.openAptMngBoardDetail","returnUrl":"/openApt/aMenu/aptLeaderMeeting/leaderMeetingDetail.open"})
open("detail.html","w").write(d)
PY
