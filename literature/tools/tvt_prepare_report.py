#!/usr/bin/env python3
"""Prepare the verified TVT corpus for report generation."""

import json
from pathlib import Path

import iotj_prepare_report as shared


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-tvt-semantic-communications-2023-present"

shared.SURVEY = SURVEY
shared.INCLUDED = SURVEY / "notes" / "included.jsonl"

RELATED_TITLE_OVERRIDES = {
    "Knowledge-Aware Semantic Communication System Design and Data Allocation",
    "An Efficient Federated Learning Framework for Training Semantic Communication Systems",
}


def apply_curated_screening() -> None:
    """Persist full-text-informed tier corrections before rebuilding outputs."""
    rows = shared.load_jsonl(shared.INCLUDED)
    changed = False
    for row in rows:
        if row.get("title") in RELATED_TITLE_OVERRIDES:
            changed = changed or row.get("screening_status") != "related"
            row["screening_status"] = "related"
            row["screening_reason"] = (
                "semantic-communication training, knowledge, or data-allocation layer "
                "directly adjacent to the transmitted representation"
            )
    if changed:
        shared.INCLUDED.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )


def sanitize_publishable_screening() -> None:
    """Keep the screening ledger portable and free of machine-local paths."""
    rows = shared.load_jsonl(shared.INCLUDED)
    for row in rows:
        pdf_path = Path(str(row.get("pdf_path") or ""))
        if row.get("pdf_valid") and pdf_path.name:
            row["pdf_path"] = f"papers/{pdf_path.name}"
        row.pop("institutional_access", None)
        row.pop("reused_from", None)
    shared.INCLUDED.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    apply_curated_screening()
    shared.main()
    sanitize_publishable_screening()
