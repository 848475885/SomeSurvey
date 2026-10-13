#!/usr/bin/env python3
"""Run the project-approved slow IEEE downloader for the TVT corpus."""

from pathlib import Path

import iotj_ieee_download_remaining as shared


ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "literature" / "ieee-tvt-semantic-communications-2023-present"

shared.SURVEY = SURVEY
shared.NOTES = SURVEY / "notes"
shared.PAPERS = SURVEY / "papers"


if __name__ == "__main__":
    shared.main()
