import copy
from datetime import date
from collections import Counter
from typing import Union, Sequence, Optional

from .Defines import Ganzhi, Tiangan, Dizhi, Shishen, Wuxing, Yinyang, ShierZhangsheng, TianganRelation, DizhiRelation
from .Calendar import CalendarUtils, CalendarDate
from .Rules import TraitTuple, HiddenTianganDict, Rules


class BaziUtils:
  @staticmethod
  def get_day_ganzhi(dt: Union[date, CalendarDate]) -> Ganzhi:
    '''
    Return the corresponding Ganzhi of the given date in the sexagenary cycle.
    返回输入日期的日柱。

    Args:
    - dt: (Union[date, CalendarDate]) A date in the sexagenary cycle.

    Return: (Ganzhi) The Day Ganzhi (日柱).
    '''

    assert isinstance(dt, (date, CalendarDate))

    solar_date: CalendarDate = CalendarUtils.to_solar(dt)
    jiazi_day_date: date = date(2024, 3, 1) # 2024-03-01 is a day of "甲子".
    offset: int = (solar_date.to_date() - jiazi_day_date).days
    return Ganzhi.list_sexagenary_cycle()[offset % 60]

  @staticmethod
  def find_month_tiangan(year_tiangan: Tiangan, month_dizhi: Dizhi) -> Tiangan:
    '''
    Find out the Tiangan of the given month in the given year.
    输入年柱天干和月柱地支，返回月柱天干。

    Args:
    - year_tiangan: (Tiangan) The Tiangan of the Year Ganzhi (年柱天干).
    - month_dizhi: (Dizhi) The Dizhi of the Month Ganzhi (月柱地支 / 月令).

    Return: (Tiangan) The Tiangan of the Month Ganzhi (月柱天干).
    '''

    assert isinstance(year_tiangan, Tiangan)
    assert isinstance(month_dizhi, Dizhi)

    month_index: int = (month_dizhi.index - 2) % 12 # First month is "寅".
    first_month_tiangan: Tiangan = Rules.YEAR_TO_MONTH_TABLE[year_tiangan]
    month_tiangan_index: int = (first_month_tiangan.index + month_index) % 10
    return Tiangan.from_index(month_tiangan_index)

  @staticmethod
  def find_hour_tiangan(day_tiangan: Tiangan, hour_dizhi: Dizhi) -> Tiangan:
    '''
    Find out the Tiangan of the given hour (时辰) in the given day.
    输入日柱天干和时柱地支，返回时柱天干。

    Args:
    - day_tiangan: (Tiangan) The Tiangan of the Day Ganzhi (日柱天干).
    - hour_dizhi: (Dizhi) The Dizhi of the Hour Ganzhi (时柱地支).

    Return: (Tiangan) The Tiangan of the Hour Ganzhi (时柱天干).
    '''

    assert isinstance(day_tiangan, Tiangan)
    assert isinstance(hour_dizhi, Dizhi)

    hour_index: int = hour_dizhi.index
    first_hour_tiangan: Tiangan = Rules.DAY_TO_HOUR_TABLE[day_tiangan]
    hour_tiangan_index: int = (first_hour_tiangan.index + hour_index) % 10
    return Tiangan.from_index(hour_tiangan_index)

  @staticmethod
  def get_tiangan_traits(tg: Tiangan) -> TraitTuple:
    '''
    Get the Wuxing and Yinyang of the given Tiangan.
    输入天干，返回它的五行和阴阳。

    Args:
    - tg: (Tiangan) The Tiangan.

    Return: (TraitTuple) The Wuxing and Yinyang of the given Tiangan.
    '''

    assert isinstance(tg, Tiangan)
    return copy.deepcopy(Rules.TIANGAN_TRAITS[tg])
  
  @staticmethod
  def get_dizhi_traits(dz: Dizhi) -> TraitTuple:
    '''
    Get the Wuxing and Yinyang of the given Dizhi.
    输入地支，返回它的五行和阴阳。

    Args:
    - dz: (Dizhi) The Dizhi.

    Return: (TraitTuple) The Wuxing and Yinyang of the given Dizhi.
    '''

    assert isinstance(dz, Dizhi)
    return copy.deepcopy(Rules.DIZHI_TRAITS[dz])
  
  @staticmethod
  def get_hidden_tiangans(dz: Dizhi) -> HiddenTianganDict:
    '''
    Return the percentage of hidden Tiangans in the given Dizhi.
    输入地支，返回其中的藏干，以及各藏干的百分比。

    Args:
    - dz: (Dizhi) The Dizhi.

    Return: (HiddenTianganDict) The percentage of hidden Tiangans in the given Dizhi.
    '''

    assert isinstance(dz, Dizhi)
    return copy.deepcopy(Rules.HIDDEN_TIANGANS[dz])
  
  @staticmethod
  def get_shishen(day_master: Tiangan, other: Union[Tiangan, Dizhi]) -> Shishen:
    '''
    Get the Shishen of the given Tiangan.
    输入日主和某天干或者地支，返回天干或地支对应的十神。

    Args:
    - day_master: (Tiangan) The Tiangan of the Day Master.
    - other: (Union[Tiangan, Dizhi]) The Tiangan or Dizhi of the other.

    Return: (Shishen) The Shishen of the given Tiangan or Dizhi.

    Example:
    - get_shishen(Tiangan("甲"), Tiagan("甲")) -> Shishen("比肩") # "甲" is the "比肩" of "甲".
    - get_shishen(Tiangan("甲"), Dizhi("寅")) -> Shishen("比肩")  # "寅" is the "比肩" of "甲".
    - get_shishen(Tiangan("壬"), Dizhi("戌")) -> Shishen("七杀")  # "戌" is the "七杀" of "壬".
    '''

    assert isinstance(day_master, Tiangan)
    assert isinstance(other, (Tiangan, Dizhi))

    if isinstance(other, Tiangan):
      other_tg: Tiangan = other
    else:
      hidden_tiangans: HiddenTianganDict = BaziUtils.get_hidden_tiangans(other)
      # Find out the key of the hidden tiangan with the highest percentage (即寻找地支中的主气).
      other_tg: Tiangan = max(hidden_tiangans.items(), key=lambda pair: pair[1])[0]

    day_master_traits: TraitTuple = BaziUtils.get_tiangan_traits(day_master)
    other_traits: TraitTuple = BaziUtils.get_tiangan_traits(other_tg)

    homogeneous: bool = day_master_traits.yinyang == other_traits.yinyang # Whether the two Tiangans are of the same Yinyang type.
    day_master_wuxing: Wuxing = day_master_traits.wuxing # The Wuxing of the Day Master.
    other_wuxing: Wuxing = other_traits.wuxing           # The Wuxing of the other.
    
    if day_master_wuxing == other_wuxing:           # 比劫
      if homogeneous:
        return Shishen.from_str('比')
      else:
        return Shishen.from_str('劫')
    elif day_master_wuxing.generates(other_wuxing): # 食伤
      if homogeneous:
        return Shishen.from_str('食')
      else:
        return Shishen.from_str('伤')
    elif day_master_wuxing.destructs(other_wuxing): # 财星
      if homogeneous:
        return Shishen.from_str('才')
      else:
        return Shishen.from_str('财')
    elif other_wuxing.generates(day_master_wuxing): # 印枭
      if homogeneous:
        return Shishen.from_str('枭')
      else:
        return Shishen.from_str('印')
    else:                                           # 官杀
      assert other_wuxing.destructs(day_master_wuxing) 
      if homogeneous:
        return Shishen.from_str('杀')
      else:
        return Shishen.from_str('官')

  @staticmethod
  def get_nayin_str(gz: Ganzhi) -> str:
    '''
    Get the Nayin string of the given Ganzhi (i.e. pillar).
    输入干支，返回干支对应的纳音。

    Args:
    - gz: (Ganzhi) The Ganzhi / pillar.

    Return: (str) The Nayin string of the given Ganzhi.

    Example:
    - get_nayin_str(Ganzhi.from_str("甲子")) -> "海中金"
    '''

    assert isinstance(gz, Ganzhi)
    
    tg, dz = gz
    tg_traits, dz_traits = BaziUtils.get_tiangan_traits(tg), BaziUtils.get_dizhi_traits(dz)
    assert tg_traits.yinyang == dz_traits.yinyang # The yinyang of Tiangan and Dizhi should be the same.

    return Rules.NAYIN[gz]

  @staticmethod
  def get_12zhangsheng(tg: Tiangan, dz: Dizhi) -> ShierZhangsheng:
    '''
    Get the shier zhangsheng for the input Tiangan and Dizhi.
    输入天干和地支，返回对应的十二长生。

    Args:
    - tg: (Tiangan) The Tiangan.
    - dz: (Dizhi) The Dizhi.

    Return: (ShierZhangsheng) The Shier Zhangsheng of the given Ganzhi.

    Example:
    - get_12zhangsheng(Tiangan.甲, Dizhi.子) -> ShierZhangsheng.沐浴
    - get_12zhangsheng(Tiangan.丙, Dizhi.午) -> ShierZhangsheng.帝旺
    - get_12zhangsheng(Tiangan.辛, Dizhi.丑) -> ShierZhangsheng.养
    '''
    
    assert isinstance(tg, Tiangan)
    assert isinstance(dz, Dizhi)

    tg_yinyang: Yinyang = BaziUtils.get_tiangan_traits(tg).yinyang
    zhangsheng_place: Dizhi = Rules.TIANGAN_ZHANGSHENG[tg]

    if tg_yinyang is Yinyang.YIN:
      offset: int = zhangsheng_place.index - dz.index
    else:
      assert tg_yinyang is Yinyang.YANG
      offset: int = dz.index - zhangsheng_place.index

    return ShierZhangsheng.from_index(offset % 12)
  
  @staticmethod
  def find_12zhangsheng_dizhi(tg: Tiangan, place: ShierZhangsheng) -> Dizhi:
    '''
    Find the Dizhi of the input Tiangan and ShierZhangsheng.
    输入天干和十二长生，返回对应的地支。

    This is intended to be the opposite query of `get_12zhangsheng`.
    本方法用于反向查询十二长生所在地支。

    Args:
    - tg: (Tiangan) The Tiangan.
    - place: (ShierZhangsheng) The ShierZhangsheng.

    Return: (Dizhi) The Dizhi of the given Tiangan and ShierZhangsheng.

    Example:
    - find_12zhangsheng_dizhi(Tiangan.甲, ShierZhangsheng.沐浴) -> Dizhi.子
    - find_12zhangsheng_dizhi(Tiangan.丙, ShierZhangsheng.帝旺) -> Dizhi.午
    - find_12zhangsheng_dizhi(Tiangan.辛, ShierZhangsheng.养) -> Dizhi.丑
    '''

    assert isinstance(tg, Tiangan)
    assert isinstance(place, ShierZhangsheng)

    tg_yinyang: Yinyang = BaziUtils.get_tiangan_traits(tg).yinyang
    zhangsheng_dizhi: Dizhi = Rules.TIANGAN_ZHANGSHENG[tg]
    offset: int = place.index if tg_yinyang is Yinyang.YANG else -place.index
    return Dizhi.from_index((zhangsheng_dizhi.index + offset) % 12)
  
  @staticmethod
  def get_tiangan_lu(tg: Tiangan) -> Dizhi:
    '''
    Return the Dizhi of Lu (禄) for the given Tiangan.
    输入天干，返回该天干对应的禄。

    Args:
    - tg: (Tiangan) The Tiangan.

    Return: (Dizhi) The Lu Dizhi of the given Tiangan.

    Example:
    - get_lu(Tiangan.甲) -> Dizhi.寅
    '''

    assert isinstance(tg, Tiangan)
    return Rules.TIANGAN_LU[tg]


class TianganRelationUtils:
  @staticmethod
  def find_tiangan_combos(tiangans: Sequence[Tiangan], relation: TianganRelation) -> list[frozenset[Tiangan]]:
    '''
    Find all possible Tiangan combos in the given `tiangans` that satisfy the `relation`.
    返回 `tiangans` 中所有满足该关系的组合。

    Note:
    - The returned frozensets don't reveal the directions.
    - For example, if the returned value for SHENG relation is [{甲, 丁}], then we are unable to infer it is 甲 that generates 丁 or 丁 that generates 甲.
    - For mutual/non-directional relations (e.g. HE and CHONG), that's fine, because we don't care about the direction.
    - For uni-directional relations, please use other static methods in this class to check that (e.g. `TianganRelationUtils.sheng` and `TianganRelationUtils.ke`). 
    - 返回的 frozensets 中没有体现关系作用的方向。
    - 比如说，如果检查输入天干的相生关系并返回 [{甲, 丁}]，那么不能从返回结果中看出是甲生丁还是丁生甲。
    - 对于无方向的关系来说（合、冲），我们不用关心返回结果中的方向。
    - 对于有方向的关系来说（生、克），请使用其他静态方法来检查（如 `TianganRelationUtils.sheng` 和 `TianganRelationUtils.ke`）。

    Args:
    - tiangans: (Sequence[Tiangan]) The Tiangans to check.
    - relation: (TianganRelation) The relation to check.

    Return: (list[frozenset[Tiangan]]) The result containing all matching Tiangan combos. Note that returned frozensets don't reveal the directions.

    Examples:
    - find_tiangan_combos([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.合):
      - return: [{Tiangan.丙, Tiangan.辛}]
    - find_tiangan_combos([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.冲):
      - return: [{Tiangan.甲, Tiangan.庚}]
    - find_tiangan_combos([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.生):
      - return: [{Tiangan.甲, Tiangan.丙}, {Tiangan.甲, Tiangan.丁}]
      - Note that the returned frozensets don't contain the direction.
    - find_tiangan_combos([Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛], TianganRelation.克):
      - return: [{Tiangan.甲, Tiangan.庚}, {Tiangan.甲, Tiangan.辛}, {Tiangan.丙, Tiangan.庚}, {Tiangan.丙, Tiangan.辛},
                 {Tiangan.丁, Tiangan.庚}, {Tiangan.丁, Tiangan.辛}]
      - Note that the returned frozensets don't contain the direction.
    '''

    assert isinstance(relation, TianganRelation)
    assert all(isinstance(tg, Tiangan) for tg in tiangans)

    tg_tuple: tuple[Tiangan, ...] = tuple(tiangans)

    if relation is TianganRelation.合:
      return [copy.deepcopy(combo) for combo in Rules.TIANGAN_HE if combo.issubset(tg_tuple)]
    elif relation is TianganRelation.冲:
      return [copy.deepcopy(combo) for combo in Rules.TIANGAN_CHONG if combo.issubset(tg_tuple)]
    elif relation is TianganRelation.生:
      return [frozenset(combo) for combo in Rules.TIANGAN_SHENG if set(tg_tuple).issuperset(combo)]
    else: 
      assert relation is TianganRelation.克
      return [frozenset(combo) for combo in Rules.TIANGAN_KE if set(tg_tuple).issuperset(combo)]

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
  

class DizhiRelationUtils:
  @staticmethod
  def find_dizhi_combos(dizhis: Sequence[Dizhi], relation: DizhiRelation) -> list[frozenset[Dizhi]]:
    '''
    Find all possible Dizhi combos in the given `dizhis` that satisfy the `relation`.
    返回`dizhis`中所有满足该关系的组合。

    Note:
    - The returned frozensets don't reveal the directions.
    - For example, if the returned value for SHENG relation is [{午, 寅}], then we are unable to infer it is 寅 that generates 午 or 午 that generates 寅.
    - For mutual/non-directional relations (e.g. SANHE, SANHUI, ...), that's fine, because we don't care about the direction.
    - For uni-directional relations, please use other static methods in this class to check that (e.g. `DizhiRelationUtils.sheng`, `DizhiRelationUtils.ke`, ...). 
    - For XING relation, it's a bit more complicated.
      - Some definitions require all the Dizhis to appear in order to qualify the SANXING (三刑) relation (a subset of XING).
      - Some definitions consider only two Dizhis appearing a valid XING relation (e.g. only 丑 and 未 can form a XING relation).
      - In this method, for 丑未戌 and 寅卯巳 SANXING, it is required that all three Dizhis to present in order to qualify the XING relation.
      - Use `DizhiRelationUtils.xing` to do more fine-grained checking.
    - 返回的 frozensets 中没有体现关系作用的方向。
    - 比如说，如果检查输入地支的相生关系并返回 [{午, 寅}]，那么不能从返回结果中看出是寅生午还是午生寅。
    - 对于无方向的关系来说（合、会），我们不用关心返回结果中的方向。
    - 对于有方向的关系来说（生、克等），请使用其他静态方法来检查（如 `DizhiRelationUtils.sheng`， `DizhiRelationUtils.ke` 等）。
    - 对于刑关系，更复杂一些：
      - 对于辰午酉亥自刑，只需要同时出现两次就满足相刑关系。
      - 对于子卯相刑，只需要子、卯都出现就满足相刑关系。
      - 对于丑未戌、寅巳申三刑，有的看法认为需要三个地支同时出现才算刑，有的看法认为只需要出现两个也算相刑。
      - 本方法的实现中，对于丑未戌、寅巳申三刑，需要同时出现三个地支才算相刑。
      - 请使用 `DizhiRelationUtils.xing` 来进行更细粒度的检查。

    Note:
    - For ANHE relation, the `Rules.AnheDef.NORMAL_EXTENDED` definition is used, as it is the widest definition.
    - 对于暗合关系的查询，默认使用 `Rules.AnheDef.NORMAL_EXTENDED` 定义，因为它包含最多的暗合地支组合。

    Note:
    - For XING relation, all Dizhis should appear in order to qualify the XING relation.
    - `Rules.XingDef.NORMAL` definition is used.
    - e.g., if only 丑 and 未 appear in the input, then the XING relation is not satisfied (戌 missing).
    - 对于刑关系，所有的地支都出现才能满足相刑关系。
    - 默认使用 `Rules.XingDef.NORMAL` 定义。
    - 举例来说，如果输入中只有丑、未，那么不符合相刑关系（缺少戌）。

    Args:
    - dizhis: (Sequence[Dizhi]) The Dizhis to check.
    - relation: (DizhiRelation) The relation to check.

    Return: (list[frozenset[Dizhi]]) The result containing all matching Dizhi combos.

    Examples:
    - find_dizhi_combos([Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.午, Dizhi.未], DizhiRelation.三会)
      - return: [{Dizhi.寅, Dizhi.卯, Dizhi.辰}]
    - find_dizhi_combos([Dizhi.寅, Dizhi.卯, Dizhi.丑, Dizhi.午, Dizhi.申], DizhiRelation.暗合)
      - return: [{ Dizhi.卯, Dizhi.申}, { Dizhi.寅, Dizhi.午}, { Dizhi.寅, Dizhi.丑}]
      - `Rules.AnheDef.NORMAL_EXTENDED` is used.
    - find_dizhi_combos([Dizhi.寅,Dizhi.巳, Dizhi.申, Dizhi.辰], DizhiRelation.刑)
      - return: [{ Dizhi.子, Dizhi.卯}, { Dizhi.寅, Dizhi.巳, Dizhi.申 }]
      - Only one 辰 appears in the input - not forming a XING relation.
    - find_dizhi_combos([Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.辰, Dizhi.辰], DizhiRelation.刑)
      - return: [{ Dizhi.寅, Dizhi.巳, Dizhi.申 }, { Dizhi.辰 }] # Only one 辰 in the returned set!
      - 辰 appear twice in the input - forming a XING relation.
    - find_dizhi_combos([Dizhi.卯, Dizhi.子, Dizhi.寅, Dizhi.巳], DizhiRelation.刑)
      - return: [{ Dizhi.子, Dizhi.卯}]
      - `Rules.XingDef.STRICT` is used.
      - 申 is missing - "寅巳申" all three dizhis are required to form a XING relation.
    '''

    assert isinstance(relation, DizhiRelation), f'Unexpected type of relation: {type(relation)}'
    assert isinstance(dizhis, Sequence), "Non-sequence input loses the info of Dizhis' frequency."
    assert all(isinstance(dz, Dizhi) for dz in dizhis)
    dz_tuple: tuple[Dizhi, ...] = tuple(dizhis)

    # The following `copy.deepcopy` can be removed actually... Since frozenset is immutable.
    if relation is DizhiRelation.三会:
      return [copy.deepcopy(combo) for combo in Rules.DIZHI_SANHUI if combo.issubset(dz_tuple)]
    
    elif relation is DizhiRelation.六合:
      return [copy.deepcopy(combo) for combo in Rules.DIZHI_LIUHE if combo.issubset(dz_tuple)]
    
    elif relation is DizhiRelation.暗合:
      anhe_table: frozenset[frozenset[Dizhi]] = Rules.DIZHI_ANHE[Rules.AnheDef.NORMAL_EXTENDED] # Use `NORMAL_EXTENDED` here, which has the widest definition.
      return [copy.deepcopy(combo) for combo in anhe_table if combo.issubset(dz_tuple)]
    
    elif relation is DizhiRelation.通合:
      return [copy.deepcopy(combo) for combo in Rules.DIZHI_TONGHE if combo.issubset(dz_tuple)]
    
    elif relation is DizhiRelation.通禄合:
      return [copy.deepcopy(combo) for combo in Rules.DIZHI_TONGLUHE if combo.issubset(dz_tuple)]
    
    elif relation is DizhiRelation.三合:
      return [copy.deepcopy(combo) for combo in Rules.DIZHI_SANHE if combo.issubset(dz_tuple)]
    
    elif relation is DizhiRelation.半合:
      return [copy.deepcopy(combo) for combo in Rules.DIZHI_BANHE if combo.issubset(dz_tuple)]
    
    elif relation is DizhiRelation.刑:
      dz_counter: Counter[Dizhi] = Counter(dz_tuple)

      ret: set[frozenset[Dizhi]] = set()
      for xing_tuple in Rules.DIZHI_XING[Rules.XingDef.STRICT]:
        # Sadly direct comparisons not implemented on `Counter` with Python 3.9.
        # Otherwise we can use `dz_counter >= Counter(xing_tuple)` here.
        xing_dz_counter: Counter[Dizhi] = Counter(xing_tuple)
        if dz_counter & xing_dz_counter == xing_dz_counter:
          ret.add(frozenset(xing_tuple))

      return list(ret)
    
    elif relation is DizhiRelation.冲:
      return [copy.deepcopy(combo) for combo in Rules.DIZHI_CHONG if combo.issubset(dz_tuple)]

    return []

  @staticmethod
  def sanhui(dz1: Dizhi, dz2: Dizhi, dz3: Dizhi) -> Optional[Wuxing]:
    '''
    Check if the input Dizhis are in SANHUI (三会) relation. If so, return the corresponding Wuxing. If not, return `None`.
    We don't care the order of the inputs, since SANHUI relation is non-directional/mutual.
    检查输入的地支是否构成三会关系。如果是，返回三会后形成的五行。否则返回 `None`。
    返回结果与输入的地支顺序无关，因为三会关系是无方向的。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.
    - dz3: (Dizhi) The third Dizhi.

    Return: (Optional[Wuxing]) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in SANHUI (三会) relation.

    Examples:
    - sanhui(Dizhi.寅, Dizhi.卯, Dizhi.辰)
      - return: Wuxing.木
    - sanhui(Dizhi.寅, Dizhi.卯, Dizhi.丑)
      - return: None
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2, dz3))
    combo: frozenset[Dizhi] = frozenset((dz1, dz2, dz3))
    return Rules.DIZHI_SANHUI.get(combo, None)
  
  @staticmethod
  def liuhe(dz1: Dizhi, dz2: Dizhi) -> Optional[Wuxing]:
    '''
    Check if the input Dizhis are in LIUHE (六合) relation. If so, return the corresponding Wuxing. If not, return `None`.
    We don't care the order of the inputs, since LIUHE relation is non-directional/mutual.
    检查输入的地支是否构成六合关系。如果是，返回六合后形成的五行。否则返回 `None`。
    返回结果与输入的地支顺序无关，因为六合关系是无方向的。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.

    Return: (Optional[Wuxing]) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in LIUHE (六合) relation.

    Examples:
    - liuhe(Dizhi.寅, Dizhi.亥)
      - return: Wuxing.木
    - liuhe(Dizhi.寅, Dizhi.辰)
      - return: None
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
    combo: frozenset[Dizhi] = frozenset((dz1, dz2))
    return Rules.DIZHI_LIUHE.get(combo, None)
  
  @staticmethod
  def anhe(dz1: Dizhi, dz2: Dizhi, *, definition: Rules.AnheDef = Rules.AnheDef.NORMAL) -> bool:
    '''
    Check if the input Dizhis are in ANHE (暗合) relation. If so, return `True`. If not, return `False`.
    There are multiple definitions for ANHE. The default definition is `Rules.AnheDef.NORMAL`.
    检查输入的地支是否构成暗合关系。如果是，返回 `True`。否则返回 `False`。
    暗合关系的看法有多种，默认使用 `Rules.AnheDef.NORMAL`。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.
    - definition: (Rules.AnheDef) The definition of the ANHE relation. Default to `Rules.AnheDef.NORMAL`.

    Return: (bool) Whether the Dizhis form in ANHE (暗合) relation.

    Examples:
    - anhe(Dizhi.寅, Dizhi.午)
      - return: True
    - anhe(Dizhi.寅, Dizhi.丑)
      - return: False
    - anhe(Dizhi.寅, Dizhi.丑, Rules.AnheDef.NORMAL_EXTENDED)
      - return: True
    - anhe(Dizhi.寅, Dizhi.午, Rules.AnheDef.MANGPAI)
      - return: False
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
    assert isinstance(definition, Rules.AnheDef)
    combo: frozenset[Dizhi] = frozenset((dz1, dz2))
    return combo in Rules.DIZHI_ANHE[definition]
  
  @staticmethod
  def tonghe(dz1: Dizhi, dz2: Dizhi) -> bool:
    '''
    Check if the input Dizhis are in TONGHE (通合) relation. If so, return `True`. If not, return `False`.
    检查输入的地支是否构成通合关系。如果是，返回 `True`。否则返回 `False`。
    通合指的是两个地支的所有藏干都两两相合。通合常用于盲派。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.

    Return: (bool) Whether the Dizhis form in TONGHE (通合) relation.

    Examples:
    - tonghe(Dizhi.寅, Dizhi.午)
      - return: False
    - tonghe(Dizhi.寅, Dizhi.丑)
      - return: True
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
    combo: frozenset[Dizhi] = frozenset((dz1, dz2))
    return combo in Rules.DIZHI_TONGHE
  
  @staticmethod
  def tongluhe(dz1: Dizhi, dz2: Dizhi) -> bool:
    '''
    Check if the input Dizhis are in TONGLUHE (通禄合) relation. If so, return `True`. If not, return `False`.
    检查输入的地支是否构成通禄合关系。如果是，返回 `True`。否则返回 `False`。
    通禄合指的是五合的天干在地支对应的禄身之间的相合。通禄合常用于盲派。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.

    Return: (bool) Whether the Dizhis form in TONGLUHE (通禄合) relation.

    Examples:
    - tonghe(Dizhi.寅, Dizhi.午)
      - return: True
    - tonghe(Dizhi.寅, Dizhi.丑)
      - return: False
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
    combo: frozenset[Dizhi] = frozenset((dz1, dz2))
    return combo in Rules.DIZHI_TONGLUHE
  
  @staticmethod
  def sanhe(dz1: Dizhi, dz2: Dizhi, dz3: Dizhi) -> Optional[Wuxing]:
    '''
    Check if the input Dizhis are in SANHE (三合) relation. If so, return the corresponding Wuxing. If not, return `None`.
    检查输入的地支是否构成三合关系。如果是，返回对应的五行。如果不是，返回 `None`。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.
    - dz3: (Dizhi) The third Dizhi.

    Return: (Optional[Wuxing]) The corresponding Wuxing if the Dizhis form in SANHE (三合) relation. Otherwise, return `None`.

    Examples:
    - sanhe(Dizhi.亥, Dizhi.卯, Dizhi.未)
      - return: Wuxing.木
    - sanhe(Dizhi.亥, Dizhi.卯, Dizhi.丑)
      - return: None
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2, dz3))
    combo: frozenset[Dizhi] = frozenset((dz1, dz2, dz3))
    return Rules.DIZHI_SANHE.get(combo, None)

  @staticmethod
  def banhe(dz1: Dizhi, dz2: Dizhi) -> Optional[Wuxing]:
    '''
    Check if the input Dizhis are in BANHE (半合) relation. If so, return the corresponding Wuxing. If not, return `None`.
    检查输入的地支是否构成半合关系。如果是，返回对应的五行。如果不是，返回 `None`。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.

    Return: (Optional[Wuxing]) The corresponding Wuxing if the Dizhis form in BANHE (半合) relation. Otherwise, return `None`.

    Examples:
    - banhe(Dizhi.亥, Dizhi.卯)
      - return: Wuxing.木
    - banhe(Dizhi.卯, Dizhi.未)
      - return: Wuxing.木
    - banhe(Dizhi.亥, Dizhi.丑)
      - return: None
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
    combo: frozenset[Dizhi] = frozenset((dz1, dz2))
    return Rules.DIZHI_BANHE.get(combo, None)

  @staticmethod
  def xing(*dizhis: Dizhi, definition: Rules.XingDef = Rules.XingDef.STRICT) -> Optional[Rules.XingSubType]:
    '''
    Check if the input Dizhis is a exact match for XING (刑) relation. If so, return the type of the XING relation. If not, return `None`.
    There are multiple definitions for 刑. The default definition is `Rules.XingDef.STRICT`.
    If `Rules.XingDef.LOOSE` is used, then the `dizhis` order (direction) matters.
    If `Rules.XingDef.STRICT` is used, then the `dizhis` order does not matter.

    检查输入的地支是否刚好构成相刑关系。如果是，返回相刑的类型。如果不是，返回 `None`。
    相刑关系的看法有多种，默认使用 `Rules.XingDef.STRICT`。
    如果使用 `Rules.XingDef.LOOSE`，则 `dizhis` 的顺序会影响结果。
    如果使用 `Rules.XingDef.STRICT`，则 `dizhis` 的顺序不会影响结果。

    Note:
    - Maximum length of the input `dizhis` is 3.
    - `dizhis` 的最大长度为 3。

    Args:
    - *dizhis: (Dizhi) The Dizhis to check.
    - definition: (Rules.XingDef) The definition for 刑.

    Return: (Optional[Rules.XingSubType]) The type of the XING relation if the Dizhis form in XING (刑) relation. Otherwise, return `None`.

    Examples:
    - xing([Dizhi.寅, Dizhi.巳, Dizhi.申])
      - return: XingSubType.SANXING
    - xing([Dizhi.寅, Dizhi.巳], Rules.XingDef.STRICT)
      - return: None
    - xing([Dizhi.寅, Dizhi.巳], Rules.XingDef.LOOSE)
      - return: XingSubType.SANXING
    - xing((Dizhi.午))
      - return: None
    - xing((Dizhi.午, Dizhi.午))
      - return: XingSubType.ZIXING
    - xing((Dizhi.午), Rules.XingDef.LOOSE)
      - return: None
    - xing([Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午]) # Not a exact match.
      - return: None
    - xing([Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午, Dizhi.午]) # Multiple matches.
      - return: None
    '''

    assert all(isinstance(dz, Dizhi) for dz in dizhis)
    assert 0 <= len(dizhis) <= 3
    assert isinstance(definition, Rules.XingDef)

    xing_rules: dict[tuple[Dizhi, ...], Rules.XingSubType] = Rules.DIZHI_XING[definition]
    return xing_rules.get(dizhis, None)

  @staticmethod
  def chong(dz1: Dizhi, dz2: Dizhi) -> bool:
    '''
    Check if the input Dizhis are in CHONG (冲) relation. If so, return `True`. If not, return `False`.
    检查输入的地支是否构成冲关系。如果是，返回 `True`。否则返回 `False`。

    Args:
    - dz1: (Dizhi) The first Dizhi.
    - dz2: (Dizhi) The second Dizhi.

    Return: (bool) Whether the Dizhis form in CHONG (冲) relation.

    Examples:
    - chong(Dizhi.子, Dizhi.午)
      - return: True
    - chong(Dizhi.午, Dizhi.子)
      - return: True
    - chong(Dizhi.子, Dizhi.丑)
      - return: False
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
    return frozenset((dz1, dz2)) in Rules.DIZHI_CHONG
