# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from itertools import starmap, product, compress, chain
from typing import Final, TypedDict, Callable, Union, Iterable

from ..Common import GanzhiData
from ..Defines import Tiangan, Dizhi
from ..BaziChart import BaziChart, TransitOptions, TransitDatabase
from ..Utils import ShenshaUtils, TianganUtils, DizhiUtils
from ..Discoverer.GanzhiDiscoverer import GanzhiDiscoverer


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
    self._ganzhi_discoverer: Final[GanzhiDiscoverer] = GanzhiDiscoverer(chart)

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
    y_dz, m_dz, d_dz, h_dz = self._chart.bazi.four_dizhis
    return DizhiUtils.discover_mutual([d_dz], [y_dz, m_dz, h_dz])
  
  @property
  def star_relations(self) -> GanzhiData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]:
    '''Relations that the Star of Relationship / 配偶星 / 婚姻星 has.'''
    stars = self._chart.relationship_stars
    at_birth_discovery = self._ganzhi_discoverer.at_birth

    tg = at_birth_discovery.tiangan.filter(lambda _, combo : stars.tiangan in combo)
    dz = at_birth_discovery.dizhi.filter(lambda _, combo : any(dz in combo for dz in stars.dizhi))
    return GanzhiData(tg, dz)



class TransitAnalysis:
  '''Analysis of Relationship at Transits / 流年大运等的亲密关系分析'''
  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = copy.deepcopy(chart)
    self._transit_db: Final[TransitDatabase] = chart.transit_db
    self._ganzhi_discoverer: Final[GanzhiDiscoverer] = GanzhiDiscoverer(chart)

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

    assert self._transit_db.support(gz_year, options)
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
