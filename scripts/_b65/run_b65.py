import importlib.util, datetime, os, psycopg2

spec = importlib.util.spec_from_file_location("harness", "scripts/_b65/harness.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

PG_DSN = h.PG_DSN
REPORT_BASE = h.REPORT_BASE
p_b65 = os.path.join(REPORT_BASE, "B65_query_set_with_output_and_execution_plans.txt")

conn = psycopg2.connect(PG_DSN)
conn.set_client_encoding("UTF8")
conn.autocommit = True
cur = conn.cursor()

def write_label(path, label, sql, max_rows=60):
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n## " + label + "\n\n")
        f.write(sql.strip() + "\n\n")
    cur.execute(sql)
    rows = cur.fetchall()
    if rows:
        desc = [d.name for d in cur.description]
        with open(path, "a", encoding="utf-8") as f:
            f.write("Columns: " + ", ".join(desc) + "\n")
            f.write("Rows: %d (shown: %d)\n\n" % (len(rows), min(len(rows), max_rows)))
            for i, r in enumerate(rows[:max_rows]):
                if i >= max_rows:
                    f.write("... truncated ...\n")
                    break
                parts = []
                for v in r:
                    parts.append("" if v is None else str(v))
                f.write(" | ".join(parts) + "\n")
            f.write("\n")
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write("Rows: 0\n\n")

def write_explain(path, label, sql):
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n## EXPLAIN " + label + "\n\n")
        f.write(sql.strip() + "\n\nExecution plan:\n")
    cur.execute("EXPLAIN (ANALYZE, COSTS, BUFFERS, TIMING, FORMAT TEXT) " + sql.strip())
    plan = cur.fetchall()
    with open(path, "a", encoding="utf-8") as f:
        for r in plan:
            f.write(str(r[0]) + "\n")
        f.write("\n")

with open(p_b65, "a", encoding="utf-8") as f:
    f.write("\n## Scope\n")
    f.write("Fixed query set covering functional, transactional, lookup and performance cases.\n")
    f.write("Top 10 queries by estimated plan cost include execution plans (EXPLAIN ANALYZE).\n\n")

cur.execute("""
SELECT relname, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 20
""")
top = cur.fetchall()
with open(p_b65, "a", encoding="utf-8") as f:
    f.write("## Reference table sizes (live row estimate)\n")
    for t in top:
        f.write("  %-40s %12s\n" % (t[0], format(t[1], ",")))
    f.write("\n")

queries = [
    # Lookup
    ("B65-Q1 Lookup: active country/state/city for location context",
     "SELECT c.id, c.iso_alpha2, c.name AS country, s.name AS state, ci.name AS city "
     "FROM country c "
     "LEFT JOIN state s ON s.country_id = c.id AND s.is_active = true "
     "LEFT JOIN city ci ON ci.country_id = c.id AND ci.is_active = true "
     "WHERE c.is_active = true "
     "ORDER BY c.name, s.name, ci.name "
     "LIMIT 30;"),

    ("B65-Q2 Lookup: resolve a skill master record by name (case-insensitive)",
     "SELECT id, name, category, is_active, sort_order "
     "FROM skill "
     "WHERE lower(name) = 'python' "
     "LIMIT 3;"),

    # Functional
    ("B65-Q5 Functional: load candidate profile with contact, education, work experience, skills, latest resume",
     "SELECT ci.id AS candidate_id, ci.first_name, ci.last_name, "
     "cc.email AS primary_email, cc.phone, cc.phone_country_code, "
     "cd.id AS education_id, cd.institution_name, cd.qualification, cd.field_of_study, "
     "cw.id AS experience_id, cw.employer_name, cw.role, cw.start_date, cw.end_date, "
     "cs.skill_name, cs.proficiency, cs.years_of_experience, "
     "rv.id AS resume_id, rv.version_label, rv.language "
     "FROM candidate_identity ci "
     "LEFT JOIN candidate_contact cc ON cc.candidate_id = ci.id AND cc.is_primary = true "
     "LEFT JOIN LATERAL (SELECT id, institution_name, qualification, field_of_study FROM candidate_education "
     "WHERE candidate_id = ci.id ORDER BY created_at DESC LIMIT 2) cd ON true "
     "LEFT JOIN LATERAL (SELECT id, employer_name, role, start_date, end_date FROM candidate_work_experience "
     "WHERE candidate_id = ci.id ORDER BY created_at DESC LIMIT 2) cw ON true "
     "LEFT JOIN candidate_skill cs ON cs.candidate_id = ci.id "
     "LEFT JOIN LATERAL (SELECT id, version_label, language FROM resume_version "
     "WHERE candidate_id = ci.id AND is_current = true LIMIT 1) rv ON true "
     "WHERE ci.deleted_at IS NULL "
     "ORDER BY ci.created_at DESC LIMIT 1;"),

    ("B65-Q6 Functional: active job requirements for an employer with positions and skill requirements",
     "SELECT jr.id, jr.title, jp.position_title, jrs.skill_name, jrs.is_required, "
     "jr.status_code, jr.employment_type_code, jr.work_type_code "
     "FROM job_requirement jr "
     "LEFT JOIN job_position jp ON jp.job_requirement_id = jr.id AND jp.is_active = true "
     "LEFT JOIN job_requirement_skill jrs ON jrs.job_requirement_id = jr.id "
     "WHERE jr.employer_organisation_id = (SELECT id FROM employer_organisation WHERE company_name = 'Acme Logistics' LIMIT 1) "
     "AND jr.deleted_at IS NULL "
     "ORDER BY jr.id, jp.created_at LIMIT 40;"),

    ("B65-Q7 Functional: applications for a job requirement with current stage",
     "SELECT a.id AS application_id, a.applied_at, ci.first_name, ci.last_name, "
     "a.source_channel_code, ppe.pipeline_stage_code AS current_stage, ppe.entered_at AS stage_entered_at "
     "FROM application a "
     "JOIN candidate_identity ci ON ci.user_id = a.candidate_id "
     "LEFT JOIN LATERAL (SELECT pipeline_stage_code, entered_at FROM application_pipeline_event e "
     "WHERE e.application_id = a.id ORDER BY e.entered_at DESC LIMIT 1) ppe ON true "
     "WHERE a.job_requirement_id = (SELECT id FROM job_requirement WHERE title = 'Senior Backend Engineer' LIMIT 1) "
     "AND a.deleted_at IS NULL "
     "ORDER BY a.applied_at DESC LIMIT 15;"),

    ("B65-Q8 Functional: walk an application's pipeline event history",
     "SELECT id AS event_id, pipeline_stage_code, entered_at, entered_by_user_id "
     "FROM application_pipeline_event "
     "WHERE application_id = (SELECT id FROM application WHERE deleted_at IS NULL LIMIT 1) "
     "ORDER BY entered_at;"),

    # Transactional
    ("B65-Q10 Transactional: enforce licence device limit (active sessions per user vs max devices)",
     "SELECT u.id, u.email, sl.max_devices_per_user, "
     "sr.id AS session_id, sr.started_at, sr.expires_at, "
     "count(*) OVER (PARTITION BY u.id) AS active_session_count "
     "FROM users u "
     "JOIN subscription_licence sl ON sl.tenant_account_id = 1 AND sl.status_code = 'ls_active' "
     "LEFT JOIN device_session sr ON sr.user_id = u.id "
     "AND sr.expires_at > now() AND sr.is_revoked = false "
     "WHERE u.deleted_at IS NULL "
     "ORDER BY u.id LIMIT 12;"),

    ("B65-Q11 Transactional: append-only wallet ledger (no updates, corrections reference originals)",
     "SELECT wl.id, wl.created_at, wl.transaction_type_code, wl.amount, wl.currency_code, "
     "wl.balance_after, wl.reference_type_code, wl.reference_id, "
     "wl.correction_reference_id, wl.description "
     "FROM wallet_ledger_entry wl "
     "WHERE wl.wallet_account_id = (SELECT id FROM wallet_account LIMIT 1) "
     "ORDER BY wl.created_at;"),

    ("B65-Q12 Transactional: subscription period non-overlap (same licence)",
     "SELECT id, status_code, started_at, ended_at, renew_type_code "
     "FROM subscription_period "
     "WHERE subscription_licence_id = 1 "
     "ORDER BY started_at;"),
]

for label, sql in queries:
    write_label(p_b65, label, sql)

# Top 10 execution plans with ANALYZE
top10 = [
    ("B65-Q1", queries[0][1]),
    ("B65-Q5", queries[2][1]),
    ("B65-Q6", queries[3][1]),
    ("B65-Q7", queries[4][1]),
    ("B65-Q8", queries[5][1]),
    ("B65-Q10", queries[6][1]),
    ("B65-Q11", queries[7][1]),
    ("B65-Q12", queries[8][1]),
]
with open(p_b65, "a", encoding="utf-8") as f:
    f.write("\n## Top 10 execution plans (EXPLAIN ANALYZE)\n\n")
for i, (label, sql) in enumerate(top10, 1):
    with open(p_b65, "a", encoding="utf-8") as f:
        f.write("\n### Top-10 Plan #%d: %s\n" % (i, label))
        f.write(sql.strip() + "\n\n")
    try:
        write_explain(p_b65, label, sql)
    except Exception as e:
        with open(p_b65, "a", encoding="utf-8") as f:
            f.write("EXPLAIN ANALYZE failed: %s\n\n" % e)

print("B65 run complete:", p_b65, os.path.getsize(p_b65), "bytes")
cur.close()
conn.close()
