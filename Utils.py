import copy
from datetime import date
from typing import Union

from .Defines import Ganzhi, Tiangan, Dizhi, Shishen, Wuxing, Yinyang, ShierZhangsheng
from .Calendar import CalendarUtils, CalendarDate
from .Rules import (
  TraitTuple, HiddenTianganDict,
  YEAR_TO_MONTH_TABLE, DAY_TO_HOUR_TABLE, TIANGAN_TRAITS, DIZHI_TRAITS, 
  HIDDEN_TIANGANS_PERCENTAGE_TABLE, NAYIN_TABLE, TIANGAN_ZHANGSHENG_TABLE
)

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
    first_month_tiangan: Tiangan = YEAR_TO_MONTH_TABLE[year_tiangan]
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
    first_hour_tiangan: Tiangan = DAY_TO_HOUR_TABLE[day_tiangan]
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
    return copy.deepcopy(TIANGAN_TRAITS[tg])
  
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
    return copy.deepcopy(DIZHI_TRAITS[dz])
  
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
    return copy.deepcopy(HIDDEN_TIANGANS_PERCENTAGE_TABLE[dz])
  
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

    return NAYIN_TABLE[gz]

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
    zhangsheng_place: Dizhi = TIANGAN_ZHANGSHENG_TABLE[tg]

    if tg_yinyang is Yinyang.YIN:
      offset: int = zhangsheng_place.index - dz.index
    else:
      assert tg_yinyang is Yinyang.YANG
      offset: int = dz.index - zhangsheng_place.index

    return ShierZhangsheng.from_index(offset % 12)
