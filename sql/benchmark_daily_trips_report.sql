SELECT
    date_day,
    sum(trip_count) AS trip_count
FROM reporting.mart_daily_borough
WHERE date_day >= toDate('2024-01-01')
  AND date_day < toDate('2024-04-01')
GROUP BY date_day
ORDER BY date_day
SETTINGS
    max_threads = 2,
    use_query_cache = 0,
    log_queries = 1,
    log_queries_probability = 1,
    log_queries_min_query_duration_ms = 0,
    log_comment = 'day7_report';