# NGEE-Tropics Data Assistant Skill

An [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) that lets Claude find, inspect, download, and analyze
[NGEE-Tropics](https://ngee-tropics.lbl.gov/) datasets published on [ESS-DIVE](https://ess-dive.lbl.gov/).

Ask Claude something like *"What soil carbon data is available from Manaus?"* or *"Download the LAI datasets from Panama and plot them"*, and the skill does the following:

1. Asks a couple of clarifying questions: what data you need and what you want to do with it.
2. Searches a bundled catalog of about 143 NGEE-Tropics datasets. Searching makes no API calls.
3. Downloads the datasets you pick from ESS-DIVE by DOI.
4. Writes analysis and plotting scripts into a timestamped session folder, so every request stays reproducible.

## Repository layout

```
skills/ngee-tropics-data-assistant-skill/
├── SKILL.md                         # instructions Claude follows
├── assets/ngee_tropics_datasets.csv # the dataset catalog (single source of truth)
├── references/                      # catalog design, CSV schema, session workflow
└── scripts/
    ├── search_datasets.py           # search/filter the catalog
    ├── download_dataset.py          # download a dataset's files by DOI
    ├── catalog.py                   # catalog module + incremental `sync` from ESS-DIVE
    ├── build_catalog.py             # wrapper around `catalog.py sync`
    ├── test_search_datasets.py
    └── requirements.txt
```

## Installation

### Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code) (or another client that supports Agent Skills)
- Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- *(Optional, recommended)* An ESS-DIVE API token

### Add the skill to a project

The skill's instructions use paths relative to `.claude/skills/` in your project, so install it there:

```bash
git clone https://github.com/NGEET/data-assistant-skill.git
mkdir -p your-project/.claude/skills
cp -r data-assistant-skill/skills/ngee-tropics-data-assistant-skill your-project/.claude/skills/
```

Then start Claude Code from `your-project/`. Claude creates a shared `.venv/` in the project root and installs
the dependencies from `scripts/requirements.txt` the first time the skill runs.

### ESS-DIVE token (optional)

Without a token, the skill still works, but rate limits apply and private datasets are unavailable.
Get a token from your [ESS-DIVE account settings](https://data.ess-dive.lbl.gov/), then put it in a `.env` file:

```bash
echo 'ESSDIVE_API_TOKEN=your-token-here' > your-project/.env
```

The scripts look for `.env` in this order: OS environment, `<project>/.env`,
`.claude/skills/ngee-tropics-data-assistant-skill/.env`, `.claude/skills/.env`, `.claude/.env`.
Don't commit `.env`.

## Usage

### With Claude

Open Claude Code in your project and ask in plain language. For example:

- "What NGEE-Tropics datasets have water table measurements?"
- "Find leaf area index data from Panama published after 2020"
- "Download soil carbon datasets from Brazil and summarize them"

Claude invokes the skill automatically. You can also call it directly with `/ngee-tropics-data-assistant-skill`.

Each request writes its output to its own folder:

```
sessions/20260305_143022_soil-carbon-brazil-2020/
├── data/        # downloaded files
├── analyze.py   # generated analysis
├── visualize.py # generated plots
├── figures/
└── results/
```

### Running the scripts directly

```bash
SKILL=.claude/skills/ngee-tropics-data-assistant-skill

# Search the catalog (no network). Filters: --name --description --keywords --creator
# --variable --spatial --start-date --end-date; -v for detail; --list-columns
.venv/bin/python $SKILL/scripts/search_datasets.py --name "soil carbon" --spatial Brazil -v

# Download a dataset (use --dry-run to only list its files)
.venv/bin/python $SKILL/scripts/download_dataset.py --doi 10.15485/2530733 --output ./data

# Refresh the catalog from ESS-DIVE (incremental, about 5 API calls plus 1 per new or updated dataset)
.venv/bin/python $SKILL/scripts/catalog.py sync
```

## Keeping the catalog up to date

`assets/ngee_tropics_datasets.csv` is a fully enriched snapshot of the NGEE-Tropics collection, keyed by
ESS-DIVE's versioned `search_id`. `catalog.py sync` lists the current collection, reuses rows that haven't changed,
enriches only new or revised datasets, and removes datasets that were taken down upstream.
Use `--rebuild` to force a full refresh. See
[`references/catalog-design.md`](skills/ngee-tropics-data-assistant-skill/references/catalog-design.md) for details.

To update the published catalog, run a sync and open a PR with the updated CSV.

## Development

```bash
cd skills/ngee-tropics-data-assistant-skill
uv run --with-requirements scripts/requirements.txt --with pytest pytest scripts/
```

## License

BSD 3-Clause. See [LICENSE](LICENSE).
