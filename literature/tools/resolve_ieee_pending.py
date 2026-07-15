from __future__ import annotations

import csv
import re
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
SESSION = requests.Session(); SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


def main() -> None:
    rows = []
    for path in ROOT.glob("*/notes/ieee_pending.csv"):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                row = {"Team": path.parent.parent.name, "Title": row["title"], "Doi": row["doi"].lower()}
                rows.append(row)
    unique = {}
    for row in rows:
        unique.setdefault(row["Doi"], row)
    resolved = []
    for idx, row in enumerate(unique.values(), 1):
        response = SESSION.get("https://doi.org/" + row["Doi"], allow_redirects=True, timeout=60)
        match = re.search(r"/document/(\d+)", response.url)
        if not match:
            match = re.search(r"arnumber=(\d+)", response.url)
        row["arnumber"] = match.group(1) if match else ""
        row["doi_url"] = response.url
        resolved.append(row)
        print(idx, len(unique), row["arnumber"], row["Title"])
        time.sleep(.3)
    out = ROOT / "ieee_pending_late_with_arnumber.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Team", "Title", "Doi", "arnumber", "doi_url"])
        writer.writeheader(); writer.writerows(resolved)


if __name__ == "__main__":
    main()
