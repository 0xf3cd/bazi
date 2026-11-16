# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''干支值类型 Ganzhi 及中文名称干支。'''

import functools

from collections.abc import Iterable
from typing import NamedTuple, Self

from .tiangan import Tiangan
from .dizhi import Dizhi


class _GanzhiFields(NamedTuple):
  tiangan: Tiangan
  dizhi:   Dizhi


class Ganzhi(_GanzhiFields):
  '''六十甲子中的干支；字段错型抛 TypeError，阴阳不配抛 ValueError。'''
  __slots__ = ()

  def __new__(cls, tiangan: Tiangan, dizhi: Dizhi) -> Self:
    if not isinstance(tiangan, Tiangan):
      raise TypeError(f'Expected Tiangan, got {type(tiangan)}')
    if not isinstance(dizhi, Dizhi):
      raise TypeError(f'Expected Dizhi, got {type(dizhi)}')
    if tiangan.index % 2 != dizhi.index % 2:
      raise ValueError(f'Unsupported sexagenary Ganzhi: {tiangan}{dizhi}')
    return super().__new__(cls, tiangan, dizhi)

  @classmethod
  def _make(cls, iterable: Iterable[object]) -> Self: # type: ignore[override] # mypy 的 NamedTuple 泛型类参数不能与子类 Self 对齐。
    # NamedTuple 的 _replace 和 Python 3.13+ 的 __replace__ 都经由 _make。
    return cls(*super()._make(iterable))

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
    '''在六十甲子中前进 step 步。

    step 接受 int（含 bool 与 int 子类），可为零或负数。
    '''
    if not isinstance(step, int):
      raise TypeError(f'Expected int, got {type(step)}')
    return self.__shift(step)

  @functools.lru_cache(maxsize=1024)
  def __shift(self, step: int) -> 'Ganzhi':
    tiangan_index, dizhi_index = self.tiangan.index, self.dizhi.index
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
