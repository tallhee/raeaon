set -x
mkdir -p probe/out; cd probe/out
B=https://openapt.seoul.go.kr
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124"
curl -sSL -A "$UA" -c jar -b jar "$B/openApt/index.do?aptCode=A10020294" -o index.html -w "%{http_code}\n" > code.txt
# 스크립트 파일 전부
grep -oE '<script[^>]+src="[^"]+"' index.html | sed -E 's/.*src="([^"]+)"/\1/' | sort -u > scripts.txt
i=0; while read s; do i=$((i+1)); case "$s" in http*) u="$s";; /*) u="$B$s";; *) u="$B/openApt/$s";; esac
  curl -sSL -A "$UA" -b jar "$u" -o "js_$i.js"; echo "$i $u" >> scripts_map.txt; done < scripts.txt
# 입대의 관련 마크업과 인라인 스크립트
grep -n -i -E "입주자대표회의|선거관리|board|bbs|onclick|fn_|\.do" index.html | head -400 > hits.txt
ls -la > ls.txt
