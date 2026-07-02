from __future__ import annotations

import csv
import html
import json
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")[:96]


def asset_slug(pdf: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", pathlib.Path(pdf).stem.lower()).strip("_")[:80]


PAPERS = [
    {
        "title": "Semantic Information Recovery in Wireless Networks",
        "pdf": "2022_Xu_Semantic_Communication_Information_Bottleneck_View.pdf",
        "year": 2022,
        "authors": "Edgar Beck, Carsten Bockelmann, Armin Dekorsy",
        "venue": "arXiv:2204.13366 / IEEE-style manuscript",
        "source": "arXiv",
        "identifier": "arXiv:2204.13366",
        "task": "语义信息恢复；SINFONY 分布式多点图像分类/语义恢复。",
        "datasets": "CIFAR-10 图像；分布式多发端场景把图像观测拆给多个 sender。",
        "baselines": "经典数字通信链路、分离式 source/channel coding、无 bottleneck DNN 分类模型。",
        "metrics": "classification error/accuracy、rate-normalized SNR shift、channel uses。",
        "channel": "AWGN；神经端到端语义通信链路。",
        "conditions": "通过发送端输出维度/信道使用数形成 bottleneck；比较不同信道使用数和 SNR。",
        "intro": [
            "现有通信系统主要追求 bit-level 复原，但 Weaver 意义上的语义通信希望保留 message 的意义而非逐符号一致。",
            "已有一些 SemCom 工作使用交叉熵或 DNN 近似，却没有把完整通信 Markov chain 和语义随机变量联系起来。",
            "本文把语义定义为 hidden random variable，并把端到端通信任务写成 Information Bottleneck 问题。",
        ],
        "method": "提出 SINFONY：发送端 DNN 从消息/图像中抽取低维 channel input，信道层输出 y，接收端 DNN 估计语义变量 z。分布式版本让多个 sender 只发送各自观测中对语义 z 有用的部分。",
        "ib_formula": "$$\\max_\\theta I_\\theta(Z;Y)\\quad \\text{s.t.}\\quad I_\\theta(S;Y)\\le I_C,$$ 或 Lagrangian 形式 $$\\max_\\theta I_\\theta(Z;Y)-\\beta I_\\theta(S;Y).$$ 实现时用 $$\\mathcal L_{CE}=-\\mathbb E[\\log q_\\phi(z|y)]$$ 作为 $-I(Z;Y)$ 的可训练上界/替代。",
        "ib_variables": "$S$ 是原始 message/source，$Z$ 是隐藏语义变量/标签，$X$ 是 encoder 输出的 channel input，$Y$ 是信道后接收表示，$q_\\phi(z|y)$ 是接收端分类后验，$I_C$ 或 channel-use 数控制 bottleneck 强度。",
        "ib_process": "给定一个 batch 图像 $s_i$ 和标签 $z_i$：1) 每个 sender 的 encoder 产生 channel symbols $x_i$；2) AWGN 信道得到 $y_i$；3) receiver softmax 输出 $q_\\phi(z|y_i)$；4) 用真实标签计算交叉熵 $-\\log q_\\phi(z_i|y_i)$ 并对 batch 求平均；5) bottleneck 不是另算压缩率，而是通过减少 channel uses/encoder 输出维度来限制 $I(S;Y)$，从而逼迫网络只保留能降低 CE 的语义信息。",
        "channel_handling": "信道噪声直接作用在 learned channel symbols 上；IB 目标不显式建模 bit error，而是通过端到端训练和受限 channel uses 学习对语义恢复有用且抗噪的表示。",
        "result": "SINFONY 在分布式图像分类场景相对传统链路取得显著 rate-normalized SNR shift，显示 IB 约束下的语义表示能在少量 channel uses 下保持任务信息。",
        "limitation": "理论框架清晰，但实际实现中 $I(S;Y)$ 主要由 channel-use 维度间接控制，互信息本身没有逐 batch 精确估计。",
        "judgement": "核心。方法设计直接以 IB/Infomax 为理论基础，不只是 introduction 提及。",
    },
    {
        "title": "Adaptive Information Bottleneck Guided Joint Source and Channel Coding for Image Transmission",
        "pdf": "2023_Sun_Adaptive_Information_Bottleneck_JSCC_Image_Transmission.pdf",
        "year": 2023,
        "authors": "Lunan Sun, Yang Yang, Mingzhe Chen, Caili Guo, Walid Saad, H. Vincent Poor",
        "venue": "IEEE Transactions on Wireless Communications / arXiv:2203.06492",
        "source": "arXiv",
        "identifier": "arXiv:2203.06492",
        "task": "图像 JSCC 重建，同时降低不必要传输信息。",
        "datasets": "MNIST、CIFAR-10、SVHN、Cityscapes 等图像数据。",
        "baselines": "IABF、IB-JSCC fixed-beta、BPG/JPEG + channel coding、DeepJSCC 类方法。",
        "metrics": "MSE、PSNR、storage/transmitted data、downstream task accuracy、inference time。",
        "channel": "DMC/BSC-like error channel、parallel channels 等；训练和测试 error probability 可变化。",
        "conditions": "固定 codeword 长度时比较 MSE/PSNR；另比较达到同等 MSE 所需传输量。",
        "intro": [
            "DeepJSCC 通常固定信道资源并最小化重建 MSE，可能传输超过任务所需的信息。",
            "传统 IB 面向有监督标签，不直接适用于无监督图像重建。",
            "本文重新设计图像传输 IB 目标，并用自适应 beta 平衡重建质量和表示压缩。",
        ],
        "method": "AIB-JSCC 仍是 autoencoder JSCC，但训练目标不是单纯 MSE，而是最大化接收码字关于输入图像的信息，同时压低发送码字关于输入图像的信息；beta 由训练过程中的 MSE 动态调整。",
        "ib_formula": "论文定义 $$IB_\\beta(X,Y,\\hat Y)=I(X;\\hat Y)-\\beta I(X;Y).$$ 训练时最大化其可微下界，等价最小化 $$\\mathcal L=-\\widehat I_{VL}(X;\\hat Y)+\\beta\\widehat I_{CLUB}(X;Y),$$ 其中 $\\widehat I_{VL}$ 是接收重建相关的 variational lower bound，$\\widehat I_{CLUB}$ 是发送码字互信息的 CLUB upper bound。",
        "ib_variables": "$X$ 原图，$Y$ encoder 产生的 codeword/channel input，$\\hat Y$ noisy received codeword 或 decoder 输入；$\\beta$ 控制压缩项权重；$\\phi,\\theta$ 是 encoder/decoder 与互信息估计器参数。",
        "ib_process": "给定 batch 图像：1) encoder 得到 $y\\sim p_\\phi(y|x)$；2) 信道扰动得到 $\\hat y$；3) decoder 得到重建 $\\hat x$；4) 用 Gaussian likelihood 或 MSE 形式计算 $\\widehat I_{VL}(X;\\hat Y)$，本质上奖励 $\\hat y$ 能重建 $x$；5) 用 CLUB 估计 $I(X;Y)$ 的上界，惩罚 $y$ 记住过多原图细节；6) 根据当前 epoch 的 batch/validation MSE 用 PID-like 自适应算法更新 $\\beta$，再进入下一轮训练。",
        "channel_handling": "信道作为训练图中的非训练层，error probability/channel state 参与损失计算；IB 的压缩项提高表示稳健性，避免 codeword 过拟合输入细节。",
        "result": "AIB-JSCC 在多数据集上低于固定 beta IB-JSCC 和 IABF 的 MSE，并在同等重建误差下需要更少传输资源。",
        "limitation": "互信息估计依赖 VIMCO/CLUB 近似和额外估计器；目标更偏图像 JSCC，语义任务性不如分类/推理型 TSC 明确。",
        "judgement": "核心。IB 是训练目标和 beta 自适应算法的中心。",
    },
    {
        "title": "Robust Information Bottleneck for Task-Oriented Communication with Digital Modulation",
        "pdf": "2023_Xu_Robust_Information_Bottleneck_Task_Oriented_Communication_Digital_Modulation.pdf",
        "year": 2023,
        "authors": "Songjie Xie, Shuai Ma, Ming Ding, Yuanming Shi, MingJian Tang, Youlong Wu",
        "venue": "IEEE Journal on Selected Areas in Communications, 2023",
        "source": "arXiv",
        "identifier": "arXiv:2209.10382",
        "task": "任务导向通信/分类，兼容数字调制。",
        "datasets": "MNIST、CIFAR-10 等分类数据集。",
        "baselines": "DeepJSCC、VIB/IB variants、traditional digital modulation baselines。",
        "metrics": "classification accuracy、robustness under SNR/channel variation、semantic representation quality。",
        "channel": "数字调制链路，PSK/BPSK 等离散调制；考虑信道扰动。",
        "conditions": "不同 SNR、调制阶数和 beta 设置。",
        "intro": [
            "Task-oriented communication 去掉冗余后更脆弱，且连续 JSCC 与现代数字调制系统不完全兼容。",
            "普通 IB 追求 minimal sufficient representation，但没有把传输鲁棒性写入目标。",
            "本文提出 Robust Information Bottleneck，使表示同时 task-informative、compact、channel-robust。",
        ],
        "method": "编码器产生任务语义表示并映射到数字调制符号，信道后接收表示用于分类。RIB 把接收端任务信息、发送-接收保真度和输入冗余三者放在同一个互信息目标中。",
        "ib_formula": "$$\\max I(Y;\\hat Z)+\\beta\\left[I(Z;\\hat Z)-I(X;\\hat Z)\\right].$$ $I(Y;\\hat Z)$ 保证任务标签可推断，$I(Z;\\hat Z)$ 保证传输鲁棒/保真，$I(X;\\hat Z)$ 惩罚接收表示携带过多输入无关信息。",
        "ib_variables": "$X$ 输入样本，$Y$ 任务标签，$Z$ 发送端语义表示/调制前表示，$\\hat Z$ 经信道和解调后的接收表示，$\\beta$ 控制鲁棒冗余与压缩的权衡。",
        "ib_process": "一个 batch 中：1) encoder 得到 $Z$，并经数字调制和信道得到 $\\hat Z$；2) classifier 对 $\\hat Z$ 预测标签，交叉熵近似 $-I(Y;\\hat Z)$；3) 用变分分布/互信息估计器估计 $I(Z;\\hat Z)$，奖励接收表示保留发送表示；4) 估计或上界 $I(X;\\hat Z)$，惩罚输入冗余；5) 三项按 RIB 目标合成为 batch loss 反向传播。",
        "channel_handling": "显式把信道失真后的 $\\hat Z$ 放进 IB 目标，目标中的 $I(Z;\\hat Z)$ 正是为抗信道扰动保留必要冗余。",
        "result": "RIB 在数字调制条件下比单纯 CE/普通 IB 更稳健，能在低 SNR 或调制受限时保持更好的任务准确率。",
        "limitation": "互信息项需要变分近似；RIB 的 beta 和调制配置仍需实验调参。",
        "judgement": "核心。它是本主题最典型的 RIB 方法论文。",
    },
    {
        "title": "Semantic Communications Based on Adaptive Generative Models and Information Bottleneck",
        "pdf": "2023_Xu_Semantic_Communications_Adaptive_Generative_Models_IB.pdf",
        "year": 2023,
        "authors": "Sergio Barbarossa, Danilo Comminiello, Eleonora Grassucci, Francesco Pezone, Stefania Sardellitti, Paolo Di Lorenzo",
        "venue": "arXiv:2309.02387 / IEEE Communications Magazine style",
        "source": "arXiv",
        "identifier": "arXiv:2309.02387",
        "task": "基于生成模型的图像/语义重建与分类任务通信。",
        "datasets": "图像重建示例；生成模型/VAE latent representation。",
        "baselines": "传统符号级恢复、固定 latent 维度生成模型、无自适应 bottleneck 版本。",
        "metrics": "reconstruction accuracy/MSE、delay、transmit power、channel-aware symbol count。",
        "channel": "无线信道状态驱动在线 bottleneck 调整。",
        "conditions": "根据 channel state 在线改变发送 latent symbols 数量。",
        "intro": [
            "语义通信不需要逐符号复原，而是要恢复等价语义。",
            "生成模型可在接收端重建内容，但需要决定传多少 latent 信息。",
            "本文用 IB 原理把表示复杂度、重建精度、发射功率/延迟联系起来。",
        ],
        "method": "发送端 recognition model 把输入映射到 latent variable，接收端 generative model 用收到的 latent 生成图像或执行任务；IB 用来选择和调节要发送的 latent 维度/符号数。",
        "ib_formula": "论文给出的改造 IB 形式是 $$\\min I(X;T)+\\beta\\,\\mathrm{MSE}(Y,\\hat Y),$$ 其中 $I(X;T)$ 表示 latent 表示复杂度/通信开销，MSE 表示语义目标或重建失真。",
        "ib_variables": "$X$ 输入数据，$T$ 生成模型 latent representation，$Y$ 目标语义/原始内容，$\\hat Y$ 接收端生成结果，$\\beta$ 平衡少传 latent 与保持准确重建。",
        "ib_process": "对一个 batch：1) recognition encoder 产生 latent posterior 或 latent code $T$；2) 根据当前信道状态选择发送的 latent components；3) receiver/generative decoder 得到 $\\hat Y$；4) 计算重建 MSE 或任务误差；5) 计算 latent 信息复杂度，VAE 实现中通常对应 posterior 与 prior 的 KL 或被选择 latent 维度的信息量；6) 优化 $I(X;T)+\\beta MSE$，并在线调节 bottleneck 强度。",
        "channel_handling": "信道状态不是简单噪声层，而是决定 bottleneck 的在线控制量：信道差时减少/改变传输 latent，信道好时允许更多 latent 保真。",
        "result": "展示了生成模型与自适应 IB 可在不同信道状态下调节传输率并保持可接受语义恢复。",
        "limitation": "偏 conceptual/framework，实验细节和统一可复现实验不如后续 TWC/JSAC 论文完整。",
        "judgement": "核心。IB 直接参与生成语义通信系统的 rate-accuracy-delay tradeoff。",
    },
    {
        "title": "Improving Channel Resilience for Task-Oriented Semantic Communications: A Unified Information Bottleneck Approach",
        "pdf": "2024_Qin_Improving_Channel_Resilience_Unified_Information_Bottleneck.pdf",
        "year": 2024,
        "authors": "Shuai Lyu, Yao Sun, Linke Guo, Xiaoyong Yuan, Fang Fang, Lan Zhang, Xianbin Wang",
        "venue": "arXiv:2405.00135 / IEEE Communications Letters under review",
        "source": "arXiv",
        "identifier": "arXiv:2405.00135",
        "task": "任务导向语义通信中的 feature-level channel resilience；案例是 OFDM/subchannel allocation。",
        "datasets": "图像分类数据集；VGG16 作为 encoder/decoder backbone。",
        "baselines": "随机或非 IB 的 subchannel allocation、平均分配、无 channel-resilient mask 方案。",
        "metrics": "inference accuracy、robustness under dynamic subchannels、SNR sweep。",
        "channel": "OFDM/频率选择性子信道；16 pilots，data subcarriers 512；SNR/subchannel 动态变化。",
        "conditions": "IB hyperparameter beta=0.3；对 encoded feature units 注入人工噪声估计鲁棒性。",
        "intro": [
            "TSC 已能压缩任务相关信息，但通常忽视不同 feature units 对信道错误的敏感性差异。",
            "OFDM 宽带信道中不同 subchannel 质量不同，敏感 feature 若落到坏子信道会导致错误推理。",
            "本文用 IB 解释 feature robustness，并把结果用于子信道分配。",
        ],
        "method": "固定已训练 TSC encoder/decoder，在 encoded features 上引入人工噪声 $\\sigma$，用 IB 目标评估哪些 feature 在保持标签信息同时对输入冗余更敏感，再生成 robustness mask 做 subchannel allocation。",
        "ib_formula": "基础目标 $$\\min \\mathcal L(\\phi,\\theta)=-I(\\hat Z;Y)+\\beta I(\\hat Z;X).$$ 鲁棒性估计中引入人工噪声得到 $$\\min \\mathcal L(\\sigma)=-I(\\tilde Z;Y|\\phi,\\theta)+\\beta I(\\tilde Z;X|\\phi,\\theta).$$",
        "ib_variables": "$X$ 输入，$Y$ 任务标签，$\\hat Z$ 接收特征，$\\tilde Z$ 是在 encoded feature 上加人工噪声后的表示，$\\sigma$ 表示各 feature unit 的噪声/扰动强度，$\\beta$ 控制压缩项。",
        "ib_process": "给定 batch：1) 用固定 encoder 产生 feature map $Z$；2) 对某个 feature unit 或 mask 加人工噪声得到 $\\tilde Z$；3) decoder/classifier 输出标签概率并计算交叉熵，作为 $-I(\\tilde Z;Y)$ 的替代；4) 用 KL 上界估计 $I(\\tilde Z;X)$；5) 对不同 feature unit 得到 robustness score；6) 将敏感/重要 feature 分配到质量更好的 OFDM subchannels。",
        "channel_handling": "不是只训练一个抗噪 encoder，而是把 IB 估计结果映射到实际 radio resource allocation，显式利用子信道质量差异。",
        "result": "在动态 subchannel 条件下，IB-based allocation 比基线保持更高推理准确率。",
        "limitation": "IB 主要用于 feature sensitivity/分配，而不是端到端共同优化整个语义编解码器。",
        "judgement": "核心。论文的方法主体就是 IB robustness mask。",
    },
    {
        "title": "Privacy-Preserving Task-Oriented Semantic Communications Against Model Inversion Attacks",
        "pdf": "2024_Qin_Privacy_Preserving_Task_Oriented_Semantic_Communications_IBAL.pdf",
        "year": 2024,
        "authors": "Yanhu Wang, Shuaishuai Guo, Yiqin Deng, Haixia Zhang, Yuguang Fang",
        "venue": "arXiv:2312.03252 / IEEE Transactions-style manuscript",
        "source": "arXiv",
        "identifier": "arXiv:2312.03252",
        "task": "隐私保护任务导向语义通信，抵抗 model inversion attack。",
        "datasets": "MNIST、CIFAR-10、ImageNet-2012 额外实验。",
        "baselines": "NECST-G、NECST-G-DP、ESCS、IBAL-D-NO、加密增强版本等。",
        "metrics": "classification accuracy、SSIM/PSNR privacy指标、privacy-utility tradeoff。",
        "channel": "AWGN、Rayleigh fading；IBAL-D 考虑动态 SNR。",
        "conditions": "静态/动态信道；lambda 与 MGDA 自适应权重；model inversion adversary。",
        "intro": [
            "只传任务相关特征并不能自动防止隐私泄露，攻击者可用 model inversion 重建输入。",
            "直接差分隐私加噪会牺牲任务性能。",
            "本文结合 IB 和 adversarial learning，在保留标签信息同时压缩输入隐私信息。",
        ],
        "method": "IBAL 的 transmitter 提取任务相关特征，receiver 做分类，adversary decoder 试图从 transmitted feature 重建输入。训练交替进行：先训练 adversary decoder，再训练通信网络欺骗 adversary。",
        "ib_formula": "IB 部分为 $$\\mathcal L_{IB}=-I(\\hat Z;Y)+\\beta I(\\hat Z;S).$$ 变分上界可写为 $$\\mathbb E[-\\log q_\\phi(y|\\hat z)]+\\beta\\,\\mathrm{KL}(p_\\theta(\\hat z|s)\\|q(\\hat z)).$$ 总目标再结合 adversarial reconstruction/privacy loss，IBAL-D 用信道噪声项调整隐私权重。",
        "ib_variables": "$S$ 原始输入，$Y$ 任务标签，$Z/\\hat Z$ 发端/经信道特征，$q_\\phi(y|\\hat z)$ 是 receiver classifier，$p_\\theta(\\hat z|s)$ 是编码+信道诱导分布，$q(\\hat z)$ 是变分 prior。",
        "ib_process": "一个训练循环：1) 用当前 transmitter 产生特征并过信道；2) adversary decoder 最小化 MSE 重建输入，模拟攻击者；3) transmitter/receiver 用真实标签计算分类 CE；4) 计算 KL 压缩项惩罚特征保留过多输入信息；5) 同时让 adversary 重建误差变大，形成 privacy loss；6) MGDA/自适应权重在分类性能、IB 压缩、隐私重建失真之间求折中。",
        "channel_handling": "信道进入 $p_\\theta(\\hat z|s)=p_\\theta(z|s)p_{channel}(\\hat z|z)$，IBAL-D 还根据噪声方差动态调整隐私保护强度。",
        "result": "IBAL 在保持较好分类准确率同时显著降低 SSIM/PSNR 重建质量，相比 DP baseline 有更好的 privacy-utility tradeoff。",
        "limitation": "训练复杂，需要模拟 adversary；隐私评估依赖所选 inversion model 和图像相似性指标。",
        "judgement": "核心。IB 不是背景概念，而是隐私语义通信 loss 的主体。",
    },
    {
        "title": "Disentangled Information Bottleneck guided Privacy-Protective JSCC for Image Transmission",
        "pdf": "2024_Sun_Disentangled_Information_Bottleneck_Privacy_Protective_JSCC.pdf",
        "year": 2024,
        "authors": "Lunan Sun, Yang Yang, Mingzhe Chen, Caili Guo",
        "venue": "arXiv:2309.10263",
        "source": "arXiv",
        "identifier": "arXiv:2309.10263",
        "task": "隐私保护图像 JSCC；把 public/private information disentangle。",
        "datasets": "MNIST、CIFAR-10/SVHN 等图像数据。",
        "baselines": "privacy-protective JSCC、adversarial JSCC、separate image compression/coding。",
        "metrics": "reconstruction quality、eavesdropping accuracy、inference time。",
        "channel": "无线图像传输信道；合法接收端和 eavesdropper 接收端。",
        "conditions": "private subcodeword 加密，public subcodeword 公开传输。",
        "intro": [
            "JSCC 的 channel input 与原图高度相关，容易泄露隐私。",
            "已有方法直接去除隐私信息会损害合法接收端重建。",
            "本文用 DIB 把 public/private subcodewords 分离：公开部分不含隐私，私有部分加密传输。",
        ],
        "method": "encoder 被拆成 public encoder 和 private encoder，分别输出 $Y^t$ 与 $Y^s$。DIB 训练让 $Y^s$ 包含 private attribute，$Y^t$ 与 $Y^s$ 尽量独立，并保持图像重建质量。",
        "ib_formula": "DIB 目标包含三类互信息：最大化 private subcodeword 与 private label 的 $I(Y^s;S)$，最小化 public/private subcodewords 之间的 $I(Y^t;Y^s)$，并最小化重建失真 $d(X,\\hat X)$。论文再用变分近似和 density-ratio trick 得到可微 loss。",
        "ib_variables": "$X$ 图像，$S$ private attribute，$Y^t$ public subcodeword，$Y^s$ private subcodeword，$\\hat X$ 合法接收端重建，Eve 用接收码字估计 $S$。",
        "ib_process": "对 batch：1) public/private encoder 得到 $y^t,y^s$；2) classifier 从 $y^s$ 预测 private label，用 CE 奖励 $I(Y^s;S)$；3) density-ratio discriminator 估计 $I(Y^t;Y^s)$，训练时惩罚两者相关；4) decoder 用 $y^t,y^s$ 重建图像并计算 MSE/重建 loss；5) 加密器/解密器按最大熵原则训练，使窃听者在没有密码时对 private 信息不确定。",
        "channel_handling": "合法端有解密后的 private subcodeword，窃听端缺少密码；信道影响重建和窃听准确率，但 IB 主要处理 public/private 表示分解。",
        "result": "DIB-PPJSCC 降低 eavesdropping private-attribute accuracy，同时保持或提升合法图像重建质量和推理速度。",
        "limitation": "需要明确 private attribute 标签；隐私保护依赖属性定义和加密模块。",
        "judgement": "核心。DIB 是 public/private 语义分解的训练目标。",
    },
    {
        "title": "Contrastive Learning and Adversarial Disentanglement for Privacy-Aware Task-Oriented Semantic Communication",
        "pdf": "2025_Erak_CLAD_Privacy_Aware_Task_Oriented_Semantic_Communication.pdf",
        "year": 2025,
        "authors": "Omar Erak, Omar Alhussein, Wen Tong",
        "venue": "arXiv:2410.22784",
        "source": "arXiv",
        "identifier": "arXiv:2410.22784",
        "task": "6G-IoT privacy-aware task-oriented semantic communication。",
        "datasets": "图像/IoT 分类任务数据；论文报告多个隐私和任务实验。",
        "baselines": "standard task-oriented SemCom、adversarial/privacy baselines、contrastive/disentanglement ablations。",
        "metrics": "task accuracy、privacy leakage、semantic extraction quality、Information Retention Index (IRI)。",
        "channel": "任务导向通信链路；关注带宽与隐私而非特定数字调制。",
        "conditions": "contrastive encoder + adversarial disentanglement；IRI 作为 MI proxy。",
        "intro": [
            "任务导向 SemCom 只传任务相关信息，但特征仍可能包含 task-irrelevant private information。",
            "直接估计最小充分表示的 mutual information 很难复现。",
            "本文提出 IB-inspired CLAD，用 contrastive learning 保留任务相关信息，用 adversarial disentanglement 丢弃无关信息。",
        ],
        "method": "CLAD 不是直接写传统 IB loss，而是用对比学习近似 sufficiency，用 adversarial branch 压制 task-irrelevant/private 信息，并提出 IRI 作为 encoded feature 对输入保留信息量的 proxy。",
        "ib_formula": "IB 思想对应 $$\\max I(Z;Y)-\\beta I(Z;X_{private/noise})$$。CLAD 的实现把 $I(Z;Y)$ 替换为 supervised/contrastive task loss，把最小性替换为 adversarial disentanglement loss 和 IRI 监控。",
        "ib_variables": "$X$ 输入，$Y$ 任务标签，$Z$ 编码语义特征，task-irrelevant/private factor 是 adversary 试图预测但 encoder 需要抑制的内容；IRI 用作 $I(Z;X)$ 的相对代理指标。",
        "ib_process": "对 batch：1) encoder 输出 $z$；2) contrastive loss 拉近同类/同任务相关样本、推远不同类，增强 $Z$ 对 $Y$ 的充分性；3) task head 用 CE 计算任务损失；4) adversarial head 尝试从 $z$ 预测隐私/无关属性，encoder 通过梯度反转或对抗优化让该预测失败；5) 计算 IRI 观察 $z$ 对输入的保留程度；6) 总 loss 在任务准确和隐私最小之间折中。",
        "channel_handling": "主要研究语义特征本身的 privacy-aware bottleneck，信道建模不是核心贡献。",
        "result": "CLAD 在任务性能、隐私保护和 IRI 上优于若干 baselines。",
        "limitation": "IB 是 inspired/代理实现而非完整互信息变分推导；需要后续补读代码和实验细节。",
        "judgement": "核心但需继续丰富。方法设计明确以 IB minimal sufficient representation 为中心。",
    },
    {
        "title": "Task-Agnostic Semantic Communications Relying on Information Bottleneck and Federated Meta-Learning",
        "pdf": "2025_Yuan_Task_Agnostic_Semantic_Communications_IB_Meta_Learning.pdf",
        "year": 2025,
        "authors": "Hao Wei, Wenjing Xu, Peiying Zhang et al.",
        "venue": "arXiv:2504.21723 / IEEE record 11264466",
        "source": "arXiv",
        "identifier": "arXiv:2504.21723",
        "task": "任务无关多模态语义通信；快速适配多任务。",
        "datasets": "CIFAR-10 图像分类、CLEVR VQA、CMU-MOSI 多模态情感分析。",
        "baselines": "Specific SC、vanilla FL/FML、w/o DMIB、Univocal/Syncretic/Confluent DMIB variants。",
        "metrics": "test loss、task accuracy、training latency、energy cost、convergence。",
        "channel": "动态无线信道；语义特征自适应传输与资源管理。",
        "conditions": "Federated meta-learning；inner/outer learning rates；用户选择与资源分配。",
        "intro": [
            "传统 SemCom 往往为特定任务训练，难以适配未知任务和多模态输入。",
            "多模态有冗余和互补信息，需要理论化地学习 minimal sufficient representations。",
            "本文提出 DMIB + FML 的 TASC 框架。",
        ],
        "method": "先用 DMIB 学习单模态和多模态语义表示，再用 federated meta-learning 让系统能快速适配本地新任务；同时做语义特征传输和资源管理。",
        "ib_formula": "传统 IB：$$\\mathcal L_{IB,k}=\\zeta I(X_k;Z_k)-I(Y_k;Z_k)\\equiv \\zeta I(X_k;Z_k)+H(Y_k|Z_k).$$ U-DMIB 对每个 modality 求和；S-DMIB 用 fused representation $S_k$：$$\\mathcal L_{S-DMIB}=\\zeta I(Z_k;S_k)+H(Y_k|S_k).$$ 变分形式为 KL 到 $\\mathcal N(0,I)$ 加 CE/MAE。",
        "ib_variables": "$X_k^m$ 是用户 k 的第 m 模态输入，$Z_k^m$ 是单模态 latent，$S_k$ 是融合表示，$Y_k$ 是任务标签/目标，$\\zeta$ 控制压缩。",
        "ib_process": "一个 batch：1) 各模态 encoder 输出均值/协方差 $\\mu,\\Sigma$ 并采样 $z$；2) 计算 $KL(\\mathcal N(\\mu,\\Sigma)\\|\\mathcal N(0,I))$ 作为 $I(X;Z)$ 上界；3) classifier/VQA/sentiment head 输出任务预测，分类任务用 CE，回归/情感可用 MAE；4) U-DMIB 对单模态逐项计算，S-DMIB 对融合特征计算；5) Confluent DMIB 把两者相加；6) FML 内循环用本地 train split 更新，外循环用 test split/meta loss 更新。",
        "channel_handling": "IB 学到的语义特征再进入自适应传输和资源分配，动态信道主要影响哪些用户/特征被传输以及训练延迟能耗。",
        "result": "TASC 在多任务上接近 task-specific SemCom，且相对 vanilla FML 降低 test loss 并提升适配速度。",
        "limitation": "系统复杂，IB、FML、资源优化多模块耦合；初版报告后续应进一步补充每个数据集的网络细节。",
        "judgement": "核心。DMIB 是语义编码原则。",
    },
    {
        "title": "Multi-Modal Multi-Task Semantic Communication: A Distributed Information Bottleneck Perspective",
        "pdf": "2025_Nguyen_Multi_Modal_Multi_Task_Semantic_Communication_DIB.pdf",
        "year": 2025,
        "authors": "Nguyen et al.",
        "venue": "arXiv:2510.04000",
        "source": "arXiv",
        "identifier": "arXiv:2510.04000",
        "task": "多模态多任务分布式语义通信；任务感知 modality selection。",
        "datasets": "AV-MNIST、MM-Fi 多模态人体/动作数据。",
        "baselines": "VDDIB、RS-DIB、MI-DIB/TADIB-prev、DLSC、full participation DIB。",
        "metrics": "negative cross entropy/relevance、Top-1 accuracy、MPJPE/MSE、sum-rate、active links、training time。",
        "channel": "分布式设备到接收端的多模态链路；带 hard link constraints。",
        "conditions": "pTADIB 用概率松弛选择任务-模态链接；使用 common randomness 协调选择。",
        "intro": [
            "多模态多任务 SemCom 不能简单让所有模态全部参与，链路受限时需要按任务选择最有用模态。",
            "标准 DIB 适合多 encoder，但缺少任务感知和硬链路约束。",
            "本文提出 TADIB/pTADIB，使 modality selection 成为 IB 优化的一部分。",
        ],
        "method": "TADIB 把每个 task-modality pair 的 rate-relevance 贡献写成 DIB 分数，再用概率松弛从离散选择转为可训练策略，训练后在推理时采样/确定 active links。",
        "ib_formula": "标准 DIB 类目标含 $$H(Y_t|Z_{m,t})+I(X_m;Z_{m,t}).$$ TADIB 对 task t 和 modality m 计算 task-modality score，并在 pTADIB 中把 selection variable 的期望加入目标；经验变分目标用 CE/MSE 估计 $H(Y|Z)$，用 KL 估计 $I(X;Z)$。",
        "ib_variables": "$X_m$ 是第 m 个 modality，$Z_{m,t}$ 是该 modality 为任务 t 编码的 latent，$Y_t$ 是任务输出，selection variable 决定该 modality-task link 是否激活。",
        "ib_process": "一个 batch：1) 同步抽取各模态样本；2) 对每个 modality-task encoder 得到 latent posterior；3) 用 decoder/head 预测任务并计算 CE 或 MSE；4) 计算 posterior-prior KL 作为 rate；5) 由可学习选择策略给每个 link 权重/概率；6) 对所有被选择或按概率加权的 task-modality IB 项求和，外加 link constraint/coordination regularizer，反向传播。",
        "channel_handling": "主要体现在 link budget/active links 上，而不是物理层噪声；TADIB 关心在有限链路下最大化 relevance。",
        "result": "pTADIB 在 AV-MNIST 和 MM-Fi 上在满足硬链路约束时接近或超过 full DIB baseline，并显著减少 active links 和训练时间。",
        "limitation": "2025 arXiv 预印本；具体无线物理信道建模较弱，偏分布式语义选择理论。",
        "judgement": "核心。DIB 是方法的理论主体。",
    },
    {
        "title": "Information Bottleneck Guided Joint Source-Channel Coding with HARQ",
        "pdf": "Information_Bottleneck_Guided_Joint_Source-Channel_Coding_with_HARQ.pdf",
        "year": 2025,
        "authors": "Haoxuan Zhang, Lunan Sun, Caili Guo, Yang Yang",
        "venue": "IEEE WCNC 2025",
        "source": "IEEE",
        "identifier": "IEEE 10978742; DOI 10.1109/WCNC61545.2025.10978742",
        "task": "图像 JSCC + HARQ 重传；压缩 retransmission redundancy。",
        "datasets": "Cityscapes 图像训练/测试。",
        "baselines": "Deep JSCC、HARQ-JSCC、BPG + LDPC、SSCC HARQ。",
        "metrics": "PSNR、visual reconstruction、SNR train/test robustness。",
        "channel": "AWGN；两轮/多轮 retransmission 的 HARQ-JSCC。",
        "conditions": "SNRtrain=5 dB 等；比较 beta=0 与 beta>0。",
        "intro": [
            "HARQ-JSCC 能改善恶劣信道下重建，但重传信号可能包含大量与第一次接收重复的信息。",
            "只最小化多轮重建 MSE 没有显式压缩重传冗余。",
            "本文把 IB 引入 HARQ-JSCC，使第二次/重传信号补充而不是重复信息。",
        ],
        "method": "第一轮 encoder/decoder 得到初始接收表示和重建；第二轮 encoder 根据原图和/或第一轮信息生成重传信号。IB 目标鼓励重传减少冗余并提升最终重建。",
        "ib_formula": "论文设计 HARQ-IBJSC 目标，核心思想为最大化 $I(X;\\hat Z_1,\\hat Z_2)$ 同时惩罚重传与已有接收信息的冗余互信息；再推导可微 lower bound 作为训练 loss。beta=0 时退化为类似 HARQ-JSCC 的 MSE 目标。",
        "ib_variables": "$X$ 原图，$\\hat Z_1$ 第一轮接收信息，$\\hat Z_2$ 重传接收信息，$r(x|\\hat z_1,\\hat z_2)$ 是变分重建 posterior，$E_\\gamma$ 是 MI estimator。",
        "ib_process": "训练 batch：1) 第一轮 encoder 发送并经信道得到 $\\hat z_1$，decoder 得到初始重建；2) 第二轮 encoder 产生重传信号，经信道得到 $\\hat z_2$；3) 最终 decoder 用 $\\hat z_1,\\hat z_2$ 重建图像并计算 MSE/likelihood 项；4) 训练 MI estimator 估计重传与已有信息/原图之间的互信息；5) 用下界 loss 更新第二轮 encoder/decoder，让 $\\hat z_2$ 更像增量语义信息。",
        "channel_handling": "HARQ 本身处理信道失败；IB 进一步约束重传内容，减少重复传输并提升低 SNR 重建。",
        "result": "HARQ-IBJSC 相比 HARQ-JSCC 在多种 SNR 下提升 PSNR，最高约 1 dB。",
        "limitation": "会议论文篇幅短，IB 目标细节和更多语义任务验证还有扩展空间。",
        "judgement": "核心。IB 直接定义 HARQ 重传训练目标。",
    },
    {
        "title": "Robust Information Bottleneck Guided Non-Autoregressive Semantic Communication With Synonymous Mapping",
        "pdf": "2026_Wu_RIB_NASC_Synonymous_Mapping.pdf",
        "year": 2026,
        "authors": "Mingtong Zhang, Haixia Zhang, Dongfeng Yuan, Ping Zhang",
        "venue": "IEEE Transactions on Wireless Communications, 2026",
        "source": "IEEE",
        "identifier": "IEEE 11476854",
        "task": "文本语义通信；非自回归语义解码；同义映射恢复 underlying semantics。",
        "datasets": "European Parliament proceedings，约 2.2M English sentences，长度 4-30 words。",
        "baselines": "DeepSC、NA-DeepSC、Huffman-LDPC；RIB/decoder ablations。",
        "metrics": "BLEU、sentence similarity、decoding latency、model size/FLOPs。",
        "channel": "AWGN、Rayleigh fading、imperfect CSI Rayleigh。",
        "conditions": "SCR R=2/4 等；synonymous sentence number M，replacement probability pr=0.2，beta sweep。",
        "intro": [
            "文本 SemCom 常用 CE/MSE 等 syntactic loss，不能直接对齐 underlying semantic recovery。",
            "自回归解码延迟高，不适合低时延语义通信。",
            "本文把 RIB 和 synonymous mapping 结合，为语义等价恢复设计训练目标。",
        ],
        "method": "RIB-NASC 采用 Transformer encoder 型非自回归 semantic decoder；通过同义句生成估计不可见 semantic source 的后验，从而计算 RIB 目标的变分下界。",
        "ib_formula": "$$\\max I(S;\\hat Z)+\\beta\\left[I(Z;\\hat Z)-I(X;\\hat Z)\\right].$$ 训练时最小化 negative variational lower bound $$\\hat{\\mathcal L}_{VRIB}(\\theta,\\phi)$$，其中 $I(S;\\hat Z)$ 用 synonymous mapping 后验估计，$I(X;\\hat Z)$ 用 variational upper bound，$I(Z;\\hat Z)$ 用 Donsker-Varadhan/MINE-like lower bound。",
        "ib_variables": "$X$ 原句，$S$ underlying semantic source，$Z$ 发送语义表示，$\\hat Z$ 经信道接收表示，$X_{syn}$ 是同义句集合，$p_\\phi(s|\\hat z)$ 由多个同义句 posterior 近似。",
        "ib_process": "对一个文本 batch：1) 对每句 x 生成 M 个 synonymous sentences；2) encoder 产生发送表示 z，经信道得到 $\\hat z$；3) 非自回归 decoder 并行预测句子 token；4) 用同义句后验求和估计 $p(s|\\hat z)$，计算语义充分性项；5) 用变分 prior 估计 $I(X;\\hat Z)$ 的 KL 上界；6) 用 MI estimator 估计 $I(Z;\\hat Z)$；7) 合成 $\\hat L_{VRIB}$ 更新通信模型和 MI 模块。",
        "channel_handling": "RIB 目标显式包含 $I(Z;\\hat Z)$，因此信道后的表示保真是训练目标一部分；同义映射让模型不只追 token exact match。",
        "result": "RIB-NASC 在 BLEU 和 sentence similarity 上优于 DeepSC/NA-DeepSC，并将自回归 decoding latency 降低约 96.7%。",
        "limitation": "同义句生成和 posterior 近似带来训练复杂度；语义等价质量依赖 synonym generation 质量。",
        "judgement": "核心。IB 目标、同义后验估计和训练算法全部围绕 RIB 展开。",
    },
    {
        "title": "TOIB: Task-Oriented Orthogonalised Information Bottleneck for Distributed Semantic Communication",
        "pdf": "2026_Wu_TOIB_Distributed_Semantic_Communication.pdf",
        "year": 2026,
        "authors": "Jiaxiang Wang, Zhaohui Yang, Yahao Ding, Ye Hu, Mohammad Shikh-Bahaei",
        "venue": "arXiv:2604.11053",
        "source": "arXiv",
        "identifier": "arXiv:2604.11053",
        "task": "多用户分布式语义通信分类，抑制 cross-user semantic interference。",
        "datasets": "CIFAR-10 classification。",
        "baselines": "Deep JSCC、multi-user Deep VIB (alpha=0)、single-user upper bound。",
        "metrics": "classification accuracy、cross-decoding accuracy、latent visualization、SNR sweep。",
        "channel": "AWGN 多用户语义通信；低 SNR 强调鲁棒性。",
        "conditions": "beta=0.1，alpha=0.01；两用户/多用户 cross-user pair。",
        "intro": [
            "已有 IB-based SemCom 多聚焦单用户，忽视多用户 latent 表示之间的耦合和干扰。",
            "并行优化多个用户的 IB 目标会导致 latent-space redundancy 或 cross-decoding 错误。",
            "本文在 IB 中加入 task-conditioned orthogonality 项。",
        ],
        "method": "TOIB 为每个用户学习 VIB 表示，同时构造 matched/mismatched cross-user pairs，用条件互信息正则约束不同用户 latent 在任务条件下尽量正交。",
        "ib_formula": "$$\\mathcal L_{TOIB}=\\sum_i[-I(U_i;Y_i)+\\beta I(X_i;Z_i)]+\\alpha\\sum_{i\\ne j}I(Z_i;Z_j|W_{ij}).$$ 变分形式包含 CE、KL 和 CLUB 条件互信息估计。",
        "ib_variables": "$X_i$ 用户 i 输入，$Z_i$ 用户 i 语义 latent，$Y_i$ 信道接收表示，$U_i$ 任务标签/语义目标，$W_{ij}$ 是 task-conditioning pair variable，$\\alpha$ 控制跨用户正交。",
        "ib_process": "batch 训练：1) 每个用户 encoder 输出 latent posterior 并采样 $z_i$；2) 经信道得到 $y_i$，classifier 计算 CE；3) 每用户 KL posterior-prior 计算 compression 项；4) 构造用户对 $(i,j)$ 和条件变量 $W_{ij}$；5) CLUB estimator 估计 $I(Z_i;Z_j|W_{ij})$，作为 orthogonality penalty；6) 三部分合成 loss 并交替更新通信网络和 CLUB estimator。",
        "channel_handling": "信道噪声进入 $Y_i$，CE 项在 noisy received representation 上计算；orthogonality 项减少跨用户语义干扰。",
        "result": "TOIB 在多 SNR 下优于 Deep JSCC 和 Deep VIB，cross-decoding accuracy 显示用户间语义干扰被压低。",
        "limitation": "2026 arXiv 初稿，实验主要 CIFAR-10 分类，尚需更多模态和真实无线验证。",
        "judgement": "核心。它把 IB 扩展为带条件互信息正交项的多用户目标。",
    },
    {
        "title": "Disentangled Information Bottleneck Guided Multidevice Cooperative Task-Oriented Semantic Communication",
        "pdf": "Disentangled_Information_Bottleneck_Guided_Multidevice_Cooperative_Task-Oriented_Semantic_Communication.pdf",
        "year": 2026,
        "authors": "Meiyu Sun, Dapeng Wu, Puning Zhang, Ruyan Wang",
        "venue": "IEEE Transactions on Communications, 2026",
        "source": "IEEE",
        "identifier": "IEEE 11442655; DOI 10.1109/TCOMM.2026.3675469",
        "task": "多设备协同任务导向语义通信；common/private feature disentanglement 与 selective transmission。",
        "datasets": "MNIST、CIFAR-10、Downsampled ImageNet、ModelNet40 等多视图/多设备任务。",
        "baselines": "DeepJSCC without IB、independent IB、DIB/multi-view baselines、selective transmission ablations。",
        "metrics": "classification/retrieval accuracy、mAP、communication cost、feature importance、saliency。",
        "channel": "多设备到边缘服务器的语义符号传输；考虑 SNR 和通信开销。",
        "conditions": "先 basic IB 压缩，再 DisenIB 分解，再 MI-based selective transmission。",
        "intro": [
            "多设备协同能提升任务性能，但各设备特征存在大量冗余。",
            "粗粒度冗余消除不解释哪些特征共享、哪些特征私有。",
            "本文用 Disentangled IB 把 common/private features 显式拆开。",
        ],
        "method": "每个设备先用基本 IB 学局部 compressed semantic feature，再用 DisenIB 把特征拆为 common 和 private，最后根据 $I(V_k^c;\\hat V)$ 与 $I(V_k^p;\\hat V)$ 估计重要性选择传输。",
        "ib_formula": "基本 IB 的变分上界形如 $$\\mathbb E[-\\log q(y|z_k)]+\\beta KL[p(z_k|x_k)\\|q(z_k)].$$ DisenIB 目标包含任务项 $$-I(Y;\\hat V)-\\alpha\\sum_k I(Y;\\tilde V_k)$$ 与 disentanglement 项，鼓励 common features 共享、private features 与 common 独立。",
        "ib_variables": "$X_k$ 第 k 设备输入，$Z_k$ 压缩 latent，$V_k^c,V_k^p$ common/private encoded features，$\\hat V$ 聚合接收表示，$Y$ 任务标签。",
        "ib_process": "训练分阶段：1) local semantic encoder 输出 $z_k$ 并计算 CE+KL 的 basic IB loss；2) global JSCC encoder 把各设备特征拆为 $v_k^c,v_k^p$；3) 用 CE 奖励聚合表示完成任务；4) 用一致性约束/MINE 最大化 common feature 共享信息；5) 用 density-ratio discriminator 最小化 $I(V_k^c;V_k^p)$；6) 训练后用 MI estimator 评估 common/private 特征对任务的贡献，选择性传输高贡献特征。",
        "channel_handling": "信道影响多设备传输特征，selective transmission 根据特征重要性节省信道资源；IB 目标主要处理语义冗余和特征分解。",
        "result": "DisenIB-TOSC 在多任务上优于 baselines，并在减少通信成本时保持或提升任务性能。",
        "limitation": "训练阶段多、MI estimator 多，计算复杂度明显高于普通 TOSC。",
        "judgement": "核心。DIB/DisenIB 是整个框架的理论根基。",
    },
    {
        "title": "Multi-Task-Oriented Broadcast for Edge AI Inference via Information Bottleneck",
        "pdf": "Multi-Task-Oriented_Broadcast_for_Edge_AI_Inference_via_Information_Bottleneck.pdf",
        "year": 2023,
        "authors": "Yuhan Yang, Youlong Wu, Shuai Ma, Yuanming Shi",
        "venue": "IEEE GLOBECOM 2023",
        "source": "IEEE",
        "identifier": "IEEE 10437085; DOI 10.1109/GLOBECOM54140.2023.10437085",
        "task": "多用户广播信道上的多任务 edge AI inference。",
        "datasets": "MultiMNIST 风格 stitched image，多任务二分类/分类推理。",
        "baselines": "Deep JSCC with BCE、Digital JPEG、task-independent broadcast baselines。",
        "metrics": "task error rate、robustness to channel noise、compression ratio n/r、SNR sweep。",
        "channel": "degraded Gaussian broadcast channel。",
        "conditions": "two-phase training；每个任务 feature dimension 32，broadcast compact dimension 16 等设置。",
        "intro": [
            "多用户广播中不同设备任务不同、信道质量不同，直接广播统一特征会面临准确率和鲁棒性折中。",
            "IB 可学习任务相关且压缩的特征，但需扩展到 broadcast。",
            "本文提出两阶段 IB：先为每个任务提取特征，再压缩成鲁棒 broadcast signal。",
        ],
        "method": "Phase I 对每个任务训练 VIB feature extractor；Phase II 用 DIB/VDIB 把多任务特征压成 common broadcast signal，并通过 broadcast channel 发送。",
        "ib_formula": "Phase I: $$\\mathcal L_{IB,k}=H(Y_k|U_k)+\\gamma I(X;U_k)$$，变分为 CE + KL。Phase II: $$\\mathcal L_{DIB}=I(Z;U_{1:K})-\\mu\\sum_k I(U_k;\\hat Z_k),$$ 用 VDIB 近似优化 broadcast robust representation。",
        "ib_variables": "$X$ edge transmitter 输入，$U_k$ 第 k 个任务的 task-relevant feature，$Z$ compact broadcast signal，$\\hat Z_k$ 第 k 个设备接收的 noisy broadcast signal，$Y_k$ 第 k 个任务标签。",
        "ib_process": "batch 训练：Phase I 中 encoder 得到 $u_k$，task head 计算 BCE/CE，同时 KL 压缩 $u_k$；Phase II 中 broadcast encoder 把 $u_{1:K}$ 压成 $z$，通过 degraded Gaussian channel 得到各用户 $\\hat z_k$，各 task head 计算 BCE/CE，另用 KL/variational terms 约束 $z$ 不携带冗余多任务特征。",
        "channel_handling": "直接面向 degraded broadcast channel；IB 的第二阶段把信道鲁棒性和多任务共享压缩放在同一训练目标里。",
        "result": "相比 Deep JSCC 和 digital JPEG，IB broadcast 在多 SNR/压缩比下有更好的错误率与鲁棒性折中。",
        "limitation": "会议版较短，任务和数据集相对合成；后续 TWC rate-splitting 版更完整。",
        "judgement": "核心/先导。IB 是广播特征提取和压缩的核心目标。",
    },
    {
        "title": "Joint Source-Channel Coding for Task-Oriented Broadcast Communications: An Information Bottleneck Approach With Rate Splitting",
        "pdf": "Joint_Source-Channel_Coding_for_Task-Oriented_Broadcast_Communications_An_Information_Bottleneck_Approach_With_Rate_Splitting.pdf",
        "year": 2026,
        "authors": "Youlong Wu, Jingfeng Huang, Yuanming Shi, Shuai Ma, Kai Niu, Meixia Tao, Khaled B. Letaief",
        "venue": "IEEE Transactions on Wireless Communications, 2026",
        "source": "IEEE",
        "identifier": "IEEE 11434868",
        "task": "多任务 edge inference 的 task-oriented broadcast；Marton/rate-splitting + IB。",
        "datasets": "EuroSAT/remote sensing 等多任务推理数据；TWC 版扩展更多任务。",
        "baselines": "DeepJSCC、Digital BPG/JPEG、single-phase IB variants、GLOBECOM 2023 broadcast IB。",
        "metrics": "task accuracy/error、reconstruction fidelity、SNR robustness、phase ablation。",
        "channel": "multi-user broadcast channel；common/private codewords。",
        "conditions": "两阶段 rate-splitting：common feature + task-specific private feature。",
        "intro": [
            "多任务广播不仅要压缩，还要利用任务相关性和广播信道结构。",
            "早期 IB broadcast 没有充分区分 common/private information。",
            "本文把 Marton rate splitting 与 IB 对齐：共享任务信息走 common codeword，私有任务信息走 private codewords。",
        ],
        "method": "Phase 1 提取 common feature $U_c$；Phase 2 在 $U_c$ 条件下提取各任务 private feature $U_k$。两阶段都用 variational IB objective 训练，并映射到 rate-splitting broadcast codewords。",
        "ib_formula": "Common phase: $$\\mathcal L_{IB,c}= -I(Y;U_c)+\\gamma I(X;U_c).$$ Variational bound: $$\\mathcal L_{VIB,c}=\\mathbb E[-\\log p_\\phi(y|u_c)]+\\gamma\\mathbb E[KL(p_\\theta(u_c|x)\\|r_c(u_c))].$$ Private phase: $$\\mathcal L_{IB,k}= -I(Y_k;\\hat U_k|\\hat U_{c,k})+\\eta I(X;U_k|U_c),$$ 同样化为 conditional CE + conditional KL。",
        "ib_variables": "$X$ 输入，$Y$ 全任务标签集合，$Y_k$ 第 k 任务，$U_c$ common feature，$U_k$ private feature，$\\hat U_{c,k},\\hat U_k$ 是经信道到用户 k 的接收特征，$r_c,r_k$ 是变分 prior。",
        "ib_process": "batch：1) common encoder 输出 $p(u_c|x)$，采样 $u_c$；2) common task head 预测多任务标签，算 CE；3) 计算 $KL(p(u_c|x)||r_c)$；4) private encoder 在 $x,u_c$ 条件下输出 $u_k$，经 broadcast channel 得到用户接收；5) private head 用 $\\hat u_k,\\hat u_{c,k}$ 预测任务 k 并算 CE；6) 计算 conditional KL $KL(p(u_k|u_c,x)||r_k(u_k|u_c))$；7) 按 gamma/eta 加权训练。",
        "channel_handling": "将 IB common/private features 直接对应 Marton common/private codewords，使任务相关性和 broadcast channel degradation 结构一致。",
        "result": "Rate-Splitting IB 在 SNR sweep 和多任务扩展中优于 DeepJSCC 与单阶段 baselines。",
        "limitation": "模型和训练目标复杂；需要为不同任务/信道选择 common-private 拆分超参数。",
        "judgement": "核心。TWC 完整版把 IB 与广播信息论结构深度结合。",
    },
]


RELATED = [
    {
        "title": "Semantic Communication Unlearning via Variational Information Bottleneck",
        "year": 2025,
        "reason": "检索命中 VIB + semantic communication unlearning；出版源疑似 MDPI/Future Internet，按本项目既有惯例暂不纳入核心，后续若需要可作为相关应用单独核查。",
    },
    {
        "title": "Goal-oriented communication for edge learning based on the information bottleneck",
        "year": 2022,
        "reason": "是 goal-oriented/edge learning 与 IB 的重要背景，但不一定以 semantic communication 系统为主体，本轮作为背景引用线索。",
    },
    {
        "title": "Deep variational information bottleneck / classical IB papers",
        "year": 2017,
        "reason": "方法基础，不在 2021 至今语义通信应用范围内，只作为理论来源。",
    },
]


SEARCH_LOG = [
    "检索时间：2026-06-29。",
    "核心检索式：`information bottleneck semantic communication`, `robust information bottleneck semantic communication`, `variational information bottleneck task-oriented semantic communication`, `distributed information bottleneck semantic communication`, `information bottleneck JSCC semantic communication`, `privacy semantic communication information bottleneck`, `semantic communication information bottleneck HARQ`, `orthogonalised information bottleneck semantic communication`, `rate splitting information bottleneck broadcast communication`。",
    "筛选标准：必须在方法设计、目标函数、训练损失、资源分配或特征选择中实际使用 IB/VIB/DIB/RIB/DMIB/TOIB，而不是 introduction 中顺带提及。",
    "数据库与来源：arXiv、IEEE Xplore、web academic search；IEEE 独占全文使用 ieee-xplore-literature 串行下载。",
    "当前为第一轮深读版：已经覆盖单用户语义恢复、图像 JSCC、数字调制 RIB、隐私 IBAL/DIB、多模态 DMIB/TADIB、多用户 TOIB、多设备 DisenIB、HARQ-IBJSC、broadcast/rate-splitting IB 等主要路线。",
]


def sorted_papers() -> list[dict]:
    return sorted(PAPERS, key=lambda p: (p["year"], p["title"].lower()))


def method_asset(pdf: str) -> str:
    prefix = asset_slug(pdf)
    matches = sorted((ROOT / "assets").glob(f"{prefix}_method_p*.png"))
    return f"assets/{matches[0].name}" if matches else ""


def result_asset(pdf: str) -> str:
    prefix = asset_slug(pdf)
    matches = sorted((ROOT / "assets").glob(f"{prefix}_result_p*.png"))
    return f"assets/{matches[0].name}" if matches else ""


def page_from_asset(asset: str) -> str:
    m = re.search(r"_p(\d+)\.png$", asset)
    return m.group(1) if m else "?"


def table(rows: list[list[object]], headers: list[str]) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "\n".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def nav_html(papers: list[dict]) -> str:
    parts = []
    year = None
    for p in papers:
        if p["year"] != year:
            year = p["year"]
            parts.append(f"<div class='nav-year'>{year}</div>")
        parts.append(f"<a class='paper-link' href='#{slug(p['title'])}'>{esc(p['title'])}</a>")
    return "\n".join(parts)


def paper_section(p: dict) -> str:
    m_asset = method_asset(p["pdf"])
    r_asset = result_asset(p["pdf"])
    intro = "".join(f"<li>{esc(x)}</li>" for x in p["intro"])
    figs = ""
    if m_asset:
        figs += f"""<figure><img src="{esc(m_asset)}" loading="lazy" alt="{esc(p['title'])} method"><figcaption>方法/架构图页：来自《{esc(p['title'])}》PDF p.{page_from_asset(m_asset)}。</figcaption></figure>"""
    if r_asset:
        figs += f"""<figure><img src="{esc(r_asset)}" loading="lazy" alt="{esc(p['title'])} result"><figcaption>关键结果图/表页：来自《{esc(p['title'])}》PDF p.{page_from_asset(r_asset)}。</figcaption></figure>"""
    return f"""
    <article id="{slug(p['title'])}" class="paper">
      <h2>{esc(p['title'])}</h2>
      <h3>基本信息</h3>
      {table([
        ["作者", p["authors"]],
        ["发表/来源", f"{p['venue']} / {p['source']} / {p['year']}"],
        ["标识", p["identifier"]],
        ["任务", p["task"]],
      ], ["字段", "内容"])}
      <h3>数据集与 Baseline</h3>
      {table([
        ["数据集", p["datasets"]],
        ["Baseline", p["baselines"]],
        ["评价指标", p["metrics"]],
        ["信道类型", p["channel"]],
        ["实验条件", p["conditions"]],
      ], ["字段", "内容"])}
      <h3>Introduction 讲述逻辑</h3>
      <ol class="logic">{intro}</ol>
      <h3>方法概述</h3>
      <p>{esc(p["method"])}</p>
      <h3>信息瓶颈理论具体如何用上</h3>
      <div class="ib-block"><strong>公式/目标：</strong>{p["ib_formula"]}</div>
      <p><strong>变量含义：</strong>{esc(p["ib_variables"])}</p>
      <div class="calc"><strong>给定一个 batch 时如何计算：</strong>{esc(p["ib_process"])}</div>
      <h3>信道处理机制</h3>
      <p>{esc(p["channel_handling"])}</p>
      <h3>主要结果与图表</h3>
      <div class="figgrid">{figs}</div>
      <p>{esc(p["result"])}</p>
      <h3>局限性与 Codex 判断</h3>
      <p><strong>局限性：</strong>{esc(p["limitation"])}</p>
      <p><strong>判断：</strong>{esc(p["judgement"])}</p>
    </article>
    """


def build_html() -> str:
    papers = sorted_papers()
    overview_rows = [[p["year"], p["title"], p["task"], p["channel"], p["source"], p["judgement"]] for p in papers]
    comparison_rows = [[p["year"], p["title"], p["ib_formula"], p["ib_process"][:220] + ("..." if len(p["ib_process"]) > 220 else ""), p["datasets"], p["baselines"]] for p in papers]
    related_rows = [[r["year"], r["title"], r["reason"]] for r in sorted(RELATED, key=lambda r: (r["year"], r["title"]))]
    search_items = "".join(f"<li>{esc(x)}</li>" for x in SEARCH_LOG)
    sections = "\n".join(paper_section(p) for p in papers)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>信息瓶颈应用于语义通信文献调研</title>
  <script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']]}}}};</script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
  <style>
    :root {{ --ink:#182230; --muted:#667085; --line:#d7dde5; --paper:#fff; --soft:#f6f8fb; --accent:#0f766e; --accent2:#6941c6; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:#eef2f6; font:15px/1.65 "Segoe UI","Microsoft YaHei",Arial,sans-serif; }}
    .layout {{ display:grid; grid-template-columns:340px minmax(0,1fr); min-height:100vh; }}
    nav {{ position:sticky; top:0; height:100vh; overflow:auto; padding:18px; background:#17202a; color:#e8eef6; }}
    nav h1 {{ font-size:18px; line-height:1.35; margin:0 0 12px; }}
    nav .small {{ color:#a8b3c2; font-size:12px; margin-bottom:14px; }}
    nav a {{ display:block; color:#dbeafe; text-decoration:none; padding:8px 6px; border-bottom:1px solid rgba(255,255,255,.08); font-size:13px; }}
    nav a:hover {{ background:rgba(255,255,255,.08); }}
    .nav-year {{ color:#93c5fd; font-weight:700; margin:16px 0 4px; padding:6px 4px; border-top:1px solid rgba(255,255,255,.16); }}
    .paper-link {{ padding-left:14px; }}
    main {{ padding:28px 36px 80px; max-width:1280px; }}
    header, section, article.paper {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:24px; margin-bottom:22px; box-shadow:0 1px 2px rgba(16,24,40,.06); }}
    h1,h2,h3 {{ line-height:1.25; margin:0 0 12px; }}
    h1 {{ font-size:30px; }}
    h2 {{ font-size:23px; }}
    h3 {{ font-size:17px; margin-top:22px; color:#12364f; }}
    p {{ margin:8px 0; }}
    .lead {{ font-size:16px; color:#344054; }}
    .badges {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
    .badge {{ background:#ecfdf3; color:#05603a; border:1px solid #a6f4c5; border-radius:999px; padding:4px 10px; font-size:12px; }}
    .badge.alt {{ background:#f4f3ff; color:#5925dc; border-color:#d9d6fe; }}
    .table-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:6px; margin:12px 0; }}
    table {{ width:100%; border-collapse:collapse; min-width:760px; background:#fff; }}
    th,td {{ text-align:left; vertical-align:top; padding:9px 10px; border-bottom:1px solid #edf1f6; }}
    th {{ background:#f8fafc; color:#344054; font-weight:650; }}
    tr:last-child td {{ border-bottom:0; }}
    .logic {{ padding-left:22px; }}
    .ib-block,.calc {{ background:#f8fafc; border-left:4px solid var(--accent); padding:12px 14px; margin:12px 0; }}
    .calc {{ background:#f0fdfa; }}
    .figgrid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:14px; }}
    figure {{ margin:0; border:1px solid var(--line); border-radius:6px; background:#fbfcfe; overflow:hidden; }}
    figure img {{ width:100%; display:block; background:#fff; }}
    figcaption {{ padding:10px 12px; color:#475467; font-size:13px; }}
    @media (max-width:980px) {{ .layout {{ grid-template-columns:1fr; }} nav {{ position:relative; height:auto; max-height:55vh; }} main {{ padding:18px; }} }}
  </style>
</head>
<body>
<div class="layout">
  <nav>
    <h1>信息瓶颈应用于语义通信</h1>
    <div class="small">2021 至今；只纳入方法中实际使用 IB/VIB/DIB/RIB 的论文。</div>
    <a href="#overview">总览与检索策略</a>
    <a href="#comparison">IB 用法横向比较</a>
    {nav_html(papers)}
    <a href="#related">相关但非核心</a>
  </nav>
  <main>
    <header id="overview">
      <h1>信息瓶颈应用于语义通信：2021 至今文献调研初版</h1>
      <p class="lead">本页是新的独立调研，不要求计算实际 payload/压缩率，而是把重点替换为：论文如何具体使用 Information Bottleneck，目标函数是什么、变量是什么、给定一个 batch 时每一项如何计算。</p>
      <div class="badges"><span class="badge">核心深读 {len(papers)} 篇</span><span class="badge alt">图页 {len(list((ROOT/'assets').glob('*.png')))} 张</span><span class="badge alt">IEEE/arXiv 混合来源</span></div>
      <h3>检索策略</h3>
      <ul>{search_items}</ul>
      <h3>核心论文总览</h3>
      {table(overview_rows, ["年份","完整论文标题","任务","信道","来源","纳入判断"])}
    </header>
    <section id="comparison">
      <h2>IB 用法横向比较</h2>
      {table(comparison_rows, ["年份","论文","IB 目标/公式","给定 batch 的计算过程摘要","数据集","Baseline"])}
    </section>
    {sections}
    <section id="related">
      <h2>相关但非核心/待核查</h2>
      {table(related_rows, ["年份","标题","原因"])}
    </section>
  </main>
</div>
</body>
</html>"""


def write_csv(path: pathlib.Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    papers = sorted_papers()
    (ROOT / "index.html").write_text(build_html(), encoding="utf-8-sig")
    with (ROOT / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for p in papers:
            rec = {
                "title": p["title"],
                "year": p["year"],
                "authors": p["authors"],
                "venue": p["venue"],
                "source": p["source"],
                "identifier": p["identifier"],
                "task": p["task"],
                "pdf": str(pathlib.Path("papers") / p["pdf"]).replace("\\", "/"),
                "download_status": "downloaded",
                "analysis_status": "initial_deep_section_in_index_html",
                "core_reason": p["judgement"],
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    write_csv(
        ROOT / "included_core.csv",
        [
            {
                "year": p["year"],
                "title": p["title"],
                "source": p["source"],
                "venue": p["venue"],
                "task": p["task"],
                "ib_usage": re.sub(r"<[^>]+>", "", p["ib_formula"]),
                "pdf": p["pdf"],
            }
            for p in papers
        ],
        ["year", "title", "source", "venue", "task", "ib_usage", "pdf"],
    )
    candidate_rows = [{"year": p["year"], "title": p["title"], "decision": "included_core", "reason": p["judgement"]} for p in papers]
    candidate_rows.extend({"year": r["year"], "title": r["title"], "decision": "related_or_excluded", "reason": r["reason"]} for r in RELATED)
    candidate_rows.sort(key=lambda r: (int(r["year"]) if str(r["year"]).isdigit() else 9999, r["title"]))
    write_csv(ROOT / "candidate_pool.csv", candidate_rows, ["year", "title", "decision", "reason"])
    (ROOT / "search_strategy.md").write_text("# Search Strategy\n\n" + "\n".join(f"- {x}" for x in SEARCH_LOG) + "\n", encoding="utf-8-sig")


if __name__ == "__main__":
    main()
