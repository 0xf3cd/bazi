# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Sequence, Optional

from ..Defines import Tiangan, Wuxing, TianganRelation
from ..Rules import Rules


class TianganUtils:
  '''
  This class is used to find all possible Tiangan combos that satisfy different `TianganRelation`s.
  All methods' returns are expected to be immutable.
  '''

  @staticmethod
  def search(tiangans: Sequence[Tiangan], relation: TianganRelation) -> tuple[frozenset[Tiangan], ...]:
    '''
    Find all possible Tiangan combos in the given `tiangans` that satisfy the `relation`.
    返回 `tiangans` 中所有满足该关系的组合。

    Note:
    - The returned frozensets don't reveal the directions.
    - For example, if the returned value for SHENG relation is ({甲, 丁},), then we are unable to infer it is 甲 that generates 丁 or 丁 that generates 甲.
    - For mutual/non-directional relations (e.g. HE and CHONG), that's fine, because we don't care about the direction.
    - For uni-directional relations, please use other static methods in this class to check that (e.g. `TianganUtils.sheng` and `TianganUtils.ke`). 
    - 返回的 frozensets 中没有体现关系作用的方向。
    - 比如说，如果检查输入天干的相生关系并返回 ({甲, 丁},)，那么不能从返回结果中看出是甲生丁还是丁生甲。
    - 对于无方向的关系来说（合、冲），我们不用关心返回结果中的方向。
    - 对于有方向的关系来说（生、克），请使用其他静态方法来检查（如 `TianganUtils.sheng` 和 `TianganUtils.ke`）。

    Args:
    - tiangans: (Sequence[Tiangan]) The Tiangans to check.
    - relation: (TianganRelation) The relation to check.

    Return: (list[frozenset[Tiangan]]) The result containing all matching Tiangan combos. Note that returned frozensets don't reveal the directions.

    Examples:
    - search([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.合):
      - return: ({Tiangan.丙, Tiangan.辛})
    - search([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.冲):
      - return: ({Tiangan.甲, Tiangan.庚})
    - search([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.生):
      - return: ({Tiangan.甲, Tiangan.丙}, {Tiangan.甲, Tiangan.丁})
      - Note that the returned frozensets don't contain the direction.
    - search([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.克):
      - return: ({Tiangan.甲, Tiangan.庚}, {Tiangan.甲, Tiangan.辛}, {Tiangan.丙, Tiangan.庚}, {Tiangan.丙, Tiangan.辛},
                 {Tiangan.丁, Tiangan.庚}, {Tiangan.丁, Tiangan.辛})
      - Note that the returned frozensets don't contain the direction.
    '''

    assert isinstance(relation, TianganRelation)
    assert all(isinstance(tg, Tiangan) for tg in tiangans)

    if relation is TianganRelation.合:
      return tuple(combo for combo in Rules.TIANGAN_HE if combo.issubset(tiangans))
    elif relation is TianganRelation.冲:
      return tuple(combo for combo in Rules.TIANGAN_CHONG if combo.issubset(tiangans))
    
    # Otherwise, relation is `TianganRelation.生` or `TianganRelation.克`.
    tg_set: set[Tiangan] = set(tiangans)

    if relation is TianganRelation.生:
      return tuple(frozenset(combo) for combo in Rules.TIANGAN_SHENG if tg_set.issuperset(combo))
    else: 
      assert relation is TianganRelation.克
      return tuple(frozenset(combo) for combo in Rules.TIANGAN_KE if tg_set.issuperset(combo))

  @staticmethod
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

    fs: frozenset[Tiangan] = frozenset((tg1, tg2))
    if fs in Rules.TIANGAN_HE:
      return Rules.TIANGAN_HE[fs]
    return None
  
  @staticmethod
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
    return frozenset((tg1, tg2)) in Rules.TIANGAN_CHONG
  
  @staticmethod
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
    return (tg1, tg2) in Rules.TIANGAN_SHENG
  
  @staticmethod
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
    return (tg1, tg2) in Rules.TIANGAN_KE
