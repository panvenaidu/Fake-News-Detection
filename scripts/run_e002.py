#!/usr/bin/env python3
"""Run canonical CUDA E002 training for one or all BP-6W-v1 seeds.

This command exits before training when CUDA is unavailable.  Use the separate
smoke-test script for the approved local implementation verification.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fakenews_baselines.e002_text import load_json_config, train_one_seed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run canonical BP-6W-v1 E002 training.")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "e002_text_bp6w_v1.json",
        help="Path to the frozen E002 JSON configuration.",
    )
    seed_group = parser.add_mutually_exclusive_group(required=True)
    seed_group.add_argument("--seed", type=int, help="One approved seed: 42, 43 or 44.")
    seed_group.add_argument("--all-seeds", action="store_true", help="Run seeds 42, 43 and 44.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json_config(args.config)
    config["_config_path"] = str(args.config.relative_to(PROJECT_ROOT))
    seeds = config["training"]["seeds"] if args.all_seeds else [args.seed]
    invalid_seeds = set(seeds).difference(config["training"]["seeds"])
    if invalid_seeds:
        raise ValueError(f"Only approved BP-6W-v1 seeds are allowed: {sorted(invalid_seeds)}")
    summaries = [train_one_seed(config, PROJECT_ROOT, seed) for seed in seeds]
    output: dict = {"seed_summaries": summaries}
    if args.all_seeds:
        metrics = ("macro_f1", "accuracy", "balanced_accuracy", "weighted_f1")
        output["three_seed_test_summary"] = {
            metric: {
                "mean": statistics.mean(
                    summary["test_metrics"][metric] for summary in summaries
                ),
                "sample_standard_deviation": statistics.stdev(
                    summary["test_metrics"][metric] for summary in summaries
                ),
            }
            for metric in metrics
        }
        summary_path = (
            PROJECT_ROOT
            / config["artifacts"]["output_root"]
            / "E002-bert-base-uncased-6way-BP6Wv1-three-seed-summary.json"
        )
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(output, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
