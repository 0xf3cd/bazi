# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from typing import Final

from .BaziChart import BaziChart
# from .Utils.TianganUtils 


class RelationAnalyzer:
  '''
  This class takes a BaziChart and analyzes Tiangans' and Dizhis' relations.
  '''

  def __init__(self, chart: BaziChart) -> None:
    self._chart: Final[BaziChart] = copy.deepcopy(chart)

  @property
  def chart(self) -> BaziChart:
    return copy.deepcopy(self._chart)
