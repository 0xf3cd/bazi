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
    self._hash: int | None = None
  def __getitem__(self, key: FrozenDictKeyType) -> FrozenDictValueType:
    return self._data[key]
  def __iter__(self) -> Iterator[FrozenDictKeyType]:
    return iter(self._data)
  def __len__(self) -> int:
    return len(self._data)
  def __hash__(self) -> int:
    # Tuple semantics, computed lazily: equal contents hash equal (in sync with
    # `Mapping.__eq__`), and unhashable contents (e.g. the description corpus holds
    # lists) raise TypeError on the first hash attempt.
    # 元组语义，惰性计算：内容相等则哈希相等（与 `Mapping.__eq__` 一致），
    # 内容不可哈希（如语料表的 list 值）则首次求哈希时抛 TypeError。
    if self._hash is None:
      self._hash = hash(frozenset(self._data.items()))
    return self._hash

#endregion

