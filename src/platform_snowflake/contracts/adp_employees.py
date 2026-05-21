"""Typed row contract for ADP_EMPLOYEES.

Field names match Snowflake column names (lowercase) verbatim so the
adapter can build a row by `dict(zip(cols, fetched_row))` and validate
into this model with no remapping. Every column we currently consume is
included; add as needed.
"""
from __future__ import annotations

from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ADPEmployeeRow(BaseModel):
    """One row of `<CSM_DB>.CORPORATE.ADP_EMPLOYEES`."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    adp_id: str | None = None
    paynum: str | None = None  # cast to str on ingest — see _coerce_paynum
    fname: str | None = None
    mname: str | None = None
    lname: str | None = None
    job_title: str | None = None
    email: str | None = None

    region_identifier: str | None = None
    region_code: str | None = None
    region_short_name: str | None = None
    region_long_name: str | None = None

    store_number: str | None = None  # cast to str on ingest
    store_location: str | None = None

    s_date: date | None = None  # hire date
    t_date: date | None = None  # termination date
    # ADP_EMPLOYEES.ADPREHIREDATE — populated when an employee is rehired
    # after a separation. Aliased so consumers can read `rehire_date`
    # without leaking the ALL-CAPS column name.
    rehire_date: date | None = Field(default=None, alias="adprehiredate")

    status: str | None = None
    status_name: str | None = None
    termcode: str | None = None
    termination_description: str | None = None

    work_level_code: str | None = None
    work_level_description: str | None = None
    position: str | None = None
    position_short_description: str | None = None
    position_long_description: str | None = None

    company_id: str | None = None
    company_name: str | None = None
    # NOTE: ADP_EMPLOYEES has no CMPYCODE column. PT-vs-not is resolved
    # via STORE_NUMBER → LOCATIONS_ALL_V.CMPYCODE. Field kept here only
    # for legacy mock-fixture compatibility; never populated from a live
    # SELECT.
    cmpycode: str | None = None

    reports_to_adp_id: str | None = None
    reports_to_paynum: str | None = None  # cast to str
    reports_to_formatted_name: str | None = None

    paygroup: str | None = None
    paytype: str | None = None
    manager_yn: str | None = None  # "Y"/"N"

    @field_validator("paynum", "store_number", "reports_to_paynum", mode="before")
    @classmethod
    def _coerce_to_str(cls, v):
        """ADP returns these as NUMBER(38,0); strings everywhere downstream
        keeps FK comparisons sane."""
        if v is None:
            return None
        return str(v)

    @field_validator("manager_yn", mode="before")
    @classmethod
    def _normalize_yn(cls, v):
        if v is None:
            return None
        return str(v).strip().upper() or None

    # ----- convenience -------------------------------------------------

    @property
    def is_manager(self) -> bool:
        return (self.manager_yn or "").upper() == "Y"

    @property
    def is_active(self) -> bool:
        """Treat ADP STATUS='A' (active) as active; anything else (T, L,
        etc.) as inactive."""
        return (self.status or "").strip().upper() == "A"

    @property
    def display_name(self) -> str:
        return " ".join(p for p in (self.fname, self.lname) if p)
