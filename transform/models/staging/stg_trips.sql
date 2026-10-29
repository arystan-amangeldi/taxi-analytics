WITH typed AS (
    SELECT
        parseDateTime64BestEffortOrNull(
            tpep_pickup_datetime, 6, 'America/New_York'
        ) AS pickup_at,

        parseDateTime64BestEffortOrNull(
            tpep_dropoff_datetime, 6, 'America/New_York'
        ) AS dropoff_at,

        PULocationID AS pickup_location_id,
        DOLocationID AS dropoff_location_id,
        trip_distance AS distance_miles,
        fare_amount AS fare_usd,
        total_amount AS total_amount_usd,
        payment_type,
        source_file,
        loaded_at

    FROM {{ source('raw', 'trips') }}
)

SELECT
    *,
    toDate(pickup_at) AS pickup_date
FROM typed