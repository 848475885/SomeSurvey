#!/usr/bin/env python3
"""Find legal OA copies missed by DOI-only metadata lookups."""

from __future__ import annotations

import json
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote

import requests

import iotj_oa_download as shared


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-tvt-semantic-communications-2023-present"
NOTES = SURVEY / "notes"
PAPERS = SURVEY / "papers"
UA = "Digital-SemCom-Survey/1.0 (legal OA title resolver)"
KNOWN_OA_BY_DOI = {
    "10.1109/tvt.2024.3507919": [
        {
            "url": "https://ira.lib.polyu.edu.hk/bitstream/10397/115250/1/Zhan_Novel_Double_Protograph.pdf",
            "provider": "PolyU Institutional Research Archive",
            "match": 1.0,
        }
    ],
    "10.1109/tvt.2026.3706678": [
        {
            "url": "https://arxiv.org/pdf/2508.08686",
            "provider": "arXiv",
            "match": 1.0,
        }
    ],
}

shared.SURVEY = SURVEY
shared.NOTES = NOTES
shared.PAPERS = PAPERS


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalized(a), normalized(b)).ratio()


def semantic_scholar_candidates(session: requests.Session, title: str) -> list[dict]:
    response = session.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": title, "limit": 5, "fields": "title,openAccessPdf,externalIds,year"},
        timeout=60,
    )
    if response.status_code != 200:
        return []
    return list(response.json().get("data") or [])


def openalex_candidates(session: requests.Session, title: str) -> list[dict]:
    response = session.get(
        "https://api.openalex.org/works",
        params={"search": title, "per-page": 5, "select": "title,locations,best_oa_location,ids,publication_year"},
        timeout=60,
    )
    if response.status_code != 200:
        return []
    return list(response.json().get("results") or [])


def candidate_urls(title: str, s2: list[dict], oa: list[dict]) -> list[dict]:
    found: list[dict] = []
    for item in s2:
        score = similarity(title, str(item.get("title") or ""))
        if score < 0.92:
            continue
        pdf = (item.get("openAccessPdf") or {}).get("url")
        arxiv = (item.get("externalIds") or {}).get("ArXiv")
        if pdf:
            found.append({"url": pdf, "provider": "Semantic Scholar", "match": score})
        if arxiv:
            found.append({"url": f"https://arxiv.org/pdf/{quote(str(arxiv), safe='')}", "provider": "arXiv via Semantic Scholar", "match": score})
    for item in oa:
        score = similarity(title, str(item.get("title") or ""))
        if score < 0.92:
            continue
        locations = list(item.get("locations") or [])
        if item.get("best_oa_location"):
            locations.insert(0, item["best_oa_location"])
        for location in locations:
            pdf = (location or {}).get("pdf_url")
            if pdf:
                found.append({"url": pdf, "provider": "OpenAlex title search", "match": score})
    dedup: list[dict] = []
    seen: set[str] = set()
    for item in found:
        url = item["url"]
        if url not in seen and "ieeexplore.ieee.org" not in url:
            seen.add(url)
            dedup.append(item)
    return dedup


def main() -> None:
    records = shared.read_jsonl(NOTES / "included.jsonl")
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    log_path = NOTES / "title_oa_download_log.jsonl"
    downloaded = 0
    for index, record in enumerate(records, start=1):
        if record.get("pdf_valid"):
            continue
        title = str(record.get("title") or "")
        s2 = semantic_scholar_candidates(session, title)
        time.sleep(1.05)
        oa = openalex_candidates(session, title)
        time.sleep(0.2)
        urls = list(KNOWN_OA_BY_DOI.get(str(record.get("doi") or "").lower(), []))
        urls.extend(candidate_urls(title, s2, oa))
        target = shared.target_for(record)
        attempts: list[dict] = []
        for candidate in urls:
            ok, detail = shared.download(session, candidate["url"], target)
            event = {**candidate, "ok": ok, "detail": detail}
            attempts.append(event)
            if ok:
                record.update(
                    {
                        "pdf_status": "downloaded_open_version_title_matched_validated",
                        "pdf_path": str(target.resolve()),
                        "pdf_valid": True,
                        "pdf_header_ok": True,
                        "pdf_bytes": target.stat().st_size,
                        "sha256": shared.digest(target),
                        "download_source": detail,
                        "title_match_score": round(float(candidate["match"]), 4),
                    }
                )
                downloaded += 1
                break
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"title": title, "attempts": attempts, "success": bool(record.get("pdf_valid"))}, ensure_ascii=False) + "\n")
        shared.write_jsonl(NOTES / "included.jsonl", records)
        print(json.dumps({"n": index, "success": bool(record.get("pdf_valid")), "sources": len(urls), "title": title}, ensure_ascii=False), flush=True)
    print(json.dumps({"downloaded": downloaded, "remaining": sum(not row.get("pdf_valid") for row in records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
