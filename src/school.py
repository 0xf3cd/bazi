# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''The home of the chart-level configuration: `BaziConfig` (every knob steering chart
computation), the school-divergence knobs (`BaziSchool` / `DayRollover` / `KeyStem`), and `BaziPrecision`.'''

from enum import Enum
from dataclasses import dataclass
from typing import Final

from .calendar import CalendarBackend


class BaziPrecision(Enum):
  '''
  BaziPrecision is used to specify the precision when generating the Bazi chart.

  As per the rules of Bazi system, new years start on the days of Start of Spring (LICHUN / 立春), and new months start
  on the days of 12 Jieqis (LICHUN, JINGZHE, QINGMING, LIXIA... / 立春, 惊蛰, 清明, 立夏...).

  So, even born on the same day, two persons can have different Year Ganzhi (年柱) and Month Ganzhi (月柱).

  The 3 levels -- DAY, HOUR, MINUTE -- are three granularities of ONE rule, not three
  approximations of a single truth. A birth belongs to the new year / month when
  `birth >= jieqi`, compared at the granularity the birth is known to; a tie resolves to the
  NEW pillar. That tie-break is the same one the calendar layer freezes -- see
  `calendar/celestial_data/SCHEMA.md`, "Boundary convention".
  三档是同一条规则的三个粒度，不是对同一真值的三种逼近：出生按「已知的粒度」与节气时刻比较，
  `birth >= jieqi` 归新年 / 新月，相等归新。

  - DAY    -- the birth is known to the day, so dates are compared.    只知道日期，比到日。
  - HOUR   -- known to the 时辰, so (date, 时辰) is compared.           知道时辰，比到时辰。
  - MINUTE -- known to the minute, so (date, hour, minute) is compared. 知道到分，比到分。

  `HOUR` means a 时辰 (a traditional double-hour, 子时 starting at 23:00), not a clock hour:
  birth records come at day, 时辰, or minute granularity -- never "hour but not minute".

  For example, LICHUN / 立春 of 2000 falls at 2000-02-04 20:40:23 (per the celestial backend;
  the HKO backend publishes the date only). Then:
  - DAY:    everyone born on 2000-02-04 gets "庚辰" and Month Dizhi "寅", including those born
            before 20:40:23 -- at day granularity, 02-04 >= 02-04 is a tie, and ties go new.
            Those born on 2000-02-03 get "己卯" and "丑".
  - HOUR:   born in 戌时 [19:00, 21:00), the 时辰 holding the jieqi, gets "庚辰" and "寅" (a tie
            again); born in 酉时 [17:00, 19:00) or earlier that day gets "己卯" and "丑".
  - MINUTE: born at or after 20:40 gets "庚辰" and "寅"; before it, "己卯" and "丑".

  This is a rule, not an estimate, and the difference is visible at the extremes: LICHUN of
  2017 falls at 2017-02-03 23:34:03, so DAY assigns all of 02-03 to the new year even though
  98% of that day precedes the jieqi. That is what the rule says, not a defect in it -- an
  estimator would have to flip its answer based on a clock time the DAY caller is not claiming
  to know, which would also make ganzhi month lengths depend on it.

  Because 子时 spans midnight, the tie 时辰 can start on the previous civil day: LICHUN of
  2009 falls at 2009-02-04 00:49:48, in the 子时 that began at 02-03 23:00, so a HOUR birth
  at 2009-02-03 23:30 ties and belongs to the new year -- on a day that DAY assigns to the
  old side. The granularities are three readings of one rule, not nested refinements.
  子时跨午夜，tie 时辰可始于节气前一公历日——三档是同一规则的三种读法，不是嵌套细化。

  HOUR and MINUTE need real jieqi moments, so they require the celestial backend --
  `Bazi.__init__` rejects the HKO backend for them (its `jieqi_moment` is a midnight
  placeholder, see `CalendarUtilsProtocol`).
  '''
  DAY    = 0
  HOUR   = 1
  MINUTE = 2

  def __str__(self) -> str:
    if self is self.DAY:
      return 'day'
    elif self is self.HOUR:
      return 'hour'
    else:
      assert self is self.MINUTE
      return 'minute'


class DayRollover(Enum):
  '''
  The rule that decides when the Day Pillar (日柱) rolls over to the next day (换日点).
  日柱换日点的流派分歧。

  - WAN_ZISHI (晚子时): the day pillar rolls at 23:00, when 子时 begins -- a birth in
    [23:00, 24:00) already carries the next day's day pillar. This is the default, matching
    the majority school and the behaviour `test_bazi` has long pinned.
    晚子时：23:00 子时一开始即换日柱。默认，多数派口径，即现状行为。
  - ZIZHENG (子正): the day pillar rolls at 00:00 (midnight) -- the whole 子时 keeps
    the civil day's day pillar.
    子正：0:00 才换日柱，整个子时不提前换。

  Note:
  - The year and month pillars do NOT follow this knob -- their attribution is
    `BaziPrecision`'s rule (`birth >= jieqi` at the known granularity, ties go new). The two
    mechanisms are independent: a 23:30 WAN_ZISHI birth takes the next day's day pillar while
    its year/month attribution stays put.
    年/月柱不随此旋钮——它们的归属是 `BaziPrecision` 的规则，两条机制相互独立。

  No change should be made to the existing definitions. Only add new definitions.
  '''
  WAN_ZISHI = 0
  ZIZHENG   = 1


class KeyStem(Enum):
  '''
  The Tiangan a 神煞 lookup keys on, where schools disagree (查法锚干).
  神煞查法所锚的天干（流派分歧处）。

  - DAY_MASTER: key on the Day Master (日干 / 日主) -- the 《三命通会》 reading, and the
    default this library has always used for 红艳.
    以日干为锚——《三命通会》口径，本库红艳查法的既有默认。
  - YEAR_MASTER: key on the Year Tiangan (年干).
    以年干为锚。

  Note: the 查法 consumption lands in #69 PR-2 -- until then this knob feeds eq / JSON
  only, not the computed chart. 查法消费在 #69 PR-2 落地；此前本旋钮只影响相等性 / JSON，不影响盘面。

  No change should be made to the existing definitions. Only add new definitions.
  '''
  DAY_MASTER  = 0
  YEAR_MASTER = 1


@dataclass(frozen=True)
class BaziSchool:
  '''
  The school (流派) profile of a chart: the variant knobs where schools disagree.
  Immutable; a chart carries one profile end to end.
  命盘的流派档案：各流派分歧旋钮的取值。不可变；一张盘从头到尾持有一份。

  Fields must stay immutable types (enums / frozen value types) -- no `dict` / `list`
  defaults, so a shared default instance can never be mutated through.
  字段只许不可变类型（枚举 / frozen 值类型），共享默认实例不可能被改脏。

  The field defaults below are the single definition of the default school (多数派口径);
  `DEFAULT_SCHOOL` picks them up, and `BaziConfig.school` points at that same instance --
  the defaults are written down exactly once.
  默认流派只在字段默认值处定义一次；`DEFAULT_SCHOOL` 构造即默认，`BaziConfig.school` 指向同一实例。

  `hongyan_key` does not steer the chart yet -- its 查法 consumption lands in #69 PR-2;
  until then it feeds eq / JSON only. `hongyan_key` 的查法消费在 #69 PR-2 落地，此前不进盘面。
  '''
  day_rollover: DayRollover = DayRollover.WAN_ZISHI
  hongyan_key:  KeyStem     = KeyStem.DAY_MASTER

  def __post_init__(self) -> None:
    # Type check at runtime (same shape as `CalendarDate`).
    if not isinstance(self.day_rollover, DayRollover):
      raise TypeError(f'Expected DayRollover, got {type(self.day_rollover)}')
    if not isinstance(self.hongyan_key, KeyStem):
      raise TypeError(f'Expected KeyStem, got {type(self.hongyan_key)}')


'''The default school profile: 晚子时换日 + 红艳以日干为锚 (《三命通会》). / 默认流派档案：晚子时换日、红艳查日干。'''
DEFAULT_SCHOOL: Final[BaziSchool] = BaziSchool()


@dataclass(frozen=True)
class BaziConfig:
  '''
  The chart-level configuration of a `Bazi`: every knob that affects what the chart
  computes, carried as one immutable value. A `Bazi` stores its `BaziConfig`, and the
  config feeds `__eq__` / `__hash__` / JSON as a unit (same precedent as `backend`).
  命盘级配置：凡影响盘面演算的旋钮聚合为一个不可变值。`Bazi` 持有它，
  相等性 / 哈希 / JSON 都以它为单位进出（同 `backend` 先例）。

  - precision: (BaziPrecision) The precision of the birth time / 出生时间精度。
  - backend: (CalendarBackend) The calendar backend for all calendar conversions / 历法后端。
  - school: (BaziSchool) The school profile; defaults to `DEFAULT_SCHOOL`. / 流派档案，默认 `DEFAULT_SCHOOL`。

  Gender is deliberately NOT here: it does not affect the four pillars' computation
  channel this config aggregates, and stays a `Bazi.create` argument (its string coercion
  lives there too, as before).
  性别刻意不在此：它不进本配置聚合的排盘算路，仍是 `Bazi.create` 的参数（字符串解析也留在那里）。

  The constructor takes the strict types only; string coercion lives in `from_values`.
  构造只收严格枚举类型；字符串解析收在 `from_values`。
  '''
  precision: BaziPrecision    = BaziPrecision.DAY
  backend:   CalendarBackend  = CalendarBackend.CELESTIAL
  school:    BaziSchool       = DEFAULT_SCHOOL

  def __post_init__(self) -> None:
    # Type check at runtime; no coercion here (same shape as `CalendarDate`).
    if not isinstance(self.precision, BaziPrecision):
      raise TypeError(f'Expected BaziPrecision, got {type(self.precision)}')
    if not isinstance(self.backend, CalendarBackend):
      raise TypeError(f'Expected CalendarBackend, got {type(self.backend)}')
    if not isinstance(self.school, BaziSchool):
      raise TypeError(f'Expected BaziSchool, got {type(self.school)}')

  @classmethod
  def from_values(cls, precision: BaziPrecision | str = BaziPrecision.DAY,
                  backend: CalendarBackend | str = CalendarBackend.CELESTIAL,
                  school: BaziSchool = DEFAULT_SCHOOL) -> 'BaziConfig':
    '''
    Build a `BaziConfig`, coercing string spellings to the enums -- the same acceptance
    face `Bazi.create` historically parsed (one alias table, one rejection face).
    从字符串/枚举构造 `BaziConfig`——与 `Bazi.create` 既有解析面同一张别名表、同一个拒绝面。

    Args:
    - precision: (BaziPrecision | str) The precision of the birth time.
      - Supported string values: "分"/"分钟"/"时"/"小时"/"天"/"日"/"m"/"min"/"minute"/"h"/"hour"/"d"/"day"
        (case insensitive). Anything else raises `ValueError`.
    - backend: (CalendarBackend | str) The calendar backend.
      - Supported string values: the member names and values of `CalendarBackend`
        (e.g. "HKO"/"hko", case insensitive), resolved by `CalendarBackend.from_str`.
        Anything else raises `ValueError`.
    - school: (BaziSchool) The school profile; no string spelling. A wrong type raises
      `TypeError` from the constructor's runtime gate.

    Return: (BaziConfig) The coerced, frozen config.
    '''

    if not isinstance(precision, (BaziPrecision, str)):
      raise TypeError(f'Expected BaziPrecision or str, got {type(precision)}')
    if not isinstance(backend, (CalendarBackend, str)):
      raise TypeError(f'Expected CalendarBackend or str, got {type(backend)}')

    _precision: BaziPrecision
    if isinstance(precision, BaziPrecision):
      _precision = precision
    else:
      assert isinstance(precision, str)
      if precision.lower() in ['分', '分钟', 'm', 'min', 'minute']:
        _precision = BaziPrecision.MINUTE
      elif precision.lower() in ['时', '小时', 'h', 'hour']:
        _precision = BaziPrecision.HOUR
      elif precision.lower() in ['天', '日', 'd', 'day']:
        _precision = BaziPrecision.DAY
      else:
        raise ValueError(f'Unsupported precision: {precision}')

    _backend: CalendarBackend
    if isinstance(backend, CalendarBackend):
      _backend = backend
    else:
      assert isinstance(backend, str)
      _backend = CalendarBackend.from_str(backend)

    return cls(precision=_precision, backend=_backend, school=school)


'''The default config: DAY precision, the celestial backend, and `DEFAULT_SCHOOL` -- the
constructor defaults are the canonical definition; `from_values`'s signature defaults are a
second spelling of the same, pinned equivalent by `test_defaults_are_defined_once`.
默认配置：日级精度、celestial 后端、默认流派——构造默认值是正典；`from_values` 的签名默认值是
第二处拼写，由 `test_defaults_are_defined_once` 钉住等价。'''
DEFAULT_CONFIG: Final[BaziConfig] = BaziConfig()
