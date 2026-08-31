# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''The home of the chart-level configuration: `BaziConfig` (computation knobs plus the
school profile), the school-divergence declarations (`BaziSchool` / `DayRollover` / `KeyStem` /
`TianyiAnchor` / `JinyuAnchor` / `ShenshaAnchorProfile`),
and option enums (`BaziPrecision` / `DayunYearRule`).'''

from enum import Enum
from dataclasses import dataclass
from typing import Final

from .calendar import CalendarBackend
from .rules import DizhiRules, ShenshaRules


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


class DayunYearRule(Enum):
  '''
  The rule projecting each precise Dayun (大运) boundary to a year label.
  把每个精确大运边界投影为年份标签的规则。

  - JIE_PROJECTED: label each boundary by the Ganzhi year containing it, as determined by
    its owning Jie;
    the first label is floored at the chart's precision-attributed birth year.
    逐个边界按所属节投影干支年；首步标签不早于命盘按精度归属的出生年。
  - FIXED_DECADE: keep a traditional ten-year table from the shared first label. Later
    labels name table positions, not necessarily the Ganzhi years containing the boundaries.
    从共享首标签起按固定十年排表；后续标签表示年表位次，不保证是边界所在干支年。
  '''
  JIE_PROJECTED = 'jie_projected'
  FIXED_DECADE  = 'fixed_decade'

  def __str__(self) -> str:
    return self.value

  @staticmethod
  def from_str(s: str) -> 'DayunYearRule':
    '''
    Parse a `DayunYearRule` from its member name or value (case insensitive).
    从成员名或值解析 `DayunYearRule`（大小写不敏感）。

    Args:
    - s: (str) The string to parse. Raises `ValueError` if it matches no rule.
    '''
    if not isinstance(s, str):
      raise TypeError(f'Expected str, got {type(s)}')
    for member in DayunYearRule:
      if s.lower() in (member.name.lower(), member.value.lower()):
        return member
    raise ValueError(f'Unsupported Dayun year rule: {s}')


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

  Note: this knob is consumed at evaluation time by the 红艳 lookup in relationship analysis
  (`analyzer/relationship.py`); the four pillars never follow it. It also feeds eq / JSON as
  part of `BaziSchool`. 本旋钮由红艳查法在评估期消费；四柱不随它动。它也随 `BaziSchool`
  进相等性 / JSON。

  No change should be made to the existing definitions. Only add new definitions.
  '''
  DAY_MASTER  = 0
  YEAR_MASTER = 1


class TianyiAnchor(Enum):
  '''The anchor stem(s) used to look up TIANYI GUIREN (天乙贵人).
  查询天乙贵人所用的锚干。

  - DAY_MASTER: use the Day Master only; 袁树珊《命理探源》 says「以日为主」.
    只查日干。
  - YEAR_MASTER: use the year Tiangan only, as in the year-based reading.
    只查年干。
  - YEAR_AND_DAY: inspect both year and day Tiangans, the modern mainstream reading
    used by 问真 and 高人. This is the default.
    年干、日干兼查；现代通行默认口径。

  This enum is separate from `KeyStem` because 红艳 has no year-and-day reading.
  本枚举不复用 `KeyStem`，因为红艳没有年日兼查口径。

  The profile is consumed at evaluation time; it never changes the four pillars.
  The chart declares it via `BaziSchool.tianyi_anchor`; it feeds equality, hashing,
  and JSON as part of the school profile.
  本配置仅在神煞评估期消费，不改变四柱；由
  `BaziSchool.tianyi_anchor` 按盘声明，并随流派档案进相等性、哈希与 JSON。

  Sources / 出处:
  - 《命理探源》: https://upload.wikimedia.org/wikipedia/commons/5/52/NLC416-07jh011647-5318_命理探源.pdf
  - 问真: https://book.taiyi.me/命/神煞大全
  - 高人: https://github.com/gaorenyes/gaorenyes.github.io

  No change should be made to the existing definitions. Only add new definitions.
  '''
  DAY_MASTER   = 0
  YEAR_MASTER  = 1
  YEAR_AND_DAY = 2


class JinyuAnchor(Enum):
  '''The anchor stem(s) used to look up JINYU (金舆).
  查询金舆所用的锚干。

  - DAY_MASTER: use the Day Master only, following Yuan Shushan's 《命理探源》. This is
    the default.
    只查日干；从袁树珊《命理探源》。这是默认口径。
  - YEAR_AND_DAY: inspect both year and day Tiangans, following 问真.
    年干、日干兼查；从问真。

  Sources / 出处:
  - 袁树珊《命理探源》: https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
  - 问真: https://book.taiyi.me/命/神煞大全

  No change should be made to the existing definitions. Only add new definitions.
  '''
  DAY_MASTER   = 0
  YEAR_AND_DAY = 1


class ZaishaAnchor(Enum):
  '''The anchor branch(es) used to look up ZAISHA (灾煞).
  查询灾煞所用的锚支。

  - YEAR: use the birth-year branch and inspect the month, day, and hour branches,
    following 问真. This is the default.
    以出生年支查月、日、时支；从问真。这是默认口径。
  - YEAR_AND_DAY: use both the year and day branches; each inspects the remaining three
    branches, following 高人.
    年支、日支分别查其余三支；从高人。

  Sources / 出处:
  - 问真: https://book.taiyi.me/命/神煞大全#灾煞
  - 高人: https://github.com/gaorenyes/gaorenyes.github.io/blob/817ad1f8f463d489087ac6c44ec69165e1181454/README.md#L367-L439

  No change should be made to the existing definitions. Only add new definitions.
  '''
  YEAR         = 0
  YEAR_AND_DAY = 1


class ShenshaAnchorProfile(Enum):
  '''The source profile governing the anchor branches of YIMA, HUAGAI, JIANGXING,
  JIESHA, and WANGSHEN. 驿马、华盖、将星、劫煞、亡神共用的锚支出处 profile。

  - WENZHEN: anchor on both the year and day branches and inspect the remaining branches;
    the modern 问真 reading and the default this library has always used.
    年支、日支分别查余支；问真现代口径，也是本库既有默认。
  - MINGLI_TANYUAN: anchor on the day branch only, following Yuan Shushan's
    《命理探源》 for all five. At birth, inspect the year, month, and hour branches.
    五项均从袁树珊《命理探源》取日支为锚；原局查年、月、时支。

  Taohua (桃花) deliberately does not follow this profile: its day-only reading in
  《命理探源》 also requires a matching Nayin and limits targets to the month and hour.
  Changing only its anchor would create a rule the source does not state.
  桃花不随本配置：《命理探源》的日支桃花另有纳音条件，且只查月、时；不能只切锚而沿用现表。

  The profile affects only Shensha evaluation. It never changes the four pillars.
  本配置仅在神煞评估期消费，不改变四柱。

  Sources / 出处:
  - 《命理探源·卷三强弱》, pp. 64–71 / 第 64–71 页:
    https://commons.wikimedia.org/wiki/File:NLC416-07jh011647-5318_命理探源.pdf
  - Searchable reference / 可检索参考:
    https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
  - Wenzhen / 问真: https://book.taiyi.me/命/神煞大全

  No change should be made to the existing definitions. Only add new definitions.
  '''
  WENZHEN        = 0
  MINGLI_TANYUAN = 1


@dataclass(frozen=True)
class BaziSchool:
  '''
  The school (流派) profile of a chart: the value each variant knob takes where schools
  disagree. The profile only declares -- it computes nothing. Whoever needs a knob reads
  it at its own stage: `day_rollover` steers the day pillar when the chart is computed,
  the rest are read at evaluation time (神煞 lookups, relation discovery). Every field
  feeds `__eq__` / `__hash__` / JSON, so two charts differing only in a knob are two charts.
  命盘的流派档案：本盘在各流派分歧处所取的看法。档案只声明、不演算——谁要哪个口径，谁在自己的阶段
  读它：`day_rollover` 在排盘期决定日柱，其余在评估期读（神煞查法、关系查法）。每个字段
  都进相等性 / 哈希 / JSON，只差一个旋钮的两张盘就是两张盘。

  Not here: `precision` / `backend` (chart computation knobs, not school divergences)
  and gender -- see `BaziConfig`.
  不在此：`precision` / `backend`（算路，不是流派）与性别——见 `BaziConfig`。

  Fields must stay immutable types (enums / frozen value types) -- no `dict` / `list`
  defaults, so a shared default instance can never be mutated through.
  字段只许不可变类型（枚举 / frozen 值类型），共享默认实例不可能被改脏。

  The field defaults below are the single definition of the default school (默认口径);
  `DEFAULT_SCHOOL` picks them up, and `BaziConfig.school` points at that same instance --
  the defaults are written down exactly once.
  默认流派只在字段默认值处定义一次；`DEFAULT_SCHOOL` 构造即默认，`BaziConfig.school` 指向同一实例。
  '''
  day_rollover:  DayRollover = DayRollover.WAN_ZISHI
  hongyan_key:   KeyStem     = KeyStem.DAY_MASTER
  # Rule-definition enums live with their tables; only referenced here.
  # 规则定义枚举与各自规则表同住，这里只引用。
  anhe_def:      DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED
  xing_def:      DizhiRules.XingDef = DizhiRules.XingDef.LOOSE
  gong_def:      DizhiRules.GongDef = DizhiRules.GongDef.SAME_STEM_NARROW
  yangren_def:   ShenshaRules.YangrenDef = ShenshaRules.YangrenDef.ZIPING
  tianyi_anchor: TianyiAnchor = TianyiAnchor.YEAR_AND_DAY
  tianyi_def:    ShenshaRules.TianyiDef = ShenshaRules.TianyiDef.GENG_WITH_JIA_WU
  shensha_anchor_profile: ShenshaAnchorProfile = ShenshaAnchorProfile.WENZHEN
  jinyu_anchor: JinyuAnchor = JinyuAnchor.DAY_MASTER
  feiren_def: ShenshaRules.FeirenDef = ShenshaRules.FeirenDef.ZIPING
  zaisha_anchor: ZaishaAnchor = ZaishaAnchor.YEAR

  def __post_init__(self) -> None:
    # Type check at runtime (same shape as `CalendarDate`).
    if not isinstance(self.day_rollover, DayRollover):
      raise TypeError(f'Expected DayRollover, got {type(self.day_rollover)}')
    if not isinstance(self.hongyan_key, KeyStem):
      raise TypeError(f'Expected KeyStem, got {type(self.hongyan_key)}')
    if not isinstance(self.anhe_def, DizhiRules.AnheDef):
      raise TypeError(f'Expected AnheDef, got {type(self.anhe_def)}')
    if not isinstance(self.xing_def, DizhiRules.XingDef):
      raise TypeError(f'Expected XingDef, got {type(self.xing_def)}')
    if not isinstance(self.gong_def, DizhiRules.GongDef):
      raise TypeError(f'Expected GongDef, got {type(self.gong_def)}')
    if not isinstance(self.yangren_def, ShenshaRules.YangrenDef):
      raise TypeError(f'Expected YangrenDef, got {type(self.yangren_def)}')
    if not isinstance(self.tianyi_anchor, TianyiAnchor):
      raise TypeError(f'Expected TianyiAnchor, got {type(self.tianyi_anchor)}')
    if not isinstance(self.tianyi_def, ShenshaRules.TianyiDef):
      raise TypeError(f'Expected TianyiDef, got {type(self.tianyi_def)}')
    if not isinstance(self.shensha_anchor_profile, ShenshaAnchorProfile):
      raise TypeError(f'Expected ShenshaAnchorProfile, got {type(self.shensha_anchor_profile)}')
    if not isinstance(self.jinyu_anchor, JinyuAnchor):
      raise TypeError(f'Expected JinyuAnchor, got {type(self.jinyu_anchor)}')
    if not isinstance(self.feiren_def, ShenshaRules.FeirenDef):
      raise TypeError(f'Expected FeirenDef, got {type(self.feiren_def)}')
    if not isinstance(self.zaisha_anchor, ZaishaAnchor):
      raise TypeError(f'Expected ZaishaAnchor, got {type(self.zaisha_anchor)}')


DEFAULT_SCHOOL: Final[BaziSchool] = BaziSchool()


@dataclass(frozen=True)
class BaziConfig:
  '''
  The chart-level configuration of a `Bazi`: the knobs steering chart computation
  (`precision` / `backend`), the default Dayun year projection, and the school profile
  (流派档案, which evaluation-time lookups read), carried as one immutable value. A `Bazi`
  stores its `BaziConfig`, and the config feeds `__eq__` / `__hash__` / JSON as a unit
  (same precedent as `backend`). Transit projection is therefore part of chart identity
  even though it does not change the four pillars or the physical Dayun timeline.
  命盘级配置：排盘算路旋钮（`precision` / `backend`）、默认大运年份投影与流派档案（评估期查法
  读取），聚合为一个不可变值。`Bazi` 持有它，相等性 / 哈希 / JSON 都以它为单位进出；流运
  投影因此属于命盘身份，即使它不改变四柱与大运物理时刻线。

  - precision: (BaziPrecision) The precision of the birth time / 出生时间精度。
  - backend: (CalendarBackend) The calendar backend for all calendar conversions / 历法后端。
  - school: (BaziSchool) The school profile; defaults to `DEFAULT_SCHOOL`. / 流派档案，默认 `DEFAULT_SCHOOL`。
  - dayun_year_rule: (DayunYearRule) The default Dayun year projection. / 默认大运年份投影。

  Gender is deliberately NOT here: it does not affect the four pillars' computation
  channel this config aggregates, and stays a `Bazi.create` argument (its string coercion
  lives there too, as before).
  性别刻意不在此：它不进本配置聚合的排盘算路，仍是 `Bazi.create` 的参数（字符串解析也留在那里）。

  The constructor takes the strict types only; string coercion lives in `from_values`.
  构造只收严格枚举类型；字符串解析收在 `from_values`。
  '''
  precision:        BaziPrecision   = BaziPrecision.DAY
  backend:          CalendarBackend = CalendarBackend.CELESTIAL
  school:           BaziSchool      = DEFAULT_SCHOOL
  dayun_year_rule:  DayunYearRule   = DayunYearRule.JIE_PROJECTED

  def __post_init__(self) -> None:
    # Type check at runtime; no coercion here (same shape as `CalendarDate`).
    if not isinstance(self.precision, BaziPrecision):
      raise TypeError(f'Expected BaziPrecision, got {type(self.precision)}')
    if not isinstance(self.backend, CalendarBackend):
      raise TypeError(f'Expected CalendarBackend, got {type(self.backend)}')
    if not isinstance(self.school, BaziSchool):
      raise TypeError(f'Expected BaziSchool, got {type(self.school)}')
    if not isinstance(self.dayun_year_rule, DayunYearRule):
      raise TypeError(f'Expected DayunYearRule, got {type(self.dayun_year_rule)}')

  @classmethod
  def from_values(cls, precision: BaziPrecision | str = BaziPrecision.DAY,
                  backend: CalendarBackend | str = CalendarBackend.CELESTIAL,
                  school: BaziSchool = DEFAULT_SCHOOL,
                  dayun_year_rule: DayunYearRule | str = DayunYearRule.JIE_PROJECTED) -> 'BaziConfig':
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
    - dayun_year_rule: (DayunYearRule | str) The Dayun year projection.
      - Supported string values: the member names and values of `DayunYearRule`
        (e.g. "FIXED_DECADE"/"fixed_decade", case insensitive), resolved by
        `DayunYearRule.from_str`. Anything else raises `ValueError`.

    Return: (BaziConfig) The coerced, frozen config.
    '''

    if not isinstance(precision, (BaziPrecision, str)):
      raise TypeError(f'Expected BaziPrecision or str, got {type(precision)}')
    if not isinstance(backend, (CalendarBackend, str)):
      raise TypeError(f'Expected CalendarBackend or str, got {type(backend)}')
    if not isinstance(dayun_year_rule, (DayunYearRule, str)):
      raise TypeError(f'Expected DayunYearRule or str, got {type(dayun_year_rule)}')

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

    _dayun_year_rule: DayunYearRule
    if isinstance(dayun_year_rule, DayunYearRule):
      _dayun_year_rule = dayun_year_rule
    else:
      assert isinstance(dayun_year_rule, str)
      _dayun_year_rule = DayunYearRule.from_str(dayun_year_rule)

    return cls(
      precision=_precision,
      backend=_backend,
      school=school,
      dayun_year_rule=_dayun_year_rule,
    )


'''The default config: DAY precision, the celestial backend, `DEFAULT_SCHOOL`, and
JIE_PROJECTED Dayun years -- the constructor defaults are the canonical definition;
`from_values`'s signature defaults are a second spelling of the same, pinned equivalent by
`test_defaults_are_defined_once`.
默认配置：日级精度、celestial 后端、默认流派、逐节投影大运年份——构造默认值是正典；
`from_values` 的签名默认值是第二处拼写，由 `test_defaults_are_defined_once` 钉住等价。'''
DEFAULT_CONFIG: Final[BaziConfig] = BaziConfig()
