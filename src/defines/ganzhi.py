# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import functools

from typing import NamedTuple

from .tiangan import Tiangan
from .dizhi import Dizhi


class Ganzhi(NamedTuple):
  '''Ganzhi / Stem-branch / 干支'''
  tiangan: Tiangan
  dizhi:   Dizhi

  @classmethod
  def from_strs(cls, tiangan_str: str, dizhi_str: str) -> 'Ganzhi':
    return cls(Tiangan.from_str(tiangan_str), Dizhi.from_str(dizhi_str))
  
  @classmethod
  def from_str(cls, tiangan_dizhi_str: str) -> 'Ganzhi':
    assert len(tiangan_dizhi_str) == 2
    return cls(Tiangan.from_str(tiangan_dizhi_str[0]), Dizhi.from_str(tiangan_dizhi_str[1]))
  
  def __str__(self) -> str:
    return f'{self.tiangan}{self.dizhi}'
  
  @staticmethod
  def list_sexagenary_cycle() -> list['Ganzhi']:
    '''
    Return a list of all 60 `Ganzhi` pairs in the sexagenary cycle.
    列出所有 60 甲子中的所有天干地支组合。

    Return: a list of `Ganzhi` tuples representing the 60 ganzhi pairs.
    '''
    tiangan_list: list[Tiangan] = Tiangan.as_list() * 6
    dizhi_list: list[Dizhi] = Dizhi.as_list() * 5
    assert len(tiangan_list) == len(dizhi_list)
    assert len(tiangan_list) == 60 # 60 甲子
    return [Ganzhi(tg, dz) for tg, dz in zip(tiangan_list, dizhi_list)]

  @staticmethod
  def list_sexagenary_cycle_strs() -> list[str]:
    '''
    Return a list of all 60 `Ganzhi` pairs in the sexagenary cycle as strings.
    列出所有 60 甲子中的所有天干地支组合（以字符串形式）。

    Return: a list of strings representing the 60 ganzhi pairs.
    '''
    return [str(gz) for gz in Ganzhi.list_sexagenary_cycle()]

  @functools.lru_cache(maxsize=1024)
  def next(self, step: int = 1) -> 'Ganzhi':
    assert isinstance(step, int)
    cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
    return cycle[(cycle.index(self) + step) % 60]

  @functools.lru_cache(maxsize=1024)
  def prev(self, step: int = 1) -> 'Ganzhi':
    assert isinstance(step, int)
    cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
    return cycle[(cycle.index(self) - step) % 60]

干支 = Ganzhi # Alias
