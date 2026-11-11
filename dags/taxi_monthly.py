import os
from datetime import timedelta

import pendulum
from airflow.sdk import DAG, Param, get_current_context, task
from airflow.providers.standard.operators.bash import BashOperator
from airflow.timetables.interval import CronDataIntervalTimetable


PROJECT_ROOT = os.environ["TAXI_PROJECT_ROOT"]
MONTHS = ["2024-01", "2024-02", "2024-03"]


with DAG(
    dag_id="taxi_monthly",
    description="Load a taxi source month and rebuild Q1 reporting",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2024, 3, 31, tz="UTC"),
    schedule=CronDataIntervalTimetable(
        "0 0 1 * *",
        timezone="UTC",
    ),
    catchup=True,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(hours=1),
    default_args={
        "retries": 1,
        "retry_delay": timedelta(seconds=30),
        "execution_timeout": timedelta(minutes=20),
    },
    params={
        "month": Param(
            "2024-01",
            type="string",
            enum=MONTHS,
            description="Source month for a manual run",
        ),
        "force_reload": Param(
            False,
            type="boolean",
            description="Reload trips even if this delivery is unchanged",
        ),
    },
    tags=["taxi", "batch-elt"],
) as dag:

    @task
    def resolve_month():
        context = get_current_context()

        if context["dag_run"].run_type == "manual":
            month = context["params"]["month"]
        else:
            month = context["data_interval_start"].strftime("%Y-%m")

        if month not in MONTHS:
            raise ValueError(
                f"Month outside this project's Q1 scope: {month}"
            )

        print(f"Processing source month: {month}")
        return month

    period = resolve_month()

    task_env = {
        "PROJECT_ROOT": PROJECT_ROOT,
        "PROCESSING_MONTH": "{{ ti.xcom_pull(task_ids='resolve_month') }}",
        "FORCE_RELOAD": "{{ 'true' if params.force_reload else 'false' }}",
        "PYTHONUNBUFFERED": "1",
    }

    download_sources = BashOperator(
        task_id="download_sources",
        bash_command=(
            '"$PROJECT_ROOT/.venv/bin/python" '
            'download_month.py --month "$PROCESSING_MONTH"'
        ),
        cwd=PROJECT_ROOT,
        env=task_env,
        append_env=True,
        do_xcom_push=False,
    )

    load_trips = BashOperator(
        task_id="load_trips",
        bash_command="""
        set -euo pipefail

        if [ -f "$PROJECT_ROOT/data/fail_trip_load" ]; then
            exec "$PROJECT_ROOT/.venv/bin/python" load_trip_month.py \
                --month "$PROCESSING_MONTH" \
                --force \
                --fail-after-batches 1
        fi

        if [ "$FORCE_RELOAD" = "true" ]; then
            exec "$PROJECT_ROOT/.venv/bin/python" load_trip_month.py \
                --month "$PROCESSING_MONTH" \
                --force
        else
            exec "$PROJECT_ROOT/.venv/bin/python" load_trip_month.py \
                --month "$PROCESSING_MONTH"
        fi
        """,
        cwd=PROJECT_ROOT,
        env=task_env,
        append_env=True,
        do_xcom_push=False,
    )

    load_weather = BashOperator(
        task_id="load_weather",
        bash_command=(
            '"$PROJECT_ROOT/.venv/bin/python" '
            'load_weather.py --months 2024-01 2024-02 2024-03'
        ),
        cwd=PROJECT_ROOT,
        env=task_env,
        append_env=True,
        do_xcom_push=False,
    )

    build_models = BashOperator(
        task_id="build_models",
        bash_command=(
            '"$PROJECT_ROOT/.venv-dbt/bin/dbt" '
            'build --profiles-dir .'
        ),
        cwd=f"{PROJECT_ROOT}/transform",
        env=task_env,
        append_env=True,
        do_xcom_push=False,
    )

    publish_report = BashOperator(
        task_id="publish_report",
        bash_command=(
            '"$PROJECT_ROOT/.venv/bin/python" publish_reporting.py'
        ),
        cwd=PROJECT_ROOT,
        env=task_env,
        append_env=True,
        do_xcom_push=False,
    )

    period >> download_sources >> load_trips >> load_weather >> build_models >> publish_report