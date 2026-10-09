#!/usr/bin/env python3
"""Static acceptance checks for the IoTJ semantic-communication report."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-iotj-semantic-communications-2023-present"
REQUIRED_HEADINGS = {
    "Motivation｜Introduction 怎样导出本文方案",
    "方法与端到端信息流",
    "数字化方案与真实传输开销",
    "信道怎样作用，以及 decoder 实际拿到什么",
    "实验设置与主要结论",
    "通信价值、局限与 Codex 判断",
}
POLLUTION = (
    "Authorized licensed use",
    "Downloaded on",
    "Restrictions apply",
    "Member, IEEE",
    "Fellow, IEEE",
    "本页是对原专题的整体重建",
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def validate_html(path: Path, local: bool, expected_titles: set[str]) -> list[str]:
    errors: list[str] = []
    source = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(source, "html.parser")
    articles = soup.select("article.paper")
    if len(articles) != len(expected_titles):
        errors.append(f"{path.name}: expected {len(expected_titles)} articles, found {len(articles)}")
    ids = [article.get("id", "") for article in articles]
    duplicates = [value for value, count in Counter(ids).items() if value and count > 1]
    if duplicates:
        errors.append(f"{path.name}: duplicate article ids: {duplicates}")
    titles = {heading.get_text(" ", strip=True) for heading in soup.select("article.paper h2")}
    if titles != expected_titles:
        errors.append(f"{path.name}: title set mismatch ({len(expected_titles - titles)} missing, {len(titles - expected_titles)} extra)")
    nav_targets = {link.get("href", "")[1:] for link in soup.select("nav a:not(.top-link)[href^='#']")}
    if nav_targets != set(ids):
        errors.append(f"{path.name}: navigation/article anchor mismatch")
    if "content-visibility:auto" in source.replace(" ", ""):
        errors.append(f"{path.name}: content-visibility:auto would destabilize hash navigation")
    if ".paper{content-visibility:visible" not in source.replace(" ", ""):
        errors.append(f"{path.name}: visible paper layout guard missing")
    if "revealPaperTarget" not in source or "history.pushState" not in source:
        errors.append(f"{path.name}: deterministic anchor handler missing")
    if "scrollIntoView({block:'start',behavior:'instant'})" not in source:
        errors.append(f"{path.name}: anchor navigation is not instant and may drift on repeated clicks")
    if r"inlineMath:[['\\(','\\)']]" not in source or r"displayMath:[['\\[','\\]']]" not in source:
        errors.append(f"{path.name}: MathJax delimiters are not double-escaped for JavaScript")
    if "�" in source:
        errors.append(f"{path.name}: Unicode replacement character present")
    for marker in POLLUTION:
        if marker in source:
            errors.append(f"{path.name}: polluted display text: {marker}")
    for article in articles:
        title_node = article.find("h2")
        title = title_node.get_text(" ", strip=True) if title_node else article.get("id", "")
        headings = {node.get_text(" ", strip=True) for node in article.find_all("h3")}
        missing_headings = REQUIRED_HEADINGS - headings
        if missing_headings:
            errors.append(f"{path.name}: {title}: missing headings {sorted(missing_headings)}")
        if len(article.select("ol.story li")) != 7:
            errors.append(f"{path.name}: {title}: Introduction story does not have 7 steps")
        figures = article.select(".fig-grid figure")
        if len(figures) < 2:
            errors.append(f"{path.name}: {title}: expected method and result evidence figures")
        for figure in figures:
            image = figure.find("img")
            if not image or not (SURVEY / image.get("src", "")).exists():
                errors.append(f"{path.name}: {title}: missing image asset")
            caption = figure.get_text(" ", strip=True)
            if "PDF p." not in caption or title not in caption:
                errors.append(f"{path.name}: {title}: incomplete figure provenance")
        text_length = len(article.get_text(" ", strip=True))
        if text_length < 1400:
            errors.append(f"{path.name}: {title}: analysis too short ({text_length} chars)")
        button = article.select_one(".paper-head .button")
        href = button.get("href", "") if button else ""
        if local and not href.startswith("papers/"):
            errors.append(f"{path.name}: {title}: local PDF link missing")
        if not local and (href.startswith("papers/") or href.lower().endswith(".pdf")):
            errors.append(f"{path.name}: {title}: restricted/local PDF exposed")
    if len(soup.select("#pending tbody tr")) != 13:
        errors.append(f"{path.name}: pending-fulltext table does not contain 13 papers")
    return errors


def main() -> None:
    manifest = load_jsonl(SURVEY / "manifest.jsonl")
    pending = load_jsonl(SURVEY / "notes" / "pending_fulltext.jsonl")
    analysis = load_jsonl(SURVEY / "notes" / "synthesized_analysis.jsonl")
    audit = load_jsonl(SURVEY / "notes" / "reread_audit.jsonl")
    expected_titles = {row["title"] for row in manifest}
    errors: list[str] = []
    if not (len(manifest) == len(analysis) == len(audit) == 87):
        errors.append(f"record counts: manifest={len(manifest)}, analysis={len(analysis)}, audit={len(audit)}")
    if len(pending) != 13:
        errors.append(f"pending count: {len(pending)}")
    if any(not row.get("pdf_exists") or not row.get("pdf_sha256") for row in audit):
        errors.append("reread audit has missing PDF/hash evidence")
    if any(len(row.get("assets") or []) < 2 for row in analysis):
        errors.append("analysis record lacks two evidence assets")
    errors.extend(validate_html(SURVEY / "index.html", False, expected_titles))
    errors.extend(validate_html(SURVEY / "index_local.html", True, expected_titles))
    print(json.dumps({
        "status": "PASS" if not errors else "FAIL",
        "verified_articles": len(manifest),
        "pending_fulltext": len(pending),
        "analysis_records": len(analysis),
        "audit_records": len(audit),
        "asset_pngs": len(list((SURVEY / "assets").glob("*.png"))),
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
