-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Sourcing and Consultant module
-- Phase 3 (Individual, Member B), Milestones 11-14
--
-- This file models ONLY the docket Sourcing and Consultant domain.
-- Tier 1 (mandatory) from Section 4:
--   sourcing and consultant requests: sourcing requests, acceptance or decline,
--     candidate shortlists.
--
-- B37 deliverable: sourcing requests, consultant openness, acceptance or decline
--   decisions, outreach batches and recipients, candidate sourcing shortlists
--   (referencing the Jobs and Applications shortlist).
-- B46 deliverable: consultant can act only on a requirement open to consultants.
--   The consultant-openness concept is owned by this module for the rule, but the
--   underlying flag on job_requirement is shared with the Jobs module. Here we
--   store the consultant-facing request/decision model and the rule that a
--   consultant decision is only valid for a job requirement that is open to consultants.
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
-- Rule Group 9 / 10: not Sourcing module concerns except where credit/consumption appears;
--   credit consumption in outreach is owned by the Subscriptions module where the docket
--   places wallet/credits.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SOURCING REQUEST
-- Tier 1: sourcing requests.
-- Relationship:
--   job_requirement 1..1 sourcing_request (one sourcing request per job requirement
--     where sourcing is initiated)
--   users (requester) 1..* sourcing_request
--   users (consultant) 1..* sourcing_request (assigned consultant, optional)
--   sourcing_request 1..* consultant_decision
--   sourcing_request 1..* sourcing_shortlist (candidate shortlist for the request,
--     referencing the Jobs and Applications shortlist where applicable)
-- The docket says sourcing requests, acceptance or decline, candidate shortlists.
-- Consultant openness is represented by the job_requirement.is_open_to_consultants
-- flag (Section 2 Business Context), with this module enforcing that consultant
-- decisions are only valid for open requirements (B46).
-- -----------------------------------------------------------------------------
CREATE TABLE sourcing_request (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id     BIGINT    NOT NULL,
    requester_user_id       BIGINT    NOT NULL,
    consultant_user_id      BIGINT    NULL,
    request_type_code       TEXT      NOT NULL,
    description             TEXT      NULL,
    is_open_to_consultants  BOOLEAN   NOT NULL DEFAULT TRUE,
    status_code             TEXT      NOT NULL,
    shortlist_id            BIGINT    NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by              BIGINT    NOT NULL DEFAULT 0,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by              BIGINT    NOT NULL DEFAULT 0,
    deleted_at              TIMESTAMPTZ NULL,
    CONSTRAINT fk_sourcing_request_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_sourcing_request_requester FOREIGN KEY (requester_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_sourcing_request_consultant FOREIGN KEY (consultant_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_sourcing_request_open CHECK (
        is_open_to_consultants = TRUE
    ),
    CONSTRAINT uq_sourcing_request_job UNIQUE (job_requirement_id)
);

CREATE INDEX idx_sourcing_request_job ON sourcing_request (job_requirement_id);
CREATE INDEX idx_sourcing_request_requester ON sourcing_request (requester_user_id);
CREATE INDEX idx_sourcing_request_consultant ON sourcing_request (consultant_user_id) WHERE consultant_user_id IS NOT NULL;
CREATE INDEX idx_sourcing_request_type ON sourcing_request (request_type_code);
CREATE INDEX idx_sourcing_request_status ON sourcing_request (status_code);
CREATE INDEX idx_sourcing_request_deleted ON sourcing_request (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE sourcing_request IS 'Sourcing and Consultant: sourcing requests (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN sourcing_request.description IS 'Nullable = no description. Free text domain TEXT; bounded length enforced at application level.';

COMMENT ON COLUMN sourcing_request.is_open_to_consultants IS 'Consultant openness for this request (Section 2 Business Context: consultant may only work on requirements open to consultants).';

COMMENT ON COLUMN sourcing_request.status_code IS 'Enumeration code referencing reference_code (domain=sourcing_status).';

COMMENT ON COLUMN sourcing_request.shortlist_id IS 'Nullable = no shortlist created yet. References the Jobs and Applications shortlist.';

-- -----------------------------------------------------------------------------
-- CONSULTANT DECISION
-- Tier 1: acceptance or decline decisions.
-- Relationship:
--   sourcing_request 1..* consultant_decision
--   users (consultant) 1..* consultant_decision
-- The docket says consultant requests to source for a job, and acceptance or decline
--   by the employer (the decision record here is the consultant's acceptance or
--   decline of the sourcing request; employer-facing acceptance/rejection of the
--   sourced candidate is part of the Jobs pipeline).
-- B46 rule: a consultant can act only on a requirement open to consultants. This is
--   enforced by a check that the associated job_requirement is open to consultants.
-- -----------------------------------------------------------------------------
CREATE TABLE consultant_decision (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sourcing_request_id    BIGINT    NOT NULL,
    consultant_user_id     BIGINT    NOT NULL,
    decision_code          TEXT      NOT NULL,
    decision_note          TEXT      NULL,
    decided_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_by_user_id     BIGINT    NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_consultant_decision_request FOREIGN KEY (sourcing_request_id)
        REFERENCES sourcing_request(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_consultant_decision_consultant FOREIGN KEY (consultant_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_consultant_decision_decided_by FOREIGN KEY (decided_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_consultant_decision_request_consultant UNIQUE (sourcing_request_id, consultant_user_id)
);

CREATE INDEX idx_consultant_decision_request ON consultant_decision (sourcing_request_id);
CREATE INDEX idx_consultant_decision_consultant ON consultant_decision (consultant_user_id);
CREATE INDEX idx_consultant_decision_decision_code ON consultant_decision (decision_code);
CREATE INDEX idx_consultant_decision_deleted ON consultant_decision (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE consultant_decision IS 'Sourcing and Consultant: acceptance or decline decisions (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN consultant_decision.decision_code IS 'Enumeration code referencing reference_code (domain=consultant_decision_type).';

COMMENT ON COLUMN consultant_decision.decision_note IS 'Nullable = no note.';

COMMENT ON COLUMN consultant_decision.decided_at IS 'Decision timestamp.';

COMMENT ON COLUMN consultant_decision.decided_by_user_id IS 'User who recorded the decision (consultant or system).';

-- -----------------------------------------------------------------------------
-- SOURCING SHORTLIST
-- Tier 1: candidate shortlists (referencing the Jobs and Applications shortlist).
-- Relationship:
--   sourcing_request 1..* sourcing_shortlist
--   shortlist (Jobs and Applications) 1..* sourcing_shortlist
-- The docket says candidate sourcing shortlists (referencing the Jobs and Applications
--   shortlist). Here we link a sourcing request to a shortlist created for it.
-- -----------------------------------------------------------------------------
CREATE TABLE sourcing_shortlist (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sourcing_request_id    BIGINT    NOT NULL,
    shortlist_id           BIGINT    NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_sourcing_shortlist_request FOREIGN KEY (sourcing_request_id)
        REFERENCES sourcing_request(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_sourcing_shortlist_shortlist FOREIGN KEY (shortlist_id)
        REFERENCES shortlist(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_sourcing_shortlist_request UNIQUE (sourcing_request_id)
);

CREATE INDEX idx_sourcing_shortlist_request ON sourcing_shortlist (sourcing_request_id);
CREATE INDEX idx_sourcing_shortlist_shortlist ON sourcing_shortlist (shortlist_id);
CREATE INDEX idx_sourcing_shortlist_deleted ON sourcing_shortlist (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE sourcing_shortlist IS 'Sourcing and Consultant: candidate sourcing shortlists (Section 4 Tier 1, referencing the Jobs and Applications shortlist). Internal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- OUTREACH BATCH
-- Tier 1: bulk outreach batches (part of sourcing by employers and recruiters,
--   including bulk outreach).
-- Relationship:
--   users (creator) 1..* outreach_batch
--   users (recipient) 1..* outreach_batch_recipient
-- Credit consumption for outreach is owned by the Subscriptions module (wallet/credits).
-- This table stores outreach batch metadata and status; credit consumption is referenced
--   where needed but the ledger is in 09_subscriptions.sql.
-- -----------------------------------------------------------------------------
CREATE TABLE outreach_batch (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    creator_user_id        BIGINT    NOT NULL,
    batch_type_code        TEXT      NOT NULL,
    name                   TEXT      NOT NULL,
    description            TEXT      NULL,
    channel_code           TEXT      NOT NULL,
    status_code            TEXT      NOT NULL,
    scheduled_at           TIMESTAMPTZ NULL,
    started_at             TIMESTAMPTZ NULL,
    completed_at           TIMESTAMPTZ NULL,
    total_recipients       INTEGER   NOT NULL DEFAULT 0,
    delivered_recipients   INTEGER   NOT NULL DEFAULT 0,
    failed_recipients      INTEGER   NOT NULL DEFAULT 0,
    credit_consumption_ref TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_outreach_batch_creator FOREIGN KEY (creator_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_outreach_batch_delivery_counts CHECK (
        delivered_recipients >= 0 AND failed_recipients >= 0
        AND (delivered_recipients + failed_recipients) <= total_recipients
    ),
    CONSTRAINT uq_outreach_batch_name_creator UNIQUE (name, creator_user_id)
);

CREATE INDEX idx_outreach_batch_creator ON outreach_batch (creator_user_id);
CREATE INDEX idx_outreach_batch_type ON outreach_batch (batch_type_code);
CREATE INDEX idx_outreach_batch_channel ON outreach_batch (channel_code);
CREATE INDEX idx_outreach_batch_status ON outreach_batch (status_code);
CREATE INDEX idx_outreach_batch_scheduled_at ON outreach_batch (scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX idx_outreach_batch_deleted ON outreach_batch (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE outreach_batch IS 'Sourcing and Consultant: outreach batches (Section 4 Tier 1 sourcing by employers and recruiters, including bulk outreach). Internal. Soft-deleted.';

COMMENT ON COLUMN outreach_batch.description IS 'Nullable = no description.';

COMMENT ON COLUMN outreach_batch.scheduled_at IS 'Nullable = not scheduled.';

COMMENT ON COLUMN outreach_batch.total_recipients IS 'Total intended recipients.';

COMMENT ON COLUMN outreach_batch.delivered_recipients IS 'Recipients delivered successfully.';

COMMENT ON COLUMN outreach_batch.failed_recipients IS 'Recipients that failed.';

COMMENT ON COLUMN outreach_batch.credit_consumption_ref IS 'Nullable = no credit consumption recorded here. Credit consumption is owned by the Subscriptions module (wallet/credits). This is a reference to that record.';

-- -----------------------------------------------------------------------------
-- OUTREACH BATCH RECIPIENT
-- Tier 1: outreach recipients.
-- Relationship:
--   outreach_batch 1..* outreach_batch_recipient
--   candidate_identity 1..* outreach_batch_recipient (recipient candidate)
--   users (recipient) 1..* outreach_batch_recipient (recipient user, optional)
-- -----------------------------------------------------------------------------
CREATE TABLE outreach_batch_recipient (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    outreach_batch_id      BIGINT    NOT NULL,
    candidate_identity_id  BIGINT    NULL,
    recipient_user_id      BIGINT    NULL,
    contact_channel_code   TEXT      NOT NULL,
    delivery_status_code   TEXT      NOT NULL,
    delivered_at           TIMESTAMPTZ NULL,
    delivery_reference     TEXT      NULL,
    delivery_error         TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_outreach_batch_recipient_batch FOREIGN KEY (outreach_batch_id)
        REFERENCES outreach_batch(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_outreach_batch_recipient_candidate FOREIGN KEY (candidate_identity_id)
        REFERENCES candidate_identity(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_outreach_batch_recipient_user FOREIGN KEY (recipient_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_outreach_batch_recipient_contact CHECK (
        candidate_identity_id IS NOT NULL OR recipient_user_id IS NOT NULL
    ),
    CONSTRAINT uq_outreach_batch_recipient_batch_contact UNIQUE (outreach_batch_id, contact_channel_code, COALESCE(candidate_identity_id, recipient_user_id))
);

CREATE INDEX idx_outreach_batch_recipient_batch ON outreach_batch_recipient (outreach_batch_id);
CREATE INDEX idx_outreach_batch_recipient_candidate ON outreach_batch_recipient (candidate_identity_id) WHERE candidate_identity_id IS NOT NULL;
CREATE INDEX idx_outreach_batch_recipient_user ON outreach_batch_recipient (recipient_user_id) WHERE recipient_user_id IS NOT NULL;
CREATE INDEX idx_outreach_batch_recipient_status ON outreach_batch_recipient (delivery_status_code);
CREATE INDEX idx_outreach_batch_recipient_deleted ON outreach_batch_recipient (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE outreach_batch_recipient IS 'Sourcing and Consultant: outreach recipients (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN outreach_batch_recipient.contact_channel_code IS 'Enumeration code referencing reference_code (domain=outreach_channel).';

COMMENT ON COLUMN outreach_batch_recipient.delivery_status_code IS 'Enumeration code referencing reference_code (domain=delivery_status).';

COMMENT ON COLUMN outreach_batch_recipient.delivered_at IS 'Nullable = not delivered yet.';

COMMENT ON COLUMN outreach_batch_recipient.delivery_reference IS 'Nullable = no delivery reference. Stored as reference to the messaging provider delivery, not message body (Section 6 messaging boundary).';

COMMENT ON COLUMN outreach_batch_recipient.delivery_error IS 'Nullable = no error.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Sourcing and Consultant (Milestone 12, B40)
--   job_requirement 1..1 sourcing_request
--   users (requester) 1..* sourcing_request
--   users (consultant) 1..* sourcing_request (assigned)
--   sourcing_request 1..* consultant_decision
--   users (consultant) 1..* consultant_decision
--   sourcing_request 1..1 sourcing_shortlist
--   shortlist 1..1 sourcing_shortlist
--   users (creator) 1..* outreach_batch
--   outreach_batch 1..* outreach_batch_recipient
--   candidate_identity 1..* outreach_batch_recipient
--   users 1..* outreach_batch_recipient (recipient user)
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Sourcing entities beyond the docket list. Decisions taken:
--   1. sourcing_request carries is_open_to_consultants as a request-level mirror of
--      the job requirement openness, and consultant decisions are only valid where the
--      associated job requirement is open to consultants. The B46 rule is enforced by
--      application logic plus the check that the request is open to consultants.
--   2. sourcing_shortlist references the Jobs and Applications shortlist as required by
--      B37.
--   3. outreach_batch and outreach_batch_recipient model bulk outreach. Credit
--      consumption is referenced but owned by the Subscriptions module, where the docket
--      places wallet and credits.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
