"""Env-aware Snowflake settings.

Field names use the platform's `DATABASE_*` env prefix so a single set
of env vars works across every MFE (inventory, continued-education, …).

Mapping summary (env var → field):

  DATABASE_ACCOUNT          → database_account
  DATABASE_USER             → database_user
  DATABASE_PASSWORD         → database_password
  DATABASE_WAREHOUSE        → database_warehouse
  DATABASE_ROLE             → database_role
  DATABASE_NAME             → database_name        (default DB for the conn)
  DATABASE_RAW_DATABASE     → database_raw_database
  DATABASE_TRF_DATABASE     → database_trf_database
  DATABASE_CSM_DATABASE     → database_csm_database (explicit override)
  DATABASE_CORPORATE_SCHEMA → database_corporate_schema
  DATABASE_APP_SCHEMA       → database_app_schema
  DATABASE_ACCOUNTING_SCHEMA→ database_accounting_schema
  APP_ENVIRONMENT           → app_environment      (drives DEV vs PROD CSM default)
  DATABASE_MODE_OVERRIDE    → database_mode_override ("mock"|"live")
"""
from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


LOCAL_ENVIRONMENTS = {"local", "dev", "development", "test"}

Mode = Literal["mock", "live"]


class SnowflakeSettings(BaseSettings):
    """Snowflake connection + DB routing. Read once at startup; feature
    code resolves names via `csm_corporate_table()` / `*_fqn` properties."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment governs default DB + mock vs live decision.
    app_environment: str = "local"

    # Connection (live mode only).
    database_account: str = ""
    database_user: str = ""
    database_password: str = ""
    database_warehouse: str = ""
    database_role: str = ""
    database_name: str = ""  # default DB attached to the connection

    # Per-DB names (each MFE picks the one it needs).
    database_raw_database: str = ""
    database_trf_database: str = ""
    database_csm_database: str = ""  # explicit override of env-derived default

    # Schemas (most consumers stick with CORPORATE).
    database_corporate_schema: str = "CORPORATE"
    database_app_schema: str = ""
    database_accounting_schema: str = ""

    # Hard override (forces mock even with creds, or live even in dev).
    database_mode_override: str = ""

    # Table names — overridable per deployment if the snowflake schema
    # ever renames them; defaults match the prod schema.
    adp_employees_table: str = "ADP_EMPLOYEES"
    locations_table: str = "LOCATIONS_ALL_V"

    # ----- derived ------------------------------------------------------

    @property
    def normalized_app_environment(self) -> str:
        return self.app_environment.strip().lower() or "local"

    @property
    def is_local_environment(self) -> bool:
        return self.normalized_app_environment in LOCAL_ENVIRONMENTS

    @property
    def has_live_credentials(self) -> bool:
        return bool(
            self.database_account
            and self.database_user
            and self.database_password
            and self.database_warehouse
        )

    @property
    def mode(self) -> Mode:
        """Resolution order:
        1. DATABASE_MODE_OVERRIDE (explicit `mock` or `live`)
        2. Live credentials present → live
        3. Fallback → mock
        """
        override = self.database_mode_override.strip().lower()
        if override in ("mock", "live"):
            return override  # type: ignore[return-value]
        if self.has_live_credentials:
            return "live"
        return "mock"

    # ----- DB-name resolution ------------------------------------------

    @property
    def effective_csm_database(self) -> str:
        """CSM DB name: explicit override (DATABASE_CSM_DATABASE or
        DATABASE_NAME) wins; otherwise local/dev → DEV_CSM_DB; else
        PROD_CSM_DB."""
        for raw in (self.database_csm_database, self.database_name):
            value = (raw or "").strip()
            if value:
                return value
        return "DEV_CSM_DB" if self.is_local_environment else "PROD_CSM_DB"

    @property
    def effective_raw_database(self) -> str:
        value = (self.database_raw_database or "").strip()
        if value:
            return value
        return "DEV_RAW_DB" if self.is_local_environment else "PROD_RAW_DB"

    @property
    def effective_trf_database(self) -> str:
        value = (self.database_trf_database or "").strip()
        if value:
            return value
        return "DEV_TRF_DB" if self.is_local_environment else "PROD_TRF_DB"

    # ----- FQN builders -------------------------------------------------

    def csm_corporate_table(self, table: str) -> str:
        """{csm_db}.{corporate_schema}.{table} — the most common path."""
        return f"{self.effective_csm_database}.{self.database_corporate_schema}.{table}"

    def qualified(self, database: str, schema: str, table: str) -> str:
        """Generic builder for any DB/schema/table triple."""
        return f"{database}.{schema}.{table}"

    @property
    def adp_employees_fqn(self) -> str:
        return self.csm_corporate_table(self.adp_employees_table)

    @property
    def locations_fqn(self) -> str:
        return self.csm_corporate_table(self.locations_table)
