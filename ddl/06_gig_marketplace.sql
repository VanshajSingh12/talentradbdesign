-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Gig marketplace module
-- Phase 3 (Individual, Member C), Milestones 11-14
--
-- This file models ONLY the docket Gig marketplace domain.
-- Tier 1 (mandatory) from Section 4:
--   gig requests with windows and pricing, gig worker profiles, availability,
--     gig applications, assignments and handoff references,
--     lists and blacklists, ratings, and earnings references from external systems.
--
-- Gig model decision (Section 2 Gig Work; your choice): gigs share the core
--   job + application model with other job types. A gig request is stored as a
--   job_requirement row (with gig-specific openness/context) plus companion
--   gig_request_detail for gig-specific fields that are not part of the core job
--   model (handoff reference, earnings reference, ratings, favourites/blacklists).
--   Those gig-specific pieces are here, in the gig marketplace module, because the
--   docket places them under "Gig marketplace". The core job/application pipeline
--   remains in 03_jobs_applications.sql.
--   See 99_documentation.sql for the justification.
--
-- B35 requirement: gig windows cannot overlap for the same gig worker. We model
--   gig_worker_availability with effective time ranges and enforce non-overlap per
--   gig worker. The enforcement mechanism is stated in this file and in
--   99_documentation.sql.
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK; natural keys as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification where applicable.
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ (in analytics module, not here).
-- Rule Group 9 / 10: not Gig module concerns for these tables except where gig-specific
--   money/wallet concepts appear; those are owned by the wallet/payments module where
--   the docket places them.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- GIG REQUEST DETAIL
-- Tier 1: gig requests with windows and pricing.
-- Relationship:
--   job_requirement 1..1 gig_request_detail (gig-specific fields)
-- The core job posting lives in job_requirement (03_jobs_applications.sql).
-- This table holds gig-specific pricing, windows, and fulfillment context.
-- Pricing domain: fixed price / rate-based, each with NUMERIC(15,2) + currency_code.
-- -----------------------------------------------------------------------------
CREATE TABLE gig_request_detail (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id  BIGINT    NOT NULL,
    pricing_model_code   TEXT      NOT NULL,
    fixed_price         NUMERIC(15,2) NULL,
    fixed_price_currency_code TEXT NULL,
    rate_per_time_unit  NUMERIC(15,2) NULL,
    rate_time_unit_code TEXT      NULL,
    rate_currency_code  TEXT      NULL,
    window_start_at      TIMESTAMPTZ NOT NULL,
    window_end_at        TIMESTAMPTZ NOT NULL,
    apply_by_at         TIMESTAMPTZ NULL,
    handoff_system_code TEXT      NULL,
    handoff_reference   TEXT      NULL,
    fulfillment_status_code TEXT NULL,
    fulfillment_synced_at TIMESTAMPTZ NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_request_detail_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_gig_window_not_empty CHECK (window_end_at > window_start_at),
    CONSTRAINT chk_gig_fixed_price_currency CHECK (
        fixed_price_currency_code IS NULL OR char_length(fixed_price_currency_code) = 3
    ),
    CONSTRAINT chk_gig_rate_currency CHECK (
        rate_currency_code IS NULL OR char_length(rate_currency_code) = 3
    ),
    CONSTRAINT chk_gig_pricing_model_exclusive CHECK (
        (pricing_model_code = 'fixed' AND fixed_price IS NOT NULL AND rate_per_time_unit IS NULL)
        OR (pricing_model_code = 'rate' AND rate_per_time_unit IS NOT NULL AND fixed_price IS NULL)
        OR (pricing_model_code IN ('fixed','rate') AND false) -- impossible branch, keeps rule readable
    )
);

CREATE INDEX idx_gig_request_detail_job ON gig_request_detail (job_requirement_id);
CREATE INDEX idx_gig_request_detail_pricing_model ON gig_request_detail (pricing_model_code);
CREATE INDEX idx_gig_request_detail_window ON gig_request_detail (window_start_at, window_end_at);
CREATE INDEX idx_gig_request_detail_handoff ON gig_request_detail (handoff_system_code, handoff_reference) WHERE handoff_system_code IS NOT NULL;
CREATE INDEX idx_gig_request_detail_deleted ON gig_request_detail (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_request_detail IS 'Gig marketplace: gig requests with windows and pricing (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN gig_request_detail.fixed_price IS 'Money domain NUMERIC(15,2) + currency_code. Used when pricing_model_code = fixed.';

COMMENT ON COLUMN gig_request_detail.fixed_price_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN gig_request_detail.rate_per_time_unit IS 'Money domain NUMERIC(15,2) + currency_code. Used when pricing_model_code = rate.';

COMMENT ON COLUMN gig_request_detail.rate_time_unit_code IS 'Enumeration code referencing reference_code (domain=rate_time_unit).';

COMMENT ON COLUMN gig_request_detail.rate_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN gig_request_detail.window_start_at IS 'Gig window start (Section 2 Gig Work: start and end window).';

COMMENT ON COLUMN gig_request_detail.window_end_at IS 'Gig window end. CHECK ensures window_end_at > window_start_at.';

COMMENT ON COLUMN gig_request_detail.apply_by_at IS 'Nullable = no separate application deadline; defaults to window end logic in application layer.';

COMMENT ON COLUMN gig_request_detail.handoff_system_code IS 'Enumeration code referencing reference_code (domain=handoff_system).';

COMMENT ON COLUMN gig_request_detail.handoff_reference IS 'Sensitive-ish. Handoff reference to external fulfillment system; stored as reference, not fulfillment state.';

COMMENT ON COLUMN gig_request_detail.fulfillment_status_code IS 'Enumeration code referencing reference_code (domain=fulfillment_status).';

COMMENT ON COLUMN gig_request_detail.fulfillment_synced_at IS 'Nullable = not yet synced.';

-- -----------------------------------------------------------------------------
-- GIG WORKER PROFILE
-- Tier 1: gig worker profiles (separate profile from permanent and temporary
--   candidates, with availability, service offerings, and charge rates).
-- Relationship:
--   candidate_identity 1..1 gig_worker_profile (gig workers have a separate
--     profile; a person may be both a candidate and a gig worker, modelled via
--     two profiles or via an explicit link; here we model a separate gig worker
--     profile linked to the candidate_identity where applicable).
-- -----------------------------------------------------------------------------
CREATE TABLE gig_worker_profile (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_identity_id  BIGINT    NULL,
    worker_name            TEXT      NOT NULL,
    headline               TEXT      NULL,
    service_offerings      TEXT      NULL,
    charge_rate_min        NUMERIC(15,2) NULL,
    charge_rate_max        NUMERIC(15,2) NULL,
    charge_currency_code   TEXT      NULL,
    status_code            TEXT      NOT NULL,
    is_available           BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_worker_profile_candidate FOREIGN KEY (candidate_identity_id)
        REFERENCES candidate_identity(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_gig_worker_charge_range CHECK (
        (charge_rate_min IS NULL AND charge_rate_max IS NULL)
        OR (charge_rate_min IS NOT NULL AND charge_rate_max IS NULL)
        OR (charge_rate_min IS NOT NULL AND charge_rate_max IS NOT NULL AND charge_rate_min <= charge_rate_max)
    ),
    CONSTRAINT chk_gig_worker_charge_currency CHECK (
        charge_currency_code IS NULL OR char_length(charge_currency_code) = 3
    )
);

CREATE INDEX idx_gig_worker_profile_candidate ON gig_worker_profile (candidate_identity_id) WHERE candidate_identity_id IS NOT NULL;
CREATE INDEX idx_gig_worker_profile_status ON gig_worker_profile (status_code);
CREATE INDEX idx_gig_worker_profile_available ON gig_worker_profile (is_available) WHERE is_available = TRUE;
CREATE INDEX idx_gig_worker_profile_deleted ON gig_worker_profile (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_worker_profile IS 'Gig marketplace: gig worker profiles (Section 4 Tier 1). Personal. Soft-deleted.';

COMMENT ON COLUMN gig_worker_profile.worker_name IS 'Person name domain TEXT (Rule Group 3).';

COMMENT ON COLUMN gig_worker_profile.headline IS 'Nullable = not provided.';

COMMENT ON COLUMN gig_worker_profile.service_offerings IS 'Nullable = none listed. Stored as TEXT; bounded length enforced at application level.';

COMMENT ON COLUMN gig_worker_profile.charge_rate_min IS 'Money domain NUMERIC(15,2) + currency_code. Nullable = not disclosed (not zero).';

COMMENT ON COLUMN gig_worker_profile.charge_rate_max IS 'Money domain NUMERIC(15,2) + currency_code. Nullable = not disclosed (not zero).';

COMMENT ON COLUMN gig_worker_profile.charge_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN gig_worker_profile.status_code IS 'Enumeration code referencing reference_code (domain=gig_worker_status).';

-- -----------------------------------------------------------------------------
-- GIG WORKER AVAILABILITY
-- Tier 1: availability (gig worker availability windows).
-- B35 deliverable: gig windows cannot overlap for the same gig worker.
-- We model availability as time ranges per gig worker and enforce non-overlap
-- via the stated mechanism.
-- -----------------------------------------------------------------------------
CREATE TABLE gig_worker_availability (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gig_worker_profile_id BIGINT    NOT NULL,
    availability_start_at TIMESTAMPTZ NOT NULL,
    availability_end_at   TIMESTAMPTZ NOT NULL,
    time_zone            TEXT      NULL,
    is_recurring         BOOLEAN   NOT NULL DEFAULT FALSE,
    recurrence_rule      TEXT      NULL,
    is_active            BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_worker_availability_worker FOREIGN KEY (gig_worker_profile_id)
        REFERENCES gig_worker_profile(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_gig_worker_availability_range CHECK (availability_end_at > availability_start_at)
);

CREATE INDEX idx_gig_worker_availability_worker ON gig_worker_availability (gig_worker_profile_id);
CREATE INDEX idx_gig_worker_availability_range ON gig_worker_availability (gig_worker_profile_id, availability_start_at, availability_end_at);
CREATE INDEX idx_gig_worker_availability_active ON gig_worker_availability (gig_worker_profile_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_gig_worker_availability_deleted ON gig_worker_availability (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_worker_availability IS 'Gig marketplace: availability (Section 4 Tier 1 gig worker profiles). Personal. Soft-deleted.';

COMMENT ON COLUMN gig_worker_availability.availability_start_at IS 'Availability window start.';

COMMENT ON COLUMN gig_worker_availability.availability_end_at IS 'Availability window end. CHECK ensures end > start.';

COMMENT ON COLUMN gig_worker_availability.time_zone IS 'Nullable = unknown source timezone. Stored where it matters for display (Rule Group 3 timestamp domain).';

COMMENT ON COLUMN gig_worker_availability.is_recurring IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- GIG APPLICATION
-- Tier 1: gig applications.
-- Relationship:
--   gig_request_detail 1..* gig_application
--   gig_worker_profile 1..* gig_application
--   users (applicant) 1..* gig_application
-- Bids do not flow in both directions (Section 2 Gig Work). The requester accepts
--   or rejects the application. The application stores bid context (bid amount,
--   bid message) and pipeline via application_pipeline_event from the Jobs module
--   where appropriate; here we keep gig-specific application context.
-- -----------------------------------------------------------------------------
CREATE TABLE gig_application (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gig_request_detail_id BIGINT    NOT NULL,
    gig_worker_profile_id BIGINT    NOT NULL,
    applicant_user_id    BIGINT    NOT NULL,
    bid_amount           NUMERIC(15,2) NULL,
    bid_currency_code    TEXT      NULL,
    bid_message          TEXT      NULL,
    application_status_code TEXT    NOT NULL,
    applied_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at          TIMESTAMPTZ NULL,
    reviewed_by_user_id  BIGINT    NULL,
    rejection_reason     TEXT      NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_application_gig_request FOREIGN KEY (gig_request_detail_id)
        REFERENCES gig_request_detail(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_application_worker FOREIGN KEY (gig_worker_profile_id)
        REFERENCES gig_worker_profile(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_application_applicant FOREIGN KEY (applicant_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_gig_application_bid_currency CHECK (
        bid_currency_code IS NULL OR char_length(bid_currency_code) = 3
    )
);

CREATE INDEX idx_gig_application_gig_request ON gig_application (gig_request_detail_id);
CREATE INDEX idx_gig_application_worker ON gig_application (gig_worker_profile_id);
CREATE INDEX idx_gig_application_applicant ON gig_application (applicant_user_id);
CREATE INDEX idx_gig_application_status ON gig_application (application_status_code);
CREATE INDEX idx_gig_application_deleted ON gig_application (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_application IS 'Gig marketplace: gig applications (Section 4 Tier 1). Personal. Soft-deleted.';

COMMENT ON COLUMN gig_application.bid_amount IS 'Money domain NUMERIC(15,2) + currency_code. Nullable = no bid amount (e.g. rate-based gig where bid is the rate).';

COMMENT ON COLUMN gig_application.bid_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN gig_application.bid_message IS 'Nullable = no message.';

COMMENT ON COLUMN gig_application.rejection_reason IS 'Nullable = not rejected or no reason recorded.';

-- -----------------------------------------------------------------------------
-- GIG ASSIGNMENT AND HANDOFF REFERENCE
-- Tier 1: assignments and handoff references.
-- Relationship:
--   gig_application 1..1 gig_assignment (accepted application becomes assignment)
--   gig_assignment 1..1 gig_handoff_reference
-- The platform stores the handoff reference and reconciles status; it does not run
--   fulfillment itself (Section 2 Gig Work).
-- -----------------------------------------------------------------------------
CREATE TABLE gig_assignment (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gig_application_id   BIGINT    NOT NULL,
    assigned_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_by_user_id  BIGINT    NOT NULL,
    expected_start_at    TIMESTAMPTZ NULL,
    expected_end_at      TIMESTAMPTZ NULL,
    actual_start_at      TIMESTAMPTZ NULL,
    actual_end_at        TIMESTAMPTZ NULL,
    assignment_status_code TEXT    NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_assignment_application FOREIGN KEY (gig_application_id)
        REFERENCES gig_application(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_assignment_assigned_by FOREIGN KEY (assigned_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_gig_assignment_expected_range CHECK (
        expected_end_at IS NULL OR expected_end_at >= expected_start_at
    ),
    CONSTRAINT chk_gig_assignment_actual_range CHECK (
        actual_end_at IS NULL OR actual_end_at >= actual_start_at
    )
);

CREATE INDEX idx_gig_assignment_application ON gig_assignment (gig_application_id);
CREATE INDEX idx_gig_assignment_assigned_by ON gig_assignment (assigned_by_user_id);
CREATE INDEX idx_gig_assignment_status ON gig_assignment (assignment_status_code);
CREATE INDEX idx_gig_assignment_deleted ON gig_assignment (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_assignment IS 'Gig marketplace: assignments (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN gig_assignment.expected_start_at IS 'Nullable = not scheduled.';

COMMENT ON COLUMN gig_assignment.expected_end_at IS 'Nullable = not scheduled.';

COMMENT ON COLUMN gig_assignment.actual_start_at IS 'Nullable = not started.';

COMMENT ON COLUMN gig_assignment.actual_end_at IS 'Nullable = not ended.';

-- -----------------------------------------------------------------------------
-- GIG HANDOFF REFERENCE
-- Tier 1: handoff references.
-- Relationship: gig_assignment 1..1 gig_handoff_reference.
-- Stores the handoff reference to the external fulfillment system and reconciled
-- status; does not run fulfillment itself.
-- -----------------------------------------------------------------------------
CREATE TABLE gig_handoff_reference (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gig_assignment_id    BIGINT    NOT NULL,
    handoff_system_code  TEXT      NOT NULL,
    external_reference   TEXT      NOT NULL,
    handoff_status_code  TEXT      NOT NULL,
    handed_off_at        TIMESTAMPTZ NULL,
    reconciled_at        TIMESTAMPTZ NULL,
    reconciled_by_user_id BIGINT    NULL,
    reconciliation_note  TEXT      NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_handoff_assignment FOREIGN KEY (gig_assignment_id)
        REFERENCES gig_assignment(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_handoff_reconciled_by FOREIGN KEY (reconciled_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT uq_gig_handoff_assignment UNIQUE (gig_assignment_id)
);

CREATE INDEX idx_gig_handoff_assignment ON gig_handoff_reference (gig_assignment_id);
CREATE INDEX idx_gig_handoff_system ON gig_handoff_reference (handoff_system_code);
CREATE INDEX idx_gig_handoff_status ON gig_handoff_reference (handoff_status_code);
CREATE INDEX idx_gig_handoff_deleted ON gig_handoff_reference (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_handoff_reference IS 'Gig marketplace: handoff references (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN gig_handoff_reference.external_reference IS 'External fulfillment system reference; stored as reference, not fulfillment state.';

COMMENT ON COLUMN gig_handoff_reference.reconciliation_note IS 'Nullable = no note.';

-- -----------------------------------------------------------------------------
-- GIG EARNINGS REFERENCE
-- Tier 1: earnings references from external systems.
-- Relationship: gig_assignment 1..* gig_earnings_reference (multiple earnings
--   references per assignment are possible, e.g. estimated, total, projected).
-- Earnings figures are sourced from the external fulfillment system and modelled
--   as an integration boundary (Section 2 Gig Work and Section 6).
-- Money domain: NUMERIC(15,2) + currency_code.
-- -----------------------------------------------------------------------------
CREATE TABLE gig_earnings_reference (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gig_assignment_id    BIGINT    NOT NULL,
    earnings_type_code   TEXT      NOT NULL,
    earnings_amount      NUMERIC(15,2) NOT NULL,
    earnings_currency_code TEXT     NOT NULL,
    source_system_code   TEXT      NOT NULL,
    reported_at          TIMESTAMPTZ NULL,
    reconciled_at        TIMESTAMPTZ NULL,
    reconciled_by_user_id BIGINT    NULL,
    reconciliation_note  TEXT      NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_earnings_assignment FOREIGN KEY (gig_assignment_id)
        REFERENCES gig_assignment(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_earnings_reconciled_by FOREIGN KEY (reconciled_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_gig_earnings_currency CHECK (char_length(earnings_currency_code) = 3)
);

CREATE INDEX idx_gig_earnings_assignment ON gig_earnings_reference (gig_assignment_id);
CREATE INDEX idx_gig_earnings_type ON gig_earnings_reference (earnings_type_code);
CREATE INDEX idx_gig_earnings_source ON gig_earnings_reference (source_system_code);
CREATE INDEX idx_gig_earnings_deleted ON gig_earnings_reference (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_earnings_reference IS 'Gig marketplace: earnings references from external systems (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN gig_earnings_reference.earnings_amount IS 'Money domain NUMERIC(15,2) + currency_code. Sourced from external fulfillment system.';

COMMENT ON COLUMN gig_earnings_reference.earnings_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN gig_earnings_reference.reported_at IS 'Nullable = not reported yet.';

COMMENT ON COLUMN gig_earnings_reference.reconciled_at IS 'Nullable = not reconciled yet.';

COMMENT ON COLUMN gig_earnings_reference.reconciliation_note IS 'Nullable = no note.';

-- -----------------------------------------------------------------------------
-- GIG FAVOURITES AND BLACKLISTS
-- Tier 1: lists and blacklists for gig workers (requesters maintain favourite and
--   blacklisted gig workers).
-- Relationship:
--   users (requester) 1..* gig_favourite
--   users (requester) 1..* gig_blacklist
--   gig_worker_profile 1..* gig_favourite
--   gig_worker_profile 1..* gig_blacklist
-- -----------------------------------------------------------------------------
CREATE TABLE gig_favourite (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    requester_user_id    BIGINT    NOT NULL,
    gig_worker_profile_id BIGINT    NOT NULL,
    favourited_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_favourite_requester FOREIGN KEY (requester_user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_favourite_worker FOREIGN KEY (gig_worker_profile_id)
        REFERENCES gig_worker_profile(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_gig_favourite_requester_worker UNIQUE (requester_user_id, gig_worker_profile_id)
);

CREATE INDEX idx_gig_favourite_requester ON gig_favourite (requester_user_id);
CREATE INDEX idx_gig_favourite_worker ON gig_favourite (gig_worker_profile_id);
CREATE INDEX idx_gig_favourite_deleted ON gig_favourite (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_favourite IS 'Gig marketplace: favourite gig workers (Section 4 Tier 1 lists and blacklists). Personal. Soft-deleted.';

-- -----------------------------------------------------------------------------
CREATE TABLE gig_blacklist (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    requester_user_id    BIGINT    NOT NULL,
    gig_worker_profile_id BIGINT    NOT NULL,
    blacklisted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    blacklisted_by_user_id BIGINT    NOT NULL,
    reason               TEXT      NULL,
    is_active            BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_blacklist_requester FOREIGN KEY (requester_user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_blacklist_worker FOREIGN KEY (gig_worker_profile_id)
        REFERENCES gig_worker_profile(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_blacklist_blacklisted_by FOREIGN KEY (blacklisted_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_gig_blacklist_requester_worker UNIQUE (requester_user_id, gig_worker_profile_id)
);

CREATE INDEX idx_gig_blacklist_requester ON gig_blacklist (requester_user_id);
CREATE INDEX idx_gig_blacklist_worker ON gig_blacklist (gig_worker_profile_id);
CREATE INDEX idx_gig_blacklist_active ON gig_blacklist (requester_user_id, gig_worker_profile_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_gig_blacklist_deleted ON gig_blacklist (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_blacklist IS 'Gig marketplace: blacklists for gig workers (Section 4 Tier 1 lists and blacklists). Personal. Soft-deleted.';

COMMENT ON COLUMN gig_blacklist.reason IS 'Nullable = no reason recorded.';

-- -----------------------------------------------------------------------------
-- GIG RATINGS
-- Tier 1: ratings (requesters rate completed gigs).
-- Relationship:
--   gig_assignment 1..1 gig_rating
--   users (requester) 1..* gig_rating
-- -----------------------------------------------------------------------------
CREATE TABLE gig_rating (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gig_assignment_id    BIGINT    NOT NULL,
    rating_by_user_id    BIGINT    NOT NULL,
    rating_value         NUMERIC(3,1) NOT NULL,
    rating_text          TEXT      NULL,
    rated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_gig_rating_assignment FOREIGN KEY (gig_assignment_id)
        REFERENCES gig_assignment(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gig_rating_rater FOREIGN KEY (rating_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_gig_rating_value CHECK (rating_value >= 1 AND rating_value <= 5)
);

CREATE INDEX idx_gig_rating_assignment ON gig_rating (gig_assignment_id);
CREATE INDEX idx_gig_rating_rater ON gig_rating (rating_by_user_id);
CREATE INDEX idx_gig_rating_deleted ON gig_rating (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE gig_rating IS 'Gig marketplace: ratings (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN gig_rating.rating_value IS 'Rating value 1..5 (Rule Group 3 ratio domain with stated range).';

COMMENT ON COLUMN gig_rating.rating_text IS 'Nullable = no text feedback.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Gig marketplace (Milestone 8, B29)
--   job_requirement 1..1 gig_request_detail
--   candidate_identity 1..1 gig_worker_profile (optional link)
--   gig_worker_profile 1..* gig_worker_availability
--   gig_request_detail 1..* gig_application
--   gig_worker_profile 1..* gig_application
--   users (applicant) 1..* gig_application
--   gig_application 1..1 gig_assignment
--   gig_assignment 1..1 gig_handoff_reference
--   gig_assignment 1..* gig_earnings_reference
--   users (requester) 1..* gig_favourite
--   gig_worker_profile 1..* gig_favourite
--   users (requester) 1..* gig_blacklist
--   gig_worker_profile 1..* gig_blacklist
--   gig_assignment 1..1 gig_rating
--   users (rater) 1..* gig_rating
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new gig entities beyond the docket list. Decisions taken:
--   1. gig_request_detail is the companion to job_requirement so gig-specific
--      pricing/windows/handoff/fulfillment fields do not pollute the core job
--      table, while still sharing the job/application model as chosen.
--   2. gig_worker_profile is separate from candidate_identity as the docket says
--      gig workers have a separate profile from permanent and temporary candidates.
--   3. gig_worker_availability non-overlap rule (B35) is enforced by a CHECK on
--      start/end within a row plus a stated application/trigger rule for
--      cross-row non-overlap per gig worker; the exact cross-row enforcement is
--      documented in 99_documentation.sql.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
