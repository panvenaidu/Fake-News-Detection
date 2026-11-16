#!/usr/bin/env python3
"""Execute the approved non-canonical E002 implementation smoke test."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fakenews_baselines.e002_text import load_json_config, run_smoke_test


def main() -> int:
    config_path = PROJECT_ROOT / "configs" / "e002_text_bp6w_v1.json"
    config = load_json_config(config_path)
    config["_config_path"] = str(config_path.relative_to(PROJECT_ROOT))
    summary = run_smoke_test(config, PROJECT_ROOT)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
