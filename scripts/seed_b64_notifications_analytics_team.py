#!/usr/bin/env python3
"""
B64 Seed: Notifications, Analytics and shared team items data.
Seeds:
  - notification preferences, job alert preferences, language preferences
  - privacy settings
  - notification deliveries (high-volume write path)
  - community posts + reactions
  - support tickets + replies
  - FAQs + FAQ categories
  - analytics dimension tables (date, country, city, employer, candidate, job, pipeline stage)
  - analytics fact tables (application pipeline, time-to-hire, source channel, employer activity, candidate activity, gig marketplace)
  - credential verification (shared team item) — already seeded by B62; supplement here
  - consent records (shared team item) — already seeded by B62; supplement here
  - audit events (shared team item) — already seeded by B62; supplement here
  - blocking list entries (shared team item) — already seeded by B62; supplement here

Run against the connected postgres with:
  PG_DSN=postgres://talentradb:changeme@localhost:5431/talentra python scripts/seed_b64_notifications_analytics_team.py

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
NUM_NOTIFICATIONS = 5000
NUM_COMMUNITY_POSTS = 200
NUM_SUPPORT_TICKETS = 50
NUM_FAQS = 100
NUM_ANALYTICS_FACTS = 5000

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
    print("=== B64 Seed: Notifications, Analytics & Shared Team Items ===\n")

    conn = psycopg2.connect(DSN)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    try:
        # ------------------------------------------------------------------
        # 1. Notification preferences, alerts, language, privacy
        # ------------------------------------------------------------------
        print("[1/4] Seeding notification preferences, alerts, privacy...")
        _seed_notification_preferences(cur)
        conn.commit()
        _seed_job_alert_preferences(cur)
        conn.commit()
        _seed_language_preferences(cur)
        conn.commit()
        _seed_privacy_settings(cur)
        conn.commit()

        # ------------------------------------------------------------------
        # 2. Notification deliveries, community, support, FAQs
        # ------------------------------------------------------------------
        print("[2/4] Seeding notification deliveries, community, support, FAQs...")
        _seed_notification_deliveries(cur)
        conn.commit()
        _seed_community_posts(cur)
        conn.commit()
        _seed_community_post_reactions(cur)
        conn.commit()
        _seed_support_tickets(cur)
        conn.commit()
        _seed_support_ticket_replies(cur)
        conn.commit()
        _seed_faq_categories(cur)
        conn.commit()
        _seed_faqs(cur)
        conn.commit()

        # ------------------------------------------------------------------
        # 3. Analytics dimensions
        # ------------------------------------------------------------------
        print("[3/4] Seeding analytics dimensions...")
        _seed_analytics_dim_date(cur)
        conn.commit()
        _seed_analytics_dim_country(cur)
        conn.commit()
        _seed_analytics_dim_city(cur)
        conn.commit()
        _seed_analytics_dim_employer_organisation(cur)
        conn.commit()
        _seed_analytics_dim_candidate(cur)
        conn.commit()
        _seed_analytics_dim_job_requirement(cur)
        conn.commit()
        _seed_analytics_dim_application_pipeline_stage(cur)
        conn.commit()

        # ------------------------------------------------------------------
        # 4. Analytics facts
        # ------------------------------------------------------------------
        print("[4/4] Seeding analytics facts...")
        _seed_analytics_fact_application_pipeline(cur)
        conn.commit()
        _seed_analytics_fact_time_to_hire(cur)
        conn.commit()
        _seed_analytics_fact_source_channel(cur)
        conn.commit()
        _seed_analytics_fact_employer_activity(cur)
        conn.commit()
        _seed_analytics_fact_candidate_activity(cur)
        conn.commit()
        _seed_analytics_fact_gig_marketplace(cur)
        conn.commit()

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        print("\n=== FINAL TABLE COUNTS ===")
        for table in [
            "notification_preference",
            "job_alert_preference",
            "language_preference",
            "privacy_setting",
            "notification_delivery",
            "community_post",
            "community_post_reaction",
            "support_ticket",
            "support_ticket_reply",
            "faq_category",
            "faq",
            "analytics_dim_date",
            "analytics_dim_country",
            "analytics_dim_city",
            "analytics_dim_employer_organisation",
            "analytics_dim_candidate",
            "analytics_dim_job_requirement",
            "analytics_dim_application_pipeline_stage",
            "analytics_fact_application_pipeline",
            "analytics_fact_time_to_hire",
            "analytics_fact_source_channel",
            "analytics_fact_employer_activity",
            "analytics_fact_candidate_activity",
            "analytics_fact_gig_marketplace",
        ]:
            cur.execute(f"SELECT count(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]:,}")

    except Exception:
        conn.rollback()
        print("B64 SEED FAILED — rolled back", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()
    print("\nB64 seed completed!")


# ===========================================================================
# Notification preferences, alerts, language, privacy
# ===========================================================================

def _seed_notification_preferences(cur):
    cur.execute("SELECT count(*) FROM notification_preference")
    existing = cur.fetchone()[0]
    if existing >= 200:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'notification_channel'")
    channels = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'notification_type'")
    types = [r[0] for r in cur.fetchall()]
    if not channels or not types:
        print("  [SKIP] notification reference codes missing; run B60 first")
        return

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return

    to_insert = []
    for uid in user_ids[:100]:
        for channel in channels[:2]:
            for ntype in types[:2]:
                to_insert.append(
                    (
                        uid,
                        channel,
                        ntype,
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
            "INSERT INTO notification_preference(user_id, channel_code, "
            "notification_type_code, is_enabled, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_job_alert_preferences(cur):
    cur.execute("SELECT count(*) FROM job_alert_preference")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'alert_frequency'")
    frequencies = [r[0] for r in cur.fetchall()]
    if not frequencies:
        print("  [SKIP] alert_frequency reference codes missing; run B60 first")
        return

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return

    to_insert = []
    for i, uid in enumerate(user_ids[:50]):
        to_insert.append(
            (
                uid,
                f"Alert {i + 1}",
                '{"keywords": ["python", "developer"]}',
                frequencies[0] if frequencies else "daily",
                "email",
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
            "INSERT INTO job_alert_preference(user_id, alert_name, criteria, "
            "frequency_code, delivery_channel_codes, is_active, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_language_preferences(cur):
    cur.execute("SELECT count(*) FROM language_preference")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return

    to_insert = []
    for uid in user_ids[:100]:
        to_insert.append(
            (
                uid,
                "en",
                "en",
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
            "INSERT INTO language_preference(user_id, ui_language_code, "
            "content_language_code, is_active, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_privacy_settings(cur):
    cur.execute("SELECT count(*) FROM privacy_setting")
    existing = cur.fetchone()[0]
    if existing >= 200:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'setting_type'")
    setting_types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return

    to_insert = []
    for uid in user_ids[:100]:
        to_insert.append(
            (
                uid,
                "profile_visibility",
                "public",
                setting_types[0] if setting_types else "boolean",
                True,
                now_str(),
                0,
                now_str(),
                0,
                None,
            )
        )
        to_insert.append(
            (
                uid,
                "email_visible",
                "true",
                setting_types[0] if setting_types else "boolean",
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
            "INSERT INTO privacy_setting(user_id, setting_key, setting_value, "
            "setting_type_code, is_active, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ===========================================================================
# Notification deliveries, community, support, FAQs
# ===========================================================================

def _seed_notification_deliveries(cur):
    cur.execute("SELECT count(*) FROM notification_delivery")
    existing = cur.fetchone()[0]
    if existing >= NUM_NOTIFICATIONS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'notification_channel'")
    channels = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'notification_type'")
    types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'delivery_status'")
    statuses = [r[0] for r in cur.fetchall()]
    if not channels or not types or not statuses:
        print("  [SKIP] notification reference codes missing; run B60 first")
        return

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return

    to_insert = []
    for i in range(NUM_NOTIFICATIONS - existing):
        uid = user_ids[i % len(user_ids)]
        to_insert.append(
            (
                uid,
                types[0] if types else "job_alert",
                channels[0] if channels else "email",
                "New job match alert",
                "You have a new job match",
                statuses[0] if statuses else "sent",
                now_str(),
                now_str(),
                now_str(),
                None,
                f"delivery_ref_{i}",
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
                "INSERT INTO notification_delivery(recipient_user_id, "
                "notification_type_code, channel_code, subject, body_text, "
                "delivery_status_code, scheduled_at, sent_at, delivered_at, "
                "read_at, delivery_reference, delivery_error, created_at, "
                "created_by, updated_at, updated_by, deleted_at) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO notification_delivery(recipient_user_id, "
            "notification_type_code, channel_code, subject, body_text, "
            "delivery_status_code, scheduled_at, sent_at, delivered_at, "
            "read_at, delivery_reference, delivery_error, created_at, "
            "created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_community_posts(cur):
    cur.execute("SELECT count(*) FROM community_post")
    existing = cur.fetchone()[0]
    if existing >= NUM_COMMUNITY_POSTS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'community_type'")
    types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'post_visibility'")
    visibilities = [r[0] for r in cur.fetchall()]
    if not types or not visibilities:
        print("  [SKIP] community reference codes missing; run B60 first")
        return

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return

    from faker import Faker

    Faker.seed(SEED + 6)
    f = Faker()

    to_insert = []
    for i in range(NUM_COMMUNITY_POSTS - existing):
        uid = user_ids[i % len(user_ids)]
        to_insert.append(
            (
                uid,
                types[0] if types else "discussion",
                f.sentence(nb_words=8)[:200],
                f.text(max_nb_chars=500)[:1000],
                "en",
                visibilities[0] if visibilities else "public",
                False,
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
                "INSERT INTO community_post(author_user_id, community_type_code, "
                "title, body_text, language_code, visibility_code, is_pinned, "
                "is_published, created_at, created_by, updated_at, updated_by, "
                "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO community_post(author_user_id, community_type_code, "
            "title, body_text, language_code, visibility_code, is_pinned, "
            "is_published, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_community_post_reactions(cur):
    cur.execute("SELECT count(*) FROM community_post_reaction")
    existing = cur.fetchone()[0]
    if existing >= 300:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'reaction_type'")
    types = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM community_post")
    post_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not post_ids or not types:
        print("  [SKIP] reaction reference codes missing; run B60 first")
        return

    to_insert = []
    for i, pid in enumerate(post_ids[:150]):
        uid = user_ids[i % len(user_ids)]
        to_insert.append(
            (
                pid,
                uid,
                types[0] if types else "like",
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
            "INSERT INTO community_post_reaction(community_post_id, reactor_user_id, "
            "reaction_type_code, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_support_tickets(cur):
    cur.execute("SELECT count(*) FROM support_ticket")
    existing = cur.fetchone()[0]
    if existing >= NUM_SUPPORT_TICKETS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'support_category'")
    categories = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'support_priority'")
    priorities = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT code FROM reference_code WHERE domain = 'support_status'")
    statuses = [r[0] for r in cur.fetchall()]
    if not categories or not priorities or not statuses:
        print("  [SKIP] support reference codes missing; run B60 first")
        return

    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return

    from faker import Faker

    Faker.seed(SEED + 7)
    f = Faker()

    to_insert = []
    for i in range(NUM_SUPPORT_TICKETS - existing):
        reporter = user_ids[i % len(user_ids)]
        to_insert.append(
            (
                reporter,
                None,
                categories[0] if categories else "billing",
                priorities[0] if priorities else "low",
                statuses[0] if statuses else "open",
                f"S Support ticket subject {i + 1}",
                f.text(max_nb_chars=300)[:500],
                "en",
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
                "INSERT INTO support_ticket(reporter_user_id, assignee_user_id, "
                "category_code, priority_code, status_code, subject, description, "
                "language_code, created_at, created_by, updated_at, updated_by, "
                "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO support_ticket(reporter_user_id, assignee_user_id, "
            "category_code, priority_code, status_code, subject, description, "
            "language_code, created_at, created_by, updated_at, updated_by, "
            "deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_support_ticket_replies(cur):
    cur.execute("SELECT count(*) FROM support_ticket_reply")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT id FROM support_ticket")
    ticket_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]
    if not ticket_ids or not user_ids:
        return

    from faker import Faker

    Faker.seed(SEED + 8)
    f = Faker()

    to_insert = []
    for i, tid in enumerate(ticket_ids[:50]):
        author = user_ids[(i + 5) % len(user_ids)]
        to_insert.append(
            (
                tid,
                author,
                f.text(max_nb_chars=200)[:400],
                False,
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
            "INSERT INTO support_ticket_reply(support_ticket_id, reply_author_user_id, "
            "reply_text, is_internal, created_at, created_by, updated_at, "
            "updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_faq_categories(cur):
    cur.execute("SELECT count(*) FROM faq_category")
    existing = cur.fetchone()[0]
    if existing >= 5:
        return

    categories = [
        ("general", "General", "General FAQ category", 10, True),
        ("billing", "Billing", "Billing FAQ category", 20, True),
        ("technical", "Technical", "Technical FAQ category", 30, True),
        ("account", "Account", "Account FAQ category", 40, True),
        ("jobs", "Jobs", "Jobs FAQ category", 50, True),
    ]
    to_insert = [(c, name, desc, order, active, now_str(), 0, now_str(), 0, None)
                 for c, name, desc, order, active in categories]
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO faq_category(category_code, name, description, sort_order, "
            "is_active, created_at, created_by, updated_at, updated_by, deleted_at) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_faqs(cur):
    cur.execute("SELECT count(*) FROM faq")
    existing = cur.fetchone()[0]
    if existing >= NUM_FAQS:
        return

    cur.execute("SELECT code FROM reference_code WHERE domain = 'faq_category'")
    categories = [r[0] for r in cur.fetchall()]
    if not categories:
        print("  [SKIP] faq_category reference codes missing; run B60 first")
        return

    from faker import Faker

    Faker.seed(SEED + 9)
    f = Faker()

    to_insert = []
    for i in range(NUM_FAQS - existing):
        cat = categories[i % len(categories)]
        to_insert.append(
            (
                cat,
                f.sentence(nb_words=6)[:200],
                f.text(max_nb_chars=500)[:1000],
                "en",
                i,
                True,
                0,
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
                "INSERT INTO faq(category_code, question, answer, language_code, "
                "sort_order, is_published, view_count, created_at, created_by, "
                "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO faq(category_code, question, answer, language_code, "
            "sort_order, is_published, view_count, created_at, created_by, "
            "updated_at, updated_by, deleted_at) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ===========================================================================
# Analytics dimensions
# ===========================================================================

def _seed_analytics_dim_country(cur):
    cur.execute("SELECT count(*) FROM analytics_dim_country")
    existing = cur.fetchone()[0]
    if existing >= 30:
        return

    # Use list comprehension to avoid reusing cursor - fetch all results first
    cur.execute("SELECT iso_alpha2, name, iso_alpha3, is_active FROM country")
    all_countries = cur.fetchall()
    to_insert = []
    for iso2, name, iso3, active in all_countries:
        to_insert.append((iso2, name, iso3, active, now_str(), 0, now_str(), 0))
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_dim_country(country_code, country_name, "
            "iso_alpha3, is_active, created_at, created_by, updated_at, "
            "updated_by) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_dim_date(cur):
    cur.execute("SELECT count(*) FROM analytics_dim_date")
    existing = cur.fetchone()[0]
    if existing >= 365:
        return

    to_insert = []
    for i in range(365 - existing):
        d = datetime.now() - timedelta(days=365 - i)
        to_insert.append(
            (
                d.date(),
                d.weekday() + 1,
                d.day,
                d.timetuple().tm_yday,
                d.isocalendar()[1],
                d.month,
                d.strftime("%B"),
                (d.month - 1) // 3 + 1,
                d.year,
                d.year == datetime.now().year,
                now_str(),
                0,
                now_str(),
                0,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO analytics_dim_date(date_key, day_of_week, day_of_month, "
                "day_of_year, week_of_year, month_of_year, month_name, quarter, "
                "year, is_current, created_at, created_by, updated_at, updated_by) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_dim_date(date_key, day_of_week, day_of_month, "
            "day_of_year, week_of_year, month_of_year, month_name, quarter, "
            "year, is_current, created_at, created_by, updated_at, updated_by) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_dim_city(cur):
    cur.execute("SELECT count(*) FROM analytics_dim_city")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT name, country_id, latitude, longitude FROM city")
    cities = cur.fetchall()
    cur.execute("SELECT iso_alpha2 FROM country")
    country_codes = [r[0] for r in cur.fetchall()]
    if not cities or not country_codes:
        print("  [SKIP] no cities in master data; run B60 first")
        return

    to_insert = []
    for i, (name, cid, lat, lon) in enumerate(cities[:100]):
        cc = country_codes[cid % len(country_codes)] if country_codes else "IN"
        state = None
        to_insert.append(
            (
                name,
                cc,
                state,
                lat,
                lon,
                True,
                now_str(),
                0,
                now_str(),
                0,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_dim_city(city_name, country_code, state_name, "
            "latitude, longitude, is_active, created_at, created_by, updated_at, "
            "updated_by) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_dim_employer_organisation(cur):
    cur.execute("SELECT count(*) FROM analytics_dim_employer_organisation")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT id, company_name, industry_name, country FROM employer_organisation WHERE is_verified = true")
    employers = cur.fetchall()
    cur.execute("SELECT iso_alpha2 FROM country")
    country_codes = [r[0] for r in cur.fetchall()]
    if not employers or not country_codes:
        print("  [SKIP] no employers in organisation data; run B62 first")
        return

    to_insert = []
    for eid, name, industry, country in employers[:100]:
        cc = country_codes[0] if country_codes else "IN"
        to_insert.append(
            (
                eid,
                name,
                industry,
                None,
                cc,
                None,
                True,
                now_str(),
                None,
                True,
                now_str(),
                0,
                now_str(),
                0,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_dim_employer_organisation(employer_organisation_id, "
            "company_name, industry_name, size_code, country_code, city_name, "
            "is_verified, effective_from, effective_to, is_current, created_at, "
            "created_by, updated_at, updated_by) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_dim_candidate(cur):
    cur.execute("SELECT count(*) FROM analytics_dim_candidate")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT id, first_name, last_name, profile_status_code FROM candidate_identity")
    candidates = cur.fetchall()
    cur.execute("SELECT iso_alpha2 FROM country")
    country_codes = [r[0] for r in cur.fetchall()]
    if not candidates or not country_codes:
        print("  [SKIP] no candidates in profile data; run B60 first")
        return

    import hashlib

    to_insert = []
    for cid, fn, ln, status in candidates[:100]:
        cc = country_codes[0] if country_codes else "IN"
        email_hash = hashlib.sha256(f"{fn}.{ln}@example.com".encode()).hexdigest()[:32]
        fn_hash = hashlib.sha256(fn.encode()).hexdigest()[:16]
        ln_hash = hashlib.sha256(ln.encode()).hexdigest()[:16]
        to_insert.append(
            (
                cid,
                email_hash,
                fn_hash,
                ln_hash,
                status,
                cc,
                None,
                None,
                now_str(),
                None,
                True,
                now_str(),
                0,
                now_str(),
                0,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_dim_candidate(candidate_identity_id, email_hash, "
            "first_name_hash, last_name_hash, profile_status_code, country_code, "
            "city_name, primary_skill_name, effective_from, effective_to, "
            "is_current, created_at, created_by, updated_at, updated_by) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_dim_job_requirement(cur):
    cur.execute("SELECT count(*) FROM analytics_dim_job_requirement")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute(
        "SELECT id, title, employment_type_code, work_type_code, industry_name, "
        "location_country, status_code, is_open_to_consultants, is_remote_allowed "
        "FROM job_requirement"
    )
    jobs = cur.fetchall()
    cur.execute("SELECT iso_alpha2 FROM country")
    country_codes = [r[0] for r in cur.fetchall()]
    if not jobs or not country_codes:
        print("  [SKIP] no jobs in data; run B61 first")
        return

    to_insert = []
    for jid, title, emp_type, work_type, industry, country, status, consultant, remote in jobs[:100]:
        cc = country_codes[0] if country_codes else "IN"
        to_insert.append(
            (
                jid,
                title,
                emp_type,
                work_type,
                industry,
                cc,
                None,
                None,
                None,
                None,
                consultant,
                remote,
                status,
                now_str(),
                None,
                True,
                now_str(),
                0,
                now_str(),
                0,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_dim_job_requirement(job_requirement_id, title, "
            "employment_type_code, work_type_code, industry_name, country_code, "
            "city_name, compensation_min, compensation_max, "
            "compensation_currency_code, is_open_to_consultants, is_remote_allowed, "
            "status_code, effective_from, effective_to, is_current, created_at, "
            "created_by, updated_at, updated_by) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_dim_application_pipeline_stage(cur):
    cur.execute("SELECT count(*) FROM analytics_dim_application_pipeline_stage")
    existing = cur.fetchone()[0]
    if existing >= 6:
        return

    stages = [
        ("applied", "Applied", 10, False),
        ("shortlisted", "Shortlisted", 20, False),
        ("interviewed", "Interviewed", 30, False),
        ("offered", "Offered", 40, False),
        ("joined", "Joined", 50, True),
        ("rejected", "Rejected", 60, True),
    ]
    to_insert = [(code, name, order, terminal, now_str(), 0, now_str(), 0)
                 for code, name, order, terminal in stages]
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_dim_application_pipeline_stage(pipeline_stage_code, "
            "stage_name, stage_order, is_terminal, created_at, created_by, "
            "updated_at, updated_by) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ===========================================================================
# Analytics facts
# ===========================================================================

def _seed_analytics_fact_application_pipeline(cur):
    cur.execute("SELECT count(*) FROM analytics_fact_application_pipeline")
    existing = cur.fetchone()[0]
    if existing >= NUM_ANALYTICS_FACTS:
        return

    cur.execute(
        "SELECT e.id, a.candidate_id, a.job_requirement_id, e.entered_at, e.pipeline_stage_code "
        "FROM application_pipeline_event e "
        "JOIN application a ON a.id = e.application_id "
        "WHERE e.application_id IS NOT NULL LIMIT 5000"
    )
    pipeline_events = cur.fetchall()
    cur.execute("SELECT id, employer_organisation_id, location_country, location_city, industry_name "
                "FROM job_requirement")
    job_map = {r[0]: r for r in cur.fetchall()}
    cur.execute("SELECT date_key FROM analytics_dim_date LIMIT 365")
    date_keys = [r[0] for r in cur.fetchall()]
    if not pipeline_events or not date_keys:
        print("  [SKIP] no pipeline events or date dimension; run B61/B60 first")
        return

    to_insert = []
    for app_id, cid, jid, entered_at, stage in pipeline_events[:NUM_ANALYTICS_FACTS]:
        job = job_map.get(jid)
        if not job:
            continue
        date_key = entered_at.date() if isinstance(entered_at, datetime) else entered_at
        if date_key not in date_keys:
            date_key = date_keys[0]
        to_insert.append(
            (
                app_id,
                cid,
                jid,
                job[1],
                stage,
                entered_at if isinstance(entered_at, datetime) else datetime.strptime(str(entered_at), "%Y-%m-%d %H:%M:%S"),
                date_key,
                job[2],
                job[3],
                job[4],
                now_str(),
                0,
                now_str(),
                0,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO analytics_fact_application_pipeline(application_id, "
                "candidate_identity_id, job_requirement_id, employer_organisation_id, "
                "pipeline_stage_code, entered_at, date_key, country_code, city_name, "
                "industry_name, created_at, created_by, updated_at, updated_by) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_fact_application_pipeline(application_id, "
            "candidate_identity_id, job_requirement_id, employer_organisation_id, "
            "pipeline_stage_code, entered_at, date_key, country_code, city_name, "
            "industry_name, created_at, created_by, updated_at, updated_by) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_fact_time_to_hire(cur):
    cur.execute("SELECT count(*) FROM analytics_fact_time_to_hire")
    existing = cur.fetchone()[0]
    if existing >= 500:
        return

    cur.execute("SELECT id, candidate_id, job_requirement_id, applied_at FROM application")
    apps = cur.fetchall()
    cur.execute("SELECT application_id, entered_at FROM application_pipeline_event "
                "WHERE pipeline_stage_code = 'joined'")
    joined = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT id, employer_organisation_id, location_country, location_city, industry_name "
                "FROM job_requirement")
    job_map = {r[0]: r for r in cur.fetchall()}
    cur.execute("SELECT date_key FROM analytics_dim_date LIMIT 365")
    date_keys = [r[0] for r in cur.fetchall()]
    if not apps or not date_keys:
        print("  [SKIP] no applications or date dimension; run B61/B60 first")
        return

    to_insert = []
    for app_id, cid, jid, applied_at in apps[:500]:
        job = job_map.get(jid)
        if not job:
            continue
        joined_at = joined.get(app_id)
        days = (joined_at - applied_at).days if joined_at and applied_at else None
        date_key = applied_at.date() if isinstance(applied_at, datetime) else applied_at
        if date_key not in date_keys:
            date_key = date_keys[0]
        outcome = "joined" if joined_at else "rejected"
        to_insert.append(
            (
                app_id,
                cid,
                jid,
                job[1],
                applied_at if isinstance(applied_at, datetime) else datetime.strptime(str(applied_at), "%Y-%m-%d %H:%M:%S"),
                joined_at,
                None,
                days,
                outcome,
                date_key,
                job[2],
                job[3],
                job[4],
                now_str(),
                0,
                now_str(),
                0,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO analytics_fact_time_to_hire(application_id, "
                "candidate_identity_id, job_requirement_id, employer_organisation_id, "
                "applied_at, joined_at, rejected_at, days_to_outcome, outcome_code, "
                "date_key, country_code, city_name, industry_name, created_at, "
                "created_by, updated_at, updated_by) VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_fact_time_to_hire(application_id, "
            "candidate_identity_id, job_requirement_id, employer_organisation_id, "
            "applied_at, joined_at, rejected_at, days_to_outcome, outcome_code, "
            "date_key, country_code, city_name, industry_name, created_at, "
            "created_by, updated_at, updated_by) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_fact_source_channel(cur):
    cur.execute("SELECT count(*) FROM analytics_fact_source_channel")
    existing = cur.fetchone()[0]
    if existing >= 500:
        return

    cur.execute("SELECT id, candidate_id, job_requirement_id, source_channel_code, applied_at "
                "FROM application")
    apps = cur.fetchall()
    cur.execute("SELECT id, employer_organisation_id, location_country, industry_name "
                "FROM job_requirement")
    job_map = {r[0]: r for r in cur.fetchall()}
    cur.execute("SELECT date_key FROM analytics_dim_date LIMIT 365")
    date_keys = [r[0] for r in cur.fetchall()]
    if not apps or not date_keys:
        print("  [SKIP] no applications or date dimension; run B61/B60 first")
        return

    to_insert = []
    for app_id, cid, jid, source, applied_at in apps[:500]:
        job = job_map.get(jid)
        if not job:
            continue
        date_key = applied_at.date() if isinstance(applied_at, datetime) else applied_at
        if date_key not in date_keys:
            date_key = date_keys[0]
        to_insert.append(
            (
                app_id,
                cid,
                jid,
                job[1],
                source,
                applied_at if isinstance(applied_at, datetime) else datetime.strptime(str(applied_at), "%Y-%m-%d %H:%M:%S"),
                date_key,
                job[2],
                job[3],
                now_str(),
                0,
                now_str(),
                0,
            )
        )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO analytics_fact_source_channel(application_id, "
                "candidate_identity_id, job_requirement_id, employer_organisation_id, "
                "source_channel_code, applied_at, date_key, country_code, "
                "industry_name, created_at, created_by, updated_at, updated_by) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_fact_source_channel(application_id, "
            "candidate_identity_id, job_requirement_id, employer_organisation_id, "
            "source_channel_code, applied_at, date_key, country_code, "
            "industry_name, created_at, created_by, updated_at, updated_by) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_fact_employer_activity(cur):
    cur.execute("SELECT count(*) FROM analytics_fact_employer_activity")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT id FROM employer_organisation WHERE is_verified = true")
    employer_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT date_key FROM analytics_dim_date LIMIT 365")
    date_keys = [r[0] for r in cur.fetchall()]
    if not employer_ids or not date_keys:
        print("  [SKIP] no employers or date dimension; run B62/B60 first")
        return

    to_insert = []
    for eid in employer_ids[:50]:
        for dk in date_keys[:2]:
            to_insert.append(
                (
                    eid,
                    dk,
                    random.randint(0, 5),
                    random.randint(0, 50),
                    random.randint(0, 20),
                    random.randint(0, 10),
                    random.randint(0, 5),
                    random.randint(0, 3),
                    random.randint(0, 10),
                    now_str(),
                    0,
                    now_str(),
                    0,
                )
            )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO analytics_fact_employer_activity(employer_organisation_id, "
                "activity_date_key, job_posts_count, applications_received_count, "
                "shortlisted_count, interviewed_count, offered_count, joined_count, "
                "rejected_count, created_at, created_by, updated_at, updated_by) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_fact_employer_activity(employer_organisation_id, "
            "activity_date_key, job_posts_count, applications_received_count, "
            "shortlisted_count, interviewed_count, offered_count, joined_count, "
            "rejected_count, created_at, created_by, updated_at, updated_by) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_fact_candidate_activity(cur):
    cur.execute("SELECT count(*) FROM analytics_fact_candidate_activity")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    cur.execute("SELECT id FROM candidate_identity")
    candidate_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT date_key FROM analytics_dim_date LIMIT 365")
    date_keys = [r[0] for r in cur.fetchall()]
    if not candidate_ids or not date_keys:
        print("  [SKIP] no candidates or date dimension; run B60 first")
        return

    to_insert = []
    for cid in candidate_ids[:50]:
        for dk in date_keys[:2]:
            to_insert.append(
                (
                    cid,
                    dk,
                    random.randint(0, 5),
                    random.randint(0, 20),
                    random.randint(0, 10),
                    now_str(),
                    0,
                    now_str(),
                    0,
                )
            )
        if len(to_insert) >= BATCH:
            _insert_many(
                cur,
                "INSERT INTO analytics_fact_candidate_activity(candidate_identity_id, "
                "activity_date_key, applications_sent_count, profile_views_count, "
                "searches_count, created_at, created_by, updated_at, updated_by) "
                "VALUES %s ON CONFLICT DO NOTHING",
                to_insert,
                page_size=BATCH,
            )
            to_insert = []
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_fact_candidate_activity(candidate_identity_id, "
            "activity_date_key, applications_sent_count, profile_views_count, "
            "searches_count, created_at, created_by, updated_at, updated_by) "
            "VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


def _seed_analytics_fact_gig_marketplace(cur):
    cur.execute("SELECT count(*) FROM analytics_fact_gig_marketplace")
    existing = cur.fetchone()[0]
    if existing >= 100:
        return

    # Fetch real gig rows to populate the fact table
    cur.execute(
        "SELECT ga.id, gd.id, gd.job_requirement_id, ga.gig_worker_profile_id, "
        "ga.application_status_code, ga.applied_at, ga.bid_amount, ga.bid_currency_code "
        "FROM gig_application ga "
        "JOIN gig_request_detail gd ON gd.id = ga.gig_request_detail_id "
        "ORDER BY ga.id LIMIT 2000"
    )
    gig_app_rows = cur.fetchall()
    assignment_map = {}
    cur.execute("SELECT id, gig_application_id FROM gig_assignment ORDER BY id")
    for aid, gaid in cur.fetchall():
        assignment_map[gaid] = aid
    handoff_map = {}
    cur.execute("SELECT id, gig_assignment_id FROM gig_handoff_reference ORDER BY id")
    for hid, aid in cur.fetchall():
        handoff_map.setdefault(aid, hid)
    cur.execute("SELECT id, gig_assignment_id, rating_value FROM gig_rating ORDER BY id")
    rating_map = {}
    for rid, aid, val in cur.fetchall():
        rating_map.setdefault(aid, (rid, val))
    cur.execute(
        "SELECT id, gig_assignment_id, earnings_amount, earnings_currency_code "
        "FROM gig_earnings_reference ORDER BY id"
    )
    earnings_map = {}
    for eid, aid, amount, currency in cur.fetchall():
        earnings_map.setdefault(aid, (eid, amount, currency))
    cur.execute("SELECT date_key FROM analytics_dim_date ORDER BY date_key")
    date_keys = [r[0] for r in cur.fetchall()]
    if not date_keys:
        print("  [SKIP] no date dimension; run B60 first")
        return

    to_insert = []
    for gaid, grd, grj, worker_id, stage, applied_at, amount, currency in gig_app_rows[:100]:
        assignment_id = assignment_map.get(gaid)
        handoff_id = handoff_map.get(assignment_id) if assignment_id else None
        rating = rating_map.get(assignment_id) if assignment_id else None
        earnings = earnings_map.get(assignment_id) if assignment_id else None
        date_key = applied_at.date() if isinstance(applied_at, datetime) else date_keys[0]
        if date_key not in date_keys:
            date_key = date_keys[0]
        to_insert.append(
            (
                grd,
                grj,
                worker_id,
                assignment_id,
                gaid,
                handoff_id,
                earnings[0] if earnings else None,
                stage,
                rating[1] if rating else None,
                earnings[1] if earnings else None,
                earnings[2] if earnings else None,
                date_key,
                now_str(),
                0,
                now_str(),
                0,
            )
        )
    if to_insert:
        _insert_many(
            cur,
            "INSERT INTO analytics_fact_gig_marketplace(gig_request_detail_id, "
            "job_requirement_id, gig_worker_profile_id, assignment_id, "
            "application_id, handoff_reference_id, earnings_reference_id, "
            "pipeline_stage_code, rating_value, earnings_amount, "
            "earnings_currency_code, date_key, created_at, created_by, "
            "updated_at, updated_by) VALUES %s ON CONFLICT DO NOTHING",
            to_insert,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_str():
    return "now()"


if __name__ == "__main__":
    main()
