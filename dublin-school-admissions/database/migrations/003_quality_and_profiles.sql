CREATE VIEW IF NOT EXISTS v_school_profile AS
 SELECT s.roll,s.name,s.roster_status,s.geographic_scope,s.website_url,
 MAX(CASE WHEN m.attribute='ethos' THEN m.value_text END) AS ethos,
 MAX(CASE WHEN m.attribute='language' THEN m.value_text END) AS language,
 MAX(CASE WHEN m.attribute='gender' THEN m.value_text END) AS gender,
 MAX(CASE WHEN m.attribute='patronage' THEN m.value_text END) AS patronage,
 MAX(CASE WHEN m.attribute='school_type' THEN m.value_text END) AS school_type
 FROM school s LEFT JOIN school_metadata m ON m.roll=s.roll GROUP BY s.roll;
CREATE VIEW IF NOT EXISTS v_revision_conflicts AS
 SELECT p.roll,p.academic_year,p.cohort_id,g.phase,g.table_scope,o.metric_code,COUNT(DISTINCT n.document_id) AS document_versions,COUNT(DISTINCT o.value_integer) AS different_values,
 MIN(o.value_integer) AS smallest_source_assertion,MAX(o.value_integer) AS largest_source_assertion
 FROM observation o JOIN observation_group g ON g.group_id=o.group_id JOIN school_period p ON p.period_id=g.period_id JOIN notice n ON n.notice_id=g.notice_id
 WHERE o.value_status='observed'
 GROUP BY p.roll,p.academic_year,p.cohort_id,g.phase,g.table_scope,o.metric_code HAVING COUNT(DISTINCT o.value_integer)>1;
CREATE VIEW IF NOT EXISTS v_preferred_with_lineage_quality AS
 SELECT f.*,CASE WHEN EXISTS(SELECT 1 FROM v_revision_conflicts x WHERE x.roll=f.roll AND x.academic_year=f.academic_year AND x.cohort_id=f.cohort_id AND x.phase=f.phase AND x.table_scope=f.table_scope) THEN 1 ELSE 0 END AS cross_edition_conflict,
 (SELECT GROUP_CONCAT(DISTINCT ds.source_id) FROM document_source ds WHERE ds.document_id=f.document_id) AS source_ids,
 (SELECT GROUP_CONCAT(DISTINCT gl.raw_id) FROM group_lineage gl WHERE gl.group_id=f.group_id) AS raw_lineage_ids
 FROM v_preferred_comparable f;
