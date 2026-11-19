# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''排盘、天干地支关系与神煞的规则表。

BaziRules、TianganRules、DizhiRules 与 ShenshaRules 分别保存对应规则；
DizhiRelationDefinitions 承载可选择的地支关系定义。
API 页列出表的名称、类型与说明，完整表值可从源码入口或按键查阅。

Examples:
```python
from bazi.defines import Tiangan, Dizhi, Ganzhi, Wuxing
from bazi.rules import BaziRules, TianganRules, ShenshaRules

assert BaziRules.NAYIN[Ganzhi.from_str('甲子')] == '海中金'
assert TianganRules.TIANGAN_HE[frozenset({Tiangan.甲, Tiangan.己})] is Wuxing.土
assert ShenshaRules.TAOHUA[Dizhi.申] is Dizhi.酉
```
'''

import itertools
from dataclasses import dataclass
from collections.abc import Callable
from enum import Enum
from typing import Final, TypeVar

from .common import frozendict, check_declared_types, _compact_dataclass_repr
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


def _zhangsheng_rows(
  zhangsheng: frozendict[Tiangan, Dizhi],
  traits: frozendict[Tiangan, TraitTuple],
) -> frozendict[Tiangan, tuple[Dizhi, ...]]:
  '''各天干从长生位起，阳干顺行、阴干逆行。'''
  return frozendict({
    tg: tuple(
      Dizhi.from_index((start.index + place.index * (1 if traits[tg].yinyang is Yinyang.阳 else -1)) % len(Dizhi))
      for place in ShierZhangsheng
    )
    for tg, start in zhangsheng.items()
  })


class BaziRules:
  '''Bazi 与 BaziChart 的基础规则。'''

  # 四时本令；季月分段的前段仍属该季节，转土时刻由命盘所选 TuwangDef 决定。
  # 五状态的生克次序见《三命通会》卷二〈論五行旺相休囚死並寄生十二宫〉：
  # https://zh.wikisource.org/w/index.php?oldid=761691
  MONTH_WUXING: Final[frozendict[Dizhi, Wuxing]] = frozendict({
    Dizhi.寅 : Wuxing.木, Dizhi.卯 : Wuxing.木, Dizhi.辰 : Wuxing.木,
    Dizhi.巳 : Wuxing.火, Dizhi.午 : Wuxing.火, Dizhi.未 : Wuxing.火,
    Dizhi.申 : Wuxing.金, Dizhi.酉 : Wuxing.金, Dizhi.戌 : Wuxing.金,
    Dizhi.亥 : Wuxing.水, Dizhi.子 : Wuxing.水, Dizhi.丑 : Wuxing.水,
  })

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

  # 十二长生依 ShierZhangsheng 顺序排列的地支位置。
  _ZHANGSHENG_ROWS: Final[frozendict[Tiangan, tuple[Dizhi, ...]]] = _zhangsheng_rows(
    TIANGAN_ZHANGSHENG,
    TIANGAN_TRAITS,
  )

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
    '''
    NORMAL           = 0 # 卯申、巳酉、亥午、子巳、寅午 - 这也是所谓的“通禄合”/“通禄暗合”，与天干五合一一对应。
                         # 选 NORMAL 时 `DIZHI_ANHE[NORMAL]` 与 `DIZHI_TONGLUHE` 逐项相同——discovery 会在
                         # 暗合与通禄合两个键下给出相同组合，那是同一证据，不是两条独立证据。
    NORMAL_EXTENDED  = 1 # 卯申、巳酉、亥午、子巳、寅午 + 寅丑。这六组的藏干没有明显的冲突，而且有藏干相合的关系。
    MANGPAI          = 2 # 卯申、寅丑、午亥。盲派最认可这三对暗合。

  # 该表格用于查询地支之间的通禄合关系。
  # 通禄合关系是无方向的。若两个天干相合，那么它们在地支中的禄身也能相合，从而构成地支的通禄合关系。
  DIZHI_TONGLUHE: Final[frozenset[frozenset[Dizhi]]] = frozenset([
    frozenset((Dizhi.卯, Dizhi.申)),
    frozenset((Dizhi.巳, Dizhi.酉)),
    frozenset((Dizhi.亥, Dizhi.午)),
    frozenset((Dizhi.子, Dizhi.巳)),
    frozenset((Dizhi.寅, Dizhi.午)),
  ])

  # 该表格用于查询地支之间的暗合关系。
  # 暗合关系是无方向的。
  DIZHI_ANHE: Final[frozendict[AnheDef, frozenset[frozenset[Dizhi]]]] = frozendict({
    AnheDef.NORMAL          : DIZHI_TONGLUHE,
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
  # 与同名神煞的区别见知识条目 concept.dizhi_po.readings。
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
  # 相生关系是单向的。
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

  def __repr__(self) -> str:
    return _compact_dataclass_repr(self)


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
  '''神煞规则表与可选定义。各表附知识条目入口；现代来源的关系见 concept.shensha_sources.readings。'''

  # 桃花取三合组的沐浴位；表值与查法见 shensha.taohua.readings。
  TAOHUA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '酉',
      '寅午戌' : '卯',
      '亥卯未' : '子',
      '巳酉丑' : '午',
    },
    Dizhi,
  )

  # 红艳按天干查地支，采用高人十干表；表值与查法见 shensha.hongyan.readings。
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

  # 红鸾从子年起卯，随年支逆数；出处见 shensha.hongluan_tianxi.readings。
  HONGLUAN: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    dz: _offset_dizhi(Dizhi.卯, -dz.index) for dz in Dizhi
  })

  # 天喜从子年起酉，随年支逆数；出处见 shensha.hongluan_tianxi.readings。
  TIANXI: Final[frozendict[Dizhi, Dizhi]] = frozendict({
    dz: _offset_dizhi(Dizhi.酉, -dz.index) for dz in Dizhi
  })

  # 驿马按三合组取支；表值与现代查法见 shensha.yima.table、shensha.yima.lookup，
  # 日锚出处见 concept.mingli_tanyuan.readings。
  YIMA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '寅',
      '寅午戌' : '申',
      '亥卯未' : '巳',
      '巳酉丑' : '亥',
    },
    Dizhi,
  )

  # 华盖取三合墓库；表值见 shensha.huagai.table，查法与袁氏转引见 shensha.huagai.readings。
  HUAGAI: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '寅午戌' : '戌',
      '亥卯未' : '未',
      '申子辰' : '辰',
      '巳酉丑' : '丑',
    },
    Dizhi,
  )

  # 将星取三合局的帝旺位；出处见 shensha.jiangxing.readings。
  JIANGXING: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '子',
      '寅午戌' : '午',
      '亥卯未' : '卯',
      '巳酉丑' : '酉',
    },
    Dizhi,
  )

  # 灾煞取三合局将星的对冲支；出处见 shensha.zaisha.readings。
  ZAISHA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '午',
      '寅午戌' : '子',
      '巳酉丑' : '卯',
      '亥卯未' : '酉',
    },
    Dizhi,
  )

  # 劫煞取三合局五行的绝位；出处见 shensha.jiesha_wangshen.readings。
  JIESHA: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '巳',
      '寅午戌' : '亥',
      '亥卯未' : '申',
      '巳酉丑' : '寅',
    },
    Dizhi,
  )

  # 亡神取三合局五行的临官位；出处见 shensha.jiesha_wangshen.readings。
  WANGSHEN: Final[frozendict[Dizhi, Dizhi]] = _expand_dizhi_groups(
    {
      '申子辰' : '亥',
      '寅午戌' : '巳',
      '亥卯未' : '寅',
      '巳酉丑' : '申',
    },
    Dizhi,
  )

  # 孤辰、寡宿取出生年支方位组的进前一辰、退后一辰；出处见 shensha.guchen_guasu.readings。
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
  # 出处：《三命通会·卷三·论十干禄》及 https://book.taiyi.me/命/神煞大全#禄神。
  LUSHEN: Final[frozendict[Tiangan, Dizhi]] = BaziRules.TIANGAN_LU

  # 金舆取天干禄位前二辰；表值与查法见 shensha.jinyu.readings。
  JINYU: Final[frozendict[Tiangan, Dizhi]] = _lu_offset(2)

  # 魁罡固定取四个日柱，《渊海子平·论魁罡》与《三命通会·卷六·魁罡》所载相同。
  # 出处：
  # - https://book.taiyi.me/命/子平推命/渊海子平(神煞篇)
  # - https://book.taiyi.me/命/三命通会/三命通会(卷六)
  KUIGANG: Final[frozenset[Ganzhi]] = frozenset((
    Ganzhi.from_str('庚辰'),
    Ganzhi.from_str('壬辰'),
    Ganzhi.from_str('戊戌'),
    Ganzhi.from_str('庚戌'),
  ))

  # 天赦按月令所属四时查日柱：春戊寅、夏甲午、秋戊申、冬甲子。
  # 表值出处：
  # - 《三命通会·卷三·论天月德》：https://book.taiyi.me/命/三命通会/三命通会(卷三)
  # - 袁树珊《命理探源》转引《渊海子平》：
  #   https://ctext.org/wiki.pl?if=gb&chapter=827425&remap=gb
  # 查法锚出处：https://book.taiyi.me/命/神煞大全#天赦日。
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
    - DIWANG：十干各取帝旺位。

    飞刃：
    - ZIPING：仅五阳干有飞刃，取阳刃对冲支。
    - LUMING：十干皆有飞刃，取古禄命羊刃对冲支。
    - DIWANG：十干各取帝旺位的对冲支。

    `BaziSchool.yangren_def` 与 `BaziSchool.feiren_def` 独立，可任意组合羊刃与飞刃定义。

    羊刃与飞刃的表值及查法出处见知识条目 shensha.yangren_feiren.readings。
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
      tg: row[ShierZhangsheng.帝旺.index]
      for tg, row in BaziRules._ZHANGSHENG_ROWS.items()
    }),
  })

  FEIREN: Final[frozendict[YangrenDef, frozendict[Tiangan, Dizhi | None]]] = frozendict({
    definition: frozendict({tg: None if dz is None else _offset_dizhi(dz, 6) for tg, dz in table.items()})
    for definition, table in YANGREN.items()
  })

  class TianyiDef(Enum):
    '''天乙贵人的查法定义；口诀、庚辛分组与阳贵／阴贵表彼此牵连，按出处保留完整档案，
    不作无出处的自由组合。

    - GENG_WITH_JIA_WU：庚与甲戊同组、辛取午寅的传统合并表。
    - GENG_WITH_XIN：庚改与辛同组的合并表。
    - YANGGUI、YINGUI：依《三命通会》所引通玄经推法命名的阳贵、阴贵表；
      两表合并即为 GENG_WITH_JIA_WU。

    `BaziSchool.tianyi_def` 与 `BaziSchool.tianyi_anchor` 相互独立，
    本表不代选使用时间或界线。各表与查法的出处见知识条目 shensha.tianyi.readings。
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
    '''文昌的查法定义。两表只在辛一格分歧。

    - XIN_ZI：辛 → 子。
    - XIN_XU：辛 → 戌。

    默认取 XIN_ZI。两读与禄命法文昌贵的区别、表值与查法出处见知识条目 shensha.wenchang.readings。
    '''
    XIN_ZI = 0
    XIN_XU = 1

  # 文昌按所选定义查支，锚点由流派配置选择。
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

  # 禄命法文昌贵，以年干查支；与文昌分列，出处见 shensha.wenchanggui.readings。
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

    默认 REN_GUI_BOTH。两读与锚点的出处见知识条目 shensha.taiji.readings。
    '''
    REN_GUI_BOTH    = 0
    REN_SI_GUI_SHEN = 1

  # 太极贵人按所选定义查支，一个天干可对应多支；锚点由流派配置选择。
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

    - WUXING_JINGJI：禄 + 7，禄前第八位。
    - MODERN：禄 + 8，果老一脉的禄前第九位，也是现代通行表。

    默认 MODERN。

    两读无一格重合：每个天干在两读下各得不同地支，故命中结果不会含混。

    表值、锚点与查找位置的来源说明见知识条目 shensha.guoyin.readings。
    '''
    WUXING_JINGJI   = 0
    MODERN          = 1

  # 这些表格用于查询国印贵人。
  # 各读法分别从禄派生自身表；表值相同不合并知识身份。
  GUOYIN: Final[frozendict[GuoyinDef, frozendict[Tiangan, Dizhi]]] = frozendict({
    GuoyinDef.WUXING_JINGJI : _lu_offset(7),
    GuoyinDef.MODERN        : _lu_offset(8),
  })

  # 六甲旬空：一旬十干配十支，余下二支。六旬字面表展开为六十个合法干支锚，各锚取所在旬的冻结二支。
  # 二支定义与出处见 shensha.kongwang.xunkong，锚点与查询范围见 shensha.kongwang.repository。
  KONGWANG: Final[frozendict[Ganzhi, frozenset[Dizhi]]] = frozendict({
    Ganzhi.from_str(head).next(offset): frozenset(Dizhi(dz) for dz in absent)
    for head, absent in (
      ('甲子', '戌亥'), ('甲戌', '申酉'), ('甲申', '午未'),
      ('甲午', '辰巳'), ('甲辰', '寅卯'), ('甲寅', '子丑'),
    )
    for offset in range(10)
  })
