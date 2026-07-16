#!/usr/bin/env python3
"""Rebuild team-paper prose as Chinese synthesis rather than raw quotations.

The existing ``structured_analysis.jsonl`` files remain the audit layer: they
contain page-addressable extracts.  This script creates a separate
``synthesized_analysis.jsonl`` presentation layer.  It deliberately derives
the story from the clean bibliographic abstract plus method/result evidence,
then translates the newly composed synthesis.  The public HTML never renders
the raw English extracts.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEAM_DIRS = {
    "kai-niu": "kai-niu-semantic-communications",
    "zhijin-qin": "zhijin-qin-semantic-communications",
    "meixia-tao": "meixia-tao-semantic-communications",
    "deniz-gunduz": "deniz-gunduz-semantic-communications",
    "surrey": "yi-ma-mahdi-mashhadi-semantic-communications",
    "qmul": "arumugam-nallanathan-deepsc-semantic-communications",
}


def norm_space(text: str) -> str:
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("–", "-")
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    text = norm_space(text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text) if len(s.strip()) > 25]


def choose(items: list[str], patterns: tuple[str, ...], fallback: str = "") -> str:
    for item in items:
        low = item.lower()
        if any(re.search(pattern, low) for pattern in patterns):
            return item
    return fallback


def clean_claim(text: str) -> str:
    text = norm_space(text)
    text = re.sub(r"^(abstract\s*[-:]?|index terms\s*[-:]?)\s*", "", text, flags=re.I)
    text = re.sub(r"^(however|nevertheless|therefore|thus|moreover|furthermore),?\s+", "", text, flags=re.I)
    return text.strip(" ;")


def rhetorical_abstract(a: dict) -> dict[str, str]:
    ss = sentences(a.get("abstract", ""))
    background = next((s for s in ss if not re.search(r"\b(we propose|this (paper|letter)|results|experiment)", s, re.I)), ss[0] if ss else "")
    problem = choose(ss, (r"\bhowever\b", r"\bchallenge", r"\blimit", r"\bfail", r"\black", r"\bshortcoming", r"\bdifficult"))
    proposal = choose(ss, (r"\bwe propose", r"\bwe present", r"\bwe develop", r"\bwe design", r"\bthis (paper|letter) proposes", r"\bwe introduce"))
    mechanism = choose(ss, (r"\bspecifically", r"\bto this end", r"\bby (leveraging|using|jointly|exploiting|introducing)", r"\bbased on", r"\bconsists of", r"\bcomprises"))
    result = choose(list(reversed(ss)), (r"\bexperimental results", r"\bnumerical results", r"\bresults (show|demonstrate|indicate)", r"\boutperform", r"\bachieves?"))
    if not problem:
        intro_problem = ((a.get("evidence") or {}).get("problem") or {}).get("text", "")
        problem = intro_problem
    if not proposal:
        proposal = f"The paper develops the method described by its title: {a.get('title','')}."
    if not mechanism:
        intro_mechanism = ((a.get("evidence") or {}).get("mechanism") or {}).get("text", "")
        mechanism = intro_mechanism or proposal
    if not result:
        result = "The experiments are intended to test whether the proposed mechanism improves the target communication objective under the stated resource and channel conditions."
    return {k: clean_claim(v) for k, v in {
        "background": background, "problem": problem, "proposal": proposal,
        "mechanism": mechanism, "result": result,
    }.items()}


def infer_task(a: dict) -> tuple[str, str, str]:
    """Infer the paper's actual application, without letting cited work win.

    The old extractor searched method snippets before the title/abstract.  That
    made a retinal-image paper become speech/VQA merely because its related-work
    paragraph mentioned those tasks.  Bibliographic title and clean abstract are
    therefore authoritative; full-text snippets are only the last fallback.
    """
    title = a.get("title", "").lower()
    abstract = a.get("abstract", "").lower()
    method = " ".join(x.get("text", "") for x in (a.get("method_evidence") or [])[:5]).lower()
    datasets = " ".join(a.get("datasets") or []).lower()
    metrics = " ".join(a.get("metrics") or []).lower()
    rules = [
        (("speech", "audio", "voice", "speech-to-text"), "语音/音频传输或识别", "speech or audio", "speech waveform, text transcript, or recognition result"),
        (("video", "talking-head", "gop", "panoramic"), "视频传输或生成", "video frames or video semantics", "reconstructed or generated video"),
        (("point cloud", "3d scene", "3-d scene", "nerf", "gaussian splatting", "volumetric"), "点云/三维场景传输", "point cloud or 3D-scene observations", "reconstructed 3D content or downstream 3D task output"),
        (("text transmission", "text semantic", "machine translation", "language transmission", "token communication"), "文本传输/机器翻译", "a sentence or token sequence", "recovered text or a translation result"),
        (("vqa", "classification", "segmentation", "tracking", "inference", "task-oriented", "goal-oriented"), "任务导向推理", "source data together with a downstream task", "the task decision rather than necessarily the original source"),
        (("image", "visual", "photograph"), "图像传输或生成", "an input image", "a reconstructed or generated image"),
        (("resource allocation", "power allocation", "scheduling", "offloading"), "语义感知资源分配", "users, tasks, and their channel/resource states", "a resource-allocation policy and the resulting semantic utility"),
        (("theory", "metric", "rate-distortion", "information conductivity", "semantic value"), "语义信息度量与理论", "a source-task-channel probability model", "a bound, metric, or optimization principle"),
        (("multimedia", "multi-media"), "多媒体传输", "multimedia source content", "reconstructed multimedia content"),
    ]
    for words, label, inp, out in rules:
        if any(word in title for word in words):
            return label, inp, out
    # Strong experimental evidence outranks incidental application words in an
    # abstract (for example "contextual" used to trigger the substring "text").
    if any(x in datasets for x in ("kodak", "clic", "cifar", "imagenet", "cityscapes", "div2k", "coco")) or any(x in metrics for x in ("psnr", "ssim", "lpips")):
        return "图像传输或生成", "an input image", "a reconstructed or generated image"
    if any(phrase in abstract for phrase in ("wireless image transmission", "image transmission", "input image", "image reconstruction")):
        return "图像传输或生成", "an input image", "a reconstructed or generated image"
    if any(phrase in abstract for phrase in ("speech transmission", "speech signal", "speech recognition", "audio transmission")):
        return "语音/音频传输或识别", "speech or audio", "speech waveform, text transcript, or recognition result"
    for words, label, inp, out in rules:
        if any(word in abstract for word in words):
            return label, inp, out
    for words, label, inp, out in rules:
        if any(word in method for word in words):
            return label, inp, out
    return "通用语义通信系统", "source data and a communication task", "reconstructed content or task output"


def infer_theme(a: dict) -> str:
    title = a.get("title", "").lower()
    text = (title + " " + a.get("abstract", "")).lower()
    if any(w in title for w in ("a theory of semantic communication", "fundamental limitation", "rate-distortion", "information conductivity", "semantic similarity score", "semantic value", "semantic information theory", "information-theoretic metric")):
        return "theory"
    ordered = [
        ("security", ("security", "secure", "privacy", "eavesdrop", "encryption", "covert", "backdoor", "unlearning")),
        ("resource", ("resource allocation", "power allocation", "scheduling", "offloading", "fairness", "qoe")),
        ("multiuser", ("multi-user", "multiuser", "multiple access", "broadcast", "noma", "multicast", "relay", "full-duplex")),
        ("digital", ("digital", "bit-level", "vector quant", "vq-", "codebook", "constellation", "coding-modulation", "qam", "ofdm", "otfs", "harq", "packet")),
        ("generative", ("generative", "diffusion", "foundation model", "large language model", "llm", "prompt", "aigc", "nerf", "gaussian splatting")),
        ("task", ("task-oriented", "goal-oriented", "classification", "segmentation", "tracking", "vqa", "edge inference")),
        ("adaptive", ("adaptive", "channel-transferable", "feedback", "controllable", "dynamic")),
    ]
    for theme, words in ordered:
        if any(w in title for w in words):
            return theme
    return "jscc"


def specific_problem(theme: str, raw: str, task: str) -> str:
    low = raw.lower()
    defaults = {
        "theory": "Existing semantic systems use task-specific accuracy or reconstruction scores, but lack the common quantity or bound needed to compare semantic information efficiency across systems.",
        "security": "A semantic representation can still leak source content or be manipulated even when the legitimate receiver reconstructs well; reliability-only designs do not quantify this threat.",
        "resource": "Existing schemes commonly fix or optimize radio resources using bit rate or average distortion, without reflecting that users and samples have different task-level semantic value.",
        "multiuser": "Most semantic codecs are designed as point-to-point links and do not exploit cross-user semantic correlation or jointly handle heterogeneous channels, interference, and user fairness.",
        "digital": "Many learned semantic links stop at a continuous latent, leaving quantization, finite-symbol mapping, and the consequence of bit/index errors outside the learned design.",
        "generative": "Reconstruction-oriented links transmit many source details even when the receiver has a strong generative prior, while existing generative schemes do not fully control latency, hallucination, and channel-conditioned fidelity.",
        "task": "A reconstruction-oriented transmitter spends bandwidth on information that the downstream task does not need and may still fail to protect a small feature that determines the task decision.",
        "adaptive": "A semantic encoder trained for one bandwidth or channel condition has a fixed representation and cannot reallocate rate and protection when the operating point changes.",
        "jscc": f"Existing communication designs do not jointly preserve the semantic content required by the {task} objective under the paper's bandwidth and noisy-channel constraints.",
    }
    signals = {
        "multiuser": ("multi-user", "multiple user", "broadcast", "correlation", "interference"),
        "digital": ("digital", "quant", "bit", "index", "constellation"),
        "generative": ("generative", "diffusion", "prior", "halluc"),
        "security": ("secure", "privacy", "eaves", "attack", "leak"),
        "resource": ("resource", "power", "bandwidth", "allocation", "fair"),
        "task": ("task", "classification", "decision", "irrelevant"),
        "adaptive": ("adaptive", "dynamic", "vary", "mismatch", "fixed"),
        "theory": ("metric", "measure", "bound", "theory", "definition"),
        "jscc": ("semantic", "bit or symbol", "source-channel", "bandwidth", "latency"),
    }
    polluted = re.search(r"IEEE|Member,|Fellow,|Abstract|VOL\.|TRANSACTIONS|WORKSHOP|\bpp\.\s*\d", raw, re.I)
    return raw if raw and not polluted and any(s in low for s in signals[theme]) else defaults[theme]


def specific_prior(theme: str, problem: str) -> str:
    low = problem.lower()
    if "digital" in low and "analog" in low:
        return "An analog-only branch degrades gracefully but lacks a native bit-level security and protocol interface, whereas a digital-only branch offers that interface but can suffer saturation and a decoding cliff. Improving either branch in isolation keeps the other failure mode."
    if re.search(r"bit or symbol|bit-error|symbol-error|\bber\b|\bser\b", low):
        return "A bit-level objective treats every bit error as the same event and does not know whether the changed bit alters sentence meaning, speech intelligibility, or a task decision. Adding a stronger conventional code may reduce BER, but it does not directly optimize semantic distortion."
    if any(x in low for x in ("domain knowledge", "conceptual", "medical", "region of interest")):
        return "A single image path can learn visually useful features, but domain concepts are absent from both its input and loss. It can therefore reconstruct a plausible image while damaging the medically or operationally important structure that motivated the application."
    return PRIOR_LIMIT[theme]


PRIOR_LIMIT = {
    "theory": "Earlier systems can report task accuracy or reconstruction quality, but without the proposed quantity or bound they cannot compare semantic efficiency on a common information-theoretic basis. The missing object is a definition and optimization criterion, not another neural-network block.",
    "security": "Earlier reliability-oriented semantic encoders optimize the legitimate receiver and do not model what an eavesdropper, attacker, or curious server can infer from the transmitted representation. Better reconstruction alone therefore does not remove semantic leakage or manipulation risk.",
    "resource": "A fixed or bit-rate-oriented allocation cannot distinguish samples, users, and tasks with different semantic importance. It may spend power and bandwidth on low-value details while starving the user whose task quality is most sensitive to the channel.",
    "multiuser": "Running a point-to-point semantic codec independently for every user ignores shared content, heterogeneous channels, interference, and fairness. The single-user optimum therefore need not be feasible or spectrally efficient once users share the same medium.",
    "digital": "A continuous latent or a separately designed conventional link does not specify how semantic information is quantized, mapped to finite symbols, and protected when bits or indices are wrong. That interface gap cannot be closed by only improving the source autoencoder.",
    "generative": "Conventional reconstruction-oriented transmission spends channel uses describing details that a strong receiver prior could synthesize. It also lacks a mechanism for deciding which compact condition is sufficient and how generation errors should be traded against latency and fidelity.",
    "task": "Reconstructing every source detail is an unnecessarily strong objective when the receiver only needs a decision. A codec trained for pixel or waveform fidelity may discard a small task-critical feature while preserving visually plausible but irrelevant content.",
    "adaptive": "A model trained for one bandwidth, SNR, or channel distribution has a fixed bottleneck and protection pattern. When operating conditions change, repeating inference with the same representation cannot reassign rate or redundancy to the information that has become fragile.",
    "jscc": "Separate compression and channel coding, or an end-to-end model that ignores the paper's targeted semantic factor, optimizes mismatched intermediate objectives. The resulting representation is not explicitly shaped for the joint bandwidth, power, channel, and semantic-quality constraint studied here.",
}


PROGRESS_FALLBACK = {
    "theory": "Semantic communication research has produced task-specific distortion and utility measures, creating a basis for asking which semantic information is worth transmitting.",
    "security": "End-to-end semantic encoders can preserve the information needed by the legitimate receiver with fewer channel resources than reconstruction-oriented links.",
    "resource": "Semantic encoders and task-oriented links have established rate-quality curves that make it possible to optimize radio and computation resources against task utility.",
    "multiuser": "Point-to-point semantic communication has shown that learned representations can reduce channel use while preserving reconstruction or task performance.",
    "digital": "Learned semantic encoders have shown strong compression and graceful degradation, and recent work has begun to connect their latent representations to finite digital interfaces.",
    "generative": "Pretrained generative models can reconstruct plausible source detail from compact semantic conditions, suggesting that predictable content need not all be sent over the radio link.",
    "task": "Task-oriented communication has shown that a transmitter can send task-sufficient features instead of reconstructing every source sample at the receiver.",
    "adaptive": "Learned joint source-channel coding has already demonstrated end-to-end gains over fixed separated pipelines under matched training and test conditions.",
    "jscc": "Deep joint source-channel coding has shown that compression and channel robustness can be learned together, yielding graceful degradation and strong quality at limited channel bandwidth.",
}


def best_mechanism_claim(a: dict, rhet: dict) -> str:
    """Choose a method-specific mechanism, filtering headers and vague slogans."""
    candidates: list[tuple[int, str]] = [(3, x) for x in sentences(a.get("abstract", ""))]
    candidates += [(2, clean_claim(x.get("text", ""))) for x in (a.get("representation_evidence") or [])]
    candidates += [(1, clean_claim(x.get("text", ""))) for x in (a.get("method_evidence") or [])]
    banned = re.compile(
        r"IEEE|Member,|Fellow,|Abstract|By introducing AI|expected to evolve|"
        r"recent progress|related work|contributions .* summarized|this paper is organized|"
        r"Fig\.|Table\s+[IVX]|reshape layer|dense layer|IEEE",
        re.I,
    )
    cues = re.compile(
        r"(consists? of|comprises?|integrat|combine|jointly|concatenat|maps? .* to|"
        r"entropy model|hyperprior|attention|codebook|quantiz|modulat|allocat|"
        r"diffusion|prompt|side information|adaptive rate|feature importance|"
        r"semantic encoder|channel encoder|decoder receives)",
        re.I,
    )
    result_like = re.compile(r"results?|outperform|we (show|prove|demonstrate)|achiev|performance (gain|improv)|simulation", re.I)
    problem_like = re.compile(r"challenge|limitation|however|fail to|cannot|incompatible|vulnerab", re.I)
    ranked = [
        (priority, x) for priority, x in candidates
        if 45 <= len(x) <= 520 and not banned.search(x) and cues.search(x)
        and not result_like.search(x) and not problem_like.search(x)
    ]
    if ranked:
        return max(ranked, key=lambda item: (item[0], bool(re.search(r"specifically|to this end|consists|comprises", item[1], re.I)), -abs(len(item[1]) - 180)))[1]
    fallback = clean_claim(rhet.get("mechanism", ""))
    return fallback if fallback and not banned.search(fallback) and not result_like.search(fallback) and not problem_like.search(fallback) else clean_claim(rhet.get("proposal", ""))


def compact_list(values: list[str] | None, fallback: str) -> str:
    clean = []
    for value in values or []:
        value = norm_space(str(value))
        if value and value.lower() not in {x.lower() for x in clean}:
            clean.append(value)
    return ", ".join(clean[:8]) if clean else fallback


IMPORTANCE = {
    "语音/音频传输或识别": "The issue matters because intelligibility, recognition accuracy, and packet-loss concealment can collapse even when waveform distortion changes only slightly; a useful system must preserve linguistic content at low bitrate and under channel errors.",
    "视频传输或生成": "The issue matters because video consumes sustained bandwidth and has a strict latency budget; an error can also propagate across frames, so temporal consistency and graceful quality degradation are communication-level concerns.",
    "点云/三维场景传输": "The issue matters because XR and 3D perception sources are extremely large while interaction is delay-sensitive. Preserving geometry or task-relevant objects with fewer channel uses directly improves latency and wireless load.",
    "文本传输/机器翻译": "The issue matters because a few token errors can change the whole sentence meaning. Reliability must therefore be judged by recovered meaning or downstream language-task quality, not only by bit error rate.",
    "任务导向推理": "The issue matters because edge devices often need a timely decision rather than a faithful copy. Sending only task-sufficient information can reduce radio usage and latency, but only if the task-critical evidence survives the channel.",
    "图像传输或生成": "The issue matters because limited channel uses force the system to choose which visual information to protect. Perceptual or domain-critical structures may be more valuable than average pixel fidelity, especially at low SNR or high compression.",
    "多媒体传输": "The issue matters because a practical multimedia link must handle heterogeneous visual, audio, or text representations within one bandwidth and latency budget; a gain on only one modality may not translate to end-to-end service quality.",
    "语义感知资源分配": "The issue matters at network scale: power, bandwidth, computation, and delay are shared resources. A semantically blind scheduler can waste scarce resources without improving any user's actual task quality.",
    "语义信息度量与理论": "The issue matters because a field cannot compare systems or prove limits without a well-defined semantic objective. A defensible metric separates genuine communication gain from a change of dataset, model, or task score.",
    "通用语义通信系统": "The issue matters because semantic quality must be achieved under a real budget of channel uses, power, and delay; otherwise an apparent machine-learning gain may not translate into a communication-system gain.",
}


def infer_digital_and_channel(a: dict, theme: str) -> tuple[str, str, str, str]:
    title_abstract = (a.get("title", "") + " " + a.get("abstract", "")).lower()
    own_method = " ".join(x.get("text", "") for x in ((a.get("method_evidence") or [])[:4] + (a.get("representation_evidence") or [])[:3] + (a.get("digital_evidence") or [])[:3])).lower()
    evidence = title_abstract + " " + own_method
    if theme == "theory" and not re.search(r"vector quant|codebook|bit-level|constellation|qam|digital semantic", title_abstract):
        digital = "上层理论工作：不单独定义可发送语义格式"
        channel_class = "抽象信源—信道—语义失真模型；不对应一条具体神经收发链路"
        transmitted = "the random variable or semantic message defined by the information-theoretic model"
        decoder = "the abstract semantic decoder or decision rule in the theorem"
    elif theme == "resource" and not re.search(r"vector quant|codebook|bit-level|constellation|qam|digital semantic|deepjscc|joint source.channel", title_abstract):
        digital = "上层优化/理论工作：不单独定义可发送语义格式"
        channel_class = "沿用底层语义通信链路或抽象速率模型"
        transmitted = "the semantic rate, task utility, or channel-use variable defined by the underlying system model"
        decoder = "the receiver model assumed by the system formulation"
    elif re.search(r"hybrid digital.analog|digital.analog|hda-deepsc", title_abstract):
        digital = "混合数字—模拟语义表示"
        channel_class = "量化 bitstream 与连续模拟语义特征并行传输并在接收端融合"
        transmitted = "a digital branch carrying quantized/entropy-coded bits and an analog branch carrying continuous semantic features"
        decoder = "the demodulated/channel-decoded digital bits together with the noisy analog semantic features"
    elif re.search(r"vector quant|vq-|codebook|bit-level|bitstream|discrete denoising|quantized|digital semantic", title_abstract):
        digital = "显式数字语义表示：bit、离散 token 或码本 index"
        channel_class = "离散变量经数字链路传输；需检查残余 bit/index error"
        transmitted = "quantized bits, discrete tokens, or codebook indices rather than an unconstrained continuous latent"
        decoder = "decoded bits/indices or their noisy/soft estimates, followed by semantic dequantization and reconstruction"
    elif re.search(r"constellation|coding.modulation|qam|psk|ofdm|otfs|harq|packet-level", title_abstract):
        digital = "有限星座/标准波形接口"
        channel_class = "调制符号或编码包经过有噪声物理层"
        transmitted = "finite-constellation symbols, OFDM/OTFS resources, or protected packets"
        decoder = "equalized or soft-demodulated symbols and then the semantic representation"
    elif re.search(r"prompt|token", title_abstract):
        digital = "离散 token/文本提示；物理层通常由传统数字链路承载"
        channel_class = "语义层产生离散条件，链路层可靠性多由外部数字系统承担"
        transmitted = "a compact textual prompt or token sequence"
        decoder = "the received prompt/tokens, which condition a pretrained generative model"
    elif re.search(r"deepjscc|joint source.channel|channel symbols|end-to-end wireless|awgn|rayleigh", title_abstract) or (theme in {"jscc", "multiuser", "task", "adaptive"} and re.search(r"semantic encoder|channel encoder|jointly designed|end-to-end|channel symbols", own_method)):
        digital = "连续神经 JSCC 信道符号（不属于严格数字语义通信）"
        channel_class = "带噪连续 latent/复信道符号端到端联合训练"
        transmitted = "power-normalized real or complex-valued neural channel symbols"
        decoder = "the noisy continuous symbols after the differentiable channel or equalizer"
    else:
        digital = "语义 feature/latent；论文未给出完整量化到 bitstream 的接口"
        channel_class = "信道接口报告不足或由传统链路抽象承担"
        transmitted = "a semantic feature or latent representation whose exact bit mapping is not fully specified"
        decoder = "the recovered semantic feature assumed by the paper's receiver"
    return digital, channel_class, transmitted, decoder


def infer_layer(theme: str, digital: str, task: str) -> tuple[str, str, str, str]:
    if theme == "theory":
        return "语义信息理论与性能度量", "定义语义信息、失真、价值或可达边界，为系统比较和优化提供共同坐标。", "可以把它理解为给新的学习任务定义 loss 和 generalization bound；重点是定义是否可计算、是否与通信资源挂钩。", "审稿价值来自可比较、可优化或可证明的语义通信指标，而不是单个数据集上的网络增益。"
    if theme == "security":
        return "通信安全与隐私", "把窃听、攻击或隐私泄露加入语义链路，联合考察合法接收性能与攻击者获得的信息。", "latent 并不天然匿名；它可能仍可被反演或操控，因而要像评估对抗学习一样同时看合法端和攻击端。", "价值在于给出可靠性、保密性、语义泄露和资源开销之间的可测权衡。"
    if theme == "resource":
        return "资源分配与跨层优化", "把任务/语义质量映射为网络效用，再分配功率、带宽、算力或时延预算。", "相当于外层优化器调用多个模型的 rate-quality 曲线；问题不只是训练网络，而是决定有限资源给谁。", "价值在于回答同一无线资源下系统能服务多少用户、达到怎样的公平性、时延和能效。"
    if theme == "multiuser":
        return "多用户接入、广播或中继", "研究多个用户共享频谱、干扰或中继时，语义相关性和异构信道如何改变发送策略。", "不能把它看成简单扩大 batch size；每个接收端看到的信道和所需语义都不同，发送信号还会相互干扰。", "价值在于提升频谱复用、覆盖或公平性，并证明优于逐用户运行点到点模型。"
    if "有限星座" in digital:
        return "调制/波形与数字物理层接口", "决定语义表示如何变成有限星座、子载波、数据包或多天线信号。", "这是神经网络 bottleneck 接到实际 modem 的位置；需要明确 bit、symbol、CSI、功率和误码。", "价值在于补上可部署接口并量化频谱效率、误码、PAPR、CSI 或 MIMO 增益。"
    if theme == "digital" and "显式数字" in digital:
        return "数字语义编码与学习接收机", "在语义编码器和无线物理层之间加入量化、码本、bitstream 或学习式数字接收机。", "相当于把 autoencoder 的 latent 真正变成可发送的离散对象；必须追踪 index/bit 错误怎样影响重建。", "价值在于把连续神经仿真推进到数字协议接口，并检验有限星座、误码和接收复杂度。"
    if theme == "task" or task == "任务导向推理":
        return "任务导向联合信源信道设计", "只传下游任务所需信息，并把信道扰动纳入任务性能优化。", "类似 split inference，但中间特征必须经过带宽受限且有噪声的无线信道，任务准确率是最终目标。", "价值在于用更少信道使用完成相同任务，并降低端到端时延和设备能耗。"
    return "联合信源信道编码（JSCC）与语义信源编码", "在一个系统中共同设计压缩、语义保真和抗信道噪声机制。", "可把它看成带真实信道瓶颈的 autoencoder；中间表示的维度、功率和噪声位置都是通信约束。", "价值要由相同带宽、功率和信道条件下的质量、鲁棒性或时延收益来证明。"


def evidence_pages(a: dict, keys: tuple[str, ...], default: list[int]) -> list[int]:
    pages = []
    for key in keys:
        value = a.get(key)
        if isinstance(value, list):
            pages.extend(int(x.get("page", 0)) for x in value if x.get("page"))
        elif isinstance(value, dict):
            if value.get("page"):
                pages.append(int(value["page"]))
            else:
                pages.extend(int(x.get("page", 0)) for x in value.values() if isinstance(x, dict) and x.get("page"))
    return sorted(set(pages))[:3] or default


def best_setup_claim(a: dict) -> str:
    datasets = compact_list(a.get("datasets"), "the source/task dataset stated in the paper")
    baselines = compact_list(a.get("baselines"), "the paper's stated reference systems")
    metrics = compact_list(a.get("metrics"), "the task or reconstruction metric stated in the paper")
    channel = compact_list(a.get("channels") or a.get("channel_models"), "the channel model stated in the experiment")
    conditions = []
    for item in (a.get("channel_evidence") or []) + (a.get("overhead_evidence") or []):
        claim = clean_claim(item.get("text", ""))
        if re.search(r"SNR\s*[=]|at\s+SNR|CBR\s*[=]|CR\s*[=]|bandwidth ratio\s*[=]|BER\s*[=]", claim, re.I) and not re.search(r"Fig\.|Table|IEEE|Member,|Fellow,", claim, re.I):
            conditions.append(claim)
    condition = conditions[0] if conditions else "Exact SNR, bandwidth ratio, and power constraints must be read together with the corresponding result figure."
    return (
        f"The experiments use {datasets}; compare against {baselines}; evaluate with {metrics}; "
        f"and use {channel}. A representative reported operating condition is: {condition}"
    )


def best_result_claim(a: dict, rhet: dict) -> str:
    if rhet.get("result") and "intended to test" not in rhet["result"]:
        return rhet["result"]
    claims = [clean_claim(x.get("text", "")) for x in (a.get("experiment_evidence") or [])]
    claims = [x for x in claims if re.search(r"outperform|improv|gain|achiev|degrad|robust|save|reduce|from (these|the) results|results (show|demonstrate)", x, re.I) and not re.search(r"IEEE|Member,|Fellow,|Abstract|Fig\.|Table\s+[IVX]", x, re.I)]
    if claims:
        return claims[0]
    return "The experiments compare the proposed design with the stated baselines under matched resource and channel conditions, testing both end quality and robustness rather than only training loss."


def compose_english(a: dict) -> tuple[dict, dict]:
    rhet = rhetorical_abstract(a)
    task, input_desc, output_desc = infer_task(a)
    theme = infer_theme(a)
    digital, channel_class, transmitted, decoder = infer_digital_and_channel(a, theme)
    layer, layer_exp, beginner, reviewer = infer_layer(theme, digital, task)
    method_name = a.get("title", "the proposed method")
    problem = specific_problem(theme, rhet["problem"], task)
    background = rhet["background"] or PROGRESS_FALLBACK[theme]
    if len(background) < 35 or re.search(r"IEEE|Member,|Fellow,|Abstract", background, re.I):
        background = PROGRESS_FALLBACK[theme]
    progress = f"Before this paper, the relevant line of work had established that {background}"
    importance = IMPORTANCE[task]
    proposal = f"The paper therefore develops {method_name}. Its concrete design is summarized as follows: {rhet['proposal']}"
    method_mechanism = best_mechanism_claim(a, rhet)
    prior = (
        f"{specific_prior(theme, problem)} More concretely, the earlier pipeline lacks the paper-specific mechanism "
        f"later introduced here: {method_mechanism}"
    )
    mechanism_effect = {
        "theory": "The proposed definition makes the semantic objective explicit and therefore measurable or optimizable.",
        "security": "The threat or privacy variable now enters training or optimization together with legitimate-receiver quality.",
        "resource": "Semantic importance now changes the allocation decision instead of being evaluated only after resources are fixed.",
        "multiuser": "Cross-user correlation and heterogeneous links now shape a joint transmitted representation rather than duplicated independent messages.",
        "digital": "The learned latent is forced through the stated discrete or hybrid interface, so the receiver is designed for the representation it will actually observe.",
        "generative": "The transmitter sends a compact condition and the receiver prior supplies predictable detail, reducing the information that must cross the channel.",
        "task": "Task-relevant evidence directly controls the bottleneck and loss, so radio resources are not spent equally on irrelevant source detail.",
        "adaptive": "The representation or protection pattern can change with the operating condition instead of remaining fixed after training.",
        "jscc": "Semantic fidelity and channel robustness are optimized in the same path, so the bottleneck is shaped for the actual noisy link.",
    }[theme]
    mechanism = f"The causal link is that {method_mechanism} {mechanism_effect}"
    result_claim = best_result_claim(a, rhet)
    claim = f"The paper tests whether that causal mechanism survives a fair communication comparison. The reported evidence is: {result_claim}"
    method_detail = rhet["proposal"] if norm_space(rhet["proposal"]).lower() == norm_space(method_mechanism).lower() else f"{rhet['proposal']} {method_mechanism}"
    method = f"The system is an end-to-end communication link for {task}. {method_detail} The key is how the learned representation is connected to the stated channel and resource constraint, not the mere use of a larger neural network."
    setup = best_setup_claim(a)
    result = result_claim
    representation = f"The transmitter sends {transmitted}. This is classified as: {digital}. The distinction is important because a continuous neural symbol, a hard codebook index, and a channel-decoded bitstream fail in different ways."
    overhead = "The communication cost is interpreted using the paper's stated channel uses, compression/bandwidth ratio, bit rate, code rate, token count, or allocated wireless resources. When the paper does not report a complete bit-level interface, the report does not invent a bitrate from latent dimension alone."
    channel = f"In the proposed transmission path, the channel is handled as follows: {channel_class}. An LDPC, QAM, or other conventional scheme mentioned only as a comparison baseline is not used to classify the proposed receiver."
    decoder_input = f"The receiver actually starts from {decoder}. It then reconstructs {output_desc}. This statement makes clear whether the learned decoder sees noisy continuous symbols, erroneous discrete variables, soft information, or an already channel-decoded representation."
    limitation = {
        "theory": "该定义是否能在真实高维信源上计算、能否跨任务预测系统收益仍需验证；形式化指标本身不等于可部署的无线增益。",
        "security": "威胁模型和攻击者知识通常是预先限定的；对自适应攻击、域外数据和真实无线实现的安全结论仍不能直接外推。",
        "resource": "优化依赖估计的 rate-quality 曲线和信道状态；信道估计误差、非平稳业务以及端到端推理开销仍是落地限制。",
        "multiuser": "证据多来自固定用户数与信道模型的仿真；扩展性、反馈开销、同步和与真实调度器的集成仍未充分回答。",
        "digital": "虽已有数字接口，残余 bit/index 错误、有限码长开销、同步以及完整 PHY 兼容性仍需进一步验证。",
        "generative": "生成先验可节省传输，但幻觉、域偏移、共享模型成本、推理时延和语义忠实度仍是核心风险。",
        "task": "收益与任务和数据集绑定；对未知任务、分布偏移、置信度校准以及稀有关键样本的失败仍需更强证据。",
        "adaptive": "适配只在有限的带宽/信道范围内验证；控制信令、在线稳定性及超出训练范围后的外推仍不确定。",
        "jscc": "收益主要在基准数据与仿真信道上建立；若论文没有额外实验证据，量化、分包、标准兼容和空口验证仍不完整。",
    }[theme]
    pages_intro = evidence_pages(a, ("method_evidence",), [1])
    pages_problem = evidence_pages(a, ("evidence",), [1])
    pages_method = evidence_pages(a, ("method_evidence", "representation_evidence"), [1, 2])
    pages_digital = evidence_pages(a, ("digital_evidence", "overhead_evidence"), pages_method)
    pages_channel = evidence_pages(a, ("channel_evidence",), pages_method)
    pages_result = evidence_pages(a, ("experiment_evidence",), [max(1, int(a.get("pdf_pages") or 1))])
    fields = {
        "motivation.progress": progress,
        "motivation.problem": problem,
        "motivation.prior_limit": prior,
        "motivation.importance": importance,
        "motivation.proposal": proposal,
        "motivation.mechanism": mechanism,
        "motivation.claim": claim,
        "method_summary": method,
        "flow.input": f"The source is {input_desc}.",
        "flow.encoder": f"The sender applies the paper's semantic/source-channel encoder: {method_mechanism}",
        "flow.transmitted": f"The transmitted object is {transmitted}.",
        "flow.channel": f"The transmission follows the channel/resource model evaluated in the paper; its treatment is summarized as {channel_class}.",
        "flow.receiver": f"The receiver begins with {decoder} and applies the proposed decoder, inference model, or generator.",
        "flow.output": f"The final output is {output_desc}.",
        "representation_summary": representation,
        "overhead_summary": overhead,
        "channel_summary": channel,
        "decoder_input_summary": decoder_input,
        "experiment_setup_summary": setup,
        "experiment_result_summary": result,
    }
    meta = {
        "task_type": task, "theme": theme, "digitalization_class": digital,
        "channel_handling_class": channel_class, "communication_layer": layer,
        "layer_explanation": layer_exp, "beginner_explanation": beginner,
        "reviewer_value": reviewer, "limitations": limitation,
        "pages": {
            "intro": pages_intro, "problem": pages_problem, "method": pages_method,
            "digital": pages_digital, "channel": pages_channel, "result": pages_result,
        },
    }
    return fields, meta


class EdgeTranslator:
    def __init__(self) -> None:
        self.token = ""

    def refresh(self) -> None:
        last_error = None
        for attempt in range(5):
            try:
                request = urllib.request.Request(
                    "https://edge.microsoft.com/translate/auth",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(request, timeout=30) as response:
                    self.token = response.read().decode("utf-8")
                return
            except Exception as exc:
                last_error = exc
                time.sleep(1.5 * (attempt + 1))
        raise last_error

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not self.token:
            self.refresh()
        payload = json.dumps([{"Text": t} for t in texts], ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            "https://api-edge.cognitive.microsofttranslator.com/translate?api-version=3.0&from=en&to=zh-Hans",
            data=payload,
            method="POST",
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json; charset=UTF-8"},
        )
        last_error = None
        for attempt in range(5):
            try:
                request.headers["Authorization"] = f"Bearer {self.token}"
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except Exception as exc:
                last_error = exc
                self.refresh()
                time.sleep(1.5 * (attempt + 1))
        else:
            raise last_error
        return [item["translations"][0]["text"] for item in data]


def polish_zh(text: str) -> str:
    replacements = {
        "通道": "信道", "联合源信道": "联合信源信道", "源信道": "信源信道",
        "编码译码器": "编解码器", "发件人": "发送端", "接收器": "接收端",
        "语义通讯": "语义通信", "位流": "bitstream", "比特流": "bitstream",
        "码本索引": "码本 index", "信道使用情况": "信道使用次数",
        "通信管道": "通信链路", "语义传播": "语义通信", "语义交流": "语义通信",
        "bit或符号": "比特或符号", "bito r符号": "比特或符号",
        "本信提出": "论文提出", "这封信提出": "论文提出", "本函提出": "论文提出",
        "代码分类为": "表示归类为", "驱动申请": "对应应用", "损失中": "训练目标中",
        "微分信道": "可微信道模型", "重建重建": "重建", "无线电使用": "无线资源占用",
        "象征性错误": "少量符号错误", "来源数据": "信源数据", "信源和信道匹配": "资源与信道匹配",
        "深度联合信信源信道编码": "深度联合信源信道编码", "公平的交流比较": "公平的通信比较",
        "这里稍后介绍": "本文引入", "在此稍后介绍": "本文引入", "具体而言，早期的管道": "具体而言，已有链路",
        "专用纸质机制": "论文特有机制", "专用论文机制": "论文特有机制", "后来这里介绍的": "本文随后引入的",
        "后来这里引入的": "本文随后引入的", "早期的流水线": "已有链路", "早期流水线": "已有链路",
        "纸质机制": "论文机制", "本信中": "论文中", "这封信中": "论文中",
        "专用纸张机制": "论文特有机制", "专用纸机制": "论文特有机制", "论文专属机制": "论文特有机制",
        "这里后来引入的": "本文随后引入的", "几个少量符号错误": "少量符号错误",
        "联合信信源信道": "联合信源信道",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()


def translate_fields(items: list[tuple[dict, dict, dict]]) -> None:
    translator = EdgeTranslator()
    pending: list[tuple[dict, str, str]] = []
    for record, fields, _ in items:
        for key, value in fields.items():
            pending.append((record, key, value))
    for start in range(0, len(pending), 40):
        batch = pending[start:start + 40]
        translated = translator.translate_batch([x[2] for x in batch])
        for (record, key, _), zh in zip(batch, translated):
            record.setdefault("_translated", {})[key] = polish_zh(zh)
        print(f"translated {min(start + 40, len(pending))}/{len(pending)}")
        time.sleep(0.25)


def cited(text: str, *pages: int) -> dict:
    return {"text": text, "pages": list(pages)}


# Papers called out during visual QA receive hand-written, page-addressable
# synthesis.  These overrides are deliberately kept in the generator so a
# future rebuild cannot silently restore the defective extracted prose.
MANUAL_OVERRIDES = {
    "domain-knowledge-driven-semantic-communication-for-image-transmission-over-wireless-channels-2022": {
        "task_type": "医学视网膜图像传输与重建",
        "theme": "jscc",
        "digitalization_class": "连续神经 JSCC 信道符号（不属于严格数字语义通信）",
        "channel_handling_class": "连续复数语义符号经 AWGN/Rayleigh 信道，接收端直接从带噪符号重建",
        "communication_layer": "联合信源信道编码（JSCC）与领域语义信源编码",
        "layer_explanation": "工作位于图像信源表示与物理信道之间：它改变发送端提取什么特征，并把这些特征直接映射成受功率约束的复信道符号。",
        "beginner_explanation": "可以把它看成一个带无线噪声瓶颈的双输入 autoencoder：除原始视网膜图像外，再把血管分割图作为医学先验输入。它不是把分割图另存成一个可靠 bitstream。",
        "reviewer_value": "在相同压缩比和信道条件下，若能优先保住血管等医学 ROI，就比只提高平均像素质量更符合业务目标；这体现的是“有限信道资源应该保护什么”的通信价值。",
        "limitations": "领域知识依赖额外的血管分割器和 DRIVE 上训练的 U-Net；实验只覆盖视网膜图像与仿真 AWGN/Rayleigh 信道，尚不能证明对其他医学概念、分割错误或真实空口同样有效。",
        "motivation": {
            "progress": cited("此前的神经语义图像链路已经能通过端到端压缩去除像素和信号层冗余，并在有限带宽下直接传输连续语义特征。", 1),
            "problem": cited("只沿图像像素路径学习时，模型并不知道哪些结构具有医学意义；它可能重建出视觉上合理的眼底图，却模糊或破坏真正决定诊断价值的血管区域。", 1, 2),
            "prior_limit": cited("给普通 JSCC 增大网络或继续优化平均重建损失，仍不会自动引入“血管是关键区域”这一领域概念。缺失的是进入编码输入和训练路径的显式领域知识，而不是又一个通用卷积层。", 1, 2),
            "importance": cited("无线带宽越紧、SNR 越低，系统越必须选择优先保留哪些内容。医学图像中，ROI 的结构正确性比背景像素的平均误差更重要，因此这是资源优先级问题而不只是图像美化。", 1, 4),
            "proposal": cited("DKSC 为原图和医学 ROI 建立两条并行语义路径：原图路径提取信息层特征，血管分割路径提取概念层特征；发送前将两路特征拼接，接收端再联合恢复视网膜图像。", 2, 3),
            "mechanism": cited("因为血管分割特征在进入信道前就与图像特征合并，有限维度和训练梯度会显式为医学结构分配表示能力；端到端加入 AWGN/Rayleigh 噪声后，接收端同时学习从受损的两类连续特征恢复图像。它由此正面对应“普通像素路径忽略关键概念”的问题。", 2, 3, 4),
            "claim": cited("作者要验证的不是“双路径一定更深”，而是在相同压缩比和信道条件下，引入真实领域知识能否比普通 JSCC、JPEG+LDPC 以及去掉真实 ROI 的 DKSC-variant 更好地恢复医学结构，并保持随 SNR 变化的鲁棒性。", 4, 5),
        },
        "method_summary": cited("输入是视网膜 RGB 图像及其由 U-Net 得到的血管分割图。两套编码分支分别提取图像语义和 MedROI 语义，得到特征 Y 与 Y′；二者拼接为 Ye，经功率约束后作为复信道符号发送。AWGN 或 Rayleigh 信道产生退化信号，双路径解码器利用两类特征联合重建原图。", 2, 3, 4),
        "system_flow": {
            "input": cited("原始视网膜图像，以及由领域知识提取器产生的血管分割图（MedROI）。", 2),
            "encoder": cited("图像路径和 MedROI 路径分别编码，末端将 Y 与 Y′ 拼接为联合语义表示 Ye。", 2, 3),
            "transmitted": cited("经功率归一化的连续复数张量 Ye∈C^(l×m×k)；论文没有把它量化成 VQ index 或 bitstream。", 2),
            "channel": cited("训练和测试显式加入 AWGN 与 Rayleigh 衰落，并改变测试 SNR 与压缩比。", 2, 4),
            "receiver": cited("接收端取得带噪连续符号，双分支解码后融合信息层与概念层特征。", 2, 3),
            "output": cited("重建的视网膜图像，重点观察血管 ROI 和整体感知质量。", 4, 5),
        },
        "representation_summary": cited("DKSC 发送的是连续神经信道符号，不是数字化语义 token。码本大小、index bit 数和 BER 因而不适用；若日后接入真实数字 PHY，还需另外设计量化、调制和残余误码处理。", 2, 3),
        "overhead_summary": cited("论文以带宽压缩比 N/K（文中也用 CR 展示不同压缩设置）衡量开销，并通过两条路径的信道数 k1、k2 分配表示容量。Table II 显示总容量固定时比较不同分配，k1=k2=32 的结果最好；这说明开销是连续符号维度分配，而不是可直接换算的 bit 数。", 2, 4, 5),
        "channel_summary": cited("所提 DKSC 在可微 AWGN/Rayleigh 层上端到端训练。JPEG+LDPC 只是分离式 baseline，不能据此把 DKSC 归为“传统信道编码后的数字链路”。", 4),
        "decoder_input_summary": cited("语义解码器直接看到的是受噪声或衰落影响的连续复符号；不存在先做 LDPC 译码再得到无误 VQ index 的步骤，因此论文也没有处理 index 跳变。", 2, 4),
        "experiment_setup_summary": cited("医学图像来自 Kaggle 视网膜数据，血管分割器在 DRIVE 上训练；比较普通 JSCC 与 JPEG+LDPC，信道为 AWGN/Rayleigh，改变 SNR 和压缩比，指标为 SSIM 与 LPIPS。", 3, 4),
        "experiment_result_summary": cited("DKSC 在所测信道与压缩设置下优于普通 JSCC 和分离式方案；低 SNR 时 JPEG+LDPC 出现 cliff effect。去掉真实领域知识的 DKSC-variant 虽略好于 JSCC，却在 LPIPS 上明显落后于完整 DKSC，支持“收益来自 MedROI 语义而不只是双路径容量”的解释。", 4, 5),
    },
    "nonlinear-transform-source-channel-coding-for-semantic-communications-2022": {
        "task_type": "图像传输与感知重建",
        "theme": "adaptive",
        "digitalization_class": "主干为连续 NTSCC 信道符号；量化 hyperprior 作为可靠数字侧信息传输",
        "channel_handling_class": "内容自适应的连续 JSCC 主干经 AWGN；量化侧信息由传统可靠信道编码保护",
        "communication_layer": "非线性变换信源编码与联合信源信道编码（NTSCC）",
        "layer_explanation": "它把 learned image compression 的非线性分析变换、熵模型和 rate-distortion 目标接到 DeepJSCC 主干，决定不同图像内容应占用多少信道符号。",
        "beginner_explanation": "可类比带 hyperprior 的 learned image codec，但主 latent 不做熵编码后发 bit，而是由神经 JSCC 直接映射成连续信道符号；熵模型主要用来估计每个 latent 的信息量并分配带宽。",
        "reviewer_value": "价值在于同一系统同时获得内容自适应码率、感知 rate-distortion 优化和 JSCC 的平滑退化，补上固定 CBR DeepJSCC 在高分辨率和高码率区编码增益不足的问题。",
        "limitations": "主干仍是仿真 AWGN 上的连续符号接口；hyperprior 的可靠数字传输假设了容量接近码或 LDPC/Polar，但其有限码长开销、反馈和真实调制实现没有完整计入。",
        "motivation": {
            "progress": cited("传统分离式图像传输已拥有成熟的压缩与纠错，DeepJSCC 又证明了端到端联合优化可在低 SNR 下避免突然崩溃；非线性变换编码则能用 hyperprior 学到图像 latent 的概率结构。", 1, 2, 3),
            "problem": cited("标准 DeepJSCC 通常用固定维度信道表示，不能根据每幅图像及其局部 latent 的信息量灵活分配信道次数；随着 CBR 或图像分辨率提高，其性能曲线容易变平，编码增益追不上强分离式方案。", 1, 2),
            "prior_limit": cited("只加深 DeepJSCC 网络仍缺少可解释的内容码率模型；只采用 learned compression 的量化与熵编码，又会把主链路变成对残余 bit 错误敏感的分离系统。需要的是用概率模型指导 JSCC 的连续带宽分配。", 2, 3),
            "importance": cited("无线图像的内容复杂度并不相同。固定 CBR 会给简单区域浪费符号、给复杂区域分配不足；这直接限制频谱效率，也使模型难以跨 CIFAR10、Kodak、CLIC 等分辨率工作。", 1, 11),
            "proposal": cited("NTSCC 先用非线性分析变换得到 latent y，并学习 hyperprior/条件熵模型估计各维信息量；随后依据该信息量给 latent 分配可变数量的 JSCC 信道符号，接收端通过相应解码器和合成变换恢复图像。", 2, 3, 5, 7),
            "mechanism": cited("熵模型把“哪部分内容更难压缩”变成逐 latent 的码率代价，adaptive-rate JSCC 再把这一代价转换为实际信道带宽；因此符号预算随内容变化，同时主 latent 保留连续 JSCC 的抗噪声与平滑退化。该机制正面解决固定 CBR 和源分布适配不足。", 5, 7),
            "claim": cited("作者要证明：在相同 CBR/SNR 下，内容感知的 NTSCC 能优于固定码率 DeepJSCC 和实际 BPG+LDPC，并接近理想 BPG+Capacity；当测试 SNR 低于训练点时仍像 DeepJSCC 一样平滑退化。", 10, 11, 12),
        },
        "method_summary": cited("发送端依次执行非线性分析变换 ga、hyperprior 分析 ha、条件熵估计和深度 JSCC 编码 fe。量化 hyperprior z 用于预测 y 的分布与带宽需求，y 则按估计信息量变成可变长度连续信道码字 s。AWGN 后，JSCC 解码与非线性合成变换恢复图像。训练目标联合考虑端到端失真、感知质量和信道带宽代价。", 3, 5, 7),
        "system_flow": {
            "input": cited("不同分辨率的自然图像。", 10, 11),
            "encoder": cited("非线性分析变换提取 y，hyperprior/条件熵模型估计其概率，再由 adaptive-rate DeepJSCC 产生信道码字。", 3, 5, 7),
            "transmitted": cited("主链路是按内容分配长度的连续实/复信道符号 s；另有量化 hyperprior 侧信息。", 3, 5, 7),
            "channel": cited("主链路通过 AWGN；侧信息假设由 LDPC、Polar 等高可靠数字信道编码保护。", 3, 6, 7),
            "receiver": cited("接收端先从带噪连续码字恢复 latent，再结合可靠收到的 hyperprior 完成合成变换。", 5, 7),
            "output": cited("重建图像，并以 PSNR/MS-SSIM 或感知失真和带宽成本评价。", 10, 11),
        },
        "representation_summary": cited("论文包含量化 latent 的概率建模，但不能简单归类为“整条链路发送 VQ index”。主语义 latent y 由 DeepJSCC 直接变成连续信道码字；被量化并可靠数字传输的是较小的 hyperprior/side information。", 3, 5, 7),
        "overhead_summary": cited("CBR 定义为 R=k/m，其中 m 是源维度、k 是主链路信道使用次数。条件熵项 −log P(y_i|z) 用于估计各 latent 的信息量并决定分配的 k；侧信息还产生额外开销，不能在比较时忽略。", 1, 5, 7),
        "channel_summary": cited("主码字在训练中显式加入 AWGN，因而网络学习从连续受损表示恢复；BPG+LDPC 是 baseline。量化侧信息则单独假设由容量接近码、LDPC 或 Polar 可靠保护，形成混合接口。", 3, 6, 7, 10),
        "decoder_input_summary": cited("主解码器接收带 AWGN 的连续码字 ŝ，而不是有误 VQ index；同时使用经过传统信道译码的 hyperprior。论文因此处理连续主 latent 的噪声，但没有把主表示的 bit/index 跳变作为核心误差模型。", 1, 5, 7),
        "experiment_setup_summary": cited("数据集覆盖 CIFAR10、Kodak 与 CLIC2021；比较 DeepJSCC、BPG+LDPC、BPG+Capacity、NTC+LDPC/Capacity，在 AWGN 下扫描 CBR 与 SNR，并以 PSNR 等 rate-distortion 指标评价。", 10, 11),
        "experiment_result_summary": cited("NTSCC 在三个数据集的多数 CBR 上优于固定码率 DeepJSCC，图像分辨率和 CBR 越高差距越明显；它超过实际 BPG+LDPC，并与理想 BPG+Capacity 具有竞争力。SNR 失配时 NTSCC 平滑退化，而 BPG+LDPC 在译码门限附近出现 cliff effect。", 11, 12),
    },
    "token-communications-a-large-model-driven-framework-for-cross-modal-context-aware-semantic-communications-2025": {
        "motivation": {
            "progress": cited("大模型已能把图像、文本等不同模态映射到 token，并利用上下文生成缺失内容；这使“发送紧凑 token、接收端借助模型补全”成为新的语义通信接口。", 1, 2),
            "problem": cited("现有生成式语义通信通常分别处理各模态，尚未系统利用跨模态 token 之间的上下文冗余；直接发送全部 token 又会抵消大模型本应带来的带宽收益。", 1, 2),
            "prior_limit": cited("普通压缩只看单个模态内部的统计冗余，传统跨模态融合又往往发生在接收后，二者都不能在发送前判断哪些 token 已可由另一模态和上下文预测。", 2, 3),
            "importance": cited("token 是大模型应用的实际输入输出单位；若无线链路仍按原始媒体分别传输，模型共享知识无法转化为时延和频谱收益。", 2, 4),
            "proposal": cited("TokCom 用生成基础模型/多模态大模型统一处理跨模态 token，在发送端选择上下文不可预测的 token，并在接收端结合已收 token 与本地模型恢复或生成所需内容。", 2, 3, 4),
            "mechanism": cited("跨模态上下文把一部分待传 token 变成可由接收端先验预测的信息；只发送条件性更强、不可替代的 token，理论上就能降低链路负载。该作用机制是“利用条件冗余”，并非简单扩大语言模型。", 3, 4),
            "claim": cited("论文通过典型图像语义通信示例验证：利用 token 间上下文可以减少发送量并提高带宽效率，同时讨论这种接口向无线协议各层扩展时的复杂度与可靠性问题。", 3, 4),
        },
    },
}


def merge_dict(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def build_record(original: dict, meta: dict) -> dict:
    a = dict(original)
    t = a.pop("_translated")
    pages = meta.pop("pages")
    a.update(meta)
    a["analysis_version"] = "fulltext_synthesis_v2_2026-07-16"
    a["analysis_status"] = "fulltext_synthesized_v2"
    a["motivation"] = {
        "progress": {"text": t["motivation.progress"], "pages": pages["intro"]},
        "problem": {"text": t["motivation.problem"], "pages": pages["problem"]},
        "prior_limit": {"text": t["motivation.prior_limit"], "pages": pages["problem"]},
        "importance": {"text": t["motivation.importance"], "pages": pages["intro"]},
        "proposal": {"text": t["motivation.proposal"], "pages": pages["intro"]},
        "mechanism": {"text": t["motivation.mechanism"], "pages": pages["method"]},
        "claim": {"text": t["motivation.claim"], "pages": pages["result"]},
    }
    a["method_summary"] = {"text": t["method_summary"], "pages": pages["method"]}
    a["system_flow"] = {
        key: {"text": t[f"flow.{key}"], "pages": pages["method"] if key not in {"channel"} else pages["channel"]}
        for key in ("input", "encoder", "transmitted", "channel", "receiver", "output")
    }
    a["representation_summary"] = {"text": t["representation_summary"], "pages": pages["digital"]}
    a["overhead_summary"] = {"text": t["overhead_summary"], "pages": pages["digital"]}
    a["channel_summary"] = {"text": t["channel_summary"], "pages": pages["channel"]}
    a["decoder_input_summary"] = {"text": t["decoder_input_summary"], "pages": pages["channel"]}
    a["experiment_setup_summary"] = {"text": t["experiment_setup_summary"], "pages": pages["channel"]}
    a["experiment_result_summary"] = {"text": t["experiment_result_summary"], "pages": pages["result"]}
    for old in ("evidence", "method_evidence", "representation_evidence", "digital_evidence", "overhead_evidence", "channel_evidence", "experiment_evidence", "digitalization_judgment", "channel_handling_judgment"):
        a.pop(old, None)
    return merge_dict(a, MANUAL_OVERRIDES.get(a.get("citation_key", ""), {}))


def process(team_keys: list[str]) -> None:
    work: list[tuple[dict, dict, dict, Path]] = []
    blocked: list[tuple[dict, Path]] = []
    for key in team_keys:
        root = ROOT / "literature" / TEAM_DIRS[key]
        source = root / "notes" / "structured_analysis.jsonl"
        for line in source.read_text(encoding="utf-8").splitlines():
            a = json.loads(line)
            if a.get("analysis_status") == "blocked_missing_fulltext":
                blocked.append((a, root))
                continue
            fields, meta = compose_english(a)
            work.append((a, fields, meta, root))
    translate_fields([(a, f, m) for a, f, m, _ in work])
    by_root: dict[Path, list[dict]] = {ROOT / "literature" / TEAM_DIRS[k]: [] for k in team_keys}
    for a, _, meta, root in work:
        by_root[root].append(build_record(a, meta))
    for a, root in blocked:
        by_root[root].append(a)
    for root, rows in by_root.items():
        order = {json.loads(line)["citation_key"]: i for i, line in enumerate((root / "notes" / "structured_analysis.jsonl").read_text(encoding="utf-8").splitlines())}
        rows.sort(key=lambda x: order[x["citation_key"]])
        target = root / "notes" / "synthesized_analysis.jsonl"
        target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        print(f"wrote {len(rows)} records -> {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teams", default="all")
    args = parser.parse_args()
    keys = list(TEAM_DIRS) if args.teams == "all" else [x.strip() for x in args.teams.split(",") if x.strip()]
    process(keys)


if __name__ == "__main__":
    main()
