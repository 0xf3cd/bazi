from importlib import import_module
from typing import Any

from . import HkoData
from .CalendarDefines import CalendarType, CalendarDate
from .CalendarUtilsProtocol import CalendarUtilsProtocol
from .CalendarBackend import CalendarBackend, calendar_utils_of

__all__ = [
  'HkoData',
  'CalendarType', 'CalendarDate', 'CalendarUtilsProtocol',
  'HkoDataCalendarUtils', 'CelestialCalendarUtils',
  'CalendarBackend', 'calendar_utils_of',
]

def __getattr__(name: str) -> Any:
  # Both backends read their data tables at import time, which requires those tables to be
  # present. Import them lazily (PEP 562) so that the offline tools which *regenerate* the
  # tables (`python -m src.Calendar.HkoData.Encoder`,
  # `python -m src.Calendar.CelestialData.Generator`) can still run when they are missing.
  if name in ('HkoDataCalendarUtils', 'CelestialCalendarUtils'):
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
