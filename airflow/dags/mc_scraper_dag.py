from __future__ import annotations

import glob
import json
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.sdk import Variable

from _assets import MC_RAW_ASSET

_DATA = "/opt/airflow/data"
_MC_FEED = f"{_DATA}/mc"
_WAREHOUSE = f"{_DATA}/warehouse.duckdb"

# Rate/politeness knobs sourced from Airflow Variables (Admin > Variables in the
# UI) so they can be changed live without recreating containers. Templated into
# the scraper subprocess env; the `.get(name, default)` keeps DAGs working even
# before the variables are seeded.
_MC_RATE_ENV = {
    "MC_REQUEST_DELAY_MIN": "{{ var.value.get('mc_request_delay_min', '1.0') }}",
    "MC_REQUEST_DELAY_MAX": "{{ var.value.get('mc_request_delay_max', '3.0') }}",
    "MC_MAX_RETRIES": "{{ var.value.get('mc_max_retries', '5') }}",
}
_MC_DISCOVER_ENV = {
    "MC_DISCOVER_BY_YEAR": "{{ var.value.get('mc_discover_by_year', 'false') }}",
    "MC_DISCOVER_YEAR_MIN": "{{ var.value.get('mc_discover_year_min', '1990') }}",
    "MC_DISCOVER_YEAR_MAX": "{{ var.value.get('mc_discover_year_max', '2026') }}",
    "MC_DISCOVER_MAX_PER_YEAR": "{{ var.value.get('mc_discover_max_per_year', '2000') }}",
}


@dag(
    dag_id="mc_scraper",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["metacritic"],
)
def mc_scraper_dag():

    # Resolve the Metacritic API key ONCE, then hand it to every downstream task
    # via MC_API_KEY. get_api_key() short-circuits on that env var, so the ~20k
    # movie scrapes never re-hit the homepage — the main bot-block vector.
    fetch_api_key = BashOperator(
        task_id="fetch_api_key",
        bash_command="python -m metacritic apikey",
        retries=3,
        retry_delay=timedelta(seconds=30),
    )
    _MC_API_KEY = "{{ ti.xcom_pull(task_ids='fetch_api_key') }}"

    discover_movies = BashOperator(
        task_id="discover_movies",
        # Metacritic intermittently serves a bot page with no embedded API key;
        # a single fetch can fail transiently, so retry before failing the DAG.
        retries=2,
        retry_delay=timedelta(seconds=30),
        bash_command=(
            # Dev default: two small browse passes (~200 movies).
            # Catalog scale (MC_DISCOVER_BY_YEAR=true): shard by release year to
            # exceed the finder's single-query result cap and reach the full ~20k.
            # NOTE: --sort-by needs the = form because the value starts with '-'.
            'if [ "${MC_DISCOVER_BY_YEAR:-false}" = "true" ]; then\n'
            '  for y in $(seq ${MC_DISCOVER_YEAR_MIN:-1990} ${MC_DISCOVER_YEAR_MAX:-2026}); do\n'
            '    echo "=== discovering year $y ===";\n'
            '    python -m metacritic browse --sort-by=-metaScore --year-min $y --year-max $y --max-items ${MC_DISCOVER_MAX_PER_YEAR:-2000};\n'
            '  done;\n'
            'else\n'
            '  python -m metacritic browse --sort-by=-metaScore --max-items 100 &&\n'
            '  python -m metacritic browse --sort-by=-releaseDate --max-items 100;\n'
            'fi'
        ),
        env={"FEED_URI": _MC_FEED, "MC_API_KEY": _MC_API_KEY, **_MC_RATE_ENV, **_MC_DISCOVER_ENV},
        append_env=True,
    )

    @task
    def get_movies() -> list[str]:
        discovered_dir = Path(f"{_MC_FEED}/discovered_movies")
        if not discovered_dir.exists():
            return []
        slugs = []
        decoder = json.JSONDecoder(strict=False)
        for fp in discovered_dir.glob("*.json"):
            with open(fp) as f:
                items = decoder.decode(f.read())
            slugs.extend(item["slug"] for item in items)
        slugs = list(dict.fromkeys(slugs))
        # `mc_movie_limit` Airflow Variable caps how many movies to scrape.
        # 0 (or negative) = no cap (every discovered movie). Editable live in
        # Admin > Variables without recreating containers.
        limit = int(Variable.get("mc_movie_limit", default="10"))
        if limit <= 0:
            return slugs
        return slugs[:limit]

    _REVIEW_PAGES = 2

    @task
    def build_scrape_commands(slugs: list[str]) -> list[str]:
        commands = [
            f"python -m metacritic movie {slug} all --max-pages {_REVIEW_PAGES}"
            for slug in slugs
        ]
        # Batch to stay under Airflow's max_map_length (1024)
        batch_size = max(50, -(-len(commands) // 1000))
        return [
            "; ".join(commands[i : i + batch_size])
            for i in range(0, len(commands), batch_size)
        ]

    @task(outlets=[MC_RAW_ASSET], pool="duckdb")
    def load_raw_to_duckdb() -> None:
        import duckdb

        con = duckdb.connect(_WAREHOUSE)
        con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

        for table, subdir in [
            ("mc_general", "general"),
            ("mc_critic_reviews", "critic_reviews"),
            ("mc_user_reviews", "user_reviews"),
        ]:
            con.execute(f"""
                CREATE TABLE IF NOT EXISTS bronze.{table} (
                    _loaded_at TIMESTAMP,
                    _source_file VARCHAR,
                    data JSON
                )
            """)
            # Full-snapshot load: clear the table so re-runs don't accumulate
            # duplicate copies of every file (bronze stays 1x the files on disk).
            con.execute(f"TRUNCATE bronze.{table}")
            for fp in glob.glob(f"{_MC_FEED}/{subdir}/*.json"):
                with open(fp, errors="replace") as f:
                    raw = f.read()
                try:
                    content = json.dumps(json.loads(raw))
                except json.JSONDecodeError as e:
                    print(f"Skipping malformed file {fp}: {e}")
                    continue
                con.execute(
                    f"INSERT INTO bronze.{table} (_loaded_at, _source_file, data) VALUES (current_timestamp, ?, ?)",
                    [fp, content],
                )

        con.close()

    slugs = get_movies()
    fetch_api_key >> discover_movies >> slugs

    commands = build_scrape_commands(slugs=slugs)
    scrape = BashOperator.partial(
        task_id="scrape_movies",
        env={"FEED_URI": _MC_FEED, "MC_API_KEY": _MC_API_KEY, **_MC_RATE_ENV},
        append_env=True,
        # Bound concurrency to a safe request rate (pool), and let a throttling
        # episode self-heal: back off, retry, then resume-skip the done movies.
        pool="mc_scrape",
        retries=3,
        retry_delay=timedelta(minutes=2),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=30),
    ).expand(bash_command=commands)

    load = load_raw_to_duckdb()
    scrape >> load


mc_scraper_dag()
