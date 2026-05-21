"""platform-snowflake-client — agnostic Snowflake adapter for endymion MFEs.

This lib owns *only* the wire layer to Snowflake. It does not host
queries for any specific feature; consumers write their own queries
against `SnowflakeClient.query(sql, params)` and validate result rows
into the typed contracts shipped here.

Public surface:

    from platform_snowflake import SnowflakeClient, SnowflakeSettings
    from platform_snowflake.contracts import ADPEmployeeRow, LocationRow
"""
from .client import SnowflakeClient, configure_logging
from .exceptions import (
    DriverNotInstalled,
    MissingCredentials,
    QueryFailed,
    SnowflakeClientError,
)
from .settings import SnowflakeSettings

__all__ = [
    "DriverNotInstalled",
    "MissingCredentials",
    "QueryFailed",
    "SnowflakeClient",
    "SnowflakeClientError",
    "SnowflakeSettings",
    "configure_logging",
]
