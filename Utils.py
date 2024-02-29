from datetime import date
from bazi import Ganzhi, CalendarUtils, CalendarDate

def get_day_ganzhi(dt: date | CalendarDate) -> Ganzhi:
  solar_date: CalendarDate = CalendarUtils.to_solar(dt)
  jiazi_day_date: date = date(2024, 3, 1) # 2024-03-01 is a day of "甲子".
  offset: int = (solar_date.to_date() - jiazi_day_date).days
  return Ganzhi.list_sexagenary_cycle()[offset % 60]
