#!/usr/bin/env python3
"""
B62 Seed: Administration, Organisation and Gig Marketplace data.
Seeds:
  - roles, permissions, permission assignments
  - role assignments for seeded users
  - tenant accounts, employer organisations, company locations
  - tax registration identifiers, verification status records
  - recruiter mappings (effective-dated), account administrators
  - organisation hierarchy
  - credential verification + recovery records for seeded users
  - sessions, consent records, audit events, blocking list entries
  - gig requests (job_requirement + gig_request_detail), gig worker profiles
  - gig worker availability, gig applications, gig assignments, handoff references
  - gig earnings references, gig favourites/blacklists, gig ratings

Run against the connected postgres with:
  PG_DSN=postgres://talentradb:changeme@localhost:5431/talentra python scripts/seed_b62_admin_org_gig.py

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
NUM_EMPLOYERS = 200
NUM_RECRUITERS = 50
NUM_GIG_REQUESTS = 500
NUM_GIG_WORKERS = 300
NUM_GIG_APPLICATIONS = 2000

BATCH = 10_000
SEED = 42

DSN = os.environ.get(
    "PG_DSN",
    "dbname=talentra user=talentradb password=changeme host=localhost port=5431",
)


def now_str():
    return "now()"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    print("=== B62 Seed: Administration, Organisation & Gig Marketplace ===\n")

    conn = psycopg2.connect(DSN)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    try:
        # ------------------------------------------------------------------
        # 1. Roles / permissions / assignments
        # ------------------------------------------------------------------
        print("[1/6] Seeding roles, permissions, assignments...")
        _seed_roles(cur)
        conn.commit()
        _seed_permissions(cur)
        conn.commit()
        _seed_permission_assignments(cur)
        conn.commit()

        # Ensure we have users to assign roles to
        _ensure_users(cur)
        conn.commit()
        user_ids = _get_user_ids(cur)
        print(f"  users available: {len(user_ids):,}")

        _seed_role_assignments(cur, user_ids)
        conn.commit()

        # ------------------------------------------------------------------
        # 2. Administration: credentials, sessions, consent, audit, blocking
        # ------------------------------------------------------------------
        print("[2/6] Seeding credentials, sessions, consent, audit, blocking...")
        _seed_credentials(cur, user_ids)
        conn.commit()
        _seed_sessions(cur, user_ids)
        conn.commit()
        _seed_consent_records(cur, user_ids)
        conn.commit()
        _seed_audit_events(cur, user_ids)
        conn.commit()
        _seed_blocking_list(cur, user_ids)
        conn.commit()

        # ------------------------------------------------------------------
        # 3. Organisation: tenant accounts, employers, locations, mappings
        # ------------------------------------------------------------------
        print("[3/6] Seeding organisation data...")
        _ensure_tenant(cur)
        conn.commit()
        tenant_id = _get_platform_tenant_id(cur)
        print(f"  tenant_account id: {tenant_id}")

        _seed_employer_organisations(cur, tenant_id, NUM_EMPLOYERS)
        conn.commit()
        employer_ids = _get_verified_employer_ids(cur)
        print(f"  employer_organisation (verified): {len(employer_ids):,}")

        _seed_company_locations(cur, employer_ids)
        conn.commit()
        _seed_tax_registration_identifiers(cur, employer_ids)
        conn.commit()
        _seed_verification_status_records(cur, employer_ids)
        conn.commit()

        recruiter_ids = user_ids[:NUM_RECRUITERS]
        _seed_recruiter_mappings(cur, employer_ids, recruiter_ids)
        conn.commit()
        _seed_account_administrators(cur, tenant_id, user_ids)
        conn.commit()
        _seed_organisation_hierarchy(cur, employer_ids)
        conn.commit()

        # ------------------------------------------------------------------
        # 4. Gig marketplace: requests, workers, applications, assignments
        # ------------------------------------------------------------------
        print("[4/6] Seeding gig marketplace data...")
        _ensure_jobs_for_gigs(cur, employer_ids, user_ids)
        conn.commit()
        job_ids = _get_gig_job_ids(cur)
        print(f"  gig-capable job_requirement: {len(job_ids):,}")

        gig_worker_ids = _seed_gig_worker_profiles(cur, user_ids)
        conn.commit()
        if gig_worker_ids is None:
            print("  [WARN] gig_worker_profile seeding returned None; continuing without gigs")
            gig_worker_ids = []
        else:
            print(f"  gig_worker_profile: {len(gig_worker_ids):,}")
        _seed_gig_worker_availability(cur, gig_worker_ids)
        conn.commit()

        gig_request_detail_ids = _seed_gig_request_details(cur, job_ids)
        conn.commit()
        if gig_request_detail_ids is None:
            print("  [WARN] gig_request_detail seeding returned None; continuing without gig requests")
            gig_request_detail_ids = []
        else:
            print(f"  gig_request_detail: {len(gig_request_detail_ids):,}")

        applicant_ids = user_ids[NUM_RECRUITERS : NUM_RECRUITERS + 200]
        app_ids = _seed_gig_applications(cur, gig_request_detail_ids, gig_worker_ids, applicant_ids)
        conn.commit()
        if app_ids is None:
            print("  [WARN] gig_application seeding returned None; continuing without gig applications")
            app_ids = []
        else:
            print(f"  gig_application: {len(app_ids):,}")

        _seed_gig_assignments(cur, app_ids, user_ids)
        conn.commit()
        _seed_gig_handoff_references(cur)
        conn.commit()
        _seed_gig_earnings_references(cur)
        conn.commit()
        _seed_gig_favourites_blacklists(cur, user_ids, gig_worker_ids)
        conn.commit()
        _seed_gig_ratings(cur)
        conn.commit()

        # ------------------------------------------------------------------
        # 5. Summary
        # ------------------------------------------------------------------
        print("\n=== FINAL TABLE COUNTS ===")
        for table in [
            "role_lookup",
            "permission",
            "permission_assignment",
            "role_assignment",
            "credential_verification",
            "credential_recovery",
            "session_record",
            "consent_record",
            "audit_event",
            "blocking_list",
            "tenant_account",
            "employer_organisation",
            "company_location",
            "tax_registration_identifier",
            "verification_status_record",
            "recruiter_mapping",
            "account_administrator",
            "organisation_hierarchy",
            "gig_request_detail",
            "gig_worker_profile",
            "gig_worker_availability",
            "gig_application",
            "gig_assignment",
            "gig_handoff_reference",
            "gig_earnings_reference",
            "gig_favourite",
            "gig_blacklist",
            "gig_rating",
        ]:
            cur.execute(f"SELECT count(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]:,}")

    except Exception:
        conn.rollback()
        print("B62 SEED FAILED — rolled back", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()
    print("\nB62 seed completed!")


# ===========================================================================
# Roles / permissions
# ===========================================================================

def _seed_roles(cur):
    rows = [
        ("super_admin", "Super Admin", "Platform super administrator", True),
        ("admin", "Admin", "Platform administrator", True),
        ("account_admin", "Account Admin", "Account-level administrator", True),
        ("candidate", "Candidate", "Candidate actor", True),
        ("employer", "Employer", "Employer actor", True),
        ("recruiter", "Recruiter", "Recruiter actor", True),
        ("consultant", "Consultant", "Consultant actor", True),
    ]
    existing = set()
    cur.execute("SELECT code FROM role_lookup")
    for r in cur.fetchall():
        existing.add(r[0])
    to_insert = [(code, name, desc, True, now_str(), 0, now_str(), 0, None)
                 for code, name, desc, _ in rows if code not in existing]
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO role_lookup(code, name, description, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_permissions(cur):
    rows = [
        ("manage_users", "Manage users", "users", True),
        ("manage_jobs", "Manage jobs", "jobs", True),
        ("view_candidates", "View candidates", "candidates", True),
        ("post_jobs", "Post jobs", "jobs", True),
        ("manage_organisations", "Manage organisations", "organisations", True),
        ("manage_gigs", "Manage gigs", "gigs", True),
        ("view_analytics", "View analytics", "analytics", True),
        ("manage_billing", "Manage billing", "billing", True),
    ]
    existing = set()
    cur.execute("SELECT code FROM permission")
    for r in cur.fetchall():
        existing.add(r[0])
    to_insert = [(code, name, scope, True, now_str(), 0, now_str(), 0, None)
                 for code, name, scope, _ in rows if code not in existing]
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO permission(code, name, resource_scope, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_permission_assignments(cur):
    cur.execute("SELECT id, code FROM role_lookup")
    role_by_code = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT id, code FROM permission")
    perm_by_code = {r[0]: r[1] for r in cur.fetchall()}

    mappings = [
        ("super_admin", "manage_users"),
        ("super_admin", "manage_jobs"),
        ("super_admin", "view_candidates"),
        ("super_admin", "post_jobs"),
        ("super_admin", "manage_organisations"),
        ("super_admin", "manage_gigs"),
        ("super_admin", "view_analytics"),
        ("super_admin", "manage_billing"),
        ("admin", "manage_users"),
        ("admin", "manage_jobs"),
        ("admin", "view_candidates"),
        ("admin", "post_jobs"),
        ("admin", "manage_organisations"),
        ("admin", "manage_gigs"),
        ("admin", "view_analytics"),
        ("account_admin", "manage_organisations"),
        ("employer", "post_jobs"),
        ("employer", "view_candidates"),
        ("recruiter", "post_jobs"),
        ("recruiter", "view_candidates"),
        ("consultant", "view_candidates"),
        ("candidate", "view_candidates"),
    ]
    existing = set()
    cur.execute("SELECT role_id, permission_id FROM permission_assignment")
    for r in cur.fetchall():
        existing.add((r[0], r[1]))
    to_insert = []
    for role_code, perm_code in mappings:
        rid = next((rid for rid, c in role_by_code.items() if c == role_code), None)
        pid = next((pid for pid, c in perm_by_code.items() if c == perm_code), None)
        if rid and pid and (rid, pid) not in existing:
            to_insert.append(
                (rid, pid, now_str(), None, True, now_str(), 0, now_str(), 0, None)
            )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO permission_assignment(role_id, permission_id, granted_at, "
            "granted_by_user_id, is_active, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _ensure_users(cur):
    cur.execute("SELECT count(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (actor_type_code, email, is_active, created_by, updated_by) "
            "SELECT 'candidate', 'candidate_' || n || '@example.com', true, 0, 0 "
            "FROM generate_series(1, 500) AS n "
            "ON CONFLICT DO NOTHING"
        )
        cur.connection.commit()
        print("  users: created 500 candidates")
    else:
        print(f"  users: {_count(cur, 'users'):,} existing")


def _get_user_ids(cur):
    cur.execute("SELECT id FROM users ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _seed_role_assignments(cur, user_ids):
    cur.execute("SELECT id, code FROM role_lookup")
    roles = {r[1]: r[0] for r in cur.fetchall()}
    existing = set()
    cur.execute("SELECT user_id, role_id FROM role_assignment WHERE is_active = true")
    for r in cur.fetchall():
        existing.add((r[0], r[1]))

    # Assign roles based on actor type implied by ordering:
    # first 50 recruiters, next 200 employers, rest candidates
    to_insert = []
    for uid in user_ids:
        if uid <= 50:
            role_code = "recruiter"
        elif uid <= 250:
            role_code = "employer"
        else:
            role_code = "candidate"
        rid = roles.get(role_code)
        if rid and (uid, rid) not in existing:
            to_insert.append(
                (uid, rid, now_str(), None, True, now_str(), 0, now_str(), 0, None)
            )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO role_assignment(user_id, role_id, assigned_at, "
            "assigned_by_user_id, is_active, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )# ===========================================================================
# Administration: credentials, sessions, consent, audit, blocking
# ===========================================================================


def _seed_credentials(cur, user_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'credential_type'")
    cred_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'credential_status'")
    cred_statuses = [r[0] for r in cur.fetchall()]
    if not cred_types or not cred_statuses:
        print("  [SKIP] credential reference codes missing; run B60 first")
        return

    # Prefer the value the B60 seed uses ('active'); fall back to the first value
    # the DB actually has if 'active' is absent.
    cred_status = next((s for s in cred_statuses if s == 'active'), cred_statuses[0])

    existing = set()
    cur.execute("SELECT user_id, credential_type_code FROM credential_verification WHERE deleted_at IS NULL")
    for r in cur.fetchall():
        existing.add((r[0], r[1]))

    # credential_verification column order (no is_active):
    # user_id, credential_type_code, credential_status_code, verified_at,
    # last_used_at, last_used_ip, last_used_user_agent, failure_count,
    # locked_until, recovery_token_ref, recovery_anchor_hash,
    # created_at, created_by, updated_at, updated_by, deleted_at
    to_insert = []
    for uid in user_ids[:200]:
        if (uid, cred_types[0]) not in existing:
            to_insert.append(
                (
                    uid,
                    cred_types[0],
                    cred_status,
                    now_str(),
                    now_str(),
                    None,
                    None,
                    0,
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
            "INSERT INTO credential_verification(user_id, credential_type_code, "
            "credential_status_code, verified_at, last_used_at, last_used_ip, "
            "last_used_user_agent, failure_count, locked_until, recovery_token_ref, "
            "recovery_anchor_hash, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )

    # Recovery records (sparse). credential_recovery has no is_active column.
    # Only insert when a recovery_type_code exists in reference_code; otherwise skip.
    cur.execute("SELECT code FROM reference_code WHERE domain = 'recovery_type'")
    recovery_codes = [r[0] for r in cur.fetchall()]
    if not recovery_codes:
        print("  [SKIP] recovery_type reference codes missing; run B60 first")
        return

    recovery_type_code = recovery_codes[0]
    recovery_rows = []
    now_dt = datetime.now()
    for uid in user_ids[:20]:
        recovery_rows.append(
            (
                uid,
                recovery_type_code,
                None,
                now_dt,
                None,
                None,
                None,
                None,
                "completed",
                now_dt,
                0,
                now_dt,
                0,
                None,
            )
        )
    _insert_many(
        cur,
        "INSERT INTO credential_recovery(user_id, recovery_type_code, token_ref, "
        "requested_at, used_at, used_by_user_id, ip_address, user_agent, "
        "status_code, created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        recovery_rows,
    )


def _seed_sessions(cur, user_ids):
    now = datetime.now()
    expires = now + timedelta(days=7)
    to_insert = []
    for uid in user_ids[:100]:
        to_insert.append(
            (
                uid,
                f"session_ref_{uid}_1",
                f"device_{uid % 10}",
                "127.0.0.1",
                "Codebuff seed",
                now,
                now,
                None,
                expires,
                False,
                None,
                None,
                now,
                0,
                now,
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO session_record(user_id, session_token_ref, device_ref, "
            "ip_address, user_agent, started_at, last_activity_at, ended_at, "
            "expires_at, is_revoked, revoked_at, revoked_by_user_id, created_at, "
            "created_by, updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT "
            "DO NOTHING",
            to_insert,
        )


def _seed_consent_records(cur, user_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'consent_type'")
    consent_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'consent_value'")
    consent_values = [r[0] for r in cur.fetchall()]

    if not consent_types:
        print("  [SKIP] consent_type reference codes missing; run B60 first")
        return

    if not consent_values:
        print("  [SKIP] consent_value reference codes missing; run B60 first")
        return

    to_insert = []
    # consent_record column order:
    # user_id, consent_type_code, consent_value_code, recorded_at,
    # recorded_by_user_id, ip_address, created_at, created_by, updated_at,
    # updated_by, deleted_at
    consent_now = datetime.now()
    for ctype in consent_types[:2]:
        consent_val = consent_values[0]
        for uid in user_ids[:100]:
            to_insert.append(
                (
                    uid,
                    ctype,
                    consent_val,
                    consent_now,
                    None,
                    None,
                    consent_now,
                    0,
                    consent_now,
                    0,
                    None,
                )
            )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO consent_record(user_id, consent_type_code, consent_value_code, "
            "recorded_at, recorded_by_user_id, ip_address, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_audit_events(cur, user_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'event_type'")
    event_types = [r[0] for r in cur.fetchall()]

    if not event_types:
        print("  [SKIP] event_type reference codes missing; run B60 first")
        return

    event_type = next((c for c in event_types if c == 'login'), event_types[0])
    audit_now = datetime.now()
    to_insert = []
    for uid in user_ids[:50]:
        to_insert.append(
            (
                uid,
                event_type,
                "users",
                uid,
                audit_now,
                "127.0.0.1",
                "Codebuff seed",
                "Seeded audit event",
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO audit_event(actor_user_id, event_type_code, target_table, "
            "target_id, occurred_at, source_ip, source_user_agent, detail) "
            "VALUES %s",
            to_insert,
        )


def _seed_blocking_list(cur, user_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'blocked_party_type'")
    party_types = [r[0] for r in cur.fetchall()]

    if not party_types:
        print("  [SKIP] blocked_party_type reference codes missing; run B60 first")
        return

    blocking_now = datetime.now()
    to_insert = []
    for i, uid in enumerate(user_ids[:50]):
        blocked_id = user_ids[(i + 51) % len(user_ids)]
        to_insert.append(
            (
                uid,
                party_types[0],
                blocked_id,
                blocking_now,
                uid,
                "Seeded blocking entry",
                True,
                blocking_now,
                0,
                blocking_now,
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO blocking_list(blocker_user_id, blocked_party_type_code, "
            "blocked_party_id, blocked_at, blocked_by_user_id, reason, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ===========================================================================
# Organisation
# ===========================================================================

def _ensure_tenant(cur):
    cur.execute("SELECT count(*) FROM tenant_account")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO tenant_account "
            "(account_type_code, name, status_code, is_active, created_by, updated_by) "
            "VALUES ('platform', 'Talentra Platform', 'active', true, 0, 0) "
            "ON CONFLICT DO NOTHING"
        )
        cur.connection.commit()
        print("  tenant_account: created")
    else:
        print("  tenant_account: exists")


def _get_platform_tenant_id(cur):
    cur.execute(
        "SELECT id FROM tenant_account WHERE account_type_code = 'platform' LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        raise SystemExit("No platform tenant_account found")
    return row[0]


def _seed_employer_organisations(cur, tenant_id, n):
    cur.execute("SELECT count(*) FROM employer_organisation WHERE is_verified = true")
    existing = cur.fetchone()[0]
    if existing >= n:
        print(f"  employer_organisation: {existing:,} verified (target met)")
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'employer_type'")
    employer_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'verification_status'")
    verification_statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'account_status'")
    account_statuses = [r[0] for r in cur.fetchall()]
    if not employer_types or not verification_statuses:
        print("  [SKIP] employer reference codes missing; run B60 first")
        return

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        raise SystemExit("No users found")

    from faker import Faker

    Faker.seed(SEED + 2)
    f = Faker()

    to_insert = []
    for i in range(max(0, n - existing)):
        uid = user_ids[i % len(user_ids)]
        to_insert.append(
            (
                tenant_id,
                f.company()[:200],
                f.catch_phrase()[:100],
                f.url()[:200],
                random.choice(["Technology", "Financial Services", "Healthcare"]),
                employer_types[0] if employer_types else "small",
                "IN",
                "+919876543210",
                "Rao & Associates",
                f.email()[:254],
                "+919876543210",
                f.street_address()[:200],
                None,
                f.city()[:100],
                "State",
                "IN",
                "500001",
                28.6139,
                77.2090,
                "seed",
                False,
                verification_statuses[0] if verification_statuses else None,
                0,
                now_str(),
                uid,
                now_str(),
                uid,
                None,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO employer_organisation(tenant_account_id, company_name, "
                "legal_name, website, industry_name, size_code, type_code, "
                "primary_contact_name, primary_contact_email, primary_contact_phone, "
                "address_line1, address_line2, city, state, country, postal_code, "
                "latitude, longitude, coordinates_source, is_verified, "
                "verification_status_code, mapped_recruiter_count, created_at, "
                "created_by, updated_at, updated_by, deleted_at) VALUES %s "
                "ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO employer_organisation(tenant_account_id, company_name, "
            "legal_name, website, industry_name, size_code, type_code, "
            "primary_contact_name, primary_contact_email, primary_contact_phone, "
            "address_line1, address_line2, city, state, country, postal_code, "
            "latitude, longitude, coordinates_source, is_verified, "
            "verification_status_code, mapped_recruiter_count, created_at, "
            "created_by, updated_at, updated_by, deleted_at) VALUES %s "
            "ON CONFLICT DO NOTHING",
            to_insert,
        )


def _get_verified_employer_ids(cur):
    cur.execute(
        "SELECT id FROM employer_organisation WHERE is_verified = true ORDER BY id"
    )
    return [r[0] for r in cur.fetchall()]


def _seed_company_locations(cur, employer_ids):
    to_insert = []
    for eid in employer_ids:
        to_insert.append(
            (
                eid,
                "Head Office",
                "Main Street",
                None,
                "Delhi",
                "State",
                "IN",
                "500001",
                28.6139,
                77.2090,
                "seed",
                True,
                True,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO company_location(employer_organisation_id, location_name, "
                "address_line1, address_line2, city, state, country, postal_code, "
                "latitude, longitude, coordinates_source, is_head_office, is_active, "
                "created_at, created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO company_location(employer_organisation_id, location_name, "
            "address_line1, address_line2, city, state, country, postal_code, "
            "latitude, longitude, coordinates_source, is_head_office, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_tax_registration_identifiers(cur, employer_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'tax_identifier_type'")
    tax_types = [r[0] for r in cur.fetchall()]
    if not tax_types:
        print("  [SKIP] tax_identifier_type reference codes missing; run B60 first")
        return
    to_insert = []
    for eid in employer_ids[:100]:
        to_insert.append(
            (
                eid,
                "IN",
                tax_types[0],
                f"GST{eid:08d}",
                f"**-{eid % 100:02d}",
                True,
                None,
                None,
                now_str(),
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
            "INSERT INTO tax_registration_identifier(employer_organisation_id, "
            "country_code, identifier_type_code, identifier_value, "
            "identifier_display_mask, is_primary, valid_from, valid_to, "
            "verified_at, verification_status_code, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_verification_status_records(cur, employer_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'verification_type'")
    ver_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'verification_status'")
    ver_statuses = [r[0] for r in cur.fetchall()]

    if not ver_types or not ver_statuses:
        print("  [SKIP] verification reference codes missing; run B60 first")
        return

    verification_now = datetime.now()
    to_insert = []
    for eid in employer_ids[:100]:
        to_insert.append(
            (
                eid,
                ver_types[0],
                ver_statuses[0],
                verification_now,
                None,
                "Seeded verification",
                verification_now,
                0,
                verification_now,
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO verification_status_record(employer_organisation_id, "
            "verification_type_code, verification_status_code, verified_at, "
            "verified_by_user_id, outcome_notes, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_recruiter_mappings(cur, employer_ids, recruiter_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'recruiter_mapping_type'")
    mapping_types = [r[0] for r in cur.fetchall()]
    if not mapping_types:
        print("  [SKIP] recruiter_mapping_type reference codes missing; run B60 first")
        return
    to_insert = []
    for eid in employer_ids[:50]:
        rid = recruiter_ids[employer_ids.index(eid) % len(recruiter_ids)]
        to_insert.append(
            (
                eid,
                rid,
                mapping_types[0] if mapping_types else "direct",
                now_str(),
                None,
                False,
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
            "INSERT INTO recruiter_mapping(employer_organisation_id, recruiter_user_id, "
            "mapping_type_code, effective_start, effective_end, is_primary, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_account_administrators(cur, tenant_id, user_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'account_admin_role'")
    admin_roles = [r[0] for r in cur.fetchall()]
    if not admin_roles:
        print("  [SKIP] account_admin_role reference codes missing; run B60 first")
        return
    to_insert = []
    for uid in user_ids[:5]:
        to_insert.append(
            (
                tenant_id,
                uid,
                admin_roles[0] if admin_roles else "owner",
                True,
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
            "INSERT INTO account_administrator(tenant_account_id, "
            "administrator_user_id, admin_role_code, is_primary, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_organisation_hierarchy(cur, employer_ids):
    to_insert = []
    for i in range(1, min(50, len(employer_ids))):
        parent_id = employer_ids[i - 1]
        child_id = employer_ids[i]
        to_insert.append(
            (
                parent_id,
                child_id,
                "subsidiary",
                now_str(),
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
            "INSERT INTO organisation_hierarchy(parent_organisation_id, "
            "child_organisation_id, relationship_type_code, effective_start, "
            "effective_end, is_active, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ===========================================================================
# Gig marketplace
# ===========================================================================

def _ensure_jobs_for_gigs(cur, employer_ids, user_ids):
    """Ensure we have gig-capable job_requirements (open_to_consultants + published)."""
    cur.execute("SELECT count(*) FROM job_requirement WHERE is_open_to_consultants = true")
    existing = cur.fetchone()[0]
    if existing >= NUM_GIG_REQUESTS:
        print(f"  job_requirement (gig-capable): {existing:,} (target met)")
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

    Faker.seed(SEED + 3)
    f = Faker()

    to_insert = []
    remaining = NUM_GIG_REQUESTS - existing
    for i in range(remaining):
        eid = employer_ids[i % len(employer_ids)] if employer_ids else 1
        uid = user_ids[i % len(user_ids)] if user_ids else 1
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
                "Gig Location",
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


def _get_gig_job_ids(cur):
    cur.execute(
        "SELECT id FROM job_requirement WHERE is_open_to_consultants = true ORDER BY id"
    )
    return [r[0] for r in cur.fetchall()]


def _seed_gig_worker_profiles(cur, user_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'gig_worker_status'")
    statuses = [r[0] for r in cur.fetchall()]

    if not statuses:
        print("  [SKIP] gig_worker_status reference codes missing; run B60 first")
        return

    from faker import Faker

    Faker.seed(SEED + 4)
    f = Faker()

    cur.execute("SELECT count(*) FROM gig_worker_profile")
    existing = cur.fetchone()[0]
    if existing >= NUM_GIG_WORKERS:
        cur.execute("SELECT id FROM gig_worker_profile ORDER BY id")
        return [r[0] for r in cur.fetchall()]

    to_insert = []
    for i in range(NUM_GIG_WORKERS - existing):
        uid = user_ids[i % len(user_ids)] if user_ids else 1
        to_insert.append(
            (
                uid,
                f.name()[:150],
                f.sentence(nb_words=6)[:200],
                "Development, Consulting",
                50.0,
                200.0,
                "USD",
                statuses[0],
                True,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO gig_worker_profile(candidate_identity_id, worker_name, "
                "headline, service_offerings, charge_rate_min, charge_rate_max, "
                "charge_currency_code, status_code, is_available, created_at, "
                "created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO gig_worker_profile(candidate_identity_id, worker_name, "
            "headline, service_offerings, charge_rate_min, charge_rate_max, "
            "charge_currency_code, status_code, is_available, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )

    cur.execute("SELECT id FROM gig_worker_profile ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _seed_gig_worker_availability(cur, gig_worker_ids):
    to_insert = []
    for wid in gig_worker_ids:
        for _ in range(random.randint(1, 3)):
            start = datetime.now() - timedelta(days=random.randint(0, 30))
            end = start + timedelta(days=random.randint(1, 30))
            to_insert.append(
                (
                    wid,
                    start.strftime("%Y-%m-%d %H:%M:%S"),
                    end.strftime("%Y-%m-%d %H:%M:%S"),
                    "Asia/Kolkata",
                    random.choice([True, False]),
                    None,
                    True,
                    now_str(),
                    0,
                    now_str(),
                    0,
                    None,
                )
            )
            if len(to_insert) >= BATCH:
                _insert_many(
                    cur,
                    "INSERT INTO gig_worker_availability(gig_worker_profile_id, "
                    "availability_start_at, availability_end_at, time_zone, "
                    "is_recurring, recurrence_rule, is_active, created_at, "
                    "created_by, updated_at, updated_by, deleted_at) "
                    "VALUES %s ON CONFLICT DO NOTHING",
                    to_insert,
                    page_size=BATCH,
                )
                to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO gig_worker_availability(gig_worker_profile_id, "
            "availability_start_at, availability_end_at, time_zone, "
            "is_recurring, recurrence_rule, is_active, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_gig_request_details(cur, job_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'pricing_model'")
    pricing_models = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'handoff_system'")
    handoff_systems = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'fulfillment_status'")
    fulfillment_statuses = [r[0] for r in cur.fetchall()]
    if not pricing_models or not handoff_systems:
        print("  [SKIP] gig reference codes missing; run B60 first")
        return []

    cur.execute("SELECT count(*) FROM gig_request_detail")
    existing = cur.fetchone()[0]
    if existing >= NUM_GIG_REQUESTS:
        cur.execute("SELECT id FROM gig_request_detail ORDER BY id")
        return [r[0] for r in cur.fetchall()]

    to_insert = []
    for i in range(NUM_GIG_REQUESTS - existing):
        jid = job_ids[i % len(job_ids)] if job_ids else 1
        pm = pricing_models[i % len(pricing_models)]
        start = datetime.now() + timedelta(days=i)
        end = start + timedelta(days=random.randint(7, 30))
        to_insert.append(
            (
                jid,
                pm,
                500.0 if pm == "fixed" else None,
                "USD" if pm == "fixed" else None,
                25.0 if pm == "rate" else None,
                "hour" if pm == "rate" else None,
                "USD" if pm == "rate" else None,
                start,
                end,
                None,
                handoff_systems[0] if handoff_systems else "external_fulfillment",
                f"handoff_ref_{jid}_{i}",
                fulfillment_statuses[0] if fulfillment_statuses else "pending",
                None,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO gig_request_detail(job_requirement_id, pricing_model_code, "
                "fixed_price, fixed_price_currency_code, rate_per_time_unit, "
                "rate_time_unit_code, rate_currency_code, window_start_at, "
                "window_end_at, apply_by_at, handoff_system_code, handoff_reference, "
                "fulfillment_status_code, fulfillment_synced_at, created_at, "
                "created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO gig_request_detail(job_requirement_id, pricing_model_code, "
            "fixed_price, fixed_price_currency_code, rate_per_time_unit, "
            "rate_time_unit_code, rate_currency_code, window_start_at, "
            "window_end_at, apply_by_at, handoff_system_code, handoff_reference, "
            "fulfillment_status_code, fulfillment_synced_at, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )

    cur.execute("SELECT id FROM gig_request_detail ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _seed_gig_applications(cur, gig_request_detail_ids, gig_worker_ids, applicant_ids):
    cur.execute("SELECT code FROM reference_code WHERE domain = 'application_channel'")
    channels = [r[0] for r in cur.fetchall()]
    if not channels:
        print("  [SKIP] application_channel reference codes missing; run B60 first")
        return []

    cur.execute("SELECT count(*) FROM gig_application")
    existing = cur.fetchone()[0]
    if existing >= NUM_GIG_APPLICATIONS:
        cur.execute("SELECT id FROM gig_application ORDER BY id")
        return [r[0] for r in cur.fetchall()]

    # guard against empty helper lists (can happen when upstream seeding skipped)
    if not gig_request_detail_ids or not gig_worker_ids or not applicant_ids:
        print("  [SKIP] gig application seeding requires gig requests, gig workers, and applicants; run B60/B62 fully first")
        return []

    to_insert = []
    for i in range(NUM_GIG_APPLICATIONS - existing):
        grd_id = gig_request_detail_ids[i % len(gig_request_detail_ids)]
        worker_id = gig_worker_ids[i % len(gig_worker_ids)]
        applicant_id = applicant_ids[i % len(applicant_ids)]
        applied_at = datetime.now() - timedelta(days=random.randint(0, 60))
        to_insert.append(
            (
                grd_id,
                worker_id,
                applicant_id,
                100.0 + (i % 500),
                "USD",
                f"Bid message for application {i}",
                "applied",
                applied_at,
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
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO gig_application(gig_request_detail_id, "
                "gig_worker_profile_id, applicant_user_id, bid_amount, "
                "bid_currency_code, bid_message, application_status_code, "
                "applied_at, reviewed_at, reviewed_by_user_id, rejection_reason, "
                "created_at, created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO gig_application(gig_request_detail_id, "
            "gig_worker_profile_id, applicant_user_id, bid_amount, "
            "bid_currency_code, bid_message, application_status_code, "
            "applied_at, reviewed_at, reviewed_by_user_id, rejection_reason, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )

    cur.execute("SELECT id FROM gig_application ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _seed_gig_assignments(cur, app_ids, user_ids):
    cur.execute("SELECT count(*) FROM gig_assignment")
    existing = cur.fetchone()[0]
    accepted = [a for a in app_ids if a and (a % 5 == 0)]  # 20% accepted
    to_insert = []
    for i, app_id in enumerate(accepted):
        if i >= 200:  # limit assignments
            break
        assigned_at = datetime.now() - timedelta(days=random.randint(0, 30))
        to_insert.append(
            (
                app_id,
                assigned_at,
                user_ids[0] if user_ids else 1,
                assigned_at + timedelta(days=1),
                assigned_at + timedelta(days=7),
                None,
                None,
                "assigned",
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
            "INSERT INTO gig_assignment(gig_application_id, assigned_at, "
            "assigned_by_user_id, expected_start_at, expected_end_at, "
            "actual_start_at, actual_end_at, assignment_status_code, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_gig_handoff_references(cur):
    cur.execute("SELECT id FROM gig_assignment")
    assignment_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'handoff_system'")
    handoff_systems = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'fulfillment_status'")
    fulfillment_statuses = [r[0] for r in cur.fetchall()]
    if not handoff_systems or not assignment_ids:
        return

    to_insert = []
    for aid in assignment_ids[:100]:
        to_insert.append(
            (
                aid,
                handoff_systems[0] if handoff_systems else "external_fulfillment",
                f"ext_ref_{aid}",
                fulfillment_statuses[0] if fulfillment_statuses else "pending",
                None,
                None,
                None,
                "Seeded handoff",
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
            "INSERT INTO gig_handoff_reference(gig_assignment_id, handoff_system_code, "
            "external_reference, handoff_status_code, handed_off_at, reconciled_at, "
            "reconciled_by_user_id, reconciliation_note, created_at, created_by, "
            "updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_gig_earnings_references(cur):
    cur.execute("SELECT id FROM gig_assignment")
    assignment_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'earnings_type'")
    earnings_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'source_system'")
    source_systems = [r[0] for r in cur.fetchall()]
    if not earnings_types or not source_systems or not assignment_ids:
        return

    to_insert = []
    if assignment_ids and earnings_types and source_systems:
        for aid in assignment_ids[:100]:
            to_insert.append(
                (
                    aid,
                    earnings_types[0],
                    1000.0,
                    "USD",
                    source_systems[0],
                    None,
                    None,
                    None,
                    "Seeded earnings reference",
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
            "INSERT INTO gig_earnings_reference(gig_assignment_id, earnings_type_code, "
            "earnings_amount, earnings_currency_code, source_system_code, reported_at, "
            "reconciled_at, reconciled_by_user_id, reconciliation_note, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )
    else:
        missing = []
        if not assignment_ids:
            missing.append("gig_assignment")
        if not earnings_types:
            missing.append("earnings_type")
        if not source_systems:
            missing.append("source_system")
        print(f"  [SKIP] gig earnings reference seeding requires: {', '.join(missing)}")


def _seed_gig_favourites_blacklists(cur, user_ids, gig_worker_ids):
    cur.execute("SELECT count(*) FROM gig_favourite")
    fav_existing = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM gig_blacklist")
    bl_existing = cur.fetchone()[0]
    if fav_existing >= 100 and bl_existing >= 50:
        return

    if not gig_worker_ids:
        print("  [SKIP] gig favourite/blacklist seeding requires gig workers; run B60/B62 fully first")
        return

    fav_now = datetime.now()
    # Favourites
    to_insert = []
    for uid in user_ids[:50]:
        wid = gig_worker_ids[uid % len(gig_worker_ids)]
        to_insert.append(
            (
                uid,
                wid,
                fav_now,
                fav_now,
                0,
                fav_now,
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO gig_favourite(requester_user_id, gig_worker_profile_id, "
            "favourited_at, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )

    # Blacklists
    to_insert = []
    bl_now = datetime.now()
    for uid in user_ids[:30]:
        wid = gig_worker_ids[(uid + 10) % len(gig_worker_ids)]
        to_insert.append(
            (
                uid,
                wid,
                bl_now,
                uid,
                "Seeded blacklist",
                True,
                bl_now,
                0,
                bl_now,
                0,
                None,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO gig_blacklist(requester_user_id, gig_worker_profile_id, "
            "blacklisted_at, blacklisted_by_user_id, reason, is_active, "
            "created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_gig_ratings(cur):
    cur.execute("SELECT id FROM gig_assignment")
    assignment_ids = [r[0] for r in cur.fetchall()]
    if not assignment_ids:
        return
    to_insert = []
    for aid in assignment_ids[:50]:
        to_insert.append(
            (
                aid,
                1,
                4.5,
                "Great work",
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
            "INSERT INTO gig_rating(gig_assignment_id, rating_by_user_id, "
            "rating_value, rating_text, rated_at, created_at, created_by, "
            "updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


if __name__ == "__main__":
    main()
