WITH source_totals AS (
    SELECT
        COUNT(*) AS trip_count,
        SUM(fare_amount) AS fare
    FROM {{ source('raw', 'trips') }}
),

fact_totals AS (
    SELECT
        COUNT(*) AS trip_count,
        SUM(fare_usd) AS fare
    FROM {{ ref('fct_trips') }}
)

SELECT
    s.trip_count AS source_rows,
    f.trip_count AS fact_rows,
    s.fare AS source_fare,
    f.fare AS fact_fare

FROM source_totals s
CROSS JOIN fact_totals f

WHERE s.trip_count != f.trip_count
   OR abs(s.fare - f.fare) > 0.01