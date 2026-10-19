# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''干支值类型 Ganzhi 及中文名称干支。'''

import functools

from typing import NamedTuple

from .tiangan import Tiangan
from .dizhi import Dizhi


class Ganzhi(NamedTuple):
  '''干支（Ganzhi）。'''
  tiangan: Tiangan
  dizhi:   Dizhi

  @classmethod
  def from_strs(cls, tiangan_str: str, dizhi_str: str) -> 'Ganzhi':
    return cls(Tiangan.from_str(tiangan_str), Dizhi.from_str(dizhi_str))
  
  @classmethod
  def from_str(cls, tiangan_dizhi_str: str) -> 'Ganzhi':
    if len(tiangan_dizhi_str) != 2:
      raise ValueError(f'Unsupported Ganzhi string: {tiangan_dizhi_str}')
    return cls(Tiangan.from_str(tiangan_dizhi_str[0]), Dizhi.from_str(tiangan_dizhi_str[1]))
  
  def __str__(self) -> str:
    return f'{self.tiangan}{self.dizhi}'
  
  @staticmethod
  def list_sexagenary_cycle() -> list['Ganzhi']:
    '''
    按六十甲子顺序列出全部干支组合。

    Return: (list[Ganzhi]) 六十甲子列表。
    '''
    tiangan_list: list[Tiangan] = Tiangan.as_list() * 6
    dizhi_list: list[Dizhi] = Dizhi.as_list() * 5
    assert len(tiangan_list) == len(dizhi_list)
    assert len(tiangan_list) == 60 # 60 甲子
    return [Ganzhi(tg, dz) for tg, dz in zip(tiangan_list, dizhi_list)]

  @staticmethod
  def list_sexagenary_cycle_strs() -> list[str]:
    '''
    按六十甲子顺序列出全部干支字符串。

    Return: (list[str]) 六十甲子字符串列表。
    '''
    return [str(gz) for gz in Ganzhi.list_sexagenary_cycle()]

  def next(self, step: int = 1) -> 'Ganzhi':
    '''在六十甲子中前进 step 步；阴阳不配的干支抛 ValueError。

    step 接受 int（含 bool 与 int 子类），可为零或负数。
    '''
    if not isinstance(step, int):
      raise TypeError(f'Expected int, got {type(step)}')
    return self.__shift(step)

  @functools.lru_cache(maxsize=1024)
  def __shift(self, step: int) -> 'Ganzhi':
    tiangan_index, dizhi_index = self.tiangan.index, self.dizhi.index
    if tiangan_index % 2 != dizhi_index % 2:
      raise ValueError(f'Unsupported sexagenary Ganzhi: {self}')
    return Ganzhi(
      Tiangan.from_index((tiangan_index + step) % 10),
      Dizhi.from_index((dizhi_index + step) % 12),
    )

  def prev(self, step: int = 1) -> 'Ganzhi':
    '''在六十甲子中后退 step 步；输入契约与 next 相同。'''
    if not isinstance(step, int):
      raise TypeError(f'Expected int, got {type(step)}')
    return self.__shift(-step)

干支 = Ganzhi # 中文别名
