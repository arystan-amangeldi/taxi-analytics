-- Exercise A: Trips by pickup borough
SELECT z.borough, COUNT(*) as trip_count
FROM raw.trips t
JOIN raw.taxi_zones z ON t.PULocationID = z.location_id
GROUP BY z.borough
ORDER BY trip_count DESC;

-- Exercise B: Join cardinality and unmatched zones
SELECT COUNT(*) AS trips_before_join
FROM raw.trips;

SELECT
    COUNT(*) AS rows_after_join,
    COUNT(*) - COUNT(z.location_id) AS unmatched_trips
FROM raw.trips t
LEFT JOIN raw.taxi_zones z
    ON t.PULocationID = z.location_id
SETTINGS join_use_nulls = 1;

-- Harder challenge: Trips with daily weather
SELECT
    COUNT(*) AS total_trips,
    COUNT(w.weather_date) AS trips_with_weather,
    COUNT(*) - COUNT(w.weather_date) AS trips_without_weather
FROM raw.trips t
LEFT JOIN raw.weather_daily w
    ON toDateOrNull(substring(t.tpep_pickup_datetime, 1, 10))
       = w.weather_date
SETTINGS join_use_nulls = 1;