SELECT
    log_comment AS query_variant,
    count(*) AS measured_runs,
    quantileExact(0.5)(query_duration_ms) AS median_ms,
    quantileExact(0.5)(read_rows) AS median_read_rows,
    round(
        quantileExact(0.5)(read_bytes) / 1048576,
        3
    ) AS median_read_mib,
    round(
        max(memory_usage) / 1048576,
        3
    ) AS max_query_memory_mib
FROM system.query_log
WHERE type = 'QueryFinish'
  AND is_initial_query = 1
  AND startsWith(
      query_id,
      concat({benchmark_id:String}, '_')
  )
  AND NOT endsWith(query_id, '_0')
GROUP BY log_comment
ORDER BY log_comment;