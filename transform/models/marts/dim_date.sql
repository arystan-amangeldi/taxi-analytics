{{ config(order_by='date_day') }}

WITH calendar AS (
    SELECT
        toDate('2024-01-01') + toInt32(number) AS date_day
    FROM numbers(91)
)

SELECT
    date_day,
    toYear(date_day) AS year_number,
    toMonth(date_day) AS month_number,
    toDayOfWeek(date_day) AS weekday_number,
    toDayOfWeek(date_day) IN (6, 7) AS is_weekend
FROM calendar