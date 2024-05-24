# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from collections import Counter
from typing import Sequence, Optional, Final

from ..Common import frozendict
from ..Defines import Dizhi, Wuxing, DizhiRelation
from ..Rules import DizhiRules


'''
Functions in this file are used to find all possible Dizhi combos that satisfy different `DizhiRelation`s.
All methods' returns are expected to be immutable.
'''


'''Represents a Dizhi combo that satisfies a certain `DizhiRelation`.'''
DizhiCombo = frozenset[Dizhi]

'''A list of all possible Dizhi combos that satisfy a certain `DizhiRelation`.'''
DizhiRelationCombos = tuple[DizhiCombo, ...]

'''A frozendict that stores the Dizhi combos that satisfy every `DizhiRelation`.'''
DizhiRelationDiscovery = frozendict[DizhiRelation, DizhiRelationCombos]


def sanhui(dz1: Dizhi, dz2: Dizhi, dz3: Dizhi) -> Optional[Wuxing]:
  '''
  Check if the input Dizhis are in SANHUI (三会) relation. If so, return the corresponding Wuxing. If not, return `None`.
  We don't care the order of the inputs, since SANHUI relation is non-directional/mutual.
  检查输入的地支是否构成三会关系。如果是，返回三会后形成的五行。否则返回 `None`。
  返回结果与输入的地支顺序无关，因为三会关系是无方向的。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.
  - dz3: (Dizhi) The third Dizhi.

  Return: (Optional[Wuxing]) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in SANHUI (三会) relation.

  Examples:
  - sanhui(Dizhi.寅, Dizhi.卯, Dizhi.辰)
    - return: Wuxing.木
  - sanhui(Dizhi.寅, Dizhi.卯, Dizhi.丑)
    - return: None
  '''

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2, dz3))
  combo: DizhiCombo = DizhiCombo((dz1, dz2, dz3))
  return DizhiRules.DIZHI_SANHUI.get(combo, None)


def liuhe(dz1: Dizhi, dz2: Dizhi) -> Optional[Wuxing]:
  '''
  Check if the input Dizhis are in LIUHE (六合) relation. If so, return the corresponding Wuxing. If not, return `None`.
  We don't care the order of the inputs, since LIUHE relation is non-directional/mutual.
  检查输入的地支是否构成六合关系。如果是，返回六合后形成的五行。否则返回 `None`。
  返回结果与输入的地支顺序无关，因为六合关系是无方向的。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (Optional[Wuxing]) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in LIUHE (六合) relation.

  Examples:
  - liuhe(Dizhi.寅, Dizhi.亥)
    - return: Wuxing.木
  - liuhe(Dizhi.寅, Dizhi.辰)
    - return: None
  '''

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
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

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
  assert isinstance(definition, DizhiRules.AnheDef)
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

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
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
  - tonghe(Dizhi.寅, Dizhi.午)
    - return: True
  - tonghe(Dizhi.寅, Dizhi.丑)
    - return: False
  '''

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
  combo: DizhiCombo = DizhiCombo((dz1, dz2))
  return combo in DizhiRules.DIZHI_TONGLUHE


def sanhe(dz1: Dizhi, dz2: Dizhi, dz3: Dizhi) -> Optional[Wuxing]:
  '''
  Check if the input Dizhis are in SANHE (三合) relation. If so, return the corresponding Wuxing. If not, return `None`.
  检查输入的地支是否构成三合关系。如果是，返回对应的五行。如果不是，返回 `None`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.
  - dz3: (Dizhi) The third Dizhi.

  Return: (Optional[Wuxing]) The corresponding Wuxing if the Dizhis form in SANHE (三合) relation. Otherwise, return `None`.

  Examples:
  - sanhe(Dizhi.亥, Dizhi.卯, Dizhi.未)
    - return: Wuxing.木
  - sanhe(Dizhi.亥, Dizhi.卯, Dizhi.丑)
    - return: None
  '''

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2, dz3))
  combo: DizhiCombo = DizhiCombo((dz1, dz2, dz3))
  return DizhiRules.DIZHI_SANHE.get(combo, None)


def banhe(dz1: Dizhi, dz2: Dizhi) -> Optional[Wuxing]:
  '''
  Check if the input Dizhis are in BANHE (半合) relation. If so, return the corresponding Wuxing. If not, return `None`.
  检查输入的地支是否构成半合关系。如果是，返回对应的五行。如果不是，返回 `None`。

  Args:
  - dz1: (Dizhi) The first Dizhi.
  - dz2: (Dizhi) The second Dizhi.

  Return: (Optional[Wuxing]) The corresponding Wuxing if the Dizhis form in BANHE (半合) relation. Otherwise, return `None`.

  Examples:
  - banhe(Dizhi.亥, Dizhi.卯)
    - return: Wuxing.木
  - banhe(Dizhi.卯, Dizhi.未)
    - return: Wuxing.木
  - banhe(Dizhi.亥, Dizhi.丑)
    - return: None
  '''

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
  combo: DizhiCombo = DizhiCombo((dz1, dz2))
  return DizhiRules.DIZHI_BANHE.get(combo, None)


def xing(*dizhis: Dizhi, definition: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> Optional[DizhiRules.XingSubType]:
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

  Return: (Optional[DizhiRules.XingSubType]) The type of the XING relation if the Dizhis form in XING (刑) relation. Otherwise, return `None`.

  Examples:
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申])
    - return: XingSubType.SANXING
  - xing(*[Dizhi.寅, Dizhi.巳], DizhiRules.XingDef.STRICT)
    - return: None
  - xing(*[Dizhi.寅, Dizhi.巳], DizhiRules.XingDef.LOOSE)
    - return: XingSubType.SANXING
  - xing(Dizhi.午)
    - return: None
  - xing(Dizhi.午, Dizhi.午)
    - return: XingSubType.ZIXING
  - xing(Dizhi.午, DizhiRules.XingDef.LOOSE)
    - return: None
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午]) # Not a exact match.
    - return: None
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午, Dizhi.午]) # Multiple matches.
    - return: None
  '''

  assert all(isinstance(dz, Dizhi) for dz in dizhis)
  assert len(dizhis) <= 3
  assert isinstance(definition, DizhiRules.XingDef)

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

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
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

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
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

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
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
  - sheng(Dizhi.卯, Dizhi.癸)
    - return: False
  - sheng(Dizhi.癸, Dizhi.卯)
    - return: True
  - sheng(Dizhi.丑, Dizhi.子)
    - return: False
  - sheng(Dizhi.丑, Dizhi.午)
    - return: False
  - sheng(Dizhi.午, Dizhi.丑)
    - return: True
  '''

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
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

  assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
  return (dz1, dz2) in DizhiRules.DIZHI_KE


def search(dizhis: Sequence[Dizhi], relation: DizhiRelation) -> DizhiRelationCombos:
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
    - In this method, for 丑未戌 and 寅卯巳 SANXING, it is required that any two of the three to present in order to qualify the XING relation.
    - Use `xing` to do more fine-grained checking.
  - 返回的 combos 中没有体现关系作用的方向。
  - 比如说，如果检查输入地支的相生关系并返回 ({午, 寅})，那么不能从返回结果中看出是寅生午还是午生寅。
  - 对于无方向的关系来说（合、会），我们不用关心返回结果中的方向。
  - 对于有方向的关系来说（生、克等），请使用其他方法来检查（如 `sheng`， `ke` 等）。
  - 对于刑关系，更复杂一些：
    - 对于辰午酉亥自刑，只需要同时出现两次就满足相刑关系。
    - 对于子卯相刑，只需要子、卯都出现就满足相刑关系。
    - 对于丑未戌、寅巳申三刑，有的看法认为需要三个地支同时出现才算刑，有的看法认为只需要出现两个也算相刑。
    - 本方法的实现中，对于丑未戌、寅巳申三刑，只需要同时出现两个地支就算相刑。
    - 请使用 `xing` 来进行更细粒度的检查。

  Note:
  - For ANHE relation, the `DizhiRules.AnheDef.NORMAL_EXTENDED` definition is used, as it is the widest definition.
  - 对于暗合关系的查询，默认使用 `DizhiRules.AnheDef.NORMAL_EXTENDED` 定义，因为它包含最多的暗合地支组合。

  Note:
  - For XING relation, all Dizhis should appear in order to qualify the XING relation.
  - `DizhiRules.XingDef.NORMAL` definition is used.
  - e.g., if only 丑 and 未 appear in the input, then the XING relation is not satisfied (戌 missing).
  - 对于刑关系，所有的地支都出现才能满足相刑关系。
  - 默认使用 `DizhiRules.XingDef.NORMAL` 定义。
  - 举例来说，如果输入中只有丑、未，那么不符合相刑关系（缺少戌）。

  Args:
  - dizhis: (Sequence[Dizhi]) The Dizhis to check.
  - relation: (DizhiRelation) The relation to check.

  Return: (DizhiRelationCombos) The result containing all matching Dizhi combos.

  Examples:
  - search([Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.午, Dizhi.未], DizhiRelation.三会)
    - return: ({Dizhi.寅, Dizhi.卯, Dizhi.辰})
  - search([Dizhi.寅, Dizhi.卯, Dizhi.丑, Dizhi.午, Dizhi.申], DizhiRelation.暗合)
    - return: ({ Dizhi.卯, Dizhi.申}, { Dizhi.寅, Dizhi.午}, { Dizhi.寅, Dizhi.丑})
    - `DizhiRules.AnheDef.NORMAL_EXTENDED` is used.
  - search([Dizhi.寅,Dizhi.巳, Dizhi.申, Dizhi.辰], DizhiRelation.刑)
    - return: ({ Dizhi.寅, Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.巳 }, { Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.申 })
    - Only one 辰 appears in the input - not forming a XING relation.
  - search([Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.辰, Dizhi.辰], DizhiRelation.刑)
    - return: ({ Dizhi.寅, Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.巳 }, { Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.申 }, { Dizhi.辰 }) # Only one 辰 in the returned set!
    - 辰 appear twice in the input - forming a XING relation.
  - search([Dizhi.卯, Dizhi.子, Dizhi.寅, Dizhi.巳], DizhiRelation.刑)
    - return: ({ Dizhi.子, Dizhi.卯}, { Dizhi.寅, Dizhi.巳 })
    - `DizhiRules.XingDef.LOOSE` is used.
  '''

  assert isinstance(relation, DizhiRelation), f'Unexpected type of relation: {type(relation)}'
  assert isinstance(dizhis, Sequence), "Non-sequence input loses the info of Dizhis' frequency."
  assert all(isinstance(dz, Dizhi) for dz in dizhis)

  if relation is DizhiRelation.三会:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_SANHUI if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.六合:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_LIUHE if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.暗合:
    anhe_table: frozenset[DizhiCombo] = DizhiRules.DIZHI_ANHE[DizhiRules.AnheDef.NORMAL_EXTENDED] # Use `NORMAL_EXTENDED` here, which has the widest definition.
    return DizhiRelationCombos(combo for combo in anhe_table if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.通合:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_TONGHE if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.通禄合:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_TONGLUHE if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.三合:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_SANHE if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.半合:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_BANHE if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.刑:
    dz_counter: Counter[Dizhi] = Counter(dizhis)

    ret: set[DizhiCombo] = set()
    for xing_tuple in DizhiRules.DIZHI_XING[DizhiRules.XingDef.LOOSE]:
      # Sadly direct comparisons not implemented on `Counter` with Python 3.9.
      # Otherwise we can use `dz_counter >= Counter(xing_tuple)` here.
      xing_dz_counter: Counter[Dizhi] = Counter(xing_tuple)
      if dz_counter & xing_dz_counter == xing_dz_counter:
        ret.add(DizhiCombo(xing_tuple))

    return DizhiRelationCombos(ret)
  
  elif relation is DizhiRelation.冲:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_CHONG if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.破:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_PO if combo.issubset(dizhis))
  
  elif relation is DizhiRelation.害:
    return DizhiRelationCombos(combo for combo in DizhiRules.DIZHI_HAI if combo.issubset(dizhis))

  # Else, `relation` must be `生` or `克`.
  assert relation is DizhiRelation.生 or relation is DizhiRelation.克
  rules: frozenset[tuple[Dizhi, Dizhi]] = DizhiRules.DIZHI_KE if relation is DizhiRelation.克 else DizhiRules.DIZHI_SHENG
  frozen_rules: frozenset[DizhiCombo] = frozenset(map(DizhiCombo, rules))
  dz_set: set[Dizhi] = set(dizhis)
  return DizhiRelationCombos(combo for combo in frozen_rules if all(dz in dz_set for dz in combo))


def discover(dizhis: Sequence[Dizhi]) -> DizhiRelationDiscovery:
  '''
  Discover all possible Dizhi combos of all `DizhiRelation`s (SANHUI, LIUHE, XING...) in the given `dizhis`.
  This method further invokes `search`.

  返回给定地支中所有可能的地支关系组合（三会、六合、刑等）。
  这个方法通过调用 `search` 来实现。

  Note:
  - The returned frozendict has all `DizhiRelation` keys, but some values may be empty.
  - 返回的字典的键为所有的 `DizhiRelation`，但返回字典的某些值可能为空（即 `DizhiRelationCombos` 可能为空）。

  Note:
  - For XING relation, `XingDef.LOOSE` is used; For ANHE relation, `AnheDef.NORMAL_EXTENDED` is used.
  - 对于相刑的关系，使用 `XingDef.LOOSE` 模式。对于暗合的关系，使用 `AnheDef.NORMAL_EXTENDED` 模式。

  Args:
  - dizhis: (Sequence[Dizhi]) The Dizhis to check.

  Return: (DizhiRelationDiscovery) The result containing all matching Dizhi combos. Note that returned combos don't reveal the directions.
  '''

  assert all(isinstance(dz, Dizhi) for dz in dizhis)
  return frozendict({
    rel : search(dizhis, rel) for rel in DizhiRelation
  })


def discover_mutual(dizhis1: Sequence[Dizhi], dizhis2: Sequence[Dizhi]) -> DizhiRelationDiscovery:
  '''
  Discover all possible Dizhi combos of all `DizhiRelation`s (SANHUI, LIUHE, XING...) among the given `dizhis1` and `dizhis2`.
  Note that it is required that the Dizhis in a returned combo come from both `dizhis1` and `dizhis2`, which means
  `dizhis1` and `dizhis2` mutually form the combo.

  找出输入的两组地支中所有可能的关系组合（三会、六合、刑等）。
  注意返回的地支组合中的地支必须同时来自两组 `dizhis1` 和 `dizhis2` 中。

  Note:
  - For XING relation, `XingDef.LOOSE` is used; For ANHE relation, `AnheDef.NORMAL_EXTENDED` is used.
  - 对于相刑的关系，使用 `XingDef.LOOSE` 模式。对于暗合的关系，使用 `AnheDef.NORMAL_EXTENDED` 模式。

  Args:
  - dizhis1: (Sequence[Dizhi]) The first set of Dizhis to check.
  - dizhis2: (Sequence[Dizhi]) The second set of Dizhis to check.

  Return: (DizhiRelationDiscovery) The result containing all matching Dizhi combos. Note that returned combos don't reveal the directions.
  
  Examples:
  - discover_mutual([子], [丑])
    - return: {
      DizhiRelation.合: DizhiRelationCombos({子, 丑},),
      DizhiRelation.冲: DizhiRelationCombos(), // empty
      DizhiRelation.生: DizhiRelationCombos(), // empty
      DizhiRelation.克: DizhiRelationCombos({子, 丑},)
      DizhiRelation.刑: DizhiRelationCombos(), // empty
      // ... and other empty DizhiRelationCombos...
    }
  - discover_mutual([子, 丑], [])
    - return: {
      DizhiRelation.合: DizhiRelationCombos(), // empty
      DizhiRelation.冲: DizhiRelationCombos(), // empty
      DizhiRelation.生: DizhiRelationCombos(), // empty
      DizhiRelation.克: DizhiRelationCombos(), // empty
      DizhiRelation.刑: DizhiRelationCombos(), // empty
      // ... and so on
    }
  '''

  assert all(isinstance(dz, Dizhi) for dz in dizhis1)
  assert all(isinstance(dz, Dizhi) for dz in dizhis2)
  
  dz1_set: Final[set[Dizhi]] = set(dizhis1)
  dz2_set: Final[set[Dizhi]] = set(dizhis2)

  def __is_valid(combo: DizhiCombo) -> bool:
    if combo.isdisjoint(dz1_set): # This means Dizhis in `combo` are all from `dizhis2`.
      return False
    if combo.isdisjoint(dz2_set): # This means Dizhis in `combo` are all from `dizhis1`.
      return False
    return True
  
  # Discover all possible combos with `dz1_set` and `dz2_set` combined.
  # Check each combo's validity and only keep valid ones.
  return frozendict({
    rel : DizhiRelationCombos(filter(__is_valid, combos))
    for rel, combos in discover(list(dizhis1) + list(dizhis2)).items()
  })
