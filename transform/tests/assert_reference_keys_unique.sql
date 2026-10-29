SELECT
    'zones' AS dataset,
    toString(location_id) AS key_value
FROM {{ ref('dim_zones') }}
GROUP BY location_id
HAVING COUNT(*) > 1

UNION ALL

SELECT
    'weather' AS dataset,
    toString(weather_date) AS key_value
FROM {{ ref('stg_weather') }}
GROUP BY weather_date
HAVING COUNT(*) > 1

UNION ALL

SELECT
    'calendar' AS dataset,
    toString(date_day) AS key_value
FROM {{ ref('dim_date') }}
GROUP BY date_day
HAVING COUNT(*) > 1