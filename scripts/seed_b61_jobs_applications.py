#!/usr/bin/env python3
"""
B61 Seed: Jobs and Applications at laptop scale.
Seeds 100,000 job requirements and 5,000,000 applications across the full
status pipeline (applied, shortlisted, interviewed, offered, joined, rejected).
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
NUM_CANDIDATES = 10_000        # enough candidates to support 5M unique (c,j) pairs
NUM_JOBS = 100_000
NUM_APPLICATIONS = 5_000_000

BATCH_SIZE_CANDIDATES = 5_000
BATCH_SIZE_SKILLS = 20_000
BATCH_SIZE_APPLICATIONS = 50_000
BATCH_SIZE_PIPELINE = 50_000

SEED = 42

# ---------------------------------------------------------------------------
# Pipeline stage distribution (must sum to 1.0)
# "across the full status pipeline": every stage represented
# ---------------------------------------------------------------------------
PIPELINE_STAGES = [
    ("applied",      0.45),   # 45% still applied
    ("shortlisted",  0.20),   # 20% shortlisted
    ("interviewed",  0.15),   # 15% interviewed
    ("offered",      0.10),   # 10% offered
    ("joined",       0.05),   # 5% joined
    ("rejected",     0.05),   # 5% rejected
]
assert abs(sum(w for _, w in PIPELINE_STAGES) - 1.0) < 1e-9, "weights must sum to 1"

DSN = os.environ.get("PG_DSN", "dbname=talentra user=talentradb password=changeme host=localhost port=5431")


def main():
    random.seed(SEED)

    print("=== B61 Seed (laptop scale) ===")
    print(f"Targets: {NUM_JOBS} jobs, {NUM_APPLICATIONS:,} applications, {NUM_CANDIDATES:,} candidates")
    print()

    conn = psycopg2.connect(DSN)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    # -------------------------------------------------------------------
    # Load reference data
    # -------------------------------------------------------------------
    print("Loading reference data...")
    cur.execute("SELECT code FROM reference_code WHERE domain = 'candidate_status'")
    candidate_statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'gender'")
    genders = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'contact_type'")
    contact_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'assessment_type'")
    assessment_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'proficiency'")
    proficiencies = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'job_status'")
    job_statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'job_visibility'")
    job_visibilities = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'application_channel'")
    application_channels = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'pipeline_stage'")
    pipeline_stages = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'source_channel'")
    source_channels = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM skill")
    skill_names = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM industry")
    industries = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM job_role")
    job_roles = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM language_lookup")
    language_names = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM employment_type ORDER BY id")
    employment_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM work_type ORDER BY id")
    work_types = [r[0] for r in cur.fetchall()]
    print("  Reference data loaded.\n")

    # Ensure referential integrity rows exist
    _ensure_tenant(cur)
    _ensure_users(cur, NUM_CANDIDATES + 500)          # candidates + recruiters
    _ensure_employers(cur)                              # employer organisations

    # -------------------------------------------------------------------
    # Candidates
    # -------------------------------------------------------------------
    print(f"Seeding {NUM_CANDIDATES:,} candidates...")
    candidate_ids = _seed_candidates(cur, NUM_CANDIDATES)
    print(f"  candidate_identity: {len(candidate_ids):,}")
    print(f"  candidate_contact: {_count(cur, 'candidate_contact'):,}")
    print(f"  candidate_skill:    {_count(cur, 'candidate_skill'):,}")
    print(f"  candidate_language: {_count(cur, 'candidate_language'):,}")
    print(f"  assessment:         {_count(cur, 'assessment'):,}\n")

    # -------------------------------------------------------------------
    # Jobs
    # -------------------------------------------------------------------
    print(f"Seeding {NUM_JOBS:,} jobs...")
    job_ids = _seed_jobs(cur, NUM_JOBS)
    print(f"  job_requirement:         {_count(cur, 'job_requirement'):,}")
    print(f"  job_requirement_skill:  {_count(cur, 'job_requirement_skill'):,}")
    print(f"  job_requirement_requirement: {_count(cur, 'job_requirement_requirement'):,}\n")

    # -------------------------------------------------------------------
    # Applications + pipeline events  (the big one)
    # -------------------------------------------------------------------
    print(f"Seeding {NUM_APPLICATIONS:,} applications across full pipeline...")
    app_count, pipeline_count = _seed_applications_and_pipeline(
        cur, candidate_ids, job_ids, NUM_APPLICATIONS
    )
    print(f"  application:           {app_count:,}")
    print(f"  application_pipeline_event: {pipeline_count:,}\n")

    # -------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------
    print("=== FINAL TABLE COUNTS ===")
    for table in [
        "candidate_identity",
        "candidate_contact",
        "candidate_skill",
        "candidate_language",
        "assessment",
        "job_requirement",
        "job_requirement_skill",
        "job_requirement_requirement",
        "application",
        "application_pipeline_event",
    ]:
        cur.execute(f"SELECT count(*) FROM {table}")
        print(f"  {table}: {cur.fetchone()[0]:,}")

    _pipeline_distribution(cur)

    cur.close()
    conn.close()
    print("\nB61 seed completed!")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _ensure_users(cur, n):
    cur.execute("SELECT count(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (actor_type_code, email, is_active, created_by, updated_by) "
            "SELECT 'candidate', 'candidate_' || n || '@example.com', true, 0, 0 "
            "FROM generate_series(1, %s) AS n "
            "ON CONFLICT DO NOTHING",
            (n,),
        )
        cur.connection.commit()
        cur.execute("SELECT count(*) FROM users")
        print(f"  users: {cur.fetchone()[0]:,}")
    else:
        print(f"  users: {_count(cur, 'users'):,}")


def _ensure_employers(cur):
    cur.execute("SELECT count(*) FROM employer_organisation")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO employer_organisation "
            "(tenant_account_id, company_name, type_code, country, is_verified, "
            "mapped_recruiter_count, created_by, updated_by) "
            "SELECT ta.id, 'Company ' || n, 'small', 'IN', true, 0, 0, 0 "
            "FROM tenant_account ta, generate_series(1, 200) AS n "
            "WHERE ta.account_type_code = 'platform' "
            "ON CONFLICT DO NOTHING"
        )
        cur.connection.commit()
        cur.execute("SELECT count(*) FROM employer_organisation WHERE is_verified = true")
        print(f"  employer_organisation: {cur.fetchone()[0]:,}")
    else:
        cur.execute("SELECT count(*) FROM employer_organisation WHERE is_verified = true")
        print(f"  employer_organisation: {_count(cur, 'employer_organisation'):,}")


def _count(cur, table):
    cur.execute(f"SELECT count(*) FROM {table}")
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

def _seed_candidates(cur, n):
    from faker import Faker

    Faker.seed(SEED)

    cur.execute("SELECT count(*) FROM candidate_identity")
    if cur.fetchone()[0] >= n:
        cur.execute("SELECT id FROM candidate_identity ORDER BY id")
        return [r[0] for r in cur.fetchall()]

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        raise SystemExit("No users found - run seed_master_reference.py first")

    rows = []
    batch = []
    for i in range(n):
        locale = random.choice(["en_US", "hi_IN", "es_ES", "fr_FR"])
        f = Faker(locale)
        user_id = random.choice(user_ids)
        batch.append(
            (
                user_id,
                None,
                f.first_name()[:150],
                None,
                f.last_name()[:150],
                None,
                None,
                random.choice(genders) if random.random() > 0.1 else None,
                random.choice(candidate_statuses),
                round(random.uniform(20, 100), 2),
                datetime.now() - timedelta(days=random.randint(0, 365)),
            )
        )
        if len(batch) >= BATCH_SIZE_CANDIDATES:
            psycopg2.extras.execute_values(
                cur,
                (
                    "INSERT INTO candidate_identity "
                    "(user_id, title, first_name, middle_name, last_name, preferred_name, "
                    "date_of_birth, gender, profile_status_code, profile_completion_score, "
                    "latest_login_at) "
                    "VALUES %s ON CONFLICT DO NOTHING"
                ),
                batch,
                page_size=BATCH_SIZE_CANDIDATES,
            )
            batch = []

    if batch:
        psycopg2.extras.execute_values(
            cur,
            (
                "INSERT INTO candidate_identity "
                "(user_id, title, first_name, middle_name, last_name, preferred_name, "
                "date_of_birth, gender, profile_status_code, profile_completion_score, "
                "latest_login_at) "
                "VALUES %s ON CONFLICT DO NOTHING"
            ),
            batch,
            page_size=len(batch),
        )
    cur.connection.commit()

    cur.execute("SELECT id FROM candidate_identity ORDER BY id")
    candidate_ids = [r[0] for r in cur.fetchall()]
    return candidate_ids


def _seed_candidate_contacts(cur, candidate_ids):
    cur.execute("SELECT count(*) FROM candidate_contact")
    if cur.fetchone()[0] > 0:
        return

    rows = []
    for cid in candidate_ids:
        rows.append(
            (
                cid,
                random.choice(contact_types),
                f"candidate_{cid}@example.com",
                "+1234567890",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                True,
                datetime.now(),
                0,
                datetime.now(),
                0,
                None,
            )
        )
        if len(rows) >= 10_000:
            psycopg2.extras.execute_values(
                cur,
                (
                    "INSERT INTO candidate_contact "
                    "(candidate_id, contact_type_code, email, phone, phone_country_code, "
                    "address_line1, address_line2, city, state, country, postal_code, "
                    "is_primary, created_at, created_by, updated_at, updated_by, deleted_at) "
                    "VALUES %s ON CONFLICT DO NOTHING"
                ),
                rows,
                page_size=10_000,
            )
            rows = []
    if rows:
        psycopg2.extras.execute_values(
            cur,
            (
                "INSERT INTO candidate_contact "
                "(candidate_id, contact_type_code, email, phone, phone_country_code, "
                "address_line1, address_line2, city, state, country, postal_code, "
                "is_primary, created_at, created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING"
            ),
            rows,
            page_size=len(rows),
        )
    cur.connection.commit()


def _seed_candidate_skills(cur, candidate_ids):
    cur.execute("SELECT count(*) FROM candidate_skill")
    if cur.fetchone()[0] > 0:
        return

    rows = []
    for cid in candidate_ids:
        for _ in range(random.randint(1, 5)):
            rows.append(
                (
                    cid,
                    random.choice(skill_names),
                    random.choice(proficiencies),
                    round(random.uniform(0, 20), 1),
                    datetime.now(),
                    0,
                    datetime.now(),
                    0,
                    None,
                )
            )
            if len(rows) >= BATCH_SIZE_SKILLS:
                psycopg2.extras.execute_values(
                    cur,
                    (
                        "INSERT INTO candidate_skill "
                        "(candidate_id, skill_name, proficiency, years_of_experience, "
                        "created_at, created_by, updated_at, updated_by, deleted_at) "
                        "VALUES %s ON CONFLICT DO NOTHING"
                    ),
                    rows,
                    page_size=BATCH_SIZE_SKILLS,
                )
                rows = []
    if rows:
        psycopg2.extras.execute_values(
            cur,
            (
                "INSERT INTO candidate_skill "
                "(candidate_id, skill_name, proficiency, years_of_experience, "
                "created_at, created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING"
            ),
            rows,
            page_size=len(rows),
        )
    cur.connection.commit()


def _seed_candidate_languages(cur, candidate_ids):
    cur.execute("SELECT count(*) FROM candidate_language")
    if cur.fetchone()[0] > 0:
        return

    rows = []
    for cid in candidate_ids:
        for _ in range(random.randint(1, 3)):
            rows.append(
                (
                    cid,
                    random.choice(language_names),
                    random.choice(["basic", "intermediate", "advanced"]),
                    random.choice([True, False]),
                    datetime.now(),
                    0,
                    datetime.now(),
                    0,
                    None,
                )
            )
            if len(rows) >= BATCH_SIZE_SKILLS:
                psycopg2.extras.execute_values(
                    cur,
                    (
                        "INSERT INTO candidate_language "
                        "(candidate_id, language_name, proficiency, is_native, "
                        "created_at, created_by, updated_at, updated_by, deleted_at) "
                        "VALUES %s ON CONFLICT DO NOTHING"
                    ),
                    rows,
                    page_size=BATCH_SIZE_SKILLS,
                )
                rows = []
    if rows:
        psycopg2.extras.execute_values(
            cur,
            (
                "INSERT INTO candidate_language "
                "(candidate_id, language_name, proficiency, is_native, "
                "created_at, created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING"
            ),
            rows,
            page_size=len(rows),
        )
    cur.connection.commit()


def _seed_assessments(cur, candidate_ids):
    cur.execute("SELECT count(*) FROM assessment")
    if cur.fetchone()[0] > 0:
        return

    rows = []
    for cid in candidate_ids:
        for _ in range(random.randint(0, 2)):
            rows.append(
                (
                    cid,
                    random.choice(assessment_types),
                    round(random.uniform(40, 100), 2),
                    100,
                    datetime.now() - timedelta(days=random.randint(0, 365)),
                    datetime.now(),
                    0,
                    datetime.now(),
                    0,
                    None,
                )
            )
            if len(rows) >= BATCH_SIZE_SKILLS:
                psycopg2.extras.execute_values(
                    cur,
                    (
                        "INSERT INTO assessment "
                        "(candidate_id, assessment_type_code, score, max_score, "
                        "taken_at, created_at, created_by, updated_at, updated_by, deleted_at) "
                        "VALUES %s ON CONFLICT DO NOTHING"
                    ),
                    rows,
                    page_size=BATCH_SIZE_SKILLS,
                )
                rows = []
    if rows:
        psycopg2.extras.execute_values(
            cur,
            (
                "INSERT INTO assessment "
                "(candidate_id, assessment_type_code, score, max_score, "
                "taken_at, created_at, created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING"
            ),
            rows,
            page_size=len(rows),
        )
    cur.connection.commit()


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def _seed_jobs(cur, n):
    cur.execute("SELECT count(*) FROM job_requirement")
    if cur.fetchone()[0] >= n:
        cur.execute("SELECT id FROM job_requirement ORDER BY id")
        return [r[0] for r in cur.fetchall()]

    # Load reference data needed for job seeding
    cur.execute("SELECT code FROM employment_type ORDER BY id")
    employment_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM work_type ORDER BY id")
    work_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM industry")
    industries = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name FROM job_role")
    job_roles = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'job_status'")
    job_statuses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'job_visibility'")
    job_visibilities = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT id FROM employer_organisation WHERE is_verified = true")
    employer_ids = [r[0] for r in cur.fetchall()]
    if not employer_ids:
        raise SystemExit("No verified employers - run seed_master_reference.py first")

    cur.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        raise SystemExit("No users - run seed_master_reference.py first")

    from faker import Faker

    Faker.seed(SEED + 1)

    # Insert jobs in batches, collecting returned IDs
    job_ids = []
    for start in range(0, n, 5_000):
        end = min(start + 5_000, n)
        batch = []
        for _ in range(end - start):
            f = Faker()
            batch.append(
                (
                    random.choice(employer_ids),
                    random.choice(user_ids),
                    f.job()[:200],
                    f.text(max_nb_chars=400)[:2000],
                    "en",
                    random.choice(employment_types),
                    random.choice(work_types),
                    random.choice(industries),
                    random.choice(job_roles),
                    "Job Location",
                    "State",
                    "IN",
                    None,
                    None,
                    None,
                    None,
                    None,
                    random.choice([True, False]),
                    random.choice([True, False]),
                    random.choice(job_statuses),
                    random.choice(job_visibilities),
                    random.choice(job_statuses),
                    None,
                    None,
                    None,
                    None,
                )
            )
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
                "VALUES %s RETURNING id"
            ),
            batch,
            page_size=5_000,
        )
        batch_ids = [r[0] for r in cur.fetchall()]
        job_ids.extend(batch_ids)
        cur.connection.commit()
        print(f"    jobs inserted so far: {len(job_ids):,}")

    # Job skills + textual requirements
    cur.execute("SELECT id FROM job_requirement ORDER BY id")
    all_job_ids = [r[0] for r in cur.fetchall()]
    
    # Load skill names for job skills
    cur.execute("SELECT name FROM skill")
    skill_names = [r[0] for r in cur.fetchall()]
    
    job_skill_rows = []
    job_req_rows = []
    for jid in all_job_ids:
        for _ in range(random.randint(1, 5)):
            job_skill_rows.append((jid, random.choice(skill_names)))
        for _ in range(random.randint(1, 3)):
            f2 = Faker(SEED + int(jid) % 10000)
            job_req_rows.append((jid, f2.text(max_nb_chars=200)[:500]))

    psycopg2.extras.execute_values(
        cur,
        (
            "INSERT INTO job_requirement_skill "
            "(job_requirement_id, skill_name) "
            "VALUES %s ON CONFLICT DO NOTHING"
        ),
        job_skill_rows,
        page_size=20_000,
    )
    psycopg2.extras.execute_values(
        cur,
        (
            "INSERT INTO job_requirement_requirement "
            "(job_requirement_id, requirement_text) "
            "VALUES %s ON CONFLICT DO NOTHING"
        ),
        job_req_rows,
        page_size=20_000,
    )
    cur.connection.commit()
    return job_ids


# ---------------------------------------------------------------------------
# Applications + pipeline events
# ---------------------------------------------------------------------------

def _seed_applications_and_pipeline(cur, candidate_ids, job_ids, total):
    cur.execute("SELECT count(*) FROM application")
    existing = cur.fetchone()[0]
    if existing >= total:
        print(f"  applications already exist ({existing:,}); skipping")
        cur.execute("SELECT count(*) FROM application_pipeline_event")
        print(f"  pipeline events already exist ({cur.fetchone()[0]:,}); skipping")
        return existing, cur.fetchone()[0]

    # Load reference data needed
    cur.execute("SELECT code FROM reference_code WHERE domain = 'application_channel'")
    application_channels = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'source_channel'")
    source_channels = [r[0] for r in cur.fetchall()]

    # Build weighted stage sampling based on the distribution
    stage_names = [s for s, _ in PIPELINE_STAGES]
    stage_cdf = []
    cumulative = 0.0
    for _, weight in PIPELINE_STAGES:
        cumulative += weight
        stage_cdf.append(cumulative)

    def choose_stage(r):
        """Select a pipeline stage based on the weighted distribution."""
        for i, cutoff in enumerate(stage_cdf):
            if r < cutoff:
                return stage_names[i]
        return stage_names[-1]  # fallback to last stage

    # Pre-pick the application_channel and source_channel lists (same for all)
    app_channels = application_channels if application_channels else ["portal"]
    src_channels = source_channels if source_channels else ["organic"]

    cur.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cur.fetchall()]

    remaining = total - existing
    apps_inserted = 0
    pipeline_inserted = 0

    print(f"    inserting {remaining:,} application+pipeline pairs...")

    # Generate applications using deterministic pairing.
    # Strategy: Distribute applications evenly across the candidate×job matrix.
    # We iterate through candidates, and for each candidate, pick jobs using
    # a hash-based approach that guarantees uniqueness without collision tracking.
    #
    # For candidate i, job selection = hash(i, k) % total_jobs where k is
    # the application number for that candidate. This spreads applications
    # across different jobs for each candidate.
    
    total_candidates = len(candidate_ids)
    total_jobs = len(job_ids)
    
    # Use a deterministic pseudo-random function for job selection
    # This avoids storing state while ensuring good distribution
    def hash_to_job(candidate_idx, app_num):
        """Deterministically map (candidate, app_num) to a job index."""
        # Use a simple hash mixing to spread across job space
        h = (candidate_idx * 2654435761 + app_num * 40503) % total_jobs
        return h
    
    batch_num = 0
    global_app_counter = 0  # Separate counter to avoid mutation during loop
    
    while apps_inserted < remaining:
        batch_apps = []
        batch_pipeline = []
        batch_size = min(BATCH_SIZE_APPLICATIONS, remaining - apps_inserted)
        
        # Generate batch using deterministic pairing
        for i in range(batch_size):
            # Use global_app_counter which doesn't change during the inner loop
            candidate_idx = global_app_counter % total_candidates
            cid = candidate_ids[candidate_idx]
            
            # Calculate which application number this is for this candidate
            app_num_for_candidate = global_app_counter // total_candidates
            
            # Deterministically select job using hash
            job_idx = hash_to_job(candidate_idx, app_num_for_candidate)
            jid = job_ids[job_idx]
            
            global_app_counter += 1
            
            applied_at = datetime.now() - timedelta(days=random.randint(0, 365))
            batch_apps.append(
                (
                    cid,
                    jid,
                    None,
                    applied_at,
                    random.choice(app_channels),
                    applied_at,
                    0,
                    applied_at,
                    0,
                    None,
                )
            )
            
            stage = choose_stage(random.random())
            batch_pipeline.append(
                (
                    None,
                    stage,
                    applied_at + timedelta(days=random.randint(1, 60)),
                    random.choice(user_ids),
                    datetime.now(),
                    0,
                    datetime.now(),
                    0,
                )
            )
        
        if not batch_apps:
            break
        
        # Insert batch
        from psycopg2.extras import execute_values
        
        execute_values(
            cur,
            (
                "INSERT INTO application "
                "(candidate_id, job_requirement_id, resume_version_id, "
                "applied_at, source_channel_code, created_at, created_by, "
                "updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING RETURNING id"
            ),
            batch_apps,
            page_size=len(batch_apps),
        )
        app_rows = cur.fetchall()
        app_ids = [r[0] for r in app_rows]
        
        inserted = len(app_ids)
        apps_inserted += inserted
        
        if inserted:
            pipeline_rows = []
            for idx, app_id in enumerate(app_ids):
                p = batch_pipeline[idx]
                pipeline_rows.append(
                    (app_id, p[1], p[2], p[3], p[4], p[5], p[6], p[7])
                )
            
            execute_values(
                cur,
                (
                    "INSERT INTO application_pipeline_event "
                    "(application_id, pipeline_stage_code, entered_at, "
                    "entered_by_user_id, created_at, created_by, updated_at, "
                    "updated_by) "
                    "VALUES %s"
                ),
                pipeline_rows,
                page_size=len(pipeline_rows),
            )
            pipeline_inserted += inserted
        
        cur.connection.commit()
        batch_num += 1
        
        if apps_inserted % 100_000 == 0 and apps_inserted > 0:
            print(f"    ... {apps_inserted:,}/{remaining:,} applications "
                  f"({pipeline_inserted:,} pipeline events)")

    total_apps = existing + apps_inserted
    print(f"    done: {total_apps:,} applications, {pipeline_inserted:,} pipeline events")
    return total_apps, pipeline_inserted

    total_apps = existing + apps_inserted
    total_pipeline = pipeline_inserted
    print(f"    done: {total_apps:,} applications, {total_pipeline:,} pipeline events")
    return total_apps, total_pipeline


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _pipeline_distribution(cur):
    print("\n=== PIPELINE STAGE DISTRIBUTION ===")
    cur.execute(
        "SELECT pipeline_stage_code, count(*) "
        "FROM application_pipeline_event "
        "GROUP BY pipeline_stage_code "
        "ORDER BY count(*) DESC"
    )
    total = 0
    for stage, cnt in cur.fetchall():
        total += cnt
        print(f"  {stage:16s}: {cnt:,}")
    print(f"  {'TOTAL':16s}: {total:,}")


if __name__ == "__main__":
    main()
