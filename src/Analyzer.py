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

    # Cache at-birth tiangan relation analysis since it won't change...
    self._atbirth_tiangan_analysis: Final[TianganUtils.TianganRelationDiscovery] = TianganUtils.discover(self._atbirth_tiangans)

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
    - `option`: Specifies the Tiangas to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Returns: (Result[TianganRelationDiscovery]) Analysis results of Tiangans of the given year.

    Examples:
    - tiangan(1984, TransitOption.DAYUN_LIUNIAN)
      - Transit Tiangans picked from Dayun (the Dayun that 1984 falls into) and Liunian (1984).
        1984 年所属的大运和流年的天干参与分析。
      - Result contains / 返回结果:
        - at_birth: The relations between at-birth Tiangans that can be analyzed from birth chart.
                    原局的四天干之间的关系。
        - transits: The relations between transit Tiangans - for this example, the relation between Dayun's Tiangan and Liunian's Tiangan.
                    运（小运、大运、流年）的天干之间的关系，对于这个例子来说则是流年天干和大运天干之间的关系。
        - mutual: The mutual relations between at-birth Tiangans and transit Tiangans.
                  原局天干和运（小运、大运、流年）天干之间的关系/互相作用力，对于这个例子来说是原局四天干与流年大运天干之间形成的力量关系。
    - tiangan(2024, TransitOption.XIAOYUN)
      - Transit Tiangans picked from Xiaoyun of ganzhi year 2024.
        2024 年对应的小运的天干参与分析。
      - Result contains / 返回结果:
        - at_birth: The relations between at-birth Tiangans that can be analyzed from birth chart.
                    原局的四天干之间的关系。
        - transits: The relations between transit Tiangans - for this example, the result will be empty because only Xiaoyun is selected.
                    运（小运、大运、流年）的天干之间的关系，对于这个例子来说结果为空，因为只有小运参与分析（需要至少两个天干才能形成天干关系）。
        - mutual: The mutual relations between at-birth Tiangans and transit Tiangans.
                  原局天干和运（小运、大运、流年）天干之间的关系/互相作用力，对于这个例子来说是原局四天干与小运天干之间形成的力量关系。
    '''

    assert isinstance(gz_year, int)
    assert isinstance(option, RelationAnalyzer.TransitOption) and option in RelationAnalyzer.TransitOption

    if not self.supports(gz_year, option):
      raise ValueError(f'Inputs not supported. Year: {gz_year}, option: {option}')
    
    transit_tiangans: list[Tiangan] = []
    if option.value & RelationAnalyzer.TransitOption.XIAOYUN.value:
      transit_tiangans.append(self._xiaoyun_ganzhis[gz_year].tiangan)
    if option.value & RelationAnalyzer.TransitOption.DAYUN.value:
      transit_tiangans.append(self._dayun_ganzhis[gz_year].tiangan)
    if option.value & RelationAnalyzer.TransitOption.LIUNIAN.value:
      transit_tiangans.append(self._liunian_ganzhis[gz_year].tiangan)

    return Result(
      at_birth = self._atbirth_tiangan_analysis, # Sending an immutable analysis result.
      transits = TianganUtils.discover(transit_tiangans),
      mutual   = TianganUtils.discover_mutually(self._atbirth_tiangans, transit_tiangans),
    )
