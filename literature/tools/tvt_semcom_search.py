#!/usr/bin/env python3
"""Build the IEEE TVT semantic-communication candidate census."""

from __future__ import annotations

import re
from pathlib import Path

import iotj_semcom_search as base


ROOT = Path(__file__).resolve().parents[2]
base.OUT = ROOT / "literature" / "ieee-tvt-semantic-communications-2023-present"
base.NOTES = base.OUT / "notes"
base.SOURCE_ID = "S10936095"
base.VENUE = "IEEE Transactions on Vehicular Technology"
base.CROSSREF_ISSN = "0018-9545"
base.ISSNS = ["0018-9545", "1939-9359"]
base.START = "2023-01-01"
base.END = "2026-10-13"

base.QUERIES = list(dict.fromkeys(base.QUERIES + [
    "vehicular semantic communication",
    "V2X semantic communication",
    "semantic communication autonomous driving",
    "semantic-aware vehicular network",
    "task-oriented vehicular communication",
    "goal-oriented vehicular communication",
    "image transmission vehicular network",
    "video transmission vehicular network",
    "feature transmission edge inference",
    "joint source channel coding image transmission",
    "joint source channel coding video transmission",
    "semantic HARQ vehicular",
]))

base.TOPIC_RE = re.compile(
    base.TOPIC_RE.pattern
    + r"|vehicular semantic (?:communication|communications|transmission|network)"
    + r"|semantic[- ]aware vehicular"
    + r"|(?:image|video|feature) (?:transmission|communication) (?:over|for|in) (?:wireless|vehicular|v2x)"
    + r"|collaborative inference (?:over|in) (?:wireless|vehicular|v2x)",
    re.I,
)


if __name__ == "__main__":
    base.main()
