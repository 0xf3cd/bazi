# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Final

from ..Common import GanzhiData
from ..Defines import Tiangan, Dizhi, Ganzhi

from ..BaziChart import BaziChart, TransitOptions, TransitDatabase

from ..Utils import TianganUtils, DizhiUtils


class GanzhiDiscoverer:
  '''Discovers the Tiangan's and Dizhi's relations of the birth chart and transits. 原局和小运/大运/流年的天干地支关系分析。'''

  GanzhiRelationDiscovery = GanzhiData[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]

  def __init__(self, chart: BaziChart) -> None:
    self._atbirth_tiangans: Final[tuple[Tiangan, Tiangan, Tiangan, Tiangan]] = chart.bazi.four_tiangans
    self._atbirth_dizhis: Final[tuple[Dizhi, Dizhi, Dizhi, Dizhi]] = chart.bazi.four_dizhis

    self._transit_db: Final[TransitDatabase] = TransitDatabase(chart)

  def support(self, gz_year: int, options: TransitOptions) -> bool:
    '''
    Returns `True` if the given `gz_year` and `options` are both supported.
    '''
    return self._transit_db.support(gz_year, options)
  
  def __validate_and_get_transit_ganzhis(self, gz_year: int, options: TransitOptions) -> tuple[Ganzhi, ...]:
    '''
    Return the Ganzhis of the transits of the given `gz_year` and `options`.

    返回所选中的小运、大运或流年对应的干支。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `option`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Returns: (tuple[Ganzhi]) The Ganzhis of the transits of the given `gz_year` and `options`.
    
    Example:
    - transit_ganzhis(1984, TransitOptions.DAYUN_LIUNIAN)
      - Return the Ganzhis of Dayun (the Dayun that 1984 falls into) and Liunian (1984).
        返回 1984 年所属的大运和流年的干支。
    '''

    assert isinstance(gz_year, int)
    assert isinstance(options, TransitOptions) and options in TransitOptions

    if not self.support(gz_year, options):
      raise ValueError(f'Inputs not supported. Year: {gz_year}, options: {options}')
    
    return self._transit_db.ganzhis(gz_year, options)
  
  @property
  def at_birth(self) -> GanzhiRelationDiscovery:
    '''
    Return a `GanzhiRelationDiscovery` object that represents Tiangans' and Dizhis' relations at birth.

    返回一个 `GanzhiRelationDiscovery`，代表了出生时的天干地支关系。
    '''
    return GanzhiDiscoverer.GanzhiRelationDiscovery(
      TianganUtils.discover(self._atbirth_tiangans),
      DizhiUtils.discover(self._atbirth_dizhis)
    )

  def transits_only(self, gz_year: int, options: TransitOptions) -> GanzhiRelationDiscovery:
    '''
    Return a `GanzhiRelationDiscovery` object that represents Tiangans' and Dizhis' relations of transit pillars.
    
    返回一个 `GanzhiRelationDiscovery`, 代表了小运/大运/流年之间关系的分析结果。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。
  
    Returns: (GanzhiRelationDiscovery) Discovery results of pillars (i.e. Tiangans and Dizhis) of the given year.
    
    Example:
    - mutual(1984, TransitOptions.DAYUN_LIUNIAN)
      - Return all relations that Dayun (the Dayun that 1984 falls into) and Liunian (1984) can form.
        返回结果包含 1984 年所属大运和流年能够构成的所有关系（即大运和流年的关系，不包含和原盘的关系）。
    - mutual(2024, TransitOptions.XIAOYUN)
      - Return will be empty since only Xiaoyun is selected, and at least 2 Tiangans/Dizhis can form any relation.
        返回结果将会为空，因为只有小运被选中。而至少需要 2 个天干或地支才能够构成某种关系。
    '''

    transit_ganzhis: tuple[Ganzhi, ...] = self.__validate_and_get_transit_ganzhis(gz_year, options)
    return GanzhiDiscoverer.GanzhiRelationDiscovery(
      TianganUtils.discover(tuple(map(lambda gz : gz.tiangan, transit_ganzhis))), 
      DizhiUtils.discover(tuple(map(lambda gz : gz.dizhi, transit_ganzhis))),
    )

  def transits_mutual(self, gz_year: int, options: TransitOptions) -> GanzhiRelationDiscovery:
    '''
    Return a `GanzhiRelationDiscovery` object that represents Tiangans' and Dizhis' relations of the at-birth 4 pillars and transit pillars.

    返回一个 `GanzhiRelationDiscovery`, 代表了原局和运（小运/大运/流年）之间的关系的分析结果。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Returns: (GanzhiRelationDiscovery) Discovery results of pillars (i.e. Tiangans and Dizhis) of the given year.

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

    transit_ganzhis: tuple[Ganzhi, ...] = self.__validate_and_get_transit_ganzhis(gz_year, options)
    return GanzhiDiscoverer.GanzhiRelationDiscovery(
      TianganUtils.discover_mutual(self._atbirth_tiangans, tuple(map(lambda gz : gz.tiangan, transit_ganzhis))), 
      DizhiUtils.discover_mutual(self._atbirth_dizhis, tuple(map(lambda gz : gz.dizhi, transit_ganzhis))),
    )
