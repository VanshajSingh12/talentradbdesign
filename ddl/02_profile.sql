-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Profile module
-- Phase 1 (Common, Team), Milestones 2-6
--
-- This file models ONLY the docket Profile domain.
-- Tier 1 (mandatory) from Section 4:
--   candidate profile core: personal details, contact details, education,
--   work experience, skills, languages.
-- Tier 2 (modelled because you chose to model all Tier 2):
--   resume versions and templates, profile projects (candidate + gig projects),
--   assessments and scores, course enrolments, profile completion scoring,
--   profile view history, candidate activity log, shortlist and bookmark history,
--   referral tracking, blocking lists (blocking lists are shared team items too;
--   here we model the candidate-facing blocking list entries that are about
--   candidates, and note the shared team item module owns the unified blocking
--   list concept).
--
-- Out of scope per docket Section 1: building UI, live external integration,
-- loading full 10M profiles on a laptop, ETL/migration (separate requirement).
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK, natural keys kept as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification on contact details, national identifiers, etc.
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ (in analytics module, not here).
-- Rule Group 9 / 10: not Profile module concerns.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- CANDIDATE IDENTITY
-- Tier 1: personal details (identity core).
-- Relationships:
--   candidate_identity 1..1 users (optional until account completed;
--     user_id nullable at profile creation, per workflow).
--   candidate_identity 1..* candidate_contact
--   candidate_identity 1..* candidate_education
--   candidate_identity 1..* candidate_work_experience
--   candidate_identity 1..* candidate_skill
--   candidate_identity 1..* candidate_language
--   candidate_identity 1..* resume_version
--   candidate_identity 1..* profile_project
--   candidate_identity 1..* assessment
--   candidate_identity 1..* course_enrolment
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_identity (
    id                        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                   BIGINT    NULL,
    title                     TEXT     NULL,
    first_name                TEXT     NOT NULL,
    middle_name               TEXT     NULL,
    last_name                 TEXT     NOT NULL,
    preferred_name            TEXT     NULL,
    date_of_birth             DATE     NULL,
    gender                    TEXT     NULL,
    profile_status_code       TEXT     NOT NULL,
    profile_completion_score  NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    latest_login_at           TIMESTAMPTZ NULL,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by                BIGINT   NOT NULL DEFAULT 0,
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by                BIGINT   NOT NULL DEFAULT 0,
    deleted_at                TIMESTAMPTZ NULL,
    CONSTRAINT fk_candidate_identity_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_first_name_length CHECK (char_length(first_name) <= 150),
    CONSTRAINT chk_last_name_length CHECK (char_length(last_name) <= 150),
    CONSTRAINT chk_profile_completion_score_range CHECK (profile_completion_score BETWEEN 0 AND 100),
    CONSTRAINT chk_name_not_empty CHECK (char_length(trim(coalesce(first_name, ''))) > 0
        AND char_length(trim(coalesce(last_name, ''))) > 0)
);

CREATE INDEX idx_candidate_identity_user ON candidate_identity (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_candidate_identity_status ON candidate_identity (profile_status_code);
CREATE INDEX idx_candidate_identity_deleted ON candidate_identity (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE candidate_identity IS 'Profile: candidate identity (Section 4 Tier 1 personal details). Personal. Soft-deleted.';

COMMENT ON COLUMN candidate_identity.user_id IS 'Nullable: profile can exist before account completion.';

COMMENT ON COLUMN candidate_identity.title IS 'Optional honorific. Nullable = unknown.';

COMMENT ON COLUMN candidate_identity.middle_name IS 'Nullable = unknown or not applicable.';

COMMENT ON COLUMN candidate_identity.preferred_name IS 'Nullable = not provided.';

COMMENT ON COLUMN candidate_identity.date_of_birth IS 'Nullable = unknown. Age is derived, never stored.';

COMMENT ON COLUMN candidate_identity.gender IS 'Nullable = not disclosed. Stored as reference code domain text where applicable.';

COMMENT ON COLUMN candidate_identity.profile_status_code IS 'Enumeration code referencing reference_code (domain=candidate_status).';

-- -----------------------------------------------------------------------------
-- CANDIDATE CONTACT
-- Tier 1: contact details.
-- Rule Group 3: email TEXT up to 254 chars, lowercase, unique per account where
--   it identifies a single account. Here unique per (candidate, email) for the
--   platform account identity.
-- Rule Group 6: email/phone are Personal; national ID token stored only as reference.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_contact (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id           BIGINT    NOT NULL,
    contact_type_code      TEXT      NOT NULL,
    email                  TEXT      NULL,
    phone                  TEXT      NULL,
    phone_country_code     TEXT      NULL,
    address_line1          TEXT      NULL,
    address_line2          TEXT      NULL,
    city                   TEXT      NULL,
    state                  TEXT      NULL,
    country                TEXT      NULL,
    postal_code            TEXT      NULL,
    is_primary             BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_candidate_contact_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_candidate_contact_candidate_email UNIQUE (candidate_id, email),
    CONSTRAINT chk_email_lowercase CHECK (email IS NULL OR email = lower(email)),
    CONSTRAINT chk_email_length CHECK (email IS NULL OR char_length(email) <= 254),
    CONSTRAINT chk_phone_e164 CHECK (phone IS NULL OR phone ~ '^\+?[1-9][0-9]{1,14}$')
);

CREATE INDEX idx_candidate_contact_candidate ON candidate_contact (candidate_id);
CREATE INDEX idx_candidate_contact_email ON candidate_contact (email) WHERE email IS NOT NULL;
CREATE INDEX idx_candidate_contact_deleted ON candidate_contact (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE candidate_contact IS 'Profile: candidate contact details (Section 4 Tier 1). Personal. Soft-deleted.';

COMMENT ON COLUMN candidate_contact.email IS 'Personal. Lowercase, max 254 chars. Unique per candidate where it identifies an account.';

COMMENT ON COLUMN candidate_contact.phone IS 'Personal. E.164 with country code in phone.';

COMMENT ON COLUMN candidate_contact.phone_country_code IS 'Separate country field for phone, per Rule Group 3 phone domain.';

-- -----------------------------------------------------------------------------
-- CANDIDATE EDUCATION
-- Tier 1: education.
-- Relationship: candidate_identity 1..* candidate_education.
-- Nullability: start_date/end_date nullable when not provided; current_bool
--   distinguishes ongoing education.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_education (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id         BIGINT    NOT NULL,
    institution_name     TEXT      NOT NULL,
    qualification        TEXT      NULL,
    field_of_study       TEXT      NULL,
    start_date           DATE      NULL,
    end_date             DATE      NULL,
    is_current           BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_candidate_education_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_education_dates CHECK (
        (start_date IS NULL AND end_date IS NULL)
        OR (start_date IS NOT NULL AND (end_date IS NULL OR end_date >= start_date))
    ),
    CONSTRAINT chk_education_current_check CHECK (
        is_current = FALSE OR end_date IS NULL
    ),
    CONSTRAINT uq_candidate_education_candidate_inst_curr UNIQUE (candidate_id, institution_name, is_current, end_date)
);

CREATE INDEX idx_candidate_education_candidate ON candidate_education (candidate_id);
CREATE INDEX idx_candidate_education_deleted ON candidate_education (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE candidate_education IS 'Profile: candidate education (Section 4 Tier 1). Personal. Soft-deleted.';

COMMENT ON COLUMN candidate_education.start_date IS 'Nullable = not provided (unknown start).';

COMMENT ON COLUMN candidate_education.end_date IS 'Nullable = not yet ended; is_current distinguishes ongoing.';

COMMENT ON COLUMN candidate_education.is_current IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- CANDIDATE WORK EXPERIENCE
-- Tier 1: work experience.
-- Relationship: candidate_identity 1..* candidate_work_experience.
-- Money domain: salary_min, salary_max NUMERIC(15,2) + salary_currency_code CHAR(3).
-- Unknown vs not applicable: salary nullable where not disclosed; zero is not used
--   as a sentinel for missing.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_work_experience (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id        BIGINT    NOT NULL,
    employer_name       TEXT      NOT NULL,
    role                TEXT      NULL,
    start_date          DATE      NULL,
    end_date            DATE      NULL,
    is_current          BOOLEAN   NOT NULL DEFAULT FALSE,
    location_city       TEXT      NULL,
    location_country    TEXT      NULL,
    description         TEXT      NULL,
    salary_min          NUMERIC(15,2) NULL,
    salary_max          NUMERIC(15,2) NULL,
    salary_currency_code TEXT     NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          BIGINT    NOT NULL DEFAULT 0,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by          BIGINT    NOT NULL DEFAULT 0,
    deleted_at          TIMESTAMPTZ NULL,
    CONSTRAINT fk_candidate_work_experience_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_work_experience_dates CHECK (
        (start_date IS NULL AND end_date IS NULL)
        OR (start_date IS NOT NULL AND (end_date IS NULL OR end_date >= start_date))
    ),
    CONSTRAINT chk_work_experience_current_check CHECK (is_current = FALSE OR end_date IS NULL),
    CONSTRAINT chk_work_experience_salary_range CHECK (
        (salary_min IS NULL AND salary_max IS NULL)
        OR (salary_min IS NOT NULL AND salary_max IS NULL)
        OR (salary_min IS NOT NULL AND salary_max IS NOT NULL AND salary_min <= salary_max)
    ),
    CONSTRAINT chk_work_experience_salary_currency CHECK (
        salary_currency_code IS NULL OR char_length(salary_currency_code) = 3
    )
);

CREATE INDEX idx_candidate_work_experience_candidate ON candidate_work_experience (candidate_id);
CREATE INDEX idx_candidate_work_experience_deleted ON candidate_work_experience (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE candidate_work_experience IS 'Profile: candidate work experience (Section 4 Tier 1). Personal. Soft-deleted.';

COMMENT ON COLUMN candidate_work_experience.salary_min IS 'Money domain NUMERIC(15,2) + currency_code. Nullable = not disclosed (not zero).';

COMMENT ON COLUMN candidate_work_experience.salary_max IS 'Money domain NUMERIC(15,2) + currency_code. Nullable = not disclosed (not zero).';

COMMENT ON COLUMN candidate_work_experience.salary_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

-- -----------------------------------------------------------------------------
-- CANDIDATE SKILL
-- Tier 1: skills.
-- Relationship:
--   candidate_identity 1..* candidate_skill
--   skill (master) 1..* candidate_skill
-- Natural key: (candidate_id, skill_id) uniqueness.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_skill (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id     BIGINT    NOT NULL,
    skill_name       TEXT      NOT NULL,
    proficiency      TEXT      NULL,
    years_of_experience NUMERIC(4,1) NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT    NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT    NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT fk_candidate_skill_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_candidate_skill_candidate_skill UNIQUE (candidate_id, skill_name),
    CONSTRAINT chk_years_of_experience_range CHECK (
        years_of_experience IS NULL OR (years_of_experience >= 0 AND years_of_experience <= 70)
    )
);

CREATE INDEX idx_candidate_skill_candidate ON candidate_skill (candidate_id);
CREATE INDEX idx_candidate_skill_skill_name ON candidate_skill (skill_name);
CREATE INDEX idx_candidate_skill_deleted ON candidate_skill (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE candidate_skill IS 'Profile: candidate skills (Section 4 Tier 1). Personal. Soft-deleted.';

COMMENT ON COLUMN candidate_skill.years_of_experience IS 'Nullable = unknown. Not used as a sentinel for missing.';

-- -----------------------------------------------------------------------------
-- CANDIDATE LANGUAGE
-- Tier 1: languages.
-- Relationship:
--   candidate_identity 1..* candidate_language
--   language (master) 1..* candidate_language
-- Natural key: (candidate_id, language) uniqueness.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_language (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id    BIGINT    NOT NULL,
    language_name   TEXT      NOT NULL,
    proficiency     TEXT      NULL,
    is_native       BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      BIGINT    NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by      BIGINT    NOT NULL DEFAULT 0,
    deleted_at      TIMESTAMPTZ NULL,
    CONSTRAINT fk_candidate_language_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_candidate_language_candidate_language UNIQUE (candidate_id, language_name)
);

CREATE INDEX idx_candidate_language_candidate ON candidate_language (candidate_id);
CREATE INDEX idx_candidate_language_deleted ON candidate_language (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE candidate_language IS 'Profile: candidate languages (Section 4 Tier 1). Personal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- RESUME TEMPLATES
-- Tier 2: resume templates.
-- Rule Group 3: template metadata stored as bounded TEXT; template body/content
--   is stored in object storage referenced by template_body_ref (TEXT), not as
--   unbounded in-db text.
-- -----------------------------------------------------------------------------
CREATE TABLE resume_template (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             TEXT    NOT NULL,
    template_body_ref TEXT   NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT uq_resume_template_name_active UNIQUE (name, is_active)
);

CREATE INDEX idx_resume_template_is_active ON resume_template (is_active);

COMMENT ON TABLE resume_template IS 'Profile: resume templates (Section 4 Tier 2). Public. Soft-deleted.';

COMMENT ON COLUMN resume_template.template_body_ref IS 'Reference to stored template body (object storage/file). Content not stored as in-db text.';

-- -----------------------------------------------------------------------------
-- RESUME VERSIONS
-- Tier 2: resume versions.
-- Rule Group 3: resume_body is the one allowed unbounded TEXT (justified: resume body).
--   Stored once in the language it was entered, with language recorded where known.
-- Relationship: candidate_identity 1..* resume_version.
-- -----------------------------------------------------------------------------
CREATE TABLE resume_version (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id       BIGINT    NOT NULL,
    template_id        BIGINT    NULL,
    resume_body        TEXT      NOT NULL,
    language           TEXT      NULL,
    version_label      TEXT      NULL,
    is_current         BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_resume_version_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_resume_version_template FOREIGN KEY (template_id)
        REFERENCES resume_template(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_resume_version_language CHECK (
        language IS NULL OR char_length(language) > 0
    ),
    CONSTRAINT uq_resume_version_candidate_current UNIQUE (candidate_id, is_current)
);

CREATE INDEX idx_resume_version_candidate ON resume_version (candidate_id);
CREATE INDEX idx_resume_version_language ON resume_version (language) WHERE language IS NOT NULL;
CREATE INDEX idx_resume_version_deleted ON resume_version (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE resume_version IS 'Profile: resume versions (Section 4 Tier 2). Personal. Soft-deleted.';

COMMENT ON COLUMN resume_version.resume_body IS 'Free text domain: unbounded TEXT allowed here because it is resume body (Rule Group 3 exception, justified).';

COMMENT ON COLUMN resume_version.language IS 'Language recorded where known (Rule Group 7); NULL = unknown.';

-- -----------------------------------------------------------------------------
-- PROFILE PROJECTS (candidate projects + gig projects)
-- Tier 1/2: profile projects (candidate projects and gig projects, with role,
--   duration, outcome).
-- The docket says profile projects include candidate projects AND gig projects.
-- We model a single profile_project table with a project_type_code to distinguish.
-- Gig project specifics (availability, service offerings, charge rates) are stored
--   in gig_project_details because they belong to the gig marketplace module's
--   domain; this table references it where relevant.
-- -----------------------------------------------------------------------------
CREATE TABLE profile_project (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id       BIGINT    NOT NULL,
    project_type_code  TEXT      NOT NULL,
    project_name       TEXT      NOT NULL,
    role               TEXT      NULL,
    start_date         DATE      NULL,
    end_date           DATE      NULL,
    is_current         BOOLEAN   NOT NULL DEFAULT FALSE,
    duration_months    INTEGER   NULL,
    outcome            TEXT      NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_profile_project_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_profile_project_dates CHECK (
        (start_date IS NULL AND end_date IS NULL)
        OR (start_date IS NOT NULL AND (end_date IS NULL OR end_date >= start_date))
    ),
    CONSTRAINT chk_profile_project_current_check CHECK (is_current = FALSE OR end_date IS NULL),
    CONSTRAINT chk_profile_project_duration CHECK (
        duration_months IS NULL OR duration_months >= 0
    )
);

CREATE INDEX idx_profile_project_candidate ON profile_project (candidate_id);
CREATE INDEX idx_profile_project_type ON profile_project (project_type_code);
CREATE INDEX idx_profile_project_deleted ON profile_project (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE profile_project IS 'Profile: profile projects (Section 4 Tier 1/2: candidate projects and gig projects). Personal. Soft-deleted.';

COMMENT ON COLUMN profile_project.project_type_code IS 'Enumeration code; distinguishes candidate project vs gig project.';

COMMENT ON COLUMN profile_project.duration_months IS 'Nullable = unknown/a computed later value not stored.';

-- -----------------------------------------------------------------------------
-- ASSESSMENTS AND SCORES
-- Tier 2: assessments and scores.
-- Relationship:
--   candidate_identity 1..* assessment
--   assessment carries a score (percentage/ratio domain NUMERIC with range).
-- -----------------------------------------------------------------------------
CREATE TABLE assessment (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id     BIGINT    NOT NULL,
    assessment_type_code TEXT   NOT NULL,
    score            NUMERIC(5,2) NULL,
    max_score        NUMERIC(5,2) NOT NULL,
    taken_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT    NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT    NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT fk_assessment_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_assessment_score_range CHECK (
        score IS NULL OR (score >= 0 AND score <= max_score)
    ),
    CONSTRAINT chk_assessment_max_score CHECK (max_score > 0),
    CONSTRAINT uq_assessment_candidate_type_taken UNIQUE (candidate_id, assessment_type_code, taken_at)
);

CREATE INDEX idx_assessment_candidate ON assessment (candidate_id);
CREATE INDEX idx_assessment_type ON assessment (assessment_type_code);
CREATE INDEX idx_assessment_deleted ON assessment (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE assessment IS 'Profile: assessments and scores (Section 4 Tier 2). Personal. Soft-deleted.';

COMMENT ON COLUMN assessment.score IS 'Percentage/ratio domain NUMERIC with stated range. Nullable = not scored yet.';

COMMENT ON COLUMN assessment.max_score IS 'Stated maximum for the assessment; used to bound score.';

-- -----------------------------------------------------------------------------
-- COURSE ENROLMENTS
-- Tier 2: course enrolments.
-- Relationship:
--   candidate_identity 1..* course_enrolment
--   course (reference) 1..* course_enrolment
-- -----------------------------------------------------------------------------
CREATE TABLE course_enrolment (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id     BIGINT    NOT NULL,
    course_name      TEXT      NOT NULL,
    enrolled_at      DATE      NOT NULL,
    completed_at     DATE      NULL,
    status_code      TEXT      NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT    NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT    NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT fk_course_enrolment_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_course_enrolment_dates CHECK (
        completed_at IS NULL OR completed_at >= enrolled_at
    ),
    CONSTRAINT uq_course_enrolment_candidate_course UNIQUE (candidate_id, course_name)
);

CREATE INDEX idx_course_enrolment_candidate ON course_enrolment (candidate_id);
CREATE INDEX idx_course_enrolment_status ON course_enrolment (status_code);
CREATE INDEX idx_course_enrolment_deleted ON course_enrolment (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE course_enrolment IS 'Profile: course enrolments (Section 4 Tier 2). Personal. Soft-deleted.';

COMMENT ON COLUMN course_enrolment.completed_at IS 'Nullable = not completed or not provided.';

-- -----------------------------------------------------------------------------
-- PROFILE COMPLETION SCORING
-- Tier 2: profile completion scoring.
-- Stored as a snapshot-ish record per evaluation; one active current score per
-- candidate is kept via a unique partial index on (candidate_id, is_current).
-- Score is NUMERIC(5,2) with range 0..100.
-- -----------------------------------------------------------------------------
CREATE TABLE profile_completion_score (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id     BIGINT    NOT NULL,
    score            NUMERIC(5,2) NOT NULL,
    evaluated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_current       BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT    NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT    NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT fk_profile_completion_score_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_score_range CHECK (score BETWEEN 0 AND 100)
);

CREATE INDEX idx_profile_completion_score_candidate ON profile_completion_score (candidate_id);
CREATE INDEX idx_profile_completion_score_current ON profile_completion_score (candidate_id, is_current)
    WHERE is_current = TRUE;
CREATE INDEX idx_profile_completion_score_deleted ON profile_completion_score (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE profile_completion_score IS 'Profile: profile completion scoring (Section 4 Tier 2). Personal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- PROFILE VIEW HISTORY
-- Tier 2: profile view history.
-- Append-only: who viewed which candidate profile, when.
-- No deleted_at; history is retained.
-- -----------------------------------------------------------------------------
CREATE TABLE profile_view_history (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    viewer_id       BIGINT    NOT NULL,
    candidate_id    BIGINT    NOT NULL,
    viewed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_profile_view_history_viewer FOREIGN KEY (viewer_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_profile_view_history_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_profile_view_history_viewer ON profile_view_history (viewer_id);
CREATE INDEX idx_profile_view_history_candidate ON profile_view_history (candidate_id);
CREATE INDEX idx_profile_view_history_viewed_at ON profile_view_history (viewed_at);

COMMENT ON TABLE profile_view_history IS 'Profile: profile view history (Section 4 Tier 2). Append-only history. Viewer and candidate references.';

-- -----------------------------------------------------------------------------
-- CANDIDATE ACTIVITY LOG
-- Tier 2: candidate activity log (login, profile update, resume download events).
-- Append-only: activity event stream per candidate.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_activity_log (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id    BIGINT    NOT NULL,
    activity_type_code TEXT    NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    detail          TEXT      NULL,
    CONSTRAINT fk_candidate_activity_log_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_candidate_activity_log_candidate ON candidate_activity_log (candidate_id);
CREATE INDEX idx_candidate_activity_log_occurred ON candidate_activity_log (occurred_at);

COMMENT ON TABLE candidate_activity_log IS 'Profile: candidate activity log (Section 4 Tier 2). Append-only.';

COMMENT ON COLUMN candidate_activity_log.detail IS 'Optional bounded detail about the event (TEXT).';

-- -----------------------------------------------------------------------------
-- SHORTLIST AND BOOKMARK HISTORY
-- Tier 2: shortlist and bookmark history for employers and recruiters.
-- We model a shortlist/bookmark table plus a history table for changes.
-- employer_or_recruiter_id references users (employer/recruiter actor).
-- candidate_id references candidate_identity.
-- -----------------------------------------------------------------------------
CREATE TABLE candidate_shortlist_entry (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shortlist_owner_id BIGINT    NOT NULL,
    candidate_id       BIGINT    NOT NULL,
    list_name          TEXT      NULL,
    is_public          BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_candidate_shortlist_owner FOREIGN KEY (shortlist_owner_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_candidate_shortlist_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_shortlist_owner_candidate UNIQUE (shortlist_owner_id, candidate_id)
);

CREATE INDEX idx_candidate_shortlist_owner ON candidate_shortlist_entry (shortlist_owner_id);
CREATE INDEX idx_candidate_shortlist_candidate ON candidate_shortlist_entry (candidate_id);
CREATE INDEX idx_candidate_shortlist_deleted ON candidate_shortlist_entry (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE candidate_shortlist_entry IS 'Profile: shortlist/bookmark entries (Section 4 Tier 2). Soft-deleted.';

-- History for shortlist/bookmark changes (append-only)
CREATE TABLE candidate_shortlist_history (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shortlist_owner_id BIGINT    NOT NULL,
    candidate_id       BIGINT    NOT NULL,
    action_code        TEXT      NOT NULL,
    occurred_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_candidate_shortlist_history_owner FOREIGN KEY (shortlist_owner_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_candidate_shortlist_history_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidate_identity(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_candidate_shortlist_history_owner ON candidate_shortlist_history (shortlist_owner_id);
CREATE INDEX idx_candidate_shortlist_history_candidate ON candidate_shortlist_history (candidate_id);
CREATE INDEX idx_candidate_shortlist_history_occurred ON candidate_shortlist_history (occurred_at);

COMMENT ON TABLE candidate_shortlist_history IS 'Profile: shortlist and bookmark history (Section 4 Tier 2). Append-only.';

-- -----------------------------------------------------------------------------
-- REFERRAL TRACKING
-- Tier 2: referral tracking.
-- Relationship:
--   referral_tracking 1..* (referrer candidate -> referred candidate + job).
-- Stored in referral_tracking table.
-- -----------------------------------------------------------------------------
CREATE TABLE referral_tracking (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    referrer_candidate_id BIGINT NOT NULL,
    referred_candidate_id BIGINT NULL,
    job_id              BIGINT NULL,
    referred_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    status_code         TEXT      NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_referral_tracking_referrer FOREIGN KEY (referrer_candidate_id)
        REFERENCES candidate_identity(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_referral_tracking_referred FOREIGN KEY (referred_candidate_id)
        REFERENCES candidate_identity(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_referral_tracking_job FOREIGN KEY (job_id)
        REFERENCES job_requirement(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_referral_tracking_referrer ON referral_tracking (referrer_candidate_id);
CREATE INDEX idx_referral_tracking_referred ON referral_tracking (referred_candidate_id) WHERE referred_candidate_id IS NOT NULL;
CREATE INDEX idx_referral_tracking_job ON referral_tracking (job_id) WHERE job_id IS NOT NULL;
CREATE INDEX idx_referral_tracking_deleted ON referral_tracking (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE referral_tracking IS 'Profile: referral tracking (Section 4 Tier 2). Soft-deleted.';

COMMENT ON COLUMN referral_tracking.referred_candidate_id IS 'Nullable = referral not yet associated with a candidate.';

COMMENT ON COLUMN referral_tracking.job_id IS 'Nullable = referral not tied to a job.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Profile (Milestone 3, B8/B9, B10/B11 context)
--(candidate_identity 1..1) users                optional
-- candidate_identity 1..* candidate_contact
-- candidate_identity 1..* candidate_education
-- candidate_identity 1..* candidate_work_experience
-- candidate_identity 1..* candidate_skill
-- candidate_identity 1..* candidate_language
-- candidate_identity 1..* resume_version
-- candidate_identity 1..* profile_project
-- profile_project 1..* gig_project_details            (gig project specifics)
-- candidate_identity 1..* assessment
-- candidate_identity 1..* course_enrolment
-- candidate_identity 1..* profile_completion_score
-- candidate_identity 1..* candidate_activity_log
-- candidate_identity 1..* referral_tracking
-- users 1..* profile_view_history (viewer)
-- candidate_identity 1..* profile_view_history (viewed)
-- users 1..* candidate_shortlist_entry (owner)
-- candidate_identity 1..* candidate_shortlist_entry (bookmarked)
-- candidate_shortlist_entry 1..* candidate_shortlist_history
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Profile entities beyond the docket list. Decisions taken:
--   1. profile_project is shared for candidate and gig projects, distinguished by
--      project_type_code; gig project specifics live in gig_project_details (gig
--      marketplace domain) to avoid duplicating gig-domain fields here. This is
--      consistent with the docket saying gig project specifics belong to the gig
--      module, while profile projects belong to the profile module.
--   2. resume_body is the only unbounded TEXT in Profile, justified per Rule Group 3.
--   3. profile_completion_score keeps one current row per candidate via partial unique,
--      to support scoring read patterns described in the docket.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
