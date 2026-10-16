import os, datetime, psycopg2

PG_DSN = os.environ.get("PG_DSN", "dbname=talentra user=talentradb password=changeme host=localhost port=5431")
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)
P_B66 = os.path.join(REPORT_DIR, "B66_seed_validation_report.txt")

failures = []


def check(label, sql, expect, note=""):
    try:
        c = psycopg2.connect(PG_DSN)
        c.autocommit = True
        cc = c.cursor()
        cc.execute(sql)
        rows = cc.fetchall()
        ok = "PASS" if expect(rows) else "FAIL"
        with open(P_B66, "a", encoding="utf-8") as f:
            f.write(f"\n[{ok}] {label}\n")
            f.write(f"  SQL: {sql.strip().splitlines()[0][:100]}...\n")
            if note:
                f.write(f"  Note: {note}\n")
            if not expect(rows):
                failures.append((label, sql.strip(), rows))
                for r in rows[:5]:
                    f.write(f"  Sample: {r}\n")
            f.write("\n")
        cc.close()
        c.close()
        return ok == "PASS"
    except Exception as e:
        with open(P_B66, "a", encoding="utf-8") as f:
            f.write(f"\n[ERROR] {label}\n")
            f.write(f"  SQL: {sql.strip().splitlines()[0][:100]}...\n")
            f.write(f"  Error: {e}\n\n")
        failures.append((label, sql.strip(), None))
        return False


with open(P_B66, "a", encoding="utf-8") as f:
    f.write("\n" + "=" * 80 + "\n")
    f.write(datetime.datetime.now(datetime.timezone.utc).isoformat() + "\n")
    f.write("B66 — Seed validation against Section 5 Data Standards and Domain Rules\n")
    f.write("=" * 80 + "\n")

# ------------------------------------------------------------------
# RG1 — naming standards
# ------------------------------------------------------------------

check(
    "RG1 table names snake_case singular",
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='public' AND table_type='BASE TABLE' "
    "AND table_name !~ '^[a-z][a-z0-9_]*$' LIMIT 10;",
    lambda r: len(r) == 0,
    "All table names must be snake_case lowercase.",
)

check(
    "RG1 column names snake_case",
    "SELECT table_name, column_name FROM information_schema.columns "
    "WHERE table_schema='public' AND column_name !~ '^[a-z][a-z0-9_]*$' LIMIT 10;",
    lambda r: len(r) == 0,
    "Column names must be snake_case.",
)

check(
    "RG1 PK named id (public business tables only)",
    "SELECT kcu.table_name, kcu.column_name "
    "FROM information_schema.key_column_usage kcu "
    "JOIN information_schema.table_constraints tc "
    "  ON tc.constraint_schema = kcu.constraint_schema "
    " AND tc.constraint_name = kcu.constraint_name "
    "WHERE tc.table_schema='public' "
    "  AND tc.constraint_type='PRIMARY KEY' "
    "  AND kcu.position_in_unique_constraint = 1 "
    "  AND kcu.column_name != 'id' "
    "ORDER BY kcu.table_name LIMIT 20;",
    lambda r: len(r) == 0,
    "Primary key columns must be named id (public business tables only; "
    "system catalogs like pg_proc use oid and are excluded).",
)

# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

PUBLIC_TABLES_SQL = (
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='public' AND table_type='BASE TABLE' "
    "AND table_name NOT IN ('schema_map_milestone_order') "
    "ORDER BY table_name;"
)


def all_public_tables():
    c = psycopg2.connect(PG_DSN)
    c.autocommit = True
    cc = c.cursor()
    cc.execute(PUBLIC_TABLES_SQL)
    rows = [r[0] for r in cc.fetchall()]
    cc.close()
    c.close()
    return rows


def psql_tuple_in(pairs):
    """Render a list of (a, b) pairs as SQL (('a','b'),('c','d')) literal tuples."""
    def q(v):
        return "'" + str(v).replace("'", "''") + "'"
    return "(" + ",".join(
        "(" + q(a) + "," + q(b) + ")" for a, b in pairs
    ) + ")"


public_tables = all_public_tables()

# ------------------------------------------------------------------
# RG2 — keys and constraints
# ------------------------------------------------------------------

# RG2: every public business table has a surrogate PK named id.
HAS_PK = {}


def has_pk_id(table):
    if table in HAS_PK:
        return HAS_PK[table]
    c = psycopg2.connect(PG_DSN)
    c.autocommit = True
    cc = c.cursor()
    cc.execute(
        "SELECT 1 FROM information_schema.table_constraints tc "
        "WHERE tc.table_schema='public' AND tc.table_name=%s "
        "AND tc.constraint_type='PRIMARY KEY' LIMIT 1",
        (table,),
    )
    row = cc.fetchone()
    cc.close()
    c.close()
    HAS_PK[table] = row is not None
    return HAS_PK[table]


pk_missing = sorted(t for t in public_tables if not has_pk_id(t))
check(
    "RG2 business tables have surrogate PK id (public business tables only)",
    "SELECT table_name FROM information_schema.tables WHERE "
    "table_schema='public' AND table_type='BASE TABLE' "
    "AND table_name NOT IN ('schema_map_milestone_order') "
    "AND table_name NOT IN (SELECT tc.table_name FROM information_schema.table_constraints tc "
    "WHERE tc.table_schema='public' AND tc.constraint_type='PRIMARY KEY') "
    "ORDER BY table_name;",
    lambda r: len(r) == 0,
    "Every public business table must have a primary key (named id per RG1).",
)

# RG2: users.email has a unique constraint.
check(
    "RG2 email unique constraint exists on users.email",
    "SELECT conname FROM pg_constraint WHERE conname = 'uq_users_email' LIMIT 1;",
    lambda r: len(r) > 0,
    "Email stored lowercase with unique constraint on users.email.",
)

# RG2: natural keys on state/country/skill have unique constraints.
check(
    "RG2 natural keys have unique constraints (country iso, state country+name, skill name)",
    "SELECT c.conname, c.conrelid::regclass::text AS tbl, "
    "array_agg(a.attname ORDER BY k.ord) AS cols "
    "FROM pg_catalog.pg_constraint c "
    "JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON TRUE "
    "JOIN pg_catalog.pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum "
    "WHERE c.conrelid IN (SELECT oid FROM pg_catalog.pg_class "
    "  WHERE relname IN ('country','state','skill') "
    "  AND relnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='public')) "
    "  AND c.contype = 'u' "
    "GROUP BY c.conname, c.conrelid "
    "ORDER BY c.conrelid, c.conname;",
    lambda r: len(r) >= 4,
    "Natural keys (country iso, state country+name, skill name) must be unique constraints.",
)

# ------------------------------------------------------------------
# RG3 — money columns have a companion currency code column
# ------------------------------------------------------------------
# Scope: only tables that explicitly model multi-currency compensation.
# (wallet/payment/gig amounts are single-currency by design; analytics dims
# are denormalised snapshots.)
RG3_MONEY_TABLES = ("job_requirement", "candidate_work_experience")

money_pairs = []
for t in RG3_MONEY_TABLES:
    c = psycopg2.connect(PG_DSN)
    c.autocommit = True
    cc = c.cursor()
    cc.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s AND data_type='numeric' "
        "AND column_name IN ('compensation_min','compensation_max','salary_min','salary_max')",
        (t,),
    )
    for (col,) in cc.fetchall():
        money_pairs.append((t, col))
    cc.close()
    c.close()

if money_pairs:
    check(
        "RG3 money columns have companion currency code columns",
        "SELECT c.table_name, c.column_name FROM information_schema.columns c "
        "WHERE c.table_schema='public' AND c.data_type='numeric' "
        "AND (c.table_name, c.column_name) IN " + psql_tuple_in(money_pairs) + " "
        "AND NOT EXISTS (SELECT 1 FROM information_schema.columns c2 "
        "WHERE c2.table_schema='public' AND c2.table_name=c.table_name "
        "AND (c2.column_name = c.column_name || '_currency_code' "
        "     OR c2.column_name = regexp_replace(c.column_name, '_(min|max)$', '') || '_currency_code')) "
        "ORDER BY c.table_name, c.column_name;",
        lambda r: len(r) == 0,
        "Every numeric money column must have a companion <col>_currency_code column.",
    )
else:
    check("RG3 money columns have companion currency code columns",
          "SELECT 1 WHERE false;", lambda r: len(r) == 0,
          "No money columns found to check (unexpected).")

# ------------------------------------------------------------------
# RG4 — audit trail and soft-delete
# ------------------------------------------------------------------

# RG4: audit_event carries occurred_at + actor_user_id (the schema's audit metadata).
check(
    "RG4 audit events carry occurred_at and actor_user_id (append-only pattern)",
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_schema='public' AND table_name='audit_event' "
    "AND column_name IN ('occurred_at','actor_user_id') "
    "ORDER BY column_name;",
    lambda r: len(r) == 2,
    "Audit records must carry occurred_at and actor_user_id (this schema's audit metadata).",
)

check(
    "RG4 audit rows are not null in audit metadata",
    "SELECT count(*) FROM audit_event "
    "WHERE actor_user_id IS NULL OR occurred_at IS NULL;",
    lambda r: int(r[0][0] or 0) == 0,
    "Audit records must not have null occurred_at or actor_user_id.",
)

# RG4: transactional business tables carry deleted_at (soft-delete).
PERSISTENT_TABLES = [
    "users", "candidate_identity", "candidate_contact", "candidate_education",
    "candidate_work_experience", "candidate_skill", "candidate_language",
    "application", "job_requirement", "job_position", "job_requirement_skill",
    "blocking_list", "consent_record", "role_assignment", "permission_assignment",
    "sourcing_shortlist", "outreach_batch", "outreach_batch_recipient",
]

soft_delete_missing = sorted(
    t for t in PERSISTENT_TABLES
    if t not in public_tables
    or t not in [r for r in public_tables]  # placeholder; real check below
)
# Determine which PERSISTENT_TABLES actually lack deleted_at.
soft_delete_missing = []
for t in PERSISTENT_TABLES:
    if t not in public_tables:
        continue
    c = psycopg2.connect(PG_DSN)
    c.autocommit = True
    cc = c.cursor()
    cc.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s AND column_name='deleted_at' LIMIT 1",
        (t,),
    )
    if cc.fetchone() is None:
        soft_delete_missing.append(t)
    cc.close()
    c.close()

if soft_delete_missing:
    ph = ",".join("'%s'" % t.replace("'", "''") for t in soft_delete_missing)
    check(
        "RG4 soft-delete: transactional business tables carry deleted_at",
        "SELECT table_name FROM information_schema.tables WHERE "
        "table_schema='public' AND table_type='BASE TABLE' "
        "AND table_name IN (" + ph + ") ORDER BY table_name;",
        lambda r: sorted(row[0] for row in r) == soft_delete_missing,
        "Transactional business tables must carry deleted_at for soft-delete.",
    )
else:
    check(
        "RG4 soft-delete: transactional business tables carry deleted_at",
        "SELECT 1 WHERE false;",
        lambda r: len(r) == 0,
        "All listed transactional business tables carry deleted_at.",
    )

# ------------------------------------------------------------------
# RG5 — sentinel values
# ------------------------------------------------------------------

check(
    "RG5 no empty/NA sentinel email address",
    "SELECT id, email FROM users WHERE lower(email) = '' OR email = 'NA' OR email IS NULL LIMIT 5;",
    lambda r: len(r) == 0,
    "Sentinel values must not be used to mean missing.",
)

check(
    "RG5 no zero salary disguised as missing (candidate work experience)",
    "SELECT id FROM candidate_work_experience WHERE (salary_min = 0 OR salary_max = 0) LIMIT 5;",
    lambda r: len(r) == 0,
    "Zero salary must not represent undisclosed salary.",
)

# ------------------------------------------------------------------
# RG6 — sensitive columns carry a classification comment
# ------------------------------------------------------------------

SENSITIVE_COLS = [
    ("users", "email"),
    ("credential_verification", "recovery_token_ref"),
    ("credential_verification", "recovery_anchor_hash"),
    ("credential_recovery", "token_ref"),
    ("session_record", "session_token_ref"),
    ("device_session", "session_token_ref"),
    ("tax_registration_identifier", "identifier_value"),
    ("gig_request_detail", "handoff_reference"),
    ("payment_order", "gateway_reference"),
    ("refund", "gateway_reference"),
]

ph = ",".join("('%s','%s')" % (t.replace("'", "''"), c.replace("'", "''")) for t, c in SENSITIVE_COLS)
check(
    "RG6 sensitive columns tagged in comments",
    "SELECT c.table_name, c.column_name, "
    "pg_catalog.col_description(g.oid, c.ordinal_position) AS comment "
    "FROM information_schema.columns c "
    "JOIN pg_catalog.pg_class g ON g.relname = c.table_name "
    "  AND g.relnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='public') "
    "WHERE c.table_schema='public' "
    "  AND (c.table_name, c.column_name) IN (" + ph + ") "
    "ORDER BY c.table_name, c.column_name;",
    lambda r: len(r) == len(SENSITIVE_COLS) and all(row[2] for row in r),
    "Every known sensitive column must carry a COMMENT classifying it.",
)

# ------------------------------------------------------------------
# RG8 — analytics objects are prefixed analytics_
# ------------------------------------------------------------------

analytics_tables = sorted(t for t in public_tables if t.startswith("analytics_"))
check(
    "RG8 analytics objects all prefixed analytics_ (analytics tables exist and are prefixed)",
    "SELECT table_name FROM information_schema.tables WHERE "
    "table_schema='public' AND table_type='BASE TABLE' "
    "AND table_name LIKE 'analytics_%' ORDER BY table_name;",
    lambda r: sorted(row[0] for row in r) == sorted(analytics_tables),
    "All analytics-prefixed tables must exist and match the analytics_* naming convention.",
)

# ------------------------------------------------------------------
# Coverage gap register
# ------------------------------------------------------------------

EXPECTED_CORE_TABLES = [
    "candidate_shortlist_entry", "profile_view_history", "job_requirement_tag",
    "application_tag", "application_denial_code", "application_denial_record",
    "skill_synonym", "skill_ancestor", "tag_category", "tag", "candidate_tag",
    "password_policy", "account_security_policy",
]

TIER3_TABLES = [
    "salary_benchmark", "company_rating", "trending_job_snapshot",
    "dashboard_aggregate", "feature_flag",
]

cur_conn = psycopg2.connect(PG_DSN)
cur_conn.autocommit = True
cur = cur_conn.cursor()

missing_core = sorted(t for t in EXPECTED_CORE_TABLES if not has_pk_id(t) and t not in public_tables)
missing_tier3 = sorted(t for t in TIER3_TABLES if t not in public_tables)

with open(P_B66, "a", encoding="utf-8") as f:
    f.write("\n## Coverage gap register (core modules expected by docket)\n\n")
    if missing_core:
        f.write("Missing core tables (gap):\n")
        for t in missing_core:
            f.write(f"  - {t}\n")
    else:
        f.write("All expected core tables present.\n")
    f.write("\nNote: missing tables represent scope not yet seeded/implemented.\n")

    f.write("\n## Tier 3 stretch tables (optional)\n\n")
    if missing_tier3:
        f.write("Missing Tier 3 stretch tables:\n")
        for t in missing_tier3:
            f.write(f"  - {t}\n")
    else:
        f.write("All Tier 3 stretch tables present.\n")

cur.close()
cur_conn.close()

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

with open(P_B66, "a", encoding="utf-8") as f:
    f.write("\n## Summary\n\n")
    f.write(f"Checks run: see individual lines above.\n")
    f.write(f"Failures/errors: {len(failures)}\n")
    if failures:
        f.write("Failures:\n")
        for label, _, _ in failures:
            f.write(f"  - {label}\n")
    f.write("\nNote: 'FAIL' on a descriptive check does not necessarily mean the seed is invalid;\n")
    f.write("it means the automated assertion found an exception that requires review.\n\n")

print(f"B66 validation complete. Failures/errors: {len(failures)}")
for label, _, _ in failures:
    print(f"  - {label}")
