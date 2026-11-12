from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def main():
    root = Path(__file__).resolve().parents[1]

    original = (
        root
        / "data"
        / "raw"
        / "yellow_tripdata_2024-01.parquet"
    )

    fixture = (
        root
        / "data"
        / "drills"
        / "missing_fare"
        / original.name
    )

    fixture.parent.mkdir(parents=True, exist_ok=True)

    with pq.ParquetFile(original) as source:
        field_index = source.schema_arrow.get_field_index("fare_amount")

        if field_index < 0:
            raise ValueError("Original file already lacks fare_amount")

        changed_schema = source.schema_arrow.remove(field_index)
        original_rows = source.metadata.num_rows

        with pq.ParquetWriter(
            fixture,
            changed_schema,
            compression="snappy",
        ) as writer:
            for batch in source.iter_batches(batch_size=100_000):
                table = pa.Table.from_batches([batch])
                table = table.drop(["fare_amount"])
                writer.write_table(table)

    with pq.ParquetFile(fixture) as changed:
        if changed.metadata.num_rows != original_rows:
            raise ValueError("Fixture row count differs from original")

        if "fare_amount" in changed.schema_arrow.names:
            raise ValueError("Fixture still contains fare_amount")

    print(f"Created: {fixture}")
    print(f"Rows preserved: {original_rows:,}")
    print("Removed column: fare_amount")


if __name__ == "__main__":
    main()