# Zhijin Qin Semantic Communications: Search Strategy and Saturation Log

## Scope

- 时间范围：2021-01-01 至 2026-07-10。
- 作者锚点：Zhijin Qin（清华大学；OpenAlex `A5044671638`；Semantic Scholar 主实体 `67022972`；DBLP `157/9149`）。
- 纳入：Zhijin Qin 作为作者、且以 semantic communication、task/goal-oriented communication、semantic-aware network、semantic source-channel coding、semantic compression/transmission 为实质研究对象的论文。
- 包含正式期刊/会议论文和尚无正式版本的 arXiv 预印本；同一论文的预印本与正式版本只保留正式版本。
- 排除：编者按、专著和专著章节、仅在背景中提及语义通信的边缘智能论文、视频分割挑战报告，以及不涉及通信信道或语义任务的纯压缩论文。

## Author disambiguation

- OpenAlex 主实体有 304 条全时期成果，最新机构为 Tsinghua University；2021 年后共有 178 条作品记录。
- Semantic Scholar 将近年成果拆分到多个同名实体，因此同时检查 `67022972`、`2256787925`、`2286690160`、`2099587837`、`2380664613`、`2329882981`、`2381803956`，并要求论文作者表中出现精确姓名 `Zhijin Qin`。
- DBLP 作者实体 `157/9149` 明确标注 `isnot Zhijing Qin`，用于排除拼写近似的另一位作者。

## Databases and queries

1. OpenAlex author works：`authorships.author.id:A5044671638`，时间从 2021-01-01 开始，共 178 条。
2. OpenAlex author-with-topic searches：`semantic communication`、`task-oriented communication`、`DeepSC`、`goal-oriented communication`。
3. Semantic Scholar author papers：主作者实体及六个拆分实体；获取题名、摘要、DOI、arXiv ID、开放 PDF 和引文元数据。
4. DBLP：作者主页 XML `pid/157/9149.xml`，用于正式出版物和作者消歧交叉检查。
5. arXiv：`au:"Zhijin Qin"`，按提交时间排序，共返回 105 条全时期记录；重点补齐 2025—2026 年索引尚未收录的新论文。
6. DOI 官方跳转：用于把 IEEE DOI 解析成 IEEE document number，再由 `$ieee-xplore-literature` 获取正式全文。
7. Google Scholar：尝试公开检索 `"Zhijin Qin" "semantic communication"`，页面连接超时，未将其作为可复现数据源。

## Screening result

- 初始主题候选：130 条 OpenAlex 命中。
- 合并 arXiv 与 Semantic Scholar 的索引滞后条目后，进行正式版/预印本去重及人工规则筛选。
- 最终纳入：90 篇。
- 排除或边界：20 条，原因逐条记录在 `excluded_or_boundary.csv`。
- 全文：88 篇已下载并完成文本提取；2 篇未获全文。

## Full-text acquisition

- 56 篇通过 arXiv 合法开放版本串行下载。
- 4 篇复用本项目此前下载的相同全文。
- 28 篇通过 `$ieee-xplore-literature`、机构认证 Chrome 和 IEEE document number 串行下载；机构访问显示 `Peng Cheng Laboratory`。
- IEEE 下载使用 180 秒 WebSocket 超时、每篇额外 7 秒间隔，并验证 `HTTP 200`、`application/pdf` 和 `%PDF-` 文件头。
- *Toward Wisdom-Evolutionary and Primitive-Concise 6G...* 为金色开放论文，但 ScienceDirect 脚本请求返回 403，正常浏览器页面触发 CAPTCHA，未绕过验证。
- *Goal-oriented communications for future cyber–physical systems* 的 Nature 页面未提供开放 PDF，直链返回 HTML，未绕过付费访问。

## Saturation assessment

第一轮 OpenAlex 主题检索产生主要历史语料；Semantic Scholar 拆分实体补充正式 DOI 和少量最新论文；arXiv 作者检索补充 2025—2026 年索引滞后论文。随后 DBLP、正式 DOI 跳转和重复题名核对没有再产生新的 2021—2024 核心论文。新增项主要是正式版替换、专著章节或非语义通信边界项，因此在 2026-07-10 时点判定达到作者维度的实用检索饱和，而不宣称未来更新意义上的绝对完备。
