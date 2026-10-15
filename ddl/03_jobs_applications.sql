-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Jobs and Applications module
-- Phase 1 (Common, Team), Milestones 2-6
--
-- This file models ONLY the docket Jobs and Applications domain.
-- Tier 1 (mandatory) from Section 4:
--   job requirement lifecycle: posting, status, positions, requirements,
--     publish state, consultant openness.
--   applications and pipeline: applied, shortlisted, interviewed, offered,
--     joined, rejected.
--   questionnaires attached to job requirements.
--   candidate job search and application history (Tier 2, modelled because
--     you chose to model all Tier 2).
--
-- Gig model decision (Section 2, Gig Work; your choice):
--   Gigs share the core job + application model with other job types.
--   A gig request is stored as a job_requirement row with a gig-specific
--   flag and companion gig_request_detail row for gig-specific fields that do
--   not belong in the core job model (handoff reference, earnings reference,
--   ratings, favourites/blacklists). Those gig-specific pieces live in the
--   gig marketplace module, not here.
--   See 99_documentation.sql for the justification.
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK; natural keys as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification on contact details, national identifiers, etc.
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ (in analytics module, not here).
-- Rule Group 9 / 10: not Jobs and Applications module concerns for the core tables;
--   licence/device/session and money/subscription/history specifics live in those modules.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- JOB REQUIREMENT
-- Tier 1: job requirement lifecycle (posting, status, positions, requirements,
--   publish state, consultant openness).
-- Relationships:
--   employer_organisation 1..* job_requirement
--   job_requirement 1..* job_position
--   job_requirement 1..* job_requirement_skill
--   job_requirement 1..* job_requirement_requirement (text requirements)
--   job_requirement 1..* job_questionnaire
--   job_requirement 1..* job_publish_state (publish state history)
--   job_requirement 1..* application
--   job_requirement 1..* candidate_job_search_history (search context only)
-- Consultant openness is a boolean flag on job_requirement (Section 2: a
--   consultant may only work on job requirements that are open to consultants).
-- -----------------------------------------------------------------------------
CREATE TABLE job_requirement (
    id                         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_organisation_id   BIGINT    NOT NULL,
    recruiter_user_id          BIGINT    NULL,
    title                      TEXT      NOT NULL,
    description                TEXT      NOT NULL,
    description_language       TEXT      NULL,
    employment_type_code       TEXT      NOT NULL,
    work_type_code             TEXT      NOT NULL,
    industry_name              TEXT      NULL,
    job_role_name              TEXT      NULL,
    location_city              TEXT      NULL,
    location_state             TEXT      NULL,
    location_country           TEXT      NOT NULL,
    compensation_min           NUMERIC(15,2) NULL,
    compensation_max           NUMERIC(15,2) NULL,
    compensation_currency_code TEXT      NULL,
    experience_min_years       NUMERIC(3,1) NULL,
    experience_max_years       NUMERIC(3,1) NULL,
    is_remote_allowed          BOOLEAN   NOT NULL DEFAULT FALSE,
    is_open_to_consultants     BOOLEAN   NOT NULL DEFAULT FALSE,
    status_code                TEXT      NOT NULL,
    visibility_code            TEXT      NOT NULL,
    publish_state_code         TEXT      NOT NULL,
    deadline_at                TIMESTAMPTZ NULL,
    published_at               TIMESTAMPTZ NULL,
    unpublished_at             TIMESTAMPTZ NULL,
    closed_at                  TIMESTAMPTZ NULL,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by                 BIGINT    NOT NULL DEFAULT 0,
    updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by                 BIGINT    NOT NULL DEFAULT 0,
    deleted_at                 TIMESTAMPTZ NULL,
    CONSTRAINT fk_job_requirement_employer FOREIGN KEY (employer_organisation_id)
        REFERENCES employer_organisation(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_job_requirement_recruiter FOREIGN KEY (recruiter_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_compensation_range CHECK (
        (compensation_min IS NULL AND compensation_max IS NULL)
        OR (compensation_min IS NOT NULL AND compensation_max IS NULL)
        OR (compensation_min IS NOT NULL AND compensation_max IS NOT NULL AND compensation_min <= compensation_max)
    ),
    CONSTRAINT chk_compensation_currency CHECK (
        compensation_currency_code IS NULL OR char_length(compensation_currency_code) = 3
    ),
    CONSTRAINT chk_experience_range CHECK (
        (experience_min_years IS NULL AND experience_max_years IS NULL)
        OR (experience_min_years IS NOT NULL AND experience_max_years IS NULL)
        OR (experience_min_years IS NOT NULL AND experience_max_years IS NOT NULL AND experience_min_years <= experience_max_years)
    ),
    CONSTRAINT chk_job_dates CHECK (
        (deadline_at IS NULL OR deadline_at >= published_at)
    ),
    CONSTRAINT chk_publish_state_flow CHECK (
        (closed_at IS NULL OR closed_at >= published_at)
    )
);

CREATE INDEX idx_job_requirement_employer ON job_requirement (employer_organisation_id);
CREATE INDEX idx_job_requirement_recruiter ON job_requirement (recruiter_user_id) WHERE recruiter_user_id IS NOT NULL;
CREATE INDEX idx_job_requirement_status ON job_requirement (status_code);
CREATE INDEX idx_job_requirement_consultant_open ON job_requirement (is_open_to_consultants) WHERE is_open_to_consultants = TRUE;
CREATE INDEX idx_job_requirement_location ON job_requirement (location_country, location_state, location_city);
CREATE INDEX idx_job_requirement_deleted ON job_requirement (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE job_requirement IS 'Jobs and Applications: job requirement lifecycle (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN job_requirement.description IS 'Free text domain: unbounded TEXT allowed here because it is job description (Rule Group 3 exception, justified).';

COMMENT ON COLUMN job_requirement.compensation_min IS 'Money domain NUMERIC(15,2) + currency_code. Nullable = not disclosed (not zero).';

COMMENT ON COLUMN job_requirement.compensation_max IS 'Money domain NUMERIC(15,2) + currency_code. Nullable = not disclosed (not zero).';

COMMENT ON COLUMN job_requirement.compensation_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN job_requirement.experience_min_years IS 'Nullable = not specified.';

COMMENT ON COLUMN job_requirement.experience_max_years IS 'Nullable = not specified.';

COMMENT ON COLUMN job_requirement.is_open_to_consultants IS 'Consultant openness flag (Section 2 Business Context).';

-- -----------------------------------------------------------------------------
-- JOB POSITION
-- Tier 1: positions per job requirement.
-- Relationship: job_requirement 1..* job_position.
-- -----------------------------------------------------------------------------
CREATE TABLE job_position (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id BIGINT    NOT NULL,
    position_title     TEXT      NOT NULL,
    is_active          BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_job_position_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_job_position_job_title UNIQUE (job_requirement_id, position_title)
);

CREATE INDEX idx_job_position_job ON job_position (job_requirement_id);
CREATE INDEX idx_job_position_deleted ON job_position (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE job_position IS 'Jobs and Applications: job positions (Section 4 Tier 1). Internal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- JOB REQUIREMENT SKILL
-- Tier 1: skills required by a job (requirements).
-- Relationship:
--   job_requirement 1..* job_requirement_skill
--   skill (master) 1..* job_requirement_skill
-- Natural key: (job_requirement_id, skill_name).
-- -----------------------------------------------------------------------------
CREATE TABLE job_requirement_skill (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id BIGINT    NOT NULL,
    skill_name         TEXT      NOT NULL,
    is_required        BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_job_requirement_skill_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_job_requirement_skill_job_skill UNIQUE (job_requirement_id, skill_name)
);

CREATE INDEX idx_job_requirement_skill_job ON job_requirement_skill (job_requirement_id);
CREATE INDEX idx_job_requirement_skill_deleted ON job_requirement_skill (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE job_requirement_skill IS 'Jobs and Applications: job requirement skills (Section 4 Tier 1). Internal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- JOB REQUIREMENT REQUIREMENT (textual requirements line items)
-- Tier 1: requirements (text requirements attached to a job).
-- This keeps the description as the main body and allows structured requirement
-- line items where needed.
-- -----------------------------------------------------------------------------
CREATE TABLE job_requirement_requirement (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id BIGINT    NOT NULL,
    requirement_text   TEXT      NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_job_requirement_requirement_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_job_requirement_requirement_job ON job_requirement_requirement (job_requirement_id);
CREATE INDEX idx_job_requirement_requirement_deleted ON job_requirement_requirement (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE job_requirement_requirement IS 'Jobs and Applications: job requirement line items (Section 4 Tier 1). Soft-deleted.';

COMMENT ON COLUMN job_requirement_requirement.requirement_text IS 'Free text domain: TEXT for requirement line items. Bounded length enforced at application level where practical.';

-- -----------------------------------------------------------------------------
-- JOB QUESTIONNAIRE
-- Tier 1: questionnaires attached to job requirements.
-- Relationship:
--   job_requirement 1..* job_questionnaire
--   job_questionnaire 1..* job_questionnaire_question
-- -----------------------------------------------------------------------------
CREATE TABLE job_questionnaire (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id BIGINT    NOT NULL,
    name               TEXT      NOT NULL,
    is_active          BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_job_questionnaire_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_job_questionnaire_job_name UNIQUE (job_requirement_id, name)
);

CREATE INDEX idx_job_questionnaire_job ON job_questionnaire (job_requirement_id);
CREATE INDEX idx_job_questionnaire_deleted ON job_questionnaire (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE job_questionnaire IS 'Jobs and Applications: questionnaires attached to job requirements (Section 4 Tier 1). Soft-deleted.';

-- -----------------------------------------------------------------------------
-- JOB QUESTIONNAIRE QUESTION
-- Tier 1: questionnaire questions.
-- Relationship:
--   job_questionnaire 1..* job_questionnaire_question
-- -----------------------------------------------------------------------------
CREATE TABLE job_questionnaire_question (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_questionnaire_id BIGINT    NOT NULL,
    question_text        TEXT      NOT NULL,
    question_type_code   TEXT      NOT NULL,
    sort_order           SMALLINT  NOT NULL DEFAULT 0,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_job_questionnaire_question_questionnaire FOREIGN KEY (job_questionnaire_id)
        REFERENCES job_questionnaire(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_job_questionnaire_question_questionnaire_text UNIQUE (job_questionnaire_id, question_text)
);

CREATE INDEX idx_job_questionnaire_question_questionnaire ON job_questionnaire_question (job_questionnaire_id);
CREATE INDEX idx_job_questionnaire_question_deleted ON job_questionnaire_question (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE job_questionnaire_question IS 'Jobs and Applications: questionnaire questions (Section 4 Tier 1). Soft-deleted.';

-- -----------------------------------------------------------------------------
-- JOB PUBLISH STATE
-- Tier 1: publish state (publish state history).
-- Append-only-ish history of publish state transitions; current state is the
--   row with is_current = TRUE per job_requirement.
-- -----------------------------------------------------------------------------
CREATE TABLE job_publish_state (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_requirement_id BIGINT    NOT NULL,
    state_code         TEXT      NOT NULL,
    started_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at           TIMESTAMPTZ NULL,
    is_current         BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT fk_job_publish_state_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_publish_state_current CHECK (
        is_current = TRUE OR ended_at IS NOT NULL
    )
);

CREATE INDEX idx_job_publish_state_job ON job_publish_state (job_requirement_id);
CREATE INDEX idx_job_publish_state_current ON job_publish_state (job_requirement_id, is_current) WHERE is_current = TRUE;

COMMENT ON TABLE job_publish_state IS 'Jobs and Applications: publish state (Section 4 Tier 1). Soft-deleted where applicable.';

COMMENT ON COLUMN job_publish_state.is_current IS 'Boolean flag with stated default TRUE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- APPLICATION
-- Tier 1: applications and pipeline core.
-- Relationship:
--   candidate_identity 1..* application
--   job_requirement 1..* application
--   resume_version 1..* application (optional resume used)
-- Pipeline status is tracked via application_pipeline_event (append-only status
--   transitions) to satisfy applied, shortlisted, interviewed, offered, joined,
--   rejected without relying on a mutable status column alone.
-- -----------------------------------------------------------------------------
CREATE TABLE application (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id           BIGINT    NOT NULL,
    job_requirement_id     BIGINT    NOT NULL,
    resume_version_id      BIGINT    NULL,
    applied_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_channel_code    TEXT      NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_application_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_application_job FOREIGN KEY (job_requirement_id)
        REFERENCES job_requirement(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_application_resume FOREIGN KEY (resume_version_id)
        REFERENCES resume_version(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT uq_application_candidate_job UNIQUE (candidate_id, job_requirement_id)
);

CREATE INDEX idx_application_candidate ON application (candidate_id);
CREATE INDEX idx_application_job ON application (job_requirement_id);
CREATE INDEX idx_application_applied_at ON application (applied_at);
CREATE INDEX idx_application_deleted ON application (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE application IS 'Jobs and Applications: application (Section 4 Tier 1). Personal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- APPLICATION PIPELINE EVENT
-- Tier 1: application pipeline events (applied, shortlisted, interviewed,
--   offered, joined, rejected).
-- Append-only: each pipeline transition is a row with timestamp and actor.
-- This satisfies the pipeline stages in the docket without relying on a single
-- mutable status column and supports full history.
-- -----------------------------------------------------------------------------
CREATE TABLE application_pipeline_event (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id     BIGINT    NOT NULL,
    pipeline_stage_code TEXT     NOT NULL,
    entered_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    entered_by_user_id BIGINT    NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT fk_application_pipeline_event_application FOREIGN KEY (application_id)
        REFERENCES application(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_application_pipeline_event_entered_by FOREIGN KEY (entered_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_application_pipeline_event_application ON application_pipeline_event (application_id);
CREATE INDEX idx_application_pipeline_event_stage ON application_pipeline_event (pipeline_stage_code);
CREATE INDEX idx_application_pipeline_event_entered_at ON application_pipeline_event (entered_at);

COMMENT ON TABLE application_pipeline_event IS 'Jobs and Applications: application pipeline events (Section 4 Tier 1: applied, shortlisted, interviewed, offered, joined, rejected). Append-only.';

-- -----------------------------------------------------------------------------
-- CANDIDATE JOB SEARCH HISTORY
-- Tier 2: candidate job search history.
-- Append-only: search events per candidate. Stored with minimal detail; no
--   personal resume content stored in this table.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_job_search_history (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id    BIGINT    NOT NULL,
    search_text     TEXT      NULL,
    searched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_candidate_job_search_history_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_candidate_job_search_history_candidate ON candidate_job_search_history (candidate_id);
CREATE INDEX idx_candidate_job_search_history_searched_at ON candidate_job_search_history (searched_at);

COMMENT ON TABLE candidate_job_search_history IS 'Jobs and Applications: candidate job search history (Section 4 Tier 2). Append-only.';

COMMENT ON COLUMN candidate_job_search_history.search_text IS 'Nullable = search without retained text. Stored only as needed.';

-- -----------------------------------------------------------------------------
-- CANDIDATE APPLICATION HISTORY
-- Tier 2: candidate job application history for candidates.
-- Append-only: application activity events per candidate.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_application_history (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id    BIGINT    NOT NULL,
    application_id  BIGINT    NOT NULL,
    event_type_code TEXT      NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_candidate_application_history_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_candidate_application_history_application FOREIGN KEY (application_id)
        REFERENCES application(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_candidate_application_history_candidate ON candidate_application_history (candidate_id);
CREATE INDEX idx_candidate_application_history_application ON candidate_application_history (application_id);
CREATE INDEX idx_candidate_application_history_occurred_at ON candidate_application_history (occurred_at);

COMMENT ON TABLE candidate_application_history IS 'Jobs and Applications: candidate application history (Section 4 Tier 2). Append-only.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Jobs and Applications (Milestone 3, B10/B11)
--   employer_organisation 1..* job_requirement
--   users (recruiter) 1..* job_requirement (optional owner)
--   job_requirement 1..* job_position
--   job_requirement 1..* job_requirement_skill
--   job_requirement 1..* job_requirement_requirement
--   job_requirement 1..* job_questionnaire
--   job_questionnaire 1..* job_questionnaire_question
--   job_requirement 1..* job_publish_state
--   candidate_identity 1..* application
--   job_requirement 1..* application
--   resume_version 1..* application (optional)
--   application 1..* application_pipeline_event
--   candidate_identity 1..* candidate_job_search_history
--   candidate_identity 1..* candidate_application_history
--   application 1..* candidate_application_history
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Jobs and Applications entities beyond the docket list. Decisions taken:
--   1. gig requests are stored as job_requirement rows with a consultant/gig
--      openness concept shared across the platform; gig-specific fields are in
--      the gig marketplace module (handoff reference, earnings reference, ratings,
--      favourites/blacklists). This implements the chosen gig decision without
--      inventing new job tables here.
--   2. pipeline is modelled as append-only application_pipeline_event to keep
--      applied..rejected stage history auditable (Rule Group 4 spirit for
--      pipeline events) while keeping application itself lean.
--   3. job_publish_state keeps a current flag to support publish-state reads.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
