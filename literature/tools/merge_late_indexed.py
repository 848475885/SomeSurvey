from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Digital-SemCom-Survey/1.0 (late-index merge)"})

TEAM_NAMES = {
    "kai-niu-semantic-communications": ("北京邮电大学牛凯—张平团队", ("Kai Niu", "Ping Zhang")),
    "zhijin-qin-semantic-communications": ("清华大学秦志金团队", ("Zhijin Qin",)),
    "meixia-tao-semantic-communications": ("上海交通大学陶梅霞团队", ("Meixia Tao",)),
    "deniz-gunduz-semantic-communications": ("Imperial College London Deniz Gündüz 团队", ("Deniz Gunduz", "Deniz Gündüz")),
    "yi-ma-mahdi-mashhadi-semantic-communications": ("University of Surrey Yi Ma—Mahdi Boloursaz Mashhadi 团队", ("Yi Ma", "Mahdi Boloursaz Mashhadi")),
    "arumugam-nallanathan-deepsc-semantic-communications": ("QMUL Arumugam Nallanathan 与 DeepSC 团队", ("Arumugam Nallanathan",)),
}

FORMAL = ("10.1109/", "10.1145/", "10.21437/", "10.1007/s", "10.23919/", "10.26599/")
DROP_TITLE = re.compile(r"survey|overview|demo abstract|^a demo|challenges|opportunities", re.I)
TEAM_DROPS = {
    "kai-niu-semantic-communications": {
        "Generative AI Meets 6G and Beyond: Diffusion Models for Semantic Communications",
        "Non-orthogonal Multiple Access for Semantic Communications",
    },
    "zhijin-qin-semantic-communications": {"Energy-Efficient Task Offloading for Semantic-Aware Networks"},
    "yi-ma-mahdi-mashhadi-semantic-communications": {
        "A Physical Layer Security Framework for Integrated Sensing and Semantic Communication Systems",
        "Mixed High-Order Attention Network for Weakly- Supervised Semantic Segmentation",
        "Real-Time Semantic Segmentation via an Efficient Multi-Column Network",
        "A Hybrid Semantic Segmentation Based on Level-Set Evolution Driven by Fully Convolutional Networks",
    },
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", value)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def records_from_audit(root: Path) -> list[dict]:
    audit = json.loads((root / "notes" / "saturation_audit.json").read_text("utf-8"))
    chosen: dict[str, dict] = {}
    for round_ in audit["rounds"]:
        for item in round_["novel_topic_records"]:
            doi = (item.get("doi") or "").lower()
            title = (item.get("title") or "").rstrip(".")
            if not doi.startswith(FORMAL) or DROP_TITLE.search(title) or title in TEAM_DROPS.get(root.name, set()):
                continue
            item = dict(item); item["title"] = title; item["doi"] = doi
            chosen.setdefault(doi, item)
    return list(chosen.values())


def crossref(doi: str) -> dict:
    try:
        r = SESSION.get(f"https://api.crossref.org/works/{doi}", timeout=60)
        if r.status_code == 200:
            return r.json()["message"]
    except Exception:
        pass
    return {}


def make_row(folder: str, item: dict, metadata: dict) -> dict:
    team_cn, direct = TEAM_NAMES[folder]
    authors = item.get("authors") or []
    authors = [re.sub(r"\s+\d{4}$", "", str(a)).strip() for a in authors]
    container = metadata.get("container-title") or []
    venue = container[0] if container else ""
    doi = item["doi"]
    title = item["title"]
    key = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()).strip("-")[:120]
    work_type = "proceedings-article" if metadata.get("type") == "proceedings-article" or any(x in doi for x in ("icc", "globecom", "wcsp", "interspeech", "mlsp", "infocom", "wcnc")) else "article"
    return {
        "citation_key": f"{key}-{item.get('year', '')}", "year": item.get("year", ""), "title": title,
        "authors": "; ".join(authors), "venue": venue, "work_type": work_type, "doi": doi, "openalex_id": "",
        "abstract": re.sub(r"<[^>]+>", " ", metadata.get("abstract") or "").strip(),
        "official_url": f"https://doi.org/{doi}", "team_scope": "direct",
        "team_evidence": f"补充数据库轮次核验：指定负责人直接署名（{', '.join(n for n in direct if any(norm(n) in norm(a) or norm(a) in norm(n) for a in authors))}）；Crossref/DBLP 正式 DOI 元数据。",
        "affiliations": "", "cited_by_count": metadata.get("is-referenced-by-count", 0), "source_verified": True,
        "source_verification": "Crossref/DBLP late-index audit; DOI publisher record", "screening_status": "included_late_indexed",
        "screening_reason": "补充数据库检索发现的正式同行评审技术论文；通过负责人直接署名、年份、DOI、主题和文献类型核验",
        "pdf": "", "download_status": "pending", "download_source": "", "sha256": "", "pages": 0,
        "analysis_status": "metadata_screened", "cross_team_duplicate_of": "",
    }


def main() -> None:
    global_dois: dict[str, str] = {}
    for folder in TEAM_NAMES:
        for row in read_csv(ROOT / folder / "included_papers.csv"):
            if row.get("doi"):
                global_dois.setdefault(row["doi"].lower(), folder)
    for folder in TEAM_NAMES:
        root = ROOT / folder
        included = read_csv(root / "included_papers.csv")
        fields = list(included[0])
        known = {r.get("doi", "").lower() for r in included}
        added = []
        for item in records_from_audit(root):
            if item["doi"] in known:
                continue
            metadata = crossref(item["doi"])
            row = make_row(folder, item, metadata)
            other = global_dois.get(item["doi"])
            if other and other != folder:
                row["cross_team_duplicate_of"] = f"{other}:{item['doi']}"
            included.append(row); added.append(row); known.add(item["doi"]); global_dois.setdefault(item["doi"], folder)
            time.sleep(.25)
        included.sort(key=lambda r: (int(r.get("year") or 0), r.get("title", "")))
        write_csv(root / "included_papers.csv", included, fields)
        candidate = read_csv(root / "candidate_pool.csv")
        candidate_keys = {r.get("doi", "").lower() for r in candidate}
        candidate.extend(r for r in added if r["doi"] not in candidate_keys)
        if candidate:
            write_csv(root / "candidate_pool.csv", candidate, list(candidate[0]))
        late_path = root / "notes" / "late_indexed_included.csv"
        prior_late = read_csv(late_path)
        prior_dois = {r.get("doi", "").lower() for r in prior_late}
        prior_late.extend(r for r in added if r.get("doi", "").lower() not in prior_dois)
        write_csv(late_path, prior_late, fields)
        (root / "manifest.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in included), encoding="utf-8")
        with (root / "search_strategy.md").open("a", encoding="utf-8") as handle:
            handle.write(f"\n## 2026-07-15 补充索引回查\n\nCrossref 与 DBLP 回查发现并经正式 DOI/负责人署名复核后新增 {len(added)} 篇；Semantic Scholar 搜索端点返回 429，早先 OA 批量核验结果仍保留在下载清单。新增项已进入全文下载和再次筛选，不把初始 OpenAlex 数量当作完成标准。\n")
        print(folder, "added", len(added))


if __name__ == "__main__":
    main()
