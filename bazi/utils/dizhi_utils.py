# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>


'''地支关系判断、搜索与组合发现。

discover 处理地支，discover_ganzhis 保留干支与柱位；definitions 参数选择关系读法。'''

from collections import Counter
from dataclasses import dataclass
from itertools import combinations, product
from typing import Final
from collections.abc import Sequence, Iterable

from ..common import frozendict, check_declared_types
from ..defines import Tiangan, Dizhi, Ganzhi, Wuxing, DizhiRelation
from ..rules import BaziRules, DizhiRules, DizhiRelationDefinitions, DEFAULT_DIZHI_RELATION_DEFINITIONS
from .relation_discovery import RelationDiscovery, _ordered_combos, _ordered_relation_pairs


'''
查询满足各 DizhiRelation 的地支组合；返回结果不可变。
'''


'''满足某地支关系的一个组合。'''
DizhiCombo = frozenset[Dizhi]

'''满足某地支关系的全部组合元组。'''
DizhiRelationCombos = tuple[DizhiCombo, ...]

class DizhiRelationDiscovery(RelationDiscovery[DizhiRelation, Dizhi]):
  '''地支关系到满足它的地支组合的冻结映射。拱局组合只含两个实支，不含所拱虚支；用
  `gonghe` / `gonghui` 恢复虚支。若生成该结果的干支查法使用了
  `gong_def`，调用 `gonghe` 时传 `DizhiRules.GONG_GONGHE_SCOPE[gong_def]`。'''


@dataclass(frozen=True)
class GanzhiOccurrence:
  '''一次关系查询中位于某个零基序号的具体干支值。相等与哈希使用两个字段；序号只属于
  该次查询的输入序列。

  Args:
  - index: (int) 该次查询输入序列中的零基序号。
  - ganzhi: (Ganzhi) 此位置的完整干支。
  '''
  index:  int
  ganzhi: Ganzhi

  def __post_init__(self) -> None:
    check_declared_types(self)
    if self.index < 0:
      raise ValueError(f'Expected a non-negative index, got {self.index}')


'''地支满足某关系的具体干支位置组合。'''
GanzhiRelationCombo = frozenset[GanzhiOccurrence]

'''地支满足某关系的全部具体干支位置组合。'''
GanzhiRelationCombos = tuple[GanzhiRelationCombo, ...]

class GanzhiRelationDiscovery(frozendict[DizhiRelation, GanzhiRelationCombos]):
  '''地支关系到满足它的具体干支位置组合的冻结映射；具体出现序号按
  生成该结果的入口所定义的查询序列解释，详见各入口说明。'''

  def to_dizhi_discovery(self) -> DizhiRelationDiscovery:
    '''把具体出现投影为地支，显式丢弃位置与天干；投影后相同的地支组合会去重。拱局投影保留
    两个实支；拱局键的结果形状与虚支恢复契约见 `DizhiRelationDiscovery`。'''
    projected: dict[DizhiRelation, tuple[DizhiCombo, ...]] = {}
    for relation, combos in self.items():
      unique: dict[DizhiCombo, None] = {}
      for combo in combos:
        unique[DizhiCombo(occurrence.ganzhi.dizhi for occurrence in combo)] = None
      if len(unique) > 0:
        projected[relation] = tuple(unique)
    return DizhiRelationDiscovery(projected)


def sanhui(dz1: Dizhi, dz2: Dizhi, dz3: Dizhi) -> Wuxing | None:
  '''
  检查输入的地支是否构成三会关系。
  返回结果与输入的地支顺序无关，因为三会关系是无方向的。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。
  - dz3: (Dizhi) 第三地支。

  Return: (Wuxing | None) 三会对应五行；不构成三会时为 None。

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
  检查输入的地支是否构成六合关系。
  返回结果与输入的地支顺序无关，因为六合关系是无方向的。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。

  Return: (Wuxing | None) 六合对应五行；不构成六合时为 None。

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
  检查输入的地支是否构成暗合关系。
  暗合关系的看法有多种，默认使用 `DizhiRules.AnheDef.NORMAL_EXTENDED`。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。
  - definition: (DizhiRules.AnheDef) 暗合定义，默认 NORMAL_EXTENDED。

  Return: (bool) 是否构成暗合。

  Examples:
  - anhe(Dizhi.寅, Dizhi.午)
    - return: True
  - anhe(Dizhi.寅, Dizhi.丑)
    - return: True
  - anhe(Dizhi.寅, Dizhi.丑, definition=DizhiRules.AnheDef.NORMAL)
    - return: False
  - anhe(Dizhi.寅, Dizhi.午, definition=DizhiRules.AnheDef.MANGPAI)
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
  检查输入的地支是否构成通合关系。
  通合指的是两个地支的所有藏干都两两相合。通合常用于盲派。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。

  Return: (bool) 是否构成通合。

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
  检查输入的地支是否构成通禄合关系。
  通禄合指的是五合的天干在地支对应的禄身之间的相合。通禄合常用于盲派。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。

  Return: (bool) 是否构成通禄合。

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
  检查输入的地支是否构成三合关系。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。
  - dz3: (Dizhi) 第三地支。

  Return: (Wuxing | None) 三合对应五行；不构成三合时为 None。

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
  检查输入的地支是否构成半合关系。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。

  Return: (Wuxing | None) 半合对应五行；不构成半合时为 None。

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


def gonghe(dz1: Dizhi, dz2: Dizhi, *,
           definition: DizhiRules.GongheDef = DizhiRules.GongheDef.NARROW) -> Dizhi | None:
  '''返回两支按所选拱合定义拱出的第三支；结构不成立时返回 `None`。

  本直接查询只回答地支结构，不判断柱位相邻、流派天干条件或所拱之支是否已经填实；
  查单一序列的完整成立条件时使用 `search_ganzhis` / `discover_ganzhis`，查两组输入时使用
  `discover_mutual_ganzhis`。

  Args:
  - dz1: (Dizhi) 第一参与支。
  - dz2: (Dizhi) 第二参与支。
  - definition: (DizhiRules.GongheDef) 狭义缺中神，广义收三合任意两支。

  Return: (Dizhi | None) 所拱之支；不符合所选定义时为 None。

  Examples:
  - gonghe(Dizhi.申, Dizhi.辰)
    - return: Dizhi.子
  - gonghe(Dizhi.申, Dizhi.子)
    - return: None
  - gonghe(Dizhi.申, Dizhi.子, definition=DizhiRules.GongheDef.WIDE)
    - return: Dizhi.辰
  '''
  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  if not isinstance(definition, DizhiRules.GongheDef):
    raise TypeError(f'Expected GongheDef, got {type(definition)}')
  return DizhiRules.DIZHI_GONGHE[definition].get(DizhiCombo((dz1, dz2)), None)


def gonghui(dz1: Dizhi, dz2: Dizhi) -> Dizhi | None:
  '''返回两支三会端点拱出的中神；结构不成立时返回 `None`。

  本直接查询只查地支结构；单一序列的柱位、天干与填实条件由
  `search_ganzhis` / `discover_ganzhis` 判断，两组输入由 `discover_mutual_ganzhis` 判断。

  Args:
  - dz1: (Dizhi) 第一参与支。
  - dz2: (Dizhi) 第二参与支。

  Return: (Dizhi | None) 所拱中神；结构不成立时为 None。

  Examples:
  - gonghui(Dizhi.寅, Dizhi.辰)
    - return: Dizhi.卯
  - gonghui(Dizhi.寅, Dizhi.卯)
    - return: None
  '''
  if not all(isinstance(dz, Dizhi) for dz in (dz1, dz2)):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in (dz1, dz2)]}')
  return DizhiRules.DIZHI_GONGHUI.get(DizhiCombo((dz1, dz2)), None)


def xing(*dizhis: Dizhi, definition: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE) -> DizhiRules.XingSubType | None:
  '''
  检查输入的地支是否刚好构成相刑关系。
  相刑关系的看法有多种，默认使用 `DizhiRules.XingDef.LOOSE`。
  如果使用 `DizhiRules.XingDef.LOOSE`，则 `dizhis` 的顺序会影响结果。
  如果使用 `DizhiRules.XingDef.STRICT`，则 `dizhis` 的顺序不会影响结果。

  Note:
  - `dizhis` 的最大长度为 3，超过时抛出 `ValueError`。

  Args:
  - *dizhis: (Dizhi) 待查地支。
  - definition: (DizhiRules.XingDef) 相刑的定义。

  Return: (DizhiRules.XingSubType | None) 相刑类型；不构成相刑时返回 `None`。

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
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午])
    - raise: ValueError
  - xing(*[Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午, Dizhi.午])
    - raise: ValueError
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
  检查输入的地支是否构成冲关系。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。

  Return: (bool) 是否相冲。

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
  检查输入的地支是否构成破关系。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。

  Return: (bool) 是否相破。

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
  检查输入的地支是否构成相害关系。

  Args:
  - dz1: (Dizhi) 第一地支。
  - dz2: (Dizhi) 第二地支。

  Return: (bool) 是否相害。

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
  检查输入的地支是否构成生关系。
  相生关系只关注五行，不区分阴阳。

  Args:
  - dz1: (Dizhi) 生的一方。
  - dz2: (Dizhi) 被生的一方。

  Return: (bool) 是否 dz1 生 dz2。

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
  检查输入的地支是否构成相克关系。
  相克关系只关注五行，不区分阴阳。

  Args:
  - dz1: (Dizhi) 克的一方。
  - dz2: (Dizhi) 被克的一方。

  Return: (bool) 是否 dz1 克 dz2。

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


_SUBSET_SEARCH_COMBOS: Final[frozendict[DizhiRelation, DizhiRelationCombos]] = frozendict({
  DizhiRelation.三会:  _ordered_combos(DizhiRules.DIZHI_SANHUI),
  DizhiRelation.六合:  _ordered_combos(DizhiRules.DIZHI_LIUHE),
  DizhiRelation.通合:  _ordered_combos(DizhiRules.DIZHI_TONGHE),
  DizhiRelation.通禄合: _ordered_combos(DizhiRules.DIZHI_TONGLUHE),
  DizhiRelation.三合:  _ordered_combos(DizhiRules.DIZHI_SANHE),
  DizhiRelation.半合:  _ordered_combos(DizhiRules.DIZHI_BANHE),
  DizhiRelation.冲:   _ordered_combos(DizhiRules.DIZHI_CHONG),
  DizhiRelation.破:   _ordered_combos(DizhiRules.DIZHI_PO),
  DizhiRelation.害:   _ordered_combos(DizhiRules.DIZHI_HAI),
  DizhiRelation.生:   _ordered_relation_pairs(DizhiRules.DIZHI_SHENG),
  DizhiRelation.克:   _ordered_relation_pairs(DizhiRules.DIZHI_KE),
})

_ANHE_SEARCH_COMBOS: Final[frozendict[DizhiRules.AnheDef, DizhiRelationCombos]] = frozendict({
  definition: _ordered_combos(combos) for definition, combos in DizhiRules.DIZHI_ANHE.items()
})


def search(dizhis: Sequence[Dizhi], relation: DizhiRelation, *,
           definitions: DizhiRelationDefinitions = DEFAULT_DIZHI_RELATION_DEFINITIONS) -> DizhiRelationCombos:
  '''
  返回 `dizhis` 中所有满足该关系的组合。

  Note:
  - 只接受 `Sequence`，非序列在遍历前抛出 `TypeError`；空序列合法，重复地支保留自刑重数。
  - 组合不含作用方向，合、会本身无向；生、克的方向用 sheng / ke 单独判断。
    例如组合 {午, 寅} 本身不表示寅生午或午生寅。
  - 对于刑关系，更复杂一些：
    - 对于辰午酉亥自刑，只需要同时出现两次就满足相刑关系。
    - 对于子卯相刑，只需要子、卯都出现就满足相刑关系。
    - 对于丑未戌、寅巳申三刑，有的看法认为需要三个地支同时出现才算刑，有的看法认为只需要出现两个也算相刑。
    - 用哪个定义由 `definitions.xing_def` 决定；默认 `XingDef.LOOSE` 下，丑未戌、寅巳申三取二即算。
    - 需要具体刑类型及方向时用 xing。
  - 拱合、拱会依赖柱位与天干；本纯地支入口对两者抛 `ValueError`，请用 `search_ganzhis`。
  - 暗合查询的表由 `definitions.anhe_def` 选择，默认 `DizhiRules.AnheDef.NORMAL_EXTENDED`（最宽定义）。
  - 结果顺序：三会、六合、三合、半合按定义序，暗合等集合型关系按组合成员枚举序；
    刑按规则表首次组合出现序，生克先按施方、受方枚举序排列，再折为保序去重的无向组合。

  Args:
  - dizhis: (Sequence[Dizhi]) 待查地支；重数参与自刑判断。
  - relation: (DizhiRelation) 待查关系。
  - definitions: (DizhiRelationDefinitions) 已校验的关系定义；本入口只读取暗合与刑定义。

  Return: (DizhiRelationCombos) 所有匹配组合，不包含作用方向。

  Examples:
  - search([Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.午, Dizhi.未], DizhiRelation.三会)
    - return: ({Dizhi.寅, Dizhi.卯, Dizhi.辰})
  - search([Dizhi.寅, Dizhi.卯, Dizhi.丑, Dizhi.午, Dizhi.申], DizhiRelation.暗合)
    - return: ({ Dizhi.丑, Dizhi.寅}, { Dizhi.寅, Dizhi.午}, { Dizhi.卯, Dizhi.申})
  - search([Dizhi.寅,Dizhi.巳, Dizhi.申, Dizhi.辰], DizhiRelation.刑)
    - return: ({ Dizhi.寅, Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.巳 }, { Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.申 })
    - 输入只有一个辰，不构成自刑。
  - search([Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.辰, Dizhi.辰], DizhiRelation.刑)
    - return: ({ Dizhi.寅, Dizhi.巳, Dizhi.申 }, { Dizhi.辰 }, { Dizhi.寅, Dizhi.巳 }, { Dizhi.巳, Dizhi.申 }, { Dizhi.寅, Dizhi.申 })
    - 输入两个辰构成自刑；返回组合的集合中只保留一个辰。
  - search([Dizhi.卯, Dizhi.子, Dizhi.寅, Dizhi.巳], DizhiRelation.刑)
    - return: ({ Dizhi.子, Dizhi.卯}, { Dizhi.寅, Dizhi.巳 })
  '''

  if not isinstance(relation, DizhiRelation):
    raise TypeError(f'Expected DizhiRelation, got {type(relation)}')
  if not isinstance(dizhis, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(dizhis)}')
  if not all(isinstance(dz, Dizhi) for dz in dizhis):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis]}')
  if not isinstance(definitions, DizhiRelationDefinitions):
    raise TypeError(f'Expected DizhiRelationDefinitions, got {type(definitions)}')

  if relation in DizhiRules.GONG_RELATIONS:
    raise ValueError(f'{relation} requires Ganzhi positions; use search_ganzhis')

  if relation is DizhiRelation.刑:
    # 多重集语义（自刑要求同一地支出现两次），普通子集判定不适用。
    dz_counter: Counter[Dizhi] = Counter(dizhis)

    ret: dict[DizhiCombo, None] = {}
    for xing_tuple in DizhiRules.DIZHI_XING[definitions.xing_def]:
      xing_dz_counter: Counter[Dizhi] = Counter(xing_tuple)
      if dz_counter & xing_dz_counter == xing_dz_counter:
        ret[DizhiCombo(xing_tuple)] = None

    return DizhiRelationCombos(ret)

  # 其余关系同构：保留完整出现在输入中的组合。暗合的表按 `definitions.anhe_def` 选，其余静态解析。
  combos = (
    _ANHE_SEARCH_COMBOS[definitions.anhe_def] if relation is DizhiRelation.暗合 else _SUBSET_SEARCH_COMBOS[relation]
  )
  dz_set: set[Dizhi] = set(dizhis)
  return DizhiRelationCombos(combo for combo in combos if combo.issubset(dz_set))


def discover(dizhis: Sequence[Dizhi], *,
             definitions: DizhiRelationDefinitions = DEFAULT_DIZHI_RELATION_DEFINITIONS) -> DizhiRelationDiscovery:
  '''
  返回给定地支中所有可能的地支关系组合（三会、六合、刑等）。
  各关系由 `search` 求值。

  Note:
  - 返回的字典的键中可能不包含所有的 `DizhiRelation`。
  - 只接受 `Sequence`，非序列在遍历前抛出 `TypeError`；空序列合法，重复地支保留自刑重数。
  - 本纯地支发现不含拱合、拱会；需要柱位与天干条件时使用 `discover_ganzhis`。
  - 默认定义、选表及组合不保留作用方向的语义见 `search`。

  Args:
  - dizhis: (Sequence[Dizhi]) 待查地支。
  - definitions: (DizhiRelationDefinitions) 关系定义，原样传给 `search`。

  Return: (DizhiRelationDiscovery) 所有匹配组合的冻结映射，不包含作用方向。
  '''

  if not isinstance(dizhis, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(dizhis)}')
  if not all(isinstance(dz, Dizhi) for dz in dizhis):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis]}')
  if not isinstance(definitions, DizhiRelationDefinitions):
    raise TypeError(f'Expected DizhiRelationDefinitions, got {type(definitions)}')
  return DizhiRelationDiscovery({
    rel : result
    for rel in DizhiRelation
    if rel not in DizhiRules.GONG_RELATIONS
    if len(result := search(dizhis, rel, definitions=definitions)) > 0
  })


def _gong_tiangan_qualified(
  gz1: Ganzhi,
  gz2: Ganzhi,
  tiangans: tuple[Tiangan, ...],
  formation: Wuxing,
  gong_def: DizhiRules.GongDef,
) -> bool:
  '''应用一档有来源的拱局天干条件。'''
  if gong_def in (DizhiRules.GongDef.SAME_STEM_NARROW, DizhiRules.GongDef.SAME_STEM_WIDE):
    return gz1.tiangan is gz2.tiangan
  elif gong_def is DizhiRules.GongDef.TRANSFORMING_NARROW:
    return any(BaziRules.TIANGAN_TRAITS[tg].wuxing is formation for tg in tiangans)
  else:
    assert gong_def is DizhiRules.GongDef.LU_NARROW
    return DizhiRules.DIZHI_GONG_LU_TIANGAN[formation] in tiangans


def _search_gong(
  ganzhis: tuple[Ganzhi, ...],
  relation: DizhiRelation,
  index_pairs: Iterable[tuple[int, int]],
  gong_def: DizhiRules.GongDef,
) -> GanzhiRelationCombos:
  '''在调用方选定的柱位对中查拱局。'''
  assert relation in DizhiRules.GONG_RELATIONS
  assert isinstance(gong_def, DizhiRules.GongDef)

  if relation is DizhiRelation.拱会 and gong_def is DizhiRules.GongDef.LU_NARROW:
    return () # 见禄字来源只定义狭义拱合，不含拱会。

  tiangans: tuple[Tiangan, ...] = tuple(gz.tiangan for gz in ganzhis)
  dizhis: frozenset[Dizhi] = frozenset(gz.dizhi for gz in ganzhis)
  gonghe_def: DizhiRules.GongheDef = DizhiRules.GONG_GONGHE_SCOPE[gong_def]

  ret: list[GanzhiRelationCombo] = []
  for index1, index2 in index_pairs:
    gz1, gz2 = ganzhis[index1], ganzhis[index2]
    target: Dizhi | None = (
      gonghe(gz1.dizhi, gz2.dizhi, definition=gonghe_def)
      if relation is DizhiRelation.拱合
      else gonghui(gz1.dizhi, gz2.dizhi)
    )
    if target is None or target in dizhis:
      continue

    complete: DizhiCombo = DizhiCombo((gz1.dizhi, gz2.dizhi, target))
    formation: Wuxing = (
      DizhiRules.DIZHI_SANHE[complete]
      if relation is DizhiRelation.拱合
      else DizhiRules.DIZHI_SANHUI[complete]
    )
    if _gong_tiangan_qualified(gz1, gz2, tiangans, formation, gong_def):
      ret.append(GanzhiRelationCombo((GanzhiOccurrence(index1, gz1), GanzhiOccurrence(index2, gz2))))
  return GanzhiRelationCombos(ret)


def search_ganzhis(ganzhis: Sequence[Ganzhi], relation: DizhiRelation, *,
                   definitions: DizhiRelationDefinitions = DEFAULT_DIZHI_RELATION_DEFINITIONS) -> GanzhiRelationCombos:
  '''找出地支满足 `relation` 的具体干支位置组合。

  输入序列中的零基序号就是具体出现的身份，因此不同位置的相同干支或地支不会混同。
  对现有不依赖位置的关系，逐项投影到地支并去重后与 `search` 完全等价。

  拱合、拱会在本入口应用来源档案，只查相邻具体出现；所拱之支已在输入中出现时不再论暗拱。
  返回组合只含两个实支；虚支恢复契约见 `DizhiRelationDiscovery`。

  非拱组合先沿 `search` 的地支组合序，再按输入序号展开同值的多处出现；
  拱局按相邻柱位对的顺序返回。

  Args:
  - ganzhis: (Sequence[Ganzhi]) 有序干支序列；地支重数参与自刑判断。
  - relation: (DizhiRelation) 待查关系。
  - definitions: (DizhiRelationDefinitions) 关系定义；拱局读取 `gong_def`，只查相邻具体出现。

  Return: (GanzhiRelationCombos) 所有匹配的具体出现组合，不包含作用方向。
  '''

  if not isinstance(ganzhis, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(ganzhis)}')
  if not all(isinstance(gz, Ganzhi) for gz in ganzhis):
    raise TypeError(f'Expected all Ganzhi, got {[type(gz) for gz in ganzhis]}')
  if not isinstance(relation, DizhiRelation):
    raise TypeError(f'Expected DizhiRelation, got {type(relation)}')
  if not isinstance(definitions, DizhiRelationDefinitions):
    raise TypeError(f'Expected DizhiRelationDefinitions, got {type(definitions)}')

  concrete_ganzhis: tuple[Ganzhi, ...] = tuple(ganzhis)
  if relation in DizhiRules.GONG_RELATIONS:
    adjacent_pairs = zip(range(len(concrete_ganzhis) - 1), range(1, len(concrete_ganzhis)))
    return _search_gong(concrete_ganzhis, relation, adjacent_pairs, definitions.gong_def)

  dizhis: tuple[Dizhi, ...] = tuple(gz.dizhi for gz in concrete_ganzhis)
  occurrences: tuple[GanzhiOccurrence, ...] = tuple(
    GanzhiOccurrence(index, gz) for index, gz in enumerate(concrete_ganzhis)
  )

  ret: list[GanzhiRelationCombo] = []
  for combo in search(dizhis, relation, definitions=definitions):
    # 自刑对投影为单支集合；具体出现身份保留两个实际参与者。
    participant_count: int = 2 if relation is DizhiRelation.刑 and len(combo) == 1 else len(combo)
    ret.extend(
      GanzhiRelationCombo(candidate)
      for candidate in combinations(occurrences, participant_count)
      if DizhiCombo(occurrence.ganzhi.dizhi for occurrence in candidate) == combo
    )
  return GanzhiRelationCombos(ret)


def discover_ganzhis(ganzhis: Sequence[Ganzhi], *,
                     definitions: DizhiRelationDefinitions = DEFAULT_DIZHI_RELATION_DEFINITIONS,
                     relations: Sequence[DizhiRelation] = tuple(DizhiRelation)) -> GanzhiRelationDiscovery:
  '''保留输入位置与天干，发现具体干支之间的所选地支关系。

  Note:
  - 没有匹配组合的关系不会出现在返回映射中。
  - 返回的组合不体现有向关系的方向。
  - 拱局的来源档案、相邻、填实与结果形状语义同 `search_ganzhis`。
  - 关系按 `relations` 的首次出现顺序求值，重复关系只查一次。
  - 输入须为 `Sequence`；非序列在遍历前抛出 `TypeError`。

  Args:
  - ganzhis: (Sequence[Ganzhi]) 有序干支序列。
  - definitions: (DizhiRelationDefinitions) 关系定义，原样传给 `search_ganzhis`。
  - relations: (Sequence[DizhiRelation]) 只求值这些关系，默认全部；空序列不求值任何关系。

  Return: (GanzhiRelationDiscovery) 保留具体出现位置的冻结关系映射。
  '''

  if not isinstance(ganzhis, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(ganzhis)}')
  if not all(isinstance(gz, Ganzhi) for gz in ganzhis):
    raise TypeError(f'Expected all Ganzhi, got {[type(gz) for gz in ganzhis]}')
  if not isinstance(definitions, DizhiRelationDefinitions):
    raise TypeError(f'Expected DizhiRelationDefinitions, got {type(definitions)}')
  if not isinstance(relations, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(relations)}')
  if not all(isinstance(rel, DizhiRelation) for rel in relations):
    raise TypeError(f'Expected all DizhiRelation, got {[type(rel) for rel in relations]}')

  return GanzhiRelationDiscovery({
    rel : result
    for rel in dict.fromkeys(relations)
    if len(result := search_ganzhis(
      ganzhis,
      rel,
      definitions=definitions,
    )) > 0
  })


def discover_mutual_ganzhis(ganzhis1: Sequence[Ganzhi], ganzhis2: Sequence[Ganzhi], *,
                            definitions: DizhiRelationDefinitions = DEFAULT_DIZHI_RELATION_DEFINITIONS,
                            relations: Sequence[DizhiRelation] = tuple(DizhiRelation)) -> GanzhiRelationDiscovery:
  '''发现参与柱横跨两组输入的所选干支关系。

  具体出现序号属于概念上的 `ganzhis1 + ganzhis2`；第二组从 `len(ganzhis1)` 起算。
  跨组拱局按岁运作用口径直接成为候选；单侧内部的拱局不进跨组结果。
  所拱之支已在任一组出现时不再论暗拱；组合只含真实参与者，保留完整干支与位置。
  拱局组合按左侧柱位优先的两侧柱位对顺序返回；非拱组合沿 `search_ganzhis` 的查询顺序。

  Note:
  - 两组输入都须为 `Sequence`，在遍历任一组前检查；空序列合法。
  - 关系按 `relations` 的首次出现顺序求值，重复关系只查一次；没有组合的键不返回。
  - 非拱关系同样要求具体参与者来自两侧，与 `discover_mutual` 的按值查法不同。
  - 返回的组合不体现有向关系的方向。

  Args:
  - ganzhis1: (Sequence[Ganzhi]) 第一组有序干支。
  - ganzhis2: (Sequence[Ganzhi]) 第二组有序干支。
  - definitions: (DizhiRelationDefinitions) 关系定义。
  - relations: (Sequence[DizhiRelation]) 只求值这些关系，默认全部；空序列不求值任何关系。

  Return: (GanzhiRelationDiscovery) 参与者横跨两侧的具体出现组合。
  '''
  if not isinstance(ganzhis1, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(ganzhis1)}')
  if not isinstance(ganzhis2, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(ganzhis2)}')
  if not all(isinstance(gz, Ganzhi) for gz in ganzhis1):
    raise TypeError(f'Expected all Ganzhi, got {[type(gz) for gz in ganzhis1]}')
  if not all(isinstance(gz, Ganzhi) for gz in ganzhis2):
    raise TypeError(f'Expected all Ganzhi, got {[type(gz) for gz in ganzhis2]}')
  if not isinstance(definitions, DizhiRelationDefinitions):
    raise TypeError(f'Expected DizhiRelationDefinitions, got {type(definitions)}')
  if not isinstance(relations, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(relations)}')
  if not all(isinstance(rel, DizhiRelation) for rel in relations):
    raise TypeError(f'Expected all DizhiRelation, got {[type(rel) for rel in relations]}')

  first: tuple[Ganzhi, ...] = tuple(ganzhis1)
  second: tuple[Ganzhi, ...] = tuple(ganzhis2)
  combined: tuple[Ganzhi, ...] = first + second
  split: int = len(first)

  def __search(relation: DizhiRelation) -> GanzhiRelationCombos:
    if relation in DizhiRules.GONG_RELATIONS:
      return _search_gong(
        combined,
        relation,
        product(range(split), range(split, len(combined))),
        definitions.gong_def,
      )

    combos = search_ganzhis(
      combined,
      relation,
      definitions=definitions,
    )
    return GanzhiRelationCombos(
      combo for combo in combos
      if any(occurrence.index < split for occurrence in combo)
      and any(occurrence.index >= split for occurrence in combo)
    )

  return GanzhiRelationDiscovery({
    relation : result
    for relation in dict.fromkeys(relations)
    if len(result := __search(relation)) > 0
  })


def discover_mutual(dizhis1: Sequence[Dizhi], dizhis2: Sequence[Dizhi], *,
                    definitions: DizhiRelationDefinitions = DEFAULT_DIZHI_RELATION_DEFINITIONS) -> DizhiRelationDiscovery:
  '''
  找出输入的两组地支中所有可能的关系组合（三会、六合、刑等）。
  返回组合须与两组地支值集均相交，不追踪具体出现；按值过滤语义见 RelationDiscovery.mutual_only。

  Note:
  - 返回的字典的键中可能不包含所有的 `DizhiRelation`。
  - 两组输入都须为 `Sequence`，在遍历任一组前检查；重复地支保留自刑重数。
  - 本纯地支跨组入口不含拱合、拱会；其跨作用域查法见 `discover_mutual_ganzhis`。
  - 默认定义、选表及组合不保留作用方向的语义见 `search`。

  Args:
  - dizhis1: (Sequence[Dizhi]) 第一组地支。
  - dizhis2: (Sequence[Dizhi]) 第二组地支。
  - definitions: (DizhiRelationDefinitions) 关系定义，原样传给 `search`。

  Return: (DizhiRelationDiscovery) 跨组匹配组合的冻结映射，不包含作用方向。
  
  Examples:
  - discover_mutual([子], [丑])
    - return: {
      DizhiRelation.六合: DizhiRelationCombos({子, 丑},),
      DizhiRelation.克: DizhiRelationCombos({子, 丑},)
    }
  - discover_mutual([子, 丑], [])
    - return: {} // 空的冻结映射。
  '''

  if not isinstance(dizhis1, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(dizhis1)}')
  if not isinstance(dizhis2, Sequence):
    raise TypeError(f'Expected a Sequence, got {type(dizhis2)}')
  if not all(isinstance(dz, Dizhi) for dz in dizhis1):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis1]}')
  if not all(isinstance(dz, Dizhi) for dz in dizhis2):
    raise TypeError(f'Expected all Dizhi, got {[type(dz) for dz in dizhis2]}')
  if not isinstance(definitions, DizhiRelationDefinitions):
    raise TypeError(f'Expected DizhiRelationDefinitions, got {type(definitions)}')

  # 自刑依赖重数（同一地支两侧各现一次也构成自刑），故两侧拼接——集合并会静默破坏
  # 自刑。与天干侧的集合并是刻意分歧。
  return discover(list(dizhis1) + list(dizhis2), definitions=definitions).mutual_only(set(dizhis1), set(dizhis2))
