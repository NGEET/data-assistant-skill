---
name: ngee-tropics-data-assistant-skill
description: Explore, search, and download NGEE Tropics tropical ecosystem datasets from ESS-DIVE. Use when asked about NGEE data, tropical forest datasets, soil carbon, LAI, hydrology, or ESS-DIVE downloads.
---

# NGEE Tropics Data Exploration

Standalone skill for discovering and downloading NGEE Tropics datasets (~143 datasets from ESS-DIVE). Uses uv-managed virtualenv per session for isolation.

**`assets/ngee_tropics_datasets.csv` is the single source of truth** — a fully-enriched catalog keyed by the versioned `search_id`. All searches read it directly with **zero API calls** (all fields, cheap or rich).

The network is only touched to keep it current, via `catalog.py sync` (or `build_catalog.py`):
- **Enumerate** the current NGEE Tropics frame (~5 calls) to see what's published.
- **Reuse** unchanged rows (0 calls); **enrich** only new or newly-versioned datasets (1 call each); **drop** rows removed upstream. Updates are detected automatically because ESS-DIVE bumps the `search_id` timestamp on every revision.

Steady state to refresh: ~5 calls + 1 per change. See `references/catalog-design.md`.

## Pre-flight Checklist

Before doing anything else, run through these in order:

**1. Check environment variable:**
```bash
.venv/bin/python -c "import os; print('Token OK' if os.getenv('ESSDIVE_API_TOKEN') else 'WARNING: ESSDIVE_API_TOKEN not set')"
```
(Ensure `.venv` exists first — see Session Workflow below.)
If missing, warn the user:
> "ESSDIVE_API_TOKEN is not set. Proceeding without authentication (rate limits apply, private datasets unavailable). Set it in `.env` or `.claude/skills/ngee-tropics-data-assistant-skill/.env` and restart."

Do NOT proceed silently — always surface this warning before any downloads.

**2. Ask clarifying questions** before starting any work:
- What type of data? (soil carbon, LAI, water table, biomass, other)
- Geographic region? (Brazil/Manaus, Peru, Panama, all sites)
- Date range constraints?
- Goal: explore/list only, or download for analysis?
- If downloading: what analysis is planned?

Ask the two most important questions first (data type + goal), then follow up. Do not dump all questions at once.

**3. Create session folder** for all outputs (see Session Workflow below).

## Session Workflow

Every request creates a unique session folder. All generated files, downloaded data, and scripts go there. See `references/session-workflow.md` for full setup details.

**Folder naming**: `sessions/YYYYMMDD_HHMMSS_<slug>/`
- Slug = lowercase hyphenated summary of the question (max 50 chars)
- Example: `sessions/20260305_143022_soil-carbon-brazil-2020/`

## Quick Start (uv + session folder)

```bash
# 1. Create root virtualenv (once, shared across sessions)
uv venv .venv
uv pip install --python .venv/bin/python \
  -r .claude/skills/ngee-tropics-data-assistant-skill/scripts/requirements.txt

# 2. Set session path and create it
SESSION=sessions/YYYYMMDD_HHMMSS_your-slug
mkdir -p $SESSION/data

# 3. Search datasets (reads the assets CSV, 0 API calls; add --sync to refresh first)
.venv/bin/python .claude/skills/ngee-tropics-data-assistant-skill/scripts/search_datasets.py \
  --name "soil carbon" --verbose

# 4. Download a dataset (DOI from search results)
.venv/bin/python .claude/skills/ngee-tropics-data-assistant-skill/scripts/download_dataset.py \
  --doi 10.15485/2530733 --output $SESSION/data

# (optional) Refresh the catalog from ESS-DIVE — incremental, ~5 calls + 1 per change
.venv/bin/python .claude/skills/ngee-tropics-data-assistant-skill/scripts/catalog.py sync
```

## Workflow

1. **Pre-flight** — check env var, ask clarifying questions, create session folder
2. **Search** — `search_datasets.py` to find datasets by name/keywords/creator/variable/spatial/date. Reads the CSV directly, 0 API calls. Add `--sync` to refresh the CSV from ESS-DIVE first
3. **Inspect** — for custom filters, `import catalog` and use `catalog.load_dataframe()` to work with the catalog inline as a pandas DataFrame
4. **Download** — `download_dataset.py --doi <DOI> --output $SESSION/data` (fetches that dataset's distribution fresh, 1 call)
5. **Analyze** — save analysis scripts to `$SESSION/analyze.py`, run with `.venv/bin/python`
6. **Visualize** — save plots script to `$SESSION/visualize.py`, run with `MPLBACKEND=Agg .venv/bin/python`; figures go in `$SESSION/figures/`

## Resources

- `assets/ngee_tropics_datasets.csv` — **the catalog** (single source of truth): 143 fully-enriched datasets, keyed by versioned `search_id`. Read by every search
- `scripts/catalog.py` — catalog module: `sync` / `show` CLI + importable `sync()`, `load_dataframe()`, `build_frame()`, `enrich()`
- `scripts/search_datasets.py` — CLI search/filter tool (reads the CSV, 0 API calls; `--sync` to refresh first)
- `scripts/download_dataset.py` — ESS-DIVE file downloader (fetches one dataset's files)
- `scripts/build_catalog.py` — thin wrapper over `catalog.py sync`: incremental refresh (~5 calls + 1 per change; `--rebuild` forces a full ~148-call rebuild)
- `scripts/requirements.txt` — Python dependencies (pandas, httpx, python-dotenv, matplotlib, seaborn, numpy)
- `references/data-schema.md` — CSV column definitions and research domain notes
- `references/session-workflow.md` — session folder structure and uv virtualenv details

## Research Domains

Soil carbon, LAI, water table, biomass, tropical forest sites (Brazil/Peru/Panama), climate change impacts.
