from datetime import date
from .Defines import Ganzhi, Tiangan, Dizhi
from .Calendar import CalendarUtils, CalendarDate
from .Rules import YEAR_TO_MONTH_MAPPINGS, DAY_TO_HOUR_MAPPINGS

def get_day_ganzhi(dt: date | CalendarDate) -> Ganzhi:
  '''
  Return the corresponding Ganzhi of the given date in the sexagenary cycle.
  返回输入日期的日柱。

  Args:
  - dt: (date | CalendarDate) A date in the sexagenary cycle.

  Return: (Ganzhi) The Day Ganzhi (日柱).
  '''

  solar_date: CalendarDate = CalendarUtils.to_solar(dt)
  jiazi_day_date: date = date(2024, 3, 1) # 2024-03-01 is a day of "甲子".
  offset: int = (solar_date.to_date() - jiazi_day_date).days
  return Ganzhi.list_sexagenary_cycle()[offset % 60]


def find_month_tiangan(year_tiangan: Tiangan, month_dizhi: Dizhi) -> Tiangan:
  '''
  Find out the Tiangan of the given month in the given year.
  输入年柱天干和月柱地支，返回月柱天干。

  Args:
  - year_tiangan: (Tiangan) The Tiangan of the Year Ganzhi (年柱天干).
  - month_dizhi: (Dizhi) The Dizhi of the Month Ganzhi (月柱地支 / 月令).

  Return: (Tiangan) The Tiangan of the Month Ganzhi (月柱天干).
  '''

  month_index: int = (month_dizhi.index - 2) % 12 # First month is "寅".
  first_month_tiangan: Tiangan = YEAR_TO_MONTH_MAPPINGS[year_tiangan]
  month_tiangan_index: int = (first_month_tiangan.index + month_index) % 10
  return Tiangan.from_index(month_tiangan_index)


def find_hour_tiangan(day_tiangan: Tiangan, hour_dizhi: Dizhi) -> Tiangan:
  '''
  Find out the Tiangan of the given hour (时辰) in the given day.
  输入日柱天干和时柱地支，返回时柱天干。

  Args:
  - day_tiangan: (Tiangan) The Tiangan of the Day Ganzhi (日柱天干).
  - hour_dizhi: (Dizhi) The Dizhi of the Hour Ganzhi (时柱地支).

  Return: (Tiangan) The Tiangan of the Hour Ganzhi (时柱天干).
  '''

  hour_index: int = hour_dizhi.index
  first_hour_tiangan: Tiangan = DAY_TO_HOUR_MAPPINGS[day_tiangan]
  hour_tiangan_index: int = (first_hour_tiangan.index + hour_index) % 10
  return Tiangan.from_index(hour_tiangan_index)
