"""Generic LOCATIONS_ALL_V dev fixtures.

A small location set covering multiple CMPYCODEs, regions, and an
explicitly closed row so consumers can exercise their filter logic.
Region attachment uses a sidecar map because LOCATIONS_ALL_V has no
region columns in production — region lives on ADP_EMPLOYEES."""
from __future__ import annotations

import functools

from ..contracts.locations import LocationRow


def _loc(
    *,
    locationid: str,
    name: str,
    altname: str | None,
    addr1: str | None,
    city: str | None,
    state: str | None,
    cmpycode: str,
    is_open: bool,
    region_identifier: str | None = None,
    region_code: str | None = None,
    region_short_name: str | None = None,
) -> LocationRow:
    return LocationRow(
        locationid=locationid,
        name=name,
        altname=altname,
        addr1=addr1,
        city=city,
        state=state,
        cmpycode=cmpycode,
        is_open=is_open,
    ).model_copy(
        update={
            # LocationRow doesn't carry region fields in the prod schema —
            # they live on ADP_EMPLOYEES. We attach them here via a side
            # channel for dev convenience (regional filtering tests).
        }
    )


DEV_LOCATIONS: tuple[LocationRow, ...] = (
    _loc(locationid="100", name="Nashville HQ",         altname="Nashville HQ",     addr1="100 Main St",            city="Nashville",     state="TN", cmpycode="20", is_open=True),
    _loc(locationid="101", name="Brentwood Site",       altname="Brentwood",        addr1="200 Concord Rd",         city="Brentwood",     state="TN", cmpycode="20", is_open=True),
    _loc(locationid="102", name="Franklin Site",        altname="Franklin",         addr1="300 Cool Springs Blvd",  city="Franklin",      state="TN", cmpycode="20", is_open=True),
    _loc(locationid="103", name="Chattanooga Site",     altname="Chattanooga",      addr1="400 Riverfront Pkwy",    city="Chattanooga",   state="TN", cmpycode="20", is_open=True),
    _loc(locationid="200", name="Denver HQ",            altname="Denver HQ",        addr1="1100 17th St",           city="Denver",        state="CO", cmpycode="20", is_open=True),
    _loc(locationid="201", name="Boulder Site",         altname="Boulder",          addr1="2200 Pearl St",          city="Boulder",       state="CO", cmpycode="20", is_open=True),
    _loc(locationid="202", name="Fort Collins Site",    altname="Fort Collins",     addr1="3300 College Ave",       city="Fort Collins",  state="CO", cmpycode="20", is_open=True),
    # Closed site
    _loc(locationid="104", name="Memphis Site",         altname="Memphis (closed)", addr1="500 Beale St",           city="Memphis",       state="TN", cmpycode="20", is_open=False),
    # Off-program corporate site (different CMPYCODE)
    _loc(locationid="900", name="Corporate Annex",      altname="Corporate Annex",  addr1="900 HQ Way",             city="Nashville",     state="TN", cmpycode="70", is_open=True),
)


# Region attached to dev locations via a sidecar map (keeps LocationRow
# faithful to LOCATIONS_ALL_V which doesn't carry region columns).
DEV_LOCATION_REGION: dict[str, tuple[str, str, str]] = {
    "100": ("EAST", "E", "East"),
    "101": ("EAST", "E", "East"),
    "102": ("EAST", "E", "East"),
    "103": ("EAST", "E", "East"),
    "104": ("EAST", "E", "East"),
    "200": ("WEST", "W", "West"),
    "201": ("WEST", "W", "West"),
    "202": ("WEST", "W", "West"),
}


@functools.lru_cache(maxsize=1)
def dev_locations_by_id() -> dict[str, LocationRow]:
    return {loc.locationid: loc for loc in DEV_LOCATIONS}
