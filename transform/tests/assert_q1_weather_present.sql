SELECT
    source_file,
    source_row_number,
    pickup_date
FROM {{ ref('fct_trips') }}
WHERE pickup_date >= toDate('2024-01-01')
  AND pickup_date < toDate('2024-04-01')
  AND has_weather = 0