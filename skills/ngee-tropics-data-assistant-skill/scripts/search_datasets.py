#!/usr/bin/env python3
"""
NGEE Tropics Dataset Search Tool

Searches the local, fully-enriched catalog CSV (assets/ngee_tropics_datasets.csv).
Every search — by name, keywords, creator, variable, spatial, or date — reads the
CSV directly with ZERO API calls, because the CSV already holds all fields.

Use --sync to refresh the CSV from ESS-DIVE first (incremental: ~5 calls + 1 per
new/updated dataset). See catalog.py for the sync mechanism.

Usage:
    python search_datasets.py --name "soil carbon"
    python search_datasets.py --keywords "LAI"
    python search_datasets.py --variable "water table"
    python search_datasets.py --spatial "Brazil"
    python search_datasets.py --creator "Smith"
    python search_datasets.py --start-date 2018-01-01 --end-date 2022-12-31
    python search_datasets.py --sync --name "soil"   # refresh first, then search
    python search_datasets.py --list-columns
    python search_datasets.py                          # list all datasets
"""

import argparse
import sys

try:
    import pandas as pd  # noqa: F401  (used via catalog.load_dataframe)
except ImportError:
    print("pandas required: pip install pandas")
    sys.exit(1)

import catalog


def search(df, name=None, description=None, keywords=None, creator=None,
           variable=None, spatial=None, start_date=None, end_date=None):
    """Apply substring/date filters and return matching rows."""
    if name:
        df = df[df["name"].str.contains(name, case=False, na=False)]
    if description:
        df = df[df["description"].str.contains(description, case=False, na=False)]
    if keywords:
        df = df[df["keywords"].str.contains(keywords, case=False, na=False)]
    if creator:
        df = df[df["creator"].str.contains(creator, case=False, na=False)]
    if variable:
        df = df[df["variableMeasured"].str.contains(variable, case=False, na=False)]
    if spatial:
        df = df[df["spatialCoverage"].str.contains(spatial, case=False, na=False)]
    if start_date:
        df = df[df["datePublished"] >= start_date]
    if end_date:
        df = df[df["datePublished"] <= end_date]
    return df


def print_results(df, verbose=False):
    if df.empty:
        print("No datasets found matching the criteria.")
        return
    print(f"Found {len(df)} dataset(s):\n")
    for _, row in df.iterrows():
        print(f"Name:      {row.get('name', 'N/A')}")
        print(f"ID:        {row.get('@id', 'N/A')}")
        print(f"Published: {row.get('datePublished', 'N/A')}")
        print(f"URL:       {row.get('search_viewUrl', 'N/A')}")
        if verbose:
            print(f"Keywords:  {row.get('keywords', 'N/A')}")
            print(f"Spatial:   {row.get('spatialCoverage', 'N/A')}")
            print(f"Temporal:  {row.get('temporalCoverage', 'N/A')}")
            desc = str(row.get("description", ""))
            print(f"Desc:      {desc[:200]}{'...' if len(desc) > 200 else ''}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Search NGEE Tropics dataset catalog")
    parser.add_argument("--name", help="Filter by dataset name (substring)")
    parser.add_argument("--description", help="Filter by description text")
    parser.add_argument("--keywords", help="Filter by keywords")
    parser.add_argument("--creator", help="Filter by creator name")
    parser.add_argument("--variable", help="Filter by variable measured")
    parser.add_argument("--spatial", help="Filter by spatial coverage (e.g., 'Brazil')")
    parser.add_argument("--start-date", help="Published on/after this date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Published on/before this date (YYYY-MM-DD)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show more detail")
    parser.add_argument("--sync", action="store_true", help="Refresh the CSV from ESS-DIVE first")
    parser.add_argument("--list-columns", action="store_true", help="List available columns")
    args = parser.parse_args()

    if args.sync:
        catalog.sync(log=lambda m: print(m, file=sys.stderr))

    try:
        df = catalog.load_dataframe()
    except FileNotFoundError:
        print("No catalog CSV found. Run: python catalog.py sync", file=sys.stderr)
        sys.exit(1)

    if args.list_columns:
        print("Available columns:")
        for col in df.columns:
            print(f"  {col}")
        return

    results = search(
        df,
        name=args.name,
        description=args.description,
        keywords=args.keywords,
        creator=args.creator,
        variable=args.variable,
        spatial=args.spatial,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print_results(results, verbose=args.verbose)


if __name__ == "__main__":
    main()
