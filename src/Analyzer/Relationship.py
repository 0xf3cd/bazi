# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from itertools import starmap, product, compress, chain
from typing import Final, TypedDict, Callable, Union, Iterable

from ..Defines import Tiangan, Dizhi
from ..BaziChart import BaziChart
from ..Utils import ShenshaUtils, TianganUtils, DizhiUtils
from ..Discoverer.GanzhiDiscoverer import GanzhiDiscoverer


class RelationshipAnalysis(TypedDict):
  # The Taohua Dizhis   (桃花星所在地支)
  taohua:   frozenset[Dizhi]
  # The Hongyan Dizhis  (红艳星所在地支)
  hongyan:  frozenset[Dizhi]
  # The Hongluan Dizhis (红鸾星所在地支)
  hongluan: frozenset[Dizhi]
  # The Tianxi Dizhis   (天喜星所在地支)
  tianxi:   frozenset[Dizhi]

  # The relations that the day master and other Tiangans form.
  # 日主与其他天干形成的关系（合、冲等）
  day_master_relations: TianganUtils.TianganRelationDiscovery

  # The relations that the house of relationship and other Dizhis form.
  # 夫妻宫与其他地支形成的关系（合、冲等）
  house_relations: DizhiUtils.DizhiRelationDiscovery

  # The relations that relationship stars and other Tiangans form.
  # 夫妻星与其他天干形成的关系（合、冲等）
  tg_star_relations: TianganUtils.TianganRelationDiscovery

  # The relations that relationship stars and other Dizhis form.
  # 夫妻星与其他地支形成的关系（合、冲等）
  dz_star_relations: DizhiUtils.DizhiRelationDiscovery


class RelationshipAnalyzer:
  _FirstArgType = Iterable[Union[Tiangan, Dizhi]]
  _SecondArgType = Iterable[Dizhi]
  _ArgsType = tuple[_FirstArgType, _SecondArgType]
  @staticmethod
  def __find_shensha(
    f: Callable[..., bool],
    *args: _ArgsType,
  ) -> Iterable[Dizhi]:
    '''An fp-styled helper private method for finding Shensha (神煞).'''
    producted_args = list(chain(*map(lambda a : product(*a), args)))
    results = starmap(f, producted_args)
    return map(lambda x : x[1], compress(producted_args, results))
  
  def __init__(self, bazi_chart: BaziChart) -> None:
    self._bazi_chart: Final[BaziChart] = copy.deepcopy(bazi_chart)
    self._ganzhi_discoverer: Final[GanzhiDiscoverer] = GanzhiDiscoverer(self._bazi_chart)

  @property
  def at_birth(self) -> RelationshipAnalysis:
    y_tg, m_tg, d_tg, h_tg = self._bazi_chart.bazi.four_tiangans
    y_dz, m_dz, d_dz, h_dz = self._bazi_chart.bazi.four_dizhis
    
    stars = self._bazi_chart.relationship_stars
    at_birth_discovery = self._ganzhi_discoverer.at_birth

    return {
      'taohua' :  frozenset(self.__find_shensha(ShenshaUtils.taohua,   ([y_dz],  [m_dz, d_dz, h_dz]), 
                                                                       ([d_dz],  [y_dz, m_dz, h_dz]))),
      'hongyan':  frozenset(self.__find_shensha(ShenshaUtils.hongyan,  ([d_tg],  [y_dz, m_dz, d_dz, h_dz]))),
      'hongluan': frozenset(self.__find_shensha(ShenshaUtils.hongluan, ([y_dz],  [m_dz, d_dz, h_dz]))),
      'tianxi':   frozenset(self.__find_shensha(ShenshaUtils.tianxi,   ([y_dz],  [m_dz, d_dz, h_dz]))),

      'day_master_relations': TianganUtils.discover_mutual([d_tg], [y_tg, m_tg, h_tg]),
      'house_relations': DizhiUtils.discover_mutual([d_dz], [y_dz, m_dz, h_dz]),

      'tg_star_relations': at_birth_discovery.tiangan.filter(lambda _, combo : stars.tiangan in combo),
      'dz_star_relations': at_birth_discovery.dizhi.filter(lambda _, combo : any(dz in combo for dz in stars.dizhi)),
    }
