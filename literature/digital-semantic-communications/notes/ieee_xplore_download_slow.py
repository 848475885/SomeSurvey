#!/usr/bin/env python3
"""Run the IEEE Xplore download skill with a longer DevTools socket timeout."""

from __future__ import annotations

import importlib.util
import itertools
import pathlib
import sys

SCRIPT = pathlib.Path(r"C:\Users\Qihao\.codex\skills\ieee-xplore-literature\scripts\ieee_xplore_download.py")

spec = importlib.util.spec_from_file_location("ieee_xplore_download", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {SCRIPT}")

ieee = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ieee)


class SlowCdpTab:
    def __init__(self, ws_url: str) -> None:
        self.ws = ieee.websocket.create_connection(ws_url, timeout=180, suppress_origin=True)
        self.ids = itertools.count(1)
        self.call("Runtime.enable")
        self.call("Page.enable")

    close = ieee.CdpTab.close
    call = ieee.CdpTab.call
    evaluate = ieee.CdpTab.evaluate
    navigate = ieee.CdpTab.navigate


ieee.CdpTab = SlowCdpTab
sys.exit(ieee.main())
