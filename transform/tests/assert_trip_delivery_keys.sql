SELECT source_file
FROM {{ source('raw', 'trips') }}
GROUP BY source_file
HAVING
    COUNT(*) != uniqExact(source_row_number)
    OR MIN(source_row_number) != 1
    OR MAX(source_row_number) != COUNT(*)
    OR uniqExact(source_sha256) != 1
    OR countIf(source_sha256 = '') > 0