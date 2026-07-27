from importlib import import_module
from typing import Any

from . import HkoData
from .CalendarDefines import CalendarType, CalendarDate
from .CalendarUtilsProtocol import CalendarUtilsProtocol
from .CalendarBackend import CalendarBackend, calendar_utils_of

__all__ = [
  'HkoData',
  'CalendarType', 'CalendarDate', 'CalendarUtilsProtocol', 'HkoDataCalendarUtils',
  'CalendarBackend', 'calendar_utils_of',
]

def __getattr__(name: str) -> Any:
  # `HkoDataCalendarUtils` instantiates the decoder databases at import time, which
  # requires the encoded data files to be present. Import it lazily (PEP 562) so the
  # offline encoder (`python -m src.Calendar.HkoData.Encoder`) can still run to
  # regenerate the data when it is missing.
  if name == 'HkoDataCalendarUtils':
    return import_module('.HkoDataCalendarUtils', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
