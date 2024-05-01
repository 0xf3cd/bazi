# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import itertools
from enum import Enum
from typing import NamedTuple
from .Defines import Tiangan, Dizhi, Ganzhi, Wuxing, Yinyang


class TraitTuple(NamedTuple):
  wuxing: Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


HiddenTianganDict = dict[Tiangan, int]


'''
TODO:
Currently, all tables in `RuleReader` are returned by @property methods. 
When accessing a table in `Rules`, a new table (a dict/list/whatever) is created every time.
This is intended - in order to avoid malicious/unintended modification of the table.

However, this raises a performance concern. As generating a new table upon every access is an expensive operation.
Instead, a immutable table should be returned - so that the table can't be modified anyways,
and there's no need to return a new table every time.
For future reference: tuple and frozenset are built-in immutable data structures.

With that being said, I think current implementation is fine - I don't care much about the performace at this point.
'''
class Rules:
  # The mappings are used to figure out the first month's Tiangan in a ganzhi year, i.e. 年上起月表.
  @property
  def YEAR_TO_MONTH_TABLE(self) -> dict[Tiangan, Tiangan]:
    return {
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
    }

  # The mappings are used to figure out the first hour's Tiangan in a ganzhi day, i.e. 日上起时表.
  @property
  def DAY_TO_HOUR_TABLE(self) -> dict[Tiangan, Tiangan]:
    return {
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
    }

  # The table is used to query the Wuxing and Yinyang of a given Tiangan (i.e. Stem / 天干).
  # 该字典用于查询给定天干的五行和阴阳。
  @property
  def TIANGAN_TRAITS(self) -> dict[Tiangan, TraitTuple]:
    return {
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
    }


  # The table is used to query the Wuxing and Yinyang of a given Dizhi (i.e. Branch / 地支).
  # 该字典用于查询给定地支的五行和阴阳。
  @property
  def DIZHI_TRAITS(self) -> dict[Dizhi, TraitTuple]:
    return {
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
    }


  # The table is used to find the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
  # 该字典用于查询给定地支的藏干和它们所占的百分比。
  @property
  def HIDDEN_TIANGANS(self) -> dict[Dizhi, HiddenTianganDict]:
    return {
      Dizhi.子 : { Tiangan.癸 : 100 },
      Dizhi.丑 : { Tiangan.己 : 60, Tiangan.癸 : 30, Tiangan.辛 : 10 },
      Dizhi.寅 : { Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10 },
      Dizhi.卯 : { Tiangan.乙 : 100 },
      Dizhi.辰 : { Tiangan.戊 : 60, Tiangan.乙 : 30, Tiangan.癸 : 10 },
      Dizhi.巳 : { Tiangan.丙 : 60, Tiangan.庚 : 30, Tiangan.戊 : 10 },
      Dizhi.午 : { Tiangan.丁 : 70, Tiangan.己 : 30 },
      Dizhi.未 : { Tiangan.己 : 60, Tiangan.丁 : 30, Tiangan.乙 : 10 },
      Dizhi.申 : { Tiangan.庚 : 60, Tiangan.壬 : 30, Tiangan.戊 : 10 },
      Dizhi.酉 : { Tiangan.辛 : 100 },
      Dizhi.戌 : { Tiangan.戊 : 60, Tiangan.辛 : 30, Tiangan.丁 : 10 },
      Dizhi.亥 : { Tiangan.壬 : 70, Tiangan.甲 : 30 },
    }


  # The table is used to query the NAYIN (纳音) of a given Ganzhi (i.e. Stem-branch / Ganzhi / 干支).
  # 该字典用于查询给定干支的纳音。
  @property
  def NAYIN(self) -> dict[Ganzhi, str]:
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
    return nayin_mapping_table


  # The table is used to query the dizhi where the Zhangsheng locates for each Tiangan.
  # 该字典用于查询每个天干的长生所在的地支。
  @property
  def TIANGAN_ZHANGSHENG(self) -> dict[Tiangan, Dizhi]:
    return {
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
    }
  

  # This table is used to query Tiangans' LU (禄) in Dizhis.
  # 该字典用于查询天干的禄/禄身。
  @property
  def TIANGAN_LU(self) -> dict[Tiangan, Dizhi]:
    return {
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
    }


  # The table is used to query the HE (合) relation across all Tiangans.
  # HE relation is a non-directional/mutual relation.
  # 该表格用于查询天干之间的相合关系。
  # 相合关系是无方向的。如甲己相合是双向的关系，互相相合。
  @property
  def TIANGAN_HE(self) -> dict[frozenset[Tiangan], Wuxing]:
    return {
      frozenset((Tiangan.甲, Tiangan.己)) : Wuxing.土,
      frozenset((Tiangan.乙, Tiangan.庚)) : Wuxing.金,
      frozenset((Tiangan.丙, Tiangan.辛)) : Wuxing.水,
      frozenset((Tiangan.丁, Tiangan.壬)) : Wuxing.木,
      frozenset((Tiangan.戊, Tiangan.癸)) : Wuxing.火,
    }


  # The table is used to query the CHONG (冲) relation across all Tiangans.
  # CHONG relation is a non-directional/mutual relation.
  # 该表格用于查询天干之间的相冲关系。
  # 相冲关系是无方向的。如甲庚相冲是双向的关系，互相相冲。相冲双方均减力，旺者减力小，弱者减力大。
  @property
  def TIANGAN_CHONG(self) -> frozenset[frozenset[Tiangan]]:
    return frozenset((
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
  @property
  def TIANGAN_SHENG(self) -> frozenset[tuple[Tiangan, Tiangan]]:
    traits_rule = self.TIANGAN_TRAITS
    ret: list[tuple[Tiangan, Tiangan]] = []
    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      tg1_trait: TraitTuple = traits_rule[tg1]
      tg2_trait: TraitTuple = traits_rule[tg2]
      if tg1_trait.wuxing.generates(tg2_trait.wuxing): # Yinyang not considered. 天干相生不考虑阴阳。
        ret.append((tg1, tg2)) # Direction: tg1 -> tg2
    return frozenset(ret)


  # The table is used to query the KE (克) relation across all Tiangans.
  # KE relation is a uni-directional relation.
  # Yinyang is not considered in KE relation - only Wuxing is considered.
  # 该表格用于查询天干之间的相克关系。
  # 相克关系是单向的。如壬丙相克，是壬水克丙火。
  # 天干相克不考虑阴阳，只考虑五行。
  @property
  def TIANGAN_KE(self) -> frozenset[tuple[Tiangan, Tiangan]]:
    traits_rule = self.TIANGAN_TRAITS
    ret: list[tuple[Tiangan, Tiangan]] = []
    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      tg1_trait: TraitTuple = traits_rule[tg1]
      tg2_trait: TraitTuple = traits_rule[tg2]
      if tg1_trait.wuxing.destructs(tg2_trait.wuxing): # Yinyang not considered. 天干相克不考虑阴阳。
        ret.append((tg1, tg2)) # Direction: tg1 -> tg2
    return frozenset(ret)


  # The table is used to query the SANHUI (三会) relation across all Dizhis.
  # SANHUI relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的三会局。
  # 三会是无方向的。如寅卯辰三会木局是三个地支之间相互的关系。
  @property
  def DIZHI_SANHUI(self) -> dict[frozenset[Dizhi], Wuxing]:
    return {
      frozenset((Dizhi.寅, Dizhi.卯, Dizhi.辰)) : Wuxing.木,
      frozenset((Dizhi.巳, Dizhi.午, Dizhi.未)) : Wuxing.火,
      frozenset((Dizhi.申, Dizhi.酉, Dizhi.戌)) : Wuxing.金,
      frozenset((Dizhi.亥, Dizhi.子, Dizhi.丑)) : Wuxing.水,
    }
  

  # The table is used to query the LIUHE (六合) relation across all Dizhis.
  # LIUHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的六合局。
  # 六合关系是无方向的。如子、丑相合是相互的关系。
  @property
  def DIZHI_LIUHE(self) -> dict[frozenset[Dizhi], Wuxing]:
    return {
      frozenset((Dizhi.子, Dizhi.丑)) : Wuxing.土,
      frozenset((Dizhi.寅, Dizhi.亥)) : Wuxing.木,
      frozenset((Dizhi.卯, Dizhi.戌)) : Wuxing.火,
      frozenset((Dizhi.辰, Dizhi.酉)) : Wuxing.金,
      frozenset((Dizhi.巳, Dizhi.申)) : Wuxing.水,
      frozenset((Dizhi.午, Dizhi.未)) : Wuxing.土,
    }
  
  class AnheDef(Enum):
    '''
    The definition of ANHE relation. Different definitions mean different query tables.
    不同的地支暗合关系看法。
    '''
    NORMAL           = 0 # 卯申、巳酉、亥午、子巳、寅午 - 这也是所谓的“通禄合”/“通禄暗合”，与天干五合一一对应。
    NORMAL_EXTENDED  = 1 # 卯申、巳酉、亥午、子巳、寅午 + 寅丑。这六组的藏干没有明显的冲突，而且有藏干相合的关系。
    MANGPAI          = 2 # 卯申、寅丑、午亥。盲派最认可这三对暗合。
    # No change should be made to the existing definitions.
    # Only add new definitions.


  # The tables are used to query the ANHE (暗合) relation across all Dizhis.
  # ANHE relation is a non-directional/mutual relation.
  # All tables for different `AnheDef` are returned as a dict.
  # 该表格用于查询地支之间的暗合关系。
  # 暗合关系是无方向的。
  @property
  def DIZHI_ANHE(self) -> dict[AnheDef, frozenset[frozenset[Dizhi]]]:
    d: dict[Rules.AnheDef, frozenset[frozenset[Dizhi]]] = {}

    d[Rules.AnheDef.NORMAL] = frozenset([
      frozenset((Dizhi.卯, Dizhi.申)),
      frozenset((Dizhi.巳, Dizhi.酉)),
      frozenset((Dizhi.亥, Dizhi.午)),
      frozenset((Dizhi.子, Dizhi.巳)),
      frozenset((Dizhi.寅, Dizhi.午)),
    ])

    d[Rules.AnheDef.NORMAL_EXTENDED] = frozenset([
      frozenset((Dizhi.卯, Dizhi.申)),
      frozenset((Dizhi.巳, Dizhi.酉)),
      frozenset((Dizhi.亥, Dizhi.午)),
      frozenset((Dizhi.子, Dizhi.巳)),
      frozenset((Dizhi.寅, Dizhi.午)),
      frozenset((Dizhi.寅, Dizhi.丑)),
    ])

    d[Rules.AnheDef.MANGPAI] = frozenset([
      frozenset((Dizhi.卯, Dizhi.申)),
      frozenset((Dizhi.寅, Dizhi.丑)),
      frozenset((Dizhi.午, Dizhi.亥)),
    ])

    return d
  
  # The table is used to query the TONGHE (通合) relation across all Dizhis.
  # TONGHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的通合关系。
  # 通合关系是无方向的。通合代表藏干中所有气都能两两相合。
  @property
  def DIZHI_TONGHE(self) -> frozenset[frozenset[Dizhi]]:
    return frozenset([
      frozenset((Dizhi.寅, Dizhi.丑)),
      frozenset((Dizhi.午, Dizhi.亥)),
    ])

  # The table is used to query the TONGLUHE (通禄合) relation across all Dizhis.
  # TONGLUHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的通禄合关系。
  # 通禄合关系是无方向的。若两个天干相合，那么它们在地支中的禄身也能相合，从而构成地支的通禄合关系。
  @property
  def DIZHI_TONGLUHE(self) -> frozenset[frozenset[Dizhi]]:
    return frozenset([
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
  @property
  def DIZHI_SANHE(self) -> dict[frozenset[Dizhi], Wuxing]:
    return {
      frozenset((Dizhi.巳, Dizhi.酉, Dizhi.丑)) : Wuxing.金,
      frozenset((Dizhi.亥, Dizhi.卯, Dizhi.未)) : Wuxing.木,
      frozenset((Dizhi.申, Dizhi.子, Dizhi.辰)) : Wuxing.水,
      frozenset((Dizhi.寅, Dizhi.午, Dizhi.戌)) : Wuxing.火,
    }

  # The table is used to query the BANHE (半合) relation across all Dizhis.
  # BANHE relation is a non-directional/mutual relation.
  # 该表格用于查询地支之间的半合局。
  # 半合关系是无方向的。
  @property
  def DIZHI_BANHE(self) -> dict[frozenset[Dizhi], Wuxing]:
    return {
      frozenset((Dizhi.巳, Dizhi.酉)) : Wuxing.金,
      frozenset((Dizhi.酉, Dizhi.丑)) : Wuxing.金,
      frozenset((Dizhi.亥, Dizhi.卯)) : Wuxing.木,
      frozenset((Dizhi.卯, Dizhi.未)) : Wuxing.木,
      frozenset((Dizhi.申, Dizhi.子)) : Wuxing.水,
      frozenset((Dizhi.子, Dizhi.辰)) : Wuxing.水,
      frozenset((Dizhi.寅, Dizhi.午)) : Wuxing.火,
      frozenset((Dizhi.午, Dizhi.戌)) : Wuxing.火,
    }
