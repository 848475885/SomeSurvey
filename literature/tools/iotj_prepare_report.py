#!/usr/bin/env python3
"""Prepare the verified IoTJ corpus for the local/public HTML report."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-iotj-semantic-communications-2023-present"
INCLUDED = SURVEY / "notes" / "included.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def sanitize_public_row(row: dict) -> dict:
    """Remove local acquisition metadata from publishable corpus records."""
    item = dict(row)
    item.pop("institutional_access", None)
    item.pop("reused_from", None)
    return item


def main() -> None:
    rows = load_jsonl(INCLUDED)
    manifest: list[dict] = []
    pending: list[dict] = []
    failures: list[str] = []

    for row in rows:
        raw_path = Path(str(row.get("pdf_path") or ""))
        if raw_path and not raw_path.is_absolute():
            raw_path = SURVEY / raw_path
        if row.get("pdf_valid") and raw_path.exists():
            data = raw_path.read_bytes()
            if not data.startswith(b"%PDF-"):
                failures.append(f"invalid header: {raw_path.name}")
                continue
            with fitz.open(raw_path) as document:
                pages = document.page_count
                first_text = " ".join(document[index].get_text("text") for index in range(min(2, pages)))
            title_words = [word for word in normalize_title(str(row.get("title") or "")).split() if len(word) >= 5]
            text_words = set(normalize_title(first_text).split())
            title_match = sum(word in text_words for word in title_words) / max(1, len(title_words))
            item = sanitize_public_row(row)
            item["pdf_path"] = f"papers/{raw_path.name}"
            item["pdf_pages"] = pages
            item["pdf_bytes"] = raw_path.stat().st_size
            item["sha256"] = digest(raw_path)
            item["pdf_header_ok"] = True
            item["pdf_title_token_match"] = round(title_match, 4)
            manifest.append(item)
        else:
            item = sanitize_public_row(row)
            item.pop("pdf_path", None)
            item["fulltext_status"] = "pending"
            item["fulltext_note"] = "已完成题录与主题筛选；本版未取得可验证全文，暂不生成方法与实验结论。"
            pending.append(item)

    manifest.sort(key=lambda row: (int(row.get("year") or 0), str(row.get("title") or "").lower()))
    pending.sort(key=lambda row: (int(row.get("year") or 0), str(row.get("title") or "").lower()))
    if failures:
        raise SystemExit("\n".join(failures))

    (SURVEY / "manifest.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manifest),
        encoding="utf-8",
    )
    (SURVEY / "notes" / "pending_fulltext.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in pending),
        encoding="utf-8",
    )
    print(json.dumps({
        "verified_fulltext": len(manifest),
        "core": sum(row.get("screening_status") == "core" for row in manifest),
        "related": sum(row.get("screening_status") == "related" for row in manifest),
        "pending_fulltext": len(pending),
        "minimum_title_token_match": min((row["pdf_title_token_match"] for row in manifest), default=0),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
