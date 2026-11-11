WITH source_counts AS (
    SELECT
        source_file,
        count(*) AS source_rows
    FROM {{ source('raw', 'trips') }}
    GROUP BY source_file
),

fact_counts AS (
    SELECT
        source_file,
        count(*) AS fact_rows
    FROM {{ ref('fct_trips') }}
    GROUP BY source_file
)

SELECT
    coalesce(s.source_file, f.source_file) AS source_file,
    s.source_rows,
    f.fact_rows
FROM source_counts s
FULL OUTER JOIN fact_counts f
    ON s.source_file = f.source_file
WHERE coalesce(s.source_rows, 0) != coalesce(f.fact_rows, 0)