mkdir -p probe/out7
python3 - <<'PY'
import re,urllib.request,urllib.parse,http.cookiejar
B="https://openapt.seoul.go.kr"; page="/commonPortal/programLink.do?jspNm=/portal/aMenu/aptInfo/aptInfo.open"
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",B+page)]
tok=re.search(r'name="csrf-token" content="([^"]+)"',op.open(B+page).read().decode()).group(1)
d=urllib.parse.urlencode({"query":"aptInfo.selectAptInfoDetail","searchValue":"aptCode:A10021122","returnUrl":"portal/aMenu/aptInfo/detailComponent/aptInfoBasic","csrfToken":tok}).encode()
open("probe/out7/basic.html","w").write(op.open(B+"/commonPortal/select.do",d).read().decode("utf-8","replace"))
PY
