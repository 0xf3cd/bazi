# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date, datetime, timedelta

from ..defines import Ganzhi, Tiangan, Dizhi, Shishen, Wuxing, ShierZhangsheng
from ..data_types import TraitTuple, HiddenTianganDict
from ..rules import BaziRules
from ..school import DayRollover


def ganzhi_of_day(dt: date) -> Ganzhi:
  '''
  返回输入日期的日柱。

  Args:
  - dt: (date) 公历日期。

  Return: (Ganzhi) 日柱。
  '''

  if not isinstance(dt, date):
    raise TypeError(f'Expected date, got {type(dt)}')
  if isinstance(dt, datetime):
    # datetime 输入只取日期。
    dt = date(dt.year, dt.month, dt.day)

  jiazi_day_date: date = date(2024, 3, 1) # 2024-03-01 为甲子日。
  offset: int = (dt - jiazi_day_date).days
  return Ganzhi(Tiangan.甲, Dizhi.子).next(offset)


def _ganzhi_of_day_at_moment(moment: datetime, day_rollover: DayRollover) -> Ganzhi:
  '''按所选换日点返回 `moment` 时刻的日柱。'''
  assert isinstance(moment, datetime)
  assert isinstance(day_rollover, DayRollover)

  if day_rollover is DayRollover.WAN_ZISHI:
    day_offset = 1 if moment.hour >= 23 else 0
  elif day_rollover is DayRollover.ZIZHENG:
    day_offset = 0
  else:
    raise AssertionError(f'DayRollover not wired up: {day_rollover}') # pragma: no cover # 不可达的枚举穷尽检查。
  return ganzhi_of_day(moment + timedelta(days=day_offset))


def ganzhi_of_year(ganzhi_year: int) -> Ganzhi:
  '''
  输入干支历年份，返回对应的天干和地支。

  Args:
  - ganzhi_year: (int) 干支年坐标。

  Return: (Ganzhi) 对应年份的干支。
  '''

  if not isinstance(ganzhi_year, int):
    raise TypeError(f'Expected int, got {type(ganzhi_year)}')
  return Ganzhi(Tiangan.甲, Dizhi.子).next(ganzhi_year - 1984) # 1984 为甲子年。


def month_tiangan(year_tiangan: Tiangan, month_dizhi: Dizhi) -> Tiangan:
  '''
  输入年柱天干和月柱地支，返回月柱天干。

  Args:
  - year_tiangan: (Tiangan) 年柱天干。
  - month_dizhi: (Dizhi) 月柱地支，即月令。

  Return: (Tiangan) 月柱天干。
  '''

  if not isinstance(year_tiangan, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(year_tiangan)}')
  if not isinstance(month_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(month_dizhi)}')

  month_index: int = (month_dizhi.index - Dizhi.寅.index) % 12
  first_month_tiangan: Tiangan = BaziRules.YEAR_TO_MONTH_TABLE[year_tiangan]
  month_tiangan_index: int = (first_month_tiangan.index + month_index) % 10
  return Tiangan.from_index(month_tiangan_index)


def hour_tiangan(day_tiangan: Tiangan, hour_dizhi: Dizhi) -> Tiangan:
  '''
  输入日柱天干和时柱地支，返回时柱天干。

  Args:
  - day_tiangan: (Tiangan) 日柱天干。
  - hour_dizhi: (Dizhi) 时柱地支。

  Return: (Tiangan) 时柱天干。
  '''

  if not isinstance(day_tiangan, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(day_tiangan)}')
  if not isinstance(hour_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(hour_dizhi)}')

  hour_index: int = hour_dizhi.index
  first_hour_tiangan: Tiangan = BaziRules.DAY_TO_HOUR_TABLE[day_tiangan]
  hour_tiangan_index: int = (first_hour_tiangan.index + hour_index) % 10
  return Tiangan.from_index(hour_tiangan_index)


def tiangan_traits(tg: Tiangan) -> TraitTuple:
  '''
  输入天干，返回它的五行和阴阳。

  Args:
  - tg: (Tiangan) 待查天干。

  Return: (TraitTuple) 天干的五行和阴阳。
  '''

  if not isinstance(tg, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg)}')
  return BaziRules.TIANGAN_TRAITS[tg]


def dizhi_traits(dz: Dizhi) -> TraitTuple:
  '''
  输入地支，返回它的五行和阴阳。

  Args:
  - dz: (Dizhi) 待查地支。

  Return: (TraitTuple) 地支的五行和阴阳。
  '''

  if not isinstance(dz, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dz)}')
  return BaziRules.DIZHI_TRAITS[dz]


def traits(tg_or_dz: Tiangan | Dizhi) -> TraitTuple:
  '''
  输入天干或者地支，返回它的五行和阴阳。

  Args:
  - tg_or_dz: (Tiangan | Dizhi) 待查天干或地支。

  Return: (TraitTuple) 对应的五行和阴阳。
  '''

  if not isinstance(tg_or_dz, (Tiangan, Dizhi)):
    raise TypeError(f'Expected Tiangan or Dizhi, got {type(tg_or_dz)}')
  if isinstance(tg_or_dz, Tiangan):
    return tiangan_traits(tg_or_dz)
  else:
    assert isinstance(tg_or_dz, Dizhi)
    return dizhi_traits(tg_or_dz)


def hidden_tiangans(dz: Dizhi) -> HiddenTianganDict:
  '''
  输入地支，返回其中的藏干，以及各藏干的百分比。

  Args:
  - dz: (Dizhi) 待查地支。

  Return: (HiddenTianganDict) 藏干及其百分比。
  '''

  if not isinstance(dz, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dz)}')
  return BaziRules.HIDDEN_TIANGANS[dz]


def shishen(day_master: Tiangan, other: Tiangan | Dizhi) -> Shishen:
  '''
  输入日主和某天干或者地支，返回天干或地支对应的十神。

  Args:
  - day_master: (Tiangan) 日主天干。
  - other: (Tiangan | Dizhi) 待查天干或地支；地支取主气。

  Return: (Shishen) 对应十神。

  Examples:
  - shishen(Tiangan("甲"), Tiangan("甲")) -> Shishen("比肩") # 甲为甲的比肩。
  - shishen(Tiangan("甲"), Dizhi("寅")) -> Shishen("比肩")  # 寅为甲的比肩。
  - shishen(Tiangan("壬"), Dizhi("戌")) -> Shishen("七杀")  # 戌为壬的七杀。
  '''

  if not isinstance(day_master, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(day_master)}')
  if not isinstance(other, (Tiangan, Dizhi)):
    raise TypeError(f'Expected Tiangan or Dizhi, got {type(other)}')

  def __find_tg() -> Tiangan:
    if isinstance(other, Tiangan):
      return other
    else:
      hiddens: HiddenTianganDict = hidden_tiangans(other)
      # 取藏干中百分比最高的主气。
      return max(hiddens.items(), key=lambda pair: pair[1])[0]
  
  other_tg: Tiangan = __find_tg()

  day_master_traits: TraitTuple = tiangan_traits(day_master)
  other_traits: TraitTuple = tiangan_traits(other_tg)

  homogeneous: bool = day_master_traits.yinyang == other_traits.yinyang # 两干阴阳是否相同。
  day_master_wuxing: Wuxing = day_master_traits.wuxing # 日主五行。
  other_wuxing: Wuxing = other_traits.wuxing           # 对方五行。
  
  if day_master_wuxing == other_wuxing:           # 比劫
    if homogeneous:
      return Shishen.比肩
    else:
      return Shishen.劫财
  elif day_master_wuxing.generates(other_wuxing): # 食伤
    if homogeneous:
      return Shishen.食神
    else:
      return Shishen.伤官
  elif day_master_wuxing.destructs(other_wuxing): # 财星
    if homogeneous:
      return Shishen.偏财
    else:
      return Shishen.正财
  elif other_wuxing.generates(day_master_wuxing): # 印枭
    if homogeneous:
      return Shishen.偏印
    else:
      return Shishen.正印
  else:                                           # 官杀
    assert other_wuxing.destructs(day_master_wuxing) 
    if homogeneous:
      return Shishen.七杀
    else:
      return Shishen.正官


def nayin_str(gz: Ganzhi) -> str:
  '''
  返回六十甲子干支对应的纳音；不属于六十甲子的组合抛出 `ValueError`。
  `Ganzhi` 本身允许全部 120 种天干、地支组合，本入口单独检查纳音的适用性。

  Args:
  - gz: (Ganzhi) 待查纳音的干支。

  Return: (str) 对应的纳音。

  Examples:
  - nayin_str(Ganzhi.from_str("甲子")) -> "海中金"
  '''

  if not isinstance(gz, Ganzhi):
    raise TypeError(f'Expected Ganzhi, got {type(gz)}')
  
  tg, dz = gz
  tg_traits, dz_traits = traits(tg), traits(dz)
  if tg_traits.yinyang != dz_traits.yinyang:
    raise ValueError(f'Unsupported Ganzhi for Nayin: {gz}')

  return BaziRules.NAYIN[gz]


def shier_zhangsheng(tg: Tiangan, dz: Dizhi) -> ShierZhangsheng:
  '''
  输入天干和地支，返回对应的十二长生。

  Args:
  - tg: (Tiangan) 待查天干。
  - dz: (Dizhi) 待查地支。

  Return: (ShierZhangsheng) 对应的十二长生。

  Examples:
  - shier_zhangsheng(Tiangan.甲, Dizhi.子) -> ShierZhangsheng.沐浴
  - shier_zhangsheng(Tiangan.丙, Dizhi.午) -> ShierZhangsheng.帝旺
  - shier_zhangsheng(Tiangan.辛, Dizhi.丑) -> ShierZhangsheng.养
  '''
  
  if not isinstance(tg, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg)}')
  if not isinstance(dz, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dz)}')

  return ShierZhangsheng.from_index(BaziRules._ZHANGSHENG_ROWS[tg].index(dz))


def from_shier_zhangsheng(tg: Tiangan, place: ShierZhangsheng) -> Dizhi:
  '''
  输入天干和十二长生，返回对应的地支，即 `shier_zhangsheng` 的反查。

  Args:
  - tg: (Tiangan) 待查天干。
  - place: (ShierZhangsheng) 十二长生位。

  Return: (Dizhi) 对应地支。

  Examples:
  - from_shier_zhangsheng(Tiangan.甲, ShierZhangsheng.沐浴) -> Dizhi.子
  - from_shier_zhangsheng(Tiangan.丙, ShierZhangsheng.帝旺) -> Dizhi.午
  - from_shier_zhangsheng(Tiangan.辛, ShierZhangsheng.养) -> Dizhi.丑
  '''

  if not isinstance(tg, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg)}')
  if not isinstance(place, ShierZhangsheng):
    raise TypeError(f'Expected ShierZhangsheng, got {type(place)}')

  return BaziRules._ZHANGSHENG_ROWS[tg][place.index]


def lu(tg: Tiangan) -> Dizhi:
  '''
  输入天干，返回该天干对应的禄。

  Args:
  - tg: (Tiangan) 待查天干。

  Return: (Dizhi) 禄位地支。

  Examples:
  - lu(Tiangan.甲) -> Dizhi.寅
  '''

  if not isinstance(tg, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(tg)}')
  return BaziRules.TIANGAN_LU[tg]
