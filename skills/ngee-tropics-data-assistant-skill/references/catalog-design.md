# NGEE Tropics Catalog — Why & What

A short note on how the dataset catalog is built and why it works the way it does.
Read this if you're wondering where the data comes from or how to refresh it.

## The idea in one line

`assets/ngee_tropics_datasets.csv` **is** the catalog and the cache. Searches read it
directly (0 API calls). The network is only touched to keep it up to date, and even
then only for datasets that actually changed.

## How the ESS-DIVE API shaped this

The catalog comes from one API: `https://api.ess-dive.lbl.gov/packages`.

Two quirks drove the design:

1. **Search is fuzzy.** Filtering `providerName="Next-Generation Ecosystem
   Experiments (NGEE) Tropics"` returns **447** datasets — it matches NGEE *Arctic*
   **and** Tropics. We narrow to the real **143** by keeping only those whose
   `citation` contains `"(NGEE) Tropics"` (confirmed against the Tropics org UUID
   `a441fe85-…` in the full metadata).

2. **Search results are lightweight.** The list endpoint returns only **7 fields**
   per dataset (name, description, datePublished, …). The fields that matter —
   `distribution` (download URLs), `keywords`, `creator`, `variableMeasured`,
   `spatialCoverage`, `provider`, … — only appear when you fetch each dataset
   individually via `GET /packages/{id}`.

So a full catalog needs 5 list calls + 1 call per dataset = ~148 calls. We pay that
**once**, store the result in the CSV, and never pay it again unless something
changes.

## How refresh stays cheap: incremental sync

`catalog.py sync` (also exposed as `build_catalog.py`) keeps the CSV current without
rebuilding it:

1. **Enumerate** the current frame (~5 calls) to see what's published now.
2. Match each dataset by its **stable DOI** (`@id`) and compare `dateModified`:
   - in the CSV and stored `dateModified` ≥ live `dateModified` → **reuse the row, 0 calls**
   - new, or live `dateModified` is newer → **enrich it (1 call)**
   - in the CSV but gone from the frame → **drop it**
3. Write the merged catalog back to the CSV.

**Why `dateModified`, not the versioned id.** The versioned `search_id` (e.g.
`ess-dive-ac295f…-20260107T093000551`) encodes the *upload* time and never changes
after that. But a dataset's metadata can be edited in place — `dateModified` advances
while the id stays the same (132 of 143 datasets already have a `dateModified` later
than their upload). Keying on the id alone would silently reuse those stale rows.
`dateModified` catches both cases: a new version bumps it, and so does an in-place
edit. No TTLs, no staleness heuristics — the modification timestamp tells us what
changed.

## Why the CSV is the single source of truth

Because the CSV already holds **every field for every dataset**, there's nothing to
enrich at search time — cheap and rich filters alike (`--name`, `--keywords`,
`--variable`, `--spatial`, `--creator`, dates) just read the file. That's why we
removed the earlier separate `.cache/` layer: it was a second copy of what the CSV
already is.

## Cost in practice

| What you do | API calls |
|---|---|
| Any search (name / keywords / variable / spatial / date) | **0** |
| Download one or two datasets | 1 per download |
| Refresh the catalog, nothing changed | ~5 (frame only) |
| Refresh, N datasets new or updated | ~5 + N |
| Full rebuild (`--rebuild`) | ~148 |

## Where things live

- `assets/ngee_tropics_datasets.csv` — the catalog. Read by every search.
- `scripts/catalog.py` — the module: `sync()` (incremental refresh), `load_dataframe()`
  (read the CSV), plus `build_frame()` / `enrich()`. CLI: `catalog.py sync [--rebuild]`,
  `catalog.py show`.
- `scripts/search_datasets.py` — reads the CSV and filters; `--sync` refreshes first.
- `scripts/download_dataset.py` — fetches one dataset's files on demand.
- `scripts/build_catalog.py` — thin wrapper over `catalog.py sync`.

## Config

- `ESSDIVE_API_TOKEN` — optional; higher rate limits and access to private datasets.
  Loaded from `.env` (project root or the skill dir).
