-- Independent fact-table total for the reporting scope.
SELECT
    count(*) AS total_trips,
    round(sum(fare_usd), 2) AS recorded_fares_usd
FROM analytics.fct_trips
WHERE pickup_date >= toDate('2024-01-01')
  AND pickup_date < toDate('2024-04-01');


-- Compare against the published aggregate.
SELECT
    sum(trip_count) AS total_trips,
    round(sum(total_fare_usd), 2) AS recorded_fares_usd
FROM reporting.mart_daily_borough;


-- Expected points for the daily line chart.
SELECT
    pickup_date AS date_day,
    count(*) AS total_trips
FROM analytics.fct_trips
WHERE pickup_date >= toDate('2024-01-01')
  AND pickup_date < toDate('2024-04-01')
GROUP BY pickup_date
ORDER BY pickup_date;


-- Independent borough totals.
SELECT
    ifNull(z.borough, 'Unmatched zone') AS borough,
    round(sum(t.fare_usd), 2) AS recorded_fares_usd
FROM analytics.fct_trips t
LEFT JOIN analytics.dim_zones z
    ON t.pickup_location_id = z.location_id
WHERE t.pickup_date >= toDate('2024-01-01')
  AND t.pickup_date < toDate('2024-04-01')
GROUP BY borough
ORDER BY recorded_fares_usd DESC
SETTINGS join_use_nulls = 1;