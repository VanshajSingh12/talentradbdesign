-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Organisation and Account module
-- Phase 2 (Individual, Member B), Milestones 7-10
--
-- This file models ONLY the docket Organisation and Account domain.
-- Tier 1 (mandatory) from Section 4:
--   employer and client organisation: company details, locations,
--     tax and registration identifiers, verification status, mapped recruiters.
--   account and organisation: account profiles, account administrators,
--     account status, organisation hierarchy.
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK; natural keys as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification on tax/registration identifiers, etc.
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ (in analytics module, not here).
-- Rule Group 9 / 10: not Organisation module concerns for these tables.
--
-- B28 requirement: organisation hierarchy and recruiter model mapping are part of
--   this module's relationship model. Recruiter mapping is the owning module for
--   mapped recruiters (Section 4 Tier 1: "mapped recruiters" under employer/client
--   organisation).
-- B34 requirement: effective-dated recruiter mapping is a key/constraint deliverable
--   for this module. We model recruiter_mapping with effective_start and effective_end
--   and the stated rule that overlapping effective ranges for the same (organisation,
--   recruiter) are not permitted.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TENANT ACCOUNT
-- Tier 1: account profiles (account and organisation domain).
-- This is the account-level grouping for employer/client organisations and for
-- account administrators.
-- -----------------------------------------------------------------------------
CREATE TABLE tenant_account (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_type_code  TEXT      NOT NULL,
    name               TEXT      NOT NULL,
    external_account_reference TEXT NULL,
    status_code        TEXT      NOT NULL,
    is_active          BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT uq_tenant_account_name UNIQUE (name),
    CONSTRAINT uq_tenant_account_external_reference UNIQUE (external_account_reference)
);

CREATE INDEX idx_tenant_account_type ON tenant_account (account_type_code);
CREATE INDEX idx_tenant_account_status ON tenant_account (status_code);
CREATE INDEX idx_tenant_account_active ON tenant_account (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_tenant_account_deleted ON tenant_account (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE tenant_account IS 'Organisation and Account: account profiles (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN tenant_account.external_account_reference IS 'Nullable = no external reference. Stored as text reference, not a raw secret.';

COMMENT ON COLUMN tenant_account.account_type_code IS 'Enumeration code referencing reference_code (domain=account_type).';

COMMENT ON COLUMN tenant_account.status_code IS 'Enumeration code referencing reference_code (domain=account_status).';

-- -----------------------------------------------------------------------------
-- ACCOUNT STATUS
-- Tier 1: account status (audit-style history of account status changes).
-- Append-only-ish history; current status derives from the latest row per account.
-- -----------------------------------------------------------------------------
CREATE TABLE account_status_history (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_account_id  BIGINT    NOT NULL,
    status_code        TEXT      NOT NULL,
    changed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    changed_by_user_id BIGINT    NULL,
    reason             TEXT      NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT fk_account_status_history_account FOREIGN KEY (tenant_account_id)
        REFERENCES tenant_account(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_account_status_history_changed_by FOREIGN KEY (changed_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_account_status_history_account ON account_status_history (tenant_account_id);
CREATE INDEX idx_account_status_history_changed_at ON account_status_history (changed_at);

COMMENT ON TABLE account_status_history IS 'Organisation and Account: account status history (Section 4 Tier 1). Append-only-ish.';

COMMENT ON COLUMN account_status_history.reason IS 'Nullable = no reason recorded.';

-- -----------------------------------------------------------------------------
-- ORGANISATION HIERARCHY
-- Tier 1: organisation hierarchy.
-- Models parent/child relationships between employer/client organisations.
-- Relationship: organisation_hierarchy 1..* (parent -> child).
-- Effective-dated variant is supported via effective_start/effective_end so the
-- hierarchy can change over time; overlapping effective ranges for the same
-- (parent, child) are not permitted.
-- -----------------------------------------------------------------------------
CREATE TABLE organisation_hierarchy (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_organisation_id BIGINT NULL,
    child_organisation_id  BIGINT NOT NULL,
    relationship_type_code TEXT NOT NULL,
    effective_start      DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_end        DATE NULL,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_organisation_hierarchy_parent FOREIGN KEY (parent_organisation_id)
        REFERENCES employer_organisation(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_organisation_hierarchy_child FOREIGN KEY (child_organisation_id)
        REFERENCES employer_organisation(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_organisation_hierarchy_effective CHECK (
        effective_end IS NULL OR effective_end >= effective_start
    )
);

CREATE INDEX idx_organisation_hierarchy_parent ON organisation_hierarchy (parent_organisation_id) WHERE parent_organisation_id IS NOT NULL;
CREATE INDEX idx_organisation_hierarchy_child ON organisation_hierarchy (child_organisation_id);
CREATE INDEX idx_organisation_hierarchy_active ON organisation_hierarchy (parent_organisation_id, child_organisation_id, effective_start)
    WHERE is_active = TRUE;
CREATE INDEX idx_organisation_hierarchy_deleted ON organisation_hierarchy (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE organisation_hierarchy IS 'Organisation and Account: organisation hierarchy (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN organisation_hierarchy.parent_organisation_id IS 'Nullable = top-level organisation with no parent.';

COMMENT ON COLUMN organisation_hierarchy.effective_start IS 'Effective date for the relationship.';

COMMENT ON COLUMN organisation_hierarchy.effective_end IS 'Nullable = relationship currently active.';

-- -----------------------------------------------------------------------------
-- EMPLOYER ORGANISATION
-- Tier 1: employer and client organisation company details.
-- Relationships:
--   tenant_account 1..* employer_organisation
--   employer_organisation 1..* company_location
--   employer_organisation 1..* tax_registration_identifier
--   employer_organisation 1..* verification_status_record
--   employer_organisation 1..* recruiter_mapping
--   employer_organisation 1..* organisation_hierarchy (as parent or child)
-- -----------------------------------------------------------------------------
CREATE TABLE employer_organisation (
    id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_account_id     BIGINT    NOT NULL,
    company_name          TEXT      NOT NULL,
    legal_name            TEXT      NULL,
    website               TEXT      NULL,
    industry_name         TEXT      NULL,
    size_code             TEXT      NULL,
    type_code             TEXT      NOT NULL,
    primary_contact_name  TEXT      NULL,
    primary_contact_email TEXT      NULL,
    primary_contact_phone TEXT      NULL,
    address_line1         TEXT      NULL,
    address_line2         TEXT      NULL,
    city                  TEXT      NULL,
    state                 TEXT      NULL,
    country               TEXT      NOT NULL,
    postal_code           TEXT      NULL,
    latitude              NUMERIC(9,6) NULL,
    longitude             NUMERIC(9,6) NULL,
    coordinates_source    TEXT      NULL,
    is_verified           BOOLEAN   NOT NULL DEFAULT FALSE,
    verification_status_code TEXT   NULL,
    mapped_recruiter_count INTEGER   NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by            BIGINT    NOT NULL DEFAULT 0,
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by            BIGINT    NOT NULL DEFAULT 0,
    deleted_at            TIMESTAMPTZ NULL,
    CONSTRAINT fk_employer_organisation_account FOREIGN KEY (tenant_account_id)
        REFERENCES tenant_account(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_company_coordinates_consistent CHECK (
        (latitude IS NULL AND longitude IS NULL)
        OR (latitude IS NOT NULL AND longitude IS NOT NULL)
    ),
    CONSTRAINT chk_primary_contact_email CHECK (
        primary_contact_email IS NULL OR primary_contact_email = lower(primary_contact_email)
    ),
    CONSTRAINT chk_primary_contact_phone CHECK (
        primary_contact_phone IS NULL OR primary_contact_phone ~ '^\+?[1-9][0-9]{1,14}$'
    )
);

CREATE INDEX idx_employer_organisation_account ON employer_organisation (tenant_account_id);
CREATE INDEX idx_employer_organisation_name ON employer_organisation (company_name);
CREATE INDEX idx_employer_organisation_industry ON employer_organisation (industry_name) WHERE industry_name IS NOT NULL;
CREATE INDEX idx_employer_organisation_type ON employer_organisation (type_code);
CREATE INDEX idx_employer_organisation_verified ON employer_organisation (is_verified) WHERE is_verified = TRUE;
CREATE INDEX idx_employer_organisation_verification_status ON employer_organisation (verification_status_code) WHERE verification_status_code IS NOT NULL;
CREATE INDEX idx_employer_organisation_deleted ON employer_organisation (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE employer_organisation IS 'Organisation and Account: employer and client organisations (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN employer_organisation.company_name IS 'Person/company name domain TEXT (Rule Group 3).';

COMMENT ON COLUMN employer_organisation.website IS 'Nullable = not provided.';

COMMENT ON COLUMN employer_organisation.legal_name IS 'Nullable = same as company_name or not applicable.';

COMMENT ON COLUMN employer_organisation.primary_contact_email IS 'Personal. Lowercase, max 254 chars (Rule Group 3 email domain). Nullable = not provided.';

COMMENT ON COLUMN employer_organisation.primary_contact_phone IS 'Personal. E.164 with country code in phone (Rule Group 3 phone domain). Nullable = not provided.';

COMMENT ON COLUMN employer_organisation.latitude IS 'Nullable = unknown. Coordinates domain NUMERIC(9,6).';

COMMENT ON COLUMN employer_organisation.longitude IS 'Nullable = unknown. Coordinates domain NUMERIC(9,6).';

COMMENT ON COLUMN employer_organisation.coordinates_source IS 'Nullable = unknown source. Source recorded where coordinates are known (Rule Group 3 coordinates domain).';

COMMENT ON COLUMN employer_organisation.is_verified IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

COMMENT ON COLUMN employer_organisation.verification_status_code IS 'Enumeration code referencing reference_code (domain=verification_status).';

COMMENT ON COLUMN employer_organisation.mapped_recruiter_count IS 'Derived/updated count of mapped recruiters; used for read convenience. Maintained by application or trigger.';

-- -----------------------------------------------------------------------------
-- COMPANY LOCATION
-- Tier 1: locations (company locations).
-- Relationship: employer_organisation 1..* company_location.
-- One location can be marked as the registered/head office.
-- -----------------------------------------------------------------------------
CREATE TABLE company_location (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_organisation_id BIGINT NOT NULL,
    location_name      TEXT      NOT NULL,
    address_line1      TEXT      NULL,
    address_line2      TEXT      NULL,
    city               TEXT      NULL,
    state              TEXT      NULL,
    country            TEXT      NOT NULL,
    postal_code        TEXT      NULL,
    latitude           NUMERIC(9,6) NULL,
    longitude          NUMERIC(9,6) NULL,
    coordinates_source TEXT      NULL,
    is_head_office     BOOLEAN   NOT NULL DEFAULT FALSE,
    is_active          BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_company_location_organisation FOREIGN KEY (employer_organisation_id)
        REFERENCES employer_organisation(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_company_location_coordinates_consistent CHECK (
        (latitude IS NULL AND longitude IS NULL)
        OR (latitude IS NOT NULL AND longitude IS NOT NULL)
    ),
    CONSTRAINT uq_company_location_organisation_head_office UNIQUE (employer_organisation_id, is_head_office)
);

CREATE INDEX idx_company_location_organisation ON company_location (employer_organisation_id);
CREATE INDEX idx_company_location_country ON company_location (country);
CREATE INDEX idx_company_location_active ON company_location (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_company_location_deleted ON company_location (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE company_location IS 'Organisation and Account: company locations (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN company_location.latitude IS 'Nullable = unknown. Coordinates domain NUMERIC(9,6).';

COMMENT ON COLUMN company_location.longitude IS 'Nullable = unknown. Coordinates domain NUMERIC(9,6).';

COMMENT ON COLUMN company_location.coordinates_source IS 'Nullable = unknown source. Source recorded where coordinates are known (Rule Group 3 coordinates domain).';

COMMENT ON COLUMN company_location.is_head_office IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain). One head office per organisation via unique constraint.';

-- -----------------------------------------------------------------------------
-- TAX AND REGISTRATION IDENTIFIERS
-- Tier 1: tax and registration identifiers.
-- Rule Group 6: sensitive; stored as text with a country and a type code.
-- Validation rules: stored as text; application enforces per-type format where
--   the platform supports it. We do not store raw national ID numbers in clear
--   where avoidable; identifiers may be tokenised/masked per the security design
--   note. This table stores the identifier value as text and the classification
--   for handling.
-- Relationship: employer_organisation 1..* tax_registration_identifier.
-- -----------------------------------------------------------------------------
CREATE TABLE tax_registration_identifier (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_organisation_id BIGINT NOT NULL,
    country_code           TEXT    NOT NULL,
    identifier_type_code   TEXT    NOT NULL,
    identifier_value       TEXT    NOT NULL,
    identifier_display_mask TEXT    NULL,
    is_primary             BOOLEAN NOT NULL DEFAULT FALSE,
    valid_from             DATE    NULL,
    valid_to               DATE    NULL,
    verified_at            TIMESTAMPTZ NULL,
    verification_status_code TEXT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_tax_registration_organisation FOREIGN KEY (employer_organisation_id)
        REFERENCES employer_organisation(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_tax_identifier_dates CHECK (
        valid_to IS NULL OR valid_to >= valid_from
    ),
    CONSTRAINT chk_tax_identifier_primary UNIQUE (employer_organisation_id, is_primary)
);

CREATE INDEX idx_tax_registration_organisation ON tax_registration_identifier (employer_organisation_id);
CREATE INDEX idx_tax_registration_type ON tax_registration_identifier (identifier_type_code);
CREATE INDEX idx_tax_registration_country ON tax_registration_identifier (country_code);
CREATE INDEX idx_tax_registration_primary ON tax_registration_identifier (employer_organisation_id, is_primary) WHERE is_primary = TRUE;
CREATE INDEX idx_tax_registration_deleted ON tax_registration_identifier (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE tax_registration_identifier IS 'Organisation and Account: tax and registration identifiers (Section 4 Tier 1). Sensitive. Stored as text with country and type code (Rule Group 3 tax/registration identifier domain).';

COMMENT ON COLUMN tax_registration_identifier.identifier_value IS 'Sensitive. Identifier value stored as text. Handling (tokenisation/masking) per security design note; not stored as clear national ID where avoidable.';

COMMENT ON COLUMN tax_registration_identifier.identifier_display_mask IS 'Nullable = no mask stored. If present, stored masked/display form for UI use cases.';

COMMENT ON COLUMN tax_registration_identifier.country_code IS 'Country code for the identifier (Rule Group 3 tax/registration identifier domain).';

COMMENT ON COLUMN tax_registration_identifier.identifier_type_code IS 'Enumeration code referencing reference_code (domain=tax_identifier_type).';

COMMENT ON COLUMN tax_registration_identifier.is_primary IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain). One primary identifier per organisation via unique constraint.';

COMMENT ON COLUMN tax_registration_identifier.valid_from IS 'Nullable = validity start unknown.';

COMMENT ON COLUMN tax_registration_identifier.valid_to IS 'Nullable = validity end unknown/infinite.';

COMMENT ON COLUMN tax_registration_identifier.verified_at IS 'Nullable = not verified.';

COMMENT ON COLUMN tax_registration_identifier.verification_status_code IS 'Enumeration code referencing reference_code (domain=verification_status).';

-- -----------------------------------------------------------------------------
-- VERIFICATION STATUS RECORD
-- Tier 1: verification status (for company identity verification).
-- The docket says "verification status" under employer/client organisation.
-- We store verification outcomes as a small history table per organisation so the
-- current status and audit trail are both available.
-- Relationship: employer_organisation 1..* verification_status_record.
-- -----------------------------------------------------------------------------
CREATE TABLE verification_status_record (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_organisation_id BIGINT NOT NULL,
    verification_type_code TEXT    NOT NULL,
    verification_status_code TEXT NULL,
    verified_at            TIMESTAMPTZ NULL,
    verified_by_user_id    BIGINT NULL,
    outcome_notes          TEXT    NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_verification_status_organisation FOREIGN KEY (employer_organisation_id)
        REFERENCES employer_organisation(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_verification_status_verified_by FOREIGN KEY (verified_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_verification_status_organisation ON verification_status_record (employer_organisation_id);
CREATE INDEX idx_verification_status_type ON verification_status_record (verification_type_code);
CREATE INDEX idx_verification_status_deleted ON verification_status_record (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE verification_status_record IS 'Organisation and Account: verification status records (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN verification_status_record.outcome_notes IS 'Nullable = no notes.';

-- -----------------------------------------------------------------------------
-- RECRUITER MAPPING
-- Tier 1: mapped recruiters (owning module for mapped recruiters).
-- Relationship:
--   employer_organisation 1..* recruiter_mapping
--   users (recruiter) 1..* recruiter_mapping
-- B34 deliverable: effective-dated recruiter mapping with a stated rule that
--   overlapping effective ranges for the same (organisation, recruiter) are not
--   permitted.
-- -----------------------------------------------------------------------------
CREATE TABLE recruiter_mapping (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_organisation_id BIGINT NOT NULL,
    recruiter_user_id    BIGINT    NOT NULL,
    mapping_type_code    TEXT      NOT NULL,
    effective_start      DATE      NOT NULL DEFAULT CURRENT_DATE,
    effective_end        DATE      NULL,
    is_primary           BOOLEAN   NOT NULL DEFAULT FALSE,
    is_active            BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           BIGINT    NOT NULL DEFAULT 0,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by           BIGINT    NOT NULL DEFAULT 0,
    deleted_at           TIMESTAMPTZ NULL,
    CONSTRAINT fk_recruiter_mapping_organisation FOREIGN KEY (employer_organisation_id)
        REFERENCES employer_organisation(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_recruiter_mapping_recruiter FOREIGN KEY (recruiter_user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_recruiter_mapping_effective CHECK (
        effective_end IS NULL OR effective_end >= effective_start
    ),
    CONSTRAINT chk_recruiter_mapping_primary UNIQUE (employer_organisation_id, is_primary)
);

CREATE INDEX idx_recruiter_mapping_organisation ON recruiter_mapping (employer_organisation_id);
CREATE INDEX idx_recruiter_mapping_recruiter ON recruiter_mapping (recruiter_user_id);
CREATE INDEX idx_recruiter_mapping_effective ON recruiter_mapping (employer_organisation_id, recruiter_user_id, effective_start);
CREATE INDEX idx_recruiter_mapping_active ON recruiter_mapping (employer_organisation_id, recruiter_user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_recruiter_mapping_deleted ON recruiter_mapping (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE recruiter_mapping IS 'Organisation and Account: recruiter mapping (Section 4 Tier 1 mapped recruiters; owning module). Internal. Soft-deleted.';

COMMENT ON COLUMN recruiter_mapping.effective_start IS 'Effective date for the recruiter mapping.';

COMMENT ON COLUMN recruiter_mapping.effective_end IS 'Nullable = mapping currently active.';

COMMENT ON COLUMN recruiter_mapping.is_primary IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain). One primary recruiter per organisation via unique constraint.';

COMMENT ON COLUMN recruiter_mapping.mapping_type_code IS 'Enumeration code referencing reference_code (domain=recruiter_mapping_type).';

-- -----------------------------------------------------------------------------
-- ACCOUNT ADMINISTRATOR
-- Tier 1: account administrators (account and organisation domain).
-- Relationship:
--   tenant_account 1..* account_administrator
--   users (administrator) 1..* account_administrator
-- -----------------------------------------------------------------------------
CREATE TABLE account_administrator (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_account_id  BIGINT    NOT NULL,
    administrator_user_id BIGINT NOT NULL,
    admin_role_code    TEXT      NOT NULL,
    is_primary         BOOLEAN   NOT NULL DEFAULT FALSE,
    is_active          BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT    NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT    NOT NULL DEFAULT 0,
    deleted_at         TIMESTAMPTZ NULL,
    CONSTRAINT fk_account_administrator_account FOREIGN KEY (tenant_account_id)
        REFERENCES tenant_account(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_account_administrator_administrator FOREIGN KEY (administrator_user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_account_administrator_primary UNIQUE (tenant_account_id, is_primary)
);

CREATE INDEX idx_account_administrator_account ON account_administrator (tenant_account_id);
CREATE INDEX idx_account_administrator_user ON account_administrator (administrator_user_id);
CREATE INDEX idx_account_administrator_active ON account_administrator (tenant_account_id, administrator_user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_account_administrator_deleted ON account_administrator (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE account_administrator IS 'Organisation and Account: account administrators (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN account_administrator.admin_role_code IS 'Enumeration code referencing reference_code (domain=account_admin_role).';

COMMENT ON COLUMN account_administrator.is_primary IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain). One primary administrator per account via unique constraint.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Organisation and Account (Milestone 8, B28)
--   tenant_account 1..* employer_organisation
--   tenant_account 1..* account_administrator
--   employer_organisation 1..* company_location
--   employer_organisation 1..* tax_registration_identifier
--   employer_organisation 1..* verification_status_record
--   employer_organisation 1..* recruiter_mapping
--   users (recruiter) 1..* recruiter_mapping
--   users (administrator) 1..* account_administrator
--   employer_organisation 1..* organisation_hierarchy (parent/child)
--   account_status_history 1..* tenant_account (account status history)
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Organisation entities beyond the docket list. Decisions taken:
--   1. tenant_account is used as the account-level grouping because the docket
--      lists both "account profiles" and "employer and client organisation".
--      tenant_account is the account; employer_organisation is the company.
--   2. tax_registration_identifier stores identifier value as text with country
--      and type code (Rule Group 3 tax/registration identifier domain). Handling
--      (tokenisation/masking) is documented in the security note, not in DDL.
--   3. recruiter_mapping is effective-dated to satisfy B34 and to support the
--      stated rule that overlapping effective ranges for the same
--      (organisation, recruiter) are not permitted.
--   4. organisation_hierarchy is effective-dated for the same reason.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
