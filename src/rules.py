# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import itertools
from enum import Enum
from typing import Final

from .common import frozendict
from .data_types import TraitTuple, HiddenTianganDict
from .defines import Tiangan, Dizhi, Ganzhi, Wuxing, Yinyang


# All rule tables are plain `Final` class attributes, built once at import time.
# `Final` is the reassignment guard, enforced by mypy; there is no runtime guard.


# Computed tables are built by module-level `_lower_snake` builders (named after their
# tables), because loops/comprehensions in a class body cannot see class-level names.
def _nayin() -> frozendict[Ganzhi, str]:
  NAYIN_STR_LIST: list[str] = [
    '海中金', '炉中火', '大林木', '路旁土', '剑锋金', '山头火',
    '涧下水', '城头土', '白蜡金', '杨柳木', '泉中水', '屋上土',
    '霹雳火', '松柏木', '长流水', '沙中金', '山下火', '平地木',
    '壁上土', '金箔金', '覆灯火', '天河水', '大驿土', '钗钏金',
    '桑柘木', '大溪水', '沙中土', '天上火', '石榴木', '大海水',
  ]
  nayin_mapping_table: dict[Ganzhi, str] = {}
  cycle = Ganzhi.list_sexagenary_cycle()
  for index, gz in enumerate(cycle):
    nayin_mapping_table[gz] = NAYIN_STR_LIST[index // 2]
  return frozendict(nayin_mapping_table)


class BaziRules:
  '''Rules for `Bazi` and `BaziChart`.'''

  # The mappings are used to figure out the first month's Tiangan in a ganzhi year, i.e. 年上起月表.
  YEAR_TO_MONTH_TABLE: Final[frozendict[Tiangan, Tiangan]] = frozendict({
    Tiangan.甲 : Tiangan.丙, # First month in year of "甲" is "丙寅".
    Tiangan.乙 : Tiangan.戊, # First month in year of "乙" is "戊寅".
    Tiangan.丙 : Tiangan.庚, # First month in year of "丙" is "庚寅".
    Tiangan.丁 : Tiangan.壬, # First month in year of "丁" is "壬寅".
    Tiangan.戊 : Tiangan.甲, # First month in year of "戊" is "甲寅".
    Tiangan.己 : Tiangan.丙, # First month in year of "己" is "丙寅".
    Tiangan.庚 : Tiangan.戊, # First month in year of "庚" is "戊寅".
    Tiangan.辛 : Tiangan.庚, # First month in year of "辛" is "庚寅".
    Tiangan.壬 : Tiangan.壬, # First month in year of "壬" is "壬寅".
    Tiangan.癸 : Tiangan.甲, # First month in year of "癸" is "甲寅".
  })

  # The mappings are used to figure out the first hour's Tiangan in a ganzhi day, i.e. 日上起时表.
  DAY_TO_HOUR_TABLE: Final[frozendict[Tiangan, Tiangan]] = frozendict({
    Tiangan.甲 : Tiangan.甲, # First hour in day of "甲" is "甲子".
    Tiangan.乙 : Tiangan.丙, # First hour in day of "乙" is "丙子".
    Tiangan.丙 : Tiangan.戊, # First hour in day of "丙" is "戊子".
    Tiangan.丁 : Tiangan.庚, # First hour in day of "丁" is "庚子".
    Tiangan.戊 : Tiangan.壬, # First hour in day of "戊" is "壬子".
    Tiangan.己 : Tiangan.甲, # First hour in day of "己" is "甲子".
    Tiangan.庚 : Tiangan.丙, # First hour in day of "庚" is "丙子".
    Tiangan.辛 : Tiangan.戊, # First hour in day of "辛" is "戊子".
    Tiangan.壬 : Tiangan.庚, # First hour in day of "壬" is "庚子".
    Tiangan.癸 : Tiangan.壬, # First hour in day of "癸" is "壬子".
  })

  # The table is used to query the Wuxing and Yinyang of a given Tiangan (i.e. Stem / 天干).
  # 该字典用于查询给定天干的五行和阴阳。
  TIANGAN_TRAITS: Final[frozendict[Tiangan, TraitTuple]] = frozendict({
    Tiangan.甲 : TraitTuple(Wuxing.木, Yinyang.阳),
    Tiangan.乙 : TraitTuple(Wuxing.木, Yinyang.阴),
    Tiangan.丙 : TraitTuple(Wuxing.火, Yinyang.阳),
    Tiangan.丁 : TraitTuple(Wuxing.火, Yinyang.阴),
    Tiangan.戊 : TraitTuple(Wuxing.土, Yinyang.阳),
    Tiangan.己 : TraitTuple(Wuxing.土, Yinyang.阴),
    Tiangan.庚 : TraitTuple(Wuxing.金, Yinyang.阳),
    Tiangan.辛 : TraitTuple(Wuxing.金, Yinyang.阴),
    Tiangan.壬 : TraitTuple(Wuxing.水, Yinyang.阳),
    Tiangan.癸 : TraitTuple(Wuxing.水, Yinyang.阴),
  })

  # The table is used to query the Wuxing and Yinyang of a given Dizhi (i.e. Branch / 地支).
  # 该字典用于查询给定地支的五行和阴阳。
  DIZHI_TRAITS: Final[frozendict[Dizhi, TraitTuple]] = frozendict({
    Dizhi.子 : TraitTuple(Wuxing.水, Yinyang.阳),
    Dizhi.丑 : TraitTuple(Wuxing.土, Yinyang.阴),
    Dizhi.寅 : TraitTuple(Wuxing.木, Yinyang.阳),
    Dizhi.卯 : TraitTuple(Wuxing.木, Yinyang.阴),
    Dizhi.辰 : TraitTuple(Wuxing.土, Yinyang.阳),
    Dizhi.巳 : TraitTuple(Wuxing.火, Yinyang.阴),
    Dizhi.午 : TraitTuple(Wuxing.火, Yinyang.阳),
    Dizhi.未 : TraitTuple(Wuxing.土, Yinyang.阴),
    Dizhi.申 : TraitTuple(Wuxing.金, Yinyang.阳),
    Dizhi.酉 : TraitTuple(Wuxing.金, Yinyang.阴),
    Dizhi.戌 : TraitTuple(Wuxing.土, Yinyang.阳),
    Dizhi.亥 : TraitTuple(Wuxing.水, Yinyang.阴),
  })

  # The table is used to find the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
  # 该字典用于查询给定地支的藏干和它们所占的百分比。
  HIDDEN_TIANGANS: Final[frozendict[Dizhi, HiddenTianganDict]] = frozendict({
    Dizhi.子 : HiddenTianganDict({ Tiangan.癸 : 100 }),
    Dizhi.丑 : HiddenTianganDict({ Tiangan.己 : 60, Tiangan.癸 : 30, Tiangan.辛 : 10 }),
    Dizhi.寅 : HiddenTianganDict({ Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10 }),
    Dizhi.卯 : HiddenTianganDict({ Tiangan.乙 : 100 }),
    Dizhi.辰 : HiddenTianganDict({ Tiangan.戊 : 60, Tiangan.乙 : 30, Tiangan.癸 : 10 }),
    Dizhi.巳 : HiddenTianganDict({ Tiangan.丙 : 60, Tiangan.庚 : 30, Tiangan.戊 : 10 }),
    Dizhi.午 : HiddenTianganDict({ Tiangan.丁 : 70, Tiangan.己 : 30 }),
    Dizhi.未 : HiddenTianganDict({ Tiangan.己 : 60, Tiangan.丁 : 30, Tiangan.乙 : 10 }),
    Dizhi.申 : HiddenTianganDict({ Tiangan.庚 : 60, Tiangan.壬 : 30, Tiangan.戊 : 10 }),
    Dizhi.酉 : HiddenTianganDict({ Tiangan.辛 : 100 }),
    Dizhi.戌 : HiddenTianganDict({ Tiangan.戊 : 60, Tiangan.辛 : 30, Tiangan.丁 : 10 }),
    Dizhi.亥 : HiddenTianganDict({ Tiangan.壬 : 70, Tiangan.甲 : 30 }),
  })

  # The table is used to query the NAYIN (纳音) of a given Ganzhi (i.e. Stem-branch / Ganzhi / 干支).
  # 该字典用于查询给定干支的纳音。
  NAYIN: Final[frozendict[Ganzhi, str]] = _nayin()

  # The table is used to query the dizhi where the Zhangsheng locates for each Tiangan.
  # 该字典用于查询每个天干的长生所在的地支。
  TIANGAN_ZHANGSHENG: Final[frozendict[Tiangan, Dizhi]] = frozendict({
    Tiangan.甲 : Dizhi.亥,
    Tiangan.乙 : Dizhi.午,
    Tiangan.丙 : Dizhi.寅,
    Tiangan.丁 : Dizhi.酉,
    Tiangan.戊 : Dizhi.寅,
    Tiangan.己 : Dizhi.酉,
    Tiangan.庚 : Dizhi.巳,
    Tiangan.辛 : Dizhi.子,
    Tiangan.壬 : Dizhi.申,
    Tiangan.癸 : Dizhi.卯,
  })

  # This table is used to query Tiangans' LU (禄) in Dizhis.
  # 该字典用于查询天干的禄/禄身。
  TIANGAN_LU: Final[frozendict[Tiangan, Dizhi]] = frozendict({
    Tiangan.甲 : Dizhi.寅,
    Tiangan.乙 : Dizhi.卯,
    Tiangan.丙 : Dizhi.巳,
    Tiangan.丁 : Dizhi.午,
    Tiangan.戊 : Dizhi.巳,
    Tiangan.己 : Dizhi.午,
    Tiangan.庚 : Dizhi.申,
    Tiangan.辛 : Dizhi.酉,
    Tiangan.壬 : Dizhi.亥,
    Tiangan.癸 : Dizhi.子,
  })



def _tiangan_sheng(traits: frozendict[Tiangan, TraitTuple]) -> frozenset[tuple[Tiangan, Tiangan]]:
  ret: list[tuple[Tiangan, Tiangan]] = []
  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    tg1_trait: TraitTuple = traits[tg1]
    tg2_trait: TraitTuple = traits[tg2]
    if tg1_trait.wuxing.generates(tg2_trait.wuxing): # Yinyang not considered. 天干相生不考虑阴阳。
      ret.append((tg1, tg2)) # Direction: tg1 -> tg2
  return frozenset(ret)


def _tiangan_ke(traits: frozendict[Tiangan, TraitTuple]) -> frozenset[tuple[Tiangan, Tiangan]]:
  ret: list[tuple[Tiangan, Tiangan]] = []
  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    tg1_trait: TraitTuple = traits[tg1]
    tg2_trait: TraitTuple = traits[tg2]
    if tg1_trait.wuxing.destructs(tg2_trait.wuxing): # Yinyang not considered. 天干相克不考虑阴阳。
      ret.append((tg1, tg2)) # Direction: tg1 -> tg2
  return frozenset(ret)


class TianganRules:
  '''Rules for Tiangan relations / 天干关系'''

  # The table is used to query the HE (合) relation across all Tiangans.
  # HE relation is a non-directional/mutual relation.
  # 该表格用于查询天干之间的相合关系。
  # 相合关系是无方向的。如甲己相合是双向的关系，互相相合。
  TIANGAN_HE: Final[frozendict[frozenset[Tiangan], Wuxing]] = frozendict({
    frozenset((Tiangan.甲, Tiangan.己)) : Wuxing.土,
    frozenset((Tiangan.乙, Tiangan.庚)) : Wuxing.金,
    frozenset((Tiangan.丙, Tiangan.辛)) : Wuxing.水,
    frozenset((Tiangan.丁, Tiangan.壬)) : Wuxing.木,
    frozenset((Tiangan.戊, Tiangan.癸)) : Wuxing.火,
  })

  # The table is used to query the CHONG (冲) relation across all Tiangans.
  # CHONG relation is a non-directional/mutual relation.
  # 该表格用于查询天干之间的相冲关系。
  # 相冲关系是无方向的。如甲庚相冲是双向的关系，互相相冲。相冲双方均减力，旺者减力小，弱者减力大。
  TIANGAN_CHONG: Final[frozenset[frozenset[Tiangan]]] = frozenset((
    frozenset((Tiangan.甲, Tiangan.庚)),
    frozenset((Tiangan.乙, Tiangan.辛)),
    frozenset((Tiangan.丙, Tiangan.壬)),
    frozenset((Tiangan.丁, Tiangan.癸)),
  ))

  # The table is used to query the SHENG (生) relation across all Tiangans.
  # SHENG relation is a uni-directional relation.
  # Yinyang is not considered in SHENG relation - only Wuxing is considered.
  # 该表格用于查询天干之间的相生关系。
  # 相生关系是单向的。如甲丁相生，则是甲木生丁火。
  # 天干相生不考虑阴阳，只考虑五行。
  TIANGAN_SHENG: Final[frozenset[tuple[Tiangan, Tiangan]]] = _tiangan_sheng(BaziRules.TIANGAN_TRAITS)

  # The table is used to query the KE (克) relation across all Tiangans.
  # KE relation is a uni-directional relation.
  # Yinyang is not considered in KE relation - only Wuxing is considered.
  # 该表格用于查询天干之间的相克关系。
  # 相克关系是单向的。如壬丙相克，是壬水克丙火。
  # 天干相克不考虑阴阳，只考虑五行。
  TIANGAN_KE: Final[frozenset[tuple[Tiangan, Tiangan]]] = _tiangan_ke(BaziRules.TIANGAN_TRAITS)



def _dizhi_xing_strict(sub_type: type['DizhiRules.XingSubType']) -> frozendict[tuple[Dizhi, ...], 'DizhiRules.XingSubType']:
  d: dict[tuple[Dizhi, ...], DizhiRules.XingSubType] = {}
  for dz_tuple in itertools.permutations((Dizhi.丑, Dizhi.未, Dizhi.戌)):
    d[dz_tuple] = sub_type.三刑
  for dz_tuple in itertools.permutations((Dizhi.寅, Dizhi.巳, Dizhi.申)):
    d[dz_tuple] = sub_type.三刑
  for dz_tuple in itertools.permutations((Dizhi.子, Dizhi.卯)):
    d[dz_tuple] = sub_type.子卯刑
  for dz in (Dizhi.午, Dizhi.辰, Dizhi.酉, Dizhi.亥):
    d[(dz, dz)] = sub_type.自刑
  return frozendict(d)


def _dizhi_xing_loose(sub_type: type['DizhiRules.XingSubType']) -> frozendict[tuple[Dizhi, ...], 'DizhiRules.XingSubType']:
  d: dict[tuple[Dizhi, ...], DizhiRules.XingSubType] = dict(_dizhi_xing_strict(sub_type))
  for dz_tuple in ((Dizhi.丑, Dizhi.戌), (Dizhi.戌, Dizhi.未), (Dizhi.未, Dizhi.丑)):
    d[dz_tuple] = sub_type.三刑
  for dz_tuple in ((Dizhi.寅, Dizhi.巳), (Dizhi.巳, Dizhi.申), (Dizhi.申, Dizhi.寅)):
    d[dz_tuple] = sub_type.三刑
  return frozendict(d)


def _dizhi_sheng(dizhi_traits: frozendict[Dizhi, TraitTuple]) -> frozenset[tuple[Dizhi, Dizhi]]:
  ret: list[tuple[Dizhi, Dizhi]] = []
  for dz1, dz2 in itertools.permutations(Dizhi, 2):
    trait1, trait2 = dizhi_traits[dz1], dizhi_traits[dz2]
    if trait1.wuxing.generates(trait2.wuxing):
      ret.append((dz1, dz2))
  return frozenset(ret)


def _dizhi_ke(dizhi_traits: frozendict[Dizhi, TraitTuple]) -> frozenset[tuple[Dizhi, Dizhi]]:
  ret: list[tuple[Dizhi, Dizhi]] = []
  for dz1, dz2 in itertools.permutations(Dizhi, 2):
    trait1, trait2 = dizhi_traits[dz1], dizhi_traits[dz2]
    if trait1.wuxing.destructs(trait2.wuxing):
      ret.append((dz1, dz2))
  return frozenset(ret)


class DizhiRules:
  '''Rules for Dizhi relations / 地支关系'''

  class GongheDef(Enum):
    '''The structural scope of 拱合. `NARROW` only accepts a 三合 pair missing its
    middle branch; `WIDE` accepts any two branches and returns the third. 狭义拱合只收
    三合缺中神；广义拱合收三合任意两支并拱出第三支。

    Sources / 出处:
    - Narrow: https://services.shen88.cn/bazisuanming/pc-74297.html
    - Wide: https://www.sohu.com/a/471337600_310486
    '''
    NARROW = 0
    WIDE   = 1

  class GongDef(Enum):
    '''Source-backed profiles for the contextual conditions of 拱合 / 拱会.
    拱合、拱会成立条件的来源档案；只列有出处的组合，不把分歧轴任意拼接。

    - SAME_STEM_NARROW: adjacent participants share one Tiangan; narrow 拱合 plus 拱会.
      相邻两柱同干；狭义拱合并收拱会。默认，独立来源最多。
    - SAME_STEM_WIDE: the same Tiangan condition with wide 拱合 plus 拱会.
      两柱同干；广义拱合并收拱会。
    - TRANSFORMING_NARROW: the query scope exposes a Tiangan of the formed Wuxing;
      narrow 拱合 plus 拱会. 查询范围透出化神；狭义拱合并收拱会。
    - LU_NARROW: the query scope exposes 乙 / 丁 / 辛 / 癸 for the formed Wuxing;
      narrow 拱合 only. Its source does not extend the rule to 拱会.
      查询范围见所拱五行的乙、丁、辛、癸禄字；只收狭义拱合，来源未把本条扩到拱会。

    Sources / 出处:
    - Same stem, wide scope: https://www.sohu.com/a/471337600_310486
    - Transforming Tiangan: https://www.suanzhun.net/article/2395.html
    - Lu Tiangan: https://services.shen88.cn/bazisuanming/pc-74297.html
    - 拱会 / 夹 terminology: https://www.sohu.com/a/805277582_120167645
    '''
    SAME_STEM_NARROW    = 0
    SAME_STEM_WIDE      = 1
    TRANSFORMING_NARROW = 2
    LU_NARROW           = 3

  # The table is used to query the SANHUI (三会) relation across all Dizhis.
  # SANHUI relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的三会局。
  # 三会是无方向的。如寅卯辰三会木局是三个地支之间相互的关系。
  DIZHI_SANHUI: Final[frozendict[frozenset[Dizhi], Wuxing]] = frozendict({
    frozenset((Dizhi.寅, Dizhi.卯, Dizhi.辰)) : Wuxing.木,
    frozenset((Dizhi.巳, Dizhi.午, Dizhi.未)) : Wuxing.火,
    frozenset((Dizhi.申, Dizhi.酉, Dizhi.戌)) : Wuxing.金,
    frozenset((Dizhi.亥, Dizhi.子, Dizhi.丑)) : Wuxing.水,
  })

  # 三会缺中神。部分现代来源称「拱会」，盲派、梁湘润系称「夹」；机械结构相同，
  # 本库按 `DizhiRelation.拱会` 这一已选公开名称报告，术语分歧留在知识层。
  DIZHI_GONGHUI: Final[frozendict[frozenset[Dizhi], Dizhi]] = frozendict({
    frozenset((Dizhi.寅, Dizhi.辰)) : Dizhi.卯,
    frozenset((Dizhi.巳, Dizhi.未)) : Dizhi.午,
    frozenset((Dizhi.申, Dizhi.戌)) : Dizhi.酉,
    frozenset((Dizhi.亥, Dizhi.丑)) : Dizhi.子,
  })

  # The table is used to query the LIUHE (六合) relation across all Dizhis.
  # LIUHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的六合局。
  # 六合关系是无方向的。如子、丑相合是相互的关系。
  DIZHI_LIUHE: Final[frozendict[frozenset[Dizhi], Wuxing]] = frozendict({
    frozenset((Dizhi.子, Dizhi.丑)) : Wuxing.土,
    frozenset((Dizhi.寅, Dizhi.亥)) : Wuxing.木,
    frozenset((Dizhi.卯, Dizhi.戌)) : Wuxing.火,
    frozenset((Dizhi.辰, Dizhi.酉)) : Wuxing.金,
    frozenset((Dizhi.巳, Dizhi.申)) : Wuxing.水,
    frozenset((Dizhi.午, Dizhi.未)) : Wuxing.土,
  })

  class AnheDef(Enum):
    '''
    The definitions of ANHE relation. Different definitions mean different query tables.
    不同的地支暗合关系看法。

    ANHE is non-directional, so every query entry (`anhe` / `search` / `discover`) sees the
    same table per definition -- there is no entry-layer divergence like `XingDef`'s.
    暗合无方向，各查法入口（`anhe` / `search` / `discover`）看到的表一致——无 `XingDef`
    那种入口层分歧。

    This knob is declared per chart via `BaziSchool.anhe_def` and read at evaluation time
    by relation discovery (`analyzer/relationship.py`); member names are serialized into JSON.
    本旋钮由 `BaziSchool.anhe_def` 按盘声明，关系查法在评估期读取；成员名进 JSON。

    No change should be made to the existing definitions. Only add new definitions.
    '''
    NORMAL           = 0 # 卯申、巳酉、亥午、子巳、寅午 - 这也是所谓的“通禄合”/“通禄暗合”，与天干五合一一对应。
                         # 选 NORMAL 时 `DIZHI_ANHE[NORMAL]` 与 `DIZHI_TONGLUHE` 逐项相同——discovery 会在
                         # 暗合与通禄合两个键下给出相同组合，那是同一证据，不是两条独立证据。
    NORMAL_EXTENDED  = 1 # 卯申、巳酉、亥午、子巳、寅午 + 寅丑。这六组的藏干没有明显的冲突，而且有藏干相合的关系。
    MANGPAI          = 2 # 卯申、寅丑、午亥。盲派最认可这三对暗合。

  # The tables are used to query the ANHE (暗合) relation across all Dizhis.
  # ANHE relation is a non-directional/mutual relation.
  # All tables for different `AnheDef` are returned as a dict.
  # 该表格用于查询地支之间的暗合关系。
  # 暗合关系是无方向的。
  DIZHI_ANHE: Final[frozendict[AnheDef, frozenset[frozenset[Dizhi]]]] = frozendict({
    AnheDef.NORMAL          : frozenset([
      frozenset((Dizhi.卯, Dizhi.申)),
      frozenset((Dizhi.巳, Dizhi.酉)),
      frozenset((Dizhi.亥, Dizhi.午)),
      frozenset((Dizhi.子, Dizhi.巳)),
      frozenset((Dizhi.寅, Dizhi.午)),
    ]),
    AnheDef.NORMAL_EXTENDED : frozenset([
      frozenset((Dizhi.卯, Dizhi.申)),
      frozenset((Dizhi.巳, Dizhi.酉)),
      frozenset((Dizhi.亥, Dizhi.午)),
      frozenset((Dizhi.子, Dizhi.巳)),
      frozenset((Dizhi.寅, Dizhi.午)),
      frozenset((Dizhi.寅, Dizhi.丑)),
    ]),
    AnheDef.MANGPAI         : frozenset([
      frozenset((Dizhi.卯, Dizhi.申)),
      frozenset((Dizhi.寅, Dizhi.丑)),
      frozenset((Dizhi.午, Dizhi.亥)),
    ]),
  })

  # The table is used to query the TONGHE (通合) relation across all Dizhis.
  # TONGHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的通合关系。
  # 通合关系是无方向的。通合代表藏干中所有气都能两两相合。
  DIZHI_TONGHE: Final[frozenset[frozenset[Dizhi]]] = frozenset([
    frozenset((Dizhi.寅, Dizhi.丑)),
    frozenset((Dizhi.午, Dizhi.亥)),
  ])

  # The table is used to query the TONGLUHE (通禄合) relation across all Dizhis.
  # TONGLUHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的通禄合关系。
  # 通禄合关系是无方向的。若两个天干相合，那么它们在地支中的禄身也能相合，从而构成地支的通禄合关系。
  DIZHI_TONGLUHE: Final[frozenset[frozenset[Dizhi]]] = frozenset([
    frozenset((Dizhi.卯, Dizhi.申)),
    frozenset((Dizhi.巳, Dizhi.酉)),
    frozenset((Dizhi.亥, Dizhi.午)),
    frozenset((Dizhi.子, Dizhi.巳)),
    frozenset((Dizhi.寅, Dizhi.午)),
  ])

  # The table is used to query the SANHE (三合) relation across all Dizhis.
  # SANHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的三合局。
  # 三合关系是无方向的。
  DIZHI_SANHE: Final[frozendict[frozenset[Dizhi], Wuxing]] = frozendict({
    frozenset((Dizhi.巳, Dizhi.酉, Dizhi.丑)) : Wuxing.金,
    frozenset((Dizhi.亥, Dizhi.卯, Dizhi.未)) : Wuxing.木,
    frozenset((Dizhi.申, Dizhi.子, Dizhi.辰)) : Wuxing.水,
    frozenset((Dizhi.寅, Dizhi.午, Dizhi.戌)) : Wuxing.火,
  })

  # The table is used to query the BANHE (半合) relation across all Dizhis.
  # BANHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的半合局。
  # 半合关系是无方向的。
  DIZHI_BANHE: Final[frozendict[frozenset[Dizhi], Wuxing]] = frozendict({
    frozenset((Dizhi.巳, Dizhi.酉)) : Wuxing.金,
    frozenset((Dizhi.酉, Dizhi.丑)) : Wuxing.金,
    frozenset((Dizhi.亥, Dizhi.卯)) : Wuxing.木,
    frozenset((Dizhi.卯, Dizhi.未)) : Wuxing.木,
    frozenset((Dizhi.申, Dizhi.子)) : Wuxing.水,
    frozenset((Dizhi.子, Dizhi.辰)) : Wuxing.水,
    frozenset((Dizhi.寅, Dizhi.午)) : Wuxing.火,
    frozenset((Dizhi.午, Dizhi.戌)) : Wuxing.火,
  })

  # 拱合返回所拱之支，而不是化五行。狭义只收缺中神；广义收三合任意两支。
  DIZHI_GONGHE: Final[frozendict[GongheDef, frozendict[frozenset[Dizhi], Dizhi]]] = frozendict({
    GongheDef.NARROW : frozendict({
      frozenset((Dizhi.巳, Dizhi.丑)) : Dizhi.酉,
      frozenset((Dizhi.亥, Dizhi.未)) : Dizhi.卯,
      frozenset((Dizhi.申, Dizhi.辰)) : Dizhi.子,
      frozenset((Dizhi.寅, Dizhi.戌)) : Dizhi.午,
    }),
    GongheDef.WIDE : frozendict({
      frozenset((Dizhi.巳, Dizhi.丑)) : Dizhi.酉,
      frozenset((Dizhi.巳, Dizhi.酉)) : Dizhi.丑,
      frozenset((Dizhi.酉, Dizhi.丑)) : Dizhi.巳,
      frozenset((Dizhi.亥, Dizhi.未)) : Dizhi.卯,
      frozenset((Dizhi.亥, Dizhi.卯)) : Dizhi.未,
      frozenset((Dizhi.卯, Dizhi.未)) : Dizhi.亥,
      frozenset((Dizhi.申, Dizhi.辰)) : Dizhi.子,
      frozenset((Dizhi.申, Dizhi.子)) : Dizhi.辰,
      frozenset((Dizhi.子, Dizhi.辰)) : Dizhi.申,
      frozenset((Dizhi.寅, Dizhi.戌)) : Dizhi.午,
      frozenset((Dizhi.寅, Dizhi.午)) : Dizhi.戌,
      frozenset((Dizhi.午, Dizhi.戌)) : Dizhi.寅,
    }),
  })

  # The Yin Tiangan used by the 见禄字 profile for each non-earth formation.
  # 见禄字口径按所拱木火金水分别取乙丁辛癸；三合、三会无土局。
  DIZHI_GONG_LU_TIANGAN: Final[frozendict[Wuxing, Tiangan]] = frozendict({
    Wuxing.木 : Tiangan.乙,
    Wuxing.火 : Tiangan.丁,
    Wuxing.金 : Tiangan.辛,
    Wuxing.水 : Tiangan.癸,
  })

  class XingDef(Enum):
    '''
    The definitions of XING relation. This makes a difference on two combos - 丑未戌、寅巳申。
    不同的地支相刑的看法。主要区别在于丑未戌、寅巳申之间相刑的定义。

    - Definition layer (holds at every query entry): STRICT requires all three Dizhis of
      丑未戌 / 寅巳申 to appear; LOOSE requires any two of the three.
      定义层（各查法入口共有）：STRICT 要求丑未戌 / 寅巳申三支齐现；LOOSE 三取二即成立。
    - Entry layer: only order-exact lookups (`dizhi_utils.xing`) see the direction (谁刑谁);
      the batch entries `search` / `discover` compare as multisets and cannot.
      入口层：方向（谁刑谁）只有按序查法（`dizhi_utils.xing`）可见；
      批量入口（`search` / `discover`）按多重集比对，看不出方向。

    This knob is declared per chart via `BaziSchool.xing_def` and read at evaluation time
    by relation discovery (`analyzer/relationship.py`); member names are serialized into JSON.
    本旋钮由 `BaziSchool.xing_def` 按盘声明，关系查法在评估期读取；成员名进 JSON。

    No change should be made to the existing definitions. Only add new definitions.
    '''
    STRICT = 0 # For 丑未戌 and 寅巳申, a XING relation is formed only when all three Dizhis appear.
    LOOSE  = 1 # For 丑未戌 and 寅巳申, any two of the three suffice. In order-exact lookups
               # (`dizhi_utils.xing`) the pair must also follow the cycle direction
               # 丑->戌->未->丑 / 寅->巳->申->寅: (丑,戌) forms XING while (戌,丑) does not.
               # The direction is locked in by the implementation and `test_dizhi_utils`.

  class XingSubType(Enum):
    SANXING   = 0 # 丑未戌、寅巳申三刑
    ZIMAOXING = 1 # 子卯相刑
    ZIXING    = 2 # 自刑

    三刑   = SANXING
    子卯刑 = ZIMAOXING
    自刑   = ZIXING

  # The table is used to query the XING (刑) relation across all Dizhis.
  # XING relation is a directional relation.
  # 该表格用于查询地支之间的刑。
  # 相刑是有方向的。
  DIZHI_XING: Final[frozendict[XingDef, frozendict[tuple[Dizhi, ...], XingSubType]]] = frozendict({
    XingDef.STRICT : _dizhi_xing_strict(XingSubType),
    XingDef.LOOSE  : _dizhi_xing_loose(XingSubType),
  })

  # The table is used to query the CHONG (冲) relation across all Dizhis.
  # CHONG relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的冲。
  # 相冲是无方向的，两个地支之间互相相冲。
  DIZHI_CHONG: Final[frozenset[frozenset[Dizhi]]] = frozenset([frozenset(dz_tuple) for dz_tuple in (
    (Dizhi.子, Dizhi.午), (Dizhi.丑, Dizhi.未),
    (Dizhi.寅, Dizhi.申), (Dizhi.卯, Dizhi.酉),
    (Dizhi.辰, Dizhi.戌), (Dizhi.巳, Dizhi.亥),
  )])

  # The table is used to query the PO (破) relation across all Dizhis.
  # PO relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的破。
  # 相破是无方向的，两个地支之间互相破坏。
  DIZHI_PO: Final[frozenset[frozenset[Dizhi]]] = frozenset([frozenset(dz_tuple) for dz_tuple in (
    (Dizhi.子, Dizhi.酉), (Dizhi.卯, Dizhi.午),
    (Dizhi.辰, Dizhi.丑), (Dizhi.未, Dizhi.戌),
    (Dizhi.寅, Dizhi.亥), (Dizhi.巳, Dizhi.申),
  )])

  # The table is used to query the HAI (害, i.e. 穿) relation across all Dizhis.
  # HAI relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的害（即相穿）。
  # 相害是无方向的，两个地支之间两两相害。
  DIZHI_HAI: Final[frozenset[frozenset[Dizhi]]] = frozenset([frozenset(dz_tuple) for dz_tuple in (
    (Dizhi.子, Dizhi.未), (Dizhi.丑, Dizhi.午),
    (Dizhi.寅, Dizhi.巳), (Dizhi.卯, Dizhi.辰),
    (Dizhi.申, Dizhi.亥), (Dizhi.酉, Dizhi.戌),
  )])

  # The table is used to query the SHENG (生) relation across all Dizhis.
  # SHENG relation is a uni-directional relation.
  # Yinyang is not considered in SHENG relation - only Wuxing is considered.
  # 该表格用于查询地支之间的相生关系。
  # 相生关系是单向的。如丙寅相生，则是寅木生丙火。
  # 地支相生不考虑阴阳，只考虑五行。
  DIZHI_SHENG: Final[frozenset[tuple[Dizhi, Dizhi]]] = _dizhi_sheng(BaziRules.DIZHI_TRAITS)

  # The table is used to query the KE (克) relation across all Dizhis.
  # KE relation is a uni-directional relation.
  # Yinyang is not considered in KE relation - only Wuxing is considered.
  # 该表格用于查询地支之间的相克关系。
  # 相克关系是单向的。如寅丑相克，则是寅木克丑土。
  # 地支相克不考虑阴阳，只考虑五行。
  DIZHI_KE: Final[frozenset[tuple[Dizhi, Dizhi]]] = _dizhi_ke(BaziRules.DIZHI_TRAITS)



class ShenshaRules:
  '''Rules for Shensha / 神煞'''

  # The table is used to find out TAOHUA (桃花). A.k.a. XIANCHI TAOHUA (咸池桃花).
  # 该表格用于查询桃花星。桃花即咸池桃花。
  TAOHUA: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    Dizhi(k_str) : Dizhi(v_str)
    for k_strs, v_str in {
      '申子辰' : '酉',
      '寅午戌' : '卯',
      '亥卯未' : '子',
      '巳酉丑' : '午',
    }.items()
    for k_str in k_strs
  })

  # The table is used to find out HONGYAN (红艳). From 《三命通会》: "甲乙逢午、丙寅、丁未、
  # 戊辰、己辰、庚戌、辛酉、壬子、癸申，为红艳煞".
  # 该表格用于查询红艳星。出自《三命通会》。
  # One cell diverges across text lineages: the prose above reads 乙→午 (问真八字 follows it), while
  # this table takes the verse lineage 「甲乙午申庚见戌」 → 乙→申 (both pinned in #69's research).
  # 乙 一格两谱系分叉:散文本作乙午(问真等从之),本表从歌诀本作乙申。
  # A variant table reading 庚申/癸戌 (instead of 庚戌/癸申) also circulates, but it is
  # attested only in a single aggregator-site text lineage, so it is not adopted here
  # (research of 2026-08-04, see issue #69).
  # 另有庚申/癸戌异表流传，但仅见聚合站单一文本谱系，未采（2026-08-04 考证，详见 #69）。
  HONGYAN: Final[frozendict[Tiangan, Dizhi]] = frozendict({
    Tiangan.甲 : Dizhi.午,
    Tiangan.乙 : Dizhi.申,
    Tiangan.丙 : Dizhi.寅,
    Tiangan.丁 : Dizhi.未,
    Tiangan.戊 : Dizhi.辰,
    Tiangan.己 : Dizhi.辰,
    Tiangan.庚 : Dizhi.戌,
    Tiangan.辛 : Dizhi.酉,
    Tiangan.壬 : Dizhi.子,
    Tiangan.癸 : Dizhi.申,
  })

  # The table is used to find out HONGLUAN (红鸾).
  # 该表格用于查询红鸾星。
  HONGLUAN: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    Dizhi.子 : Dizhi.卯,
    Dizhi.丑 : Dizhi.寅,
    Dizhi.寅 : Dizhi.丑,
    Dizhi.卯 : Dizhi.子,
    Dizhi.辰 : Dizhi.亥,
    Dizhi.巳 : Dizhi.戌,
    Dizhi.午 : Dizhi.酉,
    Dizhi.未 : Dizhi.申,
    Dizhi.申 : Dizhi.未,
    Dizhi.酉 : Dizhi.午,
    Dizhi.戌 : Dizhi.巳,
    Dizhi.亥 : Dizhi.辰,
  })

  # The table is used to find out TIANXI (天喜).
  # 该表格用于查询天喜星。
  TIANXI: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    Dizhi.子 : Dizhi.酉,
    Dizhi.丑 : Dizhi.申,
    Dizhi.寅 : Dizhi.未,
    Dizhi.卯 : Dizhi.午,
    Dizhi.辰 : Dizhi.巳,
    Dizhi.巳 : Dizhi.辰,
    Dizhi.午 : Dizhi.卯,
    Dizhi.未 : Dizhi.寅,
    Dizhi.申 : Dizhi.丑,
    Dizhi.酉 : Dizhi.子,
    Dizhi.戌 : Dizhi.亥,
    Dizhi.亥 : Dizhi.戌,
  })

  # The table is used to find out YIMA (驿马).
  # 该表格用于查询驿马星。
  YIMA: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    Dizhi(k_str) : Dizhi(v_str)
    for k_strs, v_str in {
      '申子辰' : '寅',
      '寅午戌' : '申',
      '亥卯未' : '巳',
      '巳酉丑' : '亥',
    }.items()
    for k_str in k_strs
  })
