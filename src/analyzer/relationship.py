# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import functools

from dataclasses import dataclass
from enum import Enum, IntFlag, auto, unique
from itertools import product
from typing import Final, TypedDict
from collections.abc import Callable, Iterable, Sequence

from ..common import frozendict
from ..data_types import GanzhiData
from ..defines import Tiangan, Dizhi, Ganzhi, Shishen, DizhiRelation
from ..rules import DizhiRules
from ..school import KeyStem, BaziSchool
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

def find_shensha(
  f: Callable[..., bool],
  *args: _ArgsType,
) -> Iterable[Dizhi]:
  '''A private/internal helper for finding Shensha (神煞): yield the Dizhi of every
  (key, dizhi) pair that the predicate `f` accepts.'''
  return (dz for keys, dizhis in args for key, dz in product(keys, dizhis) if f(key, dz))


@unique
class _KeySource(Enum):
  '''The key(s) that a Shensha is looked up by (查询神煞时所用的 key).'''
  YEAR_DIZHI        = auto() # By the year pillar's Dizhi only (只看年支).
  YEAR_OR_DAY_DIZHI = auto() # By the year or day pillar's Dizhi (看年支或日支).
  KEY_TIANGAN       = auto() # By a key Tiangan (查法锚干): day master by default, year tiangan per school. Sole consumer today: 红艳 (see `_hongyan_anchor`).


@dataclass(frozen=True)
class _ShenshaSpec:
  '''
  The spec of a Shensha: the predicate and the key source (神煞的规格：判断函数和查询 key).

  Note: the predicate's first-parameter type must match `key` (e.g. a `Tiangan`-keyed predicate
  pairs with `KEY_TIANGAN`). This contract is guarded by the runtime asserts in `shensha_utils`
  and the registry tests, not by the type system.
  '''
  predicate: Callable[..., bool]
  key:       _KeySource


'''The registry of the Shenshas that relationship analysis currently supports (亲密关系分析目前支持的神煞注册表).'''
_REGISTRY: Final[frozendict[str, _ShenshaSpec]] = frozendict({
  'taohua'  : _ShenshaSpec(shensha_utils.taohua,   _KeySource.YEAR_OR_DAY_DIZHI),
  'hongyan' : _ShenshaSpec(shensha_utils.hongyan,  _KeySource.KEY_TIANGAN),
  'hongluan': _ShenshaSpec(shensha_utils.hongluan, _KeySource.YEAR_DIZHI),
  'tianxi'  : _ShenshaSpec(shensha_utils.tianxi,   _KeySource.YEAR_DIZHI),
  'yima'    : _ShenshaSpec(shensha_utils.yima,     _KeySource.YEAR_OR_DAY_DIZHI),
  'huagai'  : _ShenshaSpec(shensha_utils.huagai,   _KeySource.YEAR_OR_DAY_DIZHI),
})


def _hongyan_anchor(bazi: Bazi) -> Tiangan:
  '''The anchor Tiangan a HONGYAN (红艳) lookup keys on (查法锚干, issue #69): the registry
  records the static default (`_KeySource.KEY_TIANGAN`, the 《三命通会》 reading), and the
  chart's school profile overrides it at evaluation time -- `KeyStem.YEAR_MASTER` keys on
  the year tiangan instead. 红艳查法的锚干：注册表记静态默认（查日干），评估期由盘的
  `BaziSchool.hongyan_key` 覆盖（可查年干）。'''
  key_stem: Final[KeyStem] = bazi.config.school.hongyan_key
  if key_stem is KeyStem.DAY_MASTER:
    return bazi.day_master
  elif key_stem is KeyStem.YEAR_MASTER:
    return bazi.year_pillar.tiangan
  else:
    # Invariant: every `KeyStem` member must be wired up above. Reaching here means we
    # added a member but forgot to wire it -- not something users can trigger.
    # `raise` instead of `assert` so the guard survives `python -O`.
    raise AssertionError(f'`KeyStem` not wired up in `_hongyan_anchor`: {key_stem}') # pragma: no cover # Unreachable invariant guard.


def _eval_at_birth(spec: _ShenshaSpec, bazi: Bazi) -> frozenset[Dizhi]:
  '''Evaluate a Shensha against the at-birth Bazi / 在原局上评估某个神煞。'''
  y_dz, m_dz, d_dz, h_dz = bazi.four_dizhis

  args: tuple[_ArgsType, ...]
  if spec.key is _KeySource.YEAR_DIZHI:
    args = (([y_dz], [m_dz, d_dz, h_dz]),)
  elif spec.key is _KeySource.YEAR_OR_DAY_DIZHI:
    args = (([y_dz], [m_dz, d_dz, h_dz]), ([d_dz], [y_dz, m_dz, h_dz]))
  elif spec.key is _KeySource.KEY_TIANGAN:
    args = (([_hongyan_anchor(bazi)], [y_dz, m_dz, d_dz, h_dz]),)
  else:
    # Invariant: every `_KeySource` member must be wired up above. Reaching here means we
    # added a member but forgot to update this evaluator -- not something users can trigger.
    # `raise` instead of `assert` so the guard survives `python -O`.
    raise AssertionError(f'`_KeySource` not wired up in `_eval_at_birth`: {spec.key}') # pragma: no cover # Unreachable invariant guard.

  return frozenset(find_shensha(spec.predicate, *args))


def _eval_transits(spec: _ShenshaSpec, bazi: Bazi, transit_dizhis: Iterable[Dizhi]) -> frozenset[Dizhi]:
  '''Evaluate a Shensha against the transit Dizhis / 在流运地支上评估某个神煞。'''
  first_args: _FirstArgType
  if spec.key is _KeySource.YEAR_DIZHI:
    first_args = [bazi.year_pillar.dizhi]
  elif spec.key is _KeySource.YEAR_OR_DAY_DIZHI:
    first_args = [bazi.year_pillar.dizhi, bazi.day_pillar.dizhi]
  elif spec.key is _KeySource.KEY_TIANGAN:
    first_args = [_hongyan_anchor(bazi)]
  else:
    # Invariant: every `_KeySource` member must be wired up above. Reaching here means we
    # added a member but forgot to update this evaluator -- not something users can trigger.
    # `raise` instead of `assert` so the guard survives `python -O`.
    raise AssertionError(f'`_KeySource` not wired up in `_eval_transits`: {spec.key}') # pragma: no cover # Unreachable invariant guard.

  return frozenset(find_shensha(spec.predicate, (first_args, transit_dizhis)))


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
  # The Taohua Dizhis   (桃花星所在地支)
  taohua:   frozenset[Dizhi]
  # The Hongyan Dizhis  (红艳星所在地支)
  hongyan:  frozenset[Dizhi]
  # The Hongluan Dizhis (红鸾星所在地支)
  hongluan: frozenset[Dizhi]
  # The Tianxi Dizhis   (天喜星所在地支)
  tianxi:   frozenset[Dizhi]
  # The Yima Dizhis     (驿马星所在地支)
  yima:     frozenset[Dizhi]
  # The Huagai Dizhis   (华盖星所在地支)
  huagai:   frozenset[Dizhi]


class AtBirthAnalysis:
  '''Analysis of Relationship at Birth / 出生时的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = chart

  @property
  def shensha(self) -> ShenshaAnalysis:
    bazi = self._chart.bazi
    return {
      'taohua' :  _eval_at_birth(_REGISTRY['taohua'],   bazi),
      'hongyan':  _eval_at_birth(_REGISTRY['hongyan'],  bazi),
      'hongluan': _eval_at_birth(_REGISTRY['hongluan'], bazi),
      'tianxi':   _eval_at_birth(_REGISTRY['tianxi'],   bazi),
      'yima'   :  _eval_at_birth(_REGISTRY['yima'],     bazi),
      'huagai' :  _eval_at_birth(_REGISTRY['huagai'],   bazi),
    }

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

    返回给定流运的亲密关系分析所含神煞（桃花、红艳、红鸾、天喜、驿马、华盖）。

    Args:
    - transits: (TransitSet) The selected transits to analyze. 参与分析的流运。

    Returns:
    - (ShenshaAnalysis) The Shensha analysis of the given transits.
    '''

    self._check_transits(transits)
    transit_ganzhis = transits.ganzhis
    transit_dizhis = tuple(gz.dizhi for gz in transit_ganzhis)

    bazi = self._chart.bazi
    return {
      'taohua' :  _eval_transits(_REGISTRY['taohua'],   bazi, transit_dizhis),
      'hongyan':  _eval_transits(_REGISTRY['hongyan'],  bazi, transit_dizhis),
      'hongluan': _eval_transits(_REGISTRY['hongluan'], bazi, transit_dizhis),
      'tianxi':   _eval_transits(_REGISTRY['tianxi'],   bazi, transit_dizhis),
      'yima'   :  _eval_transits(_REGISTRY['yima'],     bazi, transit_dizhis),
      'huagai' :  _eval_transits(_REGISTRY['huagai'],   bazi, transit_dizhis),
    }
  
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
