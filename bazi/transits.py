# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''流运数据类型及命盘小运、大运查询。'''

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, unique
from typing import Final, TypeVar

from .common import check_declared_types, frozendict
from .data_types import DayunTuple
from .defines import Ganzhi, Dizhi
from .bazi_chart import BaziChart, _check_chart
from .calendar import CalendarUtilsProtocol, calendar_utils_of
from .calendar.dates import GanzhiYearMonth


'''查询与物理大运边界共用的可排序投影。'''
_DayunKey = TypeVar('_DayunKey', GanzhiYearMonth, tuple[int, ...])


class DayunDatabase:
  '''按所选规则的起运年份标签区间定位大运；相邻标签划分区间，末区间固定为十个标签年，因此可与
  物理 `end_moment` 不一致。'''
  def __init__(self, chart: BaziChart) -> None:
    _check_chart(chart)
    self._dayuns: Final[tuple[DayunTuple, ...]] = tuple(chart.dayun)
    self._empty_timeline_error: Final[str] = chart._dayun_empty_timeline_message

  def __getitem__(self, gz_year: int) -> DayunTuple:
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if len(self._dayuns) == 0:
      raise ValueError(self._empty_timeline_error)
    if gz_year < self._dayuns[0].ganzhi_year:
      raise ValueError(f'Year {gz_year} is before the first Dayun year {self._dayuns[0].ganzhi_year}')

    end_ganzhi_year: Final[int] = self._dayuns[-1].ganzhi_year + 10
    if gz_year >= end_ganzhi_year:
      raise ValueError(f'Year {gz_year} is on or after the end of the Dayun label range {end_ganzhi_year}')

    for dayun in reversed(self._dayuns):
      if gz_year >= dayun.ganzhi_year:
        return dayun
    raise AssertionError('Unreachable Dayun lookup state') # pragma: no cover # 上方已检查下界。


@unique
class TransitKind(Enum):
  '''流运种类。'''
  XIAOYUN = 'xiaoyun'
  DAYUN   = 'dayun'
  LIUNIAN = 'liunian'
  LIUYUE  = 'liuyue'
  LIURI   = 'liuri'


@dataclass(frozen=True)
class TransitSet:
  '''一组不可变且顺序固定的具名流运干支。'''
  xiaoyun: Ganzhi | None = None
  dayun:   Ganzhi | None = None
  liunian: Ganzhi | None = None
  liuyue:  Ganzhi | None = None
  liuri:   Ganzhi | None = None

  def __post_init__(self) -> None:
    check_declared_types(self)
    values = (self.xiaoyun, self.dayun, self.liunian, self.liuyue, self.liuri)
    if not any(gz is not None for gz in values):
      raise ValueError('A TransitSet cannot be empty')

  @property
  def items(self) -> tuple[tuple[TransitKind, Ganzhi], ...]:
    '''按固定顺序返回现有流运。'''
    pairs = (
      (TransitKind.XIAOYUN, self.xiaoyun),
      (TransitKind.DAYUN,   self.dayun),
      (TransitKind.LIUNIAN, self.liunian),
      (TransitKind.LIUYUE,  self.liuyue),
      (TransitKind.LIURI,   self.liuri),
    )
    return tuple((kind, gz) for kind, gz in pairs if gz is not None)

  def __iter__(self) -> Iterator[TransitKind]:
    return (kind for kind, _ in self.items)

  def __contains__(self, kind: object) -> bool:
    return any(current is kind for current, _ in self.items)

  @property
  def ganzhis(self) -> tuple[Ganzhi, ...]:
    '''按固定流运顺序返回现有干支。'''
    return tuple(gz for _, gz in self.items)

  @property
  def json(self) -> dict[str, str]:
    '''JSON 可序列化的具名表示。'''
    return {kind.value: str(gz) for kind, gz in self.items}

  def select(self, *kinds: TransitKind) -> 'TransitSet':
    '''按固定顺序返回指定的流运；指定的种类必须全部存在。'''
    if len(kinds) == 0:
      raise ValueError('Expected at least one TransitKind')
    for kind in kinds:
      if not isinstance(kind, TransitKind):
        raise TypeError(f'Expected TransitKind, got {type(kind)}')
    if len(set(kinds)) != len(kinds):
      raise ValueError(f'Duplicate transit kinds: {kinds}')

    present = dict(self.items)
    missing = tuple(kind for kind in kinds if kind not in present)
    if len(missing) > 0:
      raise ValueError(f'Transit kinds not available: {missing}')

    return TransitSet(**{kind.value: present[kind] for kind in kinds})


class TransitDatabase:
  '''查询命盘小运、按年份标签解释的大运及按物理边界解释的大运。

  `_dayun_at_*` 是供 TransitChart 使用的包内物理边界入口；调用方先校验坐标、出生下界及
  历法可用性，这些入口只解释交运边界，不重复公开入口校验，也不承诺包外调用。
  '''
  def __init__(self, chart: BaziChart) -> None:
    _check_chart(chart)
    bazi = chart.bazi
    # 出生年采用按出生精度归属的 Bazi.ganzhi_year，与年柱同源。
    # HOUR 跨午夜相等窗口内，日期级 ganzhi_date.year 可与它不同，误用会使所有小运年错一位。
    self._birth_ganzhi_year: Final[int] = bazi.ganzhi_year
    self._birth_month_key: Final[GanzhiYearMonth] = bazi.ganzhi_year_month
    self._utils: Final[CalendarUtilsProtocol] = calendar_utils_of(bazi.config.backend)
    self._dayun_db: Final[DayunDatabase] = DayunDatabase(chart)
    self._dayuns: Final[tuple[DayunTuple, ...]] = self._dayun_db._dayuns

    # 仅历法流运的路径不能读取 BaziChart.xiaoyun，该属性需要首步大运标签。
    xiaoyuns = () if len(self._dayuns) == 0 else chart.xiaoyun
    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      self._birth_ganzhi_year + age - 1 : gz
      for age, gz in xiaoyuns
    })

  def xiaoyun(self, gz_year: int) -> Ganzhi | None:
    '''返回 `gz_year` 的小运；超出小运年份范围时返回 `None`。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    return self._xiaoyun_ganzhis.get(gz_year)

  def dayun(self, gz_year: int) -> Ganzhi | None:
    '''按命盘年份标签返回干支年坐标 `gz_year` 的大运。
    有限年份视图延伸到末标签后十年，可与末步物理区间不同；视图外返回 `None`。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    try:
      return self._dayun_db[gz_year].ganzhi
    except ValueError:
      return None

  def _physical_dayun(
    self,
    query_key: _DayunKey,
    start_key: Callable[[int, DayunTuple], _DayunKey],
  ) -> Ganzhi | None:
    assert isinstance(query_key, (GanzhiYearMonth, tuple))
    assert callable(start_key)

    for index in reversed(range(len(self._dayuns))):
      dayun = self._dayuns[index]
      if start_key(index, dayun) <= query_key:
        return dayun.ganzhi
    return None

  def _dayun_at_month(self, gz_year: int, gz_month: Dizhi) -> Ganzhi | None:
    assert isinstance(gz_year, int)
    assert isinstance(gz_month, Dizhi)

    def __start_key(index: int, dayun: DayunTuple) -> GanzhiYearMonth:
      key = GanzhiYearMonth.from_jie(self._utils.prev_jie(dayun.start_moment))
      return max(key, self._birth_month_key) if index == 0 else key

    return self._physical_dayun(
      GanzhiYearMonth.from_dizhi(gz_year, gz_month),
      __start_key,
    )

  def _dayun_at_date(self, solar_date: date) -> Ganzhi | None:
    assert type(solar_date) is date

    def __start_key(_index: int, dayun: DayunTuple) -> tuple[int, ...]:
      start = dayun.start_moment.date()
      return start.year, start.month, start.day

    return self._physical_dayun(
      (solar_date.year, solar_date.month, solar_date.day),
      __start_key,
    )

  def _dayun_at_moment(self, solar_moment: datetime) -> Ganzhi | None:
    assert isinstance(solar_moment, datetime)
    assert solar_moment.tzinfo is None

    def __key(moment: datetime) -> tuple[int, ...]:
      whole_second = moment.replace(microsecond=0)
      return (
        whole_second.year, whole_second.month, whole_second.day,
        whole_second.hour, whole_second.minute, whole_second.second,
      )

    return self._physical_dayun(
      __key(solar_moment),
      lambda _index, dayun: __key(dayun.start_moment),
    )
