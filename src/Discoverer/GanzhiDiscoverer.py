# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Final

from ..Common import frozendict, PillarData, DayunDatabase, TransitOptions
from ..Defines import Tiangan, Dizhi, Ganzhi

from ..BaziChart import BaziChart

from ..Utils import BaziUtils, TianganUtils, DizhiUtils
from ..Calendar.CalendarDefines import CalendarDate


class GanzhiDiscoverer:
  '''Discovers the Tiangan's and Dizhi's relations of the birth chart and transits. 原局和小运/大运/流年的天干地支关系分析。'''

  def __init__(self, chart: BaziChart) -> None:
    self._birth_ganzhi_date: CalendarDate = chart.bazi.ganzhi_date

    self._atbirth_tiangans: Final[tuple[Tiangan, Tiangan, Tiangan, Tiangan]] = chart.bazi.four_tiangans
    self._atbirth_dizhis: Final[tuple[Dizhi, Dizhi, Dizhi, Dizhi]] = chart.bazi.four_dizhis

    birth_gz_year: Final[int] = chart.bazi.ganzhi_date.year
    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      birth_gz_year + age - 1 : gz
      for age, gz in chart.xiaoyun
    })

    self._first_dayun_start_gz_year: Final[int] = next(chart.dayun).ganzhi_year
    self._dayun_db: Final[DayunDatabase] = chart.dayun_db

  @property
  def at_birth(self) -> PillarData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]:
    return PillarData(TianganUtils.discover(self._atbirth_tiangans), DizhiUtils.discover(self._atbirth_dizhis))

  def support(self, gz_year: int, option: TransitOptions) -> bool:
    '''
    Returns `True` if the given `gz_year` and `option` are both supported.
    '''
    assert isinstance(gz_year, int)
    assert isinstance(option, TransitOptions) and option in TransitOptions

    if option.value & TransitOptions.XIAOYUN.value:
      if gz_year not in self._xiaoyun_ganzhis:
        return False
    if option.value & TransitOptions.DAYUN.value:
      if gz_year < self._first_dayun_start_gz_year:
        return False
    if option.value & TransitOptions.LIUNIAN.value:
      if gz_year < self._birth_ganzhi_date.year:
        return False
    return True
  
  def __validate_and_get_transit_ganzhis(self, gz_year: int, option: TransitOptions) -> tuple[Ganzhi, ...]:
    '''
    Return the Ganzhis of the transits of the given `gz_year` and `option`.

    返回所选中的小运、大运或流年对应的干支。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `option`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Returns: (tuple[Ganzhi]) The Ganzhis of the transits of the given `gz_year` and `option`.
    
    Example:
    - transit_ganzhis(1984, TransitOptions.DAYUN_LIUNIAN)
      - Return the Ganzhis of Dayun (the Dayun that 1984 falls into) and Liunian (1984).
        返回 1984 年所属的大运和流年的干支。
    '''

    assert isinstance(gz_year, int)
    assert isinstance(option, TransitOptions) and option in TransitOptions

    if not self.support(gz_year, option):
      raise ValueError(f'Inputs not supported. Year: {gz_year}, option: {option}')
    
    transit_ganzhis: list[Ganzhi] = []
    if option.value & TransitOptions.XIAOYUN.value:
      assert gz_year in self._xiaoyun_ganzhis
      transit_ganzhis.append(self._xiaoyun_ganzhis[gz_year])
    if option.value & TransitOptions.DAYUN.value:
      assert gz_year >= self._first_dayun_start_gz_year
      transit_ganzhis.append(self._dayun_db[gz_year].ganzhi)
    if option.value & TransitOptions.LIUNIAN.value:
      assert gz_year >= self._birth_ganzhi_date.year
      transit_ganzhis.append(BaziUtils.ganzhi_of_year(gz_year))

    return tuple(transit_ganzhis)

  def transits(self, gz_year: int, option: TransitOptions) -> PillarData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]:
    '''
    Return a `PillarData[TianganRelationDiscovery, DizhiRelationDiscovery]` object that represents Tiangans' and Dizhis' relations of transit pillars.
    
    返回一个 `PillarData[TianganRelationDiscovery, DizhiRelationDiscovery]`, 代表了小运/大运/流年之间关系的分析结果。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `option`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Returns: (PillarData[TianganRelationDiscovery, DizhiRelationDiscovery]) Discovery results of pillars (i.e. Tiangans and Dizhis) of the given year.
    
    Example:
    - mutual(1984, TransitOptions.DAYUN_LIUNIAN)
      - Return all relations that Dayun (the Dayun that 1984 falls into) and Liunian (1984) can form.
        返回结果包含 1984 年所属大运和流年能够构成的所有关系（即大运和流年的关系，不包含和原盘的关系）。
    - mutual(2024, TransitOptions.XIAOYUN)
      - Return will be empty since only Xiaoyun is selected, and at least 2 Tiangans/Dizhis can form any relation.
        返回结果将会为空，因为只有小运被选中。而至少需要 2 个天干或地支才能够构成某种关系。
    '''

    transit_ganzhis: tuple[Ganzhi, ...] = self.__validate_and_get_transit_ganzhis(gz_year, option)
    return PillarData(
      TianganUtils.discover(tuple(map(lambda gz : gz.tiangan, transit_ganzhis))),
      DizhiUtils.discover(tuple(map(lambda gz : gz.dizhi, transit_ganzhis))),
    )

  def mutual(self, gz_year: int, option: TransitOptions) -> PillarData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]:
    '''
    Return a `PillarData[TianganRelationDiscovery, DizhiRelationDiscovery]` object that represents Tiangans' and Dizhis' relations of the at-birth 4 pillars and transit pillars.

    返回一个 `PillarData[TianganRelationDiscovery, DizhiRelationDiscovery]`, 代表了原局和运（小运/大运/流年）之间的关系的分析结果。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `option`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Returns: (PillarData[TianganRelationDiscovery, DizhiRelationDiscovery]) Discovery results of pillars (i.e. Tiangans and Dizhis) of the given year.

    Examples:
    - mutual(1984, TransitOptions.DAYUN_LIUNIAN)
      - Dayun (the Dayun that 1984 falls into) and Liunian (1984) are picked.
        1984 年所属的大运和流年参与分析。
      - Result contains: The mutual relations between at-birth Ganzhis/pillars and transit Ganzhis/pillars.
        返回结果：原局四柱和运（小运、大运、流年）之间的关系/互相作用力，对于这个例子来说是原局的天干地支与流年大运的天干地支之间形成的力量关系。
    - mutual(2024, TransitOptions.XIAOYUN)
      - Xiaoyun of ganzhi year 2024 is picked.
        2024 年对应的小运参与分析。
      - Result contains: The mutual relations between at-birth Ganzhis/pillars and transit Ganzhis/pillars.
        返回结果：原局四柱和运（小运、大运、流年）之间的关系/互相作用力，对于这个例子来说是原局的天干地支与小运的天干地支之间形成的力量关系。
    '''

    transit_ganzhis: tuple[Ganzhi, ...] = self.__validate_and_get_transit_ganzhis(gz_year, option)
    return PillarData(
      TianganUtils.discover_mutual(self._atbirth_tiangans, tuple(map(lambda gz : gz.tiangan, transit_ganzhis))),
      DizhiUtils.discover_mutual(self._atbirth_dizhis, tuple(map(lambda gz : gz.dizhi, transit_ganzhis))),
    )
