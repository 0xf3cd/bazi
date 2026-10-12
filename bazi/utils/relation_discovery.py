# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import TypeVar, Generic, Self
from collections.abc import Callable, Collection, Set as AbstractSet

from ..common import frozendict
from ..defines.enum_base import IndexedBaziEnum


_IndexedItem = TypeVar('_IndexedItem', bound=IndexedBaziEnum)


def _ordered_relation_pairs(
  pairs: Collection[tuple[_IndexedItem, _IndexedItem]],
) -> tuple[frozenset[_IndexedItem], ...]:
  '''按施方、受方的枚举序排列有向对，再投影为保序去重的无向组合。'''
  ordered = sorted(pairs, key=lambda pair: tuple(item.index for item in pair))
  return tuple(dict.fromkeys(frozenset(pair) for pair in ordered))


RelationType = TypeVar('RelationType')
RelationItemType = TypeVar('RelationItemType')
class RelationDiscovery(
  frozendict[RelationType, tuple[frozenset[RelationItemType], ...]],
  Generic[RelationType, RelationItemType],
):
  '''
  天干/地支关系发现结果的泛型基类：关系到组合的冻结映射，支持按组合过滤与合并。
  '''

  def filter(self, f: Callable[[RelationType, frozenset[RelationItemType]], bool]) -> Self:
    '''只保留 `f` 接受的组合；不再有组合的关系整键丢弃。'''
    if not callable(f):
      raise TypeError(f'Expected a callable, got {type(f)}')
    return type(self)({
      rel : filtered
      for rel, combos in self.items()
      if len(filtered := tuple(c for c in combos if f(rel, c))) > 0
    })

  def merge(self, other: Self) -> Self:
    '''合并两个发现结果；关系键与组合都按左侧、右侧的首次出现顺序保留，重复组合去重。'''
    if not isinstance(other, type(self)):
      raise TypeError(f'Expected {type(self).__name__}, got {type(other)}')
    d: dict[RelationType, dict[frozenset[RelationItemType], None]] = {}
    for discovery in (self, other):
      for rel, combos in discovery.items():
        d.setdefault(rel, {}).update(dict.fromkeys(combos))

    return type(self)({ rel : tuple(combos) for rel, combos in d.items() })

  def mutual_only(self, items1: AbstractSet[RelationItemType], items2: AbstractSet[RelationItemType]) -> Self:
    '''只保留与两侧值集均相交的组合；与任一侧不相交即单侧组合。

    Note: 按值判定，不追踪具体出现：组合全由单侧凑成，只要另一侧也有相同值，就会被保留。
    `discover_mutual([子, 丑], [子])` 仍保留六合{子,丑}（子出现在两侧值集里，尽管一侧就够凑）。'''
    if not isinstance(items1, AbstractSet):
      raise TypeError(f'Expected AbstractSet, got {type(items1)}')
    if not isinstance(items2, AbstractSet):
      raise TypeError(f'Expected AbstractSet, got {type(items2)}')
    return self.filter(lambda rel, combo: not combo.isdisjoint(items1) and not combo.isdisjoint(items2))
