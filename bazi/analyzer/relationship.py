# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import functools

from dataclasses import dataclass
from enum import Enum, IntFlag, auto, unique
from itertools import product
from typing import Final, TypedDict, cast
from collections.abc import Callable, Iterable

from ..common import frozendict
from ..data_types import GanzhiData
from ..defines import Tiangan, Dizhi, Ganzhi, Shishen, DizhiRelation
from ..rules import DizhiRules
from ..school import Anchor, BaziSchool
from ..bazi import Bazi
from ..bazi_chart import BaziChart
from ..transits import TransitSet
from ..utils import bazi_utils, shensha_utils, tiangan_utils, dizhi_utils


'''从命盘流派解析神煞判断函数的可选 definition 参数。'''
_DefinitionResolver = Callable[[BaziSchool], object]


@unique
class _AnchorKind(Enum):
  '''神煞查法取锚柱的天干还是地支。'''
  TIANGAN = auto()
  DIZHI   = auto()


'''各 Anchor 选择的柱位序号，按年、月、日、时排序。'''
_ANCHOR_PILLARS: Final[frozendict[Anchor, tuple[int, ...]]] = frozendict({
  Anchor.YEAR:         (0,),
  Anchor.DAY:          (2,),
  Anchor.YEAR_AND_DAY: (0, 2),
})

'''在流派有分歧处，从命盘流派解析神煞锚柱。'''
_AnchorResolver = Callable[[BaziSchool], Anchor]


@dataclass(frozen=True)
class _ShenshaSpec:
  '''
  神煞的规格：判断函数、查法锚、展示标签，以及可选的流派定义参数。

  kind 指定取锚柱天干还是地支；anchor 指定锚柱，无分歧时为固定 Anchor，
  有分歧时为读取命盘选项的解析函数。两者均须依该神煞自身出处，不能沿用既有神煞作默认，见 #167。

  Note:
  - predicate 的首参数类型须与 kind 一致；给定 definition 时，须通过同名仅关键字参数接收解析结果。
    各判断函数在运行时校验，注册表类型不能表达此契约。
  - label 是展示名，经 SHENSHA_LABELS 供渲染方使用，不参与查法。
  '''
  predicate:  Callable[..., bool]
  kind:       _AnchorKind
  anchor:     Anchor | _AnchorResolver
  label:      str
  definition: _DefinitionResolver | None = None


'''亲密关系分析支持的地支结果神煞注册表。'''
_REGISTRY: Final[frozendict[str, _ShenshaSpec]] = frozendict({
  # 桃花不设旋钮：《命理探源》的日支桃花另有纳音条件且只查月、时，只切锚会造出出处未言的规则。
  'taohua'     : _ShenshaSpec(shensha_utils.taohua,      _AnchorKind.DIZHI,   Anchor.YEAR_AND_DAY, '桃花'),
  'hongluan'   : _ShenshaSpec(shensha_utils.hongluan,    _AnchorKind.DIZHI,   Anchor.YEAR, '红鸾'),
  'hongyan'    : _ShenshaSpec(shensha_utils.hongyan,     _AnchorKind.TIANGAN, lambda school: school.hongyan_anchor, '红艳'),
  'tianxi'     : _ShenshaSpec(shensha_utils.tianxi,      _AnchorKind.DIZHI,   Anchor.YEAR, '天喜'),
  'yima'       : _ShenshaSpec(shensha_utils.yima,        _AnchorKind.DIZHI,   lambda school: school.yima_anchor, '驿马'),
  'huagai'     : _ShenshaSpec(shensha_utils.huagai,      _AnchorKind.DIZHI,   lambda school: school.huagai_anchor, '华盖'),
  'yangren'    : _ShenshaSpec(
    shensha_utils.yangren,
    _AnchorKind.TIANGAN,
    Anchor.DAY,
    '羊刃',
    lambda school: school.yangren_def,
  ),
  'feiren'     : _ShenshaSpec(
    shensha_utils.feiren,
    _AnchorKind.TIANGAN,
    Anchor.DAY,
    '飞刃',
    lambda school: school.feiren_def,
  ),
  'tianyi'     : _ShenshaSpec(
    shensha_utils.tianyi,
    _AnchorKind.TIANGAN,
    lambda school: school.tianyi_anchor,
    '天乙贵人',
    lambda school: school.tianyi_def,
  ),
  'jiangxing'  : _ShenshaSpec(shensha_utils.jiangxing,   _AnchorKind.DIZHI,   lambda school: school.jiangxing_anchor, '将星'),
  'zaisha'     : _ShenshaSpec(shensha_utils.zaisha,      _AnchorKind.DIZHI,   lambda school: school.zaisha_anchor, '灾煞'),
  'jiesha'     : _ShenshaSpec(shensha_utils.jiesha,      _AnchorKind.DIZHI,   lambda school: school.jiesha_anchor, '劫煞'),
  'wangshen'   : _ShenshaSpec(shensha_utils.wangshen,    _AnchorKind.DIZHI,   lambda school: school.wangshen_anchor, '亡神'),
  'guchen'     : _ShenshaSpec(shensha_utils.guchen,      _AnchorKind.DIZHI,   Anchor.YEAR, '孤辰'),
  'guasu'      : _ShenshaSpec(shensha_utils.guasu,       _AnchorKind.DIZHI,   Anchor.YEAR, '寡宿'),
  'lushen'     : _ShenshaSpec(shensha_utils.lushen,      _AnchorKind.TIANGAN, Anchor.DAY, '禄神'),
  'jinyu'      : _ShenshaSpec(shensha_utils.jinyu,       _AnchorKind.TIANGAN, lambda school: school.jinyu_anchor, '金舆'),
  # 文昌与文昌贵是两颗星，不是一颗星的两种读法；两表的重合面写在 `ShenshaRules.WENCHANGGUI`。
  'wenchang'   : _ShenshaSpec(
    shensha_utils.wenchang,
    _AnchorKind.TIANGAN,
    lambda school: school.wenchang_anchor,
    '文昌',
    lambda school: school.wenchang_def,
  ),
  'wenchanggui': _ShenshaSpec(shensha_utils.wenchanggui, _AnchorKind.TIANGAN, Anchor.YEAR, '文昌贵'),
  # 太极贵人一干所对地支数不一（戊己占四库）。多支是 predicate 内部的事，
  # 注册表与分析结果的形状不变。
  'taiji'      : _ShenshaSpec(
    shensha_utils.taiji,
    _AnchorKind.TIANGAN,
    lambda school: school.taiji_anchor,
    '太极贵人',
    lambda school: school.taiji_def,
  ),
  # 国印贵人两读共用一个旋钮，无一格重合，详见 `ShenshaRules.GuoyinDef`。
  'guoyin'     : _ShenshaSpec(
    shensha_utils.guoyin,
    _AnchorKind.TIANGAN,
    lambda school: school.guoyin_anchor,
    '国印贵人',
    lambda school: school.guoyin_def,
  ),
})


'''按注册序提供神煞展示标签，供 run_relationship_analyzer.py 等渲染方使用；
从注册表推导，新增条目无需维护第二份列表。'''
SHENSHA_LABELS: Final[frozendict[str, str]] = frozendict({
  name: spec.label for name, spec in _REGISTRY.items()
})


def _anchor_keys(spec: _ShenshaSpec, bazi: Bazi) -> tuple[tuple[int, Tiangan | Dizhi], ...]:
  '''该神煞在本盘上的柱位序号与查询值，按年、月、日、时排序。'''
  anchor = spec.anchor if isinstance(spec.anchor, Anchor) else spec.anchor(bazi.config.school)
  pillars = bazi.pillars
  if spec.kind is _AnchorKind.TIANGAN:
    return tuple((index, pillars[index].tiangan) for index in _ANCHOR_PILLARS[anchor])
  return tuple((index, pillars[index].dizhi) for index in _ANCHOR_PILLARS[anchor])


def _shensha_predicate(spec: _ShenshaSpec, school: BaziSchool) -> Callable[..., bool]:
  '''存在流派定义参数时，按盘绑定该参数。'''
  if spec.definition is None:
    return spec.predicate
  definition = spec.definition(school)
  return functools.partial(spec.predicate, definition=definition)


def _eval_at_birth(spec: _ShenshaSpec, bazi: Bazi) -> frozenset[Dizhi]:
  '''在原局上判断某神煞。
  干锚查四支，支锚查其余三支（地支不自查），双锚按柱各查一次。
  '''
  dizhis = bazi.four_dizhis
  keys = _anchor_keys(spec, bazi)

  predicate = _shensha_predicate(spec, bazi.config.school)
  return frozenset(
    dz
    for index, key in keys
    for candidate_index, dz in enumerate(dizhis)
    if spec.kind is _AnchorKind.TIANGAN or candidate_index != index
    if predicate(key, dz)
  )


def _eval_transits(spec: _ShenshaSpec, bazi: Bazi, transit_dizhis: Iterable[Dizhi]) -> frozenset[Dizhi]:
  '''在流运地支上判断某神煞。
  流运地支不可能是锚柱自身，故每个锚值均查全部流运支。
  '''
  predicate = _shensha_predicate(spec, bazi.config.school)
  return frozenset(
    dz
    for (_, key), dz in product(_anchor_keys(spec, bazi), transit_dizhis)
    if predicate(key, dz)
  )


_DAY_PILLAR_INDEX: Final[int] = 2


def _day_pillar_participates(combo: dizhi_utils.GanzhiRelationCombo) -> bool:
  '''检查组合中是否有日柱这一具体出现，不以相同地支值代替柱位。'''
  return any(occurrence.index == _DAY_PILLAR_INDEX for occurrence in combo)


def _project_gong(
  discovery: dizhi_utils.GanzhiRelationDiscovery,
  predicate: Callable[[dizhi_utils.GanzhiRelationCombo], bool],
) -> dizhi_utils.DizhiRelationDiscovery:
  '''先按具体参与柱过滤拱局，再投影地支。'''
  return dizhi_utils.GanzhiRelationDiscovery({
    relation : filtered
    for relation in DizhiRules.GONG_RELATIONS
    if len(filtered := tuple(combo for combo in discovery.get(relation, ()) if predicate(combo))) > 0
  }).to_dizhi_discovery()


def _with_gong(
  existing: dizhi_utils.DizhiRelationDiscovery,
  gong: dizhi_utils.DizhiRelationDiscovery,
) -> dizhi_utils.DizhiRelationDiscovery:
  '''加入不重叠的拱局键，不重排既有组合。'''
  assert set(existing).isdisjoint(gong)
  return dizhi_utils.DizhiRelationDiscovery({**existing, **gong})


class ShenshaAnalysis(TypedDict):
  # 桃花星所在地支。
  taohua:      frozenset[Dizhi]
  # 红艳星所在地支。
  hongyan:     frozenset[Dizhi]
  # 红鸾星所在地支。
  hongluan:    frozenset[Dizhi]
  # 天喜星所在地支。
  tianxi:      frozenset[Dizhi]
  # 驿马星所在地支。
  yima:        frozenset[Dizhi]
  # 华盖星所在地支。
  huagai:      frozenset[Dizhi]
  # 羊刃所在地支。
  yangren:     frozenset[Dizhi]
  # 飞刃所在地支。
  feiren:      frozenset[Dizhi]
  # 天乙贵人所在地支。
  tianyi:      frozenset[Dizhi]
  # 将星所在地支。
  jiangxing:   frozenset[Dizhi]
  # 灾煞所在地支。
  zaisha:      frozenset[Dizhi]
  # 劫煞所在地支。
  jiesha:      frozenset[Dizhi]
  # 亡神所在地支。
  wangshen:    frozenset[Dizhi]
  # 孤辰所在地支。
  guchen:      frozenset[Dizhi]
  # 寡宿所在地支。
  guasu:       frozenset[Dizhi]
  # 禄神所在地支。
  lushen:      frozenset[Dizhi]
  # 金舆所在地支。
  jinyu:       frozenset[Dizhi]
  # 文昌所在地支。
  wenchang:    frozenset[Dizhi]
  # 文昌贵所在地支。
  wenchanggui: frozenset[Dizhi]
  # 太极贵人所在地支。
  taiji:       frozenset[Dizhi]
  # 国印贵人所在地支。
  guoyin:      frozenset[Dizhi]


class AtBirthShenshaAnalysis(ShenshaAnalysis):
  # 魁罡日柱。
  kuigang: Ganzhi | None
  # 天赦日柱。
  tianshe: Ganzhi | None


class AtBirthAnalysis:
  '''原局亲密关系分析。'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @property
  def shensha(self) -> AtBirthShenshaAnalysis:
    bazi = self._chart.bazi
    # 注册条目各存于自身键下，再加入两个整柱神煞，它们返回干支而非地支集合。
    # 推导式无法按 TypedDict 检查，由 test_analyses_are_built_from_the_registry 核对键集。
    return cast(AtBirthShenshaAnalysis, {
      **{name: _eval_at_birth(spec, bazi) for name, spec in _REGISTRY.items()},
      'kuigang'  : bazi.day_pillar if shensha_utils.kuigang(bazi.day_pillar) else None,
      'tianshe'  : bazi.day_pillar if shensha_utils.tianshe(bazi.month_commander, bazi.day_pillar) else None,
    })

  @property
  def day_master_relations(self) -> tiangan_utils.TianganRelationDiscovery:
    y_tg, m_tg, d_tg, h_tg = self._chart.bazi.four_tiangans
    return tiangan_utils.discover_mutual([d_tg], [y_tg, m_tg, h_tg])
  
  @property
  def house_relations(self) -> dizhi_utils.DizhiRelationDiscovery:
    '''婚姻宫的关系；拱局按本盘流派判断，只保留日柱这一具体出现参与的组合。'''
    # 非拱保留完整发现路径，以支持三支组合；原局上等价于日支与其余三支的跨组发现。
    # 重复日支值时，按值过滤会误收其他柱形成的拱局，因此先过滤具体参与柱，再投影。
    bazi: Final[Bazi] = self._chart.bazi
    definitions = bazi.config.school.relation_definitions
    existing = dizhi_utils.discover(bazi.four_dizhis, definitions=definitions).filter(
      lambda _, combo : self._chart.house_of_relationship in combo
    )
    gong = _project_gong(
      dizhi_utils.discover_ganzhis(
        bazi.pillars,
        definitions=definitions,
        relations=DizhiRules.GONG_RELATIONS,
      ),
      _day_pillar_participates,
    )
    return _with_gong(existing, gong)
  
  @property
  def star_relations(self) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''配偶星的天干、地支关系；拱局按本盘流派判断，只保留实支参与者含配偶星地支的组合。'''
    stars = self._chart.relationship_stars
    bazi: Final[Bazi] = self._chart.bazi
    definitions = bazi.config.school.relation_definitions

    tg = tiangan_utils.discover(bazi.four_tiangans).filter(lambda _, combo : stars.tiangan in combo)
    existing = dizhi_utils.discover(bazi.four_dizhis, definitions=definitions).filter(
      lambda _, combo : any(dz in combo for dz in stars.dizhi)
    )
    gong = _project_gong(
      dizhi_utils.discover_ganzhis(
        bazi.pillars,
        definitions=definitions,
        relations=DizhiRules.GONG_RELATIONS,
      ),
      lambda combo : any(occurrence.ganzhi.dizhi in stars.dizhi for occurrence in combo),
    )
    return GanzhiData(tg, _with_gong(existing, gong))



class TransitAnalysis:
  '''流运亲密关系分析。'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @staticmethod
  def _check_transits(transits: object) -> None:
    if not isinstance(transits, TransitSet):
      raise TypeError(f'Expected TransitSet, got {type(transits)}')

  def shensha(self, transits: TransitSet) -> ShenshaAnalysis:
    '''
    返回给定流运的亲密关系神煞分析。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Returns:
    - (ShenshaAnalysis) 给定流运的神煞结果。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = tuple(gz.dizhi for gz in transit_ganzhis)

    bazi = self._chart.bazi
    # 与原局同一份名册，只是查在流运地支上；说明见原局那处。
    return cast(ShenshaAnalysis, {
      name: _eval_transits(spec, bazi, transit_dizhis) for name, spec in _REGISTRY.items()
    })
  
  def day_master_relations(self, transits: TransitSet) -> tiangan_utils.TianganRelationDiscovery:
    '''
    返回日主和其他流运的天干之间的关系。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (tiangan_utils.TianganRelationDiscovery) 日主与流运天干的关系。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_tiangans = tuple(gz.tiangan for gz in transit_ganzhis)

    return tiangan_utils.discover_mutual([self._chart.bazi.day_master], transit_tiangans)

  def house_relations(self, transits: TransitSet) -> dizhi_utils.DizhiRelationDiscovery:
    '''
    返回配偶宫/婚姻宫和其他流运的地支之间的关系。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (dizhi_utils.DizhiRelationDiscovery) 婚姻宫与流运地支的关系。

    Note:
    - 拱局按本盘流派判断，只保留日柱这一具体出现参与的组合。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = [gz.dizhi for gz in transit_ganzhis]

    house = self._chart.house_of_relationship
    bazi = self._chart.bazi
    definitions = bazi.config.school.relation_definitions

    # 三支组合可横跨婚姻宫、另一原局支与流运支；先查完整原局侧，再保留有流运参与的宫组合。
    # discover_mutual 按值查，只有重复的宫支值不能证明多支组合有流运参与；单支自刑则可以。
    def __is_house_transit_relation(_: DizhiRelation, combo: frozenset[Dizhi]) -> bool:
      if house not in combo:
        return False
      if len(combo) == 1:
        return house in transit_dizhis
      return not (combo - {house}).isdisjoint(transit_dizhis)

    existing = dizhi_utils.discover_mutual(
      bazi.four_dizhis,
      transit_dizhis,
      definitions=definitions,
    ).filter(__is_house_transit_relation)
    gong = _project_gong(
      dizhi_utils.discover_mutual_ganzhis(
        bazi.pillars,
        transit_ganzhis,
        definitions=definitions,
        relations=DizhiRules.GONG_RELATIONS,
      ),
      _day_pillar_participates,
    )
    return _with_gong(existing, gong)
  
  @unique
  class Level(IntFlag):
    # 只分析流运。
    TRANSITS_ONLY        = 1 << 0

    # 分析流运与原局的跨组关系。
    MUTUAL               = 1 << 1

    # 合并上述两种范围。
    ALL                  = TRANSITS_ONLY | MUTUAL

  '''level 参数支持的全部常量级别。'''
  _ALL_LEVELS: Final[tuple[Level, ...]] = (Level.TRANSITS_ONLY, Level.MUTUAL, Level.ALL)

  def star_relations(
    self,
    transits: TransitSet,
    *, level: Level = Level.ALL,
  ) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''
    返回配偶星/婚姻星和其他流运的干支之间的关系。

    Args:
    - transits: (TransitSet) 参与分析的流运。
    - level: (Level) 分析范围。

    Return: (GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery])
    配偶星与流运干支的天干、地支关系。

    Note:
    - 拱局按本盘流派判断，并只保留实支参与者含配偶星地支的组合。`TRANSITS_ONLY` 的相邻关系
      按 `transits.ganzhis` 中实际存在的流运计算；缩小 `TransitSet` 可能因此改变拱局相邻关系。
    '''

    if not isinstance(level, TransitAnalysis.Level):
      raise TypeError(f'Expected Level, got {type(level)}')
    if level not in TransitAnalysis._ALL_LEVELS:
      raise ValueError(f'Unsupported level: {level}')
    self._check_transits(transits)

    transit_ganzhis = transits.ganzhis
    transit_tg = tuple(gz.tiangan for gz in transit_ganzhis)
    transit_dz = tuple(gz.dizhi for gz in transit_ganzhis)

    at_birth_tg = self._chart.bazi.four_tiangans
    at_birth_dz = self._chart.bazi.four_dizhis
    at_birth_ganzhis = self._chart.bazi.pillars
    definitions = self._chart.bazi.config.school.relation_definitions
    stars = self._chart.relationship_stars

    tg = tiangan_utils.TianganRelationDiscovery({})
    dz = dizhi_utils.DizhiRelationDiscovery({})
    gong_dz = dizhi_utils.DizhiRelationDiscovery({})
    if level & TransitAnalysis.Level.TRANSITS_ONLY:
      tg = tg.merge(tiangan_utils.discover(transit_tg))
      dz = dz.merge(
        dizhi_utils.discover(transit_dz, definitions=definitions),
      )
      gong_dz = gong_dz.merge(
        _project_gong(
          dizhi_utils.discover_ganzhis(
            transit_ganzhis,
            definitions=definitions,
            relations=DizhiRules.GONG_RELATIONS,
          ),
          lambda _: True,
        ),
      )
    if level & TransitAnalysis.Level.MUTUAL:
      tg = tg.merge(tiangan_utils.discover_mutual(at_birth_tg, transit_tg))
      dz = dz.merge(
        dizhi_utils.discover_mutual(at_birth_dz, transit_dz, definitions=definitions),
      )
      gong_dz = gong_dz.merge(
        _project_gong(
          dizhi_utils.discover_mutual_ganzhis(
            at_birth_ganzhis,
            transit_ganzhis,
            definitions=definitions,
            relations=DizhiRules.GONG_RELATIONS,
          ),
          lambda _: True,
        ),
      )
    dz = _with_gong(dz, gong_dz)

    return GanzhiData(
      tg.filter(lambda _, combo : stars.tiangan in combo),
      dz.filter(lambda _, combo : any(dz in combo for dz in stars.dizhi)),
    )
  
  def zhengyin(self, transits: TransitSet) -> GanzhiData[bool, bool]:
    '''
    检查流运的天干地支是否包含正印，即是否在走正印运。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (GanzhiData[bool, bool]) 天干、地支是否分别含正印。
    '''

    self._check_transits(transits)

    f = functools.partial(bazi_utils.shishen, self._chart.bazi.day_master)
    transit_ganzhis = transits.ganzhis

    return GanzhiData(
      any(f(gz.tiangan) is Shishen.正印 for gz in transit_ganzhis),
      any(f(gz.dizhi)   is Shishen.正印 for gz in transit_ganzhis),
    )
  
  def star(self, transits: TransitSet) -> GanzhiData[bool, bool]:
    '''
    检查流运的天干地支是否包含夫妻星/婚姻星。

    Args:
    - transits: (TransitSet) 参与分析的流运。

    Return: (GanzhiData[bool, bool]) 天干、地支是否分别含配偶星。
    '''

    self._check_transits(transits)

    stars = self._chart.relationship_stars
    transit_ganzhis = transits.ganzhis

    return GanzhiData(
      any(gz.tiangan is stars.tiangan for gz in transit_ganzhis),
      any(gz.dizhi   in stars.dizhi   for gz in transit_ganzhis),
    )



class RelationshipAnalyzer:
  '''组合 AtBirthAnalysis 与 TransitAnalysis 的亲密关系分析入口。'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @functools.cached_property
  def at_birth(self) -> AtBirthAnalysis:
    return AtBirthAnalysis(self._chart)

  @functools.cached_property
  def transits(self) -> TransitAnalysis:
    return TransitAnalysis(self._chart)
