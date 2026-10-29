{{ config(order_by='location_id') }}

SELECT
    location_id,
    borough,
    zone_name,
    service_zone
FROM {{ ref('stg_zones') }}