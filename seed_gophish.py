#!/usr/bin/env python3
"""
Seed a GoPhish SQLite database with a fake campaign, results and events,
so you can test API endpoints against realistic data.

Usage:
    1. Stop GoPhish (or at least make sure nothing is writing to the DB).
    2. Back up your DB:   cp gophish.db gophish.db.bak
    3. python seed_gophish.py --db /path/to/gophish.db --targets 50

Only uses the Python standard library.
"""
import argparse
import json
import random
import sqlite3
import string
from datetime import datetime, timedelta, timezone

FIRST = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi",
         "Ivan", "Judy", "Mallory", "Niaj", "Olivia", "Peggy", "Rupert",
         "Sybil", "Trent", "Victor", "Walter", "Zoe"]
LAST = ["Smith", "Johnson", "Lee", "Garcia", "Brown", "Davis", "Miller",
        "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White"]
POSITIONS = ["Engineer", "Accountant", "Manager", "Analyst", "HR Specialist",
             "Sales Rep", "Support Agent", "Director", "Intern"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
]
# (lat, lon) roughly spread around the world
LOCATIONS = [(40.71, -74.00), (51.50, -0.12), (35.68, 139.69), (-33.86, 151.21),
             (41.74, -111.83), (48.85, 2.35), (19.43, -99.13), (52.52, 13.40)]

# Result statuses used by GoPhish, in funnel order
STATUS_ORDER = ["Email Sent", "Email Opened", "Clicked Link", "Submitted Data"]


def ts(dt):
    """Format a datetime the way go-sqlite3 can parse it back."""
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "+00:00"


def rid():
    return "".join(random.choices(string.ascii_letters + string.digits, k=7))


def insert(cur, table, row):
    """Insert only the columns that actually exist in this GoPhish version."""
    cols = {r[1] for r in cur.execute(f"PRAGMA table_info({table})")}
    if not cols:
        raise SystemExit(f"Table '{table}' not found - is this a GoPhish DB?")
    row = {k: v for k, v in row.items() if k in cols}
    names = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    cur.execute(f"INSERT INTO {table} ({names}) VALUES ({marks})", list(row.values()))
    return cur.lastrowid


def get_user_id(cur, username):
    if username:
        r = cur.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    else:
        r = cur.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    if not r:
        raise SystemExit("No matching user found in the users table.")
    return r[0]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default="gophish.db", help="path to gophish.db")
    p.add_argument("--user", default=None, help="username that should own the campaign (default: first user)")
    p.add_argument("--name", default=None, help="campaign name")
    p.add_argument("--targets", type=int, default=25, help="number of fake recipients")
    p.add_argument("--campaigns", type=int, default=1, help="how many campaigns to create")
    p.add_argument("--status", default="Completed", choices=["Completed", "In progress"])
    p.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible data")
    p.add_argument("--domain", default="example.test", help="email domain for fake targets")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    now = datetime.now(timezone.utc)

    try:
        user_id = get_user_id(cur, args.user)

        # --- Supporting objects the campaign references ---------------------
        template_id = insert(cur, "templates", {
            "user_id": user_id, "name": f"Fake Template {rid()}",
            "envelope_sender": "", "subject": "Action required: password expiry",
            "text": "Your password expires soon. Visit {{.URL}}",
            "html": "<p>Your password expires soon. <a href='{{.URL}}'>Update it</a>.</p>{{.Tracker}}",
            "modified_date": ts(now),
        })
        page_id = insert(cur, "pages", {
            "user_id": user_id, "name": f"Fake Landing Page {rid()}",
            "html": "<html><body><form method='post'><input name='username'>"
                    "<input name='password' type='password'></form></body></html>",
            "capture_credentials": 1, "capture_passwords": 0,
            "redirect_url": "", "modified_date": ts(now),
        })
        smtp_id = insert(cur, "smtp", {
            "user_id": user_id, "interface_type": "SMTP",
            "name": f"Fake SMTP {rid()}", "host": "localhost:25",
            "username": "", "password": "", "from_address": f"it-support@{args.domain}",
            "ignore_cert_errors": 1, "modified_date": ts(now),
        })

        # --- Campaigns ------------------------------------------------------
        for c in range(args.campaigns):
            launch = now - timedelta(days=random.randint(3, 14), hours=random.randint(0, 23))
            name = args.name or f"Test Campaign {launch:%Y-%m-%d} #{rid()}"
            if args.campaigns > 1 and args.name:
                name = f"{args.name} {c + 1}"

            campaign_id = insert(cur, "campaigns", {
                "user_id": user_id, "name": name,
                "created_date": ts(launch - timedelta(minutes=5)),
                "launch_date": ts(launch),
                "send_by_date": ts(launch + timedelta(hours=1)),
                "completed_date": ts(launch + timedelta(days=2)) if args.status == "Completed" else None,
                "status": args.status,
                "template_id": template_id, "page_id": page_id, "smtp_id": smtp_id,
                "url": "http://localhost:8080",
            })

            insert(cur, "events", {
                "campaign_id": campaign_id, "email": "", "time": ts(launch - timedelta(minutes=5)),
                "message": "Campaign Created", "details": "",
            })

            counts = {s: 0 for s in STATUS_ORDER + ["Error"]}
            reported_count = 0

            for pos in range(args.targets):
                first, last = random.choice(FIRST), random.choice(LAST)
                email = f"{first}.{last}{random.randint(1, 99)}@{args.domain}".lower()
                r_id = rid()
                lat, lon = random.choice(LOCATIONS)
                ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
                ua = random.choice(USER_AGENTS)

                send_time = launch + timedelta(seconds=random.randint(0, 3600))

                # Decide how far down the funnel this target goes
                if random.random() < 0.03:
                    final = "Error"
                else:
                    final = "Email Sent"
                    if random.random() < 0.70:
                        final = "Email Opened"
                        if random.random() < 0.40:
                            final = "Clicked Link"
                            if random.random() < 0.40:
                                final = "Submitted Data"
                reported = final != "Error" and random.random() < 0.10

                events = []  # (time, message, details)
                if final == "Error":
                    events.append((send_time, "Error Sending Email",
                                   json.dumps({"error": "550 mailbox unavailable"})))
                else:
                    events.append((send_time, "Email Sent", ""))
                    t = send_time
                    reached = STATUS_ORDER.index(final)
                    browser = {"address": ip, "user-agent": ua}
                    if reached >= 1:
                        t += timedelta(minutes=random.randint(1, 600))
                        events.append((t, "Email Opened", json.dumps({"payload": {}, "browser": browser})))
                    if reached >= 2:
                        t += timedelta(seconds=random.randint(5, 600))
                        events.append((t, "Clicked Link",
                                       json.dumps({"payload": {"rid": [r_id]}, "browser": browser})))
                    if reached >= 3:
                        t += timedelta(seconds=random.randint(10, 300))
                        events.append((t, "Submitted Data", json.dumps({
                            "payload": {"rid": [r_id], "username": [email],
                                        "password": ["[redacted-fake]"]},
                            "browser": browser})))
                    if reported:
                        t += timedelta(minutes=random.randint(1, 120))
                        events.append((t, "Email Reported", json.dumps({"browser": browser})))

                last_time = events[-1][0]
                has_ip = final in ("Email Opened", "Clicked Link", "Submitted Data")

                insert(cur, "results", {
                    "campaign_id": campaign_id, "user_id": user_id, "r_id": r_id,
                    "email": email, "first_name": first, "last_name": last,
                    "position": random.choice(POSITIONS), "status": final,
                    "ip": ip if has_ip else "",
                    "latitude": lat if has_ip else 0.0,
                    "longitude": lon if has_ip else 0.0,
                    "send_date": ts(send_time), "reported": 1 if reported else 0,
                    "modified_date": ts(last_time),
                })
                for et, msg, details in events:
                    insert(cur, "events", {
                        "campaign_id": campaign_id, "email": email,
                        "time": ts(et), "message": msg, "details": details,
                    })

                counts[final] += 1
                reported_count += int(reported)

            print(f"Created campaign id={campaign_id} '{name}' ({args.targets} targets)")
            print("  final statuses:", {k: v for k, v in counts.items() if v},
                  f"reported={reported_count}")

        conn.commit()
        print("Done.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
