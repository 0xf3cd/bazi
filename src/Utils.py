import copy
from datetime import date
from typing import Union, Iterable, Optional

from .Defines import Ganzhi, Tiangan, Dizhi, Shishen, Wuxing, Yinyang, ShierZhangsheng, TianganRelation, DizhiRelation
from .Calendar import CalendarUtils, CalendarDate
from .Rules import TraitTuple, HiddenTianganDict, RULES


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
    first_month_tiangan: Tiangan = RULES.YEAR_TO_MONTH_TABLE[year_tiangan]
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
    first_hour_tiangan: Tiangan = RULES.DAY_TO_HOUR_TABLE[day_tiangan]
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
    return copy.deepcopy(RULES.TIANGAN_TRAITS[tg])
  
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
    return copy.deepcopy(RULES.DIZHI_TRAITS[dz])
  
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
    return copy.deepcopy(RULES.HIDDEN_TIANGANS[dz])
  
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

    return RULES.NAYIN[gz]

  @staticmethod
  def get_shier_zhangsheng(tg: Tiangan, dz: Dizhi) -> ShierZhangsheng:
    '''
    Get the shier zhangsheng for the input Tiangan and Dizhi.
    输入天干和地支，返回对应的十二长生。

    Args:
    - tg: (Tiangan) The Tiangan.
    - dz: (Dizhi) The Dizhi.

    Return: (ShierZhangsheng) The Shier Zhangsheng of the given Ganzhi.

    Example:
    - get_shier_zhangsheng(Tiangan.甲, Dizhi.子) -> ShierZhangsheng.沐浴
    - get_shier_zhangsheng(Tiangan.丙, Dizhi.午) -> ShierZhangsheng.帝旺
    - get_shier_zhangsheng(Tiangan.辛, Dizhi.丑) -> ShierZhangsheng.养
    '''
    
    assert isinstance(tg, Tiangan)
    assert isinstance(dz, Dizhi)

    tg_yinyang: Yinyang = BaziUtils.get_tiangan_traits(tg).yinyang
    zhangsheng_place: Dizhi = RULES.TIANGAN_ZHANGSHENG[tg]

    if tg_yinyang is Yinyang.YIN:
      offset: int = zhangsheng_place.index - dz.index
    else:
      assert tg_yinyang is Yinyang.YANG
      offset: int = dz.index - zhangsheng_place.index

    return ShierZhangsheng.from_index(offset % 12)


class TianganRelationUtils:
  @staticmethod
  def find_tiangan_combos(tiangans: Iterable[Tiangan], relation: TianganRelation) -> list[frozenset[Tiangan]]:
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
    tg_set: set[Tiangan] = set(tiangans)
    for tg in tg_set:
      assert isinstance(tg, Tiangan)

    if relation is TianganRelation.合:
      return [copy.deepcopy(combo) for combo in RULES.TIANGAN_HE if tg_set.issuperset(combo)]
    elif relation is TianganRelation.冲:
      return [copy.deepcopy(combo) for combo in RULES.TIANGAN_CHONG if tg_set.issuperset(combo)]
    elif relation is TianganRelation.生:
      return [frozenset(combo) for combo in RULES.TIANGAN_SHENG if tg_set.issuperset(combo)]
    else: 
      assert relation is TianganRelation.克
      return [frozenset(combo) for combo in RULES.TIANGAN_KE if tg_set.issuperset(combo)]

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
    if fs in RULES.TIANGAN_HE:
      return RULES.TIANGAN_HE[fs]
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
    return frozenset((tg1, tg2)) in RULES.TIANGAN_CHONG
  
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
    return (tg1, tg2) in RULES.TIANGAN_SHENG
  
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
    return (tg1, tg2) in RULES.TIANGAN_KE
  

class DizhiRelationUtils:
  @staticmethod
  def find_dizhi_combos(dizhis: Iterable[Dizhi], relation: DizhiRelation) -> list[frozenset[Dizhi]]:
    '''
    Find all possible Dizhi combos in the given `dizhis` that satisfy the `relation`.
    返回`dizhis`中所有满足该关系的组合。

    Note:
    - The returned frozensets don't reveal the directions.
    - For example, if the returned value for SHENG relation is [{午, 寅}], then we are unable to infer it is 寅 that generates 午 or 午 that generates 寅.
    - For mutual/non-directional relations (e.g. SANHE, SANHUI, ...), that's fine, because we don't care about the direction.
    - For uni-directional relations, please use other static methods in this class to check that (e.g. `DizhiRelationUtils.sheng`, `DizhiRelationUtils.ke`, ...). 
    - 返回的 frozensets 中没有体现关系作用的方向。
    - 比如说，如果检查输入地支的相生关系并返回 [{午, 寅}]，那么不能从返回结果中看出是寅生午还是午生寅。
    - 对于无方向的关系来说（合、会），我们不用关心返回结果中的方向。
    - 对于有方向的关系来说（生、克等），请使用其他静态方法来检查（如 `DizhiRelationUtils.sheng`， `DizhiRelationUtils.ke` 等）。

    Args:
    - dizhis: (Sequence[Dizhi]) The Dizhis to check.
    - relation: (DizhiRelation) The relation to check.

    Return: (list[frozenset[Dizhi]]) The result containing all matching Dizhi combos.

    Examples:
    - find_dizhi_combos(Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.午, Dizhi.未], DizhiRelation.三会)
      - return: [{Dizhi.寅, Dizhi.卯, Dizhi.辰}]
    '''

    assert isinstance(relation, DizhiRelation)
    dz_set: set[Dizhi] = set(dizhis)
    for dz in dz_set:
      assert isinstance(dz, Dizhi)

    if relation is DizhiRelation.三会:
      return [copy.deepcopy(combo) for combo in RULES.DIZHI_SANHUI if dz_set.issuperset(combo)]
    # elif relation is DizhiRelation.六合:
    #   return [copy.deepcopy(combo) for combo in RULES.DIZHI_LIUHE if dz_set.issuperset(combo)]
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

    Return: (Optional[Wuxing]) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in Sanhui (三会) relation.
    '''

    assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2, dz3))
    combo: frozenset[Dizhi] = frozenset((dz1, dz2, dz3))
    return RULES.DIZHI_SANHUI.get(combo, None)
  
  # @staticmethod
  # def liuhe(dz1: Dizhi, dz2: Dizhi) -> Optional[Wuxing]:
  #   '''
  #   Check if the input Dizhis are in Liuhe (六合) relation. If so, return the corresponding Wuxing. If not, return `None`.
  #   检查输入的地支是否构成六合关系。如果是，返回六合后形成的五行。否则返回 `None`。

  #   Args:
  #   - dz1: (Dizhi) The first Dizhi.
  #   - dz2: (Dizhi) The second Dizhi.

  #   Return: (Optional[Wuxing]) The Wuxing that the Dizhis form, or `None` if the Dizhis are not in Liuhe (六合) relation.
  #   '''

  #   assert all(isinstance(dz, Dizhi) for dz in (dz1, dz2))
  #   combo: frozenset[Dizhi] = frozenset((dz1, dz2))
  #   return RULES.DIZHI_LIUHE.get(combo, None)
