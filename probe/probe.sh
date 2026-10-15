mkdir -p probe/out8
python3 - <<'PY'
import re,urllib.request,urllib.parse,http.cookiejar,html
B="https://openapt.seoul.go.kr"
for code in ["A10020294","A13824006","A10023043"]:
    op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",f"{B}/openApt/index.do?aptCode={code}")]
    idx=op.open(f"{B}/openApt/index.do?aptCode={code}").read().decode()
    tok=re.search(r'name="csrf-token" content="([^"]+)"',idx).group(1)
    def post(p,d): return op.open(B+p,urllib.parse.urlencode({**d,"csrfToken":tok}).encode()).read().decode("utf-8","replace")
    l=post("/boardForm/selectBoardList.do",{"aptCode":code,"returnUrl":"/openApt/aMenu/mngAgree/mngAgreeList.open","query":"openAptMngCommonBoard.openAptMngBoardList","bbsCommCode":"09"})
    open(f"probe/out8/list_{code}.html","w").write(l)
    m=re.search(r"onDetail\(\s*'?(\d+)",l)
    rd=re.search(r'name="returnUrl"[^>]*value="([^"]*Detail[^"]*)"',l)
    if m:
        d=post("/boardForm/boardDetail.do",{"aptCode":code,"searchValue":f"aptCode:{code}|bbsCommCode:09|nttId:{m.group(1)}","query":"openAptMngCommonBoard.openAptMngBoardDetail","returnUrl":rd.group(1) if rd else "/openApt/aMenu/mngAgree/mngAgreeDetail.open"})
        open(f"probe/out8/detail_{code}.html","w").write(d)
PY
