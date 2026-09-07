#!/usr/bin/env python3
"""
download_images.py

Reliable, resumable, concurrent image downloader for Fakeddit baseline dataset.
Only downloads images from an approved manifest CSV.
Validates downloaded images with PIL to detect corrupt/incomplete files.
"""

import os
import sys
import time
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

import pandas as pd
import requests
from PIL import Image

# Default configuration
DEFAULT_MANIFEST = "data/baseline_sample_manifest.csv"
DEFAULT_OUTPUT_DIR = "images"
DEFAULT_REPORT = "results/download_test_100_report.json"
DEFAULT_WORKERS = 8
DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}

def verify_image(filepath):
    """Verify that the image file exists, is non-empty, and can be decoded by PIL."""
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return False
        with Image.open(filepath) as img:
            img.verify()
        return True
    except Exception:
        return False

def download_single_image(row, output_dir, timeout=10, retries=2):
    item_id = str(row["id"])
    url = str(row["image_url"])
    split = str(row.get("split", "unknown"))
    
    target_path = os.path.join(output_dir, f"{item_id}.jpg")
    tmp_path = os.path.join(output_dir, f"{item_id}.jpg.tmp")
    
    # Check if already downloaded and valid
    if os.path.exists(target_path):
        if verify_image(target_path):
            file_size = os.path.getsize(target_path)
            return {
                "id": item_id,
                "split": split,
                "status": "already_exists",
                "file_size": file_size,
                "url": url,
                "error": None
            }
        else:
            # Corrupted existing file, delete and redownload
            try:
                os.remove(target_path)
            except OSError:
                pass
    
    # URL check
    if not url or url.lower() == "nan" or not url.startswith("http"):
        return {
            "id": item_id,
            "split": split,
            "status": "invalid_url",
            "file_size": 0,
            "url": url,
            "error": "URL missing or not http"
        }
        
    last_error = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
            if resp.status_code == 200:
                # Write to tmp file
                with open(tmp_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify downloaded image
                if verify_image(tmp_path):
                    os.replace(tmp_path, target_path)
                    file_size = os.path.getsize(target_path)
                    return {
                        "id": item_id,
                        "split": split,
                        "status": "success",
                        "file_size": file_size,
                        "url": url,
                        "error": None
                    }
                else:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    return {
                        "id": item_id,
                        "split": split,
                        "status": "corrupt_image",
                        "file_size": 0,
                        "url": url,
                        "error": "File downloaded but invalid/unreadable by PIL"
                    }
            elif resp.status_code in [404, 410, 403]:
                # Unavailable URL / permanent error
                return {
                    "id": item_id,
                    "split": split,
                    "status": "unavailable_http_error",
                    "file_size": 0,
                    "url": url,
                    "error": f"HTTP {resp.status_code}"
                }
            else:
                last_error = f"HTTP {resp.status_code}"
                time.sleep(0.5)
        except (requests.RequestException, Exception) as e:
            last_error = str(e)
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            time.sleep(0.5)
            
    return {
        "id": item_id,
        "split": split,
        "status": "failed_network_error",
        "file_size": 0,
        "url": url,
        "error": last_error
    }

def main():
    parser = argparse.ArgumentParser(description="Download images for Fakeddit baseline manifest.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path to manifest CSV")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to save images")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Path to save download report JSON")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of images to download")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Number of download threads")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout (seconds)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Number of retries")
    args = parser.parse_args()

    if not os.path.exists(args.manifest):
        print(f"Error: Manifest file not found at {args.manifest}")
        sys.exit(1)

    df = pd.read_csv(args.manifest)
    total_manifest_rows = len(df)
    print(f"Loaded manifest '{args.manifest}' with {total_manifest_rows} total rows.")

    if args.limit is not None:
        df = df.iloc[:args.limit].copy()
        print(f"Limiting execution to first {len(df)} samples.")

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)

    rows = df.to_dict(orient="records")
    results = []
    
    start_time = time.time()
    print(f"Starting download of {len(rows)} images with {args.workers} workers...")
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(download_single_image, row, args.output_dir, args.timeout, args.retries): row
            for row in rows
        }
        
        completed_count = 0
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed_count += 1
            if completed_count % 20 == 0 or completed_count == len(rows):
                print(f"Progress: {completed_count}/{len(rows)} ({completed_count / len(rows) * 100:.1f}%)")

    elapsed = time.time() - start_time
    
    # Analyze results
    status_counts = {}
    valid_sizes = []
    failed_items = []
    
    for r in results:
        st = r["status"]
        status_counts[st] = status_counts.get(st, 0) + 1
        if st in ["success", "already_exists"]:
            valid_sizes.append(r["file_size"])
        else:
            failed_items.append(r)
            
    total_valid = len(valid_sizes)
    total_failed = len(failed_items)
    actual_storage_bytes = sum(valid_sizes)
    actual_storage_mb = actual_storage_bytes / (1024 * 1024)
    avg_size_bytes = (actual_storage_bytes / total_valid) if total_valid > 0 else 0
    avg_size_kb = avg_size_bytes / 1024
    
    # Extrapolate for full manifest (80,000 samples)
    est_total_80k_gb = (total_manifest_rows * avg_size_bytes) / (1024 ** 3) if avg_size_bytes > 0 else 0
    
    report_data = {
        "manifest_path": args.manifest,
        "manifest_total_rows": total_manifest_rows,
        "attempted_count": len(rows),
        "successful_downloads": total_valid,
        "failed_downloads": total_failed,
        "status_breakdown": status_counts,
        "actual_storage_bytes": actual_storage_bytes,
        "actual_storage_mb": round(actual_storage_mb, 3),
        "actual_storage_kb": round(actual_storage_bytes / 1024, 2),
        "average_image_size_bytes": round(avg_size_bytes, 1),
        "average_image_size_kb": round(avg_size_kb, 2),
        "estimated_80k_storage_gb": round(est_total_80k_gb, 3),
        "elapsed_seconds": round(elapsed, 2),
        "failed_samples": failed_items[:50]  # first 50 failures for inspection
    }
    
    with open(args.report, "w") as f:
        json.dump(report_data, f, indent=2)
        
    print("\n" + "="*50)
    print("DOWNLOAD TEST REPORT")
    print("="*50)
    print(f"Manifest Rows: {total_manifest_rows}")
    print(f"Attempted: {len(rows)}")
    print(f"Successful & Valid: {total_valid} ({total_valid / len(rows) * 100:.1f}%)")
    print(f"Failed: {total_failed} ({total_failed / len(rows) * 100:.1f}%)")
    print(f"Status Breakdown: {status_counts}")
    print(f"Actual Storage Used: {actual_storage_mb:.2f} MB ({actual_storage_bytes:,} bytes)")
    print(f"Actual Average Image Size: {avg_size_kb:.2f} KB/image")
    print(f"Estimated Storage for Full 80,000 Subset: {est_total_80k_gb:.3f} GB")
    print(f"Elapsed Time: {elapsed:.2f} seconds ({elapsed / len(rows):.2f} s/image)")
    print(f"Report saved to: {args.report}")
    print("="*50)

if __name__ == "__main__":
    main()
