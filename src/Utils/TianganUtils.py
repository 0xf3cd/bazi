# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Sequence, Optional, Final

from ..Defines import Tiangan, Wuxing, TianganRelation
from ..Common import frozendict
from ..Rules import TianganRules


'''
Functions in this file are used to find all possible Tiangan combos that satisfy different `TianganRelation`s.
All methods' returns are expected to be immutable.
'''


'''Represents a Tiangan combo that satisfies a certain `TianganRelation`.'''
TianganCombo = frozenset[Tiangan]

'''A list of all possible Tiangan combos that satisfy a certain `TianganRelation`.'''
TianganRelationCombos = tuple[TianganCombo, ...]

'''A frozendict that stores the Tiangan combos that satisfy every `TianganRelation`.'''
TianganRelationDiscovery = frozendict[TianganRelation, TianganRelationCombos]


def he(tg1: Tiangan, tg2: Tiangan) -> Optional[Wuxing]:
  '''
  Check if the input two Tiangans are in HE relation. If so, return the corresponding Wuxing. If not, return `None`.
  We don't care the order of the inputs, since HE relation is non-directional/mutual.
  检查输入的两个天干是否构成相合关系。如果是，返回合化后形成的五行。如果不是，返回 `None`。
  返回结果与输入的天干顺序无关，因为相合关系是无方向的。

  Note that the two Tiangans may not qualify for Hehua (合化), which depends on the bazi chart.
  注意，这两个天干可能并不能合化。具体需要根据八字原盘来决定。

  Args:
  - tg1: (Tiangan) The first Tiangan.
  - tg2: (Tiangan) The second Tiangan.

  Return: (Optional[Wuxing]) The Wuxing that the two Tiangans form, or `None` if the two Tiangans are not in HE relation.

  Examples:
  - he(Tiangan.甲, Tiangan.丙):
    - return: None
  - he(Tiangan.甲, Tiangan.己):
    - return: Wuxing("土")
  - he(Tiangan.己, Tiangan.甲):
    - return: Wuxing("土")
  '''

  assert isinstance(tg1, Tiangan)
  assert isinstance(tg2, Tiangan)

  fs: TianganCombo = TianganCombo((tg1, tg2))
  if fs in TianganRules.TIANGAN_HE:
    return TianganRules.TIANGAN_HE[fs]
  return None


def chong(tg1: Tiangan, tg2: Tiangan) -> bool:
  '''
  Check if the input two Tiangans are in CHONG relation.
  We don't care the order of the inputs, since CHONG relation is non-directional/mutual.
  检查输入的两个天干是否构成相冲关系。
  返回结果与输入的天干顺序无关，因为相冲关系是无方向的。

  Args:
  - tg1: (Tiangan) The first Tiangan.
  - tg2: (Tiangan) The second Tiangan.

  Return: (bool) Whether the two Tiangans are in CHONG relation.

  Examples:
  - chong(Tiangan.甲, Tiangan.丙):
    - return: False
  - chong(Tiangan.甲, Tiangan.庚):
    - return: True
  - chong(Tiangan.庚, Tiangan.甲):
    - return: True
  '''

  assert isinstance(tg1, Tiangan)
  assert isinstance(tg2, Tiangan)
  return TianganCombo((tg1, tg2)) in TianganRules.TIANGAN_CHONG


def sheng(tg1: Tiangan, tg2: Tiangan) -> bool:
  '''
  Check if the input two Tiangans are in SHENG relation.
  The order of the inputs is important, since SHENG relation is uni-directional.
  检查输入的两个天干是否构成相生关系。
  返回结果与输入的天干顺序有关，因为相生关系是单向的。

  Args:
  - tg1: (Tiangan) The first Tiangan.
  - tg2: (Tiangan) The second Tiangan.

  Return: (bool) Whether the two Tiangans are in SHENG relation.

  Examples:
  - sheng(Tiangan.甲, Tiangan.丙):
    - return: True
  - sheng(Tiangan.丙, Tiangan.甲):
    - return: False
  - sheng(Tiangan.庚, Tiangan.甲):
    - return: False
  '''

  assert isinstance(tg1, Tiangan)
  assert isinstance(tg2, Tiangan)
  return (tg1, tg2) in TianganRules.TIANGAN_SHENG


def ke(tg1: Tiangan, tg2: Tiangan) -> bool:
  '''
  Check if the input two Tiangans are in KE relation.
  The order of the inputs is important, since KE relation is uni-directional.
  检查输入的两个天干是否构成相克关系。
  返回结果与输入的天干顺序有关，因为相克关系是单向的。

  Args:
  - tg1: (Tiangan) The first Tiangan.
  - tg2: (Tiangan) The second Tiangan.

  Return: (bool) Whether the two Tiangans are in KE relation.

  Examples:
  - ke(Tiangan.甲, Tiangan.丙):
    - return: False
  - ke(Tiangan.甲, Tiangan.庚):
    - return: False
  - ke(Tiangan.庚, Tiangan.甲):
    - return: True
  '''

  assert isinstance(tg1, Tiangan)
  assert isinstance(tg2, Tiangan)
  return (tg1, tg2) in TianganRules.TIANGAN_KE


def search(tiangans: Sequence[Tiangan], relation: TianganRelation) -> TianganRelationCombos:
  '''
  Find all possible Tiangan combos in the given `tiangans` that satisfy the `relation`.
  返回 `tiangans` 中所有满足该关系的组合。

  Note:
  - The returned combos don't reveal the directions.
  - For example, if the returned value for SHENG relation is ({甲, 丁},), then we are unable to infer it is 甲 that generates 丁 or 丁 that generates 甲.
  - For mutual/non-directional relations (e.g. HE and CHONG), that's fine, because we don't care about the direction.
  - For uni-directional relations, please use other methods in this class to check that (e.g. `.sheng` and `.ke`). 
  - 返回的 combos 中没有体现关系作用的方向。
  - 比如说，如果检查输入天干的相生关系并返回 ({甲, 丁},)，那么不能从返回结果中看出是甲生丁还是丁生甲。
  - 对于无方向的关系来说（合、冲），我们不用关心返回结果中的方向。
  - 对于有方向的关系来说（生、克），请使用其他方法来检查（如 `.sheng` 和 `.ke`）。

  Args:
  - tiangans: (Sequence[Tiangan]) The Tiangans to check.
  - relation: (TianganRelation) The relation to check.

  Return: (TianganRelationCombos) The result containing all matching Tiangan combos. Note that returned combos don't reveal the directions.

  Examples:
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.合):
    - return: ({丙, 辛})
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.冲):
    - return: ({甲, 庚})
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.生):
    - return: ({甲, 丙}, {甲, 丁})
    - Note that the returned combos don't contain the direction.
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.克):
    - return: ({甲, 庚}, {甲, 辛}, {丙, 庚}, {丙, 辛},
               {丁, 庚}, {丁, 辛})
    - Note that the returned combos don't contain the direction.
  '''

  assert isinstance(relation, TianganRelation)
  assert all(isinstance(tg, Tiangan) for tg in tiangans)

  if relation is TianganRelation.合:
    return TianganRelationCombos(combo for combo in TianganRules.TIANGAN_HE if combo.issubset(tiangans))
  elif relation is TianganRelation.冲:
    return TianganRelationCombos(combo for combo in TianganRules.TIANGAN_CHONG if combo.issubset(tiangans))
  
  # Otherwise, relation is `TianganRelation.生` or `TianganRelation.克`.
  tg_set: Final[set[Tiangan]] = set(tiangans)

  if relation is TianganRelation.生:
    return TianganRelationCombos(TianganCombo(combo) for combo in TianganRules.TIANGAN_SHENG if tg_set.issuperset(combo))
  else: 
    assert relation is TianganRelation.克
    return TianganRelationCombos(TianganCombo(combo) for combo in TianganRules.TIANGAN_KE if tg_set.issuperset(combo))


def discover(tiangans: Sequence[Tiangan]) -> TianganRelationDiscovery:
  '''
  Discover all possible Tiangan combos (HE, CHONG, SHENG, KE...) in the given `tiangans`.
  This method further invokes `search`.

  返回给定天干中所有可能的天干关系组合（合、冲、生、克等）。
  这个方法通过调用 `search` 来实现。

  Note:
  - It is possible that some `TianganRelation`s are not in the returned frozendict as keys.
  - 返回的字典的键中可能不包含所有的 `TianganRelation`。

  Args:
  - tiangans: (Sequence[Tiangan]) The Tiangans to check.

  Return: (TianganRelationDiscovery) The result containing all matching Tiangan combos. Note that returned combos don't reveal the directions.
  '''

  assert all(isinstance(tg, Tiangan) for tg in tiangans)
  return frozendict({
    rel : result
    for rel in TianganRelation
    if len(result := search(tiangans, rel)) > 0
  })


def discover_mutual(tiangans1: Sequence[Tiangan], tiangans2: Sequence[Tiangan]) -> TianganRelationDiscovery:
  '''
  Discover all possible Tiangan combos (HE, CHONG, SHENG, KE...) among the given `tiangans1` and `tiangans2`.
  Note that it is required that the Tiangans in a returned combo come from both `tiangans1` and `tiangans2`, which means
  `tiangans1` and `tiangans2` mutually form the combo.

  找出输入的两组天干中的所有可能的关系组合（合、冲、生、克等）。
  注意返回的天干组合中的天干必须同时来自两组 `tiangans1` 和 `tiangans2` 中。

  Note:
  - It is possible that some `TianganRelation`s are not in the returned frozendict as keys.
  - 返回的字典的键中可能不包含所有的 `TianganRelation`。

  Args:
  - tiangans1: (Sequence[Tiangan]) The first set of Tiangans to check.
  - tiangans2: (Sequence[Tiangan]) The second set of Tiangans to check.

  Return: (TianganRelationDiscovery) The result containing all matching Tiangan combos. Note that returned combos don't reveal the directions.
  
  Examples:
  - discover_mutual([甲], [己])
    - return: {
      TianganRelation.合: TianganRelationCombos({甲, 己},),
      TianganRelation.克: TianganRelationCombos({甲, 己},)
    }
  - discover_mutual([甲, 己], [])
    - return: {} // Empty returned frozendict!
  '''

  assert all(isinstance(tg, Tiangan) for tg in tiangans1)
  assert all(isinstance(tg, Tiangan) for tg in tiangans2)

  tg1_set: Final[set[Tiangan]] = set(tiangans1)
  tg2_set: Final[set[Tiangan]] = set(tiangans2)

  def __is_valid(combo: TianganCombo) -> bool:
    if combo.isdisjoint(tg1_set): # This means Tiangans in `combo` are all from `tiangans2`.
      return False
    if combo.isdisjoint(tg2_set): # This means Tiangans in `combo` are all from `tiangans1`.
      return False
    return True

  # Discover all possible combos with `tg1_set` and `tg2_set` combined.
  # Check each combo's validity and only keep valid ones.
  return frozendict({
    rel : result
    for rel, combos in discover(list(tg1_set | tg2_set)).items()
    if len(result := TianganRelationCombos(filter(__is_valid, combos))) > 0
  })
