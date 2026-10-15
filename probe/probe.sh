mkdir -p probe/out10
python3 - <<'PY'
import re,urllib.request,urllib.parse,http.cookiejar,json
B="https://openapt.seoul.go.kr"; page="/commonPortal/programLink.do?jspNm=/portal/aMenu/aptInfo/aptInfo.open"
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",B+page)]
tok=re.search(r'name="csrf-token" content="([^"]+)"',op.open(B+page).read().decode()).group(1)
def s(v): 
    h=op.open(B+"/commonPortal/select.do",urllib.parse.urlencode({"query":"aptInfo.selectAptMapDataList","searchValue":v,"returnUrl":"portal/aMenu/aptInfo/aptInfoSearch","csrfToken":tok}).encode()).read().decode("utf-8","replace")
    return {"cnt":re.findall(r'schReCnt[^>]*>([\d,]+)<',h),"n":len(re.findall(r'dlApt(A\d{8})',h)),"names":re.findall(r'<dt>\s*<a[^>]*>([^<]+)',h)[:400]}
out={"gu":s("aptNm:|gu:동작구|dong:"),"name":s("aptNm:흑석리버파크자이|gu:|dong:"),"dong":s("aptNm:|gu:동작구|dong:흑석동")}
json.dump(out,open("probe/out10/r.json","w"),ensure_ascii=False,indent=1)
PY
