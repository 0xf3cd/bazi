# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Final
from collections.abc import Sequence

from ..common import frozendict
from ..defines import Tiangan, Wuxing, TianganRelation
from ..rules import TianganRules
from .relation_discovery import RelationDiscovery, _ordered_relation_pairs


'''
查询满足各 TianganRelation 的天干组合；返回结果不可变。
'''


'''满足某天干关系的一个组合。'''
TianganCombo = frozenset[Tiangan]

'''满足某天干关系的全部组合元组。'''
TianganRelationCombos = tuple[TianganCombo, ...]

class TianganRelationDiscovery(RelationDiscovery[TianganRelation, Tiangan]):
  '''天干关系到满足它的天干组合的冻结映射。'''


def he(tg1: Tiangan, tg2: Tiangan) -> Wuxing | None:
  '''
  按无向相合关系查对应五行，不相合时返回 None。
  本函数不判断实际合化条件；能否合化仍须结合原盘。

  Args:
  - tg1: (Tiangan) 第一天干。
  - tg2: (Tiangan) 第二天干。

  Return: (Wuxing | None) 合所对应的五行；不相合时为 None，不据此判定实际合化。

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
  检查输入的两个天干是否构成相冲关系。
  返回结果与输入的天干顺序无关，因为相冲关系是无方向的。

  Args:
  - tg1: (Tiangan) 第一天干。
  - tg2: (Tiangan) 第二天干。

  Return: (bool) 是否相冲。

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
  检查输入的两个天干是否构成相生关系。
  返回结果与输入的天干顺序有关，因为相生关系是单向的。

  Args:
  - tg1: (Tiangan) 生的一方。
  - tg2: (Tiangan) 被生的一方。

  Return: (bool) 是否 tg1 生 tg2。

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
  检查输入的两个天干是否构成相克关系。
  返回结果与输入的天干顺序有关，因为相克关系是单向的。

  Args:
  - tg1: (Tiangan) 克的一方。
  - tg2: (Tiangan) 被克的一方。

  Return: (bool) 是否 tg1 克 tg2。

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


_SEARCH_COMBOS: Final[frozendict[TianganRelation, TianganRelationCombos]] = frozendict({
  TianganRelation.合: tuple(TianganRules.TIANGAN_HE),
  TianganRelation.冲: tuple(sorted(TianganRules.TIANGAN_CHONG, key=lambda combo: tuple(sorted(tg.index for tg in combo)))),
  TianganRelation.生: _ordered_relation_pairs(TianganRules.TIANGAN_SHENG),
  TianganRelation.克: _ordered_relation_pairs(TianganRules.TIANGAN_KE),
})


def search(tiangans: Sequence[Tiangan], relation: TianganRelation) -> TianganRelationCombos:
  '''
  返回 `tiangans` 中所有满足该关系的组合。

  Note:
  - 只接受 `Sequence`，非序列在遍历前抛出 `TypeError`；空序列合法，重复天干不影响结果。
  - 组合不含作用方向，合、冲本身无向；生、克的方向用 sheng / ke 单独判断。
    例如组合 {甲, 丁} 本身不表示甲生丁或丁生甲。

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
  - search([甲, 丙, 丁, 庚, 辛], TianganRelation.克):
    - return: ({丙, 庚}, {丙, 辛}, {丁, 庚}, {丁, 辛},
               {甲, 庚}, {甲, 辛})
  '''

  if not isinstance(tiangans, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(tiangans)}')
  if not isinstance(relation, TianganRelation):
    raise TypeError(f'Expected TianganRelation, got {type(relation)}')
  if not all(isinstance(tg, Tiangan) for tg in tiangans):
    raise TypeError(f'Expected all Tiangan, got {[type(tg) for tg in tiangans]}')

  if relation not in _SEARCH_COMBOS:
    raise ValueError(f'Unsupported TianganRelation: {relation}') # pragma: no cover # 当前全部枚举成员均在表内。

  tg_set: Final[set[Tiangan]] = set(tiangans)
  return TianganRelationCombos(combo for combo in _SEARCH_COMBOS[relation] if combo.issubset(tg_set))


def discover(tiangans: Sequence[Tiangan]) -> TianganRelationDiscovery:
  '''
  返回给定天干中所有可能的天干关系组合（合、冲、生、克等）。
  各关系由 `search` 求值。

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
  返回组合须与两组天干值集均相交，不追踪具体出现；按值过滤语义见 RelationDiscovery.mutual_only。

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

  # 天干关系不看重数，两侧取集合并；地支侧须拼接，因为自刑依赖重数。
  return discover(list(tg1_set | tg2_set)).mutual_only(tg1_set, tg2_set)
