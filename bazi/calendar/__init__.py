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
  # 两后端导入时读取数据表；用 PEP 562 延迟导入，使缺表时仍能运行离线重建工具：
  # python -m bazi.calendar.hko_data.encoder
  # python -m bazi.calendar.celestial_data.generator
  if name in ('hko_data_utils', 'celestial_utils'):
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
