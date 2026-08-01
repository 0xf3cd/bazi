# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Final

from .enum_base import BaziEnum


class Wuxing(BaziEnum):
  '''Wuxing / 五行'''
  WOOD  = '木'
  FIRE  = '火'
  EARTH = '土'
  METAL = '金'
  WATER = '水'

  # Aliases
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
    Check if the input wuxing can be generated from the current.
    检查五行的相生关系，如果当前的五行可以生出输入的五行，则返回 True，否则返回 False。

    Args:
    - self: Wuxing object
    - wx: Wuxing object

    Returns:
    - True if the input wuxing can be generated from the current.
    - False otherwise

    Examples:
    - Wuxing.水.generates(Wuxing.木) -> True  # Water nourishes Wood / 水生木
    - Wuxing.木.generates(Wuxing.火) -> True  # Wood feeds Fire / 木生火
    - Wuxing.火.generates(Wuxing.木) -> False # Fire does not generate Wood / 火不生木
    '''
    return _GENERATES[self] is wx

  def destructs(self, wx: 'Wuxing') -> bool:
    '''
    Check if the input wuxing can be destroyed by the current.
    检查五行的相克关系，如果当前的五行克输入的五行，则返回 True，否则返回 False。

    Args:
    - self: Wuxing object
    - wx: Wuxing object

    Returns:
    - True if the input wuxing can be destroyed by the current.
    - False otherwise

    Examples:
    - Wuxing.金.destructs(Wuxing.木) -> True  # Metal destroys Wood / 金克木
    - Wuxing.土.destructs(Wuxing.水) -> True  # Earth destroys Water / 土克水
    - Wuxing.水.destructs(Wuxing.土) -> False # Water does not destroy Earth / 水不克土
    '''
    return _DESTRUCTS[self] is wx

# Both relations are walks along the generation cycle (相生环: 木→火→土→金→水→木):
# generation is one step, destruction two steps (隔位相克).
_CYCLE: Final[tuple[Wuxing, ...]] = (Wuxing.木, Wuxing.火, Wuxing.土, Wuxing.金, Wuxing.水)
_GENERATES: Final[dict[Wuxing, Wuxing]] = { wx : _CYCLE[(i + 1) % len(_CYCLE)] for i, wx in enumerate(_CYCLE) }
_DESTRUCTS: Final[dict[Wuxing, Wuxing]] = { wx : _CYCLE[(i + 2) % len(_CYCLE)] for i, wx in enumerate(_CYCLE) }


五行 = Wuxing # Alias
