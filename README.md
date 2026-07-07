# movies-elt-pipeline

Local ELT pipeline that scrapes movie data from **Rotten Tomatoes** and **Metacritic**, loads raw JSON into **DuckDB**, and transforms it with **dbt**. Orchestrated by Apache Airflow running in Docker Compose.

## Architecture

```
Rotten Tomatoes  ──► Scrapy spider  ──┐
                                       ├──► JSON files ──► DuckDB (raw) ──► dbt (silver/gold)
Metacritic       ──► Python scraper ──┘

Orchestration: Airflow 3.2.1 · LocalExecutor · Docker Compose
```

| Layer | Tool |
|---|---|
| Extraction | Scrapy (RT) · `mc-scrape` Python package (Metacritic) |
| Orchestration | Apache Airflow 3.2.1 (LocalExecutor) |
| Raw storage | JSON files on disk + DuckDB `raw` schema |
| Transformation | dbt Core with `dbt-duckdb` |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- Python 3.10+ and [uv](https://docs.astral.sh/uv/) *(optional — only needed to run `dbt` or query DuckDB from your host instead of inside the containers)*
- [DuckDB CLI](https://duckdb.org/docs/installation/) *(optional — only needed to query DuckDB from your host)*

The Docker Compose stack is self-contained: the Airflow image bundles the scrapers, `dbt-core`, and `dbt-duckdb` (see `airflow/Dockerfile`), so nothing below is required just to run the pipeline end-to-end. It's only needed if you want to run `dbt` commands or query the warehouse directly from your host machine.

## Local Development Setup

To run `dbt` commands or the scrapers directly on your host (outside Docker), create a virtual environment and install the dependencies for the piece you're working on:

```bash
# From the repo root
uv venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows

# dbt (cinemetrics/)
uv pip install -r cinemetrics/requirements.txt

# Rotten Tomatoes spider (optional)
uv pip install -r rottentomatoes_spider/requirements.txt

# Metacritic scraper (optional — uses its own uv-managed environment)
cd mc_scrape && uv sync && cd ..
```

`cinemetrics/requirements.txt` pins the Python packages dbt needs (`dbt-core`, `dbt-duckdb`). It does not include the DuckDB CLI binary — install that separately if you want to query `data/warehouse.duckdb` from a terminal instead of through Python.

## Running the Pipeline (End-to-End)

1. **Start the infrastructure**:
   ```bash
   # Start everything (builds image on first run)
   docker compose up --build -d
   ```
2. **Trigger the DAGs**: 
   Access the Airflow UI at `http://localhost:8080` (default credentials: `airflow` / `airflow`).
   Unpause the DAGs: `rt_scraper`, `mc_scraper`, and `dbt_build`.
3. **Run dbt manually (optional)**:
   With the [local dev environment](#local-development-setup) set up and activated, you can also run transformations manually:
   ```bash
   cd cinemetrics
   dbt deps    # installs dbt packages declared in packages.yml (e.g. dbt_expectations)
   dbt build
   dbt test
   ```
   `dbt build` reads/writes `data/warehouse.duckdb` by default (see `cinemetrics/profiles.yml`), the same file the Docker pipeline uses — run this while the containers are idle to avoid DuckDB file-lock conflicts.

## Querying the data

Scraped data lands in `data/warehouse.duckdb`. Query it with the DuckDB CLI:

```bash
duckdb data/warehouse.duckdb
```

```sql
SHOW ALL TABLES;

-- Raw records
SELECT _source_file, _loaded_at FROM raw.rt_reviews LIMIT 5;

-- Extract fields from JSON
SELECT
    json_extract_string(record, '$.movie_id') AS movie,
    json_extract_string(record, '$.quote')    AS quote
FROM raw.rt_reviews,
LATERAL (SELECT unnest(data::JSON[])) t(record)
LIMIT 10;
```

### Using the DuckDB browser UI

DuckDB ships a local web UI for browsing schemas/tables and running SQL visually, as an alternative to the CLI prompt. From the same `duckdb` CLI session:

```sql
CALL start_ui();
```

This opens `http://localhost:4213` in your browser. Notes:

- The first call downloads the `ui` extension from DuckDB's extension repository, so it needs internet access once; after that it's cached locally and works offline.
- The UI connects to whichever database file you opened the CLI with (`data/warehouse.duckdb` in the command above) — it shares the same connection, so any query you've already run in the CLI is reflected there.
- Use the schema browser on the left to explore `raw`, `silver`, and `gold` schemas/tables, and the SQL editor pane to run ad-hoc queries with results rendered as a table.
- Close the UI with `CALL close_ui();`, or just close the CLI session.

## Project structure

```
.
├── airflow/
│   ├── Dockerfile          # Airflow image with scrapers baked in
│   ├── dags/
│   │   ├── rt_scraper_dag.py
│   │   ├── mc_scraper_dag.py
│   │   └── dbt_build_dag.py
│   └── sql/
│       └── init_warehouse.sql
├── cinemetrics/            # dbt project for data transformation
├── docs/                   # Documentation and practical guides
├── rottentomatoes_spider/  # Scrapy project for Rotten Tomatoes
├── mc_scrape/              # Python package for Metacritic
├── data/                   # Runtime data (gitignored)
│   └── warehouse.duckdb
└── docker-compose.yml
```

## DAGs

| DAG | Schedule | Description |
|---|---|---|
| `rt_scraper` | daily | Discovers movies in theaters, then scrapes score, details, and reviews for each |
| `mc_scraper` | daily | Browses Metacritic catalog, then scrapes general info and critic/user reviews |
| `dbt_build`  | daily | Runs dbt tests and builds the silver and gold layers in DuckDB |

Raw data is loaded into DuckDB under the `raw` schema with three columns: `_loaded_at`, `_source_file`, and `data` (full JSON). Silver and Gold layers are created via dbt.
