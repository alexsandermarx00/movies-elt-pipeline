ARG AIRFLOW_VERSION=3.2.1
FROM apache/airflow:${AIRFLOW_VERSION}

USER root
COPY rottentomatoes_spider/ /opt/scrapers/rottentomatoes_spider/
COPY mc_scrape/ /opt/scrapers/mc_scrape/
RUN chown -R airflow: /opt/scrapers/

USER airflow
RUN pip install --no-cache-dir \
    scrapy==2.14.2 \
    itemadapter==0.13.1 \
    duckdb

RUN pip install --no-cache-dir /opt/scrapers/mc_scrape/
