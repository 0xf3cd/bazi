# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum
from typing import cast

from .utils_protocol import CalendarUtilsProtocol


class CalendarBackend(Enum):
  '''
  The calendar backend that a `Bazi` uses for all calendar conversions
  (solar <-> lunar <-> ganzhi, jieqi moments, etc.).
  命盘进行历法换算（公历 <-> 农历 <-> 干支、节气时刻等）所使用的历法后端。

  - HKO: based on the data from Hong Kong Observatory. Day-level precision,
    meaning that the accurate times of Jieqis are unknown.
    基于香港天文台数据的历法。日级精度，即无法得知节气的准确时刻。

  - CELESTIAL: based on astronomical algorithms (the `celestial-calendar` project).
    Knows the accurate moments of Jieqis, at second granularity.
    基于天文算法（`celestial-calendar` 项目）的历法。得知节气的准确时刻，精度到秒。

  - CELESTIAL_ALGO2: the same, with the second of celestial-calendar's two lunar
    algorithms. It differs from CELESTIAL on 6 of the 199 supported lunar years;
    CELESTIAL tracks the official HKO almanac and is the one to prefer.
    同上，但采用 celestial-calendar 的第二套阴历算法。199 个支持年份中有 6 年与
    CELESTIAL 不同；CELESTIAL 贴合香港天文台官方历书，应优先选用。

  The lunar algorithm is part of the backend's identity rather than a switch on it; see
  `celestial_utils` for why.
  阴历算法是后端身份的一部分，而非其上的开关；原因见 `celestial_utils`。

  See https://github.com/0xf3cd/bazi/issues/2 and
      https://github.com/0xf3cd/bazi/issues/6
  '''
  HKO = 'hko'
  CELESTIAL = 'celestial'
  CELESTIAL_ALGO2 = 'celestial-algo2'

  def __str__(self) -> str:
    # The value *is* the wire format, so a new member cannot be forgotten here.
    return self.value

  @staticmethod
  def from_str(s: str) -> 'CalendarBackend':
    '''
    Parse a `CalendarBackend` from a string (case insensitive).
    Both the member name and the value are accepted, e.g. 'HKO' and 'hko'.
    从字符串解析历法后端（大小写不敏感）。成员名和值都可以，例如 'HKO' 和 'hko'。

    Args:
    - s: (str) The string to parse. Raises `ValueError` if it matches no backend.
    '''
    if not isinstance(s, str):
      raise TypeError(f'Expected str, got {type(s)}')
    for member in CalendarBackend:
      if s.lower() in (member.name.lower(), member.value.lower()):
        return member
    raise ValueError(f'Unsupported backend: {s}')


def calendar_utils_of(backend: CalendarBackend | str) -> CalendarUtilsProtocol:
  '''
  Resolve a `CalendarBackend` to the actual calendar utils, lazily.
  The resolved utils conform to `CalendarUtilsProtocol`.
  把历法后端声明解析成实际的历法工具（懒加载），解析结果遵循 `CalendarUtilsProtocol`。
  '''
  if not isinstance(backend, (CalendarBackend, str)):
    raise TypeError(f'Expected CalendarBackend or str, got {type(backend)}')
  _backend: CalendarBackend = backend if isinstance(backend, CalendarBackend) else CalendarBackend.from_str(backend)

  if _backend is CalendarBackend.HKO:
    # `hko_data_utils` instantiates the decoder databases at import time.
    # Import it lazily so that users of other backends never pay that cost.
    from . import hko_data_utils
    # A module structurally conforms to `CalendarUtilsProtocol` at runtime (calls on it hit
    # module-level functions with the same signatures, minus `self`), but mypy cannot see a
    # module as an instance, hence the `cast`.  The `cast` silences the static member-and-
    # signature check; the runtime nets only partially pay that back: `test_backend`'s
    # isinstance asserts member existence (nothing more -- `runtime_checkable` ignores
    # signatures), and `test_hko_data_utils` exercises the real signatures by
    # direct calls.
    return cast(CalendarUtilsProtocol, hko_data_utils)

  if _backend in (CalendarBackend.CELESTIAL, CalendarBackend.CELESTIAL_ALGO2):
    # Likewise lazy: reading the tables costs the same as the HKO decoder.
    from .celestial_utils import ALGO1, ALGO2
    # An instance satisfies the instance-shaped protocol directly (issue #86), so this
    # branch is fully type-checked -- no `cast`.
    return ALGO1 if _backend is CalendarBackend.CELESTIAL else ALGO2

  # Invariant: every enum member must be wired up above. Reaching here means we
  # added a member but forgot to resolve it -- not something users can trigger.
  # `raise` instead of `assert` so the guard survives `python -O`.
  raise AssertionError(f'Backend not wired up in `calendar_utils_of`: {_backend}') # pragma: no cover # Unreachable invariant guard.
