from pathlib import Path

import requests


def download_file(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")

    print(f"Downloading {destination.name}")

    with requests.get(url, stream=True, timeout=(10, 60)) as response:
        response.raise_for_status()

        with temporary.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)

    temporary.replace(destination)
    print(f"Saved {destination.stat().st_size:,} bytes")


def main():
    raw = Path(__file__).resolve().parent / "data" / "raw"
    base_url = "https://d37ci6vzurychx.cloudfront.net"

    download_file(
        f"{base_url}/trip-data/yellow_tripdata_2024-01.parquet",
        raw / "yellow_tripdata_2024-01.parquet",
    )

    download_file(
        f"{base_url}/misc/taxi_zone_lookup.csv",
        raw / "taxi_zone_lookup.csv",
    )


if __name__ == "__main__":
    main()