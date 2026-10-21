import json
import os
from datetime import date
from pathlib import Path

import clickhouse_connect
import psycopg
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


def replace_small_table(client, name, columns, rows):
    if not rows:
        raise ValueError(f"{name}: source is empty")

    target = f"raw.{name}"
    incoming = f"raw.{name}_incoming"

    client.command(f"TRUNCATE TABLE {incoming}")

    client.insert(
        incoming,
        rows,
        column_names=columns,
    )

    loaded = client.query(
        f"SELECT count() FROM {incoming}"
    ).first_row[0]

    if loaded != len(rows):
        raise ValueError(f"{name}: source and target counts differ")

    client.command(
        f"EXCHANGE TABLES {target} AND {incoming}"
    )

    print(f"Published {loaded:,} rows to {target}")



def load_trips(client, raw):
    path = raw / "yellow_tripdata_2024-01.parquet"

    columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "trip_distance",
        "fare_amount",
        "total_amount",
        "payment_type",
    ]

    with pq.ParquetFile(path) as trips:
        expected = trips.metadata.num_rows

        if expected == 0:
            raise ValueError("Trip source is empty")

        client.command("TRUNCATE TABLE raw.trips_incoming")
        rows_sent = 0

        for batch in trips.iter_batches(
            batch_size=100_000,
            columns=columns,
        ):
            table = pa.Table.from_batches([batch])

            for name in [
                "tpep_pickup_datetime",
                "tpep_dropoff_datetime",
            ]:
                index = table.schema.get_field_index(name)
                table = table.set_column(
                    index,
                    name,
                    pc.cast(table[name], pa.string()),
                )

            table = table.append_column(
                "source_file",
                pa.array([path.name] * batch.num_rows),
            )

            client.insert_arrow("raw.trips_incoming", table)

            rows_sent += batch.num_rows
            print(f"Sent {rows_sent:,} / {expected:,} trip rows")

        loaded = client.query(
            "SELECT count() FROM raw.trips_incoming"
        ).first_row[0]

        if not (loaded == rows_sent == expected):
            raise ValueError(
                f"Trip count mismatch: "
                f"source={expected}, sent={rows_sent}, loaded={loaded}"
            )

    client.command(
        "EXCHANGE TABLES raw.trips AND raw.trips_incoming"
    )

    print(f"Published {loaded:,} trips")




def main():
    raw = Path(__file__).resolve().parent / "data" / "raw"

    with psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="taxi",
        user="taxi",
        password=os.environ["TAXI_PG_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        zones = connection.execute(
            """
            SELECT location_id, borough, zone, service_zone
            FROM reference.taxi_zones
            ORDER BY location_id
            """
        ).fetchall()

    with (raw / "weather_nyc_2024-01.json").open(
        encoding="utf-8",
    ) as source:
        daily = json.load(source)["daily"]

    weather_rows = [
        (date.fromisoformat(day), temperature, precipitation)
        for day, temperature, precipitation in zip(
            daily["time"],
            daily["temperature_2m_mean"],
            daily["precipitation_sum"],
            strict=True,
        )
    ]

    client = clickhouse_connect.get_client(
        host="127.0.0.1",
        port=8123,
        username="taxi",
        password=os.environ["TAXI_CH_PASSWORD"],
        database="raw",
        settings={"async_insert": 0, "max_threads": 2},
    )

    try:
        replace_small_table(
            client,
            "taxi_zones",
            ["location_id", "borough", "zone", "service_zone"],
            zones,
        )

        replace_small_table(
            client,
            "weather_daily",
            ["weather_date", "temperature_c", "precipitation_mm"],
            weather_rows,
        )

        load_trips(client, raw)

    finally:
        client.close()


if __name__ == "__main__":
    main()