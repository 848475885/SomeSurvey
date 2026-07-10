from __future__ import annotations

import csv
import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "notes"


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).lower()
    return re.sub(r"[^a-z0-9]", "", value)


def abstract_from_inverted(index: dict | None) -> str:
    if not index:
        return ""
    words: dict[int, str] = {}
    for word, positions in index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[pos] for pos in sorted(words))


def category_for(title: str, abstract: str) -> str:
    text = f"{title} {abstract}".lower()
    if any(k in text for k in ("survey", "principles and challenges", "from bits to semantics", "theories, technologies", "ten challenges", "beyond transmitting bits", "generalized semantic communication", "intellicise", "goal-oriented communications for future")):
        return "基础理论与综述"
    if any(k in text for k in ("security", "secure", "eavesdrop", "adversarial", "trustworthiness", "semantic noise", "semantic impairment")):
        return "鲁棒性、安全与语义噪声"
    if any(k in text for k in ("speech", "speech-to-text", "text communication", "for text", "large language model", "large speech model", "streaming speech", "translation")):
        return "文本、语音与大模型"
    if any(k in text for k in ("image", "video", "extended reality", "holographic", "gaussian splatting", "scene classification", "compressed sensing", "vision transformer")):
        return "图像、视频与沉浸媒体"
    if any(k in text for k in ("multi-task", "multimodal", "multi-modal", "vqa", "scene graph", "internet of vehicles", "multi-user", "semantic feature multiple access")):
        return "多模态、多任务与多用户"
    if any(k in text for k in ("vector quant", "codebook", "token", "constellation", "digital", "hybrid digital-analog", "modulation")):
        return "数字化、量化与调制"
    return "语义网络、资源分配与边缘智能"


def scope_for(title: str, abstract: str) -> str:
    text = f"{title} {abstract}".lower()
    if any(k in text for k in ("resource allocation", "task offloading", "computational offloading", "computing networks", "qoe", "non-terrestrial networks", "caching and offloading")):
        return "系统与网络层"
    if any(k in text for k in ("survey", "principles and challenges", "ten challenges", "theories, technologies", "from bits to semantics", "beyond transmitting bits")):
        return "综述/观点"
    return "核心算法/系统"


EXCLUDE_PATTERNS = {
    "series editorial": "期刊系列编者按，不是研究论文",
    "guest editorial": "专题编者按，不是研究论文",
    "the fifth issue of the series": "期刊系列编者按，不是研究论文",
    "federated multi-view synthesizing": "研究主题是联邦多视图生成，不以语义通信为核心",
    "meta federated reinforcement learning": "通用分布式资源分配论文，不以语义通信为核心",
    "energy-efficient distributed spiking": "无线边缘智能论文，不以语义通信为核心",
    "on privacy, security, and trustworthiness in distributed wireless large ai models": "无线大模型安全综述，不以语义通信为核心",
    "enabling green wireless communications with neuromorphic": "神经形态持续学习论文，不以语义通信为核心",
    "the 1st solution for mose": "视频分割挑战方案，不属于语义通信",
    "lsvos 2025 challenge report": "视频分割挑战报告，不属于语义通信",
    "=deep learning enabled semantic communications": "专著而非单篇论文",
    "progic:": "生成式图像压缩论文，未显式建模通信信道或语义任务，列为相关边界",
    "end-to-end semantic information transmission": "专著章节，非独立论文",
    "prior knowledge base": "专著章节，非独立论文",
    "structural coding": "专著章节，非独立论文",
    "qoe optimization for wireless multimedia communications": "专著章节，非独立论文",
    "real-world applications": "专著章节，非独立论文",
    "efficient learned image compression without entropy coding": "图像压缩论文，未显式研究通信信道或语义任务",
    "flowcodec": "生成式图像压缩论文，未显式研究通信信道或语义任务",
    "contextcodec": "神经语音编码论文，作为相关边界而非语义通信核心",
}


ALIASES = {
    norm("Task-Oriented Multi-User Semantic Communications for Multimodal Data"): norm("Task-Oriented Multi-User Semantic Communications for VQA"),
    norm("Task-Oriented Multi-User Semantic Communications for VQA Task"): norm("Task-Oriented Multi-User Semantic Communications for VQA"),
    norm("Task-Oriented Semantic Communications for Multimodal Data"): norm("Task-Oriented Multi-User Semantic Communications for VQA"),
    norm("A Robust Semantic Communication System for Image"): norm("A Robust Semantic Communication System for Image Transmission"),
    norm("Towards Intelligent Communications: Large Model Empowered Semantic Communications"): norm("Toward Intelligent Communications: Large Model Empowered Semantic Communications"),
    norm("Semantic Communication for Internet of Vehicles: A Multi-User Cooperative Approach"): norm("Semantic Communication for the Internet of Vehicles: A Multiuser Cooperative Approach"),
}


FORMAL_OVERRIDES = {
    norm("Adaptive Sampling and Joint Semantic-Channel Coding under Dynamic Channel Environment"): {
        "doi": "10.1109/ICC52391.2025.11161632",
        "venue": "IEEE ICC, 2025",
        "year": 2025,
    },
    norm("Multi-Task Semantic Communications via Large Models"): {
        "doi": "10.1109/MCOMSTD.2025.3605634",
        "venue": "IEEE Communications Standards Magazine, 2025",
        "year": 2025,
    },
    norm("Large AI Model-Enabled Generative Semantic Communications for Image Transmission"): {
        "doi": "10.1109/GLOBECOM59602.2025.11432458",
        "venue": "IEEE GLOBECOM, 2025",
        "year": 2025,
    },
}


def load_openalex_details() -> dict[str, dict]:
    details: dict[str, dict] = {}
    for filename in ("openalex_zhijin_works_2021.json", "openalex_zhijin_works_2021_p2.json"):
        data = json.loads((NOTES / filename).read_text(encoding="utf-8"))
        for work in data["results"]:
            details[work["id"]] = work
    return details


def load_arxiv() -> list[dict]:
    root = ET.parse(NOTES / "arxiv_zhijin_qin.xml").getroot()
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    rows = []
    for entry in root.findall("a:entry", ns):
        title = " ".join((entry.findtext("a:title", default="", namespaces=ns)).split())
        abstract = " ".join((entry.findtext("a:summary", default="", namespaces=ns)).split())
        published = entry.findtext("a:published", default="", namespaces=ns)
        if not published or int(published[:4]) < 2021:
            continue
        authors = "; ".join(a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns))
        arxiv_id = entry.findtext("a:id", default="", namespaces=ns).split("/abs/")[-1].split("v")[0]
        doi = entry.findtext("arxiv:doi", default="", namespaces=ns)
        journal_ref = entry.findtext("arxiv:journal_ref", default="", namespaces=ns)
        rows.append({
            "id": f"arxiv:{arxiv_id}", "title": title, "year": int(published[:4]),
            "authors": authors, "doi": doi, "arxiv_id": arxiv_id,
            "venue": journal_ref or "arXiv", "abstract": abstract,
            "oa_url": f"https://arxiv.org/pdf/{arxiv_id}", "cited_by_count": 0,
        })
    return rows


def load_candidates() -> tuple[list[dict], list[dict]]:
    details = load_openalex_details()
    raw: list[dict] = []
    with (ROOT / "candidate_pool.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            work = details.get(row["openalex_id"], {})
            raw.append({
                "id": row["openalex_id"], "title": row["title"], "year": int(row["year"]),
                "authors": row["authors"], "doi": row["doi"], "arxiv_id": "",
                "venue": row["venue"], "abstract": abstract_from_inverted(work.get("abstract_inverted_index")),
                "oa_url": row["oa_url"], "cited_by_count": int(row["cited_by_count"] or 0),
            })
    # Add author-matched arXiv papers missed by lagging bibliographic indexes.
    relevance = re.compile(r"semantic|task[- ]oriented|goal[- ]oriented|joint source|joint semantic|learned image transmission|generative image compression|speech coding", re.I)
    known_ids = {r["id"] for r in raw}
    for row in load_arxiv():
        if relevance.search(f'{row["title"]} {row["abstract"]}') and row["id"] not in known_ids:
            raw.append(row)
    grouped: dict[str, list[dict]] = {}
    for row in raw:
        key = ALIASES.get(norm(row["title"]), norm(row["title"]))
        grouped.setdefault(key, []).append(row)
    included: list[dict] = []
    excluded: list[dict] = []
    for key, variants in grouped.items():
        # Prefer a formal DOI record over arXiv, then the newest bibliographic record.
        variants.sort(key=lambda r: (not bool(r["doi"]), r["doi"].lower().startswith("10.48550"), -r["year"]))
        selected = dict(variants[0])
        selected["arxiv_id"] = next((r["arxiv_id"] for r in variants if r.get("arxiv_id")), "")
        if not selected["arxiv_id"]:
            arxiv_doi = next((r["doi"] for r in variants if r.get("doi", "").lower().startswith("10.48550/arxiv.")), "")
            if arxiv_doi:
                selected["arxiv_id"] = arxiv_doi.split("arxiv.", 1)[1]
        if not selected["abstract"]:
            selected["abstract"] = next((r["abstract"] for r in variants if r.get("abstract")), "")
        if not selected["authors"]:
            selected["authors"] = next((r["authors"] for r in variants if r.get("authors")), "")
        if key in FORMAL_OVERRIDES:
            selected.update(FORMAL_OVERRIDES[key])
        lower_title = selected["title"].lower()
        reason = next((
            reason for pattern, reason in EXCLUDE_PATTERNS.items()
            if (lower_title == pattern[1:] if pattern.startswith("=") else pattern in lower_title)
        ), "")
        if reason:
            selected["screening_reason"] = reason
            excluded.append(selected)
            continue
        selected["category"] = category_for(selected["title"], selected["abstract"])
        selected["scope_status"] = scope_for(selected["title"], selected["abstract"])
        selected["pdf"] = ""
        selected["download_status"] = "pending"
        selected["analysis_status"] = "metadata_screened"
        included.append(selected)
    included.sort(key=lambda r: (r["year"], r["title"].lower()))
    excluded.sort(key=lambda r: (r["year"], r["title"].lower()))
    return included, excluded


def write_csvs(included: list[dict], excluded: list[dict]) -> None:
    fields = ["year", "title", "authors", "venue", "doi", "arxiv_id", "category", "scope_status", "abstract", "oa_url", "id", "cited_by_count", "pdf", "download_status", "analysis_status"]
    with (ROOT / "included_papers.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(included)
    with (ROOT / "excluded_or_boundary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields2 = ["year", "title", "doi", "screening_reason"]
        writer = csv.DictWriter(f, fieldnames=fields2, extrasaction="ignore")
        writer.writeheader(); writer.writerows(excluded)


def main() -> None:
    included, excluded = load_candidates()
    write_csvs(included, excluded)
    counts = Counter(row["year"] for row in included)
    print(f"included={len(included)} excluded={len(excluded)}")
    print("years=" + ", ".join(f"{year}:{counts[year]}" for year in sorted(counts)))


if __name__ == "__main__":
    main()
