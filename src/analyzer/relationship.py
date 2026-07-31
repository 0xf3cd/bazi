# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import functools

from dataclasses import dataclass
from enum import Enum, IntFlag, auto, unique
from itertools import starmap, product, compress, chain
from typing import Final, TypedDict
from collections.abc import Callable, Iterable

from ..common import GanzhiData, frozendict
from ..defines import Tiangan, Dizhi, Shishen, DizhiRelation
from ..bazi import Bazi
from ..bazi_chart import BaziChart
from ..transits import TransitMoment, TransitOptions
from ..transit_chart import TransitChart
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
  '''An fp-styled helper private/internal function for finding Shensha (神煞).'''
  producted_args = list(chain(*(product(*a) for a in args)))
  results = starmap(f, producted_args)
  return (x[1] for x in compress(producted_args, results))


@unique
class _KeySource(Enum):
  '''The key(s) that a Shensha is looked up by (查询神煞时所用的 key).'''
  YEAR_DIZHI        = auto() # By the year pillar's Dizhi only (只看年支).
  YEAR_OR_DAY_DIZHI = auto() # By the year or day pillar's Dizhi (看年支或日支).
  DAY_MASTER        = auto() # By the day master (看日主).


@dataclass(frozen=True)
class _ShenshaSpec:
  '''
  The spec of a Shensha: the predicate and the key source (神煞的规格：判断函数和查询 key).

  Note: the predicate's first-parameter type must match `key` (e.g. a `Tiangan`-keyed predicate
  pairs with `DAY_MASTER`). This contract is guarded by the runtime asserts in `shensha_utils`
  and the registry tests, not by the type system.
  '''
  predicate: Callable[..., bool]
  key:       _KeySource


'''The registry of the Shenshas that relationship analysis currently supports (亲密关系分析目前支持的神煞注册表).'''
_REGISTRY: Final[frozendict[str, _ShenshaSpec]] = frozendict({
  'taohua'  : _ShenshaSpec(shensha_utils.taohua,   _KeySource.YEAR_OR_DAY_DIZHI),
  'hongyan' : _ShenshaSpec(shensha_utils.hongyan,  _KeySource.DAY_MASTER),
  'hongluan': _ShenshaSpec(shensha_utils.hongluan, _KeySource.YEAR_DIZHI),
  'tianxi'  : _ShenshaSpec(shensha_utils.tianxi,   _KeySource.YEAR_DIZHI),
  'yima'    : _ShenshaSpec(shensha_utils.yima,     _KeySource.YEAR_OR_DAY_DIZHI),
})


def _eval_at_birth(spec: _ShenshaSpec, bazi: Bazi) -> frozenset[Dizhi]:
  '''Evaluate a Shensha against the at-birth Bazi / 在原局上评估某个神煞。'''
  dm = bazi.day_master
  y_dz, m_dz, d_dz, h_dz = bazi.four_dizhis

  args: tuple[_ArgsType, ...]
  if spec.key is _KeySource.YEAR_DIZHI:
    args = (([y_dz], [m_dz, d_dz, h_dz]),)
  elif spec.key is _KeySource.YEAR_OR_DAY_DIZHI:
    args = (([y_dz], [m_dz, d_dz, h_dz]), ([d_dz], [y_dz, m_dz, h_dz]))
  elif spec.key is _KeySource.DAY_MASTER:
    args = (([dm], [y_dz, m_dz, d_dz, h_dz]),)
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
  elif spec.key is _KeySource.DAY_MASTER:
    first_args = [bazi.day_master]
  else:
    # Invariant: every `_KeySource` member must be wired up above. Reaching here means we
    # added a member but forgot to update this evaluator -- not something users can trigger.
    # `raise` instead of `assert` so the guard survives `python -O`.
    raise AssertionError(f'`_KeySource` not wired up in `_eval_transits`: {spec.key}') # pragma: no cover # Unreachable invariant guard.

  return frozenset(find_shensha(spec.predicate, (first_args, transit_dizhis)))



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


class AtBirthAnalysis:
  '''Analysis of Relationship at Birth / 出生时的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = copy.deepcopy(chart)

  @property
  def shensha(self) -> ShenshaAnalysis:
    bazi = self._chart.bazi
    return {
      'taohua' :  _eval_at_birth(_REGISTRY['taohua'],   bazi),
      'hongyan':  _eval_at_birth(_REGISTRY['hongyan'],  bazi),
      'hongluan': _eval_at_birth(_REGISTRY['hongluan'], bazi),
      'tianxi':   _eval_at_birth(_REGISTRY['tianxi'],   bazi),
      'yima'   :  _eval_at_birth(_REGISTRY['yima'],     bazi),
    }

  @property
  def day_master_relations(self) -> tiangan_utils.TianganRelationDiscovery:
    y_tg, m_tg, d_tg, h_tg = self._chart.bazi.four_tiangans
    return tiangan_utils.discover_mutual([d_tg], [y_tg, m_tg, h_tg])
  
  @property
  def house_relations(self) -> dizhi_utils.DizhiRelationDiscovery:
    '''Relations that the House of Relationship / 婚姻宫 has.'''
    # Unlike Tiangan relations, Dizhi relation combos can contain up to 3 Dizhis.
    # So use `discover` here instead of `discover_mutual`, otherwise some combos will be missed.
    #
    # With that being said, for AtBirth analysis, this problem doesn't exist.
    # Still use `discover` with `filter` though - it is expected to be equivalent to `discover_mutual([d_dz], [*other_three_dz])`
    return dizhi_utils.discover(self._chart.bazi.four_dizhis).filter(
      lambda _, combo : self._chart.house_of_relationship in combo
    )
  
  @property
  def star_relations(self) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''Relations that the Star(s) of Relationship / 配偶星 / 婚姻星 has.'''
    stars = self._chart.relationship_stars

    tg = tiangan_utils.discover(self._chart.bazi.four_tiangans).filter(lambda _, combo : stars.tiangan in combo)
    dz = dizhi_utils.discover(self._chart.bazi.four_dizhis).filter(lambda _, combo : any(dz in combo for dz in stars.dizhi))
    return GanzhiData(tg, dz)



class TransitAnalysis:
  '''Analysis of Relationship at Transits / 流年大运等的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = copy.deepcopy(chart)
    self._transit_chart: Final[TransitChart] = TransitChart(self._chart)

  def support(self, gz_year: int, options: TransitOptions) -> bool:
    '''
    Returns `True` if the given `gz_year` and `options` are both supported.
    '''
    return self._transit_chart.support(TransitMoment(gz_year), options)

  def shensha(self, gz_year: int, options: TransitOptions) -> ShenshaAnalysis:
    '''
    Return the relationship-related Shenshas of the given transits.

    返回给定流年大运等的亲密关系相关的神煞（桃花、红艳、红鸾、天喜、驿马）。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns:
    - (ShenshaAnalysis) The analysis of the relationship-related Shenshas of the given transits.
    '''

    assert self.support(gz_year, options)
    transit_ganzhis = self._transit_chart.ganzhis(TransitMoment(gz_year), options)
    transit_dizhis = tuple(gz.dizhi for gz in transit_ganzhis)

    bazi = self._chart.bazi
    return {
      'taohua' :  _eval_transits(_REGISTRY['taohua'],   bazi, transit_dizhis),
      'hongyan':  _eval_transits(_REGISTRY['hongyan'],  bazi, transit_dizhis),
      'hongluan': _eval_transits(_REGISTRY['hongluan'], bazi, transit_dizhis),
      'tianxi':   _eval_transits(_REGISTRY['tianxi'],   bazi, transit_dizhis),
      'yima'   :  _eval_transits(_REGISTRY['yima'],     bazi, transit_dizhis),
    }
  
  def day_master_relations(self, gz_year: int, options: TransitOptions) -> tiangan_utils.TianganRelationDiscovery:
    '''
    Return the Tiangan relations that the day master and other transit Tiangans form.
    
    返回日主和其他流运的天干之间的关系。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns: (tiangan_utils.TianganRelationDiscovery) The Tiangan relations that the day master and other transit Tiangans form.
    '''

    assert self.support(gz_year, options)
    transit_ganzhis = self._transit_chart.ganzhis(TransitMoment(gz_year), options)
    transit_tiangans = tuple(gz.tiangan for gz in transit_ganzhis)

    return tiangan_utils.discover_mutual([self._chart.bazi.day_master], transit_tiangans)

  def house_relations(self, gz_year: int, options: TransitOptions) -> dizhi_utils.DizhiRelationDiscovery:
    '''
    Return the Dizhi relations that the House of Relationship and other transit Dizhis form.

    返回配偶宫/婚姻宫和其他流运的地支之间的关系。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns: (dizhi_utils.DizhiRelationDiscovery) The Dizhi relations that the House of Relationship and other transit Dizhis form.
    '''

    assert self.support(gz_year, options)
    transit_ganzhis = self._transit_chart.ganzhis(TransitMoment(gz_year), options)
    transit_dizhis = [gz.dizhi for gz in transit_ganzhis]

    house = self._chart.house_of_relationship
    bazi = self._chart.bazi

    result = dizhi_utils.discover_mutual([house], transit_dizhis)

    # Unlike Tiangan relations, Dizhi relation combos can contain up to 3 Dizhis.
    # So `discover_mutual([house], transit_dizhis)` may contain incomplete results.
    #
    # Combos that contain 3 Dizhis are missing. So adding them manually.

    def __discover(rel: DizhiRelation) -> dizhi_utils.DizhiRelationDiscovery:
      def __filter(rel: DizhiRelation, combo: frozenset[Dizhi]) -> bool:
        if len(combo) != 3:
          return False
        for dz1 in transit_dizhis:
          for dz2 in [bazi.year_pillar.dizhi, bazi.month_pillar.dizhi, bazi.hour_pillar.dizhi]:
            if combo == frozenset([dz1, dz2, house]):
              return True
        return False

      return dizhi_utils.DizhiRelationDiscovery({
        rel : dizhi_utils.search(list(bazi.four_dizhis) + transit_dizhis, rel)
      }).filter(__filter)

    result = result.merge(__discover(DizhiRelation.三合))
    result = result.merge(__discover(DizhiRelation.三会))
    result = result.merge(__discover(DizhiRelation.刑))
    return result
  
  @unique
  class Level(IntFlag):
    # Analyze only transits. 只分析流运。
    TRANSITS_ONLY        = 1 << 0

    # Analyze the effects that transits and at-birth have on each other. 分析流运和原局互相的影响。
    MUTUAL               = 1 << 1

    # Analyze all effects, basically all of above. 分析所有影响。
    ALL                  = TRANSITS_ONLY | MUTUAL

  def star_relations(
    self, 
    gz_year: int, 
    options: TransitOptions, 
    *, level: Level = Level.ALL,
  ) -> GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]:
    '''
    Return the Tiangan and Dizhi relations that the Star(s) of Relationship and other transit Ganzhis form.

    返回配偶星/婚姻星和其他流运的干支之间的关系。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。
    - level: (Level) The level of the analysis. 返回分析的级别。

    Returns: (GanzhiData[tiangan_utils.TianganRelationDiscovery, dizhi_utils.DizhiRelationDiscovery]) The Tiangan and Dizhi relations that the Star(s) of Relationship and other transit Ganzhis form.
    '''

    assert level in TransitAnalysis.Level
    assert self.support(gz_year, options)

    transit_ganzhis = self._transit_chart.ganzhis(TransitMoment(gz_year), options)
    transit_tg = tuple(gz.tiangan for gz in transit_ganzhis)
    transit_dz = tuple(gz.dizhi for gz in transit_ganzhis)

    at_birth_tg = self._chart.bazi.four_tiangans
    at_birth_dz = self._chart.bazi.four_dizhis

    tg = tiangan_utils.TianganRelationDiscovery({})
    dz = dizhi_utils.DizhiRelationDiscovery({})
    if level & TransitAnalysis.Level.TRANSITS_ONLY:
      tg = tg.merge(tiangan_utils.discover(transit_tg))
      dz = dz.merge(dizhi_utils.discover(transit_dz))
    if level & TransitAnalysis.Level.MUTUAL:
      tg = tg.merge(tiangan_utils.discover_mutual(at_birth_tg, transit_tg))
      dz = dz.merge(dizhi_utils.discover_mutual(at_birth_dz, transit_dz))

    stars = self._chart.relationship_stars
    return GanzhiData(
      tg.filter(lambda _, combo : stars.tiangan in combo),
      dz.filter(lambda _, combo : any(dz in combo for dz in stars.dizhi)),
    )
  
  def zhengyin(self, gz_year: int, options: TransitOptions) -> GanzhiData[bool, bool]:
    '''
    Check if the transits' Tiangans and Dizhis contain Zhengyin (正印).

    检查流运的天干地支是否包含正印，即是否在走正印运。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns: (GanzhiData[bool, bool]) Whether the transits' Tiangans and Dizhis contain Zhengyin (正印).
    '''

    assert self.support(gz_year, options)
  
    f = functools.partial(bazi_utils.shishen, self._chart.bazi.day_master)
    transit_ganzhis = self._transit_chart.ganzhis(TransitMoment(gz_year), options)

    return GanzhiData(
      any(f(gz.tiangan) is Shishen.正印 for gz in transit_ganzhis),
      any(f(gz.dizhi)   is Shishen.正印 for gz in transit_ganzhis),
    )
  
  def star(self, gz_year: int, options: TransitOptions) -> GanzhiData[bool, bool]:
    '''
    Check if the transits' Tiangans and Dizhis contain the Star(s) of Relationship.

    检查流运的天干地支是否包含夫妻星/婚姻星。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns: (GanzhiData[bool, bool]) Whether the transits' Tiangans and Dizhis contain the Star(s) of Relationship.
    '''

    assert self.support(gz_year, options)

    stars = self._chart.relationship_stars
    transit_ganzhis = self._transit_chart.ganzhis(TransitMoment(gz_year), options)

    return GanzhiData(
      any(gz.tiangan is stars.tiangan for gz in transit_ganzhis),
      any(gz.dizhi   in stars.dizhi   for gz in transit_ganzhis),
    )



class RelationshipAnalyzer:
  '''A thin wrapper of `AtBirthAnalysis` and `TransitAnalysis`.'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = copy.deepcopy(chart)

  @property
  def at_birth(self) -> AtBirthAnalysis:
    return AtBirthAnalysis(self._chart)

  @property
  def transits(self) -> TransitAnalysis:
    return TransitAnalysis(self._chart)
