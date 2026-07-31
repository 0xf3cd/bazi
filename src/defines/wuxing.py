# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum


class Wuxing(Enum):
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
  def from_str(cls, s: str) -> 'Wuxing':
    assert isinstance(s, str)
    assert len(s) == 1
    return cls(s)

  @classmethod
  def as_list(cls) -> list['Wuxing']:
    return list(cls)

  def __str__(self) -> str:
    return str(self.value)
  
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
    if self is Wuxing.木:
      return wx is Wuxing.火
    elif self is Wuxing.火:
      return wx is Wuxing.土
    elif self is Wuxing.土:
      return wx is Wuxing.金
    elif self is Wuxing.金:
      return wx is Wuxing.水
    else:
      assert self is Wuxing.水
      return wx is Wuxing.木
    
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
    if self is Wuxing.木:
      return wx is Wuxing.土
    elif self is Wuxing.火:
      return wx is Wuxing.金
    elif self is Wuxing.土:
      return wx is Wuxing.水
    elif self is Wuxing.金:
      return wx is Wuxing.木
    else:
      assert self is Wuxing.水
      return wx is Wuxing.火

五行 = Wuxing # Alias
