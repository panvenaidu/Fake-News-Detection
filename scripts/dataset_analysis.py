import pandas as pd
import os
import json

data_dir = "data/Fakeddit datasetv2.0/all_samples (also includes non multimodal)"
files = {
    "train": "all_train.tsv",
    "validate": "all_validate.tsv",
    "test": "all_test_public.tsv"
}

results = {}
total_multimodal = 0

for split, filename in files.items():
    filepath = os.path.join(data_dir, filename)
    print(f"Analyzing {split} ({filename})...")
    
    # Read TSV
    df = pd.read_csv(filepath, sep="\t")
    
    # Row counts
    row_count = len(df)
    
    # Missing values
    missing_values = df.isnull().sum().to_dict()
    
    # has_image count
    # convert has_image to boolean
    if 'hasImage' in df.columns:
        has_image_col = 'hasImage'
    elif 'has_image' in df.columns:
        has_image_col = 'has_image'
    else:
        has_image_col = None

    if has_image_col:
        # Fakeddit might use True/False strings or 1/0
        if df[has_image_col].dtype == object:
            has_image_mask = df[has_image_col].astype(str).str.lower() == 'true'
        else:
            has_image_mask = df[has_image_col].astype(bool)
        has_image_count = has_image_mask.sum()
    else:
        has_image_count = 0
        has_image_mask = pd.Series([False]*len(df))
        
    # usable multimodal samples
    if has_image_col and 'image_url' in df.columns:
        multimodal_df = df[has_image_mask & df['image_url'].notna() & (df['image_url'] != "")]
        usable_multimodal_count = len(multimodal_df)
    else:
        usable_multimodal_count = 0
        multimodal_df = pd.DataFrame()
        
    total_multimodal += usable_multimodal_count
        
    # Label distributions on multimodal subset
    distributions = {}
    if usable_multimodal_count > 0:
        for label_col in ['2_way_label', '3_way_label', '6_way_label']:
            if label_col in multimodal_df.columns:
                dist = multimodal_df[label_col].value_counts().to_dict()
                distributions[label_col] = dist
                
    # Duplicates
    if 'id' in df.columns:
        duplicate_ids = df.duplicated(subset=['id']).sum()
    else:
        duplicate_ids = 0

    results[split] = {
        "row_count": row_count,
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "missing_values": missing_values,
        "has_image_count": int(has_image_count),
        "usable_multimodal_count": int(usable_multimodal_count),
        "duplicate_ids": int(duplicate_ids),
        "multimodal_distributions": distributions
    }

print("\n=== DATASET ANALYSIS REPORT ===\n")
for split, data in results.items():
    print(f"--- {split.upper()} ---")
    print(f"Row count: {data['row_count']}")
    print(f"has_image count: {data['has_image_count']}")
    print(f"Usable multimodal count: {data['usable_multimodal_count']}")
    print(f"Duplicate IDs: {data['duplicate_ids']}")
    
    print("\nColumns and Missing Values:")
    for col in data['columns']:
        print(f"  - {col} ({data['dtypes'][col]}): {data['missing_values'][col]} missing")
        
    print("\nMultimodal Label Distributions:")
    for label, dist in data['multimodal_distributions'].items():
        print(f"  {label}: {dist}")
    print("\n")

print(f"Total usable multimodal samples across all splits: {total_multimodal}")
avg_image_size_kb = 40  # Estimate
estimated_storage_gb = (total_multimodal * avg_image_size_kb) / (1024 * 1024)
print(f"Estimated image storage (at {avg_image_size_kb}KB/img): {estimated_storage_gb:.2f} GB")

with open("results/dataset_analysis.json", "w") as f:
    json.dump(results, f, indent=2)
