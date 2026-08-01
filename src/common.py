# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import TypeVar, Final
from collections.abc import Iterator, Mapping


######################################################
#region Immutable data structures

FrozenDictKeyType = TypeVar('FrozenDictKeyType')
FrozenDictValueType = TypeVar('FrozenDictValueType')
class frozendict(Mapping[FrozenDictKeyType, FrozenDictValueType]):
  '''
  My simple implementation of a frozen, immutable dict.

  Shallow-frozen: the mapping itself never changes, and lookups return the stored
  values as-is (no defensive copies). A holder of mutable values protects them at
  its own boundary (e.g. `Interpreter` deep-copies corpus entries).
  浅冻结：映射本身不可变，取值原样返回、不做防御性拷贝。持有可变值的一方在自己的
  边界自行防护（如 `Interpreter` 深拷语料条目）。
  '''
  def __init__(self, data: Mapping[FrozenDictKeyType, FrozenDictValueType]) -> None:
    self._data: Final[Mapping[FrozenDictKeyType, FrozenDictValueType]] = dict(data)
  def __getitem__(self, key: FrozenDictKeyType) -> FrozenDictValueType:
    return self._data[key]
  def __iter__(self) -> Iterator[FrozenDictKeyType]:
    return iter(self._data)
  def __len__(self) -> int:
    return len(self._data)

#endregion

