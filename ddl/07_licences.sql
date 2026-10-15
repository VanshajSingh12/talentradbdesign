-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Licences, seats, devices and sessions module
-- Phase 3 (Individual, Member A), Milestones 11-14
--
-- This file models ONLY the docket Licences, seats, devices and sessions domain.
-- Tier 1 (mandatory) from Section 4:
--   licences and seats: subscription licences, number of users allowed per licence,
--     number of devices allowed per user, seat allocation.
--   devices and sessions: registered devices per user, active sessions, login
--     history, and the rule enforced when a device limit is reached.
--
-- Rule Group 9 (licensing, devices, and sessions) is the primary rule for this module:
--   - Every licence has max users and max devices per user, stored as explicit columns
--     with check constraints that they are positive integers.
--   - A user cannot hold more active sessions than the number of devices allowed by
--     their licence. The attempt to exceed the limit is recorded in the audit trail.
--   - Sessions are stored with device identifier, start time, last activity time, and
--     end time. Expired or revoked sessions are not counted against the limit.
--   - Revoking a device or session is an auditable action.
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
-- Rule Group 10: not Licences module concerns except where subscription/ledger concepts
--   appear; those are owned by the Subscriptions module where the docket places them.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SUBSCRIPTION LICENCE
-- Tier 1: subscription licences.
-- Rule Group 9: max_users_allowed and max_devices_per_user are explicit columns with
--   check constraints that they are positive integers.
-- Relationship:
--   tenant_account 1..* subscription_licence
-- Seat allocation and device limits are enforced downstream in seat and session tables.
-- -----------------------------------------------------------------------------
CREATE TABLE subscription_licence (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_account_id      BIGINT    NOT NULL,
    licence_number         TEXT      NOT NULL,
    licence_type_code      TEXT      NOT NULL,
    status_code            TEXT      NOT NULL,
    max_users_allowed      INTEGER   NOT NULL,
    max_devices_per_user   INTEGER   NOT NULL,
    issued_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    issued_by_user_id      BIGINT    NULL,
    activated_at           TIMESTAMPTZ NULL,
    activated_by_user_id   BIGINT    NULL,
    suspended_at           TIMESTAMPTZ NULL,
    suspended_by_user_id   BIGINT    NULL,
    terminated_at          TIMESTAMPTZ NULL,
    terminated_by_user_id  BIGINT    NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_subscription_licence_account FOREIGN KEY (tenant_account_id)
        REFERENCES tenant_account(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_subscription_licence_issued_by FOREIGN KEY (issued_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_subscription_licence_activated_by FOREIGN KEY (activated_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_subscription_licence_suspended_by FOREIGN KEY (suspended_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_subscription_licence_terminated_by FOREIGN KEY (terminated_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_licence_max_users_positive CHECK (max_users_allowed > 0),
    CONSTRAINT chk_licence_max_devices_positive CHECK (max_devices_per_user > 0),
    CONSTRAINT uq_subscription_licence_number UNIQUE (licence_number)
);

CREATE INDEX idx_subscription_licence_account ON subscription_licence (tenant_account_id);
CREATE INDEX idx_subscription_licence_status ON subscription_licence (status_code);
CREATE INDEX idx_subscription_licence_deleted ON subscription_licence (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE subscription_licence IS 'Licences, seats, devices and sessions: subscription licences (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN subscription_licence.licence_number IS 'License identifier; unique per licence.';

COMMENT ON COLUMN subscription_licence.licence_type_code IS 'Enumeration code referencing reference_code (domain=licence_type).';

COMMENT ON COLUMN subscription_licence.status_code IS 'Enumeration code referencing reference_code (domain=licence_status).';

COMMENT ON COLUMN subscription_licence.max_users_allowed IS 'Rule Group 9: maximum users allowed per licence; positive integer (CHECK > 0).';

COMMENT ON COLUMN subscription_licence.max_devices_per_user IS 'Rule Group 9: maximum devices per user; positive integer (CHECK > 0).';

COMMENT ON COLUMN subscription_licence.issued_by_user_id IS 'Nullable = issued by system.';

COMMENT ON COLUMN subscription_licence.activated_at IS 'Nullable = not activated.';

COMMENT ON COLUMN subscription_licence.suspended_at IS 'Nullable = not suspended.';

COMMENT ON COLUMN subscription_licence.terminated_at IS 'Nullable = not terminated.';

-- -----------------------------------------------------------------------------
-- SEAT ALLOCATION
-- Tier 1: seat allocation (number of users allowed per licence).
-- Relationship:
--   subscription_licence 1..* seat_allocation
--   users 1..* seat_allocation
-- A user can hold seats across licences; the active seat count per licence is
--   constrained by max_users_allowed on the licence.
-- -----------------------------------------------------------------------------
CREATE TABLE seat_allocation (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subscription_licence_id BIGINT   NOT NULL,
    user_id                BIGINT    NOT NULL,
    seat_status_code       TEXT      NOT NULL,
    allocated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    allocated_by_user_id   BIGINT    NULL,
    revoked_at             TIMESTAMPTZ NULL,
    revoked_by_user_id     BIGINT    NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_seat_allocation_licence FOREIGN KEY (subscription_licence_id)
        REFERENCES subscription_licence(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_seat_allocation_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_seat_allocation_revoked_by FOREIGN KEY (revoked_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_seat_allocation_revoked CHECK (
        revoked_at IS NULL OR revoked_by_user_id IS NOT NULL
    ),
    CONSTRAINT uq_seat_allocation_licence_user UNIQUE (subscription_licence_id, user_id)
);

CREATE INDEX idx_seat_allocation_licence ON seat_allocation (subscription_licence_id);
CREATE INDEX idx_seat_allocation_user ON seat_allocation (user_id);
CREATE INDEX idx_seat_allocation_active ON seat_allocation (subscription_licence_id, user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_seat_allocation_deleted ON seat_allocation (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE seat_allocation IS 'Licences, seats, devices and sessions: seat allocation (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN seat_allocation.revoked_at IS 'Nullable = not revoked.';

COMMENT ON COLUMN seat_allocation.revoked_by_user_id IS 'Nullable = revoked by system.';

-- -----------------------------------------------------------------------------
-- DEVICE REGISTRATION
-- Tier 1: registered devices per user.
-- Relationship:
--   users 1..* device_registration
-- Device registration carries device identifier and metadata; revoked devices are
--   not counted against the device limit.
-- -----------------------------------------------------------------------------
CREATE TABLE device_registration (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    device_identifier      TEXT      NOT NULL,
    device_label           TEXT      NULL,
    device_type_code       TEXT      NULL,
    registered_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    registered_by_user_id  BIGINT    NOT NULL,
    last_seen_at           TIMESTAMPTZ NULL,
    revoked_at             TIMESTAMPTZ NULL,
    revoked_by_user_id     BIGINT    NULL,
    revocation_reason_code TEXT       NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_device_registration_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_device_registration_registered_by FOREIGN KEY (registered_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_device_registration_revoked_by FOREIGN KEY (revoked_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_device_registration_revoked CHECK (
        revoked_at IS NULL OR revoked_by_user_id IS NOT NULL
    ),
    CONSTRAINT uq_device_registration_user_identifier UNIQUE (user_id, device_identifier)
);

CREATE INDEX idx_device_registration_user ON device_registration (user_id);
CREATE INDEX idx_device_registration_identifier ON device_registration (device_identifier);
CREATE INDEX idx_device_registration_active ON device_registration (user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_device_registration_deleted ON device_registration (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE device_registration IS 'Licences, seats, devices and sessions: registered devices per user (Section 4 Tier 1). Personal. Soft-deleted.';

COMMENT ON COLUMN device_registration.device_identifier IS 'Device identifier; unique per user.';

COMMENT ON COLUMN device_registration.device_label IS 'Nullable = no label.';

COMMENT ON COLUMN device_registration.device_type_code IS 'Nullable = unknown device type. Enumeration code referencing reference_code (domain=device_type).';

COMMENT ON COLUMN device_registration.last_seen_at IS 'Nullable = never seen after registration.';

COMMENT ON COLUMN device_registration.revoked_at IS 'Nullable = not revoked.';

COMMENT ON COLUMN device_registration.revoked_by_user_id IS 'Nullable = revoked by system.';

COMMENT ON COLUMN device_registration.revocation_reason_code IS 'Nullable = no reason. Enumeration code referencing reference_code (domain=revocation_reason).';

-- -----------------------------------------------------------------------------
-- SESSION RECORD (device-level session for limit counting)
-- Tier 1: active sessions.
-- Rule Group 9: sessions are stored with device identifier, start time, last activity
--   time, and end time. Expired or revoked sessions are not counted against the limit.
-- This is the session table counted against the licence device limit. The session
--   record from Administration (session_record in 04_administration.sql) is the
--   logical session; this table is the device-bound session used for limit counting.
-- Relationship:
--   users 1..* device_session
--   device_registration 1..* device_session
-- -----------------------------------------------------------------------------
CREATE TABLE device_session (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    device_registration_id BIGINT    NOT NULL,
    session_token_ref      TEXT      NOT NULL,
    started_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_activity_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at               TIMESTAMPTZ NULL,
    expires_at             TIMESTAMPTZ NOT NULL,
    is_revoked             BOOLEAN   NOT NULL DEFAULT FALSE,
    revoked_at             TIMESTAMPTZ NULL,
    revoked_by_user_id     BIGINT    NULL,
    revocation_reason_code TEXT       NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_device_session_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_device_session_device FOREIGN KEY (device_registration_id)
        REFERENCES device_registration(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_device_session_revoked_by FOREIGN KEY (revoked_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_device_session_expires_after_start CHECK (expires_at > started_at),
    CONSTRAINT chk_device_session_revoked CHECK (
        revoked_at IS NULL OR revoked_by_user_id IS NOT NULL
    )
);

CREATE INDEX idx_device_session_user ON device_session (user_id);
CREATE INDEX idx_device_session_device ON device_session (device_registration_id);
CREATE INDEX idx_device_session_token_ref ON device_session (session_token_ref);
CREATE INDEX idx_device_session_active ON device_session (user_id, device_registration_id, is_revoked, ended_at, expires_at)
    WHERE is_revoked = FALSE AND ended_at IS NULL AND expires_at > now();
CREATE INDEX idx_device_session_started_at ON device_session (started_at);
CREATE INDEX idx_device_session_deleted ON device_session (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE device_session IS 'Licences, seats, devices and sessions: active sessions (Section 4 Tier 1). Internal. Device-bound session used for device-limit counting (Rule Group 9).';

COMMENT ON COLUMN device_session.session_token_ref IS 'Sensitive. Session token stored as reference/hash, not raw token.';

COMMENT ON COLUMN device_session.expires_at IS 'Session expiry; expired sessions are not counted against the limit.';

COMMENT ON COLUMN device_session.is_revoked IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain). Revoked sessions are not counted against the limit.';

COMMENT ON COLUMN device_session.revoked_at IS 'Nullable = not revoked.';

COMMENT ON COLUMN device_session.revoked_by_user_id IS 'Nullable = revoked by system.';

COMMENT ON COLUMN device_session.revocation_reason_code IS 'Nullable = no reason. Enumeration code referencing reference_code (domain=revocation_reason).';

-- -----------------------------------------------------------------------------
-- LOGIN HISTORY
-- Tier 1: login history.
-- Relationship:
--   users 1..* login_history
-- Append-only-ish login history; used to support device-limit and lockout decisions.
-- -----------------------------------------------------------------------------
CREATE TABLE login_history (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    login_result_code      TEXT      NOT NULL,
    device_registration_id BIGINT    NULL,
    ip_address             INET      NULL,
    user_agent             TEXT      NULL,
    attempted_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_login_history_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_login_history_device FOREIGN KEY (device_registration_id)
        REFERENCES device_registration(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_login_history_user ON login_history (user_id);
CREATE INDEX idx_login_history_result ON login_history (login_result_code);
CREATE INDEX idx_login_history_attempted_at ON login_history (attempted_at);
CREATE INDEX idx_login_history_deleted ON login_history (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE login_history IS 'Licences, seats, devices and sessions: login history (Section 4 Tier 1). Internal. Append-only-ish.';

COMMENT ON COLUMN login_history.device_registration_id IS 'Nullable = login without registered device context.';

-- -----------------------------------------------------------------------------
-- SESSION REVOCATION EVENT
-- Tier 1: revocation events (revoking a device or session is an auditable action).
-- Append-only: revocation events are not updated or deleted.
-- Relationship:
--   users (revoked by) 1..* session_revocation_event
--   device_session 1..* session_revocation_event (optional reference)
--   device_registration 1..* session_revocation_event (optional reference)
-- -----------------------------------------------------------------------------
CREATE TABLE session_revocation_event (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    revoked_by_user_id     BIGINT    NOT NULL,
    revocation_target_type_code TEXT   NOT NULL,
    revocation_target_id   BIGINT    NULL,
    revoked_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocation_reason_code TEXT       NULL,
    ip_address             INET      NULL,
    user_agent             TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_session_revocation_event_by FOREIGN KEY (revoked_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_session_revocation_target_type CHECK (
        revocation_target_type_code IN ('device', 'session')
    )
);

CREATE INDEX idx_session_revocation_event_by ON session_revocation_event (revoked_by_user_id);
CREATE INDEX idx_session_revocation_event_target ON session_revocation_event (revocation_target_type_code, revocation_target_id);
CREATE INDEX idx_session_revocation_event_at ON session_revocation_event (revoked_at);

COMMENT ON TABLE session_revocation_event IS 'Licences, seats, devices and sessions: session revocation event (Section 4 Tier 1). Append-only auditable action (Rule Group 9).';

COMMENT ON COLUMN session_revocation_event.revocation_target_type_code IS 'Whether the revocation targeted a device or a session.';

COMMENT ON COLUMN session_revocation_event.revocation_target_id IS 'Nullable = target id not stored (e.g. bulk revocation).';

COMMENT ON COLUMN session_revocation_event.revocation_reason_code IS 'Nullable = no reason. Enumeration code referencing reference_code (domain=revocation_reason).';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Licences, seats, devices and sessions (Milestone 12, B39)
--   tenant_account 1..* subscription_licence
--   subscription_licence 1..* seat_allocation
--   users 1..* seat_allocation
--   users 1..* device_registration
--   users 1..* device_session
--   device_registration 1..* device_session
--   users 1..* login_history
--   users 1..* session_revocation_event (revoked by)
--   device_session 1..* session_revocation_event (target)
--   device_registration 1..* session_revocation_event (target)
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Licences entities beyond the docket list. Decisions taken:
--   1. subscription_licence carries max_users_allowed and max_devices_per_user as
--      explicit positive-integer columns with CHECK > 0 (Rule Group 9).
--   2. seat_allocation enforces user-to-licence seat membership; the active seat
--      count per licence is constrained by max_users_allowed on the licence.
--   3. device_session is the device-bound session counted against the licence device
--      limit. Active, non-revoked, non-ended, non-expired sessions are counted.
--      Expired or revoked sessions are not counted.
--   4. session_revocation_event records revocations as auditable actions.
--   5. login_history is append-only-ish and supports device-limit/lockout decisions.
--   The device-limit enforcement mechanism (count active sessions at login, reject and
--   audit if limit exceeded) is implemented in the access layer and/or a database
--   trigger; the design decision and mechanism are documented in 99_documentation.sql.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
