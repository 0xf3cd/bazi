# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Final

from .enum_base import BaziEnum


class Wuxing(BaziEnum):
  '''五行（Wuxing）。'''
  WOOD  = '木'
  FIRE  = '火'
  EARTH = '土'
  METAL = '金'
  WATER = '水'

  # 中文别名
  木 = WOOD
  火 = FIRE
  土 = EARTH
  金 = METAL
  水 = WATER

  @classmethod
  def _str_len(cls) -> int | None:
    return 1

  def generates(self, wx: 'Wuxing') -> bool:
    '''
    检查当前五行是否生输入五行。

    Args:
    - self: (Wuxing) 生的一方。
    - wx: (Wuxing) 被生的一方。

    Return: (bool) 相生时为 True，否则为 False。

    Examples:
    - Wuxing.水.generates(Wuxing.木) -> True  # 水生木
    - Wuxing.木.generates(Wuxing.火) -> True  # 木生火
    - Wuxing.火.generates(Wuxing.木) -> False # 火不生木
    '''
    return _GENERATES[self] is wx

  def destructs(self, wx: 'Wuxing') -> bool:
    '''
    检查当前五行是否克输入五行。

    Args:
    - self: (Wuxing) 克的一方。
    - wx: (Wuxing) 被克的一方。

    Return: (bool) 相克时为 True，否则为 False。

    Examples:
    - Wuxing.金.destructs(Wuxing.木) -> True  # 金克木
    - Wuxing.土.destructs(Wuxing.水) -> True  # 土克水
    - Wuxing.水.destructs(Wuxing.土) -> False # 水不克土
    '''
    return _DESTRUCTS[self] is wx

# 相生环为木→火→土→金→水→木；前进一位为相生，前进两位为相克（隔位相克）。
_CYCLE: Final[tuple[Wuxing, ...]] = (Wuxing.木, Wuxing.火, Wuxing.土, Wuxing.金, Wuxing.水)
_GENERATES: Final[dict[Wuxing, Wuxing]] = { wx : _CYCLE[(i + 1) % len(_CYCLE)] for i, wx in enumerate(_CYCLE) }
_DESTRUCTS: Final[dict[Wuxing, Wuxing]] = { wx : _CYCLE[(i + 2) % len(_CYCLE)] for i, wx in enumerate(_CYCLE) }


五行 = Wuxing # 中文别名
