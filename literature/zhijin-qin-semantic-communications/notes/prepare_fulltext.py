from __future__ import annotations

import csv
import difflib
import json
import re
import unicodedata
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
TEXT = ROOT / "notes" / "text"
ASSETS = ROOT / "assets"


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).lower()
    return re.sub(r"[^a-z0-9]", "", value)


def safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")[:150]


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if len(s.strip()) > 30]


def extract_abstract(text: str) -> str:
    match = re.search(r"\bAbstract\s*[—–-]?\s*(.*?)(?:\bIndex Terms\b|\bKeywords\b|\bI\.\s*INTRODUCTION\b|\b1\.\s*Introduction\b)", text, re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()[:5000]


DATASETS = ["CIFAR-10", "CIFAR-100", "ImageNet", "MS COCO", "COCO", "CLEVR", "Europarl", "Flickr8k", "Flickr30k", "LibriSpeech", "LJSpeech", "UrbanSound8K", "MNIST", "Kodak", "DIV2K", "Vimeo-90K", "Cityscapes", "ModelNet40", "UCF101", "HMDB51"]
CHANNELS = ["AWGN", "Rayleigh", "Rician", "binary symmetric channel", "packet erasure channel", "MIMO", "OFDM", "OTFS", "fading channel", "erasure channel"]
METRICS = ["PSNR", "MS-SSIM", "SSIM", "LPIPS", "DISTS", "BLEU", "BERT similarity", "BERTScore", "word error rate", "WER", "accuracy", "mIoU", "MOS", "PESQ", "STOI", "semantic similarity"]
METHODS = ["DeepSC", "DeepJSCC", "Transformer", "Swin Transformer", "LSTM", "GRU", "GAN", "VQ-VAE", "vector quantization", "codebook", "diffusion", "large language model", "large model", "knowledge graph", "scene graph", "HARQ", "LDPC", "reinforcement learning", "federated learning", "multi-task learning", "domain adaptation", "unequal error protection"]

LANDMARKS = {
    "Deep Learning Enabled Semantic Communication Systems",
    "Semantic Communication Systems for Speech Transmission",
    "Task-Oriented Multi-User Semantic Communications for VQA",
    "Beyond Transmitting Bits: Context, Semantics, and Task-Oriented Communications",
    "Robust Semantic Communications With Masked VQ-VAE Enabled Codebook",
    "Vector Quantized Semantic Communication System",
    "Semantic Communication With Memory",
    "Semantic Communications With Variable-Length Coding for Extended Reality",
    "A Unified Multi-Task Semantic Communication System for Multimodal Data",
    "Task-Oriented Scene Graph-Based Semantic Communications With Adaptive Channel Coding",
    "Toward Intelligent Communications: Large Model Empowered Semantic Communications",
    "Hybrid Digital-Analog Semantic Communications",
    "Semantic Communication Based on Large Language Model for Underwater Image Transmission",
    "Joint Semantic-Channel Coding and Modulation for Token Communications",
    "Knowledge Graph-Enhanced Robust Cognitive Semantic Communication Against Semantic Impairment",
    "Large AI Model-Enabled Generative Semantic Communications for Image Transmission",
    "Distribution-Aware Constellation Learning for Image Transmission",
    "Semantic Feature Multiple Access Empowered Integrated Learning and Communication Networks",
}


def find_pdf(title: str, pdfs: list[Path]) -> tuple[Path | None, float]:
    target = norm(title)
    exact = [p for p in pdfs if norm(p.stem) == target]
    if exact:
        return exact[0], 1.0
    best = max(((difflib.SequenceMatcher(None, target, norm(p.stem)).ratio(), p) for p in pdfs), default=(0.0, None))
    return (best[1], best[0]) if best[0] >= 0.78 else (None, best[0])


def hits(text: str, values: list[str]) -> list[str]:
    return [value for value in values if re.search(r"\b" + re.escape(value) + r"\b", text, re.I)]


def evidence_sentences(text: str, pattern: str, limit: int = 3) -> list[str]:
    chosen = []
    for sentence in sentences(text):
        if re.search(pattern, sentence, re.I) and 40 <= len(sentence) <= 700:
            chosen.append(sentence)
        if len(chosen) == limit:
            break
    return chosen


def render_pages(doc: fitz.Document, title: str) -> list[dict]:
    if title not in LANDMARKS:
        return []
    page_text = [page.get_text("text") for page in doc]
    method_page = 0
    for i, text in enumerate(page_text[: min(6, len(page_text))]):
        if re.search(r"Fig\.\s*[12]", text, re.I) and re.search(r"system|architecture|framework|model|overview", text, re.I):
            method_page = i; break
    result_page = max(0, len(doc) - 2)
    for i in range(max(method_page + 1, 2), len(page_text)):
        if re.search(r"Fig\.|Table", page_text[i], re.I) and re.search(r"result|performance|outperform|PSNR|BLEU|accuracy|SSIM|WER", page_text[i], re.I):
            result_page = i; break
    rendered = []
    for kind, page_no in (("method", method_page), ("result", result_page)):
        filename = f"{safe(title)}_{kind}_p{page_no + 1}.png"
        pix = doc[page_no].get_pixmap(matrix=fitz.Matrix(0.9, 0.9), alpha=False)
        pix.save(ASSETS / filename)
        rendered.append({"kind": kind, "page": page_no + 1, "file": f"assets/{filename}"})
    return rendered


def main() -> None:
    TEXT.mkdir(parents=True, exist_ok=True); ASSETS.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((ROOT / "included_papers.csv").open(encoding="utf-8-sig")))
    pdfs = list(PAPERS.glob("*.pdf"))
    notes = []
    unmatched = []
    for row in rows:
        pdf, score = find_pdf(row["title"], pdfs)
        if pdf is None:
            row.update(pdf="", download_status="not_downloaded", analysis_status="metadata_and_abstract")
            notes.append({**row, "datasets": [], "channels": [], "metrics": [], "methods": [], "evidence": [], "figures": []})
            unmatched.append((row["title"], score))
            continue
        try:
            doc = fitz.open(pdf)
            page_text = [page.get_text("text") for page in doc]
            full_text = "\n\n".join(page_text)
            (TEXT / f"{safe(row['title'])}.txt").write_text(full_text, encoding="utf-8")
            pdf_abstract = extract_abstract("\n".join(page_text[:2]))
            if pdf_abstract:
                row["abstract"] = pdf_abstract
            row.update(pdf=f"papers/{pdf.name}", download_status="downloaded", analysis_status="fulltext_extracted")
            evidence = evidence_sentences(full_text, r"we propose|we present|we develop|simulation results|experimental results|outperform|achiev")
            notes.append({**row, "pages": len(doc), "datasets": hits(full_text, DATASETS), "channels": hits(full_text, CHANNELS),
                          "metrics": hits(full_text, METRICS), "methods": hits(full_text, METHODS), "evidence": evidence,
                          "figures": render_pages(doc, row["title"])})
            doc.close()
        except Exception as exc:
            row.update(pdf=f"papers/{pdf.name}", download_status="downloaded", analysis_status=f"extract_failed: {type(exc).__name__}")
            notes.append({**row, "datasets": [], "channels": [], "metrics": [], "methods": [], "evidence": [], "figures": []})
    fields = list(rows[0].keys())
    with (ROOT / "included_papers.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    (NOTES_JSON := ROOT / "notes" / "structured_notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"papers={len(rows)} matched={len(rows)-len(unmatched)} unmatched={len(unmatched)} assets={len(list(ASSETS.glob('*.png')))}")
    for title, score in unmatched:
        print(f"UNMATCHED {score:.3f} {title}")


if __name__ == "__main__":
    main()
