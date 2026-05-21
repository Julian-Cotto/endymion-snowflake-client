"""Generic ADP_EMPLOYEES dev fixtures.

A small org tree (top-of-chain → regional managers → site managers →
leaf employees) sized to exercise org-chart traversal, region scoping,
and CMPYCODE filtering. Role + title naming is intentionally domain-
neutral so MFEs that import this don't inherit one feature's vocabulary.
"""
from __future__ import annotations

import functools
from datetime import date, timedelta

from ..contracts.adp_employees import ADPEmployeeRow


def _years_ago(years: int) -> date:
    return date.today() - timedelta(days=365 * years)


# Compact constructor — every fixture row goes through ADPEmployeeRow so
# the same validation rules apply in mock mode and live mode.
def _emp(
    *,
    paynum: str,
    adp_id: str,
    upn: str,
    fname: str,
    lname: str,
    role: str,
    employment_status: str,
    cmpycode: str,
    store_number: str | None,
    store_location: str | None,
    region_identifier: str | None,
    region_code: str | None,
    region_short_name: str | None,
    reports_to_paynum: str | None,
    reports_to_name: str | None,
    is_manager: bool,
    status: str,
    start_date: date,
) -> ADPEmployeeRow:
    is_ft = employment_status == "FT"
    return ADPEmployeeRow(
        paynum=paynum,
        adp_id=adp_id,
        email=upn,
        fname=fname,
        lname=lname,
        job_title=role,
        position_long_description=role,
        work_level_code="F" if is_ft else "P",
        work_level_description="Full-Time" if is_ft else "Part-Time",
        paytype="S" if is_ft else "H",
        cmpycode=cmpycode,
        store_number=store_number,
        store_location=store_location,
        region_identifier=region_identifier,
        region_code=region_code,
        region_short_name=region_short_name,
        reports_to_paynum=reports_to_paynum,
        reports_to_formatted_name=reports_to_name,
        manager_yn="Y" if is_manager else "N",
        status=status,
        status_name="Active" if status == "A" else "Terminated",
        s_date=start_date,
    )


DEV_EMPLOYEES: tuple[ADPEmployeeRow, ...] = (
    # Top of chain
    _emp(
        paynum="10000001", adp_id="ADP-00001", upn="org-head@example.local",
        fname="Morgan", lname="Hayes", role="VP of Operations",
        employment_status="FT", cmpycode="20",
        store_number=None, store_location="Corporate",
        region_identifier=None, region_code=None, region_short_name=None,
        reports_to_paynum=None, reports_to_name=None,
        is_manager=True, status="A", start_date=_years_ago(10),
    ),
    # Regional managers
    _emp(
        paynum="20000001", adp_id="ADP-00010", upn="rm-east@example.local",
        fname="Alex", lname="East", role="Regional Manager",
        employment_status="FT", cmpycode="20",
        store_number="100", store_location="Nashville HQ",
        region_identifier="EAST", region_code="E", region_short_name="East",
        reports_to_paynum="10000001", reports_to_name="Morgan Hayes",
        is_manager=True, status="A", start_date=_years_ago(6),
    ),
    _emp(
        paynum="20000002", adp_id="ADP-00011", upn="rm-west@example.local",
        fname="Dana", lname="West", role="Regional Manager",
        employment_status="FT", cmpycode="20",
        store_number="200", store_location="Denver HQ",
        region_identifier="WEST", region_code="W", region_short_name="West",
        reports_to_paynum="10000001", reports_to_name="Morgan Hayes",
        is_manager=True, status="A", start_date=_years_ago(5),
    ),
    # Site managers
    _emp(
        paynum="30000001", adp_id="ADP-00100", upn="mgr-east1@example.local",
        fname="Sam", lname="Easton", role="Site Manager",
        employment_status="FT", cmpycode="20",
        store_number="101", store_location="Brentwood TN",
        region_identifier="EAST", region_code="E", region_short_name="East",
        reports_to_paynum="20000001", reports_to_name="Alex East",
        is_manager=True, status="A", start_date=_years_ago(4),
    ),
    _emp(
        paynum="30000002", adp_id="ADP-00101", upn="mgr-west1@example.local",
        fname="Robin", lname="Westman", role="Site Manager",
        employment_status="FT", cmpycode="20",
        store_number="201", store_location="Boulder CO",
        region_identifier="WEST", region_code="W", region_short_name="West",
        reports_to_paynum="20000002", reports_to_name="Dana West",
        is_manager=True, status="A", start_date=_years_ago(3),
    ),
    # Leaf employees
    _emp(
        paynum="40000001", adp_id="ADP-01001", upn="field-east-a@example.local",
        fname="Jordan", lname="Carter", role="Specialist",
        employment_status="FT", cmpycode="20",
        store_number="101", store_location="Brentwood TN",
        region_identifier="EAST", region_code="E", region_short_name="East",
        reports_to_paynum="30000001", reports_to_name="Sam Easton",
        is_manager=False, status="A", start_date=_years_ago(2),
    ),
    _emp(
        paynum="40000002", adp_id="ADP-01002", upn="field-east-b@example.local",
        fname="Riley", lname="Nguyen", role="Specialist Assistant",
        employment_status="PT", cmpycode="20",
        store_number="101", store_location="Brentwood TN",
        region_identifier="EAST", region_code="E", region_short_name="East",
        reports_to_paynum="30000001", reports_to_name="Sam Easton",
        is_manager=False, status="A",
        start_date=date.today() - timedelta(days=45),  # short-tenure row
    ),
    _emp(
        paynum="40000003", adp_id="ADP-01003", upn="field-west-a@example.local",
        fname="Avery", lname="Park", role="Specialist",
        employment_status="FT", cmpycode="20",
        store_number="201", store_location="Boulder CO",
        region_identifier="WEST", region_code="W", region_short_name="West",
        reports_to_paynum="30000002", reports_to_name="Robin Westman",
        is_manager=False, status="A", start_date=_years_ago(1),
    ),
    # Off-program row (different CMPYCODE) — exercises filter logic
    _emp(
        paynum="40000099", adp_id="ADP-01099", upn="off-program@example.local",
        fname="Casey", lname="Outside", role="Corporate Analyst",
        employment_status="FT", cmpycode="70",
        store_number="900", store_location="Corporate",
        region_identifier=None, region_code=None, region_short_name=None,
        reports_to_paynum="20000001", reports_to_name="Alex East",
        is_manager=False, status="A", start_date=_years_ago(2),
    ),
    # Default-dev convenience rows that feature backends spin up against
    _emp(
        paynum="20000099", adp_id="ADP-00099", upn="dev@example.local",
        fname="Dev", lname="Manager", role="Regional Manager",
        employment_status="FT", cmpycode="20",
        store_number="100", store_location="Nashville HQ",
        region_identifier="EAST", region_code="E", region_short_name="East",
        reports_to_paynum="10000001", reports_to_name="Morgan Hayes",
        is_manager=True, status="A", start_date=_years_ago(6),
    ),
    _emp(
        paynum="40000020", adp_id="ADP-01020", upn="field-dev@example.local",
        fname="Pat", lname="Devson", role="Specialist",
        employment_status="FT", cmpycode="20",
        store_number="100", store_location="Nashville HQ",
        region_identifier="EAST", region_code="E", region_short_name="East",
        reports_to_paynum="20000099", reports_to_name="Dev Manager",
        is_manager=False, status="A", start_date=_years_ago(2),
    ),
    _emp(
        paynum="40000010", adp_id="ADP-01010", upn="provider@example.local",
        fname="Provider", lname="DevUser", role="Specialist",
        employment_status="FT", cmpycode="20",
        store_number="101", store_location="Brentwood TN",
        region_identifier="EAST", region_code="E", region_short_name="East",
        reports_to_paynum="30000001", reports_to_name="Sam Easton",
        is_manager=False, status="A", start_date=_years_ago(2),
    ),
)


@functools.lru_cache(maxsize=1)
def dev_employees_by_email() -> dict[str, ADPEmployeeRow]:
    return {e.email.lower(): e for e in DEV_EMPLOYEES if e.email}


@functools.lru_cache(maxsize=1)
def dev_employees_by_paynum() -> dict[str, ADPEmployeeRow]:
    return {e.paynum: e for e in DEV_EMPLOYEES if e.paynum}
