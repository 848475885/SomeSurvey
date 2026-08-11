#!/usr/bin/env python3
"""Prepare public and local editions of the IEEE TWC survey page.

The local edition keeps links to downloaded papers.  The public edition uses
DOI/IEEE publication pages and contains no local PDF paths.  The script also
sanitizes the public manifest while preserving a git-ignored local copy.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path, PureWindowsPath


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-twc-semantic-communications-2023-present"
PUBLIC_HTML = SURVEY / "index.html"
LOCAL_HTML = SURVEY / "index_local.html"
MANIFEST = SURVEY / "manifest.jsonl"
LOCAL_MANIFEST = SURVEY / "notes" / "manifest_local.jsonl"
FINALIZATION = SURVEY / "notes" / "finalization_summary.json"


PUBLIC_CSS = """
.skip-link{position:fixed;z-index:20;left:12px;top:8px;transform:translateY(-150%);background:#fff;color:#10243d;padding:8px 12px;border-radius:7px;box-shadow:0 4px 18px #0003}.skip-link:focus{transform:none}
.home-link{margin-bottom:14px!important;padding:9px 10px!important;border:1px solid #ffffff35!important;border-radius:8px;background:#ffffff0d;font-weight:700}
.paper{content-visibility:auto;contain-intrinsic-size:auto 920px;scroll-margin-top:18px}.paper:target{outline:3px solid #7cb9ff;outline-offset:3px}
nav{overscroll-behavior:contain;scrollbar-width:thin}img{background:#eef3f9}.edition{display:inline-block;margin:0 0 12px;padding:4px 9px;border-radius:999px;background:#eaf3ff;color:#0b5cad;font-size:12px;font-weight:700}
@media print{nav{display:none}main{margin:0;max-width:none}.paper{content-visibility:visible;break-inside:avoid}.pdf,.skip-link{display:none}}
""".strip()


def load_manifest() -> list[dict]:
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]


def paper_filename(value: str) -> str:
    if not value:
        return ""
    return PureWindowsPath(value).name


def sanitize_manifest(rows: list[dict]) -> None:
    if not LOCAL_MANIFEST.exists():
        shutil.copy2(MANIFEST, LOCAL_MANIFEST)
    public_rows = []
    for original in rows:
        row = dict(original)
        filename = paper_filename(str(row.get("pdf_path", "")))
        row["pdf_path"] = f"papers/{filename}" if filename else ""
        row.pop("institutional_access", None)
        reused = str(row.get("reused_from", ""))
        if re.match(r"^[A-Za-z]:[\\/]", reused):
            row["reused_from"] = "verified local duplicate"
        public_rows.append(row)
    MANIFEST.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in public_rows) + "\n",
        encoding="utf-8",
    )


def sanitize_finalization() -> None:
    if not FINALIZATION.exists():
        return
    data = json.loads(FINALIZATION.read_text(encoding="utf-8"))
    data["html"] = "index.html"
    data["local_html"] = "index_local.html"
    FINALIZATION.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def publication_url(row: dict) -> str:
    doi = str(row.get("doi", "")).strip()
    if doi:
        return f"https://doi.org/{doi}"
    return str(row.get("ieee_document_url") or row.get("publisher_url") or "https://ieeexplore.ieee.org/")


def common_decorations(page: str, local: bool) -> str:
    description = (
        "IEEE Transactions on Wireless Communications 2023 年以来语义通信论文全景调研，"
        "包含筛选记录、逐篇分析、通信系统定位、关键图表与横向比较。"
    )
    meta = (
        f"<meta name='description' content='{html.escape(description)}'>"
        "<meta name='color-scheme' content='light'>"
        "<meta name='theme-color' content='#10243d'>"
    )
    if "name='description'" not in page:
        page = page.replace("<title>", meta + "<title>", 1)
    if PUBLIC_CSS not in page:
        page = page.replace("</style>", PUBLIC_CSS + "</style>", 1)
    if "class='skip-link'" not in page:
        page = page.replace("<body>", "<body><a class='skip-link' href='#content'>跳到正文</a>", 1)
    page = page.replace("<main>", "<main id='content'>", 1)
    if "class='home-link'" not in page:
        page = page.replace("<nav>", "<nav aria-label='论文目录'><a class='home-link' href='../'>← 返回调研主页</a>", 1)
    edition = "本地阅读版 · PDF 链接" if local else "公开发布版 · 出版链接"
    if "class='edition'" not in page:
        page = page.replace("<main id='content'>", f"<main id='content'><span class='edition'>{edition}</span>", 1)
    if local:
        page = page.replace(
            "<title>IEEE TWC 语义通信论文全景调研（2023 至今）</title>",
            "<title>IEEE TWC 语义通信论文全景调研（本地阅读版）</title>",
            1,
        )
    return page


def make_public(page: str, by_title: dict[str, dict], by_filename: dict[str, dict]) -> str:
    article_pattern = re.compile(r"<article\b.*?</article>", re.S)

    def convert_article(match: re.Match[str]) -> str:
        block = match.group(0)
        title_match = re.search(r"<h2>(.*?)</h2>", block, re.S)
        title = html.unescape(re.sub(r"<.*?>", "", title_match.group(1))).strip() if title_match else ""
        row = by_title.get(title, {})
        url = publication_url(row)
        block = re.sub(r"href=(['\"])papers/.*?\.pdf\1", lambda _: f"href='{html.escape(url, quote=True)}'", block)
        block = block.replace("打开本地 PDF", "DOI / IEEE Xplore")
        block = block.replace(">本地 PDF</a>", ">出版页面</a>")
        return block

    page = article_pattern.sub(convert_article, page)

    # The cross-paper comparison table sits outside the article blocks and has
    # one PDF link per paper.  Convert those links by their local filename.
    def convert_remaining(match: re.Match[str]) -> str:
        quote = match.group(1)
        path = match.group(2)
        row = by_filename.get(PureWindowsPath(path).name, {})
        return f"href={quote}{html.escape(publication_url(row), quote=True)}{quote}"

    page = re.sub(r"href=(['\"])(papers/.*?\.pdf)\1", convert_remaining, page)
    page = re.sub(r">PDF</a>", ">出版页面</a>", page)
    return page


def normalize(page: str) -> str:
    return "\n".join(line.rstrip() for line in page.splitlines()) + "\n"


def main() -> None:
    rows = load_manifest()
    source_path = LOCAL_HTML if LOCAL_HTML.exists() else PUBLIC_HTML
    source = source_path.read_text(encoding="utf-8")
    if not re.search(r"href=['\"]papers/", source):
        raise SystemExit("Local source page has no local PDF links; refusing to overwrite both editions.")

    by_title = {str(row.get("title", "")).strip(): row for row in rows}
    by_filename = {paper_filename(str(row.get("pdf_path", ""))): row for row in rows}
    local_page = common_decorations(source, local=True)
    public_source = source.replace("本地阅读版 · PDF 链接", "公开发布版 · 出版链接")
    public_source = public_source.replace(
        "<title>IEEE TWC 语义通信论文全景调研（本地阅读版）</title>",
        "<title>IEEE TWC 语义通信论文全景调研（2023 至今）</title>",
        1,
    )
    public_page = common_decorations(make_public(public_source, by_title, by_filename), local=False)

    LOCAL_HTML.write_text(normalize(local_page), encoding="utf-8")
    PUBLIC_HTML.write_text(normalize(public_page), encoding="utf-8")
    sanitize_manifest(rows)
    sanitize_finalization()

    local_links = len(re.findall(r"href=['\"]papers/", local_page))
    public_links = len(re.findall(r"href=['\"]papers/", public_page))
    print(f"local edition: {local_links} local PDF links")
    print(f"public edition: {public_links} local PDF links")
    print(f"manifest: {len(rows)} sanitized records")
    if local_links == 0 or public_links != 0:
        raise SystemExit("Publication validation failed.")


if __name__ == "__main__":
    main()
