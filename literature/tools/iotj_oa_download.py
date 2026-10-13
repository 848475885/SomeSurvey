#!/usr/bin/env python3
"""Download legal open versions of missing IoTJ survey papers."""

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-iotj-semantic-communications-2023-present"
NOTES = SURVEY / "notes"
PAPERS = SURVEY / "papers"
UA = "Digital-SemCom-Survey/1.0 (legal open-access retrieval)"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def safe_name(value: str, limit: int = 112) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value[:limit].rstrip("_") or "paper"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def target_for(record: dict) -> Path:
    lead = ((record.get("authors") or ["Unknown"])[0]).split()[-1]
    return PAPERS / f"{record.get('year')}_{safe_name(lead,24)}_{safe_name(record.get('title',''))}.pdf"


def openalex_urls(session: requests.Session, doi: str) -> list[str]:
    url = f"https://api.openalex.org/works/https://doi.org/{quote(doi, safe='')}"
    response = session.get(url, params={"select": "locations,best_oa_location,open_access"}, timeout=60)
    if response.status_code != 200:
        return []
    payload = response.json()
    urls: list[str] = []
    locations = list(payload.get("locations") or [])
    if payload.get("best_oa_location"):
        locations.insert(0, payload["best_oa_location"])
    for location in locations:
        candidate = location.get("pdf_url")
        if candidate and candidate not in urls:
            urls.append(candidate)
    return urls


def semantic_scholar_urls(session: requests.Session, doi: str) -> list[str]:
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{quote(doi, safe='')}"
    response = session.get(url, params={"fields": "openAccessPdf,externalIds"}, timeout=60)
    if response.status_code != 200:
        return []
    payload = response.json()
    pdf = (payload.get("openAccessPdf") or {}).get("url")
    arxiv = (payload.get("externalIds") or {}).get("ArXiv")
    urls = [pdf] if pdf else []
    if arxiv:
        urls.append(f"https://arxiv.org/pdf/{arxiv}")
    return list(dict.fromkeys(x for x in urls if x))


def download(session: requests.Session, url: str, target: Path) -> tuple[bool, str]:
    try:
        response = session.get(url, timeout=120, allow_redirects=True)
        content = response.content
        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and content.startswith(b"%PDF-") and len(content) > 20_000:
            target.write_bytes(content)
            return True, response.url
        return False, f"HTTP {response.status_code} {content_type} {len(content)} bytes"
    except Exception as exc:
        return False, str(exc)


def main() -> None:
    records = read_jsonl(NOTES / "included.jsonl")
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    log: list[dict] = []
    downloaded = 0
    for index, record in enumerate(records, start=1):
        current = Path(record.get("pdf_path") or "")
        if current and not current.is_absolute():
            current = SURVEY / current
        if record.get("pdf_valid") and current.exists():
            continue
        doi = record.get("doi") or ""
        urls = []
        urls.extend(openalex_urls(session, doi))
        time.sleep(0.12)
        if not urls or all("ieeexplore.ieee.org" in x for x in urls):
            urls.extend(semantic_scholar_urls(session, doi))
            time.sleep(0.9)
        urls = list(dict.fromkeys(x for x in urls if x))
        target = target_for(record)
        attempts = []
        for url in urls:
            ok, detail = download(session, url, target)
            attempts.append({"url": url, "ok": ok, "detail": detail})
            if ok:
                record.update(
                    {
                        "pdf_status": "downloaded_open_version_validated",
                        "pdf_path": str(target.resolve()),
                        "pdf_valid": True,
                        "pdf_header_ok": True,
                        "pdf_bytes": target.stat().st_size,
                        "sha256": digest(target),
                        "download_source": detail,
                    }
                )
                downloaded += 1
                break
        log.append({"doi": doi, "title": record.get("title"), "attempts": attempts, "success": bool(record.get("pdf_valid"))})
        print(json.dumps({"n": index, "success": bool(record.get("pdf_valid")), "title": record.get("title"), "sources": len(urls)}, ensure_ascii=False), flush=True)
    write_jsonl(NOTES / "included.jsonl", records)
    write_jsonl(NOTES / "oa_download_log.jsonl", log)
    print(json.dumps({"downloaded": downloaded, "remaining": sum(not r.get("pdf_valid") for r in records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
