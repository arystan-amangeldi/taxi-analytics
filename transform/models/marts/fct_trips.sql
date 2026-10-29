{{ config(order_by='source_file') }}

SELECT
    t.*,

    CASE
        WHEN t.dropoff_at >= t.pickup_at
        THEN dateDiff('second', t.pickup_at, t.dropoff_at) / 60.0
        ELSE NULL
    END AS duration_minutes,

    w.temperature_c,
    w.precipitation_mm,
    w.weather_date IS NOT NULL AS has_weather

FROM {{ ref('stg_trips') }} t

LEFT JOIN {{ ref('stg_weather') }} w
    ON t.pickup_date = w.weather_date