import argparse
import calendar
import json
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq
import requests


RAW = Path(__file__).resolve().parent / "data" / "raw"


def download(url, path, params=None):
    if path.exists():
        print(f"KEEP {path.name}")
        return

    temporary = path.with_suffix(path.suffix + ".part")

    with requests.get(
        url,
        params=params,
        stream=True,
        timeout=(10, 120),
    ) as response:
        response.raise_for_status()

        with temporary.open("wb") as destination:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                destination.write(chunk)

    if path.suffix == ".parquet":
        rows = pq.ParquetFile(temporary).metadata.num_rows

        if rows == 0:
            raise ValueError("Downloaded an empty trip file")

        print(f"Downloaded {rows:,} trip rows")
    else:
        with temporary.open(encoding="utf-8") as source:
            json.load(source)

    temporary.replace(path)
    print(f"SAVED {path.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM")
    args = parser.parse_args()

    start = date.fromisoformat(f"{args.month}-01")
    end = start.replace(
        day=calendar.monthrange(start.year, start.month)[1]
    )

    RAW.mkdir(parents=True, exist_ok=True)

    name = f"yellow_tripdata_{start:%Y-%m}.parquet"

    download(
        f"https://d37ci6vzurychx.cloudfront.net/trip-data/{name}",
        RAW / name,
    )

    download(
        "https://archive-api.open-meteo.com/v1/archive",
        RAW / f"weather_nyc_{start:%Y-%m}.json",
        params={
            "latitude": 40.7128,
            "longitude": -74.0060,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "America/New_York",
            "temperature_unit": "celsius",
            "precipitation_unit": "mm",
        },
    )


if __name__ == "__main__":
    main()