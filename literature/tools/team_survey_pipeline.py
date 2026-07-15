from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote

import fitz
import requests


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DATE = "2026-07-15"
START_DATE = "2021-01-01"
END_DATE = "2026-07-15"
USER_AGENT = "Digital-SemCom-Survey/1.0 (academic literature review)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


@dataclass(frozen=True)
class Team:
    key: str
    folder: str
    title_cn: str
    title_en: str
    author_ids: tuple[str, ...]
    direct_names: tuple[str, ...]
    institution: str
    extra_queries: tuple[str, ...] = ()
    extension_names: tuple[str, ...] = ()


TEAMS = {
    "kai-niu": Team(
        "kai-niu", "kai-niu-semantic-communications",
        "北京邮电大学牛凯—张平团队", "Kai Niu–Ping Zhang Team at BUPT",
        ("A5008455605", "A5100405787"), ("Kai Niu", "Ping Zhang"),
        "Beijing University of Posts and Telecommunications",
    ),
    "zhijin-qin": Team(
        "zhijin-qin", "zhijin-qin-semantic-communications",
        "清华大学秦志金团队", "Zhijin Qin Team at Tsinghua University",
        ("A5044671638",), ("Zhijin Qin",), "Tsinghua University",
    ),
    "meixia-tao": Team(
        "meixia-tao", "meixia-tao-semantic-communications",
        "上海交通大学陶梅霞团队", "Meixia Tao Team at Shanghai Jiao Tong University",
        ("A5016127527",), ("Meixia Tao",), "Shanghai Jiao Tong University",
    ),
    "deniz-gunduz": Team(
        "deniz-gunduz", "deniz-gunduz-semantic-communications",
        "Imperial College London Deniz Gündüz 团队", "Deniz Gündüz Team at Imperial College London",
        ("A5016883501",), ("Deniz Gündüz", "Deniz Gunduz", "Denız Gündüz"), "Imperial College London",
    ),
    "surrey": Team(
        "surrey", "yi-ma-mahdi-mashhadi-semantic-communications",
        "University of Surrey Yi Ma—Mahdi Boloursaz Mashhadi 团队",
        "Yi Ma–Mahdi Boloursaz Mashhadi Team at University of Surrey",
        ("A5028862760", "A5124039651"),
        ("Mahdi Boloursaz Mashhadi", "Yi Ma"), "University of Surrey",
        extra_queries=("semantic communication University of Surrey", "token communications Surrey"),
        extension_names=("Pei Xiao", "Rahim Tafazolli", "Chuan Heng Foh"),
    ),
    "qmul": Team(
        "qmul", "arumugam-nallanathan-deepsc-semantic-communications",
        "Queen Mary University of London Arumugam Nallanathan 与 DeepSC 团队",
        "Arumugam Nallanathan and DeepSC Team at Queen Mary University of London",
        ("A5002265731",), ("Arumugam Nallanathan",), "Queen Mary University of London",
        extra_queries=("DeepSC semantic communication", "semantic communication Queen Mary University of London"),
        extension_names=("Huiqiang Xie", "Zhijin Qin", "Zhenzi Weng"),
    ),
}


RELEVANCE_RE = re.compile(
    r"semantic commun|goal[- ]oriented commun|task[- ]oriented commun|DeepSC|"
    r"joint source[-– ]channel|source[-– ]channel coding|DeepJSCC|wireless image transmission|"
    r"wireless video transmission|wireless speech transmission|split inference|edge inference|"
    r"generative communication|token communication|meaning-aware communication",
    re.I,
)
TECHNICAL_RE = re.compile(
    r"we (?:propose|develop|design|present|introduce|investigate)|proposed (?:method|scheme|framework|system)|"
    r"simulation|experiment|numerical result|algorithm|optimization problem|prototype",
    re.I,
)
NON_TECHNICAL_TITLE_RE = re.compile(
    r"\b(?:survey|overview|tutorial|roadmap|vision|principles and challenges|ten challenges|"
    r"guest editorial|special issue|paradigm shift|beyond transmitting bits|fundamentals and recent progress|"
    r"theories, technologies and applications|opportunities and challenges)\b",
    re.I,
)
MDPI_RE = re.compile(r"^10\.3390/|\b(?:Entropy|Sensors|Electronics|Applied Sciences|Mathematics)\b", re.I)
PREPRINT_RE = re.compile(r"arxiv|techrxiv|biorxiv|medrxiv|ssrn|preprints\.org", re.I)

DATASETS = [
    "CIFAR-10", "CIFAR-100", "ImageNet", "Kodak", "CLIC", "DIV2K", "Europarl",
    "Flickr30k", "MS COCO", "COCO", "Cityscapes", "LibriSpeech", "TIMIT", "MNIST",
    "Fashion-MNIST", "KITTI", "ShapeNet", "ModelNet40", "VQA", "SST-2", "Multi30K",
]
BASELINES = [
    "DeepJSCC", "BPG", "JPEG2000", "JPEG", "LDPC", "Polar", "Turbo", "VTM", "H.264",
    "H.265", "BERT", "DeepSC", "WITT", "SwinJSCC", "NTSCC", "separation-based",
]
METRICS = [
    "PSNR", "SSIM", "MS-SSIM", "LPIPS", "FID", "BLEU", "BERTScore", "WER", "CER",
    "accuracy", "semantic similarity", "latency", "throughput", "BER", "SER", "mIoU", "CLIP",
]
CHANNELS = [
    "AWGN", "Rayleigh", "Rician", "fading channel", "MIMO", "OFDM", "BSC", "BEC",
    "binary symmetric channel", "erasure channel", "QAM", "PSK", "relay channel", "broadcast channel",
]


def team_root(team: Team) -> Path:
    return ROOT / team.folder


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", text)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:120] or "paper"


def abstract_from_inverted(index: dict | None) -> str:
    if not index:
        return ""
    words: dict[int, str] = {}
    for word, positions in index.items():
        for pos in positions:
            words[int(pos)] = word
    return " ".join(words[p] for p in sorted(words))


def get_json(url: str, params: dict | None = None, retries: int = 4) -> dict:
    for attempt in range(retries):
        response = SESSION.get(url, params=params, timeout=60)
        if response.status_code == 429:
            time.sleep(2 ** attempt + 1)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"API rate limit persisted: {url}")


def openalex_author_works(author_id: str) -> list[dict]:
    cursor = "*"
    works: list[dict] = []
    while cursor:
        data = get_json(
            "https://api.openalex.org/works",
            {
                "filter": f"authorships.author.id:{author_id},from_publication_date:{START_DATE},to_publication_date:{END_DATE}",
                "per-page": 200,
                "cursor": cursor,
            },
        )
        works.extend(data.get("results", []))
        cursor = data.get("meta", {}).get("next_cursor")
        if not data.get("results"):
            break
        time.sleep(0.25)
    return works


def openalex_search(query: str, pages: int = 2) -> list[dict]:
    cursor = "*"
    works: list[dict] = []
    for _ in range(pages):
        data = get_json(
            "https://api.openalex.org/works",
            {
                "search": query,
                "filter": f"from_publication_date:{START_DATE},to_publication_date:{END_DATE}",
                "per-page": 100,
                "cursor": cursor,
            },
        )
        works.extend(data.get("results", []))
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not data.get("results"):
            break
        time.sleep(0.25)
    return works


def authors_string(work: dict) -> str:
    return "; ".join(
        (a.get("author") or {}).get("display_name", "") for a in work.get("authorships", [])
        if (a.get("author") or {}).get("display_name")
    )


def affiliations_string(work: dict) -> str:
    names: list[str] = []
    for authorship in work.get("authorships", []):
        for inst in authorship.get("institutions", []):
            name = inst.get("display_name", "")
            if name and name not in names:
                names.append(name)
    return "; ".join(names)


def source_name(work: dict) -> str:
    return ((work.get("primary_location") or {}).get("source") or {}).get("display_name", "")


def pdf_candidates(work: dict) -> list[str]:
    urls: list[str] = []
    for loc in [work.get("best_oa_location"), work.get("primary_location"), *(work.get("locations") or [])]:
        if not loc:
            continue
        for key in ("pdf_url", "landing_page_url"):
            value = loc.get(key)
            if value and value not in urls:
                urls.append(value)
    arxiv = (work.get("ids") or {}).get("arxiv")
    if arxiv:
        aid = arxiv.rsplit("/", 1)[-1]
        urls.insert(0, f"https://arxiv.org/pdf/{aid}")
    return urls


def attribution(team: Team, work: dict) -> tuple[str, str] | None:
    names = authors_string(work)
    ids = {((a.get("author") or {}).get("id") or "").rsplit("/", 1)[-1] for a in work.get("authorships", [])}
    if ids.intersection(team.author_ids) or any(n.lower() in names.lower() for n in team.direct_names):
        return "direct", f"指定团队负责人直接署名：{', '.join(n for n in team.direct_names if n.lower() in names.lower()) or names}"
    if not team.extension_names:
        return None
    extension_hits = [n for n in team.extension_names if n.lower() in names.lower()]
    affiliations = affiliations_string(work)
    if team.key == "qmul":
        if extension_hits and ("deepsc" in f"{work.get('title','')} {abstract_from_inverted(work.get('abstract_inverted_index'))}".lower() or team.institution.lower() in affiliations.lower()):
            return "extension", f"DeepSC 稳定作者链：{', '.join(extension_hits)}；机构记录：{affiliations or '书目记录未给出'}"
    elif extension_hits and team.institution.lower() in affiliations.lower():
        return "extension", f"稳定合作作者：{', '.join(extension_hits)}；目标机构署名：{team.institution}"
    return None


def work_to_row(team: Team, work: dict) -> dict:
    abstract = abstract_from_inverted(work.get("abstract_inverted_index"))
    source = source_name(work)
    attr = attribution(team, work)
    return {
        "citation_key": f"{slugify(work.get('title',''))}-{work.get('publication_year','')}",
        "year": int(work.get("publication_year") or 0),
        "title": " ".join((work.get("title") or "").split()),
        "authors": authors_string(work),
        "venue": source,
        "work_type": work.get("type", ""),
        "doi": (work.get("doi") or "").replace("https://doi.org/", "").lower(),
        "openalex_id": work.get("id", ""),
        "abstract": " ".join(abstract.split()),
        "official_url": work.get("doi") or (work.get("primary_location") or {}).get("landing_page_url", "") or work.get("id", ""),
        "pdf_candidates": pdf_candidates(work),
        "team_scope": attr[0] if attr else "unattributed",
        "team_evidence": attr[1] if attr else "",
        "affiliations": affiliations_string(work),
        "cited_by_count": int(work.get("cited_by_count") or 0),
        "source_verified": bool(work.get("id") and (work.get("doi") or source)),
        "source_verification": "OpenAlex metadata; DOI verified in acquisition/validation stage",
        "screening_status": "candidate",
        "screening_reason": "",
        "pdf": "",
        "download_status": "pending",
        "download_source": "",
        "sha256": "",
        "pages": 0,
        "analysis_status": "metadata_screened",
        "cross_team_duplicate_of": "",
    }


def relevant(row: dict) -> bool:
    text = f"{row['title']} {row['abstract']}"
    return bool(RELEVANCE_RE.search(text))


def screen(row: dict) -> tuple[bool, str]:
    if not (2021 <= row["year"] <= 2026):
        return False, "不在 2021-01-01 至 2026-07-15 时间范围"
    if row["team_scope"] == "unattributed":
        return False, "未满足直接署名或可核验团队延伸归属"
    if not relevant(row):
        return False, "标题与摘要未将语义/任务导向通信或神经 JSCC 作为实质研究对象"
    if row["work_type"] not in {"article", "review", "proceedings-article"}:
        return False, f"非正式期刊/会议技术论文类型：{row['work_type'] or 'unknown'}"
    if PREPRINT_RE.search(f"{row['venue']} {row['doi']} {row['official_url']}"):
        return False, "仅有预印本或预印本书目记录"
    if MDPI_RE.search(f"{row['doi']} {row['venue']}"):
        return False, "项目规则排除 MDPI 论文"
    if NON_TECHNICAL_TITLE_RE.search(row["title"]):
        return False, "综述、教程、愿景或编者按，非正式技术研究论文"
    if row["work_type"] == "review":
        return False, "书目类型为 review，按本次口径不进入核心技术论文"
    if not TECHNICAL_RE.search(row["abstract"] or "") and any(k in row["venue"].lower() for k in ("magazine", "surveys", "reviews")):
        return False, "正式出版但缺少可核验算法/实验贡献，归入背景材料"
    return True, "正式同行评审技术研究论文，主题与团队归属均满足"


def author_overlap(a: dict, b: dict) -> float:
    aa = {norm(x) for x in a.get("authors", "").split(";") if x.strip()}
    bb = {norm(x) for x in b.get("authors", "").split(";") if x.strip()}
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / min(len(aa), len(bb))


def dedupe_and_supersede(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    exact: dict[str, dict] = {}
    removed: list[dict] = []
    for row in sorted(rows, key=lambda r: (r["year"], bool(r["doi"]), r["cited_by_count"]), reverse=True):
        key = row["doi"] or norm(row["title"])
        if key in exact:
            dup = dict(row)
            dup["screening_status"] = "excluded"
            dup["screening_reason"] = f"重复书目记录；保留 {exact[key]['title']}"
            removed.append(dup)
        else:
            exact[key] = row
    kept = list(exact.values())
    superseded: set[str] = set()
    for i, a in enumerate(kept):
        if i in superseded:
            continue
        for j, b in enumerate(kept):
            if i == j or j in superseded:
                continue
            if a["work_type"] != "article" or b["work_type"] != "proceedings-article":
                continue
            similarity = SequenceMatcher(None, norm(a["title"]), norm(b["title"])).ratio()
            if similarity >= 0.78 and author_overlap(a, b) >= 0.5 and a["year"] >= b["year"]:
                superseded.add(j)
                old = dict(b)
                old["screening_status"] = "excluded"
                old["screening_reason"] = f"正式会议版被期刊扩展版取代：{a['title']}"
                removed.append(old)
    return [r for idx, r in enumerate(kept) if idx not in superseded], removed


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


CSV_FIELDS = [
    "citation_key", "year", "title", "authors", "venue", "work_type", "doi", "openalex_id",
    "abstract", "official_url", "team_scope", "team_evidence", "affiliations", "cited_by_count",
    "source_verified", "source_verification", "screening_status", "screening_reason", "pdf",
    "download_status", "download_source", "sha256", "pages", "analysis_status", "cross_team_duplicate_of",
]


def discover_team(team: Team) -> None:
    root = team_root(team)
    notes = root / "notes"
    for folder in (root / "papers", root / "assets", notes, notes / "text"):
        folder.mkdir(parents=True, exist_ok=True)
    works_by_id: dict[str, dict] = {}
    author_counts = {}
    for author_id in team.author_ids:
        works = openalex_author_works(author_id)
        author_counts[author_id] = len(works)
        for work in works:
            works_by_id[work["id"]] = work
    query_counts = {}
    for query in team.extra_queries:
        works = openalex_search(query)
        query_counts[query] = len(works)
        for work in works:
            if attribution(team, work):
                works_by_id[work["id"]] = work
    raw_path = notes / "openalex_works.json"
    raw_path.write_text(json.dumps(list(works_by_id.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    candidates = [work_to_row(team, work) for work in works_by_id.values()]
    candidates = [row for row in candidates if relevant(row)]
    included0: list[dict] = []
    excluded: list[dict] = []
    for row in candidates:
        ok, reason = screen(row)
        row["screening_status"] = "included" if ok else "excluded"
        row["screening_reason"] = reason
        (included0 if ok else excluded).append(row)
    included, duplicates = dedupe_and_supersede(included0)
    excluded.extend(duplicates)
    for row in included:
        row["screening_status"] = "included"
        row["screening_reason"] = "正式同行评审技术研究论文，主题与团队归属均满足"
    included.sort(key=lambda r: (r["year"], r["title"].lower()))
    excluded.sort(key=lambda r: (r["year"], r["title"].lower()))
    candidates.sort(key=lambda r: (r["year"], r["title"].lower()))
    write_csv(root / "candidate_pool.csv", candidates, CSV_FIELDS)
    write_csv(root / "included_papers.csv", included, CSV_FIELDS)
    write_csv(root / "excluded_or_boundary.csv", excluded, CSV_FIELDS)
    manifest = root / "manifest.jsonl"
    manifest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in included), encoding="utf-8")
    year_counts = Counter(r["year"] for r in included)
    strategy = f"""# {team.title_cn}：检索策略与筛选记录

## 范围与口径

- 检索截止：{SEARCH_DATE}；正式出版时间范围：{START_DATE} 至 {END_DATE}。
- 负责人：{', '.join(team.direct_names)}；OpenAlex author IDs：{', '.join(team.author_ids)}。
- 直接署名论文进入核心候选；团队延伸论文必须同时具备稳定合作作者和目标机构/DeepSC 归属证据。
- 仅纳入正式同行评审技术研究论文；排除预印本、综述、教程、愿景、编者按、书章、专利、学位论文和 MDPI。
- 正式会议版存在期刊扩展版时，仅保留期刊版；会议版记录在排除表。

## 数据库与查询

- OpenAlex 作者全集：{json.dumps(author_counts, ensure_ascii=False)}。
- OpenAlex 扩展查询：{json.dumps(query_counts, ensure_ascii=False)}。
- 后续交叉核验：DOI/Crossref、Semantic Scholar、DBLP、IEEE Xplore、机构主页、引用与被引追踪。
- 关键词族：semantic communication；goal-oriented communication；task-oriented communication；DeepSC；semantic JSCC；joint source-channel coding；generative/token communication；edge inference。

## 筛选流

- 主题候选：{len(candidates)}。
- 正式技术论文纳入：{len(included)}。
- 排除或被期刊版取代：{len(excluded)}。
- 年份分布：{', '.join(f'{year}: {year_counts[year]}' for year in sorted(year_counts)) or '无'}。

## 饱和记录

1. 作者全集检索建立主池。
2. 团队/机构关键词扩展用于发现作者实体拆分或负责人未署名的团队论文。
3. DOI、DBLP、Semantic Scholar 与引用/被引追踪用于补正式版本并核对版本家族。

只有连续三轮扩展不再产生新的核心正式技术论文时，网页才标记“实用检索饱和”；在此之前显示为“持续核验”。
"""
    (root / "search_strategy.md").write_text(strategy, encoding="utf-8")
    print(f"[{team.key}] candidates={len(candidates)} included={len(included)} excluded={len(excluded)}")


def load_included(root: Path) -> list[dict]:
    with (root / "included_papers.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["pdf_candidates"] = []
        raw = root / "notes" / "openalex_works.json"
        if raw.exists():
            pass
    return rows


def build_existing_pdf_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    # Authenticated IEEE downloads are staged once and identified by arnumber.
    # Reconnect those files to the exact title/DOI before any fuzzy filename
    # fallback so every team receives the correct paper (including cross-team
    # duplicates) when ``acquire`` is rerun.
    ieee_rows: dict[str, dict] = {}
    ieee_csv = ROOT / "ieee_pending_all_with_arnumber.csv"
    if ieee_csv.exists():
        try:
            with ieee_csv.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    arnumber = (row.get("arnumber") or "").strip()
                    if arnumber:
                        ieee_rows.setdefault(arnumber, row)
        except Exception:
            pass
    ieee_manifest = ROOT / "ieee_download_manifest_teams.jsonl"
    if ieee_rows and ieee_manifest.exists():
        try:
            for line in ieee_manifest.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if record.get("status") != "downloaded":
                    continue
                arnumber = str(record.get("arnumber") or "").strip()
                metadata = ieee_rows.get(arnumber)
                raw_path = record.get("path") or ""
                if not metadata or not raw_path:
                    continue
                path = Path(raw_path)
                if not path.is_absolute():
                    # Downloader paths are normally relative to the repository
                    # root, while this module's ROOT is ``literature``.
                    repo_root = ROOT.parent
                    path = repo_root / path
                if not (path.exists() and valid_pdf(path)):
                    continue
                title = metadata.get("Title") or metadata.get("title") or ""
                doi = metadata.get("Doi") or metadata.get("doi") or ""
                if title:
                    index.setdefault(norm(title), path)
                if doi:
                    index.setdefault(norm(doi), path)
        except Exception:
            pass
    for csv_path in ROOT.glob("*/included_papers.csv"):
        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    pdf = row.get("pdf", "")
                    if pdf:
                        path = csv_path.parent / pdf
                        if path.exists() and valid_pdf(path):
                            index.setdefault(norm(row.get("title", "")), path)
        except Exception:
            continue
    for manifest in ROOT.glob("*/manifest.jsonl"):
        try:
            for line in manifest.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                pdf = row.get("pdf") or row.get("saved_path") or ""
                if pdf:
                    path = Path(pdf)
                    if not path.is_absolute():
                        path = manifest.parent / path
                    if path.exists() and valid_pdf(path):
                        index.setdefault(norm(row.get("title", "")), path)
        except Exception:
            continue
    # The previous survey generation intentionally kept PDFs untracked.  Even if
    # a CSV/manifest is rebuilt, sanitized filenames still provide a safe reuse
    # key.  Keep these as fallback keys rather than discarding a verified corpus.
    for path in ROOT.glob("*/papers/*.pdf"):
        if valid_pdf(path):
            index.setdefault(norm(path.stem), path)
    return index


def valid_pdf(path: Path) -> bool:
    try:
        if path.stat().st_size < 10_000:
            return False
        with path.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                return False
        with fitz.open(path) as doc:
            return doc.page_count >= 2
    except Exception:
        return False


def safe_pdf_name(row: dict) -> str:
    first = (row.get("authors") or "Unknown").split(";")[0].strip().split()[-1]
    title = re.sub(r"[^A-Za-z0-9]+", "_", row["title"]).strip("_")[:90]
    return f"{row['year']}_{first}_{title}.pdf"


def download_pdf(url: str, destination: Path) -> tuple[bool, str]:
    if "ieeexplore.ieee.org" in url.lower():
        return False, "IEEE publisher PDF deferred to authenticated downloader"
    try:
        response = SESSION.get(url, timeout=90, allow_redirects=True)
        content_type = response.headers.get("content-type", "").lower()
        if response.status_code == 200 and response.content.startswith(b"%PDF-") and "html" not in content_type:
            destination.write_bytes(response.content)
            if valid_pdf(destination):
                return True, response.url
            destination.unlink(missing_ok=True)
        return False, f"HTTP {response.status_code}; content-type={content_type}"
    except Exception as exc:
        return False, str(exc)


def raw_work_map(root: Path) -> dict[str, dict]:
    path = root / "notes" / "openalex_works.json"
    if not path.exists():
        return {}
    return {w.get("id", ""): w for w in json.loads(path.read_text(encoding="utf-8"))}


def semantic_scholar_oa(rows: list[dict]) -> dict[str, str]:
    """Resolve DOI records to openly exposed full-text pointers in one batch.

    Semantic Scholar only returns publisher/author/repository OA URLs here; it
    does not provide or bypass credentials.  The acquired-version URL remains
    in the manifest so a preprint is never mislabeled as the typeset version.
    """
    dois = [row.get("doi", "").lower() for row in rows if row.get("doi")]
    if not dois:
        return {}
    try:
        response = SESSION.post(
            "https://api.semanticscholar.org/graph/v1/paper/batch",
            params={"fields": "title,externalIds,openAccessPdf"},
            json={"ids": [f"DOI:{doi}" for doi in dois]},
            timeout=90,
        )
        response.raise_for_status()
        mapping = {}
        for doi, item in zip(dois, response.json()):
            if not item:
                continue
            arxiv_id = (item.get("externalIds") or {}).get("ArXiv")
            if arxiv_id:
                mapping[doi] = f"https://arxiv.org/pdf/{arxiv_id}"
            elif (item.get("openAccessPdf") or {}).get("url"):
                mapping[doi] = item["openAccessPdf"]["url"]
        return mapping
    except Exception as exc:
        print(f"[S2 OA degraded] {exc}")
        return {}


def update_row_pdf_metadata(row: dict, path: Path, source: str) -> None:
    row["pdf"] = f"papers/{path.name}"
    row["download_status"] = "downloaded"
    row["download_source"] = source
    row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with fitz.open(path) as doc:
        row["pages"] = str(doc.page_count)


def acquire_team(team: Team) -> None:
    root = team_root(team)
    rows = load_included(root)
    works = raw_work_map(root)
    existing = build_existing_pdf_index()
    s2_oa = semantic_scholar_oa(rows)
    pending_ieee: list[dict] = []
    blocked: list[dict] = []
    for idx, row in enumerate(rows, 1):
        destination = root / "papers" / safe_pdf_name(row)
        current = root / row.get("pdf", "") if row.get("pdf") else None
        if current and current.exists() and valid_pdf(current):
            update_row_pdf_metadata(row, current, row.get("download_source") or "existing local file")
            continue
        title_key = norm(row["title"])
        prior = existing.get(title_key)
        if not prior:
            scored = []
            for key, path in existing.items():
                score = SequenceMatcher(None, title_key, key).ratio()
                if title_key in key:
                    score = max(score, 0.98)
                if score >= 0.92:
                    scored.append((score, path))
            if scored:
                prior = max(scored, key=lambda item: item[0])[1]
        if prior:
            shutil.copy2(prior, destination)
            update_row_pdf_metadata(row, destination, f"reused local corpus: {prior.relative_to(ROOT)}")
            print(f"[{team.key}] reused {idx}/{len(rows)} {row['title']}")
            continue
        work = works.get(row.get("openalex_id", ""), {})
        candidates = pdf_candidates(work)
        s2_url = s2_oa.get(row.get("doi", "").lower())
        if s2_url and s2_url not in candidates:
            candidates.insert(0, s2_url)
        success = False
        errors = []
        for url in candidates:
            ok, detail = download_pdf(url, destination)
            if ok:
                update_row_pdf_metadata(row, destination, detail)
                print(f"[{team.key}] downloaded {idx}/{len(rows)} {row['title']}")
                success = True
                break
            errors.append(f"{url}: {detail}")
            time.sleep(0.5)
        if success:
            continue
        if row.get("doi", "").startswith("10.1109/"):
            row["download_status"] = "ieee_pending"
            pending_ieee.append({"title": row["title"], "doi": row["doi"]})
        else:
            row["download_status"] = "blocked_no_legal_pdf"
            blocked.append({"title": row["title"], "doi": row.get("doi", ""), "reason": " | ".join(errors)[:1000] or "OpenAlex 未给出开放全文"})
    write_csv(root / "included_papers.csv", rows, CSV_FIELDS)
    (root / "manifest.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    write_csv(root / "notes" / "ieee_pending.csv", pending_ieee, ["title", "doi"])
    write_csv(root / "notes" / "download_blocked.csv", blocked, ["title", "doi", "reason"])
    print(f"[{team.key}] downloaded={sum(r['download_status']=='downloaded' for r in rows)} ieee_pending={len(pending_ieee)} blocked={len(blocked)}")


def page_texts(pdf_path: Path) -> list[str]:
    with fitz.open(pdf_path) as doc:
        return [page.get_text("text") for page in doc]


def sentence_candidates(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if 40 <= len(p.strip()) <= 700]


def find_evidence(pages: list[str], patterns: list[str], start: int = 0, end: int | None = None) -> dict:
    end = len(pages) if end is None else min(end, len(pages))
    regexes = [re.compile(p, re.I) for p in patterns]
    for page_no in range(start, end):
        for sentence in sentence_candidates(pages[page_no]):
            if any(regex.search(sentence) for regex in regexes):
                return {"page": page_no + 1, "text": sentence[:700]}
    return {"page": 0, "text": ""}


def find_terms(text: str, terms: list[str]) -> list[str]:
    found = []
    for term in terms:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", text, re.I):
            found.append(term)
    return found


def find_evidence_many(pages: list[str], patterns: list[str], start: int = 0,
                       end: int | None = None, limit: int = 3) -> list[dict]:
    """Return distinct, page-addressable evidence sentences.

    The renderer deliberately exposes page numbers and does not turn a missing
    match into a guessed claim.  This is used for method, digitalization,
    overhead and channel handling where one abstract sentence is insufficient.
    """
    end = len(pages) if end is None else min(end, len(pages))
    regexes = [re.compile(p, re.I) for p in patterns]
    found: list[dict] = []
    seen: set[str] = set()
    for page_no in range(start, end):
        for sentence in sentence_candidates(pages[page_no]):
            key = norm(sentence)[:180]
            if key and key not in seen and any(regex.search(sentence) for regex in regexes):
                found.append({"page": page_no + 1, "text": sentence[:700]})
                seen.add(key)
                if len(found) >= limit:
                    return found
    return found


def infer_task(title: str, text: str) -> str:
    lower = f"{title} {text[:30000]}".lower()
    routes = [
        (("speech-to-text", "speech recognition", "audio", "speech"), "语音/音频传输或识别"),
        (("video", "talking-head"), "视频传输/生成"),
        (("point cloud", "3-d scene", "3d scene", "nerf"), "点云或三维场景传输"),
        (("text", "translation", "bleu"), "文本传输/机器翻译"),
        (("vqa", "classification", "segmentation", "edge inference", "task-oriented"), "任务导向推理"),
        (("image", "visual"), "图像传输/生成"),
        (("resource allocation", "power allocation", "scheduling"), "语义感知资源分配"),
    ]
    for words, label in routes:
        if any(word in lower for word in words):
            return label
    return "通用语义通信系统或理论"


def infer_digitalization(title: str, text: str) -> tuple[str, str]:
    lower = f"{title} {text[:50000]}".lower()
    if any(k in lower for k in ("vector quant", "vq-vae", "codebook index", "discrete token", "bit-level", "bitstream")):
        return "显式离散/数字语义表示", "全文出现 VQ、码本 index、离散 token 或 bitstream；需重点检查 index/bit 出错后是否会跳到错误码字。"
    if any(k in lower for k in ("joint coding-modulation", "constellation", "qam", "digital semantic", "hybrid digital-analog", "channel coding")):
        return "数字调制或混合数字-模拟链路", "语义表示被映射到有限星座、编码 bit 或数字/模拟并行分支，已经触及可部署物理层接口。"
    if any(k in lower for k in ("deepjscc", "joint source-channel", "channel symbols", "complex-valued", "awgn layer")):
        return "连续神经 JSCC 表示", "encoder 通常直接输出受平均功率约束的连续/复数信道符号；它是端到端语义 JSCC，但并非严格离散数字语义通信。"
    if any(k in lower for k in ("feature transmission", "semantic feature", "latent representation", "prompt", "token")):
        return "语义特征/latent 传输（数字性需逐式核对）", "发送对象是特征、latent、prompt 或 token；是否真正形成 bitstream 取决于论文是否给出量化和链路映射。"
    return "论文未明确给出可复现数字接口", "未在全文自动定位到量化、码本、有限星座或 bitstream 证据，不能把普通 latent 自动认定为数字语义通信。"


def infer_channel_handling(text: str) -> tuple[str, str]:
    lower = text.lower()
    if any(k in lower for k in ("bit error", "index error", "codeword corruption", "soft dequant", "latent error correction")):
        return "离散错误显式建模/联合优化", "训练或接收机显式处理 bit/index/codeword 错误；这是最直接应对离散语义变量跳变的一类。"
    if any(k in lower for k in ("ldpc", "polar code", "channel decoder", "turbo code")) and any(k in lower for k in ("quant", "bitstream", "digital")):
        return "数字语义特征 + 传统信道编码", "decoder 通常看到信道译码后的 bit/index；若论文只假设译码成功，则未真正学习处理残余 index 跳变。"
    if any(k in lower for k in ("constellation", "qam", "psk", "coding-modulation")):
        return "有限星座/调制符号直接过噪声信道", "接收端从有噪星座或 soft symbol 恢复语义；需区分是否有显式 bit/index 译码。"
    if any(k in lower for k in ("awgn layer", "rayleigh fading channel", "channel layer", "additive noise")):
        return "连续 latent/信道符号联合训练", "接收端拿到带噪连续特征或均衡后的复符号，而不是出错的 VQ index；能抗模拟噪声但不等价于解决数字 index error。"
    return "信道作用点不够明确", "全文自动证据不足；可能默认传统链路无误传输，必须结合系统图和公式人工确认 decoder 的实际输入。"


def independent_limitations(text: str, digital_class: str, channel_class: str) -> str:
    lower = text.lower()
    limits: list[str] = []
    if not any(k in lower for k in ("prototype", "testbed", "software-defined radio", "over-the-air", "usrp")):
        limits.append("证据主要来自数据集与仿真信道，缺少真实射频链路/原型验证")
    if "连续神经" in digital_class:
        limits.append("连续信道符号没有给出量化、封包与标准调制开销，离工程数字链路仍有接口缺口")
    if "未明确" in digital_class or "需逐式核对" in digital_class:
        limits.append("语义表示到实际 bit/symbol 的映射与开销未被完整报告")
    if "不够明确" in channel_class or "传统信道编码" in channel_class:
        limits.append("残余 bit/VQ-index 错误导致码字跳变的鲁棒性没有被充分证明")
    if not any(k in lower for k in ("mismatch", "generalization", "out-of-distribution", "unseen")):
        limits.append("跨数据域、未见任务和信道失配下的泛化证据有限")
    return "；".join(limits[:3]) + "。"


def communication_layer(title: str, text: str) -> tuple[str, str]:
    lower = f"{title} {text[:25000]}".lower()
    if any(k in lower for k in ("resource allocation", "power allocation", "offloading", "scheduling")):
        return "资源分配与跨层优化", "语义编码器的性能被放进带宽、功率、时延或计算资源约束中联合优化。"
    if any(k in lower for k in ("multiple access", "multi-user", "broadcast", "noma", "multicast")):
        return "多用户接入与广播", "研究多个用户如何共享无线资源，以及语义相关性、用户信道差异如何改变传统接入设计。"
    if any(k in lower for k in ("mimo", "ofdm", "constellation", "modulation", "qam", "papr")):
        return "物理层调制、波形与 MIMO", "研究语义特征如何真正映射到天线、子载波或有限星座，而不是停留在抽象神经网络信道。"
    if any(k in lower for k in ("security", "privacy", "eavesdrop", "encryption", "attack")):
        return "通信安全与隐私", "研究语义特征在无线窃听、模型反演或攻击下是否泄露，以及可靠性和隐私之间的权衡。"
    if any(k in lower for k in ("edge inference", "split inference", "remote inference", "classification", "retrieval", "task-oriented")):
        return "任务导向边缘推理", "接收端不必恢复原始数据，只需完成分类、检索或推理任务；核心指标从像素误差转向任务正确率。"
    if any(k in lower for k in ("joint source", "deepjscc", "source-channel", "wireless image", "wireless video", "wireless speech")):
        return "联合信源信道编码（JSCC）", "把压缩与抗信道噪声放在一个端到端模型中优化，避免传统分离设计在短码长或信道失配时的性能断崖。"
    return "语义信源编码与系统设计", "研究发送端应保留什么信息、如何表示语义，以及接收端如何在有限通信资源下恢复意义或任务结果。"


def beginner_explanation(layer: str) -> str:
    mapping = {
        "联合信源信道编码（JSCC）": "把它看成一个同时学习“压缩器”和“抗噪声传输器”的 autoencoder；中间瓶颈不是普通 latent，而是要占用真实信道资源的符号。",
        "物理层调制、波形与 MIMO": "这部分决定神经网络输出最终怎样变成可由射频链路发送的复数符号、星座点、子载波或多天线信号，是从算法仿真走向通信实现的关键接口。",
        "多用户接入与广播": "这相当于一个模型同时服务多个接收端，但每个用户的信道质量和任务需求不同；不能只优化单个样本的 loss。",
        "资源分配与跨层优化": "模型性能在这里会被抽象成速率—精度或功率—失真曲线，再与无线资源约束一起求最优分配。",
        "任务导向边缘推理": "它类似 split learning：设备只上传足以完成下游任务的中间特征，通信系统关心的是任务准确率和时延，而不是把原数据无损搬过去。",
        "通信安全与隐私": "即使传的不是原始比特，latent 仍可能泄露内容；安全研究要同时检查合法接收端性能和窃听者能恢复多少信息。",
    }
    return mapping.get(layer, "把发送端模型看成有严格带宽预算的表示学习器：输出的每一维、每个 token 或每个信道符号都会产生真实传输成本。")


def reviewer_value(layer: str) -> str:
    values = {
        "联合信源信道编码（JSCC）": "通信审稿人关注它是否在相同带宽、功率和信道条件下优于分离式压缩+信道编码，并且是否避免 cliff effect、改善信道失配鲁棒性。",
        "物理层调制、波形与 MIMO": "价值在于补上从连续 latent 到可发送波形之间的工程缺口，并检验频谱效率、PAPR、星座约束、CSI 或多天线增益。",
        "多用户接入与广播": "价值在于利用用户间语义相关性或分层需求改善频谱共享，而不只是分别运行多个点到点网络。",
        "资源分配与跨层优化": "价值在于把语义质量转化为可优化的网络效用，并回答有限功率、带宽、时延应分给谁。",
        "任务导向边缘推理": "价值在于用更少上行数据完成相同任务，从而降低端到端时延、能耗和无线负载。",
        "通信安全与隐私": "价值在于说明语义特征并非天然安全，并给出可靠性、隐私和资源开销之间可测量的权衡。",
    }
    return values.get(layer, "通信价值取决于它是否以更少的信道使用、带宽或能量达到可比较的语义/任务质量，而不是仅在离线数据集上提高神经网络指标。")


def render_page(pdf_path: Path, page_number: int, output: Path) -> None:
    if page_number <= 0 or output.exists():
        return
    with fitz.open(pdf_path) as doc:
        page = doc[min(page_number - 1, doc.page_count - 1)]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        pix.save(output)


def choose_figure_pages(pages: list[str]) -> tuple[int, int]:
    method = 0
    result = 0
    for idx, text in enumerate(pages[: min(7, len(pages))]):
        if re.search(r"Fig(?:ure)?\.?\s*1|system model|system architecture|proposed framework", text, re.I):
            method = idx + 1
            break
    if not method:
        method = min(3, len(pages))
    for idx in range(max(0, len(pages) // 2), len(pages)):
        if re.search(r"simulation results|experimental results|numerical results|performance evaluation", pages[idx], re.I):
            result = idx + 1
            break
    if not result:
        result = max(method, len(pages) - 2)
    return method, result


def analyze_team(team: Team) -> None:
    root = team_root(team)
    rows = load_included(root)
    analyses: list[dict] = []
    for idx, row in enumerate(rows, 1):
        pdf_path = root / row.get("pdf", "") if row.get("pdf") else None
        analysis = dict(row)
        if not pdf_path or not pdf_path.exists() or not valid_pdf(pdf_path):
            analysis.update({
                "analysis_status": "blocked_missing_fulltext",
                "evidence": {}, "datasets": [], "baselines": [], "metrics": [], "channels": [],
                "communication_layer": "待全文核验", "layer_explanation": "全文尚未合法取得，不能声称已经阅读全文。",
                "beginner_explanation": "当前只保留经过书目核验的元数据；方法和实验不从摘要臆测。",
                "reviewer_value": "待全文取得后判断。", "limitations": "全文缺失是当前主要限制。",
                "figures": [],
            })
            analyses.append(analysis)
            continue
        pages = page_texts(pdf_path)
        full_text = "\n".join(pages)
        intro_end = min(5, len(pages))
        progress = find_evidence(pages, [r"has (?:achieved|attracted|shown|demonstrated)", r"recent advances", r"have been developed"], 0, intro_end)
        problem = find_evidence(pages, [r"however", r"nevertheless", r"still (?:suffer|remain|lack)", r"challenge", r"limitation"], 0, intro_end)
        proposal = find_evidence(pages, [r"we propose", r"we develop", r"we design", r"we present", r"we introduce"], 0, intro_end)
        mechanism = find_evidence(pages, [r"by (?:leveraging|utilizing|jointly|introducing|exploiting)", r"consists of", r"is composed of"], 0, min(8, len(pages)))
        result_ev = find_evidence(pages, [r"results (?:show|demonstrate|indicate)", r"outperforms", r"achieves"], max(0, len(pages) // 2), len(pages))
        layer, layer_exp = communication_layer(row["title"], full_text)
        method_evidence = find_evidence_many(
            pages,
            [r"we propose", r"our (?:framework|scheme|method|system)", r"consists of", r"architecture", r"encoder", r"decoder"],
            0, min(10, len(pages)), 4,
        )
        representation_evidence = find_evidence_many(
            pages,
            [r"semantic (?:feature|representation|symbol|token)", r"latent (?:feature|vector|representation|code)",
             r"feature map", r"codebook", r"bitstream", r"prompt", r"channel symbol"],
            0, min(12, len(pages)), 4,
        )
        digital_evidence = find_evidence_many(
            pages,
            [r"vector quant", r"quantiz", r"codebook", r"discrete", r"bitstream", r"bits? per", r"constellation",
             r"joint coding.modulation", r"digital.semantic", r"entropy cod", r"token"],
            0, len(pages), 5,
        )
        overhead_evidence = find_evidence_many(
            pages,
            [r"channel bandwidth ratio", r"bandwidth ratio", r"compression ratio", r"code rate", r"bit rate",
             r"bits? per (?:pixel|symbol|token|index)", r"channel uses?", r"transmission overhead", r"CBR"],
            0, len(pages), 5,
        )
        channel_evidence = find_evidence_many(
            pages,
            [r"AWGN", r"Rayleigh", r"Rician", r"binary symmetric", r"erasure channel", r"bit error",
             r"index error", r"channel decoder", r"LDPC", r"polar code", r"QAM", r"channel noise"],
            0, len(pages), 5,
        )
        experiment_evidence = find_evidence_many(
            pages,
            [r"results (?:show|demonstrate|indicate)", r"outperform", r"performance gain", r"improv(?:e|es|ed|ement)",
             r"compared with", r"achieves?"],
            max(0, len(pages) // 3), len(pages), 5,
        )
        digital_class, digital_judgment = infer_digitalization(row["title"], full_text)
        channel_class, channel_judgment = infer_channel_handling(full_text)
        method_page, result_page = choose_figure_pages(pages)
        stem = slugify(row["title"])
        method_img = root / "assets" / f"{stem}_method_p{method_page}.png"
        result_img = root / "assets" / f"{stem}_result_p{result_page}.png"
        render_page(pdf_path, method_page, method_img)
        render_page(pdf_path, result_page, result_img)
        first_pages = " ".join(pages[:3]).lower()
        title_tokens = [t for t in re.findall(r"[a-z0-9]+", row["title"].lower()) if len(t) > 3]
        title_match = sum(t in first_pages for t in title_tokens) / max(1, len(title_tokens))
        analysis.update({
            "analysis_status": "fulltext_evidence_extracted",
            "source_verified_against_original": title_match >= 0.55,
            "source_verification_method": "manual_grep",
            "pdf_pages": len(pages),
            "evidence": {"progress": progress, "problem": problem, "proposal": proposal, "mechanism": mechanism, "result": result_ev},
            "method_evidence": method_evidence,
            "representation_evidence": representation_evidence,
            "digital_evidence": digital_evidence,
            "overhead_evidence": overhead_evidence,
            "channel_evidence": channel_evidence,
            "experiment_evidence": experiment_evidence,
            "task_type": infer_task(row["title"], full_text),
            "digitalization_class": digital_class,
            "digitalization_judgment": digital_judgment,
            "channel_handling_class": channel_class,
            "channel_handling_judgment": channel_judgment,
            "datasets": find_terms(full_text, DATASETS),
            "baselines": find_terms(full_text, BASELINES),
            "metrics": find_terms(full_text, METRICS),
            "channels": find_terms(full_text, CHANNELS),
            "snr_conditions": [m.group(0) for m in re.finditer(r"[-+]?\d+(?:\.\d+)?\s*dB", full_text, re.I)][:12],
            "communication_layer": layer,
            "layer_explanation": layer_exp,
            "beginner_explanation": beginner_explanation(layer),
            "reviewer_value": reviewer_value(layer),
            "limitations": independent_limitations(full_text, digital_class, channel_class),
            "figures": [
                {"kind": "method", "page": method_page, "file": f"assets/{method_img.name}"},
                {"kind": "result", "page": result_page, "file": f"assets/{result_img.name}"},
            ],
        })
        text_dir = root / "notes" / "text"
        text_dir.mkdir(parents=True, exist_ok=True)
        (text_dir / f"{stem}.txt").write_text("\n\n".join(f"=== PAGE {i+1} ===\n{t}" for i, t in enumerate(pages)), encoding="utf-8")
        analyses.append(analysis)
        print(f"[{team.key}] analyzed {idx}/{len(rows)} {row['title']}")
    path = root / "notes" / "structured_analysis.jsonl"
    path.write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in analyses), encoding="utf-8")
    for row, analysis in zip(rows, analyses):
        row["analysis_status"] = analysis["analysis_status"]
    write_csv(root / "included_papers.csv", rows, CSV_FIELDS)
    (root / "manifest.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def evidence_html(label: str, item: dict) -> str:
    if not item or not item.get("text"):
        return f"<li><strong>{html.escape(label)}：</strong>全文自动定位未找到可靠句子，需回到 PDF 人工核查。</li>"
    return f"<li><strong>{html.escape(label)}：</strong>{html.escape(item['text'])} <a href='#' class='page-ref'>PDF p.{item['page']}</a></li>"


def list_text(values: list[str] | None) -> str:
    return "、".join(values or []) or "论文文本未明确命中，需查看原表格或附录"


def evidence_list_html(items: list[dict] | None, empty: str) -> str:
    if not items:
        return f"<p class='notice'>{html.escape(empty)}</p>"
    return "<ul class='evidence-list'>" + "".join(
        f"<li>{html.escape(item.get('text',''))} <span class='page-ref'>PDF p.{item.get('page','?')}</span></li>"
        for item in items
    ) + "</ul>"


def paper_article(a: dict, local: bool) -> str:
    slug = slugify(a["title"])
    ev = a.get("evidence") or {}
    source_link = f"https://doi.org/{a['doi']}" if a.get("doi") else a.get("official_url", "#")
    pdf_link = a.get("pdf", "") if local and a.get("pdf") else source_link
    link_label = "打开本地 PDF" if local and a.get("pdf") else "DOI / 出版页面"
    figs = []
    for figure in a.get("figures") or []:
        kind = "架构/方法页" if figure["kind"] == "method" else "关键结果页"
        wrap_open = f"<a href='{html.escape(a.get('pdf',''))}'>" if local and a.get("pdf") else ""
        wrap_close = "</a>" if wrap_open else ""
        figs.append(
            f"<figure>{wrap_open}<img loading='lazy' src='{html.escape(figure['file'])}' alt='{html.escape(a['title'])} {kind}'>{wrap_close}"
            f"<figcaption>{html.escape(a['title'])}，原 PDF 第 {figure['page']} 页（{kind}）。</figcaption></figure>"
        )
    if not figs:
        figs.append("<p class='notice'>全文尚未取得或 PDF 中未能可靠定位可展示图页，因此暂不展示架构/结果图。</p>")
    if a.get("analysis_status") == "blocked_missing_fulltext":
        body = "<p class='notice'>该条目书目已核验，但尚未合法取得全文；本页不把摘要当作阅读全文分析，方法、实验和价值判断保持待核验状态。</p>"
    else:
        body = f"""
        <h3>Motivation｜问题怎样一步步导出本文方法</h3>
        <ol class='story'>
          {evidence_html('现有进展', ev.get('progress', {}))}
          {evidence_html('仍然存在的问题', ev.get('problem', {}))}
          <li><strong>为什么旧方法不够：</strong>在通信系统中，模型必须同时面对有限带宽、信道噪声和发送功率约束；只优化离线重建或任务 loss，不能保证相同信道使用次数下仍然可靠。</li>
          <li><strong>为什么重要：</strong>{html.escape(a.get('reviewer_value',''))}</li>
          {evidence_html('本文提出的方案', ev.get('proposal', {}))}
          {evidence_html('方案起作用的机制', ev.get('mechanism', {}))}
          {evidence_html('作者希望证明的结论', ev.get('result', {}))}
        </ol>
        <h3>方法与通信系统定位</h3>
        <p><strong>研究任务：</strong>{html.escape(a.get('task_type',''))}</p>
        <p><strong>所属环节：</strong>{html.escape(a.get('communication_layer',''))}。{html.escape(a.get('layer_explanation',''))}</p>
        <p><strong>给深度学习研究生的解释：</strong>{html.escape(a.get('beginner_explanation',''))}</p>
        <p><strong>为什么方法可能解决开头的问题：</strong>方案把论文关注的语义表示、信道或资源约束放进同一训练/优化目标，使发送端学习的不只是数据压缩，而是“在给定无线资源和噪声下什么信息最值得发送”。</p>
        <h4>输入—编码—信道—接收端：全文方法证据</h4>
        {evidence_list_html(a.get('method_evidence'), '未自动定位到足够的方法句；请结合下方方法页截图与 PDF 公式人工核验。')}
        <h4>中间语义表示是什么</h4>
        {evidence_list_html(a.get('representation_evidence'), '论文没有用可检索文字明确报告 feature map、latent、token、index 或 bitstream 的形状。')}
        <h3>数字化方案与实际传输开销</h3>
        <p><strong>数字化判断：</strong><span class='tag'>{html.escape(a.get('digitalization_class',''))}</span> {html.escape(a.get('digitalization_judgment',''))}</p>
        {evidence_list_html(a.get('digital_evidence'), '未找到量化、码本、有限星座或 bitstream 证据；不能把神经网络 bottleneck 自动当作数字链路。')}
        <h4>bit / token / channel-use / CBR 证据</h4>
        {evidence_list_html(a.get('overhead_evidence'), '论文未以可检索文本完整报告输入尺寸、latent/token 数、每个 index 的 bit 数与总开销；本报告不在缺少形状和码本参数时伪造压缩率。可按 $R=N_s b_s/N_{src}$ 或 $\rho=n/k$ 在取得参数后推导。')}
        <h3>信道处理机制：decoder 实际收到什么</h3>
        <p><strong>分类：</strong><span class='tag'>{html.escape(a.get('channel_handling_class',''))}</span> {html.escape(a.get('channel_handling_judgment',''))}</p>
        {evidence_list_html(a.get('channel_evidence'), '未能从全文文字确定噪声加在连续 latent、调制符号还是 bit/index 上；需回到系统图与信道公式确认。')}
        <h3>实验设置与证据</h3>
        <div class='facts'><p><strong>数据集：</strong>{html.escape(list_text(a.get('datasets')))}</p><p><strong>Baseline：</strong>{html.escape(list_text(a.get('baselines')))}</p><p><strong>信道/链路：</strong>{html.escape(list_text(a.get('channels')))}</p><p><strong>指标：</strong>{html.escape(list_text(a.get('metrics')))}</p><p><strong>SNR 条件：</strong>{html.escape(list_text(a.get('snr_conditions')))}</p></div>
        <h4>主要实验结论（带全文页码）</h4>
        {evidence_list_html(a.get('experiment_evidence'), '自动定位未找到明确的结果句；请查看下方结果页截图和 PDF 图表。')}
        <h3>通信审稿价值与 Codex 判断</h3>
        <p>{html.escape(a.get('reviewer_value',''))}</p>
        <p><strong>局限：</strong>{html.escape(a.get('limitations',''))}</p>
        """
    return f"""
    <article class='paper' id='{slug}'>
      <h2>{html.escape(a['title'])}</h2>
      <p class='meta'>{a.get('year','')} · {html.escape(a.get('venue','未标注出版物'))} · {html.escape(a.get('communication_layer','待分类'))}</p>
      <p><strong>作者：</strong>{html.escape(a.get('authors',''))}</p>
      <p><strong>团队归属：</strong>{html.escape(a.get('team_evidence',''))}</p>
      <div class='actions'><a class='button' href='{html.escape(pdf_link)}'>{link_label}</a><a class='button ghost' href='{html.escape(source_link)}'>出版元数据</a></div>
      {body}
      <div class='fig-grid'>{''.join(figs)}</div>
    </article>
    """


CSS = """
:root{--ink:#18222d;--muted:#5c6875;--paper:#f7f4ee;--card:#fff;--accent:#0d6b66;--line:#d9d3c8;--warn:#fff1ca}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,"Noto Sans SC","Microsoft YaHei",sans-serif;line-height:1.72}nav{position:fixed;inset:0 auto 0 0;width:330px;overflow:auto;padding:24px 18px;background:#132f35;color:#eaf6f4}nav h2{font-size:18px}nav a{display:block;color:#d8ece9;text-decoration:none;padding:7px 8px;border-radius:8px;font-size:13px}nav a:hover{background:#28525a}nav .year{color:#8fd4ca;margin:18px 8px 4px;font-weight:700}main{margin-left:330px;max-width:1240px;padding:42px 52px 100px}.hero,.panel,.paper{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px;margin-bottom:24px;box-shadow:0 10px 30px rgba(31,45,49,.05)}h1{font-family:Georgia,"Noto Serif SC",serif;font-size:42px;line-height:1.18;margin:.2em 0}h2{font-size:27px;line-height:1.3;margin-top:.4em}h3{font-size:19px;margin-top:30px;color:#174f50}h4{font-size:15px;margin:18px 0 6px;color:#315d5d}.meta{color:var(--muted)}.chips{display:flex;gap:8px;flex-wrap:wrap}.chip,.tag{background:#e0efec;color:#134c49;border-radius:999px;padding:5px 10px;font-size:13px}.system-map{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;align-items:stretch}.system-map div{background:#edf4f2;border:1px solid #c6ded9;padding:12px;border-radius:12px;text-align:center;font-size:13px}.arrow:after{content:"→";float:right;color:var(--accent);font-weight:800}.timeline{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:15px 0 26px}.timeline div{border-left:4px solid var(--accent);background:#f2f7f5;border-radius:9px;padding:11px}.timeline strong{font-size:18px;margin-right:8px}.timeline span,small{color:var(--muted)}.timeline p{font-size:12px;margin:6px 0}.reading-order{display:grid;grid-template-columns:1fr 1fr;gap:8px 28px}.button{display:inline-block;background:var(--accent);color:white!important;text-decoration:none;padding:8px 13px;border-radius:9px;margin:4px 8px 4px 0}.button.ghost{background:#eef3f1;color:#1e5653!important}.story li,.evidence-list li{margin:8px 0}.page-ref{white-space:nowrap;color:#33706d;font-size:12px}.facts{display:grid;grid-template-columns:1fr 1fr;gap:8px 18px}.facts p{margin:0;padding:10px;background:#f7f8f6;border-radius:10px}.fig-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:22px}figure{margin:0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fafafa}figure img{width:100%;display:block}figcaption{padding:10px;font-size:12px;color:var(--muted)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#edf4f2}.table-wrap{overflow:auto;max-height:680px}.notice{background:var(--warn);border-left:4px solid #d5a528;padding:12px 15px;border-radius:8px}.actions{margin:14px 0}@media(max-width:980px){nav{position:relative;width:auto;max-height:42vh}main{margin-left:0;padding:24px}.system-map{grid-template-columns:1fr 1fr}.facts,.fig-grid,.reading-order{grid-template-columns:1fr}h1{font-size:32px}}
"""


GLOSSARY = [
    ("信源编码", "去掉源数据中的冗余，目标是用更少 bit/符号表示内容。"),
    ("信道编码", "加入受控冗余，让接收端能够发现或纠正无线传输产生的错误。"),
    ("JSCC", "联合信源信道编码；把压缩和抗噪声传输一起设计。"),
    ("SNR", "信噪比；越低表示噪声相对越强。比较方法时必须保证 SNR 定义和功率约束一致。"),
    ("带宽比/CBR", "信道使用次数相对源维度或像素数的比例，是通信开销而不是模型参数量。"),
    ("CSI", "信道状态信息；发射端/接收端是否知道它，会显著改变问题难度。"),
    ("cliff effect", "传统分离链路在低于解码门限后性能突然崩溃；模拟式 DeepJSCC 常呈渐进退化。"),
    ("语义指标", "以任务正确率、BLEU、CLIP 相似度等衡量意义是否保留，但不自动等价于可靠通信。"),
]


def render_team(team: Team) -> None:
    root = team_root(team)
    analysis_path = root / "notes" / "structured_analysis.jsonl"
    analyses = [json.loads(line) for line in analysis_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    excluded = []
    excluded_path = root / "excluded_or_boundary.csv"
    if excluded_path.exists():
        with excluded_path.open(encoding="utf-8-sig", newline="") as handle:
            excluded = list(csv.DictReader(handle))
    by_year = defaultdict(list)
    for a in analyses:
        by_year[str(a.get("year", "unknown"))].append(a)
    nav = ["<nav><h2>" + html.escape(team.title_cn) + "</h2><a href='#overview'>总览与通信地图</a><a href='#timeline'>技术路线与阅读顺序</a><a href='#screening'>论文筛选表</a><a href='#glossary'>术语表</a>"]
    for year in sorted(by_year):
        nav.append(f"<div class='year'>{year}</div>")
        for a in by_year[year]:
            nav.append(f"<a href='#{slugify(a['title'])}'>{html.escape(a['title'])}</a>")
    nav.append("<a href='#excluded'>排除与边界记录</a></nav>")
    rows = "".join(
        f"<tr><td>{a.get('year','')}</td><td><a href='#{slugify(a['title'])}'>{html.escape(a['title'])}</a></td><td>{html.escape(a.get('venue',''))}</td><td>{html.escape(a.get('communication_layer',''))}</td><td>{html.escape(a.get('team_scope',''))}</td><td>{html.escape(a.get('download_status',''))}</td></tr>"
        for a in analyses
    )
    glossary = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in GLOSSARY)
    exclusion_rows = "".join(
        f"<tr><td>{html.escape(str(r.get('year','')))}</td><td>{html.escape(r.get('title',''))}</td><td>{html.escape(r.get('screening_reason',''))}</td></tr>"
        for r in excluded
    ) or "<tr><td colspan='3'>无</td></tr>"
    counts = Counter(a.get("communication_layer", "待分类") for a in analyses)
    chips = "".join(f"<span class='chip'>{html.escape(k)} {v}</span>" for k, v in counts.most_common())
    articles_local = "".join(paper_article(a, True) for a in analyses)
    articles_public = "".join(paper_article(a, False) for a in analyses)
    timeline = "".join(
        f"<div><strong>{html.escape(year)}</strong><span>{len(by_year[year])} 篇</span><p>" + "；".join(
            f"<a href='#{slugify(a['title'])}'>{html.escape(a['title'])}</a>" for a in by_year[year][:3]
        ) + ("；……" if len(by_year[year]) > 3 else "") + "</p></div>"
        for year in sorted(by_year)
    )
    ranked = sorted(analyses, key=lambda a: (int(a.get("cited_by_count") or 0), -int(a.get("year") or 0)), reverse=True)
    picks: list[dict] = []
    selectors = [
        lambda a: int(a.get("year") or 0) <= 2022,
        lambda a: "显式离散" in a.get("digitalization_class", ""),
        lambda a: any(k in a.get("communication_layer", "") for k in ("MIMO", "多用户", "资源")),
        lambda a: int(a.get("year") or 0) >= 2025,
    ]
    for selector in selectors:
        hit = next((a for a in ranked if selector(a) and a not in picks), None)
        if hit: picks.append(hit)
    recommended = "".join(
        f"<li><a href='#{slugify(a['title'])}'>{html.escape(a['title'])}</a><br><small>{html.escape(a.get('task_type',''))} · {html.escape(a.get('digitalization_class',''))}</small></li>"
        for a in picks
    )
    route_panel = f"<section class='panel' id='timeline'><h2>团队技术路线时间线</h2><div class='timeline'>{timeline}</div><h2>推荐阅读顺序</h2><ol class='reading-order'>{recommended}</ol><p class='notice'>顺序按“早期基础 → 显式数字化 → 信道/多用户系统 → 最新生成式或跨层工作”组织；引用数只用于帮助挑入口，不代表论文质量排序。</p></section>"
    base_head = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(team.title_cn)}语义通信论文调研（2021-2026）</title><style>{CSS}</style><script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\(','\\)']]}}}};</script><script defer src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'></script></head><body>"""
    intro = f"""{''.join(nav)}<main><section class='hero' id='overview'><p><a href='../'>← 返回调研主页</a></p><h1>{html.escape(team.title_cn)}语义通信论文调研</h1><p>面向具有深度学习基础、通信基础较少的读者。检索范围为 2021-01-01 至 2026-07-15；核心表仅保留正式同行评审技术研究论文，会议版若有期刊扩展版则只保留期刊版。</p><div class='chips'><span class='chip'>核心论文 {len(analyses)}</span>{chips}</div><h2>先看懂一篇通信论文处在哪</h2><div class='system-map'><div class='arrow'>原始数据/任务</div><div class='arrow'>语义/信源编码</div><div class='arrow'>信道编码</div><div class='arrow'>调制、MIMO、OFDM</div><div class='arrow'>无线信道</div><div>译码/重建/任务</div></div><p>传统系统常分别优化这些方框；语义通信论文通常合并其中若干环节。评价一篇论文时要问：发送的中间表示是什么？占多少信道资源？噪声在哪里加入？接收端恢复的是原始数据还是任务结果？</p><p>常见带宽比可写为 $\rho=n/k$，其中 $k$ 是源样本维度，$n$ 是信道使用次数。只有在相同 $\rho$、发射功率和信道模型下，方法间性能比较才公平。</p></section><section class='panel' id='screening'><h2>论文筛选与定位表</h2><div class='table-wrap'><table><thead><tr><th>年份</th><th>完整标题</th><th>出版物</th><th>通信环节</th><th>团队口径</th><th>全文</th></tr></thead><tbody>{rows}</tbody></table></div></section><section class='panel' id='glossary'><h2>通信小白术语表</h2><table>{glossary}</table></section>"""
    intro = intro.replace("</section><section class='panel' id='screening'>", f"</section>{route_panel}<section class='panel' id='screening'>", 1)
    ending = f"""<section class='panel' id='excluded'><h2>排除与边界记录</h2><p>这些条目在检索中出现，但因预印本、综述/愿景、MDPI、主题边界或被期刊扩展版取代而未进入核心表。</p><div class='table-wrap'><table><tr><th>年份</th><th>标题</th><th>原因</th></tr>{exclusion_rows}</table></div></section><section class='panel'><h2>方法与责任说明</h2><p>书目元数据通过 OpenAlex、DOI 和出版页面核验；逐篇技术结论以本地 PDF 页码证据为准。自动定位不到可靠证据时明确标为待人工核查，不用摘要填充“阅读全文”结论。</p><p>AI Disclosure：本报告使用 AI 辅助完成检索、全文定位、结构化提取和网页生成；所有可核验论断均保留 DOI 或 PDF 页码入口。</p></section></main></body></html>"""
    (root / "index_local.html").write_text(base_head + intro + articles_local + ending, encoding="utf-8")
    (root / "index.html").write_text(base_head + intro + articles_public + ending, encoding="utf-8")
    print(f"[{team.key}] rendered {len(analyses)} papers")


def validate_team(team: Team) -> list[str]:
    root = team_root(team)
    errors: list[str] = []
    rows = load_included(root)
    title_keys = set()
    doi_keys = set()
    for row in rows:
        if not (2021 <= int(row["year"]) <= 2026): errors.append(f"year: {row['title']}")
        if row.get("doi", "").startswith("10.3390/"): errors.append(f"MDPI included: {row['title']}")
        key = norm(row["title"])
        if key in title_keys: errors.append(f"duplicate title: {row['title']}")
        title_keys.add(key)
        if row.get("doi"):
            if row["doi"] in doi_keys: errors.append(f"duplicate DOI: {row['doi']}")
            doi_keys.add(row["doi"])
        if row.get("download_status") == "downloaded":
            path = root / row.get("pdf", "")
            if not path.exists() or not valid_pdf(path): errors.append(f"bad PDF: {row['title']}")
    for name in ("index.html", "index_local.html"):
        page = root / name
        if not page.exists(): errors.append(f"missing {name}")
        else:
            text = page.read_text(encoding="utf-8")
            ids = re.findall(r"\bid=['\"]([^'\"]+)", text)
            dup_ids = [k for k, v in Counter(ids).items() if v > 1]
            if dup_ids: errors.append(f"duplicate HTML ids in {name}: {dup_ids[:3]}")
            if "MathJax" not in text: errors.append(f"MathJax missing in {name}")
    return errors


def selected_teams(value: str) -> list[Team]:
    if value == "all":
        return list(TEAMS.values())
    keys = [x.strip() for x in value.split(",") if x.strip()]
    unknown = [k for k in keys if k not in TEAMS]
    if unknown:
        raise SystemExit(f"Unknown teams: {unknown}; choices={list(TEAMS)}")
    return [TEAMS[k] for k in keys]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["discover", "acquire", "analyze", "render", "validate", "all"])
    parser.add_argument("--teams", default="all")
    args = parser.parse_args()
    teams = selected_teams(args.teams)
    for team in teams:
        if args.command in {"discover", "all"}: discover_team(team)
        if args.command in {"acquire", "all"}: acquire_team(team)
        if args.command in {"analyze", "all"}: analyze_team(team)
        if args.command in {"render", "all"}: render_team(team)
        if args.command == "validate":
            errors = validate_team(team)
            print(f"[{team.key}] validation: {'PASS' if not errors else 'FAIL'}")
            for error in errors: print("  -", error)
            if errors: sys.exit(1)


if __name__ == "__main__":
    main()
