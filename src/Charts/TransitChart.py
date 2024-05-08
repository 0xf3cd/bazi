# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from typing import Final

from ..Bazi import Bazi


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
  
流年大运 = TransitChart
