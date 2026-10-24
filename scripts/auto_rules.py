#!/usr/bin/env python3
"""규정 비교표 자동 추출 (규칙 기반, 무료).

수집해 둔 운영규정(bylaws.json)과 회의결과(minutes.json)에서
방문차량 시간·요금, 추가 차량 요금, 커뮤니티 운영시간·요금·횟수, 식당 관련 줄을
단어 규칙으로 골라 docs/data/rules_auto.json 에 적는다.

- 사람이 확인해 적은 docs/data/rules.json 은 건드리지 않는다.
- 사이트는 rules.json 에 없는 단지·주제만 이 파일에서 가져와 '자동 추출 · 원문 확인 필요'로 보여준다.
- 값은 원문 줄을 그대로 옮긴 것(해석하지 않음)이라 표가 깨진 곳은 엉뚱할 수 있다.
"""
from __future__ import annotations

import json
import re
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data"
TODAY = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d")

NUM_WON = r"[\d,]{3,}\s*원|\d+\s*만\s*원|\d+천\s*원"
FIELDS = {
    "allowance": {},
    "parking": {
        "visitor_fee": [r"방문.{0,40}\d+\s*시간", r"방문.{0,60}(?:" + NUM_WON + ")", r"무료\s*주차\s*시간.{0,40}\d"],
        "per_unit_by_area": [r"(?:[1-5]\s*대\s*(?:추가|째|보유|이상|초과|무료|부과|:)|추가\s*[1-5]\s*대|기본\s*대수|대당).{0,40}(?:" + NUM_WON + "|무료)"],
        "public_facility_users_allowed": [r"(?:상가|공공개방|개방시설|어린이집).{0,40}(?:무료|" + NUM_WON + r"|\d+\s*대)"],
    },
    "community": {
        "hours": [r"(?:평일|주말|[월화수목금토일]요일|[월화]\s*~|공휴일|운영\s*시간|이용\s*시간).{0,30}\d{1,2}\s*:\s*\d{2}\s*~\s*(?:익일\s*)?\d{1,2}\s*:\s*\d{2}"],
        "fee": [r"(?:기본\s*(?:운영비|이용료|관리비)|커뮤니티\s*운영비|부분공동관리비|세대분담금|초과\s*시|1회|회당|이용료).{0,40}(?:" + NUM_WON + ")"],
        "entry_limit": [r"월\s*\d+\s*회", r"\d+\s*회\s*무료"],
    },
    "dining": {
        "operator_selection": [r"(?:식당|다이닝|조식|카페테리아).{0,40}(?:위탁|입찰|적격심사|업체\s*선정|수의계약)"],
        "hours": [r"(?:식당|다이닝|조식|중식|석식|카페테리아).{0,40}\d{1,2}\s*:\s*\d{2}"],
        "price": [r"(?:식당|다이닝|조식|중식|석식|1식|식권|식대|식사).{0,40}(?:" + NUM_WON + ")"],
    },
}
DOC_TOPIC = [("parking", r"주차"), ("community", r"커뮤니티|휘트니스|헬스|주민공동시설|시설물?\s*사용|센터\s*운영"),
             ("dining", r"커뮤니티|식당|다이닝|조식|주민공동시설")]
SKIP_LINE = re.compile(r"[·…]{4,}|위반금|과태료|손해|분실|벌칙|연체|회의|일\s*시|행사|일정|개최|수리|공사|교체|구매|구입|예산|"
                       r"상여|급여|인건비|시급|수수료|보증금|투표|동의서|강사|레슨|강습|PT|청소|창고|택배|사무실|용역비")
HEAD_KW = {"parking": r"주차|방문\s*차량|차량", "community": r"커뮤니티|헬스|피트니스|사우나|수영|골프|이용|운영\s*시간|휴관|운영규정",
           "dining": r"식당|다이닝|조식|중식|석식|카페테리아|식사"}


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" |-·•※")


def pick(lines: list[str], pats: list[str], limit=3) -> list[str]:
    out = []
    for ln in lines:
        s = clean(ln)
        if len(s) < 6 or len(s) > 200 or SKIP_LINE.search(s):
            continue
        hangul = len(re.findall(r"[가-힣]", s))
        if hangul < 3 or hangul < len(s) * 0.15:  # 글자 인식이 깨진 줄
            continue
        if any(re.search(p, s) for p in pats) and s not in out:
            out.append(s)
            if len(out) >= limit:
                break
    return out


def load(p: Path, d):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return d


def main() -> int:
    bylaws = load(DATA / "bylaws.json", {"docs": []})
    minutes = load(DATA / "minutes.json", {"items": [], "complexes": []})
    cxinfo = {c["name"]: c for c in minutes.get("complexes", [])}
    found: dict[tuple, dict] = {}  # (complex, topic) -> {date, fields, sources}

    def offer(cx, topic, date, fields, src):
        if not any(fields.values()):
            return
        cur = found.get((cx, topic))
        if cur and cur["date"] >= date:  # 더 최근 자료만 덮어쓴다
            return
        found[(cx, topic)] = {"date": date, "fields": fields, "sources": [src]}

    # 1) 운영규정 (관리규약 본문은 금액이 거의 없어 제외)
    for d in bylaws.get("docs", []):
        title = d.get("title", "")
        if re.search(r"관리규약", title) and not re.search(r"주차|커뮤니티", title):
            continue
        for topic, tp in DOC_TOPIC:
            if not re.search(tp, title):
                continue
            for f in d.get("files", []):
                tp_path = DATA / f.get("text_path", "-")
                if not tp_path.exists() or not f.get("url"):
                    continue
                lines = tp_path.read_text(encoding="utf-8").splitlines()
                fields = {k: " / ".join(pick(lines, pats)) or None for k, pats in FIELDS[topic].items()}
                offer(d["complex"], topic, d.get("date", ""), fields,
                      {"text": f"{title} ({d.get('date', '')})", "url": f["url"], "code": d.get("code"), "bbs": "09",
                       "post": title})
                break

    # 2) 회의결과: 해당 주제로 분류되고 부결이 아닌 안건
    for it in minutes.get("items", []):
        if it.get("status") != "done" or it.get("kind") == "doc":
            continue
        url = next((f.get("url") for f in it.get("files", []) if f.get("url")), None)
        for a in it.get("agenda") or []:
            if "부결" in (a.get("votes") or ""):
                continue
            for topic in set(a.get("topics", [])) & set(FIELDS):
                if not re.search(HEAD_KW[topic], a.get("head", "")):
                    continue
                lines = (a.get("head", "") + "\n" + a.get("text", "")).splitlines()
                fields = {k: " / ".join(pick(lines, pats, 2)) or None for k, pats in FIELDS[topic].items()}
                if url:
                    offer(it["complex"], topic, it.get("date", ""), fields,
                          {"text": f"회의결과: {clean(a.get('head', ''))[:40]} ({it.get('date', '')})", "url": url,
                           "code": it.get("code"), "bbs": it.get("bbs"), "post": it.get("title")})

    # 3) 입대의 운영비(출석수당·직책수당): 단지별 최신 관리규약의 '운영비' 조항
    def fixamt(t: str) -> str:
        t = re.sub(r"\s+", " ", t).strip()
        t = re.sub(r"만\s*원?\s*(\d[\d,]*)\s*원", r"\1만 원", t)  # '매월 만 100 원' 처럼 깨진 배치
        return t
    latest: dict[str, dict] = {}
    for d in bylaws.get("docs", []):
        if "규약" in d.get("title", "") and not re.search(r"비교|개정안|\(안\)|제안서", d.get("title", "")):
            if d.get("date", "") >= latest.get(d["complex"], {}).get("date", ""):
                latest[d["complex"]] = d
    for cx, d in latest.items():
        f = next((f for f in d.get("files", []) if (DATA / f.get("text_path", "-")).exists()), None)
        if not f:
            continue
        lines = (DATA / f["text_path"]).read_text(encoding="utf-8").splitlines()
        start = next((i for i, l in enumerate(lines) if re.search(r"제\s*\d+\s*조\s*\(?\s*(입주자대표회의\s*)?운영비", l)
                      and not re.search(r"[·…\-]{4,}", l)), None)
        if start is None:
            continue
        block = lines[start:start + 80]
        def grab(pat, n=1):
            outl = []
            for i, l in enumerate(block):
                if re.search(pat, l):
                    t = fixamt(" ".join(block[i:i + n]))
                    if re.search(r"\d", t):
                        outl.append(t[:110])
            return " / ".join(outl[:3]) or None
        def tidy(v, cut=True):
            if not v:
                return v
            v = v if not cut else re.split(r"\s\d\s*\.\s*(?:회장|감사|이사|다음|그 밖)|\s-\s*\d+\s*-", v)[0]
            return re.sub(r"(^|/ )\d\s*\.\s*", r"\1", v).strip()
        fields = {"attend": tidy(grab(r"출\s*석", 4)), "chair": tidy(grab(r"회장\s*(직책|업무)\S*\s*:"), False),
                  "others": tidy(grab(r"(부회장|감사|이사|총무)\s*(직책|업무)\S*\s*:"), False)}
        if any(fields.values()) and f.get("url"):
            offer(cx, "allowance", d.get("date", ""), fields,
                  {"text": f"{d.get('title', '')} 운영비 조항 ({d.get('date', '')})", "url": f["url"], "code": d.get("code"),
                   "bbs": "09", "post": d.get("title")})

    rows: dict[str, dict] = {}
    for (cx, topic), v in sorted(found.items()):
        info = cxinfo.get(cx, {})
        r = rows.setdefault(cx, {"name": cx, "sigungu": info.get("sigungu"), "households": info.get("households"),
                                 "auto": True})
        r[topic] = {**v["fields"], "sources": v["sources"], "as_of": v["date"], "checked": None, "auto_run": TODAY}
    out = {"updated": TODAY, "note": "규칙으로 원문 줄을 옮긴 것. 사람 확인 전.", "complexes": list(rows.values())}
    (DATA / "rules_auto.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"자동 추출: {len(rows)}개 단지, {len(found)}개 주제")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
