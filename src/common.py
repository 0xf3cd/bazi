# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from typing import TypeVar, Final
from collections.abc import Iterator, Mapping


######################################################
#region Immutable data structures

FrozenDictKeyType = TypeVar('FrozenDictKeyType')
FrozenDictValueType = TypeVar('FrozenDictValueType')
class frozendict(Mapping[FrozenDictKeyType, FrozenDictValueType]):
  '''
  My simple implementation of a frozen, immutable dict.
  '''
  def __init__(self, data: Mapping[FrozenDictKeyType, FrozenDictValueType]) -> None:
    self._data: Final[Mapping[FrozenDictKeyType, FrozenDictValueType]] = copy.deepcopy(data)
  def __getitem__(self, key: FrozenDictKeyType) -> FrozenDictValueType:
    # Use deepcopy to avoid changing the original dict.
    # The value may not be deepcopyable though...
    return copy.deepcopy(self._data[key])
  def __iter__(self) -> Iterator[FrozenDictKeyType]:
    return iter(self._data)
  def __len__(self) -> int:
    return len(self._data)

#endregion

