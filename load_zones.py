import csv
import os
from pathlib import Path

import psycopg


def main():
    path = (
        Path(__file__).resolve().parent
        / "data"
        / "raw"
        / "taxi_zone_lookup.csv"
    )

    with path.open(encoding="utf-8", newline="") as source:
        zones = list(csv.DictReader(source))

    if not zones:
        raise ValueError("Zone source is empty")

    with psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="taxi",
        user="taxi",
        password=os.environ["TAXI_PG_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE reference.taxi_zones")

            with cursor.copy(
                """
                COPY reference.taxi_zones
                    (location_id, borough, zone, service_zone)
                FROM STDIN
                """
            ) as copy:
                for zone in zones:
                    copy.write_row(
                        (
                            int(zone["LocationID"]),
                            zone["Borough"],
                            zone["Zone"],
                            zone["service_zone"],
                        )
                    )

            loaded = cursor.execute(
                "SELECT count(*) FROM reference.taxi_zones"
            ).fetchone()[0]

            if loaded != len(zones):
                raise ValueError("Zone source and target counts differ")

    print(f"Committed {loaded:,} zones to PostgreSQL")


if __name__ == "__main__":
    main()