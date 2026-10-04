from pathlib import Path

import requests


def main():
    raw = Path(__file__).resolve().parent / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "America/New_York",
    }

    destination = raw / "weather_nyc_2024-01.json"
    temporary = destination.with_suffix(".json.part")

    with requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params=params,
        timeout=(10, 60),
    ) as response:
        response.raise_for_status()
        response.json()
        temporary.write_bytes(response.content)

    temporary.replace(destination)
    print(f"Saved {destination.name}")


if __name__ == "__main__":
    main()