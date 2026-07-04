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
- [uv](https://docs.astral.sh/uv/) *(optional — for querying DuckDB locally)*
- [DuckDB CLI](https://duckdb.org/docs/installation/) *(optional — for querying DuckDB locally)*

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
   You can also run transformations manually locally using `dbt`:
   ```bash
   cd cinemetrics
   dbt deps
   dbt build
   dbt test
   ```

## Querying the data

Scraped data lands in `data/warehouse.duckdb`. Query it with the DuckDB CLI:

```bash
duckdb data/warehouse.duckdb
```

```sql
-- Open the browser UI (http://localhost:4213)
CALL start_ui();

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
