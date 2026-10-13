#!/usr/bin/env python3
"""Static acceptance checks for the TVT semantic-communication report."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-tvt-semantic-communications-2023-present"
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


def validate_html(path: Path, local: bool, expected_titles: set[str], pending_count: int) -> list[str]:
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
        errors.append(f"{path.name}: full-title article set mismatch")
    nav_targets = {link.get("href", "")[1:] for link in soup.select("nav a:not(.top-link)[href^='#']")}
    if nav_targets != set(ids):
        errors.append(f"{path.name}: navigation/article anchor mismatch")
    compact = source.replace(" ", "")
    if "content-visibility:auto" in compact:
        errors.append(f"{path.name}: content-visibility:auto would destabilize hash navigation")
    if ".paper{content-visibility:visible" not in compact:
        errors.append(f"{path.name}: visible paper layout guard missing")
    if "revealPaperTarget" not in source or "history.pushState" not in source:
        errors.append(f"{path.name}: deterministic anchor handler missing")
    if "scrollIntoView({block:'start',behavior:'instant'})" not in source:
        errors.append(f"{path.name}: anchor navigation may drift")
    if r"inlineMath:[['\\(','\\)']]" not in source or r"displayMath:[['\\[','\\]']]" not in source:
        errors.append(f"{path.name}: MathJax delimiters are not double-escaped")
    if "�" in source:
        errors.append(f"{path.name}: Unicode replacement character present")
    for marker in POLLUTION:
        if marker in source:
            errors.append(f"{path.name}: polluted display text: {marker}")
    for article in articles:
        title_node = article.find("h2")
        title = title_node.get_text(" ", strip=True) if title_node else article.get("id", "")
        headings = {node.get_text(" ", strip=True) for node in article.find_all("h3")}
        missing = REQUIRED_HEADINGS - headings
        if missing:
            errors.append(f"{path.name}: {title}: missing headings {sorted(missing)}")
        if len(article.select("ol.story li")) != 7:
            errors.append(f"{path.name}: {title}: Introduction story does not have 7 steps")
        figures = article.select(".fig-grid figure")
        if len(figures) < 2:
            errors.append(f"{path.name}: {title}: method/result evidence missing")
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
            errors.append(f"{path.name}: {title}: local PDF exposed in public edition")
    if len(soup.select("#pending tbody tr")) != pending_count:
        errors.append(f"{path.name}: pending table count mismatch")
    return errors


def main() -> None:
    included = load_jsonl(SURVEY / "notes" / "included.jsonl")
    manifest = load_jsonl(SURVEY / "manifest.jsonl")
    pending = load_jsonl(SURVEY / "notes" / "pending_fulltext.jsonl")
    analysis = load_jsonl(SURVEY / "notes" / "synthesized_analysis.jsonl")
    audit = load_jsonl(SURVEY / "notes" / "reread_audit.jsonl")
    expected_titles = {row["title"] for row in manifest}
    errors: list[str] = []
    included_tiers = Counter(row.get("screening_status") for row in included)
    if len(included) != 99 or included_tiers != Counter({"core": 59, "related": 40}):
        errors.append(f"included screening counts: total={len(included)}, tiers={dict(included_tiers)}")
    if not (len(manifest) == len(analysis) == len(audit) == 88):
        errors.append(f"record counts: manifest={len(manifest)}, analysis={len(analysis)}, audit={len(audit)}")
    if len(pending) != 11:
        errors.append(f"pending count: {len(pending)}")
    if any(not row.get("pdf_exists") or not row.get("pdf_sha256") for row in audit):
        errors.append("reread audit has missing PDF/hash evidence")
    if any(len(row.get("assets") or []) < 2 for row in analysis):
        errors.append("analysis record lacks two evidence assets")
    if any("institutional_access" in row or "reused_from" in row for row in manifest + included):
        errors.append("publishable metadata exposes local acquisition fields")
    if any(Path(str(row.get("pdf_path") or "")).is_absolute() for row in manifest + included):
        errors.append("publishable metadata exposes an absolute PDF path")
    analysis_by_title = {row["title"]: row for row in analysis}
    tokencom = analysis_by_title.get(
        "TokenComSR: Task-Sensitivity-Guided Token Communication for Wireless Image Super-Resolution",
        {},
    )
    if tokencom.get("task_type") != "图像传输、压缩或生成":
        errors.append("TokenComSR task classification regressed")
    public_source = (SURVEY / "index.html").read_text(encoding="utf-8")
    if "IoTJ 论文" in public_source or "IoT 网络决策" in public_source:
        errors.append("TVT report contains journal-template leakage")
    errors.extend(validate_html(SURVEY / "index.html", False, expected_titles, len(pending)))
    errors.extend(validate_html(SURVEY / "index_local.html", True, expected_titles, len(pending)))
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
