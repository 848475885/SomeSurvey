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
- 已取得并校验全文：88 篇。其中首轮已有 42 篇，本轮以可见 Chrome 和已登录机构访问环境从 IEEE Xplore 串行补齐 43 篇，并从 PolyU 机构仓储、arXiv 等合法开放来源补齐 3 篇。
- 待全文核验：11 篇。对这些论文再次核对 IEEE Xplore 详情页、PDF 入口、精确题名、arXiv、作者主页和机构仓储后，PDF 入口仍回跳至详情/授权页面，或未发现可直接下载的合法全文；这些论文只保留题录与筛选状态，不生成全文方法结论。
- IEEE 下载节奏：逐篇访问，论文页停留 10 秒，两篇之间随机等待 15—25 秒；PDF 准备状态每 20 秒重试一次、最多 8 次。遇到 WAF、验证码、异常 HTML 或访问限制立即停止批量请求。
- 文件验证：所有 88 份全文均检查 `%PDF-` 文件头、页数、可解析性、文件大小和 SHA-256；标题匹配异常的作者接受稿另以首页题名、作者和 DOI 人工核对。

候选池、纳入表、排除表、下载队列与请求审计分别保存在 `candidate_pool.jsonl`、`included.jsonl`、`excluded.jsonl`、`ieee_download_queue.csv` 和 `search_audit.json`。
