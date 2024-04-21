# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from .Bazi import BaziChart
from .Defines import Shishen
from .Descriptions import ShishenDescription, SHISHEN_DESCRIPTIONS

class Interpretation:
  '''
  This class takes a BaziChart and interprets it.
  '''

  @staticmethod
  def interpret_shishen(shishen: Shishen) -> ShishenDescription:
    '''Interpret the given Shishen and return the corresponding description.'''
    assert isinstance(shishen, Shishen)
    return copy.deepcopy(SHISHEN_DESCRIPTIONS[shishen])

  def __init__(self, chart: BaziChart) -> None:
    '''
    This method initializes a new instance of the Interpretation class by
    creating a deep copy of the provided BaziChart object.

    Args:
    - chart: (BaziChart) The BaziChart object to be interpreted.

    Raises:
      AssertionError: If the provided chart is not an instance of BaziChart.
    '''
    assert isinstance(chart, BaziChart)
    self._chart: BaziChart = copy.deepcopy(chart)

  @property
  def chart(self) -> BaziChart:
    return copy.deepcopy(self._chart)
