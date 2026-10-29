SELECT
    weather_date,
    temperature_c,
    precipitation_mm
FROM {{ source('raw', 'weather_daily') }}