from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.sdk import Asset

from mc_scraper_dag import MC_RAW_ASSET
from rt_scraper_dag import RT_RAW_ASSET

_DBT_DIR = "/opt/airflow/cinemetrics"

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
    BashOperator(
        task_id="dbt_build",
        bash_command=_DBT_CMD,
        pool="duckdb",
    )


dbt_build_dag()
