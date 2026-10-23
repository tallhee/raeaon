#!/usr/bin/env python3
"""사이트용 가벼운 데이터 만들기.

수집 상태 파일(minutes.json 20MB+, bylaws.json 6MB+)은 수집기가 이어받기용으로 쓰는 큰 파일이라
사이트가 그대로 받으면 느리다. 화면에 필요한 필드만 골라 docs/data/site/ 아래에 줄바꿈 없이 저장한다.
  site/meta.json     단지 목록·지역·주제·주제어 (작음, 첫 화면에서 바로 읽음)
  site/minutes.json  회의결과(읽은 것만, 안건 필드만)
  site/docs.json     장기수선·감사·기타공개자료
  site/bylaws.json   관리규약 조항
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "docs" / "data"
OUT = DATA / "site"
OUT.mkdir(exist_ok=True)


def load(p, d):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return d


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


m = load(DATA / "minutes.json", {"items": []})
dump("meta.json", {k: m.get(k) for k in ("updated", "topics", "groups", "regions", "complexes", "terms")})
F = ("complex", "title", "date", "category", "board", "code", "bbs")
files = lambda i: [{"url": f["url"]} for f in i.get("files", []) if f.get("url")]
mins, docs = [], []
for i in m.get("items", []):
    if i.get("status") != "done":
        continue
    base = {k: i.get(k) for k in F if i.get(k) is not None}
    base["files"] = files(i)
    if i.get("kind") == "doc":
        docs.append({**base, "snips": i.get("snips", [])})
    elif i.get("agenda"):
        mins.append({**base, "agenda": [{k: a.get(k) for k in ("head", "text", "topics", "votes") if a.get(k)} for a in i["agenda"]]})
key = lambda x: x.get("date") or ""
dump("minutes.json", {"updated": m.get("updated"), "items": sorted(mins, key=key, reverse=True)})
dump("docs.json", {"updated": m.get("updated"), "items": sorted(docs, key=key, reverse=True)})
b = load(DATA / "bylaws.json", {"docs": []})
dump("bylaws.json", {"updated": b.get("updated"), "topics": b.get("topics"),
                     "docs": [{**{k: d.get(k) for k in ("complex", "title", "date", "code")}, "files": files(d),
                               "clauses": d.get("clauses", [])} for d in b.get("docs", []) if d.get("clauses")]})
for f in sorted(OUT.glob("*.json")):
    print(f.name, f.stat().st_size)
