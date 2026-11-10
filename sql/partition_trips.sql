CREATE TABLE raw.trips_partitioned AS raw.trips
ENGINE = MergeTree
PARTITION BY source_file
ORDER BY source_file;

INSERT INTO raw.trips_partitioned
SELECT *
FROM raw.trips;

SELECT throwIf(
    (SELECT COUNT(*) FROM raw.trips)
        !=
    (SELECT COUNT(*) FROM raw.trips_partitioned),
    'Migration row counts differ'
);

SELECT throwIf(
    abs(
        (SELECT SUM(fare_amount) FROM raw.trips)
        -
        (SELECT SUM(fare_amount) FROM raw.trips_partitioned)
    ) > 0.01,
    'Migration fare totals differ'
);

EXCHANGE TABLES raw.trips AND raw.trips_partitioned;

ALTER TABLE raw.trips
    ADD COLUMN source_sha256 LowCardinality(String),
    ADD COLUMN source_row_number UInt64;

CREATE TABLE raw.trips_work AS raw.trips;