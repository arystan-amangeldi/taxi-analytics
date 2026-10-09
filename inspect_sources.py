import csv
import json
from pathlib import Path
from time import perf_counter
from datetime import date, timedelta

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

for name, values in daily.items():
    for index, value in enumerate(values):
        if value is None:
            raise ValueError(f"Missing value in {name} at index {index}")

print("Missing weather values: PASS")

if not (len(dates) == len(temperatures) == len(precipitation)):
    raise ValueError("Weather arrays have different lengths")

formatted_dates = [date.fromisoformat(d) for d in dates]

expected_dates = [
    date(2024, 1, 1) + timedelta(days=i) for i in range(31)
]

if formatted_dates != expected_dates:
    raise ValueError("Expected January 1-31, 2024, once each and in order")

print("January date coverage: PASS")

for index, value in enumerate(precipitation):
    if value < 0:
        raise ValueError(f"Negative precipitation on {dates[index]}: {value}")

print("Nonnegative precipitation: PASS")

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
zero_distances = 0
negative_fares = 0
drop_off_before_pickups = 0

largest_batch_bytes = 0

for batch in trips.iter_batches(batch_size=100_000, columns=columns):
    rows_scanned += batch.num_rows
    largest_batch_bytes = max(largest_batch_bytes, batch.nbytes)

    distances = batch.column("trip_distance")
    missing_distances += distances.null_count

    negative_dist = pc.less(distances, 0)
    negative_distances += pc.sum(
        pc.cast(negative_dist, "int64")
    ).as_py() or 0

    zero_dist = pc.equal(distances, 0)
    zero_distances += pc.sum(
        pc.cast(zero_dist, "int64")
    ).as_py() or 0

    fare_amounts = batch.column("fare_amount")

    negative_fare = pc.less(fare_amounts, 0)
    negative_fares += pc.sum(
        pc.cast(negative_fare, "int64")
    ).as_py() or 0

    pick_ups = batch.column("tpep_pickup_datetime")
    drop_offs = batch.column("tpep_dropoff_datetime")

    drop_off_before_pickup = pc.less(drop_offs, pick_ups)
    drop_off_before_pickups += pc.sum(
        pc.cast(drop_off_before_pickup, "int64")
    ).as_py() or 0


if rows_scanned != trips.metadata.num_rows:
    raise ValueError("Scanned count does not match file metadata")

print("Scanned rows:", rows_scanned)
print("Missing distances:", missing_distances)
print("Negative distances:", negative_distances)

print("Zero-distance trips: {} | {}%".format(zero_distances, round(zero_distances / rows_scanned * 100, 4)))
print("Negative fares: {} | {}%".format(negative_fares, round(negative_fares / rows_scanned * 100, 4)))
print("Dropoff before pickup: {} | {}%".format(drop_off_before_pickups, round(drop_off_before_pickups / rows_scanned * 100, 4)))

print("Largest batch MiB:", round(largest_batch_bytes / 1024**2, 2))
print("Scan seconds:", round(perf_counter() - started, 2))