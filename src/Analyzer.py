# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import itertools

from enum import Enum
from typing import Final, Generic, TypeVar

from .Common import frozendict
from .Defines import Tiangan, Dizhi, Ganzhi

from .BaziChart import BaziChart
from .Utils import TianganUtils


ResultDataType = TypeVar('ResultDataType')
class Result(Generic[ResultDataType]):
  '''Represents the analysis. It's generic-typed because it's used in different contexts.'''

  def __init__(
    self, *, 
    at_birth: ResultDataType,
    transits: ResultDataType,
    mutual:   ResultDataType,
  ) -> None:
    self._at_birth: Final[ResultDataType] = copy.deepcopy(at_birth)
    self._transits: Final[ResultDataType] = copy.deepcopy(transits)
    self._mutual:   Final[ResultDataType] = copy.deepcopy(mutual)

  @property
  def at_birth(self) -> ResultDataType:
    '''
    The analysis at birth time (birth chart)
    原盘分析
    '''
    return self._at_birth
  
  @property
  def transits(self) -> ResultDataType:
    '''
    The analysis of the transits (Xiaoyun/Dayun/Liunian)
    小运/大运/流年的分析
    '''
    return self._transits
  
  @property
  def mutual(self) -> ResultDataType:
    '''
    The analysis of the mutual effects/relations between birth chart and transits (Xiaoyun/Dayun/Liunian)
    原局与小运/大运/流年之间的相互作用力/关系的分析
    '''
    return self._mutual



class RelationAnalyzer:
  '''Analyzes the Tiangan's and Dizhi's relations.'''

  class TransitOption(Enum):
    XIAOYUN         = 0x1
    DAYUN           = 0x2
    LIUNIAN         = 0x4
    XIAOYUN_LIUNIAN = 0x1 | 0x4 # Pylance doesn't like "XIAOYUN | LIUNIAN"
    DAYUN_LIUNIAN   = 0x2 | 0x4 # Pylance doesn't like "DAYUN | LIUNIAN"

  def __init__(self, chart: BaziChart) -> None:
    self._atbirth_tiangans: Final[tuple[Tiangan, Tiangan, Tiangan, Tiangan]] = chart.bazi.four_tiangans
    self._atbirth_dizhis: Final[tuple[Dizhi, Dizhi, Dizhi, Dizhi]] = chart.bazi.four_dizhis

    self._liunian_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      year : gz
      for year, gz in itertools.islice(chart.liunian, 200) # only consider the first 200 years...
    })

    self._dayun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      year + offset : gz
      for year, gz in itertools.islice(chart.dayun, 20) # only consider the first 200 years...
      for offset in range(10)
    })

    birth_gz_year: Final[int] = chart.bazi.ganzhi_date.year
    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      birth_gz_year + age - 1 : gz
      for age, gz in chart.xiaoyun
    })

  def supports(self, gz_year: int, option: TransitOption) -> bool:
    '''
    Returns `True` if the given `gz_year` and `option` are both supported.
    '''
    assert isinstance(gz_year, int)
    assert isinstance(option, RelationAnalyzer.TransitOption) and option in RelationAnalyzer.TransitOption

    if option.value & RelationAnalyzer.TransitOption.XIAOYUN.value:
      if gz_year not in self._xiaoyun_ganzhis:
        return False
    if option.value & RelationAnalyzer.TransitOption.DAYUN.value:
      if gz_year not in self._dayun_ganzhis:
        return False
    if option.value & RelationAnalyzer.TransitOption.LIUNIAN.value:
      if gz_year not in self._liunian_ganzhis:
        return False
    return True

  def tiangan(self, gz_year: int, option: TransitOption) -> Result[TianganUtils.TianganRelationDiscovery]:
    '''
    Return a `Result[TianganRelationDiscovery]` object that represents Tiangans' relations of the at-birth 4 Tiangans and transit Tiangans.

    返回一个 `Result[TianganRelationDiscovery]`, 代表了原局、运、原局和运之间的关系的分析结果。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit Tiangans. 干支纪年法中的年，主要用于计算运（大运流年等）的天干。
# - `option`: The option of Tiangans' relations to be analyzed. 用于分析的天干关系的级别。
#   - If `Level.DAYUN`, first locate the input `gz_year` falls into which Dayun, and only consider the Dayun's Tiangan.
#   - If `Level.LIUNIAN`, only consider the Liunian's Tiangan.
#   - If `Level.DAYUN_LIUNIAN`, consider both the Dayun and the Liunian's Tiangans.

    Returns: (Result[TianganRelationDiscovery]) Analysis results of Tiangans of the given year.
    '''

    assert isinstance(gz_year, int)
    assert isinstance(option, RelationAnalyzer.TransitOption) and option in RelationAnalyzer.TransitOption

    if not self.supports(gz_year, option):
      raise ValueError(f'Inputs not supported. Year: {gz_year}, level: {option}')
    
    transit_tiangans: list[Tiangan] = []
    if option.value & RelationAnalyzer.TransitOption.XIAOYUN.value:
      transit_tiangans.append(self._xiaoyun_ganzhis[gz_year].tiangan)
    if option.value & RelationAnalyzer.TransitOption.DAYUN.value:
      transit_tiangans.append(self._dayun_ganzhis[gz_year].tiangan)
    if option.value & RelationAnalyzer.TransitOption.LIUNIAN.value:
      transit_tiangans.append(self._liunian_ganzhis[gz_year].tiangan)

    return Result(
      at_birth = TianganUtils.discover(self._atbirth_tiangans),
      transits = TianganUtils.discover(transit_tiangans),
      mutual   = TianganUtils.discover_mutually(self._atbirth_tiangans, transit_tiangans),
    )
