from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PURE_JSCC = "全文定位为传统/神经联合信源信道编码、Polar/LDPC 或 CSI 反馈研究，未把语义、任务效用或意义保持作为实质研究对象；转入相关背景清单"
NON_TECH = "全文属于综述、愿景、教程、项目/范式说明或挑战讨论，缺少本次口径要求的独立技术方法与可核验实验；转入背景清单"
SUPERSEDED = "存在同团队、同方法家族且作者高度重合的正式期刊扩展版；按既定口径由期刊版取代"
DUPLICATE = "同一正式论文的机构仓储/书目重复记录；保留 DOI 对应的出版社记录"


EXCLUSIONS: dict[str, dict[str, str]] = {
    "kai-niu-semantic-communications": {
        "A Novel Deep Learning Architecture for Wireless Image Transmission": PURE_JSCC,
        "Neural Joint Source-Channel Decoding using Arithmetic Codes": PURE_JSCC,
        "Distributed Image Transmission Using Deep Joint Source-Channel Coding": PURE_JSCC,
        "Distributed Joint Source-Channel Polar Coding": PURE_JSCC,
        "Joint Source-Channel Polar-Coded Modulation": PURE_JSCC,
        "Joint Successive Cancellation List Decoding for the Double Polar Codes": PURE_JSCC,
        "Learned Image Transmission over MIMO Fading Channels": PURE_JSCC,
        "Rate-Compatible Joint Source-Channel Coding Scheme Based on 5GNR LDPC Codes": PURE_JSCC,
        "AdaJSCC: Instance-Adaptive Joint Source-Channel Coding for Wireless Image Transmission": PURE_JSCC,
        "Enhanced Joint Source-Channel Polarization Effect Based on Polarizing Matrix Extension": PURE_JSCC,
        "MambaJSCC: Deep Joint Source-Channel Coding with Visual State Space Model": PURE_JSCC,
        "SwinJSCC: Taming Swin Transformer for Deep Joint Source-Channel Coding": PURE_JSCC,
        "Learning Joint Source-Channel Coding for Wireless Image Transmission: A Benchmark": PURE_JSCC,
        "Learning to Decode Double Polar Codes for Joint Source-Channel Coding": PURE_JSCC,
        "Deep Joint Source-Channel Coding-based Multi-rate CSI Feedback for Time-varying Massive MIMO Channels": PURE_JSCC,
        "Toward Wisdom-Evolutionary and Primitive-Concise 6G: A New Paradigm of Semantic Communication Networks": NON_TECH,
        "Joint source-channel coding for 6G communications": NON_TECH,
        "Semantic Communication for the Internet of Vehicles: A Multiuser Cooperative Approach": NON_TECH,
        "Generative AI for Space-Air-Ground Integrated Networks": NON_TECH,
        "Semantic Communication Empowered NTN for IoT: Benefits and Challenges": NON_TECH,
        "ComAI: The Convergence of Communication and Artificial Intelligence": NON_TECH,
        "Generative AI Meets Wireless Networking: An Interactive Paradigm for Intent-Driven Communications": NON_TECH,
        "Trustworthy Intelligent Networks for Low-Altitude Economy": NON_TECH,
        "SemAudio: Semantic-Aware Streaming Communications for Real-Time Audio Transmission": SUPERSEDED + "：SemAudio: Semantic Communication for Audio Streaming Transmission (IEEE TVT, 2025)",
    },
    "zhijin-qin-semantic-communications": {
        "Toward Wisdom-Evolutionary and Primitive-Concise 6G: A New Paradigm of Semantic Communication Networks": NON_TECH,
        "A Generalized Semantic Communication System: From Sources to Channels": NON_TECH,
        "Multimedia Semantic Communications: Representation, Encoding and Transmission": NON_TECH,
        "Semantic Communication for the Internet of Vehicles: A Multiuser Cooperative Approach": NON_TECH,
        "AI Empowered Wireless Communications: From Bits to Semantics": NON_TECH,
        "Computing Networks Enabled Semantic Communications": NON_TECH,
        "Toward Intelligent Communications: Large Model Empowered Semantic Communications": NON_TECH,
        "Balancing Security and Efficiency in GAI-Driven Semantic Communication: Challenges, Solutions, and Future Paths": NON_TECH,
        "On the Role of Semantic Communication in Non-Terrestrial Networks": NON_TECH,
        "Semantic Communication Enabled Holographic Video Processing and Transmission": NON_TECH,
        "Semantic Communications for Speech Recognition": SUPERSEDED + "：Deep Learning Enabled Semantic Communications With Speech Recognition and Synthesis (IEEE TWC, 2023)",
        "Semantic Communications for Speech Signals": SUPERSEDED + "：Semantic Communication Systems for Speech Transmission (IEEE JSAC, 2021)",
        "A Robust Deep Learning Enabled Semantic Communication System for Text": SUPERSEDED + "：A Robust Semantic Text Communication System (IEEE TWC, 2024)",
        "A Unified Multi-Task Semantic Communication System with Domain Adaptation": SUPERSEDED + "：A Unified Multi-Task Semantic Communication System for Multimodal Data (IEEE TCOM, 2024)",
        "Mem-DeepSC: A Semantic Communication System with Memory": SUPERSEDED + "：Semantic Communication With Memory (IEEE JSAC, 2023)",
        "Semantic-Aware Speech-to-Text Transmission Over MIMO Channels": SUPERSEDED + "：Semantic MIMO Systems for Speech-to-Text Transmission (IEEE TWC, 2024)",
        "Hybrid Digital-Analog Joint Semantic-Channel Coding for Image Transmission": SUPERSEDED + "：Hybrid Digital-Analog Semantic Communications (IEEE JSAC, 2025)",
        "Synchronous Semantic Communications for Video and Speech": SUPERSEDED + "：Synchronous Multi-Modal Semantic Communication System With Packet-Level Coding (IEEE TWC, 2025)",
    },
    "meixia-tao-semantic-communications": {
        "Federated Edge Learning for 6G: Foundations, Methodologies, and Applications": NON_TECH,
        "MambaJSCC: Deep Joint Source-Channel Coding with Visual State Space Model": PURE_JSCC,
        "Distributed Nonlinear Transform Source-Channel Coding for Wireless Correlated Image Transmission": PURE_JSCC,
        "SNR-EQ-JSCC: Joint Source-Channel Coding With SNR-Based Embedding and Query": PURE_JSCC,
        "Learning Based Joint Coding-Modulation for Digital Semantic Communication Systems": SUPERSEDED + "：Joint Coding-Modulation for Digital Semantic Communications via Variational Autoencoder (IEEE TCOM, 2024)",
        "A Superposition Code Approach for Digital Semantic Communications Over Broadcast Channels": SUPERSEDED + "：Deep Learning-Based Superposition Coded Modulation for Hierarchical Semantic Communications Over Broadcast Channels (IEEE TCOM, 2024)",
        "CDDM: Channel Denoising Diffusion Models for Wireless Communications": SUPERSEDED + "：CDDM: Channel Denoising Diffusion Models for Wireless Semantic Communications (IEEE TWC, 2024)",
        "Fusion-Based Multi-User Semantic Communications for Wireless Image Transmission Over Degraded Broadcast Channels": SUPERSEDED + "：Multi-User Semantic Fusion for Semantic Communications over Degraded Broadcast Channels (China Communications, 2024)",
        "Image Semantic Communication over Fading Channel: A Learned Broadcast Approach": SUPERSEDED + "：A deep learning based broadcast approach for image semantic communication over fading channels (China Communications, 2024)",
        "DM-MIMO: Diffusion Models for Robust Semantic Communications over MIMO Channels": SUPERSEDED + "：Semantic Communication Over MIMO Channels via Score-Based Reverse Mean Propagation (IEEE TWC, 2026)",
        "MIMO Semantic Communication via Score-Based Reverse Mean Propagation": SUPERSEDED + "：Semantic Communication Over MIMO Channels via Score-Based Reverse Mean Propagation (IEEE TWC, 2026)",
        "Prompt-based Multimodal Semantic Communication for Multi-spectral Image Segmentation": SUPERSEDED + "：ProMSC-MIS: Prompt-Based Multimodal Semantic Communication for Multi-Spectral Image Segmentation (IEEE OJ-COMS, 2025)",
    },
    "deniz-gunduz-semantic-communications": {
        "Transformer-Empowered 6G Intelligent Networks: From Massive MIMO Processing to Semantic Communication": NON_TECH,
        "Deep Joint Source-Channel Coding for Semantic Communications": NON_TECH,
        "Goal-Oriented and Semantic Communication in 6G AI-Native Networks: The 6G-GOALS Approach": NON_TECH,
        "AirNet: Neural Network Transmission over the Air": SUPERSEDED + "：AirNet: Neural Network Transmission Over the Air (IEEE TWC, 2024)",
        "DeepJSCC-Q: Channel Input Constrained Deep Joint Source-Channel Coding": SUPERSEDED + "：DeepJSCC-Q: Constellation Constrained Deep Joint Source-Channel Coding (IEEE JSAIT, 2022)",
        "Deep-Learning-Aided Wireless Video Transmission": SUPERSEDED + "：DeepWiVe: Deep-Learning-Aided Wireless Video Transmission (IEEE JSAC, 2022)",
        "Progressive Transmission of High-Dimensional Data Features for Inference at the Network Edge": SUPERSEDED + "：Progressive Feature Transmission for Split Classification at the Wireless Edge (IEEE TWC, 2022)",
        "A Hybrid Joint Source-Channel Coding Scheme for Mobile Multi-Hop Networks": SUPERSEDED + "：A Deep Joint Source-Channel Coding Scheme for Hybrid Mobile Multi-Hop Networks (IEEE JSAC, 2025)",
        "Deep Joint Source-Channel Coding Over the Relay Channel": SUPERSEDED + "：Process-and-Forward: Deep Joint Source-Channel Coding Over Cooperative Relay Networks (IEEE JSAC, 2025)",
    },
    "yi-ma-mahdi-mashhadi-semantic-communications": {
        "Semantic-Aware Power Allocation for Generative Semantic Communications with Foundation Models": SUPERSEDED + "：Generative Semantic Communications With Foundation Models: Perception-Error Analysis and Semantic-Aware Power Allocation (IEEE JSAC, 2025)",
        "Adaptive Semantic Communication for Gaze-guided Stereo Media Transmission": SUPERSEDED + "：Channel-Adaptive Semantic Communication for Stereoscopic Media: Design and Prototype Implementation (IEEE TCCN, 2026)",
        "Channel-adaptive Semantic Communication for Stereoscopic Media:Design and Prototype Implementation": DUPLICATE,
    },
    "arumugam-nallanathan-deepsc-semantic-communications": {
        "Generative Artificial Intelligence for Mobile Communications: A Diffusion Model Perspective": NON_TECH,
        "Goal-Oriented Semantic Communications for 6G Networks": NON_TECH,
        "Semantic Communications for Speech Recognition": SUPERSEDED + "：Deep Learning Enabled Semantic Communications With Speech Recognition and Synthesis (IEEE TWC, 2023)",
        "Semantic Communications for Speech Signals": SUPERSEDED + "：Semantic Communication Systems for Speech Transmission (IEEE JSAC, 2021)",
        "A Robust Deep Learning Enabled Semantic Communication System for Text": SUPERSEDED + "：A Robust Semantic Text Communication System (IEEE TWC, 2024)",
        "A Unified Multi-Task Semantic Communication System with Domain Adaptation": SUPERSEDED + "：A Unified Multi-Task Semantic Communication System for Multimodal Data (IEEE TCOM, 2024)",
        "Mem-DeepSC: A Semantic Communication System with Memory": SUPERSEDED + "：Semantic Communication With Memory (IEEE JSAC, 2023)",
        "Contrastive Learning based Semantic Communication for Wireless Image Transmission": SUPERSEDED + "：Contrastive Learning-Based Semantic Communications (IEEE TCOM, 2024)",
    },
}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for folder, rules in EXCLUSIONS.items():
        root = ROOT / folder
        included_path = root / "included_papers.csv"
        included = read_csv(included_path)
        fields = list(included[0]) if included else []
        excluded_path = root / "excluded_or_boundary.csv"
        excluded = read_csv(excluded_path)
        seen = {(r.get("doi") or "", r.get("title") or "") for r in excluded}
        kept: list[dict] = []
        log: list[dict] = []
        for row in included:
            reason = rules.get(row.get("title", ""))
            if not reason:
                kept.append(row)
                continue
            moved = dict(row)
            moved["screening_status"] = "excluded_after_fulltext_review"
            moved["screening_reason"] = reason
            moved["analysis_status"] = "fulltext_screened_out"
            key = (moved.get("doi") or "", moved.get("title") or "")
            if key not in seen:
                excluded.append(moved)
                seen.add(key)
            log.append({"title": moved.get("title", ""), "doi": moved.get("doi", ""), "reason": reason})

        write_csv(included_path, kept, fields)
        if excluded:
            excluded_fields = list(excluded[0])
            for f in fields:
                if f not in excluded_fields:
                    excluded_fields.append(f)
            write_csv(excluded_path, excluded, excluded_fields)
        write_csv(root / "notes" / "fulltext_screening_log.csv", log, ["title", "doi", "reason"])
        (root / "manifest.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in kept), encoding="utf-8"
        )
        print(f"[{folder}] included={len(kept)} moved_after_fulltext={len(log)}")


if __name__ == "__main__":
    main()
