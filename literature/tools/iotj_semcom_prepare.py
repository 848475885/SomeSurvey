#!/usr/bin/env python3
"""Screen the IoTJ candidate census and prepare the authenticated PDF queue."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-iotj-semantic-communications-2023-present"
NOTES = SURVEY / "notes"
PAPERS = SURVEY / "papers"

EXCLUDED_TITLES = {
    "A Survey on Digital Twins: Architecture, Enabling Technologies, Security and Privacy, and Future Prospects": "broad digital-twin survey; semantic communication is only peripheral context",
    "Distributed Machine Learning for UAV Swarms: Computing, Sensing, and Semantics": "distributed-learning survey/overview without a semantic communication link design",
    "Federated Learning for the Healthcare Metaverse: Concepts, Applications, Challenges, and Future Directions": "healthcare-metaverse federated-learning survey outside the communication-system scope",
    "Adversarial Attacks and Defenses in 6G Network-Assisted IoT Systems": "security survey; semantic communication appears as background rather than the studied link",
    "Applications of Generative AI (GAI) for Mobile and Wireless Networking: A Survey": "broad wireless GAI survey retained only as a search trace",
    "CASIT: Collective Intelligent Agent System for Internet of Things": "IoT agent framework without an evaluated semantic/JSCC transmission chain",
    "Joint Sensing, Communication, and Computation in UAV-Assisted Systems": "integrated-system paper without a semantic representation or DeepJSCC mechanism",
    "SSFU: Selective Semantic Feature Unlearning for Federated Learning in 6G Internet of Things Systems": "federated unlearning paper; communication semantics are not the transmitted-object contribution",
    "Artificial Intelligence of Things as a Foundation for Agentic AI Systems: Architectures, Applications, and Challenges": "AIoT architecture survey outside the semantic-link/DeepJSCC scope",
}

RELATED_RE = re.compile(
    r"resource allocation|resource management|offloading|beamforming|trajectory optimization|spectrum sharing|"
    r"rate[-–]distortion|similarity score|source value|semantic-aware architecture|digital-twin synchronization|"
    r"wireless power transfer|\bWPT\b|energy efficient|performance optimization|federated learning framework|"
    r"semantic communication approach for multiscene target detection|semantic and logical communication-control|"
    r"lattice-based analog mappings|semantic approach to successive interference cancellation",
    re.I,
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def norm_doi(value: object) -> str:
    return str(value or "").lower().replace("https://doi.org/", "").strip()


def safe_name(value: str, limit: int = 112) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value[:limit].rstrip("_") or "paper"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def existing_pdf_map() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for manifest in (ROOT / "literature").rglob("manifest.jsonl"):
        if SURVEY in manifest.parents:
            continue
        for row in read_jsonl(manifest):
            doi = norm_doi(row.get("doi"))
            if not doi:
                continue
            raw = row.get("pdf_path") or row.get("local_pdf") or row.get("path") or row.get("pdf")
            if not raw:
                continue
            candidate = Path(str(raw))
            if not candidate.is_absolute():
                candidate = manifest.parent / candidate
            if candidate.exists() and candidate.read_bytes()[:5] == b"%PDF-":
                found.setdefault(doi, candidate.resolve())
    return found


def main() -> None:
    PAPERS.mkdir(parents=True, exist_ok=True)
    candidates = read_jsonl(NOTES / "candidate_pool.jsonl")
    local = existing_pdf_map()
    included: list[dict] = []
    excluded: list[dict] = []

    for record in candidates:
        title = record.get("title", "")
        if title in EXCLUDED_TITLES:
            record["screening_status"] = "excluded"
            record["screening_reason"] = EXCLUDED_TITLES[title]
            excluded.append(record)
            continue
        tier = "related" if RELATED_RE.search(title) else "core"
        record["screening_status"] = tier
        record["screening_reason"] = (
            "direct semantic/DeepJSCC representation, transmission, receiver, or end-to-end system"
            if tier == "core"
            else "network/theory/control layer directly optimized around a semantic communication link"
        )
        record["publication_year_basis"] = "formal IoTJ volume year when available; otherwise current Early Access year"
        doi = norm_doi(record.get("doi"))
        source = local.get(doi)
        if source:
            lead = (record.get("authors") or ["Unknown"])[0].split()[-1]
            target = PAPERS / f"{record.get('year')}_{safe_name(lead,24)}_{safe_name(title)}.pdf"
            if not target.exists() or sha256(target) != sha256(source):
                shutil.copy2(source, target)
            record.update(
                {
                    "pdf_status": "reused_local_validated",
                    "pdf_path": str(target.resolve()),
                    "pdf_valid": True,
                    "pdf_header_ok": True,
                    "pdf_bytes": target.stat().st_size,
                    "sha256": sha256(target),
                    "reused_from": str(source),
                }
            )
        else:
            record.update({"pdf_status": "queued_ieee", "pdf_path": "", "pdf_valid": False, "reused_from": ""})
        included.append(record)

    included.sort(key=lambda r: (int(r.get("year") or 9999), (r.get("title") or "").lower()))
    excluded.sort(key=lambda r: (int(r.get("year") or 9999), (r.get("title") or "").lower()))
    write_jsonl(NOTES / "included.jsonl", included)
    write_jsonl(NOTES / "excluded.jsonl", excluded)

    with (NOTES / "ieee_download_queue.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["title", "doi"])
        writer.writeheader()
        for row in included:
            if row.get("pdf_status") == "queued_ieee":
                writer.writerow({"title": row.get("title", ""), "doi": row.get("doi", "")})

    strategy = f"""# IEEE IoTJ 语义通信与 DeepJSCC 调研：检索与筛选记录

## 范围

- 刊物：IEEE Internet of Things Journal（ISSN 2327-4662 / 2372-2541）
- 时间：2023-01-01 至 2026-10-09；以正式卷年为主，尚未编入卷期的论文按 Early Access 年记录。
- 主题：语义通信、任务/目标导向通信、DeepJSCC、数字语义表示、无线图像/视频/语音传输，以及直接围绕语义链路展开的资源与网络优化。

## 检索轮次

1. OpenAlex 全刊元数据扫描：对日期范围内 IoTJ 全部记录读取标题与可用摘要，再以语义通信/JSCC/任务通信词族筛选。
2. Crossref 独立关键词检索：覆盖 digital semantic communication、VQ/PQ、codebook、quantization、index/bit error、OFDM、semantic-aware channel coding、DeepJSCC 等 {len(__import__('iotj_semcom_search').QUERIES)} 组查询。
3. IEEE Xplore/网页搜索复核：核对期刊归属、卷期、DOI、document number 与 Early Access 记录。
4. 引用与被引扩展：围绕数字语义、量化/调制、图像/视频 DeepJSCC 核心论文检查同刊新增工作；无新核心题名时记为检索饱和。

## 筛选标准

- 核心纳入：论文直接设计语义表示、语义编解码器、JSCC/DeepJSCC、量化/调制、信道鲁棒接收或端到端语义传输系统。
- 相关纳入：论文以语义链路为明确前提，重点优化资源、控制、调度、波束、轨迹或理论度量。
- 排除：综合性 IoT/安全/联邦学习/数字孪生综述，或仅把“semantic”用于知识表示、分割、协议字段、缓存命名等非通信语义含义的论文。

## 当前流量

- 去重候选：{len(candidates)} 篇。
- 核心纳入：{sum(r['screening_status']=='core' for r in included)} 篇。
- 相关纳入：{sum(r['screening_status']=='related' for r in included)} 篇。
- 排除：{len(excluded)} 篇。
- 已有合法本地全文：{sum(r.get('pdf_valid') for r in included)} 篇；其余进入 IEEE Xplore 串行下载队列。

候选池、纳入表、排除表与数据库请求统计分别保存在 `candidate_pool.jsonl`、`included.jsonl`、`excluded.jsonl` 和 `search_audit.json`。
"""
    (NOTES / "search_strategy.md").write_text(strategy, encoding="utf-8")
    print(json.dumps({
        "candidate": len(candidates),
        "included": len(included),
        "core": sum(r["screening_status"] == "core" for r in included),
        "related": sum(r["screening_status"] == "related" for r in included),
        "excluded": len(excluded),
        "reused": sum(bool(r.get("pdf_valid")) for r in included),
        "queued": sum(r.get("pdf_status") == "queued_ieee" for r in included),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
