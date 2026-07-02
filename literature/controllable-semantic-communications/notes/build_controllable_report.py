from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIR = ROOT / "papers"
ASSETS_DIR = ROOT / "assets"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug(value: str) -> str:
    keep = []
    last_dash = False
    for ch in value.lower():
        if ch.isalnum():
            keep.append(ch)
            last_dash = False
        elif not last_dash:
            keep.append("-")
            last_dash = True
    return "".join(keep).strip("-")


def p(
    *,
    year: int,
    title: str,
    authors: str,
    venue: str,
    source: str,
    identifier: str,
    source_url: str,
    pdf: str,
    asset_prefix: str,
    mode: str,
    task: str,
    control_axis: str,
    control_signal: str,
    flexibility: str,
    intro: str,
    method: str,
    experiment: str,
    channel: str,
    result: str,
    limitation: str,
    not_pure: str,
    core_level: str = "核心",
) -> dict:
    return {
        "year": year,
        "title": title,
        "authors": authors,
        "venue": venue,
        "source": source,
        "identifier": identifier,
        "source_url": source_url,
        "pdf": pdf,
        "asset_prefix": asset_prefix,
        "mode": mode,
        "task": task,
        "control_axis": control_axis,
        "control_signal": control_signal,
        "flexibility": flexibility,
        "intro": intro,
        "method": method,
        "experiment": experiment,
        "channel": channel,
        "result": result,
        "limitation": limitation,
        "not_pure": not_pure,
        "core_level": core_level,
    }


PAPERS = [
    p(
        year=2021,
        title="Semantic Communication With Adaptive Universal Transformer",
        authors="Qing Zhou, Rongpeng Li, Zhifeng Zhao, Chenghui Peng, Hang Zhang",
        venue="IEEE Wireless Communications Letters, 2022; arXiv preprint posted in 2021",
        source="IEEE / arXiv",
        identifier="arXiv:2108.09119; DOI 10.1109/LWC.2021.3132067",
        source_url="https://arxiv.org/abs/2108.09119",
        pdf="papers/2021_Zhou_Semantic_Communication_With_Adaptive_Universal_Transformer.pdf",
        asset_prefix="2021_zhou_semantic_communication_with_adaptive_universal_transformer",
        mode="模拟式文本 SemCom",
        task="文本语义传输 / 机器翻译式句子恢复",
        control_axis="语义复杂度与信道条件共同驱动的 adaptive circulation",
        control_signal="句子语义差异、SNR、训练中的停止概率 / remainder",
        flexibility="主要不是改变物理 payload 长度，而是改变 Transformer 循环计算深度；它是“可控 SemCom”的早期形态，说明固定网络深度无法同等处理所有句子。",
        intro="论文从 DeepSC 已能端到端学习语义编码讲起，但指出固定 Transformer 结构把不同句子、不同信道状态都送入同一计算路径，不能体现句子语义复杂度差异。作者把 Universal Transformer 的 adaptive computation 思路引入语义通信，让系统在需要时多循环、在简单样本上少循环，并希望证明低 SNR 下自适应结构比固定 DNN 更稳。",
        method="发送端使用语义编码器和信道编码器，接收端使用信道解码器和 Transformer 解码器。Adaptive UT 在中间层引入循环和 halting/remainder 机制，每个输入可根据当前表示决定是否继续迭代。训练损失以交叉熵为主，目标是保持原句与恢复句之间的语义一致。可控点在于计算路径和语义抽取强度，而不是传统意义的固定长度源编码。",
        experiment="数据集使用 Europarl 语料；baseline 包括传统 Huffman/RS、Huffman/Turbo 以及固定 Transformer / DNN 式语义通信；指标包括 BLEU、SER 和不同 SNR 下的语义恢复质量。",
        channel="论文显式测试 AWGN 与 Rayleigh fading。信道作用在连续信道符号上，解码器接收带噪连续表示；没有离散 index/bit payload，因此不存在 VQ index 跳变问题。",
        result="结果显示在低 SNR 区域 adaptive UT 相对固定结构有更好 BLEU/SER，且训练 SNR 选择会影响跨 SNR 泛化。它证明“一个固定语义处理深度”不是最优。",
        limitation="它对“传输符号数可变”的支持较弱，更多是可变计算深度和语义处理强度；仍属于模拟式 DeepSC 范式，和后续 rate-adaptive / variable-length 方法相比 payload 控制不够直接。",
        not_pure="不是单独建立资源分配优化问题，而是在语义编码网络内部加入 adaptive computation 机制。",
        core_level="相关核心",
    ),
    p(
        year=2022,
        title="Adaptive Bit Rate Control in Semantic Communication With Incremental Knowledge-Based HARQ",
        authors="Qing Zhou, Rongpeng Li, Zhifeng Zhao, Chenghui Peng, Hang Zhang",
        venue="IEEE Open Journal of the Communications Society, 2022",
        source="IEEE / arXiv",
        identifier="arXiv:2203.06634; DOI 10.1109/OJCOMS.2022.3189023",
        source_url="https://arxiv.org/abs/2203.06634",
        pdf="papers/2022_Zhou_Adaptive_Bit_Rate_Control_IK_HARQ.pdf",
        asset_prefix="2022_zhou_adaptive_bit_rate_control_ik_harq",
        mode="数字式文本 SemCom",
        task="文本语义传输，带 HARQ 的渐进语义补充",
        control_axis="句子级 bit rate 与增量重传次数",
        control_signal="信道条件、语义恢复反馈、策略网络输出的编码 bit 长度",
        flexibility="同一句文本不是固定映射成固定 bit 长度；系统可先发较短语义编码，失败或语义不足时再通过 IK-HARQ 发增量知识。",
        intro="传统 HARQ 以 bit 正确为目标，语义通信则更关心恢复意义。论文指出固定 bit 长度语义编码在好信道浪费、坏信道不足；直接重复发送也忽视已恢复知识。作者提出多 bit-length 语义编码和 incremental knowledge HARQ，让编码率和重传内容随信道/语义反馈调整。",
        method="语义编码器产生不同长度的语义 bit 表示；policy network 在每轮选择编码 bit rate。接收端通过语义解码和 denoiser 恢复文本，反馈机制判断是否需要追加知识。IK-HARQ 的关键是后续重传不是简单重复，而是补充此前未可靠恢复的语义增量。",
        experiment="文本数据集以 Europarl 类机器翻译语料为主；baseline 包括固定长度 DeepSC、传统编码调制、普通 HARQ / incremental redundancy HARQ；指标为 BLEU、语义相似度、传输 bit 数和重传次数。",
        channel="论文考虑有噪信道下的 bit/语义编码错误，并通过 denoising 与 HARQ 反馈处理。decoder 得到的是经信道污染后再处理的语义表示，不是默认无误 bitstream。",
        result="结果显示 adaptive bit rate 可在不同 SNR 下减少冗余 bit，同时 IK-HARQ 在低 SNR 下提升语义恢复质量。",
        limitation="适用对象主要是文本，语义反馈与增量知识的定义依赖特定语义编码器；对现代 LLM token 级通信的适配仍需要重新设计。",
        not_pure="核心贡献是多长度语义编码器、策略网络和 IK-HARQ 流程，不是离线求解传输量分配。",
    ),
    p(
        year=2022,
        title="Deep Joint Source-Channel Coding for Wireless Image Transmission With Adaptive Rate Control",
        authors="Minsu Yang, Hyeji Kim",
        venue="IEEE ICASSP, 2022",
        source="IEEE / arXiv",
        identifier="arXiv:2110.04456",
        source_url="https://arxiv.org/abs/2110.04456",
        pdf="papers/2022_Yang_DeepJSCC_Adaptive_Rate_Control.pdf",
        asset_prefix="2022_yang_deepjscc_adaptive_rate_control",
        mode="模拟式图像 DeepJSCC",
        task="无线图像传输",
        control_axis="每幅图像的 channel use / compression ratio",
        control_signal="图像内容与 SNR，经 policy network 产生掩码或 rate decision",
        flexibility="单一模型支持多码率，并能根据输入图像和信道条件动态选择发送多少 latent channel。",
        intro="早期 DeepJSCC 对固定 bandwidth ratio 训练一个固定模型，部署时如果图像内容简单或信道很好，仍消耗同样符号数；若信道差，固定率又可能不足。本文把 adaptive rate control 放进神经 JSCC，使同一网络可服务多个 rate。",
        method="图像经 CNN/attention 编码成 latent feature。Rate-control policy 根据内容特征和 SNR 产生 gating mask，选择部分特征通道送入功率归一化和 AWGN 信道。未发送特征在接收端补零或由 decoder 隐式恢复。训练时联合优化重建损失和 rate 约束。",
        experiment="常用 CIFAR-10 等图像数据集；baseline 为固定率 DeepJSCC、不同 rate 单独训练模型、BPG+capacity 或 BPG+LDPC 类分离方案；指标包括 PSNR/MS-SSIM 与 bandwidth ratio。",
        channel="信道为 AWGN。decoder 接收带噪连续 latent；控制的是连续符号数量，不涉及数字 bit/index 错误。",
        result="在相同平均 channel use 下，adaptive rate 对不同图像分配不同 latent 数，通常比固定率 DeepJSCC 有更好 rate-distortion 表现。",
        limitation="rate control 粒度主要是 latent channel/gating；没有面向实际数字链路的 packet、bit 或调制符号约束。",
        not_pure="虽然有 rate 约束，但核心是可训练的 policy/gating 编码器，而不是外层资源优化模型。",
    ),
    p(
        year=2022,
        title="Nonlinear Transform Source-Channel Coding for Semantic Communications",
        authors="Jincheng Dai, Sixian Wang, Kailin Tan, Zhongwei Si, Xiaoqi Qin, Kai Niu, Ping Zhang",
        venue="IEEE Journal on Selected Areas in Communications, 2022",
        source="IEEE / arXiv",
        identifier="arXiv:2112.10961",
        source_url="https://arxiv.org/abs/2112.10961",
        pdf="papers/2022_Dai_NTSCC_Semantic_Communications.pdf",
        asset_prefix="2022_dai_ntscc_semantic_communications",
        mode="模拟式/混合式 NTSCC",
        task="图像语义传输",
        control_axis="基于 latent 熵的 patch-wise variable-length / adaptive bandwidth",
        control_signal="latent 条件熵、hyperprior、目标 rate-distortion 权重",
        flexibility="不是把每个图像块映射成等长 channel symbols，而是用熵模型判断哪些 latent 需要更多带宽。",
        intro="论文认为传统 DeepJSCC 直接把源映射成连续符号，缺乏可解释的 rate 控制；而传统压缩+信道编码虽有 bitstream，却会在低 SNR 下 cliff。NTSCC 引入神经压缩中的 nonlinear transform 与 hyperprior，把语义 latent 的概率结构用于自适应传输。",
        method="源图像先经分析变换得到 latent y，hyperprior z 估计 y 的条件分布。高熵 latent 分量被分配更多信道资源，低熵分量用更少资源。超先验可作为数字侧信息，主 latent 经深度 JSCC 进行模拟传输，解码端利用 hyperprior refined codec。",
        experiment="CIFAR-10、Kodak、CLIC2021 等不同分辨率图像；baseline 包括 BPG+LDPC、BPG+capacity、DeepJSCC 及神经压缩方案；指标为 PSNR、MS-SSIM、LPIPS、CBR。",
        channel="主要建模 AWGN。主语义 latent 经过连续有噪信道；hyperprior 侧信息按论文设定可以数字可靠传输或计入带宽成本。没有 VQ index 错误，但明确处理了连续 latent 的信道噪声。",
        result="相对传统 DeepJSCC 可节省约 20% 带宽，并在大尺寸图像上提供更稳定的感知质量。",
        limitation="hybrid 侧信息的实际数字保护成本依赖实现；如果严格落到 packetized digital system，还需要额外的 bitstream/error 设计。",
        not_pure="自适应来自熵模型、hyperprior 和编码网络结构，而不是只在系统层分配数据量。",
    ),
    p(
        year=2022,
        title="Channel-Adaptive Wireless Image Transmission With OFDM",
        authors="Tao Wu, Zhongwei Si, Jincheng Dai, Kai Niu, Mingyu Lu, Hang Zhang",
        venue="IEEE Wireless Communications Letters, 2022",
        source="IEEE / arXiv",
        identifier="arXiv:2205.02417; DOI 10.1109/LWC.2022.3204837",
        source_url="https://arxiv.org/abs/2205.02417",
        pdf="papers/2022_Wu_Channel_Adaptive_Wireless_Image_Transmission_OFDM.pdf",
        asset_prefix="2022_wu_channel_adaptive_wireless_image_transmission_ofdm",
        mode="模拟式 OFDM DeepJSCC",
        task="OFDM 无线图像传输",
        control_axis="子载波 CSI 与噪声条件下的特征映射和功率/重要性分配",
        control_signal="CSI、SNR/noise level、latent feature",
        flexibility="符号数通常由给定 CBR 决定，但不同子载波和信道状态下发送特征的映射与权重会变；属于 channel-condition controllable。",
        intro="普通 DeepJSCC 往往假设平坦 AWGN，而真实宽带 OFDM 子载波质量不同。固定特征-子载波映射会把重要语义特征放到差子载波上。论文把 CSI 引入编码器注意力，使语义特征根据频域信道自适应分配。",
        method="编码器提取图像 latent 后，dual attention / channel-adaptive 模块根据 CSI 和噪声调整特征重要性与 OFDM 子载波映射。输出经功率归一化送入 OFDM 信道，接收端解调后由 decoder 重建。",
        experiment="CIFAR-10、Kodak 等图像；baseline 包括 DeepJSCC、OFDM-guided JSCC、传统 BPG/LDPC 组合；指标为 PSNR/MS-SSIM 和 CBR。",
        channel="考虑 OFDM 频率选择性衰落与 AWGN。decoder 接收连续 noisy OFDM symbols；没有离散 bit error，而是连续子载波噪声/衰落。",
        result="在频率选择性信道下，CSI-aware 映射明显优于忽略 CSI 的 DeepJSCC，尤其在低 SNR 或子载波质量不均时。",
        limitation="不改变总 channel use，因此对“可变 payload”的支持弱于 adaptive-rate 方法；更像信道自适应语义映射。",
        not_pure="核心在编码器注意力和 OFDM 特征映射网络，而不是独立求解 OFDM 资源分配。",
        core_level="相关核心",
    ),
    p(
        year=2023,
        title="WITT: A Wireless Image Transmission Transformer for Semantic Communications",
        authors="Ke Yang, Sixian Wang, Jincheng Dai, Kailin Tan, Kai Niu, Ping Zhang",
        venue="IEEE ICASSP, 2023",
        source="IEEE / arXiv",
        identifier="arXiv:2211.00937",
        source_url="https://arxiv.org/abs/2211.00937",
        pdf="papers/2023_Yang_WITT_Wireless_Image_Transmission_Transformer.pdf",
        asset_prefix="2023_yang_witt_wireless_image_transmission_transformer",
        mode="模拟式 Transformer JSCC",
        task="无线图像传输",
        control_axis="SNR / CSI 条件下的 spatial modulation 与 latent scaling",
        control_signal="信道状态信息、SNR、图像 patch/token 表示",
        flexibility="一套 Transformer 模型可适配不同分辨率和信道状态；payload 长度通常由配置固定，但 latent 内容和强度随信道控制。",
        intro="CNN DeepJSCC 对长距离依赖和多分辨率泛化有限，也常需为不同 SNR 训练多个模型。WITT 将 Swin Transformer 引入语义通信，并用信道状态调制 latent 表示。",
        method="图像被切成 patch/token，通过 Swin Transformer 编码为语义 latent。Spatial modulation 模块将 CSI/SNR 注入网络，对 latent 进行缩放和重加权，然后通过连续信道传输并重建。",
        experiment="Kodak、CLIC、DIV2K/CIFAR 类图像传输实验；baseline 包括 BPG+LDPC、BPG+capacity、DeepJSCC、NTSCC 等；指标包括 PSNR、MS-SSIM、LPIPS。",
        channel="通常测试 AWGN 与 fading 条件，decoder 接收带噪连续 latent。信道条件作为 side information 注入网络。",
        result="在多 SNR、多分辨率设置下保持较好重建质量，说明信道条件显式注入可提升泛化。",
        limitation="它是 channel-adaptive 而非 rate-adaptive；若用户最关心“不固定传输符号数”，WITT 应作为背景核心而非最强证据。",
        not_pure="控制发生在 Transformer 编码网络内部的条件调制，不是外层资源优化。",
        core_level="相关核心",
    ),
    p(
        year=2023,
        title="Semantic Communications With Variable-Length Coding for Extended Reality",
        authors="Wenhao Zhang, Yang Shi, H. Vincent Poor, Shuguang Cui",
        venue="IEEE Journal of Selected Topics in Signal Processing, 2023",
        source="IEEE / arXiv",
        identifier="arXiv:2302.08645; DOI 10.1109/JSTSP.2023.3300509",
        source_url="https://arxiv.org/abs/2302.08645",
        pdf="papers/2023_Zhang_Variable_Length_Coding_Extended_Reality.pdf",
        asset_prefix="2023_zhang_variable_length_coding_extended_reality",
        mode="数字/语义信道编码，XR",
        task="扩展现实 XR 内容语义传输",
        control_axis="语义内容与噪声容忍度驱动的 variable-length semantic-channel coding",
        control_signal="源内容语义量、对信道噪声的容忍度、rate allocation network 输出",
        flexibility="明确提出每个语义样本的 code length 可变；语义少或容错强的内容用短码，语义复杂/敏感的内容用长码。",
        intro="XR 业务要求低延迟和高沉浸质量，固定长度语义编码会把相同资源分配给重要性不同的内容。作者提出变量长度语义-信道编码，目标是在不牺牲 XR 体验的情况下减少冗余传输。",
        method="系统先用 rate allocation network 估计语义信息的最佳码长，再用 proxy functions 使 variable-length coding 可端到端训练。编码器与信道编码联合产生不同长度的符号序列，decoder 根据接收序列恢复 XR 语义内容。",
        experiment="实验面向 XR/视觉内容传输，比较固定长度语义编码、传统压缩传输和已有 DeepJSCC/variable-rate 方法；指标关注重建质量、语义质量和传输长度。",
        channel="考虑有噪无线信道，variable-length code 经信道后由语义 decoder 处理；论文重点是码长自适应而非显式 VQ index error。",
        result="在相同语义质量目标下减少平均传输长度；复杂内容自动分配更长码字。",
        limitation="实验场景较专，rate allocation network 的泛化依赖训练分布；对真实 packet loss / HARQ 的处理仍有限。",
        not_pure="虽然名字包含 allocation，但它将码长估计嵌入可训练 variable-length semantic-channel coding，而不是纯系统优化。",
    ),
    p(
        year=2023,
        title="Toward Adaptive Semantic Communications: Efficient Data Transmission via Online Learned Nonlinear Transform Source-Channel Coding",
        authors="Jincheng Dai, Kailin Tan, Sixian Wang, Zhongwei Si, Kai Niu, Mingyu Lu, Hang Zhang, Ping Zhang",
        venue="IEEE Journal on Selected Areas in Communications, 2023",
        source="IEEE / arXiv",
        identifier="arXiv:2211.04339; DOI 10.1109/JSAC.2023.3288246",
        source_url="https://arxiv.org/abs/2211.04339",
        pdf="papers/2023_Dai_Toward_Adaptive_Semantic_Communications_Online_NTSCC.pdf",
        asset_prefix="2023_dai_toward_adaptive_semantic_communications_online_ntscc",
        mode="模拟式 online-adaptive NTSCC",
        task="图像传输",
        control_axis="面向单个源样本和当前信道的在线自适应",
        control_signal="待传图像、当前信道状态、在线优化后的 codec / representation",
        flexibility="不只在离线阶段给定几个 rate；部署时可针对当前图像和信道在线微调表示或编解码器，实现 instance-wise adaptation。",
        intro="已有 NTSCC 具有熵模型和 rate control，但仍多为离线训练模型。真实语义通信中源内容和信道状态持续变化，固定模型难以在每次传输中都最优。本文提出 online learned NTSCC，把部署时自适应作为核心。",
        method="以 NTSCC 为基础，发送前根据当前源图像和信道对部分网络/latent 表示进行在线学习或快速更新。接收端使用同步的 codec refinement 信息恢复图像。自适应目标是直接优化当前样本的 rate-distortion。",
        experiment="Kodak、CLIC 等图像；baseline 包括 NTSCC、DeepJSCC、BPG+LDPC/capacity、VVC/5G LDPC 等；指标为 PSNR、MS-SSIM、LPIPS 与带宽开销。",
        channel="主要是 AWGN/无线 fading 条件下的连续 latent 传输；自适应过程显式考虑信道噪声统计。",
        result="online adaptation 可在相同 CBR 下提升重建质量，特别是在源分布或信道与离线训练不完全匹配时。",
        limitation="在线学习带来额外计算、同步和时延开销；低时延应用是否可接受需要实测。",
        not_pure="核心是在线更新语义 codec / latent，而不是仅求解资源量分配。",
    ),
    p(
        year=2023,
        title="Improved Nonlinear Transform Source-Channel Coding to Catalyze Semantic Communications",
        authors="Sixian Wang, Jincheng Dai, Kailin Tan, Zhongwei Si, Kai Niu, Mingyu Lu, Hang Zhang, Ping Zhang",
        venue="IEEE Journal of Selected Topics in Signal Processing, 2023",
        source="IEEE / arXiv",
        identifier="arXiv:2303.14637; DOI 10.1109/JSTSP.2023.3304140",
        source_url="https://arxiv.org/abs/2303.14637",
        pdf="papers/2023_Wang_Improved_NTSCC_Catalyze_Semantic_Communications.pdf",
        asset_prefix="2023_wang_improved_ntscc_catalyze_semantic_communications",
        mode="模拟式 enhanced NTSCC",
        task="图像传输",
        control_axis="contextual entropy、rate/channel response network 与 latent feature editing",
        control_signal="contextual entropy、目标 CBR、SNR/channel state",
        flexibility="同一模型通过响应网络处理多 rate 和多 channel state；latent feature 可被在线编辑以满足不同传输条件。",
        intro="NTSCC 证明了熵建模对 SemCom 重要，但多 rate、多信道状态下往往仍需训练多个模型或做粗粒度配置。本文改进上下文熵模型和响应网络，让一个模型覆盖更多传输条件。",
        method="引入 contextual entropy model 评估 latent 信息量；rate/channel response network 根据目标 rate 和信道状态调节编码/解码；online latent feature editing 在不重训完整模型的情况下微调待传 latent。",
        experiment="常用 Kodak/CLIC 类图像传输；baseline 为 NTSCC、WITT/DeepJSCC、BPG+LDPC/capacity；指标为 PSNR、MS-SSIM、LPIPS 和 CBR。",
        channel="连续 latent 经 AWGN/无线信道，模型在训练中纳入噪声；不涉及离散 index 错误。",
        result="多 rate、多 SNR 下保持较平滑的 rate-distortion 曲线，减少为每个条件单独训练模型的需求。",
        limitation="控制主要依赖隐式网络调制，可解释性不如数字 bit allocation；实际协议如何承载 response 参数仍需设计。",
        not_pure="可控性由 entropy model 和 response network 实现，属于编码器结构设计。",
    ),
    p(
        year=2023,
        title="DeepJSCC-l++: Robust and Bandwidth-Adaptive Wireless Image Transmission",
        authors="Nikolaos B. Bian, Deniz Gunduz, et al.",
        venue="IEEE GLOBECOM, 2023",
        source="IEEE / arXiv",
        identifier="arXiv:2305.13161; IEEE 10436878",
        source_url="https://arxiv.org/abs/2305.13161",
        pdf="papers/2023_Bian_DeepJSCC_lpp_Bandwidth_Adaptive.pdf",
        asset_prefix="2023_bian_deepjscc_lpp_bandwidth_adaptive",
        mode="模拟式 bandwidth-adaptive DeepJSCC",
        task="图像传输",
        control_axis="目标 bandwidth ratio 与 SNR 作为 side information",
        control_signal="target bandwidth ratio、SNR、图像内容",
        flexibility="一个 ViT/DeepJSCC-l++ 模型覆盖多带宽和多 SNR，无需为每个 bandwidth ratio 单独训练。",
        intro="DeepJSCC-l 解决了部分带宽自适应问题，但多 rate/SNR 泛化仍有限。本文把目标带宽和 SNR 作为条件输入，让模型在部署时按需求调整传输符号数。",
        method="以 Vision Transformer 为 backbone，编码器/解码器中注入 rate/SNR side information。模型通过 latent-channel prioritization 或 truncation 控制发送维度，按目标 bandwidth ratio 截取相应数量的 channel symbols。",
        experiment="CIFAR/Kodak 等图像；baseline 为 DeepJSCC、DeepJSCC-l、BPG+LDPC/capacity；指标包括 PSNR、MS-SSIM、不同 bandwidth ratio 下的鲁棒性。",
        channel="AWGN/fading 下的连续符号传输，SNR 作为条件输入。decoder 接收的是被噪声污染且长度由 bandwidth ratio 控制的 latent。",
        result="单一模型在多个 bandwidth ratio 下接近或超过多模型 baseline，显著提升部署灵活性。",
        limitation="rate 控制通常依赖预设 target ratio；是否能完全基于输入自动决定 rate 还需要额外 policy。",
        not_pure="不是外部求解带宽分配，而是把带宽目标注入 JSCC 模型并改变 latent 使用量。",
    ),
    p(
        year=2023,
        title="Deep Joint Source-Channel Coding for Wireless Image Transmission With Entropy-Aware Adaptive Rate Control",
        authors="Weixuan Chen, Qianqian Yang, Zehui Xiong, et al.",
        venue="IEEE GLOBECOM, 2023",
        source="IEEE / arXiv",
        identifier="arXiv:2306.02825",
        source_url="https://arxiv.org/abs/2306.02825",
        pdf="papers/2023_Chen_Entropy_Aware_Adaptive_Rate_Control_DeepJSCC.pdf",
        asset_prefix="2023_chen_entropy_aware_adaptive_rate_control_deepjscc",
        mode="模拟式 entropy-aware DeepJSCC",
        task="无线图像传输",
        control_axis="feature-map entropy 与 SNR 驱动的二级 pruning",
        control_signal="feature maps、2D entropy、SNR，两个 policy network 输出 mask/pruning ratio",
        flexibility="发送端先选 feature map，再裁剪每个 feature map 内的符号；实际发送符号数随图像内容和 SNR 改变。",
        intro="固定率 DeepJSCC 忽视图像内容差异，已有 adaptive 方法多只在 feature group 级截断，粒度粗。本文把 feature map entropy 作为语义信息量估计，进一步进行 feature map selection 与 symbol pruning。",
        method="语义 encoder 得到 feature map z；Policy Network 1 基于 z、entropy 和 SNR 产生二值 mask，选择要发送的 feature maps；Policy Network 2 输出 pruning ratio 或一热剪枝索引，在保留 map 内删除冗余符号。发送端同时传输裁剪后的特征和必要的剪枝索引，接收端按 mask/索引补零后解码。",
        experiment="图像数据集与 DeepJSCC 常规设置；baseline 包括 fixed DeepJSCC、DeepJSCC+rate adaptation、BPG+LDPC；指标为 PSNR、平均 CR/CBR。",
        channel="AWGN 连续信道；信道影响被 SNR 条件纳入 policy 与 decoder。没有数字 bit flip，但能处理被噪声污染和被裁剪的连续 latent。",
        result="低 SNR 下倾向保留更多特征，高 SNR 下自动降低 CR；相比 SOTA adaptive-rate 方法在相近 CR 下有更好 PSNR。",
        limitation="需要 side information 告知 mask/pruning，实际协议开销常被简化；剪枝索引若出错的鲁棒性未充分展开。",
        not_pure="控制器是端到端训练的 policy networks，且直接作用于语义 feature maps。",
    ),
    p(
        year=2023,
        title="Predictive and Adaptive Deep Coding for Wireless Image Transmission in Semantic Communication",
        authors="Wei Zhang, Zehui Xiong, et al.",
        venue="IEEE Transactions on Wireless Communications, 2023",
        source="IEEE",
        identifier="IEEE 10015684; DOI 10.1109/TWC.2023.3234408",
        source_url="https://ieeexplore.ieee.org/document/10015684",
        pdf="papers/2023_Zhang_Predictive_Adaptive_Deep_Coding_PADC.pdf",
        asset_prefix="2023_zhang_predictive_adaptive_deep_coding_padc",
        mode="模拟式 predictive/adaptive DeepJSCC",
        task="无线图像传输",
        control_axis="目标质量约束下的 compression ratio 选择",
        control_signal="图像内容、SNR、候选 compression ratio、目标 PSNR/quality",
        flexibility="对每个图像和信道条件选择满足目标质量的最小 CR，而不是固定符号数。",
        intro="DeepJSCC 在固定 CR 下性能好，但实际系统常需要“达到指定质量即可”，不同图像在同一 SNR 下所需符号数不同。PADC 引入预测模块先估计质量，再自适应选择编码率。",
        method="DeepJSCC-V 支持 variable code length；OraNet 预测给定图像、SNR 和 CR 下的重建质量；CR optimizer 搜索满足目标 PSNR 的最低 CR。发送端据此截取或生成对应长度的 channel symbols。",
        experiment="图像传输实验；baseline 包括 fixed DeepJSCC、DeepJSCC-V、BPG+LDPC/capacity 等；指标包括目标 PSNR 达成率、平均 CR、PSNR/MS-SSIM。",
        channel="考虑 AWGN/fading 连续信道，OraNet 显式以 SNR 为输入预测信道下质量。接收端得到带噪连续 latent。",
        result="在保证目标质量时显著降低平均 CR，复杂图像/低 SNR 自动用更多符号。",
        limitation="需要可靠质量预测器；若图像分布或信道模型偏移，CR optimizer 可能低估所需资源。",
        not_pure="虽然有优化器，但核心包含 DeepJSCC-V 与 OraNet，优化变量作用于可变长度神经 codec。",
    ),
    p(
        year=2024,
        title="SCAN: Semantic Communication With Adaptive Channel Feedback",
        authors="Zhenzi Zhang, Mingzhe Chen, Walid Saad, Merouane Debbah, Chau Yuen",
        venue="IEEE Transactions on Cognitive Communications and Networking, 2024",
        source="IEEE / arXiv",
        identifier="arXiv:2306.15534; DOI 10.1109/TCCN.2024.3394867",
        source_url="https://arxiv.org/abs/2306.15534",
        pdf="papers/2024_Zhang_SCAN_Adaptive_Channel_Feedback.pdf",
        asset_prefix="2024_zhang_scan_adaptive_channel_feedback",
        mode="模拟式 MIMO SemCom",
        task="MIMO 图像语义传输 / CSI feedback",
        control_axis="每幅图像的 channel feedback overhead",
        control_signal="预测重建质量、semantic distortion outage probability、CSI/noise",
        flexibility="不是所有样本都反馈同样长度 CSI；预测质量差或语义失真风险高时分配更长反馈，质量易满足时减少反馈。",
        intro="MIMO 语义通信需要 CSI，但 CSI feedback 本身消耗资源。固定反馈长度无法兼顾不同图像和不同信道。SCAN 用语义失真概率指导反馈开销，让反馈也变成语义可控的一部分。",
        method="DeepSC-MIMO 根据 CSI/noise 编码图像；SCAN 预测不同反馈粒度下的重建质量或 outage risk，然后自适应选择反馈开销。系统目标是在语义质量约束下减少 CSI feedback。",
        experiment="图像重建任务，baseline 包括固定 CSI feedback、DeepSC-MIMO、传统 CSI 压缩反馈；指标为 PSNR/MS-SSIM、semantic distortion outage、feedback bits/channel uses。",
        channel="MIMO fading 信道。控制对象是 CSI feedback 链路；语义 payload 仍为连续 DeepJSCC latent。",
        result="在相同失真 outage 目标下减少反馈开销，并对难传图像保留更多 CSI 信息。",
        limitation="它控制的是反馈侧而非主语义 payload；如果只关心发送语义符号数，它是旁路但重要的 controllable SemCom。",
        not_pure="包含语义质量预测与 adaptive feedback 机制，不只是抽象优化模型。",
    ),
    p(
        year=2024,
        title="Deep Joint Source-Channel Coding for Adaptive Image Transmission Over MIMO Channels",
        authors="Tao Wu, Jincheng Dai, Sixian Wang, Zhongwei Si, Kai Niu, Ping Zhang",
        venue="IEEE Transactions on Wireless Communications, 2024",
        source="IEEE / arXiv",
        identifier="arXiv:2309.00470; IEEE 10597355",
        source_url="https://arxiv.org/abs/2309.00470",
        pdf="papers/2024_Wu_DeepJSCC_MIMO_Adaptive_Image_Transmission.pdf",
        asset_prefix="2024_wu_deepjscc_mimo_adaptive_image_transmission",
        mode="模拟式 MIMO DeepJSCC",
        task="MIMO 图像传输",
        control_axis="MIMO channel matrix、SNR、天线数驱动的 feature mapping/power allocation",
        control_signal="CSI、SNR、antenna configuration、图像 latent",
        flexibility="同一 ViT/DeepJSCC-MIMO 模型适配不同信道和天线配置；主要控制 mapping 和功率，而非任意改变 payload 长度。",
        intro="SISO/AWGN 下训练的 DeepJSCC 难以应对 MIMO 信道矩阵、空间流和天线数变化。论文用 Transformer 自注意力建模源特征与 MIMO 信道之间的耦合，实现 channel-adaptive 语义映射。",
        method="编码器提取图像 token/latent；CSI embedding 注入 Transformer，使网络学习在不同空间子信道上分配语义特征和功率。接收端使用对应 MIMO 检测/解码和语义 decoder 重建图像。",
        experiment="Kodak/CLIC 等图像；baseline 包括传统 MIMO 传输、DeepJSCC、channel-adaptive OFDM/JSCC；指标为 PSNR/MS-SSIM 和多天线/SNR 设置。",
        channel="MIMO fading + AWGN。信道影响连续 latent，decoder 接收 MIMO 检测后的带噪表示。",
        result="在不同天线数和 SNR 条件下比固定映射更稳，说明信道矩阵可作为语义编码控制信号。",
        limitation="payload 数量通常按配置固定；可控性更偏物理层适配。",
        not_pure="CSI 被注入编码网络并改变特征映射，不是外部资源分配。",
        core_level="相关核心",
    ),
    p(
        year=2024,
        title="Rate-Adaptive Coding Mechanism for Semantic Communications With Multi-Modal Data",
        authors="Zhenzi Zhang, Mingzhe Chen, Walid Saad, Merouane Debbah, et al.",
        venue="IEEE Transactions on Communications, 2024",
        source="IEEE / arXiv",
        identifier="arXiv:2305.10773; IEEE 10327757",
        source_url="https://arxiv.org/abs/2305.10773",
        pdf="papers/Rate-Adaptive_Coding_Mechanism_for_Semantic_Communications_With_Multi-Modal_Data.pdf",
        asset_prefix="rate_adaptive_coding_mechanism_for_semantic_communications_with_multi_modal_data",
        mode="数字/多模态 SemCom",
        task="多模态任务语义传输",
        control_axis="模态重要性与任务敏感度驱动的 rate-adaptive coding / UEP",
        control_signal="模态噪声敏感度、任务性能、语义重要性",
        flexibility="不同模态、不同样本可获得不同编码保护和传输率；不是一刀切地固定每个模态 payload。",
        intro="多模态 SemCom 中文本、图像、其他模态对任务贡献不同，固定比例传输会浪费资源或保护错对象。论文把语义重要性和信道编码结合，用 rate-adaptive / unequal protection 支撑多模态任务。",
        method="框架由多模态语义编码器、语义重要性估计、传统 channel encoder/decoder 与 rate-adaptive coding 组成。重要模态或噪声敏感特征分配更强保护或更高传输率。",
        experiment="多模态任务设置；baseline 包括固定率多模态 SemCom、传统分离编码、无 UEP 的语义系统；指标为任务准确率、语义相似度和传输开销。",
        channel="数字链路与 channel coding 显式存在，错误主要由传统译码处理；语义模型利用 UEP 减轻关键模态错误。",
        result="在资源受限或信道较差时，rate-adaptive / UEP 比均匀保护更能维持任务性能。",
        limitation="相当一部分设计靠 channel coding/UEP，离散语义 token 本身的 index error 建模不如 VQ 系列深入。",
        not_pure="虽然涉及率分配，但它配套多模态语义编码和 channel coding 机制；纳入时标为边界核心。",
        core_level="边界核心",
    ),
    p(
        year=2025,
        title="Rate-Distortion-Perception Controllable Joint Source-Channel Coding for High-Fidelity Generative Semantic Communications",
        authors="Kailin Tan, Jincheng Dai, Sixian Wang, Zhongwei Si, Kai Niu, Ping Zhang",
        venue="IEEE Transactions on Cognitive Communications and Networking, 2025",
        source="IEEE / arXiv",
        identifier="arXiv:2408.14127; DOI 10.1109/TCCN.2024.3511960",
        source_url="https://arxiv.org/abs/2408.14127",
        pdf="papers/2025_Tan_RDP_Controllable_JSCC_Generative_Semantic.pdf",
        asset_prefix="2025_tan_rdp_controllable_jscc_generative_semantic",
        mode="生成式模拟 JSCC",
        task="高保真图像语义传输 / 生成式重建",
        control_axis="rate-distortion-perception 三目标与 ROI/content 控制",
        control_signal="RDP preference、realism map、用户兴趣/注意区域、信道条件",
        flexibility="同一系统可改变传输侧对失真、感知真实度和重点内容的优先级，CCT 可把更多资源给兴趣区域。",
        intro="生成式语义通信能在低码率下产生高感知质量，但 distortion 与 perception 往往冲突；不同用户也可能关注不同区域。论文把 R-D-P 权衡和内容兴趣作为可控变量。",
        method="DPCT 通过 realism map 和条件控制调整生成式 JSCC 的 perception-distortion 权衡；CCT 针对用户兴趣内容进行优先传输或增强。编码器输出连续语义表示，生成式 decoder 在控制条件下恢复高保真图像。",
        experiment="图像重建/生成式通信数据集；baseline 包括 NTSCC、WITT、生成式压缩/JSCC、BPG+LDPC；指标包括 PSNR、MS-SSIM、LPIPS、FID/KID 等感知指标。",
        channel="连续 latent 通过有噪无线信道；控制变量主要作用在 semantic/generative decoder 和传输表示上，不涉及离散 bit error。",
        result="用户可在更高 PSNR 与更好感知质量之间调节，并能对兴趣区域获得更好重建。",
        limitation="控制目标更偏质量/感知/内容，而不是严格的符号数自适应；生成式幻觉风险需额外约束。",
        not_pure="可控性由生成式 JSCC 结构、realism map 和内容控制模块实现。",
    ),
    p(
        year=2025,
        title="Rate-Adaptive Generative Semantic Communication Using Conditional Diffusion Models",
        authors="Ke Yang, Jincheng Dai, Sixian Wang, Kailin Tan, Kai Niu, Ping Zhang",
        venue="IEEE Wireless Communications Letters, 2025",
        source="IEEE / arXiv",
        identifier="arXiv:2409.02597; DOI 10.1109/LWC.2024.3515656",
        source_url="https://arxiv.org/abs/2409.02597",
        pdf="papers/2025_Yang_Rate_Adaptive_Generative_Semantic_Communication_Diffusion.pdf",
        asset_prefix="2025_yang_rate_adaptive_generative_semantic_communication_diffusion",
        mode="生成式 rate-adaptive SemCom",
        task="图像语义传输 / diffusion 重建",
        control_axis="熵模型估计 transmitted symbols 的信息量并管理带宽",
        control_signal="symbol entropy、target rate、信道条件、diffusion conditioning",
        flexibility="根据语义 symbol 的熵和目标带宽选择发送量，decoder 用条件扩散模型补全细节。",
        intro="低码率下普通 JSCC 重建模糊，生成式模型可补细节，但如果传输率不可控则难以落地。论文结合 rate-adaptive entropy model 和 conditional diffusion decoder，让传输量可变而图像质量保持。",
        method="编码器产生语义 latent/symbol，entropy model 评估其传输代价并控制保留量；接收端以收到的语义信息作为 diffusion 条件，逐步生成或恢复图像。训练兼顾重建失真、感知质量和 rate。",
        experiment="图像数据集；baseline 包括 DeepJSCC、NTSCC、WITT、生成式压缩/扩散方案；指标为 PSNR、MS-SSIM、LPIPS、FID 与平均 rate。",
        channel="连续或符号化 latent 经有噪信道；扩散 decoder 处理不完整/带噪条件。",
        result="在较低或可变 rate 下提高感知质量，同时保持可控带宽。",
        limitation="扩散推理成本高，且低语义条件下可能引入非真实细节。",
        not_pure="rate control 与 diffusion conditional decoder 共同构成通信方法。",
    ),
    p(
        year=2025,
        title="Hybrid Digital-Analog Semantic Communications",
        authors="Huiqiang Xie, Zhijin Qin, Xiaoming Tao, et al.",
        venue="IEEE Journal on Selected Areas in Communications, 2025",
        source="IEEE / arXiv",
        identifier="arXiv:2405.12580; DOI 10.1109/JSAC.2025.3559149",
        source_url="https://arxiv.org/abs/2405.12580",
        pdf="papers/2025_Xie_Hybrid_Digital_Analog_Semantic_Communications.pdf",
        asset_prefix="2025_xie_hybrid_digital_analog_semantic_communications",
        mode="混合数字-模拟 SemCom",
        task="图像/多媒体语义传输",
        control_axis="digital stream 与 analog stream 的分配和融合",
        control_signal="rate/distortion loss、信道状态、语义特征重要性",
        flexibility="系统可在数字 bitstream 和模拟 semantic latent 之间调整承载比例；不是固定只走 analog 或 digital。",
        intro="纯模拟 DeepJSCC 对信道鲁棒但难兼容现有数字网络；纯数字语义编码可部署但存在误码 cliff。HDA-DeepSC 试图结合二者：关键语义可数字保护，残差信息可模拟平滑退化。",
        method="编码器分成 digital branch 与 analog branch，allocation/fusion modules 决定哪些语义信息进入 bitstream，哪些以连续符号发送。训练使用 rate/distortion loss 约束两条支路的协同。",
        experiment="图像语义传输实验；baseline 包括 analog DeepJSCC、digital semantic coding、BPG/LDPC 等；指标为 PSNR/MS-SSIM/LPIPS 和 rate。",
        channel="同时考虑数字链路误码/译码和模拟链路噪声。decoder 融合数字恢复特征与带噪模拟特征。",
        result="在不同信道下比单一路径更平滑，兼顾数字可靠性和模拟 graceful degradation。",
        limitation="分配策略和协议实现复杂；数字侧若出现不可纠正 bit errors，仍需更细的语义错误建模。",
        not_pure="核心是 HDA 编码结构和融合网络，而不是单纯分配传输量。",
    ),
    p(
        year=2025,
        title="Progressive Learned Image Transmission for Semantic Communication Using Hierarchical VAE",
        authors="Wenhao Zhang, et al.",
        venue="IEEE Transactions on Cognitive Communications and Networking, 2025",
        source="IEEE / arXiv",
        identifier="arXiv:2408.16340; DOI 10.1109/TCCN.2025.3546935",
        source_url="https://arxiv.org/abs/2408.16340",
        pdf="papers/2025_Zhang_Progressive_Learned_Image_Transmission_Hierarchical_VAE.pdf",
        asset_prefix="2025_zhang_progressive_learned_image_transmission_hierarchical_vae",
        mode="生成式/渐进式 SemCom",
        task="图像渐进传输",
        control_axis="层级 latent groups 的 coarse-to-fine progressive transmission",
        control_signal="层级 VAE latent、目标质量、可用带宽/信道条件",
        flexibility="可先发送粗层语义 latent，再按需要发送细层 latent；传输可以随时停止或继续增强。",
        intro="固定一次性传输不适合带宽波动和逐步预览场景。层级 VAE 天然有从全局语义到局部细节的分层结构，适合做 progressive semantic communication。",
        method="Hierarchical VAE 产生多层 latent 表示；底层/全局 latent 先传，高层/细节 latent 后传。空间 grouping 和 rate matching 控制每一步的发送量，decoder 每收到一层即可更新重建。",
        experiment="图像数据集；baseline 包括一次性 DeepJSCC/NTSCC、传统 progressive codec、BPG+LDPC；指标为每阶段 PSNR/MS-SSIM/LPIPS、rate-progress curve。",
        channel="有噪连续信道下逐层传输 latent；未收到的层由 VAE prior/decoder 预测。",
        result="同一传输可在低 rate 下给出可用预览，并随追加层逐步提升质量。",
        limitation="层级 latent 的最优发送顺序和误码保护仍有空间；若早期 coarse latent 出错，后续细节可能被带偏。",
        not_pure="渐进性来自层级 VAE 语义表示和可停止传输结构。",
    ),
    p(
        year=2025,
        title="DD-JSCC: Dynamic Deep Joint Source-Channel Coding for Semantic Communications",
        authors="Rahul Raha, Soumya Adhikary, et al.",
        venue="IEEE Wireless Communications Letters, 2026; arXiv preprint in 2025",
        source="IEEE / arXiv",
        identifier="arXiv:2507.20467",
        source_url="https://arxiv.org/abs/2507.20467",
        pdf="papers/2025_DD_JSCC_Dynamic_Deep_JSCC.pdf",
        asset_prefix="2025_dd_jscc_dynamic_deep_jscc",
        mode="模拟式 dynamic DeepJSCC",
        task="图像语义传输",
        control_axis="动态网络/动态传输路径以适配异构 SNR",
        control_signal="信道 SNR、编码器效率、接收端均衡/解码状态",
        flexibility="强调 heterogeneous SNR 下 encoder 与 receiver-side equalization 的动态配合；payload 控制证据弱于 PADC/entropy-aware 系列。",
        intro="固定 DeepJSCC 在训练 SNR 与部署 SNR 不一致时性能下降。DD-JSCC 试图让编码/解码链路随信道变化动态调整，以增强语义重建鲁棒性。",
        method="以 DeepJSCC 为基础加入动态模块，根据信道条件调整编码或解码路径，并在接收端强化均衡/语义解码。",
        experiment="无线图像重建，baseline 为 DeepJSCC、SNR-adaptive DeepJSCC 等；指标为 PSNR、MS-SSIM。",
        channel="连续信道，重点是 heterogenous SNR 条件下的鲁棒解码。",
        result="在变化 SNR 下相对固定 DeepJSCC 提升 PSNR/MS-SSIM。",
        limitation="从可控语义传输角度看，它更像鲁棒/动态网络，而不是明确的 variable-symbol coding；纳入为相关核心。",
        not_pure="方法包含动态 JSCC 架构，不是系统级优化。",
        core_level="相关核心",
    ),
    p(
        year=2025,
        title="Entropy-and-Channel-Aware Adaptive-Rate Semantic Communication With MLLM-Aided Feature Compensation",
        authors="Weixuan Chen, Qianqian Yang, Yuhao Chen, Chongwen Huang, Qian Wang, Zehui Xiong, Zhaoyang Zhang",
        venue="arXiv preprint, 2025",
        source="arXiv",
        identifier="arXiv:2501.15414",
        source_url="https://arxiv.org/abs/2501.15414",
        pdf="papers/2025_Entropy_Channel_Aware_Adaptive_Rate_Semantic_Communication.pdf",
        asset_prefix="2025_entropy_channel_aware_adaptive_rate_semantic_communication",
        mode="模拟式 MIMO adaptive-rate SemCom",
        task="MIMO Rayleigh 图像语义传输",
        control_axis="feature map selection + symbol pruning 的双层 rate control",
        control_signal="CSI、SNR、feature maps、每个 feature map 的 2D entropy",
        flexibility="两级 policy network 同时决定保留哪些 feature maps 和每个样本内保留多少 symbols，CR 可在给定上限范围内连续变化。",
        intro="论文指出 fixed-rate SemCom 在好信道浪费资源、坏信道质量下降；已有 adaptive-rate 方法常只依据 SNR 或少数离散 CR，粒度粗，且丢弃特征后缺少显式补偿。作者提出 entropy-and-channel-aware 控制，并用 MLLM/InternViT 辅助补偿被丢弃或受损特征。",
        method="语义 encoder 输出 feature maps Z1；CSI 与 SNR 经 embedding 后注入 encoder/decoder。Policy Network 1 读取 Z1、2D entropy 与 channel embedding，选择重要 feature maps；Policy Network 2 进一步决定 retained feature maps 内的 symbol cut-off。发送端只传被选择/裁剪后的 Z3，接收端经 MIMO Rayleigh 信道、L-MMSE 检测与 InternViT/LoRA feature compensation 恢复缺失结构。",
        experiment="CIFAR-10 图像；MIMO Rayleigh fading，Nt=Nr=2 或 4；CU=24/36 时最大 CR 分别约 0.25/0.375；baseline 为 BPG+LDPC 和 SwinJSCC+SA&RA；指标为 PSNR 与平均 CR。",
        channel="显式 MIMO Rayleigh + AWGN。decoder 接收带噪且被裁剪的连续特征；信道估计 CSI/SNR 被反馈到发送端，并作为控制输入。",
        result="相同或更低 CR 下比 SwinJSCC+SA&RA 高约 0.4-0.9 dB PSNR；中高 SNR 下相对 BPG+LDPC 可有约 1.5-2 dB 增益。ViT 补偿模块能在少发 11%-18% symbols 时保持接近 PSNR。",
        limitation="MLLM/InternViT 补偿带来模型规模和部署成本；论文把 mask/cut-off side information 开销简化为很小，实际链路仍需协议验证。",
        not_pure="控制由两个 policy network、entropy feature 和 MLLM 补偿端到端实现，不是单独的 rate allocation 优化。",
    ),
    p(
        year=2025,
        title="Rate-Adaptive Semantic Communication via Multi-Stage Vector Quantization",
        authors="Jinsung Park, Junyong Shin, Yongjeong Oh, Jihun Park, Yo-Seb Jeon",
        venue="arXiv preprint, 2025",
        source="arXiv",
        identifier="arXiv:2510.02646",
        source_url="https://arxiv.org/abs/2510.02646",
        pdf="papers/2025_Park_Rate_Adaptive_Semantic_Communication_MSVQ.pdf",
        asset_prefix="2025_park_rate_adaptive_semantic_communication_msvq",
        mode="数字式 MSVQ SemCom",
        task="图像语义重建",
        control_axis="按 rate 激活不同数量的 VQ stages / codebooks",
        control_signal="bit budget、stage-wise residual energy/semantic utility、entropy coding",
        flexibility="低码率只发前几级 coarse VQ index，高码率追加 residual stages；离散 payload 长度天然可变。",
        intro="单级 VQ 或固定码率数字 SemCom 难以兼顾低码率和高质量。MSVQ 将语义 latent 的残差逐级量化，使系统可以按预算逐步发送更多 index。",
        method="encoder 得到连续 semantic latent；stage 1 codebook 量化主信息，后续 codebooks 量化残差。发送端可根据预算停止在第 k 级，并用 entropy coding 压缩 index。decoder 把收到的多个 stage codewords 相加或融合恢复 latent。",
        experiment="图像重建数据集；baseline 包括 single-stage VQ、固定率数字 SemCom、传统压缩+信道编码；指标为 PSNR/MS-SSIM/LPIPS 与 bits per pixel / CBR。",
        channel="主要关注数字 VQ index payload；信道错误处理较弱，通常依赖可靠数字链路或传统 channel coding。",
        result="多 stage 结构提供平滑 rate-quality 曲线，一个模型覆盖多个 rate。",
        limitation="如果后续 residual index 出错，误差如何传播到语义 latent 仍需更细的信道联合训练。",
        not_pure="可控性来自 multi-stage codebook 架构，不是外层分配模型。",
    ),
    p(
        year=2025,
        title="Digital Semantic Communications With Variable Product Quantization for Image Transmission",
        authors="Junxiao Liang, Fengyu Wang, Yuan Zheng, Wenjun Xu, Xiaodong Xu, Jincheng Dai",
        venue="IEEE WCNC, 2025",
        source="IEEE",
        identifier="DOI 10.1109/WCNC61545.2025.10978348",
        source_url="https://doi.org/10.1109/WCNC61545.2025.10978348",
        pdf="papers/Digital_Semantic_Communications_with_Variable_Product_Quantization_for_Image_Transmission.pdf",
        asset_prefix="digital_semantic_communications_with_variable_product_quantization_for_image_tra",
        mode="数字式 VPQ SemCom",
        task="图像传输",
        control_axis="product quantization 子空间/码本数量可变",
        control_signal="目标码率、图像 latent 结构、PQ codebooks",
        flexibility="通过改变启用的 product codebook / 子向量组合，生成不同长度的离散 index 序列。",
        intro="固定 VQ codebook 很难在不同带宽下保持效率；PQ 将 latent 分解到多个子空间，天然支持按子空间组合调整传输量。本文将 variable product quantization 用于数字 SemCom 图像传输。",
        method="语义 encoder 输出 feature map 后分块或分通道进入 PQ；每个子向量从对应 codebook 选择 index。VPQ 根据目标 rate 或条件选择使用多少子码本/子向量，从而生成可变 bitstream。",
        experiment="图像传输数据集；baseline 包括 VQ semantic communication、传统压缩、模拟 DeepJSCC 等；指标包括 PSNR/MS-SSIM 和传输 bits/CBR。",
        channel="离散 index 通常通过数字链路传输，信道错误主要交给传统信道编码；论文重点是可变 PQ 源编码。",
        result="在多码率下比固定 VQ/PQ 更灵活，低码率可保持较好语义质量。",
        limitation="子 index 一旦误判会映射到不同 codeword；若没有 joint channel-aware index assignment，语义跳变仍是风险。",
        not_pure="控制点是 VPQ 量化结构和 codebook 使用方式。",
    ),
    p(
        year=2025,
        title="Fully Learnable Multi-Rate Quantization for Digital Semantic Communication Systems",
        authors="Minhoe Kim, Dong Jin Ji",
        venue="IEEE Wireless Communications Letters, 2025",
        source="IEEE",
        identifier="DOI 10.1109/LWC.2025.3581374",
        source_url="https://doi.org/10.1109/LWC.2025.3581374",
        pdf="papers/Fully_Learnable_Multi-Rate_Quantization_for_Digital_Semantic_Communication_Systems.pdf",
        asset_prefix="fully_learnable_multi_rate_quantization_for_digital_semantic_communication_syste",
        mode="数字式 learnable multi-rate quantization",
        task="图像传输",
        control_axis="learnable quantization levels / multi-rate bitstream",
        control_signal="目标 rate、Concrete categorical variables、训练中的离散化松弛",
        flexibility="同一量化模型生成不同 bit-depth/rate 的离散表示，避免为每个 rate 单独训练量化器。",
        intro="数字 SemCom 需要离散 bit，但传统量化器不可导且固定 rate。论文用可学习多码率量化解决训练和部署中的 rate 切换问题。",
        method="将量化决策建模为可学习的 categorical/concrete 随机变量，训练时用连续松弛反传，测试时输出离散 index/bit。多 rate 分支或共享量化参数让同一 semantic encoder 支持不同 bits per feature。",
        experiment="图像传输；baseline 包括固定 bit-depth 量化、VQ/PQ、模拟 DeepJSCC；指标为重建质量与 bit rate。",
        channel="数字 bitstream 可接传统 channel coding；部分实验显式考虑 BER 或离散错误。decoder 接收量化后的数字表示。",
        result="多 rate 下比固定量化器更平滑，降低多模型维护成本。",
        limitation="Concrete 松弛和真实硬判决之间仍可能有 gap；强信道错误下 index 语义距离未必被优化。",
        not_pure="可控性来自 learnable quantizer 本身。",
    ),
    p(
        year=2025,
        title="Conditional Entropy-Constrained Multi-Stage Vector Quantization for Semantic Communication",
        authors="Junyong Shin, Jihun Park, Jinsung Park, Yo-Seb Jeon",
        venue="IEEE Wireless Communications Letters, 2025/2026",
        source="IEEE",
        identifier="IEEE 11299506",
        source_url="https://ieeexplore.ieee.org/document/11299506",
        pdf="papers/Conditional_Entropy-Constrained_Multi-Stage_Vector_Quantization_for_Semantic_Communication.pdf",
        asset_prefix="conditional_entropy_constrained_multi_stage_vector_quantization_for_semantic_com",
        mode="数字式 entropy-constrained MSVQ",
        task="图像语义传输 / 重建",
        control_axis="条件熵约束下的 stage-wise VQ 与 entropy-coded payload",
        control_signal="条件概率模型、stage residual、目标 entropy/rate",
        flexibility="发送的 stage 数量和每级 index 的平均码长可按目标 rate 调整。",
        intro="MSVQ 支持渐进码率，但如果每个 index 等长发送，仍浪费统计冗余。本文把条件熵约束纳入多级 VQ，使数字语义 payload 能按概率模型自适应压缩。",
        method="每级 VQ 量化上一阶段残差；条件熵模型估计当前 stage index 在已发送 stage 条件下的概率，并用于 entropy coding 和 rate-distortion 训练。可按预算选择 stage 或码长。",
        experiment="图像重建数据集；baseline 包括 MSVQ、single VQ、传统编码和 fixed-rate digital SemCom；指标为 PSNR/MS-SSIM 与 entropy rate。",
        channel="主要是数字源编码侧；信道错误若存在通常由可靠传输假设或 channel coding 承担。",
        result="同等语义质量下减少平均 bit 数，且多 stage 提供自然的 rate scalability。",
        limitation="没有充分解决 entropy-coded index bit error 后同步失效问题；真实无线链路需强纠错。",
        not_pure="控制由条件熵模型与多级 VQ 共同实现。",
    ),
    p(
        year=2025,
        title="Digital-SC: Digital Semantic Communication With Adaptive Network Split and Learned Non-Linear Quantization",
        authors="Lei Guo, Wei Chen, Yuxuan Sun, Bo Ai",
        venue="IEEE Transactions on Cognitive Communications and Networking, 2025",
        source="IEEE",
        identifier="DOI 10.1109/TCCN.2024.3510586; IEEE 10772628",
        source_url="https://doi.org/10.1109/TCCN.2024.3510586",
        pdf="papers/Digital-SC_Digital_Semantic_Communication_With_Adaptive_Network_Split_and_Learned_Non-Linear_Quantization.pdf",
        asset_prefix="digital_sc_digital_semantic_communication_with_adaptive_network_split_and_learne",
        mode="数字式 split-computing SemCom",
        task="device-edge 图像分类 / 协同推理",
        control_axis="网络切分点、特征通道剪枝、非线性量化 bit-depth",
        control_signal="设备/边缘算力、BER、任务精度需求、feature statistics",
        flexibility="可在不同层切分并对中间特征使用不同剪枝和量化配置；实际发送的中间特征大小可变。",
        intro="边缘语义通信不是一定要传原图，也不一定固定在某个网络层传中间特征。不同设备能力、链路误码和任务精度要求会改变最佳 split/quantization。Digital-SC 把 split 与 learned quantization 联合设计。",
        method="客户端运行 DNN 前几层得到 intermediate features；adaptive network split 选择上传层；structured pruning 减少通道；learned nonlinear quantization 将长尾特征映射为 bit sequence；服务器 dequantize 后完成剩余任务。",
        experiment="CIFAR-10、Mini-ImageNet 等分类任务；baseline 包括本地/云端推理、固定 split、线性量化、无剪枝方案；指标为 accuracy、传输 bits、BER 下精度。",
        channel="数字 bitstream 通过 QAM/BER 模型；decoder 收到可能有误 bit 后 dequantize。论文测试 BER 对任务性能的影响，但主要依赖量化/剪枝/semantic learning 提升鲁棒性。",
        result="在相近精度下降下显著降低传输开销，且自适应 split 比固定层更适合不同链路。",
        limitation="网络 split 决策与实际无线调度、时延和能耗耦合较强；bit error 的语义感知纠错仍有限。",
        not_pure="可控性来自 DNN split、pruning 和 learned quantization 结构。",
    ),
    p(
        year=2025,
        title="Joint Source-Channel Coding for Channel-Adaptive Digital Semantic Communications",
        authors="Joohyuk Park, Yongjeong Oh, Seonjung Kim, Yo-Seb Jeon",
        venue="IEEE Transactions on Cognitive Communications and Networking, 2025",
        source="IEEE",
        identifier="DOI 10.1109/TCCN.2024.3422496",
        source_url="https://doi.org/10.1109/TCCN.2024.3422496",
        pdf="papers/Joint_Source-Channel_Coding_for_Channel-Adaptive_Digital_Semantic_Communications.pdf",
        asset_prefix="joint_source_channel_coding_for_channel_adaptive_digital_semantic_communications",
        mode="数字式 channel-adaptive DSC",
        task="图像分类、重建、检索",
        control_axis="离散信道条件下的 channel-adaptive source-channel representation",
        control_signal="信道 error/erasure probability、semantic feature、任务 loss",
        flexibility="数字语义表示根据离散信道状态训练/适配；可在不同 error 条件下改变编码保护或 soft representation。",
        intro="数字 SemCom 若简单把语义特征量化成 bits，再交给传统 channel coding，会忽略 bit error 对语义特征的非均匀影响。该论文尝试把离散信道条件纳入 JSCC 训练。",
        method="语义 encoder 产生数字表示，经离散信道模型或 soft-erasure representation 传输；decoder/任务头直接面向受损 digital semantic variables 训练。不同信道条件下模型可调节表示冗余和鲁棒性。",
        experiment="图像分类、重建和检索任务；baseline 包括 fixed digital SemCom、传统 JSCC/DeepJSCC、分离压缩编码；指标为 accuracy、PSNR/MS-SSIM、retrieval metrics 与 BER/erasure 条件。",
        channel="显式建模离散信道错误，decoder 可接收 bit/soft-erasure 后的表示；相比只假设无误 index，它更接近真正数字语义链路。",
        result="在高 BER/erasure 下优于未进行 channel-adaptive 训练的数字语义系统。",
        limitation="具体适配到实际 LDPC/QAM/软信息接口仍需工程化；不同任务共享同一数字表示的泛化有待验证。",
        not_pure="关键是端到端 channel-adaptive digital JSCC 表示学习。",
    ),
    p(
        year=2025,
        title="Vision Transformer-Based Semantic Communications With Importance-Aware Quantization",
        authors="Joohyuk Park, Yongjeong Oh, Yongjune Kim, Yo-Seb Jeon",
        venue="IEEE Internet of Things Journal, 2025",
        source="IEEE",
        identifier="arXiv:2412.06038; IEEE 11038757; DOI 10.1109/JIOT.2025.3580597",
        source_url="https://ieeexplore.ieee.org/document/11038757/",
        pdf="papers/Vision_Transformer-Based_Semantic_Communications_With_Importance-Aware_Quantization.pdf",
        asset_prefix="vision_transformer_based_semantic_communications_with_importance_aware_quantizat",
        mode="数字式 ViT importance-aware quantization",
        task="图像分类、多视图分类、单目标检测",
        control_axis="ViT patch importance 决定每个 patch 的 quantization level",
        control_signal="attention score、目标通信开销、BSC/Rayleigh 错误概率",
        flexibility="不同 patch 使用不同 bit-depth；高重要 patch 分配高量化等级，背景或低重要 patch 分配低等级。",
        intro="IoT 设备上传整张图像或等精度特征会浪费资源；ViT attention 已隐含哪些 patch 对任务重要。本文把 attention importance 转换为 patch-wise bit allocation，并把通信错误纳入量化误差模型。",
        method="设备端运行 DeiT/ViT 前几层提取 patch tokens 和 attention scores；根据目标开销求解或近似求解每个 patch 的 quantization level Qi；quantized bit sequence 经 BSC/AWGN/Rayleigh 数字链路传输，服务器 dequantize 后完成任务。",
        experiment="CIFAR-10/CIFAR-100、MIRO、MVP-N、COCO2017 等分类/检测任务；baseline 包括 fixed Q、Top-k、attention threshold、learned quantization；指标为分类 accuracy、IoU、通信开销。",
        channel="显式考虑 BSC bit error 以及 Rayleigh fading 下的检测误差；decoder 收到可能错误的 bit sequence 后 dequantize。论文将 quantization error 与 communication error 一起建模。",
        result="低通信开销和有误码条件下，importance-aware quantization 比固定量化保持更高任务性能。",
        limitation="量化等级分配仍带优化色彩；它之所以纳入核心，是因为控制直接作用于 patch-wise digital semantic payload，而非单纯链路资源。",
        not_pure="可控性来自 ViT attention-driven quantization 与 bit error-aware 任务模型。",
    ),
    p(
        year=2025,
        title="Semantic Codebook-Based HARQ for Wireless Image Transmission",
        authors="Gaohong Liang, Xuefei Zhang, Ji Zhang, Yao Sun, Qimei Cui, Xiaofeng Tao",
        venue="IEEE Transactions on Communications, 2025",
        source="IEEE",
        identifier="IEEE 11145114; DOI 10.1109/TCOMM.2025.3604326",
        source_url="https://doi.org/10.1109/TCOMM.2025.3604326",
        pdf="papers/Semantic_Codebook-Based_HARQ_for_Wireless_Image_Transmission.pdf",
        asset_prefix="semantic_codebook_based_harq_for_wireless_image_transmission",
        mode="数字/混合式 semantic codebook HARQ",
        task="无线图像传输",
        control_axis="基于 semantic codebook 的错误检测与按需重传",
        control_signal="received feature 与 codebook 的语义相似度、SNR、反馈 ACK/NACK",
        flexibility="只有被判定语义失真的特征或必要增量被重传；高 SNR 或语义相似度足够时减少重传。",
        intro="传统 HARQ 检查 bit/CRC 正确性，但语义通信中某些 bit 错误可能不影响语义，某些语义特征错误又会严重伤害重建。SCB-HARQ 用语义码本检测 feature-level distortion。",
        method="发送端将图像特征映射到 semantic codebook / WSFI index-map；接收端比较收到特征与 codebook 的语义相似度，低于阈值时触发 HARQ 重传或补发 masked features。阈值和 codebook 大小控制重传开销。",
        experiment="DIV2K 训练、Kodak 测试等图像；baseline 包括 DJSCC、传统 II-HARQ、无 HARQ 的 SCB；指标为 PSNR、MS-SSIM、LPIPS、重传开销。",
        channel="AWGN 与 Rayleigh fading。错误以 feature distortion 形式体现，HARQ 不仅看 bit 错误，而看语义相似度。",
        result="低 SNR 下相对 DJSCC/传统 HARQ 有明显 PSNR/MS-SSIM 改善，高 SNR 下重传需求自然减少。",
        limitation="语义相似度阈值和 codebook 质量很关键；反馈延迟和真实 HARQ 时序未完全展开。",
        not_pure="核心是 semantic codebook error detection + HARQ 机制。",
    ),
    p(
        year=2025,
        title="Unequal Error Protection for Digital Semantic Communication With Channel Coding",
        authors="Seonjung Kim, Yongjeong Oh, Yongjune Kim, Namyoon Lee, Yo-Seb Jeon",
        venue="arXiv preprint, 2025",
        source="arXiv",
        identifier="arXiv:2508.03381",
        source_url="https://arxiv.org/abs/2508.03381",
        pdf="papers/2025_Kim_UEP_Digital_Semantic_Communication.pdf",
        asset_prefix="2025_kim_uep_digital_semantic_communication",
        mode="数字式 semantic-aware channel coding",
        task="图像传输 / 数字语义 bit 保护",
        control_axis="semantic bit importance 驱动的 unequal error protection",
        control_signal="语义 bit sensitivity、channel code rate/protection level、信道条件",
        flexibility="不同 bit 或 bit groups 使用不同保护强度；重要语义 bit 获得更多冗余，不重要 bit 可少保护。",
        intro="数字语义通信的 bit 不是等价的：某些 bit 翻转会导致语义 feature 大幅跳变，其他 bit 影响很小。传统均等信道编码忽视这种不均匀性。",
        method="先估计每个数字语义 bit 的重要性或误差敏感度，再与 channel coding 结合进行 UEP。发送端将重要 bit 分配更低码率/更强纠错，接收端译码后恢复语义表示。",
        experiment="图像传输或任务实验；baseline 包括 equal error protection、无 UEP digital SemCom、传统 LDPC/Polar 配置；指标为 PSNR/MS-SSIM/accuracy 与 BER/FER。",
        channel="显式考虑 channel coding 后残余 bit error；decoder 收到经译码的 bitstream。它直接针对 bit error 对语义质量的不均匀影响。",
        result="相同总体冗余下，UEP 比均等保护更能维持语义质量，尤其在低 SNR/高 BER 下。",
        limitation="若重要性估计与真实任务不匹配，冗余可能放错位置；复杂调制链路中的软信息利用仍可加强。",
        not_pure="虽然涉及保护资源分配，但输入是 semantic bit importance，输出是 channel coding 方案，属于语义感知链路方法。",
        core_level="边界核心",
    ),
]


RELATED = [
    {
        "year": 2024,
        "title": "OFDM-Based Digital Semantic Communication With Importance Awareness",
        "status": "related_not_core",
        "reason": "全文已下载并截图。它对数字语义 bit 做 importance-aware OFDM allocation，适合作为背景；但本次用户明确排除“建立优化模型、分配语义传输数据量”的纯优化式工作，因此不放入核心可控方法主表。",
        "source": "IEEE",
        "link": "https://doi.org/10.1109/TCOMM.2024.3397862",
    },
    {
        "year": 2026,
        "title": "Adaptive Rate Control for Semantic Communications Over LEO Satellite-Ground Links",
        "status": "screened_not_core",
        "reason": "最新检索命中。摘要显示其用 RL 在有限可见窗口内选择 SwinJSCC channel dimension，系统调度/吞吐优化色彩很强；后续可作为卫星场景候选，但本轮不作为核心方法。",
        "source": "arXiv",
        "link": "https://arxiv.org/html/2605.10095v1",
    },
    {
        "year": 2024,
        "title": "An Image Adaptive Rate Mechanism in Semantic Communication for Remote Monitoring",
        "status": "candidate_pending_fulltext",
        "reason": "IEEE Xplore 检索命中，题名和摘要与图像自适应 rate control 相关；本轮尚未完成 IEEE 全文读取，列为后续补读。",
        "source": "IEEE",
        "link": "https://ieeexplore.ieee.org/document/10518138/",
    },
    {
        "year": 2025,
        "title": "Alternate Learning-Based SNR-Adaptive Sparse Semantic Visual Transmission",
        "status": "candidate_pending_fulltext",
        "reason": "IEEE TWC 核心候选，尝试用 ieee-xplore-literature 串行下载时 DevTools websocket timeout，两次失败；未遇到 WAF/CAPTCHA，但本轮未继续高频重试。",
        "source": "IEEE",
        "link": "https://doi.org/10.1109/TWC.2024.3512652",
    },
    {
        "year": 2026,
        "title": "BidDeepSC-1.58b: 1.58-bit Bidirectional Slimmable Semantic Communication System",
        "status": "related_not_core",
        "reason": "主要控制网络宽度和低比特模型计算，而不是根据输入/任务/信道灵活改变传输语义符号数。",
        "source": "IEEE",
        "link": "https://ieeexplore.ieee.org/",
    },
    {
        "year": 2026,
        "title": "SC-AFE: A Channel-Adaptive and Feature-Enhanced Semantic Communication Method",
        "status": "candidate_pending_fulltext",
        "reason": "ScienceDirect 2026 检索命中，主题相关但未取得全文；若后续需要覆盖非 IEEE 期刊，可补读。",
        "source": "ScienceDirect",
        "link": "https://www.sciencedirect.com/science/article/abs/pii/S1047320326000829",
    },
    {
        "year": 2026,
        "title": "Towards Text Semantic Communication: Two-Phase Variable Bitrate Control Algorithm",
        "status": "candidate_pending_fulltext",
        "reason": "文本 variable bitrate 方向相关，但为 Elsevier 2026 文章，本轮未获取全文；列入后续补充。",
        "source": "ScienceDirect",
        "link": "https://www.sciencedirect.com/science/article/pii/S2352864826000611",
    },
    {
        "year": 2025,
        "title": "Semantic Adaptive Communication Based on Double-Attention Mechanism",
        "status": "excluded_mdpi",
        "reason": "MDPI/Sensors，按项目既定数字语义通信调研规则和本轮 IEEE/arXiv 优先策略，不纳入核心。",
        "source": "MDPI",
        "link": "https://www.mdpi.com/1424-8220/25/23/7201",
    },
    {
        "year": 2025,
        "title": "Channel Code-Book: Semantic Image-Adaptive Transmission in Diverse Channel Environments",
        "status": "excluded_mdpi",
        "reason": "MDPI/Sensors，主题相近但按规则排除；可作为概念参考不进入主表。",
        "source": "MDPI",
        "link": "https://www.mdpi.com/1424-8220/25/1/269",
    },
]


SEARCHES = [
    "controllable semantic communication",
    "adaptive semantic communication",
    "rate-adaptive semantic communication",
    "variable-length semantic communication",
    "semantic communication adaptive rate control",
    "DeepJSCC adaptive rate control",
    "bandwidth-adaptive DeepJSCC",
    "channel-adaptive semantic communication",
    "adaptive channel feedback semantic communication",
    "progressive semantic communication",
    "hybrid digital-analog semantic communications",
    "rate-distortion-perception controllable semantic communications",
    "multi-rate quantization semantic communication",
    "variable product quantization semantic communication",
    "importance-aware quantization semantic communication",
    "semantic communication HARQ adaptive bit rate",
    "2026 adaptive rate semantic communication",
]


def asset_path(prefix: str, kind: str) -> str | None:
    matches = sorted(ASSETS_DIR.glob(f"{prefix}_{kind}_p*.png"))
    if not matches:
        return None
    return f"assets/{matches[0].name}"


def write_manifest() -> None:
    with (ROOT / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for paper in PAPERS:
            record = {
                "title": paper["title"],
                "year": paper["year"],
                "authors": paper["authors"],
                "venue": paper["venue"],
                "source": paper["source"],
                "identifier": paper["identifier"],
                "source_url": paper["source_url"],
                "pdf": paper["pdf"],
                "download_status": "downloaded" if (ROOT / paper["pdf"]).exists() else "missing",
                "analysis_status": "included_in_controllable_report",
                "mode": paper["mode"],
                "task": paper["task"],
                "control_axis": paper["control_axis"],
                "core_level": paper["core_level"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csvs() -> None:
    with (ROOT / "included_core.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year",
                "title",
                "core_level",
                "mode",
                "task",
                "control_axis",
                "control_signal",
                "flexibility",
                "venue",
                "pdf",
            ],
        )
        writer.writeheader()
        for paper in PAPERS:
            writer.writerow({k: paper[k] for k in writer.fieldnames})
    with (ROOT / "candidate_pool.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "title", "status", "source", "reason", "link"])
        writer.writeheader()
        for paper in PAPERS:
            writer.writerow(
                {
                    "year": paper["year"],
                    "title": paper["title"],
                    "status": "included_core",
                    "source": paper["source"],
                    "reason": paper["control_axis"],
                    "link": paper["source_url"],
                }
            )
        for item in RELATED:
            writer.writerow(item)


def write_search_strategy() -> None:
    text = [
        "# Controllable Semantic Communications Search Strategy",
        "",
        "## Scope",
        "",
        "时间范围：2021 年至当前日期。主题是以“可控”为核心的语义通信方法，包含模拟式、数字式、混合数字-模拟和生成式。可控性的判断标准是：发送语义符号、latent、bit/index、反馈开销、码率、保护强度或重传行为会根据输入内容、任务、目标质量或信道条件动态变化。",
        "",
        "排除规则：纯优化式论文不纳入核心，即只建立系统优化模型、只分配语义数据量/功率/子载波、而没有新的语义编码、量化、可变码长、可训练控制器、HARQ 或 channel-adaptive codec 机制的工作，放入 related_not_core。",
        "",
        "## Keywords",
        "",
    ]
    text.extend(f"- `{q}`" for q in SEARCHES)
    text.extend(
        [
            "",
            "## Databases And Sources",
            "",
            "- IEEE Xplore：优先 IEEE 论文；PADC 已通过 ieee-xplore-literature 下载全文。SparseSBC 方向尝试下载但 DevTools websocket timeout，列入待补。",
            "- arXiv：补充 IEEE 预印本、2025/2026 最新 adaptive-rate 论文。",
            "- Semantic Scholar / Google Scholar / web search：用于关键词扩展、引用线索和最新候选发现。",
            "- 已有数字语义通信调研池：复用数字式多码率量化、VPQ、Digital-SC、channel-adaptive digital SemCom、ViT IAQ、SCB-HARQ、UEP 等全文。",
            "",
            "## Saturation Note",
            "",
            "本轮重点是“可控/自适应/可变长度”方法，而非所有 semantic communication。连续检索后新增命中主要集中在系统优化、MDPI 或全文待补项；核心方法池已覆盖 2021-2026 年模拟 DeepJSCC adaptive rate、NTSCC entropy control、MIMO/CSI adaptive、variable-length XR、generative controllable、HDA、digital multi-rate quantization、UEP/HARQ 等主要路线。",
        ]
    )
    (ROOT / "search_strategy.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def render_table() -> str:
    rows = []
    for paper in sorted(PAPERS, key=lambda x: (x["year"], x["title"])):
        rows.append(
            "<tr>"
            f"<td>{paper['year']}</td>"
            f"<td><a href='#{slug(paper['title'])}'>{esc(paper['title'])}</a></td>"
            f"<td>{esc(paper['mode'])}</td>"
            f"<td>{esc(paper['task'])}</td>"
            f"<td>{esc(paper['control_axis'])}</td>"
            f"<td>{esc(paper['flexibility'])}</td>"
            f"<td>{esc(paper['core_level'])}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>年份</th><th>论文</th><th>类型</th><th>任务</th><th>可控变量</th><th>是否不固定符号</th><th>纳入级别</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def render_nav() -> str:
    parts = ["<nav class='toc'><h2>目录</h2><a href='#overview'>总览</a><a href='#taxonomy'>路线图</a>"]
    for year in sorted({p["year"] for p in PAPERS}):
        parts.append(f"<div class='toc-year'>{year}</div>")
        for paper in sorted([p for p in PAPERS if p["year"] == year], key=lambda x: x["title"]):
            parts.append(f"<a class='paper-link' href='#{slug(paper['title'])}'>{esc(paper['title'])}</a>")
    parts.append("<a href='#related'>相关但未纳入核心</a></nav>")
    return "\n".join(parts)


def render_figures(paper: dict) -> str:
    method = asset_path(paper["asset_prefix"], "method")
    result = asset_path(paper["asset_prefix"], "result")
    figures = ["<div class='fig-grid'>"]
    for kind, path, label in [
        ("方法/架构页", method, "架构或方法图截图页"),
        ("结果页", result, "关键结果图/表截图页"),
    ]:
        if path:
            figures.append(
                "<figure>"
                f"<img src='{esc(path)}' alt='{esc(paper['title'])} {kind}'>"
                f"<figcaption>{esc(label)}。来源：{esc(paper['title'])}。</figcaption>"
                "</figure>"
            )
        else:
            figures.append(
                "<figure class='missing'><figcaption>"
                f"未找到 {esc(kind)} 截图；后续可从本地论文库补裁。"
                "</figcaption></figure>"
            )
    figures.append("</div>")
    return "\n".join(figures)


def render_paper(paper: dict) -> str:
    fields = [
        ("基本信息", f"{paper['authors']}。{paper['venue']}。来源：{paper['source']}；标识：{paper['identifier']}。<br><a href='{esc(paper['source_url'])}'>外部来源</a>。"),
        ("任务与实验", paper["experiment"]),
        ("Introduction 讲述逻辑", paper["intro"]),
        ("可控机制与方法细节", paper["method"]),
        ("不固定传输符号的具体方式", f"<b>可控轴：</b>{esc(paper['control_axis'])}<br><b>控制信号：</b>{esc(paper['control_signal'])}<br><b>符号/码率灵活性：</b>{esc(paper['flexibility'])}"),
        ("信道处理", paper["channel"]),
        ("主要结果", paper["result"]),
        ("为何不是纯优化式论文", paper["not_pure"]),
        ("局限性与 Codex 判断", paper["limitation"]),
    ]
    blocks = [f"<article id='{slug(paper['title'])}' class='paper'><h2>{esc(paper['title'])}</h2>"]
    blocks.append("<div class='chips'>" + "".join(f"<span>{esc(x)}</span>" for x in [paper["year"], paper["mode"], paper["core_level"]]) + "</div>")
    for heading, body in fields:
        blocks.append(f"<h3>{esc(heading)}</h3><p>{body}</p>")
    blocks.append(render_figures(paper))
    blocks.append("</article>")
    return "\n".join(blocks)


def render_related() -> str:
    rows = []
    for item in RELATED:
        rows.append(
            "<tr>"
            f"<td>{item['year']}</td><td>{esc(item['title'])}</td><td>{esc(item['status'])}</td>"
            f"<td>{esc(item['source'])}</td><td>{esc(item['reason'])}</td>"
            f"<td><a href='{esc(item['link'])}'>link</a></td>"
            "</tr>"
        )
    return "<section id='related'><h2>相关但未纳入核心</h2><table><thead><tr><th>年份</th><th>题名</th><th>状态</th><th>来源</th><th>原因</th><th>链接</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></section>"


def render_html() -> str:
    css = dedent(
        """
        :root { color-scheme: light; --ink:#102033; --muted:#5d6b7c; --line:#d9e2ec; --soft:#f6f8fb; --brand:#0b7468; --accent:#7a4f16; }
        * { box-sizing: border-box; }
        body { margin:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif; color:var(--ink); background:white; line-height:1.7; }
        .toc { position:fixed; inset:0 auto 0 0; width:320px; overflow:auto; border-right:1px solid var(--line); background:#fbfcfe; padding:20px 18px; }
        .toc h2 { margin:0 0 10px; font-size:18px; }
        .toc a { display:block; color:#163a5f; text-decoration:none; padding:6px 0; font-size:13px; }
        .toc a:hover { color:var(--brand); }
        .toc-year { margin-top:14px; color:var(--accent); font-weight:700; font-size:13px; }
        main { margin-left:320px; padding:36px 46px 80px; max-width:1500px; }
        h1 { font-size:34px; line-height:1.2; margin:0 0 12px; }
        h2 { font-size:25px; margin:34px 0 14px; border-bottom:2px solid var(--line); padding-bottom:7px; }
        h3 { font-size:17px; margin:20px 0 6px; color:#0d3c66; }
        p { margin:0 0 10px; }
        .lead { max-width:1050px; color:var(--muted); font-size:16px; }
        .notice { border-left:5px solid var(--brand); background:var(--soft); padding:14px 18px; margin:22px 0; }
        .chips { display:flex; gap:8px; flex-wrap:wrap; margin:8px 0 18px; }
        .chips span { border:1px solid var(--line); border-radius:999px; padding:3px 10px; color:#27445f; background:#fff; font-size:12px; }
        table { width:100%; border-collapse:collapse; margin:16px 0 26px; font-size:13px; }
        th, td { border:1px solid var(--line); padding:8px 9px; vertical-align:top; }
        th { background:#edf3f8; text-align:left; }
        article.paper { padding-top:10px; }
        .fig-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin:16px 0 30px; }
        figure { margin:0; border:1px solid var(--line); background:#fff; padding:10px; }
        figure img { width:100%; display:block; max-height:640px; object-fit:contain; background:#f8fafc; }
        figcaption { color:var(--muted); font-size:12px; margin-top:8px; }
        .route-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }
        .route { border:1px solid var(--line); padding:14px; background:#fff; }
        .route b { color:var(--brand); }
        code { background:#f0f3f7; padding:1px 4px; border-radius:4px; }
        @media (max-width: 980px) { .toc { position:static; width:auto; height:auto; border-right:0; border-bottom:1px solid var(--line); } main { margin-left:0; padding:24px 18px 60px; } .fig-grid, .route-grid { grid-template-columns:1fr; } }
        """
    )
    route_cards = [
        ("输入/内容可控", "根据图像/文本本身的语义复杂度、feature entropy、attention importance 选择发送多少 latent、patch bits 或 codebook stages。代表：PADC、Entropy-aware ARC、ViT IAQ、MSVQ。"),
        ("信道可控", "把 SNR、CSI、MIMO channel matrix 或 feedback quality 注入语义 encoder/decoder，改变 mapping、反馈长度或保留符号数。代表：CA-OFDM、SCAN、MIMO DeepJSCC、Entropy-and-Channel-Aware ARC。"),
        ("任务/质量可控", "按目标 PSNR、RDP 偏好、用户兴趣区域或 HARQ 语义阈值调整传输。代表：PADC、RDP-controllable JSCC、SCB-HARQ。"),
        ("数字多码率", "通过 VQ/MSVQ/PQ/learnable quantization 改变 index/stage/bit-depth，产生可变数字语义 payload。代表：VPQ、MRQ、CEC-MSVQ、Digital-SC。"),
        ("渐进与重传", "先传核心语义，再按质量或反馈追加残差信息。代表：IK-HARQ、PLIT-HVAE、SCB-HARQ。"),
        ("混合数字-模拟", "把关键信息数字保护，残差或细节模拟传输，随信道/率约束调整两条支路。代表：HDA-DeepSC。"),
    ]
    routes = "<div class='route-grid'>" + "".join(f"<div class='route'><b>{esc(t)}</b><p>{esc(b)}</p></div>" for t, b in route_cards) + "</div>"
    papers_html = "\n".join(render_paper(paper) for paper in sorted(PAPERS, key=lambda x: (x["year"], x["title"])))
    return dedent(
        f"""
        <!doctype html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>可控语义通信方法调研（2021-至今）</title>
          <style>{css}</style>
          <script>
            window.MathJax = {{ tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] }} }};
          </script>
          <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        </head>
        <body>
        {render_nav()}
        <main>
          <section id="overview">
            <h1>可控语义通信方法调研（2021-至今）</h1>
            <p class="lead">本页调研以“可控”为核心特点的语义通信方法：系统不再把每个输入固定映射成同样数量或同样保护强度的语义符号，而是根据输入内容、任务目标、目标质量、信道状态或反馈结果动态调整语义 latent、数字 bit/index、码率、保护强度、反馈开销或重传行为。模拟式、数字式、混合数字-模拟和生成式方法均纳入；纯系统优化/资源分配论文不纳入核心。</p>
            <div class="notice"><b>本轮结果：</b>核心/边界核心 {len(PAPERS)} 篇，相关但未纳入核心 {len(RELATED)} 篇；公开页面保留截图资产与外部来源链接，清单见 <code>manifest.jsonl</code>、<code>candidate_pool.csv</code> 和 <code>search_strategy.md</code>。</div>
            {render_table()}
          </section>
          <section id="taxonomy">
            <h2>技术路线图</h2>
            {routes}
            <p class="notice">判断一篇论文是否属于本页核心，不看题名是否出现 adaptive/controllable，而看方法是否真的让语义传输表示或链路处理随输入、任务或信道变化。只在外层建立优化模型、分配功率/子载波/语义数据量，而没有新的语义 codec、可变长度编码、可训练控制器、量化/码本或 HARQ 机制的工作，被放入相关但非核心。</p>
          </section>
          <section id="papers">
            <h2>逐篇分析</h2>
            {papers_html}
          </section>
          {render_related()}
        </main>
        </body>
        </html>
        """
    )


def main() -> None:
    write_manifest()
    write_csvs()
    write_search_strategy()
    (ROOT / "index.html").write_text(render_html(), encoding="utf-8")


if __name__ == "__main__":
    main()
