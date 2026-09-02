# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''The home of the chart-level configuration: `BaziConfig` (computation knobs plus the
school profile), the school-divergence declarations (`BaziSchool` / `DayRollover` /
`Anchor`), and option enums (`BaziPrecision` / `DayunYearRule`).'''

from enum import Enum
from dataclasses import dataclass, fields
from typing import Any, Final, cast
from collections.abc import Mapping

from .calendar import CalendarBackend
from .common import check_declared_types, frozendict
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


class Anchor(Enum):
  '''
  The pillar(s) a Shensha lookup keys on, where schools disagree (查法锚柱).
  神煞查法所锚的柱位（流派分歧处）。

  - YEAR: key on the year pillar.
    以年柱为锚。
  - DAY: key on the day pillar.
    以日柱为锚。
  - YEAR_AND_DAY: key on both, each pillar supplying its own lookup.
    年、日两柱分别为锚，各查一遍。

  One knob shape serves every anchored Shensha. A member says only WHICH pillar supplies
  the key; whether the key is that pillar's Tiangan or its Dizhi belongs to the Shensha
  itself and is declared in the analyzer's registry. A Tiangan key inspects all four
  branches; a Dizhi key inspects the other three, so a branch never matches itself.
  一种旋钮形状管全部带锚神煞：成员只说 key 出自哪一柱；key 取该柱天干还是地支属于神煞自身，
  由分析层注册表声明。干锚查四支，支锚查其余三支——地支不自查。

  Which members a knob may take is not free: `_ANCHOR_CHOICES` pins the supported values
  per field, and records each value's provenance or known provenance gap on that line.
  `BaziSchool` rejects anything outside the table.
  旋钮能取哪些成员并不自由：`_ANCHOR_CHOICES` 按字段钉死本库支持的取值，并逐行记录出处或
  已知出处缺口；`BaziSchool` 拒收表外取值。

  Anchors are consumed at evaluation time and never change the four pillars. They feed
  equality / hashing / JSON as part of `BaziSchool`.
  锚只在神煞评估期消费，不改变四柱；随 `BaziSchool` 进相等性、哈希与 JSON。

  No change should be made to the existing definitions. Only add new definitions.
  '''
  YEAR         = 0
  DAY          = 1
  YEAR_AND_DAY = 2


'''The supported anchor values of each knob, with their provenance or known provenance gap
written on the corresponding line. An unlisted value is unsupported, not necessarily absent
from every school (see 驿马 below). Adding one is a knowledge change and requires a source.
各锚旋钮支持的取值，连同出处或已知出处缺口逐行记录。表外取值只表示本库不支持，不表示没有
流派如此读（见驿马）；新增取值属于知识变更，须有出处。'''
_ANCHOR_CHOICES: Final[frozendict[str, frozenset[Anchor]]] = frozendict({
  # 红艳: DAY follows 问真 (https://book.taiyi.me/命/神煞大全, 「以日干查四地支」) and 高人,
  # which lists 红艳 under its 「日干查地支」 section. 《三命通会·桃花紅艷煞》 supplies the
  # 干 -> 支 table but does not identify the anchor pillar. YEAR has been supported since
  # issue #69 but its 出处 is still missing; no YEAR_AND_DAY reading was found either.
  'hongyan_anchor':   frozenset({Anchor.DAY, Anchor.YEAR}),
  # 天乙贵人: DAY is 子平法 -- 袁树珊《命理探源》 「以日爲主。如甲日見丑見未」. YEAR is the
  # 禄命法 reading, which keys the 貴神 on the year pillar: 《五行精纪》 卷十四 引陈希烈疏
  # 「假如丑未生人，月日時得甲戊庚，是遇正天乙也。甲子人十二月生，是遇貴神」
  # (https://www.suanzhun.net/book/2742.html); the same edition's annotator states the split
  # outright at https://www.suanzhun.net/book/2728.html. YEAR_AND_DAY is the modern mainstream
  # of 问真 and 高人, and this library's default.
  'tianyi_anchor':    frozenset({Anchor.DAY, Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 金舆: DAY follows 袁树珊《命理探源》
  # (https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb); YEAR_AND_DAY follows 问真
  # (https://book.taiyi.me/命/神煞大全).
  'jinyu_anchor':     frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  # 灾煞: YEAR follows 问真 (https://book.taiyi.me/命/神煞大全#灾煞); YEAR_AND_DAY follows 高人
  # (https://github.com/gaorenyes/gaorenyes.github.io/blob/817ad1f8f463d489087ac6c44ec69165e1181454/README.md#L367-L439).
  'zaisha_anchor':    frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 驿马、华盖、将星、劫煞、亡神 share one pair of readings: YEAR_AND_DAY is 问真's modern
  # reading (https://book.taiyi.me/命/神煞大全) and this library's default, DAY is
  # 袁树珊《命理探源》 for all five -- see `BaziSchool.mingli_tanyuan`, the profile that
  # writes that book's readings out.
  # 《命理探源·卷上强弱》印页六五 also records a YEAR reading for 驿马:「申子辰年馬在寅。
  # 以年爲主。亦是一法」. Issue #181 excludes adding new readings, so it remains unsupported.
  'yima_anchor':      frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'huagai_anchor':    frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'jiangxing_anchor': frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'jiesha_anchor':    frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'wangshen_anchor':  frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
})


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
  # Anchor knobs: each field's supported values and provenance status live in `_ANCHOR_CHOICES`.
  hongyan_anchor: Anchor = Anchor.DAY
  # Rule-definition enums live with their tables; only referenced here.
  # 规则定义枚举与各自规则表同住，这里只引用。
  anhe_def:      DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED
  xing_def:      DizhiRules.XingDef = DizhiRules.XingDef.LOOSE
  gong_def:      DizhiRules.GongDef = DizhiRules.GongDef.SAME_STEM_NARROW
  yangren_def:   ShenshaRules.YangrenDef = ShenshaRules.YangrenDef.ZIPING
  tianyi_anchor: Anchor = Anchor.YEAR_AND_DAY
  tianyi_def:    ShenshaRules.TianyiDef = ShenshaRules.TianyiDef.GENG_WITH_JIA_WU
  yima_anchor:      Anchor = Anchor.YEAR_AND_DAY
  huagai_anchor:    Anchor = Anchor.YEAR_AND_DAY
  jiangxing_anchor: Anchor = Anchor.YEAR_AND_DAY
  jiesha_anchor:    Anchor = Anchor.YEAR_AND_DAY
  wangshen_anchor:  Anchor = Anchor.YEAR_AND_DAY
  jinyu_anchor: Anchor = Anchor.DAY
  feiren_def: ShenshaRules.FeirenDef = ShenshaRules.FeirenDef.ZIPING
  zaisha_anchor: Anchor = Anchor.YEAR

  def __post_init__(self) -> None:
    check_declared_types(self)
    for name, allowed in _ANCHOR_CHOICES.items():
      anchor = getattr(self, name)
      if anchor not in allowed:
        raise ValueError(f'Unsupported anchor for {name}: {anchor}; supported: {sorted(a.name for a in allowed)}')

  @classmethod
  def mingli_tanyuan(cls) -> 'BaziSchool':
    '''
    The profile of 袁树珊《命理探源》: the seven anchors that book has a reading for, each
    set to that reading. 驿马、华盖、将星、劫煞、亡神 key on the day branch alone (at birth
    they then inspect the year, month, and hour branches); 天乙贵人 and 金舆 key on the Day
    Master (「以日为主」). 金舆's is also the current default, and the preset still names it
    -- the profile declares the book's reading, so a change of default cannot silently
    rewrite it.
    《命理探源》 口径档案：该书有读法的七个锚各取其读法。驿马、华盖、将星、劫煞、亡神以日支
    为锚（原局随之查年、月、时支）；天乙贵人与金舆以日干为锚（「以日为主」）。金舆恰好也是
    当前默认，预设仍把它写出来——档案声明的是该书的读法，默认值日后改动不该悄悄改写它。

    Note:
    - Knobs the book does not speak to keep the default profile's values -- 红艳 and 灾煞,
      the rule-definition enums, and 日柱分界 are left alone. The preset declares one
      source's readings, not a whole worldview.
      该书未言及的旋钮保持默认档案的取值——红艳、灾煞、各规则定义枚举与日柱分界都不动。
      预设声明的是一份出处的读法，不是一整套世界观。

    Sources / 出处:
    - 《命理探原·卷上强弱》, 印页 62-71 (NLC scan, PDF pages 93-102):
      https://commons.wikimedia.org/wiki/File:NLC416-07jh011647-5318_命理探源.pdf
      天乙见 62-63，五项地支锚神煞见 64-71。
    - 《命理探源》 ctext edition / ctext 版（金輿祿「以日主為主，如甲日見辰」）:
      https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
      The editions differ: the NLC print has no 金舆 entry and writes 「以日爲主」 where
      ctext writes 「以日主為主」. 两版文字不同：NLC 刊本无金舆条，且相应措辞有别。

    Return: (BaziSchool) The frozen profile.
    '''

    return cls(
      tianyi_anchor=Anchor.DAY,
      yima_anchor=Anchor.DAY,
      huagai_anchor=Anchor.DAY,
      jiangxing_anchor=Anchor.DAY,
      jiesha_anchor=Anchor.DAY,
      wangshen_anchor=Anchor.DAY,
      jinyu_anchor=Anchor.DAY,
    )

  @classmethod
  def from_json(cls, d: Mapping[str, object]) -> 'BaziSchool':
    '''
    Rebuild a profile from the `school` object of `BaziChart.json` -- the inverse of that
    serialization, resolving each stored member name through the field's own declared enum.
    One reader for every enum-valued knob: a new field needs no new line here, and none
    can be forgotten either.
    从 `BaziChart.json` 的 `school` 对象还原流派档案——序列化的逆运算：每个成员名按字段自己
    声明的枚举解析。所有枚举旋钮共用一个读法，新增字段不必在此加行，也不可能漏读。

    Args:
    - d: (Mapping[str, object]) The serialized profile: every `BaziSchool` field name
      mapped to a member name of that field's enum, e.g. `{'day_rollover': 'WAN_ZISHI', ...}`.
      Keys that name no field are ignored. 不对应字段的键被忽略。

    Note:
    - The profile is taken whole or rejected: `d` that is no `Mapping` raises `TypeError`,
      a missing field raises `ValueError`, a non-`str` value raises `TypeError`, a name
      that is no member of the field's enum raises `ValueError`, and an anchor outside its
      supported set raises `ValueError` from the constructor. A partial dict never
      silently falls back to defaults -- a chart rebuilt from JSON is the chart the JSON
      describes.
      档案要么整份收下、要么被拒：入参不是 `Mapping` 抛 `TypeError`，缺字段抛 `ValueError`，
      值非 `str` 抛 `TypeError`，成员名不存在抛 `ValueError`，锚超出支持范围则由构造函数
      抛 `ValueError`。残缺字典绝不静默回落默认值——
      从 JSON 重建的盘就是 JSON 所述的盘。

    Return: (BaziSchool) The rebuilt, frozen profile.

    Examples:
    - `BaziSchool.from_json(chart.json['school']) == chart.bazi.config.school`
    '''

    if not isinstance(d, Mapping):
      raise TypeError(f'Expected Mapping, got {type(d)}')

    kwargs: dict[str, Any] = {}
    for f in fields(cls):
      if f.name not in d:
        raise ValueError(f'Missing school field: {f.name}')
      name = d[f.name]
      if not isinstance(name, str):
        raise TypeError(f'Expected str, got {type(name)}')
      declared = cast(type[Enum], f.type)
      if name not in declared.__members__:
        raise ValueError(f'Unsupported {declared.__name__}: {name}')
      kwargs[f.name] = declared[name]

    return cls(**kwargs)


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
    # No coercion here; string spellings are `from_values`'s job.
    check_declared_types(self)

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
