# 数字语义通信结构化调研笔记

更新时间：2026-06-25

## 总体判断

本轮纳入 20 篇候选，其中核心数字语义通信论文 17 篇，相关/边界论文 3 篇。核心论文的技术主线可分为五类：

1. **VQ/codebook index + 传统数字链路**：VQ-DeepSC、Masked VQ-VAE、生成式 VQ、SQ-GAN、CEC-MSVQ 等。优点是语义变量离散化清晰；不足是很多论文默认 index 由传统信道编码保障，未充分建模 index 错误。
2. **数字调制端到端学习**：JCM、MDJCM、uJSCC。重点解决数字调制不可微、调制阶数变化和星座适配问题。
3. **标量/非线性量化 bitstream + 资源分配**：Digital-SC、OFDM-based digital SemCom。关注实际链路、BER/OFDM、bit/subcarrier 分配。
4. **离散变量错误显式建模/鲁棒优化**：CAVQ、Robust Digital JSCC、UEP channel coding、MaskDSC、VQ-DSC-R。最接近“数字化后信道错误导致语义特征失真”的核心问题。
5. **相关但非严格核心**：DeepJSCC-Q 属于有限星座/信道输入约束 JSCC，不是语义任务主导；Unified Multi-Task / Rate-Adaptive 多模态提供任务和重要性背景，但数字化机制不是唯一主线。

## 横向比较表

| 论文 | 年份 | 任务 | 数字化方式 | 传输单位 | 信道处理分类 | 数据集/指标 | 主要局限 |
|---|---:|---|---|---|---|---|---|
| VQ-DeepSC | 2023 | 图像重建 | 多尺度 VQ embedding space | index -> bitstream | 2：VQ + LDPC/AMC | Cars196/Kodak, MS-SSIM | 训练未显式优化 index error |
| Masked VQ-VAE | 2023 | 分类/检索/重建 | Masked VQ-VAE + FIM | codebook indices | 3/5：语义噪声和低 SNR，非严格 bit error | ImageNet 等，accuracy/Recall/visual | 更偏语义噪声鲁棒性 |
| Learning JCM | 2022 | 图像传输 | VAE/Gumbel 数字调制 | constellation symbols | 4：调制端到端训练 | Tiny ImageNet/图像指标 | 会议短文，后续由 TCOM 扩展 |
| JCM via VAE | 2024 | 图像重建/分类 | 学习 source-to-constellation 转移概率 | constellation symbols | 4：AWGN 下联合编码调制 | Tiny ImageNet, PSNR/accuracy | 主要 AWGN，非 bit-level coding |
| OFDM digital SemCom | 2024 | 分类 | scalar quantizer + bit/subcarrier allocation | bits / OFDM symbols | 5：OFDM + importance-aware allocation | CIFAR-10, distortion/accuracy | 重点是资源分配，非 VQ index 语义邻近 |
| Digital-SC | 2025 | 边缘分类/重建 | trainable nonlinear quantization | bit sequences | 3：BER/QAM 环境 + SLL | CIFAR-10/Mini-ImageNet | 信道错误主要作为 BER 测试/策略条件 |
| MDJCM | 2025 | 可变率图像传输 | multi-order modulation + entropy/NTSCC | QAM symbols/bitstream | 4/5：多调制阶训练 + turbo decoder | Kodak/CLIC, PSNR/CBR | 关注调制不可微与多阶兼容 |
| uJSCC | 2025 | 图像重建 | VQ codebook + multi-BN universal model | codebook index -> constellation | 4：多调制阶联合训练 | CIFAR-10/CelebA, PSNR/SSIM | SNR boundary 和 codeword assignment 仍待优化 |
| D2-JSCC | 2024 | 图像重建 | deep source coding bits + random/polar coding | bits | 2/5：数字源信道联合码率选择 | Kodak/CLIC, PSNR | 依赖查表/码率匹配 |
| Robust Digital JSCC | 2024 | 分类/重建 | binary-output JSCC | binary bits | 4：BSC/erasure-like channel sampling | 图像任务, accuracy/PSNR | 会议版，规模有限 |
| MaskDSC | 2025 | 图像语义 | masked transformer + UEP | semantic bits/tokens | 5：UEP | 图像指标 | 会议版细节有限 |
| Generative VQ E2E | 2025 | 图像生成式传输 | VQ + generative reconstruction | VQ indices | 2/3：VQ index digital link | CelebA/Flickr/Kodak 等 | 侧重感知质量，信道 index error 不一定充分 |
| SQ-GAN | 2025 | 图像重建 | masked VQ + GAN | VQ indices | 2/3：VQ digital image link | 图像感知指标 | 更偏 source representation |
| CEC-MSVQ | 2026 | 速率自适应 VQ | conditional entropy MSVQ | multi-stage indices/bits | 1/2：速率-失真为主 | task performance/rate | 不主攻 noisy discrete channel |
| CAVQ | 2025 | 图像重建 | channel-aware VQ | index/constellation | 4：DMC transition-aware codebook | CIFAR-10, PSNR | arXiv，需跟踪正式出版 |
| UEP channel coding | 2025 | 图像重建 | learned semantic bits + UEP coding | semantic bits | 5：bit-level UEP with repetition/polar/LDPC | MNIST/CIFAR, PSNR/SSIM | arXiv；依赖 learned target bit-flip probabilities |
| VQ-DSC-R | 2026 | OFDM 图像传输 | Swin + VQ SQC + ANDVQ | codebook indices over OFDM | 4/5：OFDM multipath + CSI refinement + SNR adaptation | ImageNet/DIV2K-style, PSNR/MS-SSIM | arXiv；系统较复杂 |
| Rate-Adaptive Multimodal | 2024 | 多模态任务 | rate-adaptive semantic coding | multimodal semantic features/bits | 5：重要性/码率控制 | VQA 等 | 与“数字 VQ index”关系较间接 |
| Unified Multi-Task | 2024 | 多模态多任务 | semantic feature transmission | mixed semantic features | related | 多模态任务 | 不作为严格数字化核心 |
| DeepJSCC-Q | 2022 | 图像重建 | fixed channel input alphabet | constellation-constrained symbols | related | CIFAR/Kodak 类图像指标 | 非语义通信主线，作为数字 JSCC 边界 |

## 每篇论文分析要点

### 1. Vector Quantized Semantic Communication System

- **基本信息**：Fu 等，IEEE WCL 2023，IEEE arnumber 10065571，DOI 10.1109/LWC.2023.3255221。
- **Introduction 逻辑**：连续/模拟 DeepJSCC 与 DeepSC 已能做图像、文本、语音语义传输，但不兼容数字通信；VQ 能把语义特征映射为 index 并转成 bits；已有 VQ 主要用于下游任务，图像重建不足。本文提出 VQ-DeepSC，用多尺度 U-Net 特征和 GAN loss 证明 VQ 也能做重建。
- **数字化方案**：语义 encoder 输出多尺度 feature tensor；每个 feature vector 以最近邻映射到 embedding space；发送 index 而非连续特征。文中给出多尺度 codebook 向量维度 \(K_1=128,K_2=256,K_3=512,K_4=1024\)，不同模型的 codebook vector number 如 \(N_1=8,N_2=4,N_3=2,N_4=2\) 等。
- **实验**：Cars196 训练，Kodak 测试；AWGN/Rician/Rayleigh 类信道；MS-SSIM；BPG、UNet-DeepJSCC、DeepJSCC 对比；LDPC blocklength 64800 bits，并比较 20/648/64800 bits。
- **信道判断**：类别 2。index 转 bit 后经过传统 channel coding/modulation，解码端拿到 channel decoder 恢复的 indices；没有端到端显式学习 index error 的语义后果。若 VQ index 错，确实会跳到另一个 codeword，但论文主要依赖 LDPC/AMC 降低错误。

### 2. Robust Semantic Communications With Masked VQ-VAE Enabled Codebook

- **基本信息**：Hu 等，IEEE TWC 2023，arnumber 10101778，DOI 10.1109/TWC.2023.3265201。
- **Introduction 逻辑**：语义通信已在重建和任务执行上有效，但 semantic noise 未充分研究；语义噪声可来自编码、信道、解码或攻击，导致“意义误解”。本文用 adversarial training、masked VQ-VAE 和 FIM 抑制噪声相关/任务无关特征。
- **数字化方案**：ViT/Masked VQ-VAE 架构，共享 discrete codebook；发送重要 task-related features 的 codebook indices。示例开销公式中，Patch=16 分类任务约 196 symbols/image，仅为 JPEG+LDPC 的 0.36%。
- **实验**：分类、检索、重建；SNR -9 到 18 dB，训练 -3 到 12 dB；比较 JSCC、JSCC+AT、JPEG+LDPC、Masked VQ-VAE 变体；指标包括 accuracy、Recall@1、视觉质量。
- **信道判断**：类别 3/5。论文强调 semantic noise 和低 SNR 鲁棒性，也考虑接收端语义噪声；但不是严格 bit/index error transition 的建模。它通过 FIM、mask、orthogonal codebook similarity 提升鲁棒性。

### 3. Joint Coding-Modulation for Digital Semantic Communications via VAE

- **基本信息**：Bo 等，IEEE TCOM 2024；会议前身 WCSP 2022；arnumber 10495330；DOI 10.1109/TCOMM.2024.3386577。
- **Introduction 逻辑**：现有 NN 语义通信多直接输出连续信道符号，不符合数字调制；简单量化再调制会与信道状态不匹配，硬量化不可微。本文用 VAE 让 encoder 学习从源数据到离散星座符号的转移概率，用 Gumbel-Softmax 解决不可微，并联合训练编码、调制和解码。
- **数字化方案**：\(M\)-order digital modulation，channel input \(Z\) 的每个元素取自 constellation \(C=\{c_1,\dots,c_M\}\)。不是 VQ codebook index，而是概率式 constellation symbol 生成。
- **实验**：Tiny ImageNet 类图像任务；AWGN；4QAM/16QAM/64QAM；channel use 128/1024 等；指标 PSNR 和 classification accuracy；对比 analog、DeepJSCC-Q、Uniform、NN/quantization methods。
- **信道判断**：类别 4。训练中包含 AWGN channel，优化目标把 source/semantic recovery 与调制联合起来；但错误变量是星座符号而非 VQ index，未使用传统 channel coding。

### 4. OFDM-Based Digital Semantic Communication With Importance Awareness

- **基本信息**：Liu 等，IEEE TCOM 2024，arnumber 10521803，DOI 10.1109/TCOMM.2024.3397862。
- **Introduction 逻辑**：多数 SemCom 采用模拟信道和简单 AWGN，难以落到现有数字 OFDM 系统；不同语义特征重要性不同，资源分配应以任务贡献为准。本文提出 OFDM-based digital SemCom，测量语义重要性，并进行 subcarrier 和 bit allocation。
- **数字化方案**：semantic encoder 输出 \(C\) 个连续语义特征；每个 \(a_i\) 经 scalar quantizer \(Q_{b_i}\) 量化为 bits，\(M_i=2^{b_i}\) levels；bitstream 经过 channel encoder、OFDM、频率选择性信道。
- **实验**：任务导向图像分类；多径/OFDM、BSC 扩展；指标 semantic distortion 和 classification accuracy；DPPO bit allocation 相比均匀/随机等 baseline 在低 SNR 或低 bit budget 下提升明显。
- **信道判断**：类别 5。它真正把 bit errors、OFDM 子载波条件和语义重要性连接起来，但不是 VQ index/codeword 语义邻近优化。

### 5. Digital-SC

- **基本信息**：Guo 等，IEEE TCCN 2025，arnumber 10772628，DOI 10.1109/TCCN.2024.3510586。
- **Introduction 逻辑**：设备-边缘协同推理需要传输中间语义特征；模拟 SemCom 难部署，线性量化不适合长尾特征分布；不同样本和信道条件需要不同 split point 和特征维度。本文用 adaptive split、structured pruning、learned nonlinear quantization 和 SLL。
- **数字化方案**：网络 split 后的 feature maps 经 pruning 和 trainable nonlinear quantization，输出 \(b\in\{0,1\}^{w_2h_2zq}\)，每个 quantization level 表示 \(q\) bits；支持 QPSK/16QAM/64QAM。
- **实验**：CIFAR-10、Mini-ImageNet 分类；CIFAR-10 重建；AWGN/BER 条件；对比 DJSCCQ、JCM、linear quantization、analog DJSCC；低阶调制有明显提升。
- **信道判断**：类别 3/5。模型看到 BER/channel condition 并用 policy/SLL 适配，但信道错误多作为 BER 扰动和系统选择变量，非显式 VQ index transition。

### 6. MDJCM

- **基本信息**：Zhang 等，IEEE TCOM 2025，arnumber 10778620。
- **Introduction 逻辑**：NTSCC 类方法可变率强，但多是连续符号；数字调制不可微，多数数字 SemCom 固定调制阶/小数据集。本文构造 multi-order modulator/demodulator，把调制/解调视为受限量化并用 substitute training + STE fine-tune。
- **数字化方案**：基于 entropy model 的 variable-rate source coder 输出 bit sequence；multi-order QAM 调制模块支持 4/16/64/256/1024QAM；rate \(R=E[-\log_2 P_{\hat y}(Q(g_a(x)))]\)，CBR 用于比较。
- **实验**：Kodak、CLIC2021、CLIC2022；AWGN/Rayleigh；PSNR vs CBR/SNR；BPG+LDPC、JPEG/JPEG2000+LDPC、DeepJSCC、NTSCC/NTSCC+、JCM 等。
- **信道判断**：类别 4/5。端到端考虑数字调制和多阶调制，且使用 turbo decoder/两阶段训练减少调制误差；重点仍是调制不可微和多阶兼容，而非逐 bit 语义 UEP。

### 7. uJSCC

- **基本信息**：Huh 等，IEEE JSAC 2025，arnumber 10960697，DOI 10.1109/JSAC.2025.3559138。
- **Introduction 逻辑**：已有 VQ/数字 SemCom 往往为每个调制阶数训练专用模型；实际系统要根据 SNR 切换 BPSK/4QAM/16QAM/64QAM/256QAM，单模型泛化是关键。本文提出 universal JSCC，用共享 encoder-decoder + VQ codebook + modulation-specific BN。
- **数字化方案**：encoder 输出 feature vector，经 VQ codebook 得到 index \(z_i\)，index 一对一或分组映射到 constellation symbols；接收端检测 symbol 后以 \(\hat z\) dequantize。
- **实验**：CIFAR-10 与 CelebA；BPSK 到 256QAM；PSNR/SSIM/MSE；对比 model-efficient、task-effective、多模型和 DeepJSCC-Q。
- **信道判断**：类别 4。训练覆盖多个 modulation order 与 SNR range，解码端处理检测后的错误 index；未来工作仍指出 learnable SNR boundary、power-efficient codeword assignment、SNR-adaptive codebook。

### 8. CAVQ

- **基本信息**：Meng 等，arXiv 2510.18604，2025。
- **Introduction 逻辑**：VQ 能数字化语义特征，但传统 VQ 忽略 CSI；codebook size 与 modulation order 不匹配也会破坏分析。本文提出 VQJSCC + CAVQ，把 channel transition probability 加入 codebook optimization，并用 multi-codebook 解决 bit alignment。
- **数字化方案**：feature matrix \(Z=[z_1,\dots,z_N]\)，每个向量用 codebook \(M\in R^{K\times d}\) 最近邻量化为 index \(y_i\)，每个 index 需要 \(\lceil\log_2 K\rceil\) bits；index bitstream 映射到 constellation，经过 DMC \(P(\hat c|c)\)。
- **实验**：CIFAR-10；SNR 动态采样 0-18 dB；PSNR/SSIM 等；对比 analog/digital JSCC baselines。
- **信道判断**：类别 4。它明确建模“发送 index 后被 channel transition 改成另一个 index”的损失，训练时把容易混淆的 modulation symbols 对应到语义相近 codewords，是本调研中最核心的 index-error 方案之一。

### 9. Unequal Error Protection for Digital Semantic Communication with Channel Coding

- **基本信息**：Kim 等，arXiv 2508.03381，2025。
- **Introduction 逻辑**：数字语义 bit 的重要性差异可达多个数量级，传统 equal protection 浪费资源；已有 semantic UEP 多是源级/词级/模态级，不到 bit-level。本文把 learned bit-flip probabilities 视为 target protection levels，设计 bit-level repetition UEP 和 block-level polar/LDPC UEP。
- **数字化方案**：semantic encoder output 量化为 \(K=MB\) semantic bits；每个 bit 有目标 flip probability \(\mu_i\)，channel coding 后映射到 modulation symbols。
- **实验**：MNIST、CIFAR-10、CIFAR-100；feature vector 8-bit quantization；Rayleigh block fading，SNR 固定 0 dB；PSNR/SSIM vs blocklength；Block-UEP 接近 genie upper bound，显著优于 equal LDPC/Polar。
- **信道判断**：类别 5。真正对 semantic bits 的不同错误敏感度做 channel coding 设计，是“数字化后 bit error 导致语义失真”的直接回答。

### 10. VQ-DSC-R

- **基本信息**：Chen 等，arXiv 2602.15045，2026。
- **Introduction 逻辑**：VQ-enabled DSC 具有 codebook 可解释性，但存在 quantization error、gradient/codebook collapse；同时 index sequence 在 OFDM 多径和信道估计误差下会出错。本文提出 Swin + VQ SQC + ANDVQ + CDM CSI refinement + SNR ModNet。
- **数字化方案**：Swin semantic encoder 输出特征；nearest-neighbor VQ 映射到 shared semantic quantized codebook \(C\in R^{K\times N}\)，发送 index sequence \(I_s\)；OFDM 传输；ANDVQ 用 KNN adaptive noise variance 和 EMA 稳定训练。
- **实验**：图像传输，3GPP/EPA 类 multipath OFDM；BCR=0.006/0.02；codebook \(K=64,128,256\)；指标 PSNR/MS-SSIM、BER/NMSE；ANDVQ 在 K=128 表现最优。
- **信道判断**：类别 4/5。它不只考虑 index 量化，还把 OFDM 多径、CSI refinement 和 SNR adaptation 纳入系统优化，是面向真实物理层的 VQ 数字 SemCom。

## 发展脉络与研究空白

2021-2022 年的主线仍以连续 DeepSC/DeepJSCC 和有限星座约束为主；2023 年 VQ-DeepSC 和 Masked VQ-VAE 把 codebook/index 引入语义通信并证明了实用价值；2024 年 JCM/Digital-SC/OFDM 开始把数字调制、非线性量化、OFDM 和任务重要性纳入模型；2025-2026 年的重点转向多调制阶泛化、离散信道显式建模、semantic-bit UEP、OFDM 真实链路和 codebook 稳定训练。

从连续 JSCC 到数字语义通信的根本动机是部署兼容性：现有硬件、标准、信道编码、调制、OFDM、HARQ/AMC 都围绕 bits/symbols 工作。连续语义 latent 即使性能好，也难以直接落到数字基带链路。

目前已经较好解决的问题：

- 如何把语义特征离散为 index/bit/token。
- 如何绕过 VQ/quantization/modulation 不可微问题。
- 如何在不同调制阶、CBR、SNR 下做自适应。
- 如何利用语义重要性减少 bit/symbol 开销。

仍未解决好的核心问题：

- VQ index 出错后可能映射到语义完全不相近 codeword，很多论文仍靠 LDPC/Polar 假设错误很少，而不是优化 codebook-index assignment。
- 语义重要性、bit 重要性和信道码率/调制阶之间缺少统一端到端理论。
- 多数结果集中在图像小数据集或重建指标，对文本/语音/视频和多任务场景的数字化信道错误分析不足。
- 真实协议栈中的 soft information、HARQ、interleaving、LLR、pilot/CSI 误差与语义 decoder 的接口仍不清晰。

真正处理“离散语义变量经过信道后出错”的代表论文：CAVQ、UEP channel coding、Robust Digital JSCC、uJSCC、VQ-DSC-R、OFDM-based digital SemCom、MaskDSC。VQ-DeepSC、Masked VQ-VAE、生成式 VQ、SQ-GAN、CEC-MSVQ 更偏语义特征离散化与压缩，信道错误处理相对间接。

