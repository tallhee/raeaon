#!/usr/bin/env python3
"""서울시 공동주택마당(openapt)에서 단지별 입주자대표회의 회의결과 공고를 모아
첨부파일(PDF·이미지·한글) 글자를 뽑고, 안건 단위로 주제를 붙이는 수집 스크립트.

필요한 프로그램 (GitHub Actions 에서 설치): tesseract-ocr(+kor), poppler-utils, pyhwp(선택)

결과 (docs/data/)
  minutes.json            단지·회의별 안건과 주제 (사이트가 읽는 파일)
  minutes_text/<code>/<nttId>.txt   첨부에서 뽑은 전체 글자 (검토용)
  minutes_status.json     마지막 실행 기록
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import http.cookiejar
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "openapt.json").read_text(encoding="utf-8"))
DATA = ROOT / "docs" / "data"
TEXT_DIR = DATA / "minutes_text"
B = "https://openapt.seoul.go.kr"
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(KST)
DEADLINE = time.monotonic() + 60 * CFG["time_budget_minutes"]


PARSER_VERSION = 2


class Stop(BaseException):
    pass


def T(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def load(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- 사이트 세션
class Session:
    def __init__(self, code: str):
        self.code = code
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.op.addheaders = [("User-Agent", "Mozilla/5.0 (raeaon; +https://github.com/tallhee/raeaon) Chrome/124"),
                              ("Referer", f"{B}/openApt/index.do?aptCode={code}")]
        idx = self.get(f"/openApt/index.do?aptCode={code}").decode("utf-8", "replace")
        m = re.search(r'name="csrf-token" content="([^"]+)"', idx)
        if not m:
            raise RuntimeError("단지홈에서 보안 토큰을 찾지 못함 (사이트 구조 변경 가능성)")
        self.token = m.group(1)

    def _open(self, url, data=None, timeout=40):
        if time.monotonic() > DEADLINE:
            raise Stop("시간 예산 소진 — 다음 실행에서 이어서 수집")
        last = None
        for i in range(2):
            try:
                with self.op.open(url, data, timeout=timeout) as r:
                    body = r.read()
                time.sleep(CFG["delay_seconds"])
                return body
            except Exception as e:
                last = e
                time.sleep(3 * (i + 1))
        raise RuntimeError(f"요청 실패 {url[:80]}: {last}")

    def get(self, path: str) -> bytes:
        return self._open(B + path)

    def post(self, path: str, fields: dict) -> str:
        data = urllib.parse.urlencode({**fields, "csrfToken": self.token}).encode()
        return self._open(B + path, data).decode("utf-8", "replace")

    def board_page(self, bbs: str, page: int) -> str:
        b = CFG["boards"][bbs]
        return self.post("/boardForm/selectBoardList.do", {
            "aptCode": self.code, "returnUrl": b["list"], "bbsCommCode": bbs,
            "query": "openAptMngCommonBoard.openAptMngBoardList", "pageIndex": page})

    def detail(self, bbs: str, ntt: str) -> str:
        return self.post("/boardForm/boardDetail.do", {
            "aptCode": self.code, "searchValue": f"aptCode:{self.code}|bbsCommCode:{bbs}|nttId:{ntt}",
            "query": "openAptMngCommonBoard.openAptMngBoardDetail", "returnUrl": CFG["boards"][bbs]["detail"]})


def parse_list(h: str) -> list[dict]:
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        ntt = re.search(r"onDetail\(\s*'?(\d+)", tr)
        if not ntt:
            continue
        tds = {}
        for cls, td in re.findall(r'<td[^>]*class="([^"]*)"[^>]*>(.*?)</td>', tr, re.S):
            tds[cls.split()[0]] = T(td)
        rows.append({
            "nttId": ntt.group(1),
            "category": tds.get("tdState", ""),
            "title": tds.get("tdTitle", ""),
            "date": (re.search(r"\d{4}-\d{2}-\d{2}", tds.get("tdDate", "")) or [""])[0] if tds.get("tdDate") else "",
            "first_file": re.findall(r"'(FILE_\d+)'\s*,\s*'(\d+)'", tr)[:1],
        })
    return rows


def parse_detail(h: str) -> tuple[list[dict], str]:
    files, seen = [], set()
    for fid, sn, name in re.findall(
            r"FileDown\.do\?atchFileId=(FILE_\d+)&(?:amp;)?fileSn=(\d+)['\"]?\s*,\s*'([^']+)'", h):
        if (fid, sn) not in seen:
            seen.add((fid, sn))
            files.append({"atchFileId": fid, "fileSn": sn, "name": html.unescape(name)})
    if not files:  # 다른 형태의 다운로드 링크
        for fid, sn in re.findall(r"(FILE_\d+)['\"]?\s*,\s*['\"]?(\d+)", h):
            if (fid, sn) not in seen:
                seen.add((fid, sn))
                files.append({"atchFileId": fid, "fileSn": sn, "name": f"첨부{len(files)+1}"})
    # 본문(글내용): 글자 + 본문에 넣은 이미지 (원베일리처럼 공고를 본문 그림으로 올리는 단지)
    body = ""
    m = re.search(r'<div[^>]*class="[^"]*readContent[^"]*"[^>]*>(.*?)</div>\s*</div>\s*<!--\s*/readBbsWrap', h, re.S) \
        or re.search(r'<div[^>]*class="[^"]*readContent[^"]*"[^>]*>(.*?)</div>', h, re.S)
    if m:
        body = T(m.group(1))
        for k, src in enumerate(re.findall(r'<img[^>]+src="([^"]+)"', m.group(1))):
            src = html.unescape(src)
            if src.startswith("data:"):
                continue
            url = src if src.startswith("http") else B + src
            files.append({"url": url, "name": f"본문이미지{k+1}.jpg", "inline": True})
    return files, body


# ---------------------------------------------------------------- 글자 뽑기
def run(cmd: list[str], timeout=180) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def ocr_image(path: Path) -> str:
    return run(["tesseract", str(path), "-", "-l", "kor+eng", "--psm", "6"])


def extract(path: Path, name: str, max_pages: int = 20) -> tuple[str, str]:
    kind = run(["file", "-b", str(path)]).strip()
    low = name.lower()
    if "PDF" in kind:
        txt = run(["pdftotext", "-layout", str(path), "-"])
        if len(txt.strip()) >= 150:
            return txt, "pdf-text"
        with tempfile.TemporaryDirectory() as td:  # 스캔 PDF → 쪽마다 그림으로 바꿔 글자 인식
            run(["pdftoppm", "-r", "200", "-l", str(max_pages), "-png", str(path), f"{td}/p"], timeout=60 + 10 * max_pages)
            pages = sorted(Path(td).glob("p*.png"))
            return "\n\n".join(ocr_image(p) for p in pages), f"pdf-ocr({len(pages)}쪽)"
    if any(k in kind for k in ("image", "JPEG", "PNG", "TIFF", "GIF")):
        return ocr_image(path), "image-ocr"
    if low.endswith(".docx"):
        try:
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
                return html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", xml))), "docx"
        except Exception:
            return "", "docx-fail"
    if low.endswith(".hwpx") or ("Zip" in kind and low.endswith(".hwpx")):
        try:
            with zipfile.ZipFile(path) as z:
                parts = [n for n in z.namelist() if n.startswith("Contents/section")]
                return "\n".join(html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"</hp:p>", "\n", z.read(n).decode("utf-8", "replace"))))
                                 for n in sorted(parts)), "hwpx"
        except Exception:
            return "", "hwpx-fail"
    if low.endswith(".hwp") or "Hangul" in kind or "Composite Document" in kind:
        if shutil.which("hwp5txt"):
            return run(["hwp5txt", str(path)]), "hwp"
        return "", "hwp-no-tool"
    return "", f"skip({kind[:30]})"


# ---------------------------------------------------------------- 안건 나누기·주제
AGENDA_HEAD = re.compile(
    r"^\s*(?:제\s*\d+\s*호\s*(?:의안|안건)?|안건\s*\d+|\d{1,2}\s*[\.\)]\s*(?=\S)|[①-⑳])")
AGENDA_TAIL = re.compile(r"(?:의\s*건|\s건|승인\s*건)\s*(?:[\[(][^\])]*[\])])?\s*$")
VOTE = re.compile(r"(찬\s*성|반\s*대|기\s*권|보\s*류|가\s*결|부\s*결|원안\s*(?:가결|의결)|승인|의결)")


def clean(txt: str) -> str:
    lines = []
    for ln in txt.splitlines():
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if not ln:
            continue
        hangul = len(re.findall(r"[가-힣]", ln))
        if hangul < 2 and not re.search(r"\d", ln):  # 글자 인식 찌꺼기
            continue
        lines.append(ln)
    return "\n".join(lines)


GENERIC_HEAD = re.compile(r"의결\s*주문|안건\s*상정\s*및\s*토의|회의\s*개요|성원\s*보고|참석\s*현황|개회\s*선언|폐회")


def is_head(ln: str) -> bool:
    if GENERIC_HEAD.search(ln) or len(re.findall(r"[가-힣]", ln)) < 6:  # 목차·끊긴 줄은 안건 머리로 보지 않음
        return False
    if AGENDA_HEAD.match(ln) and ("건" in ln or "의안" in ln or "안건" in ln or VOTE.search(ln)):
        return True
    return len(ln) <= 90 and bool(AGENDA_TAIL.search(ln))


def split_agenda(txt: str) -> list[str]:
    """안건 머리줄(번호 + '…의 건')마다 자른다. 첫 안건 앞의 공고 머리말은 버린다."""
    chunks, cur, started = [], [], False
    for ln in txt.splitlines():
        if is_head(ln):
            if started and cur:
                chunks.append("\n".join(cur))
            cur, started = [ln], True
        elif started:
            cur.append(ln)
    if started and cur:
        chunks.append("\n".join(cur))
    return [c for c in chunks if len(c) > 15]


def topics_of(text: str) -> list[str]:
    return [k for k, t in CFG["topics"].items() if any(w in text for w in t["keywords"])]


def body_topics(text: str) -> list[str]:
    """본문으로만 붙이는 주제. head_only 주제는 강한 표현(body_keywords)이 있을 때만."""
    out = []
    for k, t in CFG["topics"].items():
        words = t.get("body_keywords", []) if t.get("head_only") else t["keywords"]
        if any(w in text for w in words):
            out.append(k)
    return out


def votes_of(text: str) -> str:
    m = re.search(r"[\[(]?\s*찬\s*성[^\n\]\)]{0,40}[\])]?", text)
    if m:
        return re.sub(r"\s+", " ", m.group(0)).strip(" []()")
    m = re.search(r"(원안\s*가결|가결|부결|원안\s*의결|승인\s*의결|보류)", text)
    return m.group(1) if m else ""


def analyze(txt: str) -> list[dict]:
    out = []
    for c in split_agenda(clean(txt)):
        first = c.splitlines()[0][:120]
        tp = topics_of(first) or body_topics(c)  # 안건 제목에 주제어가 있으면 그것만 쓴다 (없어도 안건은 남김)
        out.append({"head": first, "text": c[:900], "topics": tp, "votes": votes_of(c)})
    return out


# ---------------------------------------------------------------- 단지 찾기 (이름·지역 → aptCode)
CX_CACHE = DATA / "openapt_complexes.json"
INFO_VERSION = 3  # 기본정보 해석 방식을 바꾸면 올린다 (캐시된 단지를 다시 확인)
REGION_PREFIX = re.compile(r"^(잠실|서초|반포|송파|청담|개포|강남|강동|고덕|문정|방배|둔촌|가락)")


class Portal(Session):
    """공동주택마당 포털의 단지검색·기본정보 (단지홈 없이)."""

    def __init__(self):  # noqa: D401 - Session.__init__ 대신 포털 페이지에서 토큰을 받는다
        self.code = ""
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        page = "/commonPortal/programLink.do?jspNm=/portal/aMenu/aptInfo/aptInfo.open"
        self.op.addheaders = [("User-Agent", "Mozilla/5.0 (raeaon) Chrome/124"), ("Referer", B + page)]
        m = re.search(r'name="csrf-token" content="([^"]+)"', self.get(page).decode("utf-8", "replace"))
        if not m:
            raise RuntimeError("단지검색 페이지에서 보안 토큰을 찾지 못함")
        self.token = m.group(1)

    def search(self, name: str = "", gu: str = "", dong: str = "") -> list[dict]:
        h = self.post("/commonPortal/select.do", {"query": "aptInfo.selectAptMapDataList",
                                                  "searchValue": f"aptNm:{name}|gu:{gu}|dong:{dong}",
                                                  "returnUrl": "portal/aMenu/aptInfo/aptInfoSearch"})
        out = []
        for code, dt, dd in re.findall(r'<dl id="dlApt(A\d{8})".*?<dt>(.*?)</dt>\s*<dd>(.*?)(?:<div|</dd>)', h, re.S):
            hh = re.search(r"\(([\d,]+)세대\)", dd)
            out.append({"code": code, "name": T(dt), "road": T(re.sub(r"\([\d,]+세대\)", "", dd)),
                        "households": int(hh.group(1).replace(",", "")) if hh else 0})
        return out

    def info(self, code: str) -> dict:
        t = T(self.post("/commonPortal/select.do", {"query": "aptInfo.selectAptInfoDetail",
                                                    "searchValue": f"aptCode:{code}",
                                                    "returnUrl": "portal/aMenu/aptInfo/detailComponent/aptInfoBasic"}))
        ua = re.search(r"사용승인일\s*(\d{4})[-.](\d{2})[-.](\d{2})", t)
        hh = re.search(r"세대수\s*(\d[\d,]*)\s*세대", t)
        addr = re.search(r"주소\s*(서울\S*\s+(\S+구)\s+(\S+동))", t)
        return {"use_approval": "-".join(ua.groups()) if ua else "",
                "households": int(hh.group(1).replace(",", "")) if hh else 0,
                "sigungu": addr.group(2) if addr else "", "dong": addr.group(3) if addr else ""}


BRANDS = ["래미안", "힐스테이트", "롯데캐슬", "시그니처", "이편한세상", "자이", "아이파크", "푸르지오", "더샵",
          "디에이치", "아크로", "르엘", "센트레빌", "호반써밋", "SK뷰", "에스케이뷰", "포레나", "그랑자이", "리더스원"]


def name_tokens(name: str) -> list[str]:
    n = norm(name).replace("e편한세상", "이편한세상")
    toks = []
    for b in sorted(BRANDS, key=len, reverse=True):
        if b in n:
            toks.append(b)
            n = n.replace(b, " ")
    toks += [w for w in n.split() if len(w) >= 2]
    return toks


def norm(n: str) -> str:
    return re.sub(r"(아파트|\s|\(.*?\))", "", n or "")


def auto_groups(cx: dict) -> list[str]:
    g = set(cx.get("groups") or [])
    year = int((cx.get("use_approval") or "0")[:4] or 0)
    for key, f in CFG.get("auto_groups", {}).items():
        if f.get("min_year") and year < f["min_year"]:
            continue
        if f.get("sigungu") and cx.get("sigungu") not in f["sigungu"]:
            continue
        if f.get("min_households") and (cx.get("households") or 0) < f["min_households"]:
            continue
        g.add(key)
    return sorted(g)


def region_of(cx: dict) -> str:
    n = norm(cx.get("name", ""))
    if cx.get("via") == "gu_scan":
        return next((r["label"] for r in CFG.get("display", {}).get("regions", []) if r.get("via") == "gu_scan"), "기타")
    for r in CFG.get("display", {}).get("regions", []):
        if r.get("via"):
            continue
        if cx.get("dong") and cx["dong"] in r.get("dong", []):
            return r["label"]
        if cx.get("sigungu") and cx["sigungu"] in r.get("sigungu", []) and not r.get("dong"):
            return r["label"]
        if any(k in n for k in r.get("name", [])):
            return r["label"]
        if not (r.get("dong") or r.get("sigungu") or r.get("name")):
            return r["label"]
    return "기타"


def resolve_complexes(status: dict) -> list[dict]:
    """config 의 단지 + 이름·지역으로 찾은 단지. 찾은 결과는 캐시해 매번 다시 찾지 않는다."""
    cache = load(CX_CACHE, {"by_code": {}, "names": {}, "areas": {}})
    tg = CFG.get("targets", {})
    by_code = cache["by_code"]
    log = status.setdefault("resolve", {"found": [], "not_found": [], "ambiguous": []})
    try:
        portal = None
        today = NOW.strftime("%Y-%m-%d")

        def P():
            nonlocal portal
            portal = portal or Portal()
            return portal

        def detail(code: str, base: dict) -> dict:
            cx = by_code.setdefault(code, {"code": code})
            cx.update({k: v for k, v in base.items() if v})
            if cx.get("info_v") != INFO_VERSION:
                cx.update({k: v for k, v in P().info(code).items() if v})
                cx["info_checked"], cx["info_v"] = today, INFO_VERSION
            return cx

        for name in tg.get("names", []):
          try:
            if name in cache["names"]:
                code = cache["names"][name]
                if by_code.get(code, {}).get("info_v") != INFO_VERSION:
                    detail(code, {})
                continue
            exact = []
            variants = [name, name.replace("e편한세상", "이편한세상"), REGION_PREFIX.sub("", norm(name))]
            for q in dict.fromkeys(v for v in variants if len(v) >= 3):
                res = P().search(name=q)
                exact = [r for r in res if norm(r["name"]) == norm(q)] or \
                        [r for r in res if norm(q) in norm(r["name"])]
                if exact:
                    break
            if not exact:  # 단어 순서가 다른 경우: 브랜드·지명 조각으로 찾아 모든 조각이 들어간 단지
                toks = name_tokens(name)
                for q in sorted(toks, key=len, reverse=True)[:2]:
                    res = P().search(name=q)
                    exact = [r for r in res if all(t in norm(r["name"]).replace("e편한", "이편한") for t in toks)]
                    if exact:
                        break
            if not exact:
                log["not_found"].append(name)
                continue
            best = max(exact, key=lambda r: r["households"])
            if len(exact) > 1:
                log["ambiguous"].append(f"{name} → {best['name']}({best['households']}세대) 외 {len(exact)-1}곳")
            detail(best["code"], {"name": best["name"], "road": best["road"], "households": best["households"]})
            cache["names"][name] = best["code"]
            log["found"].append(f"{name} → {best['code']}")
          except Stop:
            raise
          except Exception as e:
            log.setdefault("errors", []).append(f"{name}: {str(e)[:120]}")

        for a in tg.get("areas", []):
          try:
              key = a.get("label") or a["area"]
              prev_a = cache["areas"].get(key, {})
              if prev_a.get("v") == INFO_VERSION and prev_a.get("checked", "") > (NOW - dt.timedelta(days=30)).strftime("%Y-%m-%d"):
                  continue  # 지역 검색은 한 달에 한 번
              parts = a["area"].split()
              gu, dong = parts[0], (parts[1] if len(parts) > 1 else "")
              codes = []
              for r in P().search(gu=gu, dong=dong):
                  if a.get("min_households") and r["households"] and r["households"] < a["min_households"]:
                      continue  # 세대수 조건은 목록에서 바로 거른다 (기본정보 조회를 줄임)
                  cx = detail(r["code"], {"name": r["name"], "road": r["road"], "households": r["households"],
                                          "sigungu": gu, "dong": dong})
                  year = int((cx.get("use_approval") or "0")[:4] or 0)
                  if a.get("min_year") and year < a["min_year"]:
                      continue
                  if a.get("min_households") and (cx.get("households") or 0) < a["min_households"]:
                      continue
                  codes.append(r["code"])
              if a.get("top"):  # 구 단위: 조건에 맞는 단지 중 세대수 큰 순으로 몇 곳만
                  codes = sorted(codes, key=lambda c: -(by_code.get(c, {}).get("households") or 0))[:a["top"]]
              cache["areas"][key] = {"checked": today, "codes": codes, "label": a.get("label", key), "v": INFO_VERSION}
              log["found"].append(f"{key}: {len(codes)}곳")
          except Stop:
            raise
          except Exception as e:
            log.setdefault("errors", []).append(f"{a.get('area')}: {str(e)[:120]}")
        gs = tg.get("gu_scan")
        if gs:
            month_ago = (NOW - dt.timedelta(days=30)).strftime("%Y-%m-%d")
            gcache = cache.setdefault("gus", {})
            for gu in gs.get("gus", []):
                try:
                    prev_g = gcache.get(gu, {})
                    if prev_g.get("v") == INFO_VERSION and prev_g.get("checked", "") > month_ago and prev_g.get("complete"):
                        continue
                    res = [r for r in P().search(gu=gu) if r["households"] >= gs.get("min_households", 1000)]
                    # 2020년 이후 단지는 대부분 새 코드(A10…)라 그쪽만 기본정보를 확인해 조회를 줄인다
                    res = [r for r in res if r["code"].startswith("A10")]
                    picked = []
                    for r in sorted(res, key=lambda r: -r["households"]):
                        cx = detail(r["code"], {"name": r["name"], "road": r["road"], "households": r["households"]})
                        if int((cx.get("use_approval") or "0")[:4] or 0) >= gs.get("min_year", 2020):
                            picked.append(r["code"])
                        if len(picked) >= gs.get("top_per_gu", 3):
                            break
                    gcache[gu] = {"checked": today, "codes": picked, "v": INFO_VERSION, "complete": True}
                    log["found"].append(f"{gu}: {len(picked)}곳")
                except Stop:
                    raise
                except Exception as e:
                    log.setdefault("errors", []).append(f"{gu}: {str(e)[:120]}")
    except Stop:
        raise
    except Exception as e:
        log.setdefault("errors", []).append(str(e)[:200])
    finally:
        save(CX_CACHE, cache)

    for cx in CFG["complexes"]:
        if by_code.get(cx["code"], {}).get("info_v") != INFO_VERSION:
            try:
                portal = portal or Portal()
                by_code.setdefault(cx["code"], {"code": cx["code"]}).update(
                    {k: v for k, v in portal.info(cx["code"]).items() if v} | {"info_v": INFO_VERSION})
            except Stop:
                raise
            except Exception:
                pass
    save(CX_CACHE, cache)
    out, seen = [], set()
    for cx in CFG["complexes"]:
        merged = {**by_code.get(cx["code"], {}), **cx}
        out.append(merged)
        seen.add(cx["code"])
    area_keys = {a.get("label") or a["area"] for a in tg.get("areas", [])}
    name_keys = set(tg.get("names", []))
    wanted = [v for k, v in cache["names"].items() if k in name_keys] + \
             [c for k, a in cache["areas"].items() if k in area_keys for c in a.get("codes", [])]
    gu_codes = {c for g in cache.get("gus", {}).values() for c in g.get("codes", [])}
    wanted += [c for c in gu_codes if c not in wanted]
    for code in wanted:
        if code in seen or code not in by_code:
            continue
        seen.add(code)
        out.append({**by_code[code], **({"via": "gu_scan"} if code in gu_codes and code not in
                                        {cache["names"][k] for k in name_keys if k in cache["names"]} else {})})
    pinned = {norm(x) for x in CFG.get("display", {}).get("pinned", [])}
    for cx in out:
        cx["groups"] = auto_groups(cx)
        cx["region"] = region_of(cx)
        cx["pinned"] = bool(cx.get("home")) or any(p and (p in norm(cx.get("name", "")) or norm(cx.get("name", "")) in p)
                                                    for p in pinned)
    return out


# ---------------------------------------------------------------- main
DA = CFG.get("doc_analysis", {})
KEY_PAT = re.compile("|".join(DA.get("key_patterns", ["$^"])))


def doc_snippets(txt: str) -> list[dict]:
    """공개자료: 주제어·핵심 표현이 있는 줄을 앞뒤 한 줄과 함께 뽑는다."""
    lines = clean(txt).splitlines()
    out, used = [], set()
    for i, ln in enumerate(lines):
        tp = topics_of(ln)
        key = bool(KEY_PAT.search(ln))
        if not (tp or key) or i in used:
            continue
        lo, hi = max(0, i - 1), min(len(lines), i + 2)
        used.update(range(lo, hi))
        chunk = "\n".join(lines[lo:hi])
        out.append({"text": chunk[:500], "topics": topics_of(chunk), "key": key})
    out.sort(key=lambda x: (not x["key"], -len(x["topics"])))
    return out[:DA.get("max_snippets", 14)]


def wanted(row: dict, board: dict | None = None) -> bool:
    if board and board.get("kind") == "doc":
        return True
    s = row["category"] + " " + row["title"]
    f = CFG["post_filter"]
    return any(w in s for w in f["include"]) and not any(w in s for w in f["exclude"])


# ---------------------------------------------------------------- 자주 나온 안건 주제어
STOP = set("""건 의 및 등 안 안건 의안 검토 승인 의결 추인 심의 재심의 결정 보고 요청 변경 시행 진행 관련 따른 위한 대한
관한 사항 기타 내용 결과 공고 회의 입주자대표회의 입대의 정기 임시 차 호 제 년 년도 월 일 가결 부결 원안 동의 찬성 반대 기권
교체 신청 세대 입주자대표회 입주민 구성 보수 시설 구매 긴급 지원 가입 공동주택 이용 점검 도입 지하 의결함 개설 일부 조치
주변 서비스 제안 만료 만기 사업자 내부 외부 시스템 행사 직원 선출 이사 공용부 용역 입찰 규정 개정 청소 유지 보고서 확정 연장
비용 금액 기간 신규 추가 재 사항의 위원 위원회 대표 구성원 동대표 회장 감사 총무 소위원회 분과 분과위원회
여부 방안 계획 운영 관리 설치 선정 계약 실시 사용 지급 부과 구입 추진 처리 개선 조정 체결 마련 운영의 보류 상정 협의 논의 검토의
건의 건으로 위해 대하여 따라 해당 인한 통한 각 및 또는 우리 단지 아파트 업체 공사 업무 집행""".split())
PARTICLE = re.compile(r"(으로|에서|에게|로서|으로써|의|을|를|은|는|이|가|에|와|과|로|도|만)$")


def head_terms(head: str) -> set[str]:
    h = re.sub(r"^[\s\W\d]*(제\s*\d+\s*호\s*(의안|안건)?|안\s*건\s*\d*|\d+\s*[\.\)]|[①-⑳])\s*[:：]?", "", head)
    h = re.sub(r"[\[(（【].*?[\])）】]", " ", h)  # 괄호 속 (찬반·업체명 등)
    toks = []
    for w in re.split(r"[^가-힣A-Za-z]+", h):
        w = PARTICLE.sub("", w)
        if len(w) >= 2 and re.fullmatch(r"[가-힣]+", w) and w not in STOP:
            toks.append(w)
    terms = set(toks)
    terms.update(f"{a} {b}" for a, b in zip(toks, toks[1:]))
    return terms


def term_stats(items: dict, complexes: list[dict]) -> list[dict]:
    home = {c["name"] for c in complexes if c.get("home")}
    by: dict[str, dict] = {}
    for it in items.values():
        if it.get("kind") == "doc" or it.get("status") != "done":
            continue
        for a in it.get("agenda", []):
            for t in head_terms(a["head"]):
                d = by.setdefault(t, {"term": t, "complexes": set(), "count": 0, "first": "9999", "first_cx": ""})
                d["complexes"].add(it["complex"])
                d["count"] += 1
                if it.get("date") and it["date"] < d["first"]:
                    d["first"], d["first_cx"] = it["date"], it["complex"]
    min_cx = CFG.get("term_filter", {}).get("min_complexes", 3)
    out = []
    for d in by.values():
        n = len(d["complexes"])
        if n < min_cx:
            continue
        out.append({"term": d["term"], "n": n, "count": d["count"], "first": d["first"], "first_cx": d["first_cx"],
                    "home": bool(home & d["complexes"])})
    # 두 단어 묶음이 한 단어와 거의 같은 단지에서만 나오면 한 단어 쪽을 남기지 않고 묶음을 우선
    out.sort(key=lambda x: (-x["n"], -x["count"]))
    keep, seen_words = [], {}
    for x in out:
        if " " in x["term"]:
            keep.append(x)
            for w in x["term"].split():
                seen_words[w] = max(seen_words.get(w, 0), x["n"])
    for x in out:
        if " " not in x["term"] and seen_words.get(x["term"], 0) < x["n"] * 0.8:
            keep.append(x)
    keep.sort(key=lambda x: (-x["n"], -x["count"]))
    return keep[:CFG.get("term_filter", {}).get("max_terms", 80)]


def apply_analysis(it: dict, full: str) -> None:
    if it.get("kind") == "doc":
        it["snips"] = doc_snippets(full)
        it["agenda"] = []
        it["topics"] = sorted({t for x in it["snips"] for t in x["topics"]})
    else:
        it["agenda"] = analyze(full)
        it["topics"] = sorted({t for a in it["agenda"] for t in a["topics"]})


def main() -> int:
    if not shutil.which("tesseract"):
        print("tesseract 가 없습니다 (워크플로에서 설치).", file=sys.stderr)
    state = load(DATA / "minutes.json", {"items": []})
    items = {f"{i['code']}-{i['bbs']}-{i['nttId']}": i for i in state["items"]}
    for i in items.values():  # 글자를 못 뽑은 글은 파서 개선 후 한 번 더 시도
        if i.get("status") == "no-text" and i.get("parser", 1) < PARSER_VERSION:
            i["status"] = "pending"
    status = {"ran_at": NOW.isoformat(timespec="minutes"), "complexes": {}, "complete": True}
    since = (NOW - dt.timedelta(days=CFG["lookback_days"])).strftime("%Y-%m-%d")
    complexes = resolve_complexes(status)

    def persist():
        lst = sorted(items.values(), key=lambda i: (i.get("date", ""), i["nttId"]), reverse=True)
        save(DATA / "minutes.json", {"updated": NOW.isoformat(timespec="minutes"),
                                     "topics": {k: v["label"] for k, v in CFG["topics"].items()},
                                     "groups": CFG["group_labels"],
                                     "regions": [r["label"] for r in CFG.get("display", {}).get("regions", [])],
                                     "complexes": [{k: c.get(k) for k in ("name", "code", "sigungu", "dong", "home", "groups",
                                                                          "households", "use_approval", "region", "pinned")}
                                                   for c in complexes],
                                     "terms": term_stats(items, complexes),
                                     "items": lst})

    try:
        # 1) 목록: 모든 단지를 먼저 훑어 새 글을 등록 (단지 하나에 시간이 몰리지 않도록)
        sessions = {}
        for cx in complexes:
            st = status["complexes"].setdefault(cx["name"], {"listed": 0, "new": 0, "done": 0, "errors": []})
            try:
                s = sessions[cx["code"]] = Session(cx["code"])
                for bbs, b in CFG["boards"].items():
                    if not b.get("enabled"):
                        continue
                    b_since = (NOW - dt.timedelta(days=b.get("lookback_days", CFG["lookback_days"]))).strftime("%Y-%m-%d")
                    taken = 0
                    for page in range(1, CFG["max_pages"] + 1):
                        lh = s.board_page(bbs, page)
                        rows = parse_list(lh)
                        dm = re.search(r'name="returnUrl"[^>]*value="([^"]*Detail[^"]*)"', lh)
                        if dm:
                            b["detail"] = dm.group(1)
                        if not rows:
                            break
                        known_hit = False
                        for r in rows:
                            if r["date"] and r["date"] < b_since:
                                continue
                            if b.get("max_posts") and taken >= b["max_posts"]:
                                break
                            key = f"{cx['code']}-{bbs}-{r['nttId']}"
                            st["listed"] += 1
                            if key in items:
                                known_hit = True
                                continue
                            if not wanted(r, b):
                                continue
                            taken += 1
                            items[key] = {**r, "code": cx["code"], "complex": cx["name"], "bbs": bbs,
                                          "board": b["label"], "kind": b.get("kind", "minutes"),
                                          "first_seen": NOW.strftime("%Y-%m-%d"), "status": "pending"}
                            st["new"] += 1
                        oldest = min((r["date"] for r in rows if r["date"]), default="")
                        if (oldest and oldest < b_since) or (known_hit and page > 1) or \
                                (b.get("max_posts") and taken >= b["max_posts"]):
                            break
            except Stop:
                raise
            except Exception as e:
                st["errors"].append(str(e)[:200])
        # 1-2) 보강 자료: 게시판 범위 밖의 공개 공고 파일 (config/seeds.json)
        seeds = load(ROOT / "config" / "seeds.json", {"seeds": []}).get("seeds", [])
        known_urls = {f.get("url") for i in items.values() for f in i.get("files", [])}
        cx_by = {norm(c["name"]): c for c in complexes}
        for sd in seeds:
            if sd["url"] in known_urls:
                continue
            cx = next((c for k, c in cx_by.items() if norm(sd["complex"]) in k or k in norm(sd["complex"])), None)
            if not cx:
                continue
            key = f"{cx['code']}-seed-{hashlib.md5(sd['url'].encode()).hexdigest()[:10]}"
            if key in items:
                continue
            title = re.sub(r"\.(jpe?g|png|pdf|hwp)$", "", sd.get("name") or "", flags=re.I) or "공개 공고"
            items[key] = {"nttId": key.split("-")[-1], "code": cx["code"], "complex": cx["name"], "bbs": "seed",
                          "board": "보강 자료", "kind": "minutes", "category": "보강", "title": title,
                          "date": sd.get("date", ""), "seed_url": sd["url"], "first_seen": NOW.strftime("%Y-%m-%d"),
                          "status": "pending"}
        persist()

        # 2) 첨부 읽기: 최근 글부터, 단지를 번갈아가며
        pending = sorted((i for i in items.values() if i.get("status") == "pending"),
                         key=lambda i: i.get("date", ""), reverse=True)
        for it in pending:
            s = sessions.get(it["code"])
            if not s:
                continue
            st = status["complexes"].setdefault(it["complex"], {"listed": 0, "new": 0, "done": 0, "errors": []})
            try:
                if it.get("seed_url"):
                    files, body = [{"url": it["seed_url"], "name": it["title"] + ".jpg", "inline": True}], ""
                else:
                    files, body = parse_detail(s.detail(it["bbs"], it["nttId"]))
                if not files and it.get("first_file"):
                    fid, sn = it["first_file"][0]
                    files = [{"atchFileId": fid, "fileSn": sn, "name": "첨부1"}]
                texts, kinds = [], []
                for f in files[:CFG["max_files_per_post"]]:
                    if not f.get("inline"):
                        f["url"] = f"{B}/open/FileDown.do?atchFileId={f['atchFileId']}&fileSn={f['fileSn']}"
                    data = s._open(f["url"])
                    if len(data) > CFG["max_file_mb"] * 1024 * 1024:
                        kinds.append("too-big")
                        continue
                    with tempfile.TemporaryDirectory() as td:
                        p = Path(td) / ("f" + Path(f["name"]).suffix[:6])
                        p.write_bytes(data)
                        txt, kind = extract(p, f["name"], DA.get("ocr_max_pages", 12) if it.get("kind") == "doc" else 20)
                    f["method"] = kind
                    kinds.append(kind)
                    if txt.strip():
                        texts.append(f"===== {f['name']} =====\n{txt}")
                full = "\n\n".join(([f"===== 본문 =====\n{body}"] if body else []) + texts)
                (TEXT_DIR / it["code"]).mkdir(parents=True, exist_ok=True)
                (TEXT_DIR / it["code"] / f"{it['nttId']}.txt").write_text(full, encoding="utf-8")
                it.update({"files": files, "methods": kinds, "chars": len(full),
                           "status": "done" if full.strip() else "no-text", "parser": PARSER_VERSION})
                apply_analysis(it, full)
                st["done"] += 1
            except Stop:
                raise
            except Exception as e:
                it["status"] = "error"
                it["error"] = str(e)[:200]
                st["errors"].append(f"{it['nttId']}: {str(e)[:150]}")
            if st["done"] % 5 == 0:
                persist()
    except Stop as e:
        status["complete"] = False
        status["stopped"] = str(e)

    # 이전 실행에서 오류 난 글은 다음 실행에서 한 번 더
    for it in items.values():
        if it.get("status") == "error" and it.get("retried") is None:
            it["status"], it["retried"] = "pending", True
    # 규칙을 고치면 예전 글에도 반영되도록, 저장해 둔 글자로 안건 분석을 다시 한다
    for it in items.values():
        tp = TEXT_DIR / it["code"] / f"{it['nttId']}.txt"
        if it.get("status") == "done" and tp.exists():
            apply_analysis(it, tp.read_text(encoding="utf-8"))
    persist()
    status["totals"] = {
        "posts": len(items),
        "done": sum(1 for i in items.values() if i.get("status") == "done"),
        "pending": sum(1 for i in items.values() if i.get("status") == "pending"),
        "agenda_items": sum(len(i.get("agenda", [])) for i in items.values()),
        "docs": sum(1 for i in items.values() if i.get("kind") == "doc" and i.get("status") == "done"),
    }
    save(DATA / "minutes_status.json", status)
    print(json.dumps(status, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
