# Check scripts

These scripts are kept under `tools/checks/`. They are intentionally not deleted; they are the audit trail for the DDL package.

## `check_reserved.py`

Purpose: scans `ddl/*.sql` for PostgreSQL reserved-identifier usage in table/view names and FK targets.

What it checks:
- table/view names from `CREATE TABLE` / `CREATE MATERIALIZED VIEW`
- FK target names from `REFERENCES <name>(...)`

What it deliberately does not flag:
- reserved words used as SQL keywords in statements or comments
- prose or documentation text

Why it exists:
- the docket targets PostgreSQL, and a few candidate names can collide with reserved identifiers

How to run:

```bash
python tools/checks/check_reserved.py
```

Exit status:
- 0 with “(none)” printed: no reserved-identifier usage detected by this script
- otherwise: list any flagged identifiers for review

Known behavior:
- It is a heuristic scan, not a full PostgreSQL parser.
- `wallet` may be flagged even if you choose to keep it as a table name; see `docs/wallet_table_note.md`.

## `inject_map.py`

Purpose: injects the milestone-order entities → relationships → columns context menu into `ddl/99_documentation.sql`.

What it does:
- appends a `schema_map_milestone_order` table definition and a large `INSERT` of milestone-ordered entity/relationship/column rows into the documentation artifact

Why it exists:
- to keep the milestone-order “context menu” as part of the executable documentation artifact, not as a separate non-runnable doc

How to run:

```bash
python tools/checks/inject_map.py
```

When to run it:
- after the base schema is stable and you want to refresh the milestone-order map in `99_documentation.sql`
- if you add new entities and want them reflected in the milestone-order map

Caution:
- it appends to `99_documentation.sql`; running it twice without resetting can duplicate content if the anchor/text has changed.
- if you re-run it after major edits, inspect the result before committing.

## Running checks together

There is no required order between them. A typical local verification loop is:

```bash
python tools/checks/check_reserved.py
python tools/checks/inject_map.py
```
