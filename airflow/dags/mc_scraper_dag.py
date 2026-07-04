from __future__ import annotations

import glob
import json
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

from _assets import MC_RAW_ASSET

_DATA = "/opt/airflow/data"
_MC_FEED = f"{_DATA}/mc"
_WAREHOUSE = f"{_DATA}/warehouse.duckdb"


@dag(
    dag_id="mc_scraper",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["metacritic"],
)
def mc_scraper_dag():

    discover_movies = BashOperator(
        task_id="discover_movies",
        bash_command=(
            # Two-pass browse: top Metascore first, then most recent releases.
            # NOTE: --sort-by needs the = form because the value starts with '-'
            # (argparse otherwise reads -metaScore as a flag).
            "python -m metacritic browse --sort-by=-metaScore --max-items 100"
            " && python -m metacritic browse --sort-by=-releaseDate --max-items 100"
        ),
        env={"FEED_URI": _MC_FEED},
        append_env=True,
    )

    _MOVIE_LIMIT = 100

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
        return list(dict.fromkeys(slugs))[:_MOVIE_LIMIT]

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
    discover_movies >> slugs

    commands = build_scrape_commands(slugs=slugs)
    scrape = BashOperator.partial(
        task_id="scrape_movies",
        env={"FEED_URI": _MC_FEED},
        append_env=True,
    ).expand(bash_command=commands)

    load = load_raw_to_duckdb()
    scrape >> load


mc_scraper_dag()
