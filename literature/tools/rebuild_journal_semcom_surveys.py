#!/usr/bin/env python3
"""Re-read and rebuild the TWC/TCCN/TCSVT semantic-communication surveys.

The previous journal pages rendered snippets produced from ``pdftotext
-layout``.  On IEEE two-column papers that representation interleaves both
columns.  This rebuild uses Poppler's normal reading-order extraction, treats
the clean bibliographic abstract as the rhetorical anchor, and creates a
separate Chinese synthesis layer.  Raw PDF text is never rendered in HTML.

Outputs per journal directory:

* ``notes/synthesized_analysis.jsonl`` -- presentation-layer paper analyses
* ``notes/reread_audit.jsonl`` -- PDF/section/evidence audit trail
* ``notes/cross_paper_comparison.csv`` -- compact comparison table
* ``index.html`` -- public edition (DOI/IEEE links, no restricted PDFs)
* ``index_local.html`` -- local reading edition (downloaded PDF links)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rewrite_team_analysis import polish_zh  # noqa: E402


ANALYSIS_VERSION = "journal_fulltext_reread_v4_2026-08-28"


JOURNALS = {
    "twc": {
        "directory": "ieee-twc-semantic-communications-2023-present",
        "short": "TWC",
        "title": "IEEE TWC 语义通信论文全景调研（2023—至今）",
        "venue": "IEEE Transactions on Wireless Communications",
        "scope": "语义通信、任务导向通信、DeepJSCC、数字语义接口及相关网络/理论工作",
        "accent": "#0b6f6a",
        "accent_dark": "#123b43",
    },
    "tccn": {
        "directory": "ieee-tccn-semantic-communications-2023-present",
        "short": "TCCN",
        "title": "IEEE TCCN 语义通信论文全景调研（2023—至今）",
        "venue": "IEEE Transactions on Cognitive Communications and Networking",
        "scope": "语义/任务通信、DeepJSCC、数字调制与码本、生成式与多用户认知网络",
        "accent": "#3454a5",
        "accent_dark": "#172b58",
    },
    "tcsvt": {
        "directory": "ieee-tcsvt-semantic-communications-2023-present",
        "short": "TCSVT",
        "title": "IEEE TCSVT 语义通信与视觉传输调研（2023—至今）",
        "venue": "IEEE Transactions on Circuits and Systems for Video Technology",
        "scope": "图像/视频无线传输、JSCC、SoftCast、任务导向与生成式视觉编码",
        "accent": "#a0522d",
        "accent_dark": "#512b1f",
    },
}


POLLUTION = re.compile(
    r"Authorized licensed use|Downloaded on|Restrictions apply|IEEE TRANSACTIONS|"
    r"Digital Object Identifier|Personal use is permitted|republication/redistribution|"
    r"rights/index\.html|Manuscript received|Date of publication|associate editor|"
    r"Corresponding author|e-mail:|©\s*20\d\d\s+IEEE|This work is licensed under",
    re.I,
)

NARRATIVE_BANNED = re.compile(
    r"Authorized licensed use|Downloaded on|IEEE TRANSACTIONS|Digital Object Identifier|"
    r"Manuscript received|is organized as follows|Section [IVX]+ (?:presents|introduces|evaluates|describes|details)|"
    r"\b(?:Fig|Table)\.|\bet al\.\s*\[|Index Terms|Member, IEEE|Fellow, IEEE|"
    r"^[A-Z][A-Z-]+(?:\s+(?:AND|and|&)\s+[A-Z][A-Z-]+)?\s*:\s*|\bRELATED WORKS?\b",
    re.I,
)

# Display-layer prose must be materially stricter than the raw evidence pool.
# IEEE reference lists, equations, and figure/table captions can survive normal
# reading-order extraction as syntactically long "sentences".  They remain
# useful in the audit layer, but must never be translated and rendered as a
# paper's method, overhead, channel model, or result narrative.
DISPLAY_BANNED = re.compile(
    r"\[[0-9]{1,3}(?:\s*[,;-]\s*[0-9]{1,3})*\]|"
    r"\b(?:vol\.|no\.|pp\.|doi\s*:|arXiv\s*:|References?)\b|"
    r"\bIEEE\s+(?:Trans\.|Transactions|J\.|Journal|Commun\.|Internet|Wireless)\b|"
    r"\b(?:Fig\.|Figure|Table)\s*[0-9IVX]+|"
    r"^[A-Z][A-Za-z'’-]+\s*,\s*[\"“]|"
    r"\b(?:is organized as follows|the rest of (?:this|the) paper)\b",
    re.I,
)

KNOWN_DATASETS = [
    "CIFAR-10", "CIFAR-100", "ImageNet", "Kodak", "CLIC", "DIV2K", "COCO",
    "MS-COCO", "Cityscapes", "CelebA", "FFHQ", "MNIST", "Fashion-MNIST",
    "Europarl", "WMT", "Flickr30K", "Flickr8K", "LibriSpeech", "Libri-Light",
    "VCTK", "TIMIT", "LJSpeech", "Common Voice", "VoxCeleb", "ModelNet40",
    "ShapeNet", "ScanNet", "S3DIS", "KITTI", "nuScenes", "DAVIS", "UVG",
    "HEVC", "Vimeo-90K", "UCF101", "HMDB51", "Something-Something V2",
    "SUIM", "EUVP", "UFO", "UIEBD", "DRIVE", "Kaggle", "BraTS",
    "Pascal VOC", "VOC2012", "ADE20K", "Tiny ImageNet", "STL-10", "BDD100K",
    "OPV2V", "V2X-Sim", "DAIR-V2X", "CARLA", "OpenCOOD", "nuScenes",
]

KNOWN_BASELINES = [
    "JPEG", "JPEG2000", "BPG", "VVC", "H.264", "H.265", "HEVC", "AV1",
    "DeepJSCC", "ADJSCC", "NTSCC", "DeepSC", "DeepSC-S", "DeepSC-ST",
    "JSCC", "SSCC", "LDPC", "Polar", "Turbo", "Reed-Solomon", "QAM",
    "OFDM", "SoftCast", "Swift", "WebP", "SwinJSCC", "ViT", "ResNet",
    "YOLO", "BERT", "RoBERTa", "GPT-2", "CLIP", "PPO", "SAC", "DQN",
    "TD3", "DDPG", "FedAvg", "VTM", "HM", "ETC", "FEC",
]

KNOWN_METRICS = [
    "PSNR", "SSIM", "MS-SSIM", "LPIPS", "FID", "KID", "MSE", "NMSE",
    "BLEU", "BERTScore", "METEOR", "CIDEr", "WER", "CER", "PESQ", "STOI",
    "MOS", "accuracy", "classification accuracy", "mAP", "IoU", "mIoU",
    "latency", "throughput", "energy efficiency", "semantic similarity", "bpp",
    "BER", "SER", "PER", "R-sum", "Rsum", "F1-score", "AUC",
]

KNOWN_CHANNELS = [
    "AWGN", "Rayleigh", "Rician", "Nakagami", "BSC", "BEC", "erasure channel",
    "binary symmetric channel", "fading channel", "MIMO", "OFDM", "OTFS",
    "packet loss", "bit flip", "wireless channel", "block fading",
]


TASK_RULES = [
    (("speech", "audio", "voice", "acoustic"), "语音/音频传输或识别", "语音波形、声学特征或说话人信息", "重建语音、识别文本或说话人任务结果"),
    (("video", "gop", "frame rate", "talking head", "streaming"), "视频传输、生成或控制", "视频帧、运动信息或时序语义", "重建/生成视频或视频任务结果"),
    (("point cloud", "3d scene", "gaussian splatting", "nerf", "metaverse"), "点云/三维场景传输", "三维点、视图或场景语义", "三维重建、渲染或下游感知结果"),
    (("image-text", "cross-modal", "multimodal", "multi-modal"), "多模态检索与任务通信", "图像、文本或其他模态的任务特征", "跨模态检索、匹配或联合推理结果"),
    (("text", "sentence", "language", "translation", "token communication"), "文本传输或语言任务", "句子、token 序列或语言语义", "恢复文本、翻译结果或语言任务输出"),
    (("image", "visual", "face", "retinal", "underwater"), "图像传输、压缩或生成", "图像及其视觉/任务语义", "重建/生成图像或视觉任务输出"),
    (("classification", "segmentation", "inference", "task-oriented", "goal-oriented", "retrieval", "recognition"), "任务导向推理", "源数据与下游任务所需特征", "分类、分割、检索或其他任务决策"),
    (("resource allocation", "power allocation", "scheduling", "deployment", "uav", "offloading"), "语义感知资源分配与网络优化", "用户、任务、信道和资源状态", "资源/部署策略及其语义效用"),
    (("theory", "rate-distortion", "fundamental", "exponent", "metric", "measure"), "语义信息度量与理论", "抽象信源—任务—信道模型", "界、度量或优化原则"),
    (("federated", "edge learning", "split learning", "over-the-air"), "边缘学习与任务通信", "梯度、模型更新或中间特征", "聚合模型或边缘推理结果"),
]


THEME_RULES = [
    ("security", ("secure", "security", "privacy", "eavesdrop", "attack", "steganography", "backdoor")),
    ("digital", ("digital", "vector quant", "vq-", "codebook", "bit-level", "constellation", "modulation", "ofdm", "otfs", "harq", "packet")),
    ("generative", ("generative", "diffusion", "foundation model", "large language model", "llm", "prompt", "nerf", "gaussian splatting")),
    ("multiuser", ("multi-user", "multiuser", "broadcast", "multiple access", "noma", "relay", "multicast")),
    ("resource", ("resource allocation", "power allocation", "scheduling", "deployment", "uav", "offloading", "energy efficient")),
    ("task", ("task-oriented", "goal-oriented", "classification", "segmentation", "inference", "retrieval")),
    ("adaptive", ("adaptive", "dynamic", "feedback", "rate control", "channel transferable")),
    ("theory", ("theory", "rate-distortion", "fundamental", "exponent", "metric", "measure")),
]


PRIOR_LIMIT_ZH = {
    "security": "只优化合法接收端的重建或任务 loss，并不会自动消除 latent 泄露、窃听或操纵风险；缺少的是把攻击者与保护目标放进同一系统模型。",
    "digital": "连续 latent 或独立设计的传统链路没有回答语义特征怎样量化、映射为有限符号，以及 bit/index 出错后为何不会跳到完全不同的语义。仅改进信源网络无法补上这一接口。",
    "generative": "把生成模型放在接收端并不等于通信开销自然降低；仍需明确发送什么条件、条件占多少资源，以及信道破坏条件时怎样约束幻觉和时延。",
    "multiuser": "把单用户语义编解码器逐个复制给多个用户，会忽略共享内容、异构信道、干扰和公平性，因而不能直接得到频谱有效的网络方案。",
    "resource": "只按 bit rate、吞吐量或平均失真分配资源，无法区分不同样本和任务的语义价值；外层优化必须得到可用的语义效用—资源曲线。",
    "task": "像素级重建是比下游决策更强、也更昂贵的目标；但只压缩 feature 又可能丢掉决定任务的少量证据，因此需要把任务 loss 与通信瓶颈联合设计。",
    "adaptive": "为固定 SNR 或带宽训练的模型具有固定瓶颈和保护方式；条件变化时重复运行同一网络，不能把码率或冗余重新分给变得脆弱的信息。",
    "theory": "不同论文各自报告准确率或重建指标，不能替代统一、可计算且与通信资源相联系的定义或可达界；缺失的是比较坐标而不是更深的网络。",
    "jscc": "分离压缩与信道编码优化的是中间 bit 可靠性，未必等价于本文关心的语义/任务质量；反过来，只做端到端网络而不交代带宽、功率和信道作用点也无法形成公平通信比较。",
    "compression": "提高无误链路上的率失真性能，并不能说明系统能承受真实无线误码或丢包；熵码流、层间依赖和生成条件一旦损坏，恢复机制必须另行设计。",
}

IMPORTANCE_ZH = {
    "语音/音频传输或识别": "语音的可懂度、识别正确率与波形误差并不总是同步，少量包丢失也可能破坏整段语言内容；有限码率下应优先保护语言与说话人语义。",
    "视频传输、生成或控制": "视频持续占用带宽且具有严格时延，单帧错误还会跨帧传播；通信系统必须同时处理时序一致性、资源占用和渐进退化。",
    "点云/三维场景传输": "XR 与三维感知的数据量极大而交互时延敏感；以更少信道使用保住几何和任务关键对象，会直接降低空口负担。",
    "文本传输或语言任务": "一个 token 错误就可能改变整句含义，因此仅看 BER 不足以评价链路；必须追踪最终语言意义或任务输出。",
    "图像传输、压缩或生成": "有限信道使用迫使系统决定哪些视觉内容值得保护；低 SNR 或高压缩率下，任务/感知关键结构往往比平均像素误差更重要。",
    "任务导向推理": "边缘设备常需要及时决策而不是完整副本；只发送任务充分信息可以降低时延与带宽，但前提是关键证据确实能穿过信道。",
    "语义感知资源分配与网络优化": "功率、带宽、算力和时延是共享资源；若调度器不知道语义效用，它可能增加吞吐量却没有改善任何用户真正关心的任务。",
    "语义信息度量与理论": "没有定义清楚的语义目标和资源坐标，就无法判断收益来自通信机制还是更换了数据集、模型或评价指标。",
    "边缘学习与任务通信": "梯度或中间特征既大又易受噪声影响，通信错误会直接改变训练收敛或推理决策；这使空口聚合与任务 loss 必须一起考虑。",
}


# Full-text reviewed presentation overrides for papers whose important digital
# interface facts are not expressed as one clean extractable sentence.  These
# are intentionally concise syntheses, not pasted PDF text; page provenance is
# preserved from the selected field that each override replaces.
CURATED_PRESENTATION_OVERRIDES = {
    "Deep Learning Enabled Semantic Communications With Speech Recognition and Synthesis": {
        "channel_summary": "DeepSC-ST 将语音语义特征映射为连续信道符号；AWGN、Rayleigh 或 Rician 噪声直接作用于这些连续符号，接收端再恢复文本或语音。",
    },
    "Robust Semantic Communications With Masked VQ-VAE Enabled Codebook": {
        "overhead_summary": "“Patch-16”设置把每个 16×16×3 图像块压缩为一个离散标量/index；因此 H×W 图像约产生 (H/16)(W/16) 个 index。若码本大小为 K，净索引开销为 (H/16)(W/16)⌈log₂K⌉ bit，尚未包含 LDPC、调制与包头。",
    },
    "Conceptual Learning and Causal Reasoning for Semantic Communication": {
        "method_summary": "发送端以 VAE 学习可解释的概念空间，并显式建模概念维度与任务变量之间的因果关系；接收端在受损语义变量上执行因果推理，恢复任务相关概念而非逐样本复刻。",
        "motivation.mechanism": "概念空间提供可解释的低维语义变量，因果图把这些变量与任务目标连接起来，使接收端能够利用结构知识补偿信道造成的语义偏移。",
    },
    "Resource Optimization for Semantic-Aware Networks With Task Offloading": {
        "method_summary": "系统先从多模态任务中提取可卸载的语义信息，再联合决定任务卸载、带宽/功率和边缘计算资源；MAPPO 用于在多用户耦合约束下学习分布式资源策略。",
    },
    "CoDS: Collaborative Perception via Digital Semantic Communication": {
        "overhead_summary": "论文用特征通道压缩比 γc=C/C₀ 和信道使用次数衡量开销；若要还原真实空口 bit 数，还需同时计入量化位宽、调制阶数、FEC 与包头。",
        "channel_summary": "连续协同感知特征先被转换为离散 bitstream；训练和仿真显式考虑数字传输错误，并通过语义感知的 bit/index 映射减小单比特错误引起的特征跳变。",
    },
    "DGSemCom: Digital Generative Semantic Communications via Discrete Denoising Diffusion Model for Latent Error Correction": {
        "channel_summary": "PQ 索引经数字信道后可能发生离散错误；接收端把纠错写成结合语义先验与信道似然的后验解码，并用离散去噪扩散模型恢复受损 latent/index。",
    },
    "ESC-MVQ: End-to-End Semantic Communication With Multi-Codebook Vector Quantization": {
        "overhead_summary": "论文以传输 bit 数相对原始图像 C×H×W×8 bit 定义压缩比；分子由多码本 index 数、各码本大小以及所选调制/FEC 共同决定。",
    },
    "SemHARQ: Semantic-Aware Hybrid Automatic Repeat Request for Multi-Task Semantic Communications": {
        "representation_summary": "发送端量化多任务语义特征并组织成可重传单元；初传后只重传被语义错误检测器判为受损的特征，其余资源用于增量语义信息。",
        "channel_summary": "初传特征经过有噪数字链路后，接收端先做任务感知的语义错误检测；SemHARQ 选择性重传受损特征并与初传结果融合，而不是要求整个 bitstream 一次无误到达。",
    },
    "Rate-Adaptive Vector Quantization for Deep Joint Source-Channel Coding": {
        "overhead_summary": "RAQJSCC 的 AMC 单元联合选择调制阶数 M_l 与有效码本大小 K_l；每个 index 的净信息量为 ⌈log₂K_l⌉ bit，真实信道使用次数还取决于调制阶数、信道码率和链路自适应约束。",
    },
    "VQ-DSC-R: Robust Vector Quantized-Enabled Digital Semantic Communication With OFDM Transmission": {
        "overhead_summary": "论文用激活码字数占总码本大小的比例（CUR）检查码本利用率，并用 bit compression ratio 衡量空口负担；完整开销还包括 index-to-bit、QAM、OFDM 导频和信道编码。",
        "channel_summary": "VQ index 被转换为 bit/QAM 符号并通过 OFDM 与 3GPP EPA 多径信道；接收端先进行 CSI refinement、均衡和数字解调，再以共享码本反量化，Stage-3 含噪训练用于降低 BER/index propagation error。",
    },
    "Generative AI-Driven Semantic Communication Networks: Architecture, Technologies, and Applications": {
        "method_summary": "该文是架构/综述工作：它提出 GAI 驱动的语义通信网络分层框架，并按知识构建、更新、共享、生成式推理和资源编排组织现有技术，而不是给出单一可复现 codec。",
    },
    "Generative Feature Imputing-A Technique for Error-Resilient Semantic Communication": {
        "method_summary": "发送端把图像编码为分组语义特征；当块衰落或数据包错误造成特征缺失时，接收端利用生成式特征填补模块和上下文先验补全受损区域，再执行重建或下游任务。",
    },
    "SINR-Adaptive and CBR-Controllable Semantic Cellular Communication Considering Imperfect CSI and Inter-Cell Co-Channel Interference": {
        "task_type": "图像传输、压缩或生成",
        "method_name": "SACC",
        "input_description": "图像及其视觉/任务语义",
        "output_description": "重建/生成图像或视觉任务输出",
    },
    "VQ-DeepVSC: A Dual-Stage Vector Quantization System for Video Semantic Communication": {
        "representation_summary": "第二阶段以语义 VQ 编码器把关键帧 latent 映射为共享码本 index；index 经数字链路发送，接收端查表并由空间归一化解码器恢复关键帧。",
    },
}


LAYER_ZH = {
    "security": ("通信安全与隐私", "把窃听、攻击或隐私泄露纳入语义链路，同时考察合法端质量与攻击端获得的信息。"),
    "digital": ("数字语义编码与物理层接口", "连接神经语义 bottleneck 与 bit、码本 index、有限星座、OFDM 或数据包。"),
    "generative": ("生成式语义信源编码", "利用接收端生成先验，把可预测细节从空口发送对象中移除。"),
    "multiuser": ("多用户接入、广播或中继", "研究多个用户共享频谱、干扰或中继时的语义相关性与异构信道。"),
    "resource": ("资源分配与跨层优化", "把语义/任务质量映射为网络效用，再分配功率、带宽、算力或时延。"),
    "task": ("任务导向联合信源信道设计", "只传下游任务需要的信息，并以任务质量而不是逐 bit 正确作为最终目标。"),
    "adaptive": ("自适应联合信源信道编码", "让表示维度、保护强度或接收策略随带宽和信道条件变化。"),
    "theory": ("语义信息理论与性能度量", "定义语义信息、失真、价值或可达边界，为系统比较提供共同坐标。"),
    "jscc": ("联合信源信道编码（JSCC）", "在同一系统中共同设计压缩、语义保真和抗信道噪声机制。"),
    "compression": ("数字视觉/特征压缩边界", "产生可存储或传输的数字码流，但无线信道通常未进入训练与实验。"),
}


@dataclass
class SentenceRef:
    page: int
    text: str


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def norm_doi(value: object) -> str:
    return str(value or "").strip().lower().replace("https://doi.org/", "")


def norm_space(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("–", "-").replace("−", "-")
    text = re.sub(r"(?<=\w)-\s+(?=[a-z])", "", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: str, limit: int = 100) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:limit].rstrip("-")


def paper_filename(value: object) -> str:
    text = str(value or "").replace("\\", "/")
    return text.rsplit("/", 1)[-1]


def split_values(value: object) -> list[str]:
    if isinstance(value, list):
        parts = [str(x) for x in value]
    else:
        parts = re.split(r"[、,;/；]", str(value or ""))
    result: list[str] = []
    for part in parts:
        item = norm_space(part).strip(".：:；; ")
        if item and item.lower() not in {x.lower() for x in result}:
            result.append(item)
    return result


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repair_headings(text: str) -> str:
    words = [
        "INTRODUCTION", "BACKGROUND", "RELATED WORK", "SYSTEM MODEL", "PROBLEM FORMULATION",
        "PROPOSED METHOD", "EXPERIMENTAL RESULTS", "SIMULATION RESULTS", "NUMERICAL RESULTS",
        "PERFORMANCE EVALUATION", "EXPERIMENTS", "RESULTS", "CONCLUSION", "CONCLUSIONS",
        "METHODOLOGY", "METHOD", "NETWORK ARCHITECTURE", "SYSTEM DESIGN",
    ]
    for word in words:
        pattern = r"\b" + r"\s*".join(map(re.escape, word)) + r"\b"
        text = re.sub(pattern, word, text, flags=re.I)
    return text


def clean_page(text: str) -> str:
    lines = []
    for raw in text.replace("\r", "").splitlines():
        line = norm_space(raw)
        if not line or POLLUTION.search(line):
            continue
        if re.fullmatch(r"\d{3,5}", line):
            continue
        if re.fullmatch(r"[A-Z][A-Z .:,'’&-]{12,}\d*", line) and "RESULT" not in line and "CONCLUSION" not in line:
            continue
        lines.append(line)
    joined = "\n".join(lines)
    joined = re.sub(r"(?<=\w)-\n(?=[a-z])", "", joined)
    joined = repair_headings(joined)
    return re.sub(r"\s+", " ", joined).strip()


def extract_pages(pdf: Path, pdftotext: str) -> list[str]:
    proc = subprocess.run(
        [pdftotext, "-enc", "UTF-8", str(pdf), "-"],
        check=True,
        capture_output=True,
    )
    text = proc.stdout.decode("utf-8", errors="replace")
    return [clean_page(page) for page in text.split("\f") if page.strip()]


def sentence_refs(pages: list[str]) -> list[SentenceRef]:
    refs: list[SentenceRef] = []
    for page, text in enumerate(pages, start=1):
        text = re.sub(r"\b([A-Z])\.\s+(?=[A-Z])", r"\1. ", text)
        chunks = re.split(r"(?<=[.!?])\s+(?=(?:[A-Z0-9(•]|[IVX]+\.\s))", text)
        for chunk in chunks:
            item = norm_space(chunk).strip("• ")
            if 38 <= len(item) <= 900 and not POLLUTION.search(item):
                refs.append(SentenceRef(page, item))
    return refs


def find_page(pages: list[str], pattern: str, start: int = 0) -> int | None:
    rx = re.compile(pattern, re.I)
    for idx in range(start, len(pages)):
        if rx.search(pages[idx]):
            return idx
    return None


def section_pools(pages: list[str], refs: list[SentenceRef]) -> dict[str, list[SentenceRef]]:
    intro_idx = find_page(pages, r"\bI\.\s+INTRODUCTION\b|\b1\.\s+INTRODUCTION\b")
    intro_idx = 0 if intro_idx is None else intro_idx
    method_idx = find_page(
        pages,
        r"\b(?:III|IV|II)\.\s+(?:SYSTEM MODEL|PROPOSED|METHOD|METHODOLOGY|SYSTEM DESIGN|NETWORK ARCHITECTURE|PROBLEM FORMULATION)",
        intro_idx,
    )
    if method_idx is None:
        method_idx = min(intro_idx + 1, max(0, len(pages) - 1))
    exp_idx = find_page(
        pages,
        r"\b(?:III|IV|V|VI|VII)\.\s+(?:EXPERIMENT|SIMULATION|NUMERICAL|PERFORMANCE|RESULT)",
        method_idx,
    )
    if exp_idx is None:
        exp_idx = max(method_idx, int(len(pages) * 0.58))
    conclusion_idx = find_page(pages, r"\b(?:CONCLUSION|CONCLUSIONS)\b", exp_idx)
    if conclusion_idx is None:
        conclusion_idx = max(exp_idx, len(pages) - 2)
    references_idx = find_page(
        pages,
        r"(?:^|\s)(?:REFERENCES|R\s*E\s*F\s*E\s*R\s*E\s*N\s*C\s*E\s*S)(?:\s|$)",
        conclusion_idx,
    )
    if references_idx is None:
        references_idx = len(pages)

    def between(lo: int, hi: int) -> list[SentenceRef]:
        return [r for r in refs if lo + 1 <= r.page <= hi + 1]

    return {
        "intro": between(intro_idx, max(intro_idx, method_idx - 1)),
        "method": between(method_idx, max(method_idx, exp_idx - 1)),
        # Stop before the bibliography.  Letting the experiment pool run to
        # EOF caused cited datasets/models (for example BERT or CLIP) to be
        # reported as baselines of the paper under review.
        "experiment": between(max(method_idx, exp_idx - 1), max(exp_idx, references_idx - 1)),
        "conclusion": between(conclusion_idx, max(conclusion_idx, references_idx - 1)),
        "all": refs,
        "indices": [intro_idx + 1, method_idx + 1, exp_idx + 1, conclusion_idx + 1],
    }


def good_narrative(ref: SentenceRef) -> bool:
    text = ref.text
    if NARRATIVE_BANNED.search(text) or DISPLAY_BANNED.search(text) or len(text) < 45 or len(text) > 460:
        return False
    if any(ord(ch) < 32 for ch in text):
        return False
    # Reject equation/list fragments.  A display sentence may mention one
    # variable, but multiple equality signs, TeX delimiters, set-membership
    # symbols, or a leading enumerator are strong extraction-contamination
    # signals on two-column IEEE PDFs.
    if text.count("=") > 1 or re.search(r"[$\\{}|]|[∈∑≈≤≥]|^\s*\(?\d{1,2}\)?\s*[:.)]", text):
        return False
    if text.count("=") and len(text) > 200:
        return False
    if re.search(
        r"^\s*\d{1,2}\s+[A-Za-z]|"
        r"(?:^|[.!?;]\s+)\d{1,2}\s*(?:\([a-z]\)|[a-z])?\s*[,.:]|"
        r"\b(?:shown|plotted|reported|illustrated|depicted|observed)\s+in\s+\d{1,2}\b|"
        r"\b(?:det|ln|log|exp|Pr|p|q|w)\s*\([^)]{1,80}\)\s*(?:=|\||,)" ,
        text,
        re.I,
    ):
        return False
    if text.count(";") > 4 or text.count("[") or text.count("]"):
        return False
    if re.match(r"^[A-Z][A-Z-]+\s+et al\.", text, re.I) or re.search(r"IEEE\s+Trans\.|\bProc\.", text, re.I):
        return False
    if re.search(r"\b(?:University|Laboratory|Foundation|Grant No\.)\b", text, re.I):
        return False
    return True


def choose_ref(pool: Iterable[SentenceRef], patterns: Iterable[str]) -> SentenceRef | None:
    refs = [r for r in pool if good_narrative(r)]
    compiled = [re.compile(p, re.I) for p in patterns]
    for rx in compiled:
        matches = [r for r in refs if rx.search(r.text)]
        if matches:
            return matches[0]
    return None


def choose_method_ref(pool: Iterable[SentenceRef], patterns: Iterable[str]) -> SentenceRef | None:
    result_like = re.compile(r"outperform|results? (?:show|demonstrate)|achiev|gain|higher than|lower than|we observe", re.I)
    refs = [r for r in pool if good_narrative(r) and not result_like.search(r.text)]
    return choose_ref(refs, patterns)


def choose_mechanism_ref(pool: Iterable[SentenceRef], patterns: Iterable[str]) -> SentenceRef | None:
    problem_like = re.compile(r"\bhowever\b|limitation|incompatible|barrier|challenge|fails? to|cannot|lack of", re.I)
    result_like = re.compile(r"outperform|results? (?:show|demonstrate)|achiev|gain|higher than|lower than|improv|increase|decrease|reduc|compared (?:with|to)|\d+(?:\.\d+)?\s*dB", re.I)
    refs = [r for r in pool if good_narrative(r) and not problem_like.search(r.text) and not result_like.search(r.text)]
    return choose_ref(refs, patterns)


def choose_own_method_ref(pool: Iterable[SentenceRef], method_label: str) -> SentenceRef | None:
    """Choose an author-method sentence, excluding cited prior work/results."""
    third_party = re.compile(
        r"\b(?:authors? in|literature|previous (?:work|study)|existing (?:work|method)|another (?:work|study)|"
        r"recent (?:work|study)|proposed by)\b|\b(?:in|from)\s*\[[0-9]{1,3}\]",
        re.I,
    )
    result_like = re.compile(r"outperform|results? (?:show|demonstrate)|achiev|gain|improv|higher than|lower than|\d+(?:\.\d+)?\s*dB", re.I)
    own_cue = re.compile(
        r"\b(?:we|our|this (?:paper|work)|the proposed)\b.{0,240}(?:propose|design|develop|formulat|framework|system|method|scheme|encoder|decoder|quantiz|map|optimiz|decompos)",
        re.I,
    )
    label_rx = re.compile(rf"\b{re.escape(method_label)}\b", re.I) if len(method_label) <= 48 else None
    for ref in pool:
        if not good_narrative(ref) or third_party.search(ref.text) or result_like.search(ref.text):
            continue
        if own_cue.search(ref.text):
            return ref
        if label_rx and label_rx.search(ref.text) and re.search(r"consists|comprises|uses|maps|encodes|decodes|optimizes|architecture|framework", ref.text, re.I):
            return ref
    return None


def choose_many(pool: Iterable[SentenceRef], pattern: str, limit: int = 2) -> list[SentenceRef]:
    rx = re.compile(pattern, re.I)
    result: list[SentenceRef] = []
    for ref in pool:
        if good_narrative(ref) and rx.search(ref.text):
            if all(ref.text.lower() != old.text.lower() for old in result):
                result.append(ref)
        if len(result) >= limit:
            break
    return result


def abstract_refs(record: dict) -> list[SentenceRef]:
    text = norm_space(record.get("abstract", ""))
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [SentenceRef(1, p) for p in parts if 35 <= len(p) <= 800]


def abstract_from_pdf(pages: list[str]) -> str:
    if not pages:
        return ""
    first = pages[0]
    match = re.search(
        r"\bAbstract\s*[-—:]?\s*(.+?)(?=\bIndex Terms\b|\bI\.\s+INTRODUCTION\b|\b1\.\s+INTRODUCTION\b)",
        first,
        re.I,
    )
    return norm_space(match.group(1)) if match else ""


def infer_task(title: str, abstract: str) -> tuple[str, str, str]:
    low_title = title.lower()
    low = f"{title} {abstract}".lower()

    def contains(text: str, keyword: str) -> bool:
        # Substring matching made "text" match "context" and "face" match
        # "interface", which mislabeled several image/resource papers.
        if re.fullmatch(r"[a-z0-9 -]+", keyword):
            return bool(re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text))
        return keyword in text

    for words, label, inp, out in TASK_RULES:
        if any(contains(low_title, w) for w in words):
            return label, inp, out
    for words, label, inp, out in TASK_RULES:
        if any(contains(low, w) for w in words):
            return label, inp, out
    return "通用语义通信系统", "信源数据和接收端任务", "重建内容或任务输出"


def infer_theme(title: str, abstract: str, journal_key: str) -> str:
    low_title = title.lower()
    low = f"{title} {abstract}".lower()
    if journal_key == "tcsvt" and "compression" in low_title and not re.search(r"transmission|semantic communication|joint source.channel|jscc|loss-resilient", low_title):
        return "compression"
    for theme, words in THEME_RULES:
        if any(w in low_title for w in words):
            return theme
    if journal_key == "tcsvt" and not re.search(r"wireless|channel|joint source.channel|semantic communication|transmission", low):
        return "compression"
    for theme, words in THEME_RULES:
        if any(w in low for w in words):
            return theme
    return "jscc"


def own_evidence_text(abstract: str, method_refs: list[SentenceRef]) -> str:
    method = " ".join(
        r.text for r in method_refs[:24]
        if not re.search(r"\bet al\.\b", r.text, re.I)
        and re.search(r"\b(?:we|our|this (?:paper|work|system)|proposed)\b", r.text, re.I)
    )
    return f"{abstract} {method}".lower()


def infer_interfaces(title: str, abstract: str, theme: str, method_refs: list[SentenceRef]) -> tuple[str, str, str, str, bool]:
    own = own_evidence_text(abstract, method_refs)
    title_abs = f"{title} {abstract}".lower()
    explicit_error = bool(re.search(r"bit (?:error|flip)|index error|packet loss|erasure|loss-resilient|corrupt|binary symmetric", own))
    digital = bool(re.search(r"vector quant|vq-|codebook|quantized index|bit-level|digital semantic|bitstream|discrete token|visual token|token modeling|binary semantic|constellation", title_abs))
    entropy_bitstream = bool(re.search(r"entropy cod|arithmetic cod|digital bitstream|bitstream", own))
    # OFDM/OTFS can carry continuous learned channel symbols.  They are not,
    # by themselves, evidence of a finite digital payload interface.
    finite_phy = bool(re.search(r"\b(?:qam|psk|constellation|modulat|harq|ldpc|polar code)\b", title_abs))
    continuous = bool(re.search(r"deepjscc|joint source.channel|joint semantic.channel|semantic.channel encoder|channel symbol|analog semantic|uncoded|softcast|awgn layer|end-to-end semantic communication", title_abs))
    compression = theme == "compression" or ("compression" in title_abs and not re.search(r"wireless|channel|jscc", title_abs))

    if theme in {"resource", "theory"}:
        representation = "上层理论/资源变量；论文不单独定义可发送语义格式"
        channel_class = "类别 5：沿用底层链路或抽象速率—效用模型"
        transmitted = "系统模型定义的语义速率、任务效用或信道资源变量"
        decoder = "系统公式假设的接收端输出或语义质量曲线"
        strict_digital = False
    elif re.search(r"hybrid digital.analog|digital.analog", title_abs):
        representation = "混合数字—模拟语义表示"
        channel_class = "类别 5：数字 bitstream 与连续模拟语义分支并行传输"
        transmitted = "量化/熵编码的数字分支，以及连续语义特征分支"
        decoder = "信道译码后的数字信息与带噪连续特征，随后进行融合恢复"
        strict_digital = True
    elif digital:
        representation = "显式数字语义表示：bit、离散 token 或码本 index"
        if explicit_error:
            channel_class = "类别 4：离散 bit/index/packet error 被显式建模或联合训练"
            decoder = "可能出错或缺失的离散 bit/token/index（或其 soft estimate）"
        elif finite_phy:
            channel_class = "类别 2：数字语义变量接入调制、信道编码或 OFDM 链路"
            decoder = "解调/信道译码后的 bit 或 index；残余错误是否进入语义 decoder 需单独判断"
        else:
            channel_class = "类别 1：形成数字表示，但物理链路按可靠 bitstream 抽象"
            decoder = "默认无误恢复的 bitstream、token 或 index"
        transmitted = "量化 bit、离散 token 或码本 index"
        strict_digital = True
    elif "harq" in title_abs and "semantic" in title_abs:
        representation = "语义特征包/调制符号与 HARQ 冗余版本"
        channel_class = "类别 5：语义感知 HARQ/重传与任务判据耦合"
        transmitted = "初传语义特征及按语义校验触发的增量冗余/重传包"
        decoder = "初传或 HARQ 重传合并后的语义特征"
        strict_digital = True
    elif finite_phy:
        representation = "有限星座/标准数字波形接口"
        channel_class = "类别 2：语义特征映射为调制符号或编码包"
        transmitted = "有限星座符号、OFDM/OTFS 资源或受保护数据包"
        decoder = "均衡或 soft demodulation 后的符号，再恢复语义表示"
        strict_digital = True
    elif continuous:
        representation = "连续神经 JSCC latent / 实复信道符号"
        channel_class = "类别 3：连续语义变量直接经过有噪声信道并端到端恢复"
        transmitted = "功率归一化的实数或复数神经信道符号"
        decoder = "AWGN/衰落作用后的带噪连续符号"
        strict_digital = False
    elif compression or entropy_bitstream:
        representation = "数字压缩 bitstream 或量化 feature；无线接口未纳入研究"
        channel_class = "类别 1：数字压缩后默认可靠传输/存储"
        transmitted = "熵编码 bitstream、分层码流或压缩 feature"
        decoder = "无误码 bitstream 解码后的 latent/图像/特征"
        strict_digital = True
    else:
        representation = "语义 feature/latent；量化到 bitstream 的接口未完整报告"
        channel_class = "类别 0：信道作用点不足，或由外部传统链路抽象承担"
        transmitted = "语义 feature 或未完整规定 bit 映射的 latent"
        decoder = "论文假设已经恢复的语义特征"
        strict_digital = False
    return representation, channel_class, transmitted, decoder, strict_digital


def term_present(term: str, text: str, case_sensitive: bool = False) -> bool:
    if case_sensitive:
        if len(term) <= 5 and term.isupper():
            return bool(re.search(rf"\b{re.escape(term)}\b", text))
        return term in text
    low = text.lower()
    needle = term.lower()
    if len(needle) <= 3 and needle.isalpha():
        return bool(re.search(rf"\b{re.escape(needle)}\b", low))
    return needle in low


def filtered_terms(candidates: Iterable[str], known: Iterable[str], text: str, limit: int, kind: str = "") -> list[str]:
    merged = list(candidates) + list(known)
    result: list[str] = []
    for term in merged:
        item = norm_space(term)
        if not item or len(item) > 60 or item.lower() in {x.lower() for x in result}:
            continue
        if item.lower() in {"bandwidth", "snr", "fading", "bit error", "energy"}:
            continue
        if term_present(item, text, case_sensitive=(kind == "dataset")):
            result.append(item)
        if len(result) >= limit:
            break
    return result


def extract_values(text: str, pattern: str, limit: int = 10) -> list[str]:
    result: list[str] = []
    for match in re.finditer(pattern, text, re.I):
        value = norm_space(match.group(0))
        if value.lower() not in {x.lower() for x in result}:
            result.append(value)
        if len(result) >= limit:
            break
    return result


def method_name(title: str, abstract: str) -> str:
    if ":" in title:
        prefix = title.split(":", 1)[0].strip()
        if len(prefix) <= 36:
            return prefix
    acronyms = list(re.finditer(r"\(([A-Z][A-Za-z0-9-]{2,20})\)", abstract))
    bad = {
        "AI", "DL", "DNN", "CNN", "RNN", "VAE", "GAN", "SNR", "AWGN", "MIMO",
        "OFDM", "OTFS", "BER", "SER", "PER", "PSNR", "SSIM", "JSCC", "DJSCC",
        "SSCC", "LLM", "KKT", "IRS", "RIS", "ISAC", "MEC", "IOT", "UAV", "NOMA",
        "RSMA", "MAC", "SIC", "PLC", "VCM", "ROI", "CSI", "FEC", "HARQ", "V2X",
        "CPS", "NTN", "AAV", "GAI", "BS", "UE", "SINR", "CBR",
    }
    ranked = []
    for match in acronyms:
        acronym = match.group(1)
        if acronym.upper().rstrip("S") in bad:
            continue
        context = abstract[max(0, match.start() - 150):match.start()].lower()
        score = 3 if re.search(r"propos|introduc|develop|design|called|named", context) else 0
        ranked.append((score, -match.start(), acronym))
    if ranked:
        return max(ranked)[2]
    named = re.search(r"\b(?:called|named|termed|denoted as)\s+(?:the\s+)?([A-Z][A-Za-z0-9-]{2,24})", abstract, re.I)
    if named and named.group(1).upper().rstrip("S") not in bad:
        return named.group(1)
    brand_tokens = re.findall(r"\b[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9-]{1,24}\b|\b[A-Z]{2,}[A-Za-z0-9-]{1,24}\b", title)
    for token in brand_tokens:
        if token.upper().rstrip("S") not in bad:
            return token
    # Some papers deliberately do not coin an acronym.  Keeping the full
    # title is more informative and less misleading than inventing a name.
    return title


def refs_to_field(refs: list[SentenceRef], join: str = " ") -> dict:
    return {"en": join.join(r.text for r in refs), "pages": sorted({r.page for r in refs})[:4]}


def fallback_field(text: str, pages: Iterable[int]) -> dict:
    return {"zh": text, "pages": sorted(set(int(p) for p in pages if p))[:4]}


def build_raw_record(record: dict, old: dict, evidence: dict, pages: list[str], journal_key: str) -> tuple[dict, dict]:
    refs = sentence_refs(pages)
    pools = section_pools(pages, refs)
    title = norm_space(record.get("title"))
    abstract = norm_space(record.get("abstract"))
    if len(abstract) < 60:
        abstract = abstract_from_pdf(pages)
    abstract_record = dict(record)
    abstract_record["abstract"] = abstract
    abs_refs = abstract_refs(abstract_record)
    task, input_desc, output_desc = infer_task(title, abstract)
    theme = infer_theme(title, abstract, journal_key)
    is_survey = bool(
        re.search(r"survey|state-of-the-art|future directions|architecture, technologies, and applications", title, re.I)
        or re.search(r"\b(?:this (?:paper|article) (?:surveys|reviews)|comprehensive survey|systematic review)\b", abstract, re.I)
    )
    if is_survey:
        task, input_desc, output_desc = (
            "综述、架构与研究路线",
            "已有语义通信系统、模型和网络机制",
            "分类体系、架构总结与研究方向",
        )
        theme = "theory"
    representation, channel_class, transmitted, decoder, strict_digital = infer_interfaces(
        title, abstract, theme, pools["method"]
    )
    method_label = method_name(title, abstract)

    progress = choose_method_ref(
        abs_refs + pools["intro"],
        (r"recent (?:advances|years|work)|has (?:shown|demonstrated|achieved)|have (?:shown|demonstrated|achieved)|benefiting from|enabled",),
    ) or (abs_refs[0] if abs_refs else SentenceRef(1, title))
    problem = choose_ref(
        abs_refs + pools["intro"],
        (r"\bhowever\b", r"challenge|limitation|bottleneck|difficult|fail|cannot|lack|suffer|incompatible|typically require|remain (?:incompatible|limited|unclear)"),
    ) or next((r for r in abs_refs[1:] + pools["intro"] if r.text != progress.text and good_narrative(r)), progress)
    proposal = choose_ref(
        abs_refs + pools["intro"],
        (r"to (?:this|that) end", r"(?:we|this paper|this work) (?:propose|present|develop|design|introduce|study)", r"our .* method"),
    ) or (abs_refs[min(1, len(abs_refs) - 1)] if abs_refs else progress)
    mechanism_patterns = (
        r"specifically|the idea (?:of|behind)|achieves? .* through|enables? .* by|we (?:design|incorporate)|during (?:the )?training|consists? of|comprises?|by (?:using|leveraging|jointly|integrating|introducing)|(?:features|information) are (?:extracted|encoded|mapped)|converts?|maps? .* (?:bit|symbol|feature)|decompos|formulat|optimization algorithm|framework includes",
        r"we design",
    )
    mechanism = choose_mechanism_ref(abs_refs, mechanism_patterns)
    if not mechanism:
        mechanism = choose_mechanism_ref(
            pools["method"],
            (
                r"\b(?:we|our|this (?:paper|work)|the proposed)\b.{0,220}(?:design|framework|system|method|scheme|encoder|decoder|quantiz|map|optimiz|decompos)",
                rf"\b{re.escape(method_label)}\b.{0,220}(?:consists|comprises|uses|maps|encodes|decodes|optimizes)",
            ),
        )
    mechanism = mechanism or proposal
    claim = choose_ref(
        list(reversed(abs_refs)) + pools["conclusion"] + pools["experiment"],
        (r"results? (?:show|demonstrate|indicate)|outperform|achieves?|improves?|reduces?|gain|verify",),
    ) or (abs_refs[-1] if abs_refs else proposal)

    method_more = choose_own_method_ref(pools["method"], method_label)
    # The abstract's proposal/mechanism is the clean rhetorical anchor.  A
    # body-method sentence is appended only after it passes the stricter
    # author-method gate above.  This keeps paper-specific detail without
    # exposing a raw PDF excerpt or a cited third-party method.
    method_refs: list[SentenceRef] = []
    for candidate in (proposal, mechanism):
        if candidate and good_narrative(candidate) and all(candidate.text != old_ref.text for old_ref in method_refs):
            method_refs.append(candidate)
    if len(method_refs) < 2 and method_more and good_narrative(method_more):
        method_refs.append(method_more)

    digital_refs = choose_many(
        abs_refs + pools["method"] + pools["experiment"],
        r"vector quant|codebook|quantiz|bitstream|bits? per|discrete token|entropy cod|constellation|channel symbols?|latent representation|feature map",
        1,
    )
    rate_pattern = r"\bCBR\b|bandwidth ratio|compression ratio|bits? per (?:pixel|token|symbol|index)|\bbpp\b|channel uses?|bit rate|bitrate|codebook size|number of (?:tokens|indices|symbols)|input (?:size|dimension)|\d+\s*[×x]\s*\d+"
    overhead_refs = choose_many(
        pools["method"] + pools["experiment"],
        rf"(?:defined as|denotes?|is set to|is fixed at|we set|we use).{{0,180}}(?:{rate_pattern})|(?:{rate_pattern}).{{0,180}}(?:defined as|denotes?|is set to|is fixed at|we set|we use)",
        1,
    )
    channel_pattern = r"AWGN|Rayleigh|Rician|fading channel|binary symmetric|erasure channel|bit (?:error|flip)|index error|packet loss|LDPC|polar code|QAM|OFDM|HARQ|channel noise|channel output"
    channel_refs = choose_many(
        abs_refs + pools["experiment"],
        rf"(?:we (?:adopt|consider|model|use)|channel (?:is|follows)|transmit(?:ted)? (?:over|through)|under .* channel|modeled as).{{0,180}}(?:{channel_pattern})|(?:{channel_pattern}).{{0,180}}(?:we (?:adopt|consider|model|use)|channel (?:is|follows)|transmit(?:ted)? (?:over|through)|modeled as)",
        1,
    )
    title_abstract_low = f"{title} {abstract}".lower()
    if ("连续" in representation or "语义 feature" in representation or "上层理论" in representation) and not re.search(
        r"vector quant|vq-|codebook|digital semantic|bitstream|discrete token|visual token|quantiz", title_abstract_low
    ):
        digital_refs = []
    if "上层理论" in representation:
        overhead_refs = []
    result_extra = choose_ref(
        pools["experiment"] + pools["conclusion"],
        (r"outperform|improv|gain|achiev|save|higher .* (?:than|dB|%)|lower.*(?:dB|%)|reduce(?:s|d)? (?:bandwidth|latency|error|distortion|cost|overhead)", r"results? (?:show|demonstrate|indicate)"),
    )
    if result_extra and (len(result_extra.text) > 340 or not good_narrative(result_extra)):
        result_extra = None

    exp_text = " ".join(r.text for r in pools["experiment"])
    method_exp_text = abstract + " " + exp_text
    old_datasets = split_values(old.get("datasets")) + split_values(evidence.get("datasets"))
    old_baselines = split_values(old.get("baselines")) + split_values(evidence.get("baselines"))
    old_metrics = split_values(old.get("metrics")) + split_values(evidence.get("metrics"))
    old_channels = split_values(old.get("channels")) + split_values(evidence.get("channels"))
    datasets = filtered_terms(old_datasets, KNOWN_DATASETS, exp_text, 10, "dataset")
    baselines = filtered_terms(old_baselines, KNOWN_BASELINES, exp_text, 12, "baseline")
    metrics = filtered_terms(old_metrics, KNOWN_METRICS, exp_text, 10, "metric")
    channels = filtered_terms(old_channels, KNOWN_CHANNELS, method_exp_text, 8, "channel")
    snr = extract_values(
        exp_text,
        r"(?:SNR|signal-to-noise ratio)\s*(?:=|of|:|from|between)?\s*-?\d+(?:\.\d+)?\s*dB|(?:at|under)\s*-?\d+(?:\.\d+)?\s*dB\s*SNR",
        10,
    )
    ber = extract_values(exp_text, r"(?:BER|bit error rate)\s*(?:=|of|:)\s*10\s*[-^]?\s*\d+|(?:BER|bit error rate)\s*(?:=|of|:)\s*\d+(?:\.\d+)?%?", 6)
    cbr = extract_values(exp_text, r"(?:CBR|bandwidth ratio|compression ratio)\s*(?:=|of|:)\s*\d+(?:\.\d+)?(?:\s*/\s*\d+)?|\d+(?:\.\d+)?\s*bpp", 8)
    if task == "通用语义通信系统" and (
        any(x in datasets for x in ("Kodak", "ImageNet", "CIFAR-10", "CIFAR-100", "CLIC", "DIV2K"))
        or any(x in metrics for x in ("PSNR", "SSIM", "MS-SSIM", "LPIPS"))
    ):
        task, input_desc, output_desc = "图像传输、压缩或生成", "图像及其视觉/任务语义", "重建/生成图像或视觉任务输出"

    tier = str(record.get("screening_status") or old.get("screening_status") or "core").lower()
    if tier not in {"core", "related"}:
        tier = "core"
    if is_survey:
        tier = "related"
        datasets, baselines, metrics, snr, ber, cbr = [], [], [], [], [], []
    layer, layer_explanation = LAYER_ZH[theme]
    importance = IMPORTANCE_ZH.get(task, "语义质量必须在真实的带宽、功率和时延预算下成立，否则模型收益不能转化为通信系统收益。")
    prior_limit = PRIOR_LIMIT_ZH[theme]

    if digital_refs:
        representation_field = refs_to_field(digital_refs)
    else:
        representation_field = fallback_field(
            f"全文没有给出可复核的 VQ/codebook/index-to-bit 接口。根据系统模型，本调研将传输表示判断为“{representation}”；不能把网络 latent 的每个浮点维度直接当成固定 bit。",
            [pools["indices"][1]],
        )
    if overhead_refs:
        overhead_field = refs_to_field(overhead_refs)
    elif "上层理论" in representation:
        overhead_field = fallback_field(
            "论文优化的是功率、带宽、时隙、用户调度或语义效用等上层资源变量，并未定义一条可逐 bit 复现的语义 codec。因而这里只报告系统约束和效用曲线，不能从优化变量反推 token/index 总 bit 数。",
            [pools["indices"][1], pools["indices"][2]],
        )
    else:
        overhead_field = fallback_field(
            "论文未同时报告输入尺寸、encoder 输出尺寸、量化精度/码本大小和帧级开销，因此不能从全文唯一重建总 bit 数。页面保留论文实际使用的 CBR、bpp、token 数或信道使用次数；缺失项不作臆测。",
            [pools["indices"][1], pools["indices"][2]],
        )
    if channel_refs:
        channel_field = refs_to_field(channel_refs)
    else:
        channel_field = fallback_field(
            f"正文未给出可单句摘录的更细信道流程；结合题名、摘要、方法与实验，本调研按“{channel_class}”解释信道作用点。",
            [pools["indices"][1], pools["indices"][2]],
        )

    authors = record.get("authors", [])
    if isinstance(authors, list):
        authors_text = "; ".join(map(str, authors))
    else:
        authors_text = str(authors or "")
    pdf_name = paper_filename(record.get("pdf_path") or old.get("pdf_name"))
    local_pdf = f"papers/{pdf_name}" if pdf_name else ""
    doi = norm_doi(record.get("doi"))
    source_url = f"https://doi.org/{doi}" if doi else record.get("ieee_document_url") or record.get("publisher_url") or "#"
    strict = "是：存在明确的离散/有限数字接口" if strict_digital else "否/不适用：主接口为连续 JSCC 或上层模型"

    # The abstract/conclusion claim is the presentation-layer result.  Body
    # result sentences often begin with a figure number after extraction
    # ("6(a), ...") and become visibly spliced after translation.  They stay
    # available through the result figure and audit pages, not inline prose.
    result_refs = [claim]

    raw = {
        "doi": doi,
        "title": title,
        "authors": authors_text,
        "year": int(record.get("year") or old.get("year") or 0),
        "venue": norm_space(record.get("venue") or old.get("venue")),
        "volume": str(record.get("volume") or old.get("volume") or ""),
        "issue": str(record.get("issue") or old.get("issue") or ""),
        "pages": str(record.get("pages") or old.get("pages") or ""),
        "ieee_document_id": str(record.get("ieee_document_id") or old.get("ieee_document_id") or ""),
        "source_url": source_url,
        "pdf": local_pdf,
        "tier": tier,
        "screening_reason": norm_space(record.get("screening_reason") or old.get("screening_reason")),
        "task_type": task,
        "theme": theme,
        "method_name": method_label,
        "communication_layer": layer,
        "layer_explanation": layer_explanation,
        "digitalization_class": representation,
        "channel_handling_class": channel_class,
        "strict_digital": strict,
        "transmitted_object": transmitted,
        "decoder_object": decoder,
        "datasets": datasets,
        "baselines": baselines,
        "metrics": metrics,
        "channels": channels,
        "snr_conditions": snr,
        "ber_conditions": ber,
        "rate_conditions": cbr,
        "input_description": input_desc,
        "output_description": output_desc,
        "motivation": {
            "progress": refs_to_field([progress]),
            "problem": refs_to_field([problem]),
            "prior_limit": fallback_field(prior_limit, [problem.page]),
            "importance": fallback_field(importance, [progress.page, problem.page]),
            "proposal": refs_to_field([proposal]),
            "mechanism": refs_to_field([mechanism]),
            "claim": refs_to_field([claim]),
        },
        "method_summary": refs_to_field(method_refs),
        "representation_summary": representation_field,
        "overhead_summary": overhead_field,
        "channel_summary": channel_field,
        "experiment_result_summary": refs_to_field(result_refs),
        "evidence_indices": pools["indices"],
        "is_survey": is_survey,
    }
    if raw["motivation"]["problem"].get("en") == raw["motivation"]["progress"].get("en"):
        raw["motivation"]["problem"] = fallback_field(
            f"在本文设定中，现有方法不能同时满足“{task}”的语义目标与通信、计算或资源约束；后续方案需要补齐这一具体瓶颈。",
            raw["motivation"]["problem"].get("pages", []),
        )

    # TCSVT's previous analysis layer contains 26 manually curated Chinese
    # records.  Preserve those paper-specific technical facts while replacing
    # the old page structure and revalidating every field against the reread
    # PDF.  TCCN also has useful concise method/interface judgments, but its
    # old extracted Introduction/result prose is deliberately not reused.
    if journal_key == "tcsvt":
        intro = old.get("intro") or []
        if len(intro) >= 6:
            mapping = {"progress": 0, "problem": 1, "importance": 2, "proposal": 3, "mechanism": 4, "claim": 5}
            for name, idx in mapping.items():
                raw["motivation"][name] = fallback_field(norm_space(intro[idx]), raw["motivation"][name].get("pages", []))
        for target, source_name in (
            ("method_summary", "method"), ("representation_summary", "representation"),
            ("overhead_summary", "overhead"), ("channel_summary", "channel"),
            ("experiment_result_summary", "results"),
        ):
            if old.get(source_name):
                raw[target] = fallback_field(norm_space(old[source_name]), raw[target].get("pages", []))
        raw["task_type"] = norm_space(old.get("task")) or raw["task_type"]
        raw["strict_digital"] = norm_space(old.get("strict")) or raw["strict_digital"]
        raw["curated_decoder"] = norm_space(old.get("decoder"))
        raw["curated_error"] = norm_space(old.get("error"))
        raw["curated_limitation"] = norm_space(old.get("limitation"))
        raw["curated_formula"] = norm_space(old.get("formula"))
        raw["datasets"] = [x for x in split_values(old.get("datasets")) if not re.search(r"输入|分辨率|尺寸|input|resolution", x, re.I)][:10]
        raw["baselines"] = split_values(old.get("baselines"))[:12]
        raw["metrics"] = split_values(old.get("metrics"))[:10]
        if not re.search(r"AWGN|Rayleigh|Rician|SNR", norm_space(old.get("channel")), re.I):
            raw["snr_conditions"] = []
    elif journal_key == "tccn":
        for target, source_name in (("method_summary", "method"), ("representation_summary", "representation")):
            value = norm_space(old.get(source_name))
            if value and "PDF p." not in value and len(value) < 1200:
                raw[target] = fallback_field(value, raw[target].get("pages", []))
        raw["curated_decoder"] = norm_space(old.get("decoder"))
        raw["curated_error"] = norm_space(old.get("error"))
        raw["curated_limitation"] = norm_space(old.get("limitation"))
        raw["curated_formula"] = norm_space(old.get("formula"))

    # A small set of manually reviewed records already contains an explicit
    # paper-specific verdict that corrupted bits/indices/packets reach the
    # learned recovery path.  Let that stronger full-text judgment upgrade a
    # generic category-1/2 result instead of discarding it.
    curated_error = raw.get("curated_error", "")
    if (
        "显式数字语义表示" in raw["digitalization_class"]
        and re.search(r"^(?:是|明确解决)|bit flip|有误码|丢包恢复|packet loss", curated_error, re.I)
    ):
        raw["channel_handling_class"] = "类别 4：离散 bit/index/packet error 被显式建模或联合训练"
        if raw["channel_summary"].get("zh", "").startswith("正文未给出可单句摘录"):
            raw["channel_summary"]["zh"] = "全文复核显示，离散 bit/index/packet error 进入作者的信道、训练或恢复流程。"

    audit = {
        "doi": doi,
        "title": title,
        "pdf": local_pdf,
        "pdf_exists": True,
        "pdf_sha256": sha256(ROOT / "literature" / JOURNALS[journal_key]["directory"] / local_pdf),
        "manifest_sha256": record.get("sha256", ""),
        "page_count_extracted": len(pages),
        "characters_reflowed": sum(map(len, pages)),
        "section_pages": {
            "introduction": pools["indices"][0],
            "method": pools["indices"][1],
            "experiment": pools["indices"][2],
            "conclusion": pools["indices"][3],
        },
        "selected_pages": sorted({
            progress.page, problem.page, proposal.page, mechanism.page, claim.page,
            *[r.page for r in digital_refs + overhead_refs + channel_refs + result_refs],
        }),
        "column_order": "pdftotext default reading order (not -layout)",
        "analysis_version": ANALYSIS_VERSION,
    }
    return raw, audit


class CachedTranslator:
    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
        self.backend = TencentTranslator()

    def translate_records(self, records: list[dict]) -> None:
        pending: list[str] = []
        for record in records:
            for field in iter_translatable_fields(record):
                text = field.get("en", "")
                if text and text not in self.cache and text not in pending:
                    pending.append(text)
        total = len(pending)
        done = 0
        while pending:
            batch: list[str] = []
            chars = 0
            # TranSmart rejects a block above 6000 characters.  Keep a safety
            # margin because its server-side count includes JSON-normalized
            # text and separators in addition to our visible source strings.
            while pending and len(batch) < 12 and chars + len(pending[0]) < 5000:
                item = pending.pop(0)
                batch.append(item)
                chars += len(item)
            translated = self.backend.translate_batch(batch)
            for source, target in zip(batch, translated):
                self.cache[source] = journal_polish(target)
            done += len(batch)
            print(f"translated {done}/{total}")
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(0.2)
        for record in records:
            for field in iter_translatable_fields(record):
                if field.get("en"):
                    field["zh"] = journal_polish(self.cache[field["en"]])
                    field.pop("en", None)


class TencentTranslator:
    """Small batch client for Tencent TranSmart's public browser endpoint.

    The request uses the same JSON interface as the public web translator and
    does not require an account, key, cookie, or browser profile.  ``curl`` is
    used because the bundled Python SSL stack can fail on some Windows hosts.
    """

    endpoint = "https://transmart.qq.com/api/imt"

    def translate_batch(self, texts: list[str]) -> list[str]:
        payload = {
            "header": {"fn": "auto_translation", "client_key": "browser-chrome"},
            "type": "plain",
            "model_category": "normal",
            "source": {"lang": "en", "text_list": texts},
            "target": {"lang": "zh"},
        }
        data = None
        last_error: Exception | None = None
        for attempt in range(10):
            try:
                proc = subprocess.run(
                    [
                        "curl.exe", "-L", "--max-time", "60", "-sS",
                        "-H", "Content-Type: application/json",
                        "-H", "User-Agent: Mozilla/5.0",
                        "--data-binary", "@-", self.endpoint,
                    ],
                    input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    capture_output=True,
                    check=True,
                )
                data = json.loads(proc.stdout.decode("utf-8"))
                if data.get("header", {}).get("ret_code") == "succ":
                    break
                last_error = RuntimeError(f"TranSmart error: {data}")
            except Exception as exc:
                last_error = exc
            time.sleep(min(2 * (attempt + 1), 12))
        else:
            raise last_error or RuntimeError("TranSmart failed without response")
        translated = data.get("auto_translation") or []
        if len(translated) != len(texts):
            raise RuntimeError(f"TranSmart returned {len(translated)} items for {len(texts)} inputs")
        return translated


def journal_polish(text: str) -> str:
    text = polish_zh(text)
    replacements = {
        "平原图像": "原始图像",
        "普通图像的视觉结构": "原始图像的视觉结构",
        "通道噪声": "信道噪声",
        "通道条件": "信道条件",
        "通道输出": "信道输出",
        "通道估计": "信道估计",
        "能够科普不同的信道环境": "能够适应不同的信道环境",
        "上级的性能": "更优的性能",
        "上级的": "更优的",
        "上级基线算法的性能": "优于基线算法的性能",
        "打击语义噪声": "对抗语义噪声",
        "强大的语义通信系统": "鲁棒的语义通信系统",
        "强大的数字语义通信框架": "鲁棒的数字语义通信框架",
        "国家的最先进的作品": "现有先进方法",
        "国家的最先进的": "现有先进的",
        "上级的传输效率": "更高的传输效率",
        "上级的生成能力": "更强的生成能力",
        "上级的语义可靠性": "更高的语义可靠性",
        "上级重建精度": "更高的重建精度",
        "上级的性能": "更优的性能",
        "上级性能": "更优的性能",
        "福尔斯": "仍然",
        "&amp;": "",
        "E2 E": "E2E",
        "6 G": "6G",
        "S2 TT": "S2TT",
        "S2 T": "S2T",
        "C C": "C&C",
        "edge servers. In本文中，语义感知的多任务卸载系统。": "边缘服务器。该系统联合考虑语义提取、任务卸载与资源分配。",
        "SC network. In本文中": "语义通信网络。本文",
        "三个关键techniques. In本文中": "三项关键技术。本文",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # ``polish_zh`` contains a legacy ``源信道`` replacement that also
    # matches the tail of an already-correct ``信源信道``.  Normalize after
    # every other replacement so repeated rebuilds are idempotent.
    text = re.sub(r"信+源信道", "信源信道", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\.(?=\s*[\u4e00-\u9fff])", "。", text)
    if text.endswith("."):
        text = text[:-1] + "。"
    return text


def apply_curated_presentation_overrides(record: dict) -> None:
    overrides = CURATED_PRESENTATION_OVERRIDES.get(record.get("title", ""), {})
    for path, text in overrides.items():
        if path.startswith("motivation."):
            key = path.split(".", 1)[1]
            field = record.get("motivation", {}).get(key)
        else:
            field = record.get(path)
        if isinstance(field, dict):
            field["zh"] = text
        elif path in record:
            record[path] = text


def polish_record_strings(value):
    """Apply terminology cleanup to every presentation-layer string.

    Translated prose is polished when it enters the cache, but curated fields
    and judgment text are appended later.  A final recursive pass keeps those
    paths under the same terminology gate.
    """
    if isinstance(value, dict):
        return {key: polish_record_strings(item) for key, item in value.items()}
    if isinstance(value, list):
        return [polish_record_strings(item) for item in value]
    if isinstance(value, str):
        return journal_polish(value)
    return value


def sanitize_method_prose(text: str) -> str:
    """Remove residual prior-work clauses from the author-method synthesis."""
    text = re.sub(r"^受文献\[[0-9]+\](?:和|、)\[[0-9]+\]的启发，", "", text)
    markers = ("在我们的先前工作[", "我们的先前工作[")
    cut = min((text.find(marker) for marker in markers if text.find(marker) >= 0), default=-1)
    if cut > 20:
        prefix = text[:cut]
        last_stop = max(prefix.rfind("。"), prefix.rfind("."))
        text = prefix[:last_stop + 1] if last_stop >= 20 else prefix
    return text.rstrip("；;，, ")


def iter_translatable_fields(record: dict) -> Iterable[dict]:
    for item in record.get("motivation", {}).values():
        if isinstance(item, dict):
            yield item
    for key in (
        "method_summary", "representation_summary", "overhead_summary", "channel_summary",
        "experiment_result_summary",
    ):
        item = record.get(key)
        if isinstance(item, dict):
            yield item


def append_judgments(record: dict) -> None:
    representation = record["digitalization_class"]
    channel_class = record["channel_handling_class"]
    method = record["method_name"]
    task = record["task_type"]
    theme = record["theme"]
    record["method_summary"]["zh"] = sanitize_method_prose(record["method_summary"].get("zh", ""))

    rep = record["representation_summary"]
    rep["zh"] = (
        f"{rep.get('zh','')} 独立判断：{method} 的主传输单位应归为“{representation}”。"
        "只有论文明确给出量化和映射时，才能把 token/index 数换算成总 bit；连续 channel symbol 只能按 channel uses/CBR 比较。"
    ).strip()

    rate = record["overhead_summary"]
    if record.get("curated_formula"):
        formula = record["curated_formula"]
        caveat = "该公式按论文定义复核；若未计入包头、FEC、重传或侧信息，仍不能直接当作真实空口总开销。"
    elif "连续" in representation:
        formula = r"\mathrm{CBR}=\frac{N_{\mathrm{complex\ channel\ uses}}}{N_{\mathrm{source\ samples}}}"
        caveat = "连续 latent 未规定每个符号的 bit-depth，不能无条件换算为 bit rate。"
    elif re.search(r"token|index|bit", representation, re.I):
        formula = r"B_{\mathrm{semantic}}=N_{\mathrm{token/index}}\left\lceil\log_2 K\right\rceil+B_{\mathrm{side/FEC}}"
        caveat = "若论文未给码本大小 K、token 数、熵码和 FEC/包头，则总 bit 数仍不可唯一确定。"
    elif "bitstream" in representation:
        formula = r"\mathrm{bpp}=\frac{B_{\mathrm{payload}}+B_{\mathrm{side}}}{H\times W}"
        caveat = "公开 bpp 若未包含包头、FEC 和重传，也不等于真实空口占用。"
    else:
        formula = r"R_{\mathrm{tx}}=\frac{\mathrm{transmitted\ resource}}{\mathrm{source\ size}}"
        caveat = "全文信息不足时只保留论文原指标，不把模型维度臆测成通信 bit。"
    rate["formula"] = formula
    rate["caveat"] = caveat

    channel = record["channel_summary"]
    channel["zh"] = f"{channel.get('zh','')} 本调研据此归为“{channel_class}”。".strip()
    if "类别 1" in channel_class and re.search(r"LDPC|Polar|QAM|OFDM|信道编码", channel.get("zh", ""), re.I):
        channel["zh"] += " 这些传统信道编码/调制条目若只属于 baseline，不改变所提语义接收机默认可靠输入的分类。"
    decoder_text = (record.get("curated_decoder") or record["decoder_object"]).rstrip("。；; ")
    record["decoder_input_summary"] = {
        "zh": f"语义 decoder 实际面对的是：{decoder_text}。",
        "pages": channel.get("pages", []),
    }
    if "类别 4" in channel_class or "HARQ/重传" in channel_class:
        error_judgment = "是。论文把离散错误/丢失放进训练或恢复流程，因而正面处理了数字变量受损后的语义恢复。"
    elif "数字 bitstream 与连续模拟" in channel_class:
        error_judgment = "部分。论文定义了数字与模拟并行接口，但是否把残余 bit/index 错误端到端传给语义 decoder，仍取决于具体信道译码假设。"
    elif "类别 2" in channel_class:
        error_judgment = "部分。论文有真实数字物理层接口，但若语义 decoder 只看到信道译码后的结果，残余 bit/index 跳变仍未必被端到端处理。"
    elif "类别 3" in channel_class:
        error_judgment = "不适用 VQ index 跳变。论文处理的是连续噪声/衰落；这不能自动证明量化和调制后的数字链路鲁棒性。"
    elif "类别 1" in channel_class:
        error_judgment = "否。论文默认数字码流可靠到达，未评估 bit flip、熵码失同步或 packet loss 对语义变量的影响。"
    else:
        error_judgment = "未正面处理。系统模型不足以追踪残余 bit/index/packet error 到最终语义质量。"
    curated_error = record.get("curated_error", "")
    if "类别 5" in channel_class and "HARQ/重传" not in channel_class and "数字 bitstream 与连续模拟" not in channel_class:
        curated_error = ""
    if (
        ("类别 4" in channel_class or "HARQ/重传" in channel_class)
        and curated_error
        and not re.search(r"^(?:是|明确解决)", curated_error)
    ):
        curated_error = ""
    record["discrete_error_judgment"] = curated_error or error_judgment

    setup_parts = []
    if record.get("is_survey"):
        setup_parts.append("该文属于综述/架构论文，不设置单一训练数据集、实验 baseline 或统一 SNR 工作点；页面中的技术名称按被综述对象处理，不冒充作者实验")
    elif record["datasets"]:
        setup_parts.append("数据集为" + "、".join(record["datasets"]))
    if not record.get("is_survey") and record["baselines"]:
        setup_parts.append("实验小节中明确出现的比较对象包括" + "、".join(record["baselines"]))
    if not record.get("is_survey") and record["metrics"]:
        setup_parts.append("指标包括" + "、".join(record["metrics"]))
    if not record.get("is_survey") and record["channels"]:
        setup_parts.append("信道/链路条件包括" + "、".join(record["channels"]))
    conditions = record["snr_conditions"] + record["ber_conditions"] + record["rate_conditions"]
    if not record.get("is_survey") and conditions:
        setup_parts.append("正文可定位的代表性工作点有" + "、".join(conditions))
    if not setup_parts:
        setup_parts.append("论文未在可稳定定位的实验段落中同时给出数据集、baseline、信道和资源工作点；应以对应结果图页为准")
    record["experiment_setup_summary"] = {
        "zh": "；".join(setup_parts) + "。",
        "pages": [record["evidence_indices"][2]],
    }

    layer = record["communication_layer"]
    if theme == "compression":
        reviewer = "价值在于改进数字视觉/特征表示的率失真或鲁棒性边界；若没有信道实验，不能把收益直接表述为无线 JSCC 增益。"
        limitation = "主要局限是信道被等价为容量或可靠文件传输：缺少 packetization、FEC、误码/丢包和端到端空口验证。"
    elif theme in {"resource", "theory"}:
        reviewer = "价值在于把语义效用接入网络优化或可达边界；关键是效用定义能否在真实链路被测量、估计并稳定用于决策。"
        limitation = "结果依赖抽象效用曲线、仿真信道和理想状态信息；底层语义 codec、控制信令与有限时延开销常未共同计入。"
    elif "类别 4" in channel_class or "HARQ/重传" in channel_class:
        reviewer = "通信价值来自把离散错误的后果纳入语义目标，而不只是降低平均 BER；应重点检查错误模型、保护开销和训练/测试失配。"
        limitation = "错误模型仍主要来自仿真；码本规模、包头/FEC、真实调制和 burst error 是否与训练分布一致，需要原型或真实链路验证。"
    elif "类别 3" in channel_class:
        reviewer = "通信价值要由相同 CBR、功率和信道条件下的质量/任务收益证明，而不是只由神经网络指标提升证明。"
        limitation = "主接口仍是连续神经符号；量化、有限星座、同步、信道估计和残余误码未形成完整数字实现。"
    else:
        reviewer = "价值应由论文在明确带宽/信道预算下对任务或重建质量的改善来判断，同时区分提出方法与传统链路 baseline。"
        limitation = "全文没有完整闭合语义表示到 bit/symbol/packet 的实现链；残余误码、控制开销和真实射频条件仍是外推风险。"
    record["reviewer_value"] = f"该工作位于“{layer}”：{reviewer}"
    curated_limitation = record.get("curated_limitation", "")
    if ("类别 4" in channel_class or "HARQ/重传" in channel_class) and "未显式" in curated_limitation:
        curated_limitation = ""
    record["limitations"] = curated_limitation or limitation

    method_detail = record["method_summary"].get("zh", "").strip()
    if len(method_detail) > 260:
        method_detail = method_detail[:257].rstrip("，,；; ") + "…"
    encoder_flow = f"发送端采用 {method}：{method_detail}" if method_detail else f"发送端采用 {method} 完成语义/信源信道处理。"
    record["system_flow"] = {
        "input": {"zh": f"输入是{task}所需的{record['input_description']}。", "pages": record["method_summary"].get("pages", [])},
        "encoder": {"zh": encoder_flow, "pages": record["method_summary"].get("pages", [])},
        "transmitted": {"zh": f"实际发送对象是{record['transmitted_object']}。", "pages": record["representation_summary"].get("pages", [])},
        "channel": {"zh": f"信道作用方式按“{channel_class}”解释。", "pages": record["channel_summary"].get("pages", [])},
        "receiver": {"zh": f"接收端从{record['decoder_object']}开始，再执行语义解码、任务推理或生成。", "pages": record["channel_summary"].get("pages", [])},
        "output": {"zh": f"最终输出为{record['output_description']}。", "pages": record["experiment_result_summary"].get("pages", [])},
    }
    record["analysis_version"] = ANALYSIS_VERSION
    record.pop("evidence_indices", None)
    record.pop("transmitted_object", None)
    record.pop("decoder_object", None)
    record.pop("input_description", None)
    record.pop("output_description", None)
    record.pop("curated_decoder", None)
    record.pop("curated_error", None)
    record.pop("curated_limitation", None)
    record.pop("curated_formula", None)
    record.pop("is_survey", None)


def figure_caption_from_page(page_text: str, kind: str) -> tuple[str, str]:
    candidates = []
    for match in re.finditer(r"\b(Fig\.\s*\d+[a-z]?)\.\s*([^\n]{20,280}?)(?=(?:\bFig\.\s*\d+|\bTable\s+[IVX0-9]+|$))", page_text, re.I):
        number = norm_space(match.group(1))
        caption = norm_space(match.group(2)).split(". ", 1)[0].strip(" .")
        if 20 <= len(caption) <= 240 and not NARRATIVE_BANNED.search(caption):
            candidates.append((number, caption))
    if not candidates:
        return "", ""
    cues = re.compile(r"system|framework|architecture|model|scheme|overview|pipeline", re.I) if kind == "method" else re.compile(r"performance|comparison|results?|accuracy|PSNR|SSIM|BER|rate", re.I)
    for number, caption in candidates:
        if cues.search(caption):
            return number, caption
    return candidates[0]


def figure_score(caption: str, kind: str) -> int:
    low = caption.lower()
    quality_penalty = 0
    if re.search(r"\b(?:shown|given|introduced) in$|\b(?:repres|compa|s)$", low):
        quality_penalty += 7
    if any(x in low for x in ("bitrate saving bitrate", "show the results its", "is information. the", "are introduced as follows", "of the comparison", "compares the reconstruction")):
        quality_penalty += 7
    if kind == "result" and "qualitative" in low:
        quality_penalty += 3
    if kind == "method":
        score = 0
        for cue, weight in (("proposed", 7), ("architecture", 7), ("framework", 7), ("system model", 6), ("block diagram", 6), ("prototype", 6), ("structure", 5), ("overview", 4), ("workflow", 4), ("scheme", 2)):
            if cue in low:
                score += weight
        for cue, weight in (("comparison", 7), ("performance", 6), ("results", 5), ("existing", 4), ("versus", 4)):
            if cue in low:
                score -= weight
        return score - quality_penalty
    score = 0
    for cue, weight in (("performance comparison", 9), ("comparison", 7), ("rate-distortion", 7), ("results", 6), ("rsum", 6), ("accuracy", 5), ("psnr", 5), ("ssim", 5), ("ber", 5), ("qoe", 5), ("ablation", 5), ("outperform", 4), ("improvement", 3)):
        if cue in low:
            score += weight
    for cue, weight in (("architecture", 5), ("framework", 5), ("system model", 5), ("structure", 3)):
        if cue in low:
            score -= weight
    return score - quality_penalty


def render_evidence_page(pdf: Path, page: int, target: Path) -> None:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    prefix = target.with_suffix("")
    subprocess.run(
        [pdftoppm, "-f", str(page), "-l", str(page), "-r", "130", "-png", "-singlefile", str(pdf), str(prefix)],
        check=True,
        capture_output=True,
    )


def attach_assets(record: dict, old: dict, evidence: dict, root: Path, pages: list[str]) -> None:
    assets = []
    for asset in old.get("assets") or []:
        file = asset.get("file", "")
        if file and (root / file).exists():
            assets.append(dict(asset))
    if not assets:
        stem = f"{record['year']}_{slugify(record['title'])}"
        candidates = list((root / "assets").glob(f"{stem}*.png"))
        if not candidates:
            prefix = f"{record['year']}_{slugify(record['title'], 72)}"
            candidates = list((root / "assets").glob(f"{prefix}*.png"))
        for path in sorted(candidates):
            kind = "method" if "_method_" in path.name else "result" if "_result_" in path.name else ""
            if not kind:
                continue
            page_match = re.search(r"_p(\d+)\.png$", path.name)
            assets.append({"kind": kind, "page": int(page_match.group(1)) if page_match else 0, "file": f"assets/{path.name}", "caption": ""})
    figures = [
        {"page": int(f.get("page") or 0), "number": str(f.get("number") or ""), "caption": norm_space(f.get("caption"))}
        for f in (evidence.get("figures") or [])
        if int(f.get("page") or 0) > 0 and 15 <= len(norm_space(f.get("caption"))) <= 320 and not POLLUTION.search(norm_space(f.get("caption")))
    ]
    # Re-select evidence pages when the old extractor chose a related-work
    # figure or an uninformative page.  Existing files are retained on disk but
    # the rebuilt HTML references the stronger page.
    pdf = root / record.get("pdf", "")
    for kind in ("method", "result"):
        ranked = sorted(
            (f for f in figures if figure_score(f["caption"], kind) > 2),
            key=lambda f: (-figure_score(f["caption"], kind), f["page"]),
        )
        if not ranked:
            continue
        best = ranked[0]
        current = next((a for a in assets if a.get("kind") == kind), None)
        current_score = figure_score(norm_space((current or {}).get("caption")), kind)
        if current and int(current.get("page") or 0) == best["page"]:
            continue
        if current_score >= figure_score(best["caption"], kind):
            continue
        file = f"assets/{record['year']}_{slugify(record['title'],86)}_{kind}_p{best['page']}.png"
        target = root / file
        if not target.exists() and pdf.exists():
            render_evidence_page(pdf, best["page"], target)
        replacement = {"kind": kind, "page": best["page"], "file": file, "caption": best["caption"], "number": f"Fig. {best['number']}" if best["number"] else ""}
        if current:
            assets[assets.index(current)] = replacement
        else:
            assets.append(replacement)
    for asset in assets[:2]:
        page = int(asset.get("page") or 0)
        kind = asset.get("kind", "method")
        chosen = None
        page_figs = [f for f in figures if int(f.get("page") or 0) == page]
        cues = re.compile(r"system|framework|architecture|model|scheme|overview|pipeline", re.I) if kind == "method" else re.compile(r"performance|comparison|results?|accuracy|PSNR|SSIM|BER|rate", re.I)
        for fig in page_figs:
            caption = norm_space(fig.get("caption"))
            if cues.search(caption) and 15 <= len(caption) <= 260 and not POLLUTION.search(caption):
                chosen = fig
                break
        if not chosen:
            for fig in page_figs:
                caption = norm_space(fig.get("caption"))
                if 15 <= len(caption) <= 260 and not POLLUTION.search(caption):
                    chosen = fig
                    break
        if chosen:
            asset["number"] = f"Fig. {chosen.get('number')}" if chosen.get("number") else ""
            asset["caption"] = norm_space(chosen.get("caption"))
        elif 1 <= page <= len(pages):
            number, caption = figure_caption_from_page(pages[page - 1], kind)
            asset["number"] = number
            asset["caption"] = caption
        if not asset.get("caption"):
            asset["caption"] = "该页包含论文的主要方法/架构图。" if kind == "method" else "该页包含论文的关键实验结果图或表。"
    record["assets"] = assets[:2]


def page_refs(item: dict, pdf_link: str, local: bool) -> str:
    refs = []
    for page in item.get("pages", [])[:4]:
        if local and pdf_link:
            refs.append(f"<a class='locator' href='{html.escape(pdf_link)}#page={page}'>PDF p.{page}</a>")
        else:
            refs.append(f"<span class='locator'>PDF p.{page}</span>")
    return " " + " ".join(refs) if refs else ""


def synthesis_li(label: str, item: dict, pdf_link: str, local: bool) -> str:
    text = item.get("zh", "")
    return f"<li><strong>{label}：</strong>{html.escape(text)}{page_refs(item, pdf_link, local)}</li>"


def synthesis_p(item: dict, pdf_link: str, local: bool) -> str:
    return f"<p>{html.escape(item.get('zh',''))}{page_refs(item, pdf_link, local)}</p>"


def list_text(values: list[str], fallback: str = "全文未稳定定位") -> str:
    return "、".join(values) if values else fallback


def article_html(record: dict, local: bool) -> str:
    slug = slugify(record["title"], 120)
    source_link = record["source_url"]
    pdf_link = record["pdf"] if local and record.get("pdf") else source_link
    primary_label = "打开本地 PDF" if local and record.get("pdf") else "DOI / IEEE 页面"
    tier_label = "核心纳入" if record["tier"] == "core" else "相关但非核心"
    tier_class = "core" if record["tier"] == "core" else "related"
    motivation = record["motivation"]
    flow = record["system_flow"]
    meta = []
    if record.get("volume"):
        meta.append("Vol. " + record["volume"])
    if record.get("issue"):
        meta.append("No. " + record["issue"])
    if record.get("pages"):
        meta.append("pp. " + record["pages"])
    figures = []
    for asset in record.get("assets", []):
        kind = "架构/方法图" if asset.get("kind") == "method" else "关键实验结果图/表"
        source = f"{asset.get('number','')} {asset.get('caption','')}".strip()
        figures.append(
            f"<figure><a href='{html.escape(asset['file'])}' target='_blank'><img loading='lazy' src='{html.escape(asset['file'])}' alt='{html.escape(record['title'])} {kind}'></a>"
            f"<figcaption><b>{kind}</b>｜来源：《{html.escape(record['title'])}》，原 PDF p.{asset.get('page','?')}，{html.escape(source)} "
            f"<a href='{html.escape(pdf_link)}{'#page='+str(asset.get('page')) if local and record.get('pdf') else ''}'>核对论文</a></figcaption></figure>"
        )
    if not figures:
        figures.append("<p class='notice'>PDF 中没有可靠定位到可展示的架构图或关键结果页；该条仅保留页码化文字证据。</p>")
    formula = record["overhead_summary"].get("formula", "")
    return rf"""
<article class='paper' id='{slug}' data-year='{record['year']}' data-tier='{record['tier']}' data-theme='{record['theme']}'>
  <header class='paper-head'>
    <div><div class='chips'><span class='tag {tier_class}'>{tier_label}</span><span class='tag year'>{record['year']}</span><span class='tag'>{html.escape(record['task_type'])}</span></div>
    <h2>{html.escape(record['title'])}</h2></div>
    <a class='button' href='{html.escape(pdf_link)}'>{primary_label}</a>
  </header>
  <div class='meta-grid'>
    <p><strong>作者</strong>{html.escape(record['authors'])}</p>
    <p><strong>出版信息</strong>{html.escape(' · '.join(meta) or record['venue'])}</p>
    <p><strong>DOI / IEEE ID</strong><a href='{html.escape(source_link)}'>{html.escape(record['doi'] or '未登记 DOI')}</a>{' / '+html.escape(record['ieee_document_id']) if record.get('ieee_document_id') else ''}</p>
    <p><strong>通信位置</strong>{html.escape(record['communication_layer'])}</p>
  </div>
  <p class='lead'><strong>一句话主旨：</strong>{html.escape(record['method_name'])} 面向{html.escape(record['task_type'])}，把问题放在“{html.escape(record['communication_layer'])}”层处理；本调研把主接口判断为“{html.escape(record['digitalization_class'])}”。</p>

  <h3>Motivation｜Introduction 怎样导出本文方案</h3>
  <ol class='story'>
    {synthesis_li('现有进展', motivation['progress'], pdf_link, local)}
    {synthesis_li('仍然存在的问题', motivation['problem'], pdf_link, local)}
    {synthesis_li('为什么已有方法解决不了', motivation['prior_limit'], pdf_link, local)}
    {synthesis_li('为什么这个问题重要', motivation['importance'], pdf_link, local)}
    {synthesis_li('本文提出什么', motivation['proposal'], pdf_link, local)}
    {synthesis_li('方案为何可能有效', motivation['mechanism'], pdf_link, local)}
    {synthesis_li('作者希望证明什么', motivation['claim'], pdf_link, local)}
  </ol>

  <h3>方法与端到端信息流</h3>
  {synthesis_p(record['method_summary'], pdf_link, local)}
  <div class='flow'>
    <div><b>输入</b><span>{html.escape(flow['input']['zh'])}</span></div>
    <div><b>发送端</b><span>{html.escape(flow['encoder']['zh'])}</span></div>
    <div><b>实际发送</b><span>{html.escape(flow['transmitted']['zh'])}</span></div>
    <div><b>信道</b><span>{html.escape(flow['channel']['zh'])}</span></div>
    <div><b>接收端</b><span>{html.escape(flow['receiver']['zh'])}</span></div>
    <div><b>输出</b><span>{html.escape(flow['output']['zh'])}</span></div>
  </div>
  <div class='callout'><strong>它在通信系统中的位置：</strong>{html.escape(record['layer_explanation'])}</div>

  <h3>数字化方案与真实传输开销</h3>
  <p><strong>是否属于严格数字语义通信：</strong>{html.escape(str(record['strict_digital']))}</p>
  <p><strong>表示判断：</strong><span class='tag'>{html.escape(record['digitalization_class'])}</span></p>
  {synthesis_p(record['representation_summary'], pdf_link, local)}
  {synthesis_p(record['overhead_summary'], pdf_link, local)}
  <div class='formula'>\[{formula}\]</div>
  <p class='mini'><strong>换算边界：</strong>{html.escape(record['overhead_summary'].get('caveat',''))}</p>

  <h3>信道怎样作用，以及 decoder 实际拿到什么</h3>
  <p><strong>信道处理类别：</strong><span class='tag'>{html.escape(record['channel_handling_class'])}</span></p>
  {synthesis_p(record['channel_summary'], pdf_link, local)}
  {synthesis_p(record['decoder_input_summary'], pdf_link, local)}
  <div class='verdict'><strong>是否真正处理离散变量出错：</strong>{html.escape(record['discrete_error_judgment'])}</div>

  <h3>实验设置与主要结论</h3>
  <div class='facts'>
    <p><strong>数据集/场景</strong>{html.escape(list_text(record['datasets']))}</p>
    <p><strong>Baseline</strong>{html.escape(list_text(record['baselines']))}</p>
    <p><strong>评价指标</strong>{html.escape(list_text(record['metrics']))}</p>
    <p><strong>信道与工作点</strong>{html.escape(list_text(record['channels'] + record['snr_conditions'] + record['ber_conditions'] + record['rate_conditions']))}</p>
  </div>
  {synthesis_p(record['experiment_setup_summary'], pdf_link, local)}
  {synthesis_p(record['experiment_result_summary'], pdf_link, local)}

  <h3>通信价值、局限与 Codex 判断</h3>
  <p>{html.escape(record['reviewer_value'])}</p>
  <p><strong>局限：</strong>{html.escape(record['limitations'])}</p>
  <div class='fig-grid'>{''.join(figures)}</div>
</article>"""


def table_rows(records: list[dict]) -> str:
    rows = []
    for r in records:
        slug = slugify(r["title"], 120)
        rows.append(
            "<tr>"
            f"<td>{r['year']}</td><td>{'核心' if r['tier']=='core' else '相关'}</td>"
            f"<td><a href='#{slug}'>{html.escape(r['title'])}</a></td>"
            f"<td>{html.escape(r['task_type'])}</td><td>{html.escape(r['digitalization_class'])}</td>"
            f"<td>{html.escape(r['channel_handling_class'])}</td>"
            f"<td>{html.escape(r['discrete_error_judgment'])}</td></tr>"
        )
    return "".join(rows)


def nav_html(records: list[dict]) -> str:
    parts = ["<a class='top-link' href='#overview'>总览与使用说明</a>", "<a class='top-link' href='#comparison'>横向比较</a>"]
    current = None
    for record in records:
        if record["year"] != current:
            current = record["year"]
            parts.append(f"<div class='nav-year'>{current}</div>")
        parts.append(f"<a href='#{slugify(record['title'],120)}' title='{html.escape(record['title'])}'>{html.escape(record['title'])}</a>")
    return "".join(parts)


CSS = r"""
:root{--ink:#17212b;--muted:#61707d;--paper:#f3f0ea;--card:#fff;--line:#d9d4ca;--accent:ACCENT;--accent-dark:ACCENT_DARK;--soft:#eef5f4;--warn:#fff3cf;--related:#755d35}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,"Noto Sans SC","Microsoft YaHei",sans-serif;line-height:1.76}a{color:var(--accent)}.skip{position:absolute;left:-9999px}.skip:focus{left:10px;top:10px;z-index:20;background:#fff;padding:8px}nav{position:fixed;inset:0 auto 0 0;width:350px;overflow:auto;background:var(--accent-dark);color:#edf7f6;padding:22px 18px 40px}nav h2{font-size:17px;margin:0 0 12px}nav input{width:100%;padding:10px;border:0;border-radius:9px;margin-bottom:10px}nav a{display:block;color:#dcefed;text-decoration:none;padding:7px 8px;border-radius:8px;font-size:12.5px;line-height:1.35}nav a:hover,nav a.active{background:rgba(255,255,255,.13)}nav .top-link{font-weight:700;color:#fff}.nav-year{color:#8ed9cf;font-weight:800;margin:18px 8px 4px}.nav-note{font-size:11px;color:#b8d1ce;margin:10px 8px}main{margin-left:350px;max-width:1320px;padding:40px 50px 100px}.hero,.panel,.paper{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px;margin-bottom:24px;box-shadow:0 10px 30px rgba(30,44,49,.05)}.hero{background:linear-gradient(145deg,#fff 0,#f7fbfa 100%)}h1{font:700 42px/1.2 Georgia,"Noto Serif SC",serif;margin:.15em 0}h2{font-size:26px;line-height:1.32;margin:.3em 0}h3{font-size:19px;color:var(--accent-dark);margin:30px 0 9px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:var(--accent);font-weight:800;font-size:12px}.hero-grid,.stats,.facts,.meta-grid{display:grid;gap:12px}.stats{grid-template-columns:repeat(4,1fr);margin:20px 0}.stat{background:var(--soft);border-radius:13px;padding:14px}.stat b{font-size:26px;display:block}.hero-grid{grid-template-columns:1.3fr .7fr}.paper{content-visibility:auto;contain-intrinsic-size:auto 1500px;scroll-margin-top:15px}.paper:target{outline:3px solid color-mix(in srgb,var(--accent) 55%,transparent);outline-offset:3px}.paper-head{display:flex;gap:22px;justify-content:space-between;align-items:flex-start}.paper-head .button{white-space:nowrap}.chips{display:flex;flex-wrap:wrap;gap:7px}.tag{display:inline-block;background:#e3efed;color:#174e49;border-radius:999px;padding:4px 9px;font-size:12px}.tag.core{background:#dff0e4;color:#22653a}.tag.related{background:#f3e9d8;color:var(--related)}.tag.year{background:#e5eaf6;color:#2e477e}.button{display:inline-block;background:var(--accent);color:#fff!important;text-decoration:none;padding:9px 13px;border-radius:9px;font-weight:700}.meta-grid{grid-template-columns:repeat(2,1fr);margin:16px 0}.meta-grid p,.facts p{margin:0;background:#f6f7f5;border-radius:10px;padding:11px}.meta-grid strong,.facts strong{display:block;color:var(--muted);font-size:12px}.lead{font-size:16px;border-left:4px solid var(--accent);padding:10px 14px;background:var(--soft);border-radius:0 9px 9px 0}.story li{margin:9px 0}.locator{display:inline-block;white-space:nowrap;background:#edf2f2;border-radius:999px;padding:1px 7px;font-size:11px;text-decoration:none;color:#3b706c}.flow{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:15px 0}.flow div{position:relative;background:var(--soft);border:1px solid #cbdeda;border-radius:11px;padding:10px;min-height:126px}.flow div:not(:last-child):after{content:"→";position:absolute;right:-9px;top:46%;z-index:1;color:var(--accent);font-weight:900}.flow b{display:block;color:var(--accent-dark);margin-bottom:5px}.flow span{font-size:12px;line-height:1.5}.callout,.verdict,.notice{padding:12px 14px;border-radius:10px}.callout{background:#edf4f8;border-left:4px solid #5282a6}.verdict{background:var(--warn);border-left:4px solid #c89626}.notice{background:var(--warn)}.formula{overflow:auto;background:#f8faf9;border:1px dashed #bdcbc8;border-radius:10px;padding:8px 12px;margin:10px 0}.mini{font-size:12px;color:var(--muted)}.facts{grid-template-columns:repeat(2,1fr)}.fig-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:20px}figure{margin:0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fafafa}figure img{display:block;width:100%;height:auto;aspect-ratio:952/1232;object-fit:contain;background:#fff}figcaption{padding:10px;font-size:12px;color:var(--muted)}.table-wrap{overflow:auto;max-height:72vh;border:1px solid var(--line);border-radius:10px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}th{position:sticky;top:0;background:#eaf1ef;z-index:1}.filters{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.filters button{border:1px solid var(--line);border-radius:999px;padding:6px 10px;background:#fff;cursor:pointer}.filters button.active{background:var(--accent);color:#fff}.hidden-paper{display:none!important}@media(max-width:1080px){nav{position:relative;width:auto;max-height:45vh}main{margin-left:0;padding:26px}.flow{grid-template-columns:repeat(3,1fr)}.stats{grid-template-columns:repeat(2,1fr)}}@media(max-width:680px){main{padding:14px}.hero,.panel,.paper{padding:18px}.paper-head{display:block}.paper-head .button{margin-top:10px}.flow,.facts,.meta-grid,.fig-grid,.hero-grid{grid-template-columns:1fr}.flow div:not(:last-child):after{content:"↓";right:50%;top:auto;bottom:-15px}.stats{grid-template-columns:1fr 1fr}h1{font-size:30px}}@media print{nav{display:none}main{margin:0;max-width:none}.paper{content-visibility:visible;break-inside:auto}.button{display:none}}
"""


JS = r"""
const papers=[...document.querySelectorAll('.paper')];
const search=document.getElementById('paper-search');
function applyFilter(){const q=(search.value||'').toLowerCase();const tier=document.querySelector('.filters button.active')?.dataset.tier||'all';papers.forEach(p=>{const okQ=!q||p.textContent.toLowerCase().includes(q);const okT=tier==='all'||p.dataset.tier===tier;p.classList.toggle('hidden-paper',!(okQ&&okT));});}
search.addEventListener('input',applyFilter);
document.querySelectorAll('.filters button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('active'));b.classList.add('active');applyFilter();}));
const links=[...document.querySelectorAll('nav a[href^="#"]')];
const observer=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id));}})},{rootMargin:'-15% 0px -75% 0px'});papers.forEach(p=>observer.observe(p));
"""


def build_html(config: dict, records: list[dict], local: bool, output: Path) -> None:
    counts = Counter(r["tier"] for r in records)
    years = sorted({r["year"] for r in records})
    digital_count = sum("显式数字" in r["digitalization_class"] or "有限星座" in r["digitalization_class"] or "bitstream" in r["digitalization_class"] for r in records)
    error_count = sum("类别 4" in r["channel_handling_class"] for r in records)
    task_counts = Counter(r["task_type"] for r in records)
    channel_counts = Counter(r["channel_handling_class"].split("：", 1)[0] for r in records)
    edition = "本地深读版" if local else "公开网页版本"
    css = CSS.replace("ACCENT_DARK", config["accent_dark"]).replace("ACCENT", config["accent"])
    task_summary = "".join(f"<li>{html.escape(k)}：{v} 篇</li>" for k, v in task_counts.most_common())
    channel_summary = "".join(f"<li>{html.escape(k)}：{v} 篇</li>" for k, v in sorted(channel_counts.items()))
    document = f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{html.escape(config['title'])}</title><style>{css}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]}},svg:{{fontCache:'global'}}}};</script>
<script defer src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'></script></head>
<body><a class='skip' href='#overview'>跳到正文</a>
<nav><h2>{config['short']} 逐篇目录</h2><input id='paper-search' type='search' placeholder='按完整标题、方法或任务筛选…'><div class='nav-note'>目录使用论文完整标题；共 {len(records)} 篇。</div>{nav_html(records)}</nav>
<main id='overview'>
<section class='hero'><div class='eyebrow'>{config['short']} · 2023—{max(years)}</div><h1>{html.escape(config['title'])}</h1>
<p>本页是对原专题的整体重建。所有 {len(records)} 篇纳入论文均重新从本地 PDF 以正确双栏阅读顺序抽取并核对；Introduction、方法、数字化接口、信道作用点和实验结论经过二次中文综合，不再显示栏间交错的原始英文片段。</p>
<div class='stats'><div class='stat'><b>{len(records)}</b>PDF 全文重读</div><div class='stat'><b>{counts['core']}</b>核心纳入</div><div class='stat'><b>{counts['related']}</b>边界相关</div><div class='stat'><b>{error_count}</b>显式处理离散错误</div></div>
<div class='callout'><b>{edition}：</b>{'论文按钮和页码 locator 均指向已下载的本地 PDF。' if local else '受版权保护的 IEEE PDF 不上传；论文按钮指向 DOI/IEEE 页面，证据图和页码用于本地研究复核。'} 内容更新于 2026-08-28，分析版本 <code>{ANALYSIS_VERSION}</code>。</div></section>

<section class='panel'><h2>阅读口径与质量控制</h2><div class='hero-grid'><div><h3>纳入范围</h3><p>{html.escape(config['scope'])}。核心/相关标签表示与语义通信问题的接近程度，不评价论文质量。正式年份以期刊卷年为准。</p><h3>重新阅读流程</h3><ol><li>逐篇校验 manifest 与本地 PDF；</li><li>使用 Poppler 正常阅读顺序重新抽取全文，避免双栏交错；</li><li>从 Introduction、方法、数字化/速率、信道与实验段落选择页码证据；</li><li>以干净书目摘要为叙事锚点，生成中文综合，原始抽取文本不进入页面；</li><li>单独判断 decoder 收到什么，以及论文是否处理残余 bit/index/packet error。</li></ol></div><div><h3>任务分布</h3><ul>{task_summary}</ul><h3>信道处理分布</h3><ul>{channel_summary}</ul></div></div>
<p class='mini'>可追溯文件：<a href='notes/synthesized_analysis.jsonl'>逐篇二次综合 JSONL</a> · <a href='notes/reread_audit.jsonl'>全文重读审计</a> · <a href='notes/cross_paper_comparison.csv'>横向比较 CSV</a>。旧 structured_analysis/evidence 只保留为抽取审计层，不再作为网页展示层。</p></section>

<section class='panel' id='comparison'><h2>{len(records)} 篇横向比较</h2><p>重点看“表示”和“信道处理”两列：有数字 bitstream 不等于处理了误码；连续 DeepJSCC 的抗噪声也不能外推到 VQ index 跳变。</p><div class='filters'><button class='active' data-tier='all'>全部</button><button data-tier='core'>仅核心</button><button data-tier='related'>仅相关</button></div>
<div class='table-wrap'><table><thead><tr><th>年</th><th>层级</th><th>完整标题</th><th>任务</th><th>传输表示</th><th>信道处理</th><th>离散错误判断</th></tr></thead><tbody>{table_rows(records)}</tbody></table></div></section>

{''.join(article_html(r, local) for r in records)}
</main><script>{JS}</script></body></html>"""
    output.write_text(document, encoding="utf-8")


def write_notes(root: Path, records: list[dict], audits: list[dict]) -> None:
    notes = root / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    (notes / "synthesized_analysis.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8"
    )
    (notes / "reread_audit.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in audits), encoding="utf-8"
    )
    fields = [
        "year", "tier", "title", "doi", "task_type", "digitalization_class",
        "channel_handling_class", "strict_digital", "datasets", "baselines", "metrics",
        "snr_conditions", "rate_conditions", "discrete_error_judgment", "limitations",
    ]
    with (notes / "cross_paper_comparison.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {key: record.get(key, "") for key in fields}
            for key in ("datasets", "baselines", "metrics", "snr_conditions", "rate_conditions"):
                row[key] = "；".join(row[key])
            writer.writerow(row)


def process_journal(key: str, pdftotext: str, translator: CachedTranslator, translate: bool) -> None:
    config = JOURNALS[key]
    root = ROOT / "literature" / config["directory"]
    manifest = load_jsonl(root / "manifest.jsonl")
    old_records = load_jsonl(root / "notes" / "structured_analysis.jsonl")
    evidence_records = load_jsonl(root / "notes" / "evidence.jsonl")
    old_by_doi = {norm_doi(r.get("doi")): r for r in old_records}
    old_by_title = {norm_space(r.get("title")).lower(): r for r in old_records}
    evidence_by_doi = {norm_doi(r.get("doi")): r for r in evidence_records}
    evidence_by_title = {norm_space(r.get("title")).lower(): r for r in evidence_records}
    records: list[dict] = []
    audits: list[dict] = []
    page_cache: dict[str, list[str]] = {}
    for index, source in enumerate(manifest, start=1):
        doi = norm_doi(source.get("doi"))
        title_key = norm_space(source.get("title")).lower()
        old = old_by_doi.get(doi) or old_by_title.get(title_key) or {}
        evidence = evidence_by_doi.get(doi) or evidence_by_title.get(title_key) or {}
        filename = paper_filename(source.get("pdf_path") or old.get("pdf_name"))
        pdf = root / "papers" / filename
        if not pdf.exists():
            raise FileNotFoundError(f"Missing PDF for {source.get('title')}: {pdf}")
        pages = extract_pages(pdf, pdftotext)
        raw, audit = build_raw_record(source, old, evidence, pages, key)
        attach_assets(raw, old, evidence, root, pages)
        records.append(raw)
        audits.append(audit)
        page_cache[doi or title_key] = pages
        print(f"[{config['short']}] reread {index}/{len(manifest)}: {source.get('title')}")
    if translate:
        translator.translate_records(records)
    else:
        missing = [field.get("en") for r in records for field in iter_translatable_fields(r) if field.get("en") and field.get("en") not in translator.cache]
        if missing:
            raise RuntimeError(f"Translation cache is missing {len(set(missing))} texts; rerun without --no-translate")
        translator.translate_records(records)
    for index, record in enumerate(records):
        apply_curated_presentation_overrides(record)
        append_judgments(record)
        records[index] = polish_record_strings(record)
    records.sort(key=lambda r: (r["year"], r["title"].lower()))
    order = {norm_doi(r.get("doi")): i for i, r in enumerate(records)}
    audits.sort(key=lambda r: order.get(norm_doi(r.get("doi")), 10**9))
    write_notes(root, records, audits)
    build_html(config, records, False, root / "index.html")
    build_html(config, records, True, root / "index_local.html")
    print(f"[{config['short']}] wrote {len(records)} synthesized records and both HTML editions")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--journals", default="twc,tccn,tcsvt", help="Comma-separated journal keys")
    parser.add_argument("--no-translate", action="store_true", help="Use an already complete translation cache")
    args = parser.parse_args()
    keys = [x.strip().lower() for x in args.journals.split(",") if x.strip()]
    unknown = [x for x in keys if x not in JOURNALS]
    if unknown:
        raise SystemExit(f"Unknown journals: {', '.join(unknown)}")
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise SystemExit("pdftotext is required")
    cache = ROOT / "tmp" / "journal_semcom_translation_cache.json"
    translator = CachedTranslator(cache)
    for key in keys:
        process_journal(key, pdftotext, translator, not args.no_translate)


if __name__ == "__main__":
    main()
