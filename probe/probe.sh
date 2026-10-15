mkdir -p probe/out6
python3 - <<'PY'
import re,urllib.request,urllib.parse,http.cookiejar
B="https://openapt.seoul.go.kr"; page="/commonPortal/programLink.do?jspNm=/portal/aMenu/aptInfo/aptInfo.open"
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",B+page)]
tok=re.search(r'name="csrf-token" content="([^"]+)"',op.open(B+page).read().decode()).group(1)
def post(d): return op.open(B+"/commonPortal/select.do",urllib.parse.urlencode({**d,"csrfToken":tok}).encode()).read().decode("utf-8","replace")
open("probe/out6/info.html","w").write(post({"query":"aptInfo.selectAptInfoDetail","aptCode":"A10021122","returnUrl":"portal/aMenu/aptInfo/aptInfoDetailView","tabCd":"1"}))
for n in ["트리지움","잠실트리지움아파트"]:
    open(f"probe/out6/s_{n}.html","w").write(post({"query":"aptInfo.selectAptMapDataList","searchValue":f"aptNm:{n}|gu:|dong:","returnUrl":"portal/aMenu/aptInfo/aptInfoSearch"}))
open("probe/out6/s_gaepo.html","w").write(post({"query":"aptInfo.selectAptMapDataList","searchValue":"aptNm:|gu:강남구|dong:개포동","returnUrl":"portal/aMenu/aptInfo/aptInfoSearch"}))
PY
