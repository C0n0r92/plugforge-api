DROP VIEW IF EXISTS v_year_on_year;
DROP VIEW IF EXISTS v_preferred_comparable;
DROP VIEW IF EXISTS v_comparison_ratios;
DROP VIEW IF EXISTS v_group_funnel;
DROP VIEW IF EXISTS v_metric_consensus;
CREATE VIEW v_metric_consensus AS
 SELECT o.group_id,o.metric_code,
 CASE WHEN COUNT(DISTINCT CASE WHEN o.value_status='observed' THEN o.value_integer END)=1 THEN MAX(o.value_integer) END AS value_integer,
 COUNT(DISTINCT CASE WHEN o.value_status='observed' THEN o.value_integer END) AS distinct_values,
 MAX(CASE WHEN o.value_status='observed' AND EXISTS(SELECT 1 FROM observation_evidence oe JOIN evidence e ON e.evidence_id=oe.evidence_id WHERE oe.observation_id=o.observation_id AND e.verified_excerpt=1 AND e.source_payload_sha256 IS NOT NULL) THEN 1 ELSE 0 END) AS has_verified_field_evidence,
 GROUP_CONCAT(DISTINCT o.value_status) AS statuses
 FROM observation o GROUP BY o.group_id,o.metric_code;
CREATE VIEW v_group_funnel AS
 SELECT g.group_id,p.roll,s.name,p.academic_year,p.year_start,p.cohort_id,c.source_label AS cohort,c.intake_kind,c.special_needs_label,g.notice_id,n.document_id,d.payload_sha256,g.phase,g.table_scope,g.as_of,g.year_status,g.cohort_matched,g.quality,g.preferred_source_rank,g.review_notes,g.definition_era,
 MAX(CASE WHEN m.metric_code='places' AND m.has_verified_field_evidence=1 THEN m.value_integer END) AS places,
 MAX(CASE WHEN m.metric_code='applications' AND m.has_verified_field_evidence=1 THEN m.value_integer END) AS applications,
 MAX(CASE WHEN m.metric_code='offers' AND m.has_verified_field_evidence=1 THEN m.value_integer END) AS offers,
 MAX(CASE WHEN m.metric_code='acceptances' AND m.has_verified_field_evidence=1 THEN m.value_integer END) AS acceptances,
 MAX(CASE WHEN m.metric_code='waiting_list_names_placed' AND m.has_verified_field_evidence=1 THEN m.value_integer END) AS waiting_list_names_placed,
 MAX(CASE WHEN m.metric_code='waiting_list_remaining' AND m.has_verified_field_evidence=1 THEN m.value_integer END) AS waiting_list_remaining,
 MAX(CASE WHEN m.metric_code='actual_admissions' AND m.has_verified_field_evidence=1 THEN m.value_integer END) AS actual_admissions,
 MAX(CASE WHEN m.distinct_values>1 THEN 1 ELSE 0 END) AS has_metric_conflict,
 CASE WHEN g.year_status='explicit_source_year' THEN 1 ELSE 0 END AS explicitly_dated,
 CASE WHEN g.year_status='explicit_source_year' AND g.cohort_matched=1 AND MAX(CASE WHEN m.distinct_values>1 THEN 1 ELSE 0 END)=0 AND g.quality<>'user_report_unverified' THEN 1 ELSE 0 END AS comparable,
 COUNT(DISTINCT CASE WHEN m.value_integer IS NOT NULL AND m.has_verified_field_evidence=1 THEN m.metric_code END) AS supported_metric_count
 FROM observation_group g JOIN school_period p ON p.period_id=g.period_id JOIN school s ON s.roll=p.roll JOIN cohort c ON c.cohort_id=p.cohort_id JOIN notice n ON n.notice_id=g.notice_id JOIN document d ON d.document_id=n.document_id LEFT JOIN v_metric_consensus m ON m.group_id=g.group_id
 GROUP BY g.group_id;
CREATE VIEW v_comparison_ratios AS
 SELECT f.*,
 CASE WHEN comparable=1 AND places>0 THEN 1.0*applications/places END AS applications_per_place,
 CASE WHEN comparable=1 AND applications>0 THEN 1.0*offers/applications END AS offers_per_application,
 CASE WHEN comparable=1 AND offers>0 THEN 1.0*acceptances/offers END AS acceptances_per_offer,
 CASE WHEN comparable=1 AND places>0 THEN 1.0*waiting_list_names_placed/places END AS waiting_list_names_per_place,
 CASE WHEN comparable=1 AND places IS NOT NULL AND applications IS NOT NULL AND offers IS NOT NULL AND acceptances IS NOT NULL AND waiting_list_names_placed IS NOT NULL THEN 1 ELSE 0 END AS complete_five_metric_funnel,
 ROW_NUMBER() OVER(PARTITION BY roll,academic_year,cohort_id,phase,table_scope ORDER BY comparable DESC,explicitly_dated DESC,has_metric_conflict ASC,CASE quality WHEN 'high' THEN 3 WHEN 'medium' THEN 2 WHEN 'low' THEN 1 ELSE 0 END DESC,preferred_source_rank DESC,supported_metric_count DESC,group_id ASC) AS deterministic_preference_rank
 FROM v_group_funnel f;
CREATE VIEW v_preferred_comparable AS SELECT * FROM v_comparison_ratios WHERE deterministic_preference_rank=1;
CREATE VIEW v_year_on_year AS
 WITH y AS (SELECT *,LAG(year_start) OVER w AS previous_year_start,LAG(applications) OVER w AS previous_applications,LAG(places) OVER w AS previous_places FROM v_preferred_comparable WHERE comparable=1 AND phase='retrospective' WINDOW w AS(PARTITION BY roll,cohort_id,phase,table_scope ORDER BY year_start))
 SELECT *,CASE WHEN year_start=previous_year_start+1 THEN applications-previous_applications END AS applications_delta,CASE WHEN year_start=previous_year_start+1 THEN places-previous_places END AS places_delta FROM y;
CREATE VIEW IF NOT EXISTS v_school_coordinates AS SELECT s.roll,s.name,l.* FROM school s JOIN school_location l ON l.location_id=(SELECT x.location_id FROM school_location x WHERE x.roll=s.roll AND x.latitude IS NOT NULL AND x.longitude IS NOT NULL ORDER BY x.as_of DESC,x.location_id LIMIT 1);
CREATE VIEW IF NOT EXISTS v_school_year_coverage AS SELECT s.roll,s.name,p.academic_year,COUNT(DISTINCT g.group_id) AS observation_groups,MAX(CASE WHEN g.year_status='explicit_source_year' THEN 1 ELSE 0 END) AS any_explicit_year,COUNT(DISTINCT CASE WHEN o.value_status='observed' THEN o.metric_code END) AS metric_types FROM school s LEFT JOIN school_period p ON p.roll=s.roll LEFT JOIN observation_group g ON g.period_id=p.period_id LEFT JOIN observation o ON o.group_id=g.group_id GROUP BY s.roll,p.academic_year;
