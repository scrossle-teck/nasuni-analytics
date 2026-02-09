-- DuckDB SQL queries for nasuni-analytics (works with Parquet produced by ingest_duckdb.py)
-- Usage: run in duckdb CLI or via duckdb.query() in Python against the parquet files directory.

-- Replace the path below with your run parquet directory (e.g. out/parquet/run-20260206-160959/*.parquet)
-- 1) Top identities with high permissions (by distinct folder count)
SELECT
  ace_name,
  COUNT(DISTINCT folder_path) AS folders_with_high_perms
FROM read_parquet('out/parquet/run-20260206-160959/*.parquet')
WHERE (
  (ace_mask IS NOT NULL AND LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%full%')
  OR (ace_mask IS NOT NULL AND LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%modify%')
  OR (ace_mask IS NOT NULL AND LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%write%')
  OR TRY_CAST(ace_mask AS BIGINT) IS NOT NULL AND TRY_CAST(ace_mask AS BIGINT) <> 0
)
GROUP BY ace_name
ORDER BY folders_with_high_perms DESC
LIMIT 200;

-- 2) ACE counts by appliance (useful to find appliances with many ACEs)
SELECT
  COALESCE(appliance_hostname, 'unknown') AS appliance_hostname,
  COUNT(*) AS ace_count
FROM read_parquet('out/parquet/run-20260206-160959/*.parquet')
GROUP BY appliance_hostname
ORDER BY ace_count DESC
LIMIT 200;

-- 3) Inherited exposures: list folders where inherited ACEs grant high permissions
SELECT folder_path, ace_name, ace_mask, ace_inherited
FROM read_parquet('out/parquet/run-20260206-160959/*.parquet')
WHERE ace_inherited = TRUE
  AND (
    LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%full%'
    OR LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%modify%'
    OR LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%write%'
    OR (TRY_CAST(ace_mask AS BIGINT) IS NOT NULL AND TRY_CAST(ace_mask AS BIGINT) <> 0)
  )
ORDER BY folder_path
LIMIT 1000;

-- 4) Folders with >1 distinct fingerprint (fast change-detection)
SELECT folder_path, COUNT(DISTINCT fingerprint_sha256) AS fingerprint_variants
FROM read_parquet('out/parquet/run-20260206-160959/*.parquet')
GROUP BY folder_path
HAVING COUNT(DISTINCT fingerprint_sha256) > 1
ORDER BY fingerprint_variants DESC
LIMIT 200;

-- 5) Owners without an obvious admin ACE (heuristic: owner present but no ace with 'admin' or 'administrators')
WITH owners AS (
  SELECT folder_path, owner
  FROM read_parquet('out/parquet/run-20260206-160959/*.parquet')
  WHERE owner IS NOT NULL
  GROUP BY folder_path, owner
)
SELECT o.folder_path, o.owner
FROM owners o
LEFT JOIN (
  SELECT DISTINCT folder_path
  FROM read_parquet('out/parquet/run-20260206-160959/*.parquet')
  WHERE LOWER(COALESCE(ace_name, '')) LIKE '%admin%'
) a ON a.folder_path = o.folder_path
WHERE a.folder_path IS NULL
LIMIT 200;
