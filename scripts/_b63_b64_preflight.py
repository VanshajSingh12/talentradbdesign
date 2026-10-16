#!/usr/bin/env python3
"""
Preflight for B63/B64 seeding.

Several B63/B64 tables depend on reference_code domains that are currently
empty in the live DB. Rather than making the seed scripts invent arbitrary
enum values at insert time, this script backfills only the specific domains
and codes required by B63/B64 when those domains are missing.

Run:
  PG_DSN=postgres://talentradb:changeme@localhost:5431/talentra \
    python scripts/_b63_b64_preflight.py
"""
import os
import sys

import psycopg2

DSN = os.environ.get(
    "PG_DSN",
    "dbname=talentra user=talentradb password=changeme host=localhost port=5431",
)

# (domain, [(code, display_name_key, sort_order), ...])
BATCHES = {
    # B63 - subscriptions / payments / wallet / sourcing / outreach
    "licence_status": [("active", "licence.status.active", 10)],
    "wallet_status": [("active", "wallet.status.active", 10)],
    "sourcing_status": [("open", "sourcing.status.open", 10)],
    "outreach_channel": [("email", "outreach.channel.email", 10)],
    # B64 - notifications / community / support
    "notification_channel": [("email", "notification.channel.email", 10)],
    "post_visibility": [("public", "post.visibility.public", 10)],
    # B62 team-item domains that are still missing (so B62 reruns can finish)
    "event_type": [("login", "event.login", 10)],
    "blocked_party_type": [
        ("candidate", "blocked_party.candidate", 10),
        ("employer", "blocked_party.employer", 20),
        ("recruiter", "blocked_party.recruiter", 30),
        ("consultant", "blocked_party.consultant", 40),
    ],
    "verification_status": [
        ("pending", "verification.status.pending", 10),
        ("verified", "verification.status.verified", 20),
        ("rejected", "verification.status.rejected", 30),
    ],
    "gig_worker_status": [
        ("active", "gig_worker.status.active", 10),
        ("inactive", "gig_worker.status.inactive", 20),
    ],
    "fulfillment_status": [("pending", "fulfillment.status.pending", 10)],
}


def _ensure_domain(cur, domain, codes):
    cur.execute("SELECT count(*) FROM reference_code WHERE domain = %s", (domain,))
    if cur.fetchone()[0] > 0:
        return 0

    rows = [
        (domain, code, display_name_key, True, sort_order)
        for code, display_name_key, sort_order in codes
    ]
    inserted = 0
    for row in rows:
        cur.execute(
            "INSERT INTO reference_code(domain, code, display_name_key, is_active, sort_order) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (domain, code) DO NOTHING",
            row,
        )
        if cur.rowcount:
            inserted += 1
    return inserted


def main():
    conn = psycopg2.connect(DSN)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()
    try:
        total = 0
        for domain, codes in BATCHES.items():
            n = _ensure_domain(cur, domain, codes)
            if n:
                cur.connection.commit()
                total += n
                print(f"  reference_code[{domain}]: inserted {n}")
            else:
                print(f"  reference_code[{domain}]: exists, skipped")
        print(f"\nPreflight complete: {total} reference_code rows inserted.")
    except Exception:
        conn.rollback()
        print("PREFLIGHT FAILED — rolled back", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import psycopg2.extras

    main()
