# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import functools

from dataclasses import dataclass
from enum import Enum, IntFlag, auto, unique
from itertools import product
from typing import Final, TypedDict, cast
from collections.abc import Callable, Iterable, Sequence

from ..common import frozendict
from ..data_types import GanzhiData
from ..defines import Tiangan, Dizhi, Ganzhi, Shishen, DizhiRelation
from ..rules import DizhiRules
from ..school import Anchor, BaziSchool
from ..bazi import Bazi
from ..bazi_chart import BaziChart
from ..transits import TransitSet
from ..utils import bazi_utils, shensha_utils, tiangan_utils, dizhi_utils


'''The type of the first argument passed to Shensha-finding functions: an iterable of Tiangan or Dizhi.'''
_FirstArgType = Iterable[Tiangan | Dizhi]

'''The type of the second argument passed to Shensha-finding functions: an iterable of Dizhi.'''
_SecondArgType = Iterable[Dizhi]

'''The type of the argument tuple that `find_shensha` accepts.'''
_ArgsType = tuple[_FirstArgType, _SecondArgType]

'''A resolver for a Shensha predicate's optional `definition` from the chart's school.'''
_DefinitionResolver = Callable[[BaziSchool], object]

def find_shensha(
  f: Callable[..., bool],
  *args: _ArgsType,
) -> Iterable[Dizhi]:
  '''A private/internal helper for finding Shensha (神煞): yield the Dizhi of every
  (key, dizhi) pair that the predicate `f` accepts.'''
  return (dz for keys, dizhis in args for key, dz in product(keys, dizhis) if f(key, dz))


@unique
class _AnchorKind(Enum):
  """Whether a Shensha keys on its anchor pillar's Tiangan or on its Dizhi
  (神煞以锚柱的天干还是地支为 key)."""
  TIANGAN = auto()
  DIZHI   = auto()


'''The pillar indices each `Anchor` selects, in four-pillar order (年、月、日、时).'''
_ANCHOR_PILLARS: Final[frozendict[Anchor, tuple[int, ...]]] = frozendict({
  Anchor.YEAR:         (0,),
  Anchor.DAY:          (2,),
  Anchor.YEAR_AND_DAY: (0, 2),
})

'''A resolver for a Shensha's `Anchor` from the chart's school, for the knobs schools disagree on.'''
_AnchorResolver = Callable[[BaziSchool], Anchor]


@dataclass(frozen=True)
class _ShenshaSpec:
  '''
  The spec of a Shensha: the predicate, the anchor it is looked up by, the display label,
  and an optional school-derived definition.
  神煞的规格：判断函数、查法锚、展示标签，以及可选的流派定义参数。

  `kind` says whether the key is the anchor pillar's Tiangan or its Dizhi; `anchor` says
  which pillar(s) supply it -- a fixed `Anchor` when no school disagrees, or a resolver
  reading the knob the school declares. Each entry must take both from that Shensha's own
  provenance; existing entries are not defaults for future ones (issue #167).
  `kind` 说 key 取锚柱的天干还是地支，`anchor` 说锚出自哪一柱——无流派分歧时是固定 `Anchor`，
  有分歧时是读盘上旋钮的解析函数。两者都须来自该神煞自身出处；既有条目不构成后续神煞的默认口径。

  Note: the predicate's first-parameter type must match `kind`. When `definition` is present, the
  predicate must accept its result through a keyword-only `definition` argument. Each predicate
  checks this contract at runtime; the registry's type does not express it.
  `label` is the Shensha's display name, published in `SHENSHA_LABELS` for the callers that
  render results; it is not part of the lookup.
  `label` 是该神煞的展示名，经 `SHENSHA_LABELS` 供渲染方使用，不参与查法。
  '''
  predicate:  Callable[..., bool]
  kind:       _AnchorKind
  anchor:     Anchor | _AnchorResolver
  label:      str
  definition: _DefinitionResolver | None = None


'''The registry of the Dizhi-valued Shenshas supported by relationship analysis
(亲密关系分析支持的地支结果神煞注册表).'''
_REGISTRY: Final[frozendict[str, _ShenshaSpec]] = frozendict({
  # 桃花 deliberately keeps a fixed anchor while 驿马、华盖、将星、劫煞、亡神 take a knob:
  # its day-branch reading in 《命理探源》 also requires a matching 纳音 and inspects only
  # the 月 and 时 branches, so offering a day anchor alone would state a rule no source does.
  # 桃花不设旋钮：《命理探源》的日支桃花另有纳音条件且只查月、时，只切锚会造出出处未言的规则。
  'taohua'   : _ShenshaSpec(shensha_utils.taohua,    _AnchorKind.DIZHI,   Anchor.YEAR_AND_DAY, '桃花'),
  'hongluan' : _ShenshaSpec(shensha_utils.hongluan,  _AnchorKind.DIZHI,   Anchor.YEAR, '红鸾'),
  'hongyan'  : _ShenshaSpec(shensha_utils.hongyan,   _AnchorKind.TIANGAN, lambda school: school.hongyan_anchor, '红艳'),
  'tianxi'   : _ShenshaSpec(shensha_utils.tianxi,    _AnchorKind.DIZHI,   Anchor.YEAR, '天喜'),
  'yima'     : _ShenshaSpec(shensha_utils.yima,      _AnchorKind.DIZHI,   lambda school: school.yima_anchor, '驿马'),
  'huagai'   : _ShenshaSpec(shensha_utils.huagai,    _AnchorKind.DIZHI,   lambda school: school.huagai_anchor, '华盖'),
  'yangren'  : _ShenshaSpec(
    shensha_utils.yangren,
    _AnchorKind.TIANGAN,
    Anchor.DAY,
    '羊刃',
    lambda school: school.yangren_def,
  ),
  'feiren'   : _ShenshaSpec(
    shensha_utils.feiren,
    _AnchorKind.TIANGAN,
    Anchor.DAY,
    '飞刃',
    lambda school: school.feiren_def,
  ),
  'tianyi'   : _ShenshaSpec(
    shensha_utils.tianyi,
    _AnchorKind.TIANGAN,
    lambda school: school.tianyi_anchor,
    '天乙贵人',
    lambda school: school.tianyi_def,
  ),
  'jiangxing': _ShenshaSpec(shensha_utils.jiangxing, _AnchorKind.DIZHI,   lambda school: school.jiangxing_anchor, '将星'),
  'zaisha'   : _ShenshaSpec(shensha_utils.zaisha,    _AnchorKind.DIZHI,   lambda school: school.zaisha_anchor, '灾煞'),
  'jiesha'   : _ShenshaSpec(shensha_utils.jiesha,    _AnchorKind.DIZHI,   lambda school: school.jiesha_anchor, '劫煞'),
  'wangshen' : _ShenshaSpec(shensha_utils.wangshen,  _AnchorKind.DIZHI,   lambda school: school.wangshen_anchor, '亡神'),
  'guchen'   : _ShenshaSpec(shensha_utils.guchen,    _AnchorKind.DIZHI,   Anchor.YEAR, '孤辰'),
  'guasu'    : _ShenshaSpec(shensha_utils.guasu,     _AnchorKind.DIZHI,   Anchor.YEAR, '寡宿'),
  'lushen'   : _ShenshaSpec(shensha_utils.lushen,    _AnchorKind.TIANGAN, Anchor.DAY, '禄神'),
  'jinyu'    : _ShenshaSpec(shensha_utils.jinyu,     _AnchorKind.TIANGAN, lambda school: school.jinyu_anchor, '金舆'),
})


'''The display label of every registered Shensha, in registry order -- the single roster
for callers that render Shensha results (`run_relationship_analyzer.py`), derived from the
registry so a new entry never needs a second list.
每个注册神煞的展示标签（按注册序）：渲染方的唯一名册，由注册表推导，新增条目不必再列一遍。'''
SHENSHA_LABELS: Final[frozendict[str, str]] = frozendict({
  name: spec.label for name, spec in _REGISTRY.items()
})


def _anchor_keys(spec: _ShenshaSpec, bazi: Bazi) -> tuple[tuple[int, Tiangan | Dizhi], ...]:
  '''The (pillar index, key) pairs a Shensha is looked up by on this chart, in
  four-pillar order. 该神煞在本盘上的查询 key 及其所属柱位（按年、月、日、时序）。'''
  anchor = spec.anchor if isinstance(spec.anchor, Anchor) else spec.anchor(bazi.config.school)
  pillars = bazi.pillars
  if spec.kind is _AnchorKind.TIANGAN:
    return tuple((index, pillars[index].tiangan) for index in _ANCHOR_PILLARS[anchor])
  return tuple((index, pillars[index].dizhi) for index in _ANCHOR_PILLARS[anchor])


def _shensha_predicate(spec: _ShenshaSpec, school: BaziSchool) -> Callable[..., bool]:
  '''Bind a Shensha predicate's school definition when it has one / 按盘绑定神煞定义参数。'''
  if spec.definition is None:
    return spec.predicate
  definition = spec.definition(school)
  return functools.partial(spec.predicate, definition=definition)


def _eval_at_birth(spec: _ShenshaSpec, bazi: Bazi) -> frozenset[Dizhi]:
  '''Evaluate a Shensha against the at-birth Bazi / 在原局上评估某个神煞。

  One rule serves every anchor: a Tiangan key inspects all four branches, a Dizhi key
  inspects the other three -- a branch never matches itself -- and a two-pillar anchor
  runs that rule once per anchored pillar.
  一条规则管所有锚：干锚查四支，支锚查其余三支（地支不自查），两柱锚就按柱各跑一遍。
  '''
  dizhis = bazi.four_dizhis
  args: tuple[_ArgsType, ...] = tuple(
    ((key,), dizhis if spec.kind is _AnchorKind.TIANGAN
             else tuple(dz for i, dz in enumerate(dizhis) if i != index))
    for index, key in _anchor_keys(spec, bazi)
  )
  return frozenset(find_shensha(_shensha_predicate(spec, bazi.config.school), *args))


def _eval_transits(spec: _ShenshaSpec, bazi: Bazi, transit_dizhis: Iterable[Dizhi]) -> frozenset[Dizhi]:
  '''Evaluate a Shensha against the transit Dizhis / 在流运地支上评估某个神煞。

  Transit branches are never the anchor's own pillar, so every key inspects all of them.
  流运地支不可能是锚柱自身，故每个 key 都查全部流运支。
  '''
  return frozenset(find_shensha(
    _shensha_predicate(spec, bazi.config.school),
    (tuple(key for _, key in _anchor_keys(spec, bazi)), transit_dizhis),
  ))


# The ONLY place this file reads the school profile for Dizhi relation discovery:
# every `dizhi_utils` batch query below goes through one of these wrappers,
# so "no bare calls in this file" is a grep-checkable invariant --
# a forgotten relation-definition argument at some call site would silently fall back to the
# hardcoded defaults (issue #69).
# 本文件唯一为地支关系查法读流派档案的地方：下文所有 `dizhi_utils` 批量查法一律走这些
# 薄包装——「本文件无裸调」是一条 grep 可验的不变量，
# 某个调用点忘传参会静默回落到硬编码默认（issue #69）。
def _dz_discover(school: BaziSchool, dizhis: Sequence[Dizhi]) -> dizhi_utils.DizhiRelationDiscovery:
  '''`dizhi_utils.discover` under the chart's school profile / 按盘的流派档案发现地支关系。'''
  return dizhi_utils.discover(dizhis, anhe_def=school.anhe_def, xing_def=school.xing_def)


def _dz_discover_mutual(school: BaziSchool, dizhis1: Sequence[Dizhi], dizhis2: Sequence[Dizhi]) -> dizhi_utils.DizhiRelationDiscovery:
  '''`dizhi_utils.discover_mutual` under the chart's school profile / 按盘的流派档案发现两组地支间的关系。'''
  return dizhi_utils.discover_mutual(dizhis1, dizhis2, anhe_def=school.anhe_def, xing_def=school.xing_def)


def _dz_discover_ganzhis(school: BaziSchool, ganzhis: Sequence[Ganzhi]) -> dizhi_utils.GanzhiRelationDiscovery:
  '''Position-preserving discovery under the chart's school / 按盘的流派档案保留柱位发现关系。'''
  return dizhi_utils.discover_ganzhis(
    ganzhis,
    anhe_def=school.anhe_def,
    xing_def=school.xing_def,
    gong_def=school.gong_def,
  )


def _dz_discover_mutual_ganzhis(
  school: BaziSchool,
  ganzhis1: Sequence[Ganzhi],
  ganzhis2: Sequence[Ganzhi],
) -> dizhi_utils.GanzhiRelationDiscovery:
  '''Position-preserving mutual discovery under the chart's school / 按盘的流派档案保留柱位发现两组关系。'''
  return dizhi_utils.discover_mutual_ganzhis(
    ganzhis1,
    ganzhis2,
    anhe_def=school.anhe_def,
    xing_def=school.xing_def,
    gong_def=school.gong_def,
  )


_DAY_PILLAR_INDEX: Final[int] = 2


def _project_gong(
  discovery: dizhi_utils.GanzhiRelationDiscovery,
  predicate: Callable[[dizhi_utils.GanzhiRelationCombo], bool],
) -> dizhi_utils.DizhiRelationDiscovery:
  '''Filter concrete Gong participants before discarding their positions / 先按具体参与柱过滤拱局，再投影地支。'''
  return dizhi_utils.GanzhiRelationDiscovery({
    relation : filtered
    for relation in DizhiRules.GONG_RELATIONS
    if len(filtered := tuple(combo for combo in discovery.get(relation, ()) if predicate(combo))) > 0
  }).to_dizhi_discovery()


def _with_gong(
  existing: dizhi_utils.DizhiRelationDiscovery,
  gong: dizhi_utils.DizhiRelationDiscovery,
) -> dizhi_utils.DizhiRelationDiscovery:
  '''Add disjoint Gong keys without reordering existing relation combos / 加入拱局键且不重排既有组合。'''
  assert set(existing).isdisjoint(gong)
  return dizhi_utils.DizhiRelationDiscovery({**existing, **gong})


class ShenshaAnalysis(TypedDict):
  # The Taohua Dizhis    (桃花星所在地支)
  taohua:    frozenset[Dizhi]
  # The Hongyan Dizhis   (红艳星所在地支)
  hongyan:   frozenset[Dizhi]
  # The Hongluan Dizhis  (红鸾星所在地支)
  hongluan:  frozenset[Dizhi]
  # The Tianxi Dizhis    (天喜星所在地支)
  tianxi:    frozenset[Dizhi]
  # The Yima Dizhis      (驿马星所在地支)
  yima:      frozenset[Dizhi]
  # The Huagai Dizhis    (华盖星所在地支)
  huagai:    frozenset[Dizhi]
  # The Yangren Dizhis   (羊刃所在地支)
  yangren:   frozenset[Dizhi]
  # The Feiren Dizhis    (飞刃所在地支)
  feiren:    frozenset[Dizhi]
  # The Tianyi Dizhis    (天乙贵人所在地支)
  tianyi:    frozenset[Dizhi]
  # The Jiangxing Dizhis (将星所在地支)
  jiangxing: frozenset[Dizhi]
  # The Zaisha Dizhis    (灾煞所在地支)
  zaisha:    frozenset[Dizhi]
  # The Jiesha Dizhis    (劫煞所在地支)
  jiesha:    frozenset[Dizhi]
  # The Wangshen Dizhis  (亡神所在地支)
  wangshen:  frozenset[Dizhi]
  # The Guchen Dizhis    (孤辰所在地支)
  guchen:    frozenset[Dizhi]
  # The Guasu Dizhis     (寡宿所在地支)
  guasu:     frozenset[Dizhi]
  # The Lushen Dizhis    (禄神所在地支)
  lushen:    frozenset[Dizhi]
  # The Jinyu Dizhis     (金舆所在地支)
  jinyu:     frozenset[Dizhi]


class AtBirthShenshaAnalysis(ShenshaAnalysis):
  # The Kuigang day pillar (魁罡日柱)
  kuigang: Ganzhi | None
  # The Tianshe day pillar (天赦日柱)
  tianshe: Ganzhi | None


class AtBirthAnalysis:
  '''Analysis of Relationship at Birth / 出生时的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @property
  def shensha(self) -> AtBirthShenshaAnalysis:
    bazi = self._chart.bazi
    # The registry is the roster: every entry lands under its own key, followed by the two
    # whole-pillar Shenshas that are not in it (they answer with a Ganzhi, not a Dizhi set).
    # A comprehension cannot type-check as a `TypedDict`, so the key set is pinned by
    # `test_analyses_are_built_from_the_registry` instead of by mypy.
    # 注册表就是名册：每个条目落在自己的键下，其后是不在表内的两个整柱神煞（它们的答案是干支，
    # 不是地支集合）。推导式无法按 `TypedDict` 类型检查，键集改由测试钉住。
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
    '''Relations that the House of Relationship / 婚姻宫 has. Gong is evaluated under the
    chart's school and retained only when the concrete day-pillar occurrence participates.
    拱局按本盘流派判断，并只保留日柱这一具体出现真正参与的组合。'''
    # For non-Gong relations, keep the complete-discovery path used for three-Dizhi combos;
    # at birth it is equivalent to mutual discovery between the day branch and the other three.
    # A value-only filter would retain a Gong pair formed by another occurrence when that
    # pillar repeats the day branch, so filter concrete participants before projection.
    bazi: Final[Bazi] = self._chart.bazi
    school: Final[BaziSchool] = bazi.config.school
    existing = _dz_discover(school, bazi.four_dizhis).filter(
      lambda _, combo : self._chart.house_of_relationship in combo
    )
    gong = _project_gong(
      _dz_discover_ganzhis(school, bazi.pillars),
      lambda combo : any(occurrence.index == _DAY_PILLAR_INDEX for occurrence in combo),
    )
    return _with_gong(existing, gong)
  
  @property
  def star_relations(self) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''Relations that the Star(s) of Relationship / 配偶星 / 婚姻星 has. Gong is evaluated
    under the chart's school and retained only when a real participant is a relationship-star
    branch. 拱局按本盘流派判断，并只保留实支参与者含配偶星地支的组合。'''
    stars = self._chart.relationship_stars
    bazi: Final[Bazi] = self._chart.bazi
    school: Final[BaziSchool] = bazi.config.school

    tg = tiangan_utils.discover(bazi.four_tiangans).filter(lambda _, combo : stars.tiangan in combo)
    existing = _dz_discover(school, bazi.four_dizhis).filter(lambda _, combo : any(dz in combo for dz in stars.dizhi))
    gong = _project_gong(
      _dz_discover_ganzhis(school, bazi.pillars),
      lambda combo : any(occurrence.ganzhi.dizhi in stars.dizhi for occurrence in combo),
    )
    return GanzhiData(tg, _with_gong(existing, gong))



class TransitAnalysis:
  '''Analysis of Relationship at Transits / 流运的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @staticmethod
  def _check_transits(transits: object) -> None:
    if not isinstance(transits, TransitSet):
      raise TypeError(f'Expected TransitSet, got {type(transits)}')

  def shensha(self, transits: TransitSet) -> ShenshaAnalysis:
    '''
    Return the Shenshas exposed by relationship analysis for the given transits.

    返回给定流运的亲密关系神煞分析。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns:
    - (ShenshaAnalysis) The Shensha analysis of the given transits.
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = tuple(gz.dizhi for gz in transit_ganzhis)

    bazi = self._chart.bazi
    # Same roster as at birth, evaluated against the transit branches; see the note there.
    # 与原局同一份名册，只是查在流运地支上；说明见原局那处。
    return cast(ShenshaAnalysis, {
      name: _eval_transits(spec, bazi, transit_dizhis) for name, spec in _REGISTRY.items()
    })
  
  def day_master_relations(self, transits: TransitSet) -> tiangan_utils.TianganRelationDiscovery:
    '''
    Return the Tiangan relations that the day master and other transit Tiangans form.
    
    返回日主和其他流运的天干之间的关系。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (tiangan_utils.TianganRelationDiscovery) The Tiangan relations that the day master and other transit Tiangans form.
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_tiangans = tuple(gz.tiangan for gz in transit_ganzhis)

    return tiangan_utils.discover_mutual([self._chart.bazi.day_master], transit_tiangans)

  def house_relations(self, transits: TransitSet) -> dizhi_utils.DizhiRelationDiscovery:
    '''
    Return the Dizhi relations that the House of Relationship and other transit Dizhis form.

    返回配偶宫/婚姻宫和其他流运的地支之间的关系。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (dizhi_utils.DizhiRelationDiscovery) The Dizhi relations that the House of Relationship and other transit Dizhis form.

    Note:
    - Gong is evaluated under the chart's school and retained only when the concrete day-pillar
      occurrence participates. 拱局按本盘流派判断，并只保留日柱这一具体出现参与的组合。
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = [gz.dizhi for gz in transit_ganzhis]

    house = self._chart.house_of_relationship
    bazi = self._chart.bazi
    school: Final[BaziSchool] = bazi.config.school

    # A three-Dizhi combo can span the house, another natal Dizhi, and a transit Dizhi.
    # Discover across the complete natal side first, then retain house combos with a transit
    # witness. `discover_mutual` is value-based, so a repeated house value alone does not
    # witness a multi-Dizhi combo; a singleton self-刑 does.
    def __is_house_transit_relation(_: DizhiRelation, combo: frozenset[Dizhi]) -> bool:
      if house not in combo:
        return False
      if len(combo) == 1:
        return house in transit_dizhis
      return not (combo - {house}).isdisjoint(transit_dizhis)

    existing = _dz_discover_mutual(school, bazi.four_dizhis, transit_dizhis).filter(__is_house_transit_relation)
    gong = _project_gong(
      _dz_discover_mutual_ganzhis(school, bazi.pillars, transit_ganzhis),
      lambda combo : any(occurrence.index == _DAY_PILLAR_INDEX for occurrence in combo),
    )
    return _with_gong(existing, gong)
  
  @unique
  class Level(IntFlag):
    # Analyze only transits. 只分析流运。
    TRANSITS_ONLY        = 1 << 0

    # Analyze the effects that transits and at-birth have on each other. 分析流运和原局互相的影响。
    MUTUAL               = 1 << 1

    # Analyze all effects, basically all of above. 分析所有影响。
    ALL                  = TRANSITS_ONLY | MUTUAL

  '''The constant level space for the `level` gate. `level` 闸的常量级别空间。'''
  _ALL_LEVELS: Final[tuple[Level, ...]] = (Level.TRANSITS_ONLY, Level.MUTUAL, Level.ALL)

  def star_relations(
    self,
    transits: TransitSet,
    *, level: Level = Level.ALL,
  ) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''
    Return the Tiangan and Dizhi relations that the Star(s) of Relationship and other transit Ganzhis form.

    返回配偶星/婚姻星和其他流运的干支之间的关系。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。
    - level: (Level) The level of the analysis. 返回分析的级别。

    Returns: (GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]) The Tiangan and Dizhi relations that the Star(s) of Relationship and other transit Ganzhis form.

    Note:
    - Gong is evaluated under the chart's school and retained only when a real participant is a
      relationship-star branch. With `TRANSITS_ONLY`, adjacency follows the present entries in
      `transits.ganzhis`; narrowing a `TransitSet` can therefore change Gong adjacency.
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
    school: Final[BaziSchool] = self._chart.bazi.config.school
    stars = self._chart.relationship_stars

    tg = tiangan_utils.TianganRelationDiscovery({})
    dz = dizhi_utils.DizhiRelationDiscovery({})
    gong_dz = dizhi_utils.DizhiRelationDiscovery({})
    if level & TransitAnalysis.Level.TRANSITS_ONLY:
      tg = tg.merge(tiangan_utils.discover(transit_tg))
      dz = dz.merge(_dz_discover(school, transit_dz))
      gong_dz = gong_dz.merge(_project_gong(
        _dz_discover_ganzhis(school, transit_ganzhis),
        lambda _: True,
      ))
    if level & TransitAnalysis.Level.MUTUAL:
      tg = tg.merge(tiangan_utils.discover_mutual(at_birth_tg, transit_tg))
      dz = dz.merge(_dz_discover_mutual(school, at_birth_dz, transit_dz))
      gong_dz = gong_dz.merge(_project_gong(
        _dz_discover_mutual_ganzhis(school, at_birth_ganzhis, transit_ganzhis),
        lambda _: True,
      ))
    dz = _with_gong(dz, gong_dz)

    return GanzhiData(
      tg.filter(lambda _, combo : stars.tiangan in combo),
      dz.filter(lambda _, combo : any(dz in combo for dz in stars.dizhi)),
    )
  
  def zhengyin(self, transits: TransitSet) -> GanzhiData[bool, bool]:
    '''
    Check if the transits' Tiangans and Dizhis contain Zhengyin (正印).

    检查流运的天干地支是否包含正印，即是否在走正印运。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (GanzhiData[bool, bool]) Whether the transits' Tiangans and Dizhis contain Zhengyin (正印).
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
    Check if the transits' Tiangans and Dizhis contain the Star(s) of Relationship.

    检查流运的天干地支是否包含夫妻星/婚姻星。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns: (GanzhiData[bool, bool]) Whether the transits' Tiangans and Dizhis contain the Star(s) of Relationship.
    '''

    self._check_transits(transits)

    stars = self._chart.relationship_stars
    transit_ganzhis = transits.ganzhis

    return GanzhiData(
      any(gz.tiangan is stars.tiangan for gz in transit_ganzhis),
      any(gz.dizhi   in stars.dizhi   for gz in transit_ganzhis),
    )



class RelationshipAnalyzer:
  '''A thin wrapper of `AtBirthAnalysis` and `TransitAnalysis`.'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @functools.cached_property
  def at_birth(self) -> AtBirthAnalysis:
    return AtBirthAnalysis(self._chart)

  @functools.cached_property
  def transits(self) -> TransitAnalysis:
    return TransitAnalysis(self._chart)
