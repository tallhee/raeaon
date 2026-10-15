mkdir -p probe/out5; cd probe/out5
B=https://openapt.seoul.go.kr; UA="Mozilla/5.0 Chrome/124"
curl -sSL -A "$UA" -c jar -b jar "$B/commonPortal/programLink.do?jspNm=/portal/aMenu/aptInfo/aptInfo.open" -o aptinfo.html
grep -n -i -E "ajax|url\s*:|\.do|search|aptNm|kaptName|function " aptinfo.html | head -150 > aptinfo_hits.txt
