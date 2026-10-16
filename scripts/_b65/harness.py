import os, datetime
from pathlib import Path

# Resolved once against the real location of this module so scripts/ and reports/ are stable.
_MODULE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
PROJECT_ROOT = _MODULE_DIR.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
REPORTS_DIR = SCRIPTS_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

PG_DSN = os.environ.get("PG_DSN", "dbname=talentra user=talentradb password=changeme host=localhost port=5431")
REPORT_BASE = str(REPORTS_DIR)



def conn():
    import psycopg2
    c = psycopg2.connect(PG_DSN)
    c.set_client_encoding("UTF8")
    c.autocommit = True
    return c


def open_report(path):
    os.makedirs(REPORT_BASE, exist_ok=True)
    full = os.path.join(REPORT_BASE, path)
    with open(full, "a", encoding="utf-8") as f:
        f.write(datetime.datetime.now(datetime.timezone.utc).isoformat() + "\n")
    return full


def write_label(cur, path, label, sql, max_rows=60):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n## {label}\n\n")
        f.write(sql.strip() + "\n\n")
    cur.execute(sql)
    rows = cur.fetchall()
    if rows:
        desc = [d.name for d in cur.description]
        with open(path, "a", encoding="utf-8") as f:
            f.write("Columns: " + ", ".join(desc) + "\n")
            f.write(f"Rows: {len(rows)} (shown: {min(len(rows), max_rows)})\n\n")
            for i, r in enumerate(rows[:max_rows]):
                if i == max_rows:
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


def write_explain(cur, path, label, sql):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n## EXPLAIN {label}\n\n{sql.strip()}\n\nExecution plan:\n")
    cur.execute("EXPLAIN (ANALYZE, COSTS, BUFFERS, TIMING, FORMAT TEXT) " + sql.strip())
    plan = cur.fetchall()
    with open(path, "a", encoding="utf-8") as f:
        for r in plan:
            f.write(str(r[0]) + "\n")
        f.write("\n")


def write_check(path, label, sql, expect, note=""):
    import psycopg2
    try:
        cur = psycopg2.connect(PG_DSN)
        cur.autocommit = True
        cur.execute(sql)
        rows = cur.fetchall()
        ok = "PASS" if expect(rows) else "FAIL"
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n[{ok}] {label}\n")
            f.write(f"  SQL: {sql.strip().splitlines()[0][:100]}...\n")
            if note:
                f.write(f"  Note: {note}\n")
            if not expect(rows):
                for r in rows[:5]:
                    f.write(f"  Sample: {r}\n")
            f.write("\n")
        cur.close()
        return ok == "PASS"
    except Exception as e:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n[ERROR] {label}\n  SQL: {sql.strip().splitlines()[0][:100]}...\n  Error: {e}\n\n")
        return False


def table_exists(cur, name):
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (name,))
    return cur.fetchone() is not None


def write_module(cur, path, queries):
    for label, sql in queries:
        write_label(cur, path, label, sql)
