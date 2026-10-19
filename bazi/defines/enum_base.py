# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''领域枚举的共同行为。

BaziEnum 提供领域枚举基类，IndexedBaziEnum 另提供索引访问。'''

import functools

from enum import Enum
from typing import Self


@functools.cache
def _members(cls: type[Enum]) -> tuple[Enum, ...]:
  return tuple(cls)


@functools.cache
def _member_indexes(cls: type[Enum]) -> dict[Enum, int]:
  # 模块私有缓存表提供 O(1) 下标；调用方只读，不用于规则表的懒加载。
  return { member : index for index, member in enumerate(cls) }


class BaziEnum(Enum):
  '''
  领域枚举的公共基类，共用 `from_str` / `as_list` / `__str__`。
  子类钩子必须是描述符（如 classmethod）；Enum 类体中的普通类属性会成为枚举成员。
  '''

  @classmethod
  def _str_len(cls) -> int | None:
    '''子类钩子：`from_str` 输入的确切长度；None 表示不设长度前置条件。'''
    return None

  @classmethod
  def from_str(cls, s: str) -> Self:
    if not isinstance(s, str):
      raise TypeError(f'Expected str, got {type(s)}')
    expected_len = cls._str_len()
    if expected_len is not None and len(s) != expected_len:
      raise ValueError(f'Unsupported {cls.__name__} string: {s}')
    return cls(s)

  @classmethod
  def as_list(cls) -> list[Self]:
    return list(cls)

  def __str__(self) -> str:
    return str(self.value)


class IndexedBaziEnum(BaziEnum):
  '''在 `BaziEnum` 之上提供 O(1) 的定义序下标（`index` / `from_index`）。'''

  @property
  def index(self) -> int:
    return _member_indexes(type(self))[self]

  @classmethod
  def from_index(cls, i: int) -> Self:
    '''按定义序取成员，下标语义同 `list`：负数回绕，越界抛 IndexError。'''
    member = _members(cls)[i]
    # functools.cache 不保留 typevar，因此在此收窄辅助函数的返回类型，同时检查运行时类型。
    assert isinstance(member, cls)
    return member
