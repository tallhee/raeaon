import re, html, json, os, subprocess, urllib.request, urllib.parse, http.cookiejar, time
B="https://openapt.seoul.go.kr"
APTS={"잠실래미안아이파크":"A10020294","원페를라":"A10020358","원펜타스":"A10022556","잠실르엘":"A10020230","파크리오":"A13824006","원베일리":"A10023043"}
OUT="probe/out3"; os.makedirs(OUT,exist_ok=True)
def T(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s))).strip()
report={}
for name,code in APTS.items():
    jar=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders=[("User-Agent","Mozilla/5.0 Chrome/124"),("Referer",f"{B}/openApt/index.do?aptCode={code}")]
    idx=op.open(f"{B}/openApt/index.do?aptCode={code}",timeout=30).read().decode("utf-8","replace")
    tok=re.search(r'name="csrf-token" content="([^"]+)"',idx).group(1)
    def post(path,d): return op.open(B+path,urllib.parse.urlencode({**d,"csrfToken":tok}).encode(),timeout=30).read().decode("utf-8","replace")
    r={"boards":{}}
    for bbs,url in (("02","/openApt/aMenu/aptLeaderMeeting/leaderMeetingList.open"),("03","/openApt/aMenu/electionCmt/electionCmtList.open")):
        h=post("/boardForm/selectBoardList.do",{"aptCode":code,"returnUrl":url,"query":"openAptMngCommonBoard.openAptMngBoardList","bbsCommCode":bbs})
        tot=re.search(r'txStrong">([\d,]+)</span>\s*건',h)
        rows=[]
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>",h,re.S)[1:]:
            tds=[T(x) for x in re.findall(r"<td[^>]*>(.*?)</td>",tr,re.S)]
            nid=re.search(r"onDetail\('?(\d+)",tr); fid=re.findall(r"'(FILE_\d+)'",tr)
            if tds: rows.append({"tds":tds,"nttId":nid.group(1) if nid else None,"file":fid[:1]})
        r["boards"][bbs]={"total":tot.group(1) if tot else None,"rows":rows[:12]}
    # 회의결과 상세 2건 → 첨부 목록, 다운로드, 추출 시험
    tests=[x for x in r["boards"]["02"]["rows"] if x["nttId"] and "결과" in " ".join(x["tds"])][:2]
    r["tests"]=[]
    for x in tests:
        d=post("/boardForm/boardDetail.do",{"aptCode":code,"searchValue":f"aptCode:{code}|bbsCommCode:02|nttId:{x['nttId']}","query":"openAptMngCommonBoard.openAptMngBoardDetail","returnUrl":"/openApt/aMenu/aptLeaderMeeting/leaderMeetingDetail.open"})
        files=sorted(set(re.findall(r"FileDown\.do\?atchFileId=(FILE_\d+)&(?:amp;)?fileSn=(\d+)',\s*'([^']+)'",d)))
        body=T(d[d.find("첨부파일"):][:3000]) if "첨부파일" in d else ""
        t={"title":x["tds"][1] if len(x["tds"])>1 else "","files":files,"body_after":body[-400:],"extract":[]}
        for fid,sn,fn in files[:3]:
            p=f"{OUT}/{code}_{fid}_{sn}"
            data=op.open(f"{B}/open/FileDown.do?atchFileId={fid}&fileSn={sn}",timeout=60).read()
            open(p,"wb").write(data)
            kind=subprocess.run(["file","-b",p],capture_output=True,text=True).stdout.strip()
            txt=""
            if "PDF" in kind: txt=subprocess.run(["pdftotext","-layout",p,"-"],capture_output=True,text=True).stdout
            elif "image" in kind or "JPEG" in kind or "PNG" in kind:
                txt=subprocess.run(["tesseract",p,"-","-l","kor+eng","--psm","6"],capture_output=True,text=True).stdout
            elif "Hangul" in kind or fn.lower().endswith((".hwp",".hwpx")):
                txt=subprocess.run(["hwp5txt",p],capture_output=True,text=True).stdout
            t["extract"].append({"name":fn,"bytes":len(data),"kind":kind,"chars":len(txt.strip()),"sample":txt.strip()[:1500]})
        r["tests"].append(t)
    report[name]=r; time.sleep(1)
json.dump(report,open(f"{OUT}/report.json","w"),ensure_ascii=False,indent=1)
