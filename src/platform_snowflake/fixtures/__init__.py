"""Dev fixtures used by repositories when client.is_mock.

Curated to exercise the full shape of CE / inventory:
- Multi-level manager chain (top → AD → mid → providers)
- Mixed CMPYCODE values
- Terminated, multi-store, and zero-staff locations
- Predictable PAYNUMs so test harnesses can pin them
"""
from .employees import DEV_EMPLOYEES, dev_employees_by_paynum, dev_employees_by_email
from .locations import DEV_LOCATIONS, dev_locations_by_id

__all__ = [
    "DEV_EMPLOYEES",
    "DEV_LOCATIONS",
    "dev_employees_by_email",
    "dev_employees_by_paynum",
    "dev_locations_by_id",
]
