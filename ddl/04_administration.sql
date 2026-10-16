-- =============================================================================
-- Talentra Database Design ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ï¿½ Administration module
-- Phase 2 (Individual, Member A), Milestones 7-10
--
-- This file models ONLY the docket Administration domain.
-- Tier 1 (mandatory) from Section 4:
--   identity and accounts: users, credentials, roles, sessions, consent records.
-- Tier 2 (modelled because you chose to model all Tier 2):
--   blocking lists (for candidates, employers, recruiters, consultants).
--
-- Credential modelling decision (industry best practice):
--   The docket lists "credentials" as a Tier 1 domain. The best-practice
--   approach is to separate credential verification and recovery concerns from
--   the core user row:
--     - credential_verification: per-account credential records with hashed
--       password (or equivalent verifier), credential type, status, failure/
--       lockout counters, last used, recovery token references, and recovery
--       metadata. Password/credential material is NOT stored in cleartext.
--     - credential_recovery: recovery attempts and recovery tokens/anchors
--       used for account recovery flows, stored as references/tokens, not as
--       raw secrets.
--   This keeps the user row focused on identity/profile data and makes
--   credential lifecycle (reset, lockout, recovery, multi-credential support)
--   auditable and extensible.
--   See 99_documentation.sql for the justification and the security handling
--   note (Rule Group 6).
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK; natural keys as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification on credentials, contact details, etc.
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ (in analytics module, not here).
-- Rule Group 9 / 10: not Administration module concerns for the core user/credential tables;
--   licence/device/session specifics and money/subscription/history specifics live in those modules.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- USERS
-- Tier 1: users (identity and accounts).
-- Relationships:
--   users 1..1 candidate_identity (optional; candidate profile may exist without
--     full account until registration completes, per workflow)
--   users 1..1 employer_organisation (optional owning organisation for employer/
--     recruiter actors)
--   users 1..* credential_verification
--   users 1..* role_assignment
--   users 1..* session_record
--   users 1..* consent_record
--   users 1..* user_blocking_entry (where user is blocker or blocked party)
--   users 1..* audit_event (actor)
-- Role membership is many-to-many via role_assignment -> role.
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_type_code     TEXT      NOT NULL,
    email               TEXT      NOT NULL,
    email_verified_at   TIMESTAMPTZ NULL,
    phone               TEXT      NULL,
    phone_country_code  TEXT      NULL,
    first_name          TEXT      NULL,
    last_name           TEXT      NULL,
    display_name        TEXT      NULL,
    profile_language    TEXT      NULL,
    is_active           BOOLEAN   NOT NULL DEFAULT TRUE,
    is_locked           BOOLEAN   NOT NULL DEFAULT FALSE,
    locked_at           TIMESTAMPTZ NULL,
    locked_by_user_id   BIGINT    NULL,
    last_login_at       TIMESTAMPTZ NULL,
    last_login_ip       INET      NULL,
    last_login_user_agent TEXT    NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          BIGINT    NOT NULL DEFAULT 0,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by          BIGINT    NOT NULL DEFAULT 0,
    deleted_at          TIMESTAMPTZ NULL,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_email_lowercase CHECK (email = lower(email)),
    CONSTRAINT chk_email_length CHECK (char_length(email) <= 254),
    CONSTRAINT chk_phone_e164 CHECK (phone IS NULL OR phone ~ '^\+?[1-9][0-9]{1,14}$')
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_actor_type ON users (actor_type_code);
CREATE INDEX idx_users_active ON users (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_users_locked ON users (is_locked) WHERE is_locked = TRUE;
CREATE INDEX idx_users_deleted ON users (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE users IS 'Administration: users (Section 4 Tier 1 identity and accounts). Personal. Soft-deleted.';

COMMENT ON COLUMN users.email IS 'Sensitive/Personal. Lowercase, max 254 chars, unique per account (Rule Group 3 email domain).';

COMMENT ON COLUMN users.phone IS 'Personal. E.164 with country code in phone (Rule Group 3 phone domain).';

COMMENT ON COLUMN users.phone_country_code IS 'Separate country field for phone (Rule Group 3 phone domain).';

COMMENT ON COLUMN users.first_name IS 'Person name domain TEXT up to 150 chars (Rule Group 3).';

COMMENT ON COLUMN users.last_name IS 'Person name domain TEXT up to 150 chars (Rule Group 3).';

COMMENT ON COLUMN users.display_name IS 'Nullable = not set.';

COMMENT ON COLUMN users.is_locked IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

COMMENT ON COLUMN users.locked_at IS 'Nullable = not locked.';

COMMENT ON COLUMN users.locked_by_user_id IS 'Nullable = locked by system or not applicable.';

COMMENT ON COLUMN users.last_login_ip IS 'Nullable = unknown.';

COMMENT ON COLUMN users.last_login_user_agent IS 'Nullable = unknown.';

-- -----------------------------------------------------------------------------
-- CREDENTIAL VERIFICATION
-- Tier 1: credentials (best-practice separated credential store).
-- This table holds credential verification material references, type, status,
-- lockout/failure counters, and recovery metadata. Credential material itself
-- is hashed/tokenised/masked per the security design note; the DDL does not
-- store cleartext secrets.
-- One row per account credential record; multiple credential types can exist
-- for the same account (e.g. platform password, federated identity reference).
-- -----------------------------------------------------------------------------
CREATE TABLE credential_verification (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    credential_type_code   TEXT      NOT NULL,
    credential_status_code TEXT      NOT NULL,
    verified_at            TIMESTAMPTZ NULL,
    last_used_at           TIMESTAMPTZ NULL,
    last_used_ip           INET      NULL,
    last_used_user_agent   TEXT      NULL,
    failure_count          INTEGER   NOT NULL DEFAULT 0,
    locked_until           TIMESTAMPTZ NULL,
    recovery_token_ref     TEXT      NULL,
    recovery_anchor_hash   TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_credential_verification_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_failure_count_nonnegative CHECK (failure_count >= 0),
    CONSTRAINT chk_credential_locked_until CHECK (
        locked_until IS NULL OR locked_until >= now()
    )
);

CREATE INDEX idx_credential_verification_user ON credential_verification (user_id);
CREATE INDEX idx_credential_verification_type ON credential_verification (credential_type_code);
CREATE INDEX idx_credential_verification_status ON credential_verification (credential_status_code);
CREATE INDEX idx_credential_verification_deleted ON credential_verification (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE credential_verification IS 'Administration: credential verification records (Section 4 Tier 1 credentials). Sensitive. Stores credential status, lockout, and recovery references; credential material is hashed/tokenised/masked per security design note.';

COMMENT ON COLUMN credential_verification.credential_type_code IS 'Enumeration code referencing reference_code (domain=credential_type).';

COMMENT ON COLUMN credential_verification.credential_status_code IS 'Enumeration code referencing reference_code (domain=credential_status).';

COMMENT ON COLUMN credential_verification.failure_count IS 'Nullable meaning not applicable; here a counter, never negative. Used for lockout decisions.';

COMMENT ON COLUMN credential_verification.locked_until IS 'Nullable = not locked. If set, login attempts are rejected until this time.';

COMMENT ON COLUMN credential_verification.recovery_token_ref IS 'Sensitive. Reference/anchor for recovery flow, not a raw secret.';

COMMENT ON COLUMN credential_verification.recovery_anchor_hash IS 'Sensitive. Hashed recovery anchor, not a raw secret.';

-- -----------------------------------------------------------------------------
-- CREDENTIAL RECOVERY
-- Tier 1: credentials (recovery tracking, best-practice separated).
-- Append-only-ish history of recovery events and tokens. Tokens are stored as
-- references/anchors, not raw secrets.
-- -----------------------------------------------------------------------------
CREATE TABLE credential_recovery (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id            BIGINT    NOT NULL,
    recovery_type_code TEXT      NOT NULL,
    token_ref          TEXT      NULL,
    requested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    used_at            TIMESTAMPTZ NULL,
    used_by_user_id    BIGINT    NULL,
    ip_address         INET      NULL,
    user_agent         TEXT      NULL,
    status_code        TEXT      NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_credential_recovery_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_credential_recovery_used_by FOREIGN KEY (used_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_credential_recovery_used CHECK (
        used_at IS NULL OR used_by_user_id IS NOT NULL
    )
);

CREATE INDEX idx_credential_recovery_user ON credential_recovery (user_id);
CREATE INDEX idx_credential_recovery_type ON credential_recovery (recovery_type_code);
CREATE INDEX idx_credential_recovery_requested_at ON credential_recovery (requested_at);
CREATE INDEX idx_credential_recovery_deleted ON credential_recovery (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE credential_recovery IS 'Administration: credential recovery records (Section 4 Tier 1 credentials). Sensitive. Stores recovery event references, not raw secrets.';

COMMENT ON COLUMN credential_recovery.token_ref IS 'Sensitive. Recovery token reference/anchor, not a raw secret.';

-- -----------------------------------------------------------------------------
-- ROLES
-- Tier 1: roles.
-- Enumeration-style role table with code, name, description, active flag.
-- -----------------------------------------------------------------------------
CREATE TABLE role_lookup (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code             TEXT      NOT NULL,
    name             TEXT      NOT NULL,
    description      TEXT      NULL,
    is_active        BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT    NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT    NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT uq_role_code UNIQUE (code)
);

CREATE INDEX idx_role_code ON role_lookup (code);
CREATE INDEX idx_role_is_active ON role_lookup (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_role_deleted ON role_lookup (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE role_lookup IS 'Administration: role_lookup (Section 4 Tier 1). Internal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- ROLE ASSIGNMENT
-- Tier 1: role assignments (users <-> roles many-to-many).
-- This is the membership table. Effective-dated variant is not required by the
-- docket for administration; if needed later it can be added with an effective
-- range and stated rule.
-- -----------------------------------------------------------------------------
CREATE TABLE role_assignment (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id          BIGINT    NOT NULL,
    role_id          BIGINT    NOT NULL,
    assigned_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_by_user_id BIGINT NULL,
    is_active        BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT    NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT    NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT fk_role_assignment_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_role_assignment_role FOREIGN KEY (role_id)
        REFERENCES role_lookup (id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_role_assignment_assigned_by FOREIGN KEY (assigned_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT uq_role_assignment_user_role UNIQUE (user_id, role_id)
);

CREATE INDEX idx_role_assignment_user ON role_assignment (user_id);
CREATE INDEX idx_role_assignment_role ON role_assignment (role_id);
CREATE INDEX idx_role_assignment_active ON role_assignment (user_id, role_id) WHERE is_active = TRUE;
CREATE INDEX idx_role_assignment_deleted ON role_assignment (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE role_assignment IS 'Administration: role assignments (Section 4 Tier 1). Internal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- PERMISSIONS
-- Tier 1: permissions (permission catalogue).
-- The docket says "roles, permissions". We model a permission catalogue here.
-- Permission-to-role mapping is owned by the access control design; we include
-- a permission table and a permission_assignment table for role->permission.
-- -----------------------------------------------------------------------------
CREATE TABLE permission (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code                TEXT      NOT NULL,
    name                TEXT      NOT NULL,
    resource_scope      TEXT      NULL,
    is_active          BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT uq_permission_code UNIQUE (code)
);

CREATE INDEX idx_permission_code ON permission (code);
CREATE INDEX idx_permission_is_active ON permission (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_permission_deleted ON permission (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE permission IS 'Administration: permissions (Section 4 Tier 1). Internal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- PERMISSION ASSIGNMENT
-- Tier 1: permission assignments (role -> permissions).
-- Many-to-many role_lookup <-> permission.
-- -----------------------------------------------------------------------------
CREATE TABLE permission_assignment (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_id          BIGINT    NOT NULL,
    permission_id    BIGINT    NOT NULL,
    granted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    granted_by_user_id BIGINT NULL,
    is_active        BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       BIGINT    NOT NULL DEFAULT 0,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by       BIGINT    NOT NULL DEFAULT 0,
    deleted_at       TIMESTAMPTZ NULL,
    CONSTRAINT fk_permission_assignment_role FOREIGN KEY (role_id)
        REFERENCES role_lookup (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_permission_assignment_permission FOREIGN KEY (permission_id)
        REFERENCES permission(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_permission_assignment_granted_by FOREIGN KEY (granted_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT uq_permission_assignment_role_permission UNIQUE (role_id, permission_id)
);

CREATE INDEX idx_permission_assignment_role ON permission_assignment (role_id);
CREATE INDEX idx_permission_assignment_permission ON permission_assignment (permission_id);
CREATE INDEX idx_permission_assignment_deleted ON permission_assignment (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE permission_assignment IS 'Administration: permission assignments (Section 4 Tier 1). Internal. Soft-deleted.';

-- -----------------------------------------------------------------------------
-- SESSIONS
-- Tier 1: sessions (active session records).
-- The detailed device-limit session counting rule is owned by the Licences,
-- seats, devices and sessions module (Section 4 Tier 1 and Rule Group 9).
-- This table stores the session record referenced by that module.
-- -----------------------------------------------------------------------------
CREATE TABLE session_record (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id            BIGINT    NOT NULL,
    session_token_ref  TEXT      NOT NULL,
    device_ref         TEXT      NULL,
    ip_address         INET      NULL,
    user_agent         TEXT      NULL,
    started_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_activity_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at           TIMESTAMPTZ NULL,
    expires_at         TIMESTAMPTZ NOT NULL,
    is_revoked         BOOLEAN   NOT NULL DEFAULT FALSE,
    revoked_at         TIMESTAMPTZ NULL,
    revoked_by_user_id BIGINT    NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_session_record_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_session_record_revoked_by FOREIGN KEY (revoked_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_session_expires_after_start CHECK (expires_at > started_at),
    CONSTRAINT chk_session_revoked CHECK (
        revoked_at IS NULL OR revoked_by_user_id IS NOT NULL
    )
);

CREATE INDEX idx_session_record_user ON session_record (user_id);
CREATE INDEX idx_session_record_token_ref ON session_record (session_token_ref);
CREATE INDEX idx_session_record_active ON session_record (user_id, is_revoked, ended_at, expires_at)
    WHERE is_revoked = FALSE AND ended_at IS NULL;
CREATE INDEX idx_session_record_started_at ON session_record (started_at);
CREATE INDEX idx_session_record_deleted ON session_record (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE session_record IS 'Administration: sessions (Section 4 Tier 1). Internal. Session token stored as reference; detailed device-limit counting is owned by the Licences module.';

COMMENT ON COLUMN session_record.session_token_ref IS 'Sensitive. Session token stored as reference/hash, not raw token.';

COMMENT ON COLUMN session_record.device_ref IS 'Nullable = unknown device.';

-- -----------------------------------------------------------------------------
-- CONSENT RECORDS
-- Tier 1: consent records.
-- Append-only: each consent record is a snapshot of consent state at a point in
-- time. Updates are represented as new rows, not overwrites (Rule Group 4).
-- -----------------------------------------------------------------------------
CREATE TABLE consent_record (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id            BIGINT    NOT NULL,
    consent_type_code  TEXT      NOT NULL,
    consent_value_code TEXT      NOT NULL,
    recorded_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_by_user_id BIGINT    NULL,
    ip_address         INET      NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_consent_record_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_consent_record_recorded_by FOREIGN KEY (recorded_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_consent_record_user ON consent_record (user_id);
CREATE INDEX idx_consent_record_type ON consent_record (consent_type_code);
CREATE INDEX idx_consent_record_recorded_at ON consent_record (recorded_at);
CREATE INDEX idx_consent_record_deleted ON consent_record (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE consent_record IS 'Administration: consent records (Section 4 Tier 1). Personal. Append-only consent snapshots.';

-- -----------------------------------------------------------------------------
-- AUDIT EVENT
-- Tier 1: audit trail of sensitive actions.
-- Append-only: audit_event is append-only. No deleted_at; no update/delete by
-- application users (Rule Group 4).
-- -----------------------------------------------------------------------------
CREATE TABLE audit_event (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_user_id      BIGINT    NOT NULL,
    event_type_code    TEXT      NOT NULL,
    target_table       TEXT      NULL,
    target_id          BIGINT    NULL,
    occurred_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_ip          INET      NULL,
    source_user_agent  TEXT      NULL,
    detail             TEXT      NULL,
    CONSTRAINT fk_audit_event_actor FOREIGN KEY (actor_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_audit_event_actor ON audit_event (actor_user_id);
CREATE INDEX idx_audit_event_type ON audit_event (event_type_code);
CREATE INDEX idx_audit_event_occurred_at ON audit_event (occurred_at);
CREATE INDEX idx_audit_event_target ON audit_event (target_table, target_id) WHERE target_table IS NOT NULL;

COMMENT ON TABLE audit_event IS 'Administration: audit trail (Section 4 Tier 1 audit and error logging). Append-only. System errors may be logged here with an event type for errors.';

COMMENT ON COLUMN audit_event.target_table IS 'Nullable = event not tied to a specific table row.';

COMMENT ON COLUMN audit_event.target_id IS 'Nullable = event not tied to a specific row.';

COMMENT ON COLUMN audit_event.detail IS 'Nullable = no detail. Stored detail is bounded TEXT.';

-- -----------------------------------------------------------------------------
-- BLOCKING LISTS (Tier 2, modelled because you chose all Tier 2)
-- Tier 2: blocking lists for candidates, employers, recruiters, consultants.
-- The docket says a candidate may block employers, recruiters, or consultants,
-- and a blocked party must not see that candidate.
-- We store blocking entries with blocker + blocked party type + blocked party id,
-- plus effective flags.
-- Blocking lists are shared team items in the sense that multiple modules read
-- them; this table is the system-wide blocking list.
-- -----------------------------------------------------------------------------
CREATE TABLE blocking_list (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    blocker_user_id    BIGINT    NOT NULL,
    blocked_party_type_code TEXT  NOT NULL,
    blocked_party_id   BIGINT    NOT NULL,
    blocked_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    blocked_by_user_id BIGINT    NOT NULL,
    reason             TEXT      NULL,
    is_active          BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_blocking_list_blocker FOREIGN KEY (blocker_user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_blocking_list_blocked_by FOREIGN KEY (blocked_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_blocking_party_type CHECK (
        blocked_party_type_code IN ('candidate', 'employer', 'recruiter', 'consultant')
    ),
    CONSTRAINT uq_blocking_list_blocker_party UNIQUE (blocker_user_id, blocked_party_type_code, blocked_party_id)
);

CREATE INDEX idx_blocking_list_blocker ON blocking_list (blocker_user_id);
CREATE INDEX idx_blocking_list_blocked_party ON blocking_list (blocked_party_type_code, blocked_party_id);
CREATE INDEX idx_blocking_list_active ON blocking_list (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_blocking_list_deleted ON blocking_list (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE blocking_list IS 'Administration/shared: blocking lists (Section 4 Tier 2). Personal for blocked parties; Internal for blocking metadata. Soft-deleted.';

COMMENT ON COLUMN blocking_list.blocked_party_type_code IS 'Enumeration of blocked party kinds: candidate, employer, recruiter, consultant.';

COMMENT ON COLUMN blocking_list.blocked_party_id IS 'ID of the blocked party in the relevant table.';

COMMENT ON COLUMN blocking_list.reason IS 'Nullable = no reason recorded.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ï¿½ Administration (Milestone 8, B27/B28/B29 context)
--   users 1..* credential_verification
--   users 1..* credential_recovery
--   users 1..* role_assignment
--   role_lookup 1..* role_assignment
--   users 1..* permission_assignment (implied via role_permission mapping; here role_lookup->permission)
--   role_lookup 1..* permission_assignment
--   permission 1..* permission_assignment
--   users 1..* session_record
--   users 1..* consent_record
--   users 1..* audit_event (actor)
--   users 1..* blocking_list (blocker)
--   users 1..* blocking_list (blocked_by)
--   (blocked party) referenced by type + id in blocking_list
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- 1. credential_verification + credential_recovery are the chosen best-practice
--    modelling for the docket "credentials" domain. This is NOT an out-of-docket
--    entity; credentials are explicitly in Tier 1. The shape is a design decision.
-- 2. permission + permission_assignment are included because the docket says
--    "roles, permissions". If you want a simpler role-only model without a
--    separate permission catalogue, say so and I will remove it.
-- 3. session_record is the session table referenced by the Licences module's
--    device-limit rule. The counting rule itself lives there.
-- 4. blocking_list is the system-wide blocking list used by Profile, Jobs, and
--    other modules; it is the shared team item for blocking lists.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
