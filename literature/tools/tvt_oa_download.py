#!/usr/bin/env python3
"""Download legal open versions for the screened TVT corpus."""

from pathlib import Path

import iotj_oa_download as shared


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-tvt-semantic-communications-2023-present"

shared.SURVEY = SURVEY
shared.NOTES = SURVEY / "notes"
shared.PAPERS = SURVEY / "papers"


if __name__ == "__main__":
    shared.main()
