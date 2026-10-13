# IEEE TVT 语义通信与 DeepJSCC 调研：检索与筛选记录

## 范围

- 刊物：IEEE Transactions on Vehicular Technology（ISSN 0018-9545 / 1939-9359）。
- 时间：2023-01-01 至 2026-10-13；正式卷年优先，尚未编入卷期的记录按 Early Access 年归档。
- 核心主题：语义通信、任务/目标导向通信、DeepJSCC、数字语义表示、无线图像/视频/语音/点云传输，以及信道鲁棒接收。
- 直接相关层：围绕语义链路开展的 V2X/UAV 资源、波束、轨迹、接入、控制和安全优化，以及与 DeepJSCC 技术路线相邻的传统 JSCC 工作。

## 检索轮次

1. OpenAlex 全刊元数据扫描：读取日期范围内 TVT 论文的题名与可用摘要，再以语义通信、任务通信和 JSCC 词族筛选。
2. Crossref 按 TVT ISSN 独立检索：覆盖项目要求的 digital semantic communication、VQ/PQ、codebook、quantization、index/bit error、OFDM、semantic-aware channel coding 与 DeepJSCC 关键词。
3. 车辆场景扩展：补充 vehicular/V2X/UAV、autonomous driving、image/video transmission、feature transmission、semantic HARQ 等组合。
4. IEEE Xplore 与全文复核：以 DOI、题名、卷期、PDF 首页和 IEEE document number 校验归属。
5. 引用与被引扩展：围绕数字量化、图像/视频 DeepJSCC、车辆协同感知和信道错误处理论文扩展；连续检索轮次没有新增核心 TVT 题名后确认饱和。

本次共执行 36 组查询。数据库请求统计见 `search_audit.json`。

## 筛选标准

- 核心纳入：直接设计语义表示、语义编解码器、DeepJSCC、量化/调制、生成式接收、信道鲁棒机制或完整语义传输系统。
- 直接相关：以语义链路为明确前提，主要贡献位于资源、控制、网络、安全或理论层；传统 JSCC 仅用于解释 DeepJSCC 的技术邻域。
- 排除：无线感知指标、CSI 反馈/预编码、联邦学习或波束预测论文中没有语义/JSCC 传输链路的记录。

## 流量与可追溯性

- 去重候选：103 篇。
- 核心纳入：59 篇。
- 直接相关：40 篇。
- 排除：4 篇。
- 已取得并校验全文：42 篇，其中 10 篇复用项目内合法版本、32 篇由 DOI/OpenAlex/Semantic Scholar/arXiv 等合法开放来源补齐。
- 待全文核验：57 篇。IEEE Xplore 串行补齐阶段返回 HTTP 418 “Unusual Traffic Detected”，已按访问规则停止自动请求；这些论文只保留题录与筛选状态，不生成全文方法结论。

候选池、纳入表、排除表、下载队列与请求审计分别保存在 `candidate_pool.jsonl`、`included.jsonl`、`excluded.jsonl`、`ieee_download_queue.csv` 和 `search_audit.json`。
