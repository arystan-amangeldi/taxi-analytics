SELECT
    location_id,
    borough,
    zone AS zone_name,
    service_zone
FROM {{ source('raw', 'taxi_zones') }}