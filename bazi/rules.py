# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import itertools
from dataclasses import dataclass
from collections.abc import Callable
from enum import Enum
from typing import Final, TypeVar

from .common import frozendict, check_declared_types
from .data_types import TraitTuple, HiddenTianganDict
from .defines import Tiangan, Dizhi, Ganzhi, Wuxing, Yinyang, DizhiRelation, ShierZhangsheng


# 规则表为普通 Final 类属性，导入时构造一次；mypy 检查重新赋值，运行时不设此检查。


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
  '''Bazi 与 BaziChart 的基础规则。'''

  # 年上起月表，给出寅月天干。
  YEAR_TO_MONTH_TABLE: Final[frozendict[Tiangan, Tiangan]] = frozendict({
    Tiangan.甲 : Tiangan.丙, # 甲年首月丙寅。
    Tiangan.乙 : Tiangan.戊, # 乙年首月戊寅。
    Tiangan.丙 : Tiangan.庚, # 丙年首月庚寅。
    Tiangan.丁 : Tiangan.壬, # 丁年首月壬寅。
    Tiangan.戊 : Tiangan.甲, # 戊年首月甲寅。
    Tiangan.己 : Tiangan.丙, # 己年首月丙寅。
    Tiangan.庚 : Tiangan.戊, # 庚年首月戊寅。
    Tiangan.辛 : Tiangan.庚, # 辛年首月庚寅。
    Tiangan.壬 : Tiangan.壬, # 壬年首月壬寅。
    Tiangan.癸 : Tiangan.甲, # 癸年首月甲寅。
  })

  # 日上起时表，给出子时天干。
  DAY_TO_HOUR_TABLE: Final[frozendict[Tiangan, Tiangan]] = frozendict({
    Tiangan.甲 : Tiangan.甲, # 甲日首时甲子。
    Tiangan.乙 : Tiangan.丙, # 乙日首时丙子。
    Tiangan.丙 : Tiangan.戊, # 丙日首时戊子。
    Tiangan.丁 : Tiangan.庚, # 丁日首时庚子。
    Tiangan.戊 : Tiangan.壬, # 戊日首时壬子。
    Tiangan.己 : Tiangan.甲, # 己日首时甲子。
    Tiangan.庚 : Tiangan.丙, # 庚日首时丙子。
    Tiangan.辛 : Tiangan.戊, # 辛日首时戊子。
    Tiangan.壬 : Tiangan.庚, # 壬日首时庚子。
    Tiangan.癸 : Tiangan.壬, # 癸日首时壬子。
  })

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

  # 该字典用于查询给定干支的纳音。
  NAYIN: Final[frozendict[Ganzhi, str]] = _nayin()

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



'''生克表的天干或地支键。'''
_TraitKey = TypeVar('_TraitKey', Tiangan, Dizhi)


def _wuxing_relations(
  traits: frozendict[_TraitKey, TraitTuple],
  relates: Callable[[Wuxing, Wuxing], bool],
) -> frozenset[tuple[_TraitKey, _TraitKey]]:
  '''仅按五行派生有方向的生克表，不考虑阴阳。'''
  return frozenset(
    (first, second)
    for first, second in itertools.product(traits, repeat=2)
    if relates(traits[first].wuxing, traits[second].wuxing)
  )


class TianganRules:
  '''天干关系规则。'''

  # 该表格用于查询天干之间的相合关系。
  # 相合关系是无方向的。如甲己相合是双向的关系，互相相合。
  TIANGAN_HE: Final[frozendict[frozenset[Tiangan], Wuxing]] = frozendict({
    frozenset((Tiangan.甲, Tiangan.己)) : Wuxing.土,
    frozenset((Tiangan.乙, Tiangan.庚)) : Wuxing.金,
    frozenset((Tiangan.丙, Tiangan.辛)) : Wuxing.水,
    frozenset((Tiangan.丁, Tiangan.壬)) : Wuxing.木,
    frozenset((Tiangan.戊, Tiangan.癸)) : Wuxing.火,
  })

  # 该表格用于查询天干之间的相冲关系。
  # 相冲关系是无方向的。如甲庚相冲是双向的关系，互相相冲。相冲双方均减力，旺者减力小，弱者减力大。
  TIANGAN_CHONG: Final[frozenset[frozenset[Tiangan]]] = frozenset((
    frozenset((Tiangan.甲, Tiangan.庚)),
    frozenset((Tiangan.乙, Tiangan.辛)),
    frozenset((Tiangan.丙, Tiangan.壬)),
    frozenset((Tiangan.丁, Tiangan.癸)),
  ))

  # 该表格用于查询天干之间的相生关系。
  # 相生关系是单向的。如甲丁相生，则是甲木生丁火。
  # 天干相生不考虑阴阳，只考虑五行。
  TIANGAN_SHENG: Final[frozenset[tuple[Tiangan, Tiangan]]] = _wuxing_relations(
    BaziRules.TIANGAN_TRAITS,
    Wuxing.generates,
  )

  # 该表格用于查询天干之间的相克关系。
  # 相克关系是单向的。如壬丙相克，是壬水克丙火。
  # 天干相克不考虑阴阳，只考虑五行。
  TIANGAN_KE: Final[frozenset[tuple[Tiangan, Tiangan]]] = _wuxing_relations(
    BaziRules.TIANGAN_TRAITS,
    Wuxing.destructs,
  )



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


class DizhiRules:
  '''地支关系规则。'''

  class GongheDef(Enum):
    '''拱合结构定义：NARROW 只收三合缺中神；WIDE 收三合任意两支并拱出第三支。

    出处：
    - 狭义：https://services.shen88.cn/bazisuanming/pc-74297.html
    - 广义：https://www.sohu.com/a/471337600_310486
    '''
    NARROW = 0
    WIDE   = 1

  class GongDef(Enum):
    '''拱合、拱会成立条件的来源档案；只列有出处的组合，不任意拼接分歧条件。

    - SAME_STEM_NARROW：两柱同干；狭义拱合并收拱会。
    - SAME_STEM_WIDE：两柱同干；广义拱合并收拱会。
    - TRANSFORMING_NARROW：查询范围透出化神；狭义拱合并收拱会。
    - LU_NARROW：查询范围见所拱五行的乙、丁、辛、癸禄字；只收狭义拱合，来源未扩到拱会。

    候选柱位由入口决定：`search_ganzhis` 只查相邻具体出现，`discover_mutual_ganzhis`
    查横跨两组输入的柱位对。

    不修改既有定义；新读法须另加定义。

    出处：
    - 同干、广义：https://www.sohu.com/a/471337600_310486
    - 透化神：https://www.suanzhun.net/article/2395.html
    - 禄字：https://services.shen88.cn/bazisuanming/pc-74297.html
    - 拱会 / 夹术语：https://www.sohu.com/a/805277582_120167645
    '''
    SAME_STEM_NARROW    = 0
    SAME_STEM_WIDE      = 1
    TRANSFORMING_NARROW = 2
    LU_NARROW           = 3

  # 拱局批量查询需要柱位与天干上下文。
  GONG_RELATIONS: Final[tuple[DizhiRelation, ...]] = (DizhiRelation.拱合, DizhiRelation.拱会)

  # 各拱局来源档案所用的拱合结构定义。
  GONG_GONGHE_SCOPE: Final[frozendict[GongDef, GongheDef]] = frozendict({
    GongDef.SAME_STEM_NARROW    : GongheDef.NARROW,
    GongDef.SAME_STEM_WIDE      : GongheDef.WIDE,
    GongDef.TRANSFORMING_NARROW : GongheDef.NARROW,
    GongDef.LU_NARROW           : GongheDef.NARROW,
  })

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
    不同的地支暗合关系看法。

    暗合无方向，每个直接或批量查法入口看到的表一致——无 `XingDef` 那种入口层分歧。

    不修改既有定义；新读法须另加定义。
    '''
    NORMAL           = 0 # 卯申、巳酉、亥午、子巳、寅午 - 这也是所谓的“通禄合”/“通禄暗合”，与天干五合一一对应。
                         # 选 NORMAL 时 `DIZHI_ANHE[NORMAL]` 与 `DIZHI_TONGLUHE` 逐项相同——discovery 会在
                         # 暗合与通禄合两个键下给出相同组合，那是同一证据，不是两条独立证据。
    NORMAL_EXTENDED  = 1 # 卯申、巳酉、亥午、子巳、寅午 + 寅丑。这六组的藏干没有明显的冲突，而且有藏干相合的关系。
    MANGPAI          = 2 # 卯申、寅丑、午亥。盲派最认可这三对暗合。

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

  # 该表格用于查询地支之间的通合关系。
  # 通合关系是无方向的。通合代表藏干中所有气都能两两相合。
  DIZHI_TONGHE: Final[frozenset[frozenset[Dizhi]]] = frozenset([
    frozenset((Dizhi.寅, Dizhi.丑)),
    frozenset((Dizhi.午, Dizhi.亥)),
  ])

  # 该表格用于查询地支之间的通禄合关系。
  # 通禄合关系是无方向的。若两个天干相合，那么它们在地支中的禄身也能相合，从而构成地支的通禄合关系。
  DIZHI_TONGLUHE: Final[frozenset[frozenset[Dizhi]]] = frozenset([
    frozenset((Dizhi.卯, Dizhi.申)),
    frozenset((Dizhi.巳, Dizhi.酉)),
    frozenset((Dizhi.亥, Dizhi.午)),
    frozenset((Dizhi.子, Dizhi.巳)),
    frozenset((Dizhi.寅, Dizhi.午)),
  ])

  # 该表格用于查询地支之间的三合局。
  # 三合关系是无方向的。
  DIZHI_SANHE: Final[frozendict[frozenset[Dizhi], Wuxing]] = frozendict({
    frozenset((Dizhi.巳, Dizhi.酉, Dizhi.丑)) : Wuxing.金,
    frozenset((Dizhi.亥, Dizhi.卯, Dizhi.未)) : Wuxing.木,
    frozenset((Dizhi.申, Dizhi.子, Dizhi.辰)) : Wuxing.水,
    frozenset((Dizhi.寅, Dizhi.午, Dizhi.戌)) : Wuxing.火,
  })

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

  # 见禄字口径按所拱木火金水分别取乙丁辛癸；三合、三会无土局。
  DIZHI_GONG_LU_TIANGAN: Final[frozendict[Wuxing, Tiangan]] = frozendict({
    Wuxing.木 : Tiangan.乙,
    Wuxing.火 : Tiangan.丁,
    Wuxing.金 : Tiangan.辛,
    Wuxing.水 : Tiangan.癸,
  })

  class XingDef(Enum):
    '''
    不同的地支相刑的看法。主要区别在于丑未戌、寅巳申之间相刑的定义。

    - 定义层（各查法入口共有）：STRICT 要求丑未戌 / 寅巳申三支齐现；LOOSE 三取二即成立。
    - 入口层：方向（谁刑谁）只有按序查法（`dizhi_utils.xing`）可见；批量查法入口按多重集
      比对，看不出方向。

    不修改既有定义；新读法须另加定义。
    '''
    STRICT = 0 # 丑未戌、寅巳申须三支齐现。
    LOOSE  = 1 # 丑未戌、寅巳申三取二；按序查法 dizhi_utils.xing 还要求符合循环方向：
               # 丑->戌->未->丑 / 寅->巳->申->寅，丑戌成立、戌丑不成立。
               # 方向由实现及 test_dizhi_utils 验证。

  class XingSubType(Enum):
    SANXING   = 0 # 丑未戌、寅巳申三刑
    ZIMAOXING = 1 # 子卯相刑
    ZIXING    = 2 # 自刑

    三刑   = SANXING
    子卯刑 = ZIMAOXING
    自刑   = ZIXING

  # 该表格用于查询地支之间的刑。
  # 相刑是有方向的。
  DIZHI_XING: Final[frozendict[XingDef, frozendict[tuple[Dizhi, ...], XingSubType]]] = frozendict({
    XingDef.STRICT : _dizhi_xing_strict(XingSubType),
    XingDef.LOOSE  : _dizhi_xing_loose(XingSubType),
  })

  # 该表格用于查询地支之间的冲。
  # 相冲是无方向的，两个地支之间互相相冲。
  DIZHI_CHONG: Final[frozenset[frozenset[Dizhi]]] = frozenset([frozenset(dz_tuple) for dz_tuple in (
    (Dizhi.子, Dizhi.午), (Dizhi.丑, Dizhi.未),
    (Dizhi.寅, Dizhi.申), (Dizhi.卯, Dizhi.酉),
    (Dizhi.辰, Dizhi.戌), (Dizhi.巳, Dizhi.亥),
  )])

  # 该表格用于查询地支之间的破。
  # 相破是无方向的，两个地支之间互相破坏。
  DIZHI_PO: Final[frozenset[frozenset[Dizhi]]] = frozenset([frozenset(dz_tuple) for dz_tuple in (
    (Dizhi.子, Dizhi.酉), (Dizhi.卯, Dizhi.午),
    (Dizhi.辰, Dizhi.丑), (Dizhi.未, Dizhi.戌),
    (Dizhi.寅, Dizhi.亥), (Dizhi.巳, Dizhi.申),
  )])

  # 该表格用于查询地支之间的害（即相穿）。
  # 相害是无方向的，两个地支之间两两相害。
  DIZHI_HAI: Final[frozenset[frozenset[Dizhi]]] = frozenset([frozenset(dz_tuple) for dz_tuple in (
    (Dizhi.子, Dizhi.未), (Dizhi.丑, Dizhi.午),
    (Dizhi.寅, Dizhi.巳), (Dizhi.卯, Dizhi.辰),
    (Dizhi.申, Dizhi.亥), (Dizhi.酉, Dizhi.戌),
  )])

  # 该表格用于查询地支之间的相生关系。
  # 相生关系是单向的。如丙寅相生，则是寅木生丙火。
  # 地支相生不考虑阴阳，只考虑五行。
  DIZHI_SHENG: Final[frozenset[tuple[Dizhi, Dizhi]]] = _wuxing_relations(
    BaziRules.DIZHI_TRAITS,
    Wuxing.generates,
  )

  # 该表格用于查询地支之间的相克关系。
  # 相克关系是单向的。如寅丑相克，则是寅木克丑土。
  # 地支相克不考虑阴阳，只考虑五行。
  DIZHI_KE: Final[frozenset[tuple[Dizhi, Dizhi]]] = _wuxing_relations(
    BaziRules.DIZHI_TRAITS,
    Wuxing.destructs,
  )


@dataclass(frozen=True)
class DizhiRelationDefinitions:
  '''地支批量查法共用的暗合、刑与拱局定义。

  构造时检查各字段的枚举类型；本对象不含排盘或神煞选项。

  Args:
  - anhe_def: (DizhiRules.AnheDef) 暗合定义。
  - xing_def: (DizhiRules.XingDef) 刑定义。
  - gong_def: (DizhiRules.GongDef) 拱局天干与结构条件。
  '''
  anhe_def: DizhiRules.AnheDef = DizhiRules.AnheDef.NORMAL_EXTENDED
  xing_def: DizhiRules.XingDef = DizhiRules.XingDef.LOOSE
  gong_def: DizhiRules.GongDef = DizhiRules.GongDef.SAME_STEM_NARROW

  def __post_init__(self) -> None:
    check_declared_types(self)


DEFAULT_DIZHI_RELATION_DEFINITIONS: Final[DizhiRelationDefinitions] = DizhiRelationDefinitions()


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


def _offset_dizhi(dizhi: Dizhi, step: int) -> Dizhi:
  '''按十二支循环移动 step 位，可为负。'''
  return Dizhi.from_index((dizhi.index + step) % len(Dizhi))


def _lu_offset(step: int) -> frozendict[Tiangan, Dizhi]:
  '''各天干禄位的固定顺向偏移。'''
  return frozendict({tg: _offset_dizhi(lu, step) for tg, lu in BaziRules.TIANGAN_LU.items()})


class ShenshaRules:
  '''神煞规则及出处。

  问真《神煞大全》与高人**不作两个独立来源计数**。
  两家引同一首口诀时引得一样，汉字序列全同，只是标点习惯不同；这本身说明不了什么——
  口诀是公共财产，况且两家并不总挑同一首（见下文天乙）。
  但**有几处断语也长段逐字相同**——断语是各家自撰的评断文字，
  本无必须一致的理由，那确实指向共享文本。反方向的事实同时存在：多数断语除了
  三五个字外毫无共同处，而且两家读法有分歧——天乙各择一个歌诀版本
  （高人并自述用的是哪一个），红艳问真作乙午而高人作乙申，即下面 `HONGYAN`
  已记的散文本／歌诀本之分。

  **哪一份是上游、是否互相读过，所查材料无一裁定。**

  **两家引同一首口诀，按一份证据计。**
  下文某一行两家给出同一读法时，读作「同一个现代读法被记录了两次」，不是「两个独立读法互相印证」。

  出处（天乙贵人、红艳、金舆、国印贵人等条）：
  - 问真《神煞大全》: https://book.taiyi.me/命/神煞大全
  - 高人: https://github.com/gaorenyes/gaorenyes.github.io/blob/817ad1f8f463d489087ac6c44ec69165e1181454/README.md
  '''

  # 下列桃花、红鸾、天喜、驿马的原局查法出处，不等于分析器对各类流运统一用表的逐项依据。

  # 桃花表值见《三命通会》卷二〈论咸池〉；四库本转录的夹注另有纳音条件，本表不含该条件。
  # 分析器以年、日支分别查其余原局柱的读法，依现代问真《神煞大全》〈桃花/咸池〉，不混同夹注。
  # 表值出处：https://zh.wikisource.org/w/index.php?oldid=761691
  TAOHUA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '酉',
      '寅午戌' : '卯',
      '亥卯未' : '子',
      '巳酉丑' : '午',
    },
    Dizhi,
  )

  # 红艳表；《三命通会》原文："甲乙逢午、丙寅、丁未、
  # 戊辰、己辰、庚戌、辛酉、壬子、癸申，为红艳煞"。
  # 歌诀本作「甲乙午申庚见戌」，两谱系见 #69 考证。
  # 乙 一格两谱系分叉：散文本作乙午（问真等从之），本表从歌诀本作乙申。
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

  # 红鸾、天喜表值同见《星学大成》卷一〈论红鸾天喜〉：子年分别起卯、酉，随年支逆数。
  # 该条论宫限，不是查其余原局柱；分析器以年支查月、日、时支，依现代问真《神煞大全》〈红鸾〉。
  # 表值出处：https://zh.wikisource.org/w/index.php?oldid=626726
  HONGLUAN: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    dz: _offset_dizhi(Dizhi.卯, -dz.index) for dz in Dizhi
  })

  # 天喜的宫限表值出处见上方红鸾；以年支查其余原局柱，依问真《神煞大全》〈天喜〉。
  TIANXI: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    dz: _offset_dizhi(Dizhi.酉, -dz.index) for dz in Dizhi
  })

  # 驿马表值见《三命通会》卷三〈论驿马〉；默认以年、日支分别查其余原局柱，依问真《神煞大全》〈驿马〉。
  # 日支查年、月、时的读法见袁树珊《命理探原》卷上〈强弱·驿马〉印页六五；扫描链接见 `BaziSchool.mingli_tanyuan`。
  # 支持口径见 `_ANCHOR_CHOICES['yima_anchor']`，默认双锚不是将袁氏所列两法合并。
  # 表值出处：https://zh.wikisource.org/w/index.php?oldid=2184219
  YIMA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '寅',
      '寅午戌' : '申',
      '亥卯未' : '巳',
      '巳酉丑' : '亥',
    },
    Dizhi,
  )

  # 华盖取三合墓库；袁树珊《命理探源》转引《三命通会》：
  # 「华盖者，形象之称也……故以三合本库为华盖也。如寅午戌
  # 见戌，火库也，巳酉丑见丑，金库也，馀仿此。」
  # 出处：https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb（#16）。
  # YEAR_AND_DAY 查法锚补充出处：百度百科「神煞」、高人。
  # 支持读法：_ANCHOR_CHOICES['huagai_anchor']。
  HUAGAI: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '寅午戌' : '戌',
      '亥卯未' : '未',
      '申子辰' : '辰',
      '巳酉丑' : '丑',
    },
    Dizhi,
  )

  # 将星取各三合局的帝旺位；《三命通会·卷三·论灾煞》逐组明列。
  # 表值出处：https://book.taiyi.me/命/三命通会/三命通会(卷三)（#152）。
  # 校核：https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb（#152）。
  # 支持读法：_ANCHOR_CHOICES['jiangxing_anchor']。
  # 查法锚出处：https://book.taiyi.me/命/神煞大全#将星（#152）。
  JIANGXING: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '子',
      '寅午戌' : '午',
      '亥卯未' : '卯',
      '巳酉丑' : '酉',
    },
    Dizhi,
  )

  # 灾煞取各三合局将星的对冲支；《三命通会·卷三·论灾煞》逐组明列。
  # 表值出处：https://book.taiyi.me/命/三命通会/三命通会(卷三)（#174）。
  # 支持读法：_ANCHOR_CHOICES['zaisha_anchor']。
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

  # 劫煞取各三合局五行的绝位；《三命通会·卷三·论劫煞亡神》逐组明列。
  # 表值出处：https://book.taiyi.me/命/三命通会/三命通会(卷三)（#153）。
  # 支持读法：_ANCHOR_CHOICES['jiesha_anchor']。
  # 查法锚出处：https://book.taiyi.me/命/神煞大全#劫煞（#153）。
  JIESHA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '巳',
      '寅午戌' : '亥',
      '亥卯未' : '申',
      '巳酉丑' : '寅',
    },
    Dizhi,
  )

  # 亡神取各三合局五行的临官位；《三命通会·卷三·论劫煞亡神》逐组明列。
  # 表值出处：https://book.taiyi.me/命/三命通会/三命通会(卷三)（#154）。
  # 支持读法：_ANCHOR_CHOICES['wangshen_anchor']。
  # 查法锚出处：https://book.taiyi.me/命/神煞大全#亡神（#154）。
  WANGSHEN: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '亥',
      '寅午戌' : '巳',
      '亥卯未' : '寅',
      '巳酉丑' : '申',
    },
    Dizhi,
  )

  # 孤辰、寡宿分别取出生年支所属方位组的进前一辰、退后一辰，见《三命通会·卷三·论孤辰寡宿》。
  # 规则出处：https://book.taiyi.me/命/三命通会/三命通会(卷三)（#161）。
  # 表值出处：https://book.taiyi.me/命/神煞大全#孤辰 和 https://book.taiyi.me/命/神煞大全#寡宿（#161）。
  # 查法锚出处：同上两条（#161）。
  # 同节所引「连属不言孤寡」及「支干朝会包裹贵人」属解释层豁免，不抹去本表给出的原始命中位置。
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

  # 禄神与 BaziRules.TIANGAN_LU 共用十干禄位表。
  # 出处：《三命通会·卷三·论十干禄》及 https://book.taiyi.me/命/神煞大全#禄神（#162）。
  LUSHEN: Final[frozendict[Tiangan, Dizhi]] = BaziRules.TIANGAN_LU

  # 金舆取各天干禄位前二辰。
  # 表值出处（#163）：
  # - 《三命通会·卷三·论金舆》: https://book.taiyi.me/命/三命通会/三命通会(卷三)
  # - 袁树珊《命理探源》: https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
  JINYU: Final[frozendict[Tiangan, Dizhi]] = _lu_offset(2)

  # 魁罡固定取四个日柱，《渊海子平·论魁罡》与《三命通会·卷六·魁罡》所载相同。
  # 出处（#175）：
  # - https://book.taiyi.me/命/子平推命/渊海子平(神煞篇)
  # - https://book.taiyi.me/命/三命通会/三命通会(卷六)
  KUIGANG: Final[frozenset[Ganzhi]] = frozenset((
    Ganzhi.from_str('庚辰'),
    Ganzhi.from_str('壬辰'),
    Ganzhi.from_str('戊戌'),
    Ganzhi.from_str('庚戌'),
  ))

  # 天赦按月令所属四时查日柱：春戊寅、夏甲午、秋戊申、冬甲子。
  # 表值出处（#176）：
  # - 《三命通会·卷三·论天月德》: https://book.taiyi.me/命/三命通会/三命通会(卷三)
  # - 袁树珊《命理探源》转引《渊海子平》：
  #   https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
  # 查法锚出处：https://book.taiyi.me/命/神煞大全#天赦日（#176）。
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
    '''羊刃（阳刃）与飞刃共用的三种定义。羊刃分歧在阴干有无刃及刃位；每套飞刃均取
    对应羊刃定义的对冲支。

    - ZIPING：子平法，仅五阳干有阳刃。
    - LUMING：古禄命法，十干皆有羊刃，取禄前一辰。
    - DIWANG：十干各取帝旺位；现代问真与高人皆采用此表，两家按一份来源计，
      见 ShenshaRules 的类说明。

    飞刃：
    - ZIPING：仅五阳干有飞刃，取阳刃对冲支。
    - LUMING：十干皆有飞刃，取古禄命羊刃对冲支。
    - DIWANG：十干各取帝旺位的对冲支。

    `BaziSchool.yangren_def` 与 `BaziSchool.feiren_def` 独立，可任意组合羊刃与飞刃定义。

    羊刃出处：
    - 《三命通会·卷三·论羊刃》同时记录 ZIPING 与 LUMING：
      https://m.guwendao.net/guwen/bookv_d6957d252951.aspx
    - 现代 DIWANG 表：https://book.taiyi.me/命/神煞大全 及
      https://github.com/gaorenyes/gaorenyes.github.io

    飞刃出处：
    - 《三命通会·卷三·论羊刃》:
      https://book.taiyi.me/命/三命通会/三命通会(卷三)
    - 《渊海子平·论阳刃》提供子平法仅五阳干的依据：
      https://book.taiyi.me/命/子平推命/渊海子平(神煞篇)
    - 现代 DIWANG 表：
      https://github.com/gaorenyes/gaorenyes.github.io/blob/817ad1f8f463d489087ac6c44ec69165e1181454/b/index.html#L748

    不修改既有定义；新读法须另加定义。
    '''
    ZIPING = 0
    LUMING = 1
    DIWANG = 2

  YANGREN: Final[frozendict[YangrenDef, frozendict[Tiangan, Dizhi | None]]] = frozendict({
    YangrenDef.ZIPING : frozendict({
      tg: _offset_dizhi(lu, 1) if BaziRules.TIANGAN_TRAITS[tg].yinyang is Yinyang.阳 else None
      for tg, lu in BaziRules.TIANGAN_LU.items()
    }),
    YangrenDef.LUMING : frozendict(_lu_offset(1)),
    YangrenDef.DIWANG : frozendict({
      tg: _offset_dizhi(
        zhangsheng,
        ShierZhangsheng.帝旺.index if BaziRules.TIANGAN_TRAITS[tg].yinyang is Yinyang.阳 else -ShierZhangsheng.帝旺.index,
      )
      for tg, zhangsheng in BaziRules.TIANGAN_ZHANGSHENG.items()
    }),
  })

  FEIREN: Final[frozendict[YangrenDef, frozendict[Tiangan, Dizhi | None]]] = frozendict({
    definition: frozendict({tg: None if dz is None else _offset_dizhi(dz, 6) for tg, dz in table.items()})
    for definition, table in YANGREN.items()
  })

  class TianyiDef(Enum):
    '''天乙贵人的查法定义；口诀、庚辛分组与昼夜表彼此牵连，按出处保留完整档案，
    不作无出处的自由组合。

    - GENG_WITH_JIA_WU：传统合并口诀「甲戊庚牛羊……六辛逢马虎」，庚与甲戊同组，辛取午寅。
    - GENG_WITH_XIN：改口诀「甲戊兼牛羊……庚辛逢马虎」，庚改与辛同组。
    - YANGGUI：该传统谱系的昼间阳贵表，与阴贵表合并即为庚随甲戊的传统合并表。
    - YINGUI：该谱系的夜间阴贵表，与阳贵表合并即为传统合并表；所引来源采用「六辛逢午马」版口诀，
      按干对分承所得十干表与本表相同。

    传统合并表有较多古籍谱系依据，问真亦采用；`BaziSchool.tianyi_def` 与
    `BaziSchool.tianyi_anchor` 相互独立，本表不代选昼夜界线。

    出处：
    - 袁树珊《命理探源》引古歌「甲戊庚牛羊……六辛逢马虎」:
      https://upload.wikimedia.org/wikipedia/commons/5/52/NLC416-07jh011647-5318_命理探源.pdf
    - 两版合并口诀：
      https://www.click2macao.com/2024/04/10/tygrkjdz/
    - 阳贵、阴贵表与所用口诀：
      https://www.usece.com/3858/
    - 问真读法：https://book.taiyi.me/命/神煞大全

    不修改既有定义；新读法须另加定义。
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
    '''文昌的查法定义。两读只在辛一格分歧，其余九干在所查各来源中相同。

    - XIN_ZI：辛 → 子。
    - XIN_XU：辛 → 戌。

    默认取 XIN_ZI：民国刊本与现代主流两条谱系都指向它。XIN_XU 出自《星学大成》，
    两个转录逐字相同，且散文给了理由。

    本表为子平法文昌（食神之临官、长生），与下方禄命法文昌贵分列；
    第三颗文星贵（「甲马乙蛇丙戊猴」）未纳入本库。

    出处限度：

    - 《命理探源》散文只逐条列甲乙丙丁戊己，末句「庚辛壬癸仿此」。
      后四干见所引口诀（「庚猪辛鼠壬逢虎，癸人见兔入云梯」），辛取子依据口诀而非散文。
    - 《星学大成》口诀作辛戌，散文说明（「独辛不以生而以戌为文昌，戌在辛之方位」），
      因此 XIN_XU 是自成一说，不是抄讹。

    出处：
    - 袁树珊《命理探源》卷三「以日主为主，如甲见己，乙见午是也」:
      https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
    - 问真《神煞大全》: https://book.taiyi.me/命/神煞大全
    - 明·万民英《星学大成》「论文昌」: https://book.taiyi.me/命/星学大成
    - 同书四库全书本，与上一条逐字相同（两处转录的底本关系未见声明）:
      https://zh.wikisource.org/zh-hans/星學大成_(四庫全書本)/全覽

    不修改既有定义；新读法须另加定义。
    '''
    XIN_ZI = 0
    XIN_XU = 1

  # 这些表格用于查询文昌星。
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

  # 该表格用于查询文昌贵，禄命法中的同名近亲。它与文昌在甲（巳）、戊（申）两格相同，
  # 其余八干皆异，因此两者分列，不并成一条。
  # 锚为年干；未见流派分歧，故本表不设旋钮。
  # 出处：
  # - 《五行精纪注释》卷十三「以年干查：甲见巳，乙见亥，丙见戌，丁见辰，戊见申，己见午，
  #   庚见寅，辛见未，壬见卯，癸见丑」；明言锚柱及全表：
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
    '''太极贵人的查法定义。两读只在壬癸分歧。

    - REN_GUI_BOTH：壬癸各兼巳申。
    - REN_SI_GUI_SHEN：壬取巳、癸取申。

    《五行精纪》一句并存两读，以「一作」引出第二读；此「一作」是同书异文，不是两家表之争：

        壬巳癸申一作壬癸巳申偏喜美，封侯万户即三公

    默认 REN_GUI_BOTH 取歌诀「一作」所指读法，也是现代两家所取。

    两处原文问题保留如下：

    - 《三命通会》两处数字转录（taiyi、算准网）作「壬癸水先得则生，
      后得巳而纳」，维基文库四库全书本作「壬癸水先得申而生後得巳而納」。
      高人引文与本节对应句式均有申。
      故该字为申，「则」是那两处转录的讹，不是这部书的异文。
    - 同节作「戊己，土也，喜生乎申，得辰戌丑未为正库」。按句式申应属戊己格，
      但问真、高人与《五行精纪》均只列四库；无来源可裁，表从三家，矛盾如实留档。

    出处：
    - 宋·廖中《五行精纪》卷十三（含「一作」异文）:
      https://book.taiyi.me/命/五行精纪/五行精纪(下)
    - 《五行精纪注释》卷十三「太极贵人，从年干取，甲乙人见子午，丙丁人见卯酉，
      戊己人见辰戌丑未，庚辛人见寅亥，壬癸人见巳申」，该书亦记锚为年干:
      https://www.suanzhun.net/book/2728.html
    - 《三命通会》卷三·论太极贵: https://book.taiyi.me/命/三命通会/三命通会(卷三)
    - 问真《神煞大全》: https://book.taiyi.me/命/神煞大全

    不修改既有定义；新读法须另加定义。
    '''
    REN_GUI_BOTH    = 0
    REN_SI_GUI_SHEN = 1

  # 这些表格用于查询太极贵人。
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
    '''国印贵人的查法定义。两读都取该干禄位的固定偏移（含禄起算），只在偏移量上分歧。

    - WUXING_JINGJI：禄 + 7，见《五行精纪注释》及下引恬裕斋抄本国印条的禄前第八位。
    - MODERN：禄 + 8，果老一脉的禄前第九位，也是现代通行表。

    默认 MODERN，表值与《张果星宗》及此处所引现代来源一致。

    两读无一格重合：每个天干在两读下各得不同地支，故命中结果不会含混。

    各来源的结论与限度：

    - 《张果星宗》的「禄勋、阳刃、唐符、国印」条载「禄前八位号唐符，第九名为国印宫」，
      并逐干举例：「甲禄到寅、卯为阳刃、酉为飞刃唐符，戌为国印。乙禄到卯、
      辰为阴刃、戌为飞刃唐符、亥为国印……」。同书「天干吉凶星例」表载
      「国印：主掌印，戌亥丑寅丑寅辰巳未申」，十格相同。
      条目例解与「天干吉凶星例」表共同支持 MODERN。例解明确含禄起算：甲禄在寅，酉为第八、戌为第九。
    - 《星学大成》「唐符禄前八位是 国印禄前九位是」为该对联的散文形；
      《神峰通考》将两星归于果老一脉（「惟张果老通玄先生命理 专用此二星
      取贵」）。
      按《张果星宗》例解的含禄起算法，「禄前九位」即禄 + 8，与 `MODERN` 同表；不据此裁定传承关系。
    - WUXING_JINGJI 依《五行精纪注释》卷十三【原文】：
      「国印星禄前第八位是，如甲申生人，至癸酉是。并《三命纂局》」。同页今人【注释】作：
      「国印星，命局见年干禄前第八位的地支，如甲申生人，甲禄在寅，寅前八位是酉」。
      年干锚与含禄起算的明文出自今人【注释】，不混作【原文】的断言。
      目录著录为恬裕斋清抄本的第二册图像 81-82 分列建節星与國印星，后者作「祿前第八位是如甲申生人至癸酉是」。
      此引文只及该见证，不证明宋代原貌或今人注释所据底本。
      两份白文转录的【建节星】则作「禄前第六位是也，如甲申生人，至癸酉是也」，与抄本及注释本有异，
      传抄关系未定（#194）。
    - `WUXING_JINGJI` 与 `FEIREN[YangrenDef.LUMING]` 十格相同；同格不裁定传抄关系。
    - 查找位置与表值分开：
      《星学大成》明言「守照身命」，即命宫身宫而非四柱，
      《张果星宗》亦作「唐符、国印守命为奇」；所引《神峰通考》段落未言查找位置。
      本库按四柱地支查的做法依此处所引现代来源，不出自上述段落。

    出处：
    - 《张果星宗》「禄勋、阳刃、唐符、国印」条与「天干吉凶星例」表:
      https://zh.wikisource.org/wiki/張果星宗
    - 《五行精纪注释》卷十三，分别列出建节星与国印星:
      https://www.suanzhun.net/book/2731.html
    - 国图抄本，目录著录为海虞瞿氏恬裕斋清抄本，第二册图像 81-82（卷十三）：
      https://commons.wikimedia.org/wiki/File:NLC892-411999013122-114407_五行精紀_第2冊.pdf
    - 《五行精纪》白文卷十三【建节星】，两份转录均载上文所引文字:
      算准网: https://www.suanzhun.net/book/1003.html
      维基文库（全文页内第十三卷）: https://zh.wikisource.org/wiki/五行精紀
    - 明·万民英《星学大成》「唐符禄前八位是 国印禄前九位是 二星守照身命为奇」:
      https://book.taiyi.me/命/星学大成
    - 维基文库标为四库全书本的电子转录将「二星守照身命为奇」排作 HTML 小字，taiyi 连排。
      对「二星守照身命为奇」核到的是网页呈现，不是该版影像，不能据此裁定本文或注文：
      https://zh.wikisource.org/zh-hans/星學大成_(四庫全書本)/全覽
    - 张楠《神峰通考》卷六「唐符国印之星 惟张果老通玄先生命理 专用此二星取贵」:
      https://book.taiyi.me/命/神峰通考/神峰通考(卷六).md
    - 问真《神煞大全》: https://book.taiyi.me/命/神煞大全

    不修改既有定义；新读法须另加定义。
    '''
    WUXING_JINGJI   = 0
    MODERN          = 1

  # 这些表格用于查询国印贵人。
  # 各读法分别从禄派生自身表；表值相同不合并知识身份。
  # 锚与被查位置见 `_ANCHOR_CHOICES`；现代一侧作四柱地支（那两家算一份，见本类 docstring），
  # 所引星学段落指身命宫，见 `GuoyinDef`。
  GUOYIN: Final[frozendict[GuoyinDef, frozendict[Tiangan, Dizhi]]] = frozendict({
    GuoyinDef.WUXING_JINGJI : _lu_offset(7),
    GuoyinDef.MODERN        : _lu_offset(8),
  })
