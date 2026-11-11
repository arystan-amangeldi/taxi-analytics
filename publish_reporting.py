import os
from math import isclose

import clickhouse_connect


def main():
    client = clickhouse_connect.get_client(
        host="127.0.0.1",
        port=8123,
        username="taxi",
        password=os.environ["TAXI_CH_PASSWORD"],
        settings={"max_threads": 2},
    )

    try:
        client.command(
            "CREATE DATABASE IF NOT EXISTS reporting ENGINE = Atomic"
        )

        # Remove only an earlier work table.
        client.command(
            "DROP TABLE IF EXISTS reporting.mart_daily_borough_incoming"
        )

        # Build a candidate snapshot without changing the published table.
        client.command("""
            CREATE TABLE reporting.mart_daily_borough_incoming
            ENGINE = MergeTree
            ORDER BY (date_day, borough)
            AS
            SELECT
                *,
                now64(3, 'UTC') AS published_at
            FROM analytics.mart_daily_borough
        """)

        candidate = client.query("""
            SELECT
                count(*),
                uniqExact(tuple(date_day, borough)),
                sum(trip_count),
                sum(total_fare_usd)
            FROM reporting.mart_daily_borough_incoming
        """).result_rows[0]

        expected = client.query("""
            SELECT
                count(*),
                sum(trip_count),
                sum(total_fare_usd)
            FROM analytics.mart_daily_borough
        """).result_rows[0]

        row_count, unique_grains, trip_count, fare_total = candidate

        if row_count == 0 or row_count != unique_grains:
            raise ValueError("Empty report or duplicate report grain")

        if (
            row_count != expected[0]
            or trip_count != expected[1]
            or not isclose(
                fare_total,
                expected[2],
                rel_tol=0,
                abs_tol=0.01,
            )
        ):
            raise ValueError("Report copy does not match the candidate")

        exists = client.query("""
            EXISTS TABLE reporting.mart_daily_borough
        """).result_rows[0][0]

        if exists:
            client.command("""
                EXCHANGE TABLES
                    reporting.mart_daily_borough
                    AND reporting.mart_daily_borough_incoming
            """)
        else:
            client.command("""
                RENAME TABLE
                    reporting.mart_daily_borough_incoming
                    TO reporting.mart_daily_borough
            """)

        print(
            f"Published {row_count:,} reporting rows "
            f"representing {trip_count:,} trips"
        )

    finally:
        client.close()


if __name__ == "__main__":
    main()