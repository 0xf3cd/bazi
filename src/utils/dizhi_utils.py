# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>


from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Final
from collections.abc import Sequence, Collection

from ..common import frozendict
from ..defines import Dizhi, Ganzhi, Wuxing, DizhiRelation
from ..rules import DizhiRules
from .relation_discovery import RelationDiscovery


'''
Functions in this file are used to find all possible Dizhi combos that satisfy different `DizhiRelation`s.
All methods' returns are expected to be immutable.
'''


'''Represents a Dizhi combo that satisfies a certain `DizhiRelation`.'''
DizhiCombo = frozenset[Dizhi]

'''A list of all possible Dizhi combos that satisfy a certain `DizhiRelation`.'''
DizhiRelationCombos = tuple[DizhiCombo, ...]

class DizhiRelationDiscovery(RelationDiscovery[DizhiRelation, Dizhi]):
  '''A frozen mapping from `DizhiRelation` to the Dizhi combos that satisfy it.
  地支关系到满足它的地支组合的冻结映射。'''


@dataclass(frozen=True)
class GanzhiOccurrence:
  '''A concrete Ganzhi occurrence in a relation query, identified by its zero-based
  index in the input sequence. 关系查询中干支的一次具体出现，以其在输入序列中的零基
  序号标识。

  Args:
  - index: (int) The occurrence's zero-based index in the query sequence.
  - ganzhi: (Ganzhi) The complete stem-branch value at that index.
  '''
  index:  int
  ganzhi: Ganzhi

  def __post_init__(self) -> None:
    if not isinstance(self.index, int):
      raise TypeError(f'Expected int, got {type(self.index)}')
    if self.index < 0:
      raise ValueError(f'Expected a non-negative index, got {self.index}')
    if not isinstance(self.ganzhi, Ganzhi):
      raise TypeError(f'Expected Ganzhi, got {type(self.ganzhi)}')


'''A concrete combo of Ganzhi occurrences whose Dizhis satisfy a `DizhiRelation`.'''
GanzhiRelationCombo = frozenset[GanzhiOccurrence]

'''All concrete Ganzhi-occurrence combos that satisfy a `DizhiRelation`.'''
GanzhiRelationCombos = tuple[GanzhiRelationCombo, ...]

class GanzhiRelationDiscovery(RelationDiscovery[DizhiRelation, GanzhiOccurrence]):
  '''A frozen mapping from `DizhiRelation` to concrete Ganzhi-occurrence combos.
  地支关系到满足它的具体干支位置组合的冻结映射。'''

  def to_dizhi_discovery(self) -> DizhiRelationDiscovery:
    '''Project occurrences to their Dizhis, explicitly discarding position and Tiangan;
    occurrence combos that collapse to the same Dizhi combo are deduplicated.
    把具体出现投影为地支，显式丢弃位置与天干；投影后相同的地支组合会去重。'''
    projected: dict[DizhiRelation, tuple[DizhiCombo, ...]] = {}
    for relation, combos in self.items():
      unique: dict[DizhiCombo, None] = {}
      for combo in combos:
        unique[DizhiCombo(occurrence.ganzhi.dizhi for occurrence in combo)] = None
      projected[relation] = tuple(unique)
    return DizhiRelationDiscovery(projected)


def sanhui(dz1: Dizhi, dz2: Dizhi, dz3: Dizhi) -> Wuxing | None:
  '''
  Check if the input Dizhis are in SANHUI (三会) relation. If so, return the corresponding Wuxing. If not, return `None`.
  We don't care the order of the inputs, since SANHUI relation is non-directional/mutual.
  检查输入的地支是否构成三会关系。如果是，返回三会后形成的五行。否则返回 `None`。
  返回结果与输入的地支顺序无关，因为三会关系是无方向的。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.
  - dz3: (Dizhi) The third Dizhi.

  Return: (Wuxing | None) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in SANHUI (三会) relation.

  Examples:
  - sanhui(Dizhi.寅, Dizhi.卯, Dizhi.辰)
    - return: Wuxing.木
  - sanhui(Dizhi.寅, Dizhi.卯, Dizhi.丑)
    - return: None
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2, dz3)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2, dz3)]}')
  combo: DizhiCombo = DizhiCombo((dz1, dz2, dz3))
  return DizhiRules.DIZHI_SANHUI.get(combo, None)


def liuhe(dz1: Dizhi, dz2: Dizhi) -> Wuxing | None:
  '''
  Check if the input Dizhis are in LIUHE (六合) relation. If so, return the corresponding Wuxing. If not, return `None`.
  We don't care the order of the inputs, since LIUHE relation is non-directional/mutual.
  检查输入的地支是否构成六合关系。如果是，返回六合后形成的五行。否则返回 `None`。
  返回结果与输入的地支顺序无关，因为六合关系是无方向的。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (Wuxing | None) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in LIUHE (六合) relation.

  Examples:
  - liuhe(Dizhi.寅, Dizhi.亥)
    - return: Wuxing.木
  - liuhe(Dizhi.寅, Dizhi.辰)
    - return: None
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  combo: DizhiCombo = DizhiCombo((dz1, dz2))
  return DizhiRules.DIZHI_LIUHE.get(combo, None)


def anhe(dz1: Dizhi, dz2: Dizhi, *, definition: DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED) -> bool:
  '''
  Check if the input Dizhis are in ANHE (暗合) relation. If so, return `True`. If not, return `False`.
  There are multiple definitions for ANHE. The default definition is `DizhiRules.AnheDef.NORMAL_EXTENDED`.
  检查输入的地支是否构成暗合关系。如果是，返回 `True`。否则返回 `False`。
  暗合关系的看法有多种，默认使用 `DizhiRules.AnheDef.NORMAL_EXTENDED`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.
  - definition: (DizhiRules.AnheDef) The definition of the ANHE relation. Default to `DizhiRules.AnheDef.NORMAL_EXTENDED`.

  Return: (bool) Whether the Dizhis form in ANHE (暗合) relation.

  Examples:
  - anhe(Dizhi.寅, Dizhi.午)
    - return: True
  - anhe(Dizhi.寅, Dizhi.丑)
    - return: True
  - anhe(Dizhi.寅, Dizhi.丑, DizhiRules.AnheDef.NORMAL)
    - return: False
  - anhe(Dizhi.寅, Dizhi.午, DizhiRules.AnheDef.MANGPAI)
    - return: False
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  if not isinstance(definition, DizhiRules.AnheDef):
    raise TypeError(f'Expected AnheDef, got {type(definition)}')
  combo: DizhiCombo = DizhiCombo((dz1, dz2))
  return combo in DizhiRules.DIZHI_ANHE[definition]


def tonghe(dz1: Dizhi, dz2: Dizhi) -> bool:
  '''
  Check if the input Dizhis are in TONGHE (通合) relation. If so, return `True`. If not, return `False`.
  检查输入的地支是否构成通合关系。如果是，返回 `True`。否则返回 `False`。
  通合指的是两个地支的所有藏干都两两相合。通合常用于盲派。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (bool) Whether the Dizhis form in TONGHE (通合) relation.

  Examples:
  - tonghe(Dizhi.寅, Dizhi.午)
    - return: False
  - tonghe(Dizhi.寅, Dizhi.丑)
    - return: True
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  combo: DizhiCombo = DizhiCombo((dz1, dz2))
  return combo in DizhiRules.DIZHI_TONGHE


def tongluhe(dz1: Dizhi, dz2: Dizhi) -> bool:
  '''
  Check if the input Dizhis are in TONGLUHE (通禄合) relation. If so, return `True`. If not, return `False`.
  检查输入的地支是否构成通禄合关系。如果是，返回 `True`。否则返回 `False`。
  通禄合指的是五合的天干在地支对应的禄身之间的相合。通禄合常用于盲派。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (bool) Whether the Dizhis form in TONGLUHE (通禄合) relation.

  Examples:
  - tongluhe(Dizhi.寅, Dizhi.午)
    - return: True
  - tongluhe(Dizhi.寅, Dizhi.丑)
    - return: False
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  combo: DizhiCombo = DizhiCombo((dz1, dz2))
  return combo in DizhiRules.DIZHI_TONGLUHE


def sanhe(dz1: Dizhi, dz2: Dizhi, dz3: Dizhi) -> Wuxing | None:
  '''
  Check if the input Dizhis are in SANHE (三合) relation. If so, return the corresponding Wuxing. If not, return `None`.
  检查输入的地支是否构成三合关系。如果是，返回对应的五行。如果不是，返回 `None`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.
  - dz3: (Dizhi) The third Dizhi.

  Return: (Wuxing | None) The corresponding Wuxing if the Dizhis form in SANHE (三合) relation. Otherwise, return `None`.

  Examples:
  - sanhe(Dizhi.亥, Dizhi.卯, Dizhi.未)
    - return: Wuxing.木
  - sanhe(Dizhi.亥, Dizhi.卯, Dizhi.丑)
    - return: None
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2, dz3)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2, dz3)]}')
  combo: DizhiCombo = DizhiCombo((dz1, dz2, dz3))
  return DizhiRules.DIZHI_SANHE.get(combo, None)


def banhe(dz1: Dizhi, dz2: Dizhi) -> Wuxing | None:
  '''
  Check if the input Dizhis are in BANHE (半合) relation. If so, return the corresponding Wuxing. If not, return `None`.
  检查输入的地支是否构成半合关系。如果是，返回对应的五行。如果不是，返回 `None`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (Wuxing | None) The corresponding Wuxing if the Dizhis form in BANHE (半合) relation. Otherwise, return `None`.

  Examples:
  - banhe(Dizhi.亥, Dizhi.卯)
    - return: Wuxing.木
  - banhe(Dizhi.卯, Dizhi.未)
    - return: Wuxing.木
  - banhe(Dizhi.亥, Dizhi.丑)
    - return: None
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  combo: DizhiCombo = DizhiCombo((dz1, dz2))
  return DizhiRules.DIZHI_BANHE.get(combo, None)


def xing(*dizhis: Dizhi, definition: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> DizhiRules.XingSubType | None:
  '''
  Check if the input Dizhis is a exact match for XING (刑) relation. If so, return the type of the XING relation. If not, return `None`.
  There are multiple definitions for 刑. The default definition is `DizhiRules.XingDef.LOOSE`.
  If `DizhiRules.XingDef.LOOSE` is used, then the `dizhis` order (direction) matters.
  If `DizhiRules.XingDef.STRICT` is used, then the `dizhis` order does not matter.

  检查输入的地支是否刚好构成相刑关系。如果是，返回相刑的类型。如果不是，返回 `None`。
  相刑关系的看法有多种，默认使用 `DizhiRules.XingDef.LOOSE`。
  如果使用 `DizhiRules.XingDef.LOOSE`，则 `dizhis` 的顺序会影响结果。
  如果使用 `DizhiRules.XingDef.STRICT`，则 `dizhis` 的顺序不会影响结果。

  Note:
  - Maximum length of the input `dizhis` is 3.
  - `dizhis` 的最大长度为 3。

  Args:
  - *dizhis: (Dizhi) The Dizhis to check.
  - definition: (DizhiRules.XingDef) The definition for 刑.

  Return: (DizhiRules.XingSubType | None) The type of the XING relation if the Dizhis form in XING (刑) relation. Otherwise, return `None`.

  Examples:
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申])
    - return: XingSubType.SANXING
  - xing(*[Dizhi.寅, Dizhi.巳], definition=DizhiRules.XingDef.STRICT)
    - return: None
  - xing(*[Dizhi.寅, Dizhi.巳], definition=DizhiRules.XingDef.LOOSE)
    - return: XingSubType.SANXING
  - xing(Dizhi.午)
    - return: None
  - xing(Dizhi.午, Dizhi.午)
    - return: XingSubType.ZIXING
  - xing(Dizhi.午, definition=DizhiRules.XingDef.LOOSE)
    - return: None
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午]) # Not a exact match.
    - return: None
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午, Dizhi.午]) # Multiple matches.
    - return: None
  '''

  if not all(isinstance(dz, Dizhi) for dz in dizhis):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis]}')
  if len(dizhis) > 3:
    raise ValueError(f'Expected at most 3 Dizhis, got {len(dizhis)}')
  if not isinstance(definition, DizhiRules.XingDef):
    raise TypeError(f'Expected XingDef, got {type(definition)}')

  xing_rules: frozendict[tuple[Dizhi, ...], DizhiRules.XingSubType] = DizhiRules.DIZHI_XING[definition]
  return xing_rules.get(dizhis, None)


def chong(dz1: Dizhi, dz2: Dizhi) -> bool:
  '''
  Check if the input Dizhis are in CHONG (冲) relation. If so, return `True`. If not, return `False`.
  检查输入的地支是否构成冲关系。如果是，返回 `True`。否则返回 `False`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (bool) Whether the Dizhis form in CHONG (冲) relation.

  Examples:
  - chong(Dizhi.子, Dizhi.午)
    - return: True
  - chong(Dizhi.午, Dizhi.子)
    - return: True
  - chong(Dizhi.子, Dizhi.丑)
    - return: False
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  return DizhiCombo((dz1, dz2)) in DizhiRules.DIZHI_CHONG


def po(dz1: Dizhi, dz2: Dizhi) -> bool:
  '''
  Check if the input Dizhis are in PO (破) relation. If so, return `True`. If not, return `False`.
  检查输入的地支是否构成破关系。如果是，返回 `True`。否则返回 `False`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (bool) Whether the Dizhis form in PO (破) relation.

  Examples:
  - po(Dizhi.卯, Dizhi.午)
    - return: True
  - po(Dizhi.午, Dizhi.卯)
    - return: True
  - po(Dizhi.丑, Dizhi.子)
    - return: False
  - po(Dizhi.丑, Dizhi.辰)
    - return: True
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  return DizhiCombo((dz1, dz2)) in DizhiRules.DIZHI_PO


def hai(dz1: Dizhi, dz2: Dizhi) -> bool:
  '''
  Check if the input Dizhis are in HAI (害) relation. If so, return `True`. If not, return `False`.
  检查输入的地支是否构成相害关系。如果是，返回 `True`。否则返回 `False`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (bool) Whether the Dizhis form in HAI (害) relation.

  Examples:
  - hai(Dizhi.卯, Dizhi.辰)
    - return: True
  - hai(Dizhi.辰, Dizhi.卯)
    - return: True
  - hai(Dizhi.丑, Dizhi.子)
    - return: False
  - hai(Dizhi.丑, Dizhi.午)
    - return: True
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  return DizhiCombo((dz1, dz2)) in DizhiRules.DIZHI_HAI


def sheng(dz1: Dizhi, dz2: Dizhi) -> bool:
  '''
  Check if the input Dizhis are in SHENG (生) relation. If so, return `True`. If not, return `False`.
  Yinyang is not checked - only Wuxing is considered.
  检查输入的地支是否构成生关系。如果是，返回 `True`。否则返回 `False`。
  相生关系只关注五行，不区分阴阳。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (bool) Whether the Dizhis form in SHENG (生) relation.

  Examples:
  - sheng(Dizhi.卯, Dizhi.亥)
    - return: False
  - sheng(Dizhi.亥, Dizhi.卯)
    - return: True
  - sheng(Dizhi.丑, Dizhi.子)
    - return: False
  - sheng(Dizhi.丑, Dizhi.午)
    - return: False
  - sheng(Dizhi.午, Dizhi.丑)
    - return: True
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  return (dz1, dz2) in DizhiRules.DIZHI_SHENG


def ke(dz1: Dizhi, dz2: Dizhi) -> bool:
  '''
  Check if the input Dizhis are in KE (克) relation. If so, return `True`. If not, return `False`.
  Yinyang is not checked - only Wuxing is considered.
  检查输入的地支是否构成相克关系。如果是，返回 `True`。否则返回 `False`。
  相克关系只关注五行，不区分阴阳。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (bool) Whether the Dizhis form in KE (克) relation.

  Examples:
  - ke(Dizhi.子, Dizhi.巳)
    - return: True
  - ke(Dizhi.巳, Dizhi.子)
    - return: False
  - ke(Dizhi.丑, Dizhi.子)
    - return: True
  - ke(Dizhi.丑, Dizhi.午)
    - return: False
  - ke(Dizhi.午, Dizhi.丑)
    - return: False
  '''

  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  return (dz1, dz2) in DizhiRules.DIZHI_KE


# The subset-style relations `search` supports, mapped to their combo tables. 暗合 is NOT
# here: its table is picked by the `anhe_def` parameter at query time. Tables are
# stored as-is -- wrapping the mapping tables in `frozenset` would trade their stable
# definition-order iteration for per-process hash order.
# `search` 支持的子集型关系与其组合表（暗合不在此列——它的表在查询期按 `anhe_def` 参数选择）。
# 表原样存放——若包一层 `frozenset`，映射表稳定的定义序迭代会退化成逐进程哈希序。
_SUBSET_SEARCH_COMBOS: Final[frozendict[DizhiRelation, Collection[DizhiCombo]]] = frozendict({
  DizhiRelation.三会:  DizhiRules.DIZHI_SANHUI,
  DizhiRelation.六合:  DizhiRules.DIZHI_LIUHE,
  DizhiRelation.通合:  DizhiRules.DIZHI_TONGHE,
  DizhiRelation.通禄合: DizhiRules.DIZHI_TONGLUHE,
  DizhiRelation.三合:  DizhiRules.DIZHI_SANHE,
  DizhiRelation.半合:  DizhiRules.DIZHI_BANHE,
  DizhiRelation.冲:   DizhiRules.DIZHI_CHONG,
  DizhiRelation.破:   DizhiRules.DIZHI_PO,
  DizhiRelation.害:   DizhiRules.DIZHI_HAI,
})


def search(dizhis: Sequence[Dizhi], relation: DizhiRelation, *,
           anhe_def: DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED,
           xing_def: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> DizhiRelationCombos:
  '''
  Find all possible Dizhi combos in the given `dizhis` that satisfy the `relation`.
  返回`dizhis`中所有满足该关系的组合。

  Note:
  - The returned combos don't reveal the directions.
  - For example, if the returned value for SHENG relation is ({午, 寅}), then we are unable to infer it is 寅 that generates 午 or 午 that generates 寅.
  - For mutual/non-directional relations (e.g. SANHE, SANHUI, ...), that's fine, because we don't care about the direction.
  - For uni-directional relations, please use other methods in this class to check that (e.g. `sheng`, `ke`, ...). 
  - For XING relation, it's a bit more complicated.
    - Some definitions require all the Dizhis to appear in order to qualify the SANXING (三刑) relation (a subset of XING).
    - Some definitions consider only two Dizhis appearing a valid XING relation (e.g. only 丑 and 未 can form a XING relation).
    - Which definition applies is chosen by `xing_def`; under the default `XingDef.LOOSE`, any two of 丑未戌 / 寅巳申 suffice (see the `xing_def` Note below).
    - Use `xing` to do more fine-grained checking.
  - 返回的 combos 中没有体现关系作用的方向。
  - 比如说，如果检查输入地支的相生关系并返回 ({午, 寅})，那么不能从返回结果中看出是寅生午还是午生寅。
  - 对于无方向的关系来说（合、会），我们不用关心返回结果中的方向。
  - 对于有方向的关系来说（生、克等），请使用其他方法来检查（如 `sheng`， `ke` 等）。
  - 对于刑关系，更复杂一些：
    - 对于辰午酉亥自刑，只需要同时出现两次就满足相刑关系。
    - 对于子卯相刑，只需要子、卯都出现就满足相刑关系。
    - 对于丑未戌、寅巳申三刑，有的看法认为需要三个地支同时出现才算刑，有的看法认为只需要出现两个也算相刑。
    - 用哪个定义由 `xing_def` 决定；默认 `XingDef.LOOSE` 下，丑未戌、寅巳申三取二即算（见下方 `xing_def` 注）。
    - 请使用 `xing` 来进行更细粒度的检查。

  Note:
  - For ANHE relation, the `anhe_def` parameter picks the table; it defaults to
    `DizhiRules.AnheDef.NORMAL_EXTENDED`, the widest definition. Charts declare this
    school reading via `BaziSchool.anhe_def`.
  - 暗合查询的表由 `anhe_def` 参数选择，默认 `DizhiRules.AnheDef.NORMAL_EXTENDED`（最宽定义）。
    盘级流派口径经 `BaziSchool.anhe_def` 声明。

  Note:
  - For XING relation, the `xing_def` parameter picks the table; it defaults to
    `DizhiRules.XingDef.LOOSE`. This is a batch entry: combos are compared as multisets,
    so direction (谁刑谁) is unobservable here -- `LOOSE` at this entry means exactly
    "any two of the three". Use `xing` for direction-aware checks (see `XingDef`'s docstring).
  - e.g., if only 丑 and 未 appear in the input, the XING relation is considered satisfied (戌 missing, but `LOOSE` definition only requires any two of the three).
  - 刑查询的表由 `xing_def` 参数选择，默认 `DizhiRules.XingDef.LOOSE`。本入口是批量查法：
    组合按多重集比对，方向（谁刑谁）不可观测——`LOOSE` 在此就等于「三取二」。
    要看方向请用 `xing`（见 `XingDef` 的 docstring）。
  - 举例来说，即使输入中只有丑、未，也符合相刑关系（缺少戌，但 `LOOSE` 定义只要求三个地支中出现两个）。

  Args:
  - dizhis: (Sequence[Dizhi]) The Dizhis to check. A sequence rather than a set --
    the frequency of Dizhis matters.
  - relation: (DizhiRelation) The relation to check.
  - anhe_def: (DizhiRules.AnheDef) The ANHE definition; only consulted for 暗合 queries.
  - xing_def: (DizhiRules.XingDef) The XING definition; only consulted for 刑 queries.

  Return: (DizhiRelationCombos) The result containing all matching Dizhi combos.

  Examples:
  - search([Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.午, Dizhi.未], DizhiRelation.三会)
    - return: ({Dizhi.寅, Dizhi.卯, Dizhi.辰})
  - search([Dizhi.寅, Dizhi.卯, Dizhi.丑, Dizhi.午, Dizhi.申], DizhiRelation.暗合)
    - return: ({ Dizhi.卯, Dizhi.申}, { Dizhi.寅, Dizhi.午}, { Dizhi.寅, Dizhi.丑})
    - The default `DizhiRules.AnheDef.NORMAL_EXTENDED` is used.
  - search([Dizhi.寅,Dizhi.巳, Dizhi.申, Dizhi.辰], DizhiRelation.刑)
    - return: ({ Dizhi.寅, Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.巳 }, { Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.申 })
    - Only one 辰 appears in the input - not forming a XING relation.
  - search([Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.辰, Dizhi.辰], DizhiRelation.刑)
    - return: ({ Dizhi.寅, Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.巳 }, { Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.申 }, { Dizhi.辰 }) # Only one 辰 in the returned set!
    - 辰 appear twice in the input - forming a XING relation.
  - search([Dizhi.卯, Dizhi.子, Dizhi.寅, Dizhi.巳], DizhiRelation.刑)
    - return: ({ Dizhi.子, Dizhi.卯}, { Dizhi.寅, Dizhi.巳 })
    - The default `DizhiRules.XingDef.LOOSE` is used.
  '''

  if not isinstance(relation, DizhiRelation):
    raise TypeError(f'Expected DizhiRelation, got {type(relation)}')
  if not isinstance(dizhis, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(dizhis)}')
  if not all(isinstance(dz, Dizhi) for dz in dizhis):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis]}')
  if not isinstance(anhe_def, DizhiRules.AnheDef):
    raise TypeError(f'Expected AnheDef, got {type(anhe_def)}')
  if not isinstance(xing_def, DizhiRules.XingDef):
    raise TypeError(f'Expected XingDef, got {type(xing_def)}')

  if relation is DizhiRelation.刑:
    # Multiset-sensitive, so plain subset tests don't apply: 自刑 needs the same Dizhi twice.
    # 多重集语义（自刑要求同一地支出现两次），普通子集判定不适用。
    dz_counter: Counter[Dizhi] = Counter(dizhis)

    ret: set[DizhiCombo] = set()
    for xing_tuple in DizhiRules.DIZHI_XING[xing_def]:
      xing_dz_counter: Counter[Dizhi] = Counter(xing_tuple)
      if dz_counter & xing_dz_counter == xing_dz_counter:
        ret.add(DizhiCombo(xing_tuple))

    return DizhiRelationCombos(ret)

  if relation is DizhiRelation.生 or relation is DizhiRelation.克:
    # The rule tables hold directed (subject, object) pairs -- fold them into direction-less
    # combos first. 生克规则表存的是有向对，先折叠成无向组合。
    pairs: frozenset[tuple[Dizhi, Dizhi]] = DizhiRules.DIZHI_KE if relation is DizhiRelation.克 else DizhiRules.DIZHI_SHENG
    pair_combos: frozenset[DizhiCombo] = frozenset(map(DizhiCombo, pairs))
    dz_set: set[Dizhi] = set(dizhis)
    return DizhiRelationCombos(combo for combo in pair_combos if combo.issubset(dz_set))

  # Every other relation shares one shape: keep the table combos fully present in the input.
  # 暗合's table is picked by `anhe_def` at query time; the rest resolve statically.
  # 其余关系同构：保留完整出现在输入中的组合。暗合的表在查询期按 `anhe_def` 选，其余静态解析。
  combos: Collection[DizhiCombo] = (
    DizhiRules.DIZHI_ANHE[anhe_def] if relation is DizhiRelation.暗合 else _SUBSET_SEARCH_COMBOS[relation]
  )
  return DizhiRelationCombos(combo for combo in combos if combo.issubset(dizhis))


def discover(dizhis: Sequence[Dizhi], *,
             anhe_def: DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED,
             xing_def: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> DizhiRelationDiscovery:
  '''
  Discover all possible Dizhi combos of all `DizhiRelation`s (SANHUI, LIUHE, XING...) in the given `dizhis`.
  This method further invokes `search`.

  返回给定地支中所有可能的地支关系组合（三会、六合、刑等）。
  这个方法通过调用 `search` 来实现。

  Note:
  - It is possible that some `DizhiRelation`s are not in the returned frozendict as keys.
  - 返回的字典的键中可能不包含所有的 `DizhiRelation`。

  Note:
  - `anhe_def` / `xing_def` are forwarded to `search` -- defaults, table picking, and
    batch-entry semantics (direction unobservable): see `search`.
  - 参数原样转给 `search`——默认值、选表、批量入口语义（方向不可观测）：见 `search`。

  Args:
  - dizhis: (Sequence[Dizhi]) The Dizhis to check.
  - anhe_def: (DizhiRules.AnheDef) The ANHE definition, forwarded to `search`.
  - xing_def: (DizhiRules.XingDef) The XING definition, forwarded to `search`.

  Return: (DizhiRelationDiscovery) The result containing all matching Dizhi combos. Note that returned combos don't reveal the directions.
  '''

  if not all(isinstance(dz, Dizhi) for dz in dizhis):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis]}')
  if not isinstance(anhe_def, DizhiRules.AnheDef):
    raise TypeError(f'Expected AnheDef, got {type(anhe_def)}')
  if not isinstance(xing_def, DizhiRules.XingDef):
    raise TypeError(f'Expected XingDef, got {type(xing_def)}')
  return DizhiRelationDiscovery({
    rel : result
    for rel in DizhiRelation
    if len(result := search(dizhis, rel, anhe_def=anhe_def, xing_def=xing_def)) > 0
  })


def search_ganzhis(ganzhis: Sequence[Ganzhi], relation: DizhiRelation, *,
                    anhe_def: DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED,
                    xing_def: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> GanzhiRelationCombos:
  '''Find the concrete Ganzhi occurrences whose Dizhis satisfy `relation`.
  找出地支满足 `relation` 的具体干支位置组合。

  The zero-based index in the input sequence is the occurrence identity. Equal Ganzhis or
  equal Dizhis at different indices therefore remain distinguishable. For the existing
  position-independent relations, projecting the result to Dizhis is exactly equivalent to
  `search`; position-dependent relations can additionally inspect order and Tiangans here.
  输入序列中的零基序号就是具体出现的身份，因此不同位置的相同干支或地支不会混同。
  对现有不依赖位置的关系，投影到地支后与 `search` 完全等价；依赖位置的关系还可在此读取
  顺序与天干。

  Args:
  - ganzhis: (Sequence[Ganzhi]) The ordered Ganzhis to check.
  - relation: (DizhiRelation) The relation to check.
  - anhe_def: (DizhiRules.AnheDef) The ANHE definition; only consulted for 暗合 queries.
  - xing_def: (DizhiRules.XingDef) The XING definition; only consulted for 刑 queries.

  Return: (GanzhiRelationCombos) All matching concrete occurrence combos.
  '''
  if not isinstance(ganzhis, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(ganzhis)}')
  if not all(isinstance(gz, Ganzhi) for gz in ganzhis):
    raise TypeError(f'Expected all Ganzhi, got {[type(gz) for gz in ganzhis]}')

  dizhis: tuple[Dizhi, ...] = tuple(gz.dizhi for gz in ganzhis)
  occurrences: tuple[GanzhiOccurrence, ...] = tuple(
    GanzhiOccurrence(index, gz) for index, gz in enumerate(ganzhis)
  )

  ret: list[GanzhiRelationCombo] = []
  for combo in search(dizhis, relation, anhe_def=anhe_def, xing_def=xing_def):
    # A self-刑 pair projects to a singleton DizhiCombo; occurrence identity restores
    # its two concrete participants. All other current combos contain distinct Dizhis.
    participant_count: int = 2 if relation is DizhiRelation.刑 and len(combo) == 1 else len(combo)
    ret.extend(
      GanzhiRelationCombo(candidate)
      for candidate in combinations(occurrences, participant_count)
      if DizhiCombo(occurrence.ganzhi.dizhi for occurrence in candidate) == combo
    )
  return GanzhiRelationCombos(ret)


def discover_ganzhis(ganzhis: Sequence[Ganzhi], *,
                      anhe_def: DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED,
                      xing_def: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> GanzhiRelationDiscovery:
  '''Discover every `DizhiRelation` among concrete Ganzhi occurrences while retaining
  their input positions and Tiangans. 保留输入位置与天干，发现具体干支之间的全部地支关系。

  Args:
  - ganzhis: (Sequence[Ganzhi]) The ordered Ganzhis to check.
  - anhe_def: (DizhiRules.AnheDef) The ANHE definition, forwarded to `search_ganzhis`.
  - xing_def: (DizhiRules.XingDef) The XING definition, forwarded to `search_ganzhis`.

  Return: (GanzhiRelationDiscovery) The position-preserving discovery result.
  '''
  if not isinstance(ganzhis, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(ganzhis)}')
  if not all(isinstance(gz, Ganzhi) for gz in ganzhis):
    raise TypeError(f'Expected all Ganzhi, got {[type(gz) for gz in ganzhis]}')
  if not isinstance(anhe_def, DizhiRules.AnheDef):
    raise TypeError(f'Expected AnheDef, got {type(anhe_def)}')
  if not isinstance(xing_def, DizhiRules.XingDef):
    raise TypeError(f'Expected XingDef, got {type(xing_def)}')

  return GanzhiRelationDiscovery({
    rel : result
    for rel in DizhiRelation
    if len(result := search_ganzhis(ganzhis, rel, anhe_def=anhe_def, xing_def=xing_def)) > 0
  })


def discover_mutual(dizhis1: Sequence[Dizhi], dizhis2: Sequence[Dizhi], *,
                     anhe_def: DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED,
                     xing_def: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> DizhiRelationDiscovery:
  '''
  Discover all possible Dizhi combos of all `DizhiRelation`s (SANHUI, LIUHE, XING...) among the given `dizhis1` and `dizhis2`.
  Note that it is required that the Dizhis in a returned combo come from both `dizhis1` and `dizhis2`, which means
  `dizhis1` and `dizhis2` mutually form the combo.

  找出输入的两组地支中所有可能的关系组合（三会、六合、刑等）。
  注意返回的地支组合中的地支必须同时来自两组 `dizhis1` 和 `dizhis2` 中。

  Note:
  - It is possible that some `DizhiRelation`s are not in the returned frozendict as keys.
  - 返回的字典的键中可能不包含所有的 `DizhiRelation`。

  Note:
  - `anhe_def` / `xing_def` are forwarded to `search` -- defaults, table picking, and
    batch-entry semantics (direction unobservable): see `search`.
  - 参数原样转给 `search`——默认值、选表、批量入口语义（方向不可观测）：见 `search`。

  Args:
  - dizhis1: (Sequence[Dizhi]) The first set of Dizhis to check.
  - dizhis2: (Sequence[Dizhi]) The second set of Dizhis to check.
  - anhe_def: (DizhiRules.AnheDef) The ANHE definition, forwarded to `search`.
  - xing_def: (DizhiRules.XingDef) The XING definition, forwarded to `search`.

  Return: (DizhiRelationDiscovery) The result containing all matching Dizhi combos. Note that returned combos don't reveal the directions.
  
  Examples:
  - discover_mutual([子], [丑])
    - return: {
      DizhiRelation.六合: DizhiRelationCombos({子, 丑},),
      DizhiRelation.克: DizhiRelationCombos({子, 丑},)
    }
  - discover_mutual([子, 丑], [])
    - return: {} // Empty returned frozendict!
  '''

  if not all(isinstance(dz, Dizhi) for dz in dizhis1):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis1]}')
  if not all(isinstance(dz, Dizhi) for dz in dizhis2):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis2]}')
  if not isinstance(anhe_def, DizhiRules.AnheDef):
    raise TypeError(f'Expected AnheDef, got {type(anhe_def)}')
  if not isinstance(xing_def, DizhiRules.XingDef):
    raise TypeError(f'Expected XingDef, got {type(xing_def)}')

  # 自刑 depends on multiplicity (the same Dizhi appearing once on each side forms 自刑),
  # so the two sides CONCATENATE -- a set union would silently break it. Deliberately
  # different from `tiangan_utils.discover_mutual`.
  # 自刑依赖重数（同一地支两侧各现一次也构成自刑），故两侧拼接——集合并会静默破坏
  # 自刑。与天干侧的集合并是刻意分歧。
  return discover(list(dizhis1) + list(dizhis2), anhe_def=anhe_def, xing_def=xing_def).mutual_only(set(dizhis1), set(dizhis2))
