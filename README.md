# NGEE-Tropics Data Assistant Skill

An [Agent Skill](https://agentskills.io) that lets AI coding agents such as Claude Code and Codex find, inspect, download, and analyze
[NGEE-Tropics](https://ngee-tropics.lbl.gov/) datasets published on [ESS-DIVE](https://ess-dive.lbl.gov/).

Ask your agent something like *"What soil carbon data is available from Manaus?"* or *"Download the LAI datasets from Panama and plot them"*, and the skill does the following:

1. Asks a couple of clarifying questions: what data you need and what you want to do with it.
2. Searches a bundled catalog of about 143 NGEE-Tropics datasets. Searching makes no API calls.
3. Downloads the datasets you pick from ESS-DIVE by DOI.
4. Writes analysis and plotting scripts into a timestamped session folder, so every request stays reproducible.

## Repository layout

```
skills/ngee-tropics-data-assistant-skill/
├── SKILL.md                         # instructions the agent follows
├── VERSION                          # published skill version (semver)
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

## Versioning

This repository uses semantic versions for the published skill package.

- Current version: **v0.1.0**
- Skill version file: `skills/ngee-tropics-data-assistant-skill/VERSION`
- Change history: [CHANGELOG.md](CHANGELOG.md)

When you publish updates, bump `VERSION` and add a matching changelog entry.

## Installation

### Requirements

- An agent that supports Agent Skills (`SKILL.md`), e.g. [Claude Code](https://docs.claude.com/en/docs/claude-code) or [Codex](https://github.com/openai/codex)
- Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- An ESS-DIVE API token

### Add the skill to a project

Copy the skill folder into your agent's skills directory:

| Agent | Project-level | User-level (all projects) |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |

For example, at the project level:

```bash
git clone https://github.com/NGEET/data-assistant-skill.git

# Claude Code
mkdir -p your-project/.claude/skills
cp -r data-assistant-skill/skills/ngee-tropics-data-assistant-skill your-project/.claude/skills/

# Codex
mkdir -p your-project/.agents/skills
cp -r data-assistant-skill/skills/ngee-tropics-data-assistant-skill your-project/.agents/skills/
```

Then start your agent from `your-project/`. The first time the skill runs, the agent creates a shared `.venv/` in the
project root and installs the dependencies from `scripts/requirements.txt`. The skill's scripts find their files
relative to their own location, so they work from any skills directory.

### ESS-DIVE token

To get a token:

1. Go to [data.ess-dive.lbl.gov](https://data.ess-dive.lbl.gov/) and click **Sign in with ORCID**. If you don't have an ORCID iD,
   [register for a free one](https://orcid.org/register).
2. Click your name in the top-right corner and select **My Profile**.
3. Go to **Settings > Authentication Token**.
4. On the **Token** tab, click **Copy**.

Then put it in a `.env` file in your project:

```bash
echo 'ESSDIVE_API_TOKEN=your-token-here' > your-project/.env
```

Tokens expire. If you get a "You do not have authorized access" error, copy a new token and update `.env`.
For more details, see the [ESS-DIVE Dataset API docs](https://docs.ess-dive.lbl.gov/programmatic-tools/ess-dive-dataset-api).

The scripts look for `.env` in this order: OS environment, `<project>/.env`, the skill folder, its parent
skills folder, and then the agent folder (e.g. `.claude/` or `.agents/`).
Don't commit `.env`.

## Usage

### With your agent

Open your agent in the project and ask in plain language. For example:

- "What NGEE-Tropics datasets have water table measurements?"
- "Find leaf area index data from Panama published after 2020"
- "Download soil carbon datasets from Brazil and summarize them"

The agent picks up the skill automatically when your request matches it. You can also call it by name:
`/ngee-tropics-data-assistant-skill` in Claude Code, or `$ngee-tropics-data-assistant-skill` in Codex.

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
SKILL=.claude/skills/ngee-tropics-data-assistant-skill   # or .agents/skills/... for Codex

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
