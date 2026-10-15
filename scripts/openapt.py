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


def extract(path: Path, name: str) -> tuple[str, str]:
    kind = run(["file", "-b", str(path)]).strip()
    low = name.lower()
    if "PDF" in kind:
        txt = run(["pdftotext", "-layout", str(path), "-"])
        if len(txt.strip()) >= 150:
            return txt, "pdf-text"
        with tempfile.TemporaryDirectory() as td:  # 스캔 PDF → 쪽마다 그림으로 바꿔 글자 인식
            run(["pdftoppm", "-r", "200", "-l", "20", "-png", str(path), f"{td}/p"], timeout=300)
            pages = sorted(Path(td).glob("p*.png"))
            return "\n\n".join(ocr_image(p) for p in pages), f"pdf-ocr({len(pages)}쪽)"
    if any(k in kind for k in ("image", "JPEG", "PNG", "TIFF", "GIF")):
        return ocr_image(path), "image-ocr"
    if low.endswith(".hwpx") or ("Zip" in kind and low.endswith(".hwpx")):
        try:
            with zipfile.ZipFile(path) as z:
                parts = [n for n in z.namelist() if n.startswith("Contents/section")]
                return "\n".join(T(z.read(n).decode("utf-8", "replace")) for n in sorted(parts)), "hwpx"
        except Exception:
            return "", "hwpx-fail"
    if low.endswith(".hwp") or "Hangul" in kind or "Composite Document" in kind:
        if shutil.which("hwp5txt"):
            return run(["hwp5txt", str(path)]), "hwp"
        return "", "hwp-no-tool"
    return "", f"skip({kind[:30]})"


# ---------------------------------------------------------------- 안건 나누기·주제
AGENDA_HEAD = re.compile(
    r"^\s*(?:제\s*\d+\s*호\s*(?:의안|안건)?|안건\s*\d+|\d{1,2}\s*[\.\)]\s*(?=\S)|[①-⑳]|[가-하]\s*[\.\)]\s*(?=\S))")
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


def is_head(ln: str) -> bool:
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
        tp = topics_of(first) or topics_of(c)  # 안건 제목에 주제어가 있으면 그것만 쓴다
        if not tp:
            continue
        out.append({"head": first, "text": c[:900], "topics": tp, "votes": votes_of(c)})
    return out


# ---------------------------------------------------------------- main
def wanted(row: dict) -> bool:
    s = row["category"] + " " + row["title"]
    f = CFG["post_filter"]
    return any(w in s for w in f["include"]) and not any(w in s for w in f["exclude"])


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

    def persist():
        lst = sorted(items.values(), key=lambda i: (i.get("date", ""), i["nttId"]), reverse=True)
        save(DATA / "minutes.json", {"updated": NOW.isoformat(timespec="minutes"),
                                     "topics": {k: v["label"] for k, v in CFG["topics"].items()},
                                     "groups": CFG["group_labels"],
                                     "complexes": [{k: c.get(k) for k in ("name", "code", "sigungu", "home", "groups")}
                                                   for c in CFG["complexes"]],
                                     "items": lst})

    try:
        # 1) 목록: 모든 단지를 먼저 훑어 새 글을 등록 (단지 하나에 시간이 몰리지 않도록)
        sessions = {}
        for cx in CFG["complexes"]:
            st = status["complexes"].setdefault(cx["name"], {"listed": 0, "new": 0, "done": 0, "errors": []})
            try:
                s = sessions[cx["code"]] = Session(cx["code"])
                for bbs, b in CFG["boards"].items():
                    if not b.get("enabled"):
                        continue
                    for page in range(1, CFG["max_pages"] + 1):
                        rows = parse_list(s.board_page(bbs, page))
                        if not rows:
                            break
                        known_hit = False
                        for r in rows:
                            if r["date"] and r["date"] < since:
                                continue
                            key = f"{cx['code']}-{bbs}-{r['nttId']}"
                            st["listed"] += 1
                            if key in items:
                                known_hit = True
                                continue
                            if not wanted(r):
                                continue
                            items[key] = {**r, "code": cx["code"], "complex": cx["name"], "bbs": bbs,
                                          "board": b["label"], "first_seen": NOW.strftime("%Y-%m-%d"),
                                          "status": "pending"}
                            st["new"] += 1
                        oldest = min((r["date"] for r in rows if r["date"]), default="")
                        if (oldest and oldest < since) or (known_hit and page > 1):
                            break
            except Stop:
                raise
            except Exception as e:
                st["errors"].append(str(e)[:200])
        persist()

        # 2) 첨부 읽기: 최근 글부터, 단지를 번갈아가며
        pending = sorted((i for i in items.values() if i.get("status") == "pending"),
                         key=lambda i: i.get("date", ""), reverse=True)
        for it in pending:
            s = sessions.get(it["code"])
            if not s:
                continue
            st = status["complexes"][it["complex"]]
            try:
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
                        txt, kind = extract(p, f["name"])
                    f["method"] = kind
                    kinds.append(kind)
                    if txt.strip():
                        texts.append(f"===== {f['name']} =====\n{txt}")
                full = "\n\n".join(([f"===== 본문 =====\n{body}"] if body else []) + texts)
                (TEXT_DIR / it["code"]).mkdir(parents=True, exist_ok=True)
                (TEXT_DIR / it["code"] / f"{it['nttId']}.txt").write_text(full, encoding="utf-8")
                it.update({"files": files, "methods": kinds, "chars": len(full),
                           "agenda": analyze(full), "status": "done" if full.strip() else "no-text",
                           "parser": PARSER_VERSION})
                it["topics"] = sorted({t for a in it["agenda"] for t in a["topics"]})
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
    persist()
    status["totals"] = {
        "posts": len(items),
        "done": sum(1 for i in items.values() if i.get("status") == "done"),
        "pending": sum(1 for i in items.values() if i.get("status") == "pending"),
        "agenda_items": sum(len(i.get("agenda", [])) for i in items.values()),
    }
    save(DATA / "minutes_status.json", status)
    print(json.dumps(status, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
