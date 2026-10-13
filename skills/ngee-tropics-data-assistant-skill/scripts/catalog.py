#!/usr/bin/env python3
"""NGEE Tropics catalog: the assets CSV is the single source of truth.

`assets/ngee_tropics_datasets.csv` holds fully-enriched rows (all schema.org fields)
keyed by the versioned `search_id`. Because it is already complete, ANY search reads
it directly with zero API calls. The network is only touched to keep it current:

  sync() -- incremental refresh:
    1. ENUMERATE the current NGEE Tropics frame (~5 calls) -> versioned ids.
    2. Keyed by `search_id`:
         - already in the CSV       -> REUSE the row (0 calls)
         - new / newly-versioned    -> ENRICH it (1 call)   [ESS-DIVE bumps the id's
           timestamp on every revision, so updates re-enrich automatically]
    3. Rows in the CSV but no longer in the frame are DROPPED (removed upstream).
    4. Write the merged catalog back to the CSV.

  Steady state: ~5 calls + 1 per genuinely new/updated dataset. No separate cache.

Env:
    ESSDIVE_API_TOKEN   optional Bearer token (higher limits, private datasets)

CLI:
    python catalog.py sync              # incremental refresh of the assets CSV
    python catalog.py sync --rebuild    # ignore existing rows, enrich everything
    python catalog.py show              # print a summary of the current CSV
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

import httpx

BASE_URL = "https://api.ess-dive.lbl.gov"
PROVIDER = "Next-Generation Ecosystem Experiments (NGEE) Tropics"
PROVIDER_UUID = "a441fe85-5ac3-41b1-bbe5-46df92682609"
CITATION_MARKER = "(NGEE) Tropics"
PAGE_SIZE = 100

SKILL_DIR = Path(__file__).parent.parent
DEFAULT_CSV = SKILL_DIR / "assets" / "ngee_tropics_datasets.csv"

# Scalar envelope fields stored with a search_ prefix.
SEARCH_SCALARS = [
    "citation", "dateModified", "dateUploaded", "id",
    "isPublic", "next", "previous", "url", "viewUrl",
]

# Column order for the CSV (matches the original snapshot).
COLUMNS = [
    "@context", "@id", "@type", "alternateName", "archivedAt", "award",
    "citation", "contributor", "creator", "datePublished", "description",
    "distribution", "editor", "funder", "hasPart", "keywords", "license",
    "measurementTechnique", "name", "provider", "search_citation",
    "search_dataset_summary", "search_dateModified", "search_dateUploaded",
    "search_id", "search_isPublic", "search_next", "search_previous",
    "search_url", "search_viewUrl", "spatialCoverage", "temporalCoverage",
    "variableMeasured",
]


# --------------------------------------------------------------------------- env

def load_env():
    """Populate ESSDIVE_API_TOKEN from .env, matching download_dataset.py order."""
    if os.getenv("ESSDIVE_API_TOKEN"):
        return
    for env_file in (Path.cwd() / ".env", SKILL_DIR / ".env",
                     SKILL_DIR.parent / ".env", SKILL_DIR.parent.parent / ".env"):
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


def _headers():
    token = os.getenv("ESSDIVE_API_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _flatten(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


# --------------------------------------------------------------------- API calls

def build_frame(client):
    """Enumerate (~5 calls) and keep the NGEE Tropics envelopes by citation.

    Returns {versioned_id: frame_row}; each row has the search_ scalars, a
    search_dataset_summary, and the lightweight JSON-LD fields available for free.
    """
    envelopes, row_start = [], 1
    while True:
        resp = client.get(
            f"{BASE_URL}/packages",
            params={"isPublic": "true", "providerName": PROVIDER,
                    "rowStart": row_start, "pageSize": PAGE_SIZE},
            headers=_headers(), timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("result", [])
        if not results:
            break
        envelopes += results
        row_start += PAGE_SIZE
        if row_start > data.get("total", 0):
            break

    rows = {}
    for env in envelopes:
        if CITATION_MARKER not in (env.get("citation") or ""):
            continue
        light = env.get("dataset") or {}
        row = {f"search_{k}": _flatten(env.get(k)) for k in SEARCH_SCALARS}
        row["search_dataset_summary"] = light.get("description")
        for k in ("@context", "@id", "@type", "name", "description", "datePublished"):
            row[k] = _flatten(light.get(k))
        rows[env["id"]] = row
    return rows


def enrich(identifier, client):
    """Fetch the full schema.org JSON-LD dataset for one id."""
    resp = client.get(f"{BASE_URL}/packages/{identifier}", headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json().get("dataset", {})


# -------------------------------------------------------------------------- CSV

def load_baseline(path=DEFAULT_CSV):
    """Return {search_id: row_dict} from the CSV, or {} if absent."""
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return {row["search_id"]: row for row in csv.DictReader(f)}
    except FileNotFoundError:
        return {}


def load_dataframe(path=DEFAULT_CSV):
    """Read the catalog CSV into a pandas DataFrame (0 API calls)."""
    import pandas as pd
    return pd.read_csv(path)


def _full_row(frame_row, full_dataset):
    """Merge a frame row with flattened full JSON-LD (full fields win)."""
    row = dict(frame_row)
    for k, v in full_dataset.items():
        row[k] = _flatten(v)
    return row


def sync(baseline_path=DEFAULT_CSV, out_path=DEFAULT_CSV, rebuild=False, log=print):
    """Incrementally refresh the catalog CSV. Returns (reused, enriched, dropped).

    Change detection is by `dateModified`, matched on the stable DOI (`@id`):
    a row is reused only if we already have it AND its stored dateModified is at
    least as recent as the live one. This catches both new versions (the versioned
    id changes) and in-place metadata edits (only dateModified moves).
    """
    baseline = {} if rebuild else load_baseline(baseline_path)
    baseline_by_doi = {r.get("@id"): r for r in baseline.values() if r.get("@id")}
    log(f"Baseline: {len(baseline)} datasets" if baseline else "Baseline: none (full rebuild)")

    load_env()
    with httpx.Client() as client:
        frame = build_frame(client)
        log(f"Frame: {len(frame)} NGEE Tropics datasets currently published")

        rows, reused, enriched = [], 0, 0
        for versioned_id, frame_row in frame.items():
            doi = frame_row.get("@id")
            live_mod = frame_row.get("search_dateModified")
            prev = baseline_by_doi.get(doi)
            prev_mod = prev.get("search_dateModified") if prev else None
            unchanged = prev is not None and prev_mod and live_mod and prev_mod >= live_mod
            if unchanged:
                rows.append(prev)
                reused += 1
            else:
                rows.append(_full_row(frame_row, enrich(versioned_id, client)))
                enriched += 1
                log(f"  + enriched {doi} (modified {live_mod})")

    current_dois = {fr.get("@id") for fr in frame.values()}
    dropped = sum(1 for d in baseline_by_doi if d not in current_dois)
    log(f"Reused {reused}, enriched {enriched} (new/updated), dropped {dropped} (removed upstream)")

    columns = list(COLUMNS)
    for r in rows:
        for k in r:
            if k not in columns:
                columns.append(k)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in columns})
    log(f"Wrote {len(rows)} datasets to {out_path}")
    return reused, enriched, dropped


# --------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description="NGEE Tropics catalog (assets CSV is the cache)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("sync", help="incrementally refresh the assets CSV")
    sp.add_argument("--rebuild", action="store_true", help="enrich everything, ignore existing rows")
    sp.add_argument("--baseline", default=str(DEFAULT_CSV))
    sp.add_argument("--out", default=str(DEFAULT_CSV))
    sub.add_parser("show", help="summarize the current CSV")
    args = ap.parse_args()

    if args.cmd == "sync":
        sync(args.baseline, args.out, rebuild=args.rebuild)
    elif args.cmd == "show":
        try:
            df = load_dataframe()
        except FileNotFoundError:
            print("No catalog CSV yet. Run: python catalog.py sync", file=sys.stderr)
            sys.exit(1)
        print(f"Catalog: {len(df)} datasets, {len(df.columns)} columns at {DEFAULT_CSV}")
        for _, row in df.head(5).iterrows():
            print(f"  - {row.get('@id')}  {str(row.get('name'))[:60]}")


if __name__ == "__main__":
    main()
