from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from _assets import MC_RAW_ASSET, RT_RAW_ASSET

_DBT_DIR = "/opt/airflow/cinemetrics"
_WAREHOUSE = "/opt/airflow/data/warehouse.duckdb"
_INIT_SQL = "/opt/airflow/sql/init_warehouse.sql"

_DBT_CMD = f"cd {_DBT_DIR} && dbt build --profiles-dir . --project-dir ."


@dag(
    dag_id="dbt_build",
    schedule=[RT_RAW_ASSET, MC_RAW_ASSET],
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["dbt", "transform"],
)
def dbt_build_dag():

    @task(pool="duckdb")
    def bootstrap_bronze() -> None:
        # Ensure every bronze source table exists so `dbt build` succeeds even
        # if a scraper hasn't loaded its data yet (silver just returns empty).
        import duckdb

        with open(_INIT_SQL) as f:
            ddl = f.read()
        con = duckdb.connect(_WAREHOUSE)
        con.execute(ddl)
        con.close()

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=_DBT_CMD,
        pool="duckdb",
    )

    bootstrap_bronze() >> dbt_build


dbt_build_dag()
