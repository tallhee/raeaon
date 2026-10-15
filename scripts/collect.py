#!/usr/bin/env python3
"""K-apt 입찰공고에서 다른 단지의 주제별 공고를 모으는 수집 스크립트.

API 키 없이 K-apt 웹페이지를 그대로 읽습니다.
  1) /bid/bidList.do      서울 지역 입찰공고를 주제 키워드로 검색
  2) /bid/bidDetail.do    공고 상세 (입찰분류, 단지 주소·세대수)
  3) /cmmn/selectKapt.do  단지 사용승인일 (비교 단지 필터용)

결과 (docs/data/)
  notices.json     주제별로 분류된 공고 (누적, 공고번호 기준 중복 제거)
  complexes.json   단지 정보 캐시
  run_status.json  마지막 실행 기록
표준 라이브러리만 사용합니다.
"""
from __future__ import annotations

import datetime as dt
import html
import http.cookiejar
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
K = CONFIG["kapt"]
BASE = K["base"]
DATA = ROOT / "docs" / "data"
DATA.mkdir(parents=True, exist_ok=True)

KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(KST)
TODAY = NOW.strftime("%Y-%m-%d")

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.addheaders = [
    ("User-Agent", "Mozilla/5.0 (raeaon-collector; +https://github.com/tallhee/raeaon)"),
    ("Accept-Language", "ko-KR,ko;q=0.9"),
]


# ---------------------------------------------------------------- utils
def load(name: str, default):
    p = DATA / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default


def save(name: str, obj) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def fetch(path: str, params: dict | None = None, data: dict | None = None, tries: int = 3) -> str:
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    last = None
    for i in range(tries):
        try:
            with opener.open(urllib.request.Request(url, data=body), timeout=40) as r:
                text = r.read().decode("utf-8", "replace")
            time.sleep(K["delay_seconds"])
            return text
        except Exception as e:  # 네트워크 오류는 잠시 쉬고 재시도
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"{path} 요청 실패: {last}")


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def csrf_token() -> str:
    page = fetch("/bid/bidList.do")
    m = re.search(r'name="_csrf"\s+content="([^"]+)"', page) or re.search(r'name="_csrf"\s+value="([^"]+)"', page)
    if not m:
        raise RuntimeError("K-apt 페이지에서 세션 토큰을 찾지 못했습니다 (페이지 구조 변경 가능성)")
    return m.group(1)


# ---------------------------------------------------------------- 목록
ROW_RE = re.compile(r'<tr[^>]*class="notice-row"[^>]*dataid="([^"]+)"[^>]*>(.*?)</tr>', re.S | re.I)
# K-apt 단지코드(A/B + 숫자 8자리)만 단지 상세 조회가 된다. KG2B 등 민간 전자입찰 코드는 제외.
KAPT_CODE = re.compile(r"^[AB]\d{8}$")


def search(keyword: str, start: str, end: str) -> list[dict]:
    out, page = [], 1
    while True:
        h = fetch("/bid/bidList.do", {
            "pageSelect": K["page_size"], "searchBidGb": "bid_gb_1", "bidTitle": keyword,
            "searchDateGb": "reg", "dateStart": start, "dateEnd": end,
            "pageNo": page, "type": "3", "bidArea": K["bid_area"],
        })
        rows = ROW_RE.findall(h)
        for bid_num, inner in rows:
            cells = [text_of(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", inner, re.S)]
            code = re.search(r"initList\(\s*4\s*,\s*'([A-Z0-9]+)'", inner)
            if len(cells) < 8:
                continue
            out.append({
                "bid_num": bid_num,
                "channel": cells[1],
                "award": cells[2],
                "title": re.sub(r"^\[[^\]]+\]\s*", "", cells[3]),
                "deadline": cells[4][:10],
                "state": cells[5],
                "complex_name": cells[6],
                "date": cells[7][:10],
                "complex_code": code.group(1) if code else "",
            })
        if len(rows) < int(K["page_size"]) or page >= 20:
            break
        page += 1
    return out


def classify(title: str) -> list[str]:
    hits = []
    for key, t in CONFIG["topics"].items():
        if any(k in title for k in t["keywords"]) and not any(x in title for x in t.get("exclude", [])):
            hits.append(key)
    return hits


# ---------------------------------------------------------------- 상세·단지
def detail(bid_num: str) -> dict:
    h = fetch("/bid/bidDetail.do", {"bidNum": bid_num, "type": "3"})
    info: dict = {}
    for th, td in re.findall(r"<th[^>]*>((?:(?!</?th).)*?)</th>\s*<td[^>]*>((?:(?!</?td).)*?)</td>", h, re.S):
        k = text_of(th)
        if k in ("입찰분류", "입찰종류", "입찰방법", "현장설명일시"):
            info[k] = text_of(td)
    # 단지 표: 헤더 행(단지명…세대수) 다음 행
    m = re.search(r"세대수\s*</th>\s*</tr>\s*<tr>(.*?)</tr>", h, re.S)
    if m:
        tds = [text_of(c) for c in re.findall(r"<td[^>]*>(.*?)(?=<td|</tr>|$)", m.group(1), re.S)]
        tds = [re.sub(r"</?td>", "", t).strip() for t in tds]
        if len(tds) >= 6:
            info["address"] = tds[1]
            hh = int(re.sub(r"\D", "", tds[5]) or 0)
            if hh:
                info["households"] = hh
            info["dong_count"] = int(re.sub(r"\D", "", tds[4]) or 0)
    return info


def complex_info(code: str, token: str) -> dict:
    h = fetch("/cmmn/selectKapt.do", data={
        "go_url": "/kaptinfo/openkaptinfo.do", "kapt_code": code,
        "bjd_code": "", "search_date": "", "kaptDuty": "ALL", "_csrf": token,
    })
    t = text_of(h)
    ua = re.search(r"사용승인일\(준공일\)\s*(\d{4}-\d{2}-\d{2})", t)
    addr = re.search(r"법정동주소\s*(\S+\s+\S+)", t)
    return {
        "use_approval": ua.group(1) if ua else "",
        "legal_address": addr.group(1) if addr else "",
    }


def region(addr: str) -> tuple[str, str]:
    parts = (addr or "").split()
    sido = parts[0] if parts else ""
    sigungu = next((p for p in parts[1:3] if p.endswith(("구", "군", "시"))), "")
    return sido, sigungu


def norm_name(name: str) -> str:
    return re.sub(r"(아파트|\s|\(.*?\))", "", name or "")


def tag_filters(cx: dict) -> list[str]:
    tags = []
    year = int((cx.get("use_approval") or "0")[:4] or 0)
    for key, f in CONFIG["filters"].items():
        if f.get("sido") and not cx.get("sido", "").startswith(f["sido"]):
            continue
        if f.get("sigungu") and cx.get("sigungu") not in f["sigungu"]:
            continue
        if f.get("min_use_approval_year") and year < f["min_use_approval_year"]:
            continue
        if f.get("min_households") and (cx.get("households") or 0) < f["min_households"]:
            continue
        tags.append(key)
    return tags


# ---------------------------------------------------------------- main
def main() -> int:
    status: dict = {"ran_at": NOW.isoformat(timespec="minutes"), "steps": {}}
    prev = {n["id"]: n for n in load("notices.json", {"items": []})["items"]}
    complexes = load("complexes.json", {})

    days = K["lookback_days"] if prev else K["first_run_lookback_days"]
    start = (NOW - dt.timedelta(days=days)).strftime("%Y-%m-%d")

    # 1) 키워드별 검색
    found: dict[str, dict] = {}
    errors = []
    keywords = sorted({k for t in CONFIG["topics"].values() for k in t["keywords"]})
    for kw in keywords:
        try:
            for r in search(kw, start, TODAY):
                found.setdefault(r["bid_num"], r)
        except Exception as e:
            errors.append(f"{kw}: {e}")
    matched = {b: r for b, r in found.items() if classify(r["title"])}
    status["steps"]["search"] = {"ok": not errors or bool(found), "keywords": len(keywords),
                                 "found": len(found), "matched": len(matched), "errors": errors[:5]}

    # 2) 새 공고만 상세 조회
    new_count, detail_err = 0, 0
    for bid, r in matched.items():
        nid = f"kapt-{bid}"
        old = prev.get(nid, {})
        item = {**old, **r, "id": nid, "source": "kapt_bid", "topics": classify(r["title"]),
                "url": f"{BASE}/bid/bidDetail.do?bidNum={urllib.parse.quote(bid)}&type=3",
                "first_seen": old.get("first_seen", TODAY)}
        if "category" not in old:
            try:
                d = detail(bid)
                item["category"] = d.get("입찰분류", "")
                item["kind"] = d.get("입찰종류", "")
                item["is_works"] = "공사" in item["category"]
                code = r["complex_code"]
                if code:
                    cx = complexes.setdefault(code, {"code": code, "kapt": bool(KAPT_CODE.match(code))})
                    cx["name"] = r["complex_name"]
                    if d.get("address"):
                        cx["address"] = d["address"]
                        cx["sido"], cx["sigungu"] = region(d["address"])
                    if d.get("households"):
                        cx["households"] = d["households"]
                        cx["dong_count"] = d.get("dong_count", 0)
                new_count += 1
            except Exception:
                detail_err += 1
        prev[nid] = item
    status["steps"]["detail"] = {"ok": detail_err == 0, "new": new_count, "errors": detail_err}

    # 3) 사용승인일이 없는 단지만 조회
    need = [c for c, cx in complexes.items()
            if KAPT_CODE.match(c) and not cx.get("use_approval") and not cx.get("ua_error")]
    ua_ok = ua_err = 0
    if need:
        try:
            token = csrf_token()
            for code in need:
                try:
                    ci = complex_info(code, token)
                    complexes[code].update({k: v for k, v in ci.items() if v})
                    if not complexes[code].get("sido") and ci.get("legal_address"):
                        complexes[code]["sido"], complexes[code]["sigungu"] = region(ci["legal_address"])
                    if ci["use_approval"]:
                        ua_ok += 1
                    else:
                        complexes[code]["ua_error"] = "사용승인일 없음"
                        ua_err += 1
                except Exception as e:
                    ua_err += 1
                    status.setdefault("complex_errors", []).append(f"{code}: {str(e)[:120]}")
        except Exception as e:
            status["steps"]["complex"] = {"ok": False, "error": str(e)[:200]}
    status["steps"].setdefault("complex", {"ok": ua_err == 0, "updated": ua_ok, "errors": ua_err})

    # 4) 같은 단지명의 정보 공유 → 수동 보정 → 필터 태그
    by_name: dict[str, dict] = {}
    for cx in complexes.values():
        if cx.get("use_approval") or cx.get("households"):
            by_name.setdefault(norm_name(cx.get("name", "")), {}).update(
                {k: cx[k] for k in ("use_approval", "households", "sido", "sigungu") if cx.get(k)})
    overrides = {norm_name(k): v for k, v in CONFIG.get("complex_overrides", {}).items() if not k.startswith("_")}
    for cx in complexes.values():
        key = norm_name(cx.get("name", ""))
        for k, v in by_name.get(key, {}).items():
            cx.setdefault(k, v)
        cx.update(overrides.get(key, {}))
    for n in prev.values():
        cx = complexes.get(n.get("complex_code", ""), {})
        n["filters"] = tag_filters(cx)
        n["households"] = cx.get("households")
        n["use_approval"] = cx.get("use_approval", "")
        n["sigungu"] = cx.get("sigungu", "")
    items = sorted(prev.values(), key=lambda n: (n.get("date", ""), n["id"]), reverse=True)
    save("notices.json", {"updated": NOW.isoformat(timespec="minutes"), "items": items})
    save("complexes.json", complexes)
    status["totals"] = {"notices": len(items), "complexes": len(complexes)}
    save("run_status.json", status)

    print(json.dumps(status, ensure_ascii=False, indent=1))
    return 0 if found or not errors else 2


if __name__ == "__main__":
    sys.exit(main())
