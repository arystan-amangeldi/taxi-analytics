SELECT
    source_file,
    COUNT(*) AS trip_count,
    ROUND(SUM(fare_amount), 2) AS fare_usd,
    ROUND(SUM(trip_distance), 2) AS distance_miles
FROM raw.trips
GROUP BY source_file
ORDER BY source_file;