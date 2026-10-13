# Session Workflow & uv Virtualenv

## Session Folder

Every user request gets a unique session folder. Naming format:

```
sessions/YYYYMMDD_HHMMSS_<slug>/
```

**Slug rules:**
- Lowercase, hyphen-separated
- Summarize the user's question in max 50 chars
- Remove stop words (a, the, for, of, etc.)

**Examples:**
- "Show me soil carbon datasets from Brazil 2020" → `soil-carbon-brazil-2020`
- "Download LAI datasets from Panama" → `lai-datasets-panama`
- "What water table data is available?" → `water-table-data`

**Full path example:** `sessions/20260305_143022_soil-carbon-brazil-2020/`

### Folder Structure

```
<project-root>/
├── .venv/              # shared uv virtualenv (created once, never commit)
├── sessions/
│   └── 20260305_143022_soil-carbon-brazil-2020/
│       ├── data/               # downloaded datasets go here
│       ├── analyze.py          # generated analysis scripts
│       ├── visualize.py        # generated visualization scripts
│       ├── figures/            # saved plots (PNG/SVG)
│       └── results/            # other output files, summary reports
```

## uv Virtualenv Setup

The virtualenv lives at `.venv/` in the project root and is shared across all sessions. Create it once:

Requires `uv`. Check availability: `uv --version`

If missing: `pip install uv` or follow https://docs.astral.sh/uv/getting-started/installation/

```bash
# Create shared virtualenv at project root (only if .venv doesn't exist)
uv venv .venv

# Install skill dependencies
uv pip install --python .venv/bin/python \
  -r $SKILL_DIR/scripts/requirements.txt

# Convenience alias
PYTHON=.venv/bin/python
```

## Running Scripts

Always use `.venv/bin/python`, never system Python:

```bash
SESSION=sessions/YYYYMMDD_HHMMSS_your-slug
mkdir -p $SESSION/data

# Search datasets
.venv/bin/python $SKILL_DIR/scripts/search_datasets.py --name "soil carbon" --verbose

# Download dataset to session data folder
.venv/bin/python $SKILL_DIR/scripts/download_dataset.py \
  --doi 10.15485/2530733 \
  --output $SESSION/data

# Run any generated analysis script
.venv/bin/python $SESSION/analysis.py
```

## Environment Variable Check

At skill activation, always verify `ESSDIVE_API_TOKEN` using the shared venv (never system Python):

```bash
.venv/bin/python -c "
import os
token = os.getenv('ESSDIVE_API_TOKEN', '').strip()
if not token:
    print('WARNING: ESSDIVE_API_TOKEN not set.')
    print('  Set in <project>/.env or $SKILL_DIR/.env')
    print('  Proceeding unauthenticated (rate limits apply, private datasets unavailable).')
else:
    print('Token OK')
"
```

**.env resolution order** (scripts auto-load in this order):
1. OS environment (`ESSDIVE_API_TOKEN` already exported)
2. `<project-root>/.env`  ← most common location
3. `$SKILL_DIR/.env`
4. `$SKILL_DIR/../.env` (the skills folder, e.g. `.claude/skills/` or `.agents/skills/`)
5. `$SKILL_DIR/../../.env` (e.g. `.claude/.env` or `.agents/.env`)

## Saving Generated Code

Any analysis scripts written during the session go in the session folder:

```bash
# Run analysis script
$PYTHON $SESSION/analyze.py

# Run visualization script (headless — no display required)
MPLBACKEND=Agg $PYTHON $SESSION/visualize.py
```

Plots go in `$SESSION/figures/`, other results in `$SESSION/results/`.

## Visualization Conventions

- Always use `MPLBACKEND=Agg` when running matplotlib in a terminal (no display)
- Save figures to `$SESSION/figures/` with numbered filenames: `01_monthly_temp.png`, `02_diurnal.png`, etc.
- Use `plt.savefig(..., dpi=150, bbox_inches="tight")` and `plt.close()` after each figure
- `seaborn.set_theme(style="whitegrid")` for consistent styling
