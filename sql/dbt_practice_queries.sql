SELECT
    ifNull(pickup.borough, 'Unmatched zone') AS pickup_borough,
    ifNull(dropoff.borough, 'Unmatched zone') AS dropoff_borough,
    COUNT(*) AS trip_count

FROM analytics.fct_trips t

LEFT JOIN analytics.dim_zones pickup
    ON t.pickup_location_id = pickup.location_id

LEFT JOIN analytics.dim_zones dropoff
    ON t.dropoff_location_id = dropoff.location_id

GROUP BY
    pickup.borough,
    dropoff.borough

ORDER BY trip_count DESC

SETTINGS join_use_nulls = 1;




SELECT
    borough,

    ROUND(
        SUM(avg_duration_minutes * trips_with_duration)
        / NULLIF(SUM(trips_with_duration), 0),
        6
    ) AS avg_duration_minutes

FROM analytics.mart_daily_borough

WHERE date_day >= toDate('2024-01-01')
  AND date_day < toDate('2024-02-01')

GROUP BY borough
ORDER BY borough;



SELECT
    ifNull(z.borough, 'Unmatched zone') AS borough,
    ROUND(AVG(t.duration_minutes), 6) AS avg_duration_minutes

FROM analytics.fct_trips t

LEFT JOIN analytics.dim_zones z
    ON t.pickup_location_id = z.location_id

WHERE t.pickup_date >= toDate('2024-01-01')
  AND t.pickup_date < toDate('2024-02-01')

GROUP BY z.borough
ORDER BY borough

SETTINGS join_use_nulls = 1;