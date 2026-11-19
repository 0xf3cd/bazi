# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''命盘配置 `BaziConfig`、流派分歧声明 `BaziSchool` / `DayRollover` / `Anchor`，
以及出生精度和大运年份投影选项 `BaziPrecision` / `DayunYearRule`。'''

from enum import Enum
from dataclasses import dataclass
from typing import Final

from .common import check_declared_types, frozendict, _compact_dataclass_repr
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
  2000 年立春为 2000-02-04 20:40:23。
  - DAY：02-04 全天取年柱庚辰、月支寅，包括 20:40:23 之前；02-03 取己卯、丑。
  - HOUR：戌时 [19:00, 21:00) 与节同一时辰，取庚辰、寅；酉时 [17:00, 19:00) 及当日更早时辰取己卯、丑。
  - MINUTE：20:40 起取庚辰、寅，之前取己卯、丑。

  2017 年立春为 2017-02-03 23:34:03，尽管当日约 98% 的时间在交节之前，DAY 仍将全天归新。
  DAY 调用方没有声明知道钟表时刻，不能据未知时刻改变归属或干支月长。

  子时跨午夜，相等时辰窗口可始于前一公历日：2009 年立春为 2009-02-04 00:49:48，
  所属子时始于 02-03 23:00，因此 HOUR 的 02-03 23:30 归新，DAY 的同日却归旧。
  三档不构成嵌套细化。
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
    默认采用此多数派读法。
  - ZIZHENG（子正）：00:00 才换日柱，子时按民用日期取日柱，不提前换。

  Note:
  - 年/月柱独立按 `BaziPrecision` 比较节时刻，相等归新。WAN_ZISHI 的 23:30 出生取次日日柱，
    不使年/月归属随之改变。
  '''
  WAN_ZISHI = 0
  ZIZHENG   = 1


class PeiouXingDef(Enum):
  '''
  配偶星取法的流派分歧。

  - ZHENGCAI_ZHENGGUAN：男命取正财干、女命取正官干。默认。
  - YINYANGGAN：《三命通会·卷七·论六亲》读法：男命取我所克五行中的阴干，女命取克我五行中的阳干。
    读法与出处见知识条目 `editorial.liuqin.spouse_star_yinyanggan.v1`。

  Note:
  - 两读在阳男、阴女十格上目标相同，在阴男、阳女十格上不同；每个（日主，性别）仍恰有一个目标天干。
  - 地支侧均取主气等于目标天干的地支。
  '''
  ZHENGCAI_ZHENGGUAN = 0
  YINYANGGAN         = 1


class Anchor(Enum):
  '''
  神煞查法所锚的柱位（流派分歧处）。

  - YEAR：以年柱为锚。
  - DAY：以日柱为锚。
  - YEAR_AND_DAY：年、日两柱分别为锚，各查一遍。

  成员只指定锚柱；取该柱天干、地支还是完整干支由神煞自身的查法决定，记录在分析层注册表中。
  `_ANCHOR_CHOICES` 按字段列出支持的取值与知识入口，`BaziSchool` 拒绝表外取值。
  '''
  YEAR         = 0
  DAY          = 1
  YEAR_AND_DAY = 2


class TuwangDef(Enum):
  '''季月土旺的三种可选口径，计日及精度政策见 BaziChart.wuxing_states。

  - WHOLE_MONTH：辰、未、戌、丑整月土旺，本库默认的简化取法。
  - AFTER_TWELVE_DAYS：开月节后十二日转土，此前仍取该季节本令。
    出处：《三命通会》卷二醉醒子段，维基文库转录：
    https://zh.wikisource.org/w/index.php?oldid=761691
  - BEFORE_EIGHTEEN_DAYS：下一四立前十八日转土，此前仍取该季节本令。
    出处：《协纪辨方书》卷一转引《神枢经》《历例》，维基文库转录：
    https://zh.wikisource.org/w/index.php?oldid=787334
    《命理探源》卷三四季土旺表亦载此说：
    https://zhonghuadiancang.com/xuanxuewushu/minglitanyuan/160972.html
  '''
  WHOLE_MONTH          = 'whole_month'
  AFTER_TWELVE_DAYS    = 'after_twelve_days'
  BEFORE_EIGHTEEN_DAYS = 'before_eighteen_days'


'''各锚选项支持的取值。表外取值只表示本库不支持；查法与出处沿各行条目 ID 查阅。'''
_ANCHOR_CHOICES: Final[frozendict[str, frozenset[Anchor]]] = frozendict({
  # 红艳：shensha.hongyan.readings。
  'hongyan_anchor':   frozenset({Anchor.DAY, Anchor.YEAR}),
  # 天乙贵人：shensha.tianyi.readings。
  'tianyi_anchor':    frozenset({Anchor.DAY, Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 金舆：shensha.jinyu.readings。
  'jinyu_anchor':     frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  # 灾煞：shensha.zaisha.readings。
  'zaisha_anchor':    frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 驿马、华盖、将星、劫煞、亡神：concept.mingli_tanyuan.readings。
  'yima_anchor':      frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'huagai_anchor':    frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'jiangxing_anchor': frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'jiesha_anchor':    frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  'wangshen_anchor':  frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  # 文昌：shensha.wenchang.readings。
  'wenchang_anchor':  frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}),
  # 太极贵人：shensha.taiji.readings。
  'taiji_anchor':     frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 国印贵人：shensha.guoyin.readings。
  'guoyin_anchor':    frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY}),
  # 六甲旬空取完整干支；查法见 shensha.kongwang.lookup、shensha.kongwang.repository。
  'kongwang_anchor':  frozenset({Anchor.DAY, Anchor.YEAR, Anchor.YEAR_AND_DAY}),
})


@dataclass(frozen=True)
class BaziSchool:
  '''
  命盘采用的流派读法。day_rollover 在排盘期决定日柱，tuwang_def 用于月令五行状态，
  其余字段选择神煞、关系与配偶星取法。

  常见选择：
  - day_rollover：按 23:00 换日柱用 WAN_ZISHI，按 00:00 换日柱用 ZIZHENG。
  - tuwang_def：季月整月土旺用 WHOLE_MONTH；按开月节后十二日或下一四立前十八日分段时，
    分别用 AFTER_TWELVE_DAYS 或 BEFORE_EIGHTEEN_DAYS。
  - peiou_xing_def：男取正财、女取正官用 ZHENGCAI_ZHENGGUAN；男取所克阴干、女取克我阳干用 YINYANGGAN。
  - kongwang_anchor：只查日柱旬空用 DAY，只查年柱用 YEAR，年、日各查一遍用 YEAR_AND_DAY。
  - 其余 `*_def` 按对应枚举说明选择读法；`*_anchor` 按查法依据的柱位选择，
    每个字段支持的成员见{doc}`配置指南 </guides/configuration>`中的锚点取值表。

  Note:
  - 出生精度见 `BaziConfig`；性别由 `Bazi` 输入。
  - 每个字段均参与相等性；只差一个选项的命盘也不同，相等档案的哈希相等。
  - 字段须为不可变类型（枚举或 frozen 值类型），不得用 dict / list 默认值，避免修改共享默认实例。
  - 默认流派由字段默认值组成；关系定义默认值取自规则层的共享对象。
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

  # 配偶星取法；两读的差异面见 PeiouXingDef。
  peiou_xing_def:   PeiouXingDef = PeiouXingDef.ZHENGCAI_ZHENGGUAN

  # 六甲旬空整柱锚；尾部追加以保留既有位置参数次序。
  kongwang_anchor:  Anchor = Anchor.DAY

  tuwang_def: TuwangDef = TuwangDef.WHOLE_MONTH

  def __post_init__(self) -> None:
    check_declared_types(self)
    for name, allowed in _ANCHOR_CHOICES.items():
      anchor = getattr(self, name)
      if anchor not in allowed:
        raise ValueError(f'Unsupported anchor for {name}: {anchor}; supported: {sorted(a.name for a in allowed)}')

  def __repr__(self) -> str:
    return _compact_dataclass_repr(self)

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
    返回《命理探原》日锚档案，出处见知识条目 concept.mingli_tanyuan.readings。
    驿马、华盖、将星以日支为锚（原局随之查年、月、时支）；天乙贵人与文昌以日干为锚。
    劫煞、亡神取日支，金舆取日干。

    Note:
    - 其余选项保持默认。

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


DEFAULT_SCHOOL: Final[BaziSchool] = BaziSchool()


@dataclass(frozen=True)
class BaziConfig:
  '''
  命盘级不可变配置，包括出生精度、大运年份投影及求值时读取的流派档案。
  Bazi 持有整个配置，配置参与相等性。大运年份投影虽不改变四柱与大运物理时刻线，
  仍属于命盘身份；相等配置的哈希相等。

  Args:
  - precision: (BaziPrecision) 出生时间精度。
  - school: (BaziSchool) 流派档案，默认 `DEFAULT_SCHOOL`。
  - dayun_year_rule: (DayunYearRule) 默认大运年份投影。

  Note:
  - 性别不影响本配置所聚合的四柱计算，仍由 `Bazi.create` 接收并解析字符串。
  - 构造只收声明类型，字符串解析由 `from_values` 提供。
  '''
  precision:        BaziPrecision   = BaziPrecision.DAY
  school:           BaziSchool      = DEFAULT_SCHOOL
  dayun_year_rule:  DayunYearRule   = DayunYearRule.JIE_PROJECTED

  def __post_init__(self) -> None:
    # 此处不转换类型；字符串解析由 from_values 提供。
    check_declared_types(self)

  def __repr__(self) -> str:
    return _compact_dataclass_repr(self)

  @classmethod
  def from_values(cls, precision: BaziPrecision | str = BaziPrecision.DAY,
                  school: BaziSchool = DEFAULT_SCHOOL,
                  dayun_year_rule: DayunYearRule | str = DayunYearRule.JIE_PROJECTED) -> 'BaziConfig':
    '''
    从枚举或支持的字符串构造 `BaziConfig`。

    Args:
    - precision: (BaziPrecision | str) 出生精度。字符串支持
      "分"/"分钟"/"时"/"小时"/"天"/"日"/"m"/"min"/"minute"/"h"/"hour"/"d"/"day"，
      大小写不敏感，其他值抛 `ValueError`。
    - school: (BaziSchool) 流派档案，不接受字符串；类型错误由构造函数抛 `TypeError`。
    - dayun_year_rule: (DayunYearRule | str) 大运年份投影；`DayunYearRule.from_str` 接受成员名或值，
      如 "FIXED_DECADE"/"fixed_decade"，大小写不敏感，其他值抛 `ValueError`。

    Return: (BaziConfig) 解析后的冻结配置。
    '''

    if not isinstance(precision, (BaziPrecision, str)):
      raise TypeError(f'Expected BaziPrecision or str, got {type(precision)}')
    if not isinstance(dayun_year_rule, (DayunYearRule, str)):
      raise TypeError(f'Expected DayunYearRule or str, got {type(dayun_year_rule)}')

    try:
      _precision = _PRECISION_ALIASES[precision.lower()] if isinstance(precision, str) else precision
    except KeyError:
      raise ValueError(f'Unsupported precision: {precision}') from None

    return cls(
      precision=_precision,
      school=school,
      dayun_year_rule=DayunYearRule.from_str(dayun_year_rule) if isinstance(dayun_year_rule, str) else dayun_year_rule,
    )


DEFAULT_CONFIG: Final[BaziConfig] = BaziConfig()
