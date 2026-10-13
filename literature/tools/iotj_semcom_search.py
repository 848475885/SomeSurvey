#!/usr/bin/env python3
"""Build a traceable IEEE IoTJ semantic-communication candidate census.

The scan deliberately starts from the complete OpenAlex venue/date corpus and
then adds independent Crossref keyword searches.  It keeps broad hits for the
audit trail; final inclusion is decided in a later full-text screening pass.
"""

from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "literature" / "ieee-iotj-semantic-communications-2023-present"
NOTES = OUT / "notes"
SOURCE_ID = "S2480266640"
VENUE = "IEEE Internet of Things Journal"
CROSSREF_ISSN = "2327-4662"
ISSNS = ["2327-4662", "2372-2541"]
START = "2023-01-01"
END = "2026-10-09"
USER_AGENT = "Digital-SemCom-Survey/1.0 (contact: local research project)"

QUERIES = [
    "semantic communication",
    "semantic communications",
    "DeepJSCC",
    "deep joint source-channel coding",
    "joint source-channel coding",
    "task-oriented communication",
    "goal-oriented communication",
    "semantic transmission",
    "semantic-aware communication",
    "digital semantic communication",
    "semantic communication vector quantization",
    "VQ semantic communication",
    "discrete semantic communication",
    "semantic communication codebook",
    "semantic communication quantization",
    "digital JSCC semantic communication",
    "semantic-aware channel coding",
    "index error semantic communication",
    "bit error semantic communication",
    "OFDM digital semantic communication",
    "product quantization semantic communication",
    "wireless image transmission",
    "wireless video transmission",
    "semantic modulation",
]

TOPIC_RE = re.compile(
    r"semantic[- ](?:communication|communications|transmission|coding|relay|offloading|broadcast|multiple access|"
    r"aware (?:communication|transmission|network|resource|spectrum|channel|modulation))|"
    r"(?:task|goal)[- ]oriented (?:communication|communications|source coding)|"
    r"deep (?:joint )?source[- ]channel|deepjscc|\bjscc\b|joint source[- ]channel coding|"
    r"wireless (?:image|video|speech) transmission",
    re.I,
)

DIRECT_TITLE_RE = re.compile(
    r"semantic.*(?:communication|transmission|modulation|broadcast|relay|offloading)|"
    r"(?:communication|transmission|modulation).*semantic|"
    r"(?:task|goal)[- ]oriented (?:communication|communications|source coding)|"
    r"deep (?:joint )?source[- ]channel|deepjscc|joint source[- ]channel coding|\bjscc\b",
    re.I,
)


def norm_title(value: str) -> str:
    value = html.unescape(unicodedata.normalize("NFKC", value or ""))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def norm_doi(value: str | None) -> str:
    return (value or "").lower().replace("https://doi.org/", "").strip()


def abstract_text(inverted: dict | None) -> str:
    if not inverted:
        return ""
    positioned: list[tuple[int, str]] = []
    for token, positions in inverted.items():
        positioned.extend((int(pos), token) for pos in positions)
    return " ".join(token for _, token in sorted(positioned))


def get_json(session: requests.Session, url: str, params: dict) -> dict:
    for attempt in range(5):
        response = session.get(url, params=params, timeout=90)
        if response.status_code == 429:
            time.sleep(3 * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"repeated 429: {response.url}")


def openalex_full_scan(session: requests.Session) -> tuple[list[dict], dict]:
    cursor = "*"
    records: list[dict] = []
    requests_made = 0
    while cursor:
        payload = get_json(
            session,
            "https://api.openalex.org/works",
            {
                "filter": f"primary_location.source.id:{SOURCE_ID},from_publication_date:{START},to_publication_date:{END}",
                "per-page": 200,
                "cursor": cursor,
                "select": "id,doi,title,publication_year,publication_date,authorships,primary_location,open_access,abstract_inverted_index,biblio,type",
            },
        )
        requests_made += 1
        for work in payload.get("results", []):
            abstract = abstract_text(work.get("abstract_inverted_index"))
            title = html.unescape(work.get("title") or "").strip()
            haystack = f"{title}\n{abstract}"
            if not TOPIC_RE.search(haystack):
                continue
            location = work.get("primary_location") or {}
            source = location.get("source") or {}
            biblio = work.get("biblio") or {}
            authors = [
                ((entry.get("author") or {}).get("display_name") or "").strip()
                for entry in work.get("authorships") or []
            ]
            authors = [name for name in authors if name]
            records.append(
                {
                    "title": title,
                    "authors": authors,
                    "year": work.get("publication_year"),
                    "publication_date": work.get("publication_date"),
                    "doi": norm_doi(work.get("doi")),
                    "venue": source.get("display_name") or VENUE,
                    "volume": biblio.get("volume") or "",
                    "issue": biblio.get("issue") or "",
                    "pages": "-".join(x for x in (biblio.get("first_page"), biblio.get("last_page")) if x),
                    "abstract": abstract,
                    "publisher_url": work.get("doi") or location.get("landing_page_url") or "",
                    "sources": ["OpenAlex full-journal metadata scan"],
                    "matched_queries": ["full-journal metadata scan"],
                    "openalex_id": work.get("id") or "",
                    "open_access": work.get("open_access") or {},
                    "oa_pdf_url": location.get("pdf_url") or "",
                    "record_type": work.get("type") or "",
                }
            )
        cursor = (payload.get("meta") or {}).get("next_cursor")
        if not payload.get("results"):
            break
        time.sleep(0.08)
    return records, {"database": "OpenAlex", "requests": requests_made, "topic_hits": len(records)}


def crossref_search(session: requests.Session) -> tuple[list[dict], dict]:
    merged: dict[str, dict] = {}
    raw_hits = 0
    errors: list[str] = []
    for query in QUERIES:
        try:
            payload = get_json(
                session,
                f"https://api.crossref.org/journals/{CROSSREF_ISSN}/works",
                {
                    "query.bibliographic": query,
                    "filter": f"from-pub-date:{START},until-pub-date:{END}",
                    "rows": 250,
                    "select": "DOI,title,author,published,container-title,volume,issue,page,abstract,URL,type",
                },
            )
            items = (payload.get("message") or {}).get("items") or []
            raw_hits += len(items)
            for item in items:
                title = html.unescape(" ".join(item.get("title") or [])).strip()
                abstract = re.sub(r"<[^>]+>", " ", html.unescape(item.get("abstract") or ""))
                if not TOPIC_RE.search(f"{title}\n{abstract}"):
                    continue
                doi = norm_doi(item.get("DOI"))
                key = doi or norm_title(title)
                if not key:
                    continue
                published = ((item.get("published") or {}).get("date-parts") or [[None]])[0]
                year = published[0] if published else None
                authors = [
                    " ".join(x for x in (a.get("given", ""), a.get("family", "")) if x).strip()
                    for a in item.get("author") or []
                ]
                if key not in merged:
                    merged[key] = {
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "doi": doi,
                        "venue": " ".join(item.get("container-title") or []) or VENUE,
                        "volume": item.get("volume") or "",
                        "issue": item.get("issue") or "",
                        "pages": item.get("page") or "",
                        "abstract": re.sub(r"\s+", " ", abstract).strip(),
                        "publisher_url": item.get("URL") or (f"https://doi.org/{doi}" if doi else ""),
                        "sources": ["Crossref keyword search"],
                        "matched_queries": [query],
                        "record_type": item.get("type") or "",
                    }
                elif query not in merged[key]["matched_queries"]:
                    merged[key]["matched_queries"].append(query)
        except Exception as exc:  # keep the audit useful when one query fails
            errors.append(f"{query}: {exc}")
        time.sleep(0.12)
    return list(merged.values()), {
        "database": "Crossref",
        "queries": QUERIES,
        "raw_hits": raw_hits,
        "topic_hits": len(merged),
        "errors": errors,
    }


def merge_records(*groups: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    aliases: dict[str, str] = {}
    for group in groups:
        for record in group:
            title_key = norm_title(record.get("title", ""))
            doi_key = norm_doi(record.get("doi"))
            key = doi_key or aliases.get(title_key) or title_key
            if title_key in aliases:
                key = aliases[title_key]
            if key not in merged:
                merged[key] = record
                aliases[title_key] = key
                continue
            current = merged[key]
            for field in ("title", "authors", "year", "publication_date", "doi", "venue", "volume", "issue", "pages", "abstract", "publisher_url", "openalex_id", "open_access", "oa_pdf_url", "record_type"):
                if not current.get(field) and record.get(field):
                    current[field] = record[field]
            for field in ("sources", "matched_queries"):
                current[field] = list(dict.fromkeys((current.get(field) or []) + (record.get(field) or [])))
    records = list(merged.values())
    for record in records:
        title = record.get("title", "")
        abstract = record.get("abstract", "")
        direct = bool(DIRECT_TITLE_RE.search(title))
        record["screening_status"] = "candidate"
        record["screening_priority"] = "high" if direct else "medium"
        record["screening_reason"] = (
            "title directly names semantic communication/DeepJSCC/task-oriented communication"
            if direct
            else "abstract or metadata contains an in-scope semantic/JSCC transmission mechanism; requires full-text screening"
        )
        record["matched_topic_terms"] = sorted(set(m.group(0) for m in TOPIC_RE.finditer(f"{title}\n{abstract}")), key=str.lower)
    records.sort(key=lambda r: (int(r.get("year") or 9999), (r.get("title") or "").lower()))
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    (OUT / "papers").mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    openalex, openalex_audit = openalex_full_scan(session)
    crossref, crossref_audit = crossref_search(session)
    candidates = merge_records(openalex, crossref)
    write_jsonl(NOTES / "candidate_pool.jsonl", candidates)

    audit = {
        "run_date": END,
        "venue": VENUE,
        "issn": ISSNS,
        "date_range": [START, END],
        "required_queries": QUERIES,
        "rounds": [openalex_audit, crossref_audit],
        "deduplicated_candidate_count": len(candidates),
        "status": "candidate census complete; manual/full-text screening pending",
    }
    (NOTES / "search_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"openalex": len(openalex), "crossref": len(crossref), "candidates": len(candidates)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
