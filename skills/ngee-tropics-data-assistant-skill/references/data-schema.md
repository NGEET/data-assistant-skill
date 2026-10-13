# NGEE Tropics Dataset Catalog - Schema Reference

## CSV File: `assets/ngee_tropics_datasets.csv`

143 datasets from ESS-DIVE following JSON-LD schema.org format.

## Key Columns for Search & Analysis

| Column | Description | Example |
|--------|-------------|---------|
| `name` | Dataset title | "Soil carbon stocks..." |
| `@id` | ESS-DIVE dataset ID | `ess-dive-abc123...` |
| `datePublished` | Publication date (YYYY-MM-DD) | `2021-03-15` |
| `description` | Full abstract | long text |
| `keywords` | Comma-separated topics | `soil, carbon, Brazil` |
| `creator` | Author list | `Smith, J; Doe, A` |
| `variableMeasured` | Variables in dataset | `SOC, bulk density` |
| `spatialCoverage` | Geographic area | `Manaus, Brazil` |
| `temporalCoverage` | Date range of data | `2016-01/2019-12` |
| `search_viewUrl` | ESS-DIVE web page URL | `https://ess-dive.lbl.gov/...` |

## Less-Used Columns

| Column | Description |
|--------|-------------|
| `@context`, `@type` | JSON-LD metadata |
| `distribution` | File download info (JSON string) |
| `citation` | Formatted citation |
| `funder` | Grant/funding source |
| `license` | Data license (usually CC BY 4.0) |
| `measurementTechnique` | Methods used |
| `award` | DOE award info |

## Data Notes

- Missing values: empty string, NaN, or `-9999`
- `keywords` and `creator` are semicolon or comma-separated strings
- `distribution` column contains JSON string with file URLs and formats
- `search_viewUrl` links directly to ESS-DIVE landing page

## Research Domains in the Catalog

- Soil respiration and carbon cycling
- Leaf area index (LAI) and vegetation structure
- Water table depth and hydrology
- Biomass and forest inventory
- Tropical forest sites: Brazil (Manaus), Peru, Panama
- Climate change impacts on tropical ecosystems

## DOI Format

Each dataset has a DOI extractable from `@id` or `search_viewUrl`:
- Format: `doi:10.15485/XXXXXXX`
- Use with `download_dataset.py --doi 10.15485/XXXXXXX`
