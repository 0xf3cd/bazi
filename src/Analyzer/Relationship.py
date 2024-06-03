# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import functools

from enum import IntFlag, unique
from itertools import starmap, product, compress, chain
from typing import Final, TypedDict, Callable, Union, Iterable

from ..Common import GanzhiData
from ..Defines import Tiangan, Dizhi, Shishen, DizhiRelation
from ..BaziChart import BaziChart
from ..Transits import TransitOptions, TransitDatabase
from ..Utils import BaziUtils, ShenshaUtils, TianganUtils, DizhiUtils


_FirstArgType = Iterable[Union[Tiangan, Dizhi]]
_SecondArgType = Iterable[Dizhi]
_ArgsType = tuple[_FirstArgType, _SecondArgType]

def find_shensha(
  f: Callable[..., bool],
  *args: _ArgsType,
) -> Iterable[Dizhi]:
  '''An fp-styled helper private/internal function for finding Shensha (神煞).'''
  producted_args = list(chain(*map(lambda a : product(*a), args)))
  results = starmap(f, producted_args)
  return map(lambda x : x[1], compress(producted_args, results))



class ShenshaAnalysis(TypedDict):
  # The Taohua Dizhis   (桃花星所在地支)
  taohua:   frozenset[Dizhi]
  # The Hongyan Dizhis  (红艳星所在地支)
  hongyan:  frozenset[Dizhi]
  # The Hongluan Dizhis (红鸾星所在地支)
  hongluan: frozenset[Dizhi]
  # The Tianxi Dizhis   (天喜星所在地支)
  tianxi:   frozenset[Dizhi]


class AtBirthAnalysis:
  '''Analysis of Relationship at Birth / 出生时的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = copy.deepcopy(chart)

  @property
  def shensha(self) -> ShenshaAnalysis:
    dm = self._chart.bazi.day_master
    y_dz, m_dz, d_dz, h_dz = self._chart.bazi.four_dizhis
    return {
      'taohua' :  frozenset(find_shensha(ShenshaUtils.taohua,   ([y_dz],  [m_dz, d_dz, h_dz]), 
                                                                ([d_dz],  [y_dz, m_dz, h_dz]))),
      'hongyan':  frozenset(find_shensha(ShenshaUtils.hongyan,  ([dm],    [y_dz, m_dz, d_dz, h_dz]))),
      'hongluan': frozenset(find_shensha(ShenshaUtils.hongluan, ([y_dz],  [m_dz, d_dz, h_dz]))),
      'tianxi':   frozenset(find_shensha(ShenshaUtils.tianxi,   ([y_dz],  [m_dz, d_dz, h_dz]))),
    }

  @property
  def day_master_relations(self) -> TianganUtils.TianganRelationDiscovery:
    y_tg, m_tg, d_tg, h_tg = self._chart.bazi.four_tiangans
    return TianganUtils.discover_mutual([d_tg], [y_tg, m_tg, h_tg])
  
  @property
  def house_relations(self) -> DizhiUtils.DizhiRelationDiscovery:
    '''Relations that the House of Relationship / 婚姻宫 has.'''
    # Unlike Tiangan relations, Dizhi relation combos can contain up to 3 Dizhis.
    # So use `discover` here instead of `discover_mutual`, otherwise some combos will be missed.
    #
    # With that being said, for AtBirth analysis, this problem doesn't exist.
    # Still use `discover` with `filter` though - it is expected to be equivalent to `discover_mutual([d_dz], [*other_three_dz])`
    return DizhiUtils.discover(self._chart.bazi.four_dizhis).filter(
      lambda _, combo : self._chart.house_of_relationship in combo
    )
  
  @property
  def star_relations(self) -> GanzhiData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]:
    '''Relations that the Star(s) of Relationship / 配偶星 / 婚姻星 has.'''
    stars = self._chart.relationship_stars

    tg = TianganUtils.discover(self._chart.bazi.four_tiangans).filter(lambda _, combo : stars.tiangan in combo)
    dz = DizhiUtils.discover(self._chart.bazi.four_dizhis).filter(lambda _, combo : any(dz in combo for dz in stars.dizhi))
    return GanzhiData(tg, dz)



class TransitAnalysis:
  '''Analysis of Relationship at Transits / 流年大运等的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = copy.deepcopy(chart)
    self._transit_db: Final[TransitDatabase] = TransitDatabase(chart)

  def support(self, gz_year: int, options: TransitOptions) -> bool:
    '''
    Returns `True` if the given `gz_year` and `options` are both supported.
    '''
    return self._transit_db.support(gz_year, options)

  def shensha(self, gz_year: int, options: TransitOptions) -> ShenshaAnalysis:
    '''
    Return the relationship-related Shenshas of the given transits.

    返回给定流年大运等的亲密关系相关的神煞（桃花、红艳、红鸾、天喜）。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns:
    - (ShenshaAnalysis) The analysis of the relationship-related Shenshas of the given transits.
    '''

    assert self.support(gz_year, options)
    transit_ganzhis = self._transit_db.ganzhis(gz_year, options)
    transit_dizhis = tuple(gz.dizhi for gz in transit_ganzhis)

    dm = self._chart.bazi.day_master
    y_dz = self._chart.bazi.year_pillar.dizhi
    d_dz = self._chart.bazi.day_pillar.dizhi

    return {
      'taohua' :  frozenset(find_shensha(ShenshaUtils.taohua,   ([y_dz, d_dz], transit_dizhis))),
      'hongyan':  frozenset(find_shensha(ShenshaUtils.hongyan,  ([dm],         transit_dizhis))),
      'hongluan': frozenset(find_shensha(ShenshaUtils.hongluan, ([y_dz],       transit_dizhis))),
      'tianxi':   frozenset(find_shensha(ShenshaUtils.tianxi,   ([y_dz],       transit_dizhis))),
    }
  
  def day_master_relations(self, gz_year: int, options: TransitOptions) -> TianganUtils.TianganRelationDiscovery:
    '''
    Return the Tiangan relations that the day master and other transit Tiangans form.
    
    返回日主和其他流运的天干之间的关系。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns: (TianganUtils.TianganRelationDiscovery) The Tiangan relations that the day master and other transit Tiangans form.
    '''

    assert self.support(gz_year, options)
    transit_ganzhis = self._transit_db.ganzhis(gz_year, options)
    transit_tiangans = tuple(gz.tiangan for gz in transit_ganzhis)

    return TianganUtils.discover_mutual([self._chart.bazi.day_master], transit_tiangans)

  def house_relations(self, gz_year: int, options: TransitOptions) -> DizhiUtils.DizhiRelationDiscovery:
    '''
    Return the Dizhi relations that the House of Relationship and other transit Dizhis form.

    返回配偶宫/婚姻宫和其他流运的地支之间的关系。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。

    Returns: (DizhiUtils.DizhiRelationDiscovery) The Dizhi relations that the House of Relationship and other transit Dizhis form.
    '''

    assert self.support(gz_year, options)
    transit_ganzhis = self._transit_db.ganzhis(gz_year, options)
    transit_dizhis = [gz.dizhi for gz in transit_ganzhis]

    house = self._chart.house_of_relationship
    bazi = self._chart.bazi

    result = DizhiUtils.discover_mutual([house], transit_dizhis)

    # Unlike Tiangan relations, Dizhi relation combos can contain up to 3 Dizhis.
    # So `discover_mutual([house], transit_dizhis)` may contain incomplete results.
    #
    # Combos that contain 3 Dizhis are missing. So adding them manually.

    def __discover(rel: DizhiRelation):
      def __filter(rel: DizhiRelation, combo: frozenset[Dizhi]):
        if len(combo) != 3:
          return False
        for dz1 in transit_dizhis:
          for dz2 in [bazi.year_pillar.dizhi, bazi.month_pillar.dizhi, bazi.hour_pillar.dizhi]:
            if combo == frozenset([dz1, dz2, house]):
              return True
        return False

      return DizhiUtils.DizhiRelationDiscovery({
        rel : DizhiUtils.search(list(bazi.four_dizhis) + transit_dizhis, rel)
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
  ) -> GanzhiData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]:
    '''
    Return the Tiangan and Dizhi relations that the House of Relationship and other Ganzhis form.

    返回配偶宫/婚姻宫和其他干支之间的关系。

    Args:
    - gz_year: (int) The year of the transits. 流年/小运/大运等的年份。
    - options: (TransitOptions) Specifying which transits to pick. 指定参与分析的流年/小运/大运等。
    - level: (Level) The level of the analysis. 返回分析的级别。

    Returns: (GanzhiData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]) The Tiangan and Dizhi relations that the House of Relationship and other transit Ganzhis form.
    '''

    assert level in TransitAnalysis.Level
    assert self.support(gz_year, options)

    transit_ganzhis = self._transit_db.ganzhis(gz_year, options)
    transit_tg = tuple(gz.tiangan for gz in transit_ganzhis)
    transit_dz = tuple(gz.dizhi for gz in transit_ganzhis)

    at_birth_tg = self._chart.bazi.four_tiangans
    at_birth_dz = self._chart.bazi.four_dizhis

    tg = TianganUtils.TianganRelationDiscovery({})
    dz = DizhiUtils.DizhiRelationDiscovery({})
    if level & TransitAnalysis.Level.TRANSITS_ONLY:
      tg = tg.merge(TianganUtils.discover(transit_tg))
      dz = dz.merge(DizhiUtils.discover(transit_dz))
    if level & TransitAnalysis.Level.MUTUAL:
      tg = tg.merge(TianganUtils.discover_mutual(at_birth_tg, transit_tg))
      dz = dz.merge(DizhiUtils.discover_mutual(at_birth_dz, transit_dz))

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
  
    f = functools.partial(BaziUtils.shishen, self._chart.bazi.day_master)
    transit_ganzhis = self._transit_db.ganzhis(gz_year, options)

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

    Returns: (bool) Whether the transits' Tiangans and Dizhis contain the Star(s) of Relationship.
    '''

    assert self.support(gz_year, options)

    stars = self._chart.relationship_stars
    transit_ganzhis = self._transit_db.ganzhis(gz_year, options)

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
