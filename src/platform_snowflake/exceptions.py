class SnowflakeClientError(Exception):
    """Base for everything raised by this library."""


class DriverNotInstalled(SnowflakeClientError):
    """`snowflake-connector-python` isn't installed but live mode is requested."""


class MissingCredentials(SnowflakeClientError):
    """Live mode requested but required env vars are missing."""


class QueryFailed(SnowflakeClientError):
    """SQL execution raised an exception."""
