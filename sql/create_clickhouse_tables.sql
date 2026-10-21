CREATE DATABASE IF NOT EXISTS raw ENGINE = Atomic;

CREATE TABLE IF NOT EXISTS raw.taxi_zones (
    location_id Int32,
    borough String,
    zone String,
    service_zone Nullable(String)
)
ENGINE = MergeTree
ORDER BY location_id;

CREATE TABLE IF NOT EXISTS raw.weather_daily (
    weather_date Date,
    temperature_c Float64,
    precipitation_mm Float64
)
ENGINE = MergeTree
ORDER BY weather_date;

CREATE TABLE IF NOT EXISTS raw.trips (
    tpep_pickup_datetime Nullable(String),
    tpep_dropoff_datetime Nullable(String),
    PULocationID Nullable(Int32),
    DOLocationID Nullable(Int32),
    trip_distance Nullable(Float64),
    fare_amount Nullable(Float64),
    total_amount Nullable(Float64),
    payment_type Nullable(Int64),
    source_file LowCardinality(String),
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY source_file;

CREATE TABLE IF NOT EXISTS raw.taxi_zones_incoming
AS raw.taxi_zones;

CREATE TABLE IF NOT EXISTS raw.weather_daily_incoming
AS raw.weather_daily;

CREATE TABLE IF NOT EXISTS raw.trips_incoming
AS raw.trips;