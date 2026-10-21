import urllib.request,re,ssl
out=[]
for path in ("/openApt/aMenu/aptLeaderMeeting/leaderMeetingList.open?aptCode=A10024152","/openApt/aMenu/mngAgree/mngAgreeList.open?aptCode=A10024152","/openApt/index.do?aptCode=A10024152"):
  try:
    h=urllib.request.urlopen("https://openapt.seoul.go.kr"+path,timeout=40).read().decode("utf-8","replace")
    out.append(f"{path}: len={len(h)} 포레나={'포레나' in h} 제14차={'제14차' in h} title={re.findall(r'<title>(.*?)</title>',h)[:1]}")
  except Exception as e: out.append(f"{path}: ERR {e}")
open('probe/out.txt','w').write("\n".join(out))
