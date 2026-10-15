# Wallet table naming note

The wallet table in `09_subscriptions.sql` is named `wallet`.

## Why it exists

The wallet domain is required by Rule Group 10 (subscriptions/wallet/payments/download history).  
The table stores tenant wallet balances and supports the append-only wallet ledger.

## Why the name is `wallet`

- The docket requires wallet support.
- The name is short, conventional, and matches how the domain is described in the docket.
- Consistency with related object names (e.g. `wallet_ledger_entry`, `wallet_id`, `idx_wallet_*`) is easy with this name.

## Reserved-identifier concern

A conservative PostgreSQL reserved-word scan can flag `wallet` as a reserved-identifier token.  
That does not automatically mean the table name is illegal in every context, but it is something to review per target environment.

## If you must rename it

If your environment requires a non-reserved table name, rename `wallet` to a safer name such as `wallet_account` or `tenant_wallet`, and update:

- the table definition
- foreign keys referencing `wallet(id)`
- indexes prefixed `idx_wallet_*`
- comments referencing `wallet`
- related references in documentation and seed scripts

If you want, tell me the exact replacement name and I will apply it consistently across DDL, FKs, indexes, comments, and docs.
