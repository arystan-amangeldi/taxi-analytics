from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent


def main():
    filename = "yellow_tripdata_2024-01.parquet"

    source_path = ROOT / "data" / "raw" / filename
    target_path = ROOT / "data" / "revisions" / filename
    temporary_path = target_path.with_suffix(".parquet.part")

    target_path.parent.mkdir(parents=True, exist_ok=True)

    changed = False
    rows_written = 0

    with pq.ParquetFile(source_path) as source:
        expected_rows = source.metadata.num_rows

        with pq.ParquetWriter(
            temporary_path,
            source.schema_arrow,
            compression="snappy",
        ) as writer:
            for batch in source.iter_batches(batch_size=100_000):
                table = pa.Table.from_batches([batch])

                if not changed:
                    fares = table["fare_amount"].to_pylist()

                    for index, fare in enumerate(fares):
                        if fare is not None:
                            fares[index] = fare + 1.00

                            field = table.schema.field("fare_amount")

                            table = table.set_column(
                                table.schema.get_field_index("fare_amount"),
                                field,
                                pa.array(fares, type=field.type),
                            )

                            changed = True

                            print(
                                f"Changed source row {rows_written + index + 1}: "
                                f"{fare} -> {fares[index]}"
                            )
                            break

                writer.write_table(table)
                rows_written += table.num_rows

    if not changed:
        raise ValueError("No non-null fare was found")

    if rows_written != expected_rows:
        raise ValueError("Source and output row counts differ")

    temporary_path.replace(target_path)

    print(f"Written {rows_written:,} rows to {target_path}")
    print("Original source file preserved")


if __name__ == "__main__":
    main()