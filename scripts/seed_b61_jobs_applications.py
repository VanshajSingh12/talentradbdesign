#!/usr/bin/env python3
"""
B61 Seed: Jobs and Applications at laptop scale.
Seeds 1000 candidate profiles, 100 job requirements, 5000 applications.
"""
import psycopg2, os, random
from faker import Faker
from datetime import datetime, timedelta
import psycopg2.extras

dsn = os.environ.get('PG_DSN', 'dbname=talentra user=talentradb password=changeme host=localhost port=5431')
conn = psycopg2.connect(dsn)
conn.set_client_encoding('UTF8')
cur = conn.cursor()
random.seed(42)
faker = Faker('en_US')

print('=== B61 Seed ===\n')

# Load reference data from reference_code
cur.execute("SELECT code FROM reference_code WHERE domain = 'candidate_status'")
candidate_statuses = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'gender'")
genders = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'contact_type'")
contact_types = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'assessment_type'")
assessment_types = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'assessment_category'")
assessment_categories = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'job_status'")
job_statuses = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'job_visibility'")
job_visibilities = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'application_channel'")
application_channels = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'proficiency'")
proficiencies = [r[0] for r in cur.fetchall()]
cur.execute("SELECT code FROM reference_code WHERE domain = 'fluency'")
fluencies = [r[0] for r in cur.fetchall()]
cur.execute('SELECT name FROM skill')
skill_names = [r[0] for r in cur.fetchall()]
cur.execute('SELECT name FROM industry')
industries = [r[0] for r in cur.fetchall()]
cur.execute('SELECT name FROM job_role')
job_roles = [r[0] for r in cur.fetchall()]
cur.execute('SELECT name FROM language_lookup')
language_names = [r[0] for r in cur.fetchall()]

# Load employment_type and work_type from their respective tables
cur.execute('SELECT code FROM employment_type ORDER BY id')
employment_types = [r[0] for r in cur.fetchall()]
cur.execute('SELECT code FROM work_type ORDER BY id')
work_types = [r[0] for r in cur.fetchall()]

print('Reference data loaded.\n')

# 1. Tenant account
cur.execute('SELECT count(*) FROM tenant_account')
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO tenant_account (account_type_code, name, status_code, is_active, created_by, updated_by) VALUES ('platform', 'Talentra Platform', 'active', true, 0, 0) ON CONFLICT DO NOTHING")
    conn.commit()
    print('tenant_account: created')

# 2. Users
cur.execute('SELECT count(*) FROM users')
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO users (actor_type_code, email, is_active, created_by, updated_by) SELECT 'candidate', 'candidate_' || n || '@example.com', true, 0, 0 FROM generate_series(1, 100) AS n ON CONFLICT DO NOTHING")
    conn.commit()
    cur.execute('SELECT count(*) FROM users')
    print(f'users: {cur.fetchone()[0]}')
    cur.execute('SELECT id FROM users ORDER BY id')
    user_ids = [r[0] for r in cur.fetchall()]
else:
    cur.execute('SELECT id FROM users ORDER BY id')
    user_ids = [r[0] for r in cur.fetchall()]

# 3. Employer organisations
cur.execute('SELECT count(*) FROM employer_organisation')
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO employer_organisation (tenant_account_id, company_name, type_code, country, is_verified, mapped_recruiter_count, created_by, updated_by) SELECT ta.id, 'Company ' || n, 'small', 'IN', true, 0, 0, 0 FROM tenant_account ta, generate_series(1, 20) AS n WHERE ta.account_type_code = 'platform' ON CONFLICT DO NOTHING")
    conn.commit()
    cur.execute('SELECT count(*) FROM employer_organisation')
    print(f'employer_organisation: {cur.fetchone()[0]}')
    cur.execute('SELECT id FROM employer_organisation WHERE is_verified = true')
    employer_ids = [r[0] for r in cur.fetchall()]
else:
    cur.execute('SELECT id FROM employer_organisation WHERE is_verified = true')
    employer_ids = [r[0] for r in cur.fetchall()]

# 4. Candidates
print('\nSeeding 1000 candidates...')
cur.execute('SELECT count(*) FROM candidate_identity')
if cur.fetchone()[0] == 0:
    candidate_rows = []
    for i in range(1000):
        locale = random.choice(['en_US', 'hi_IN', 'es_ES', 'fr_FR'])
        f = Faker(locale)
        user_id = random.choice(user_ids) if user_ids else None
        candidate_rows.append((
            user_id, None, f.first_name()[:150], None, f.last_name()[:150], None,
            None, random.choice(genders) if random.random() > 0.1 else None,
            random.choice(candidate_statuses), round(random.uniform(20, 100), 2),
            datetime.now() - timedelta(days=random.randint(0, 365))
        ))
    psycopg2.extras.execute_values(cur, 'INSERT INTO candidate_identity (user_id, title, first_name, middle_name, last_name, preferred_name, date_of_birth, gender, profile_status_code, profile_completion_score, latest_login_at) VALUES %s', candidate_rows)
    conn.commit()
    cur.execute('SELECT count(*) FROM candidate_identity')
    print(f'  candidate_identity: {cur.fetchone()[0]}')

# 5. Candidate contacts
print('Seeding candidate_contact...')
cur.execute('SELECT count(*) FROM candidate_contact')
if cur.fetchone()[0] == 0:
    cur.execute('SELECT id FROM candidate_identity')
    candidate_ids = [r[0] for r in cur.fetchall()]
    contact_rows = []
    for cid in candidate_ids:
        contact_rows.append((cid, random.choice(contact_types), f'candidate_{cid}@example.com', '+1234567890', None, faker.street_address()[:200], None, faker.city()[:100], None, None, None, True, datetime.now(), 0, datetime.now(), 0, None))
    psycopg2.extras.execute_values(cur, 'INSERT INTO candidate_contact (candidate_id, contact_type_code, email, phone, phone_country_code, address_line1, address_line2, city, state, country, postal_code, is_primary, created_at, created_by, updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING', contact_rows)
    conn.commit()
    cur.execute('SELECT count(*) FROM candidate_contact')
    print(f'  candidate_contact: {cur.fetchone()[0]}')

# 6. Candidate skills
print('Seeding candidate_skill...')
cur.execute('SELECT count(*) FROM candidate_skill')
if cur.fetchone()[0] == 0:
    cur.execute('SELECT id FROM candidate_identity')
    candidate_ids = [r[0] for r in cur.fetchall()]
    skill_rows = []
    for cid in candidate_ids:
        for _ in range(random.randint(1, 5)):
            skill_rows.append((cid, random.choice(skill_names), random.choice(proficiencies), round(random.uniform(0, 20), 1), datetime.now(), 0, datetime.now(), 0, None))
    psycopg2.extras.execute_values(cur, 'INSERT INTO candidate_skill (candidate_id, skill_name, proficiency, years_of_experience, created_at, created_by, updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING', skill_rows)
    conn.commit()
    cur.execute('SELECT count(*) FROM candidate_skill')
    print(f'  candidate_skill: {cur.fetchone()[0]}')

# 7. Candidate languages
print('Seeding candidate_language...')
cur.execute('SELECT count(*) FROM candidate_language')
if cur.fetchone()[0] == 0:
    cur.execute('SELECT id FROM candidate_identity')
    candidate_ids = [r[0] for r in cur.fetchall()]
    lang_rows = []
    for cid in candidate_ids:
        for _ in range(random.randint(1, 3)):
            lang_rows.append((cid, random.choice(language_names), random.choice(['basic', 'intermediate', 'advanced']), random.choice([True, False]), datetime.now(), 0, datetime.now(), 0, None))
    psycopg2.extras.execute_values(cur, 'INSERT INTO candidate_language (candidate_id, language_name, proficiency, is_native, created_at, created_by, updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING', lang_rows)
    conn.commit()
    cur.execute('SELECT count(*) FROM candidate_language')
    print(f'  candidate_language: {cur.fetchone()[0]}')

# 8. Assessments
print('Seeding assessment...')
cur.execute('SELECT count(*) FROM assessment')
if cur.fetchone()[0] == 0:
    cur.execute('SELECT id FROM candidate_identity')
    candidate_ids = [r[0] for r in cur.fetchall()]
    assess_rows = []
    for cid in candidate_ids:
        for _ in range(random.randint(0, 2)):
            assess_rows.append((cid, random.choice(assessment_types), round(random.uniform(40, 100), 2), 100, datetime.now() - timedelta(days=random.randint(0, 365)), datetime.now(), 0, datetime.now(), 0, None))
    psycopg2.extras.execute_values(cur, 'INSERT INTO assessment (candidate_id, assessment_type_code, score, max_score, taken_at, created_at, created_by, updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING', assess_rows)
    conn.commit()
    cur.execute('SELECT count(*) FROM assessment')
    print(f'  assessment: {cur.fetchone()[0]}')

# 9. Jobs
print('\nSeeding 100 jobs...')
cur.execute('SELECT count(*) FROM job_requirement')
if cur.fetchone()[0] == 0:
    job_rows = []
    for i in range(100):
        employer_id = random.choice(employer_ids) if employer_ids else None
        recruiter_id = random.choice(user_ids) if user_ids else None
        job_rows.append((
            employer_id, recruiter_id, faker.job()[:200], faker.text(max_nb_chars=400)[:2000], 'en',
            random.choice(employment_types), random.choice(work_types),
            random.choice(industries), random.choice(job_roles),
            'Job Location', 'State', 'IN',  # location_city, location_state, location_country
            None, None, None,  # compensation_min, compensation_max, compensation_currency_code
            None, None,  # experience_min_years, experience_max_years
            random.choice([True, False]), random.choice([True, False]),  # is_remote_allowed, is_open_to_consultants
            random.choice(job_statuses), random.choice(job_visibilities), random.choice(job_statuses),  # status, visibility, publish_state
            None, None, None, None  # deadline, published, unpublished, closed
        ))
    psycopg2.extras.execute_values(cur, 'INSERT INTO job_requirement (employer_organisation_id, recruiter_user_id, title, description, description_language, employment_type_code, work_type_code, industry_name, job_role_name, location_city, location_state, location_country, compensation_min, compensation_max, compensation_currency_code, experience_min_years, experience_max_years, is_remote_allowed, is_open_to_consultants, status_code, visibility_code, publish_state_code, deadline_at, published_at, unpublished_at, closed_at) VALUES %s RETURNING id', job_rows)
    job_ids = [r[0] for r in cur.fetchall()]
    
    job_skill_rows = []
    job_req_rows = []
    for job_id in job_ids:
        for _ in range(random.randint(1, 5)):
            job_skill_rows.append((job_id, random.choice(skill_names)))
        for _ in range(random.randint(1, 3)):
            job_req_rows.append((job_id, faker.text(max_nb_chars=200)[:500]))
    
    psycopg2.extras.execute_values(cur, 'INSERT INTO job_requirement_skill (job_requirement_id, skill_name) VALUES %s ON CONFLICT DO NOTHING', job_skill_rows)
    psycopg2.extras.execute_values(cur, 'INSERT INTO job_requirement_requirement (job_requirement_id, requirement_text) VALUES %s ON CONFLICT DO NOTHING', job_req_rows)
    conn.commit()
    cur.execute('SELECT count(*) FROM job_requirement')
    print(f'  job_requirement: {cur.fetchone()[0]}')
    cur.execute('SELECT count(*) FROM job_requirement_skill')
    print(f'  job_requirement_skill: {cur.fetchone()[0]}')
    cur.execute('SELECT count(*) FROM job_requirement_requirement')
    print(f'  job_requirement_requirement: {cur.fetchone()[0]}')

# 10. Applications
print('\nSeeding 5000 applications...')
cur.execute('SELECT count(*) FROM application')
if cur.fetchone()[0] == 0:
    cur.execute('SELECT id FROM candidate_identity ORDER BY random() LIMIT 500')
    candidate_ids = [r[0] for r in cur.fetchall()]
    cur.execute('SELECT id FROM job_requirement ORDER BY random() LIMIT 50')
    job_ids = [r[0] for r in cur.fetchall()]
    
    app_rows = []
    for i in range(5000):
        candidate_id = random.choice(candidate_ids)
        job_id = random.choice(job_ids)
        applied_at = datetime.now() - timedelta(days=random.randint(0, 365))
        app_rows.append((candidate_id, job_id, None, random.choice(application_channels), applied_at, datetime.now(), 0, datetime.now(), 0, None))
    
    psycopg2.extras.execute_values(cur, 'INSERT INTO application (candidate_id, job_requirement_id, resume_version_id, source_channel_code, applied_at, created_at, created_by, updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING', app_rows)
    conn.commit()
    cur.execute('SELECT count(*) FROM application')
    print(f'  application: {cur.fetchone()[0]}')

# Final summary
print('\n=== FINAL TABLE COUNTS ===')
for table in ['candidate_identity', 'candidate_contact', 'candidate_skill', 'candidate_language', 'assessment', 'employer_organisation', 'job_requirement', 'job_requirement_skill', 'job_requirement_requirement', 'application']:
    cur.execute(f'SELECT count(*) FROM {table}')
    print(f'  {table}: {cur.fetchone()[0]}')

cur.close()
conn.close()
print('\nB61 seed completed!')
