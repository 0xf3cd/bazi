# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import functools

from enum import Enum
from typing import Self


@functools.cache
def _members(cls: type[Enum]) -> tuple[Enum, ...]:
  return tuple(cls)


@functools.cache
def _member_indexes(cls: type[Enum]) -> dict[Enum, int]:
  # This cached table IS the O(1) `index` mechanism (not lazy loading of a rule table).
  # Module-private; callers only read. 缓存表即 O(1) 下标本体；模块私有，只读消费。
  return { member : index for index, member in enumerate(cls) }


class BaziEnum(Enum):
  '''
  Shared base of the domain enums, deduplicating the `from_str` / `as_list` / `__str__`
  boilerplate. Subclass hooks must be descriptors (e.g. classmethods) -- a plain class
  attribute in an `Enum` body would be swallowed as a member.
  领域枚举的公共基类，收敛 `from_str` / `as_list` / `__str__` 样板。子类钩子必须是
  描述符（如 classmethod）——Enum 类体里的普通类属性会被吃成枚举成员。
  '''

  @classmethod
  def _str_len(cls) -> int | None:
    '''Subclass hook: the exact `from_str` input length, or None for no length precondition.
    子类钩子：`from_str` 输入的确切长度；None 表示不设长度前置条件。'''
    return None

  @classmethod
  def from_str(cls, s: str) -> Self:
    assert isinstance(s, str)
    expected_len = cls._str_len()
    if expected_len is not None:
      assert len(s) == expected_len
    return cls(s)

  @classmethod
  def as_list(cls) -> list[Self]:
    return list(cls)

  def __str__(self) -> str:
    return str(self.value)


class IndexedBaziEnum(BaziEnum):
  '''`BaziEnum` plus O(1) definition-order indexing (`index` / `from_index`).
  在 `BaziEnum` 之上另提供 O(1) 的定义序下标（`index` / `from_index`）。'''

  @property
  def index(self) -> int:
    return _member_indexes(type(self))[self]

  @classmethod
  def from_index(cls, i: int) -> Self:
    '''Definition-order lookup with `list`-style indexing: negative indexes wrap,
    out-of-range raises IndexError. 定义序取成员，下标语义同 `list`：负数回绕，越界 IndexError。'''
    member = _members(cls)[i]
    # `functools.cache` erases the helper's generic type; this narrows it back for mypy
    # and doubles as a runtime guard. cache 包装抹平泛型，此断言兼作 mypy 窄化与运行时防线。
    assert isinstance(member, cls)
    return member
