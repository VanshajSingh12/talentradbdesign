"""
Talentra master reference loader

Purpose
-------
The DDL package in this repository defines the tables, but it does not ship
discoverable reference rows for the lookup domains the schema references via
reference_code(domain=...). The existing seed generator
(ddl/seed/generate_seed.py) also assumes these reference rows exist.

This script inserts the missing reference data:
- reference_code rows for every enum domain used across the DDL
- representative country / state / city rows
- representative skill / industry / job_role rows
- employment_type, work_type
- language_lookup rows
- qualification rows tied to education_level reference_code
- ui_translation rows keyed from the display_name_key values used by the DDL

This is intentionally a representative, laptop-scale reference load, not an
exhaustive industry taxonomy. It is meant to make the schema operable and the
existing seed generator runnable.

Encoding
--------
This script is UTF-8. Do not edit it in a tool that re-encodes it to a legacy
Windows codepage.
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Install: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


def dsn_from_env() -> str:
    pg_dsn = os.environ.get("PG_DSN", "").strip()
    if pg_dsn:
        return pg_dsn
    user = os.environ.get("POSTGRES_USER", "talentradb")
    password = os.environ.get("POSTGRES_PASSWORD", "changeme")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "talentra")
    return f"dbname={db} user={user} password={password} host={host} port={port}"


def trunc(cur, name: str) -> None:
    cur.execute(f'Truncate table "{name}" restart identity cascade')


def insert_many(cur, sql: str, rows: list[tuple]) -> None:
    if not rows:
        return
    psycopg2.extras.execute_values(cur, sql, rows, page_size=5000)


def load_reference_codes(cur) -> None:
    # Domain -> [(code, display_name_key, sort_order)]
    domains: dict[str, list[tuple[str, str, int]]] = {
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
            ("other", "contact.type.other", 40),
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
            ("cognitive", "assessment.type.cognitive", 40),
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
            ("employer", "skill.source.employer", 30),
        ],
        "fluency": [
            ("basic", "fluency.basic", 10),
            ("conversational", "fluency.conversational", 20),
            ("fluent", "fluency.fluent", 30),
            ("native", "fluency.native", 40),
        ],
        "language_proficiency": [
            ("basic", "language_proficiency.basic", 10),
            ("working", "language_proficiency.working", 20),
            ("proficient", "language_proficiency.proficient", 30),
            ("native", "language_proficiency.native", 40),
        ],
        "activity_type": [
            ("login", "activity.login", 10),
            ("profile_update", "activity.profile_update", 20),
            ("resume_download", "activity.resume_download", 30),
            ("application_submit", "activity.application_submit", 40),
        ],
        "shortlist_action": [
            ("added", "shortlist.action.added", 10),
            ("removed", "shortlist.action.removed", 20),
            ("renamed", "shortlist.action.renamed", 30),
        ],
        "referral_type": [
            ("candidate", "referral.type.candidate", 10),
            ("employee", "referral.type.employee", 20),
        ],
        "referral_status": [
            ("pending", "referral.status.pending", 10),
            ("contacted", "referral.status.contacted", 20),
            ("hired", "referral.status.hired", 30),
            ("rejected", "referral.status.rejected", 40),
        ],
        "referral_event_type": [
            ("referred", "referral_event.type.referred", 10),
            ("converted", "referral_event.type.converted", 20),
        ],
        "institution_type": [
            ("university", "institution.type.university", 10),
            ("college", "institution.type.college", 20),
            ("school", "institution.type.school", 30),
            ("training", "institution.type.training", 40),
        ],
        "job_status": [
            ("draft", "job_status.draft", 10),
            ("published", "job_status.published", 20),
            ("closed", "job_status.closed", 30),
            ("archived", "job_status.archived", 40),
        ],
        "job_visibility": [
            ("public", "job_visibility.public", 10),
            ("private", "job_visibility.private", 20),
            ("internal", "job_visibility.internal", 30),
        ],
        "question_type": [
            ("text", "question.type.text", 10),
            ("multiple_choice", "question.type.multiple_choice", 20),
            ("single_choice", "question.type.single_choice", 30),
        ],
        "recovery_type": [
            ("email_code", "recovery.type.email_code", 10),
            ("email_link", "recovery.type.email_link", 20),
            ("sms_code", "recovery.type.sms_code", 30),
        ],
        "session_status": [
            ("active", "session.status.active", 10),
            ("expired", "session.status.expired", 20),
            ("revoked", "session.status.revoked", 30),
        ],
        "consent_type": [
            ("marketing", "consent.type.marketing", 10),
            ("data_processing", "consent.type.data_processing", 20),
            ("cookies", "consent.type.cookies", 30),
        ],
        "consent_value": [
            ("granted", "consent.value.granted", 10),
            ("denied", "consent.value.denied", 20),
            ("withdrawn", "consent.value.withdrawn", 30),
        ],
        "event_type": [
            ("login", "event.login", 10),
            ("password_change", "event.password_change", 20),
            ("account_locked", "event.account_locked", 30),
        ],
        "blocked_party_type": [
            ("candidate", "blocked_party.candidate", 10),
            ("employer", "blocked_party.employer", 20),
            ("recruiter", "blocked_party.recruiter", 30),
            ("consultant", "blocked_party.consultant", 40),
        ],
        "account_type": [
            ("platform", "account.type.platform", 10),
            ("employer", "account.type.employer", 20),
            ("consultant", "account.type.consultant", 30),
        ],
        "account_status": [
            ("active", "account.status.active", 10),
            ("suspended", "account.status.suspended", 20),
            ("closed", "account.status.closed", 30),
        ],
        "verification_status": [
            ("pending", "verification.status.pending", 10),
            ("verified", "verification.status.verified", 20),
            ("failed", "verification.status.failed", 30),
        ],
        "recruiter_mapping_type": [
            ("direct", "recruiter_mapping.type.direct", 10),
            ("shared", "recruiter_mapping.type.shared", 20),
        ],
        "account_admin_role": [
            ("owner", "account_admin.role.owner", 10),
            ("admin", "account_admin.role.admin", 20),
        ],
        "credential_type": [
            ("password", "credential.type.password", 10),
            ("federated", "credential.type.federated", 20),
        ],
        "credential_status": [
            ("active", "credential.status.active", 10),
            ("locked", "credential.status.locked", 20),
            ("expired", "credential.status.expired", 30),
        ],
        "tax_identifier_type": [
            ("tax_id", "tax_identifier.type.tax_id", 10),
            ("registration", "tax_identifier.type.registration", 20),
        ],
        "employer_type": [
            ("small", "employer.type.small", 10),
            ("medium", "employer.type.medium", 20),
            ("large", "employer.type.large", 30),
        ],
        "company_size": [
            ("1_to_10", "company.size.1_to_10", 10),
            ("11_to_50", "company.size.11_to_50", 20),
            ("51_to_200", "company.size.51_to_200", 30),
            ("201_plus", "company.size.201_plus", 40),
        ],
        "licence_type": [
            ("standard", "licence.type.standard", 10),
            ("enterprise", "licence.type.enterprise", 20),
        ],
        "licence_status": [
            ("active", "licence.status.active", 10),
            ("expired", "licence.status.expired", 20),
            ("suspended", "licence.status.suspended", 30),
        ],
        "seat_status": [
            ("allocated", "seat.status.allocated", 10),
            ("available", "seat.status.available", 20),
            ("revoked", "seat.status.revoked", 30),
        ],
        "device_type": [
            ("desktop", "device.type.desktop", 10),
            ("mobile", "device.type.mobile", 20),
            ("tablet", "device.type.tablet", 30),
        ],
        "revocation_reason": [
            ("user_request", "revocation.reason.user_request", 10),
            ("security", "revocation.reason.security", 20),
            ("policy", "revocation.reason.policy", 30),
        ],
        "plan_category": [
            ("free", "plan.category.free", 10),
            ("paid", "plan.category.paid", 20),
        ],
        "billing_period": [
            ("monthly", "billing.period.monthly", 10),
            ("quarterly", "billing.period.quarterly", 20),
            ("annual", "billing.period.annual", 30),
        ],
        "renewal_type": [
            ("auto", "renewal.type.auto", 10),
            ("manual", "renewal.type.manual", 20),
        ],
        "entitlement_unit": [
            ("count", "entitlement.unit.count", 10),
            ("credits", "entitlement.unit.credits", 20),
        ],
        "payment_method": [
            ("card", "payment.method.card", 10),
            ("wallet", "payment.method.wallet", 20),
            ("bank_transfer", "payment.method.bank_transfer", 30),
        ],
        "payment_status": [
            ("initiated", "payment.status.initiated", 10),
            ("completed", "payment.status.completed", 20),
            ("failed", "payment.status.failed", 30),
            ("refunded", "payment.status.refunded", 40),
        ],
        "invoice_status": [
            ("issued", "invoice.status.issued", 10),
            ("paid", "invoice.status.paid", 20),
            ("overdue", "invoice.status.overdue", 30),
        ],
        "refund_status": [
            ("requested", "refund.status.requested", 10),
            ("approved", "refund.status.approved", 20),
            ("processed", "refund.status.processed", 30),
        ],
        "refund_type": [
            ("full", "refund.type.full", 10),
            ("partial", "refund.type.partial", 20),
        ],
        "wallet_status": [
            ("active", "wallet.status.active", 10),
            ("suspended", "wallet.status.suspended", 20),
            ("closed", "wallet.status.closed", 30),
        ],
        "wallet_transaction_type": [
            ("recharge", "wallet.tx.recharge", 10),
            ("debit", "wallet.tx.debit", 20),
            ("refund", "wallet.tx.refund", 30),
            ("adjustment", "wallet.tx.adjustment", 40),
        ],
        "wallet_reference_type": [
            ("payment_order", "wallet.ref.payment_order", 10),
            ("subscription_period", "wallet.ref.subscription_period", 20),
            ("profile_download", "wallet.ref.profile_download", 30),
        ],
        "download_format": [
            ("pdf", "download.format.pdf", 10),
            ("rtf", "download.format.rtf", 20),
            ("plain", "download.format.plain", 30),
        ],
        "subscription_status": [
            ("trial", "subscription.status.trial", 10),
            ("active", "subscription.status.active", 20),
            ("expired", "subscription.status.expired", 30),
            ("cancelled", "subscription.status.cancelled", 40),
        ],
        "notification_channel": [
            ("email", "notification.channel.email", 10),
            ("sms", "notification.channel.sms", 20),
            ("in_app", "notification.channel.in_app", 30),
        ],
        "notification_type": [
            ("job_alert", "notification.type.job_alert", 10),
            ("system", "notification.type.system", 20),
            ("message", "notification.type.message", 30),
        ],
        "alert_frequency": [
            ("immediate", "alert.frequency.immediate", 10),
            ("daily", "alert.frequency.daily", 20),
            ("weekly", "alert.frequency.weekly", 30),
        ],
        "setting_type": [
            ("boolean", "setting.type.boolean", 10),
            ("text", "setting.type.text", 20),
            ("number", "setting.type.number", 30),
        ],
        "community_type": [
            ("discussion", "community.type.discussion", 10),
            ("announcement", "community.type.announcement", 20),
        ],
        "post_visibility": [
            ("public", "post.visibility.public", 10),
            ("community", "post.visibility.community", 20),
            ("private", "post.visibility.private", 30),
        ],
        "reaction_type": [
            ("like", "reaction.type.like", 10),
            ("helpful", "reaction.type.helpful", 20),
            ("insightful", "reaction.type.insightful", 30),
        ],
        "support_category": [
            ("billing", "support.category.billing", 10),
            ("technical", "support.category.technical", 20),
            ("account", "support.category.account", 30),
        ],
        "support_priority": [
            ("low", "support.priority.low", 10),
            ("medium", "support.priority.medium", 20),
            ("high", "support.priority.high", 30),
        ],
        "support_status": [
            ("open", "support.status.open", 10),
            ("in_progress", "support.status.in_progress", 20),
            ("resolved", "support.status.resolved", 30),
            ("closed", "support.status.closed", 40),
        ],
        "faq_category": [
            ("general", "faq.category.general", 10),
            ("account", "faq.category.account", 20),
            ("billing", "faq.category.billing", 30),
        ],
        "outreach_channel": [
            ("email", "outreach.channel.email", 10),
            ("sms", "outreach.channel.sms", 20),
        ],
        "delivery_status": [
            ("pending", "delivery.status.pending", 10),
            ("sent", "delivery.status.sent", 20),
            ("delivered", "delivery.status.delivered", 30),
            ("failed", "delivery.status.failed", 40),
        ],
        "gig_worker_status": [
            ("active", "gig_worker.status.active", 10),
            ("inactive", "gig_worker.status.inactive", 20),
            ("suspended", "gig_worker.status.suspended", 30),
        ],
        "rate_time_unit": [
            ("hour", "rate.time.hour", 10),
            ("day", "rate.time.day", 20),
            ("project", "rate.time.project", 30),
        ],
        "handoff_system": [
            ("external_fulfillment", "handoff.system.external_fulfillment", 10),
        ],
        "fulfillment_status": [
            ("pending", "fulfillment.status.pending", 10),
            ("in_progress", "fulfillment.status.in_progress", 20),
            ("completed", "fulfillment.status.completed", 30),
            ("failed", "fulfillment.status.failed", 40),
        ],
        "pricing_model": [
            ("fixed", "pricing.model.fixed", 10),
            ("rate", "pricing.model.rate", 20),
        ],
        "earnings_type": [
            ("estimated", "earnings.type.estimated", 10),
            ("actual", "earnings.type.actual", 20),
            ("projected", "earnings.type.projected", 30),
        ],
        "source_system": [
            ("external_fulfillment", "source.system.external_fulfillment", 10),
        ],
        "employer_organisation_size": [
            ("small", "employer_organisation.size.small", 10),
            ("medium", "employer_organisation.size.medium", 20),
            ("large", "employer_organisation.size.large", 30),
        ],
        "consultant_decision_type": [
            ("accepted", "consultant_decision.type.accepted", 10),
            ("declined", "consultant_decision.type.declined", 20),
        ],
        "sourcing_status": [
            ("open", "sourcing.status.open", 10),
            ("assigned", "sourcing.status.assigned", 20),
            ("completed", "sourcing.status.completed", 30),
        ],
    }

    rows: list[tuple[str, str, str, int]] = []
    for domain, items in domains.items():
        for code, display_name_key, sort_order in items:
            rows.append((domain, code, display_name_key, True, sort_order))

    insert_many(
        cur,
        """
        insert into reference_code(domain, code, display_name_key, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("reference_code rows inserted:", len(rows))


def load_countries(cur) -> None:
    countries = [
        ("US", "USA", "United States", "840"),
        ("IN", "IND", "India", "356"),
        ("GB", "GBR", "United Kingdom", "826"),
        ("CA", "CAN", "Canada", "124"),
        ("AU", "AUS", "Australia", "036"),
        ("DE", "DEU", "Germany", "276"),
        ("FR", "FRA", "France", "250"),
        ("ES", "ESP", "Spain", "724"),
        ("BR", "BRA", "Brazil", "076"),
        ("AE", "ARE", "United Arab Emirates", "784"),
        ("SG", "SGP", "Singapore", "702"),
        ("JP", "JPN", "Japan", "392"),
        ("CN", "CHN", "China", "156"),
        ("KR", "KOR", "South Korea", "410"),
        ("IT", "ITA", "Italy", "380"),
        ("RU", "RUS", "Russia", "643"),
        ("ZA", "ZAF", "South Africa", "710"),
        ("NG", "NGA", "Nigeria", "566"),
        ("PK", "PAK", "Pakistan", "586"),
        ("MX", "MEX", "Mexico", "484"),
    ]
    rows = [(iso2, iso3, name, iso_numeric, True, 0) for iso2, iso3, name, iso_numeric in countries]
    insert_many(
        cur,
        """
        insert into country(iso_alpha2, iso_alpha3, name, iso_numeric, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("country rows inserted:", len(rows))


def load_states(cur) -> None:
    # (country_iso_alpha2, state_name)
    data = [
        ("US", "California"),
        ("US", "Texas"),
        ("US", "New York"),
        ("US", "Illinois"),
        ("US", "Florida"),
        ("IN", "Maharashtra"),
        ("IN", "Karnataka"),
        ("IN", "Delhi"),
        ("IN", "Tamil Nadu"),
        ("IN", "Telangana"),
        ("GB", "England"),
        ("GB", "Scotland"),
        ("GB", "Wales"),
        ("CA", "Ontario"),
        ("CA", "British Columbia"),
        ("AU", "New South Wales"),
        ("AU", "Victoria"),
        ("AU", "Queensland"),
        ("DE", "Bavaria"),
        ("DE", "Berlin"),
        ("FR", "Ile-de-France"),
        ("FR", "Provence-Alpes-Cote d'Azur"),
        ("ES", "Andalusia"),
        ("BR", "Sao Paulo"),
        ("BR", "Rio de Janeiro"),
        ("AE", "Dubai"),
        ("AE", "Abu Dhabi"),
        ("SG", "Central Singapore"),
        ("JP", "Tokyo"),
        ("KR", "Seoul"),
    ]
    # load country id map
    cur.execute("select id, iso_alpha2 from country")
    country_by_code = dict(cur.fetchall())

    rows: list[tuple[int, str, bool, int]] = []
    for code, name in data:
        cid = country_by_code.get(code)
        if cid is None:
            continue
        rows.append((cid, name, True, 0))

    insert_many(
        cur,
        """
        insert into state(country_id, name, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("state rows inserted:", len(rows))


def load_cities(cur) -> None:
    # (country_iso_alpha2, state_name_or_None, city_name)
    data = [
        ("US", "California", "San Francisco"),
        ("US", "California", "Los Angeles"),
        ("US", "Texas", "Austin"),
        ("US", "Texas", "Dallas"),
        ("US", "New York", "New York"),
        ("US", "Illinois", "Chicago"),
        ("US", "Florida", "Miami"),
        ("IN", "Maharashtra", "Mumbai"),
        ("IN", "Maharashtra", "Pune"),
        ("IN", "Karnataka", "Bengaluru"),
        ("IN", "Delhi", "New Delhi"),
        ("IN", "Tamil Nadu", "Chennai"),
        ("IN", "Telangana", "Hyderabad"),
        ("GB", "England", "London"),
        ("GB", "Scotland", "Edinburgh"),
        ("CA", "Ontario", "Toronto"),
        ("CA", "British Columbia", "Vancouver"),
        ("AU", "New South Wales", "Sydney"),
        ("AU", "Victoria", "Melbourne"),
        ("AU", "Queensland", "Brisbane"),
        ("DE", "Bavaria", "Munich"),
        ("DE", "Berlin", "Berlin"),
        ("FR", "Ile-de-France", "Paris"),
        ("ES", "Andalusia", "Madrid"),
        ("BR", "Sao Paulo", "Sao Paulo"),
        ("BR", "Rio de Janeiro", "Rio de Janeiro"),
        ("AE", "Dubai", "Dubai"),
        ("AE", "Abu Dhabi", "Abu Dhabi"),
        ("SG", "Central Singapore", "Singapore"),
        ("JP", "Tokyo", "Tokyo"),
        ("KR", "Seoul", "Seoul"),
    ]
    cur.execute("select id, iso_alpha2 from country")
    country_by_code = dict(cur.fetchall())
    cur.execute("select id, country_id, name from state")
    state_by_pair: dict[tuple[int, str], int] = {}
    for sid, cid, sname in cur.fetchall():
        state_by_pair[(cid, sname)] = sid

    rows: list[tuple[int, int | None, str, int, int, int, str, bool, int]] = []
    for code, state_name, city_name in data:
        cid = country_by_code.get(code)
        if cid is None:
            continue
        sid = state_by_pair.get((cid, state_name))
        rows.append((cid, sid, city_name, None, None, None, None, True, 0))

    insert_many(
        cur,
        """
        insert into city(country_id, state_id, name, latitude, longitude, coordinates_source, timezone, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("city rows inserted:", len(rows))


def load_skills(cur) -> None:
    skills = [
        ("Python", "Programming"),
        ("Java", "Programming"),
        ("JavaScript", "Programming"),
        ("TypeScript", "Programming"),
        ("SQL", "Data"),
        ("PostgreSQL", "Data"),
        ("Redis", "Data"),
        ("Kubernetes", "Infrastructure"),
        ("Docker", "Infrastructure"),
        ("AWS", "Cloud"),
        ("Azure", "Cloud"),
        ("GCP", "Cloud"),
        ("React", "Frontend"),
        ("Angular", "Frontend"),
        ("Vue", "Frontend"),
        ("Node.js", "Backend"),
        ("Spring", "Backend"),
        ("Django", "Backend"),
        ("FastAPI", "Backend"),
        ("Data Engineering", "Data"),
        ("Machine Learning", "Data"),
        ("DevOps", "Infrastructure"),
        ("Project Management", "Management"),
        ("Business Analysis", "Analysis"),
        ("Agile", "Process"),
        ("Scrum", "Process"),
        ("Communication", "Soft Skills"),
        ("Leadership", "Soft Skills"),
        ("Problem Solving", "Soft Skills"),
        ("SQL Server", "Data"),
    ]
    rows = [(name, category, True, 0) for name, category in skills]
    insert_many(
        cur,
        """
        insert into skill(name, category, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("skill rows inserted:", len(rows))


def load_industries(cur) -> None:
    industries = [
        ("Technology",),
        ("Financial Services",),
        ("Healthcare",),
        ("Consulting",),
        ("Retail",),
        ("Manufacturing",),
        ("Media",),
        ("Education",),
        ("Logistics",),
        ("Real Estate",),
        ("Telecom",),
        ("Energy",),
        ("Automotive",),
        ("Hospitality",),
        ("Public Sector",),
    ]
    rows = [(name, True, 0) for (name,) in industries]
    insert_many(
        cur,
        """
        insert into industry(name, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("industry rows inserted:", len(rows))


def load_job_roles(cur) -> None:
    roles = [
        ("Software Engineer",),
        ("Data Engineer",),
        ("DevOps Engineer",),
        ("Frontend Developer",),
        ("Backend Developer",),
        ("Full Stack Developer",),
        ("Data Scientist",),
        ("Machine Learning Engineer",),
        ("Solution Architect",),
        ("Product Manager",),
        ("Project Manager",),
        ("Business Analyst",),
        ("Recruiter",),
        ("Talent Acquisition Partner",),
        ("Consultant",),
        ("Account Manager",),
        ("Sales Engineer",),
        ("Technical Writer",),
        ("QA Engineer",),
        ("Cloud Engineer",),
    ]
    rows = [(name, True, 0) for (name,) in roles]
    insert_many(
        cur,
        """
        insert into job_role(name, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("job_role rows inserted:", len(rows))


def load_employment_type(cur) -> None:
    rows = [
        ("full_time", "employment_type.full_time", True, 10),
        ("part_time", "employment_type.part_time", True, 20),
        ("contract", "employment_type.contract", True, 30),
        ("intern", "employment_type.intern", True, 40),
        ("apprentice", "employment_type.apprentice", True, 50),
    ]
    insert_many(
        cur,
        """
        insert into employment_type(code, display_name_key, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("employment_type rows inserted:", len(rows))


def load_work_type(cur) -> None:
    rows = [
        ("onsite", "work_type.onsite", True, 10),
        ("remote", "work_type.remote", True, 20),
        ("hybrid", "work_type.hybrid", True, 30),
    ]
    insert_many(
        cur,
        """
        insert into work_type(code, display_name_key, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("work_type rows inserted:", len(rows))


def load_languages(cur) -> None:
    rows = [
        ("en", "eng", "English", True, 10),
        ("hi", "hin", "Hindi", True, 20),
        ("es", "spa", "Spanish", True, 30),
        ("fr", "fra", "French", True, 40),
        ("de", "deu", "German", True, 50),
        ("zh", "zho", "Chinese", True, 60),
        ("ja", "jpn", "Japanese", True, 70),
        ("ar", "ara", "Arabic", True, 80),
        ("pt", "por", "Portuguese", True, 90),
        ("ru", "rus", "Russian", True, 100),
        ("ko", "kor", "Korean", True, 110),
        ("it", "ita", "Italian", True, 120),
    ]
    insert_many(
        cur,
        """
        insert into language_lookup(iso_639_1, iso_639_3, name, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("language_lookup rows inserted:", len(rows))


def load_qualifications(cur, ref_map: dict[str, dict[str, int]]) -> None:
    # (code, name, education_level_code)
    data = [
        ("BA", "Bachelor of Arts", "undergraduate"),
        ("BSc", "Bachelor of Science", "undergraduate"),
        ("BEng", "Bachelor of Engineering", "undergraduate"),
        ("BCom", "Bachelor of Commerce", "undergraduate"),
        ("BBA", "Bachelor of Business Administration", "undergraduate"),
        ("MCA", "Master of Computer Applications", "postgraduate"),
        ("MSc", "Master of Science", "postgraduate"),
        ("MA", "Master of Arts", "postgraduate"),
        ("MBA", "Master of Business Administration", "postgraduate"),
        ("MEng", "Master of Engineering", "postgraduate"),
        ("MCom", "Master of Commerce", "postgraduate"),
        ("LLM", "Master of Laws", "postgraduate"),
        ("MFA", "Master of Fine Arts", "postgraduate"),
        ("PhD", "Doctor of Philosophy", "doctorate"),
        ("Diploma", "Diploma", "secondary"),
        ("Certificate", "Certificate", "secondary"),
    ]
    rows: list[tuple[str, str, str, bool, int]] = []
    for code, name, education_level_code in data:
        level_id = ref_map.get("education_level", {}).get(education_level_code)
        if level_id is None:
            # Fall back to first active education_level code if the name differs.
            continue
        rows.append((code, name, education_level_code, True, 0))

    insert_many(
        cur,
        """
        insert into qualification(code, name, education_level_code, is_active, sort_order)
        values %s
        """,
        rows,
    )
    print("qualification rows inserted:", len(rows))


def load_ui_translations(cur) -> None:
    # (ui_key, language_iso_639_1, value, is_default)
    rows = [
        ("candidate.status.active", "en", "Active", True),
        ("candidate.status.inactive", "en", "Inactive", True),
        ("candidate.status.pending", "en", "Pending", True),
        ("candidate.status.suspended", "en", "Suspended", True),
        ("profile.type.permanent", "en", "Permanent", True),
        ("profile.type.temporary", "en", "Temporary", True),
        ("profile.type.gig", "en", "Gig", True),
        ("contact.type.email", "en", "Email", True),
        ("contact.type.phone", "en", "Phone", True),
        ("gender.male", "en", "Male", True),
        ("gender.female", "en", "Female", True),
        ("gender.prefer_not_to_say", "en", "Prefer not to say", True),
        ("education.level.secondary", "en", "Secondary", True),
        ("education.level.undergraduate", "en", "Undergraduate", True),
        ("education.level.postgraduate", "en", "Postgraduate", True),
        ("education.level.doctorate", "en", "Doctorate", True),
        ("assessment.type.aptitude", "en", "Aptitude", True),
        ("assessment.type.technical", "en", "Technical", True),
        ("assessment.type.behavioral", "en", "Behavioral", True),
        ("assessment.category.reasoning", "en", "Reasoning", True),
        ("assessment.category.coding", "en", "Coding", True),
        ("assessment.category.communication", "en", "Communication", True),
        ("course.category.technical", "en", "Technical", True),
        ("course.level.beginner", "en", "Beginner", True),
        ("course.level.intermediate", "en", "Intermediate", True),
        ("course.level.advanced", "en", "Advanced", True),
        ("enrolment.status.enrolled", "en", "Enrolled", True),
        ("enrolment.status.completed", "en", "Completed", True),
        ("enrolment.status.dropped", "en", "Dropped", True),
        ("project.type.candidate", "en", "Candidate project", True),
        ("project.type.gig", "en", "Gig project", True),
        ("proficiency.basic", "en", "Basic", True),
        ("proficiency.intermediate", "en", "Intermediate", True),
        ("proficiency.advanced", "en", "Advanced", True),
        ("proficiency.expert", "en", "Expert", True),
        ("skill.source.self", "en", "Self-declared", True),
        ("skill.source.assessment", "en", "Assessment", True),
        ("skill.source.employer", "en", "Employer-verified", True),
        ("fluency.basic", "en", "Basic", True),
        ("fluency.conversational", "en", "Conversational", True),
        ("fluency.fluent", "en", "Fluent", True),
        ("fluency.native", "en", "Native", True),
        ("language_proficiency.basic", "en", "Basic", True),
        ("language_proficiency.working", "en", "Working proficiency", True),
        ("language_proficiency.proficient", "en", "Proficient", True),
        ("language_proficiency.native", "en", "Native", True),
        ("activity.login", "en", "Login", True),
        ("activity.profile_update", "en", "Profile update", True),
        ("activity.resume_download", "en", "Resume download", True),
        ("activity.application_submit", "en", "Application submitted", True),
        ("shortlist.action.added", "en", "Added", True),
        ("shortlist.action.removed", "en", "Removed", True),
        ("shortlist.action.renamed", "en", "Renamed", True),
        ("referral.type.candidate", "en", "Candidate referral", True),
        ("referral.type.employee", "en", "Employee referral", True),
        ("referral.status.pending", "en", "Pending", True),
        ("referral.status.contacted", "en", "Contacted", True),
        ("referral.status.hired", "en", "Hired", True),
        ("referral.status.rejected", "en", "Rejected", True),
        ("referral_event.type.referred", "en", "Referred", True),
        ("referral_event.type.converted", "en", "Converted", True),
        ("institution.type.university", "en", "University", True),
        ("institution.type.college", "en", "College", True),
        ("institution.type.school", "en", "School", True),
        ("institution.type.training", "en", "Training", True),
        ("job_status.draft", "en", "Draft", True),
        ("job_status.published", "en", "Published", True),
        ("job_status.closed", "en", "Closed", True),
        ("job_status.archived", "en", "Archived", True),
        ("job_visibility.public", "en", "Public", True),
        ("job_visibility.private", "en", "Private", True),
        ("job_visibility.internal", "en", "Internal", True),
        ("question.type.text", "en", "Text", True),
        ("question.type.multiple_choice", "en", "Multiple choice", True),
        ("question.type.single_choice", "en", "Single choice", True),
        ("recovery.type.email_code", "en", "Email code", True),
        ("recovery.type.email_link", "en", "Email link", True),
        ("recovery.type.sms_code", "en", "SMS code", True),
        ("session.status.active", "en", "Active", True),
        ("session.status.expired", "en", "Expired", True),
        ("session.status.revoked", "en", "Revoked", True),
        ("consent.type.marketing", "en", "Marketing", True),
        ("consent.type.data_processing", "en", "Data processing", True),
        ("consent.type.cookies", "en", "Cookies", True),
        ("consent.value.granted", "en", "Granted", True),
        ("consent.value.denied", "en", "Denied", True),
        ("consent.value.withdrawn", "en", "Withdrawn", True),
        ("event.login", "en", "Login", True),
        ("event.password_change", "en", "Password change", True),
        ("event.account_locked", "en", "Account locked", True),
        ("blocked_party.candidate", "en", "Candidate", True),
        ("blocked_party.employer", "en", "Employer", True),
        ("blocked_party.recruiter", "en", "Recruiter", True),
        ("blocked_party.consultant", "en", "Consultant", True),
        ("account.type.platform", "en", "Platform", True),
        ("account.type.employer", "en", "Employer", True),
        ("account.type.consultant", "en", "Consultant", True),
        ("account.status.active", "en", "Active", True),
        ("account.status.suspended", "en", "Suspended", True),
        ("account.status.closed", "en", "Closed", True),
        ("verification.status.pending", "en", "Pending", True),
        ("verification.status.verified", "en", "Verified", True),
        ("verification.status.failed", "en", "Failed", True),
        ("recruiter_mapping.type.direct", "en", "Direct", True),
        ("recruiter_mapping.type.shared", "en", "Shared", True),
        ("account_admin.role.owner", "en", "Owner", True),
        ("account_admin.role.admin", "en", "Admin", True),
        ("credential.type.password", "en", "Password", True),
        ("credential.type.federated", "en", "Federated", True),
        ("credential.status.active", "en", "Active", True),
        ("credential.status.locked", "en", "Locked", True),
        ("credential.status.expired", "en", "Expired", True),
        ("tax_identifier.type.tax_id", "en", "Tax ID", True),
        ("tax_identifier.type.registration", "en", "Registration", True),
        ("employer.type.small", "en", "Small", True),
        ("employer.type.medium", "en", "Medium", True),
        ("employer.type.large", "en", "Large", True),
        ("company.size.1_to_10", "en", "1-10", True),
        ("company.size.11_to_50", "en", "11-50", True),
        ("company.size.51_to_200", "en", "51-200", True),
        ("company.size.201_plus", "en", "201+", True),
        ("licence.type.standard", "en", "Standard", True),
        ("licence.type.enterprise", "en", "Enterprise", True),
        ("licence.status.active", "en", "Active", True),
        ("licence.status.expired", "en", "Expired", True),
        ("licence.status.suspended", "en", "Suspended", True),
        ("seat.status.allocated", "en", "Allocated", True),
        ("seat.status.available", "en", "Available", True),
        ("seat.status.revoked", "en", "Revoked", True),
        ("device.type.desktop", "en", "Desktop", True),
        ("device.type.mobile", "en", "Mobile", True),
        ("device.type.tablet", "en", "Tablet", True),
        ("revocation.reason.user_request", "en", "User request", True),
        ("revocation.reason.security", "en", "Security", True),
        ("revocation.reason.policy", "en", "Policy", True),
        ("plan.category.free", "en", "Free", True),
        ("plan.category.paid", "en", "Paid", True),
        ("billing.period.monthly", "en", "Monthly", True),
        ("billing.period.quarterly", "en", "Quarterly", True),
        ("billing.period.annual", "en", "Annual", True),
        ("renewal.type.auto", "en", "Auto-renewal", True),
        ("renewal.type.manual", "en", "Manual", True),
        ("entitlement.unit.count", "en", "Count", True),
        ("entitlement.unit.credits", "en", "Credits", True),
        ("payment.method.card", "en", "Card", True),
        ("payment.method.wallet", "en", "Wallet", True),
        ("payment.method.bank_transfer", "en", "Bank transfer", True),
        ("payment.status.initiated", "en", "Initiated", True),
        ("payment.status.completed", "en", "Completed", True),
        ("payment.status.failed", "en", "Failed", True),
        ("payment.status.refunded", "en", "Refunded", True),
        ("invoice.status.issued", "en", "Issued", True),
        ("invoice.status.paid", "en", "Paid", True),
        ("invoice.status.overdue", "en", "Overdue", True),
        ("refund.status.requested", "en", "Requested", True),
        ("refund.status.approved", "en", "Approved", True),
        ("refund.status.processed", "en", "Processed", True),
        ("refund.type.full", "en", "Full", True),
        ("refund.type.partial", "en", "Partial", True),
        ("wallet.status.active", "en", "Active", True),
        ("wallet.status.suspended", "en", "Suspended", True),
        ("wallet.status.closed", "en", "Closed", True),
        ("wallet.tx.recharge", "en", "Recharge", True),
        ("wallet.tx.debit", "en", "Debit", True),
        ("wallet.tx.refund", "en", "Refund", True),
        ("wallet.tx.adjustment", "en", "Adjustment", True),
        ("wallet.ref.payment_order", "en", "Payment order", True),
        ("wallet.ref.subscription_period", "en", "Subscription period", True),
        ("wallet.ref.profile_download", "en", "Profile download", True),
        ("download.format.pdf", "en", "PDF", True),
        ("download.format.rtf", "en", "RTF", True),
        ("download.format.plain", "en", "Plain text", True),
        ("subscription.status.trial", "en", "Trial", True),
        ("subscription.status.active", "en", "Active", True),
        ("subscription.status.expired", "en", "Expired", True),
        ("subscription.status.cancelled", "en", "Cancelled", True),
        ("notification.channel.email", "en", "Email", True),
        ("notification.channel.sms", "en", "SMS", True),
        ("notification.channel.in_app", "en", "In-app", True),
        ("notification.type.job_alert", "en", "Job alert", True),
        ("notification.type.system", "en", "System", True),
        ("notification.type.message", "en", "Message", True),
        ("alert.frequency.immediate", "en", "Immediate", True),
        ("alert.frequency.daily", "en", "Daily", True),
        ("alert.frequency.weekly", "en", "Weekly", True),
        ("setting.type.boolean", "en", "Boolean", True),
        ("setting.type.text", "en", "Text", True),
        ("setting.type.number", "en", "Number", True),
        ("community.type.discussion", "en", "Discussion", True),
        ("community.type.announcement", "en", "Announcement", True),
        ("post.visibility.public", "en", "Public", True),
        ("post.visibility.community", "en", "Community", True),
        ("post.visibility.private", "en", "Private", True),
        ("reaction.type.like", "en", "Like", True),
        ("reaction.type.helpful", "en", "Helpful", True),
        ("reaction.type.insightful", "en", "Insightful", True),
        ("support.category.billing", "en", "Billing", True),
        ("support.category.technical", "en", "Technical", True),
        ("support.category.account", "en", "Account", True),
        ("support.priority.low", "en", "Low", True),
        ("support.priority.medium", "en", "Medium", True),
        ("support.priority.high", "en", "High", True),
        ("support.status.open", "en", "Open", True),
        ("support.status.in_progress", "en", "In progress", True),
        ("support.status.resolved", "en", "Resolved", True),
        ("support.status.closed", "en", "Closed", True),
        ("faq.category.general", "en", "General", True),
        ("faq.category.account", "en", "Account", True),
        ("faq.category.billing", "en", "Billing", True),
        ("outreach.channel.email", "en", "Email", True),
        ("outreach.channel.sms", "en", "SMS", True),
        ("delivery.status.pending", "en", "Pending", True),
        ("delivery.status.sent", "en", "Sent", True),
        ("delivery.status.delivered", "en", "Delivered", True),
        ("delivery.status.failed", "en", "Failed", True),
        ("gig_worker.status.active", "en", "Active", True),
        ("gig_worker.status.inactive", "en", "Inactive", True),
        ("gig_worker.status.suspended", "en", "Suspended", True),
        ("rate.time.hour", "en", "Hour", True),
        ("rate.time.day", "en", "Day", True),
        ("rate.time.project", "en", "Project", True),
        ("handoff.system.external_fulfillment", "en", "External fulfillment", True),
        ("fulfillment.status.pending", "en", "Pending", True),
        ("fulfillment.status.in_progress", "en", "In progress", True),
        ("fulfillment.status.completed", "en", "Completed", True),
        ("fulfillment.status.failed", "en", "Failed", True),
        ("pricing.model.fixed", "en", "Fixed price", True),
        ("pricing.model.rate", "en", "Rate based", True),
        ("earnings.type.estimated", "en", "Estimated", True),
        ("earnings.type.actual", "en", "Actual", True),
        ("earnings.type.projected", "en", "Projected", True),
        ("source.system.external_fulfillment", "en", "External fulfillment", True),
        ("employer_organisation.size.small", "en", "Small", True),
        ("employer_organisation.size.medium", "en", "Medium", True),
        ("employer_organisation.size.large", "en", "Large", True),
        ("consultant_decision.type.accepted", "en", "Accepted", True),
        ("consultant_decision.type.declined", "en", "Declined", True),
        ("sourcing.status.open", "en", "Open", True),
        ("sourcing.status.assigned", "en", "Assigned", True),
        ("sourcing.status.completed", "en", "Completed", True),
    ]
    # load language id map
    cur.execute("select id, iso_639_1 from language_lookup")
    lang_by_code = dict(cur.fetchall())

    insert_rows: list[tuple[str, int, str, bool]] = []
    for ui_key, lang_code, value, is_default in rows:
        lid = lang_by_code.get(lang_code)
        if lid is None:
            continue
        insert_rows.append((ui_key, lid, value, is_default))

    insert_many(
        cur,
        """
        insert into ui_translation(ui_key, language_id, value, is_default)
        values %s
        """,
        insert_rows,
    )
    print("ui_translation rows inserted:", len(insert_rows))


def load_reference_code_map(cur) -> dict[str, dict[str, int]]:
    cur.execute(
        """
        select domain, code, id
        from reference_code
        where is_active = true
        """
    )
    result: dict[str, dict[str, int]] = {}
    for domain, code, rid in cur.fetchall():
        result.setdefault(domain, {})[code] = rid
    return result


def main() -> None:
    dsn = dsn_from_env()
    print("connecting to", dsn)
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            load_reference_codes(cur)
            load_countries(cur)
            load_states(cur)
            load_cities(cur)
            load_skills(cur)
            load_industries(cur)
            load_job_roles(cur)
            load_employment_type(cur)
            load_work_type(cur)
            load_languages(cur)

            ref_map = load_reference_code_map(cur)
            load_qualifications(cur, ref_map)
            load_ui_translations(cur)

        conn.commit()
        print("master reference load committed")
    except Exception as e:
        conn.rollback()
        print("master reference load failed, rolled back:", e, file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
