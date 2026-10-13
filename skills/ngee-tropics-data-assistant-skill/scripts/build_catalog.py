#!/usr/bin/env python3
"""Build/refresh assets/ngee_tropics_datasets.csv (thin wrapper over catalog.sync).

The assets CSV is the single source of truth; this incrementally enriches only the
datasets that are new or newly-versioned, reusing every unchanged row.

  .venv/bin/python build_catalog.py              # incremental in-place update
  .venv/bin/python build_catalog.py --rebuild    # enrich everything from scratch
  .venv/bin/python build_catalog.py --out X       # write elsewhere (e.g. to test)

See catalog.py for the sync logic and the design rationale in
references/catalog-design.md.
"""
import argparse

import catalog


def main():
    ap = argparse.ArgumentParser(description="Incrementally sync the NGEE Tropics catalog CSV")
    ap.add_argument("--baseline", default=str(catalog.DEFAULT_CSV), help="Existing CSV to reuse")
    ap.add_argument("--out", default=str(catalog.DEFAULT_CSV), help="Where to write the merged CSV")
    ap.add_argument("--rebuild", action="store_true", help="Ignore baseline; enrich everything")
    args = ap.parse_args()
    catalog.sync(args.baseline, args.out, rebuild=args.rebuild)


if __name__ == "__main__":
    main()
