#!/usr/bin/env python3
"""
download_images.py

Reliable, resumable, concurrent image downloader for Fakeddit baseline dataset.
- Only downloads images from an approved manifest CSV.
- Uses thread-local requests.Session for HTTP keep-alive and connection pooling.
- Validates downloaded images with PIL to detect corrupt/incomplete files.
- Resumes seamlessly by skipping existing valid images.
- Produces a comprehensive download report and failure log.
- Generates a clean verified paired-data manifest while preserving the original manifest.
"""

import os
import sys
import time
import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image

# Default configuration
DEFAULT_MANIFEST = "data/baseline_sample_manifest.csv"
DEFAULT_OUTPUT_DIR = "images"
DEFAULT_REPORT = "results/download_final_report.json"
DEFAULT_FAILURES = "results/download_failures.json"
DEFAULT_VERIFIED_MANIFEST = "data/verified_paired_manifest.csv"
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

# Thread-local storage for requests.Session
_thread_local = threading.local()

def get_session():
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        session.headers.update(HEADERS)
        retry_strategy = Retry(
            total=DEFAULT_RETRIES,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _thread_local.session = session
    return _thread_local.session

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

def download_single_image(row, output_dir, timeout=10):
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
            "error": "URL missing or invalid"
        }
        
    session = get_session()
    try:
        resp = session.get(url, timeout=timeout, stream=True)
        if resp.status_code == 200:
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
            
            # Verify image format and integrity
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
        else:
            return {
                "id": item_id,
                "split": split,
                "status": f"http_{resp.status_code}",
                "file_size": 0,
                "url": url,
                "error": f"HTTP {resp.status_code}"
            }
    except requests.exceptions.Timeout:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return {
            "id": item_id,
            "split": split,
            "status": "timeout",
            "file_size": 0,
            "url": url,
            "error": "Request timed out"
        }
    except requests.exceptions.RequestException as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return {
            "id": item_id,
            "split": split,
            "status": "request_exception",
            "file_size": 0,
            "url": url,
            "error": str(e)
        }
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return {
            "id": item_id,
            "split": split,
            "status": "unexpected_error",
            "file_size": 0,
            "url": url,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Download images for Fakeddit baseline manifest.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path to manifest CSV")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to save images")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Path to save final report JSON")
    parser.add_argument("--failures", default=DEFAULT_FAILURES, help="Path to save failures JSON")
    parser.add_argument("--verified-manifest", default=DEFAULT_VERIFIED_MANIFEST, help="Path for verified paired manifest")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of images to download")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Number of download threads")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout (seconds)")
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
    os.makedirs(os.path.dirname(args.failures), exist_ok=True)
    os.makedirs(os.path.dirname(args.verified_manifest), exist_ok=True)

    rows = df.to_dict(orient="records")
    results = []
    
    start_time = time.time()
    print(f"Starting download of {len(rows)} images with {args.workers} workers...")
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(download_single_image, row, args.output_dir, args.timeout): row
            for row in rows
        }
        
        completed_count = 0
        total_rows = len(rows)
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed_count += 1
            if completed_count % 1000 == 0 or completed_count == total_rows or (total_rows <= 1000 and completed_count % 50 == 0):
                pct = (completed_count / total_rows) * 100
                rate = completed_count / (time.time() - start_time)
                print(f"Progress: {completed_count}/{total_rows} ({pct:.1f}%) | {rate:.1f} images/s")

    elapsed = time.time() - start_time
    
    # Categorize results
    status_counts = {}
    valid_ids = set()
    valid_sizes = []
    failed_records = []
    already_existing_count = 0
    newly_downloaded_count = 0
    corrupt_count = 0
    
    for r in results:
        st = r["status"]
        status_counts[st] = status_counts.get(st, 0) + 1
        
        if st == "already_exists":
            already_existing_count += 1
            valid_ids.add(r["id"])
            valid_sizes.append(r["file_size"])
        elif st == "success":
            newly_downloaded_count += 1
            valid_ids.add(r["id"])
            valid_sizes.append(r["file_size"])
        elif st == "corrupt_image":
            corrupt_count += 1
            failed_records.append(r)
        else:
            failed_records.append(r)
            
    total_successful = len(valid_ids)
    total_attempted = len(rows)
    total_failed = len(failed_records)
    
    success_pct = (total_successful / total_attempted * 100) if total_attempted > 0 else 0
    failure_pct = (total_failed / total_attempted * 100) if total_attempted > 0 else 0
    
    actual_storage_bytes = sum(valid_sizes)
    actual_storage_mb = actual_storage_bytes / (1024 * 1024)
    actual_storage_gb = actual_storage_bytes / (1024 ** 3)
    avg_size_bytes = (actual_storage_bytes / total_successful) if total_successful > 0 else 0
    avg_size_kb = avg_size_bytes / 1024
    
    # Save full failures log
    with open(args.failures, "w") as f:
        json.dump(failed_records, f, indent=2)
    print(f"Full failure log saved to: {args.failures} ({len(failed_records)} entries)")
    
    # Generate clean paired-data manifest (only samples with verified images)
    verified_df = df[df["id"].astype(str).isin(valid_ids)].copy()
    verified_df["image_path"] = verified_df["id"].apply(lambda x: os.path.join(args.output_dir, f"{x}.jpg"))
    verified_df.to_csv(args.verified_manifest, index=False)
    print(f"Clean paired manifest saved to: {args.verified_manifest} ({len(verified_df)} rows)")
    
    # Generate final report
    report_data = {
        "manifest_path": args.manifest,
        "total_attempted": total_attempted,
        "successful": total_successful,
        "newly_downloaded": newly_downloaded_count,
        "already_existing": already_existing_count,
        "failed": total_failed,
        "corrupt_unreadable": corrupt_count,
        "success_percentage": round(success_pct, 2),
        "failure_percentage": round(failure_pct, 2),
        "status_breakdown": status_counts,
        "actual_storage_bytes": actual_storage_bytes,
        "actual_storage_mb": round(actual_storage_mb, 2),
        "actual_storage_gb": round(actual_storage_gb, 4),
        "average_image_size_kb": round(avg_size_kb, 2),
        "elapsed_seconds": round(elapsed, 2),
        "verified_manifest_path": args.verified_manifest,
        "verified_manifest_rows": len(verified_df),
        "failures_path": args.failures
    }
    
    with open(args.report, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"Final download report saved to: {args.report}")
    
    print("\n" + "="*60)
    print("IMAGE DOWNLOAD PIPELINE FINAL SUMMARY")
    print("="*60)
    print(f"Total Attempted:       {total_attempted:,}")
    print(f"Total Successful:      {total_successful:,} ({success_pct:.2f}%)")
    print(f"  - Newly Downloaded:  {newly_downloaded_count:,}")
    print(f"  - Already Existing:  {already_existing_count:,}")
    print(f"Total Failed:          {total_failed:,} ({failure_pct:.2f}%)")
    print(f"Corrupt / Unreadable:  {corrupt_count:,}")
    print(f"Actual Storage Used:   {actual_storage_gb:.3f} GB ({actual_storage_mb:.1f} MB)")
    print(f"Average Image Size:    {avg_size_kb:.2f} KB/image")
    print(f"Elapsed Time:          {elapsed:.1f} seconds")
    print(f"Clean Paired Manifest: {args.verified_manifest} ({len(verified_df):,} verified samples)")
    print("="*60)

if __name__ == "__main__":
    main()
