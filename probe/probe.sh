set -x
mkdir -p probe/out2; cd probe/out2
B=https://openapt.seoul.go.kr
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124"
A=A10020294
curl -sSL -A "$UA" -c jar -b jar "$B/openApt/index.do?aptCode=$A" -o index.html
T=$(grep -oE 'name="csrf-token" content="[^"]+"' index.html | sed -E 's/.*content="([^"]+)"/\1/')
echo "token=$T" > token.txt
curl -sSL -A "$UA" -c jar -b jar -e "$B/openApt/index.do?aptCode=$A" "$B/boardForm/selectBoardList.do" \
  --data-urlencode "aptCode=$A" --data-urlencode "returnUrl=/openApt/aMenu/aptLeaderMeeting/leaderMeetingList.open" \
  --data-urlencode "query=openAptMngCommonBoard.openAptMngBoardList" --data-urlencode "bbsCommCode=02" \
  --data-urlencode "csrfToken=$T" -o list.html -w "list %{http_code}\n" >> codes.txt
curl -sSL -A "$UA" -c jar -b jar -e "$B/openApt/index.do?aptCode=$A" "$B/boardForm/boardDetail.do" \
  --data-urlencode "aptCode=$A" --data-urlencode "searchValue=aptCode:$A|bbsCommCode:02|nttId:3058662" \
  --data-urlencode "query=openAptMngCommonBoard.openAptMngBoardDetail" \
  --data-urlencode "returnUrl=/openApt/aMenu/aptLeaderMeeting/leaderMeetingDetail.open" \
  --data-urlencode "csrfToken=$T" -o detail.html -w "detail %{http_code}\n" >> codes.txt
grep -n -i -E "download|fileDown|atch|첨부|\.pdf|\.hwp" detail.html | head -60 > detail_hits.txt
grep -n -i -E "goActDetail|nttId|fn_|page|paging|onclick" list.html | head -80 > list_hits.txt
