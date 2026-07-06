from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug(value: str) -> str:
    out = []
    last = False
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
            last = False
        elif not last:
            out.append("-")
            last = True
    return "".join(out).strip("-")


def paper(
    year: int,
    title: str,
    authors: str,
    venue: str,
    link: str,
    theme: str,
    task: str,
    content: str,
    contribution: str,
    relation: str,
    status: str = "included",
    notes: str = "",
) -> dict:
    return {
        "year": year,
        "title": title,
        "authors": authors,
        "venue": venue,
        "link": link,
        "theme": theme,
        "task": task,
        "content": content,
        "contribution": contribution,
        "relation": relation,
        "status": status,
        "notes": notes,
    }


PAPERS = [
    paper(
        2021,
        "Toward Wisdom-Evolutionary and Primitive-Concise 6G: A New Paradigm of Semantic Communication Networks",
        "Ping Zhang, Wenjun Xu, Hui Gao, Kai Niu, et al.",
        "Engineering, 2021",
        "https://doi.org/10.1016/j.eng.2021.11.003",
        "总体范式 / 6G 语义网络",
        "6G 语义通信网络愿景",
        "提出“智慧演进、原语简约”的 6G 语义通信网络范式，主张通信系统不再只传 bit，而要围绕语义、知识、任务和智能体协作设计。论文给出 semantic communication network 的宏观架构、语义信息流、知识驱动通信和网络智能演进路线。",
        "是牛凯团队语义通信方向的早期高影响愿景文，奠定后续“语义编码、语义信息理论、语义原生空口”的叙事框架。",
        "奠基/综述性论文，不是具体物理层算法。",
    ),
    paper(
        2021,
        "A Novel Deep Learning Architecture for Wireless Image Transmission",
        "Sixian Wang, Jincheng Dai, Shengshi Yao, Kai Niu, Ping Zhang",
        "IEEE GLOBECOM, 2021",
        "https://doi.org/10.1109/GLOBECOM46510.2021.9685036",
        "图像 JSCC / 语义通信前身",
        "无线图像端到端传输",
        "构建深度学习图像传输架构，用神经网络联合完成源压缩与信道抗噪，直接优化重建质量。虽然题名未显式使用 semantic communication，但后续 NTSCC/WITT/SwinJSCC 都沿着这条 neural JSCC 作为语义传输技术基础发展。",
        "把图像传输从传统压缩+信道编码推向端到端 learned JSCC，是牛凯团队语义图像通信路线的前驱工作。",
        "边界相关：更偏 neural JSCC，不以语义信息理论为主体。",
        status="boundary",
    ),
    paper(
        2021,
        "Semantic Coded Transmission: Architecture, Methodology, and Challenges",
        "Jincheng Dai, Ping Zhang, Kai Niu, Sixian Wang, Zhongwei Si, Xiaoqi Qin",
        "arXiv:2112.03093, 2021",
        "https://arxiv.org/abs/2112.03093",
        "总体框架 / 语义编码",
        "语义编码架构",
        "提出 semantic coded transmission 的体系化框架，强调语义编码不是简单删除 bit，而是从源中提取与任务/感知相关的语义特征，再结合信道特性做联合传输。论文讨论图像、文本等源的语义特征、语义失真、联合源信道编码和挑战。",
        "这是后续 IEEE Wireless Communications 文章“Communication Beyond Transmitting Bits”的预印本/相关版本之一。",
        "框架性论文，适合放在路线源头。",
    ),
    paper(
        2022,
        "A Paradigm Shift toward Semantic Communications",
        "Kai Niu, Jincheng Dai, Shengshi Yao, Sixian Wang, Zhongwei Si, Xiaoqi Qin, Ping Zhang",
        "IEEE Communications Magazine, 2022",
        "https://doi.org/10.1109/MCOM.001.2200099",
        "总体范式 / 语义通信",
        "语义通信范式综述",
        "系统阐述 semantic communication 为什么是从 bit 可靠传输向 meaning/task 有效传输的范式转变。论文讨论语义信息、语义编码、语义噪声、系统结构和典型应用，并把深度学习 JSCC 与语义编码联系起来。",
        "这是牛凯作为第一作者的语义通信纲领性论文，明确提出研究方向、问题和路线。",
        "高层综述/观点论文，不提供单一算法实现。",
    ),
    paper(
        2022,
        "Communication Beyond Transmitting Bits: Semantics-Guided Source and Channel Coding",
        "Jincheng Dai, Ping Zhang, Kai Niu, Sixian Wang, Zhongwei Si, Xiaoqi Qin",
        "IEEE Wireless Communications, 2023; arXiv first circulated 2022",
        "https://doi.org/10.1109/MWC.017.2100705",
        "总体框架 / 语义编码",
        "语义引导的源信道编码",
        "把 semantic coding 定义为从源信号中提取跨空间/时间的语义特征，并设计源信道编码方法传输这些特征。论文用图像、视频、语音等例子说明 neural JSCC 如何成为语义通信的技术承载，同时强调语义失真度量、语义噪声和编码结构。",
        "连接“语义通信概念”与“可实现的神经源信道编码方法”，是牛凯团队工程路线的重要综述。",
        "框架/综述性质强。",
    ),
    paper(
        2022,
        "Nonlinear Transform Source-Channel Coding for Semantic Communications",
        "Jincheng Dai, Sixian Wang, Kailin Tan, Zhongwei Si, Xiaoqi Qin, Kai Niu, Ping Zhang",
        "IEEE Journal on Selected Areas in Communications, 2022",
        "https://doi.org/10.1109/JSAC.2022.3180802",
        "图像语义传输 / NTSCC",
        "图像重建",
        "提出 NTSCC：先用 nonlinear analysis transform 把图像映射到 latent 语义空间，再在 latent 空间做深度 JSCC。论文引入 hyperprior/entropy model 估计 latent 条件分布，让不同 latent 具有自适应传输资源，并用 hyperprior 辅助解码端恢复。",
        "这是牛凯团队图像语义通信方向的代表作之一，把 learned image compression 的概率建模与 DeepJSCC 结合，解决大尺寸图像和自适应 rate 的问题。",
        "以重建质量为目标，语义任务性主要由感知/图像质量体现。",
    ),
    paper(
        2022,
        "Semantic Coding for Text Transmission: An Iterative Design",
        "Shengshi Yao, Kai Niu, Sixian Wang, Jincheng Dai",
        "IEEE Transactions on Cognitive Communications and Networking, 2022",
        "https://doi.org/10.1109/TCCN.2022.3192407",
        "文本语义通信",
        "文本传输",
        "面向文本传输提出迭代式 semantic coding。系统通过语义编码器压缩句子含义，再经信道传输和语义解码恢复文本；训练中不断改进编码/解码以保持语义相似而非逐字一致。",
        "体现牛凯团队早期从图像扩展到文本的语义通信尝试，强调语义相似性和迭代优化。",
        "主要关注文本语义恢复，和后续同义映射理论有自然连接。",
    ),
    paper(
        2022,
        "Distributed Image Transmission Using Deep Joint Source-Channel Coding",
        "Sixian Wang, Ke Yang, Jincheng Dai, Kai Niu",
        "IEEE ICASSP, 2022",
        "https://doi.org/10.1109/ICASSP43922.2022.9746268",
        "分布式图像 JSCC",
        "相关图像/多源图像传输",
        "研究多幅相关图像的分布式 learned JSCC。多个发送端分别编码相关图像，接收端联合利用相关性恢复，目标是降低总传输资源并提升重建质量。",
        "是后续分布式图像语义通信和 correlated images NTSCC 的前身。",
        "题名不显式写 semantic，但属于 semantic JSCC 技术线。",
        status="boundary",
    ),
    paper(
        2022,
        "Perceptual Learned Source-Channel Coding for High-Fidelity Image Semantic Transmission",
        "Jun Wang, Sixian Wang, Jincheng Dai, Zhongwei Si, Dekun Zhou, Kai Niu",
        "IEEE GLOBECOM, 2022",
        "https://doi.org/10.1109/GLOBECOM48099.2022.10001359",
        "图像语义传输 / 感知质量",
        "高保真图像重建",
        "把 perceptual loss 引入 learned source-channel coding，目标不只是提高 PSNR，而是让低码率/低 SNR 下的视觉感知更自然。论文通常结合对抗/感知损失与 JSCC，改善语义图像传输中的高频细节。",
        "将语义通信评价从像素失真推进到 perceptual quality，为后续 RDP-controllable JSCC 铺垫。",
        "生成/感知质量可能带来幻觉风险。",
    ),
    paper(
        2022,
        "Resolution-Adaptive Source-Channel Coding for End-to-End Wireless Image Transmission",
        "Ke Yang, Sixian Wang, Kailin Tan, Jincheng Dai, Dekun Zhou, Kai Niu",
        "IEEE GLOBECOM, 2022",
        "https://doi.org/10.1109/GLOBECOM48099.2022.10001465",
        "图像 JSCC / 分辨率自适应",
        "多分辨率图像传输",
        "解决固定输入分辨率 neural JSCC 难以处理多分辨率图像的问题，通过分辨率自适应编码/解码结构让一个模型适应不同图像尺寸和信道条件。",
        "是 WITT/SwinJSCC 多尺度、多 rate 自适应图像语义传输路线的一部分。",
        "边界相关：更偏 neural image transmission。",
        status="boundary",
    ),
    paper(
        2022,
        "Versatile Semantic Coded Transmission over MIMO Fading Channels",
        "Shengshi Yao, Sixian Wang, Jincheng Dai, Kai Niu, Ping Zhang",
        "arXiv:2210.16741, 2022",
        "https://arxiv.org/abs/2210.16741",
        "MIMO 语义传输",
        "图像/语义特征在 MIMO fading 信道中的传输",
        "把 semantic coded transmission 扩展到 MIMO fading 场景，关注语义特征如何在多天线信道中映射、传输和恢复。核心是让语义编码适应空间信道，而不是把 MIMO 只当作传统 bit pipe。",
        "补足牛凯团队语义通信在 MIMO 物理层场景中的应用。",
        "未见同名正式期刊版本，按 arXiv 候选纳入。",
    ),
    paper(
        2022,
        "Wireless Deep Video Semantic Transmission",
        "Sixian Wang, Jincheng Dai, Zijian Liang, Kai Niu, Zhongwei Si, Chao Dong, Xiaoqi Qin, Ping Zhang",
        "IEEE Journal on Selected Areas in Communications, 2023; arXiv 2022",
        "https://doi.org/10.1109/JSAC.2022.3221977",
        "视频语义传输",
        "无线视频传输",
        "面向视频源提出深度语义传输系统，利用视频帧间时空相关性提取语义表示，并通过无线信道端到端传输。相比传统视频压缩+信道编码，模型避免 cliff effect，并在低 SNR 下保持较好感知质量。",
        "把牛凯团队图像语义通信扩展到视频，是多媒体语义通信的重要代表。",
        "更强调重建/感知质量而非下游视频理解任务。",
    ),
    paper(
        2022,
        "Wireless Deep Speech Semantic Transmission",
        "Zixuan Xiao, Shengshi Yao, Jincheng Dai, Sixian Wang, Kai Niu, Ping Zhang",
        "IEEE ICASSP, 2023; arXiv 2022",
        "https://doi.org/10.1109/ICASSP49357.2023.10094680",
        "语音语义传输",
        "无线语音传输",
        "构建深度语音语义传输系统，编码器提取 speech waveform/语音语义相关表示，经无线信道传输后由解码器恢复语音。目标是低带宽、抗噪声、保持语音可懂度和质量。",
        "是牛凯团队从图像/视频扩展到语音源的重要工作。",
        "早期版本偏 waveform reconstruction，后续 SSC/packet-loss speech 进一步走向语义压缩和抗丢包。",
    ),
    paper(
        2022,
        "WITT: A Wireless Image Transmission Transformer for Semantic Communications",
        "Ke Yang, Sixian Wang, Jincheng Dai, Kailin Tan, Kai Niu, Ping Zhang",
        "IEEE ICASSP, 2023; arXiv 2022",
        "https://doi.org/10.1109/ICASSP49357.2023.10094735",
        "Transformer 图像语义传输",
        "无线图像传输",
        "把 Swin/Transformer 结构引入无线图像语义传输，用注意力机制建模长程依赖，并用 channel-state/spatial modulation 适配信道条件。相比 CNN DeepJSCC，WITT 在高分辨率图像和多 SNR 条件下更稳。",
        "是牛凯团队 Transformer-based semantic image transmission 的关键节点。",
        "仍是连续 latent JSCC，非严格数字语义通信。",
    ),
    paper(
        2022,
        "Variational Speech Waveform Compression to Catalyze Semantic Communications",
        "Shengshi Yao, Zixuan Xiao, Sixian Wang, Jincheng Dai, Kai Niu, Ping Zhang",
        "IEEE WCNC, 2023; arXiv 2022",
        "https://doi.org/10.1109/WCNC55385.2023.10118921",
        "语音语义压缩",
        "speech waveform 压缩与语义传输",
        "用变分建模压缩语音 waveform，学习低维潜变量并通过信道传输。目标是在低码率下保持语音质量和可懂度，为语音语义通信提供源表示。",
        "把 VAE/变分压缩引入 speech semantic communication。",
        "语义评价仍较依赖语音质量指标。",
    ),
    paper(
        2022,
        "A Demo of Semantic Communication: Rosefinch",
        "Hao Dong, Weijie Yue, Kai Niu",
        "IEEE WCSP, 2022",
        "https://doi.org/10.1109/WCSP55476.2022.10039193",
        "系统演示",
        "语义通信 Demo 系统",
        "展示 Rosefinch 语义通信原型系统，侧重演示语义编码/解码在真实通信流程中的工作方式和效果。",
        "说明团队不仅做理论/算法，也尝试构建可展示系统。",
        "Demo 性质，算法细节有限。",
        status="boundary",
    ),
    paper(
        2023,
        "Toward Adaptive Semantic Communications: Efficient Data Transmission via Online Learned Nonlinear Transform Source-Channel Coding",
        "Jincheng Dai, Sixian Wang, Ke Yang, Kailin Tan, Xiaoqi Qin, Zhongwei Si, Kai Niu, Ping Zhang",
        "IEEE Journal on Selected Areas in Communications, 2023",
        "https://doi.org/10.1109/JSAC.2023.3288246",
        "自适应图像语义传输",
        "图像传输",
        "在 NTSCC 基础上引入 online learned adaptation，使模型能针对当前源图像和信道状态快速适配，而不是只依赖离线训练的固定模型。目标是在源分布/信道偏移时获得更高传输效率。",
        "将牛凯团队图像语义通信路线推进到 instance/channel adaptive。",
        "在线优化可能带来额外计算和同步开销。",
    ),
    paper(
        2023,
        "Improved Nonlinear Transform Source-Channel Coding to Catalyze Semantic Communications",
        "Sixian Wang, Jincheng Dai, Xiaoqi Qin, Zhongwei Si, Kai Niu, Ping Zhang",
        "IEEE Journal of Selected Topics in Signal Processing, 2023",
        "https://doi.org/10.1109/JSTSP.2023.3304140",
        "改进 NTSCC",
        "图像传输",
        "改进 NTSCC 的概率建模、contextual entropy 和 rate/channel adaptation。用响应网络和 latent feature editing 提升多 rate、多 SNR 下的传输质量。",
        "补强 NTSCC 在多条件部署中的适应性，是图像语义传输主线论文。",
        "主要以重建/感知为目标。",
    ),
    paper(
        2023,
        "Learned Image Transmission over MIMO Fading Channels",
        "Shengshi Yao, Sixian Wang, Jincheng Dai, Kai Niu",
        "IEEE PIMRC, 2023",
        "https://doi.org/10.1109/PIMRC56721.2023.10293784",
        "MIMO 图像 JSCC",
        "MIMO fading 图像传输",
        "研究 learned image transmission 在 MIMO fading 信道中的编码、空间映射和接收恢复，关注如何让神经 JSCC 处理多天线物理信道。",
        "为后续 MIMO/CSI-aware semantic communication 提供基础。",
        "边界相关：题名不显式 semantic，但在语义 JSCC 技术线内。",
        status="boundary",
    ),
    paper(
        2023,
        "Learned Image Transmission Toward Machine-Type Semantic Communications",
        "Kailin Tan, Jincheng Dai, Sixian Wang, Ke Yang, Kai Niu",
        "IEEE PIMRC, 2023",
        "https://doi.org/10.1109/PIMRC56721.2023.10294032",
        "机器任务语义传输",
        "面向机器视觉的图像传输",
        "从 human-oriented 重建转向 machine-type semantic communication，关注传输表示对下游机器任务的有效性，而非只优化像素质量。",
        "体现牛凯团队从重建型 SemCom 向任务型 SemCom 的过渡。",
        "具体任务和泛化范围需结合全文进一步核查。",
    ),
    paper(
        2023,
        "Learned Source and Channel Coding for Talking-Head Semantic Transmission",
        "Weijie Yue, Jincheng Dai, Sixian Wang, Zhongwei Si, Kai Niu",
        "IEEE WCNC, 2023",
        "https://doi.org/10.1109/WCNC55385.2023.10118851",
        "人脸/视频语义传输",
        "talking-head 传输",
        "针对 talking-head 视频，学习源信道联合编码，利用人脸结构和语义运动信息减少传输量。接收端恢复说话人头部视频内容。",
        "展示语义通信在结构化视频/虚拟人场景中的应用。",
        "场景专用性强。",
    ),
    paper(
        2023,
        "Model Division Multiple Access for Semantic Communications",
        "Ping Zhang, Xiaodong Xu, Chen Dong, Kai Niu, et al.",
        "Frontiers of Information Technology & Electronic Engineering, 2023",
        "https://doi.org/10.1631/FITEE.2300196",
        "语义接入 / 网络架构",
        "多模型/多用户语义接入",
        "提出 MDMA：把模型作为语义通信网络中的接入和资源组织对象，面向多用户、多任务、多模型协作。区别于传统 TDMA/FDMA/CDMA，MDMA 关注语义模型分工、模型复用和任务服务。",
        "从网络接入层面拓展语义通信，说明牛凯团队不仅做编码，还做语义网络架构。",
        "概念/框架性强，工程标准化仍需发展。",
    ),
    paper(
        2023,
        "NeurJSCC Enabled Semantic Communications: Paradigms, Applications, and Potentials",
        "Sixian Wang, Jincheng Dai, Xiaoqi Qin, Kai Niu, Ping Zhang",
        "arXiv:2303.14640, 2023",
        "https://arxiv.org/abs/2303.14640",
        "Neural JSCC 综述/框架",
        "语义通信中的 neural JSCC",
        "系统总结 neural JSCC 作为 semantic communication 关键技术的范式、应用与潜力，区分显式语义编码与隐式神经编码，并讨论图像、语音、视频等多模态应用。",
        "为团队系列 NeurJSCC 工作做方法论归纳。",
        "综述/观点，非单独算法。",
    ),
    paper(
        2023,
        "Semantic Information Processing for Interoperability in the Industrial Internet of Things",
        "Kai Niu and coauthors",
        "Fundamental Research, 2023",
        "https://doi.org/10.1016/j.fmre.2023.06.003",
        "工业互联网语义互操作",
        "IIoT 语义信息处理",
        "从工业互联网互操作角度讨论语义信息处理，关注异构设备、协议和数据之间的语义对齐与表示，使系统能够理解而不仅是传输数据。",
        "扩展语义通信到工业互联网和互操作场景。",
        "更偏语义信息处理/工业应用，通信物理层较弱。",
        status="boundary",
    ),
    paper(
        2024,
        "Semantics-Division Duplexing: A Novel Full-Duplex Paradigm",
        "Kai Niu, Zijian Liang, Chao Dong, Jincheng Dai, Zhongwei Si, Ping Zhang",
        "IEEE Wireless Communications, 2024",
        "https://doi.org/10.1109/MWC.013.2300372",
        "语义网络范式 / 全双工",
        "语义分割双工",
        "提出 semantics-division duplexing，把上下行或双向通信的划分从频率/时间/码域扩展到语义域。核心思想是利用语义信息之间的差异或互补性实现同时传输和干扰管理。",
        "体现牛凯团队把语义通信推广到 MAC/duplexing 层。",
        "理论与工程实现仍需更多协议验证。",
    ),
    paper(
        2024,
        "A Mathematical Theory of Semantic Communication",
        "Kai Niu, Ping Zhang",
        "arXiv:2401.13387 / TechRxiv, 2024; SpringerBriefs, 2025",
        "https://arxiv.org/abs/2401.13387",
        "语义信息理论",
        "语义源编码、信道编码、率失真理论",
        "以 synonymous mapping 为核心，把一个语义对象对应多个句法表示形式这一事实形式化。定义 semantic entropy、up/down semantic mutual information、semantic capacity、semantic rate-distortion function，并证明语义源编码、语义信道编码、语义率失真编码定理。",
        "这是牛凯近年来最核心的理论工作，试图建立可与 Shannon 信息论对应的 Semantic Information Theory。",
        "模型抽象度高，实际任务中的同义集合构造仍是难点。",
    ),
    paper(
        2024,
        "Semantic Huffman Coding Using Synonymous Mapping",
        "Jin Xu, Kai Niu, Zijian Liang, Ping Zhang",
        "arXiv:2401.14634, 2024",
        "https://arxiv.org/abs/2401.14634",
        "同义映射 / 语义源编码",
        "语义无损源编码",
        "基于 synonymous mapping 设计 Semantic Huffman Coding。传统 Huffman 对句法符号编码，Semantic Huffman 允许同义句法表示归入同一语义集合，从而降低所需编码长度。",
        "把 SIT 中的 synonymous mapping 落到具体源编码算法。",
        "依赖语义集合/同义关系的可获得性。",
    ),
    paper(
        2024,
        "Semantic Arithmetic Coding Using Synonymous Mappings",
        "Zijian Liang, Kai Niu, Jin Xu, Ping Zhang",
        "Entropy, 2025; arXiv 2024",
        "https://doi.org/10.3390/e27040429",
        "同义映射 / 语义源编码",
        "语义算术编码",
        "将 arithmetic coding 从句法消息扩展到语义消息：同义映射把多个句法序列聚合为语义同义集合，编码器只需区分语义集合而非每个具体句法表达。论文分析平均码长和语义编码增益。",
        "是 Semantic Huffman 后更精细的语义源编码算法。",
        "实际系统需要可靠的 synonymous set 构造和语义判别器。",
    ),
    paper(
        2024,
        "Rate-Distortion-Perception Optimized Neural Speech Transmission System for High-Fidelity Semantic Communications",
        "Shengshi Yao, Zixuan Xiao, Kai Niu",
        "Sensors, 2024",
        "https://doi.org/10.3390/s24103169",
        "语音语义传输 / RDP",
        "高保真语音传输",
        "把 rate-distortion-perception 思想用于神经语音传输，兼顾码率、失真和感知质量，使低码率语音语义传输保持自然度和可懂度。",
        "把 RDP 框架从图像扩展到语音语义通信。",
        "MDPI/Sensors 论文，本项目其他数字语义调研默认排除 MDPI；人物全景调研中保留并标注。",
        status="included_mdpi",
    ),
    paper(
        2024,
        "TD-PLC: A Semantic-Aware Speech Encoding for Improved Packet Loss Concealment",
        "Jinghong Zhang, Zugang Zhao, Yonghui Liu, Jianbing Liu, Zhiqiang He, Kai Niu",
        "INTERSPEECH, 2024",
        "https://doi.org/10.21437/Interspeech.2024-823",
        "语音抗丢包",
        "packet loss concealment",
        "提出语义感知语音编码以改善丢包隐藏。发送端/接收端利用语音语义或时序上下文在 packet loss 后恢复更自然的语音。",
        "与后续 Error-Resilient Speech SemCom 和 SSC 形成语音语义通信子线。",
        "偏语音编码/PLC，通信语义理论较弱。",
        status="boundary",
    ),
    paper(
        2024,
        "Towards Task-Scalable Semantic Communications: A Preprocessing Enhanced Image Transmission Framework",
        "Yanpeng Lu, Kai Niu, Jincheng Dai",
        "IEEE WCSP, 2024",
        "https://doi.org/10.1109/WCSP62071.2024.10827630",
        "任务可扩展图像语义传输",
        "多任务/下游任务图像传输",
        "提出 preprocessing enhanced image transmission，使传输内容更适合不同下游任务，目标是让一次图像语义传输可扩展到多任务而非只服务单一重建目标。",
        "体现牛凯团队对 task-scalable SemCom 的探索。",
        "需要进一步核查具体任务和 preprocessing 结构。",
    ),
    paper(
        2024,
        "AdaJSCC: Instance-Adaptive Joint Source-Channel Coding for Wireless Image Transmission",
        "Tianjian Dang, Shengshi Yao, Siye Wang, Kai Niu, Zhenyu Liu, Jincheng Dai",
        "IEEE GLOBECOM Workshops, 2024",
        "https://doi.org/10.1109/GCWkshp64532.2024.11100771",
        "自适应图像 JSCC",
        "instance-adaptive 图像传输",
        "根据输入实例复杂度和信道条件自适应调整 JSCC 表示/码率，使不同图像获得不同传输资源。",
        "和 PADC、Entropy-aware adaptive-rate 等工作同属可控语义通信路线。",
        "workshop 版本，细节相对短。",
    ),
    paper(
        2025,
        "Intellicise Wireless Networks From Semantic Communications: A Survey, Research Issues, and Challenges",
        "Ping Zhang, Wenjun Xu, Yiming Liu, Xiaoqi Qin, Kai Niu, et al.",
        "IEEE Communications Surveys & Tutorials, 2025",
        "https://doi.org/10.1109/COMST.2024.3443193",
        "综述 / 语义无线网络",
        "语义通信到智能简约网络",
        "全面综述 semantic communications 如何驱动 intellicise wireless networks，覆盖语义信息理论、语义编码、多模态任务、网络架构、资源管理、标准化与开放问题。",
        "是牛凯团队参与的高影响综述，系统总结语义通信网络方向。",
        "综述论文。",
    ),
    paper(
        2025,
        "Rate-Distortion-Perception Controllable Joint Source-Channel Coding for High-Fidelity Generative Semantic Communications",
        "Kailin Tan, Jincheng Dai, Zhenyu Liu, Sixian Wang, Xiaoqi Qin, Wenjun Xu, Kai Niu, Ping Zhang",
        "IEEE Transactions on Cognitive Communications and Networking, 2025",
        "https://doi.org/10.1109/TCCN.2024.3511960",
        "生成式图像语义传输 / RDP 可控",
        "高保真图像生成式传输",
        "提出 RDP-controllable JSCC，在 rate、distortion、perception 之间可控权衡，并引入内容/兴趣区域控制以提升用户关心区域的重建质量。",
        "体现牛凯团队进入生成式语义通信和可控 SemCom。",
        "生成式重建可能引入非真实细节。",
    ),
    paper(
        2025,
        "Distributed Image Semantic Communication via Nonlinear Transform Coding",
        "Yufei Bo, Meixia Tao, Kai Niu",
        "arXiv:2506.07391, 2025; IEEE Transactions on Communications, 2026",
        "https://arxiv.org/abs/2506.07391",
        "分布式图像语义传输 / NTC",
        "相关图像多终端传输",
        "把 nonlinear transform coding 用于 distributed image semantic communication，利用多视角/多源相关性降低总体传输开销。系统在各发送端编码相关图像，接收端联合恢复。",
        "把 NTSCC/NTC 思想扩展到相关图像和分布式场景。",
        "需要考虑多终端同步与相关性建模成本。",
    ),
    paper(
        2025,
        "Error-Resilient Semantic Communication for Speech Transmission over Packet-Loss Networks",
        "Zhuohang Han, Jincheng Dai, Shengshi Yao, Junyi Wang, Yanlong Li, Kai Niu, Wenjun Xu, Ping Zhang",
        "arXiv:2512.08203, 2025",
        "https://arxiv.org/abs/2512.08203",
        "语音语义通信 / 抗丢包",
        "packet-loss 网络语音传输",
        "面向实时语音在 packet loss 网络中的传输，设计端到端语义编码与错误恢复机制，使丢包后仍能保持语音语义和可懂度。",
        "延续 TD-PLC 与 speech SemCom，强调实际网络 packet loss 而非单纯 AWGN。",
        "预印本，正式发表状态待跟踪。",
    ),
    paper(
        2025,
        "Extended Blahut-Arimoto Algorithm for Semantic Rate-Distortion Function",
        "Yuxin Han, Yang Liu, Yaping Sun, Kai Niu, Nan Ma, Shuguang Cui, Ping Zhang",
        "Entropy, 2025",
        "https://doi.org/10.3390/e27060651",
        "语义率失真理论",
        "计算 semantic rate-distortion function",
        "把经典 Blahut-Arimoto 算法扩展到 semantic rate-distortion function，用于求解语义失真约束下的最小编码率。该工作为 SIT 中的语义率失真提供数值计算工具。",
        "理论工具论文，服务于牛凯的 Mathematical Theory 路线。",
        "MDPI/Entropy，人物全景保留；需注意期刊来源。",
        status="included_mdpi",
    ),
    paper(
        2025,
        "NeRFCom: Feature Transform Coding Meets Neural Radiance Field for Free-View 3-D Scene Semantic Transmission",
        "Weijie Yue, Zhongwei Si, Bolin Wu, Sixian Wang, Xiaoqi Qin, Kai Niu, Jincheng Dai, Ping Zhang",
        "IEEE Communications Letters, 2025",
        "https://doi.org/10.1109/LCOMM.2025.3544882",
        "3D 场景语义传输",
        "free-view NeRF/3D scene transmission",
        "把 feature transform coding 与 Neural Radiance Field 结合，只传输支持自由视角重建的场景语义/特征表示，而非完整视频/图像序列。",
        "拓展语义通信到 3D/XR 场景。",
        "场景建模和渲染计算成本较高。",
    ),
    paper(
        2025,
        "Neural Coding Is Not Always Semantic: Toward the Standardized Coding Workflow in Semantic Communications",
        "Hai-Long Qin, Jincheng Dai, Sixian Wang, Xiaoqi Qin, Shuo Shao, Kai Niu, Wenjun Xu, Ping Zhang",
        "IEEE Communications Standards Magazine, 2025",
        "https://doi.org/10.1109/MCOMSTD.2025.3598111",
        "标准化 / 语义编码边界",
        "语义通信工作流",
        "指出并非所有 neural coding 都自动等于 semantic coding，强调语义通信需要清晰的语义对象、任务、语义度量和标准化工作流。论文提出区分语义抽取、语义表示、语义传输和语义评价的流程。",
        "对牛凯团队早期 neural JSCC 路线进行反思和规范化，是语义通信标准化的重要观点文。",
        "偏标准/观点，非算法。",
    ),
    paper(
        2025,
        "PCST: Geometry-Based Point Cloud Semantic Transmission for Low-Latency XR Communications",
        "Shouye Lyu, Tianjian Dang, Zhenyu Liu, Shuo Shao, Kai Niu, Jincheng Dai",
        "IEEE SPAWC, 2025",
        "https://doi.org/10.1109/SPAWC66079.2025.11143324",
        "点云/XR 语义传输",
        "低时延点云传输",
        "面向 XR 的点云语义传输，利用几何结构提取关键语义/几何信息以降低传输时延，同时保持场景感知质量。",
        "拓展到 3D point cloud 和 XR 低时延通信。",
        "会议论文，具体大规模场景泛化需继续跟踪。",
    ),
    paper(
        2025,
        "SSC: 106 bit/s Ultra-Low Bitrate Semantic Speech Coding",
        "Renjie Jia, Zhiqiang He, Kai Niu, Zixuan Xiao, Yonghui Liu, Jianbing Liu",
        "IEEE ICASSP, 2025",
        "https://doi.org/10.1109/ICASSP49660.2025.10889978",
        "语音语义编码",
        "超低码率语音编码",
        "提出 106 bit/s 级别的 semantic speech coding，目标是在极低码率下保留语音可懂度和语义内容，而不是传统 waveform 精确重建。",
        "是牛凯团队语音语义编码方向的重要低码率结果。",
        "语音自然度、说话人保持与语义准确性之间存在权衡。",
    ),
    paper(
        2025,
        "Semantic Information Theory and Applications",
        "Meixia Tao, Kai Niu, Youlong Wu",
        "Entropy, 2025",
        "https://doi.org/10.3390/e27111092",
        "语义信息理论综述/专题",
        "SIT 与应用",
        "总结 semantic information theory 的概念、方法和应用，包括 synonymous mapping、语义熵、语义容量、语义率失真及其在通信系统中的潜在应用。",
        "与 Mathematical Theory 互补，为 SIT 方向提供综述/应用导引。",
        "MDPI/Entropy；人物全景保留。",
        status="included_mdpi",
    ),
    paper(
        2025,
        "Semantic Markov Chain Using Synonymous Mapping",
        "Kai Niu and coauthors",
        "Tsinghua Science and Technology, 2025",
        "https://doi.org/10.26599/TST.2025.9010064",
        "语义随机过程 / 同义映射",
        "semantic Markov chain",
        "基于 synonymous mapping 定义或分析 semantic Markov chain，把经典随机过程推广到语义等价类层面。核心是研究语义状态转移，而不是具体句法状态转移。",
        "推进 SIT 从静态语义变量到动态语义过程。",
        "适用到真实数据/任务时需要构造语义状态空间。",
    ),
    paper(
        2025,
        "SwinJSCC: Taming Swin Transformer for Deep Joint Source-Channel Coding",
        "Ke Yang, Sixian Wang, Jincheng Dai, Xiaoqi Qin, Kai Niu, Ping Zhang",
        "IEEE Transactions on Cognitive Communications and Networking, 2025",
        "https://doi.org/10.1109/TCCN.2024.3424842",
        "Transformer JSCC / 图像语义传输",
        "无线图像传输",
        "建立 Swin Transformer 版 deep JSCC backbone，并用 channel state 和 target rate 条件调制 latent 表示，使一个模型可适配不同信道和码率。相对 CNN JSCC，SwinJSCC 更适合高分辨率图像。",
        "是 WITT 的加强/正式扩展，成为牛凯团队 neural JSCC 的开源基准之一。",
        "仍是连续 latent；数字链路兼容性需额外设计。",
    ),
    paper(
        2025,
        "Synonymity-Based Semantic Coding for Efficient Speech Compression",
        "Shanhui Gan, Zijian Liang, Kai Niu, Ping Zhang",
        "INTERSPEECH, 2025",
        "https://doi.org/10.21437/Interspeech.2025-2483",
        "同义性 / 语音压缩",
        "语音语义压缩",
        "把 synonymity/synonymous mapping 思想用于语音压缩：只需保持语音的语义等价或可理解内容，而不是逐样本重建 waveform，从而降低码率。",
        "将 SIT 同义映射理论落到 speech coding。",
        "需要严格定义语音语义同义集合。",
    ),
    paper(
        2025,
        "Synonymous Variational Inference for Perceptual Image Compression",
        "Zijian Liang, Kai Niu, Changshuo Wang, Jin Xu, Ping Zhang",
        "ICML, 2025",
        "https://proceedings.mlr.press/v267/liang25m.html",
        "同义性 / 感知压缩",
        "图像感知压缩",
        "提出 Synonymous Variational Inference，将感知压缩解释为恢复同义集合中的任意可接受样本，而非原始样本本身。用 SVLBO 建立 synset-oriented compression 的可优化目标。",
        "把 SIT 的同义集合思想与机器学习压缩/RDP 连接起来，是理论与感知压缩的桥梁。",
        "更偏压缩/感知理论，不一定包含信道。",
    ),
    paper(
        2025,
        "Wireless Synonymous Image Transmission with Joint Spatial-Power Domain Adaptation",
        "Kai Niu and coauthors",
        "ICCC, 2025",
        "https://doi.org/10.1109/ICCC65529.2025.11148621",
        "同义图像无线传输",
        "图像无线传输",
        "把 synonymous image transmission 与空间/功率域联合自适应结合，目标是在无线信道下传输语义等价图像表示，并根据信道或内容分配空间/功率资源。",
        "把同义映射/语义等价思想推进到物理层无线图像传输。",
        "需全文进一步核查具体模型结构。",
    ),
    paper(
        2025,
        "Learning Joint Source-Channel Coding for Wireless Image Transmission: A Benchmark",
        "Tianjian Dang, Sixian Wang, Zhenyu Liu, Shuo Shao, Kai Niu, Jincheng Dai",
        "IEEE SPAWC, 2025",
        "https://doi.org/10.1109/SPAWC66079.2025.11143290",
        "JSCC benchmark",
        "无线图像传输基准",
        "建立 learned JSCC 图像传输基准，比较不同神经 JSCC/语义图像传输方法在数据集、信道、指标和实现上的表现。",
        "为牛凯团队和社区的语义 JSCC 方法提供可复现对比基准。",
        "基准/评测性质强。",
        status="boundary",
    ),
    paper(
        2025,
        "Way to Build Native AI-Driven 6G Air Interface: Principles, Roadmap, and Outlook",
        "Ping Zhang, Kai Niu, Yiming Liu, Zijian Liang, Nan Ma, Xiaodong Xu, Wenjun Xu, et al.",
        "IEEE Transactions on Network Science and Engineering, 2026; arXiv 2025",
        "https://doi.org/10.1109/TNSE.2025.3636923",
        "6G AI 原生空口 / 语义通信",
        "AI-native air interface",
        "讨论 AI 原生 6G 空口建设原则、路线图和展望，语义通信是其中的关键组成：空口不只是传 bit，而要承载任务、模型、语义和智能协作。",
        "连接牛凯语义通信与 6G native AI air interface 方向。",
        "宏观路线图，非单一算法。",
        status="boundary",
    ),
    paper(
        2026,
        "DiT-JSCC: Rethinking Deep JSCC with Diffusion Transformers and Semantic Representations",
        "Kailin Tan, Jincheng Dai, Sixian Wang, Guo Lu, Shuo Shao, Kai Niu, Wenjun Zhang, Ping Zhang",
        "arXiv:2601.03112 / IEEE TCCN early access, 2026",
        "https://arxiv.org/abs/2601.03112",
        "扩散 Transformer JSCC",
        "图像语义传输",
        "用 Diffusion Transformer 重新设计 Deep JSCC，把语义表示和生成式扩散能力结合，以更强先验恢复信道受损或低码率图像。",
        "代表牛凯团队 2026 年生成式 semantic JSCC 新方向。",
        "扩散模型计算复杂度和生成真实性需要关注。",
    ),
    paper(
        2026,
        "SVWIT: Synonymous Variational Wireless Image Transmission for Semantic Communication",
        "Zijian Liang, Sen Wang, Kai Niu, Changshuo Wang, Jin Xu, Ping Zhang",
        "IEEE Transactions on Network Science and Engineering, 2026",
        "https://doi.org/10.1109/TNSE.2026.3695381",
        "同义变分图像无线传输",
        "图像语义传输",
        "把 synonymous variational inference 用于无线图像传输，目标不是精确恢复原图，而是在同义集合中恢复语义等价、感知合理的图像，从而突破传统 RD 限制。",
        "把 ICML SVI 感知压缩理论进一步落到无线图像语义通信。",
        "同义集合建模和信道鲁棒性是关键难点。",
    ),
    paper(
        2026,
        "Beyond Shannon: Semantic Information Theory and Methodology",
        "Ping Zhang, Kai Niu, Zijian Liang, Changshuo Wang, Jiatong Wu, Yiming Liu, Wenjun Xu, Nan Ma, Xiaodong Xu, Ruichen Zhang",
        "IEEE Transactions on Network Science and Engineering, 2026",
        "https://doi.org/10.1109/TNSE.2026.3676901",
        "语义信息理论 / 方法论",
        "Beyond Shannon SIT",
        "系统阐释为什么 semantic information theory 是 Shannon theory 的自然延伸，围绕同义映射、语义熵、语义互信息、语义容量和语义率失真组织方法论。",
        "是 Mathematical Theory 的扩展/方法论化版本，强调超越 Shannon 的理论框架。",
        "理论工作，应用落地需要任务化语义空间。",
    ),
    paper(
        2026,
        "Semantic Algorithmic Information Theory: From Kolmogorov Complexity to Semantic Equivalence",
        "Jiatong Wu, Sen Wang, Kai Niu, Yifei She, Ping Zhang",
        "Entropy, 2026",
        "https://doi.org/10.3390/e28050554",
        "语义算法信息论",
        "Kolmogorov complexity 与语义等价",
        "把算法信息论中的 Kolmogorov complexity 与 semantic equivalence 联系起来，讨论在语义等价类上定义复杂度和信息量。",
        "拓展 SIT 到算法信息论维度。",
        "MDPI/Entropy；理论抽象，应用需要进一步桥接。",
        status="included_mdpi",
    ),
    paper(
        2026,
        "A Synonymous Variational Perspective on the Rate-Distortion-Perception Tradeoff",
        "Zijian Liang, Kai Niu, Changshuo Wang, Jin Xu, Ping Zhang",
        "arXiv:2604.14603, 2026",
        "https://arxiv.org/abs/2604.14603",
        "同义变分 / RDP 理论",
        "感知压缩理论",
        "从 synonymity-based semantic information 角度重新解释 RDP tradeoff：感知重建不是恢复原样本，而是恢复同义集合中的可接受样本；分布差异项可由同义源编码目标自然导出。",
        "把 RDP 理论和牛凯的 synonymous mapping/SIT 统一起来。",
        "预印本，正式版本待跟踪。",
    ),
    paper(
        2026,
        "Joint Source-Channel Coding for Task-Oriented Broadcast Communications: An Information Bottleneck Approach With Rate Splitting",
        "Youlong Wu, Jingfeng Huang, Yuanming Shi, Shuai Ma, Kai Niu, Meixia Tao, Khaled B. Letaief",
        "IEEE Transactions on Wireless Communications, 2026",
        "https://doi.org/10.1109/TWC.2026.3671290",
        "任务导向广播语义通信 / IB",
        "多接收端 broadcast task-oriented communication",
        "用 information bottleneck 和 rate splitting 设计任务导向广播 JSCC，使公共/私有语义信息在多用户广播信道中高效传输。目标是保留任务相关信息并减少冗余。",
        "牛凯参与的任务导向/IB 语义通信方向代表。",
        "重点是任务型通信和 IB，不属于同义映射理论线。",
    ),
]


EXCLUDED = [
    ("Distributed Joint Source-Channel Polar Coding", "ISIT 2022", "联合源信道 polar coding，未以 semantic communication 为主体。"),
    ("Joint Source-Channel Polar-Coded Modulation", "ISIT 2022", "JSCC 调制/编码基础工作，非语义通信论文。"),
    ("Enhanced Joint Source-Channel Polarization Effect Based on Polarizing Matrix Extension", "IEEE Communications Letters 2024", "信息编码理论，与语义通信关系间接。"),
    ("Learning to Decode Double Polar Codes for Joint Source-Channel Coding", "IEEE TVT 2026", "polar code 解码，不纳入语义通信内容主表。"),
    ("Soft information acceleration aided subspace suppression MIMO detection", "EURASIP JWCN 2024", "MIMO 检测，不是语义通信。"),
    ("A joint optimization method for weight estimation and re-identification based on a cattle back semantic disentanglement model", "Computers and Electronics in Agriculture 2026", "这里的 semantic 是视觉特征解耦，不是通信语义。"),
]


def write_outputs() -> None:
    with (ROOT / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for item in PAPERS:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    with (ROOT / "included_papers.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["year", "title", "authors", "venue", "theme", "task", "status", "link"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in PAPERS:
            writer.writerow({k: item[k] for k in fields})
    with (ROOT / "excluded_or_boundary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "venue", "reason"])
        writer.writerows(EXCLUDED)
    strategy = dedent(
        """
        # Kai Niu Semantic Communications Search Notes

        Scope: Kai Niu / 牛凯, Beijing University of Posts and Telecommunications, semantic communication related works from 2021 to present.

        Search date: 2026-07-05.

        Main sources:
        - DBLP Kai Niu 0001 profile, XML downloaded to notes/dblp_kai_niu.xml.
        - Google Scholar public profile snapshot, downloaded to notes/scholar_kai_niu.html.
        - OpenAlex author A5008455605, downloaded all works since 2021 and semantic-filtered works.
        - Web/arXiv/IEEE/DOI lookups for missing abstracts and latest 2025-2026 preprints.
        - Semantic Scholar API was attempted, but the anonymous request returned 429 Too Many Requests; DBLP/OpenAlex/Scholar were used as the stable backbone.

        Inclusion:
        - Semantic communication / semantic coded transmission.
        - Semantic information theory, synonymous mapping, semantic source/channel coding, semantic rate-distortion.
        - Neural JSCC papers positioned as semantic communication by the authors, including image, video, speech, point cloud, NeRF and XR transmission.
        - Semantic networking, 6G semantic/native-AI air interface, model/semantics-division access/duplexing.

        Exclusion:
        - Pure polar coding, MIMO detection, channel decoding, ordinary 6G communication papers without semantic communication content.
        - Papers where "semantic" only means computer-vision semantic segmentation/disentanglement and not semantic communication.

        Notes:
        - Some works appear as arXiv preprints and later journal/conference papers. The report merges obvious duplicates and notes both versions.
        - MDPI/Entropy/Sensors papers are retained because the user requested a person-wide survey, but they are explicitly marked where relevant.
        """
    ).strip()
    (ROOT / "search_strategy.md").write_text(strategy + "\n", encoding="utf-8")


def render_html() -> str:
    css = dedent(
        """
        :root { --ink:#132235; --muted:#607086; --line:#d9e2ec; --soft:#f5f8fb; --brand:#126b62; --warn:#8a5600; }
        * { box-sizing:border-box; }
        body { margin:0; color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif; line-height:1.72; background:#fff; }
        nav { position:fixed; top:0; bottom:0; left:0; width:330px; overflow:auto; padding:20px 18px; border-right:1px solid var(--line); background:#fbfcfe; }
        nav h2 { margin:0 0 12px; font-size:18px; }
        nav a { display:block; color:#173c61; text-decoration:none; padding:5px 0; font-size:13px; }
        nav a:hover { color:var(--brand); }
        .year { margin-top:13px; color:var(--warn); font-weight:700; font-size:13px; }
        main { margin-left:330px; padding:38px 48px 90px; max-width:1520px; }
        h1 { margin:0 0 10px; font-size:34px; line-height:1.2; }
        h2 { margin:34px 0 14px; padding-bottom:7px; border-bottom:2px solid var(--line); font-size:25px; }
        h3 { margin:22px 0 7px; color:#0e3d66; font-size:18px; }
        p { margin:0 0 10px; }
        .lead { max-width:1050px; color:var(--muted); }
        .notice { border-left:5px solid var(--brand); background:var(--soft); padding:13px 16px; margin:20px 0; }
        table { width:100%; border-collapse:collapse; margin:14px 0 24px; font-size:13px; }
        th,td { border:1px solid var(--line); padding:8px 9px; vertical-align:top; }
        th { background:#edf3f8; text-align:left; }
        .chips { display:flex; flex-wrap:wrap; gap:7px; margin:8px 0 12px; }
        .chips span { border:1px solid var(--line); border-radius:999px; padding:2px 9px; font-size:12px; color:#24445f; background:#fff; }
        article { padding-top:12px; }
        .summary-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin:15px 0 20px; }
        .card { border:1px solid var(--line); padding:14px; background:#fff; }
        .card b { color:var(--brand); }
        code { background:#f0f3f7; padding:1px 4px; border-radius:4px; }
        @media (max-width:1000px){ nav{position:static;width:auto;border-right:0;border-bottom:1px solid var(--line);} main{margin-left:0;padding:24px 18px 60px;} .summary-grid{grid-template-columns:1fr;} }
        """
    )
    by_year = {}
    for item in PAPERS:
        by_year.setdefault(item["year"], []).append(item)
    nav = ["<nav><h2>牛凯语义通信论文</h2><a href='#overview'>总览</a><a href='#timeline'>时间线</a><a href='#themes'>主题脉络</a>"]
    for year in sorted(by_year):
        nav.append(f"<div class='year'>{year}</div>")
        for item in sorted(by_year[year], key=lambda x: x["title"]):
            nav.append(f"<a href='#{slug(item['title'])}'>{esc(item['title'])}</a>")
    nav.append("<a href='#excluded'>排除/边界说明</a></nav>")

    table_rows = []
    for item in PAPERS:
        table_rows.append(
            f"<tr><td>{item['year']}</td><td><a href='#{slug(item['title'])}'>{esc(item['title'])}</a></td>"
            f"<td>{esc(item['theme'])}</td><td>{esc(item['task'])}</td><td>{esc(item['venue'])}</td><td>{esc(item['status'])}</td></tr>"
        )
    overview_table = "<table><thead><tr><th>年份</th><th>论文</th><th>主题</th><th>任务/对象</th><th>发表信息</th><th>状态</th></tr></thead><tbody>" + "".join(table_rows) + "</tbody></table>"

    cards = [
        ("2021-2022：从 neural JSCC 到语义编码", "用图像/视频/语音端到端传输证明 learned JSCC 在低 SNR 下避免 cliff effect；同时用 Paradigm Shift 和 Semantics-Guided Source-Channel Coding 形成语义通信框架。"),
        ("2023-2024：自适应、多模态、网络范式", "NTSCC 改进、WITT/SwinJSCC、MIMO、talking-head、MDMA、Semantics-Division Duplexing 等工作把语义通信从单链路重建扩展到可控、多用户和网络层。"),
        ("2024-2026：同义映射和语义信息理论", "以 synonymous mapping 为核心构建 SIT，发展 Semantic Huffman/Arithmetic、Semantic Markov Chain、SVI、SVWIT、Beyond Shannon 等理论和算法。"),
    ]
    theme_html = "<div class='summary-grid'>" + "".join(f"<div class='card'><b>{esc(t)}</b><p>{esc(b)}</p></div>" for t, b in cards) + "</div>"

    articles = []
    for item in PAPERS:
        chips = "".join(f"<span>{esc(x)}</span>" for x in [item["year"], item["theme"], item["status"]])
        articles.append(
            f"<article id='{slug(item['title'])}'><h2>{esc(item['title'])}</h2><div class='chips'>{chips}</div>"
            f"<h3>基本信息</h3><p>{esc(item['authors'])}。{esc(item['venue'])}。<a href='{esc(item['link'])}'>外部链接</a></p>"
            f"<h3>研究对象</h3><p>{esc(item['task'])}</p>"
            f"<h3>内容概括</h3><p>{esc(item['content'])}</p>"
            f"<h3>主要贡献</h3><p>{esc(item['contribution'])}</p>"
            f"<h3>与牛凯语义通信路线的关系</h3><p>{esc(item['relation'])}</p>"
            + (f"<h3>备注</h3><p>{esc(item['notes'])}</p>" if item["notes"] else "")
            + "</article>"
        )
    excluded_rows = "".join(f"<tr><td>{esc(t)}</td><td>{esc(v)}</td><td>{esc(r)}</td></tr>" for t, v, r in EXCLUDED)
    return dedent(
        f"""
        <!doctype html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>牛凯 Kai Niu 语义通信论文调研（2021-至今）</title>
          <style>{css}</style>
        </head>
        <body>
        {''.join(nav)}
        <main>
          <section id="overview">
            <h1>牛凯（Kai Niu）语义通信相关论文调研（2021-至今）</h1>
            <p class="lead">本报告聚焦北京邮电大学牛凯老师 2021 年以来与 semantic communication / semantic information theory / neural JSCC semantic transmission / synonymous mapping / 6G semantic networking 相关的论文。检索日期为 2026-07-05；数据来源包括 DBLP Kai Niu 0001、Google Scholar、OpenAlex 作者实体 A5008455605、arXiv、IEEE/DOI 页面和本项目已有语义通信调研资料。</p>
            <div class="notice"><b>收录口径：</b>合并明显的 arXiv 与正式发表重复项；保留人物全景中有意义的 MDPI/Entropy/Sensors 项并明确标注；排除纯 polar coding、普通 MIMO 检测、非通信语义视觉论文。</div>
            <div class="notice"><b>检索状态：</b>Semantic Scholar API 本轮匿名请求返回 429，因此页面以 DBLP、OpenAlex 与 Google Scholar 为主干，再用 arXiv、IEEE/DOI、Springer 等页面补充 2025-2026 年新论文。后续若要做逐篇全文精读，可在本清单基础上继续下载 PDF、补图和补实验细节。</div>
            {overview_table}
          </section>
          <section id="themes"><h2>主题脉络</h2>{theme_html}</section>
          <section id="timeline"><h2>逐篇内容</h2>{''.join(articles)}</section>
          <section id="excluded"><h2>排除/边界说明</h2><table><thead><tr><th>题名</th><th>出处</th><th>原因</th></tr></thead><tbody>{excluded_rows}</tbody></table></section>
        </main>
        </body>
        </html>
        """
    )


def main() -> None:
    write_outputs()
    (ROOT / "index.html").write_text(render_html(), encoding="utf-8")


if __name__ == "__main__":
    main()
