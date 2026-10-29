{{ config(order_by=['date_day', 'borough']) }}

SELECT
    d.date_day,
    ifNull(z.borough, 'Unmatched zone') AS borough,
    d.is_weekend,
    t.temperature_c,
    t.precipitation_mm,

    COUNT(*) AS trip_count,
    countIf(t.fare_usd < 0) AS negative_fare_trip_count,
    SUM(t.fare_usd) AS total_fare_usd,
    COUNT(t.duration_minutes) AS trips_with_duration,
    AVG(t.duration_minutes) AS avg_duration_minutes

FROM {{ ref('fct_trips') }} t

JOIN {{ ref('dim_date') }} d
    ON t.pickup_date = d.date_day

LEFT JOIN {{ ref('dim_zones') }} z
    ON t.pickup_location_id = z.location_id

GROUP BY
    d.date_day,
    z.borough,
    d.is_weekend,
    t.temperature_c,
    t.precipitation_mm