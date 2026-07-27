# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum
from typing import Union, cast

from .CalendarUtilsProtocol import CalendarUtilsProtocol


class CalendarBackend(Enum):
  '''
  The calendar backend that a `Bazi` uses for all calendar conversions
  (solar <-> lunar <-> ganzhi, jieqi moments, etc.).
  命盘进行历法换算（公历 <-> 农历 <-> 干支、节气时刻等）所使用的历法后端。

  - HKO: based on the data from Hong Kong Observatory. Day-level precision,
    meaning that the accurate times of Jieqis are unknown.
    基于香港天文台数据的历法。日级精度，即无法得知节气的准确时刻。

  In the future, an astronomical-algorithm-based backend will be added,
  which knows the accurate times of Jieqis (minute-level precision) and
  hence unlocks true solar time and higher-precision Bazi charts.
  未来会加入基于天文算法的后端，得知节气的准确时刻（分钟级精度），
  从而解锁真太阳时和更高精度的命盘。

  See https://github.com/0xf3cd/bazi/issues/2 and
      https://github.com/0xf3cd/bazi/issues/6
  '''
  HKO = 'hko'

  def __str__(self) -> str:
    # Invariant: every enum member must be covered here.
    assert self is self.HKO
    return 'hko'

  @staticmethod
  def from_str(s: str) -> 'CalendarBackend':
    '''
    Parse a `CalendarBackend` from a string (case insensitive).
    Both the member name and the value are accepted, e.g. 'HKO' and 'hko'.
    从字符串解析历法后端（大小写不敏感）。成员名和值都可以，例如 'HKO' 和 'hko'。

    Args:
    - s: (str) The string to parse. Raises `ValueError` if it matches no backend.
    '''
    assert isinstance(s, str)
    for member in CalendarBackend:
      if s.lower() in (member.name.lower(), member.value.lower()):
        return member
    raise ValueError(f'Unsupported backend: {s}')


def calendar_utils_of(backend: Union[CalendarBackend, str]) -> CalendarUtilsProtocol:
  '''
  Resolve a `CalendarBackend` to the actual calendar utils, lazily.
  The resolved utils conform to `CalendarUtilsProtocol`.
  把历法后端声明解析成实际的历法工具（懒加载），解析结果遵循 `CalendarUtilsProtocol`。
  '''
  assert isinstance(backend, (CalendarBackend, str))
  _backend: CalendarBackend = backend if isinstance(backend, CalendarBackend) else CalendarBackend.from_str(backend)

  if _backend is CalendarBackend.HKO:
    # `HkoDataCalendarUtils` instantiates the decoder databases at import time.
    # Import it lazily so that users of other backends never pay that cost.
    from . import HkoDataCalendarUtils
    # A module structurally conforms to `CalendarUtilsProtocol` at runtime (the
    # protocol's staticmethods are satisfied by module-level functions), but mypy
    # cannot see that, hence the `cast`.
    return cast(CalendarUtilsProtocol, HkoDataCalendarUtils)

  # Invariant: every enum member must be wired up above. Reaching here means we
  # added a member but forgot to resolve it -- not something users can trigger.
  # `raise` instead of `assert` so the guard survives `python -O`.
  raise AssertionError(f'Backend not wired up in `calendar_utils_of`: {_backend}') # pragma: no cover # Unreachable invariant guard.
