# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum
from typing import cast

from .utils_protocol import CalendarUtilsProtocol


class CalendarBackend(Enum):
  '''
  命盘进行历法换算（公历 <-> 农历 <-> 干支、节气时刻等）所使用的历法后端。

  - HKO：基于香港天文台数据，精度到日，没有节气准确时刻。

  - CELESTIAL：基于 `celestial-calendar` 天文算法，节气时刻精度到秒。

  - CELESTIAL_ALGO2：采用 celestial-calendar 的第二套阴历算法。199 个支持年份中有 6 年与
    CELESTIAL 不同；CELESTIAL 贴合香港天文台官方历书，应优先选用。

  阴历算法是后端身份的一部分，而非其上的开关；原因见 `celestial_utils`。

  参见 https://github.com/0xf3cd/bazi/issues/2 和 https://github.com/0xf3cd/bazi/issues/6。
  '''
  HKO = 'hko'
  CELESTIAL = 'celestial'
  CELESTIAL_ALGO2 = 'celestial-algo2'

  def __str__(self) -> str:
  # 枚举值即序列化格式，新增成员无需另列格式映射。
    return self.value

  @staticmethod
  def from_str(s: str) -> 'CalendarBackend':
    '''
    从字符串解析历法后端（大小写不敏感）。成员名和值都可以，例如 'HKO' 和 'hko'。

    Args:
    - s: (str) 待解析字符串；没有匹配后端时抛 `ValueError`。
    '''
    if not isinstance(s, str):
      raise TypeError(f'Expected str, got {type(s)}')
    for member in CalendarBackend:
      if s.lower() in (member.name.lower(), member.value.lower()):
        return member
    raise ValueError(f'Unsupported backend: {s}')


def calendar_utils_of(backend: CalendarBackend | str) -> CalendarUtilsProtocol:
  '''
  把历法后端声明解析成实际的历法工具（懒加载），解析结果遵循 `CalendarUtilsProtocol`。
  '''
  if not isinstance(backend, (CalendarBackend, str)):
    raise TypeError(f'Expected CalendarBackend or str, got {type(backend)}')
  _backend: CalendarBackend = backend if isinstance(backend, CalendarBackend) else CalendarBackend.from_str(backend)

  if _backend is CalendarBackend.HKO:
    # hko_data_utils 导入时构造解码数据库；延迟导入使其他后端无需承担此成本。
    from . import hko_data_utils
    # 模块函数在运行时满足 CalendarUtilsProtocol 的结构，但 mypy 不把模块视为实例，因此 cast。
    # cast 跳过静态成员与签名检查；test_backend 的 isinstance 只验证成员存在，
    # runtime_checkable 不检查签名。test_hko_data_utils 另以实际调用验证签名。
    return cast(CalendarUtilsProtocol, hko_data_utils)

  if _backend in (CalendarBackend.CELESTIAL, CalendarBackend.CELESTIAL_ALGO2):
    # 同样延迟导入；读取表也有与 HKO 解码器相同的成本。
    from .celestial_utils import ALGO1, ALGO2
    # 实例直接满足实例方法协议，此分支完整接受类型检查，无需 cast，见 #86。
    return ALGO1 if _backend is CalendarBackend.CELESTIAL else ALGO2

  # 每个枚举成员都须在上方解析；到此表示新增成员漏接，用户不能触发。
  # 显式 raise 保证 python -O 下仍能检查该不变量。
  raise AssertionError(f'Backend not wired up in `calendar_utils_of`: {_backend}') # pragma: no cover # 不可达的不变量检查。
