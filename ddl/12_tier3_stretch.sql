-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Tier 3 optional stretch module
-- Optional stretch coverage (not assigned to a module)
--
-- This file models ONLY the docket Tier 3 optional domains that you chose to include:
--   salary benchmarks
--   company ratings
--   trending job snapshots
--   dashboard aggregates
--   feature flags
--
-- Decision recorded: you chose to include ALL Tier 3 optional domains as a separate,
--   clearly-labelled module (not assigned to any module). This is the separate module
--   for that decision. If you later decide not to include one of these, it can be removed
--   or parked without affecting the core schema.
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK; natural keys as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification where applicable (salary benchmarks/ratings are
--   reference/internal; no personal data unless derived from personal data, which is noted).
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ where applicable (here most Tier 3
--   objects are reference/dashboard tables; where they are analytical, analytics_ prefix is used).
-- Rule Group 9 / 10: not Tier 3 module concerns for those specifics.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SALARY BENCHMARKS
-- Tier 3 optional: salary benchmarks.
-- Reference data: salary benchmark ranges by role/industry/location.
-- Not owned by the platform; attributed to a source with refresh date (Section 6:
--   company review and salary data boundary: reference only, with source attribution
--   and refresh date).
-- -----------------------------------------------------------------------------
CREATE TABLE salary_benchmark (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    benchmark_code         TEXT      NOT NULL,
    role_name              TEXT      NOT NULL,
    industry_name          TEXT      NULL,
    country_code           CHAR(2)   NULL,
    city_name              TEXT      NULL,
    experience_level_code TEXT      NULL,
    min_salary             NUMERIC(15,2) NULL,
    max_salary             NUMERIC(15,2) NULL,
    median_salary          NUMERIC(15,2) NULL,
    currency_code          TEXT      NOT NULL,
    source_name            TEXT      NOT NULL,
    source_url             TEXT      NULL,
    refreshed_at           TIMESTAMPTZ NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT chk_salary_benchmark_currency CHECK (char_length(currency_code) = 3),
    CONSTRAINT chk_salary_benchmark_range CHECK (
        (min_salary IS NULL AND max_salary IS NULL)
        OR (min_salary IS NOT NULL AND max_salary IS NULL)
        OR (min_salary IS NOT NULL AND max_salary IS NOT NULL AND min_salary <= max_salary)
    ),
    CONSTRAINT uq_salary_benchmark_code UNIQUE (benchmark_code),
    CONSTRAINT uq_salary_benchmark_role_industry_country_city_experience UNIQUE (
        role_name, industry_name, country_code, city_name, experience_level_code
    )
);

CREATE INDEX idx_salary_benchmark_code ON salary_benchmark (benchmark_code);
CREATE INDEX idx_salary_benchmark_role ON salary_benchmark (role_name);
CREATE INDEX idx_salary_benchmark_industry ON salary_benchmark (industry_name) WHERE industry_name IS NOT NULL;
CREATE INDEX idx_salary_benchmark_country ON salary_benchmark (country_code) WHERE country_code IS NOT NULL;
CREATE INDEX idx_salary_benchmark_city ON salary_benchmark (city_name) WHERE city_name IS NOT NULL;
CREATE INDEX idx_salary_benchmark_experience ON salary_benchmark (experience_level_code) WHERE experience_level_code IS NOT NULL;
CREATE INDEX idx_salary_benchmark_refreshed_at ON salary_benchmark (refreshed_at) WHERE refreshed_at IS NOT NULL;

COMMENT ON TABLE salary_benchmark IS 'Tier 3 optional: salary benchmarks (Section 4 Tier 3 optional: salary benchmarks). Reference only, with source attribution and refresh date (Section 6 company review and salary data boundary).';

COMMENT ON COLUMN salary_benchmark.benchmark_code IS 'Salary benchmark code; unique per benchmark.';

COMMENT ON COLUMN salary_benchmark.role_name IS 'Role name for the benchmark.';

COMMENT ON COLUMN salary_benchmark.industry_name IS 'Nullable = not industry-specific. Industry name for the benchmark.';

COMMENT ON COLUMN salary_benchmark.country_code IS 'Nullable = not country-specific. Country code for the benchmark.';

COMMENT ON COLUMN salary_benchmark.city_name IS 'Nullable = not city-specific. City name for the benchmark.';

COMMENT ON COLUMN salary_benchmark.experience_level_code IS 'Nullable = not experience-level-specific. Experience level code for the benchmark.';

COMMENT ON COLUMN salary_benchmark.min_salary IS 'Nullable = not disclosed. Money domain NUMERIC(15,2); lower bound of benchmark.';

COMMENT ON COLUMN salary_benchmark.max_salary IS 'Nullable = not disclosed. Money domain NUMERIC(15,2); upper bound of benchmark.';

COMMENT ON COLUMN salary_benchmark.median_salary IS 'Nullable = not disclosed. Money domain NUMERIC(15,2); median of benchmark.';

COMMENT ON COLUMN salary_benchmark.currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN salary_benchmark.source_name IS 'Source attribution (Section 6: reference only, with source attribution and refresh date).';

COMMENT ON COLUMN salary_benchmark.source_url IS 'Nullable = no URL. Source URL for attribution.';

COMMENT ON COLUMN salary_benchmark.refreshed_at IS 'Nullable = not refreshed yet. Refresh date for the benchmark data.';

-- -----------------------------------------------------------------------------
-- COMPANY RATINGS
-- Tier 3 optional: company ratings.
-- Reference data: company ratings by source, with attribution and refresh date.
-- Not owned by the platform; attributed to a source (Section 6: company review and salary
--   data boundary: reference only, with source attribution and refresh date).
-- -----------------------------------------------------------------------------
CREATE TABLE company_rating (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rating_code            TEXT      NOT NULL,
    employer_organisation_id BIGINT NULL,
    company_name           TEXT      NOT NULL,
    rating_value           NUMERIC(3,1) NULL,
    rating_max             NUMERIC(3,1) NOT NULL DEFAULT 5.0,
    review_count           INTEGER   NULL,
    source_name            TEXT      NOT NULL,
    source_url             TEXT      NULL,
    refreshed_at           TIMESTAMPTZ NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT chk_company_rating_value CHECK (
        rating_value IS NULL OR (rating_value >= 0 AND rating_value <= rating_max)
    ),
    CONSTRAINT chk_company_rating_max CHECK (rating_max > 0),
    CONSTRAINT chk_company_rating_review_count_nonnegative CHECK (review_count IS NULL OR review_count >= 0),
    CONSTRAINT uq_company_rating_code UNIQUE (rating_code),
    CONSTRAINT uq_company_rating_company_source UNIQUE (company_name, source_name)
);

CREATE INDEX idx_company_rating_code ON company_rating (rating_code);
CREATE INDEX idx_company_rating_company ON company_rating (company_name);
CREATE INDEX idx_company_rating_source ON company_rating (source_name);
CREATE INDEX idx_company_rating_refreshed_at ON company_rating (refreshed_at) WHERE refreshed_at IS NOT NULL;

COMMENT ON TABLE company_rating IS 'Tier 3 optional: company ratings (Section 4 Tier 3 optional: company ratings). Reference only, with source attribution and refresh date (Section 6 company review and salary data boundary).';

COMMENT ON COLUMN company_rating.rating_code IS 'Company rating code; unique per rating.';

COMMENT ON COLUMN company_rating.employer_organisation_id IS 'Nullable = not linked to a platform employer org. Link to platform employer organisation where applicable.';

COMMENT ON COLUMN company_rating.company_name IS 'Company name for the rating.';

COMMENT ON COLUMN company_rating.rating_value IS 'Nullable = not rated. Rating value; ratio domain with stated max.';

COMMENT ON COLUMN company_rating.rating_max IS 'Maximum rating value for the scale.';

COMMENT ON COLUMN company_rating.review_count IS 'Nullable = not disclosed. Number of reviews contributing to the rating.';

COMMENT ON COLUMN company_rating.source_name IS 'Source attribution (Section 6: reference only, with source attribution and refresh date).';

COMMENT ON COLUMN company_rating.source_url IS 'Nullable = no URL. Source URL for attribution.';

COMMENT ON COLUMN company_rating.refreshed_at IS 'Nullable = not refreshed yet. Refresh date for the rating data.';

-- -----------------------------------------------------------------------------
-- TRENDING JOB SNAPSHOTS
-- Tier 3 optional: trending job snapshots.
-- Snapshot data: trending job snapshots for dashboard/UI use. Not owned by the platform as
--   live data; stored as snapshots with snapshot time.
-- -----------------------------------------------------------------------------
CREATE TABLE trending_job_snapshot (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    snapshot_time          TIMESTAMPTZ NOT NULL DEFAULT now(),
    job_requirement_id     BIGINT    NULL,
    job_title              TEXT      NOT NULL,
    employer_organisation_name TEXT NULL,
    country_code           CHAR(2)   NULL,
    city_name              TEXT      NULL,
    industry_name          TEXT      NULL,
    trend_score            NUMERIC(5,2) NULL,
    trend_rank             INTEGER   NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT chk_trending_job_snapshot_trend_score CHECK (
        trend_score IS NULL OR (trend_score >= 0 AND trend_score <= 100)
    ),
    CONSTRAINT uq_trending_job_snapshot_snapshot_time_rank UNIQUE (snapshot_time, trend_rank)
);

CREATE INDEX idx_trending_job_snapshot_snapshot_time ON trending_job_snapshot (snapshot_time);
CREATE INDEX idx_trending_job_snapshot_rank ON trending_job_snapshot (snapshot_time, trend_rank);
CREATE INDEX idx_trending_job_snapshot_job ON trending_job_snapshot (job_requirement_id) WHERE job_requirement_id IS NOT NULL;
CREATE INDEX idx_trending_job_snapshot_country ON trending_job_snapshot (country_code) WHERE country_code IS NOT NULL;

COMMENT ON TABLE trending_job_snapshot IS 'Tier 3 optional: trending job snapshots (Section 4 Tier 3 optional: trending job snapshots). Snapshot data with snapshot time.';

COMMENT ON COLUMN trending_job_snapshot.snapshot_time IS 'Snapshot time for the trending job snapshot.';

COMMENT ON COLUMN trending_job_snapshot.job_requirement_id IS 'Nullable = not linked to a platform job. Link to platform job requirement where applicable.';

COMMENT ON COLUMN trending_job_snapshot.job_title IS 'Job title for the trending job.';

COMMENT ON COLUMN trending_job_snapshot.employer_organisation_name IS 'Nullable = not linked to a platform employer. Employer organisation name for the trending job.';

COMMENT ON COLUMN trending_job_snapshot.country_code IS 'Nullable = unknown country. Country code for the trending job.';

COMMENT ON COLUMN trending_job_snapshot.city_name IS 'Nullable = unknown city. City name for the trending job.';

COMMENT ON COLUMN trending_job_snapshot.industry_name IS 'Nullable = unknown industry. Industry name for the trending job.';

COMMENT ON COLUMN trending_job_snapshot.trend_score IS 'Nullable = not scored. Trend score 0..100.';

COMMENT ON COLUMN trending_job_snapshot.trend_rank IS 'Trend rank within the snapshot.';

-- -----------------------------------------------------------------------------
-- DASHBOARD AGGREGATES
-- Tier 3 optional: dashboard aggregates.
-- Precomputed aggregates for dashboard use. These are derived from the analytics facts and
--   dimensions; they are stored as materialized/aggregate tables with refresh rules.
-- -----------------------------------------------------------------------------
CREATE TABLE dashboard_aggregate (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aggregate_code         TEXT      NOT NULL,
    aggregate_name         TEXT      NOT NULL,
    aggregate_type_code    TEXT      NOT NULL,
    snapshot_time          TIMESTAMPTZ NOT NULL DEFAULT now(),
    period_start           DATE      NULL,
    period_end             DATE      NULL,
    metric_value           NUMERIC(15,2) NULL,
    metric_currency_code   TEXT      NULL,
    metric_count           INTEGER   NULL,
    metric_text            TEXT      NULL,
    source_fact_code       TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT chk_dashboard_aggregate_metric_count_nonnegative CHECK (
        metric_count IS NULL OR metric_count >= 0
    ),
    CONSTRAINT chk_dashboard_aggregate_metric_currency CHECK (
        metric_currency_code IS NULL OR char_length(metric_currency_code) = 3
    ),
    CONSTRAINT uq_dashboard_aggregate_code UNIQUE (aggregate_code),
    CONSTRAINT uq_dashboard_aggregate_code_snapshot UNIQUE (aggregate_code, snapshot_time)
);

CREATE INDEX idx_dashboard_aggregate_code ON dashboard_aggregate (aggregate_code);
CREATE INDEX idx_dashboard_aggregate_type ON dashboard_aggregate (aggregate_type_code);
CREATE INDEX idx_dashboard_aggregate_snapshot ON dashboard_aggregate (aggregate_code, snapshot_time);
CREATE INDEX idx_dashboard_aggregate_period ON dashboard_aggregate (period_start, period_end) WHERE period_start IS NOT NULL;

COMMENT ON TABLE dashboard_aggregate IS 'Tier 3 optional: dashboard aggregates (Section 4 Tier 3 optional: dashboard aggregates). Precomputed aggregates for dashboard use.';

COMMENT ON COLUMN dashboard_aggregate.aggregate_code IS 'Dashboard aggregate code; unique per aggregate definition.';

COMMENT ON COLUMN dashboard_aggregate.aggregate_name IS 'Dashboard aggregate name.';

COMMENT ON COLUMN dashboard_aggregate.aggregate_type_code IS 'Aggregate type code (e.g. count, sum, avg, ratio).';

COMMENT ON COLUMN dashboard_aggregate.snapshot_time IS 'Snapshot time for the aggregate.';

COMMENT ON COLUMN dashboard_aggregate.period_start IS 'Nullable = not period-bound. Period start for the aggregate.';

COMMENT ON COLUMN dashboard_aggregate.period_end IS 'Nullable = not period-bound. Period end for the aggregate.';

COMMENT ON COLUMN dashboard_aggregate.metric_value IS 'Nullable = not a numeric metric. Metric value for the aggregate.';

COMMENT ON COLUMN dashboard_aggregate.metric_currency_code IS 'Nullable = not a currency metric. Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN dashboard_aggregate.metric_count IS 'Nullable = not a count metric. Metric count for the aggregate.';

COMMENT ON COLUMN dashboard_aggregate.metric_text IS 'Nullable = not a text metric. Metric text for the aggregate.';

COMMENT ON COLUMN dashboard_aggregate.source_fact_code IS 'Nullable = not derived from a fact. Source fact code the aggregate is derived from.';

-- -----------------------------------------------------------------------------
-- FEATURE FLAGS
-- Tier 3 optional: feature flags.
-- Feature flag configuration for the platform. Not mandated by the docket; included per your
--   decision to include all Tier 3 optional domains.
-- -----------------------------------------------------------------------------
CREATE TABLE feature_flag (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flag_code              TEXT      NOT NULL,
    flag_name              TEXT      NOT NULL,
    flag_description       TEXT      NULL,
    flag_key               TEXT      NOT NULL,
    is_enabled             BOOLEAN   NOT NULL DEFAULT FALSE,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    target_segment_code    TEXT      NULL,
    variation_value        TEXT      NULL,
    variation_type_code    TEXT      NULL,
    rollout_percentage     NUMERIC(5,2) NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT chk_feature_flag_rollout_percentage CHECK (
        rollout_percentage IS NULL OR (rollout_percentage >= 0 AND rollout_percentage <= 100)
    ),
    CONSTRAINT uq_feature_flag_code UNIQUE (flag_code),
    CONSTRAINT uq_feature_flag_key UNIQUE (flag_key)
);

CREATE INDEX idx_feature_flag_code ON feature_flag (flag_code);
CREATE INDEX idx_feature_flag_key ON feature_flag (flag_key);
CREATE INDEX idx_feature_flag_enabled ON feature_flag (is_enabled) WHERE is_enabled = TRUE;
CREATE INDEX idx_feature_flag_active ON feature_flag (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_feature_flag_segment ON feature_flag (target_segment_code) WHERE target_segment_code IS NOT NULL;

COMMENT ON TABLE feature_flag IS 'Tier 3 optional: feature flags (Section 4 Tier 3 optional: feature flags). Feature flag configuration.';

COMMENT ON COLUMN feature_flag.flag_code IS 'Feature flag code; unique per flag.';

COMMENT ON COLUMN feature_flag.flag_name IS 'Feature flag name.';

COMMENT ON COLUMN feature_flag.flag_description IS 'Nullable = no description.';

COMMENT ON COLUMN feature_flag.flag_key IS 'Feature flag key; unique per flag.';

COMMENT ON COLUMN feature_flag.is_enabled IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

COMMENT ON COLUMN feature_flag.is_active IS 'Boolean flag with stated default TRUE (Rule Group 3 boolean domain).';

COMMENT ON COLUMN feature_flag.target_segment_code IS 'Nullable = all users. Target segment code for the flag.';

COMMENT ON COLUMN feature_flag.variation_value IS 'Nullable = no variation. Variation value for the flag.';

COMMENT ON COLUMN feature_flag.variation_type_code IS 'Nullable = no type. Variation type code for the flag.';

COMMENT ON COLUMN feature_flag.rollout_percentage IS 'Nullable = 100% or not percentage-based. Rollout percentage 0..100.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Tier 3 optional stretch module
--   salary_benchmark (standalone reference data)
--   company_rating (standalone reference data; optional link to employer_organisation)
--   trending_job_snapshot (standalone snapshot data; optional link to job_requirement)
--   dashboard_aggregate (standalone aggregate data; derived from analytics facts)
--   feature_flag (standalone configuration data)
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Tier 3 entities beyond the docket Tier 3 optional list. Decisions taken:
--   1. This is a separate, clearly-labelled module for the docket Tier 3 optional stretch
--      coverage, as required by the docket for optional stretch coverage.
--   2. salary_benchmark and company_rating are reference-only data with source attribution and
--      refresh date, per Section 6 (company review and salary data boundary).
--   3. trending_job_snapshot stores snapshot data with snapshot time.
--   4. dashboard_aggregate stores precomputed aggregates with snapshot time and period.
--   5. feature_flag stores feature flag configuration.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
