import csv
import json
from pathlib import Path
from time import perf_counter

import pyarrow.compute as pc
import pyarrow.parquet as pq


raw = Path(__file__).resolve().parent / "data" / "raw"

with (raw / "taxi_zone_lookup.csv").open(
    encoding="utf-8",
    newline="",
) as source:
    zones = list(csv.DictReader(source))

zone_ids = [int(zone["LocationID"]) for zone in zones]

print("Zones:", len(zones))
print("Unique zone IDs:", len(set(zone_ids)))
print("First zone:", zones[0])

if len(zone_ids) != len(set(zone_ids)):
    raise ValueError("Duplicate LocationID in zone lookup")





with (raw / "weather_nyc_2024-01.json").open(
    encoding="utf-8",
) as source:
    weather = json.load(source)

daily = weather["daily"]

dates = daily["time"]
temperatures = daily["temperature_2m_mean"]
precipitation = daily["precipitation_sum"]

if not (len(dates) == len(temperatures) == len(precipitation) == 31):
    raise ValueError("Expected 31 aligned daily weather values")

if len(set(dates)) != len(dates):
    raise ValueError("Duplicate weather date")

print("Weather days:", len(dates))
print("Weather timezone:", weather["timezone"])
print("Weather units:", weather["daily_units"])
print("First weather day:", dates[0], temperatures[0], precipitation[0])





trip_path = raw / "yellow_tripdata_2024-01.parquet"
trips = pq.ParquetFile(trip_path)

print("File MiB:", round(trip_path.stat().st_size / 1024**2, 2))
print("Trip rows:", trips.metadata.num_rows)
print("Row groups:", trips.num_row_groups)
print(trips.schema_arrow)



columns = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "trip_distance",
    "fare_amount",
]

sample = next(trips.iter_batches(batch_size=5, columns=columns))

for row in sample.to_pylist():
    print(row)


started = perf_counter()

rows_scanned = 0
missing_distances = 0
negative_distances = 0
largest_batch_bytes = 0

for batch in trips.iter_batches(batch_size=100_000, columns=columns):
    rows_scanned += batch.num_rows
    largest_batch_bytes = max(largest_batch_bytes, batch.nbytes)

    distances = batch.column("trip_distance")
    missing_distances += distances.null_count

    negative = pc.less(distances, 0)
    negative_distances += pc.sum(
        pc.cast(negative, "int64")
    ).as_py() or 0

if rows_scanned != trips.metadata.num_rows:
    raise ValueError("Scanned count does not match file metadata")

print("Scanned rows:", rows_scanned)
print("Missing distances:", missing_distances)
print("Negative distances:", negative_distances)
print("Largest batch MiB:", round(largest_batch_bytes / 1024**2, 2))
print("Scan seconds:", round(perf_counter() - started, 2))