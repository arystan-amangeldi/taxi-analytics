# taxi-analytics
Batch ELT analytics taxi analytics warehouse for **9.55 million NYC yellow taxi trips**, using Python, PostgreSQL, ClickHouse, dbt Airflow

The project combines January–March 2024 trip data with taxi zones and daily NYC weather.

Link to the dataset: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page


## Start services

For the existing configured Codespace:

```bash
cd /workspaces/taxi-analytics

docker start taxi-postgres taxi-clickhouse taxi-superset

source .venv-airflow/bin/activate
source scripts/airflow_env.sh

read -rsp "Existing PostgreSQL password: " TAXI_PG_PASSWORD
printf '\n'
export TAXI_PG_PASSWORD

read -rsp "Existing ClickHouse password: " TAXI_CH_PASSWORD
printf '\n'
export TAXI_CH_PASSWORD

airflow standalone
```

Log in to Airflow and Superset and enjoy the use.
