from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- FINAL-CENSUS-BEGIN -->"
END = "<!-- FINAL-CENSUS-END -->"
TEAM_FOLDERS = {
    "kai-niu-semantic-communications", "zhijin-qin-semantic-communications", "meixia-tao-semantic-communications",
    "deniz-gunduz-semantic-communications", "yi-ma-mahdi-mashhadi-semantic-communications",
    "arumugam-nallanathan-deepsc-semantic-communications",
}


def rows(path: Path) -> list[dict]:
    if not path.exists(): return []
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))


def main() -> None:
    for strategy in ROOT.glob("*/search_strategy.md"):
        root = strategy.parent
        if root.name not in TEAM_FOLDERS:
            text = strategy.read_text("utf-8")
            if BEGIN in text and END in text:
                text = text[:text.index(BEGIN)].rstrip() + "\n"
                strategy.write_text(text, encoding="utf-8")
            continue
        included = rows(root / "included_papers.csv")
        excluded = rows(root / "excluded_or_boundary.csv")
        candidates = rows(root / "candidate_pool.csv")
        downloaded = sum(r.get("download_status") == "downloaded" for r in included)
        blocked = [r for r in included if r.get("download_status") != "downloaded"]
        audit_path = root / "notes" / "saturation_audit.json"
        audit = json.loads(audit_path.read_text("utf-8")) if audit_path.exists() else {}
        rounds = "; ".join(f"{r['database']}: raw {r['raw_hits']}, topic {r['topic_hits']}, new formal technical {len(r.get('novel_formal_technical_records', []))}" + (f", error {r['error']}" if r.get('error') else "") for r in audit.get("rounds", []))
        block_text = "；".join(f"{r['title']}（{r.get('download_status','')}）" for r in blocked) or "无"
        section = f"""{BEGIN}

## 最终复核快照（2026-07-15）

- 候选池：{len(candidates)}；核心正式技术论文：{len(included)}；排除/背景/被取代记录：{len(excluded)}。
- 全文：{downloaded}/{len(included)} 份已通过 `%PDF`、页数、标题匹配与 SHA-256 校验；合法访问阻塞：{block_text}。
- 补充轮次：{rounds}。
- 饱和判断：{audit.get('saturation_judgment', '未生成')} 这里的“实用饱和”不等于数学意义上的绝对全部；新上线索引仍可继续进入维护清单。
- 数据源实际使用：OpenAlex 作者全集/关键词、Crossref、DBLP、Semantic Scholar（OA 批量与可用搜索轮次）、IEEE Xplore、DOI/出版社页面、Springer、SciOpen、ISCA Archive；Google Scholar 不做自动抓取，作为人工复核入口记录。

{END}
"""
        text = strategy.read_text("utf-8")
        if BEGIN in text and END in text:
            text = text[:text.index(BEGIN)] + section + text[text.index(END) + len(END):]
        else:
            text = text.rstrip() + "\n\n" + section
        strategy.write_text(text, encoding="utf-8")
        print(root.name, len(candidates), len(included), len(excluded), downloaded)


if __name__ == "__main__": main()
