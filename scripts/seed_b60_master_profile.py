#!/usr/bin/env python3
"""
B60 Seed: Master reference data + 1,000,000 candidate profiles at laptop scale.

Seeds:
  - ALL reference_code domains (every enum the schema references)
  - country / state / city
  - skill / industry / job_role
  - employment_type / work_type / language_lookup
  - qualification
  - ui_translation (English)
  - 1,000,000 candidate_identity rows with multilingual names and deliberate duplicates
  - candidate_contact, candidate_skill, candidate_language, assessment
  - candidate_education, candidate_work_experience, resume_version, profile_project
  - course_enrolment, profile_completion_score, candidate_activity_log

Duplicates: a fraction of candidates share first_name+last_name pairs intentionally.
Multilingual: names drawn from en_US, hi_IN, es_ES, fr_FR, de_DE, zh_CN locales.

Run against the connected postgres with:
  PG_DSN=postgres://talentradb:changeme@localhost:5431/talentra python scripts/seed_b60_master_profile.py

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
NUM_CANDIDATES = 1_000_000  # full target; script is resumable — runs only the deficit

BATCH = 10_000          # batch size for execute_values on core tables
BATCH_LARGE = 30_000    # larger batches for child tables (skills, languages, etc.)

SEED = 42
DEDUP_RATE = 0.05       # 5% of candidates share a name pair with another candidate

DSN = os.environ.get("PG_DSN", "dbname=talentra user=talentradb password=changeme host=localhost port=5431")


# ---------------------------------------------------------------------------
# Reference code domains — exhaustive list covering every schema enum
# ---------------------------------------------------------------------------
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
    "workflow_pipeline": [
        ("applied", "workflow.pipeline.applied", 10),
        ("shortlisted", "workflow.pipeline.shortlisted", 20),
        ("interviewed", "workflow.pipeline.interviewed", 30),
        ("offered", "workflow.pipeline.offered", 40),
        ("joined", "workflow.pipeline.joined", 50),
        ("rejected", "workflow.pipeline.rejected", 60),
    ],
    "swipe_action": [
        ("right", "swipe_action.right", 10),
        ("left", "swipe_action.left", 20),
    ],
    "employment_type_code": [
        ("full_time", "employment_type_code.full_time", 10),
        ("part_time", "employment_type_code.part_time", 20),
        ("contract", "employment_type_code.contract", 30),
    ],
    "work_type_code": [
        ("onsite", "work_type_code.onsite", 10),
        ("remote", "work_type_code.remote", 20),
        ("hybrid", "work_type_code.hybrid", 30),
    ],
}


def insert_many(cur, sql, rows, page_size=10_000):
    if not rows:
        return 0
    psycopg2.extras.execute_values(cur, sql, rows, page_size=page_size)
    return len(rows)


def now():
    return "now()"


# ---------------------------------------------------------------------------
# Lookup data
# ---------------------------------------------------------------------------
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
    ("IT", "ITA", "Italy", "380"),
    ("NL", "NLD", "Netherlands", "528"),
    ("SE", "SWE", "Sweden", "752"),
    ("NO", "NOR", "Norway", "578"),
    ("DK", "DNK", "Denmark", "208"),
    ("PL", "POL", "Poland", "908"),
    ("MX", "MEX", "Mexico", "484"),
    ("AR", "ARG", "Argentina", "32"),
    ("ZA", "ZAF", "South Africa", "710"),
    ("NG", "NGA", "Nigeria", "566"),
    ("EG", "EGY", "Egypt", "818"),
    ("ID", "IDN", "Indonesia", "360"),
    ("PH", "PHL", "Philippines", "608"),
    ("VN", "VNM", "Vietnam", "704"),
    ("TH", "THA", "Thailand", "764"),
    ("MY", "MYS", "Malaysia", "458"),
]

COUNTRIES_STATES = {
    "US": ["California", "Texas", "New York", "Illinois", "Florida", "Washington", "Massachusetts", "Colorado", "Arizona", "Georgia"],
    "IN": ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Telangana", "West Bengal", "Gujarat", "Punjab", "Uttar Pradesh", "Kerala"],
    "GB": ["England", "Scotland", "Wales", "Northern Ireland"],
    "CA": ["Ontario", "British Columbia", "Quebec", "Alberta", "Manitoba"],
    "AU": ["New South Wales", "Victoria", "Queensland", "Western Australia", "South Australia"],
    "DE": ["Bavaria", "North Rhine-Westphalia", "Berlin", "Hamburg", "Baden-Württemberg"],
    "FR": ["Ile-de-France", "Provence-Alpes-Cote d'Azur", "Nouvelle-Aquitaine", "Occitanie", "Auvergne-Rhone-Alpes"],
    "ES": ["Catalonia", "Madrid", "Andalusia", "Valencia", "Basque Country"],
    "BR": ["Sao Paulo", "Rio de Janeiro", "Minas Gerais", "Rio Grande do Sul", "Parana"],
}

CITY_BATCH = {
    "US": [("California", ["San Francisco", "Los Angeles", "San Jose", "Sacramento", "Fremont"]),
           ("Texas", ["Austin", "Dallas", "Houston", "San Antonio", "Fort Worth"]),
           ("New York", ["New York", "Buffalo", "Rochester", "Yonkers", "Syracuse"]),
           ("Illinois", ["Chicago", "Aurora", "Naperville", "Joliet", "Springfield"]),
           ("Florida", ["Miami", "Orlando", "Tampa", "Jacksonville", "St. Petersburg"]),
           ("Washington", ["Seattle", "Spokane", "Tacoma", "Vancouver", "Bellevue"]),
           ("Massachusetts", ["Boston", "Worcester", "Cambridge", "Springfield", "Lowell"]),
           ("Colorado", ["Denver", "Colorado Springs", "Aurora", "Fort Collins", "Lakewood"]),
           ("Arizona", ["Phoenix", "Tucson", "Mesa", "Chandler", "Glendale"]),
           ("Georgia", ["Atlanta", "Augusta", "Columbus", "Savannah", "Athens"])],
    "IN": [("Maharashtra", ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik"]),
           ("Karnataka", ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belagavi"]),
           ("Delhi", ["New Delhi", "Delhi", "North Delhi", "South Delhi", "East Delhi"]),
           ("Tamil Nadu", ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"]),
           ("Telangana", ["Hyderabad", "Warangal", "Nizamabad", "Khammam", "Karimnagar"]),
           ("West Bengal", ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri"]),
           ("Gujarat", ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"]),
           ("Punjab", ["Chandigarh", "Ludhiana", "Amritsar", "Jalandhar", "Patiala"]),
           ("Uttar Pradesh", ["Lucknow", "Kanpur", "Ghaziabad", "Agra", "Noida"]),
           ("Kerala", ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Mangaluru"])],
    "GB": [("England", ["London", "Birmingham", "Manchester", "Leeds", "Glasgow"]),
           ("Scotland", ["Edinburgh", "Glasgow", "Aberdeen", "Dundee", "Inverness"]),
           ("Wales", ["Cardiff", "Swansea", "Newport", "Bangor", "St Davids"]),
           ("Northern Ireland", ["Belfast", "Derry", "Lisburn", "Newry", "Bangor"])],
    "CA": [("Ontario", ["Toronto", "Ottawa", "Hamilton", "London", "Windsor"]),
           ("British Columbia", ["Vancouver", "Surrey", "Richmond", "Burnaby", "Victoria"]),
           ("Quebec", ["Montreal", "Quebec City", "Laval", "Gatineau", "Sherbrooke"]),
           ("Alberta", ["Calgary", "Edmonton", "Red Deer", "Lethbridge", "Medicine Hat"]),
           ("Manitoba", ["Winnipeg", "Brandon", "Steinbach", "Thompson", "Portage la Prairie"])],
    "AU": [("New South Wales", ["Sydney", "Newcastle", "Wollongong", "Central Coast", "Coffs Harbour"]),
           ("Victoria", ["Melbourne", "Geelong", "Ballarat", "Bendigo", "Shepparton"]),
           ("Queensland", ["Brisbane", "Gold Coast", "Sunshine Coast", "Cairns", "Townsville"]),
           ("Western Australia", ["Perth", "Fremantle", "Joondalup", "Rockingham", "Albany"]),
           ("South Australia", ["Adelaide", "Mount Gambier", "Whyalla", "Murray Bridge", "Port Lincoln"])],
    "DE": [("Bavaria", ["Munich", "Nuremberg", "Augsburg", "Wuerzburg", "Regensburg"]),
           ("North Rhine-Westphalia", ["Cologne", "Dusseldorf", "Dortmund", "Essen", "Duisburg"]),
           ("Berlin", ["Berlin", "Lichtenberg", "Charlottenburg", "Neukölln", "Pankow"]),
           ("Hamburg", ["Hamburg", "Hamburg-Süd", "Hamburg-Nord", "Hamburg-West", "Hamburg-Ost"]),
           ("Baden-Württemberg", ["Stuttgart", "Karlsruhe", "Mannheim", "Freiburg", "Heidelberg"])],
    "FR": [("Ile-de-France", ["Paris", "Boulogne-Billancourt", "Saint-Denis", "Argenteuil", "Montreuil"]),
           ("Provence-Alpes-Cote d'Azur", ["Marseille", "Nice", "Toulon", "Aix-en-Provence", "Cannes"]),
           ("Nouvelle-Aquitaine", ["Bordeaux", "Limoges", "Poitiers", "La Rochelle", "Pau"]),
           ("Occitanie", ["Toulouse", "Montpellier", "Narbonne", "Perpignan", "Albi"]),
           ("Auvergne-Rhone-Alpes", ["Lyon", "Grenoble", "Saint-Etienne", "Clermont-Ferrand", "Valence"])],
    "ES": [("Catalonia", ["Barcelona", "Tarragona", "Girona", "Lleida", "Mataro"]),
           ("Madrid", ["Madrid", "Alcala de Henares", "Fuenlabrada", "Leganes", "Getafe"]),
           ("Andalusia", ["Seville", "Malaga", "Cordoba", "Cadiz", "Granada"]),
           ("Valencia", ["Valencia", "Alicante", "Castellon de la Plana", "El Puig", "Paterna"]),
           ("Basque Country", ["Bilbao", "Gasteiz", "Donostia", "Eibar", "Tolosa"])],
}

SKILLS = [
    ("Python", "Programming"), ("Java", "Programming"), ("JavaScript", "Programming"),
    ("TypeScript", "Programming"), ("C#", "Programming"), ("C++", "Programming"),
    ("Go", "Programming"), ("Rust", "Programming"), ("SQL", "Data"),
    ("PostgreSQL", "Data"), ("MySQL", "Data"), ("Oracle", "Data"),
    ("MongoDB", "Data"), ("Redis", "Data"), ("Elasticsearch", "Data"),
    ("Kubernetes", "Infrastructure"), ("Docker", "Infrastructure"),
    ("Terraform", "Infrastructure"), ("Ansible", "Infrastructure"),
    ("AWS", "Cloud"), ("Azure", "Cloud"), ("GCP", "Cloud"),
    ("React", "Frontend"), ("Angular", "Frontend"), ("Vue.js", "Frontend"),
    ("Node.js", "Backend"), ("Django", "Backend"), ("Flask", "Backend"),
    ("Spring Boot", "Backend"), ("Data Engineering", "Data"),
    ("Machine Learning", "Data"), ("DevOps", "Infrastructure"),
    ("Project Management", "Management"), ("Agile", "Process"),
    ("Scrum", "Process"), ("Communication", "Soft Skills"),
    ("Leadership", "Soft Skills"), ("SQL Server", "Data"),
    ("Ruby", "Programming"), ("Swift", "Programming"), ("Kotlin", "Programming"),
    ("PHP", "Programming"), ("Perl", "Programming"), ("R", "Data"),
    ("Tableau", "Data"), ("Power BI", "Data"), ("Spark", "Data"),
    ("Hadoop", "Data"), ("Airflow", "Data"), ("dbt", "Data"),
    ("Figma", "Design"), ("Sketch", "Design"), ("Adobe XD", "Design"),
    ("HTML", "Frontend"), ("CSS", "Frontend"), ("SASS", "Frontend"),
]

INDUSTRIES = [
    "Technology", "Financial Services", "Healthcare", "Consulting", "Retail",
    "Manufacturing", "Media", "Education", "Logistics", "Real Estate",
    "Telecom", "Construction", "Energy", "Pharmaceuticals", "Hospitality",
    "Automotive", "Aerospace", "Government", "Non-profit", "Insurance",
]

JOB_ROLES = [
    "Software Engineer", "Data Engineer", "DevOps Engineer", "Frontend Developer",
    "Backend Developer", "Full Stack Developer", "AI / ML Engineer",
    "Data Scientist", "Machine Learning Engineer", "Solution Architect",
    "Product Manager", "Project Manager", "Business Analyst", "Recruiter",
    "Talent Acquisition Partner", "Technical Recruiter", "Consultant",
    "Account Manager", "Sales Engineer", "Cloud Engineer", "Security Engineer",
    "Database Administrator", "QA Engineer", "UX Designer", "Scrum Master",
    "Engineering Manager", "VP of Engineering", "CTO", "Chief Data Officer",
    "Designer", "Content Writer", "Marketing Manager", "HR Manager",
    "Finance Manager", "Operations Manager",
]

EMPLOYMENT_TYPES = [
    ("full_time", "employment_type.full_time", 10),
    ("part_time", "employment_type.part_time", 20),
    ("contract", "employment_type.contract", 30),
    ("internship", "employment_type.internship", 40),
]

WORK_TYPES = [
    ("onsite", "work_type.onsite", 10),
    ("remote", "work_type.remote", 20),
    ("hybrid", "work_type.hybrid", 30),
]

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
    ("nl", "nld", "Dutch"),
    ("sv", "swe", "Swedish"),
    ("pl", "pol", "Polish"),
    ("tr", "tur", "Turkish"),
    ("th", "tha", "Thai"),
    ("vi", "vie", "Vietnamese"),
    ("id", "ind", "Indonesian"),
    ("ms", "msa", "Malay"),
]

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
    ("BTech", "Bachelor of Technology", "undergraduate"),
    ("MTech", "Master of Technology", "postgraduate"),
    ("MCA", "Master of Computer Applications", "postgraduate"),
    ("BPharm", "Bachelor of Pharmacy", "undergraduate"),
    ("MPharm", "Master of Pharmacy", "postgraduate"),
    ("MBBS", "Bachelor of Medicine", "undergraduate"),
    ("BArch", "Bachelor of Architecture", "undergraduate"),
    ("MArch", "Master of Architecture", "postgraduate"),
    ("LLB", "Bachelor of Laws", "undergraduate"),
    ("LLM", "Master of Laws", "postgraduate"),
]

EDUCATION_INSTITUTIONS = [
    "Massachusetts Institute of Technology",
    "Stanford University",
    "University of Oxford",
    "University of Cambridge",
    "Harvard University",
    "Indian Institute of Technology Bombay",
    "Indian Institute of Technology Delhi",
    "Indian Institute of Science",
    "National University of Singapore",
    "University of Tokyo",
    "Peking University",
    "Tsinghua University",
    "ETH Zurich",
    "Technical University of Munich",
    "Sorbonne University",
    "University of Barcelona",
    "University of Melbourne",
    "University of Toronto",
    "University of British Columbia",
    "Seoul National University",
    "Delhi University",
    "Mumbai University",
    "Osmania University",
    "University of Calcutta",
    "Anna University",
    "Jadavpur University",
    "University of Hyderabad",
    "Birla Institute of Technology",
    "Vellore Institute of Technology",
    "Amity University",
]

INSTITUTION_TYPES = [
    ("university", "institution.type.university", 10),
    ("college", "institution.type.college", 20),
    ("institute", "institution.type.institute", 30),
]

WORK_EXPERIENCE_COMPANIES = [
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Tesla",
    "Goldman Sachs", "JPMorgan Chase", "Citigroup", "Morgan Stanley",
    "Johnson & Johnson", "Pfizer", "Roche", "Novartis", "AstraZeneca",
    "Accenture", "Deloitte", "PwC", "EY", "KPMG",
    "Tata Consultancy Services", "Infosys", "Wipro", "HCL Technologies",
    "Tech Mahindra", "Zomato", "Swiggy", "Flipkart", "Paytm",
    "Reliance Industries", "Adani Group", "HDFC Bank", "ICICI Bank",
    "State Bank of India", "HSBC", "Barclays", "Deutsche Bank",
    "Siemens", "Bosch", "BMW", "Mercedes-Benz", "Volkswagen",
    "Airbus", "Boeing", "Lockheed Martin", "SpaceX",
    "Samsung", "Sony", "LG", "Huawei", "Tencent",
    "Grab", "Sea Limited", "Gojek", "Tokopedia",
    "StartUp Inc", "Nebula Labs", "Quantum Dynamics", "DataFlow Systems",
    "CloudNine Solutions", "NeuralMind AI", "GreenEnergy Corp",
]

ACTIVITY_TYPES = [
    ("login", "activity.login", 10),
    ("profile_update", "activity.profile_update", 20),
    ("resume_download", "activity.resume_download", 30),
]


# ===========================================================================
# Main
# ===========================================================================
def main():
    random.seed(SEED)
    print("=== B60 Seed: Master Reference + 1M Candidate Profiles ===\n")

    conn = psycopg2.connect(DSN)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    try:
        # ------------------------------------------------------------------
        # 1. Reference codes
        # ------------------------------------------------------------------
        print("[1/11] Loading reference_code domains...")
        n_refs = _load_reference_codes(cur)
        print(f"  reference_code: {n_refs} new rows")
        conn.commit()

        # ------------------------------------------------------------------
        # 2. Country / State / City
        # ------------------------------------------------------------------
        print("[2/11] Loading geography...")
        n_countries = _load_countries(cur)
        print(f"  country: {n_countries} new rows")
        conn.commit()

        country_by_iso = _get_country_map(cur)

        n_states = _load_states(cur, country_by_iso)
        print(f"  state: {n_states} new rows")
        conn.commit()

        state_by_country_name = _get_state_map(cur)

        n_cities = _load_cities(cur, country_by_iso, state_by_country_name)
        print(f"  city: {n_cities} new rows")
        conn.commit()

        # ------------------------------------------------------------------
        # 3. Skills / Industries / Job Roles
        # ------------------------------------------------------------------
        print("[3/11] Loading skills, industries, job roles...")
        n_skills = _load_skills(cur)
        print(f"  skill: {n_skills} new rows")
        conn.commit()

        n_ind = _load_industries(cur)
        print(f"  industry: {n_ind} new rows")
        conn.commit()

        n_roles = _load_job_roles(cur)
        print(f"  job_role: {n_roles} new rows")
        conn.commit()

        # ------------------------------------------------------------------
        # 4. Employment / Work types / Languages / Qualifications
        # ------------------------------------------------------------------
        print("[4/11] Loading employment_type, work_type, language_lookup...")
        n_emp = _load_employment_types(cur)
        print(f"  employment_type: {n_emp} new rows")
        conn.commit()

        n_wt = _load_work_types(cur)
        print(f"  work_type: {n_wt} new rows")
        conn.commit()

        n_langs = _load_languages(cur)
        print(f"  language_lookup: {n_langs} new rows")
        conn.commit()

        n_quals = _load_qualifications(cur)
        print(f"  qualification: {n_quals} new rows")
        conn.commit()

        n_inst_types = _load_institution_types(cur)
        print(f"  institution_type: {n_inst_types} new rows")
        conn.commit()

        # ------------------------------------------------------------------
        # 5. UI translations (English)
        # ------------------------------------------------------------------
        print("[5/11] Loading ui_translation (English)...")
        lang_id_en = _get_english_language_id(cur)
        if lang_id_en:
            n_ui = _load_ui_translations(cur, lang_id_en)
            print(f"  ui_translation: {n_ui} new rows")
        else:
            print("  [SKIP] no English language row")
        conn.commit()

        # ------------------------------------------------------------------
        # 6. Tenant / Users / Employers
        # ------------------------------------------------------------------
        print("[6/11] Ensuring tenant, users, employers...")
        _ensure_tenant(cur)
        conn.commit()

        _ensure_users(cur, NUM_CANDIDATES + 10_000)
        conn.commit()

        _ensure_employers(cur)
        conn.commit()

        user_ids = _get_all_user_ids(cur)
        employer_ids = _get_verified_employer_ids(cur)
        print(f"  users: {len(user_ids):,}")
        print(f"  verified employers: {len(employer_ids):,}")

        # ------------------------------------------------------------------
        # 7. Candidate profiles (the big one)
        # ------------------------------------------------------------------
        print(f"\n[7/11] Seeding {NUM_CANDIDATES:,} candidate profiles...")
        existing = _count(cur, "candidate_identity")
        print(f"  candidate_identity: {existing:,} existing")
        if existing >= NUM_CANDIDATES:
            print("  Already at target — skipping candidate insert.")
        else:
            to_add = NUM_CANDIDATES - existing
            print(f"  Adding {to_add:,} candidates in batches of {BATCH:,}...")
            _seed_candidates(cur, to_add, user_ids)
        conn.commit()
        total_cids = _count(cur, "candidate_identity")
        print(f"  candidate_identity total: {total_cids:,}")

        all_cids = _get_all_candidate_ids(cur)

        # ------------------------------------------------------------------
        # 8. Candidate child tables
        # ------------------------------------------------------------------
        print(f"\n[8/11] Seeding candidate_contact ({total_cids:,} candidates)...")
        existing_cc = _count(cur, "candidate_contact")
        if existing_cc < total_cids:
            _seed_contacts(cur, all_cids, existing_cc)
        conn.commit()
        print(f"  candidate_contact: {_count(cur, 'candidate_contact'):,}")

        print("Seeding candidate_skill...")
        existing_cs = _count(cur, "candidate_skill")
        if existing_cs < total_cids:
            _seed_skills(cur, all_cids, existing_cs)
        conn.commit()
        print(f"  candidate_skill: {_count(cur, 'candidate_skill'):,}")

        print("Seeding candidate_language...")
        existing_cl = _count(cur, "candidate_language")
        if existing_cl < total_cids:
            _seed_languages(cur, all_cids, existing_cl)
        conn.commit()
        print(f"  candidate_language: {_count(cur, 'candidate_language'):,}")

        print("Seeding assessment...")
        existing_as = _count(cur, "assessment")
        if existing_as < total_cids:
            _seed_assessments(cur, all_cids, existing_as)
        conn.commit()
        print(f"  assessment: {_count(cur, 'assessment'):,}")

        print("Seeding candidate_education...")
        existing_ce = _count(cur, "candidate_education")
        if existing_ce < total_cids:
            _seed_education(cur, all_cids, existing_ce)
        conn.commit()
        print(f"  candidate_education: {_count(cur, 'candidate_education'):,}")

        print("Seeding candidate_work_experience...")
        existing_cw = _count(cur, "candidate_work_experience")
        if existing_cw < total_cids:
            _seed_work_experience(cur, all_cids, existing_cw)
        conn.commit()
        print(f"  candidate_work_experience: {_count(cur, 'candidate_work_experience'):,}")

        print("Seeding resume_version...")
        existing_rv = _count(cur, "resume_version")
        if existing_rv < total_cids:
            _seed_resume_versions(cur, all_cids, existing_rv)
        conn.commit()
        print(f"  resume_version: {_count(cur, 'resume_version'):,}")

        print("Seeding profile_project...")
        existing_pp = _count(cur, "profile_project")
        if existing_pp < total_cids:
            _seed_profile_projects(cur, all_cids, existing_pp)
        conn.commit()
        print(f"  profile_project: {_count(cur, 'profile_project'):,}")

        print("Seeding course_enrolment...")
        existing_cen = _count(cur, "course_enrolment")
        if existing_cen < total_cids:
            _seed_course_enrolments(cur, all_cids, existing_cen)
        conn.commit()
        print(f"  course_enrolment: {_count(cur, 'course_enrolment'):,}")

        print("Seeding profile_completion_score...")
        existing_pcs = _count(cur, "profile_completion_score")
        if existing_pcs < total_cids:
            _seed_profile_completion(cur, all_cids, existing_pcs)
        conn.commit()
        print(f"  profile_completion_score: {_count(cur, 'profile_completion_score'):,}")

        print("Seeding candidate_activity_log...")
        existing_cal = _count(cur, "candidate_activity_log")
        if existing_cal < total_cids:
            _seed_activity_log(cur, all_cids, existing_cal)
        conn.commit()
        print(f"  candidate_activity_log: {_count(cur, 'candidate_activity_log'):,}")

        # ------------------------------------------------------------------
        # Final summary
        # ------------------------------------------------------------------
        print("\n=== FINAL TABLE COUNTS ===")
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
            "institution_type",
            "ui_translation",
            "tenant_account",
            "users",
            "employer_organisation",
            "candidate_identity",
            "candidate_contact",
            "candidate_skill",
            "candidate_language",
            "assessment",
            "candidate_education",
            "candidate_work_experience",
            "resume_version",
            "profile_project",
            "course_enrolment",
            "profile_completion_score",
            "candidate_activity_log",
        ]:
            cur.execute(f"SELECT count(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]:,}")

        # Duplicate check
        print("\n=== DUPLICATE NAME PAIRS ===")
        cur.execute(
            "SELECT first_name, last_name, count(*) as cnt "
            "FROM candidate_identity "
            "WHERE deleted_at IS NULL "
            "GROUP BY first_name, last_name "
            "HAVING count(*) > 1 "
            "ORDER BY cnt DESC "
            "LIMIT 10"
        )
        dupes = cur.fetchall()
        if dupes:
            print(f"  {len(dupes)} name pairs shared by >1 candidate (top 10):")
            for fn, ln, cnt in dupes:
                print(f"    '{fn} {ln}': {cnt} candidates")
        else:
            print("  No duplicate name pairs found (unexpected for this seed)")

        # Multilingual check
        print("\n=== MULTILINGUAL NAME LOCALES (sample) ===")
        cur.execute(
            "SELECT profile_status_code, count(*) FROM candidate_identity GROUP BY profile_status_code"
        )
        # We track locale via the random selection; show a sample of names
        cur.execute(
            "SELECT first_name, last_name FROM candidate_identity "
            "WHERE deleted_at IS NULL "
            "ORDER BY random() LIMIT 10"
        )
        for fn, ln in cur.fetchall():
            print(f"  {fn} {ln}")

    except Exception:
        conn.rollback()
        print("B60 SEED FAILED — rolled back", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()
    print("\nB60 seed completed!")


# ===========================================================================
# Reference data loaders
# ===========================================================================
def _load_reference_codes(cur):
    rows = []
    for domain, items in REFERENCE_CODE_DOMAINS.items():
        for code, display_name_key, sort_order in items:
            rows.append((domain, code, display_name_key, True, sort_order))
    return insert_many(
        cur,
        "INSERT INTO reference_code(domain, code, display_name_key, is_active, sort_order) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
    )


def _load_countries(cur):
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
        "INSERT INTO country(iso_alpha2, iso_alpha3, name, iso_numeric, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


def _get_country_map(cur):
    cur.execute("SELECT id, iso_alpha2 FROM country")
    return {row[1]: row[0] for row in cur.fetchall()}


def _load_states(cur, country_by_iso):
    existing = set()
    cur.execute("SELECT country_id, name FROM state")
    for row in cur.fetchall():
        existing.add((row[0], row[1]))
    rows = []
    for country_iso, state_names in COUNTRIES_STATES.items():
        country_id = country_by_iso.get(country_iso)
        if country_id is None:
            continue
        for state_name in state_names:
            if (country_id, state_name) not in existing:
                rows.append((country_id, state_name, True, 0, now(), 0, now(), 0))
    return insert_many(
        cur,
        "INSERT INTO state(country_id, name, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        rows,
    )


def _get_state_map(cur):
    cur.execute("SELECT id, country_id, name FROM state")
    return {(row[1], row[2]): row[0] for row in cur.fetchall()}


def _load_cities(cur, country_by_iso, state_by_country_name):
    existing = set()
    cur.execute("SELECT country_id, name FROM city")
    for row in cur.fetchall():
        existing.add((row[0], row[1]))
    rows = []
    seen = set()  # dedup by (country_id, city_name) across states
    for country_iso, state_groups in CITY_BATCH.items():
        country_id = country_by_iso.get(country_iso)
        if country_id is None:
            continue
        for state_name, city_names in state_groups:
            state_id = state_by_country_name.get((country_id, state_name))
            if state_id is None:
                continue
            for city_name in city_names:
                key = (country_id, city_name)
                if key not in existing and key not in seen:
                    seen.add(key)
                    rows.append((country_id, state_id, city_name, None, None, None, None,
                                  True, 0, now(), 0, now(), 0))
    return insert_many(
        cur,
        "INSERT INTO city(country_id, state_id, name, latitude, longitude, coordinates_source, "
        "timezone, is_active, sort_order, created_at, created_by, updated_at, updated_by) VALUES %s",
        rows,
    )


def _load_skills(cur):
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
        "INSERT INTO skill(name, category, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


def _load_industries(cur):
    existing = set()
    cur.execute("SELECT name FROM industry")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        (name, True, 0, now(), 0, now(), 0)
        for name in INDUSTRIES if name not in existing
    ]
    return insert_many(
        cur,
        "INSERT INTO industry(name, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


def _load_job_roles(cur):
    existing = set()
    cur.execute("SELECT name FROM job_role")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        (name, True, 0, now(), 0, now(), 0)
        for name in JOB_ROLES if name not in existing
    ]
    return insert_many(
        cur,
        "INSERT INTO job_role(name, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


def _load_employment_types(cur):
    existing = set()
    cur.execute("SELECT code FROM employment_type")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [t for t in EMPLOYMENT_TYPES if t[0] not in existing]
    return insert_many(
        cur,
        "INSERT INTO employment_type(code, display_name_key, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


def _load_work_types(cur):
    existing = set()
    cur.execute("SELECT code FROM work_type")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [t for t in WORK_TYPES if t[0] not in existing]
    return insert_many(
        cur,
        "INSERT INTO work_type(code, display_name_key, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


def _load_languages(cur):
    existing = set()
    cur.execute("SELECT iso_639_1 FROM language_lookup")
    for row in cur.fetchall():
        existing.add(row[0])
    tups = [
        (iso1, iso3, name, True, idx * 10 + 10, now(), 0, now(), 0)
        for idx, (iso1, iso3, name) in enumerate(LANGUAGES)
        if iso1 not in existing
    ]
    return insert_many(
        cur,
        "INSERT INTO language_lookup(iso_639_1, iso_639_3, name, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


def _load_qualifications(cur):
    edu_codes = {}
    cur.execute("SELECT code FROM reference_code WHERE domain = 'education_level'")
    for row in cur.fetchall():
        edu_codes[row[0]] = row[0]
    missing = [el for el in ["secondary", "undergraduate", "postgraduate", "doctorate"]
               if el not in edu_codes]
    if missing:
        print(f"  [WARN] education_level codes missing: {missing}")
        return 0
    existing = set()
    cur.execute("SELECT code FROM qualification")
    for row in cur.fetchall():
        existing.add(row[0])
    rows = []
    for code, name, edu_level in QUALIFICATIONS:
        if code not in existing and edu_level in edu_codes:
            rows.append((code, name, edu_level, True, 0, now(), 0, now(), 0))
    return insert_many(
        cur,
        "INSERT INTO qualification(code, name, education_level_code, is_active, sort_order, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        rows,
    )


def _load_institution_types(cur):
    existing = set()
    cur.execute("SELECT code FROM reference_code WHERE domain = 'institution_type'")
    for row in cur.fetchall():
        existing.add(row[0])
    rows = [t for t in INSTITUTION_TYPES if t[0] not in existing]
    if not rows:
        return 0
    # institution_type may not exist as its own table — store in reference_code instead
    return insert_many(
        cur,
        "INSERT INTO reference_code(domain, code, display_name_key, is_active, sort_order) "
        "VALUES %s ON CONFLICT DO NOTHING",
        [(domain, code, display_name_key, True, sort_order)
         for code, display_name_key, sort_order in rows
         for domain in ["institution_type"]],
    )


def _get_english_language_id(cur):
    cur.execute("SELECT id FROM language_lookup WHERE iso_639_1 = 'en'")
    row = cur.fetchone()
    return row[0] if row else None


def _load_ui_translations(cur, language_id_en):
    existing = set()
    cur.execute("SELECT ui_key FROM ui_translation WHERE language_id = %s", (language_id_en,))
    for row in cur.fetchall():
        existing.add(row[0])

    ui_rows = [
        ("candidate.status.active", "Active"),
        ("candidate.status.inactive", "Inactive"),
        ("candidate.status.pending", "Pending"),
        ("candidate.status.suspended", "Suspended"),
        ("profile.type.permanent", "Permanent"),
        ("profile.type.temporary", "Temporary"),
        ("profile.type.gig", "Gig"),
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
        ("skill.source.self", "Self-declared"),
        ("skill.source.assessment", "Assessment"),
        ("fluency.basic", "Basic"),
        ("fluency.conversational", "Conversational"),
        ("fluency.fluent", "Fluent"),
        ("language_proficiency.basic", "Basic"),
        ("language_proficiency.working", "Working"),
        ("language_proficiency.proficient", "Proficient"),
        ("activity.login", "Login"),
        ("activity.profile_update", "Profile update"),
        ("activity.resume_download", "Resume download"),
        ("shortlist.action.added", "Added"),
        ("shortlist.action.removed", "Removed"),
        ("referral.type.candidate", "Candidate"),
        ("referral.status.pending", "Pending"),
        ("referral.status.hired", "Hired"),
        ("job_status.draft", "Draft"),
        ("job_status.published", "Published"),
        ("job_status.closed", "Closed"),
        ("job_visibility.public", "Public"),
        ("job_visibility.private", "Private"),
        ("question.type.text", "Text"),
        ("question.type.multiple_choice", "Multiple choice"),
        ("credential.type.password", "Password"),
        ("credential.status.active", "Active"),
        ("credential.status.locked", "Locked"),
        ("account.type.platform", "Platform"),
        ("account.type.employer", "Employer"),
        ("account.status.active", "Active"),
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
        ("licence.type.standard", "Standard"),
        ("licence.type.enterprise", "Enterprise"),
        ("licence.status.active", "Active"),
        ("device.type.desktop", "Desktop"),
        ("device.type.mobile", "Mobile"),
        ("revocation.reason.user_request", "User request"),
        ("plan.category.free", "Free"),
        ("plan.category.paid", "Paid"),
        ("billing.period.monthly", "Monthly"),
        ("renewal.type.auto", "Auto"),
        ("entitlement.unit.count", "Count"),
        ("payment.method.card", "Card"),
        ("payment.status.initiated", "Initiated"),
        ("payment.status.completed", "Completed"),
        ("invoice.status.issued", "Issued"),
        ("refund.status.requested", "Requested"),
        ("refund.type.full", "Full"),
        ("wallet.status.active", "Active"),
        ("wallet.tx.recharge", "Recharge"),
        ("wallet.tx.debit", "Debit"),
        ("wallet.ref.payment_order", "Payment order"),
        ("download.format.pdf", "PDF"),
        ("subscription.status.trial", "Trial"),
        ("subscription.status.active", "Active"),
        ("notification.channel.email", "Email"),
        ("notification.type.job_alert", "Job alert"),
        ("alert.frequency.immediate", "Immediate"),
        ("alert.frequency.daily", "Daily"),
        ("setting.type.boolean", "Boolean"),
        ("community.type.discussion", "Discussion"),
        ("post.visibility.public", "Public"),
        ("reaction.type.like", "Like"),
        ("support.category.billing", "Billing"),
        ("support.priority.low", "Low"),
        ("support.status.open", "Open"),
        ("faq.category.general", "General"),
        ("outreach.channel.email", "Email"),
        ("delivery.status.pending", "Pending"),
        ("delivery.status.sent", "Sent"),
        ("gig_worker.status.active", "Active"),
        ("rate.time.hour", "Hour"),
        ("handoff.system.external_fulfillment", "External fulfillment"),
        ("fulfillment.status.pending", "Pending"),
        ("pricing.model.fixed", "Fixed"),
        ("pricing.model.rate", "Rate"),
        ("earnings.type.estimated", "Estimated"),
        ("source.system.external_fulfillment", "External fulfillment"),
        ("employer_organisation.size.small", "Small"),
        ("consultant_decision.type.accepted", "Accepted"),
        ("sourcing.status.open", "Open"),
        ("pipeline.stage.applied", "Applied"),
        ("pipeline.stage.shortlisted", "Shortlisted"),
        ("pipeline.stage.interviewed", "Interviewed"),
        ("pipeline.stage.offered", "Offered"),
        ("pipeline.stage.joined", "Joined"),
        ("pipeline.stage.rejected", "Rejected"),
        ("source.channel.organic", "Organic"),
        ("source.channel.referral", "Referral"),
        ("application.channel.portal", "Portal"),
        ("institution.type.university", "University"),
        ("recruiter_mapping.type.direct", "Direct"),
        ("account_admin.role.owner", "Owner"),
        ("employer.type.small", "Small"),
        ("employer.type.medium", "Medium"),
        ("company.size.1_to_10", "1-10"),
        ("seat.status.allocated", "Allocated"),
        ("tax_identifier.type.tax_id", "Tax ID"),
        ("verification.type.identity", "Identity"),
        ("verification.status.pending", "Pending"),
        ("login.result.success", "Success"),
        ("login.result.failed", "Failed"),
        ("event.login", "Login"),
        ("blocked_party.candidate", "Candidate"),
        ("entitlement.job_posts", "Job posts"),
        ("entitlement.downloads", "Downloads"),
        ("assessment.type.aptitude", "Aptitude"),
        ("assessment.type.technical", "Technical"),
        ("assessment.type.behavioral", "Behavioral"),
        ("assessment.category.reasoning", "Reasoning"),
        ("assessment.category.coding", "Coding"),
        ("assessment.category.communication", "Communication"),
        ("course.category.technical", "Technical"),
        ("course.category.management", "Management"),
        ("course.category.certification", "Certification"),
        ("course.level.beginner", "Beginner"),
        ("course.level.intermediate", "Intermediate"),
        ("course.level.advanced", "Advanced"),
        ("enrolment.status.enrolled", "Enrolled"),
        ("enrolment.status.completed", "Completed"),
        ("enrolment.status.dropped", "Dropped"),
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

    tups = [
        (ui_key, language_id_en, value, True, now(), 0, now(), 0)
        for ui_key, value in ui_rows
        if ui_key not in existing
    ]
    return insert_many(
        cur,
        "INSERT INTO ui_translation(ui_key, language_id, value, is_default, "
        "created_at, created_by, updated_at, updated_by) VALUES %s",
        tups,
    )


# ===========================================================================
# Tenant / Users / Employers
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
        print("  tenant_account: created")
    else:
        print("  tenant_account: exists")


def _ensure_users(cur, n_needed):
    cur.execute("SELECT count(*) FROM users")
    existing = cur.fetchone()[0]
    print(f"  users: {existing:,} existing (need {n_needed:,})")
    if existing < n_needed:
        to_add = n_needed - existing
        cur.execute(
            "INSERT INTO users (actor_type_code, email, is_active, created_by, updated_by) "
            "SELECT 'candidate', 'candidate_' || (n + (SELECT coalesce(max(id),0) FROM users)) || '@example.com', "
            "true, 0, 0 FROM generate_series(1, %s) AS n ON CONFLICT DO NOTHING",
            (to_add,),
        )
        cur.execute("SELECT count(*) FROM users")
        print(f"  users after: {cur.fetchone()[0]:,}")


def _ensure_employers(cur):
    cur.execute("SELECT count(*) FROM employer_organisation WHERE is_verified = true")
    existing = cur.fetchone()[0]
    print(f"  verified employers: {existing:,}")
    if existing < 200:
        to_add = 200 - existing
        cur.execute(
            "INSERT INTO employer_organisation "
            "(tenant_account_id, company_name, type_code, country, is_verified, "
            "mapped_recruiter_count, created_by, updated_by) "
            "SELECT ta.id, 'Company ' || (n + (SELECT coalesce(max(id),0) FROM employer_organisation))::text, "
            "'small', 'IN', true, 0, 0, 0 "
            "FROM tenant_account ta, generate_series(1, %s) AS n "
            "WHERE ta.account_type_code = 'platform' ON CONFLICT DO NOTHING",
            (to_add,),
        )
        cur.execute("SELECT count(*) FROM employer_organisation WHERE is_verified = true")
        print(f"  verified employers after: {cur.fetchone()[0]:,}")


def _count(cur, table):
    cur.execute(f"SELECT count(*) FROM {table}")
    return cur.fetchone()[0]


def _get_all_user_ids(cur):
    cur.execute("SELECT id FROM users ORDER BY id")
    return [r[0] for r in cur.fetchall()]


def _get_verified_employer_ids(cur):
    cur.execute("SELECT id FROM employer_organisation WHERE is_verified = true")
    return [r[0] for r in cur.fetchall()]


def _get_all_candidate_ids(cur):
    cur.execute("SELECT id FROM candidate_identity ORDER BY id")
    return [r[0] for r in cur.fetchall()]


# ===========================================================================
# 1M Candidate Profiles
# ===========================================================================
def _seed_candidates(cur, to_add, user_ids):
    from faker import Faker

    Faker.seed(SEED)

    # Pre-generate all names in bulk per locale to avoid per-row Faker overhead.
    # For 1M candidates this is ~10x faster than calling f.first_name() per row.
    locales = ["en_US", "hi_IN", "es_ES", "fr_FR", "de_DE", "zh_CN"]
    locale_fakers = {loc: Faker(loc) for loc in locales}

    # Build a pool of duplicate name pairs (DEDUP_RATE of total will share names)
    dup_pool_size = int(to_add * DEDUP_RATE)
    dup_names = []
    for _ in range(dup_pool_size // 2):
        loc = random.choice(locales)
        f = locale_fakers[loc]
        dup_names.append((f.first_name()[:150], f.last_name()[:150]))

    # Pre-generate a large pool of (first, last) name pairs per locale
    NAME_POOL_SIZE = min(to_add * 2, 200_000)
    name_pool = []
    for _ in range(NAME_POOL_SIZE):
        loc = random.choice(locales)
        f = locale_fakers[loc]
        name_pool.append((f.first_name()[:150], f.last_name()[:150]))

    rows = []
    batch = []
    name_idx = 0
    dup_idx = 0

    for i in range(to_add):
        # Decide if this candidate gets a duplicate name
        if dup_idx < len(dup_names) and random.random() < DEDUP_RATE * 2:
            first_name, last_name = dup_names[dup_idx]
            dup_idx += 1
        else:
            first_name, last_name = name_pool[name_idx % len(name_pool)]
            name_idx += 1

        user_id = random.choice(user_ids)
        batch.append((
            user_id,
            None,
            first_name,
            None,
            last_name,
            None,
            None,
            random.choice(["male", "female", "non_binary", "prefer_not_to_say"]) if random.random() > 0.1 else None,
            random.choice(["active", "inactive", "pending", "suspended"]),
            round(random.uniform(20, 100), 2),
            datetime.now() - timedelta(days=random.randint(0, 365)),
        ))

        if len(batch) >= BATCH:
            _flush_candidate_batch(cur, batch)
            batch = []

    if batch:
        _flush_candidate_batch(cur, batch)


def _flush_candidate_batch(cur, batch):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO candidate_identity "
        "(user_id, title, first_name, middle_name, last_name, preferred_name, "
        "date_of_birth, gender, profile_status_code, profile_completion_score, "
        "latest_login_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        batch,
        page_size=len(batch),
    )


# ===========================================================================
# Candidate child tables — all batch-inserted
# ===========================================================================
def _seed_contacts(cur, candidate_ids, existing_count):
    """Insert contacts only for candidates missing them."""
    contact_types = ["email", "phone", "linkedin"]
    rows = []
    for cid in candidate_ids[existing_count:]:
        rows.append((
            cid,
            random.choice(contact_types),
            f"candidate_{cid}@example.com",
            "+1234567890",
            None,
            None, None, None, None, None, None,
            True,
            datetime.now(), 0, datetime.now(), 0, None,
        ))
        if len(rows) >= BATCH_LARGE:
            _flush_contacts(cur, rows)
            rows = []
    if rows:
        _flush_contacts(cur, rows)


def _flush_contacts(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO candidate_contact "
        "(candidate_id, contact_type_code, email, phone, phone_country_code, "
        "address_line1, address_line2, city, state, country, postal_code, "
        "is_primary, created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_skills(cur, candidate_ids, existing_count):
    skill_names = _get_skill_names(cur)
    proficiencies = _get_reference_codes(cur, "proficiency")
    rows = []
    for cid in candidate_ids[existing_count:]:
        for _ in range(random.randint(1, 5)):
            rows.append((
                cid,
                random.choice(skill_names),
                random.choice(proficiencies),
                round(random.uniform(0, 20), 1),
                datetime.now(), 0, datetime.now(), 0, None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_skills(cur, rows)
            rows = []
    if rows:
        _flush_skills(cur, rows)


def _flush_skills(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO candidate_skill "
        "(candidate_id, skill_name, proficiency, years_of_experience, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_languages(cur, candidate_ids, existing_count):
    language_names = _get_language_names(cur)
    proficiencies = ["basic", "intermediate", "advanced"]
    rows = []
    for cid in candidate_ids[existing_count:]:
        for _ in range(random.randint(1, 3)):
            rows.append((
                cid,
                random.choice(language_names),
                random.choice(proficiencies),
                random.choice([True, False]),
                datetime.now(), 0, datetime.now(), 0, None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_languages(cur, rows)
            rows = []
    if rows:
        _flush_languages(cur, rows)


def _flush_languages(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO candidate_language "
        "(candidate_id, language_name, proficiency, is_native, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_assessments(cur, candidate_ids, existing_count):
    assessment_types = _get_reference_codes(cur, "assessment_type")
    rows = []
    for cid in candidate_ids[existing_count:]:
        for _ in range(random.randint(0, 2)):
            rows.append((
                cid,
                random.choice(assessment_types),
                round(random.uniform(40, 100), 2),
                100,
                datetime.now() - timedelta(days=random.randint(0, 365)),
                datetime.now(), 0, datetime.now(), 0, None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_assessments(cur, rows)
            rows = []
    if rows:
        _flush_assessments(cur, rows)


def _flush_assessments(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO assessment "
        "(candidate_id, assessment_type_code, score, max_score, "
        "taken_at, created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_education(cur, candidate_ids, existing_count):
    institutions = EDUCATION_INSTITUTIONS
    quals = _get_qualification_codes(cur)
    edu_levels = _get_reference_codes(cur, "education_level")
    inst_types = _get_reference_codes(cur, "institution_type")
    rows = []
    for cid in candidate_ids[existing_count:]:
        n_entries = random.randint(1, 4)
        used_insts = set()
        for _ in range(n_entries):
            inst = random.choice(institutions)
            while inst in used_insts:
                inst = random.choice(institutions)
            used_insts.add(inst)
            start_year = random.randint(1990, 2025)
            end_year = start_year + random.randint(2, 6)
            rows.append((
                cid,
                inst,
                random.choice(quals) if quals else None,
                None,
                f"{start_year}-01-01",
                f"{end_year}-06-30",
                False,
                datetime.now(), 0, datetime.now(), 0, None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_education(cur, rows)
            rows = []
    if rows:
        _flush_education(cur, rows)


def _flush_education(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO candidate_education "
        "(candidate_id, institution_name, qualification, field_of_study, "
        "start_date, end_date, is_current, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_work_experience(cur, candidate_ids, existing_count):
    companies = WORK_EXPERIENCE_COMPANIES
    roles = JOB_ROLES[:15]
    rows = []
    for cid in candidate_ids[existing_count:]:
        n_entries = random.randint(1, 4)
        used_companies = set()
        for _ in range(n_entries):
            company = random.choice(companies)
            while company in used_companies:
                company = random.choice(companies)
            used_companies.add(company)
            start_year = random.randint(2000, 2025)
            end_year = start_year + random.randint(1, 5)
            is_current = random.random() < 0.15
            end_date = None if is_current else f"{end_year}-06-30"
            rows.append((
                cid,
                company,
                random.choice(roles),
                f"{start_year}-01-01",
                end_date,
                is_current,
                random.choice(["Bengaluru", "Mumbai", "San Francisco", "London", "Berlin", "Toronto", "Singapore"]),
                random.choice(["IN", "US", "GB", "DE", "CA", "SG"]),
                None,
                None, None, None,
                datetime.now(), 0, datetime.now(), 0, None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_work_experience(cur, rows)
            rows = []
    if rows:
        _flush_work_experience(cur, rows)


def _flush_work_experience(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO candidate_work_experience "
        "(candidate_id, employer_name, role, start_date, end_date, is_current, "
        "location_city, location_country, description, "
        "salary_min, salary_max, salary_currency_code, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_resume_versions(cur, candidate_ids, existing_count):
    rows = []
    for cid in candidate_ids[existing_count:]:
        body = f"Resume for candidate {cid}. "
        body += f"Experienced professional with expertise across multiple domains. "
        body += f"Looking for opportunities in technology and data."
        rows.append((
            cid,
            None,                    # template_id
            body,
            "en",
            f"Version 1",
            True,                   # is_current
            datetime.now(), 0, datetime.now(), 0, None,
        ))
        if len(rows) >= BATCH_LARGE:
            _flush_resume_versions(cur, rows)
            rows = []
    if rows:
        _flush_resume_versions(cur, rows)


def _flush_resume_versions(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO resume_version "
        "(candidate_id, template_id, resume_body, language, version_label, is_current, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_profile_projects(cur, candidate_ids, existing_count):
    rows = []
    for cid in candidate_ids[existing_count:]:
        for _ in range(random.randint(0, 2)):
            start_year = random.randint(2018, 2025)
            end_year = start_year + random.randint(1, 3)
            rows.append((
                cid,
                random.choice(["candidate", "gig"]),
                f"Project {random.randint(1000, 9999)}",
                random.choice(JOB_ROLES[:10]),
                f"{start_year}-01-01",
                f"{end_year}-12-31",
                False,
                random.randint(3, 36),
                "Completed successfully",
                datetime.now(), 0, datetime.now(), 0, None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_profile_projects(cur, rows)
            rows = []
    if rows:
        _flush_profile_projects(cur, rows)


def _flush_profile_projects(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO profile_project "
        "(candidate_id, project_type_code, project_name, role, "
        "start_date, end_date, is_current, duration_months, outcome, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_course_enrolments(cur, candidate_ids, existing_count):
    courses = [
        "Python for Data Science", "Advanced SQL", "Machine Learning Fundamentals",
        "Cloud Architecture", "DevOps Essentials", "Agile Project Management",
        "Leadership in Tech", "Full Stack Web Development",
    ]
    statuses = _get_reference_codes(cur, "enrolment_status")
    rows = []
    for cid in candidate_ids[existing_count:]:
        for _ in range(random.randint(0, 2)):
            enrolled_year = random.randint(2020, 2025)
            completed = random.random() < 0.6
            rows.append((
                cid,
                random.choice(courses),
                f"{enrolled_year}-09-01",
                f"{enrolled_year + 1}-06-30" if completed else None,
                random.choice(statuses),
                datetime.now(), 0, datetime.now(), 0, None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_course_enrolments(cur, rows)
            rows = []
    if rows:
        _flush_course_enrolments(cur, rows)


def _flush_course_enrolments(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO course_enrolment "
        "(candidate_id, course_name, enrolled_at, completed_at, status_code, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_profile_completion(cur, candidate_ids, existing_count):
    rows = []
    for cid in candidate_ids[existing_count:]:
        rows.append((
            cid,
            round(random.uniform(40, 95), 2),
            datetime.now(),
            True,
            datetime.now(), 0, datetime.now(), 0, None,
        ))
        if len(rows) >= BATCH_LARGE:
            _flush_profile_completion(cur, rows)
            rows = []
    if rows:
        _flush_profile_completion(cur, rows)


def _flush_profile_completion(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO profile_completion_score "
        "(candidate_id, score, evaluated_at, is_current, "
        "created_at, created_by, updated_at, updated_by, deleted_at) "
        "VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=len(rows),
    )


def _seed_activity_log(cur, candidate_ids, existing_count):
    activity_types = _get_reference_codes(cur, "activity_type")
    rows = []
    for cid in candidate_ids[existing_count:]:
        for _ in range(random.randint(1, 5)):
            rows.append((
                cid,
                random.choice(activity_types),
                datetime.now() - timedelta(days=random.randint(0, 365)),
                None,
            ))
        if len(rows) >= BATCH_LARGE:
            _flush_activity_log(cur, rows)
            rows = []
    if rows:
        _flush_activity_log(cur, rows)


def _flush_activity_log(cur, rows):
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO candidate_activity_log "
        "(candidate_id, activity_type_code, occurred_at, detail) "
        "VALUES %s",
        rows,
        page_size=len(rows),
    )


# ===========================================================================
# Helpers
# ===========================================================================
def _get_skill_names(cur):
    cur.execute("SELECT name FROM skill")
    return [r[0] for r in cur.fetchall()]


def _get_language_names(cur):
    cur.execute("SELECT name FROM language_lookup")
    return [r[0] for r in cur.fetchall()]


def _get_reference_codes(cur, domain):
    cur.execute(f"SELECT code FROM reference_code WHERE domain = '{domain}'")
    return [r[0] for r in cur.fetchall()]


def _get_qualification_codes(cur):
    cur.execute("SELECT code FROM qualification")
    return [r[0] for r in cur.fetchall()]


if __name__ == "__main__":
    main()
