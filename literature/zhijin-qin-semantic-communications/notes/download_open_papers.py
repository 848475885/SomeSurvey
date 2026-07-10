from __future__ import annotations

import csv
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
MANIFEST = ROOT / "manifest.jsonl"


def safe_name(title: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_")[:150]
    return stem + ".pdf"


def valid_pdf(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 1000 and path.read_bytes()[:5] == b"%PDF-"


def append_manifest(record: dict) -> None:
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    rows = list(csv.DictReader((ROOT / "included_papers.csv").open(encoding="utf-8-sig")))
    PAPERS.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(rows, 1):
        dest = PAPERS / safe_name(row["title"])
        if valid_pdf(dest):
            continue
        arxiv_id = row.get("arxiv_id", "").strip()
        if not arxiv_id:
            continue
        url = f"https://arxiv.org/pdf/{arxiv_id}"
        record = {"title": row["title"], "year": row["year"], "doi": row["doi"], "arxiv_id": arxiv_id,
                  "url": url, "path": str(dest.relative_to(ROOT)).replace("\\", "/")}
        print(f"[{index}/{len(rows)}] {row['title']}", flush=True)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Digital-SemCom-Survey/1.0 academic literature review"})
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
                record.update(http_status=response.status, content_type=response.headers.get_content_type(), bytes=len(data))
            if not data.startswith(b"%PDF-"):
                raise ValueError("response is not a PDF")
            dest.write_bytes(data)
            record["status"] = "downloaded"
        except Exception as exc:
            record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        append_manifest(record)
        time.sleep(3.2)


if __name__ == "__main__":
    main()
