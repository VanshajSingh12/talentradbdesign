#!/usr/bin/env python3
"""
B63 Seed: Licences, Sourcing and Subscriptions data.
Seeds:
  - subscription licences (with max_users/max_devices)
  - seat allocations
  - device registrations + device sessions
  - login history + session revocation events
  - subscription plans + entitlements + periods
  - payment orders + status history + invoices + refunds
  - wallet accounts + ledger entries
  - profile download history
  - sourcing requests + consultant decisions + sourcing shortlists
  - outreach batches + outreach batch recipients

Run against the connected postgres with:
  PG_DSN=postgres://talentradb:changeme@localhost:5431/talentra python scripts/seed_b63_licences_sourcing_subs.py

All inserts are idempotent: a second run only adds the deficit.
"""
import os
import sys
import random
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NUM_LICENCES = 20
NUM_SEATS_PER_LICENCE = 10
NUM_DEVICES_PER_USER = 3
NUM_SUBSCRIPTION_PERIODS = 30
NUM_PAYMENT_ORDERS = 50
NUM_WALLETS = 20
NUM_DOWNLOADS = 200
NUM_SOURCING_REQUESTS = 100
NUM_OUTREACH_BATCHES = 20

BATCH = 10_000
SEED = 42

DSN = os.environ.get(
    "PG_DSN",
    "dbname=talentra user=talentradb password=changeme host=localhost port=5431",
)


def _count(cur, table):
    cur.execute(f"SELECT count(*) FROM {table}")
    return cur.fetchone()[0]


def _insert_many(cur, sql, rows, page_size=10_000):
    if not rows:
        return 0
    psycopg2.extras.execute_values(cur, sql, rows, page_size=page_size)
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    random.seed(SEED)
    print("=== B63 Seed: Licences, Sourcing & Subscriptions ===\n")

    conn = psycopg2.connect(DSN)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    try:
        # ------------------------------------------------------------------
        # 1. Licences, seats, devices, sessions
        # ------------------------------------------------------------------
        print("[1/3] Seeding licences, seats, devices, sessions...")
        _seed_subscription_licences(cur)
        conn.commit()
        licence_ids = _get_licence_ids(cur)
        print(f"  subscription_licence: {len(licence_ids):,}")

        user_ids = _get_user_ids(cur)
        print(f"  users available: {len(user_ids):,}")

        _seed_seat_allocations(cur, licence_ids, user_ids[:NUM_SEATS_PER_LICENCE * NUM_LICENCES])
        conn.commit()
        _seed_device_registrations(cur, user_ids[:50])
        conn.commit()
        _seed_device_sessions(cur, user_ids[:50])
        conn.commit()
        _seed_login_history(cur, user_ids[:50])
        conn.commit()
        _seed_session_revocation_events(cur, user_ids[:10])
        conn.commit()

        # ------------------------------------------------------------------
        # 2. Subscriptions, payments, wallet, downloads
        # ------------------------------------------------------------------
        print("[2/3] Seeding subscriptions, payments, wallet, downloads...")
        _seed_subscription_plans(cur)
        conn.commit()
        plan_ids = _get_plan_ids(cur)
        print(f"  subscription_plan: {len(plan_ids):,}")

        _seed_plan_entitlements(cur, plan_ids)
        conn.commit()
        _seed_subscription_periods(cur, licence_ids, plan_ids)
        conn.commit()
        _seed_payment_orders(cur, licence_ids, user_ids[:NUM_PAYMENT_ORDERS])
        conn.commit()
        _seed_payment_status_history(cur)
        conn.commit()
        _seed_invoices(cur)
        conn.commit()
        _seed_refunds(cur)
        conn.commit()
        _seed_wallet_accounts(cur)
        conn.commit()
        _seed_wallet_ledger_entries(cur)
        conn.commit()
        _seed_profile_download_history(cur, user_ids[:NUM_DOWNLOADS], user_ids)
        conn.commit()

        # ------------------------------------------------------------------
        # 3. Sourcing and consultant
        # ------------------------------------------------------------------
        print("[3/3] Seeding sourcing requests, decisions, outreach...")
        _ensure_jobs_for_sourcing(cur)
        conn.commit()
        job_ids = _get_sourcing_job_ids(cur)
        print(f"  sourcing-capable job_requirement: {len(job_ids):,}")

        _seed_sourcing_requests(cur, job_ids, user_ids)
        conn.commit()
        _seed_consultant_decisions(cur)
        conn.commit()
        _seed_sourcing_shortlists(cur)
        conn.commit()
        _seed_outreach_batches(cur, user_ids)
        conn.commit()
        _seed_outreach_batch_recipients(cur)
        conn.commit()

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        print("\n=== FINAL TABLE COUNTS ===")
        for table in [
            "subscription_licence",
            "seat_allocation",
            "device_registration",
            "device_session",
            "login_history",
            "session_revocation_event",
            "subscription_plan",
            "plan_entitlement",
            "subscription_period",
            "payment_order",
            "payment_status_history",
            "invoice",
            "refund",
            "wallet_account",
            "wallet_ledger_entry",
            "profile_download_history",
            "sourcing_request",
            "consultant_decision",
            "sourcing_shortlist",
            "outreach_batch",
            "outreach_batch_recipient",
        ]:
            cur.execute(f"SELECT count(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]:,}")

    except Exception:
        conn.rollback()
        print("B63 SEED FAILED — rolled back", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()
    print("\nB63 seed completed!")


# ===========================================================================
# Licences, seats, devices, sessions
# ===========================================================================

def _seed_subscription_licences(cur):
    cur.execute("SELECT count(*) FROM subscription_licence")
    existing = cur.fetchone()[0]
    if existing >= NUM_LICENCES:
        cur.execute("SELECT id FROM subscription_licence ORDER BY id")
        return [r[0] for r in cur.fetchall()]

    cur.execute("SELECT code FROM reference_code WHERE domain = 'licence_type'")
    licence_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'licence_status'")
    licence_statuses = [r[0] for r in cur.fetchall()]
    if not licence_types or not licence_statuses:
        print("  [SKIP] licence reference codes missing; run B60 first")
        return []

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM tenant_account WHERE account_type_code = 'platform'")
    tenant_rows = cur.fetchall()
    if not tenant_rows:
        print("  [SKIP] no platform tenant_account; run B62 first")
        return []
    tenant_id = tenant_rows[0][0]

    to_insert = []
    for i in range(NUM_LICENCES - existing):
        issued_by = user_ids[i % len(user_ids)] if user_ids else 0
        to_insert.append(
            (
                tenant_id,
                f"LC-{1000 + i}",
                licence_types[i % len(licence_types)],
                licence_statuses[0],
                50,
                5,
                now_str(),
                issued_by,
                now_str(),
                issued_by,
                None,
                None,
                None,
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO subscription_licence(tenant_account_id, licence_number, "
            "licence_type_code, status_code, max_users_allowed, max_devices_per_user, "
            "issued_at, issued_by_user_id, activated_at, activated_by_user_id, "
            "suspended_at, suspended_by_user_id, terminated_at, terminated_by_user_id, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )

    cur.execute("SELECT id FROM subscription_licence ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _get_licence_ids(cur):
    cur.execute("SELECT id FROM subscription_licence ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _seed_seat_allocations(cur, licence_ids, user_ids):
    cur.execute("SELECT count(*) FROM seat_allocation")
    existing = cur.fetchone()[0]
    if existing >= NUM_LICENCES * NUM_SEATS_PER_LICENCE:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'seat_status'")
    seat_statuses = [r[0] for r in cur.fetchall()]
    if not seat_statuses:
        print("  [SKIP] seat_status reference codes missing; run B60 first")
        return

    to_insert = []
    for i in range(min(NUM_LICENCES * NUM_SEATS_PER_LICENCE - existing, len(user_ids))):
        licence_id = licence_ids[i % len(licence_ids)]
        uid = user_ids[i]
        to_insert.append(
            (
                licence_id,
                uid,
                seat_statuses[0],
                now_str(),
                None,
                None,
                None,
                True,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO seat_allocation(subscription_licence_id, user_id, "
            "seat_status_code, allocated_at, allocated_by_user_id, revoked_at, "
            "revoked_by_user_id, is_active, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_device_registrations(cur, user_ids):
    cur.execute("SELECT count(*) FROM device_registration")
    existing = cur.fetchone()[0]
    if existing >= len(user_ids) * NUM_DEVICES_PER_USER:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'device_type'")
    device_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'revocation_reason'")
    revocation_reasons = [r[0] for r in cur.fetchall()]
    if not device_types:
        print("  [SKIP] device_type reference codes missing; run B60 first")
        return

    to_insert = []
    for uid in user_ids:
        for d in range(NUM_DEVICES_PER_USER):
            if _count(cur, "device_registration") >= len(user_ids) * NUM_DEVICES_PER_USER:
                break
            to_insert.append(
                (
                    uid,
                    f"device_{uid}_{d}",
                    f"Device {d} for user {uid}",
                    device_types[d % len(device_types)],
                    now_str(),
                    uid,
                    now_str(),
                    None,
                    None,
                    None,
                    True,
                    now_str(),
                    0,
                    now_str(),
                    0,
                    None,
                )
            )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO device_registration(user_id, device_identifier, device_label, "
            "device_type_code, registered_at, registered_by_user_id, last_seen_at, "
            "revoked_at, revoked_by_user_id, revocation_reason_code, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_device_sessions(cur, user_ids):
    cur.execute("SELECT count(*) FROM device_session")
    existing = cur.fetchone()[0]
    if existing >= len(user_ids) * 2:
        return

    cur.execute("SELECT id FROM device_registration")
    device_ids = [r[0] for r in cur.fetchall()]
    if not device_ids:
        return

    # Compute expires_at = now + 24 hours as a Python datetime
    from datetime import datetime, timedelta
    expires_at = datetime.utcnow() + timedelta(hours=24)

    to_insert = []
    for uid in user_ids[:50]:
        did = device_ids[(uid + 1) % len(device_ids)] if device_ids else 1
        to_insert.append(
            (
                uid,
                did,
                f"device_session_ref_{uid}",
                now_str(),
                now_str(),
                None,
                expires_at,
                False,
                None,
                None,
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO device_session(user_id, device_registration_id, "
            "session_token_ref, started_at, last_activity_at, ended_at, "
            "expires_at, is_revoked, revoked_at, revoked_by_user_id, "
            "revocation_reason_code, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_login_history(cur, user_ids):
    cur.execute("SELECT count(*) FROM login_history")
    existing = cur.fetchone()[0]
    if existing >= len(user_ids) * 3:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'login_result'")
    login_results = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM device_registration")
    device_ids = [r[0] for r in cur.fetchall()]
    if not login_results:
        print("  [SKIP] login_result reference codes missing; run B60 first")
        return

    to_insert = []
    for uid in user_ids[:50]:
        for _ in range(3):
            did = device_ids[(uid + _) % len(device_ids)] if device_ids else None
            to_insert.append(
                (
                    uid,
                    login_results[0],
                    did,
                    "127.0.0.1",
                    "Codebuff seed",
                    now_str(),
                    now_str(),
                    0,
                    now_str(),
                    0,
                    None,
                )
            )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO login_history(user_id, login_result_code, "
            "device_registration_id, ip_address, user_agent, attempted_at, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_session_revocation_events(cur, user_ids):
    cur.execute("SELECT count(*) FROM session_revocation_event")
    existing = cur.fetchone()[0]
    if existing >= 20:
        return

    to_insert = []
    for uid in user_ids[:10]:
        for i in range(2):
            to_insert.append(
                (
                    uid,
                    "session",
                    uid + i,
                    now_str(),
                    None,
                    "127.0.0.1",
                    "Codebuff seed",
                    now_str(),
                    0,
                    now_str(),
                    0,
                    None,
                )
            )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO session_revocation_event(revoked_by_user_id, "
            "revocation_target_type_code, revocation_target_id, revoked_at, "
            "revocation_reason_code, ip_address, user_agent, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ===========================================================================
# Subscriptions, payments, wallet, downloads
# ===========================================================================

def _seed_subscription_plans(cur):
    cur.execute("SELECT count(*) FROM subscription_plan")
    existing = cur.fetchone()[0]
    if existing >= 3:
        cur.execute("SELECT id FROM subscription_plan ORDER BY id")
        return [r[0] for r in cur.fetchall()]

    cur.execute("SELECT code FROM reference_code WHERE domain = 'plan_category'")
    categories = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'billing_period'")
    billing_periods = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'renewal_type'")
    renewals = [r[0] for r in cur.fetchall()]
    if not categories or not billing_periods:
        print("  [SKIP] plan reference codes missing; run B60 first")
        return []

    plans = [
        ("free", "Free Plan", "Free tier with limited features", "free", "monthly", 0.00, "USD", "auto", 0),
        ("basic", "Basic Plan", "Basic paid plan", "paid", "monthly", 29.99, "USD", "auto", 0),
        ("pro", "Pro Plan", "Professional plan", "paid", "monthly", 99.99, "USD", "auto", 14),
    ]
    to_insert = []
    for code, name, desc, cat, bp, price, currency, renewal, trial in plans:
        to_insert.append(
            (
                code,
                name,
                desc,
                cat,
                bp,
                price,
                currency,
                renewals[0] if renewals else None,
                trial,
                True,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO subscription_plan(plan_code, name, description, category_code, "
            "billing_period_code, price_amount, price_currency_code, renewal_type_code, "
            "trial_days, is_active, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )

    cur.execute("SELECT id FROM subscription_plan ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _get_plan_ids(cur):
    cur.execute("SELECT id FROM subscription_plan ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _seed_plan_entitlements(cur, plan_ids):
    cur.execute("SELECT count(*) FROM plan_entitlement")
    existing = cur.fetchone()[0]
    if existing >= 9:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'entitlement_code'")
    entitlement_codes = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'entitlement_unit'")
    entitlement_units = [r[0] for r in cur.fetchall()]
    if not entitlement_codes:
        print("  [SKIP] entitlement_code reference codes missing; run B60 first")
        return

    to_insert = []
    for pid in plan_ids:
        for ec in entitlement_codes[:3]:
            to_insert.append(
                (
                    pid,
                    ec,
                    50.0,
                    entitlement_units[0] if entitlement_units else None,
                    True,
                    now_str(),
                    0,
                    now_str(),
                    0,
                    None,
                )
            )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO plan_entitlement(subscription_plan_id, entitlement_code, "
            "entitlement_value, value_unit_code, is_active, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_subscription_periods(cur, licence_ids, plan_ids):
    cur.execute("SELECT count(*) FROM subscription_period")
    existing = cur.fetchone()[0]
    if existing >= NUM_SUBSCRIPTION_PERIODS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'subscription_status'")
    statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'renewal_type'")
    renewals = [r[0] for r in cur.fetchall()]
    if not statuses:
        print("  [SKIP] subscription_status reference codes missing; run B60 first")
        return

    to_insert = []
    for i in range(NUM_SUBSCRIPTION_PERIODS - existing):
        licence_id = licence_ids[i % len(licence_ids)] if licence_ids else 1
        plan_id = plan_ids[i % len(plan_ids)] if plan_ids else 1
        start = datetime.now() - timedelta(days=random.randint(30, 365))
        to_insert.append(
            (
                licence_id,
                plan_id,
                statuses[0],
                start,
                start + timedelta(days=30),
                renewals[0] if renewals else None,
                None,
                None,
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO subscription_period(subscription_licence_id, "
            "subscription_plan_id, status_code, started_at, ended_at, "
            "renew_type_code, cancelled_at, cancelled_by_user_id, "
            "cancellation_reason, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_payment_orders(cur, licence_ids, user_ids):
    cur.execute("SELECT count(*) FROM payment_order")
    existing = cur.fetchone()[0]
    if existing >= NUM_PAYMENT_ORDERS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'payment_method'")
    payment_methods = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'payment_status'")
    payment_statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM tenant_account WHERE account_type_code = 'platform'")
    tenant_rows = cur.fetchall()
    if not payment_methods or not payment_statuses or not tenant_rows:
        print("  [SKIP] payment reference codes missing; run B60 first")
        return

    tenant_id = tenant_rows[0][0]
    to_insert = []
    for i in range(NUM_PAYMENT_ORDERS - existing):
        uid = user_ids[i % len(user_ids)] if user_ids else 1
        to_insert.append(
            (
                f"PO-{10000 + i}",
                tenant_id,
                licence_ids[i % len(licence_ids)] if licence_ids else None,
                None,
                uid,
                payment_methods[0] if payment_methods else "card",
                payment_statuses[0] if payment_statuses else "completed",
                29.99,
                "USD",
                f"gateway_ref_{i}",
                None,
                now_str(),
                uid,
                now_str(),
                uid,
                None,
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO payment_order(order_number, tenant_account_id, "
            "subscription_licence_id, subscription_period_id, payer_user_id, "
            "payment_method_code, status_code, amount, currency_code, "
            "gateway_reference, gateway_response, initiated_at, initiated_by_user_id, "
            "completed_at, completed_by_user_id, failed_at, failure_reason, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_payment_status_history(cur):
    cur.execute("SELECT count(*) FROM payment_status_history")
    existing = cur.fetchone()[0]
    if existing >= 50:
        return

    cur.execute("SELECT id FROM payment_order")
    order_ids = [r[0] for r in cur.fetchall()]
    if not order_ids:
        return

    to_insert = []
    for oid in order_ids[:50]:
        to_insert.append(
            (
                oid,
                "completed",
                now_str(),
                None,
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO payment_status_history(payment_order_id, status_code, "
            "changed_at, changed_by_user_id, gateway_status, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_invoices(cur):
    cur.execute("SELECT count(*) FROM invoice")
    existing = cur.fetchone()[0]
    if existing >= 30:
        return

    cur.execute("SELECT id FROM payment_order")
    order_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM tenant_account WHERE account_type_code = 'platform'")
    tenant_rows = cur.fetchall()
    if not order_ids or not tenant_rows:
        return

    tenant_id = tenant_rows[0][0]
    to_insert = []
    for i, oid in enumerate(order_ids[:30]):
        issue_date = (datetime.now() - timedelta(days=i)).date()
        due_date = issue_date + timedelta(days=30)
        to_insert.append(
            (
                f"INV-{10000 + i}",
                oid,
                tenant_id,
                issue_date,
                due_date,
                "USD",
                "Subscription payment",
                29.99,
                "issued",
                1,
                now_str(),
                None,
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO invoice(invoice_number, payment_order_id, tenant_account_id, "
            "issue_date, due_date, currency_code, line_items, total_amount, "
            "status_code, issued_by_user_id, issued_at, paid_at, paid_by_user_id, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_refunds(cur):
    cur.execute("SELECT count(*) FROM refund")
    existing = cur.fetchone()[0]
    if existing >= 10:
        return

    cur.execute("SELECT id FROM payment_order")
    order_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM invoice")
    invoice_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'refund_status'")
    statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'refund_type'")
    types = [r[0] for r in cur.fetchall()]
    if not order_ids or not statuses:
        print("  [SKIP] refund reference codes missing; run B60 first")
        return

    to_insert = []
    for i, oid in enumerate(order_ids[:10]):
        iid = invoice_ids[i] if i < len(invoice_ids) else None
        to_insert.append(
            (
                f"RF-{10000 + i}",
                oid,
                iid,
                29.99,
                "USD",
                statuses[0] if statuses else "requested",
                types[0] if types else None,
                1,
                None,
                now_str(),
                None,
                None,
                None,
                "Seeded refund",
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO refund(refund_number, payment_order_id, invoice_id, "
            "refund_amount, currency_code, refund_status_code, refund_type_code, "
            "requested_by_user_id, processed_by_user_id, requested_at, processed_at, "
            "gateway_reference, gateway_response, reason, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_wallet_accounts(cur):
    cur.execute("SELECT count(*) FROM wallet_account")
    existing = cur.fetchone()[0]
    if existing >= NUM_WALLETS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'wallet_status'")
    statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM tenant_account WHERE account_type_code = 'platform'")
    tenant_rows = cur.fetchall()
    if not statuses or not tenant_rows:
        print("  [SKIP] wallet reference codes missing; run B60 first")
        return

    tenant_id = tenant_rows[0][0]
    to_insert = []
    for i in range(NUM_WALLETS - existing):
        to_insert.append(
            (
                tenant_id,
                (i % 20) + 1,
                "USD",
                100.0 + i * 10,
                statuses[0] if statuses else "active",
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO wallet_account(tenant_account_id, owner_user_id, currency_code, "
            "balance, status_code, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_wallet_ledger_entries(cur):
    cur.execute("SELECT count(*) FROM wallet_ledger_entry")
    existing = cur.fetchone()[0]
    if existing >= 50:
        return

    cur.execute("SELECT id FROM wallet_account")
    wallet_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'wallet_transaction_type'")
    tx_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'wallet_reference_type'")
    ref_types = [r[0] for r in cur.fetchall()]
    if not wallet_ids or not tx_types:
        print("  [SKIP] wallet reference codes missing; run B60 first")
        return

    to_insert = []
    for i in range(min(50 - existing, len(wallet_ids))):
        wid = wallet_ids[i]
        to_insert.append(
            (
                wid,
                tx_types[0] if tx_types else "recharge",
                100.0,
                "USD",
                100.0,
                ref_types[0] if ref_types else None,
                1,
                None,
                "Seeded ledger entry",
                1,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO wallet_ledger_entry(wallet_account_id, transaction_type_code, "
            "amount, currency_code, balance_after, reference_type_code, reference_id, "
            "correction_reference_id, description, created_by_user_id, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_profile_download_history(cur, downloader_ids, user_ids):
    cur.execute("SELECT count(*) FROM profile_download_history")
    existing = cur.fetchone()[0]
    if existing >= NUM_DOWNLOADS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'download_format'")
    formats = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM candidate_identity")
    candidate_ids = [r[0] for r in cur.fetchall()]
    if not formats or not candidate_ids:
        print("  [SKIP] download reference codes missing; run B60 first")
        return

    to_insert = []
    for i in range(NUM_DOWNLOADS - existing):
        downloader_id = downloader_ids[i % len(downloader_ids)]
        cid = candidate_ids[i % len(candidate_ids)]
        to_insert.append(
            (
                downloader_id,
                cid,
                now_str(),
                formats[0] if formats else "pdf",
                1.0,
                "USD",
                True,
                f"download_ref_{i}",
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO profile_download_history(downloader_user_id, "
            "candidate_identity_id, downloaded_at, download_format_code, "
            "credit_deducted_amount, credit_currency_code, "
            "credit_deduction_applied, download_reference, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ===========================================================================
# Sourcing and consultant
# ===========================================================================

def _ensure_jobs_for_sourcing(cur):
    """Ensure we have job_requirements that are open to consultants for sourcing."""
    cur.execute(
        "SELECT count(*) FROM job_requirement WHERE is_open_to_consultants = true"
    )
    existing = cur.fetchone()[0]
    if existing >= NUM_SOURCING_REQUESTS:
        print(f"  job_requirement (consultant-open): {existing:,} (target met)")
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'job_status'")
    job_statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'job_visibility'")
    job_visibilities = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM employment_type ORDER BY id")
    employment_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM work_type ORDER BY id")
    work_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM industry")
    industries = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM job_role")
    job_roles = [r[0] for r in cur.fetchall()]
    if not all([job_statuses, job_visibilities, employment_types, work_types]):
        print("  [SKIP] job reference data missing; run B61 first")
        return

    from faker import Faker

    Faker.seed(SEED + 5)
    f = Faker()

    cur.execute("SELECT id FROM employer_organisation WHERE is_verified = true")
    employer_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cur.fetchall()]
    if not employer_ids or not user_ids:
        print("  [SKIP] no employers or users; run B61/B62 first")
        return

    to_insert = []
    remaining = NUM_SOURCING_REQUESTS - existing
    for i in range(remaining):
        eid = employer_ids[i % len(employer_ids)]
        uid = user_ids[i % len(user_ids)]
        to_insert.append(
            (
                eid,
                uid,
                f.job()[:200],
                f.text(max_nb_chars=400)[:2000],
                "en",
                employment_types[i % len(employment_types)],
                work_types[i % len(work_types)],
                random.choice(industries),
                random.choice(job_roles),
                "Sourcing Location",
                "State",
                "IN",
                None,
                None,
                None,
                None,
                None,
                random.choice([True, False]),
                True,
                job_statuses[0] if job_statuses else "published",
                job_visibilities[0] if job_visibilities else "public",
                job_statuses[0] if job_statuses else "published",
                None,
                now_str(),
                None,
                None,
            )
        )
        if len(to_insert) >= 5000:
            psycopg2.extras.execute_values(
                cur,
                (
                    "INSERT INTO job_requirement "
                    "(employer_organisation_id, recruiter_user_id, title, description, "
                    "description_language, employment_type_code, work_type_code, "
                    "industry_name, job_role_name, location_city, location_state, "
                    "location_country, compensation_min, compensation_max, "
                    "compensation_currency_code, experience_min_years, "
                    "experience_max_years, is_remote_allowed, is_open_to_consultants, "
                    "status_code, visibility_code, publish_state_code, deadline_at, "
                    "published_at, unpublished_at, closed_at) "
                    "VALUES %s ON CONFLICT DO NOTHING RETURNING id"
                ),
                to_insert,
                page_size=5000,
            )
            to_insert = []
    if to_insert:
        psycopg2.extras.execute_values(
            cur,
            (
                "INSERT INTO job_requirement "
                "(employer_organisation_id, recruiter_user_id, title, description, "
                "description_language, employment_type_code, work_type_code, "
                "industry_name, job_role_name, location_city, location_state, "
                "location_country, compensation_min, compensation_max, "
                "compensation_currency_code, experience_min_years, "
                "experience_max_years, is_remote_allowed, is_open_to_consultants, "
                "status_code, visibility_code, publish_state_code, deadline_at, "
                "published_at, unpublished_at, closed_at) "
                "VALUES %s ON CONFLICT DO NOTHING RETURNING id"
            ),
            to_insert,
            page_size=len(to_insert),
        )


def _get_sourcing_job_ids(cur):
    cur.execute(
        "SELECT id FROM job_requirement WHERE is_open_to_consultants = true ORDER BY id"
    )
    return [r[0] for r in cur.fetchall()]


def _seed_sourcing_requests(cur, job_ids, user_ids):
    cur.execute("SELECT count(*) FROM sourcing_request")
    existing = cur.fetchone()[0]
    if existing >= NUM_SOURCING_REQUESTS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'sourcing_status'")
    statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'consultant_decision_type'")
    decision_types = [r[0] for r in cur.fetchall()]
    if not statuses:
        print("  [SKIP] sourcing reference codes missing; run B60 first")
        return

    to_insert = []
    for i in range(NUM_SOURCING_REQUESTS - existing):
        jid = job_ids[i % len(job_ids)] if job_ids else 1
        requester = user_ids[i % len(user_ids)] if user_ids else 1
        consultant = user_ids[(i + 10) % len(user_ids)] if user_ids else None
        to_insert.append(
            (
                jid,
                requester,
                consultant,
                "direct",
                "Sourcing request description",
                True,
                statuses[0] if statuses else "open",
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO sourcing_request(job_requirement_id, requester_user_id, "
            "consultant_user_id, request_type_code, description, "
            "is_open_to_consultants, status_code, shortlist_id, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_consultant_decisions(cur):
    cur.execute("SELECT count(*) FROM consultant_decision")
    existing = cur.fetchone()[0]
    if existing >= 50:
        return

    cur.execute("SELECT id FROM sourcing_request")
    request_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'consultant_decision_type'")
    decision_types = [r[0] for r in cur.fetchall()]
    if not request_ids or not decision_types:
        print("  [SKIP] consultant reference codes missing; run B60 first")
        return

    to_insert = []
    for i, rid in enumerate(request_ids[:50]):
        consultant_id = (i + 10) % 50 + 1
        to_insert.append(
            (
                rid,
                consultant_id,
                decision_types[0] if decision_types else "accepted",
                "Consultant accepted the sourcing request",
                now_str(),
                consultant_id,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO consultant_decision(sourcing_request_id, consultant_user_id, "
            "decision_code, decision_note, decided_at, decided_by_user_id, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_sourcing_shortlists(cur):
    cur.execute("SELECT count(*) FROM sourcing_shortlist")
    existing = cur.fetchone()[0]
    if existing >= 30:
        return

    cur.execute("SELECT id FROM sourcing_request")
    request_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM candidate_shortlist_entry")
    shortlist_ids = [r[0] for r in cur.fetchall()]
    if not request_ids or not shortlist_ids:
        print("  [SKIP] shortlist entries missing; run B61 first")
        return

    to_insert = []
    for i, rid in enumerate(request_ids[:30]):
        sid = shortlist_ids[i % len(shortlist_ids)]
        to_insert.append(
            (
                rid,
                sid,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO sourcing_shortlist(sourcing_request_id, shortlist_id, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_outreach_batches(cur, user_ids):
    cur.execute("SELECT count(*) FROM outreach_batch")
    existing = cur.fetchone()[0]
    if existing >= NUM_OUTREACH_BATCHES:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'outreach_channel'")
    channels = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'delivery_status'")
    statuses = [r[0] for r in cur.fetchall()]
    if not channels or not statuses:
        print("  [SKIP] outreach reference codes missing; run B60 first")
        return

    to_insert = []
    for i in range(NUM_OUTREACH_BATCHES - existing):
        creator = user_ids[i % len(user_ids)] if user_ids else 1
        to_insert.append(
            (
                creator,
                "email",
                f"Outreach Batch {i + 1}",
                "Bulk outreach batch",
                channels[0] if channels else "email",
                statuses[0] if statuses else "sent",
                None,
                now_str(),
                now_str(),
                100,
                100,
                0,
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO outreach_batch(creator_user_id, batch_type_code, name, "
            "description, channel_code, status_code, scheduled_at, started_at, "
            "completed_at, total_recipients, delivered_recipients, failed_recipients, "
            "credit_consumption_ref, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_outreach_batch_recipients(cur):
    cur.execute("SELECT count(*) FROM outreach_batch_recipient")
    existing = cur.fetchone()[0]
    if existing >= 200:
        return

    cur.execute("SELECT id FROM outreach_batch")
    batch_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM candidate_identity")
    candidate_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'outreach_channel'")
    channels = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'delivery_status'")
    statuses = [r[0] for r in cur.fetchall()]
    if not batch_ids or not channels or not statuses:
        print("  [SKIP] outreach recipient reference codes missing; run B60 first")
        return

    to_insert = []
    for i in range(min(200 - existing, len(batch_ids) * 10)):
        bid = batch_ids[i % len(batch_ids)]
        cid = candidate_ids[i % len(candidate_ids)] if candidate_ids else None
        to_insert.append(
            (
                bid,
                cid,
                None,
                channels[0] if channels else "email",
                statuses[0] if statuses else "sent",
                now_str(),
                f"delivery_ref_{i}",
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO outreach_batch_recipient(outreach_batch_id, "
            "candidate_identity_id, recipient_user_id, contact_channel_code, "
            "delivery_status_code, delivered_at, delivery_reference, delivery_error, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_ids(cur):
    cur.execute("SELECT id FROM users ORDER BY id")
    return [r[0] for r in cur.fetchall()]


from datetime import datetime, timedelta

def now_str():
    return datetime.utcnow()


if __name__ == "__main__":
    main()
