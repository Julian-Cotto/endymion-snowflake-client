"""Typed row contract for LOCATIONS_ALL_V."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class LocationRow(BaseModel):
    """One row of `<CSM_DB>.CORPORATE.LOCATIONS_ALL_V`.

    CMPYCODE is stored as VARCHAR but upstream loaders sometimes store
    it numerically; consumers should compare with `TO_VARCHAR(CMPYCODE)`
    in WHERE clauses. ISOPEN is NULL-tolerant — only explicit FALSE
    excludes a row."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    locationid: str
    altid: str | None = None
    name: str | None = None
    altname: str | None = None
    addr1: str | None = None
    addr2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    cmpycode: str | None = None
    is_open: bool = True
    latitude: str | None = None
    longitude: str | None = None
    timezone: str | None = None

    @field_validator("locationid", "cmpycode", mode="before")
    @classmethod
    def _coerce_to_str(cls, v):
        """LOCATIONID/CMPYCODE come back as VARCHAR but some columns may be
        numeric depending on upstream. Always store as string."""
        if v is None:
            return None
        return str(v)

    @field_validator("is_open", mode="before")
    @classmethod
    def _coerce_is_open(cls, v):
        if isinstance(v, bool):
            return v
        if v is None:
            return True
        if isinstance(v, str):
            return v.strip().upper() in ("Y", "YES", "T", "TRUE", "1")
        return bool(v)

    @property
    def display_label(self) -> str:
        """`#101 — Brentwood · 200 Concord Rd`."""
        parts: list[str] = [f"#{self.locationid}"]
        label = self.altname or self.name
        if label:
            parts.append(f"— {label}")
        if self.addr1:
            parts.append(f"· {self.addr1}")
        return " ".join(parts)
