'''历法日期、换算与真太阳时入口。

CalendarDate 与 JieqiTime 承载历法日期与节气时刻，utils 提供日期换算和节气查询，
solar_time 提供真太阳时换算。'''

from importlib import import_module
from typing import Any

from .dates import CalendarType, CalendarDate, JieqiTime

__all__ = [
  'CalendarType', 'CalendarDate', 'JieqiTime', 'utils', 'solar_time',
]

def __getattr__(name: str) -> Any:
  if name in ('utils', 'solar_time'):
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
