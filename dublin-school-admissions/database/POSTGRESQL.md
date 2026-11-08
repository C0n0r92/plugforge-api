# PostgreSQL migration compatibility

Core identifiers are stable TEXT keys, school rolls remain TEXT (leading zeroes matter), numeric counts are INTEGER, and dates/academic years/capture identifiers are deliberately different fields. Core DDL uses ordinary normalized tables, explicit foreign keys and indexes; no SQLite rowid is part of the public identity model.

For PostgreSQL: remove PRAGMA statements; choose TIMESTAMPTZ for actual instant fields, DATE for known full dates, and retain TEXT+precision for year-only/source-text dates. Optionally convert payload/metadata JSON TEXT to JSONB, and flags to BOOLEAN. Use ON CONFLICT DO NOTHING/upserts instead of INSERT OR IGNORE/REPLACE, GREATEST instead of SQLite scalar MAX, and STRING_AGG instead of GROUP_CONCAT. Rewrite view GROUP BY lists to include the selected joined nonaggregates (SQLite allows a looser form), retaining window-function ranking. Use psycopg parameter binding instead of SQLite question-mark parameters. Do not weaken source-payload partitioning, denominator checks, null/zero rules or explicit cohort/year flags during migration.

No live PostgreSQL server was created or tested. This is practical portability guidance, not a claim the SQLite scripts are drop-in PostgreSQL migrations. Geography tables can later adopt PostGIS with versioned sourced boundaries; school coordinate points are not catchments.
