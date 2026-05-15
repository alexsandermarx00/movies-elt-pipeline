ARG AIRFLOW_VERSION=3.1.8
FROM apache/airflow:${AIRFLOW_VERSION}
RUN pip install --no-cache-dir \
    apache-airflow-providers-cncf-kubernetes \
    boto3
