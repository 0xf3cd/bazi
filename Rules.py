# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from .Defines import Tiangan

# The mappings are used figure out the first month's Tiangan in a ganzhi year, i.e. 年上起月表.
YEAR_TO_MONTH_MAPPINGS: dict[Tiangan, Tiangan] = {
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

DAY_TO_HOUR_MAPPINGS: dict[Tiangan, Tiangan] = {
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
