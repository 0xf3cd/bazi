# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from typing import Optional

from . import Bazi


class TransitChart:
  '''
  `TransitChart` generates the transit chart based on the given bazi / bazi chart.
  `TransitChart` 基于八字生成流年大运信息。
  '''

  def __init__(self, bazi_chart: Bazi.BaziChart, *, override_gender: Optional[Bazi.BaziGender] = None) -> None:
    '''
    Takes a `Bazi.BaziChart` and optional `Bazi.BaziGender` as the input.
    接受一个 `Bazi.BaziChart` 和 `Bazi.BaziGender` 作为输入。`Bazi.BaziGender` 是可选的，默认为 `None`。

    Note:
    - In traditional Bazi's system, the order of the transits are different for two binary genders.
    - The input `override_gender`, if set, will override the gender of the bazi chart. If not specified, the order will be the same as the bazi chart gender.
    - Override `override_gender` to forcely use the order of different gender to generate the transit chart. Mainly for LGBTQ+ community.
    - 在八字体系中，两种性别对应的流年大运排盘顺序不同。
    - `override_gender` 是流年大运的排盘时所用的性别。如果未指定，则将使用八字生成时所用的性别。
    - 指定 `override_gender` 以强制使用不同性别的流年大运排盘顺序。主要用于 LGBTQ+ 人群。

    Args:
    - bazi_chart: (Bazi.BaziChart) The bazi chart to generate the transit chart.
    - override_gender: (Bazi.BaziGender) The order/gender used to generate the transit chart. It is the same as the bazi chart gender by default.
    '''

    assert isinstance(bazi_chart, Bazi.BaziChart)
    assert override_gender is None or isinstance(override_gender, Bazi.BaziGender)

    self._bazi_chart: Bazi.BaziChart = copy.deepcopy(bazi_chart)
    self._gender: Bazi.BaziGender = override_gender if override_gender else self._bazi_chart.bazi.gender

  @property
  def bazi_chart(self) -> Bazi.BaziChart:
    return copy.deepcopy(self._bazi_chart)
  
  @property
  def gender(self) -> Bazi.BaziGender:
    '''
    The gender/order used to generate the transit chart. It is the same as the bazi chart gender by default.
    用于流年大运排盘时使用的性别/顺序。默认和八字排盘时所用的性别相同。
    '''
    return self._gender

流年大运 = TransitChart
