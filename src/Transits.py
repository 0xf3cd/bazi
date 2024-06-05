# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import random

from enum import unique, IntFlag
from typing import Final, Generator

from .Common import DayunTuple, frozendict
from .Defines import Ganzhi
from .Calendar import CalendarDate
from .Utils.BaziUtils import ganzhi_of_year
from .BaziChart import BaziChart


class DayunDatabase:
  '''A database that figures out a given Ganzhi year falls into which Dayun (大运).'''
  def __init__(self, chart: BaziChart) -> None:
    self._gen: Final[Generator[DayunTuple, None, None]] = chart.dayun
    self._first_dayun: Final[DayunTuple] = next(self._gen)
    self._cache: Final[dict[int, Ganzhi]] = {
      self._first_dayun.ganzhi_year : self._first_dayun.ganzhi,
    }

  def __getitem__(self, gz_year: int) -> DayunTuple:
    assert isinstance(gz_year, int)
    assert gz_year >= self._first_dayun.ganzhi_year

    dayun_idx: int = (gz_year - self._first_dayun.ganzhi_year) // 10
    expected_gz_year: int = self._first_dayun.ganzhi_year + 10 * dayun_idx

    while expected_gz_year not in self._cache:
      next_dayun: DayunTuple = next(self._gen)
      self._cache[next_dayun.ganzhi_year] = next_dayun.ganzhi

    return DayunTuple(expected_gz_year, self._cache[expected_gz_year])


@unique
class TransitOptions(IntFlag):
  '''Specifies whether Dayun / Xiaoyun / Liunian transits should be considered. 用于指定是否考虑大运流年、小运、流年等。'''
  XIAOYUN         = 0x1
  DAYUN           = 0x2
  LIUNIAN         = 0x4
  XIAOYUN_LIUNIAN = XIAOYUN | LIUNIAN
  DAYUN_LIUNIAN   = DAYUN   | LIUNIAN

  @staticmethod
  def random() -> 'TransitOptions':
    '''Mainly for testing purpose.'''
    # Python 3.9 complains about the return type if using `random.choice(list(TransitOptions))`.
    # So explicitly list all options here.
    return random.choice([
      TransitOptions.XIAOYUN,
      TransitOptions.DAYUN,
      TransitOptions.LIUNIAN,
      TransitOptions.XIAOYUN_LIUNIAN,
      TransitOptions.DAYUN_LIUNIAN,
    ])


class TransitDatabase:
  '''A database that figures out the Ganzhis of transits.'''
  def __init__(self, chart: BaziChart) -> None:
    self._birth_ganzhi_date: CalendarDate = chart.bazi.ganzhi_date

    birth_gz_year: Final[int] = chart.bazi.ganzhi_date.year
    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      birth_gz_year + age - 1 : gz
      for age, gz in chart.xiaoyun
    })

    self._first_dayun_start_gz_year: Final[int] = next(chart.dayun).ganzhi_year
    self._dayun_db: Final[DayunDatabase] = DayunDatabase(chart)

  def support(self, gz_year: int, options: TransitOptions) -> bool:
    '''
    Return whether the given `gz_year` and `option` are supported by this `TransitDatabase`.

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (bool) Whether the given `gz_year` and `options` are supported by this `TransitDatabase`.
    '''

    assert isinstance(gz_year, int)
    assert isinstance(options, TransitOptions)
    assert options in TransitOptions

    if options.value & TransitOptions.XIAOYUN.value:
      if gz_year not in self._xiaoyun_ganzhis:
        return False
    if options.value & TransitOptions.DAYUN.value:
      if gz_year < self._first_dayun_start_gz_year:
        return False
    if options.value & TransitOptions.LIUNIAN.value:
      if gz_year < self._birth_ganzhi_date.year:
        return False

    return True

  def ganzhis(self, gz_year: int, options: TransitOptions) -> tuple[Ganzhi, ...]:
    '''
    Return the Ganzhis of the selected transits for the given `gz_year` and `option`.

    返回所选中的小运、大运或流年等对应的干支。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (tuple[Ganzhi, ...]) The Ganzhis of the selected transits for the given `gz_year` and `options`.
    '''

    assert isinstance(gz_year, int)
    assert isinstance(options, TransitOptions) and options in TransitOptions

    if not self.support(gz_year, options):
      raise ValueError(f'Inputs not supported. Year: {gz_year}, options: {options}')

    transit_ganzhis: list[Ganzhi] = []
    if options.value & TransitOptions.XIAOYUN.value:
      assert gz_year in self._xiaoyun_ganzhis
      transit_ganzhis.append(self._xiaoyun_ganzhis[gz_year])
    if options.value & TransitOptions.DAYUN.value:
      assert gz_year >= self._first_dayun_start_gz_year
      transit_ganzhis.append(self._dayun_db[gz_year].ganzhi)
    if options.value & TransitOptions.LIUNIAN.value:
      assert gz_year >= self._birth_ganzhi_date.year
      transit_ganzhis.append(ganzhi_of_year(gz_year))

    return tuple(transit_ganzhis)
