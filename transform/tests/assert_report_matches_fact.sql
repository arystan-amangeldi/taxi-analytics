WITH expected AS (
    SELECT
        COUNT(*) AS trip_count,
        SUM(fare_usd) AS fare
    FROM {{ ref('fct_trips') }}
    WHERE pickup_date >= toDate('2024-01-01')
      AND pickup_date < toDate('2024-04-01')
),

reported AS (
    SELECT
        SUM(trip_count) AS trip_count,
        SUM(total_fare_usd) AS fare
    FROM {{ ref('mart_daily_borough') }}
)

SELECT
    e.trip_count AS expected_rows,
    r.trip_count AS reported_rows,
    e.fare AS expected_fare,
    r.fare AS reported_fare

FROM expected e
CROSS JOIN reported r

WHERE e.trip_count != r.trip_count
   OR abs(e.fare - r.fare) > 0.01