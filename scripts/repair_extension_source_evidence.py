#!/usr/bin/env python3
"""Repair the Experiment 010 overlay source-evidence name collision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_existing_solver_extension import repair_frozen_source_evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("overlay", nargs="+", type=Path)
    args = parser.parse_args()
    for value in args.overlay:
        overlay = value if value.is_absolute() else ROOT / value
        state = json.loads((overlay / "run_state.json").read_text(encoding="utf-8"))
        source = Path(state["config"]["source_run_root"])
        repair_frozen_source_evidence(overlay, source)
        print(overlay)


if __name__ == "__main__":
    main()
