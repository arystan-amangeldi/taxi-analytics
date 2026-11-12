SELECT
    pickup_date AS date_day,
    count(*) AS trip_count
FROM analytics.fct_trips
WHERE pickup_date >= toDate('2024-01-01')
  AND pickup_date < toDate('2024-04-01')
GROUP BY pickup_date
ORDER BY date_day
SETTINGS
    max_threads = 2,
    use_query_cache = 0,
    log_queries = 1,
    log_queries_probability = 1,
    log_queries_min_query_duration_ms = 0,
    log_comment = 'day7_fact';