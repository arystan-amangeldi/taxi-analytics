SELECT
    source_file,
    source_row_number,
    pickup_location_id
FROM {{ ref('fct_trips') }}
WHERE pickup_location_id IS NULL
   OR pickup_location_id NOT IN (
       SELECT location_id
       FROM {{ ref('dim_zones') }}
   )