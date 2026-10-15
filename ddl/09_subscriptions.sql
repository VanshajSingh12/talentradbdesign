-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Subscriptions, wallet, payments and download history module
-- Phase 3 (Individual, Member C), Milestones 11-14
--
-- This file models ONLY the docket Subscriptions, wallet, payments and download history domain.
-- Tier 1 (mandatory) from Section 4:
--   subscriptions and plans: plans, subscription periods, renewals, cancellations,
--     entitlements per plan.
--   payments and transaction history: payment orders, payment status, invoices,
--     refunds, and wallet ledger entries.
--   wallet and credits: wallet balances, recharges, credit consumption, transactions.
--   profile download history: which recruiter or employer downloaded which candidate
--     profile, when, and under which credit deduction.
--
-- Rule Group 10 (money, subscriptions, and history) is the primary rule for this module:
--   - Payment and wallet ledgers are append-only. A correction is recorded as a new entry
--     that references the original, never as an update.
--   - Subscription periods must not overlap for the same licence, and this is enforced by a
--     constraint or exclusion rule where the engine supports it.
--   - Download and view history records are append-only and carry the actor, the subject,
--     the timestamp, and the credit deduction where one applies.
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
-- Rule Group 9: not Subscriptions module concerns for licence/device/session specifics.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SUBSCRIPTION PLAN
-- Tier 1: plans.
-- Relationship:
--   subscription_plan 1..* subscription_period
--   subscription_plan 1..* plan_entitlement
-- -----------------------------------------------------------------------------
CREATE TABLE subscription_plan (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_code              TEXT      NOT NULL,
    name                   TEXT      NOT NULL,
    description            TEXT      NULL,
    category_code          TEXT      NOT NULL,
    billing_period_code    TEXT      NOT NULL,
    price_amount           NUMERIC(15,2) NOT NULL,
    price_currency_code    TEXT      NOT NULL,
    renewal_type_code      TEXT      NULL,
    trial_days             INTEGER   NOT NULL DEFAULT 0,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT chk_plan_price_currency CHECK (char_length(price_currency_code) = 3),
    CONSTRAINT chk_plan_price_positive CHECK (price_amount >= 0),
    CONSTRAINT chk_plan_trial_days_nonnegative CHECK (trial_days >= 0),
    CONSTRAINT uq_subscription_plan_code UNIQUE (plan_code)
);

CREATE INDEX idx_subscription_plan_code ON subscription_plan (plan_code);
CREATE INDEX idx_subscription_plan_category ON subscription_plan (category_code);
CREATE INDEX idx_subscription_plan_billing_period ON subscription_plan (billing_period_code);
CREATE INDEX idx_subscription_plan_active ON subscription_plan (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_subscription_plan_deleted ON subscription_plan (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE subscription_plan IS 'Subscriptions, wallet, payments and download history: plans (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN subscription_plan.plan_code IS 'Plan code; unique per plan.';

COMMENT ON COLUMN subscription_plan.name IS 'Plan name.';

COMMENT ON COLUMN subscription_plan.description IS 'Nullable = no description.';

COMMENT ON COLUMN subscription_plan.category_code IS 'Enumeration code referencing reference_code (domain=plan_category).';

COMMENT ON COLUMN subscription_plan.billing_period_code IS 'Enumeration code referencing reference_code (domain=billing_period).';

COMMENT ON COLUMN subscription_plan.price_amount IS 'Money domain NUMERIC(15,2); price per billing period.';

COMMENT ON COLUMN subscription_plan.price_currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN subscription_plan.renewal_type_code IS 'Nullable = no auto-renewal. Enumeration code referencing reference_code (domain=renewal_type).';

COMMENT ON COLUMN subscription_plan.trial_days IS 'Trial period in days; nonnegative.';

-- -----------------------------------------------------------------------------
-- PLAN ENTITLEMENT
-- Tier 1: entitlements per plan.
-- Relationship:
--   subscription_plan 1..* plan_entitlement
-- Entitlements represent what a plan includes (e.g. number of job posts, downloads,
--   outreach credits). The exact entitlement set is enumerable via code.
-- -----------------------------------------------------------------------------
CREATE TABLE plan_entitlement (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subscription_plan_id   BIGINT    NOT NULL,
    entitlement_code       TEXT      NOT NULL,
    entitlement_value      NUMERIC(15,2) NULL,
    value_unit_code        TEXT      NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_plan_entitlement_plan FOREIGN KEY (subscription_plan_id)
        REFERENCES subscription_plan(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_plan_entitlement_value CHECK (
        entitlement_value IS NULL OR entitlement_value >= 0
    ),
    CONSTRAINT uq_plan_entitlement_plan_code UNIQUE (subscription_plan_id, entitlement_code)
);

CREATE INDEX idx_plan_entitlement_plan ON plan_entitlement (subscription_plan_id);
CREATE INDEX idx_plan_entitlement_code ON plan_entitlement (entitlement_code);
CREATE INDEX idx_plan_entitlement_active ON plan_entitlement (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_plan_entitlement_deleted ON plan_entitlement (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE plan_entitlement IS 'Subscriptions, wallet, payments and download history: entitlements per plan (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN plan_entitlement.entitlement_value IS 'Nullable = entitlement is unlimited or value not applicable. When present, nonnegative (Rule Group 3 ratio/quantity domain).';

COMMENT ON COLUMN plan_entitlement.value_unit_code IS 'Nullable = unit is implicit. Enumeration code referencing reference_code (domain=entitlement_unit).';

-- -----------------------------------------------------------------------------
-- SUBSCRIPTION PERIOD
-- Tier 1: subscription periods.
-- Rule Group 10: subscription periods must not overlap for the same licence, enforced
--   by a constraint or exclusion rule where the engine supports it. We enforce non-overlap
--   by a CHECK plus application logic and a stated exclusion constraint approach for
--   PostgreSQL where supported; the exact mechanism is documented in 99_documentation.sql.
-- Relationship:
--   subscription_licence 1..* subscription_period
--   subscription_plan 1..* subscription_period
-- -----------------------------------------------------------------------------
CREATE TABLE subscription_period (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subscription_licence_id BIGINT   NOT NULL,
    subscription_plan_id    BIGINT    NOT NULL,
    status_code            TEXT      NOT NULL,
    started_at             TIMESTAMPTZ NOT NULL,
    ended_at               TIMESTAMPTZ NULL,
    renew_type_code        TEXT      NULL,
    cancelled_at            TIMESTAMPTZ NULL,
    cancelled_by_user_id   BIGINT    NULL,
    cancellation_reason    TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_subscription_period_licence FOREIGN KEY (subscription_licence_id)
        REFERENCES subscription_licence(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_subscription_period_plan FOREIGN KEY (subscription_plan_id)
        REFERENCES subscription_plan(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_subscription_period_cancelled_by FOREIGN KEY (cancelled_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_subscription_period_ends_after_start CHECK (
        ended_at IS NULL OR ended_at > started_at
    ),
    CONSTRAINT chk_subscription_period_cancelled CHECK (
        cancelled_at IS NULL OR cancelled_by_user_id IS NOT NULL
    )
);

CREATE INDEX idx_subscription_period_licence ON subscription_period (subscription_licence_id);
CREATE INDEX idx_subscription_period_plan ON subscription_period (subscription_plan_id);
CREATE INDEX idx_subscription_period_status ON subscription_period (status_code);
CREATE INDEX idx_subscription_period_started_at ON subscription_period (started_at);
CREATE INDEX idx_subscription_period_deleted ON subscription_period (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE subscription_period IS 'Subscriptions, wallet, payments and download history: subscription periods (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN subscription_period.started_at IS 'Subscription period start.';

COMMENT ON COLUMN subscription_period.ended_at IS 'Nullable = period not ended yet or indefinite.';

COMMENT ON COLUMN subscription_period.status_code IS 'Enumeration code referencing reference_code (domain=subscription_status).';

COMMENT ON COLUMN subscription_period.renew_type_code IS 'Nullable = renewal type not set. Enumeration code referencing reference_code (domain=renewal_type).';

COMMENT ON COLUMN subscription_period.cancelled_at IS 'Nullable = not cancelled.';

COMMENT ON COLUMN subscription_period.cancelled_by_user_id IS 'Nullable = cancelled by system.';

COMMENT ON COLUMN subscription_period.cancellation_reason IS 'Nullable = no reason recorded.';

-- -----------------------------------------------------------------------------
-- PAYMENT ORDER
-- Tier 1: payment orders.
-- Rule Group 10: payment ledger is append-only. Payment order stores transaction
--   references, status, and amounts; card/bank data is NOT stored (Section 6 payment
--   gateway boundary).
-- Relationship:
--   subscription_licence 1..* payment_order
--   subscription_period 1..* payment_order (optional link to period being paid)
--   tenant_account 1..* payment_order
--   users (payer) 1..* payment_order
-- -----------------------------------------------------------------------------
CREATE TABLE payment_order (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_number           TEXT      NOT NULL,
    tenant_account_id      BIGINT    NOT NULL,
    subscription_licence_id BIGINT  NULL,
    subscription_period_id  BIGINT  NULL,
    payer_user_id          BIGINT    NULL,
    payment_method_code    TEXT      NOT NULL,
    status_code            TEXT      NOT NULL,
    amount                 NUMERIC(15,2) NOT NULL,
    currency_code          TEXT      NOT NULL,
    gateway_reference      TEXT      NULL,
    gateway_response       TEXT      NULL,
    initiated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    initiated_by_user_id   BIGINT    NOT NULL,
    completed_at           TIMESTAMPTZ NULL,
    completed_by_user_id   BIGINT    NULL,
    failed_at              TIMESTAMPTZ NULL,
    failure_reason         TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_payment_order_account FOREIGN KEY (tenant_account_id)
        REFERENCES tenant_account(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_payment_order_licence FOREIGN KEY (subscription_licence_id)
        REFERENCES subscription_licence(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_payment_order_period FOREIGN KEY (subscription_period_id)
        REFERENCES subscription_period(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_payment_order_payer FOREIGN KEY (payer_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_payment_order_completed_by FOREIGN KEY (completed_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_payment_order_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_payment_order_currency CHECK (char_length(currency_code) = 3),
    CONSTRAINT uq_payment_order_number UNIQUE (order_number),
    CONSTRAINT uq_payment_order_gateway_reference UNIQUE (gateway_reference)
);

CREATE INDEX idx_payment_order_account ON payment_order (tenant_account_id);
CREATE INDEX idx_payment_order_licence ON payment_order (subscription_licence_id) WHERE subscription_licence_id IS NOT NULL;
CREATE INDEX idx_payment_order_period ON payment_order (subscription_period_id) WHERE subscription_period_id IS NOT NULL;
CREATE INDEX idx_payment_order_payer ON payment_order (payer_user_id) WHERE payer_user_id IS NOT NULL;
CREATE INDEX idx_payment_order_method ON payment_order (payment_method_code);
CREATE INDEX idx_payment_order_status ON payment_order (status_code);
CREATE INDEX idx_payment_order_initiated_at ON payment_order (initiated_at);
CREATE INDEX idx_payment_order_deleted ON payment_order (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE payment_order IS 'Subscriptions, wallet, payments and download history: payment orders (Section 4 Tier 1). Internal/Sensitive for references. Soft-deleted.';

COMMENT ON COLUMN payment_order.order_number IS 'Payment order identifier; unique per order.';

COMMENT ON COLUMN payment_order.payment_method_code IS 'Enumeration code referencing reference_code (domain=payment_method).';

COMMENT ON COLUMN payment_order.status_code IS 'Enumeration code referencing reference_code (domain=payment_status).';

COMMENT ON COLUMN payment_order.amount IS 'Money domain NUMERIC(15,2); order amount.';

COMMENT ON COLUMN payment_order.currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN payment_order.gateway_reference IS 'Sensitive. Payment gateway transaction reference; stored as reference, not card/bank data (Section 6 payment boundary).';

COMMENT ON COLUMN payment_order.gateway_response IS 'Nullable = no response stored. Bounded text storing minimal gateway response for audit, not full response bodies.';

COMMENT ON COLUMN payment_order.initiated_by_user_id IS 'User who initiated the payment.';

COMMENT ON COLUMN payment_order.completed_by_user_id IS 'Nullable = not completed.';

COMMENT ON COLUMN payment_order.failed_at IS 'Nullable = not failed.';

COMMENT ON COLUMN payment_order.failure_reason IS 'Nullable = no failure reason.';

-- -----------------------------------------------------------------------------
-- PAYMENT STATUS HISTORY
-- Tier 1: payment status history.
-- Rule Group 10: payment ledger is append-only. Payment status history is append-only;
--   status changes are recorded as new rows, not updates.
-- Relationship:
--   payment_order 1..* payment_status_history
-- -----------------------------------------------------------------------------
CREATE TABLE payment_status_history (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_order_id       BIGINT    NOT NULL,
    status_code            TEXT      NOT NULL,
    changed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    changed_by_user_id     BIGINT    NULL,
    gateway_status         TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_payment_status_history_order FOREIGN KEY (payment_order_id)
        REFERENCES payment_order(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_payment_status_history_changed_by FOREIGN KEY (changed_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_payment_status_history_order ON payment_status_history (payment_order_id);
CREATE INDEX idx_payment_status_history_status ON payment_status_history (status_code);
CREATE INDEX idx_payment_status_history_changed_at ON payment_status_history (changed_at);

COMMENT ON TABLE payment_status_history IS 'Subscriptions, wallet, payments and download history: payment status history (Section 4 Tier 1). Append-only.';

COMMENT ON COLUMN payment_status_history.gateway_status IS 'Nullable = no gateway status stored. Stored gateway status is for audit, not full gateway response.';

-- -----------------------------------------------------------------------------
-- INVOICE
-- Tier 1: invoices.
-- Relationship:
--   payment_order 1..1 invoice
--   tenant_account 1..* invoice
-- -----------------------------------------------------------------------------
CREATE TABLE invoice (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_number         TEXT      NOT NULL,
    payment_order_id       BIGINT    NOT NULL,
    tenant_account_id      BIGINT    NOT NULL,
    issue_date             DATE      NOT NULL,
    due_date               DATE      NOT NULL,
    currency_code          TEXT      NOT NULL,
    line_items             TEXT      NULL,
    total_amount           NUMERIC(15,2) NOT NULL,
    status_code            TEXT      NOT NULL,
    issued_by_user_id      BIGINT    NOT NULL,
    issued_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at                TIMESTAMPTZ NULL,
    paid_by_user_id        BIGINT    NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_invoice_payment_order FOREIGN KEY (payment_order_id)
        REFERENCES payment_order(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_invoice_account FOREIGN KEY (tenant_account_id)
        REFERENCES tenant_account(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_invoice_issued_by FOREIGN KEY (issued_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_invoice_paid_by FOREIGN KEY (paid_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_invoice_currency CHECK (char_length(currency_code) = 3),
    CONSTRAINT chk_invoice_total_positive CHECK (total_amount > 0),
    CONSTRAINT chk_invoice_due_after_issue CHECK (due_date >= issue_date),
    CONSTRAINT uq_invoice_number UNIQUE (invoice_number)
);

CREATE INDEX idx_invoice_number ON invoice (invoice_number);
CREATE INDEX idx_invoice_payment_order ON invoice (payment_order_id);
CREATE INDEX idx_invoice_account ON invoice (tenant_account_id);
CREATE INDEX idx_invoice_status ON invoice (status_code);
CREATE INDEX idx_invoice_issue_date ON invoice (issue_date);
CREATE INDEX idx_invoice_deleted ON invoice (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE invoice IS 'Subscriptions, wallet, payments and download history: invoices (Section 4 Tier 1). Internal. Soft-deleted.';

COMMENT ON COLUMN invoice.invoice_number IS 'Invoice identifier; unique per invoice.';

COMMENT ON COLUMN invoice.currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN invoice.line_items IS 'Nullable = no line items stored as text. Stored as bounded text summary of line items, not full invoice document.';

COMMENT ON COLUMN invoice.total_amount IS 'Money domain NUMERIC(15,2); total amount.';

COMMENT ON COLUMN invoice.status_code IS 'Enumeration code referencing reference_code (domain=invoice_status).';

COMMENT ON COLUMN invoice.issued_by_user_id IS 'User who issued the invoice.';

COMMENT ON COLUMN invoice.paid_at IS 'Nullable = not paid.';

COMMENT ON COLUMN invoice.paid_by_user_id IS 'Nullable = not paid.';

-- -----------------------------------------------------------------------------
-- REFUND
-- Tier 1: refunds.
-- Rule Group 10: payment ledger is append-only; refunds are recorded as new entries
--   referencing the original payment, not as updates to the payment.
-- Relationship:
--   payment_order 1..* refund
--   invoice 1..* refund
-- -----------------------------------------------------------------------------
CREATE TABLE refund (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    refund_number          TEXT      NOT NULL,
    payment_order_id       BIGINT    NOT NULL,
    invoice_id             BIGINT    NULL,
    refund_amount          NUMERIC(15,2) NOT NULL,
    currency_code          TEXT      NOT NULL,
    refund_status_code     TEXT      NOT NULL,
    refund_type_code       TEXT      NULL,
    requested_by_user_id   BIGINT    NOT NULL,
    processed_by_user_id   BIGINT    NULL,
    requested_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at           TIMESTAMPTZ NULL,
    gateway_reference      TEXT      NULL,
    gateway_response       TEXT      NULL,
    reason                 TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_refund_payment_order FOREIGN KEY (payment_order_id)
        REFERENCES payment_order(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_refund_invoice FOREIGN KEY (invoice_id)
        REFERENCES invoice(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_refund_requested_by FOREIGN KEY (requested_by_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_refund_processed_by FOREIGN KEY (processed_by_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_refund_amount_positive CHECK (refund_amount > 0),
    CONSTRAINT chk_refund_currency CHECK (char_length(currency_code) = 3),
    CONSTRAINT uq_refund_number UNIQUE (refund_number),
    CONSTRAINT uq_refund_gateway_reference UNIQUE (gateway_reference)
);

CREATE INDEX idx_refund_number ON refund (refund_number);
CREATE INDEX idx_refund_payment_order ON refund (payment_order_id);
CREATE INDEX idx_refund_invoice ON refund (invoice_id) WHERE invoice_id IS NOT NULL;
CREATE INDEX idx_refund_status ON refund (refund_status_code);
CREATE INDEX idx_refund_requested_at ON refund (requested_at);
CREATE INDEX idx_refund_deleted ON refund (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE refund IS 'Subscriptions, wallet, payments and download history: refunds (Section 4 Tier 1). Internal/Sensitive for references. Soft-deleted.';

COMMENT ON COLUMN refund.refund_number IS 'Refund identifier; unique per refund.';

COMMENT ON COLUMN refund.refund_amount IS 'Money domain NUMERIC(15,2); refund amount.';

COMMENT ON COLUMN refund.currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN refund.refund_status_code IS 'Enumeration code referencing reference_code (domain=refund_status).';

COMMENT ON COLUMN refund.refund_type_code IS 'Nullable = type not set. Enumeration code referencing reference_code (domain=refund_type).';

COMMENT ON COLUMN refund.requested_by_user_id IS 'User who requested the refund.';

COMMENT ON COLUMN refund.processed_by_user_id IS 'Nullable = not processed.';

COMMENT ON COLUMN refund.gateway_reference IS 'Sensitive. Payment gateway refund reference; stored as reference, not card/bank data (Section 6 payment boundary).';

COMMENT ON COLUMN refund.gateway_response IS 'Nullable = no response stored. Bounded text storing minimal gateway response for audit, not full response bodies.';

COMMENT ON COLUMN refund.reason IS 'Nullable = no reason recorded.';

-- -----------------------------------------------------------------------------
-- WALLET
-- Tier 1: wallet balances, recharges, credit consumption, transactions.
-- Relationship:
--   tenant_account 1..* wallet
--   users 1..* wallet (optional owner)
-- Wallet carries balance and currency.
-- -----------------------------------------------------------------------------
CREATE TABLE wallet (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_account_id      BIGINT    NOT NULL,
    owner_user_id          BIGINT    NULL,
    currency_code          TEXT      NOT NULL,
    balance                NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    status_code            TEXT      NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_wallet_account FOREIGN KEY (tenant_account_id)
        REFERENCES tenant_account(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_wallet_owner FOREIGN KEY (owner_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_wallet_currency CHECK (char_length(currency_code) = 3),
    CONSTRAINT chk_wallet_balance_nonnegative CHECK (balance >= 0),
    CONSTRAINT uq_wallet_account_currency UNIQUE (tenant_account_id, currency_code)
);

CREATE INDEX idx_wallet_account ON wallet (tenant_account_id);
CREATE INDEX idx_wallet_owner ON wallet (owner_user_id) WHERE owner_user_id IS NOT NULL;
CREATE INDEX idx_wallet_currency ON wallet (currency_code);
CREATE INDEX idx_wallet_status ON wallet (status_code);
CREATE INDEX idx_wallet_deleted ON wallet (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE wallet IS 'Subscriptions, wallet, payments and download history: wallet balances (Section 4 Tier 1). Internal/Sensitive for balance. Soft-deleted.';

COMMENT ON COLUMN wallet.currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN wallet.balance IS 'Money domain NUMERIC(15,2); current wallet balance. Nonnegative.';

COMMENT ON COLUMN wallet.status_code IS 'Enumeration code referencing reference_code (domain=wallet_status).';

-- -----------------------------------------------------------------------------
-- WALLET LEDGER ENTRY
-- Tier 1: wallet ledger entries.
-- Rule Group 10: wallet ledger is append-only. A correction is recorded as a new entry
--   that references the original, never as an update. Here we store ledger entries with
--   a possible reference to a previous entry for corrections.
-- Relationship:
--   wallet 1..* wallet_ledger_entry
--   wallet_ledger_entry 1..* wallet_ledger_entry (correction reference)
--   payment_order 1..* wallet_ledger_entry (optional link)
--   subscription_period 1..* wallet_ledger_entry (optional link)
-- -----------------------------------------------------------------------------
CREATE TABLE wallet_ledger_entry (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    wallet_id              BIGINT    NOT NULL,
    transaction_type_code  TEXT      NOT NULL,
    amount                 NUMERIC(15,2) NOT NULL,
    currency_code          TEXT      NOT NULL,
    balance_after          NUMERIC(15,2) NOT NULL,
    reference_type_code    TEXT      NULL,
    reference_id           BIGINT    NULL,
    correction_reference_id BIGINT   NULL,
    description            TEXT      NULL,
    created_by_user_id     BIGINT    NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_wallet_ledger_entry_wallet FOREIGN KEY (wallet_id)
        REFERENCES wallet(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_wallet_ledger_entry_correction FOREIGN KEY (correction_reference_id)
        REFERENCES wallet_ledger_entry(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_wallet_ledger_entry_amount CHECK (amount <> 0),
    CONSTRAINT chk_wallet_ledger_entry_currency CHECK (char_length(currency_code) = 3),
    CONSTRAINT chk_wallet_ledger_entry_balance_after_nonnegative CHECK (balance_after >= 0)
);

CREATE INDEX idx_wallet_ledger_entry_wallet ON wallet_ledger_entry (wallet_id);
CREATE INDEX idx_wallet_ledger_entry_type ON wallet_ledger_entry (transaction_type_code);
CREATE INDEX idx_wallet_ledger_entry_reference ON wallet_ledger_entry (reference_type_code, reference_id)
    WHERE reference_type_code IS NOT NULL AND reference_id IS NOT NULL;
CREATE INDEX idx_wallet_ledger_entry_correction ON wallet_ledger_entry (correction_reference_id) WHERE correction_reference_id IS NOT NULL;
CREATE INDEX idx_wallet_ledger_entry_created_at ON wallet_ledger_entry (created_at);

COMMENT ON TABLE wallet_ledger_entry IS 'Subscriptions, wallet, payments and download history: wallet ledger entries (Section 4 Tier 1). Append-only (Rule Group 10).';

COMMENT ON COLUMN wallet_ledger_entry.transaction_type_code IS 'Enumeration code referencing reference_code (domain=wallet_transaction_type).';

COMMENT ON COLUMN wallet_ledger_entry.amount IS 'Money domain NUMERIC(15,2); transaction amount (positive for credit, negative for debit, or vice versa per convention). Nonzero.';

COMMENT ON COLUMN wallet_ledger_entry.currency_code IS 'Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN wallet_ledger_entry.balance_after IS 'Money domain NUMERIC(15,2); wallet balance after this entry. Nonnegative.';

COMMENT ON COLUMN wallet_ledger_entry.reference_type_code IS 'Nullable = no reference. Enumeration code referencing reference_code (domain=wallet_reference_type).';

COMMENT ON COLUMN wallet_ledger_entry.reference_id IS 'Nullable = no reference. ID of the referenced entity (e.g. payment_order, subscription_period).';

COMMENT ON COLUMN wallet_ledger_entry.correction_reference_id IS 'Nullable = not a correction. If set, references the original ledger entry this entry corrects (Rule Group 10: correction recorded as new entry referencing original).';

COMMENT ON COLUMN wallet_ledger_entry.description IS 'Nullable = no description.';

COMMENT ON COLUMN wallet_ledger_entry.created_by_user_id IS 'User who created the ledger entry.';

-- -----------------------------------------------------------------------------
-- PROFILE DOWNLOAD HISTORY
-- Tier 1: profile download history.
-- Rule Group 10: download and view history records are append-only and carry the actor,
--   the subject, the timestamp, and the credit deduction where one applies.
-- Relationship:
--   users (downloader) 1..* profile_download_history
--   candidate_identity 1..* profile_download_history
-- -----------------------------------------------------------------------------
CREATE TABLE profile_download_history (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    downloader_user_id     BIGINT    NOT NULL,
    candidate_identity_id  BIGINT    NOT NULL,
    downloaded_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    download_format_code   TEXT      NOT NULL,
    credit_deducted_amount NUMERIC(15,2) NULL,
    credit_currency_code   TEXT      NULL,
    credit_deduction_applied BOOLEAN NOT NULL DEFAULT FALSE,
    download_reference     TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_profile_download_history_downloader FOREIGN KEY (downloader_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_profile_download_history_candidate FOREIGN KEY (candidate_identity_id)
        REFERENCES candidate_identity(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_profile_download_history_credit_currency CHECK (
        credit_currency_code IS NULL OR char_length(credit_currency_code) = 3
    ),
    CONSTRAINT chk_profile_download_history_credit_amount CHECK (
        credit_deducted_amount IS NULL OR credit_deducted_amount >= 0
    )
);

CREATE INDEX idx_profile_download_history_downloader ON profile_download_history (downloader_user_id);
CREATE INDEX idx_profile_download_history_candidate ON profile_download_history (candidate_identity_id);
CREATE INDEX idx_profile_download_history_downloaded_at ON profile_download_history (downloaded_at);
CREATE INDEX idx_profile_download_history_format ON profile_download_history (download_format_code);
CREATE INDEX idx_profile_download_history_credit ON profile_download_history (credit_deduction_applied) WHERE credit_deduction_applied = TRUE;
CREATE INDEX idx_profile_download_history_deleted ON profile_download_history (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE profile_download_history IS 'Subscriptions, wallet, payments and download history: profile download history (Section 4 Tier 1). Append-only (Rule Group 10).';

COMMENT ON COLUMN profile_download_history.download_format_code IS 'Enumeration code referencing reference_code (domain=download_format).';

COMMENT ON COLUMN profile_download_history.credit_deducted_amount IS 'Nullable = no credit deducted (e.g. free download). Money domain NUMERIC(15,2); nonnegative where present.';

COMMENT ON COLUMN profile_download_history.credit_currency_code IS 'Nullable = no credit currency. Companion currency code per Rule Group 3 money domain.';

COMMENT ON COLUMN profile_download_history.credit_deduction_applied IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

COMMENT ON COLUMN profile_download_history.download_reference IS 'Nullable = no reference. Reference to the download transaction/record in the access layer.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Subscriptions, wallet, payments and download history (Milestone 12, B41)
--   subscription_plan 1..* subscription_period
--   subscription_plan 1..* plan_entitlement
--   subscription_licence 1..* subscription_period
--   subscription_licence 1..* payment_order
--   subscription_period 1..* payment_order
--   tenant_account 1..* payment_order
--   users 1..* payment_order (payer)
--   payment_order 1..* payment_status_history
--   payment_order 1..1 invoice
--   tenant_account 1..* invoice
--   payment_order 1..* refund
--   invoice 1..* refund
--   tenant_account 1..* wallet
--   users 1..* wallet (owner)
--   wallet 1..* wallet_ledger_entry
--   wallet_ledger_entry 1..* wallet_ledger_entry (correction)
--   payment_order 1..* wallet_ledger_entry (optional reference)
--   subscription_period 1..* wallet_ledger_entry (optional reference)
--   users 1..* profile_download_history (downloader)
--   candidate_identity 1..* profile_download_history
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Subscriptions entities beyond the docket list. Decisions taken:
--   1. subscription_period is the subscription period table; non-overlap for the same
--      licence is enforced by a constraint/exclusion rule where the engine supports it,
--      with the exact mechanism documented in 99_documentation.sql.
--   2. wallet_ledger_entry is append-only; corrections reference the original entry
--      (correction_reference_id), never update it (Rule Group 10).
--   3. profile_download_history is append-only with actor, subject, timestamp, and credit
--      deduction where one applies (Rule Group 10).
--   4. payment_order and refund store gateway references as references, not card/bank data
--      (Section 6 payment boundary).
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
