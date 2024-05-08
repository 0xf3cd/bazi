# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from typing import Final, Generator, Mapping

from ..Defines import Yinyang, Tiangan, Dizhi, Ganzhi
from ..Bazi import Bazi, BaziGender
from ..Utils import BaziUtils

from .ChartProtocol import ChartProtocol


class TransitChart:
  '''
  `TransitChart` generates the transit chart based on the given bazi / bazi chart.
  `TransitChart` 基于八字生成流年大运信息。
  '''
  def __init__(self, bazi: Bazi) -> None:
    '''
    Takes a `Bazi` as the input.
    接受一个 `Bazi` 作为输入。

    Args:
    - bazi (Bazi): A `Bazi` object.
    '''

    assert isinstance(bazi, Bazi)
    self._bazi: Final[Bazi] = copy.deepcopy(bazi)

  @property
  def bazi(self) -> Bazi:
    return copy.deepcopy(self._bazi)
  
  @property
  def dayun(self) -> Generator[Ganzhi, None, None]:
    '''
    A generator that produces the Ganzhis for Dayuns (大运). Each dayun lasts for 10 years.
    用于排大运的生成器。

    Usage: 
    ```
    tc: TransitChart = TransitChart(bazi)

    gen = tc.dayun
    first_ten_dayuns: list[Ganzhi] = [next(gen) for _ in range(10)]

    for gz in tc.dayun: # Infinite loop...
      print(gz)
    ``` 
    '''

    is_male: bool = (self._bazi.gender is BaziGender.男)
    is_year_dz_yang: bool = (BaziUtils.traits(self._bazi.year_pillar.dizhi).yinyang is Yinyang.阳)
    order: bool = (is_male == is_year_dz_yang)
    step: int = 1 if order else -1

    def __dayun_generator():
      tg, dz = self._bazi.month_pillar
      while True:
        tg = Tiangan.from_index((tg.index + step) % 10)
        dz = Dizhi.from_index((dz.index + step) % 12)
        yield Ganzhi(tg, dz)

    return __dayun_generator()
  
  @property
  def json(self) -> Mapping:
    '''
    A json dict representing the `TransitChart`.
    代表此 `TransitChart` 的 json 字典。
    '''
    return {}
  
流年大运 = TransitChart


assert isinstance(TransitChart, ChartProtocol)
