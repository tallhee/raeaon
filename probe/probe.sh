mkdir -p probe/out9
python3 - <<'PY'
import re,urllib.request,urllib.parse,http.cookiejar
B="https://openapt.seoul.go.kr"
for code in ["A10020294","A13824006","A10025850"]:
    op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",f"{B}/openApt/index.do?aptCode={code}")]
    idx=op.open(f"{B}/openApt/index.do?aptCode={code}").read().decode()
    tok=re.search(r'name="csrf-token" content="([^"]+)"',idx).group(1)
    def post(p,d): return op.open(B+p,urllib.parse.urlencode({**d,"csrfToken":tok}).encode()).read().decode("utf-8","replace")
    for bbs,url in (("04","/openApt/aMenu/repairPlan/repairPlanList.open"),("17","/openApt/eMenu/etc/mngEtcList.open"),("05","/openApt/aMenu/auditReport/auditReportList.open")):
        open(f"probe/out9/{code}_{bbs}.html","w").write(post("/boardForm/selectBoardList.do",{"aptCode":code,"returnUrl":url,"query":"openAptMngCommonBoard.openAptMngBoardList","bbsCommCode":bbs}))
    open(f"probe/out9/{code}_repairCost.html","w").write(post("/commonPortal/programLink.do",{"aptCode":code,"jspNm":"/openApt/cMenu/repairCost/repairCost.open","comcod":""}))
PY
