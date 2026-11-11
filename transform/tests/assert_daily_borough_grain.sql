SELECT
    date_day,
    borough,
    count(*) AS rows_at_grain
FROM {{ ref('mart_daily_borough') }}
GROUP BY date_day, borough
HAVING count(*) > 1