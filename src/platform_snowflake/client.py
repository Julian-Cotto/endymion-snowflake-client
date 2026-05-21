"""SnowflakeClient — connect/query helpers with mock-vs-live auto-detection.

Live mode lazily imports `snowflake.connector` so MFEs that only use mock
mode never pay the import / dep cost. The client is process-singleton via
`SnowflakeClient.from_env()`, but instances are also fine for tests."""
from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any, Iterable, Iterator

from .exceptions import DriverNotInstalled, MissingCredentials, QueryFailed
from .settings import SnowflakeSettings

logger = logging.getLogger("platform_snowflake")


class SnowflakeClient:
    """One per process. In mock mode it holds no resources; in live mode
    it lazily opens a connection on first use and caches it (thread-local)."""

    def __init__(self, settings: SnowflakeSettings | None = None) -> None:
        self.settings = settings or SnowflakeSettings()
        self._tls = threading.local()

    # ----- factory -----------------------------------------------------

    _default: "SnowflakeClient | None" = None
    _lock = threading.Lock()

    @classmethod
    def from_env(cls) -> "SnowflakeClient":
        """Process-singleton constructed from environment variables."""
        if cls._default is None:
            with cls._lock:
                if cls._default is None:
                    cls._default = cls()
        return cls._default

    @classmethod
    def reset_default(cls) -> None:
        """Test hook — drops the singleton so a new settings env can re-init."""
        with cls._lock:
            if cls._default is not None:
                try:
                    cls._default.close()
                except Exception:
                    pass
            cls._default = None

    # ----- mode --------------------------------------------------------

    @property
    def mode(self) -> str:
        return self.settings.mode

    @property
    def is_mock(self) -> bool:
        return self.settings.mode == "mock"

    # ----- live connection -----------------------------------------------

    def _connect(self):
        if self.is_mock:
            raise RuntimeError("Cannot open a Snowflake connection in mock mode.")
        if not self.settings.has_live_credentials:
            raise MissingCredentials(
                "Live mode requires SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, "
                "SNOWFLAKE_PASSWORD, SNOWFLAKE_WAREHOUSE."
            )
        try:
            import snowflake.connector as sf  # type: ignore[import-not-found]
        except ImportError as exc:
            raise DriverNotInstalled(
                "snowflake-connector-python is not installed. Add the "
                "`snowflake` extra: pip install 'platform-snowflake-client[snowflake]'."
            ) from exc

        return sf.connect(
            account=self.settings.database_account,
            user=self.settings.database_user,
            password=self.settings.database_password,
            warehouse=self.settings.database_warehouse,
            role=self.settings.database_role or None,
            database=self.settings.effective_csm_database,
            schema=self.settings.database_corporate_schema,
        )

    def _conn(self):
        conn = getattr(self._tls, "conn", None)
        if conn is None:
            conn = self._connect()
            self._tls.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._tls, "conn", None)
        if conn is not None:
            try:
                conn.close()
            finally:
                self._tls.conn = None

    # ----- query -------------------------------------------------------

    @contextmanager
    def cursor(self) -> Iterator[Any]:
        if self.is_mock:
            raise RuntimeError(
                "cursor() is unavailable in mock mode. Repository methods "
                "branch on `client.is_mock` and use fixtures instead."
            )
        cur = self._conn().cursor()
        try:
            yield cur
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def query(
        self,
        sql: str,
        params: dict[str, Any] | tuple | list | None = None,
    ) -> list[dict[str, Any]]:
        """Execute SELECT and return dict rows. Raises QueryFailed on driver
        error. Repository methods use this internally."""
        if self.is_mock:
            raise RuntimeError(
                "query() is unavailable in mock mode. Branch on client.is_mock."
            )
        try:
            with self.cursor() as cur:
                cur.execute(sql, params or {})
                cols = [c[0].lower() for c in cur.description or []]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as exc:
            logger.exception("snowflake_query_failed")
            raise QueryFailed(str(exc)) from exc

    def execute(self, sql: str, params: dict[str, Any] | tuple | list | None = None) -> int:
        if self.is_mock:
            raise RuntimeError("execute() is unavailable in mock mode.")
        try:
            with self.cursor() as cur:
                cur.execute(sql, params or {})
                return cur.rowcount or 0
        except Exception as exc:
            logger.exception("snowflake_execute_failed")
            raise QueryFailed(str(exc)) from exc

    # ----- convenience -------------------------------------------------

    @property
    def adp_employees_fqn(self) -> str:
        return self.settings.adp_employees_fqn

    @property
    def locations_fqn(self) -> str:
        return self.settings.locations_fqn

    def csm_corporate_table(self, table: str) -> str:
        return self.settings.csm_corporate_table(table)


def configure_logging(level: int = logging.INFO) -> None:
    """Optional: callers can opt-in to library logging via this hook."""
    logger.setLevel(level)
