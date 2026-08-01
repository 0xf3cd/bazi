from importlib import import_module
from typing import Any

from . import hko_data
from .dates import CalendarType, CalendarDate, JieqiTime
from .utils_protocol import CalendarUtilsProtocol
from .backend import CalendarBackend, calendar_utils_of

__all__ = [
  'hko_data',
  'CalendarType', 'CalendarDate', 'JieqiTime', 'CalendarUtilsProtocol',
  'hko_data_utils', 'celestial_utils',
  'CalendarBackend', 'calendar_utils_of',
]

def __getattr__(name: str) -> Any:
  # Both backends read their data tables at import time, which requires those tables to be
  # present. Import them lazily (PEP 562) so that the offline tools which *regenerate* the
  # tables (`python -m src.calendar.hko_data.encoder`,
  # `python -m src.calendar.celestial_data.generator`) can still run when they are missing.
  if name in ('hko_data_utils', 'celestial_utils'):
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
