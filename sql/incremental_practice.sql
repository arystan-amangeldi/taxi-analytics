SELECT
    pickup_date,
    COUNT(*) AS trip_count
FROM analytics.fct_trips
WHERE source_file = 'yellow_tripdata_2024-01.parquet'
  AND (
      pickup_date < toDate('2024-01-01')
      OR pickup_date >= toDate('2024-02-01')
  )
GROUP BY pickup_date
ORDER BY pickup_date;