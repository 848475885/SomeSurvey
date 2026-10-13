#!/usr/bin/env python3
"""Slow, resumable IEEE downloader for the remaining IoTJ survey corpus.

This imports the project-approved IEEE Xplore skill implementation and adds
handling for IEEE's transient HTTP 202 PDF preparation response.  Requests are
serial and separated by conservative intervals.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import random
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
SKILL_SCRIPT = Path.home() / ".codex" / "skills" / "ieee-xplore-literature" / "scripts" / "ieee_xplore_download.py"


def load_skill():
    spec = importlib.util.spec_from_file_location("ieee_xplore_download", SKILL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SKILL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def safe_name(value: str, limit: int = 112) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value[:limit].rstrip("_") or "paper"


def target_for(record: dict) -> Path:
    lead = ((record.get("authors") or ["Unknown"])[0]).split()[-1]
    return PAPERS / f"{record.get('year')}_{safe_name(lead,24)}_{safe_name(record.get('title',''))}.pdf"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crossref_arnumber(doi: str) -> str | None:
    """Resolve IEEE document number from Crossref syndication links."""
    try:
        response = requests.get(
            f"https://api.crossref.org/works/{quote(doi, safe='')}",
            headers={"User-Agent": "Digital-SemCom-Survey/1.0 (arnumber resolver)"},
            timeout=60,
        )
        response.raise_for_status()
        message = response.json().get("message") or {}
        urls = [str(item.get("URL") or "") for item in message.get("link") or []]
        urls.append(str(((message.get("resource") or {}).get("primary") or {}).get("URL") or ""))
        for url in urls:
            query_match = re.search(r"[?&]arnumber=(\d{8})", url)
            if query_match:
                return query_match.group(1)
            file_match = re.search(r"/(\d{8})(?:-aam)?\.pdf(?:\?|$)", url)
            if file_match:
                return file_match.group(1)
    except Exception:
        return None
    return None


def fetch_pdf(tab, arnumber: str, wait_before: float = 8.0, retries: int = 4) -> dict:
    document_url = f"https://ieeexplore.ieee.org/document/{arnumber}"
    pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}"
    tab.navigate(document_url, wait_seconds=5.0)
    time.sleep(wait_before)
    result = {}
    for attempt in range(1, retries + 1):
        result = tab.evaluate(
            f"""
(async () => {{
  const meta = {{
    title: document.title.replace(/ \\| IEEE.*$/, '').trim(),
    url: location.href,
    access: ((document.body.innerText.match(/Access provided by:\\s*([^\\n]+)/) || [])[1] || '').trim(),
    doi: ((document.body.innerText.match(/DOI:\\s*([^\\n]+)/) || [])[1] || '').trim()
  }};
  const r = await fetch({json.dumps(pdf_url)}, {{credentials: 'include'}});
  const type = r.headers.get('content-type') || '';
  const buf = await r.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {{
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }}
  return {{
    status: r.status, type, size: bytes.length,
    head: Array.from(bytes.slice(0, 5)).map(x => String.fromCharCode(x)).join(''),
    base64: (r.status === 200 && type.toLowerCase().includes('pdf')) ? btoa(binary) : '',
    meta
  }};
}})()
"""
        )
        if result.get("status") == 200 and "pdf" in result.get("type", "").lower() and result.get("head") == "%PDF-":
            return {"ok": True, "attempt": attempt, "result": result, "document_url": document_url, "pdf_url": pdf_url}
        if result.get("status") == 202:
            time.sleep(12.0)
            continue
        return {"ok": False, "attempt": attempt, "result": result, "document_url": document_url, "pdf_url": pdf_url}
    return {"ok": False, "attempt": retries, "result": result, "document_url": document_url, "pdf_url": pdf_url}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    skill = load_skill()
    # Recent Chrome builds can spend longer than 20 seconds restoring the
    # persistent IEEE profile before the DevTools endpoint starts listening.
    skill.ensure_chrome("http://127.0.0.1:9222", skill.default_profile(), 45.0)
    tab = skill.find_or_create_ieee_tab("http://127.0.0.1:9222")
    # Large IEEE PDFs can keep the Runtime.evaluate call open for more than
    # the skill's default 30-second websocket timeout while the browser
    # converts the response to base64.
    tab.ws.settimeout(180)
    records = read_jsonl(NOTES / "included.jsonl")
    pending = [r for r in records if not r.get("pdf_valid")]
    if args.limit:
        pending = pending[: args.limit]
    log_path = NOTES / "ieee_remaining_manifest.jsonl"
    completed = 0
    try:
        for index, record in enumerate(pending, start=1):
            arnumber = crossref_arnumber(str(record.get("doi") or ""))
            source_url = f"https://ieeexplore.ieee.org/document/{arnumber}" if arnumber else ""
            if not arnumber:
                arnumber, source_url = skill.resolve_document(tab, {"doi": record.get("doi"), "title": record.get("title")})
            if not arnumber:
                event = {"status": "not_found", "title": record.get("title"), "doi": record.get("doi"), "source_url": source_url}
            else:
                probe = fetch_pdf(tab, arnumber)
                response = probe.get("result") or {}
                if probe.get("ok"):
                    target = target_for(record)
                    target.write_bytes(base64.b64decode(response["base64"]))
                    record.update(
                        {
                            "pdf_status": "downloaded_ieee_validated",
                            "pdf_path": str(target.resolve()),
                            "pdf_valid": True,
                            "pdf_header_ok": True,
                            "pdf_bytes": target.stat().st_size,
                            "sha256": sha256(target),
                            "ieee_document_id": arnumber,
                            "ieee_document_url": probe["document_url"],
                            "ieee_pdf_url": probe["pdf_url"],
                            "institutional_access": (response.get("meta") or {}).get("access", ""),
                        }
                    )
                    completed += 1
                    event = {
                        "status": "downloaded", "title": record.get("title"), "doi": record.get("doi"),
                        "arnumber": arnumber, "bytes": target.stat().st_size, "path": str(target),
                        "attempt": probe.get("attempt"), "access": record.get("institutional_access", ""),
                    }
                else:
                    event = {
                        "status": "failed", "title": record.get("title"), "doi": record.get("doi"),
                        "arnumber": arnumber, "http_status": response.get("status"),
                        "content_type": response.get("type"), "bytes": response.get("size"),
                        "attempt": probe.get("attempt"),
                    }
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            write_jsonl(NOTES / "included.jsonl", records)
            print(json.dumps({"n": index, "of": len(pending), **event}, ensure_ascii=False), flush=True)
            if event["status"] == "failed":
                print("Stopping after an unresolved IEEE response.", flush=True)
                break
            time.sleep(random.uniform(8.0, 12.0))
    finally:
        tab.close()
    print(json.dumps({"downloaded_this_run": completed, "remaining": sum(not r.get("pdf_valid") for r in records)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
