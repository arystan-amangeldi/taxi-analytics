-- These anomaly counts can overlap.
SELECT
    source_file,
    countIf(fare_usd < 0) AS negative_fares,
    countIf(distance_miles = 0) AS zero_distance,
    countIf(dropoff_at < pickup_at) AS invalid_time_order,
    countIf(
        pickup_at IS NULL OR dropoff_at IS NULL
    ) AS missing_timestamp
FROM analytics.fct_trips
GROUP BY source_file
ORDER BY source_file;


-- These categories are mutually exclusive.
SELECT
    multiIf(
        pickup_date IS NULL,
        'Missing pickup date',

        pickup_date < toDate('2024-01-01')
            OR pickup_date >= toDate('2024-04-01'),
        'Outside Q1',

        'Included in Q1'
    ) AS reporting_scope,
    count(*) AS trips
FROM analytics.fct_trips
GROUP BY reporting_scope
ORDER BY reporting_scope;