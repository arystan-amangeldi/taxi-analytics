import argparse
import hashlib
import os
from datetime import date
from pathlib import Path

import clickhouse_connect
import psycopg
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent

COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
    "total_amount",
    "payment_type",
]


def file_sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def target_matches(client, source_file, checksum, expected):
    count, wrong_hashes = client.query(
        """
        SELECT count(), countIf(source_sha256 != %(checksum)s)
        FROM raw.trips
        WHERE source_file = %(source_file)s
        """,
        parameters={
            "source_file": source_file,
            "checksum": checksum,
        },
    ).first_row

    return count == expected and wrong_hashes == 0

def stage_file(client, path, source_file, checksum, fail_after_batches):
    parquet = pq.ParquetFile(path)

    missing = set(COLUMNS) - set(parquet.schema_arrow.names)
    if missing:
        raise ValueError(f"Missing source columns: {sorted(missing)}")

    expected = parquet.metadata.num_rows
    if expected == 0:
        raise ValueError("Empty trip delivery: refusing to replace a month")

    client.command("TRUNCATE TABLE raw.trips_work")

    sent = 0

    for batch_number, batch in enumerate(
        parquet.iter_batches(batch_size=100_000, columns=COLUMNS),
        start=1,
    ):
        table = pa.Table.from_batches([batch])

        for name in COLUMNS[:2]:
            table = table.set_column(
                table.schema.get_field_index(name),
                name,
                pc.cast(table[name], pa.string()),
            )

        n = table.num_rows

        table = table.append_column(
            "source_file",
            pa.array([source_file] * n),
        )

        table = table.append_column(
            "source_sha256",
            pa.array([checksum] * n),
        )

        table = table.append_column(
            "source_row_number",
            pa.array(
                range(sent + 1, sent + n + 1),
                type=pa.uint64(),
            ),
        )

        client.insert_arrow("raw.trips_work", table)

        sent += n
        print(f"Staged {sent:,}/{expected:,}")

        if fail_after_batches == batch_number:
            raise RuntimeError("Intentional failure before publication")

    staged = client.query(
        "SELECT count() FROM raw.trips_work"
    ).first_row[0]

    if sent != expected or staged != expected:
        raise ValueError("Source, sent and staged row counts differ")

    if file_sha256(path) != checksum:
        raise ValueError("Source file changed while loading")

    return expected

def load_month(pg, client, args):
    month = date.fromisoformat(f"{args.month}-01")
    source_file = f"yellow_tripdata_{month:%Y-%m}.parquet"

    path = args.input or ROOT / "data" / "raw" / source_file

    if path.name != source_file:
        raise ValueError(f"The input filename must be {source_file}")

    checksum = file_sha256(path)
    expected = pq.ParquetFile(path).metadata.num_rows

    if expected == 0:
        raise ValueError("Empty trip delivery")

    locked = pg.execute(
        "SELECT pg_try_advisory_lock(41701)"
    ).fetchone()[0]

    if not locked:
        raise RuntimeError("Another monthly trip loader is running")

    previous = pg.execute(
        """
        SELECT sha256, row_count
        FROM ops.file_loads
        WHERE source_file = %s
        """,
        (source_file,),
    ).fetchone()

    if (
        not args.force
        and previous == (checksum, expected)
        and target_matches(client, source_file, checksum, expected)
    ):
        print(f"SKIP {source_file}: identical file already published")
        return

    stage_file(
        client,
        path,
        source_file,
        checksum,
        args.fail_after_batches,
    )

    client.command(
        """
        ALTER TABLE raw.trips
        REPLACE PARTITION %(source_file)s
        FROM raw.trips_work
        """,
        parameters={"source_file": source_file},
    )

    if not target_matches(client, source_file, checksum, expected):
        raise ValueError("Published partition does not match the delivery")

    pg.execute(
        """
        INSERT INTO ops.file_loads
            (source_file, sha256, row_count, loaded_at)
        VALUES (%s, %s, %s, now())
        ON CONFLICT (source_file) DO UPDATE
        SET sha256 = EXCLUDED.sha256,
            row_count = EXCLUDED.row_count,
            loaded_at = EXCLUDED.loaded_at
        """,
        (source_file, checksum, expected),
    )

    print(
        f"PUBLISHED {source_file}: {expected:,} rows; "
        f"SHA256 {checksum[:12]}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM")
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional corrected source file",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--fail-after-batches", type=int)
    args = parser.parse_args()

    client = clickhouse_connect.get_client(
        host="127.0.0.1",
        port=8123,
        username="taxi",
        password=os.environ["TAXI_CH_PASSWORD"],
        settings={"async_insert": 0, "max_threads": 2},
    )

    try:
        with psycopg.connect(
            host="127.0.0.1",
            port=5433,
            dbname="taxi",
            user="taxi",
            password=os.environ["TAXI_PG_PASSWORD"],
            connect_timeout=10,
            autocommit=True,
        ) as pg:
            load_month(pg, client, args)
    finally:
        client.close()


if __name__ == "__main__":
    main()