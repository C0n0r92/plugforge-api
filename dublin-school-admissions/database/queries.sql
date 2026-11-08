-- 1. Edition-specific, exact period/cohort comparisons; denominator gates are in the view.
SELECT roll,name,academic_year,cohort,phase,places,applications,offers,acceptances,
 waiting_list_names_placed,applications_per_place,offers_per_application,
 acceptances_per_offer,waiting_list_names_per_place,complete_five_metric_funnel,
 explicitly_dated,cohort_matched,cross_edition_conflict,group_id,source_ids,raw_lineage_ids
FROM v_preferred_with_lineage_quality
WHERE comparable=1 AND phase='retrospective' AND applications_per_place IS NOT NULL
ORDER BY roll,academic_year,cohort;
-- Counts are application records, NOT unique children, unmet demand or school quality/rank.

-- 2. Consecutive-year deltas only. Never jump over missing years.
SELECT roll,academic_year,cohort,applications,previous_applications,applications_delta,
 places,previous_places,places_delta,group_id
FROM v_year_on_year WHERE applications_delta IS NOT NULL ORDER BY roll,academic_year;

-- 3. Explicit waiting-list offer/acceptance events, not differences inferred from other rows.
SELECT p.roll,p.academic_year,c.source_label,g.table_scope,o.metric_code,o.value_integer,
 o.definition_qualifier,o.as_of,e.page,e.excerpt,e.source_payload_sha256,s.original_url
FROM observation o JOIN observation_group g ON g.group_id=o.group_id
JOIN school_period p ON p.period_id=g.period_id JOIN cohort c ON c.cohort_id=p.cohort_id
JOIN observation_evidence oe ON oe.observation_id=o.observation_id
JOIN evidence e ON e.evidence_id=oe.evidence_id LEFT JOIN source s ON s.source_id=e.source_id
WHERE o.metric_code IN ('waiting_list_offers','waiting_list_acceptances','waiting_list_actual_admissions')
 AND o.value_status='observed' AND e.verified_excerpt=1;

-- 4. Exact residual work, by stage/cause. Candidate captures are not verified notices.
SELECT stage,status,COUNT(*) AS tasks FROM work_queue GROUP BY stage,status ORDER BY stage,status;
SELECT roll,method,status,exact_status,attempted_at,coverage_limit FROM collection_attempt WHERE status NOT IN ('attempted_success','index_search_complete');

-- 5. Nearby-school analysis INPUTS: illustrative bounding box around a supplied point.
-- Replace parameters with a real user-chosen bounding box. This is not a radius, catchment,
-- admission-eligibility inference or evidence of household demand. Coordinates retain provenance/asof.
SELECT roll,name,latitude,longitude,address,as_of,source_id,boundary_caveat
FROM v_school_coordinates WHERE latitude BETWEEN :min_lat AND :max_lat AND longitude BETWEEN :min_lon AND :max_lon;

-- 6. All mutually conflicting source versions remain inspectable, including non-preferred rows.
SELECT * FROM v_revision_conflicts ORDER BY roll,academic_year,metric_code;
SELECT * FROM import_reconciliation ORDER BY release_id,dataset;
