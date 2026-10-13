#!/usr/bin/env python3
"""
NGEE Tropics Dataset Downloader

Download all files from an ESS-DIVE dataset given its DOI.
Requires ESSDIVE_API_TOKEN env var for authenticated access (optional but recommended).

Usage:
    python download_dataset.py --doi 10.15485/2530733
    python download_dataset.py --doi "doi:10.15485/2530733" --output ./my_data
    python download_dataset.py --doi 10.15485/2530733 --dry-run

Environment:
    ESSDIVE_API_TOKEN  - Optional Bearer token for ESS-DIVE API

.env file resolution order:
    1. OS environment
    2. <project-root>/.env
    3. <skill-dir>/.env
    4. <skill-dir>/../.env      (e.g. .claude/skills/.env or .agents/skills/.env)
    5. <skill-dir>/../../.env   (e.g. .claude/.env or .agents/.env)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

try:
    import httpx
except ImportError:
    print("httpx required: pip install httpx")
    sys.exit(1)

ESSDIVE_API_BASE = "https://api.ess-dive.lbl.gov"


def load_env():
    """Load .env token following skill env resolution order."""
    if os.getenv("ESSDIVE_API_TOKEN"):
        return

    skill_dir = Path(__file__).parent.parent
    # Walk up from cwd to find project root .env (handles any invocation path)
    cwd_env = Path.cwd() / ".env"
    env_candidates = [
        cwd_env,
        skill_dir / ".env",
        skill_dir.parent / ".env",
        skill_dir.parent.parent / ".env",
    ]
    for env_file in env_candidates:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
            break


def normalize_doi(doi: str) -> str:
    """Strip URL prefix, keep as bare DOI string."""
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi


def get_dataset_metadata(doi: str, token: str = None) -> dict:
    """Fetch dataset metadata from ESS-DIVE API."""
    api_doi = f"doi:{doi}"
    encoded = quote(api_doi, safe="")
    url = f"{ESSDIVE_API_BASE}/packages/{encoded}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def download_files(doi: str, output_dir: Path, dry_run: bool = False) -> dict:
    """Download all files for a dataset DOI to output_dir."""
    load_env()
    token = os.getenv("ESSDIVE_API_TOKEN", "").strip() or None
    bare_doi = normalize_doi(doi)

    print(f"Fetching metadata for doi:{bare_doi}...")
    data = get_dataset_metadata(bare_doi, token)

    dataset = data.get("dataset", {})
    dataset_id = data.get("id", f"doi:{bare_doi}")
    name = dataset.get("name", "unknown")
    distribution = dataset.get("distribution", [])

    print(f"Dataset: {name}")
    print(f"Files:   {len(distribution)}")

    if not distribution:
        return {"dataset_id": dataset_id, "name": name, "downloaded": [], "failed": []}

    if not dry_run:
        safe_id = re.sub(r"[^\w\-]", "_", dataset_id)
        out_path = output_dir / safe_id
        out_path.mkdir(parents=True, exist_ok=True)
    else:
        out_path = output_dir

    downloaded, failed = [], []
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        for f in distribution:
            fname = f.get("name", "unknown")
            url = f.get("contentUrl")
            if not url:
                failed.append({"file": fname, "error": "no contentUrl"})
                continue

            if dry_run:
                print(f"  [dry-run] {fname}  <-  {url}")
                downloaded.append({"file": fname, "url": url})
                continue

            try:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                dest = out_path / fname
                dest.write_bytes(resp.content)
                size = len(resp.content)
                print(f"  Downloaded: {fname} ({size:,} bytes)")
                downloaded.append({"file": fname, "path": str(dest), "size": size})
            except Exception as e:
                print(f"  FAILED: {fname} - {e}", file=sys.stderr)
                failed.append({"file": fname, "error": str(e)})

    return {
        "dataset_id": dataset_id,
        "name": name,
        "output_directory": str(out_path.resolve()) if not dry_run else None,
        "downloaded": downloaded,
        "failed": failed,
    }


def main():
    parser = argparse.ArgumentParser(description="Download ESS-DIVE dataset files")
    parser.add_argument("--doi", required=True, help="Dataset DOI (any format)")
    parser.add_argument("--output", default="./ngee_data", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="List files without downloading")
    args = parser.parse_args()

    result = download_files(args.doi, Path(args.output), dry_run=args.dry_run)

    print(f"\nSummary:")
    print(f"  Success: {len(result['downloaded'])}")
    print(f"  Failed:  {len(result['failed'])}")
    if result.get("output_directory"):
        print(f"  Saved to: {result['output_directory']}")

    if result["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
