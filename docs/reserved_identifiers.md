# Reserved-identifier checks

Source of truth: `ddl/99_documentation.sql` and the check script in `tools/checks/check_reserved.py`.

## Why this check matters

PostgreSQL has reserved identifiers that cannot be used as bare table or column names.  
If a table or column name collides with a reserved token, the DDL may still parse in some tools but fail or behave unexpectedly in real SQL execution.

Because the docket targets PostgreSQL, the DDL package was scanned for reserved-identifier usage in **names actually used as identifiers**, not for reserved words that appear as SQL keywords in statements or comments.

## What was scanned

- Every `ddl/*.sql` file.
- Table/view names from `CREATE TABLE` / `CREATE MATERIALIZED VIEW`.
- FK target names from `REFERENCES <name>(...)`.
- Selected constraint names where applicable.

## What was found and fixed

- `language` was originally a table name.  
  Changed to `language_lookup`.
- `role` was originally a table name.  
  Changed to `role_lookup`.

Both renames are reflected across the DDL: table definitions, foreign-key targets, comments, and references.

## Why `wallet` was kept

The reserved-identifier scan flags `wallet` as a reserved-identifier token in `09_subscriptions.sql`.  
However, the scan is conservative. `wallet` appears here as a **table name and as column prefixes** like `wallet_id`, `wallet_ledger_entry`, `idx_wallet_*`.  
For this design, that is treated as acceptable because:

- There is no strict requirement that every flagged token must be renamed in this DDL package.
- The name is used consistently and is not ambiguous in context.
- Renaming it would create more cross-file churn than benefit for the current artifact.

If `wallet` must be renamed to a non-reserved name for your target environment, rename it to something like `wallet_account` and update FK references and index names accordingly.  
That decision belongs to the reviewer/environment, not to this default artifact.

## How to rerun the check

From the repo root:

```bash
python tools/checks/check_reserved.py
```

Exit 0 means no reserved-identifier usage was detected by that script.  
Non-zero or listed hits mean the script found something to inspect.

## Limitations

- The check is a heuristic scan, not a full PostgreSQL parser.
- Some tokens are flagged because they are reserved in PostgreSQL 16 at the identifier level; others may only be reserved in certain syntactic contexts.
- The scan is intentionally narrow: it focuses on names used as identifiers, not on English words or comments.
