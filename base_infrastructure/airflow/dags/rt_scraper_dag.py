"""
Airflow DAG: rt_scraper
Orchestrates Rotten Tomatoes film discovery and parallel extraction.

Required Airflow Variables:
  - RT_SPIDER_IMAGE:        Docker image used for all scraper pods.
  - RT_FEED_URI:            S3 URI for extraction output (e.g. s3://bucket/output/).
  - RT_DISCOVERY_FEED_URI:  S3 URI where the discovery spider writes its slug list.
"""

from __future__ import annotations

import json
from datetime import datetime

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import V1EnvVar, V1Volume, V1VolumeMount, V1HostPathVolumeSource


@dag(
    dag_id="rt_scraper",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["rottentomatoes"],
)
def rt_scraper_dag():

    output_volume = V1Volume(
        name="output",
        host_path=V1HostPathVolumeSource(path="/mnt/output"),
    )
    output_mount = V1VolumeMount(name="output", mount_path="/opt/airflow/output")

    discover_films = KubernetesPodOperator(
        task_id="discover_films",
        namespace="airflow",
        image="rt_spider:latest",
        image_pull_policy="Never",
        cmds=["scrapy", "crawl"],
        arguments=[
            "rt_discovery_spider",
            "-a", "browse_url=movies_in_theaters",
        ],
        env_vars=[
            V1EnvVar(name="FEED_URI", value="/opt/airflow/output/discovery.json"),
        ],
        volumes=[output_volume],
        volume_mounts=[output_mount],
        in_cluster=True,
        is_delete_operator_pod=True,
        get_logs=True,
    )

    @task
    def get_films() -> list[str]:
        feed_uri = "/opt/airflow/output/discovery.json"
        with open(feed_uri) as f:
            items = json.load(f)
        return [item["slug"] for item in items]

    @task
    def build_commands(slugs: list[str], action: str) -> list[list[str]]:
        return [
            ["rtspider", "-a", f"movie={slug}", "-a", f"action={action}"]
            for slug in slugs
        ]

    slugs = get_films()
    discover_films >> slugs

    for action in ["score", "details", "reviews"]:
        commands = build_commands(slugs=slugs, action=action)
        KubernetesPodOperator.partial(
            task_id=f"scrape_{action}",
            namespace="airflow",
            image="rt_spider:latest",
            image_pull_policy="Never",
            cmds=["scrapy", "crawl"],
            # TODO: Review the folder structure
            env_vars=[
                V1EnvVar(name="FEED_URI", value=f"/opt/airflow/output/{action}/%(name)s_%(time)s.json"),
            ],
            volumes=[output_volume],
            volume_mounts=[output_mount],
            pool="rt_scraper",
            in_cluster=True,
            is_delete_operator_pod=True,
            get_logs=True,
        ).expand(arguments=commands)


rt_scraper_dag()
