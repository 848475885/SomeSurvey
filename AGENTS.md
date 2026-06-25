# Digital SemCom Survey

## Project Goal

在本项目中开展关于“数字语义通信（Digital Semantic Communications）”方向的系统性文献调研。Codex 应作为研究助理，完成从论文检索、全文下载、阅读分析到最终网页报告生成的完整流程。

不要只给计划。除非用户明确要求先讨论方案，否则应直接开始执行，并持续维护下载清单、结构化笔记和最终 HTML 报告。

## Scope

调研时间范围为 2021 年至今。

研究主题聚焦于“数字语义通信”，尤其关注：

- 语义通信中的数字化表示、离散语义特征、量化语义编码
- VQ、PQ、VPQ、码本、离散 token、语义特征量化等方法
- 图像、文本、语音、视频等任务中的数字语义通信系统
- 数字化语义特征在信道中的传输、纠错、鲁棒性、联合信源信道优化问题

优先检索并纳入 IEEE 期刊和会议论文，包括 IEEE Xplore 中的论文。ArXiv 论文可作为补充或备选。不要纳入 MDPI 期刊论文。

目标是尽可能系统地覆盖该方向的重要论文，但不要求机械意义上的“绝对全部”。必须记录检索策略、关键词、数据库来源和筛选标准，保证结果可追溯。

## IEEE Xplore Download Skill

当需要从 IEEE Xplore 下载全文 PDF 时，使用已创建的 `$ieee-xplore-literature` skill。

该 skill 会通过本机已配置的专用 Chrome profile 和 Chrome DevTools 端口访问 IEEE Xplore，不读取、不导出、不复制 Chrome cookie。若机构登录失效、出现 MFA 或 CAPTCHA，应暂停并要求用户在弹出的 Chrome 窗口中手动完成登录或验证，然后继续。

为避免快速访问 IEEE Xplore 导致触发限制，下载 IEEE 论文时应遵守以下节奏：

- 不要对 IEEE Xplore 进行高并发下载。
- 默认串行处理 IEEE 论文。
- 每篇 IEEE 论文的页面访问、PDF 请求、下一篇访问之间加入安全间隔，建议 5 至 15 秒。
- 如果出现 429、WAF challenge、验证码、异常 HTML 响应或访问失败，应停止批量请求，等待用户处理或延长间隔后再继续。
- 不要绕过 paywall、CAPTCHA、机构访问控制或安全验证。

## File Organization

在项目中创建并维护以下结构：

```text
literature/digital-semantic-communications/
  papers/
  assets/
  notes/
  manifest.jsonl
  index.html
```

对每篇纳入调研的论文：

- 下载 PDF 到 `literature/digital-semantic-communications/papers/`
- 使用统一命名规则，例如 `年份_第一作者_论文关键词.pdf`
- 记录论文来源、下载链接、DOI、IEEE document number 或 arXiv ID
- 如果论文来自 IEEE Xplore，优先使用 `$ieee-xplore-literature` 获取全文
- 如果 IEEE 无法下载，再尝试作者主页、arXiv 或其他合法开放来源

维护 `manifest.jsonl`，记录每篇论文的下载状态和元数据。

## Required Per-Paper Analysis

逐篇阅读全文，并为每篇论文整理以下信息。

### Basic Information

- 论文标题
- 作者
- 发表刊物或会议
- 发表时间
- 论文来源：IEEE / arXiv / 其他
- DOI / arXiv ID / IEEE document ID
- 研究任务：图像传输、文本传输、语音传输、视频传输、分类任务等
- 是否属于严格意义上的“数字语义通信”

### Experiment Setup

整理实验信息：

- 数据集
- Baseline 方法
- 评价指标
- 信道类型，例如 AWGN、Rayleigh、BSC、BEC、实际无线信道等
- SNR / CBR / BER / 压缩率等实验条件
- 主要实验结论

### Introduction Story Logic / Motivation

阅读每篇论文的 Introduction 后，总结它的“讲故事逻辑”。按照以下结构分析，而不是只翻译摘要：

1. 现有方法已经取得了什么进展？
2. 现有方法仍然存在什么问题？
3. 为什么这些问题在数字语义通信中重要？
4. 本文提出了什么方案？
5. 这个方案如何解决上述问题？
6. 作者希望证明什么核心观点？

### Method And Digitalization Scheme

重点分析论文如何实现“数字化语义通信”。从方法部分提取并总结：

- 语义编码器结构
- 语义特征形式：feature map、latent vector、token sequence、codebook index、bitstream 或其他表示
- 量化方式：VQ、PQ、VPQ、scalar quantization、learned quantization、entropy coding 或其他
- 是否使用码本
- 码本大小
- token 数量 / index 数量 / feature map 尺寸
- 每个符号或 token 的比特数
- 总传输比特数
- 与原始输入相比的压缩率

尽量给出具体数值。如果论文没有直接给出，需要根据模型参数、特征尺寸、码本大小、bit-depth、CBR 等信息推导，并清楚说明推导过程。

压缩率分析至少包括：

- 原始输入大小
- 编码后语义特征数量
- 量化后的符号数量或 bit 数
- 实际传输开销
- 压缩率或 CBR
- 数值来自论文原文还是由 Codex 推导得到

### Channel Handling Analysis

重点分析论文如何处理信道作用于数字化语义变量之后的问题。判断论文属于哪一类：

1. 仅提取语义特征，未真正考虑信道影响。比如编码端输出数字化语义特征后，默认通过传统信道编码保证无误传输。
2. 数字化语义特征加传统信道编码。比如 VQ / token / bitstream 经过 LDPC、Polar、Turbo、QAM 等传统通信链路，语义模型主要关注特征压缩。
3. 数字化语义特征直接经过有噪声信道。比如量化后的 index、bit 或 symbol 可能出错，解码端直接处理错误后的结果。
4. 数字化语义特征与信道联合优化。比如训练过程中显式建模信道噪声、index error、bit error、codeword corruption，解码端学习从受损离散变量中恢复语义信息。
5. 其他特殊机制。比如 unequal error protection、semantic-aware channel coding、robust codebook、index assignment、soft dequantization、概率码本、冗余 token 等。

特别关注：

- 离散变量经过信道后可能发生什么错误？
- 如果 VQ index 出错，是否会映射到完全不同的码本向量？
- 论文是否显式建模 index error / bit error？
- 是否有纠错机制？
- 是否有联合训练？
- 解码端拿到的是无误码的 index、有误码的 bitstream、带噪声的连续特征、soft information，还是经过信道译码后的符号？
- 论文是否真正解决了“数字化后信道错误导致语义特征失真”的问题？

必须给出判断，而不仅是复述论文说法。

## Cross-Paper Comparison

逐篇分析之后，制作横向总结表，比较所有论文：

- 年份
- 任务类型
- 是否数字化
- 量化方式
- 是否有码本
- 传输单位：bit / token / index / symbol / continuous latent
- 压缩率或 CBR
- 是否考虑信道错误
- 是否联合信源信道优化
- 使用的数据集
- Baseline
- 主要优点
- 主要局限

进一步总结该方向的发展脉络：

- 2021 至今数字语义通信的主要技术路线如何演进？
- 从连续 JSCC 到数字语义通信的动机是什么？
- 当前论文普遍解决了什么问题？
- 仍然没有解决好的核心问题是什么？
- 哪些论文真正处理了“离散语义变量经过信道后出错”的问题？
- 未来研究空白在哪里？

## Final HTML Report

最终生成 HTML 页面：

```text
literature/digital-semantic-communications/index.html
```

HTML 页面必须满足：

- 支持公式正确渲染，优先使用 MathJax 或 KaTeX
- 展示论文架构图、主要结果图、关键表格
- 每篇论文有独立小节
- 左侧或右侧提供浮动导航栏，可以快速跳转到任意论文
- 包含总览表、逐篇分析、横向比较和结论
- 对每篇论文链接到本地 PDF 文件
- 对图表引用标明来自哪篇论文和原图编号
- 页面风格简洁，适合长期阅读和查阅

从 PDF 中提取或截图保存重要架构图和实验结果图到：

```text
literature/digital-semantic-communications/assets/
```

## Execution Phases

分阶段执行：

1. 检索论文并给出候选列表
2. 根据筛选标准确定纳入论文
3. 下载 PDF 并建立 manifest
4. 阅读论文并提取结构化信息
5. 做横向比较
6. 生成 HTML 报告
7. 检查 HTML 公式、图片、导航和本地链接是否正常

如果某篇论文无法下载全文，记录原因，并尝试寻找合法开放版本。如果某篇论文只是“语义通信”但不是“数字语义通信”，标注为相关但不核心，不要强行纳入主表。

## Report Quality Gate

最终报告不能是摘要集合。只总结 abstract 或只给每篇论文一两句话，视为未完成。

生成或返工 `index.html` 时必须满足以下硬性要求：

- 导航栏必须按照论文完整标题组织，而不是按照短名称、编号或主题词组织。
- 每篇核心论文必须有独立的完整小节，小节标题使用论文完整标题。
- 每篇核心论文的小节内必须包含：基本信息、数据集与 baseline、Introduction 讲述逻辑、方法细节、数字化方案与传输开销、信道处理机制、主要结果图、架构图、作者方案的局限性与 Codex 的判断。
- Introduction 的讲述逻辑必须放在每篇论文自己的小节中，不能只放在总览表里。
- “数字化方案与传输开销”必须是详细分析，不能是一两句概括。必须尽量给出输入尺寸、encoder 输出 feature map 或 token 序列尺寸、量化方式、码本大小、每个 index/token/symbol 的 bit 数、总 bit 数、CBR 或压缩率。若论文没有直接给出，必须列出可推导信息、推导公式、假设条件和无法确定的原因。
- “信道处理机制”必须详细分析离散变量经过信道后的错误如何建模和处理。必须说明 decoder 收到的是无误 index、有误 bitstream、带噪连续特征、soft information、信道译码后的 bit，还是其他表示。必须明确判断该论文是否真正处理了 VQ index / bit / symbol 出错导致语义特征跳变的问题。
- 每篇核心论文必须至少提取并展示一张架构图或方法图，以及一张关键实验结果图或表。若 PDF 中没有合适图表，必须在该论文小节中说明原因。不要把所有图集中放到一个“关键图页”后就不在逐篇小节中展示。
- 每张图必须标注来源论文、原图编号或页码，并链接本地 PDF。
- 每篇核心论文分析应足够长，能够让读者不打开 PDF 也能理解该论文的动机、方法、数字化传输开销和信道处理。严禁“摘要翻译式”短段落。
- 对非核心但相关的论文，可以放入“相关但非核心”部分，但必须说明为什么不纳入核心主表。

文献覆盖也有质量门槛：

- 不得在只找到十几篇论文时宣称完成 2021 至今的“数字语义通信”调研。
- 必须进行多轮检索，包括 IEEE Xplore、arXiv、Semantic Scholar、Google Scholar 或可用学术搜索，以及核心论文的引用和被引扩展。
- 至少使用以下关键词组合进行检索并记录结果：`digital semantic communication`, `semantic communication vector quantization`, `VQ semantic communication`, `discrete semantic communication`, `semantic communication codebook`, `semantic communication quantization`, `digital JSCC semantic communication`, `semantic-aware channel coding`, `index error semantic communication`, `bit error semantic communication`, `OFDM digital semantic communication`, `product quantization semantic communication`。
- 必须维护候选论文池、排除列表和纳入列表。候选池应明显多于最终核心论文列表，并说明筛选理由。
- 在确认检索饱和之前，不要停止扩展文献。检索饱和的标准是：新增关键词、引用追踪和被引追踪连续多轮不再产生新的核心数字语义通信论文。

HTML 验收要求：

- 页面必须包含浮动目录，目录项使用论文完整标题，并能跳转到对应论文小节。
- 页面必须支持公式渲染，并在压缩率、CBR、bit 数推导处使用清晰公式。
- 页面应优先服务深度阅读，不要为了紧凑牺牲细节。
- 如果已有 `index.html` 不满足上述要求，应整体返工，而不是只在原页面上补几句。
