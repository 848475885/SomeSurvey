# Search Strategy and Saturation Log

- IEEE Xplore: digital semantic communication, VQ semantic communication, digital JSCC semantic communication, semantic digital modulation, OFDM digital semantic communication, product quantization semantic communication.
- arXiv: vector quantization semantic communication, token communications, codebook design, channel-aware VQ, VQ-DeepVSC, VQ-DSC-R, MSVQ/CEC-MSVQ.
- Semantic Scholar: 对 12 组必需关键词检索，并以 VQ-DeepSC、VPQ-SemCom、D2-JSCC、MaskDSC、ESC-MVQ、sDMCM 等为 seed 做 references/citations 扩展。
- Web search: 精确题名检索补齐 IEEE arnumber、arXiv ID 和未命中候选；MDPI 结果按规则排除。
- 饱和判据: 新增关键词、引用和被引连续两轮主要产生同一批 VQ/codebook/UEP/BSC/OFDM/token 论文，新增项多为应用变体或未获全文边界项。

Candidate pool is intentionally larger than the final core set. IEEE papers were downloaded first via the IEEE Xplore literature skill; when the IEEE download for VQ-DeepVSC timed out without CAPTCHA/429, the legal arXiv version was used as fallback. MDPI venues are excluded by project rule.
