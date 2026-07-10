from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if len(s.strip()) > 25]


def pick(sentences: list[str], pattern: str, fallback: str, limit: int = 2) -> str:
    matches = [s for s in sentences if re.search(pattern, s, re.I)]
    return " ".join((matches or [fallback])[:limit])


def limitation(paper: dict) -> str:
    if paper.get("download_status") != "downloaded":
        return "全文未获，当前判断仅基于题录、摘要和交叉数据库元数据，不能替代对方法细节与实验表格的全文核验。"
    if paper.get("scope_status") == "综述/观点":
        return "本文主要贡献是框架、分类或研究议程，并不提供可与算法论文等量比较的端到端实验；其判断需结合后续实证论文验证。"
    if paper.get("scope_status") == "系统与网络层":
        return "本文重点在资源分配、网络优化或计算卸载，通常把语义编码器性能抽象为已知函数，因此对语义表示本身、真实信道误码和模型失配的解释有限。"
    category = paper.get("category", "")
    if "图像" in category:
        return "实验通常集中在有限数据集与仿真信道，重建/感知指标不必然等价于真实下游语义效用；跨场景、真实无线链路与端侧复杂度仍需进一步验证。"
    if "文本" in category:
        return "性能依赖语料、预训练语言模型和语义相似度指标；跨语言、事实一致性、幻觉以及真实时延/算力开销往往没有被同时覆盖。"
    if "安全" in category:
        return "鲁棒性或安全结论依赖给定攻击者知识、噪声模型和训练分布；对未知攻击、真实射频失真及跨模型迁移的保证仍有限。"
    if "数字化" in category:
        return "离散化提升了与数字链路的兼容性，但码本失配、index/bit error 跳变、信道译码开销和不同调制阶数下的泛化仍是关键限制。"
    return "结论主要来自论文设定的数据、任务和仿真环境；跨数据域、跨信道、端侧复杂度与真实部署可复现性仍需要独立验证。"


def chips(values: list[str]) -> str:
    if not values:
        return '<span class="muted">论文文本中未稳定识别</span>'
    return " ".join(f'<span class="chip">{esc(v)}</span>' for v in values)


def paper_card(p: dict, local_links: bool) -> str:
    ss = split_sentences(p.get("abstract", ""))
    why = pick(ss, r"however|challenge|problem|limitation|bottleneck|difficult|lack|aim", ss[0] if ss else "摘要信息不足。")
    how = pick(ss, r"we propose|we present|we develop|we design|introduc|framework|system", ss[1] if len(ss) > 1 else (ss[0] if ss else "摘要信息不足。"))
    what = pick(ss, r"result|demonstrat|outperform|achiev|improv|show that", ss[-1] if ss else "摘要信息不足。")
    doi_link = f"https://doi.org/{p['doi']}" if p.get("doi") else (f"https://arxiv.org/abs/{p['arxiv_id']}" if p.get("arxiv_id") else p.get("oa_url", ""))
    pdf_html = ""
    if p.get("pdf"):
        if local_links:
            pdf_html = f'<a class="button" href="{esc(p["pdf"])}">打开本地 PDF</a>'
        else:
            pdf_html = '<span class="button ghost">本地全文已归档</span>'
    else:
        pdf_html = '<span class="button warn">全文未获</span>'
    figures = []
    for fig in p.get("figures", []):
        label = "方法/架构页" if fig["kind"] == "method" else "关键结果页"
        source_href = p.get("pdf") if local_links and p.get("pdf") else doi_link
        figures.append(f'''<figure><a href="{esc(source_href)}"><img loading="lazy" src="{esc(fig['file'])}" alt="{esc(p['title'])} {label}"></a>
        <figcaption>{esc(p['title'])}，{label}，原 PDF 第 {fig['page']} 页。</figcaption></figure>''')
    figure_block = "".join(figures)
    evidence = "".join(f"<li>{esc(x)}</li>" for x in p.get("evidence", [])) or "<li>未从全文自动抽取到足够稳定的结果句；请结合摘要与原文。</li>"
    return f'''<article class="paper" id="{slug(p['title'])}" data-year="{p['year']}" data-category="{esc(p['category'])}">
      <h2>{esc(p['title'])}</h2>
      <div class="meta"><span>{p['year']}</span><span>{esc(p['venue'] or 'Venue 未核定')}</span><span>{esc(p['category'])}</span><span>{esc(p['scope_status'])}</span></div>
      <p class="authors">{esc(p['authors'])}</p>
      <div class="actions">{pdf_html}<a class="button ghost" href="{esc(doi_link)}">DOI / 出版页面</a></div>
      <div class="grid two">
        <section><h3>WHY｜研究动机</h3><p>{esc(why)}</p></section>
        <section><h3>HOW｜核心方法</h3><p>{esc(how)}</p></section>
        <section><h3>WHAT｜主要结论</h3><p>{esc(what)}</p></section>
        <section><h3>Codex 判断与局限</h3><p>{esc(limitation(p))}</p></section>
      </div>
      <details><summary>摘要与全文证据</summary><p>{esc(p.get('abstract') or '摘要未获。')}</p><ul>{evidence}</ul></details>
      <div class="evidence-grid">
        <div><b>数据集线索</b><br>{chips(p.get('datasets', []))}</div>
        <div><b>信道/链路线索</b><br>{chips(p.get('channels', []))}</div>
        <div><b>指标线索</b><br>{chips(p.get('metrics', []))}</div>
        <div><b>方法关键词</b><br>{chips(p.get('methods', []))}</div>
      </div>
{figure_block}
    </article>'''


def render(local_links: bool) -> str:
    papers = json.loads((ROOT / "notes" / "structured_notes.json").read_text(encoding="utf-8"))
    excluded = list(csv.DictReader((ROOT / "excluded_or_boundary.csv").open(encoding="utf-8-sig")))
    year_counts = Counter(int(p["year"]) for p in papers)
    cat_counts = Counter(p["category"] for p in papers)
    scope_counts = Counter(p["scope_status"] for p in papers)
    coauthors = Counter()
    for p in papers:
        for author in re.split(r";\s*|,\s*", p.get("authors", "")):
            if author and norm_author(author) != "zhijin qin":
                coauthors[author] += 1
    top_coauthors = coauthors.most_common(15)
    downloaded = sum(p.get("download_status") == "downloaded" for p in papers)
    fulltext = sum(p.get("analysis_status") == "fulltext_extracted" for p in papers)
    nav = "".join(f'<a href="#{slug(p["title"])}">{esc(p["title"])}</a>' for p in papers)
    overview_rows = "".join(f'<tr><td>{p["year"]}</td><td><a href="#{slug(p["title"])}">{esc(p["title"])}</a></td><td>{esc(p["category"])}</td><td>{esc(p["scope_status"])}</td><td>{"✓" if p.get("pdf") else "—"}</td></tr>' for p in papers)
    excluded_rows = "".join(f'<tr><td>{esc(p["year"])}</td><td>{esc(p["title"])}</td><td>{esc(p["screening_reason"])}</td></tr>' for p in excluded)
    year_bars = "".join(f'<div class="bar"><span>{y}</span><i style="--v:{year_counts[y]}"></i><b>{year_counts[y]}</b></div>' for y in sorted(year_counts))
    cat_list = "".join(f'<li><b>{esc(k)}</b><span>{v} 篇</span></li>' for k, v in cat_counts.most_common())
    author_list = "".join(f'<li><b>{esc(k)}</b><span>{v} 篇共著</span></li>' for k, v in top_coauthors)
    cards = "".join(paper_card(p, local_links) for p in papers)
    mode = "本地全文版" if local_links else "公开网页版"
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zhijin Qin 团队语义通信论文调研（2021—2026）</title>
<script>window.MathJax={{tex:{{inlineMath:[["\\\\(","\\\\)"]],displayMath:[["\\\\[","\\\\]"]]}}}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
:root{{--bg:#f5f7fb;--paper:#fff;--ink:#18202b;--muted:#657184;--accent:#1666c5;--line:#dbe2ec;--soft:#edf4fd;--warn:#8a4b00}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.72 system-ui,-apple-system,"Segoe UI",sans-serif}}a{{color:var(--accent)}}aside{{position:fixed;inset:0 auto 0 0;width:320px;background:#111c2f;color:#dfeaff;padding:24px 18px;overflow:auto}}aside h1{{font-size:20px;line-height:1.3}}aside input{{width:100%;padding:10px;border-radius:8px;border:1px solid #42516b;background:#172640;color:white}}nav{{display:grid;gap:6px;margin-top:18px}}nav a{{color:#cbd9ee;text-decoration:none;font-size:12px;line-height:1.35;padding:7px;border-radius:6px}}nav a:hover{{background:#253855}}main{{margin-left:320px;padding:36px;max-width:1420px}}.hero,.panel,.paper{{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:26px;margin:0 0 24px;box-shadow:0 5px 20px #2030500b}}.hero h1{{font-size:34px;margin:.2em 0}}.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.kpi{{background:var(--soft);padding:16px;border-radius:12px}}.kpi b{{font-size:27px;display:block;color:var(--accent)}}.grid.two{{display:grid;grid-template-columns:1fr 1fr;gap:15px}}.grid section{{background:#f8fafc;border-left:4px solid #a8c9ef;padding:12px 16px;border-radius:8px}}h2{{font-size:23px;line-height:1.35;margin-top:0}}h3{{font-size:15px;margin:.2em 0}}.meta,.actions{{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}}.meta span,.chip{{display:inline-block;background:#edf2f7;border-radius:999px;padding:3px 9px;font-size:12px}}.authors{{color:#3c4c61}}.button{{display:inline-block;border-radius:8px;padding:7px 11px;background:var(--accent);color:white;text-decoration:none;font-size:13px}}.button.ghost{{background:#e9eef6;color:#34455d}}.button.warn{{background:#fff0db;color:var(--warn)}}.evidence-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:14px}}.evidence-grid>div{{border:1px solid var(--line);border-radius:8px;padding:10px}}details{{margin:14px 0;border-top:1px dashed var(--line);padding-top:10px}}summary{{cursor:pointer;color:var(--accent);font-weight:650}}figure{{margin:18px 0}}figure img{{display:block;max-width:100%;margin:auto;border:1px solid var(--line);border-radius:9px}}figcaption{{font-size:12px;color:var(--muted);text-align:center}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{border-bottom:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}}.bar{{display:grid;grid-template-columns:52px 1fr 35px;gap:8px;align-items:center;margin:8px 0}}.bar i{{height:14px;background:linear-gradient(90deg,#66a7ec,#1666c5);width:calc(var(--v)*4%);min-width:8px;border-radius:8px}}.split{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}.rank{{list-style:none;padding:0}}.rank li{{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:7px 0}}.muted{{color:var(--muted)}}@media(max-width:900px){{aside{{position:relative;width:auto;max-height:420px}}main{{margin:0;padding:16px}}.kpis,.grid.two,.evidence-grid,.split{{grid-template-columns:1fr}}}}
</style></head><body><aside><h1>Zhijin Qin 团队语义通信论文</h1><p>{mode}<br>2021—2026-07-10</p><input id="q" placeholder="筛选论文标题、作者或正文…"><nav><a href="#overview">总览与方法</a><a href="#comparison">论文总表</a><a href="#synthesis">路线综合</a>{nav}<a href="#excluded">排除与边界</a></nav></aside><main>
<section class="hero" id="overview"><p class="muted">系统性作者调研 · 最后更新 2026-07-10</p><h1>Zhijin Qin 团队语义通信论文调研</h1><p>本报告以 Zhijin Qin 为作者锚点，覆盖 2021 年至今的语义通信、任务/目标导向通信、语义网络与语义源信道编码工作。作者消歧和搜索依据 OpenAlex、Semantic Scholar、DBLP、arXiv 与 DOI 官方记录；IEEE 全文使用项目专用下载 skill 串行获取。</p>
<div class="kpis"><div class="kpi"><b>{len(papers)}</b>纳入论文</div><div class="kpi"><b>{downloaded}</b>本地全文</div><div class="kpi"><b>{fulltext}</b>完成全文抽取</div><div class="kpi"><b>{len(excluded)}</b>排除/边界</div></div>
<p>全文覆盖率：\\[C_{{PDF}}=\\frac{{N_{{downloaded}}}}{{N_{{included}}}}=\\frac{{{downloaded}}}{{{len(papers)}}}={downloaded/len(papers):.1%}.\\]</p></section>
<section class="panel split"><div><h2>年度分布</h2>{year_bars}</div><div><h2>主题路线</h2><ul class="rank">{cat_list}</ul></div></section>
<section class="panel split"><div><h2>高频合作作者</h2><ul class="rank">{author_list}</ul></div><div><h2>检索与筛选结论</h2><p>130 条主题候选经作者消歧、正式版/预印本去重和全文类型筛选后纳入 {len(papers)} 篇。2025—2026 年通过 arXiv 作者检索补齐索引滞后成果。Google Scholar 页面连接失败，没有被当作可复现数据源。</p><p><a href="search_strategy.md">查看完整检索策略</a> · <a href="included_papers.csv">纳入表</a> · <a href="excluded_or_boundary.csv">排除表</a> · <a href="manifest.jsonl">下载清单</a></p></div></section>
<section class="panel" id="comparison"><h2>全部纳入论文</h2><div class="table-wrap"><table><thead><tr><th>年</th><th>完整标题</th><th>路线</th><th>层级</th><th>全文</th></tr></thead><tbody>{overview_rows}</tbody></table></div></section>
<section class="panel" id="synthesis"><h2>发展脉络与综合判断</h2><ol><li><b>2021：DeepSC 奠基。</b>从文本和语音切入，证明端到端语义编码可直接优化语义相似度、BLEU、WER 等任务指标，并展现低 SNR 鲁棒性。</li><li><b>2022：从单模态扩到多用户、多任务和语义噪声。</b>研究开始处理 VQA、场景分类、domain adaptation、资源分配、semantic noise 和 masked VQ-VAE 码本。</li><li><b>2023：记忆、可变长与数字化。</b>Mem-DeepSC、variable-length coding、VQ-DeepSC、MIMO speech-to-text 与 scene graph 路线使表示结构更加显式。</li><li><b>2024：系统化和网络化。</b>工作扩展到 GAN 文本、多模态统一模型、边云端协同、HDA、LLM、跨层安全和计算网络，并形成多篇综述。</li><li><b>2025—2026：生成式大模型、真实数字链路与新场景。</b>研究进一步覆盖 diffusion/LLM、token modulation、packet erasure、NTN、holographic/3DGS、OTFS、learnable constellation 和语义价值度量。</li></ol><h3>核心优势</h3><p>该团队并非只维护一个单一模型，而是形成了“语义表示—端到端编解码—多模态任务—网络资源—安全鲁棒—大模型生成”的连续研究谱系；早期 DeepSC 的任务指标思想逐渐扩展为码本、scene graph、memory、token 与生成式先验等多种显式语义载体。</p><h3>仍待解决的问题</h3><p>跨论文普遍依赖仿真信道和固定训练分布；语义指标在不同模态之间仍缺少统一可比性；大模型系统的事实一致性、隐私、能耗和空口时延仍不充分；数字化工作虽明显增加，但真正联合处理 bit/index error、信道译码、调制阶数和码本跳变的论文仍占少数。</p></section>
{cards}
<section class="panel" id="excluded"><h2>排除与边界记录</h2><div class="table-wrap"><table><thead><tr><th>年</th><th>标题</th><th>原因</th></tr></thead><tbody>{excluded_rows}</tbody></table></div><p class="muted">AI 辅助声明：本报告使用 Codex 协助检索、作者消歧、PDF 文本抽取、证据结构化和网页生成；题录与 DOI 通过外部学术数据库和本地全文交叉核验。自动抽取的关键词只表示全文命中，不自动等同于论文的主要实验设置。</p></section>
</main><script>const q=document.getElementById('q');q.addEventListener('input',()=>{{const s=q.value.toLowerCase();document.querySelectorAll('.paper').forEach(x=>x.style.display=x.innerText.toLowerCase().includes(s)?'block':'none')}});</script></body></html>'''


def norm_author(value: str) -> str:
    return value.replace("‐", "-").strip().lower()


def write_manifest() -> None:
    papers = json.loads((ROOT / "notes" / "structured_notes.json").read_text(encoding="utf-8"))
    missing_reasons = {
        "Toward Wisdom-Evolutionary and Primitive-Concise 6G: A New Paradigm of Semantic Communication Networks": "Gold OA publisher page returned 403; browser showed CAPTCHA; verification was not bypassed.",
        "Goal-oriented communications for future cyber–physical systems": "Nature publisher page is closed access; PDF URL returned HTML; no open author version was located.",
    }
    with (ROOT / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for p in papers:
            source = "local-existing"
            if p.get("arxiv_id"):
                source = "arXiv/open version"
            if p.get("doi", "").lower().startswith(("10.1109/", "10.23919/")) and p.get("pdf"):
                source = "IEEE Xplore authenticated skill or existing IEEE copy"
            record = {k: p.get(k, "") for k in ("title", "year", "authors", "venue", "doi", "arxiv_id", "pdf", "download_status", "analysis_status")}
            record["source"] = source
            if p["title"] in missing_reasons:
                record["failure_reason"] = missing_reasons[p["title"]]
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    write_manifest()
    (ROOT / "index.html").write_text(render(local_links=False), encoding="utf-8")
    (ROOT / "index_local.html").write_text(render(local_links=True), encoding="utf-8")
    print("rendered index.html and index_local.html")


if __name__ == "__main__":
    main()
