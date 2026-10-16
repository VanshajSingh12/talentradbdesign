#!/usr/bin/env python3
"""
Talentra master reference seed - B60 first half.

Seeds the reference/lookup domains that every other module depends on:
- reference_code (all enum domains the schema references)
- country / state / city
- skill / industry / job_role
- employment_type / work_type
- language_lookup
- qualification (links to education_level reference_code)
- ui_translation (English default strings for every reference key in use)

Run against the connected postgres with:
  PG_DSN=postgres://talentradb:changeme@localhost:5431/talentra python scripts/seed_master_reference.py

All inserts are idempotent: a second run is a no-op.
"""

import os
import sys
import psycopg2
import psycopg2.extras


def dsn():
    return os.environ.get("PG_DSN", "dbname=talentra user=talentradb password=changeme host=localhost port=5431")


def insert_many(cur, sql, rows, page_size=5000):
    if not rows:
        return 0
    psycopg2.extras.execute_values(cur, sql, rows, page_size=page_size)
    return len(rows)


def now():
    return "now()"


REFERENCE_CODE_DOMAINS = {
    "candidate_status": [
        ("active", "candidate.status.active", 10),
        ("inactive", "candidate.status.inactive", 20),
        ("pending", "candidate.status.pending", 30),
        ("suspended", "candidate.status.suspended", 40),
    ],
    "profile_type": [
        ("permanent", "profile.type.permanent", 10),
        ("temporary", "profile.type.temporary", 20),
        ("gig", "profile.type.gig", 30),
    ],
    "contact_type": [
        ("email", "contact.type.email", 10),
        ("phone", "contact.type.phone", 20),
        ("linkedin", "contact.type.linkedin", 30),
    ],
    "gender": [
        ("male", "gender.male", 10),
        ("female", "gender.female", 20),
        ("non_binary", "gender.non_binary", 30),
        ("prefer_not_to_say", "gender.prefer_not_to_say", 40),
    ],
    "education_level": [
        ("secondary", "education.level.secondary", 10),
        ("undergraduate", "education.level.undergraduate", 20),
        ("postgraduate", "education.level.postgraduate", 30),
        ("doctorate", "education.level.doctorate", 40),
    ],
    "assessment_type": [
        ("aptitude", "assessment.type.aptitude", 10),
        ("technical", "assessment.type.technical", 20),
        ("behavioral", "assessment.type.behavioral", 30),
    ],
    "assessment_category": [
        ("reasoning", "assessment.category.reasoning", 10),
        ("coding", "assessment.category.coding", 20),
        ("communication", "assessment.category.communication", 30),
    ],
    "course_category": [
        ("technical", "course.category.technical", 10),
        ("management", "course.category.management", 20),
        ("certification", "course.category.certification", 30),
    ],
    "course_level": [
        ("beginner", "course.level.beginner", 10),
        ("intermediate", "course.level.intermediate", 20),
        ("advanced", "course.level.advanced", 30),
    ],
    "enrolment_status": [
        ("enrolled", "enrolment.status.enrolled", 10),
        ("completed", "enrolment.status.completed", 20),
        ("dropped", "enrolment.status.dropped", 30),
    ],
    "project_type": [
        ("candidate", "project.type.candidate", 10),
        ("gig", "project.type.gig", 20),
    ],
    "proficiency": [
        ("basic", "proficiency.basic", 10),
        ("intermediate", "proficiency.intermediate", 20),
        ("advanced", "proficiency.advanced", 30),
        ("expert", "proficiency.expert", 40),
    ],
    "skill_source": [
        ("self", "skill.source.self", 10),
        ("assessment", "skill.source.assessment", 20),
    ],
    "fluency": [
        ("basic", "fluency.basic", 10),
        ("conversational", "fluency.conversational", 20),
        ("fluent", "fluency.fluent", 30),
    ],
    "language_proficiency": [
        ("basic", "language_proficiency.basic", 10),
        ("working", "language_proficiency.working", 20),
        ("proficient", "language_proficiency.proficient", 30),
    ],
    "activity_type": [
        ("login", "activity.login", 10),
        ("profile_update", "activity.profile_update", 20),
        ("resume_download", "activity.resume_download", 30),
    ],
    "shortlist_action": [
        ("added", "shortlist.action.added", 10),
        ("removed", "shortlist.action.removed", 20),
    ],
    "referral_type": [("candidate", "referral.type.candidate", 10)],
    "referral_status": [
        ("pending", "referral.status.pending", 10),
        ("hired", "referral.status.hired", 20),
    ],
    "job_status": [
        ("draft", "job_status.draft", 10),
        ("published", "job_status.published", 20),
        ("closed", "job_status.closed", 30),
    ],
    "job_visibility": [
        ("public", "job_visibility.public", 10),
        ("private", "job_visibility.private", 20),
    ],
    "question_type": [
        ("text", "question.type.text", 10),
        ("multiple_choice", "question.type.multiple_choice", 20),
    ],
    "credential_type": [("password", "credential.type.password", 10)],
    "credential_status": [
        ("active", "credential.status.active", 10),
        ("locked", "credential.status.locked", 20),
    ],
    "account_type": [
        ("platform", "account.type.platform", 10),
        ("employer", "account.type.employer", 20),
    ],
    "account_status": [("active", "account.status.active", 10)],
    "role": [
        ("super_admin", "role.super_admin", 10),
        ("admin", "role.admin", 20),
        ("account_admin", "role.account_admin", 30),
        ("candidate", "role.candidate", 40),
        ("employer", "role.employer", 50),
        ("recruiter", "role.recruiter", 60),
        ("consultant", "role.consultant", 70),
    ],
    "permission": [
        ("manage_users", "perm.manage_users", 10),
        ("manage_jobs", "perm.manage_jobs", 20),
        ("view_candidates", "perm.view_candidates", 30),
        ("post_jobs", "perm.post_jobs", 40),
    ],
    "licence_type": [
        ("standard", "licence.type.standard", 10),
        ("enterprise", "licence.type.enterprise", 20),
    ],
    "licence_status": [("active", "licence.status.active", 10)],
    "device_type": [
        ("desktop", "device.type.desktop", 10),
        ("mobile", "device.type.mobile", 20),
    ],
    "revocation_reason": [("user_request", "revocation.reason.user_request", 10)],
    "plan_category": [
        ("free", "plan.category.free", 10),
        ("paid", "plan.category.paid", 20),
    ],
    "billing_period": [("monthly", "billing.period.monthly", 10)],
    "renewal_type": [("auto", "renewal.type.auto", 10)],
    "entitlement_unit": [("count", "entitlement.unit.count", 10)],
    "payment_method": [("card", "payment.method.card", 10)],
    "payment_status": [
        ("initiated", "payment.status.initiated", 10),
        ("completed", "payment.status.completed", 20),
    ],
    "invoice_status": [("issued", "invoice.status.issued", 10)],
    "refund_status": [("requested", "refund.status.requested", 10)],
    "refund_type": [("full", "refund.type.full", 10)],
    "wallet_status": [("active", "wallet.status.active", 10)],
    "wallet_transaction_type": [
        ("recharge", "wallet.tx.recharge", 10),
        ("debit", "wallet.tx.debit", 20),
    ],
    "wallet_reference_type": [("payment_order", "wallet.ref.payment_order", 10)],
    "download_format": [("pdf", "download.format.pdf", 10)],
    "subscription_status": [
        ("trial", "subscription.status.trial", 10),
        ("active", "subscription.status.active", 20),
    ],
    "notification_channel": [("email", "notification.channel.email", 10)],
    "notification_type": [("job_alert", "notification.type.job_alert", 10)],
    "alert_frequency": [
        ("immediate", "alert.frequency.immediate", 10),
        ("daily", "alert.frequency.daily", 20),
    ],
    "setting_type": [("boolean", "setting.type.boolean", 10)],
    "community_type": [("discussion", "community.type.discussion", 10)],
    "post_visibility": [("public", "post.visibility.public", 10)],
    "reaction_type": [("like", "reaction.type.like", 10)],
    "support_category": [("billing", "support.category.billing", 10)],
    "support_priority": [("low", "support.priority.low", 10)],
    "support_status": [("open", "support.status.open", 10)],
    "faq_category": [("general", "faq.category.general", 10)],
    "outreach_channel": [("email", "outreach.channel.email", 10)],
    "delivery_status": [
        ("pending", "delivery.status.pending", 10),
        ("sent", "delivery.status.sent", 20),
    ],
    "gig_worker_status": [("active", "gig_worker.status.active", 10)],
    "rate_time_unit": [("hour", "rate.time.hour", 10)],
    "handoff_system": [("external_fulfillment", "handoff.system.external_fulfillment", 10)],
    "fulfillment_status": [("pending", "fulfillment.status.pending", 10)],
    "pricing_model": [
        ("fixed", "pricing.model.fixed", 10),
        ("rate", "pricing.model.rate", 20),
    ],
    "earnings_type": [("estimated", "earnings.type.estimated", 10)],
    "source_system": [("external_fulfillment", "source.system.external_fulfillment", 10)],
    "employer_organisation_size": [("small", "employer_organisation.size.small", 10)],
    "consultant_decision_type": [("accepted", "consultant_decision.type.accepted", 10)],
    "sourcing_status": [("open", "sourcing.status.open", 10)],
    "pipeline_stage": [
        ("applied", "pipeline.stage.applied", 10),
        ("shortlisted", "pipeline.stage.shortlisted", 20),
        ("interviewed", "pipeline.stage.interviewed", 30),
        ("offered", "pipeline.stage.offered", 40),
        ("joined", "pipeline.stage.joined", 50),
        ("rejected", "pipeline.stage.rejected", 60),
    ],
    "source_channel": [
        ("organic", "source.channel.organic", 10),
        ("referral", "source.channel.referral", 20),
    ],
    "application_channel": [("portal", "application.channel.portal", 10)],
    "institution_type": [("university", "institution.type.university", 10)],
    "recruiter_mapping_type": [("direct", "recruiter_mapping.type.direct", 10)],
    "account_admin_role": [("owner", "account_admin.role.owner", 10)],
    "employer_type": [
        ("small", "employer.type.small", 10),
        ("medium", "employer.type.medium", 20),
    ],
    "company_size": [("1_to_10", "company.size.1_to_10", 10)],
    "seat_status": [("allocated", "seat.status.allocated", 10)],
    "tax_identifier_type": [("tax_id", "tax_identifier.type.tax_id", 10)],
    "verification_type": [("identity", "verification.type.identity", 10)],
    "verification_status": [("pending", "verification.status.pending", 10)],
    "login_result": [
        ("success", "login.result.success", 10),
        ("failed", "login.result.failed", 20),
    ],
    "event_type": [("login", "event.login", 10)],
    "blocked_party_type": [("candidate", "blocked_party.candidate", 10)],
    "entitlement_code": [
        ("job_posts", "entitlement.job_posts", 10),
        ("downloads", "entitlement.downloads", 20),
    ],
}


def load_reference_codes(cur):
    rows = []
    for domain, items in REFERENCE_CODE_DOMAINS.items():
        for code, display_name_key, sort_order in items:
            rows.append((domain, code, display_name_key, True, sort_order))
    return insert_many(
        cur,
        """
        INSERT INTO reference_code(domain, code, display_name_key, is_active, sort_order)
        VALUES %s
        ON CONFLICT DO NOTHING
        """,
        rows,
    )


COUNTRIES = [
    ("US", "USA", "United States", "840"),
    ("IN", "IND", "India", "356"),
    ("GB", "GBR", "United Kingdom", "826"),
    ("CA", "CAN", "Canada", "124"),
    ("AU", "AUS", "Australia", "36"),
    ("DE", "DEU", "Germany", "276"),
    ("FR", "FRA", "France", "250"),
    ("ES", "ESP", "Spain", "724"),
    ("BR", "BRA", "Brazil", "76"),
    ("AE", "ARE", "United Arab Emirates", "784"),
    ("SG", "SGP", "Singapore", "702"),
    ("JP", "JPN", "Japan", "392"),
    ("CN", "CHN", "China", "156"),
    ("KR", "KOR", "South Korea", "410"),
]


def load_countries(cur):
    existing = set()
    cur.execute("SELECT iso_alpha2 FROM country")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        (iso2, iso3, name, num, True, 0, now(), 0, now(), 0)
        for iso2, iso3, name, num in COUNTRIES
        if iso2 not in existing
    ]
    return insert_many(
        cur,
        """
        INSERT INTO country(iso_alpha2, iso_alpha3, name, iso_numeric, is_active, sort_order,
                            created_at, created_by, updated_at, updated_by)
        VALUES %s
        """,
        tups,
    )


def load_states(cur, country_by_iso):
    countries_states = [
        ("US", "California"),
        ("US", "Texas"),
        ("US", "New York"),
        ("US", "Illinois"),
        ("IN", "Maharashtra"),
        ("IN", "Karnataka"),
        ("IN", "Delhi"),
        ("IN", "Tamil Nadu"),
        ("GB", "England"),
        ("GB", "Scotland"),
        ("CA", "Ontario"),
        ("CA", "British Columbia"),
        ("AU", "New South Wales"),
        ("AU", "Victoria"),
        ("DE", "Bavaria"),
        ("DE", "North Rhine-Westphalia"),
        ("FR", "Ile-de-France"),
        ("FR", "Provence-Alpes-Cote d'Azur"),
        ("ES", "Catalonia"),
        ("ES", "Madrid"),
        ("BR", "Sao Paulo"),
        ("BR", "Rio de Janeiro"),
        ("AE", "Dubai"),
        ("AE", "Abu Dhabi"),
        ("SG", "Singapore"),
        ("JP", "Tokyo"),
        ("CN", "Shanghai"),
        ("KR", "Seoul"),
    ]
    existing = set()
    cur.execute("SELECT country_id, name FROM state")
    for row in cur.fetchall():
        existing.add((row[0], row[1]))
    rows = []
    for country_iso, state_name in countries_states:
        country_id = country_by_iso.get(country_iso)
        if country_id is None:
            continue
        if (country_id, state_name) in existing:
            continue
        rows.append((country_id, state_name, True, 0, now(), 0, now(), 0))
    return insert_many(
        cur,
        """
        INSERT INTO state(country_id, name, is_active, sort_order, created_at, created_by,
                          updated_at, updated_by)
        VALUES %s
        """,
        rows,
    )


def load_cities(cur, country_by_iso, state_by_country_and_name):
    cities = [
        ("US", "California", "San Francisco"),
        ("US", "California", "Los Angeles"),
        ("US", "Texas", "Austin"),
        ("US", "Texas", "Dallas"),
        ("US", "New York", "New York"),
        ("IN", "Maharashtra", "Mumbai"),
        ("IN", "Karnataka", "Bengaluru"),
        ("IN", "Delhi", "New Delhi"),
        ("IN", "Tamil Nadu", "Chennai"),
        ("GB", "England", "London"),
        ("GB", "Scotland", "Edinburgh"),
        ("CA", "Ontario", "Toronto"),
        ("CA", "British Columbia", "Vancouver"),
        ("AU", "New South Wales", "Sydney"),
        ("AU", "Victoria", "Melbourne"),
        ("DE", "Bavaria", "Munich"),
        ("DE", "North Rhine-Westphalia", "Cologne"),
        ("FR", "Ile-de-France", "Paris"),
        ("FR", "Provence-Alpes-Cote d'Azur", "Nice"),
        ("ES", "Catalonia", "Barcelona"),
        ("ES", "Madrid", "Madrid"),
        ("BR", "Sao Paulo", "Sao Paulo"),
        ("BR", "Rio de Janeiro", "Rio de Janeiro"),
        ("AE", "Dubai", "Dubai"),
        ("AE", "Abu Dhabi", "Abu Dhabi"),
        ("SG", "Singapore", "Singapore"),
        ("JP", "Tokyo", "Tokyo"),
        ("CN", "Shanghai", "Shanghai"),
        ("KR", "Seoul", "Seoul"),
    ]
    existing = set()
    cur.execute("SELECT country_id, name FROM city")
    for row in cur.fetchall():
        existing.add((row[0], row[1]))
    rows = []
    for country_iso, state_name, city_name in cities:
        country_id = country_by_iso.get(country_iso)
        if country_id is None:
            continue
        key = (country_id, state_name)
        state_id = state_by_country_and_name.get(key)
        if (country_id, city_name) in existing:
            continue
        rows.append((
            country_id,
            state_id,
            city_name,
            None, None, None, None,
            True, 0, now(), 0, now(), 0,
        ))
    return insert_many(
        cur,
        """
        INSERT INTO city(country_id, state_id, name, latitude, longitude, coordinates_source,
                         timezone, is_active, sort_order, created_at, created_by,
                         updated_at, updated_by)
        VALUES %s
        """,
        rows,
    )


SKILLS = [
    ("Python", "Programming"),
    ("Java", "Programming"),
    ("JavaScript", "Programming"),
    ("TypeScript", "Programming"),
    ("C#", "Programming"),
    ("C++", "Programming"),
    ("Go", "Programming"),
    ("Rust", "Programming"),
    ("SQL", "Data"),
    ("PostgreSQL", "Data"),
    ("MySQL", "Data"),
    ("Oracle", "Data"),
    ("MongoDB", "Data"),
    ("Redis", "Data"),
    ("Elasticsearch", "Data"),
    ("Kubernetes", "Infrastructure"),
    ("Docker", "Infrastructure"),
    ("Terraform", "Infrastructure"),
    ("Ansible", "Infrastructure"),
    ("AWS", "Cloud"),
    ("Azure", "Cloud"),
    ("GCP", "Cloud"),
    ("React", "Frontend"),
    ("Angular", "Frontend"),
    ("Vue.js", "Frontend"),
    ("Node.js", "Backend"),
    ("Django", "Backend"),
    ("Flask", "Backend"),
    ("Spring Boot", "Backend"),
    ("Data Engineering", "Data"),
    ("Machine Learning", "Data"),
    ("DevOps", "Infrastructure"),
    ("Project Management", "Management"),
    ("Agile", "Process"),
    ("Scrum", "Process"),
    ("Communication", "Soft Skills"),
    ("Leadership", "Soft Skills"),
    ("SQL Server", "Data"),
]


def load_skills(cur):
    existing = set()
    cur.execute("SELECT name, is_active FROM skill")
    for row in cur.fetchall():
        existing.add((row[0], bool(row[1])))
    tups = [
        (name, category, True, 0, now(), 0, now(), 0)
        for name, category in SKILLS
        if (name, True) not in existing
    ]
    return insert_many(
        cur,
        """
        INSERT INTO skill(name, category, is_active, sort_order, created_at, created_by,
                          updated_at, updated_by)
        VALUES %s
        """,
        tups,
    )


INDUSTRIES = [
    "Technology",
    "Financial Services",
    "Healthcare",
    "Consulting",
    "Retail",
    "Manufacturing",
    "Media",
    "Education",
    "Logistics",
    "Real Estate",
    "Telecom",
    "Construction",
    "Energy",
    "Pharmaceuticals",
    "Hospitality",
]


def load_industries(cur):
    existing = set()
    cur.execute("SELECT name FROM industry")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        (name, True, 0, now(), 0, now(), 0)
        for name in INDUSTRIES
        if name not in existing
    ]
    return insert_many(
        cur,
        """
        INSERT INTO industry(name, is_active, sort_order, created_at, created_by,
                             updated_at, updated_by)
        VALUES %s
        """,
        tups,
    )


JOB_ROLES = [
    "Software Engineer",
    "Data Engineer",
    "DevOps Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "AI / ML Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
    "Solution Architect",
    "Product Manager",
    "Project Manager",
    "Business Analyst",
    "Recruiter",
    "Talent Acquisition Partner",
    "Technical Recruiter",
    "Consultant",
    "Account Manager",
    "Sales Engineer",
    "Cloud Engineer",
    "Security Engineer",
    "Database Administrator",
    "QA Engineer",
    "UX Designer",
    "Scrum Master",
]


def load_job_roles(cur):
    existing = set()
    cur.execute("SELECT name FROM job_role")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        (name, True, 0, now(), 0, now(), 0)
        for name in JOB_ROLES
        if name not in existing
    ]
    return insert_many(
        cur,
        """
        INSERT INTO job_role(name, is_active, sort_order, created_at, created_by,
                             updated_at, updated_by)
        VALUES %s
        """,
        tups,
    )


def load_employment_types(cur):
    existing = set()
    cur.execute("SELECT code FROM employment_type")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        ("full_time", "employment_type.full_time", True, 10, now(), 0, now(), 0),
        ("part_time", "employment_type.part_time", True, 20, now(), 0, now(), 0),
        ("contract", "employment_type.contract", True, 30, now(), 0, now(), 0),
        ("internship", "employment_type.internship", True, 40, now(), 0, now(), 0),
    ]
    new_tups = [t for t in tups if t[0] not in existing]
    return insert_many(
        cur,
        """
        INSERT INTO employment_type(code, display_name_key, is_active, sort_order,
                                    created_at, created_by, updated_at, updated_by)
        VALUES %s
        """,
        new_tups,
    )


def load_work_types(cur):
    existing = set()
    cur.execute("SELECT code FROM work_type")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        ("onsite", "work_type.onsite", True, 10, now(), 0, now(), 0),
        ("remote", "work_type.remote", True, 20, now(), 0, now(), 0),
        ("hybrid", "work_type.hybrid", True, 30, now(), 0, now(), 0),
    ]
    new_tups = [t for t in tups if t[0] not in existing]
    return insert_many(
        cur,
        """
        INSERT INTO work_type(code, display_name_key, is_active, sort_order, created_at,
                              created_by, updated_at, updated_by)
        VALUES %s
        """,
        new_tups,
    )


LANGUAGES = [
    ("en", "eng", "English"),
    ("hi", "hin", "Hindi"),
    ("es", "spa", "Spanish"),
    ("fr", "fra", "French"),
    ("de", "deu", "German"),
    ("zh", "zho", "Chinese"),
    ("ja", "jpn", "Japanese"),
    ("ar", "ara", "Arabic"),
    ("pt", "por", "Portuguese"),
    ("ru", "rus", "Russian"),
    ("ko", "kor", "Korean"),
    ("it", "ita", "Italian"),
]


def load_languages(cur):
    existing = set()
    cur.execute("SELECT iso_639_1 FROM language_lookup")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        (iso_639_1, iso_639_3, name, True, idx * 10 + 10, now(), 0, now(), 0)
        for idx, (iso_639_1, iso_639_3, name) in enumerate(LANGUAGES)
        if iso_639_1 not in existing
    ]
    return insert_many(
        cur,
        """
        INSERT INTO language_lookup(iso_639_1, iso_639_3, name, is_active, sort_order,
                                    created_at, created_by, updated_at, updated_by)
        VALUES %s
        """,
        tups,
    )


QUALIFICATIONS = [
    ("BA", "Bachelor of Arts", "undergraduate"),
    ("BSc", "Bachelor of Science", "undergraduate"),
    ("BEng", "Bachelor of Engineering", "undergraduate"),
    ("BCom", "Bachelor of Commerce", "undergraduate"),
    ("MA", "Master of Arts", "postgraduate"),
    ("MBA", "Master of Business Administration", "postgraduate"),
    ("MSc", "Master of Science", "postgraduate"),
    ("MEng", "Master of Engineering", "postgraduate"),
    ("PhD", "Doctor of Philosophy", "doctorate"),
    ("Diploma", "Diploma", "secondary"),
    ("Certificate", "Certificate", "secondary"),
]


def load_qualifications(cur, education_level_by_code):
    rows = []
    for code, name, education_level in QUALIFICATIONS:
        edu_code = education_level_by_code.get(education_level)
        if edu_code is None:
            continue
        rows.append((code, name, edu_code, True, 0, now(), 0, now(), 0))
    n = len(rows)
    if n == 0:
        print("[WARN] load_qualifications: no rows to insert (education_level codes missing)")
        return 0
    edu_codes = {r[2] for r in rows}
    cur.execute("SELECT code FROM reference_code WHERE code = ANY(%s) AND domain = 'education_level'", (list(edu_codes),))
    valid_codes = {row[0] for row in cur.fetchall()}
    if valid_codes != edu_codes:
        missing = edu_codes - valid_codes
        print(f"[WARN] load_qualifications: edu_codes not present in reference_code(domain='education_level'): {sorted(missing)}")
        print(f"[WARN] load_qualifications: skipping insert to avoid FK violation")
        return 0
    cur.execute("SELECT code FROM qualification WHERE code = ANY(%s)", ([r[0] for r in rows],))
    existing_codes = {row[0] for row in cur.fetchall()}
    new_rows = [r for r in rows if r[0] not in existing_codes]
    if not new_rows:
        print("[SKIP] load_qualifications: all qualification codes already exist")
        return 0
    return insert_many(
        cur,
        """
        INSERT INTO qualification(code, name, education_level_code, is_active, sort_order,
                                  created_at, created_by, updated_at, updated_by)
        VALUES %s
        """,
        new_rows,
    )


UI_TRANSLATIONS = [
    ("candidate.status.active", "Active"),
    ("candidate.status.inactive", "Inactive"),
    ("candidate.status.pending", "Pending"),
    ("candidate.status.suspended", "Suspended"),
    ("profile.type.permanent", "Permanent"),
    ("profile.type.gig", "Gig"),
    ("profile.type.temporary", "Temporary"),
    ("contact.type.email", "Email"),
    ("contact.type.phone", "Phone"),
    ("contact.type.linkedin", "LinkedIn"),
    ("gender.male", "Male"),
    ("gender.female", "Female"),
    ("gender.non_binary", "Non-binary"),
    ("gender.prefer_not_to_say", "Prefer not to say"),
    ("education.level.secondary", "Secondary"),
    ("education.level.undergraduate", "Undergraduate"),
    ("education.level.postgraduate", "Postgraduate"),
    ("education.level.doctorate", "Doctorate"),
    ("project.type.candidate", "Candidate project"),
    ("project.type.gig", "Gig project"),
    ("proficiency.basic", "Basic"),
    ("proficiency.intermediate", "Intermediate"),
    ("proficiency.advanced", "Advanced"),
    ("proficiency.expert", "Expert"),
    ("skill_source.self", "Self-declared"),
    ("skill_source.assessment", "Assessment"),
    ("fluency.basic", "Basic"),
    ("fluency.conversational", "Conversational"),
    ("fluency.fluent", "Fluent"),
    ("language_proficiency.basic", "Basic"),
    ("language_proficiency.working", "Working"),
    ("language_proficiency.proficient", "Proficient"),
    ("activity.login", "Login"),
    ("activity.profile_update", "Profile update"),
    ("activity.resume_download", "Resume download"),
    ("shortlist_action.added", "Added"),
    ("shortlist_action.removed", "Removed"),
    ("referral.type.candidate", "Candidate"),
    ("referral.status.pending", "Pending"),
    ("referral.status.hired", "Hired"),
    ("job_status.draft", "Draft"),
    ("job_status.published", "Published"),
    ("job_status.closed", "Closed"),
    ("job_visibility.public", "Public"),
    ("job_visibility.private", "Private"),
    ("question_type.text", "Text"),
    ("question_type.multiple_choice", "Multiple choice"),
    ("credential_type.password", "Password"),
    ("credential_status.active", "Active"),
    ("credential_status.locked", "Locked"),
    ("account_type.platform", "Platform"),
    ("account_type.employer", "Employer"),
    ("account_status.active", "Active"),
    ("role.super_admin", "Super Admin"),
    ("role.admin", "Admin"),
    ("role.account_admin", "Account Admin"),
    ("role.candidate", "Candidate"),
    ("role.employer", "Employer"),
    ("role.recruiter", "Recruiter"),
    ("role.consultant", "Consultant"),
    ("permission.manage_users", "Manage users"),
    ("permission.manage_jobs", "Manage jobs"),
    ("permission.view_candidates", "View candidates"),
    ("permission.post_jobs", "Post jobs"),
    ("licence_type.standard", "Standard"),
    ("licence_type.enterprise", "Enterprise"),
    ("licence_status.active", "Active"),
    ("device_type.desktop", "Desktop"),
    ("device_type.mobile", "Mobile"),
    ("revocation_reason.user_request", "User request"),
    ("plan_category.free", "Free"),
    ("plan_category.paid", "Paid"),
    ("billing_period.monthly", "Monthly"),
    ("renewal_type.auto", "Auto"),
    ("entitlement_unit.count", "Count"),
    ("payment_method.card", "Card"),
    ("payment_status.initiated", "Initiated"),
    ("payment_status.completed", "Completed"),
    ("invoice_status.issued", "Issued"),
    ("refund_status.requested", "Requested"),
    ("refund_type.full", "Full"),
    ("wallet_status.active", "Active"),
    ("wallet_transaction_type.recharge", "Recharge"),
    ("wallet_transaction_type.debit", "Debit"),
    ("wallet_reference_type.payment_order", "Payment order"),
    ("download_format.pdf", "PDF"),
    ("subscription_status.trial", "Trial"),
    ("subscription_status.active", "Active"),
    ("notification_channel.email", "Email"),
    ("notification_type.job_alert", "Job alert"),
    ("alert_frequency.immediate", "Immediate"),
    ("alert_frequency.daily", "Daily"),
    ("setting_type.boolean", "Boolean"),
    ("community_type.discussion", "Discussion"),
    ("post_visibility.public", "Public"),
    ("reaction_type.like", "Like"),
    ("support_category.billing", "Billing"),
    ("support_priority.low", "Low"),
    ("support_status.open", "Open"),
    ("faq_category.general", "General"),
    ("outreach_channel.email", "Email"),
    ("delivery_status.pending", "Pending"),
    ("delivery_status.sent", "Sent"),
    ("gig_worker_status.active", "Active"),
    ("rate_time_unit.hour", "Hour"),
    ("handoff_system.external_fulfillment", "External fulfillment"),
    ("fulfillment_status.pending", "Pending"),
    ("pricing_model.fixed", "Fixed"),
    ("pricing_model.rate", "Rate"),
    ("earnings_type.estimated", "Estimated"),
    ("source_system.external_fulfillment", "External fulfillment"),
    ("employer_organisation_size.small", "Small"),
    ("consultant_decision_type.accepted", "Accepted"),
    ("sourcing_status.open", "Open"),
    ("pipeline_stage.applied", "Applied"),
    ("pipeline_stage.shortlisted", "Shortlisted"),
    ("pipeline_stage.interviewed", "Interviewed"),
    ("pipeline_stage.offered", "Offered"),
    ("pipeline_stage.joined", "Joined"),
    ("pipeline_stage.rejected", "Rejected"),
    ("source_channel.organic", "Organic"),
    ("source_channel.referral", "Referral"),
    ("application_channel.portal", "Portal"),
    ("institution_type.university", "University"),
    ("recruiter_mapping_type.direct", "Direct"),
    ("account_admin_role.owner", "Owner"),
    ("employer_type.small", "Small"),
    ("employer_type.medium", "Medium"),
    ("company_size.1_to_10", "1-10"),
    ("seat_status.allocated", "Allocated"),
    ("tax_identifier_type.tax_id", "Tax ID"),
    ("verification_type.identity", "Identity"),
    ("verification_status.pending", "Pending"),
    ("login_result.success", "Success"),
    ("login_result.failed", "Failed"),
    ("event_type.login", "Login"),
    ("blocked_party_type.candidate", "Candidate"),
    ("entitlement_code.job_posts", "Job posts"),
    ("entitlement_code.downloads", "Downloads"),
    ("assessment_type.aptitude", "Aptitude"),
    ("assessment_type.technical", "Technical"),
    ("assessment_type.behavioral", "Behavioral"),
    ("assessment_category.reasoning", "Reasoning"),
    ("assessment_category.coding", "Coding"),
    ("assessment_category.communication", "Communication"),
    ("course_category.technical", "Technical"),
    ("course_category.management", "Management"),
    ("course_category.certification", "Certification"),
    ("course_level.beginner", "Beginner"),
    ("course_level.intermediate", "Intermediate"),
    ("course_level.advanced", "Advanced"),
    ("enrolment_status.enrolled", "Enrolled"),
    ("enrolment_status.completed", "Completed"),
    ("enrolment_status.dropped", "Dropped"),
    ("employment_type.full_time", "Full time"),
    ("employment_type.part_time", "Part time"),
    ("employment_type.contract", "Contract"),
    ("employment_type.internship", "Internship"),
    ("work_type.onsite", "On-site"),
    ("work_type.remote", "Remote"),
    ("work_type.hybrid", "Hybrid"),
    ("workflow.pipeline.applied", "Applied"),
    ("workflow.pipeline.shortlisted", "Shortlisted"),
    ("workflow.pipeline.interviewed", "Interviewed"),
    ("workflow.pipeline.offered", "Offered"),
    ("workflow.pipeline.joined", "Joined"),
    ("workflow.pipeline.rejected", "Rejected"),
    ("swipe_action.right", "Right"),
    ("swipe_action.left", "Left"),
    ("employment_type_code.full_time", "Full time"),
    ("employment_type_code.part_time", "Part time"),
    ("employment_type_code.contract", "Contract"),
    ("work_type_code.onsite", "On-site"),
    ("work_type_code.remote", "Remote"),
    ("work_type_code.hybrid", "Hybrid"),
    ("sms_template.job_shortlist", "Job shortlist"),
    ("notification_preference.job_match", "Job match"),
    ("candidate_profile_tag.job_matching", "Job matching"),
    ("candidate_profile_tag.readiness", "Readiness"),
    ("candidate_profile_tag.readiness.ready", "Ready"),
]


def load_ui_translations(cur, language_id_en):
    if not language_id_en:
        print("WARNING: no English language row; skipping ui_translations", file=sys.stderr)
        return 0
    existing = set()
    cur.execute(
        "SELECT ui_key, language_id FROM ui_translation WHERE language_id = %s",
        (language_id_en,),
    )
    for row in cur.fetchall():
        existing.add((row[0], row[1]))
    tups = [
        (ui_key, language_id_en, value, True, now(), 0, now(), 0)
        for ui_key, value in UI_TRANSLATIONS
        if (ui_key, language_id_en) not in existing
    ]
    return insert_many(
        cur,
        """
        INSERT INTO ui_translation(ui_key, language_id, value, is_default,
                                   created_at, created_by, updated_at, updated_by)
        VALUES %s
        """,
        tups,
    )


def main():
    conn = psycopg2.connect(dsn())
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    try:
        n_refs = load_reference_codes(cur)
        print(f"[OK] reference_code: {n_refs} rows")
        conn.commit()

        n_countries = load_countries(cur)
        print(f"[OK] country: {n_countries} rows")
        conn.commit()

        cur.execute("SELECT id, iso_alpha2 FROM country")
        country_by_iso = {row[1]: row[0] for row in cur.fetchall()}

        n_states = load_states(cur, country_by_iso)
        print(f"[OK] state: {n_states} rows")
        conn.commit()

        cur.execute("SELECT id, country_id, name FROM state")
        state_by_country_and_name = {(row[1], row[2]): row[0] for row in cur.fetchall()}

        n_cities = load_cities(cur, country_by_iso, state_by_country_and_name)
        print(f"[OK] city: {n_cities} rows")
        conn.commit()

        n_skills = load_skills(cur)
        print(f"[OK] skill: {n_skills} rows")
        conn.commit()

        n_industries = load_industries(cur)
        print(f"[OK] industry: {n_industries} rows")
        conn.commit()

        n_job_roles = load_job_roles(cur)
        print(f"[OK] job_role: {n_job_roles} rows")
        conn.commit()

        n_employment = load_employment_types(cur)
        print(f"[OK] employment_type: {n_employment} rows")
        conn.commit()

        n_work = load_work_types(cur)
        print(f"[OK] work_type: {n_work} rows")
        conn.commit()

        n_languages = load_languages(cur)
        print(f"[OK] language_lookup: {n_languages} rows")
        conn.commit()

        cur.execute("SELECT id, code FROM reference_code WHERE domain = 'education_level'")
        ed_rows = cur.fetchall()
        education_level_by_code = {row[1]: row[1] for row in ed_rows}
        print(f"[DBG] education_level domains: {len(ed_rows)} -> {list(education_level_by_code.keys())}")

        if not education_level_by_code:
            print("[WARN] education_level_by_code is empty - cannot seed qualifications")
            n_quals = 0
            conn.commit()
        else:
            missing = [el for el in ["secondary","undergraduate","postgraduate","doctorate"] if el not in education_level_by_code]
            if missing:
                print(f"[WARN] education_level codes missing in reference_code: {missing}")
                n_quals = 0
                conn.commit()
            else:
                n_quals = load_qualifications(cur, education_level_by_code)
                print(f"[OK] qualification: {n_quals} rows")
                conn.commit()

        cur.execute("SELECT id FROM language_lookup WHERE iso_639_1 = 'en'")
        en_row = cur.fetchone()
        language_id_en = en_row[0] if en_row else None

        if language_id_en:
            n_ui = load_ui_translations(cur, language_id_en)
            print(f"[OK] ui_translation: {n_ui} rows")
            conn.commit()
        else:
            print("[SKIP] ui_translation: no English language row")
            n_ui = 0

        print("\nMASTER REFERENCE SEED COMMITTED")

        print("\nMASTER REFERENCE SEED COMMITTED")

    except Exception:
        conn.rollback()
        print("MASTER REFERENCE SEED FAILED - rolled back", file=sys.stderr)
        raise
    finally:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        print("\nROW COUNTS (master data):")
        for table in [
            "reference_code",
            "country",
            "state",
            "city",
            "skill",
            "industry",
            "job_role",
            "employment_type",
            "work_type",
            "language_lookup",
            "qualification",
            "ui_translation",
        ]:
            cur.execute(f"SELECT count(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count}")
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
