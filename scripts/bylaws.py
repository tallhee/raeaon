#!/usr/bin/env python3
"""공동주택마당 단지홈 › 정보공개 › 관리규약 게시판에서 관리규약·운영규정 파일을 받아,
주차·커뮤니티·식당·공공개방시설 관련 조항(제○조, 별표)을 단지별로 뽑는다.

대상 단지는 회의결과 수집(openapt.py)과 같다 (docs/data/openapt_complexes.json 캐시 사용).

결과 (docs/data/)
  bylaws.json             단지별 규약 문서와 주제별 조항 (사이트가 읽음)
  bylaws_text/<code>/<nttId>_<fileSn>.txt   파일에서 뽑은 전체 글자
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import openapt as oa  # noqa: E402

CFG = oa.CFG
BC = CFG.get("bylaws", {})
DATA = oa.DATA
OUT = DATA / "bylaws.json"
TEXT_DIR = DATA / "bylaws_text"
oa.DEADLINE = time.monotonic() + 60 * BC.get("time_budget_minutes", 20)

ARTICLE = re.compile(r"^\s*(제\s*\d+\s*조(?:\s*의\s*\d+)?\s*[\(（【\[]?[^\n]{0,40})")
ANNEX = re.compile(r"^\s*[\[［【<〈]?\s*(별\s*표|별\s*지|붙\s*임)\s*\d*")


def wanted_doc(title: str) -> bool:
    f = BC.get("doc_filter", {})
    return any(w in title for w in f.get("include", [])) and not any(w in title for w in f.get("exclude", []))


def pick_files(files: list[dict]) -> list[dict]:
    """한 글에 여러 파일이 있으면 비교표·개정안보다 확정본을 고른다."""
    ok = [f for f in files if re.search(r"\.(pdf|hwp|hwpx|docx)$", f["name"], re.I)]
    final = [f for f in ok if not re.search(r"비교표|\(안\)|개정안|권고", f["name"])]
    return (final or ok)[:BC.get("max_files_per_post", 3)]


def split_clauses(txt: str) -> list[tuple[str, str]]:
    """제○조·별표 머리줄마다 자른다. (머리, 본문)"""
    out, head, cur = [], None, []
    for ln in txt.splitlines():
        s = ln.strip()
        if not s:
            continue
        m = ARTICLE.match(s)
        if re.search(r"[·…\.]{4,}", s) or re.search(r"·{2,}", s):  # 목차 줄
            continue
        if m or ANNEX.match(s):
            if head and cur:
                out.append((head, "\n".join(cur)))
            head, cur = s[:80], [s]
        elif head:
            cur.append(re.sub(r"[ \t]+", " ", s))
    if head and cur:
        out.append((head, "\n".join(cur)))
    return out


def clause_topics(head: str, body: str) -> list[str]:
    tp = []
    for k, t in BC["topics"].items():
        kws = t["keywords"]
        if any(w in head for w in kws) or sum(body.count(w) for w in kws) >= t.get("body_min", 3):
            tp.append(k)
    return tp


def analyze(txt: str) -> list[dict]:
    res, seen = [], set()
    for head, body in split_clauses(txt):
        tp = clause_topics(head, body)
        if not tp:
            continue
        key = re.sub(r"\s", "", body[:120])
        if key in seen:  # 목차·중복 제거
            continue
        seen.add(key)
        if len(body) < 40:  # 목차 줄
            continue
        res.append({"head": head, "text": body[:BC.get("clause_chars", 1800)], "topics": tp})
    return res


def main() -> int:
    status = {"ran_at": oa.NOW.isoformat(timespec="minutes"), "complexes": {}, "complete": True}
    complexes = oa.resolve_complexes({})
    state = load_state()
    docs = state["docs"]  # key: code-nttId

    try:
        for cx in complexes:
            st = status["complexes"].setdefault(cx["name"], {"docs": 0, "new": 0, "errors": []})
            try:
                s = oa.Session(cx["code"])
                h = s.post("/boardForm/selectBoardList.do", {
                    "aptCode": cx["code"], "returnUrl": "/openApt/aMenu/mngAgree/mngAgreeList.open",
                    "query": "openAptMngCommonBoard.openAptMngBoardList", "bbsCommCode": "09"})
                rows = [r for r in oa.parse_list(h) if wanted_doc(r["title"])]
                rows.sort(key=lambda r: r["date"], reverse=True)
                # 최신 관리규약 1건 + 최신 기타 규정들 (제목별 최신만)
                chosen, titles = [], set()
                for r in rows:
                    kind = "규약" if "규약" in r["title"] else re.sub(r"[\d\s\.\(\)_\-]|개정|제정|전문|차", "", r["title"])[:12]
                    if kind in titles:
                        continue
                    titles.add(kind)
                    chosen.append(r)
                    if len(chosen) >= BC.get("max_docs_per_complex", 5):
                        break
                st["docs"] = len(chosen)
                for r in chosen:
                    key = f"{cx['code']}-{r['nttId']}"
                    prev = docs.get(key, {})
                    hwp_empty = any(f.get("method", "").startswith("hwp") and not f.get("chars") for f in prev.get("files", []))
                    if prev.get("status") == "done" and not (hwp_empty or not prev.get("files")):
                        continue
                    d = s.post("/boardForm/boardDetail.do", {
                        "aptCode": cx["code"], "searchValue": f"aptCode:{cx['code']}|bbsCommCode:09|nttId:{r['nttId']}",
                        "query": "openAptMngCommonBoard.openAptMngBoardDetail",
                        "returnUrl": "/openApt/aMenu/mngAgree/mngAgreeDetail.open"})
                    files, _ = oa.parse_detail(d)
                    files = pick_files([f for f in files if not f.get("inline")])
                    rec = {**r, "code": cx["code"], "complex": cx["name"], "files": [], "status": "done"}
                    for f in files:
                        f["url"] = f"{oa.B}/open/FileDown.do?atchFileId={f['atchFileId']}&fileSn={f['fileSn']}"
                        data = s._open(f["url"], timeout=90)
                        if len(data) > BC.get("max_file_mb", 40) * 1024 * 1024:
                            f["method"] = "too-big"
                            rec["files"].append(f)
                            continue
                        with tempfile.TemporaryDirectory() as td:
                            p = Path(td) / ("f" + Path(f["name"]).suffix[:6])
                            p.write_bytes(data)
                            txt, kind = oa.extract(p, f["name"], max_pages=BC.get("ocr_max_pages", 80))
                        f["method"], f["chars"] = kind, len(txt)
                        tp = TEXT_DIR / cx["code"] / f"{r['nttId']}_{f['fileSn']}.txt"
                        tp.parent.mkdir(parents=True, exist_ok=True)
                        tp.write_text(txt, encoding="utf-8")
                        f["text_path"] = str(tp.relative_to(DATA))
                        rec["files"].append(f)
                    docs[key] = rec
                    st["new"] += 1
                    save_state(state, complexes)
            except oa.Stop:
                raise
            except Exception as e:
                st["errors"].append(str(e)[:200])
    except oa.Stop as e:
        status["complete"] = False
        status["stopped"] = str(e)

    save_state(state, complexes)
    status["totals"] = {"docs": len(docs), "clauses": sum(len(d.get("clauses", [])) for d in docs.values())}
    oa.save(DATA / "bylaws_status.json", status)
    print(json.dumps(status, ensure_ascii=False, indent=1))
    return 0


def load_state() -> dict:
    s = oa.load(OUT, {"docs": []})
    return {"docs": {f"{d['code']}-{d['nttId']}": d for d in s.get("docs", [])}}


def save_state(state: dict, complexes: list[dict]) -> None:
    # 저장해 둔 글자로 조항을 다시 뽑는다 (규칙을 고치면 예전 문서에도 반영)
    for d in state["docs"].values():
        clauses = []
        for f in d.get("files", []):
            tp = DATA / f.get("text_path", "-")
            if tp.exists():
                for c in analyze(tp.read_text(encoding="utf-8")):
                    clauses.append({**c, "file": f["name"], "url": f["url"]})
        d["clauses"] = clauses
    docs = sorted(state["docs"].values(), key=lambda d: (d["complex"], d.get("date", "")), reverse=False)
    oa.save(OUT, {"updated": oa.NOW.isoformat(timespec="minutes"),
                  "topics": {k: v["label"] for k, v in BC["topics"].items()},
                  "docs": docs})


if __name__ == "__main__":
    sys.exit(main())
