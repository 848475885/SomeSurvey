from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REASONS = {
    "Generative AI Meets 6G and Beyond: Diffusion Models for Semantic Communications.": "IEEE COMST 综述，非本次正式技术研究论文",
    "Non-orthogonal Multiple Access for Semantic Communications.": "会议版本被 IEEE TWC 期刊扩展版 Interference Suppressed NOMA for Semantic-Aware Communication Networks 取代",
    "Energy-Efficient Task Offloading for Semantic-Aware Networks": "会议版本被 IEEE TWC 期刊扩展版 Resource Optimization for Semantic-Aware Networks With Task Offloading 取代",
    "A Physical Layer Security Framework for Integrated Sensing and Semantic Communication Systems": "会议版本被 IEEE TCCN 期刊扩展版 A Physical Layer Security Framework for IRS-Assisted Integrated Sensing and Semantic Communication Systems 取代",
    "A Physical Layer Security Framework for Integrated Sensing and Semantic Communication Systems.": "会议版本被 IEEE TCCN 期刊扩展版取代；DBLP 重复书目",
    "Mixed High-Order Attention Network for Weakly- Supervised Semantic Segmentation": "计算机视觉语义分割，非语义通信",
    "Real-Time Semantic Segmentation via an Efficient Multi-Column Network": "计算机视觉语义分割，非语义通信",
    "A Hybrid Semantic Segmentation Based on Level-Set Evolution Driven by Fully Convolutional Networks": "计算机视觉语义分割，非语义通信",
}


def read(path: Path) -> list[dict]:
    if not path.exists(): return []
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))


def write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def main() -> None:
    for audit_path in ROOT.glob("*/notes/saturation_audit.json"):
        root = audit_path.parent.parent
        audit = json.loads(audit_path.read_text("utf-8"))
        included = read(root / "included_papers.csv")
        fields = list(included[0])
        excluded = read(root / "excluded_or_boundary.csv")
        candidates = read(root / "candidate_pool.csv")
        known_exc = {(r.get("doi", "").lower(), r.get("title", "").rstrip(".")) for r in excluded}
        known_can = {(r.get("doi", "").lower(), r.get("title", "").rstrip(".")) for r in candidates}
        added = 0
        for round_ in audit["rounds"]:
            for item in round_.get("novel_formal_technical_records", []):
                title = item.get("title", "")
                if title not in REASONS:
                    continue
                row = {f: "" for f in fields}
                row.update({"year": item.get("year", ""), "title": title.rstrip("."), "authors": "; ".join(item.get("authors") or []),
                            "doi": (item.get("doi") or "").lower(), "official_url": "https://doi.org/" + (item.get("doi") or "").lower(),
                            "team_scope": "direct", "screening_status": "excluded_after_saturation_audit",
                            "screening_reason": REASONS[title], "analysis_status": "screened_out"})
                key = (row["doi"], row["title"])
                if key not in known_exc: excluded.append(row); known_exc.add(key); added += 1
                if key not in known_can: candidates.append(row); known_can.add(key)
        write(root / "excluded_or_boundary.csv", excluded, list(excluded[0]) if excluded else fields)
        write(root / "candidate_pool.csv", candidates, list(candidates[0]) if candidates else fields)
        print(root.name, "late_exclusions", added)


if __name__ == "__main__": main()
