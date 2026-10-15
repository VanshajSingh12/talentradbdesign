from pathlib import Path

DOC = Path("ddl/99_documentation.sql")
text = DOC.read_text(errors="replace")

table_name = "schema_map_milestone_order"

# If the map already exists, append REFRESH/extension rows only, not a duplicate schema.
if "CREATE TABLE schema_map_milestone_order" in text and "SECTION: MILESTONE-ORDER CONTEXT MENU — SUPPLEMENTAL" not in text:
    print(f"existing {table_name} found; appending supplemental rows only")
    supplemental = r"""

-- ============================================================================
-- SECTION: MILESTONE-ORDER CONTEXT MENU â€” SUPPLEMENTAL / NEW-DIFFERENTIATOR ROWS
-- ============================================================================
-- This section refreshes the milestone-order entities-first context menu with the
-- new unique differentiators added from the team side. The base schema_map_milestone_order
-- table remains the same; these rows extend it with the competitive differentiators.
-- Read order for implementation: Domain table -> extension table -> transaction table -> audit/history.

INSERT INTO schema_map_milestone_order (row_order, milestone, module, entity, relationship, key_columns, primary_kpi_or_rule, quiet_comment) VALUES
-- Milestone 1 (Common): new master differentiators
(201, 'Milestone 1 (Common)', '01_master_data.sql', 'skill_ancestor',
   'skill 1..* skill_ancestor (ancestor); skill 1..* skill_ancestor (descendant)',
   'id PK, ancestor_skill_id FK, descendant_skill_id FK, ancestry_type_code, created_at, created_by',
   'Skill affinity pipeline',
   'Unique: explicit skill ancestry for normalization/merge.'),
(202, 'Milestone 1 (Common)', '01_master_data.sql', 'skill_synonym',
   'skill 1..* skill_synonym',
   'id PK, skill_id FK, synonym_text, language_code (nullable), is_active, created_at, created_by',
   'Multilingual skill matching',
   'Unique: multilingual skill synonyms.'),
(203, 'Milestone 1 (Common)', '01_master_data.sql', 'tag_category',
   'tag_category 1..* tag',
   'id PK, category_code, name, is_active, created_at, created_by',
   'Flexible tagging',
   'Unique master: tag taxonomy for candidates and jobs.'),
(204, 'Milestone 1 (Common)', '01_master_data.sql', 'tag',
   'tag_category 1..* tag; tag 1..* candidate_tag; tag 1..* job_requirement_tag; tag 1..* application_tag',
   'id PK, tag_category_id FK (nullable), name, language_code (nullable), is_active, created_at, created_by',
   'Tagging cross-module',
   'Unique: shared tag master reused by Profile, Jobs, Applications.'),

-- Milestone 2: new profile differentiators
(205, 'Milestone 2 (Candidate Profile)', '02_profile.sql', 'candidate_skill_affinity',
   'candidate_identity 1..* candidate_skill_affinity (one current via partial unique)',
   'id PK, candidate_id FK, snapshot_at, overall_affinity, top_skill_names, top_skill_count, is_current, created_at, created_by, updated_at, updated_by',
   'Unique skill-affinity KPI',
   'Unique: computed skill affinity snapshot.'),
(206, 'Milestone 2 (Candidate Profile)', '02_profile.sql', 'candidate_tag',
   'candidate_identity 1..* candidate_tag; tag 1..* candidate_tag',
   'id PK, candidate_id FK, tag_id FK, created_at, created_by',
   'Unique tagging',
   'Unique: flexible candidate tags.'),

-- Milestone 3: new org differentiators
(207, 'Milestone 3 (Employer / Org)', '05_organisation.sql', 'organisation_industry_classification',
   'employer_organisation 1..* organisation_industry_classification; industry 1..* organisation_industry_classification; reference_code (classification_type) 1..* organisation_industry_classification',
   'id PK, employer_organisation_id FK, industry_id FK, classification_type_code FK, is_primary, created_at, created_by, updated_at, updated_by',
   'Unique multi-industry classification',
   'Unique: an org can carry multiple industry tags.'),
(208, 'Milestone 3 (Employer / Org)', '05_organisation.sql', 'organisation_competitor_intel',
   'employer_organisation 1..* organisation_competitor_intel',
   'id PK, employer_organisation_id FK, source_system_code, external_reference, rating_value, review_count, salary_benchmark_code, refreshed_at, is_active, created_at, created_by, updated_at, updated_by',
   'Unique competitor intel linkage',
   'Unique: ties employer to company-review/salary boundary data (Section 6).'),

-- Milestone 4: new jobs differentiators
(209, 'Milestone 4 (Jobs & Applications)', '03_jobs_applications.sql', 'job_requirement_tag',
   'job_requirement 1..* job_requirement_tag; tag 1..* job_requirement_tag',
   'id PK, job_requirement_id FK, tag_id FK, created_at, created_by',
   'Unique job tagging',
   'Unique: tags on jobs.'),
(210, 'Milestone 4 (Jobs & Applications)', '03_jobs_applications.sql', 'application_tag',
   'application 1..* application_tag; tag 1..* application_tag',
   'id PK, application_id FK, tag_id FK, created_at, created_by',
   'Unique application tagging',
   'Unique: tags on applications.'),
(211, 'Milestone 4 (Jobs & Applications)', '03_jobs_applications.sql', 'application_denial_code',
   'application 1..* application_denial_code; reference_code (stage) 1..* application_denial_code (stage_code); users 1..* application_denial_code (recorded_by)',
   'id PK, application_id FK, stage_code FK, denial_code, reason_text (nullable), recorded_at, recorded_by_user_id (nullable)',
   'Unique denial-code analytics',
   'Unique: structured rejection reason codes.'),

-- Milestone 10: new analytics differentiators
(212, 'Milestone 10 (Analytics)', '11_analytics.sql', 'analytics_fact_skill_affinity',
   'candidate_dim 1..* fact; date_dim 1..* fact',
   'id PK, candidate_id FK, overall_affinity, top_skill_count, date_key, created_at, created_by',
   'Unique skill-affinity KPI',
   'Unique analytics fact for skill affinity.'),
(213, 'Milestone 10 (Analytics)', '11_analytics.sql', 'analytics_fact_application_denial',
   'candidate_dim 1..* fact; job_dim 1..* fact; employer_dim 1..* fact; date_dim 1..* fact',
   'id PK, application_id FK, candidate_id FK, job_requirement_id FK, employer_organisation_id FK, stage_code, denial_code, date_key, created_at, created_by',
   'Unique denial KPI',
   'Unique analytics fact for denial funnel.'),
(214, 'Milestone 10 (Analytics)', '11_analytics.sql', 'analytics_agg_denial_by_stage',
   'analytics_fact_application_denial -> materialized view',
   'month_key, stage_code, denial_code, denial_count, distinct_applications',
   'Unique denial aggregate',
   'Unique: denial aggregate by stage (nightly refresh).'),
(215, 'Milestone 10 (Analytics)', '11_analytics.sql', 'analytics_agg_dashboard_summary',
   'analytics_dim_date / employer_dim / candidate_dim -> aggregate',
   'id PK, dashboard_key, month_key, candidate_signups, job_postings, applications, placements, last_refreshed_at',
   'Tier 3 stretch: dashboard aggregates',
   'Dashboard aggregate.'),

-- Milestone 11: new administration differentiators
(216, 'Milestone 11 (Shared Team Items)', '04_administration.sql', 'password_policy',
   'password_policy 1..* credential_verification (via enforcement)',
   'id PK, policy_code, name, min_length, max_length, require_upper, require_lower, require_digit, require_special, max_age_days, history_count, lockout_after_failures, lockout_minutes, is_active, created_at, created_by, updated_at, updated_by',
   'Unique security differentiator',
   'Unique: platform-wide password policy master.'),
(217, 'Milestone 11 (Shared Team Items)', '04_administration.sql', 'account_security_policy',
   'tenant_account 1..* account_security_policy',
   'id PK, tenant_account_id FK, policy_code, effective_from, effective_to (nullable), is_primary, is_active, created_at, created_by, updated_at, updated_by',
   'Unique security differentiator',
   'Unique: per-account security policy with lockout/session/MFA.'),

-- Milestone 11 wallet rename note
(218, 'Milestone 8 (Subscriptions/Wallet/Payments)', '09_subscriptions.sql', 'wallet_account',
   'tenant_account 1..* wallet_account; wallet_account 1..* wallet_ledger_entry',
   'id PK, tenant_account_id FK, owner_user_id (nullable), currency_code, balance, status_code, created_at, created_by, updated_at, updated_by, deleted_at',
   'Rule Group 10 wallet',
   'Unique: wallet_ account renamed from wallet for strict PG reserved-word safety.'),

-- Milestone 12 Tier 3 stretch differentiators (already listed, but included for completeness)
(219, 'Milestone 12 (Tier 3 stretch)', '12_tier3_stretch.sql', 'salary_benchmark',
   'industry 1..* salary_benchmark (industry); job_role 1..* salary_benchmark (role); employer_organisation 1..* salary_benchmark (employer, nullable)',
   'id PK, industry_id FK (nullable), job_role_id FK (nullable), employer_organisation_id FK (nullable), role_code (nullable), geography_code (nullable), min_salary, max_salary, currency_code, sample_size, as_of_date, created_at, created_by',
   'Unique salary benchmarks',
   'Unique Tier 3: salary benchmarks.'),
(220, 'Milestone 12 (Tier 3 stretch)', '12_tier3_stretch.sql', 'company_rating',
   'employer_organisation 1..* company_rating; users 1..* company_rating (rated_by)',
   'id PK, employer_organisation_id FK, rated_by_user_id FK (nullable), rating_value, category_code, comment_text, created_at, created_by',
   'Unique company ratings',
   'Unique Tier 3: company ratings.'),
(221, 'Milestone 12 (Tier 3 stretch)', '12_tier3_stretch.sql', 'trending_job_snapshot',
   'job_requirement 1..* trending_job_snapshot',
   'id PK, job_requirement_id FK, snapshot_date, view_count, application_count, shortlist_count, active_offer_count, is_trending, created_at, created_by',
   'Unique trending job snapshots',
   'Unique Tier 3: trending snapshots.'),
(222, 'Milestone 12 (Tier 3 stretch)', '12_tier3_stretch.sql', 'dashboard_aggregate',
   'dashboard_aggregate 1..* dashboard_widget (owner)',
   'id PK, dashboard_key, title, refresh_interval_minutes, created_at, created_by, updated_at, updated_by',
   'Unique dashboard config',
   'Unique Tier 3: dashboard metadata.'),
(223, 'Milestone 12 (Tier 3 stretch)', '12_tier3_stretch.sql', 'feature_flag',
   'feature_flag 1..* feature_flag_target (tenant)',
   'id PK, flag_key, flag_value, scope_code, tenant_account_id FK (nullable), candidate_identity_id FK (nullable), effective_from, effective_to (nullable), created_at, created_by, updated_at, updated_by',
   'Unique feature flags',
   'Unique Tier 3: feature flags.'),

-- Closing note for differentiators
(1001, 'Post-schema', '99_documentation.sql', 'unique_differentiators',
   'See docs/unique_differentiators.md for the full list of competitive differentiators added from the team side',
   'No new tables beyond docket scope.',
   'Competitive differentiators',
   'All differentiators are in-scope and docket-justified.');
"""

    # Append after the existing schema map end.
    # We place it right after the closing ')' of the existing CREATE TABLE schema_map_milestone_order
    idx = text.find(f"CONSTRAINT uq_schema_map_row UNIQUE (row_order, entity)")
    if idx < 0:
        raise RuntimeError("could not locate existing schema_map_milestone_order constraint end")
    j = text.find(");", idx)
    if j < 0:
        raise RuntimeError("could not locate end of existing schema_map_milestone_order")
    # insert after the ');'
    end = j + 2
    DOC.write_text(text[:end] + supplemental + text[end:])
    print("supplemental rows appended after existing schema_map")
else:
    print(f"{table_name} not found; nothing appended")
