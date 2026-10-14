# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''命盘配置 `BaziConfig`、流派分歧声明 `BaziSchool` / `DayRollover` / `Anchor`，
以及出生精度和大运年份投影选项 `BaziPrecision` / `DayunYearRule`。'''

from enum import Enum
from dataclasses import dataclass, fields
from typing import Any, Final, TypedDict, cast
from collections.abc import Mapping

from .calendar import CalendarBackend
from .common import check_declared_types, frozendict
from .rules import DizhiRules, ShenshaRules, DizhiRelationDefinitions, DEFAULT_DIZHI_RELATION_DEFINITIONS


class BaziPrecision(Enum):
  '''
  出生精度，决定排盘时比较出生与节气的粒度。以立春换年，以十二节换月，
  所以同日出生也可有不同年/月柱。

  出生按「已知的粒度」与节气时刻比较，`birth >= jieqi` 归新年 / 新月，相等归新。
  这是同一规则的三个粒度，不是对同一真值的三种估计。

  - DAY：只知道日期，比到日。
  - HOUR：知道时辰，比到日期与时辰；时辰为两小时，子时始于 23:00，不是单个钟表小时。
  - MINUTE：知道到分，比到日期、小时与分钟。

  Examples:
  celestial 后端的 2000 年立春为 2000-02-04 20:40:23，HKO 只提供日期。
  - DAY：02-04 全天取年柱庚辰、月支寅，包括 20:40:23 之前；02-03 取己卯、丑。
  - HOUR：戌时 [19:00, 21:00) 与节同一时辰，取庚辰、寅；酉时 [17:00, 19:00) 及当日更早时辰取己卯、丑。
  - MINUTE：20:40 起取庚辰、寅，之前取己卯、丑。

  2017 年立春为 2017-02-03 23:34:03，尽管当日约 98% 的时间在交节之前，DAY 仍将全天归新。
  DAY 调用方没有声明知道钟表时刻，不能据未知时刻改变归属或干支月长。

  子时跨午夜，相等时辰窗口可始于前一公历日：2009 年立春为 2009-02-04 00:49:48，
  所属子时始于 02-03 23:00，因此 HOUR 的 02-03 23:30 归新，DAY 的同日却归旧。
  三档不构成嵌套细化。

  HOUR 与 MINUTE 需要真实节时刻；`Bazi.__init__` 拒绝这两档使用 HKO，
  因为它的 `jieqi_moment` 只有午夜占位，见 `CalendarUtilsProtocol`。
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


_PRECISION_ALIASES: Final[frozendict[str, BaziPrecision]] = frozendict({
  alias: precision
  for precision, aliases in (
    (BaziPrecision.MINUTE, ('分', '分钟', 'm', 'min', 'minute')),
    (BaziPrecision.HOUR,   ('时', '小时', 'h', 'hour')),
    (BaziPrecision.DAY,    ('天', '日', 'd', 'day')),
  )
  for alias in aliases
})


class DayunYearRule(Enum):
  '''
  把每个精确大运边界投影为年份标签的规则。

  - JIE_PROJECTED：逐个边界按所属节投影干支年；首步标签不早于命盘按精度归属的出生年。
  - FIXED_DECADE：从共享首标签起按传统固定十年排表；后续标签表示年表位次，不保证是边界所在干支年。
  '''
  JIE_PROJECTED = 'jie_projected'
  FIXED_DECADE  = 'fixed_decade'

  def __str__(self) -> str:
    return self.value

  @staticmethod
  def from_str(s: str) -> 'DayunYearRule':
    '''
    从成员名或值解析 `DayunYearRule`（大小写不敏感）。

    Args:
    - s: (str) 待解析字符串；没有匹配规则时抛 `ValueError`。
    '''
    if not isinstance(s, str):
      raise TypeError(f'Expected str, got {type(s)}')
    for member in DayunYearRule:
      if s.lower() in (member.name.lower(), member.value.lower()):
        return member
    raise ValueError(f'Unsupported Dayun year rule: {s}')


class DayRollover(Enum):
  '''
  日柱换日点的流派分歧。

  - WAN_ZISHI（晚子时）：23:00 子时一开始即换日柱，[23:00, 24:00) 取次日日柱。
    默认采用此多数派读法，行为由 `test_bazi` 验证。
  - ZIZHENG（子正）：00:00 才换日柱，子时按民用日期取日柱，不提前换。

  Note:
  - 年/月柱独立按 `BaziPrecision` 比较节时刻，相等归新。WAN_ZISHI 的 23:30 出生取次日日柱，
    不使年/月归属随之改变。

  不修改既有定义；新读法须另加定义。
  '''
  WAN_ZISHI = 0
  ZIZHENG   = 1


class Anchor(Enum):
  '''
  神煞查法所锚的柱位（流派分歧处）。

  - YEAR：以年柱为锚。
  - DAY：以日柱为锚。
  - YEAR_AND_DAY：年、日两柱分别为锚，各查一遍。

  成员只指定锚柱；取该柱天干还是地支由神煞自身的查法决定，记录在分析层注册表中。
  `_ANCHOR_CHOICES` 按字段列出支持的取值及出处或已知出处缺口，`BaziSchool` 拒绝表外取值。

  不修改既有定义；新读法须另加定义。
  '''
  YEAR         = 0
  DAY          = 1
  YEAR_AND_DAY = 2


'''各锚选项支持的取值，连同出处或已知出处缺口逐行记录。表外取值只表示本库不支持，不表示没有
流派如此读（见驿马）；新增取值属于知识变更，须有出处。
出处计数规则见 `ShenshaRules` 的 docstring。'''
_ANCHOR_CHOICES: Final[frozendict[str, frozenset[Anchor]]] = frozendict({
  # 红艳：DAY 依问真（https://book.taiyi.me/命/神煞大全，「以日干查四地支」）及高人，
  # 高人将红艳列于「日干查地支」节。《三命通会·桃花紅艷煞》只给干支表，未定锚柱。
  # YEAR 自 #69 起支持，但出处仍缺；所查材料亦未见 YEAR_AND_DAY 读法。
  'hongyan_anchor':   frozenset({Anchor.DAY, Anchor.YEAR}),
  # 天乙贵人：DAY 为子平法，袁树珊《命理探原》NLC 刊本「以日爲主。如甲日見丑見未」。
  # YEAR 为以年柱取贵神的禄命法，见《五行精纪》卷十四引陈希烈疏：
  # 「假如丑未生人，月日時得甲戊庚，是遇正天乙也。甲子人十二月生，是遇貴神」
  # （https://www.suanzhun.net/book/2742.html）；同版注者在
  # https://www.suanzhun.net/book/2728.html 明言两法之分。
  # YEAR_AND_DAY 为问真、高人的现代主流读法，也是本库默认值。
  'tianyi_anchor':    frozenset({Anchor.DAY, Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 金舆：DAY 依袁树珊《命理探源》
  # （https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb）；YEAR_AND_DAY 依问真
  # （https://book.taiyi.me/命/神煞大全）。
  'jinyu_anchor':     frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  # 灾煞：YEAR 依问真（https://book.taiyi.me/命/神煞大全#灾煞）；YEAR_AND_DAY 依高人
  # （https://github.com/gaorenyes/gaorenyes.github.io/blob/817ad1f8f463d489087ac6c44ec69165e1181454/README.md#L367-L439）。
  'zaisha_anchor':    frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 驿马、华盖、将星、劫煞、亡神共用两种锚读法：YEAR_AND_DAY 依问真现代查法
  # （https://book.taiyi.me/命/神煞大全），为本库默认；DAY 均依袁树珊《命理探原》NLC 刊本，
  # 见显式声明这五项读法的 BaziSchool.mingli_tanyuan。
  # 《命理探原·卷上强弱》印页六五另载驿马 YEAR 读法：「申子辰年馬在寅。
  # 以年爲主。亦是一法」。#181 不添加新读法，因此尚不支持。
  'yima_anchor':      frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'huagai_anchor':    frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'jiangxing_anchor': frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'jiesha_anchor':    frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'wangshen_anchor':  frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  # 文昌：DAY 依袁树珊《命理探源》卷三「以日主为主，如甲见己，乙见午是也」
  # （https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb）；该版作己，
  # 但本版按语「故甲以巳为文昌也」要求巳。YEAR_AND_DAY 依问真
  # （https://book.taiyi.me/命/神煞大全，「以日/年干查四地支」）与高人，为本库默认。
  # 年干部分仅有这些现代来源，所查古籍未见以年干查文昌的明文。
  'wenchang_anchor':  frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  # 太极贵人：YEAR 依《五行精纪注释》卷十三「太极贵人，从年干取」
  # （https://www.suanzhun.net/book/2728.html）。YEAR_AND_DAY 依问真
  # （https://book.taiyi.me/命/神煞大全，「以日/年干查四地支」）与高人，为本库默认。
  # 与文昌的出处缺口相反：文昌古籍锚为日干，现代来源加年干；太极古籍锚为年干，现代来源加日干。
  'taiji_anchor':     frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 国印贵人：YEAR 依《五行精纪注释》卷十三今人【注释】：
  # 「国印星，命局见年干禄前第八位的地支」
  # （https://www.suanzhun.net/book/2731.html），同页举例「甲禄在寅，
  # 寅前八位是酉」。YEAR_AND_DAY 依问真、高人的现代读法，为本库默认。
  # GuoyinDef 的抄本见证不能证明此今人注释所取的锚。
  'guoyin_anchor':    frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY}),
})


@dataclass(frozen=True)
class BaziSchool:
  '''
  命盘采用的流派读法，只声明、不演算。`day_rollover` 在排盘期决定日柱，
  其余字段在神煞与关系求值时读取。每个字段均参与相等性及 JSON；
  只差一个选项的命盘也不同，相等档案的哈希相等。

  出生精度、历法后端见 `BaziConfig`；性别由 `Bazi` 输入。
  字段须为不可变类型（枚举或 frozen 值类型），不得用 dict / list 默认值，避免修改共享默认实例。

  默认流派由字段默认值组成；关系定义默认值取自规则层的共享对象。
  `DEFAULT_SCHOOL` 构造即默认，`BaziConfig.school` 指向同一实例。
  '''
  day_rollover:  DayRollover = DayRollover.WAN_ZISHI
  anhe_def:      DizhiRules.AnheDef = DEFAULT_DIZHI_RELATION_DEFINITIONS.anhe_def
  xing_def:      DizhiRules.XingDef = DEFAULT_DIZHI_RELATION_DEFINITIONS.xing_def
  gong_def:      DizhiRules.GongDef = DEFAULT_DIZHI_RELATION_DEFINITIONS.gong_def
  yangren_def:   ShenshaRules.YangrenDef = ShenshaRules.YangrenDef.ZIPING
  feiren_def:    ShenshaRules.YangrenDef = ShenshaRules.YangrenDef.ZIPING

  # 神煞锚与各自定义；锚的出处与支持读法见 _ANCHOR_CHOICES 对应行。
  hongyan_anchor:   Anchor = Anchor.DAY
  tianyi_anchor:    Anchor = Anchor.YEAR_AND_DAY
  tianyi_def:       ShenshaRules.TianyiDef = ShenshaRules.TianyiDef.GENG_WITH_JIA_WU
  yima_anchor:      Anchor = Anchor.YEAR_AND_DAY
  huagai_anchor:    Anchor = Anchor.YEAR_AND_DAY
  jiangxing_anchor: Anchor = Anchor.YEAR_AND_DAY
  jiesha_anchor:    Anchor = Anchor.YEAR_AND_DAY
  wangshen_anchor:  Anchor = Anchor.YEAR_AND_DAY
  jinyu_anchor:     Anchor = Anchor.DAY
  zaisha_anchor:    Anchor = Anchor.YEAR
  wenchang_anchor:  Anchor = Anchor.YEAR_AND_DAY
  wenchang_def:     ShenshaRules.WenchangDef = ShenshaRules.WenchangDef.XIN_ZI
  taiji_anchor:     Anchor = Anchor.YEAR_AND_DAY
  taiji_def:        ShenshaRules.TaijiDef = ShenshaRules.TaijiDef.REN_GUI_BOTH
  guoyin_anchor:    Anchor = Anchor.YEAR_AND_DAY
  guoyin_def:       ShenshaRules.GuoyinDef = ShenshaRules.GuoyinDef.MODERN

  def __post_init__(self) -> None:
    check_declared_types(self)
    for name, allowed in _ANCHOR_CHOICES.items():
      anchor = getattr(self, name)
      if anchor not in allowed:
        raise ValueError(f'Unsupported anchor for {name}: {anchor}; supported: {sorted(a.name for a in allowed)}')

  @property
  def relation_definitions(self) -> DizhiRelationDefinitions:
    '''由本流派的暗合、刑与拱局定义构造查询对象。'''
    return DizhiRelationDefinitions(
      anhe_def=self.anhe_def,
      xing_def=self.xing_def,
      gong_def=self.gong_def,
    )

  @classmethod
  def mingli_tanyuan(cls) -> 'BaziSchool':
    '''
    据袁树珊《命理探原》NLC 刊本与《命理探源》ctext 版整理的口径档案：两版所载的八个锚各取
    其读法。驿马、华盖、将星、劫煞、亡神以日支为锚（原局随之查年、月、时支）；天乙贵人、
    金舆与文昌以日干为锚。金舆恰好也是当前默认，预设仍把它写出来——档案声明的是两版所载
    读法，默认值日后改动不该悄悄改写它。

    Note:
    - 其余选项保持默认。

    出处：
    - 《命理探原·卷上强弱》NLC 刊本：
      https://commons.wikimedia.org/wiki/File:NLC416-07jh011647-5318_命理探源.pdf
    - 《命理探源》ctext 版（金輿祿「以日主為主，如甲日見辰」）：
      https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
      两版文字不同：NLC 刊本无金舆条，作「以日爲主」；ctext 作「以日主為主」。

    Return: (BaziSchool) 冻结的流派档案。
    '''

    return cls(
      tianyi_anchor=Anchor.DAY,
      yima_anchor=Anchor.DAY,
      huagai_anchor=Anchor.DAY,
      jiangxing_anchor=Anchor.DAY,
      jiesha_anchor=Anchor.DAY,
      wangshen_anchor=Anchor.DAY,
      jinyu_anchor=Anchor.DAY,
      wenchang_anchor=Anchor.DAY,
    )

  @classmethod
  def from_json(cls, d: Mapping[str, object]) -> 'BaziSchool':
    '''
    从 `BaziChart.json` 的 `school` 对象还原流派档案，是序列化的逆运算。
    各字段按自身声明的枚举解析，新增字段也会被读取。

    Args:
    - d: (Mapping[str, object]) 每个 `BaziSchool` 字段名对应其枚举成员名，
      如 `{'day_rollover': 'WAN_ZISHI', ...}`；不对应字段的键被忽略。

    Note:
    - 入参不是 `Mapping` 抛 `TypeError`，缺字段抛 `ValueError`，
      值非 `str` 抛 `TypeError`，成员名不存在抛 `ValueError`，锚超出支持范围则由构造函数
      抛 `ValueError`。残缺字典不会回落默认值。

    Return: (BaziSchool) 还原的冻结流派档案。

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
      try:
        kwargs[f.name] = declared[name]
      except KeyError:
        raise ValueError(f'Unsupported {declared.__name__}: {name}') from None

    return cls(**kwargs)


DEFAULT_SCHOOL: Final[BaziSchool] = BaziSchool()


@dataclass(frozen=True)
class BaziConfig:
  '''
  命盘级不可变配置，包括出生精度、历法后端、大运年份投影及求值时读取的流派档案。
  Bazi 持有整个配置，配置参与相等性与 JSON。流运投影虽不改变四柱与大运物理时刻线，
  仍属于命盘身份；相等配置的哈希相等。

  Args:
  - precision: (BaziPrecision) 出生时间精度。
  - backend: (CalendarBackend) 所有历法换算所用的后端。
  - school: (BaziSchool) 流派档案，默认 `DEFAULT_SCHOOL`。
  - dayun_year_rule: (DayunYearRule) 默认大运年份投影。

  Note:
  - 性别不影响本配置所聚合的四柱计算，仍由 `Bazi.create` 接收并解析字符串。
  - 构造只收声明类型，字符串解析由 `from_values` 提供。
  '''
  precision:        BaziPrecision   = BaziPrecision.DAY
  backend:          CalendarBackend = CalendarBackend.CELESTIAL
  school:           BaziSchool      = DEFAULT_SCHOOL
  dayun_year_rule:  DayunYearRule   = DayunYearRule.JIE_PROJECTED

  def __post_init__(self) -> None:
    # 此处不转换类型；字符串解析由 from_values 提供。
    check_declared_types(self)

  @classmethod
  def from_values(cls, precision: BaziPrecision | str = BaziPrecision.DAY,
                  backend: CalendarBackend | str = CalendarBackend.CELESTIAL,
                  school: BaziSchool = DEFAULT_SCHOOL,
                  dayun_year_rule: DayunYearRule | str = DayunYearRule.JIE_PROJECTED) -> 'BaziConfig':
    '''
    从枚举或支持的字符串构造 `BaziConfig`。

    Args:
    - precision: (BaziPrecision | str) 出生精度。字符串支持
      "分"/"分钟"/"时"/"小时"/"天"/"日"/"m"/"min"/"minute"/"h"/"hour"/"d"/"day"，
      大小写不敏感，其他值抛 `ValueError`。
    - backend: (CalendarBackend | str) 历法后端；`CalendarBackend.from_str` 接受成员名或值，
      如 "HKO"/"hko"，大小写不敏感，其他值抛 `ValueError`。
    - school: (BaziSchool) 流派档案，不接受字符串；类型错误由构造函数抛 `TypeError`。
    - dayun_year_rule: (DayunYearRule | str) 大运年份投影；`DayunYearRule.from_str` 接受成员名或值，
      如 "FIXED_DECADE"/"fixed_decade"，大小写不敏感，其他值抛 `ValueError`。

    Return: (BaziConfig) 解析后的冻结配置。
    '''

    if not isinstance(precision, (BaziPrecision, str)):
      raise TypeError(f'Expected BaziPrecision or str, got {type(precision)}')
    if not isinstance(backend, (CalendarBackend, str)):
      raise TypeError(f'Expected CalendarBackend or str, got {type(backend)}')
    if not isinstance(dayun_year_rule, (DayunYearRule, str)):
      raise TypeError(f'Expected DayunYearRule or str, got {type(dayun_year_rule)}')

    try:
      _precision = _PRECISION_ALIASES[precision.lower()] if isinstance(precision, str) else precision
    except KeyError:
      raise ValueError(f'Unsupported precision: {precision}') from None

    return cls(
      precision=_precision,
      backend=CalendarBackend.from_str(backend) if isinstance(backend, str) else backend,
      school=school,
      dayun_year_rule=DayunYearRule.from_str(dayun_year_rule) if isinstance(dayun_year_rule, str) else dayun_year_rule,
    )


DEFAULT_CONFIG: Final[BaziConfig] = BaziConfig()


class _ConfigJson(TypedDict):
  backend:         str
  precision:       str
  dayun_year_rule: str
  school:          dict[str, str]


def _config_json(config: BaziConfig) -> _ConfigJson:
  '''序列化配置值；流派字段存枚举成员名。'''
  assert isinstance(config, BaziConfig)
  return {
    'backend':         str(config.backend),
    'precision':       str(config.precision),
    'dayun_year_rule': str(config.dayun_year_rule),
    'school':          {knob.name: getattr(config.school, knob.name).name for knob in fields(config.school)},
  }
