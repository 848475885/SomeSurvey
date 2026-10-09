# IEEE IoTJ 语义通信与 DeepJSCC 调研：检索与筛选记录

## 范围

- 刊物：IEEE Internet of Things Journal（ISSN 2327-4662 / 2372-2541）
- 时间：2023-01-01 至 2026-10-09；以正式卷年为主，尚未编入卷期的论文按 Early Access 年记录。
- 主题：语义通信、任务/目标导向通信、DeepJSCC、数字语义表示、无线图像/视频/语音传输，以及直接围绕语义链路展开的资源与网络优化。

## 检索轮次

1. OpenAlex 全刊元数据扫描：对日期范围内 IoTJ 全部记录读取标题与可用摘要，再以语义通信/JSCC/任务通信词族筛选。
2. Crossref 独立关键词检索：覆盖 digital semantic communication、VQ/PQ、codebook、quantization、index/bit error、OFDM、semantic-aware channel coding、DeepJSCC 等 24 组查询。
3. IEEE Xplore/网页搜索复核：核对期刊归属、卷期、DOI、document number 与 Early Access 记录。
4. 引用与被引扩展：围绕数字语义、量化/调制、图像/视频 DeepJSCC 核心论文检查同刊新增工作；无新核心题名时记为检索饱和。

## 筛选标准

- 核心纳入：论文直接设计语义表示、语义编解码器、JSCC/DeepJSCC、量化/调制、信道鲁棒接收或端到端语义传输系统。
- 相关纳入：论文以语义链路为明确前提，重点优化资源、控制、调度、波束、轨迹或理论度量。
- 排除：综合性 IoT/安全/联邦学习/数字孪生综述，或仅把“semantic”用于知识表示、分割、协议字段、缓存命名等非通信语义含义的论文。

## 当前流量

- 去重候选：109 篇。
- 核心纳入：77 篇。
- 相关纳入：23 篇。
- 排除：9 篇。
- 已有合法本地全文：10 篇；其余进入 IEEE Xplore 串行下载队列。

候选池、纳入表、排除表与数据库请求统计分别保存在 `candidate_pool.jsonl`、`included.jsonl`、`excluded.jsonl` 和 `search_audit.json`。
