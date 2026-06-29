# Search Strategy and Saturation Log

- 2026-06-29 追加泛化检索：在既有 digital semantic communication 之外加入 broad query `semantic communication`，再与 modulation、MQAM、QAM、constellation mapping、semantic codebook、HARQ、OFDM、VQ-VAE 等词组合；检索到的论文先读 abstract 判断是否真正涉及离散语义变量/数字调制/码本/bit-symbol error，而不是只看标题是否含 digital。
- 本轮新纳入核心：Important Bits Prefix M-Ary Quadrature Amplitude Modulation for Semantic Communications、Semantic-Oriented Modulation for Wireless Communication、Semantic Codebook-Based HARQ for Wireless Image Transmission、VQ-VAE Based Digital Semantic Communication with Importance-Aware OFDM Transmission。前两篇解释了为什么 `digital semantic communication` 可能漏掉 modulation-layer SemCom：题名和索引词主要写 semantic communication / modulation / MQAM，而非 digital semantic communication。
- 本轮元数据校验：部分网页 snippet 给出的 IEEE arnumber 与实际论文错配。Semantic Codebook-Based HARQ 最终用 DOI 10.1109/TCOMM.2025.3604326 下载到 IEEE 11145114；VQ-VAE+OFDM 的 IEEE snippet 编号指向无关 workshop 文，故采用 arXiv 2508.08686 开放全文并记录原因。
- IEEE Xplore: digital semantic communication, VQ semantic communication, digital JSCC semantic communication, semantic digital modulation, OFDM digital semantic communication, product quantization semantic communication.
- arXiv: vector quantization semantic communication, token communications, codebook design, channel-aware VQ, VQ-DeepVSC, VQ-DSC-R, MSVQ/CEC-MSVQ.
- Semantic Scholar: 对 12 组必需关键词检索，并以 VQ-DeepSC、VPQ-SemCom、D2-JSCC、MaskDSC、ESC-MVQ、sDMCM 等为 seed 做 references/citations 扩展。
- Web search: 精确题名检索补齐 IEEE arnumber、arXiv ID 和未命中候选；MDPI 结果按规则排除。
- 饱和判据: 新增关键词、引用和被引连续两轮主要产生同一批 VQ/codebook/UEP/BSC/OFDM/token 论文，新增项多为应用变体或未获全文边界项。

Candidate pool is intentionally larger than the final core set. IEEE papers were downloaded first via the IEEE Xplore literature skill with serial access and safe intervals; when search snippets exposed wrong arnumbers, DOI/arXiv records were used for verification and legal fallback. MDPI venues are excluded by project rule.
