#!/usr/bin/env python3
"""
create_baseline_sample.py

Reproducible stratified sampling script for Fakeddit baseline dataset.
Filters usable multimodal samples (hasImage=True, valid image_url, valid clean_title),
preserves train/validation/test split structure, and stratifies on 6_way_label.
"""

import os
import json
import pandas as pd
import numpy as np

# Configuration
DATA_DIR = "data/Fakeddit datasetv2.0/all_samples (also includes non multimodal)"
OUTPUT_MANIFEST = "data/baseline_sample_manifest.csv"
OUTPUT_REPORT = "results/sampling_report.json"
RANDOM_SEED = 42

# Target sample sizes per split (approx 80k total)
TARGET_COUNTS = {
    "train": 66000,
    "validate": 7000,
    "test": 7000
}

SPLIT_FILES = {
    "train": os.path.join(DATA_DIR, "all_train.tsv"),
    "validate": os.path.join(DATA_DIR, "all_validate.tsv"),
    "test": os.path.join(DATA_DIR, "all_test_public.tsv")
}

def load_and_filter_split(split_name, filepath):
    print(f"Loading {split_name} from {filepath}...")
    df = pd.read_csv(filepath, sep="\t")
    total_raw = len(df)
    
    # 1. Filter hasImage == True (can be True, 1, 'True', 1.0)
    has_image_mask = df["hasImage"].astype(str).str.upper().isin(["TRUE", "1", "1.0"])
    
    # 2. Filter image_url non-null & non-empty
    valid_url_mask = df["image_url"].notna() & (df["image_url"].astype(str).str.strip() != "") & (df["image_url"].astype(str).str.lower() != "nan")
    
    # Multimodal subset before clean_title check
    df_multimodal = df[has_image_mask & valid_url_mask].copy()
    total_multimodal_raw = len(df_multimodal)
    
    # 3. Handle missing clean_title
    missing_title_mask = df_multimodal["clean_title"].isna() | (df_multimodal["clean_title"].astype(str).str.strip() == "") | (df_multimodal["clean_title"].astype(str).str.lower() == "nan")
    missing_title_count = int(missing_title_mask.sum())
    
    df_usable = df_multimodal[~missing_title_mask].copy()
    df_usable["split"] = split_name
    
    filter_stats = {
        "total_raw": total_raw,
        "total_multimodal_raw": total_multimodal_raw,
        "missing_clean_title_count": missing_title_count,
        "usable_multimodal_count": len(df_usable)
    }
    
    return df_usable, filter_stats

def perform_stratified_sampling(df, target_n, seed):
    if len(df) <= target_n:
        return df.copy()
    
    # Group by 6_way_label and sample proportionally
    sampled_dfs = []
    grouped = df.groupby("6_way_label", group_keys=False)
    
    for label, group in grouped:
        frac = len(group) / len(df)
        group_target = int(round(frac * target_n))
        # Ensure at least 1 sample if group target rounded to 0
        group_target = max(1, min(group_target, len(group)))
        
        sample_g = group.sample(n=group_target, random_state=seed)
        sampled_dfs.append(sample_g)
        
    df_sampled = pd.concat(sampled_dfs, ignore_index=True)
    
    # Adjust if rounding caused slight mismatch with target_n
    if len(df_sampled) > target_n:
        df_sampled = df_sampled.sample(n=target_n, random_state=seed).reset_index(drop=True)
    elif len(df_sampled) < target_n:
        remaining = df[~df["id"].isin(df_sampled["id"])]
        extra_needed = target_n - len(df_sampled)
        if len(remaining) >= extra_needed:
            extra = remaining.sample(n=extra_needed, random_state=seed)
            df_sampled = pd.concat([df_sampled, extra], ignore_index=True)
            
    return df_sampled

def get_label_distributions(df):
    dist = {}
    for col in ["2_way_label", "3_way_label", "6_way_label"]:
        if col in df.columns:
            vc = df[col].value_counts().to_dict()
            # Convert keys to int/str for JSON serializability
            dist[col] = {str(k): int(v) for k, v in sorted(vc.items())}
    return dist

def main():
    np.random.seed(RANDOM_SEED)
    
    all_usable = []
    all_sampled = []
    stats = {}
    
    for split_name, filepath in SPLIT_FILES.items():
        df_usable, filter_stats = load_and_filter_split(split_name, filepath)
        
        target_n = TARGET_COUNTS[split_name]
        df_sampled = perform_stratified_sampling(df_usable, target_n, RANDOM_SEED)
        
        all_usable.append(df_usable)
        all_sampled.append(df_sampled)
        
        stats[split_name] = {
            "filtering": filter_stats,
            "sampled_count": len(df_sampled),
            "before_sampling_distributions": get_label_distributions(df_usable),
            "after_sampling_distributions": get_label_distributions(df_sampled)
        }
        
    full_usable_df = pd.concat(all_usable, ignore_index=True)
    full_sampled_df = pd.concat(all_sampled, ignore_index=True)
    
    # Standard columns for manifest
    manifest_cols = [
        "id", "split", "clean_title", "2_way_label", "3_way_label", "6_way_label", "image_url", "hasImage"
    ]
    manifest_df = full_sampled_df[manifest_cols].copy()
    
    # Save manifest
    os.makedirs(os.path.dirname(OUTPUT_MANIFEST), exist_ok=True)
    manifest_df.to_csv(OUTPUT_MANIFEST, index=False)
    print(f"Manifest saved to {OUTPUT_MANIFEST} with {len(manifest_df)} rows.")
    
    # Overall summary stats
    total_sampled = len(full_sampled_df)
    total_usable = len(full_usable_df)
    
    # Storage estimate (~40KB per image reference estimate)
    est_bytes = total_sampled * 40 * 1024
    est_gb = est_bytes / (1024 ** 3)
    
    overall_summary = {
        "total_usable_multimodal_samples": total_usable,
        "total_sampled_multimodal_samples": total_sampled,
        "sample_split_counts": {s: len(d) for s, d in zip(SPLIT_FILES.keys(), all_sampled)},
        "overall_before_sampling_distributions": get_label_distributions(full_usable_df),
        "overall_after_sampling_distributions": get_label_distributions(full_sampled_df),
        "estimated_image_storage_gb": round(est_gb, 3),
        "estimated_bytes_per_image": 40960,
        "random_seed": RANDOM_SEED
    }
    
    report_data = {
        "overall": overall_summary,
        "splits": stats
    }
    
    os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)
    with open(OUTPUT_REPORT, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"Sampling report saved to {OUTPUT_REPORT}.")
    
    print("\n--- SAMPLING SUMMARY ---")
    print(f"Total Usable Multimodal Samples: {total_usable}")
    print(f"Total Sampled Baseline Size: {total_sampled}")
    print(f"  - Train: {len(all_sampled[0])}")
    print(f"  - Validation: {len(all_sampled[1])}")
    print(f"  - Test: {len(all_sampled[2])}")
    print(f"Estimated Image Storage: ~{round(est_gb, 2)} GB (based on 40KB/image reference estimate)")

if __name__ == "__main__":
    main()
