# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from itertools import starmap, product, compress, chain

from typing import Final, TypedDict, Callable, Union, Iterable, TypeVar, overload

from ..Defines import Tiangan, Dizhi, TianganRelation, DizhiRelation
from ..BaziChart import BaziChart
from ..Utils import ShenshaUtils, TianganUtils, DizhiUtils


class RelationshipAnalysis(TypedDict):
  # The Taohua Dizhis   (桃花星所在地支)
  taohua:   frozenset[Dizhi]
  # The Hongyan Dizhis  (红艳星所在地支)
  hongyan:  frozenset[Dizhi]
  # The Hongluan Dizhis (红鸾星所在地支)
  hongluan: frozenset[Dizhi]
  # The Tianxi Dizhis   (天喜星所在地支)
  tianxi:   frozenset[Dizhi]

  # The relations that the house of relationship and other Dizhis form.
  # 夫妻宫与其他地支形成的关系（合、冲等）
  # house_relations: frozenset[DizhiRelation]

  # The relations that the day master and other Tiangans form.
  # 日主与其他天干形成的关系（合、冲等）
  # day_master_relations: frozenset[TianganRelation]


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
  
  # @staticmethod
  # def __find_tg_relations(it1: Iterable[Tiangan], it2: Iterable[Tiangan]) -> Iterable[TianganRelation]:
  #   '''An fp-styled helper private method for finding non-empty TianganRelations (天干关系).'''
  #   discovery = TianganUtils.discover_mutual(list(it1), list(it2))
  #   return map(lambda kv : kv[0], filter(lambda kv : len(kv[1]), discovery.items()))
  
  # @staticmethod
  # def __find_dz_relations(it1: Iterable[Dizhi], it2: Iterable[Dizhi]) -> Iterable[DizhiRelation]:
  #   '''An fp-styled helper private method for finding non-empty DizhiRelations (地支关系).'''
  #   discovery = DizhiUtils.discover_mutual(list(it1), list(it2))
    # return map(lambda kv : kv[0], filter(lambda kv : len(kv[1]), discovery.items()))

  def __init__(self, bazi_chart: BaziChart) -> None:
    self._bazi_chart: Final[BaziChart] = copy.deepcopy(bazi_chart)

  @property
  def at_birth(self) -> RelationshipAnalysis:
    y_tg, m_tg, d_tg, h_tg = self._bazi_chart.bazi.four_tiangans
    y_dz, m_dz, d_dz, h_dz = self._bazi_chart.bazi.four_dizhis

    return {
      'taohua' :  frozenset(self.__find_shensha(ShenshaUtils.taohua,   ([y_dz],  [m_dz, d_dz, h_dz]), 
                                                                       ([d_dz],  [y_dz, m_dz, h_dz]))),
      'hongyan':  frozenset(self.__find_shensha(ShenshaUtils.hongyan,  ([d_tg],  [y_dz, m_dz, d_dz, h_dz]))),
      'hongluan': frozenset(self.__find_shensha(ShenshaUtils.hongluan, ([y_dz],  [m_dz, d_dz, h_dz]))),
      'tianxi':   frozenset(self.__find_shensha(ShenshaUtils.tianxi,   ([y_dz],  [m_dz, d_dz, h_dz]))),

      # 'house_relations': frozenset(
      #   map(
      #     lambda kv : kv[0],
      #     filter(lambda kv : len(kv[1]), tiangan_discovery.items())
      #   )
      # ),
    }
