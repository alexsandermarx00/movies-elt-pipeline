from __future__ import annotations

import glob
import json
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

from _assets import MC_RAW_ASSET, RT_RAW_ASSET

_DATA = "/opt/airflow/data"
_SCRAPERS = "/opt/scrapers/rottentomatoes_spider"
_WAREHOUSE = f"{_DATA}/warehouse.duckdb"

# RT rate knobs from Airflow Variables (Admin > Variables), templated into the
# scrapy subprocess env so they can be changed live without recreating containers.
_RT_RATE_ENV = {
    "RT_DOWNLOAD_DELAY": "{{ var.value.get('rt_download_delay', '2') }}",
    "RT_RETRY_TIMES": "{{ var.value.get('rt_retry_times', '5') }}",
}


@dag(
    dag_id="rt_scraper",
    # RT consumes MC's output (resolve_crosswalk reads data/mc/general/*.json),
    # so trigger off MC's asset instead of an independent @daily schedule. This
    # enforces MC → RT ordering; @daily fired both DAGs simultaneously and RT
    # would race MC's not-yet-written general files on a fresh run.
    schedule=[MC_RAW_ASSET],
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["rottentomatoes"],
)
def rt_scraper_dag():

    @task(retries=2, retry_delay=timedelta(seconds=30))
    def resolve_crosswalk() -> None:
        """Translate MC imdb_ids → RT slugs via Wikidata SPARQL (P345→P1258).

        Reads imdb_id from MC general output files, POSTs a batched SPARQL
        query, and writes data/rt/crosswalk.json with one entry per resolved
        film. TV-series RT entries (P1258 = 'tv/...') are skipped because
        rtspider only handles /m/ paths.
        """
        import os
        import requests

        # Collect imdb_id + mc_slug + title from MC general output files.
        # Each file is a JSON array of GeneralItem objects.
        mc_movies: dict[str, dict] = {}
        for fp in glob.glob(f"{_DATA}/mc/general/*.json"):
            try:
                with open(fp) as f:
                    items = json.load(f)
                if isinstance(items, dict):
                    items = [items]
                for item in items:
                    imdb_id = item.get("imdb_id")
                    mc_slug = item.get("movie_slug") or item.get("slug")
                    if imdb_id and mc_slug and imdb_id not in mc_movies:
                        mc_movies[imdb_id] = {
                            "mc_slug": mc_slug,
                            "title": item.get("title"),
                        }
            except (json.JSONDecodeError, OSError) as e:
                print(f"Skipping {fp}: {e}")

        os.makedirs(f"{_DATA}/rt", exist_ok=True)

        if not mc_movies:
            print("No MC movies with imdb_id found; writing empty crosswalk.")
            with open(f"{_DATA}/rt/crosswalk.json", "w") as f:
                json.dump([], f)
            return

        print(f"Querying Wikidata for {len(mc_movies)} IMDB ids...")

        imdb_values = " ".join(f'"{iid}"' for iid in mc_movies)
        sparql = f"""
SELECT ?imdb ?rt WHERE {{
  VALUES ?imdb {{ {imdb_values} }}
  ?film wdt:P345 ?imdb .
  ?film wdt:P1258 ?rt .
}}
"""
        resp = requests.post(
            "https://query.wikidata.org/sparql",
            data={"query": sparql},
            headers={
                "Accept": "application/sparql-results+json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "movies-elt-pipeline/1.0 (airflow; educational)",
            },
            timeout=60,
        )
        resp.raise_for_status()
        bindings = resp.json()["results"]["bindings"]

        crosswalk = []
        for row in bindings:
            imdb_id = row["imdb"]["value"]
            rt_raw = row["rt"]["value"]  # e.g. "m/citizen_kane" or "tv/small_axe/s01"
            if rt_raw.startswith("tv/"):
                print(f"Skipping TV entry: {rt_raw} (imdb={imdb_id})")
                continue
            rt_slug = rt_raw.removeprefix("m/")
            mc_info = mc_movies.get(imdb_id, {})
            crosswalk.append({
                "imdb_id": imdb_id,
                "rt_slug": rt_slug,
                "mc_slug": mc_info.get("mc_slug"),
                "title": mc_info.get("title"),
            })

        print(f"Resolved {len(crosswalk)} MC→RT links via Wikidata.")
        with open(f"{_DATA}/rt/crosswalk.json", "w") as f:
            json.dump(crosswalk, f)

    @task
    def get_films() -> list[str]:
        with open(f"{_DATA}/rt/crosswalk.json") as f:
            items = json.load(f)
        return list(dict.fromkeys(item["rt_slug"] for item in items if item.get("rt_slug")))

    @task
    def build_commands(slugs: list[str], action: str) -> list[str]:
        import os

        # Resume: skip (slug, action) pairs already completed in a prior run
        # (marker written by the spider's closed() on success). RT_FORCE=true
        # re-scrapes everything.
        done_dir = f"{_DATA}/rt/.done/{action}"
        force = os.environ.get("RT_FORCE", "").strip().lower() == "true"
        todo = [
            s for s in slugs
            if force or not os.path.exists(f"{done_dir}/{s}.marker")
        ]
        commands = [
            f"scrapy crawl rtspider -a movie={slug} -a action={action}"
            for slug in todo
        ]
        # No-op keeps the task successful (not skipped) so downstream load still
        # runs and emits the asset when everything is already done.
        if not commands:
            return ["echo 'rt scrape: nothing to do (all slugs already done)'"]
        # Batch to stay under Airflow's max_map_length (1024): one mapped task
        # instance per batch, running its scrapy crawls sequentially.
        batch_size = max(50, -(-len(commands) // 1000))
        return [
            "; ".join(commands[i : i + batch_size])
            for i in range(0, len(commands), batch_size)
        ]

    @task(outlets=[RT_RAW_ASSET], pool="duckdb")
    def load_all_raw_to_duckdb() -> None:
        import duckdb

        con = duckdb.connect(_WAREHOUSE)
        con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

        # Crosswalk: single file, full snapshot (TRUNCATE + reload)
        con.execute("""
            CREATE TABLE IF NOT EXISTS bronze.rt_crosswalk (
                _loaded_at TIMESTAMP,
                _source_file VARCHAR,
                data JSON
            )
        """)
        crosswalk_path = f"{_DATA}/rt/crosswalk.json"
        try:
            with open(crosswalk_path) as f:
                raw = f.read()
            con.execute("TRUNCATE bronze.rt_crosswalk")
            con.execute(
                "INSERT INTO bronze.rt_crosswalk (_loaded_at, _source_file, data) "
                "VALUES (current_timestamp, ?, ?)",
                [crosswalk_path, json.dumps(json.loads(raw))],
            )
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Skipping crosswalk load: {e}")

        # Per-action tables: append new files each run
        for action in ["score", "details", "reviews", "critic_reviews"]:
            con.execute(f"""
                CREATE TABLE IF NOT EXISTS bronze.rt_{action} (
                    _loaded_at TIMESTAMP,
                    _source_file VARCHAR,
                    data JSON
                )
            """)
            for fp in glob.glob(f"{_DATA}/rt/{action}/*.json"):
                with open(fp, errors="replace") as f:
                    raw = f.read()
                try:
                    content = json.dumps(json.loads(raw))
                except json.JSONDecodeError as e:
                    print(f"Skipping malformed file {fp}: {e}")
                    continue
                con.execute(
                    f"INSERT INTO bronze.rt_{action} (_loaded_at, _source_file, data) "
                    "VALUES (current_timestamp, ?, ?)",
                    [fp, content],
                )

        con.close()

    xw = resolve_crosswalk()
    slugs = get_films()
    xw >> slugs

    scrapes = []
    for action in ["score", "details", "reviews", "critic_reviews"]:
        commands = build_commands(slugs=slugs, action=action)
        scrape = BashOperator.partial(
            task_id=f"scrape_{action}",
            cwd=_SCRAPERS,
            env={
                "FEED_URI": f"{_DATA}/rt/{action}/%(name)s_%(time)s.json",
                "RT_DONE_DIR": f"{_DATA}/rt/.done",
                **_RT_RATE_ENV,
            },
            append_env=True,
            # Bound concurrent scrapy processes (pool) + self-heal on throttling.
            pool="rt_scrape",
            retries=3,
            retry_delay=timedelta(minutes=2),
            retry_exponential_backoff=True,
            max_retry_delay=timedelta(minutes=30),
        ).expand(bash_command=commands)
        scrapes.append(scrape)

    load = load_all_raw_to_duckdb()
    for scrape in scrapes:
        scrape >> load


rt_scraper_dag()
