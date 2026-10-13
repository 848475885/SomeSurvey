#!/usr/bin/env python3
"""Screen the TVT candidate census and prepare the full-text queue."""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import iotj_semcom_prepare as shared  # noqa: E402
import tvt_semcom_search as search  # noqa: E402


SURVEY = ROOT / "literature" / "ieee-tvt-semantic-communications-2023-present"
NOTES = SURVEY / "notes"
PAPERS = SURVEY / "papers"

# These records were returned by broad JSCC/semantic-aware queries, but their
# transmitted object and contribution do not form a semantic/JSCC link.
EXCLUDED_TITLES = {
    "Rethinking Estimation Rate for Wireless Sensing: A Rate-Distortion Perspective":
        "wireless sensing metric paper without a semantic representation or source-channel transmission chain",
    "Deep Joint CSI Feedback and Multiuser Precoding for MIMO OFDM Systems":
        "joint neural CSI feedback/precoding paper; it does not study semantic communication or source-channel coding",
    "Joint Design of Sensing, Communication, and Computation for Multi-AAV-Enabled Over-the-Air Federated Learning":
        "over-the-air federated-learning system without a semantic/DeepJSCC transmitted representation",
    "Semantic-Aware Beam Prediction Approach With Multimodal Fusion":
        "beam-prediction inference paper; semantic scene features are model inputs rather than a designed semantic communication link",
}

RELATED_RE = re.compile(
    r"auction|resource allocation|resource management|bandwidth allocation|bandwidth management|"
    r"beamforming|trajectory|rate maximization|random access|digital twin synchronization|"
    r"channel optimization|channel assignment|integrated sensing|economic|economics|"
    r"secure semantic communication networks|cross-layer security|privacy protection|"
    r"knowledge discrepancy|heterogeneous semantic and bit|multiple access|semi-noma|"
    r"joint source-channel coding systems|LDPC coded compressive sensing|double polar codes|"
    r"CSI Feedback via Joint Source-Channel Coding|context-aware paradigm shift|"
    r"communication and control co-design|semantic-based resource|delay-aware|"
    r"reliable semantic communication with QoE|QoE-aware latency|aerial.?maritime energy|"
    r"integrated sensing, computing and semantic|multi-RIS|fluid antenna|"
    r"data allocation|federated learning framework",
    re.I,
)


def main() -> None:
    NOTES.mkdir(parents=True, exist_ok=True)
    PAPERS.mkdir(parents=True, exist_ok=True)
    candidates = shared.read_jsonl(NOTES / "candidate_pool.jsonl")

    shared.SURVEY = SURVEY
    local = shared.existing_pdf_map()
    included: list[dict] = []
    excluded: list[dict] = []

    for original in candidates:
        record = dict(original)
        title = str(record.get("title") or "")
        if title in EXCLUDED_TITLES:
            record["screening_status"] = "excluded"
            record["screening_reason"] = EXCLUDED_TITLES[title]
            excluded.append(record)
            continue

        tier = "related" if RELATED_RE.search(title) else "core"
        record["screening_status"] = tier
        record["screening_reason"] = (
            "direct semantic/DeepJSCC representation, transmission, receiver, security, or end-to-end system"
            if tier == "core"
            else "network, theory, conventional-JSCC, control, or resource layer directly adjacent to the semantic/JSCC link"
        )
        record["publication_year_basis"] = (
            "formal TVT volume year when available; otherwise the current Early Access year"
        )
        doi = shared.norm_doi(record.get("doi"))
        source = local.get(doi)
        if source:
            lead = (record.get("authors") or ["Unknown"])[0].split()[-1]
            target = PAPERS / (
                f"{record.get('year')}_{shared.safe_name(lead, 24)}_"
                f"{shared.safe_name(title)}.pdf"
            )
            if not target.exists() or shared.sha256(target) != shared.sha256(source):
                shutil.copy2(source, target)
            record.update(
                {
                    "pdf_status": "reused_local_validated",
                    "pdf_path": str(target.resolve()),
                    "pdf_valid": True,
                    "pdf_header_ok": True,
                    "pdf_bytes": target.stat().st_size,
                    "sha256": shared.sha256(target),
                    "reused_from": str(source),
                }
            )
        else:
            record.update(
                {
                    "pdf_status": "queued_fulltext",
                    "pdf_path": "",
                    "pdf_valid": False,
                    "reused_from": "",
                }
            )
        included.append(record)

    ordering = lambda row: (int(row.get("year") or 9999), str(row.get("title") or "").lower())
    included.sort(key=ordering)
    excluded.sort(key=ordering)
    shared.write_jsonl(NOTES / "included.jsonl", included)
    shared.write_jsonl(NOTES / "excluded.jsonl", excluded)

    with (NOTES / "ieee_download_queue.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["title", "doi"])
        writer.writeheader()
        for row in included:
            if not row.get("pdf_valid"):
                writer.writerow({"title": row.get("title", ""), "doi": row.get("doi", "")})

    core = sum(row["screening_status"] == "core" for row in included)
    related = sum(row["screening_status"] == "related" for row in included)
    reused = sum(bool(row.get("pdf_valid")) for row in included)
    strategy = f"""# IEEE TVT 语义通信与 DeepJSCC 调研：检索与筛选记录

## 范围

- 刊物：IEEE Transactions on Vehicular Technology（ISSN 0018-9545 / 1939-9359）。
- 时间：2023-01-01 至 2026-10-13；正式卷年优先，尚未编入卷期的记录按 Early Access 年归档。
- 核心主题：语义通信、任务/目标导向通信、DeepJSCC、数字语义表示、无线图像/视频/语音/点云传输，以及信道鲁棒接收。
- 直接相关层：围绕语义链路开展的 V2X/UAV 资源、波束、轨迹、接入、控制和安全优化，以及与 DeepJSCC 技术路线相邻的传统 JSCC 工作。

## 检索轮次

1. OpenAlex 全刊元数据扫描：读取日期范围内 TVT 论文的题名与可用摘要，再以语义通信、任务通信和 JSCC 词族筛选。
2. Crossref 按 TVT ISSN 独立检索：覆盖项目要求的 digital semantic communication、VQ/PQ、codebook、quantization、index/bit error、OFDM、semantic-aware channel coding 与 DeepJSCC 关键词。
3. 车辆场景扩展：补充 vehicular/V2X/UAV、autonomous driving、image/video transmission、feature transmission、semantic HARQ 等组合。
4. IEEE Xplore 与全文复核：以 DOI、题名、卷期、PDF 首页和 IEEE document number 校验归属。
5. 引用与被引扩展：围绕数字量化、图像/视频 DeepJSCC、车辆协同感知和信道错误处理论文扩展；连续检索轮次没有新增核心 TVT 题名后确认饱和。

本次共执行 {len(search.base.QUERIES)} 组查询。数据库请求统计见 `search_audit.json`。

## 筛选标准

- 核心纳入：直接设计语义表示、语义编解码器、DeepJSCC、量化/调制、生成式接收、信道鲁棒机制或完整语义传输系统。
- 直接相关：以语义链路为明确前提，主要贡献位于资源、控制、网络、安全或理论层；传统 JSCC 仅用于解释 DeepJSCC 的技术邻域。
- 排除：无线感知指标、CSI 反馈/预编码、联邦学习或波束预测论文中没有语义/JSCC 传输链路的记录。

## 流量与可追溯性

- 去重候选：{len(candidates)} 篇。
- 核心纳入：{core} 篇。
- 直接相关：{related} 篇。
- 排除：{len(excluded)} 篇。
- 已复用并校验的本地全文：{reused} 篇；其余进入合法开放版本和 IEEE Xplore 串行下载流程。

候选池、纳入表、排除表、下载队列与请求审计分别保存在 `candidate_pool.jsonl`、`included.jsonl`、`excluded.jsonl`、`ieee_download_queue.csv` 和 `search_audit.json`。
"""
    (NOTES / "search_strategy.md").write_text(strategy, encoding="utf-8")
    print(
        json.dumps(
            {
                "candidate": len(candidates),
                "included": len(included),
                "core": core,
                "related": related,
                "excluded": len(excluded),
                "reused": reused,
                "queued": len(included) - reused,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
