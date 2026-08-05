# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import TypeVar, Generic, Self
from collections.abc import Callable, Set as AbstractSet

from ..common import frozendict


RelationType = TypeVar('RelationType')
RelationItemType = TypeVar('RelationItemType')
class RelationDiscovery(
  frozendict[RelationType, tuple[frozenset[RelationItemType], ...]],
  Generic[RelationType, RelationItemType],
):
  '''
  Generic base of `TianganRelationDiscovery` / `DizhiRelationDiscovery`: a frozen mapping
  from relation to its matching combos, with combo-level filtering and merging.
  天干/地支关系发现结果的泛型基类：关系到组合的冻结映射，支持按组合过滤与合并。
  '''

  def filter(self, f: Callable[[RelationType, frozenset[RelationItemType]], bool]) -> Self:
    '''Keep only the combos accepted by `f`; relations left with no combo are dropped.
    只保留 `f` 接受的组合；不再有组合的关系整键丢弃。'''
    if not callable(f):
      raise TypeError(f'Expected a callable, got {type(f)}')
    return type(self)({
      rel : filtered
      for rel, combos in self.items()
      if len(filtered := tuple(c for c in combos if f(rel, c))) > 0
    })

  def merge(self, other: Self) -> Self:
    '''Merge two discoveries together (set-union of combos per relation).
    合并两个发现结果（每个关系下的组合做集合并）。'''
    if not isinstance(other, type(self)):
      raise TypeError(f'Expected {type(self).__name__}, got {type(other)}')
    d: dict[RelationType, set[frozenset[RelationItemType]]] = {}

    for rel, combos in self.items():
      d[rel] = set(combos)
    for rel, combos in other.items():
      d[rel] = d.get(rel, set()) | set(combos)

    return type(self)({ rel : tuple(combos) for rel, combos in d.items() })

  def mutual_only(self, items1: AbstractSet[RelationItemType], items2: AbstractSet[RelationItemType]) -> Self:
    '''Keep only the combos that draw from both sides (a combo disjoint from either side
    comes from one side only). 只保留同时取材于两侧的组合（与任一侧不相交即单侧组合）。

    Note: the test is by VALUE, not by provenance -- a combo built entirely from one side
    can still be kept if the other side happens to share the value:
    `discover_mutual([子, 丑], [子])` keeps 六合{子,丑} (子 appears in both value-sets,
    though side 1 alone completes the combo).
    按值判定，非按出处：组合全由单侧凑成，只要另一侧碰巧也有这个值，就会被保留——
    `discover_mutual([子, 丑], [子])` 仍保留六合{子,丑}（子出现在两侧值集里，尽管一侧就够凑）。'''
    if not isinstance(items1, AbstractSet):
      raise TypeError(f'Expected AbstractSet, got {type(items1)}')
    if not isinstance(items2, AbstractSet):
      raise TypeError(f'Expected AbstractSet, got {type(items2)}')
    return self.filter(lambda rel, combo: not combo.isdisjoint(items1) and not combo.isdisjoint(items2))
