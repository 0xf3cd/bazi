# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from typing import Final

from .Defines import Ganzhi
from .BaziChart import BaziChart
from .Transits import TransitOptions, TransitDatabase


class TransitChart:
  '''
  `TransitChart` reveals the transit information (i.e. Dayun / Xiaoyun / Liunian) of a given `BaziChart`.
  `TransitChart` 基于原盘（`BaziChart`）提供大运、小运、流年等运的信息。

  Note: `TransitChart` is a facade / the unified entry for querying transits.
  The actual computations are delegated to `TransitDatabase`.
  `TransitChart` 是一个门面类，作为查询运的统一入口，实际计算委托给 `TransitDatabase`。
  '''

  def __init__(self, bazi_chart: BaziChart) -> None:
    '''
    Takes a `BaziChart` as the input.
    接受一个 `BaziChart` 作为输入。

    Args:
    - `bazi_chart`: (BaziChart) The bazi chart (原盘) to generate the transit chart from.
    '''

    assert isinstance(bazi_chart, BaziChart)
    self._bazi_chart: Final[BaziChart] = copy.deepcopy(bazi_chart)
    self._transit_db: Final[TransitDatabase] = TransitDatabase(self._bazi_chart)

  @property
  def bazi_chart(self) -> BaziChart:
    '''The underlying `BaziChart` (原盘). A defensive copy is returned. 返回防御性拷贝。'''
    return copy.deepcopy(self._bazi_chart)

  def support(self, gz_year: int, options: TransitOptions) -> bool:
    '''
    Return whether the given `gz_year` and `options` are supported by this `TransitChart`.
    返回当前 `TransitChart` 是否支持给定的干支年和选项。

    Args:
    - `gz_year`: (int) The year in Ganzhi calendar. 干支纪年法中的年。
    - `options`: (TransitOptions) Specifies the transits to be picked. 用于指定是否考虑流年、小运、大运等。

    Return: (bool) Whether the given `gz_year` and `options` are supported by this `TransitChart`.
    '''

    assert isinstance(gz_year, int)
    assert isinstance(options, TransitOptions) and options in TransitOptions
    return self._transit_db.support(gz_year, options)

  def ganzhis(self, gz_year: int, options: TransitOptions) -> tuple[Ganzhi, ...]:
    '''
    Return the Ganzhis of the selected transits for the given `gz_year` and `options`.
    返回所选中的小运、大运或流年等对应的干支。

    Args:
    - `gz_year`: (int) The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `options`: (TransitOptions) Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (tuple[Ganzhi, ...]) The Ganzhis of the selected transits for the given `gz_year` and `options`.
    '''

    assert isinstance(gz_year, int)
    assert isinstance(options, TransitOptions) and options in TransitOptions
    return self._transit_db.ganzhis(gz_year, options)


流年大运 = TransitChart
