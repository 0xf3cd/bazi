# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import itertools
from collections.abc import Callable
from enum import Enum
from typing import Final, TypeVar

from .common import frozendict
from .data_types import TraitTuple, HiddenTianganDict
from .defines import Tiangan, Dizhi, Ganzhi, Wuxing, Yinyang, DizhiRelation


# All rule tables are plain `Final` class attributes, built once at import time.
# `Final` is the reassignment guard, enforced by mypy; there is no runtime guard.


# Computed tables are built by module-level `_lower_snake` builders because
# loops/comprehensions in a class body cannot see class-level names.
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
    middle branch; `WIDE` accepts any two members of one 三合 group and returns the
    third. 狭义拱合只收三合缺中神；广义拱合收三合任意两支并拱出第三支。

    Sources / 出处:
    - Narrow: https://services.shen88.cn/bazisuanming/pc-74297.html
    - Wide: https://www.sohu.com/a/471337600_310486
    '''
    NARROW = 0
    WIDE   = 1

  class GongDef(Enum):
    '''Source-backed profiles for the contextual conditions of 拱合 / 拱会.
    拱合、拱会成立条件的来源档案；只列有出处的组合，不把分歧轴任意拼接。

    - SAME_STEM_NARROW: participants share one Tiangan; narrow 拱合 plus 拱会.
      两柱同干；狭义拱合并收拱会。
    - SAME_STEM_WIDE: the same Tiangan condition with wide 拱合 plus 拱会.
      两柱同干；广义拱合并收拱会。
    - TRANSFORMING_NARROW: the query scope exposes a Tiangan of the formed Wuxing;
      narrow 拱合 plus 拱会. 查询范围透出化神；狭义拱合并收拱会。
    - LU_NARROW: the query scope exposes 乙 / 丁 / 辛 / 癸 for the formed Wuxing;
      narrow 拱合 only. Its source does not extend the rule to 拱会.
      查询范围见所拱五行的乙、丁、辛、癸禄字；只收狭义拱合，来源未把本条扩到拱会。

    Candidate positions are entry-specific: `search_ganzhis` uses adjacent occurrences, while
    `discover_mutual_ganzhis` uses pairs spanning its two input scopes.
    候选柱位由入口决定：`search_ganzhis` 只查相邻具体出现，`discover_mutual_ganzhis`
    查横跨两组输入的柱位对。

    No change should be made to the existing definitions. Only add new definitions.

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

  # Gong relations require position and Tiangan context in batch queries.
  # 拱局批量查询需要柱位与天干上下文。
  GONG_RELATIONS: Final[tuple[DizhiRelation, ...]] = (DizhiRelation.拱合, DizhiRelation.拱会)

  # The structural 拱合 scope selected by each Gong profile / 各拱局来源档案所用的拱合结构口径。
  GONG_GONGHE_SCOPE: Final[frozendict[GongDef, GongheDef]] = frozendict({
    GongDef.SAME_STEM_NARROW    : GongheDef.NARROW,
    GongDef.SAME_STEM_WIDE      : GongheDef.WIDE,
    GongDef.TRANSFORMING_NARROW : GongheDef.NARROW,
    GongDef.LU_NARROW           : GongheDef.NARROW,
  })

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

  # A 三会 group missing its middle branch. Some modern sources call it 拱会; 盲派 and
  # 梁湘润系 call it 夹. The structure is the same, and this library reports the selected
  # public name `DizhiRelation.拱会` while preserving the terminology split here.
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

    ANHE is non-directional, so every direct or batch query entry sees the same table per
    definition -- there is no entry-layer divergence like `XingDef`'s.
    暗合无方向，每个直接或批量查法入口看到的表一致——无 `XingDef` 那种入口层分歧。

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

  # Gonghe returns the arched branch, not the formed Wuxing. Narrow scope accepts only a
  # missing middle branch; wide scope accepts any two members of one 三合 group.
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
      batch query entries compare as multisets and cannot.
      入口层：方向（谁刑谁）只有按序查法（`dizhi_utils.xing`）可见；批量查法入口按多重集
      比对，看不出方向。

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


_GroupValue = TypeVar('_GroupValue')


def _expand_dizhi_groups(
  groups: dict[str, str],
  value_from_str: Callable[[str], _GroupValue],
) -> frozendict[Dizhi, _GroupValue]:
  return frozendict({
    Dizhi(key) : value_from_str(target)
    for keys, target in groups.items()
    for key in keys
  })


class ShenshaRules:
  '''Rules for Shensha / 神煞.

  How to count the sources cited below / 下面的出处怎么计数:

  Two modern compilations recur throughout this class -- 问真《神煞大全》 and 高人 -- and
  **they do not count as two independent sources.** Where they overlap it is the 口诀 that
  overlaps -- and 口诀 are common property, quoted alike by everyone. Where each house writes
  its own prose, the two diverge, and on two rules they disagree outright: 天乙, where each
  picks a different 歌诀 version (高人 names which one it uses), and 红艳, where 问真 reads
  乙 -> 午 against 高人's 乙 -> 申 -- the same split `HONGYAN` below already traces to
  散文本 vs 歌诀本.

  So "one is a copy of the other" is ruled out; "both draw on shared upstream material --
  the 口诀 and the classical 白文 -- and then write their own" fits. **Which one is upstream,
  and whether either read the other, nothing consulted settles.**

  The practical rule this yields: **a 口诀 quoted identically by two houses is one piece of
  evidence, not two** -- 口诀 are common property. Where both are named on one line below,
  read it as one modern reading attested twice, not as two independent readings that agree.

  下面反复出现的现代两家(问真《神煞大全》与高人)**不作两个独立来源计数**。
  两家重合之处重合的是**口诀**——而口诀是公共财产,人人引得一样。各家自撰的散文则彼此分开,
  并且在两条规则上正面分歧:天乙各择一个歌诀版本(高人并自述用的是哪一个),
  红艳问真作乙午而高人作乙申——即下面 `HONGYAN` 已记的散文本／歌诀本之分。

  故「一方是另一方的拷贝」不成立,「两家共享上游材料(口诀与古籍白文)再各自编写」与事实相容;
  **哪一份是上游、是否互相读过,所查材料无一裁定。**

  由此得到的记账规则:**两家引同一首口诀,是一份证据不是两份**——口诀本是公共财产。
  下文某一行同时点名两家时,读作「同一个现代读法被记录了两次」,不是「两个独立读法互相印证」。
  '''

  # The table is used to find out TAOHUA (桃花). A.k.a. XIANCHI TAOHUA (咸池桃花).
  # 该表格用于查询桃花星。桃花即咸池桃花。
  TAOHUA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '酉',
      '寅午戌' : '卯',
      '亥卯未' : '子',
      '巳酉丑' : '午',
    },
    Dizhi,
  )

  # The table is used to find out HONGYAN (红艳). From 《三命通会》: "甲乙逢午、丙寅、丁未、
  # 戊辰、己辰、庚戌、辛酉、壬子、癸申，为红艳煞".
  # 该表格用于查询红艳星。出自《三命通会》。
  # One cell diverges across text lineages: the prose above reads 乙→午 (问真八字 follows it), while
  # this table takes the verse lineage 「甲乙午申庚见戌」 → 乙→申 (both pinned in #69's research).
  # 乙 一格两谱系分叉：散文本作乙午（问真等从之），本表从歌诀本作乙申。
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
  YIMA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '寅',
      '寅午戌' : '申',
      '亥卯未' : '巳',
      '巳酉丑' : '亥',
    },
    Dizhi,
  )

  # HUAGAI (华盖) is the tomb/storage branch of each 三合 group. From 《三命通会》, as quoted
  # in Yuan Shushan's 《命理探源》:「华盖者，形象之称也……故以三合本库为华盖也。如寅午戌
  # 见戌，火库也，巳酉丑见丑，金库也，馀仿此。」
  # 华盖取各三合局的墓库；上引《三命通会》原文转引自袁树珊《命理探源》。
  # Source / 出处: https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb (issue #16).
  # Additional YEAR_AND_DAY anchor sources / YEAR_AND_DAY 查法锚补充出处: 百度百科「神煞」、高人。
  # Supported readings / 支持口径: `_ANCHOR_CHOICES['huagai_anchor']`.
  HUAGAI: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '寅午戌' : '戌',
      '亥卯未' : '未',
      '申子辰' : '辰',
      '巳酉丑' : '丑',
    },
    Dizhi,
  )

  # JIANGXING (将星) is the middle / Diwang (帝旺) branch of each 三合 group,
  # enumerated group by group in 《三命通会·卷三·论灾煞》.
  # 将星取各三合局的帝旺位；《三命通会·卷三·论灾煞》逐组明列。
  # Table source / 表值出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #152).
  # Cross-check / 校核: https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb (issue #152).
  # Supported readings / 支持口径: `_ANCHOR_CHOICES['jiangxing_anchor']`.
  # Anchor source / 查法锚出处: https://book.taiyi.me/命/神煞大全#将星 (issue #152).
  JIANGXING: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '子',
      '寅午戌' : '午',
      '亥卯未' : '卯',
      '巳酉丑' : '酉',
    },
    Dizhi,
  )

  # ZAISHA (灾煞) is the branch opposing each 三合 group's Jiangxing (将星),
  # enumerated group by group in 《三命通会·卷三·论灾煞》.
  # 灾煞取各三合局将星的对冲支；《三命通会·卷三·论灾煞》逐组明列。
  # Table source / 表值出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #174).
  # Supported readings / 支持口径: `_ANCHOR_CHOICES['zaisha_anchor']`.
  # Modern compilations also call this 白虎煞; the public rule and display retain the
  # classical name 灾煞 because other distinct 白虎 tables circulate.
  # 现代汇编亦称白虎煞；另有不同白虎表流传，故公开规则与显示仍用古名灾煞。
  ZAISHA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '午',
      '寅午戌' : '子',
      '巳酉丑' : '卯',
      '亥卯未' : '酉',
    },
    Dizhi,
  )

  # JIESHA (劫煞) is the Jue (绝) branch of each 三合 group's Wuxing,
  # enumerated group by group in 《三命通会·卷三·论劫煞亡神》.
  # 劫煞取各三合局五行的绝位；《三命通会·卷三·论劫煞亡神》逐组明列。
  # Table source / 表值出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #153).
  # Supported readings / 支持口径: `_ANCHOR_CHOICES['jiesha_anchor']`.
  # Anchor source / 查法锚出处: https://book.taiyi.me/命/神煞大全#劫煞 (issue #153).
  JIESHA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '巳',
      '寅午戌' : '亥',
      '亥卯未' : '申',
      '巳酉丑' : '寅',
    },
    Dizhi,
  )

  # WANGSHEN (亡神) is the Linguan (临官) branch of each 三合 group's Wuxing,
  # enumerated group by group in 《三命通会·卷三·论劫煞亡神》.
  # 亡神取各三合局五行的临官位；《三命通会·卷三·论劫煞亡神》逐组明列。
  # Table source / 表值出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #154).
  # Supported readings / 支持口径: `_ANCHOR_CHOICES['wangshen_anchor']`.
  # Anchor source / 查法锚出处: https://book.taiyi.me/命/神煞大全#亡神 (issue #154).
  WANGSHEN: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '亥',
      '寅午戌' : '巳',
      '亥卯未' : '寅',
      '巳酉丑' : '申',
    },
    Dizhi,
  )

  # GUCHEN (孤辰) and GUASU (寡宿) are the branches one step forward and one step back
  # from the birth-year branch's direction group in 《三命通会·卷三·论孤辰寡宿》.
  # 孤辰、寡宿分别取出生年支所属方位组的进前一辰、退后一辰。
  # Rule source / 规则出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #161).
  # Table source / 表值出处: https://book.taiyi.me/命/神煞大全#孤辰 and https://book.taiyi.me/命/神煞大全#寡宿 (issue #161).
  # Anchor source / 查法锚出处: the same entries / 同上两条 (issue #161).
  # The same section quotes the interpretation-level exclusions 「连属不言孤寡」 and
  # 「支干朝会包裹贵人」. They do not erase the raw locations here.
  # 同节所引「连属不言孤寡」及贵人包裹条款属解释层豁免，不抹去本表给出的原始命中位置。
  GUCHEN: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '亥子丑' : '寅',
      '寅卯辰' : '巳',
      '巳午未' : '申',
      '申酉戌' : '亥',
    },
    Dizhi,
  )

  GUASU: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '亥子丑' : '戌',
      '寅卯辰' : '丑',
      '巳午未' : '辰',
      '申酉戌' : '未',
    },
    Dizhi,
  )

  # LUSHEN (禄神) uses the same ten-stem Lu locations as `BaziRules.TIANGAN_LU`.
  # 禄神与十干禄位共用一张表。
  # Source / 出处: 《三命通会·卷三·论十干禄》 and https://book.taiyi.me/命/神煞大全#禄神 (issue #162).
  LUSHEN: Final[frozendict[Tiangan, Dizhi]] = BaziRules.TIANGAN_LU

  # JINYU (金舆) falls two branches after each Tiangan's Lu (禄前二辰).
  # 金舆取各天干禄位前二辰。
  # Table sources / 表值出处 (issue #163):
  # - 《三命通会·卷三·论金舆》: https://book.taiyi.me/命/三命通会/三命通会(卷三)
  # - 袁树珊《命理探源》: https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
  JINYU: Final[frozendict[Tiangan, Dizhi]] = frozendict({
    Tiangan.甲 : Dizhi.辰,
    Tiangan.乙 : Dizhi.巳,
    Tiangan.丙 : Dizhi.未,
    Tiangan.丁 : Dizhi.申,
    Tiangan.戊 : Dizhi.未,
    Tiangan.己 : Dizhi.申,
    Tiangan.庚 : Dizhi.戌,
    Tiangan.辛 : Dizhi.亥,
    Tiangan.壬 : Dizhi.丑,
    Tiangan.癸 : Dizhi.寅,
  })

  # KUIGANG (魁罡) is fixed to four day pillars in both 《渊海子平·论魁罡》
  # and 《三命通会·卷六·魁罡》.
  # 魁罡固定取四个日柱，两书所载相同。
  # Sources / 出处 (issue #175):
  # - https://book.taiyi.me/命/子平推命/渊海子平(神煞篇)
  # - https://book.taiyi.me/命/三命通会/三命通会(卷六)
  KUIGANG: Final[frozenset[Ganzhi]] = frozenset((
    Ganzhi.from_str('庚辰'),
    Ganzhi.from_str('壬辰'),
    Ganzhi.from_str('戊戌'),
    Ganzhi.from_str('庚戌'),
  ))

  # TIANSHE (天赦) matches the day pillar to the season of the Month Commander:
  # spring 戊寅, summer 甲午, autumn 戊申, and winter 甲子.
  # 天赦按月令所属四时查日柱：春戊寅、夏甲午、秋戊申、冬甲子。
  # Table sources / 表值出处 (issue #176):
  # - 《三命通会·卷三·论天月德》: https://book.taiyi.me/命/三命通会/三命通会(卷三)
  # - 《渊海子平》, as quoted in Yuan Shushan's 《命理探源》:
  #   https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
  # Anchor source / 查法锚出处: https://book.taiyi.me/命/神煞大全#天赦日 (issue #176).
  TIANSHE: Final[frozendict[Dizhi, Ganzhi]] = _expand_dizhi_groups(
    {
      '寅卯辰' : '戊寅',
      '巳午未' : '甲午',
      '申酉戌' : '戊申',
      '亥子丑' : '甲子',
    },
    Ganzhi.from_str,
  )

  class YangrenDef(Enum):
    '''The definitions shared by YANGREN (羊刃 / 阳刃) and FEIREN (飞刃).
    Yangren readings disagree on whether Yin Tiangans have Yangren and where it falls;
    each Feiren profile takes the branch opposite the corresponding Yangren profile.
    羊刃（阳刃）与飞刃共用的三种定义。羊刃口径分歧在阴干有无刃及刃位；每套飞刃均取
    对应羊刃定义的对冲支。

    - ZIPING: only the five Yang Tiangans have 阳刃.
      子平法：仅五阳干有阳刃。
    - LUMING: all ten Tiangans have Yangren on the branch immediately after their Lu (禄).
      古禄命法：十干皆有羊刃，取禄前一辰。
    - DIWANG: all ten Tiangans take their Diwang (帝旺) branch; the modern charting side
      uses this table -- 问真 and 高人 both, which is one source here, not two
      (see this class's docstring).
      十干各取帝旺位；现代排盘一侧采用此表——问真与高人皆然，而这两家算一份不算两份，
      见本类 docstring。

    For Feiren / 飞刃:
    - ZIPING: only the five Yang Tiangans have Feiren, opposite their 阳刃.
      子平法：仅五阳干有飞刃，取阳刃对冲支。
    - LUMING: all ten Tiangans take the branch opposite their LUMING Yangren.
      古禄命法：十干皆有飞刃，取古禄命羊刃对冲支。
    - DIWANG: all ten Tiangans take the branch opposite their Diwang (帝旺) branch.
      十干各取帝旺位的对冲支。

    `BaziSchool.yangren_def` and `BaziSchool.feiren_def` are independent: a chart may
    combine any Yangren profile with any Feiren profile.
    `BaziSchool.yangren_def` 与 `BaziSchool.feiren_def` 两个旋钮彼此独立，可任意组合羊刃与飞刃口径。

    Yangren sources / 羊刃出处:
    - 《三命通会·卷三·论羊刃》 records both the ZIPING and LUMING readings:
      https://m.guwendao.net/guwen/bookv_d6957d252951.aspx
    - Modern DIWANG table: https://book.taiyi.me/命/神煞大全 and
      https://github.com/gaorenyes/gaorenyes.github.io

    Feiren sources / 飞刃出处:
    - 《三命通会·卷三·论羊刃》:
      https://book.taiyi.me/命/三命通会/三命通会(卷三)
    - 《渊海子平·论阳刃》 supplies the ZIPING yang-stems-only basis:
      https://book.taiyi.me/命/子平推命/渊海子平(神煞篇)
    - Modern DIWANG table:
      https://github.com/gaorenyes/gaorenyes.github.io/blob/817ad1f8f463d489087ac6c44ec69165e1181454/b/index.html#L748

    No change should be made to the existing definitions. Only add new definitions.
    '''
    ZIPING = 0
    LUMING = 1
    DIWANG = 2

  YANGREN: Final[frozendict[YangrenDef, frozendict[Tiangan, Dizhi | None]]] = frozendict({
    YangrenDef.ZIPING : frozendict({
      Tiangan.甲 : Dizhi.卯,
      Tiangan.乙 : None,
      Tiangan.丙 : Dizhi.午,
      Tiangan.丁 : None,
      Tiangan.戊 : Dizhi.午,
      Tiangan.己 : None,
      Tiangan.庚 : Dizhi.酉,
      Tiangan.辛 : None,
      Tiangan.壬 : Dizhi.子,
      Tiangan.癸 : None,
    }),
    YangrenDef.LUMING : frozendict({
      Tiangan.甲 : Dizhi.卯,
      Tiangan.乙 : Dizhi.辰,
      Tiangan.丙 : Dizhi.午,
      Tiangan.丁 : Dizhi.未,
      Tiangan.戊 : Dizhi.午,
      Tiangan.己 : Dizhi.未,
      Tiangan.庚 : Dizhi.酉,
      Tiangan.辛 : Dizhi.戌,
      Tiangan.壬 : Dizhi.子,
      Tiangan.癸 : Dizhi.丑,
    }),
    YangrenDef.DIWANG : frozendict({
      Tiangan.甲 : Dizhi.卯,
      Tiangan.乙 : Dizhi.寅,
      Tiangan.丙 : Dizhi.午,
      Tiangan.丁 : Dizhi.巳,
      Tiangan.戊 : Dizhi.午,
      Tiangan.己 : Dizhi.巳,
      Tiangan.庚 : Dizhi.酉,
      Tiangan.辛 : Dizhi.申,
      Tiangan.壬 : Dizhi.子,
      Tiangan.癸 : Dizhi.亥,
    }),
  })

  FEIREN: Final[frozendict[YangrenDef, frozendict[Tiangan, Dizhi | None]]] = frozendict({
    YangrenDef.ZIPING : frozendict({
      Tiangan.甲 : Dizhi.酉,
      Tiangan.乙 : None,
      Tiangan.丙 : Dizhi.子,
      Tiangan.丁 : None,
      Tiangan.戊 : Dizhi.子,
      Tiangan.己 : None,
      Tiangan.庚 : Dizhi.卯,
      Tiangan.辛 : None,
      Tiangan.壬 : Dizhi.午,
      Tiangan.癸 : None,
    }),
    YangrenDef.LUMING : frozendict({
      Tiangan.甲 : Dizhi.酉,
      Tiangan.乙 : Dizhi.戌,
      Tiangan.丙 : Dizhi.子,
      Tiangan.丁 : Dizhi.丑,
      Tiangan.戊 : Dizhi.子,
      Tiangan.己 : Dizhi.丑,
      Tiangan.庚 : Dizhi.卯,
      Tiangan.辛 : Dizhi.辰,
      Tiangan.壬 : Dizhi.午,
      Tiangan.癸 : Dizhi.未,
    }),
    YangrenDef.DIWANG : frozendict({
      Tiangan.甲 : Dizhi.酉,
      Tiangan.乙 : Dizhi.申,
      Tiangan.丙 : Dizhi.子,
      Tiangan.丁 : Dizhi.亥,
      Tiangan.戊 : Dizhi.子,
      Tiangan.己 : Dizhi.亥,
      Tiangan.庚 : Dizhi.卯,
      Tiangan.辛 : Dizhi.寅,
      Tiangan.壬 : Dizhi.午,
      Tiangan.癸 : Dizhi.巳,
    }),
  })

  class TianyiDef(Enum):
    '''The definitions of TIANYI GUIREN (天乙贵人), kept as complete source-backed
    profiles because the formula, Geng/Xin grouping, and daytime/nighttime tables are
    not independent axes. 天乙贵人的查法定义；口诀分组与昼夜表彼此牵连，因此按出处保留
    完整 profile，不作无出处的自由组合。

    - GENG_WITH_JIA_WU: the traditional merged formula「甲戊庚牛羊……六辛逢马虎」.
      传统合并表：庚与甲戊同组，辛取午寅。
    - GENG_WITH_XIN: the modified merged formula「甲戊兼牛羊……庚辛逢马虎」.
      改口诀合并表：庚改与辛同组。
    - YANGGUI: the daytime / Yang Guiren half of the `GENG_WITH_JIA_WU` lineage.
      阳贵表：与阴贵表合并即为庚随甲戊的传统合并表。
    - YINGUI: the nighttime / Yin Guiren half of that lineage; the source that reads
      「六辛逢午马」by 分承 gives this same ten-stem table.
      阴贵表：与阳贵表合并即为传统合并表；「六辛逢午马」按分承所得十干表与本表相同。

    `GENG_WITH_JIA_WU` has the thicker classical lineage and is also the merged table
    used by 问真. `BaziSchool.tianyi_def` is independent of
    `BaziSchool.tianyi_anchor`; day/night boundary selection is deliberately outside these tables.
    传统合并表的古籍谱系较厚，问真亦采用；`BaziSchool.tianyi_def` 与
    `BaziSchool.tianyi_anchor` 相互独立，本表不代选昼夜界线。

    Sources / 出处:
    - 袁树珊《命理探源》引古歌「甲戊庚牛羊……六辛逢马虎」:
      https://upload.wikimedia.org/wikipedia/commons/5/52/NLC416-07jh011647-5318_命理探源.pdf
    - The two merged formulas / 两版合并口诀:
      https://www.click2macao.com/2024/04/10/tygrkjdz/
    - The Yang/Yin tables and the 分承 reading of「午马」/ 阳贵、阴贵表与「午马」分承:
      https://www.usece.com/3858/
    - 问真 profile / 问真口径: https://book.taiyi.me/命/神煞大全

    No change should be made to the existing definitions. Only add new definitions.
    '''
    GENG_WITH_JIA_WU = 0
    GENG_WITH_XIN = 1
    YANGGUI = 2
    YINGUI = 3

  TIANYI: Final[frozendict[TianyiDef, frozendict[Tiangan, frozenset[Dizhi]]]] = frozendict({
    TianyiDef.GENG_WITH_JIA_WU : frozendict({
      Tiangan.甲 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.丙 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.戊 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.己 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.庚 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.辛 : frozenset((Dizhi.午, Dizhi.寅)),
      Tiangan.壬 : frozenset((Dizhi.卯, Dizhi.巳)),
      Tiangan.癸 : frozenset((Dizhi.卯, Dizhi.巳)),
    }),
    TianyiDef.GENG_WITH_XIN : frozendict({
      Tiangan.甲 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.丙 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.戊 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.己 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.庚 : frozenset((Dizhi.午, Dizhi.寅)),
      Tiangan.辛 : frozenset((Dizhi.午, Dizhi.寅)),
      Tiangan.壬 : frozenset((Dizhi.卯, Dizhi.巳)),
      Tiangan.癸 : frozenset((Dizhi.卯, Dizhi.巳)),
    }),
    TianyiDef.YANGGUI : frozendict({
      Tiangan.甲 : frozenset((Dizhi.未,)),
      Tiangan.乙 : frozenset((Dizhi.申,)),
      Tiangan.丙 : frozenset((Dizhi.酉,)),
      Tiangan.丁 : frozenset((Dizhi.亥,)),
      Tiangan.戊 : frozenset((Dizhi.丑,)),
      Tiangan.己 : frozenset((Dizhi.子,)),
      Tiangan.庚 : frozenset((Dizhi.丑,)),
      Tiangan.辛 : frozenset((Dizhi.寅,)),
      Tiangan.壬 : frozenset((Dizhi.卯,)),
      Tiangan.癸 : frozenset((Dizhi.巳,)),
    }),
    TianyiDef.YINGUI : frozendict({
      Tiangan.甲 : frozenset((Dizhi.丑,)),
      Tiangan.乙 : frozenset((Dizhi.子,)),
      Tiangan.丙 : frozenset((Dizhi.亥,)),
      Tiangan.丁 : frozenset((Dizhi.酉,)),
      Tiangan.戊 : frozenset((Dizhi.未,)),
      Tiangan.己 : frozenset((Dizhi.申,)),
      Tiangan.庚 : frozenset((Dizhi.未,)),
      Tiangan.辛 : frozenset((Dizhi.午,)),
      Tiangan.壬 : frozenset((Dizhi.巳,)),
      Tiangan.癸 : frozenset((Dizhi.卯,)),
    }),
  })

  class WenchangDef(Enum):
    '''The definitions of WENCHANG (文昌). The two readings differ in the 辛 cell only;
    the other nine stems agree across every source consulted.
    文昌的查法定义。两读只在辛一格分歧，其余九干各家全同。

    - XIN_ZI: 辛 → 子.
    - XIN_XU: 辛 → 戌.

    `XIN_ZI` is the default: it carries both the 民国 print lineage (《命理探源》) and the
    modern mainstream. `XIN_XU` rests on 《星学大成》, whose two transcriptions agree
    verbatim and whose prose gives a reason rather than reading like a copying slip.
    默认取 XIN_ZI：民国刊本与现代主流两条谱系都指向它。XIN_XU 出自《星学大成》，
    两个转录逐字相同，且散文给了理由，不像抄讹。

    This is the 子平 star (食神 at its 临官/长生), distinct from `WENCHANGGUI` below and
    from 文星贵 (「甲马乙蛇丙戊猴」), a third star this library does not carry.
    本表是子平法的文昌（食神之临官、长生），与下方禄命法的文昌贵是两颗星，也不是文星贵。

    Two things about the sources are worth carrying here, because a later reader would
    otherwise have to re-derive them:
    出处上有两件事写在这里，免得后来者重新推一遍：

    - 《命理探源》 spells out only 甲乙丙丁戊己 in prose and closes with 「庚辛壬癸仿此」.
      The last four stems come from the verse it quotes (「庚猪辛鼠壬逢虎，癸人见兔入云梯」),
      so 辛 → 子 in `XIN_ZI` rests on that verse, not on the prose.
      探源散文只逐条写到己，末句「庚辛壬癸仿此」；后四干出自它所引口诀，
      故 `XIN_ZI` 的辛→子依据是口诀而非散文。
    - 《星学大成》 writes 辛戌 in the verse itself and explains it
      (「独辛不以生而以戌为文昌，戌在辛之方位」), so `XIN_XU` is a considered reading
      rather than a copying slip.
      《星学大成》口诀本身即作辛戌，且散文给了理由，故 `XIN_XU` 是自成一说，不是抄讹。

    Sources / 出处:
    - 袁树珊《命理探源》卷三「以日主为主，如甲见己，乙见午是也」:
      https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
    - 问真《神煞大全》: https://book.taiyi.me/命/神煞大全
    - 明·万民英《星学大成》「论文昌」: https://book.taiyi.me/命/星学大成
    - 同书四库全书本，与上一条逐字相同（两处转录的底本关系未见声明）:
      https://zh.wikisource.org/zh-hans/星學大成_(四庫全書本)/全覽

    No change should be made to the existing definitions. Only add new definitions.
    '''
    XIN_ZI = 0
    XIN_XU = 1

  # The tables are used to find out WENCHANG (文昌).
  # 这些表格用于查询文昌星。
  # Which pillar supplies the anchor stem is a school knob -- see `_ANCHOR_CHOICES`.
  # Where the star is then looked for is 四柱地支 in both modern sources; none of the
  # classical sources consulted for this star states a search range, so that part rests on
  # the modern side alone -- and the two houses there count as one source, not two
  # (see this class's docstring).
  # 锚取哪一柱属流派旋钮，见 `_ANCHOR_CHOICES`；被查位置两家现代查法均作四柱地支，
  # 而为本星查过的古籍都不交代查哪几柱，故此处只有现代一侧的出处——
  # 而那一侧的两家算一份不算两份，见本类 docstring。
  WENCHANG: Final[frozendict[WenchangDef, frozendict[Tiangan, Dizhi]]] = frozendict({
    WenchangDef.XIN_ZI : frozendict({
      Tiangan.甲 : Dizhi.巳,
      Tiangan.乙 : Dizhi.午,
      Tiangan.丙 : Dizhi.申,
      Tiangan.丁 : Dizhi.酉,
      Tiangan.戊 : Dizhi.申,
      Tiangan.己 : Dizhi.酉,
      Tiangan.庚 : Dizhi.亥,
      Tiangan.辛 : Dizhi.子,
      Tiangan.壬 : Dizhi.寅,
      Tiangan.癸 : Dizhi.卯,
    }),
    WenchangDef.XIN_XU : frozendict({
      Tiangan.甲 : Dizhi.巳,
      Tiangan.乙 : Dizhi.午,
      Tiangan.丙 : Dizhi.申,
      Tiangan.丁 : Dizhi.酉,
      Tiangan.戊 : Dizhi.申,
      Tiangan.己 : Dizhi.酉,
      Tiangan.庚 : Dizhi.亥,
      Tiangan.辛 : Dizhi.戌,
      Tiangan.壬 : Dizhi.寅,
      Tiangan.癸 : Dizhi.卯,
    }),
  })

  # The table is used to find out WENCHANGGUI (文昌贵), the 禄命法 star of the same name
  # family. It agrees with `WENCHANG` on 甲 → 巳 and 戊 → 申 and differs on the other eight
  # stems, so the two are kept apart rather than merged into one entry.
  # 该表格用于查询文昌贵，禄命法中的同名近亲。它与文昌在甲（巳）、戊（申）两格相同，
  # 其余八干皆异，因此两者分列，不并成一条。
  # Anchor: 年干. No school divergence is attested, so this table takes no knob.
  # 锚为年干；未见流派分歧，故本表不设旋钮。
  # Sources / 出处:
  # - 《五行精纪注释》卷十三「以年干查：甲见巳，乙见亥，丙见戌，丁见辰，戊见申，己见午，
  #   庚见寅，辛见未，壬见卯，癸见丑」-- states the anchor and spells the whole table out:
  #   https://www.suanzhun.net/book/2728.html
  # - 宋·廖中《五行精纪》: https://book.taiyi.me/命/五行精纪/五行精纪(下)
  # - 《三命通会》卷三，附于「论太极贵」节内:
  #   https://book.taiyi.me/命/三命通会/三命通会(卷三)
  WENCHANGGUI: Final[frozendict[Tiangan, Dizhi]] = frozendict({
    Tiangan.甲 : Dizhi.巳,
    Tiangan.乙 : Dizhi.亥,
    Tiangan.丙 : Dizhi.戌,
    Tiangan.丁 : Dizhi.辰,
    Tiangan.戊 : Dizhi.申,
    Tiangan.己 : Dizhi.午,
    Tiangan.庚 : Dizhi.寅,
    Tiangan.辛 : Dizhi.未,
    Tiangan.壬 : Dizhi.卯,
    Tiangan.癸 : Dizhi.丑,
  })

  class TaijiDef(Enum):
    '''The definitions of TAIJI GUIREN (太极贵人). The two readings differ in 壬癸 only.
    太极贵人的查法定义。两读只在壬癸分歧。

    - REN_GUI_BOTH: 壬 and 癸 each take both 巳 and 申.
    - REN_SI_GUI_SHEN: 壬 takes 巳, 癸 takes 申.

    This is not a dispute between two sources -- 《五行精纪》 carries both readings in one
    line, marking the second with 「一作」:
    这不是两家表之争 ——《五行精纪》一句之内并存两读，第二读由「一作」引出：

        壬巳癸申一作壬癸巳申偏喜美，封侯万户即三公

    `REN_GUI_BOTH` is the default: it is the reading the verse's 「一作」 points to, and the
    one both modern sources take.
    默认取 REN_GUI_BOTH：它既是歌诀「一作」所指的那读，也是现代两家所取。

    Two flaws in the received text are recorded here rather than silently repaired:
    两处原文硬伤记在这里，不悄悄修补：

    - Two digital transcriptions of 《三命通会》 (taiyi, 算准网) read 「壬癸水先得则生，
      后得巳而纳」, where the 四庫全書 edition on Wikisource reads 「壬癸水先得申而生後得巳而納」.
      高人's quotation of the passage also has 申, as does the section's own parallel phrasing.
      The character is therefore 申; 则 is a defect of those two transcriptions, not a
      variant reading of the work.
      《三命通会》有两处数字转录作「先得则生」，而四库全书本作「先得申而生」；高人转述
      与同节句式亦皆作申。故该字为申，「则」是那两处转录的讹，不是这部书的异文。
    - The same section reads 「戊己，土也，喜生乎申，得辰戌丑未为正库」. By that phrasing 申
      would belong in the 戊己 cell, yet 问真, 高人 and 《五行精纪》 all give 戊己 the four
      storage branches without 申. No source resolves this, so the tables here follow the
      three that agree and the discrepancy stays on the record.
      「喜生乎申」按句式应把申列入戊己，但三家成表皆无申；无来源可裁，表从三家，矛盾如实留档。

    Sources / 出处:
    - 宋·廖中《五行精纪》卷十三（含「一作」异文）:
      https://book.taiyi.me/命/五行精纪/五行精纪(下)
    - 《五行精纪注释》卷十三「太极贵人，从年干取，甲乙人见子午，丙丁人见卯酉，
      戊己人见辰戌丑未，庚辛人见寅亥，壬癸人见巳申」，该书亦记锚为年干:
      https://www.suanzhun.net/book/2728.html
    - 《三命通会》卷三·论太极贵: https://book.taiyi.me/命/三命通会/三命通会(卷三)
    - 问真《神煞大全》: https://book.taiyi.me/命/神煞大全

    No change should be made to the existing definitions. Only add new definitions.
    '''
    REN_GUI_BOTH    = 0
    REN_SI_GUI_SHEN = 1

  # The tables are used to find out TAIJI GUIREN (太极贵人).
  # 这些表格用于查询太极贵人。
  # A stem can answer with more than one branch, as in `TIANYI`. What has no precedent here
  # is that the cardinality varies inside a single reading: 戊己 take all four storage
  # branches while the split reading gives 壬癸 one each. Which pillar supplies the anchor
  # stem is a school knob; see `_ANCHOR_CHOICES`. The search range is 四柱地支 in both modern
  # sources, and none of the classical sources consulted for this star states one; the two
  # modern houses count as one source there, not two (see this class's docstring).
  # 一个天干可对多支，`TIANYI` 已然如此；本表无先例的是同一读法内部势数不齐——戊己占四库，
  # 而分读法的壬癸各一支。锚取哪一柱属流派旋钮，见 `_ANCHOR_CHOICES`；
  # 被查位置两家现代查法均作四柱地支，而为本星查过的古籍都不交代——
  # 且那两家算一份不算两份，见本类 docstring。
  TAIJI: Final[frozendict[TaijiDef, frozendict[Tiangan, frozenset[Dizhi]]]] = frozendict({
    TaijiDef.REN_GUI_BOTH : frozendict({
      Tiangan.甲 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.丙 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.戊 : frozenset((Dizhi.辰, Dizhi.戌, Dizhi.丑, Dizhi.未)),
      Tiangan.己 : frozenset((Dizhi.辰, Dizhi.戌, Dizhi.丑, Dizhi.未)),
      Tiangan.庚 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.辛 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.壬 : frozenset((Dizhi.巳, Dizhi.申)),
      Tiangan.癸 : frozenset((Dizhi.巳, Dizhi.申)),
    }),
    TaijiDef.REN_SI_GUI_SHEN : frozendict({
      Tiangan.甲 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.丙 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.戊 : frozenset((Dizhi.辰, Dizhi.戌, Dizhi.丑, Dizhi.未)),
      Tiangan.己 : frozenset((Dizhi.辰, Dizhi.戌, Dizhi.丑, Dizhi.未)),
      Tiangan.庚 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.辛 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.壬 : frozenset((Dizhi.巳,)),
      Tiangan.癸 : frozenset((Dizhi.申,)),
    }),
  })

  class GuoyinDef(Enum):
    '''The definitions of GUOYIN GUIREN (国印贵人). Both readings place the star at a fixed
    offset from the stem's 禄, counting 禄 as the first position; they differ only in how far.
    国印贵人的查法定义。两读都把星定在该干禄位的固定偏移处（含禄起算），分歧只在偏移量。

    - WUXING_JINGJI: 禄前第八位 -- i.e. 禄 + 7.
      《五行精纪》禄前第八位。
    - MODERN: 禄前第九位 -- i.e. 禄 + 8.
      果老一脉的禄前第九位，也是现代通行表。

    `MODERN` is the default: it is what 《张果星宗》 gives and what current 排盘 software
    shows. 默认取果老本宗表，现代两家与排盘软件同此。

    **The two readings share no cell** -- every stem gets a different branch under each,
    so a chart is never ambiguous about which reading produced a hit.
    两读无一格重合：每个天干在两读下各得不同地支，故命中结果不会含混。

    What each source does and does not settle:
    各来源定了什么、没定什么：

    - 《张果星宗》 settles `MODERN`, and settles it twice over in one book. The
      「禄勋、阳刃、唐符、国印」 entry gives the couplet 「禄前八位号唐符，第九名为国印宫」
      and then works every stem: 「甲禄到寅、卯为阳刃、酉为飞刃唐符，戌为国印。乙禄到卯、
      辰为阴刃、戌为飞刃唐符、亥为国印……」. The 「天干吉凶星例」 table elsewhere in the same
      book lists 「国印：主掌印，戌亥丑寅丑寅辰巳未申」 -- the same ten cells, transcribed
      independently. The worked example also fixes the counting: 甲禄 sits at 寅, 酉 is the
      eighth position and 戌 the ninth, so 禄 counts as the first.
      《张果星宗》一书两处互证地定下 `MODERN`：条目例解逐干列出，「天干吉凶星例」表另出一遍，
      十格相同。例解同时定死了起算法——甲禄在寅，酉为第八、戌为第九，即含禄起算。
    - 《星学大成》「唐符禄前八位是 国印禄前九位是」 is that same couplet in prose, and
      《神峰通考》 places both stars in the 果老 tradition (「惟张果老通玄先生命理，专用此二星
      取贵」). Read under the parent text's own worked example, its 「禄前九位」 is 禄 + 8 --
      the same table as `MODERN`, not a third one.
      《星学大成》那一句就是同一副对联的散文形，而《神峰通考》把这两颗星归给果老一脉。
      按父本自己的例解读，它的「禄前九位」即禄 + 8，与 `MODERN` 同表，不另成一读。
    - The 白文 of 《五行精纪》 gives the offset and an example, nothing more:
      「国印星禄前第八位是，如甲申生人，至癸酉是。并《三命纂局》」. The anchor and the
      counting convention are spelled out by the modern annotator on the same page, not by
      the 白文:「国印星，命局见年干禄前第八位的地支，如甲申生人，甲禄在寅，寅前八位是酉」.
      So `WUXING_JINGJI` rests on the 白文, while "year stem" and "禄 counts as the first"
      rest on 《五行精纪注释》 -- a distinction worth keeping, since 「甲申生人」 alone would
      also read as a year-branch anchor.
      《五行精纪》白文只给偏移与例子；年干锚与含禄起算的明文出自同页今人注释，不在白文。
      故 `WUXING_JINGJI` 依白文，而「年干」与「禄算第一位」依注释本——两者要分开记，
      因为单看「甲申生人」也可以读成年支锚。
    - `WUXING_JINGJI` shares its ten branches with a star of another name, and 《五行精纪》
      is where that is easiest to see -- but the two halves sit in different layers of the
      book, so state them separately. **白文, 卷廿四** gives 飞刃 as 「禄前一辰为羊刃，对处是
      飞刃」: 羊刃 at 禄 + 1, 飞刃 opposite it, hence 禄 + 7, 酉 for 甲. **注释本, 卷十三**
      is where 国印 sits at 禄前第八位, 甲 -> 酉 -- the 白文 there is the corrupt line noted in
      Sources below, which folds the 国印 head into 【建节星】 and reads 「禄前第六位…至癸酉」,
      self-contradictory. So it is the annotator's reconstruction, not the 白文, that puts
      国印 on 酉.
      Even so the observation holds and cuts the same way: working on this book, the
      annotator seated 国印 on the branch the book's own 卷廿四 already calls 飞刃, and flagged
      no conflict. A cell that carries two stars in one book is a poor candidate for
      "the name slipped from the adjacent couplet" -- which was the earlier worry, and is now
      the weaker reading. **Whether the annotator noticed the overlap at all is not recorded.**
      《五行精纪》里最容易看出这件事，但两半分属该书的不同文本层，故分开陈述：
      **白文卷廿四**的飞刃条作「禄前一辰为羊刃，对处是飞刃」，即羊刃在禄 + 1、飞刃取其对冲，
      得禄 + 7，甲落酉;而**国印在禄前第八位、甲落酉这一条出自注释本卷十三**——该处白文
      正是下面出处栏所记的那句残文，把国印的头句并进了【建节星】，作「禄前第六位…至癸酉」，
      自相矛盾。**所以把国印定在酉的是注释者的复原，不是白文。**
      即便如此，这个观察仍成立且指向同一边：注释者在这本书上作注，把国印安在该书卷廿四
      自己称作飞刃的那一支上，并未提示冲突。一格在同一本书里同时容下两颗星，
      就不像是「星名从相邻对联串下来」——那是先前的疑虑，如今是较弱的那一读。
      **注释者是否注意到这一重合，无从查考。**
    - Beyond that one book the same cell keeps its other name: 《张果星宗》 calls it 飞刃／
      唐符 (「飞刃：同前断，酉戌子丑子丑卯辰午未」 and 「唐符即飞刃也」 -- that identification is
      that book's own), and this repo already holds the same ten cells as
      `FEIREN[YangrenDef.LUMING]`, reached from 《三命通会》 by yet another route -- that one
      does not phrase it as 「禄前八位」 at all, but as 羊刃 at 禄 + 1 with 飞刃 opposite, and
      lands on the same branch. Among the texts that do use the phrase 「禄前八位」, they agree
      on it, on counting 禄 as the first, and on 酉 for 甲; they differ only in which name
      they put there. **The word 唐符 itself does not occur in 《五行精纪》** -- zero
      hits in the electronic full texts of that book consulted here, positive controls
      included; **ctext was not searched**, so this is "not found in what was covered", not a
      claim about every edition. (Which transcriptions those were, and how far each reaches,
      belongs to one search rather than to the star, and is recorded in the commit instead.)
      同一格在别书里保留着另一个名字：《张果星宗》称之飞刃／唐符（「唐符即飞刃也」是该书自述），
      而本仓的 `FEIREN[YangrenDef.LUMING]` 早已是同样十格，那一张又是从《三命通会》另一条路
      推出的——那一条根本不用「禄前八位」这个说法，它作「羊刃在禄 + 1、飞刃取其对冲」，
      只是落在同一支。在使用「禄前八位」这一措辞的诸书之间，说法一致、都含禄起算、
      甲都落在酉，只有安在那里的星名不同。
      **「唐符」二字在《五行精纪》中未见**——所查的该书电子全文中零命中，阴性对照同批做过；
      **ctext 未纳入检索面**，故这是「已覆盖范围内未见」，不是对所有本子的断言。
      （用了哪几份转录、各自到哪一卷，属于某一次检索而非这颗星，改记在提交里。）
    - Where to look is a separate question from which table to use. 《星学大成》 says the
      star 「守照身命」 -- the 命宫 and 身宫, not the four branches -- and 《张果星宗》 agrees
      (「唐符、国印守命为奇」). 《神峰通考》 does not say. Reading the star against 四柱地支
      is the modern sources' move and has no classical backing.
      查哪里与用哪张表是两个问题。《星学大成》明言「守照身命」，即命宫身宫而非四柱，
      《张果星宗》亦作「唐符、国印守命为奇」；《神峰通考》未言。按四柱地支查是现代两家的
      做法，无古籍背书。

    Sources / 出处:
    - 《张果星宗》「禄勋、阳刃、唐符、国印」条与「天干吉凶星例」表:
      https://zh.wikisource.org/wiki/張果星宗
    - 《五行精纪注释》卷十三（底本完整，白文两处转录把建节星与国印星并成一条残句）:
      https://www.suanzhun.net/book/2731.html
    - 明·万民英《星学大成》「唐符禄前八位是 国印禄前九位是 二星守照身命为奇」:
      https://book.taiyi.me/命/星学大成
    - 同书四库全书本，字符与上一条逐字相同，但把「二星守照身命为奇」排作小字夹注而 taiyi 本
      作正文连排——该半句是万民英本文还是注，两本的呈现不同（底本关系亦未见声明）:
      https://zh.wikisource.org/zh-hans/星學大成_(四庫全書本)/全覽
    - 张楠《神峰通考》卷六「唐符国印之星 惟张果老通玄先生命理 专用此二星取贵」:
      https://book.taiyi.me/命/神峰通考(卷六)
    - 问真《神煞大全》: https://book.taiyi.me/命/神煞大全

    No change should be made to the existing definitions. Only add new definitions.
    '''
    WUXING_JINGJI   = 0
    MODERN          = 1

  # The tables are used to find out GUOYIN GUIREN (国印贵人).
  # 这些表格用于查询国印贵人。
  # Every cell is a fixed offset from `BaziRules.TIANGAN_LU`; `test_rules.py` derives all
  # twenty from that table rather than re-reading the literals here, so a typo below cannot
  # agree with itself.
  # 每一格都是 `BaziRules.TIANGAN_LU` 的固定偏移；`test_rules.py` 由禄表推导全部二十格，
  # 不重读下面的字面值——写错一格不会自圆其说。
  # Anchor and search range: see `_ANCHOR_CHOICES`; the modern side reads 四柱地支 (its two
  # houses counting as one source -- see this class's docstring), while the classical ones
  # point at 身命宫 (see `GuoyinDef`).
  # 锚与被查位置见 `_ANCHOR_CHOICES`；现代一侧作四柱地支（那两家算一份，见本类 docstring），
  # 古籍侧指身命宫，见 `GuoyinDef`。
  GUOYIN: Final[frozendict[GuoyinDef, frozendict[Tiangan, Dizhi]]] = frozendict({
    GuoyinDef.WUXING_JINGJI : frozendict({
      Tiangan.甲 : Dizhi.酉,
      Tiangan.乙 : Dizhi.戌,
      Tiangan.丙 : Dizhi.子,
      Tiangan.丁 : Dizhi.丑,
      Tiangan.戊 : Dizhi.子,
      Tiangan.己 : Dizhi.丑,
      Tiangan.庚 : Dizhi.卯,
      Tiangan.辛 : Dizhi.辰,
      Tiangan.壬 : Dizhi.午,
      Tiangan.癸 : Dizhi.未,
    }),
    GuoyinDef.MODERN : frozendict({
      Tiangan.甲 : Dizhi.戌,
      Tiangan.乙 : Dizhi.亥,
      Tiangan.丙 : Dizhi.丑,
      Tiangan.丁 : Dizhi.寅,
      Tiangan.戊 : Dizhi.丑,
      Tiangan.己 : Dizhi.寅,
      Tiangan.庚 : Dizhi.辰,
      Tiangan.辛 : Dizhi.巳,
      Tiangan.壬 : Dizhi.未,
      Tiangan.癸 : Dizhi.申,
    }),
  })
