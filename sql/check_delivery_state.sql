SELECT
    source_file,
    count(*) AS trip_rows,
    uniqExact(source_sha256) AS checksum_versions,
    min(source_sha256) AS source_checksum,
    round(sum(fare_amount), 2) AS recorded_fares_usd
FROM raw.trips
GROUP BY source_file
ORDER BY source_file;


SELECT
    count(*) AS reporting_rows,
    sum(trip_count) AS represented_trips,
    round(sum(total_fare_usd), 2) AS recorded_fares_usd,
    max(published_at) AS published_at_utc
FROM reporting.mart_daily_borough;