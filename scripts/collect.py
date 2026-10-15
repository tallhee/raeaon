#!/usr/bin/env python3
"""다른 아파트 단지의 공고를 주제별로 모으는 수집 스크립트.

출처
  1) K-apt 공동주택 입찰공고 (국토교통부 공공데이터 API)
  2) K-apt 공동주택 기본정보 (입주연도·세대수 → 비교 단지 필터)
  3) 청약홈 APT 분양정보 (입주자모집공고 페이지 링크)

표준 라이브러리만 사용합니다. 환경변수 DATA_GO_KR_API_KEY 가 필요합니다
(공공데이터포털에서 위 API들의 활용신청 후 발급되는 '일반 인증키(Decoding)').

결과
  docs/data/notices.json    주제별로 분류된 공고 (누적, id 기준 중복 제거)
  docs/data/complexes.json  단지 기본정보 캐시
  docs/data/presale.json    서울 입주자모집공고 목록
  docs/data/run_status.json 마지막 실행의 출처별 성공/실패 기록
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
DATA = ROOT / "docs" / "data"
DATA.mkdir(parents=True, exist_ok=True)

KEY = os.environ.get("DATA_GO_KR_API_KEY", "").strip()
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(KST)
UA = {"User-Agent": "raeaon-collector/1.0 (+https://github.com/tallhee/raeaon)"}

status: dict[str, dict] = {}


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
    (DATA / name).write_text(
        json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def get_json(url: str, params: dict, tries: int = 3) -> dict:
    qs = urllib.parse.urlencode(params, safe="[]:")
    last: Exception | None = None
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{url}?{qs}", headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8", "replace")
            if text.lstrip().startswith("<"):
                # data.go.kr 은 오류를 XML 로 돌려줄 때가 많다
                msg = re.search(r"<(returnAuthMsg|resultMsg|errMsg)>([^<]+)<", text)
                raise RuntimeError(f"XML 응답: {msg.group(2) if msg else text[:200]}")
            return json.loads(text)
        except (urllib.error.URLError, RuntimeError, json.JSONDecodeError, TimeoutError) as e:
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url} 실패: {last}")


def items_of(body: dict) -> tuple[list[dict], int]:
    """data.go.kr 의 response.body.items(.item) 구조와 odcloud 의 data 구조를 모두 처리."""
    if "data" in body and isinstance(body["data"], list):
        return body["data"], int(body.get("matchCount") or body.get("totalCount") or 0)
    b = body.get("response", body).get("body", body)
    items = b.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if isinstance(items, dict):
        items = [items]
    return items or [], int(b.get("totalCount") or 0)


def pick(d: dict, *cands: str) -> str:
    """API 필드명이 버전마다 조금씩 달라 후보 이름을 순서대로 찾는다."""
    for c in cands:
        if d.get(c) not in (None, ""):
            return str(d[c]).strip()
    low = {k.lower(): v for k, v in d.items()}
    for c in cands:
        if low.get(c.lower()) not in (None, ""):
            return str(low[c.lower()]).strip()
    return ""


def classify(text: str) -> list[str]:
    return [
        key
        for key, t in CONFIG["topics"].items()
        if any(k in text for k in t["keywords"])
    ]


def norm_date(s: str) -> str:
    digits = re.sub(r"\D", "", s or "")
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return s or ""


# ---------------------------------------------------------------- K-apt 입찰공고
def collect_kapt_bids() -> list[dict]:
    url = CONFIG["endpoints"]["kapt_bid"]
    since = (NOW - dt.timedelta(days=CONFIG["lookback_days"])).strftime("%Y%m%d")
    out, page, rows = [], 1, 100
    while True:
        body = get_json(url, {
            "serviceKey": KEY, "pageNo": page, "numOfRows": rows, "_type": "json",
            "searchDate": since, "startDate": since, "endDate": NOW.strftime("%Y%m%d"),
        })
        items, total = items_of(body)
        if not items:
            break
        for it in items:
            title = pick(it, "bidTitle", "bidNm", "pblAncNm", "title", "bidSj")
            topics = classify(title)
            if not topics:
                continue
            bid_no = pick(it, "bidNum", "bidNo", "pblAncNo", "bidSeq")
            out.append({
                "id": f"kapt-bid-{bid_no or abs(hash(title))}",
                "source": "kapt_bid",
                "title": title,
                "topics": topics,
                "complex_code": pick(it, "kaptCode", "aptCode"),
                "complex_name": pick(it, "kaptName", "aptName", "kaptNm"),
                "date": norm_date(pick(it, "bidRegdate", "regDate", "pblAncDe", "bidDate")),
                "deadline": norm_date(pick(it, "bidClosedate", "bidEndDate", "closeDate")),
                "method": pick(it, "bidMethod", "bidKind", "bidType"),
                "url": "https://www.k-apt.go.kr/bid/bidList.do",
                "raw": it,
            })
        if page * rows >= total or page >= 50:
            break
        page += 1
    return out


# ---------------------------------------------------------------- K-apt 기본정보
def enrich_complexes(notices: list[dict], cache: dict) -> dict:
    url = CONFIG["endpoints"]["kapt_basis"]
    codes = {n["complex_code"] for n in notices if n.get("complex_code")} - set(cache)
    for code in sorted(codes):
        try:
            body = get_json(url, {"serviceKey": KEY, "kaptCode": code, "_type": "json"})
            b = body.get("response", body).get("body", body)
            it = b.get("item", b.get("items", {}))
            if isinstance(it, list):
                it = it[0] if it else {}
            addr = pick(it, "kaptAddr", "doroJuso")
            cache[code] = {
                "code": code,
                "name": pick(it, "kaptName"),
                "address": addr,
                "sido": addr.split()[0] if addr else "",
                "sigungu": addr.split()[1] if len(addr.split()) > 1 else "",
                "use_approval": norm_date(pick(it, "kaptUsedate")),
                "households": int(pick(it, "kaptdaCnt", "hoCnt") or 0),
                "dong_count": int(pick(it, "kaptDongCnt") or 0),
            }
        except Exception as e:  # 한 단지 실패로 전체를 멈추지 않는다
            cache[code] = {"code": code, "error": str(e)[:200]}
        time.sleep(0.2)
    return cache


def tag_filters(cx: dict) -> list[str]:
    tags = []
    if not cx or "error" in cx:
        return tags
    year = int((cx.get("use_approval") or "0")[:4] or 0)
    for key, f in CONFIG["filters"].items():
        if f.get("sido") and not cx.get("sido", "").startswith(f["sido"]):
            continue
        if f.get("sigungu") and cx.get("sigungu") not in f["sigungu"]:
            continue
        if f.get("min_use_approval_year") and year < f["min_use_approval_year"]:
            continue
        if f.get("min_households") and cx.get("households", 0) < f["min_households"]:
            continue
        tags.append(key)
    return tags


# ---------------------------------------------------------------- 청약홈
def collect_applyhome() -> list[dict]:
    url = CONFIG["endpoints"]["applyhome_detail"]
    since = (NOW - dt.timedelta(days=30 * CONFIG["applyhome_months_back"])).strftime("%Y-%m-%d")
    out, page, per = [], 1, 100
    while True:
        body = get_json(url, {
            "serviceKey": KEY, "page": page, "perPage": per,
            "cond[SUBSCRPT_AREA_CODE_NM::EQ]": "서울",
            "cond[RCRIT_PBLANC_DE::GTE]": since,
        })
        items, total = items_of(body)
        for it in items:
            out.append({
                "id": f"applyhome-{pick(it, 'PBLANC_NO', 'HOUSE_MANAGE_NO')}",
                "name": pick(it, "HOUSE_NM"),
                "address": pick(it, "HSSPLY_ADRES"),
                "households": int(pick(it, "TOT_SUPLY_HSHLDCO") or 0),
                "notice_date": pick(it, "RCRIT_PBLANC_DE"),
                "move_in": pick(it, "MVN_PREARNGE_YM"),
                "builder": pick(it, "CNSTRCT_ENTRPS_NM"),
                "notice_url": pick(it, "PBLANC_URL"),
                "homepage": pick(it, "HMPG_ADRES"),
            })
        if not items or page * per >= total or page >= 30:
            break
        page += 1
    return out


# ---------------------------------------------------------------- main
def run(name: str, fn):
    try:
        res = fn()
        status[name] = {"ok": True, "count": len(res)}
        return res
    except Exception as e:
        status[name] = {"ok": False, "error": str(e)[:300]}
        print(f"[{name}] 실패: {e}", file=sys.stderr)
        return None


def main() -> int:
    if not KEY:
        print("DATA_GO_KR_API_KEY 가 없습니다. 저장소 Settings → Secrets 에 등록하세요.", file=sys.stderr)
        return 1

    prev = {n["id"]: n for n in load("notices.json", {"items": []})["items"]}
    new = run("kapt_bid", collect_kapt_bids) or []
    for n in new:
        n.setdefault("first_seen", NOW.strftime("%Y-%m-%d"))
        if n["id"] in prev:
            n["first_seen"] = prev[n["id"]].get("first_seen", n["first_seen"])
        prev[n["id"]] = n

    complexes = load("complexes.json", {})
    try:
        complexes = enrich_complexes(list(prev.values()), complexes)
        status["kapt_basis"] = {"ok": True, "count": len(complexes)}
    except Exception as e:
        status["kapt_basis"] = {"ok": False, "error": str(e)[:300]}

    for n in prev.values():
        n["filters"] = tag_filters(complexes.get(n.get("complex_code", ""), {}))

    items = sorted(prev.values(), key=lambda n: n.get("date", ""), reverse=True)
    save("notices.json", {"updated": NOW.isoformat(timespec="minutes"), "items": items})
    save("complexes.json", complexes)

    presale = run("applyhome", collect_applyhome)
    if presale is not None:
        save("presale.json", {"updated": NOW.isoformat(timespec="minutes"), "items": presale})

    save("run_status.json", {"ran_at": NOW.isoformat(timespec="minutes"), "sources": status})
    print(json.dumps(status, ensure_ascii=False, indent=1))
    return 0 if any(s.get("ok") for s in status.values()) else 2


if __name__ == "__main__":
    sys.exit(main())
