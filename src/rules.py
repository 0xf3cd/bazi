# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import itertools
from enum import Enum
from typing import Final

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

    This knob is declared per chart via `BaziSchool.gong_def` and read at evaluation time
    by relation discovery (`analyzer/relationship.py`); member names are serialized into JSON.
    本旋钮由 `BaziSchool.gong_def` 按盘声明，关系查法在评估期读取；成员名进 JSON。

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


def _expand_dizhi_groups(groups: dict[str, str]) -> frozendict[Dizhi, Dizhi]:
  return frozendict({
    Dizhi(key) : Dizhi(target)
    for keys, target in groups.items()
    for key in keys
  })


class ShenshaRules:
  '''Rules for Shensha / 神煞'''

  # The table is used to find out TAOHUA (桃花). A.k.a. XIANCHI TAOHUA (咸池桃花).
  # 该表格用于查询桃花星。桃花即咸池桃花。
  TAOHUA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '申子辰' : '酉',
    '寅午戌' : '卯',
    '亥卯未' : '子',
    '巳酉丑' : '午',
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
  YIMA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '申子辰' : '寅',
    '寅午戌' : '申',
    '亥卯未' : '巳',
    '巳酉丑' : '亥',
  })

  # HUAGAI (华盖) is the tomb/storage branch of each 三合 group. From 《三命通会》, as quoted
  # in Yuan Shushan's 《命理探源》:「华盖者，形象之称也……故以三合本库为华盖也。如寅午戌
  # 见戌，火库也，巳酉丑见丑，金库也，馀仿此。」
  # 华盖取各三合局的墓库；上引《三命通会》原文转引自袁树珊《命理探源》。
  # Source / 出处: https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb (issue #16).
  # Mainstream modern references use the year or day branch as the anchor and inspect the other
  # pillars' branches (百度百科「神煞」; also 问真、高人).
  # 当代通行查法以年支或日支为锚，查其他柱的地支（百度百科「神煞」；问真、高人）。
  HUAGAI: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '寅午戌' : '戌',
    '亥卯未' : '未',
    '申子辰' : '辰',
    '巳酉丑' : '丑',
  })

  # JIANGXING (将星) is the middle / Diwang (帝旺) branch of each 三合 group,
  # enumerated group by group in 《三命通会·卷三·论灾煞》.
  # 将星取各三合局的帝旺位；《三命通会·卷三·论灾煞》逐组明列。
  # Table source / 表值出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #152).
  # Cross-check / 校核: https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb (issue #152).
  # Wenzhen (问真) anchors on the year or day branch and inspects the remaining branches.
  # 问真以年支或日支为锚，查余支。
  # Anchor source / 查法锚出处: https://book.taiyi.me/命/神煞大全#将星 (issue #152).
  JIANGXING: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '申子辰' : '子',
    '寅午戌' : '午',
    '亥卯未' : '卯',
    '巳酉丑' : '酉',
  })

  # JIESHA (劫煞) is the Jue (绝) branch of each 三合 group's Wuxing,
  # enumerated group by group in 《三命通会·卷三·论劫煞亡神》.
  # 劫煞取各三合局五行的绝位；《三命通会·卷三·论劫煞亡神》逐组明列。
  # Table source / 表值出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #153).
  # Wenzhen (问真) anchors on the year or day branch and inspects the remaining branches.
  # 问真以年支或日支为锚，查余支。
  # Anchor source / 查法锚出处: https://book.taiyi.me/命/神煞大全#劫煞 (issue #153).
  JIESHA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '申子辰' : '巳',
    '寅午戌' : '亥',
    '亥卯未' : '申',
    '巳酉丑' : '寅',
  })

  # WANGSHEN (亡神) is the Linguan (临官) branch of each 三合 group's Wuxing,
  # enumerated group by group in 《三命通会·卷三·论劫煞亡神》.
  # 亡神取各三合局五行的临官位；《三命通会·卷三·论劫煞亡神》逐组明列。
  # Table source / 表值出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #154).
  # Wenzhen (问真) anchors on the year or day branch and inspects the remaining branches.
  # 问真以年支或日支为锚，查余支。
  # Anchor source / 查法锚出处: https://book.taiyi.me/命/神煞大全#亡神 (issue #154).
  WANGSHEN: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '申子辰' : '亥',
    '寅午戌' : '巳',
    '亥卯未' : '寅',
    '巳酉丑' : '申',
  })

  # GUCHEN (孤辰) and GUASU (寡宿) are the branches one step forward and one step back
  # from the birth-year branch's direction group in 《三命通会·卷三·论孤辰寡宿》.
  # 孤辰、寡宿分别取出生年支所属方位组的进前一辰、退后一辰。
  # Rule source / 规则出处: https://book.taiyi.me/命/三命通会/三命通会(卷三) (issue #161).
  # Table source / 表值出处: https://book.taiyi.me/命/神煞大全#孤辰 and https://book.taiyi.me/命/神煞大全#寡宿 (issue #161).
  # Anchor source / 查法锚出处: the same entries / 同上两条 (issue #161).
  # The same section quotes the interpretation-level exclusions 「连属不言孤寡」 and
  # 「支干朝会包裹贵人」. They do not erase the raw locations here.
  # 同节所引「连属不言孤寡」及贵人包裹条款属解释层豁免，不抹去本表给出的原始命中位置。
  GUCHEN: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '亥子丑' : '寅',
    '寅卯辰' : '巳',
    '巳午未' : '申',
    '申酉戌' : '亥',
  })

  GUASU: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups({
    '亥子丑' : '戌',
    '寅卯辰' : '丑',
    '巳午未' : '辰',
    '申酉戌' : '未',
  })

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

  class YangrenDef(Enum):
    '''The definitions of YANGREN (羊刃 / 阳刃), which disagree on whether Yin
    Tiangans have Yangren and where it falls. 羊刃（阳刃）的三种定义，分歧在阴干有无刃及刃位。

    - ZIPING: only the five Yang Tiangans have 阳刃.
      子平法：仅五阳干有阳刃。
    - LUMING: all ten Tiangans have Yangren on the branch immediately after their Lu (禄).
      古禄命法：十干皆有羊刃，取禄前一辰。
    - DIWANG: all ten Tiangans take their Diwang (帝旺) branch; the 问真 and 高人
      charting programs use this table.
      十干各取帝旺位；问真与高人排盘软件采用此表。

    The lookup always keys on the Day Master and inspects all four branches; the
    chart declares the definition via `BaziSchool.yangren_def`, and member names
    are serialized into JSON. 查法固定以日干查四支；定义由 `BaziSchool.yangren_def`
    按盘声明，成员名进 JSON。

    Sources / 出处:
    - 《三命通会·卷三·论羊刃》 records both the ZIPING and LUMING readings:
      https://m.guwendao.net/guwen/bookv_d6957d252951.aspx
    - Modern DIWANG table: https://book.taiyi.me/命/神煞大全 and
      https://github.com/gaorenyes/gaorenyes.github.io

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

  class FeirenDef(Enum):
    '''The definitions of FEIREN (飞刃). Each profile takes the branch opposite the
    corresponding Yangren definition. 飞刃的三种定义；每套均取对应羊刃定义的对冲支。

    - ZIPING: only the five Yang Tiangans have Feiren, opposite their 阳刃.
      子平法：仅五阳干有飞刃，取阳刃对冲支。
    - LUMING: all ten Tiangans take the branch opposite their LUMING Yangren.
      古禄命法：十干皆有飞刃，取古禄命羊刃对冲支。
    - DIWANG: all ten Tiangans take the branch opposite their Diwang (帝旺) branch.
      十干各取帝旺位的对冲支。

    The lookup always keys on the Day Master. At birth it inspects all four branches;
    transit analysis inspects the selected transit branches. The chart declares the
    definition via `BaziSchool.feiren_def`, independently of `yangren_def`, and member
    names are serialized into JSON. 查法固定以日干为锚；原局查四支，流运查所选流运支；定义由
    `BaziSchool.feiren_def` 按盘声明，与 `yangren_def` 彼此独立，成员名进 JSON。

    Sources / 出处:
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

  FEIREN: Final[frozendict[FeirenDef, frozendict[Tiangan, Dizhi | None]]] = frozendict({
    FeirenDef.ZIPING : frozendict({
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
    FeirenDef.LUMING : frozendict({
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
    FeirenDef.DIWANG : frozendict({
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
    used by 问真. The chart declares a profile via `BaziSchool.tianyi_def`, independently
    of `BaziSchool.tianyi_anchor`; member names are serialized into JSON. Day/night boundary
    selection is deliberately outside these tables.
    传统合并表的古籍谱系较厚，问真亦采用；
    查法 profile 由 `BaziSchool.tianyi_def` 按盘声明，与锚干配置相互独立，成员名进 JSON；
    本表不代选昼夜界线。

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
