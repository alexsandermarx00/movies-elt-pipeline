# Migration Plan: Kubernetes → Docker Compose

## Context

The current infrastructure runs Airflow on Kubernetes (Minikube + Helm) using
`KubernetesPodOperator`. The goal is to simplify to `docker compose up`, with scrapers
running as subprocesses inside the Airflow container (LocalExecutor + BashOperator).

Two scrapers are available:
- `rottentomatoes_spider/` — Scrapy-based, outputs JSON via Scrapy FEED
- `mc_scrape/` — requests + deltalake, outputs Delta Lake tables directly

---

## Implementation Steps

### Step 1 — `docker-compose.yml` · Complexity: **Medium**

**New file** at repo root. Foundation for everything else.

Services:
| Service | Role |
|---|---|
| `postgres` | Airflow metadata DB |
| `airflow-init` | One-shot: DB migrate + admin user creation |
| `airflow-webserver` | UI on port 8080 |
| `airflow-scheduler` | Runs DAGs via LocalExecutor |

Volumes:
- `./airflow/dags` → `/opt/airflow/dags`
- `./data` → `/opt/airflow/data` (shared Delta Lake + JSON output)
- Named volume for logs

Key environment variables:
```
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW__CORE__LOAD_EXAMPLES=false
FEED_URI=/opt/airflow/data
```

> **Why medium:** Airflow compose requires correct UID matching, healthcheck ordering
> between services, and `airflow-init` must complete before scheduler/webserver start.

---

### Step 2 — `airflow/Dockerfile` update · Complexity: **Low-Medium**

**Modify** existing file.

Changes:
- Remove `apache-airflow-providers-cncf-kubernetes` and `boto3`
- `COPY` both scraper source trees into the image at `/opt/scrapers/`
- Install RT spider dependencies via `requirements.txt`
- Install mc_scrape as a package via `pip install .` (has `pyproject.toml`)

BashOperator tasks will use `cwd=/opt/scrapers/rottentomatoes_spider` for scrapy commands,
and mc_scrape will be runnable as `python -m metacritic`.

> **Why low-medium:** Straightforward changes, but mc_scrape uses `uv` while the image
> uses pip — need to verify `pip install .` works without a `[build-system]` table.

---

### Step 3 — Rewrite `airflow/dags/rt_scraper_dag.py` · Complexity: **Medium**

**Rewrite** existing file.

Changes:
- Remove all kubernetes imports (`KubernetesPodOperator`, `V1Volume`, `V1EnvVar`, etc.)
- Replace `discover_films` with `BashOperator`:
  ```
  scrapy crawl rt_discovery_spider -a browse_url=movies_in_theaters
  ```
- Replace `scrape_{action}` with `BashOperator.partial().expand()`:
  ```
  scrapy crawl rtspider -a movie={slug} -a action={action}
  ```
- Set `cwd=/opt/scrapers/rottentomatoes_spider` on BashOperator
- Set `env={"FEED_URI": "/opt/airflow/data/rt/%(action)s/%(name)s_%(time)s.json"}`

The DAG logic (discover → get_films → build_commands → fan-out per action) stays identical.

> **Why medium:** Operator swap is straightforward, but FEED_URI wiring and validating
> dynamic `.expand()` with BashOperator requires care.

---

### Step 4 — New `airflow/dags/mc_scraper_dag.py` · Complexity: **Medium**

**New file.** Mirrors the RT DAG pattern for the Metacritic scraper.

Flow:
1. `discover_movies` — BashOperator:
   ```
   python -m metacritic browse --max-items 50
   ```
   Writes to Delta Lake at `/opt/airflow/data/mc/discovered_movies`

2. `get_movies` — PythonOperator: reads discovered slugs from Delta Lake
   (`deltalake` is available since mc_scrape is installed in the image)

3. `scrape_movies` — `BashOperator.partial().expand()`:
   ```
   python -m metacritic movie {slug} all
   ```
   Writes to `/opt/airflow/data/mc/{general,critic_reviews,user_reviews}`

> **Why medium:** New file but follows established patterns. Main challenge is reading
> Delta Lake in a PythonOperator and wiring `FEED_URI` correctly.

---

### Step 5 — Load RT spider JSON → Delta Lake · Complexity: **Medium-High** _(optional)_

RT spider writes JSON files; mc_scrape writes Delta Lake directly. For a consistent storage
layer and clearer ELT demonstration, this gap should be closed.

**Recommended approach:** Add a `load_to_delta` PythonOperator task in the RT DAG after
scraping, which reads the JSON output and writes it to Delta Lake tables. Keeps the scraper
code untouched and makes the E→L boundary explicit in the DAG — a good thesis discussion point.

> **Why medium-high:** Requires defining PyArrow schemas from existing JSON samples
> (available in `airflow/output/`), and handling partial/failed scrape runs gracefully.

---

## Summary

| # | Task | File(s) | Complexity |
|---|------|---------|-----------|
| 1 | Create `docker-compose.yml` | `docker-compose.yml` _(new)_ | Medium |
| 2 | Update Airflow Dockerfile | `airflow/Dockerfile` | Low-Medium |
| 3 | Rewrite RT scraper DAG | `airflow/dags/rt_scraper_dag.py` | Medium |
| 4 | Create Metacritic DAG | `airflow/dags/mc_scraper_dag.py` _(new)_ | Medium |
| 5 | RT JSON → Delta Lake load step | `airflow/dags/rt_scraper_dag.py` | Medium-High |

**File to delete:** `airflow/values.yaml` — no longer needed after migration.  
**Directory to add:** `data/` — gitignored, holds all scraper output (Delta Lake + JSON).

---

## Verification

1. `docker compose up --build` — all services reach healthy state
2. `http://localhost:8080` — Airflow UI shows both DAGs
3. Trigger `rt_scraper` manually — JSON files appear under `./data/rt/`
4. Trigger `mc_scraper` manually — Delta tables appear under `./data/mc/`
5. Spot-check with DuckDB:
   ```sql
   SELECT * FROM delta_scan('./data/mc/general') LIMIT 5;
   ```
