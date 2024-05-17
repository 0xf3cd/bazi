# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import itertools

from enum import Enum
from typing import Final

from .Common import frozendict, TianganRelationDiscovery
from .Defines import Tiangan, Dizhi, Ganzhi

from .BaziChart import BaziChart
from .Utils import TianganUtils

class AtBirthAnalyzer:
  '''
  This class does analysis on birth chart (i.e. 4 pillars of Year, Month, Day, and Hour).
  '''
  def __init__(self, chart: BaziChart) -> None:
    self._tiangans: Final[tuple[Tiangan, Tiangan, Tiangan, Tiangan]] = chart.bazi.four_tiangans
    self._dizhis: Final[tuple[Dizhi, Dizhi, Dizhi, Dizhi]] = chart.bazi.four_dizhis

  @property
  def tiangan(self) -> TianganRelationDiscovery:
    return TianganUtils.discover(self._tiangans)



class TransitAnalyzer:
  '''
  This class analyzes the transit chart (i.e. Liunian and Dayun / 流年大运).
  '''

  class Level(Enum):
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

    assert len(self._liunian_ganzhis) == 200
    assert len(self._dayun_ganzhis) == 200

  def supports(self, gz_year: int, level: Level) -> bool:
    if level.value & TransitAnalyzer.Level.XIAOYUN.value:
      if gz_year not in self._xiaoyun_ganzhis:
        return False
    if level.value & TransitAnalyzer.Level.DAYUN.value:
      if gz_year not in self._dayun_ganzhis:
        return False
    if level.value & TransitAnalyzer.Level.LIUNIAN.value:
      if gz_year not in self._liunian_ganzhis:
        return False
    return True

  def tiangan(self, gz_year: int, level: Level) -> TianganRelationDiscovery:
    '''
    Return a `TianganRelationDiscovery` that represents Tiangans' relations of the at-birth 4 Tiangans and Liunian/Dayun Tiangans.

    Args:
    - `gz_year`: The year in Ganzhi calendar. 干支纪年法中的年。
    - `level`: The level of Tiangans' relations to be analyzed. 用于分析的天干关系的级别。
      - If `Level.DAYUN`, first locate the input `gz_year` falls into which Dayun, and only consider the Dayun's Tiangan.
      - If `Level.LIUNIAN`, only consider the Liunian's Tiangan.
      - If `Level.DAYUN_LIUNIAN`, consider both the Dayun and the Liunian's Tiangans.

    Returns: (TianganRelationDiscovery) Analysis results of Tiangans of the given year.
    '''

    if not self.supports(gz_year, level):
      raise ValueError(f'Inputs not supported. Year: {gz_year}, level: {level}')

    transit_tiangans: list[Tiangan] = []
    if level.value & TransitAnalyzer.Level.XIAOYUN.value:
      transit_tiangans.append(self._xiaoyun_ganzhis[gz_year].tiangan)
    if level.value & TransitAnalyzer.Level.DAYUN.value:
      transit_tiangans.append(self._dayun_ganzhis[gz_year].tiangan)
    if level.value & TransitAnalyzer.Level.LIUNIAN.value:
      transit_tiangans.append(self._liunian_ganzhis[gz_year].tiangan)
    
    assert len(transit_tiangans) > 0
    return TianganUtils.discover_mutually(self._atbirth_tiangans, transit_tiangans)
