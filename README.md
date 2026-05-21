# platform-snowflake-client

Agnostic Snowflake adapter shared across endymion MFEs. Pure-Python
library — install into each feature's venv as a local file:// dep:

```toml
# in feature's pyproject.toml
dependencies = [
  "platform-snowflake-client @ file:///../app-platform-snowflake-client",
]
```

## Scope

This library owns the **wire layer only** — connection, settings, raw
query execution, schema-level row contracts, and dev fixtures. It does
**not** ship app-specific queries. Each MFE writes its own SQL against
`SnowflakeClient.query(...)` and validates result rows into the typed
contracts shipped here.

That boundary is intentional: state of this repo should never break app
logic in an MFE. Bump versions semver-style; consumers pin or follow.

## What it owns

1. **`SnowflakeSettings`** — env-aware DB routing
   (`DEV_CSM_DB` in local/dev, `PROD_CSM_DB` elsewhere, override-able).
   FQN builders for any CORPORATE table.
2. **`SnowflakeClient`** — connection + cursor + `query()` / `execute()`,
   automatic mock-vs-live mode selection.
3. **Typed row contracts** — `ADPEmployeeRow`, `LocationRow` matching the
   real Snowflake columns 1:1 (no domain-specific properties).
4. **Dev fixtures** — small generic org tree + locations so consumers
   can run end-to-end in mock mode without Snowflake creds.

## What it does NOT own

- Pre-built repository / query classes — moved out as of `0.2.0`.
  Consumers own their queries.
- Domain-specific row helpers (FT/PT label decoding, tenure-anchor
  logic, etc.) — those belong with the feature that defines them.

## Modes

- `mock` — uses the bundled fixtures. Default when `APP_ENVIRONMENT` is
  `local`/`dev`/`development`/`test` and no live creds are set.
- `live` — actual Snowflake. Activated when creds are present
  (`DATABASE_ACCOUNT/USER/PASSWORD/WAREHOUSE`) and `APP_ENVIRONMENT` is
  non-local.

`SnowflakeClient.mode` decides at instantiation; callers branch on
`client.is_mock` where they need to.

## Quick start

```python
from platform_snowflake import SnowflakeClient
from platform_snowflake.contracts import ADPEmployeeRow
from platform_snowflake.fixtures.employees import dev_employees_by_paynum

client = SnowflakeClient.from_env()

if client.is_mock:
    row = dev_employees_by_paynum().get("40000001")
else:
    rows = client.query(
        f"SELECT * FROM {client.adp_employees_fqn} "
        f"WHERE TO_VARCHAR(PAYNUM) = %(p)s LIMIT 1",
        {"p": "40000001"},
    )
    row = ADPEmployeeRow.model_validate(rows[0]) if rows else None
```

Most MFEs wrap that pattern in their own `snowflake/query/*.py` module
so the rest of the app calls `get_by_paynum(paynum)` and doesn't care
which mode is active.

## Environment variables

Field names use the platform's `DATABASE_*` prefix so a single set of
env vars works across every MFE.

```
# Connection
APP_ENVIRONMENT=production         # local|dev|... → DEV_CSM_DB; else PROD_CSM_DB
DATABASE_ACCOUNT=<account>         # e.g. abcd-xy12345
DATABASE_USER=<svc-account>
DATABASE_PASSWORD=<secret>
DATABASE_WAREHOUSE=<wh>
DATABASE_ROLE=                     # optional
DATABASE_NAME=                     # optional default DB on the connection

# Per-DB overrides (leave blank for env-driven defaults)
DATABASE_RAW_DATABASE=
DATABASE_TRF_DATABASE=
DATABASE_CSM_DATABASE=             # e.g. STAGING_CSM_DB to override

# Schemas
DATABASE_CORPORATE_SCHEMA=CORPORATE
DATABASE_APP_SCHEMA=
DATABASE_ACCOUNTING_SCHEMA=

# Force mode for tests / offline dev
DATABASE_MODE_OVERRIDE=             # "mock" or "live"; blank = auto
```

Install with the snowflake extra (needed only in live mode):

```bash
pip install -e "../app-platform-snowflake-client[snowflake]"
```

## Versioning

Semver. `0.2.0` removed the pre-built `repositories/` package; consumers
that pinned `0.1.x` keep working until they upgrade. New row-contract
fields are additive (non-breaking) as long as defaults are set.
