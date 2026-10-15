-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Analytics layer and reporting marts module
-- Phase 4 (Individual/Team, Member C / Team), Milestones 15-18
--
-- This file models ONLY the docket Analytics layer and reporting marts domain.
-- Tier 3 (optional) from Section 4: analytics layer and reporting marts is Mandatory
--   (Tier 1 in the module table) Ã¢â‚¬â€� it is the assigned member C module in Phase 3.
--   The docket module table lists "Analytics layer Individual (Phase 3) Assigned member"
--   with scope "Star schema, dimensions, facts, aggregates for the KPIs in Section 8".
--   So analytics is NOT optional Tier 3 in the module table; it is a Phase 3 assigned
--   module. We model it here as mandated.
--
-- The "optional stretch coverage" Tier 3 domains (salary benchmarks, company ratings,
--   trending job snapshots, dashboard aggregates, feature flags) are NOT part of this
--   module; they are in 13_tier3_stretch.sql where you chose to include them.
--
-- B49 deliverable: dimensions, facts and aggregates for the KPIs in Section 8.
--   Section 8 KPIs are not detailed in the docket text provided, so we model a generic
--   but complete star schema that can support typical recruitment KPIs:
--     - pipeline funnel KPIs (applications by stage over time)
--     - time-to-hire / time-to-fill KPIs
--     - source/channel KPIs
--     - employer/candidate activity KPIs
--     - gig marketplace KPIs (applications, assignments, ratings, earnings references)
--   If the actual Section 8 KPI list differs, the star schema can be adjusted to match,
--   but the structure here is intentionally general and complete.
--
-- B58 deliverable: slowly changing dimension keys and aggregate refresh rules.
--   Dimensions use SCD Type 2 (valid_from/valid_to + is_current) where the attribute
--   changes over time, and Type 1 where only the current value matters.
--   Aggregates are materialized views with stated refresh rules (e.g. nightly refresh,
--   or refresh on pipeline event insertion for near-real-time aggregates where needed).
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK; natural keys as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification where applicable (analytics dimensions may
--   carry hashed/anonymized personal data; classification noted).
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ to distinguish them from
--   transactional tables; materialized views follow a stated naming pattern
--   (analytics_agg_*).
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- ANALYTICS DIMENSION: DATE
-- Standard date dimension for time-based KPIs.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_dim_date (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date_key               DATE      NOT NULL,
    day_of_week            SMALLINT  NOT NULL,
    day_of_month           SMALLINT  NOT NULL,
    day_of_year            SMALLINT  NOT NULL,
    week_of_year           SMALLINT  NOT NULL,
    month_of_year          SMALLINT  NOT NULL,
    month_name             TEXT      NOT NULL,
    quarter                SMALLINT  NOT NULL,
    year                   INTEGER   NOT NULL,
    is_current             BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT uq_analytics_dim_date_date_key UNIQUE (date_key)
);

CREATE INDEX idx_analytics_dim_date_date_key ON analytics_dim_date (date_key);
CREATE INDEX idx_analytics_dim_date_year_month ON analytics_dim_date (year, month_of_year);
CREATE INDEX idx_analytics_dim_date_year_quarter ON analytics_dim_date (year, quarter);

COMMENT ON TABLE analytics_dim_date IS 'Analytics: date dimension for time-based KPIs.';

-- -----------------------------------------------------------------------------
-- ANALYTICS DIMENSION: COUNTRY
-- Corresponds to master data country, used for geographic KPIs.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_dim_country (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_code           CHAR(2)   NOT NULL,
    country_name           TEXT      NOT NULL,
    iso_alpha3             CHAR(3)   NOT NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0
);

CREATE INDEX idx_analytics_dim_country_code ON analytics_dim_country (country_code);
CREATE INDEX idx_analytics_dim_country_active ON analytics_dim_country (is_active) WHERE is_active = TRUE;

COMMENT ON TABLE analytics_dim_country IS 'Analytics: country dimension (from master data country).';

-- -----------------------------------------------------------------------------
-- ANALYTICS DIMENSION: CITY
-- Corresponds to master data city, used for geographic KPIs.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_dim_city (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name              TEXT      NOT NULL,
    country_code           CHAR(2)   NOT NULL,
    state_name             TEXT      NULL,
    latitude               NUMERIC(9,6) NULL,
    longitude              NUMERIC(9,6) NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0
);

CREATE INDEX idx_analytics_dim_city_name ON analytics_dim_city (city_name);
CREATE INDEX idx_analytics_dim_city_country ON analytics_dim_city (country_code);
CREATE INDEX idx_analytics_dim_city_active ON analytics_dim_city (is_active) WHERE is_active = TRUE;

COMMENT ON TABLE analytics_dim_city IS 'Analytics: city dimension (from master data city).';

-- -----------------------------------------------------------------------------
-- ANALYTICS DIMENSION: EMPLOYER ORGANISATION
-- SCD Type 2 employer dimension for KPIs that need employer attributes over time.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_dim_employer_organisation (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_organisation_id BIGINT   NOT NULL,
    company_name           TEXT      NOT NULL,
    industry_name          TEXT      NULL,
    size_code              TEXT      NULL,
    country_code           CHAR(2)   NULL,
    city_name              TEXT      NULL,
    is_verified            BOOLEAN   NULL,
    effective_from         TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to           TIMESTAMPTZ NULL,
    is_current             BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT chk_analytics_dim_employer_current_check CHECK (
        is_current = TRUE OR effective_to IS NOT NULL
    )
);

CREATE INDEX idx_analytics_dim_employer_organisation_id ON analytics_dim_employer_organisation (employer_organisation_id);
CREATE INDEX idx_analytics_dim_employer_organisation_current ON analytics_dim_employer_organisation (employer_organisation_id, is_current)
    WHERE is_current = TRUE;
CREATE INDEX idx_analytics_dim_employer_organisation_industry ON analytics_dim_employer_organisation (industry_name) WHERE industry_name IS NOT NULL;

COMMENT ON TABLE analytics_dim_employer_organisation IS 'Analytics: employer organisation dimension (SCD Type 2).';

COMMENT ON COLUMN analytics_dim_employer_organisation.is_current IS 'Boolean flag indicating current version of the employer record (SCD Type 2 current row).';

COMMENT ON COLUMN analytics_dim_employer_organisation.effective_from IS 'Effective start of this version.';

COMMENT ON COLUMN analytics_dim_employer_organisation.effective_to IS 'Nullable = version currently active (no end yet).';

-- -----------------------------------------------------------------------------
-- ANALYTICS DIMENSION: CANDIDATE
-- SCD Type 2 candidate dimension for KPIs that need candidate attributes over time.
-- Personal data is carried in hashed/anonymized form where possible for analytics use.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_dim_candidate (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_identity_id  BIGINT    NOT NULL,
    email_hash             TEXT      NULL,
    first_name_hash        TEXT      NULL,
    last_name_hash         TEXT      NULL,
    profile_status_code    TEXT      NULL,
    country_code           CHAR(2)   NULL,
    city_name              TEXT      NULL,
    primary_skill_name     TEXT      NULL,
    effective_from         TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to           TIMESTAMPTZ NULL,
    is_current             BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT chk_analytics_dim_candidate_current_check CHECK (
        is_current = TRUE OR effective_to IS NOT NULL
    )
);

CREATE INDEX idx_analytics_dim_candidate_id ON analytics_dim_candidate (candidate_identity_id);
CREATE INDEX idx_analytics_dim_candidate_current ON analytics_dim_candidate (candidate_identity_id, is_current)
    WHERE is_current = TRUE;
CREATE INDEX idx_analytics_dim_candidate_status ON analytics_dim_candidate (profile_status_code) WHERE profile_status_code IS NOT NULL;
CREATE INDEX idx_analytics_dim_candidate_country ON analytics_dim_candidate (country_code) WHERE country_code IS NOT NULL;

COMMENT ON TABLE analytics_dim_candidate IS 'Analytics: candidate dimension (SCD Type 2, hashed personal data for analytics).';

COMMENT ON COLUMN analytics_dim_candidate.email_hash IS 'Hashed email for analytics de-duplication without storing clear email (personal data handling).';

COMMENT ON COLUMN analytics_dim_candidate.first_name_hash IS 'Hashed first name for analytics (personal data handling).';

COMMENT ON COLUMN analytics_dim_candidate.last_name_hash IS 'Hashed last name for analytics (personal data handling).';

COMMENT ON COLUMN analytics_dim_candidate.is_current IS 'Boolean flag indicating current version of the candidate record (SCD Type 2 current row).';

COMMENT ON COLUMN analytics_dim_candidate.effective_from IS 'Effective start of this version.';

COMMENT ON COLUMN analytics_dim_candidate.effective_to IS 'Nullable = version currently active (no end yet).';

-- -----------------------------------------------------------------------------
-- ANALYTICS DIMENSION: JOB REQUIREMENT
-- SCD Type 2 job dimension for KPIs that need job attributes over time.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_dim_job_requirement (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id     BIGINT    NOT NULL,
    title                  TEXT      NULL,
    employment_type_code   TEXT      NULL,
    work_type_code         TEXT      NULL,
    industry_name          TEXT      NULL,
    country_code           CHAR(2)   NULL,
    city_name              TEXT      NULL,
    compensation_min       NUMERIC(15,2) NULL,
    compensation_max       NUMERIC(15,2) NULL,
    compensation_currency_code TEXT NULL,
    is_open_to_consultants BOOLEAN   NULL,
    is_remote_allowed      BOOLEAN   NULL,
    status_code            TEXT      NULL,
    effective_from         TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to           TIMESTAMPTZ NULL,
    is_current             BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT chk_analytics_dim_job_current_check CHECK (
        is_current = TRUE OR effective_to IS NOT NULL
    )
);

CREATE INDEX idx_analytics_dim_job_requirement_id ON analytics_dim_job_requirement (job_requirement_id);
CREATE INDEX idx_analytics_dim_job_requirement_current ON analytics_dim_job_requirement (job_requirement_id, is_current)
    WHERE is_current = TRUE;
CREATE INDEX idx_analytics_dim_job_requirement_status ON analytics_dim_job_requirement (status_code) WHERE status_code IS NOT NULL;
CREATE INDEX idx_analytics_dim_job_requirement_industry ON analytics_dim_job_requirement (industry_name) WHERE industry_name IS NOT NULL;
CREATE INDEX idx_analytics_dim_job_requirement_country ON analytics_dim_job_requirement (country_code) WHERE country_code IS NOT NULL;

COMMENT ON TABLE analytics_dim_job_requirement IS 'Analytics: job requirement dimension (SCD Type 2).';

COMMENT ON COLUMN analytics_dim_job_requirement.is_current IS 'Boolean flag indicating current version of the job record (SCD Type 2 current row).';

COMMENT ON COLUMN analytics_dim_job_requirement.effective_from IS 'Effective start of this version.';

COMMENT ON COLUMN analytics_dim_job_requirement.effective_to IS 'Nullable = version currently active (no end yet).';

-- -----------------------------------------------------------------------------
-- ANALYTICS DIMENSION: APPLICATION PIPELINE STAGE
-- Static dimension for pipeline stage codes.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_dim_application_pipeline_stage (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_stage_code    TEXT      NOT NULL,
    stage_name             TEXT      NOT NULL,
    stage_order            SMALLINT  NOT NULL,
    is_terminal            BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT uq_analytics_dim_pipeline_stage_code UNIQUE (pipeline_stage_code)
);

CREATE INDEX idx_analytics_dim_pipeline_stage_code ON analytics_dim_application_pipeline_stage (pipeline_stage_code);

COMMENT ON TABLE analytics_dim_application_pipeline_stage IS 'Analytics: application pipeline stage dimension (static).';

COMMENT ON COLUMN analytics_dim_application_pipeline_stage.stage_order IS 'Stage order in the funnel.';

COMMENT ON COLUMN analytics_dim_application_pipeline_stage.is_terminal IS 'Boolean flag indicating whether the stage is terminal (e.g. joined, rejected, withdrawn).';

-- -----------------------------------------------------------------------------
-- ANALYTICS FACT: APPLICATION PIPELINE
-- Fact table for pipeline funnel KPIs.
-- One row per application stage entry (from application_pipeline_event).
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_fact_application_pipeline (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id         BIGINT    NOT NULL,
    candidate_identity_id  BIGINT    NOT NULL,
    job_requirement_id     BIGINT    NOT NULL,
    employer_organisation_id BIGINT   NOT NULL,
    pipeline_stage_code    TEXT      NOT NULL,
    entered_at             TIMESTAMPTZ NOT NULL,
    date_key               DATE      NOT NULL,
    country_code           CHAR(2)   NULL,
    city_name              TEXT      NULL,
    industry_name          TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0
);

CREATE INDEX idx_analytics_fact_application_pipeline_application ON analytics_fact_application_pipeline (application_id);
CREATE INDEX idx_analytics_fact_application_pipeline_candidate ON analytics_fact_application_pipeline (candidate_identity_id);
CREATE INDEX idx_analytics_fact_application_pipeline_job ON analytics_fact_application_pipeline (job_requirement_id);
CREATE INDEX idx_analytics_fact_application_pipeline_employer ON analytics_fact_application_pipeline (employer_organisation_id);
CREATE INDEX idx_analytics_fact_application_pipeline_stage ON analytics_fact_application_pipeline (pipeline_stage_code);
CREATE INDEX idx_analytics_fact_application_pipeline_date ON analytics_fact_application_pipeline (date_key);
CREATE INDEX idx_analytics_fact_application_pipeline_country ON analytics_fact_application_pipeline (country_code) WHERE country_code IS NOT NULL;
CREATE INDEX idx_analytics_fact_application_pipeline_industry ON analytics_fact_application_pipeline (industry_name) WHERE industry_name IS NOT NULL;

COMMENT ON TABLE analytics_fact_application_pipeline IS 'Analytics: application pipeline fact (one row per stage entry).';

COMMENT ON COLUMN analytics_fact_application_pipeline.date_key IS 'Date dimension key for time-based aggregation.';

COMMENT ON COLUMN analytics_fact_application_pipeline.country_code IS 'Nullable = unknown country. Country code from job location.';

COMMENT ON COLUMN analytics_fact_application_pipeline.city_name IS 'Nullable = unknown city. City name from job location.';

COMMENT ON COLUMN analytics_fact_application_pipeline.industry_name IS 'Nullable = unknown industry. Industry name from job.';

-- -----------------------------------------------------------------------------
-- ANALYTICS FACT: TIME TO HIRE
-- Fact table for time-to-hire / time-to-fill KPIs.
-- One row per application that reached a joined/terminal outcome, with duration measures.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_fact_time_to_hire (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id         BIGINT    NOT NULL,
    candidate_identity_id  BIGINT    NOT NULL,
    job_requirement_id     BIGINT    NOT NULL,
    employer_organisation_id BIGINT   NOT NULL,
    applied_at             TIMESTAMPTZ NOT NULL,
    joined_at              TIMESTAMPTZ NULL,
    rejected_at            TIMESTAMPTZ NULL,
    days_to_outcome        INTEGER   NULL,
    outcome_code           TEXT      NOT NULL,
    date_key               DATE      NOT NULL,
    country_code           CHAR(2)   NULL,
    city_name              TEXT      NULL,
    industry_name          TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT chk_analytics_fact_time_to_hire_days_nonnegative CHECK (
        days_to_outcome IS NULL OR days_to_outcome >= 0
    )
);

CREATE INDEX idx_analytics_fact_time_to_hire_application ON analytics_fact_time_to_hire (application_id);
CREATE INDEX idx_analytics_fact_time_to_hire_candidate ON analytics_fact_time_to_hire (candidate_identity_id);
CREATE INDEX idx_analytics_fact_time_to_hire_job ON analytics_fact_time_to_hire (job_requirement_id);
CREATE INDEX idx_analytics_fact_time_to_hire_employer ON analytics_fact_time_to_hire (employer_organisation_id);
CREATE INDEX idx_analytics_fact_time_to_hire_outcome ON analytics_fact_time_to_hire (outcome_code);
CREATE INDEX idx_analytics_fact_time_to_hire_date ON analytics_fact_time_to_hire (date_key);
CREATE INDEX idx_analytics_fact_time_to_hire_country ON analytics_fact_time_to_hire (country_code) WHERE country_code IS NOT NULL;
CREATE INDEX idx_analytics_fact_time_to_hire_industry ON analytics_fact_time_to_hire (industry_name) WHERE industry_name IS NOT NULL;

COMMENT ON TABLE analytics_fact_time_to_hire IS 'Analytics: time-to-hire / time-to-fill fact.';

COMMENT ON COLUMN analytics_fact_time_to_hire.applied_at IS 'Application application timestamp.';

COMMENT ON COLUMN analytics_fact_time_to_hire.joined_at IS 'Nullable = not joined. Join timestamp for time-to-hire calculation.';

COMMENT ON COLUMN analytics_fact_time_to_hire.rejected_at IS 'Nullable = not rejected. Rejection timestamp for time-to-reject calculation.';

COMMENT ON COLUMN analytics_fact_time_to_hire.days_to_outcome IS 'Nullable = not yet resulted. Days from application to outcome.';

COMMENT ON COLUMN analytics_fact_time_to_hire.outcome_code IS 'Outcome code (e.g. joined, rejected, withdrawn).';

COMMENT ON COLUMN analytics_fact_time_to_hire.date_key IS 'Date dimension key for time-based aggregation.';

-- -----------------------------------------------------------------------------
-- ANALYTICS FACT: SOURCE CHANNEL
-- Fact table for source/channel KPIs.
-- One row per application with source channel.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_fact_source_channel (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id         BIGINT    NOT NULL,
    candidate_identity_id  BIGINT    NOT NULL,
    job_requirement_id     BIGINT    NOT NULL,
    employer_organisation_id BIGINT   NOT NULL,
    source_channel_code    TEXT      NOT NULL,
    applied_at             TIMESTAMPTZ NOT NULL,
    date_key               DATE      NOT NULL,
    country_code           CHAR(2)   NULL,
    industry_name          TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0
);

CREATE INDEX idx_analytics_fact_source_channel_application ON analytics_fact_source_channel (application_id);
CREATE INDEX idx_analytics_fact_source_channel_candidate ON analytics_fact_source_channel (candidate_identity_id);
CREATE INDEX idx_analytics_fact_source_channel_job ON analytics_fact_source_channel (job_requirement_id);
CREATE INDEX idx_analytics_fact_source_channel_employer ON analytics_fact_source_channel (employer_organisation_id);
CREATE INDEX idx_analytics_fact_source_channel_source ON analytics_fact_source_channel (source_channel_code);
CREATE INDEX idx_analytics_fact_source_channel_date ON analytics_fact_source_channel (date_key);
CREATE INDEX idx_analytics_fact_source_channel_country ON analytics_fact_source_channel (country_code) WHERE country_code IS NOT NULL;
CREATE INDEX idx_analytics_fact_source_channel_industry ON analytics_fact_source_channel (industry_name) WHERE industry_name IS NOT NULL;

COMMENT ON TABLE analytics_fact_source_channel IS 'Analytics: source/channel fact.';

COMMENT ON COLUMN analytics_fact_source_channel.source_channel_code IS 'Source channel code for the application.';

-- -----------------------------------------------------------------------------
-- ANALYTICS FACT: EMPLOYER ACTIVITY
-- Fact table for employer activity KPIs (posts, applications received, hires).
-- One row per employer per day (or per event) with activity measures.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_fact_employer_activity (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_organisation_id BIGINT   NOT NULL,
    activity_date_key      DATE      NOT NULL,
    job_posts_count        INTEGER   NOT NULL DEFAULT 0,
    applications_received_count INTEGER NOT NULL DEFAULT 0,
    shortlisted_count      INTEGER   NOT NULL DEFAULT 0,
    interviewed_count      INTEGER   NOT NULL DEFAULT 0,
    offered_count          INTEGER   NOT NULL DEFAULT 0,
    joined_count           INTEGER   NOT NULL DEFAULT 0,
    rejected_count         INTEGER   NOT NULL DEFAULT 0,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    Not NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    Not NULL DEFAULT 0,
    CONSTRAINT chk_analytics_fact_employer_activity_counts_nonnegative CHECK (
        job_posts_count >= 0 AND applications_received_count >= 0 AND shortlisted_count >= 0
        AND interviewed_count >= 0 AND offered_count >= 0 AND joined_count >= 0 AND rejected_count >= 0
    )
);

CREATE INDEX idx_analytics_fact_employer_activity_employer ON analytics_fact_employer_activity (employer_organisation_id);
CREATE INDEX idx_analytics_fact_employer_activity_date ON analytics_fact_employer_activity (activity_date_key);

COMMENT ON TABLE analytics_fact_employer_activity IS 'Analytics: employer activity fact.';

COMMENT ON COLUMN analytics_fact_employer_activity.activity_date_key IS 'Date dimension key for time-based aggregation.';

COMMENT ON COLUMN analytics_fact_employer_activity.job_posts_count IS 'Number of job posts created by the employer on this date.';

COMMENT ON COLUMN analytics_fact_employer_activity.applications_received_count IS 'Number of applications received by the employer on this date.';

COMMENT ON COLUMN analytics_fact_employer_activity.shortlisted_count IS 'Number of applications shortlisted by the employer on this date.';

COMMENT ON COLUMN analytics_fact_employer_activity.interviewed_count IS 'Number of applications interviewed by the employer on this date.';

COMMENT ON COLUMN analytics_fact_employer_activity.offered_count IS 'Number of offers made by the employer on this date.';

COMMENT ON COLUMN analytics_fact_employer_activity.joined_count IS 'Number of candidates joined for the employer on this date.';

COMMENT ON COLUMN analytics_fact_employer_activity.rejected_count IS 'Number of applications rejected by the employer on this date.';

-- -----------------------------------------------------------------------------
-- ANALYTICS FACT: CANDIDATE ACTIVITY
-- Fact table for candidate activity KPIs (applications sent, profile views, searches).
-- One row per candidate per day with activity measures.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_fact_candidate_activity (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_identity_id  BIGINT    NOT NULL,
    activity_date_key      DATE      NOT NULL,
    applications_sent_count INTEGER   NOT NULL DEFAULT 0,
    profile_views_count    INTEGER   NOT NULL DEFAULT 0,
    searches_count         INTEGER   NOT NULL DEFAULT 0,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    Not NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    Not NULL DEFAULT 0,
    CONSTRAINT chk_analytics_fact_candidate_activity_counts_nonnegative CHECK (
        applications_sent_count >= 0 AND profile_views_count >= 0 AND searches_count >= 0
    )
);

CREATE INDEX idx_analytics_fact_candidate_activity_candidate ON analytics_fact_candidate_activity (candidate_identity_id);
CREATE INDEX idx_analytics_fact_candidate_activity_date ON analytics_fact_candidate_activity (activity_date_key);

COMMENT ON TABLE analytics_fact_candidate_activity IS 'Analytics: candidate activity fact.';

COMMENT ON COLUMN analytics_fact_candidate_activity.activity_date_key IS 'Date dimension key for time-based aggregation.';

COMMENT ON COLUMN analytics_fact_candidate_activity.applications_sent_count IS 'Number of applications sent by the candidate on this date.';

COMMENT ON COLUMN analytics_fact_candidate_activity.profile_views_count IS 'Number of profile views received by the candidate on this date.';

COMMENT ON COLUMN analytics_fact_candidate_activity.searches_count IS 'Number of job searches performed by the candidate on this date.';

-- -----------------------------------------------------------------------------
-- ANALYTICS FACT: GIG MARKETPLACE
-- Fact table for gig marketplace KPIs (applications, assignments, ratings, earnings references).
-- One row per gig application/assignment with gig KPIs.
-- -----------------------------------------------------------------------------
CREATE TABLE analytics_fact_gig_marketplace (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gig_request_detail_id  BIGINT    NOT NULL,
    job_requirement_id     BIGINT    NOT NULL,
    gig_worker_profile_id  BIGINT    NULL,
    assignment_id          BIGINT    NULL,
    application_id         BIGINT    NULL,
    handoff_reference_id   BIGINT    NULL,
    earnings_reference_id  BIGINT    NULL,
    pipeline_stage_code    TEXT      NULL,
    rating_value           NUMERIC(3,1) NULL,
    earnings_amount        NUMERIC(15,2) NULL,
    earnings_currency_code TEXT      NULL,
    date_key               DATE      NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    Not NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    Not NULL DEFAULT 0,
    CONSTRAINT chk_analytics_fact_gig_rating CHECK (
        rating_value IS NULL OR (rating_value >= 1 AND rating_value <= 5)
    ),
    CONSTRAINT chk_analytics_fact_gig_earnings_currency CHECK (
        earnings_currency_code IS NULL OR char_length(earnings_currency_code) = 3
    )
);

CREATE INDEX idx_analytics_fact_gig_marketplace_gig_request ON analytics_fact_gig_marketplace (gig_request_detail_id);
CREATE INDEX idx_analytics_fact_gig_marketplace_job ON analytics_fact_gig_marketplace (job_requirement_id);
CREATE INDEX idx_analytics_fact_gig_marketplace_worker ON analytics_fact_gig_marketplace (gig_worker_profile_id) WHERE gig_worker_profile_id IS NOT NULL;
CREATE INDEX idx_analytics_fact_gig_marketplace_assignment ON analytics_fact_gig_marketplace (assignment_id) WHERE assignment_id IS NOT NULL;
CREATE INDEX idx_analytics_fact_gig_marketplace_application ON analytics_fact_gig_marketplace (application_id) WHERE application_id IS NOT NULL;
CREATE INDEX idx_analytics_fact_gig_marketplace_pipeline_stage ON analytics_fact_gig_marketplace (pipeline_stage_code) WHERE pipeline_stage_code IS NOT NULL;
CREATE INDEX idx_analytics_fact_gig_marketplace_date ON analytics_fact_gig_marketplace (date_key);

COMMENT ON TABLE analytics_fact_gig_marketplace IS 'Analytics: gig marketplace fact.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.gig_request_detail_id IS 'Gig request detail ID.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.job_requirement_id IS 'Job requirement ID.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.gig_worker_profile_id IS 'Nullable = no worker assigned yet. Gig worker profile ID.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.assignment_id IS 'Nullable = no assignment yet. Assignment ID.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.application_id IS 'Nullable = no application yet. Application ID.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.handoff_reference_id IS 'Nullable = no handoff yet. Handoff reference ID.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.earnings_reference_id IS 'Nullable = no earnings reference yet. Earnings reference ID.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.pipeline_stage_code IS 'Nullable = no stage. Pipeline stage code.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.rating_value IS 'Nullable = not rated. Rating value 1..5.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.earnings_amount IS 'Nullable = no earnings. Earnings amount from external system.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.earnings_currency_code IS 'Nullable = no currency. Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN analytics_fact_gig_marketplace.date_key IS 'Date dimension key for time-based aggregation.';

-- -----------------------------------------------------------------------------
-- ANALYTICS MATERIALIZED VIEW: PIPELINE FUNNEL BY DAY
-- Aggregate for pipeline funnel KPIs by day.
-- Refresh rule: nightly refresh, or incremental refresh on pipeline event insertion
--   where near-real-time is required (documented in 99_documentation.sql).
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW analytics_agg_pipeline_funnel_by_day AS
SELECT
    afp.date_key,
    afp.pipeline_stage_code,
    COUNT(*) AS application_stage_entries,
    COUNT(DISTINCT afp.application_id) AS distinct_applications,
    COUNT(DISTINCT afp.candidate_identity_id) AS distinct_candidates,
    COUNT(DISTINCT afp.job_requirement_id) AS distinct_jobs,
    COUNT(DISTINCT afp.employer_organisation_id) AS distinct_employers
FROM analytics_fact_application_pipeline afp
GROUP BY afp.date_key, afp.pipeline_stage_code;

CREATE INDEX idx_analytics_agg_pipeline_funnel_by_day_date ON analytics_agg_pipeline_funnel_by_day (date_key);
CREATE INDEX idx_analytics_agg_pipeline_funnel_by_day_stage ON analytics_agg_pipeline_funnel_by_day (pipeline_stage_code);

COMMENT ON MATERIALIZED VIEW analytics_agg_pipeline_funnel_by_day IS 'Analytics: pipeline funnel aggregate by day. Refresh rule: nightly; incremental refresh on pipeline event insertion where near-real-time is required.';

-- -----------------------------------------------------------------------------
-- ANALYTICS MATERIALIZED VIEW: TIME TO HIRE BY MONTH
-- Aggregate for time-to-hire KPIs by month.
-- Refresh rule: nightly refresh.
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW analytics_agg_time_to_hire_by_month AS
SELECT
    date_trunc('month', afth.applied_at)::date AS month_key,
    afth.outcome_code,
    COUNT(*) AS application_count,
    COUNT(*) FILTER (WHERE afth.joined_at IS NOT NULL) AS joined_count,
    COUNT(*) FILTER (WHERE afth.rejected_at IS NOT NULL) AS rejected_count,
    AVG(afth.days_to_outcome) AS avg_days_to_outcome,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY afth.days_to_outcome) AS median_days_to_outcome
FROM analytics_fact_time_to_hire afth
GROUP BY date_trunc('month', afth.applied_at)::date, afth.outcome_code;

CREATE INDEX idx_analytics_agg_time_to_hire_by_month_month ON analytics_agg_time_to_hire_by_month (month_key);
CREATE INDEX idx_analytics_agg_time_to_hire_by_month_outcome ON analytics_agg_time_to_hire_by_month (outcome_code);

COMMENT ON MATERIALIZED VIEW analytics_agg_time_to_hire_by_month IS 'Analytics: time-to-hire aggregate by month. Refresh rule: nightly.';

-- -----------------------------------------------------------------------------
-- ANALYTICS MATERIALIZED VIEW: SOURCE CHANNEL MIX BY MONTH
-- Aggregate for source/channel KPIs by month.
-- Refresh rule: nightly refresh.
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW analytics_agg_source_channel_by_month AS
SELECT
    date_trunc('month', afs.applied_at)::date AS month_key,
    afs.source_channel_code,
    COUNT(*) AS applications,
    COUNT(DISTINCT afs.candidate_identity_id) AS distinct_candidates,
    COUNT(DISTINCT afs.job_requirement_id) AS distinct_jobs
FROM analytics_fact_source_channel afs
GROUP BY date_trunc('month', afs.applied_at)::date, afs.source_channel_code;

CREATE INDEX idx_analytics_agg_source_channel_by_month_month ON analytics_agg_source_channel_by_month (month_key);
CREATE INDEX idx_analytics_agg_source_channel_by_month_source ON analytics_agg_source_channel_by_month (source_channel_code);

COMMENT ON MATERIALIZED VIEW analytics_agg_source_channel_by_month IS 'Analytics: source/channel mix aggregate by month. Refresh rule: nightly.';

-- -----------------------------------------------------------------------------
-- ANALYTICS MATERIALIZED VIEW: EMPLOYER ACTIVITY ROLLUP BY MONTH
-- Aggregate for employer activity KPIs by month.
-- Refresh rule: nightly refresh.
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW analytics_agg_employer_activity_by_month AS
SELECT
    date_trunc('month', efa.activity_date_key)::date AS month_key,
    efa.employer_organisation_id,
    SUM(efa.job_posts_count) AS job_posts_count,
    SUM(efa.applications_received_count) AS applications_received_count,
    SUM(efa.shortlisted_count) AS shortlisted_count,
    SUM(efa.interviewed_count) AS interviewed_count,
    SUM(efa.offered_count) AS offered_count,
    SUM(efa.joined_count) AS joined_count,
    SUM(efa.rejected_count) AS rejected_count
FROM analytics_fact_employer_activity efa
GROUP BY date_trunc('month', efa.activity_date_key)::date, efa.employer_organisation_id;

CREATE INDEX idx_analytics_agg_employer_activity_by_month_month ON analytics_agg_employer_activity_by_month (month_key);
CREATE INDEX idx_analytics_agg_employer_activity_by_month_employer ON analytics_agg_employer_activity_by_month (employer_organisation_id);

COMMENT ON MATERIALIZED VIEW analytics_agg_employer_activity_by_month IS 'Analytics: employer activity aggregate by month. Refresh rule: nightly.';

-- -----------------------------------------------------------------------------
-- ANALYTICS MATERIALIZED VIEW: CANDIDATE ACTIVITY ROLLUP BY MONTH
-- Aggregate for candidate activity KPIs by month.
-- Refresh rule: nightly refresh.
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW analytics_agg_candidate_activity_by_month AS
SELECT
    date_trunc('month', cfa.activity_date_key)::date AS month_key,
    cfa.candidate_identity_id,
    SUM(cfa.applications_sent_count) AS applications_sent_count,
    SUM(cfa.profile_views_count) AS profile_views_count,
    SUM(cfa.searches_count) AS searches_count
FROM analytics_fact_candidate_activity cfa
GROUP BY date_trunc('month', cfa.activity_date_key)::date, cfa.candidate_identity_id;

CREATE INDEX idx_analytics_agg_candidate_activity_by_month_month ON analytics_agg_candidate_activity_by_month (month_key);
CREATE INDEX idx_analytics_agg_candidate_activity_by_month_candidate ON analytics_agg_candidate_activity_by_month (candidate_identity_id);

COMMENT ON MATERIALIZED VIEW analytics_agg_candidate_activity_by_month IS 'Analytics: candidate activity aggregate by month. Refresh rule: nightly.';

-- -----------------------------------------------------------------------------
-- ANALYTICS MATERIALIZED VIEW: GIG MARKETPLACE KPI BY DAY
-- Aggregate for gig marketplace KPIs by day.
-- Refresh rule: nightly refresh; incremental refresh on gig events where near-real-time
--   is required (documented in 99_documentation.sql).
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW analytics_agg_gig_marketplace_by_day AS
SELECT
    afg.date_key,
    COUNT(*) AS gig_fact_rows,
    COUNT(DISTINCT afg.gig_request_detail_id) AS distinct_gig_requests,
    COUNT(DISTINCT afg.job_requirement_id) AS distinct_jobs,
    COUNT(DISTINCT afg.gig_worker_profile_id) AS distinct_workers,
    COUNT(DISTINCT afg.assignment_id) AS distinct_assignments,
    COUNT(DISTINCT afg.application_id) AS distinct_applications,
    COUNT(DISTINCT afg.handoff_reference_id) AS distinct_handoffs,
    COUNT(DISTINCT afg.earnings_reference_id) AS distinct_earnings_references,
    COUNT(afg.rating_value) FILTER (WHERE afg.rating_value IS NOT NULL) AS rated_count,
    AVG(afg.rating_value) FILTER (WHERE afg.rating_value IS NOT NULL) AS avg_rating,
    SUM(afg.earnings_amount) FILTER (WHERE afg.earnings_amount IS NOT NULL) AS total_earnings,
    COUNT(DISTINCT afg.pipeline_stage_code) FILTER (WHERE afg.pipeline_stage_code IS NOT NULL) AS distinct_pipeline_stages
FROM analytics_fact_gig_marketplace afg
GROUP BY afg.date_key;

CREATE INDEX idx_analytics_agg_gig_marketplace_by_day_date ON analytics_agg_gig_marketplace_by_day (date_key);

COMMENT ON MATERIALIZED VIEW analytics_agg_gig_marketplace_by_day IS 'Analytics: gig marketplace KPI aggregate by day. Refresh rule: nightly; incremental refresh on gig events where near-real-time is required.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Analytics (Milestone 16, B52)
--   analytics_dim_date 1..* analytics_fact_* (date_key)
--   analytics_dim_country 1..* analytics_dim_city
--   analytics_dim_city 1..* analytics_fact_application_pipeline (country/city)
--   analytics_dim_employer_organisation 1..* analytics_fact_application_pipeline (employer)
--   analytics_dim_candidate 1..* analytics_fact_application_pipeline (candidate)
--   analytics_dim_job_requirement 1..* analytics_fact_application_pipeline (job)
--   analytics_dim_application_pipeline_stage 1..* analytics_fact_application_pipeline (pipeline_stage_code)
--   analytics_fact_application_pipeline 1..* analytics_fact_time_to_hire (related application)
--   analytics_fact_application_pipeline 1..* analytics_fact_source_channel (related application)
--   analytics_fact_employer_activity rollup from pipeline facts
--   analytics_fact_candidate_activity rollup from candidate activity facts
--   analytics_fact_gig_marketplace from gig entities
--   analytics_agg_* materialized views aggregate over facts
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new analytics entities beyond the docket scope. Decisions taken:
--   1. Analytics is modelled as the assigned Phase 3 module (not optional Tier 3) per the
--      module table in the docket.
--   2. Dimensions use SCD Type 2 where attributes change over time (employer, candidate,
--      job) and Type 1 / static for reference dimensions (date, country, city, pipeline stage).
--   3. Aggregates are materialized views with stated refresh rules (nightly default; incremental
--      where near-real-time is required). Exact refresh cadence is documented in 99_documentation.sql.
--   4. Candidate dimension carries hashed personal data for analytics de-duplication without
--      storing clear personal data (personal data handling).
--   5. The KPI set is intentionally general to cover typical recruitment KPIs; if Section 8
--      specifies exact KPIs, the facts/aggregates can be adjusted to match.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
