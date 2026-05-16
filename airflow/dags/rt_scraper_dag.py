from __future__ import annotations

import glob
import json
from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

_DATA = "/opt/airflow/data"
_SCRAPERS = "/opt/scrapers/rottentomatoes_spider"
_WAREHOUSE = f"{_DATA}/warehouse.duckdb"


@dag(
    dag_id="rt_scraper",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["rottentomatoes"],
)
def rt_scraper_dag():

    discover_films = BashOperator(
        task_id="discover_films",
        bash_command="scrapy crawl rt_discovery_spider -a browse_url=movies_in_theaters",
        cwd=_SCRAPERS,
        env={"FEED_URI": f"{_DATA}/rt/discovery.json"},
        append_env=True,
    )

    @task
    def get_films() -> list[str]:
        with open(f"{_DATA}/rt/discovery.json") as f:
            items = json.load(f)
        return [item["slug"] for item in items]

    @task
    def build_commands(slugs: list[str], action: str) -> list[str]:
        return [
            f"scrapy crawl rtspider -a movie={slug} -a action={action}"
            for slug in slugs
        ]

    @task
    def load_raw_to_duckdb(action: str) -> None:
        import duckdb

        files = glob.glob(f"{_DATA}/rt/{action}/*.json")
        if not files:
            return

        con = duckdb.connect(_WAREHOUSE)
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.rt_{action} (
                _loaded_at TIMESTAMP,
                _source_file VARCHAR,
                data JSON
            )
        """)
        for fp in files:
            with open(fp, errors="replace") as f:
                raw = f.read()
            try:
                content = json.dumps(json.loads(raw))
            except json.JSONDecodeError as e:
                print(f"Skipping malformed file {fp}: {e}")
                continue
            con.execute(
                f"INSERT INTO raw.rt_{action} (_loaded_at, _source_file, data) VALUES (current_timestamp, ?, ?)",
                [fp, content],
            )
        con.close()

    slugs = get_films()
    discover_films >> slugs

    for action in ["score", "details", "reviews"]:
        commands = build_commands(slugs=slugs, action=action)
        scrape = BashOperator.partial(
            task_id=f"scrape_{action}",
            cwd=_SCRAPERS,
            env={"FEED_URI": f"{_DATA}/rt/{action}/%(name)s_%(time)s.json"},
            append_env=True,
        ).expand(bash_command=commands)
        load = load_raw_to_duckdb.override(task_id=f"load_{action}_to_duckdb")(action=action)
        scrape >> load


rt_scraper_dag()
