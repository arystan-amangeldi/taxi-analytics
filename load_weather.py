import argparse
import calendar
import json
import math
import os
from datetime import date, timedelta
from pathlib import Path

import clickhouse_connect


RAW = Path(__file__).resolve().parent / "data" / "raw"


def read_month(month):
    start = date.fromisoformat(f"{month}-01")
    days = calendar.monthrange(start.year, start.month)[1]

    path = RAW / f"weather_nyc_{start:%Y-%m}.json"

    with path.open(encoding="utf-8") as source:
        weather = json.load(source)

    if weather["timezone"] != "America/New_York":
        raise ValueError("Weather timezone must be America/New_York")

    units = weather["daily_units"]

    if (
        units["temperature_2m_mean"] != "°C"
        or units["precipitation_sum"] != "mm"
    ):
        raise ValueError("Expected weather in Celsius and millimetres")

    daily = weather["daily"]

    dates = [date.fromisoformat(value) for value in daily["time"]]
    expected_dates = [
        start + timedelta(days=i)
        for i in range(days)
    ]

    if dates != expected_dates:
        raise ValueError(f"Incorrect date coverage for {month}")

    rows = []

    for day, temperature, rain in zip(
        dates,
        daily["temperature_2m_mean"],
        daily["precipitation_sum"],
        strict=True,
    ):
        if temperature is None or rain is None:
            raise ValueError(f"Missing weather on {day}")

        if (
            not math.isfinite(temperature)
            or not math.isfinite(rain)
            or rain < 0
        ):
            raise ValueError(f"Invalid weather on {day}")

        rows.append((day, temperature, rain))

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", nargs="+", required=True)
    args = parser.parse_args()

    if len(args.months) != len(set(args.months)):
        raise ValueError("Do not repeat a month")

    rows = []

    for month in args.months:
        rows.extend(read_month(month))

    client = clickhouse_connect.get_client(
        host="127.0.0.1",
        port=8123,
        username="taxi",
        password=os.environ["TAXI_CH_PASSWORD"],
    )

    try:
        client.command("TRUNCATE TABLE raw.weather_daily_incoming")

        client.insert(
            "raw.weather_daily_incoming",
            rows,
            column_names=[
                "weather_date",
                "temperature_c",
                "precipitation_mm",
            ],
        )

        count = client.query(
            "SELECT count() FROM raw.weather_daily_incoming"
        ).first_row[0]

        if count != len(rows):
            raise ValueError("Weather source and target counts differ")

        client.command(
            "EXCHANGE TABLES "
            "raw.weather_daily AND raw.weather_daily_incoming"
        )
    finally:
        client.close()

    print(f"Published {len(rows)} weather days")


if __name__ == "__main__":
    main()