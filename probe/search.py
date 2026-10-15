import re,html,json,urllib.request,urllib.parse,http.cookiejar,sys
B="https://openapt.seoul.go.kr"
names=["올림픽파크포레온","올림픽선수촌","메이플자이","래미안라그란데","잠실올림픽아이파크","헬리오시티","래미안솔베뉴","개포자이프레지던스","올림픽파크","선수촌","자이프레지던스","솔베뉴","라그란데","잠실올림픽"]
ret=sys.argv[1]
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",B+"/commonPortal/programLink.do?jspNm=/portal/aMenu/aptInfo/aptInfo.open")]
pg=op.open(B+"/commonPortal/programLink.do?jspNm=/portal/aMenu/aptInfo/aptInfo.open").read().decode()
tok=re.search(r'name="csrf-token" content="([^"]+)"',pg).group(1)
out={}
for n in names:
    d=urllib.parse.urlencode({"query":"aptInfo.selectAptMapDataList","searchValue":f"aptNm:{n}|gu:|dong:","returnUrl":ret,"csrfToken":tok}).encode()
    h=op.open(B+"/commonPortal/select.do",d).read().decode("utf-8","replace")
    if n==names[0]: open("probe/out5/search_sample.html","w").write(h)
    hits=[]
    for m in re.finditer(r"(A\d{8})",h):
        ctx=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",h[max(0,m.start()-300):m.start()+300])))
        hits.append((m.group(1),ctx[:260]))
    out[n]=list(dict(hits).items())[:8]
json.dump(out,open("probe/out5/search.json","w"),ensure_ascii=False,indent=1)
