# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import dataclass
from typing import TypeVar, Generic, NamedTuple, Self
from collections.abc import Iterator, Callable, Set as AbstractSet

from .common import frozendict
from .defines import Wuxing, Yinyang, Tiangan, Ganzhi


'''
Immutable domain value shapes shared across layers (rules / utils / chart / transits).
跨层共享的不可变领域值类型。Split out of `common.py` (issue #99), which now keeps the
infrastructure primitives only.
'''


class TraitTuple(NamedTuple):
  '''Representing the Wuxing and Yinyang of a Tiangan or Dizhi. 某天干或地支的五行和阴阳。'''
  wuxing:  Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


class DayunTuple(NamedTuple):
  '''Representing the Dayun of a bazi chart. 八字命盘的某步大运。'''
  ganzhi_year: int
  ganzhi:      Ganzhi


class XiaoyunTuple(NamedTuple):
  '''Representing the Xiaoyun of a bazi chart. 八字命盘的某个小运。'''
  xusui:  int    # 虚岁
  ganzhi: Ganzhi


class LiunianTuple(NamedTuple):
  '''Representing a Liunian. 流年。'''
  ganzhi_year: int
  ganzhi:      Ganzhi


class HiddenTianganDict(frozendict[Tiangan, int]):
  '''
  `HiddenTianganDict` reveals the hidden Tiangans info.
  The dict represents the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
  A `HiddenTianganDict` is simply a `frozendict` with a customized `__str__` function.

  `HiddenTianganDict` 代表了某个地支的藏干和藏干各自所占的百分比。
  '''
  def __str__(self) -> str:
    sorted_kv = sorted(self.items(), key=lambda kv : kv[1], reverse=True)
    return ','.join([f'{k}:{v}' for k, v in sorted_kv])


PillarDataType = TypeVar('PillarDataType')
@dataclass(frozen=True)
class BaziData(Generic[PillarDataType]):
  '''
  A generic class for storing Bazi data.
  A `BaziData` object stores 4 `PillarDataType` objects for year, month, day, and hour.
  '''
  year: PillarDataType
  month: PillarDataType
  day: PillarDataType
  hour: PillarDataType

  def __iter__(self) -> Iterator[PillarDataType]:
    return iter((self.year, self.month, self.day, self.hour))


TianganDataType = TypeVar('TianganDataType')
DizhiDataType = TypeVar('DizhiDataType')
@dataclass(frozen=True)
class GanzhiData(Generic[TianganDataType, DizhiDataType]):
  '''
  A helper class for storing the data of a Pillar/Ganzhi.
  Can be used with `BaziData` class.
  '''
  tiangan: TianganDataType
  dizhi: DizhiDataType


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
    assert callable(f)
    return type(self)({
      rel : filtered
      for rel, combos in self.items()
      if len(filtered := tuple(c for c in combos if f(rel, c))) > 0
    })

  def merge(self, other: Self) -> Self:
    '''Merge two discoveries together (set-union of combos per relation).
    合并两个发现结果（每个关系下的组合做集合并）。'''
    assert isinstance(other, type(self))
    d: dict[RelationType, set[frozenset[RelationItemType]]] = {}

    for rel, combos in self.items():
      d[rel] = set(combos)
    for rel, combos in other.items():
      d[rel] = d.get(rel, set()) | set(combos)

    return type(self)({ rel : tuple(combos) for rel, combos in d.items() })

  def mutual_only(self, items1: AbstractSet[RelationItemType], items2: AbstractSet[RelationItemType]) -> Self:
    '''Keep only the combos that draw from both sides (a combo disjoint from either side
    comes from one side only). 只保留同时取材于两侧的组合（与任一侧不相交即单侧组合）。'''
    return self.filter(lambda rel, combo: not combo.isdisjoint(items1) and not combo.isdisjoint(items2))
