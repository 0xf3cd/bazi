# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import itertools
from typing import NamedTuple
from .Defines import Tiangan, Dizhi, Ganzhi, Wuxing, Yinyang

# The mappings are used to figure out the first month's Tiangan in a ganzhi year, i.e. 年上起月表.
YEAR_TO_MONTH_TABLE: dict[Tiangan, Tiangan] = {
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
DAY_TO_HOUR_TABLE: dict[Tiangan, Tiangan] = {
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


class TraitTuple(NamedTuple):
  wuxing: Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)

# The table is used to query the Wuxing and Yinyang of a given Tiangan (i.e. Stem / 天干).
# 该字典用于查询给定天干的五行和阴阳。
TIANGAN_TRAITS: dict[Tiangan, TraitTuple] = {
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
DIZHI_TRAITS: dict[Dizhi, TraitTuple] = {
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


HiddenTianganDict = dict[Tiangan, int]

# The table is used to find the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
# 该字典用于查询给定地支的藏干和它们所占的百分比。
HIDDEN_TIANGANS_PERCENTAGE_TABLE: dict[Dizhi, HiddenTianganDict] = {
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

# The list of all 30 Nayins (纳音) in string.
NAYIN_STR_LIST: list[str] = [
  '海中金', '炉中火', '大林木', '路旁土', '剑锋金', '山头火', 
  '涧下水', '城头土', '白蜡金', '杨柳木', '泉中水', '屋上土', 
  '霹雳火', '松柏木', '长流水', '沙中金', '山下火', '平地木', 
  '壁上土', '金箔金', '覆灯火', '天河水', '大驿土', '钗钏金', 
  '桑柘木', '大溪水', '沙中土', '天上火', '石榴木', '大海水',
]

def __gen_nayin_mapping_table() -> dict[Ganzhi, str]:
  '''
  Generate the mapping table of Ganzhi to the corresponding Nayin.
  '''
  nayin_mapping_table: dict[Ganzhi, str] = {}
  cycle = Ganzhi.list_sexagenary_cycle()
  for index, gz in enumerate(cycle):
    nayin_mapping_table[gz] = NAYIN_STR_LIST[index // 2]
  return nayin_mapping_table

NAYIN_TABLE: dict[Ganzhi, str] = __gen_nayin_mapping_table()


# The table is used to query the dizhi where the Zhangsheng locates for each Tiangan.
# 该字典用于查询每个天干的长生所在的地支。
TIANGAN_ZHANGSHENG_TABLE: dict[Tiangan, Dizhi] = {
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


# The table is used to query the HE relation across all Tiangans.
# 该表格用于查询天干之间的相合关系。
TIANGAN_HE_TABLE: dict[frozenset[Tiangan], Wuxing] = {
  frozenset((Tiangan.甲, Tiangan.己)) : Wuxing.土,
  frozenset((Tiangan.乙, Tiangan.庚)) : Wuxing.金,
  frozenset((Tiangan.丙, Tiangan.辛)) : Wuxing.水,
  frozenset((Tiangan.丁, Tiangan.壬)) : Wuxing.木,
  frozenset((Tiangan.戊, Tiangan.癸)) : Wuxing.火,
}


# The table is used to query the CHONG relation across all Tiangans.
# 该表格用于查询天干之间的相冲关系。
TIANGAN_CHONG_TABLE: list[set[Tiangan]] = [
  set((Tiangan.甲, Tiangan.庚)),
  set((Tiangan.乙, Tiangan.辛)),
  set((Tiangan.丙, Tiangan.壬)),
  set((Tiangan.丁, Tiangan.癸)),
]


def __populate_tg_sheng_table() -> list[set[Tiangan]]:
  ret: list[set[Tiangan]] = []
  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    tg1_trait: TraitTuple = TIANGAN_TRAITS[tg1]
    tg2_trait: TraitTuple = TIANGAN_TRAITS[tg2]
    if tg1_trait.wuxing.generates(tg2_trait.wuxing): # Yinyang not considered. 天干相生不考虑阴阳。
      ret.append({tg1, tg2})
  return ret

# The table is used to query the SHENG relation across all Tiangans.
# 该表格用于查询天干之间的相生关系。
TIANGAN_SHENG_TABLE: list[set[Tiangan]] = __populate_tg_sheng_table()


def __populate_tg_ke_table() -> list[set[Tiangan]]:
  ret: list[set[Tiangan]] = []
  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    tg1_trait: TraitTuple = TIANGAN_TRAITS[tg1]
    tg2_trait: TraitTuple = TIANGAN_TRAITS[tg2]
    if tg1_trait.wuxing.destructs(tg2_trait.wuxing): # Yinyang not considered. 天干相克不考虑阴阳。
      ret.append({tg1, tg2})
  return ret

# The table is used to query the KE relation across all Tiangans.
# 该表格用于查询天干之间的相克关系。
TIANGAN_KE_TABLE: list[set[Tiangan]] = __populate_tg_ke_table()
