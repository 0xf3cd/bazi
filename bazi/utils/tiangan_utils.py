# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Final
from collections.abc import Sequence

from ..defines import Tiangan, Wuxing, TianganRelation
from ..rules import TianganRules
from .relation_discovery import RelationDiscovery


'''
Functions in this file are used to find all possible Tiangan combos that satisfy different `TianganRelation`s.
All methods' returns are expected to be immutable.
'''


'''Represents a Tiangan combo that satisfies a certain `TianganRelation`.'''
TianganCombo = frozenset[Tiangan]

'''A list of all possible Tiangan combos that satisfy a certain `TianganRelation`.'''
TianganRelationCombos = tuple[TianganCombo, ...]

class TianganRelationDiscovery(RelationDiscovery[TianganRelation, Tiangan]):
  '''A frozen mapping from `TianganRelation` to the Tiangan combos that satisfy it.
  天干关系到满足它的天干组合的冻结映射。'''


def he(tg1: Tiangan, tg2: Tiangan) -> Wuxing | None:
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

  Return: (Wuxing | None) The Wuxing that the two Tiangans form, or `None` if the two Tiangans are not in HE relation.

  Examples:
  - he(Tiangan.甲, Tiangan.丙):
    - return: None
  - he(Tiangan.甲, Tiangan.己):
    - return: Wuxing("土")
  - he(Tiangan.己, Tiangan.甲):
    - return: Wuxing("土")
  '''

  if not isinstance(tg1, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg1)}')
  if not isinstance(tg2, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg2)}')

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

  if not isinstance(tg1, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg1)}')
  if not isinstance(tg2, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg2)}')
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

  if not isinstance(tg1, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg1)}')
  if not isinstance(tg2, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg2)}')
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

  if not isinstance(tg1, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg1)}')
  if not isinstance(tg2, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg2)}')
  return (tg1, tg2) in TianganRules.TIANGAN_KE


def search(tiangans: Sequence[Tiangan], relation: TianganRelation) -> TianganRelationCombos:
  '''
  返回 `tiangans` 中所有满足该关系的组合。

  Note:
  - 只接受 `Sequence`，非序列在遍历前抛出 `TypeError`；空序列合法，重复天干不影响结果。
  - 返回的 combos 中没有体现关系作用的方向。
  - 比如说，如果检查输入天干的相生关系并返回 ({甲, 丁},)，那么不能从返回结果中看出是甲生丁还是丁生甲。
  - 对于无方向的关系来说（合、冲），我们不用关心返回结果中的方向。
  - 对于有方向的关系来说（生、克），请使用其他方法来检查（如 `.sheng` 和 `.ke`）。

  Args:
  - tiangans: (Sequence[Tiangan]) 待查天干。
  - relation: (TianganRelation) 待查关系。

  Return: (TianganRelationCombos) 所有匹配组合，不包含作用方向。

  Examples:
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.合):
    - return: ({丙, 辛})
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.冲):
    - return: ({甲, 庚})
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.生):
    - return: ({甲, 丙}, {甲, 丁})
    - 返回组合不包含方向。
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.克):
    - return: ({甲, 庚}, {甲, 辛}, {丙, 庚}, {丙, 辛},
               {丁, 庚}, {丁, 辛})
    - 返回组合不包含方向。
  '''

  if not isinstance(tiangans, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(tiangans)}')
  if not isinstance(relation, TianganRelation):
    raise TypeError(f'Expected TianganRelation, got {type(relation)}')
  if not all(isinstance(tg, Tiangan) for tg in tiangans):
    raise TypeError(f'Expected all Tiangan, got {[type(tg) for tg in tiangans]}')

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
  返回给定天干中所有可能的天干关系组合（合、冲、生、克等）。
  这个方法通过调用 `search` 来实现。

  Note:
  - 返回的字典的键中可能不包含所有的 `TianganRelation`。
  - 只接受 `Sequence`，非序列在遍历前抛出 `TypeError`；空序列合法，重复天干不影响结果。

  Args:
  - tiangans: (Sequence[Tiangan]) 待查天干。

  Return: (TianganRelationDiscovery) 所有匹配组合的冻结映射，不包含作用方向。
  '''

  if not isinstance(tiangans, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(tiangans)}')
  if not all(isinstance(tg, Tiangan) for tg in tiangans):
    raise TypeError(f'Expected all Tiangan, got {[type(tg) for tg in tiangans]}')
  return TianganRelationDiscovery({
    rel : result
    for rel in TianganRelation
    if len(result := search(tiangans, rel)) > 0
  })


def discover_mutual(tiangans1: Sequence[Tiangan], tiangans2: Sequence[Tiangan]) -> TianganRelationDiscovery:
  '''
  找出输入的两组天干中的所有可能的关系组合（合、冲、生、克等）。
  注意返回的天干组合中的天干必须同时来自两组 `tiangans1` 和 `tiangans2` 中。

  Note:
  - 返回的字典的键中可能不包含所有的 `TianganRelation`。
  - 两组输入都须为 `Sequence`，在遍历任一组前检查；重复天干不影响结果。

  Args:
  - tiangans1: (Sequence[Tiangan]) 第一组天干。
  - tiangans2: (Sequence[Tiangan]) 第二组天干。

  Return: (TianganRelationDiscovery) 跨组匹配组合的冻结映射，不包含作用方向。
  
  Examples:
  - discover_mutual([甲], [己])
    - return: {
      TianganRelation.合: TianganRelationCombos({甲, 己},),
      TianganRelation.克: TianganRelationCombos({甲, 己},)
    }
  - discover_mutual([甲, 己], [])
    - return: {} // 空的冻结映射。
  '''

  if not isinstance(tiangans1, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(tiangans1)}')
  if not isinstance(tiangans2, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(tiangans2)}')
  if not all(isinstance(tg, Tiangan) for tg in tiangans1):
    raise TypeError(f'Expected all Tiangan, got {[type(tg) for tg in tiangans1]}')
  if not all(isinstance(tg, Tiangan) for tg in tiangans2):
    raise TypeError(f'Expected all Tiangan, got {[type(tg) for tg in tiangans2]}')

  tg1_set: Final[set[Tiangan]] = set(tiangans1)
  tg2_set: Final[set[Tiangan]] = set(tiangans2)

  # Tiangan relations are multiplicity-blind, so the two sides combine by set union.
  # Deliberately different from `dizhi_utils.discover_mutual`, which CONCATENATES the
  # inputs because 自刑 there depends on multiplicity.
  # 天干关系不看重数，两侧集合并即可——与地支侧的拼接是刻意分歧（自刑依赖重数）。
  return discover(list(tg1_set | tg2_set)).mutual_only(tg1_set, tg2_set)
