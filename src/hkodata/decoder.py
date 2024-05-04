#!/usr/bin/env python3
#
# bazi/hko/decoder.py
# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
#
# Decode the encoded data produced by encoder.py.

from pathlib import Path
from datetime import date
from typing import TypedDict, Optional

from ..Defines import Jieqi, Ganzhi
from .common import END_YEAR, START_YEAR, get_jieqi_encoded_data_path, get_lunardate_encoded_data_path, date_to_bytes, bytes_to_date, bytes_to_int
from .encoder import do_encode, encoded_data_ready


JieqiDates = dict[Jieqi, date] # Jieqi -> Solar-calendar Date

class DecodedJieqiDates:
  '''
  This class is used to query the solar-calendar date (Gregorian Calendar) of each Jieqi in each solar-calendar year.

  TODO: Creation of `DecodedJieqiDates` can be time-consuming. Optimization needed in the future??
  ''' 

  date_bytes_len: int = len(date_to_bytes(date(2000, 1, 1)))

  def __init__(self) -> None:
    if not encoded_data_ready():
      do_encode()

    self._start_year = START_YEAR
    self._end_year = END_YEAR

    jieqi_encoded_path: Path = get_jieqi_encoded_data_path()
    assert jieqi_encoded_path.exists() and jieqi_encoded_path.is_file()
    assert jieqi_encoded_path.stat().st_size % DecodedJieqiDates.date_bytes_len == 0, f'Encoded jieqi data should be a multiple of {DecodedJieqiDates.date_bytes_len} bytes, but it is {jieqi_encoded_path.stat().st_size} bytes.'
    assert jieqi_encoded_path.stat().st_size % (DecodedJieqiDates.date_bytes_len * 24) == 0, f'There are 24 jieqis in each year, so encoded jieqi data should be a multiple of 24 * {DecodedJieqiDates.date_bytes_len} bytes, but it is {jieqi_encoded_path.stat().st_size} bytes.'

    with jieqi_encoded_path.open('rb') as f:
      encoded_bytes: bytes = f.read()
    
    assert len(encoded_bytes) == 24 * (self._end_year - self._start_year + 1) * DecodedJieqiDates.date_bytes_len
    self._bytes = encoded_bytes

    # In Georgian calendar, the first Jieqi is "小寒".
    # But in `Jieqi`'s order, the first Jieqi is "立春".
    jieqi_list: list[Jieqi] = Jieqi.as_list()
    self._actual_jieqi_order: list[Jieqi] = jieqi_list[-2:] + jieqi_list[:-2] # This is the real order in HKO data.

    self._jieqi_offset_mapping: dict[Jieqi, int] = { k : v for k, v in zip(self._actual_jieqi_order, range(0, 24 * DecodedJieqiDates.date_bytes_len, DecodedJieqiDates.date_bytes_len)) }
    assert len(self._jieqi_offset_mapping) == 24

    self._cached_datetimes: dict[int, JieqiDates] = {}

  @property
  def start_year(self) -> int:
    '''Note: Gregorian/Solar year / 公历年'''
    return self._start_year
  
  @property
  def end_year(self) -> int:
    '''Note: Gregorian/Solar year / 公历年'''
    return self._end_year

  def __read_bytes_for_jieqi(self, year: int, jieqi: Jieqi) -> bytes:
    assert year in self.supported_year_range()
    offset: int = self._jieqi_offset_mapping[jieqi]
    return self._bytes[(year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len + offset : (year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len + offset + DecodedJieqiDates.date_bytes_len]

  def __getitem__(self, year: int) -> JieqiDates:
    '''Note: `year` means Gregorian/Solar year / 公历年'''
    assert year in self.supported_year_range()

    # Extract the bytes for the input `year`.
    year_bytes: bytes = self._bytes[(year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len : (year - self.start_year + 1) * 24 * DecodedJieqiDates.date_bytes_len]
    assert len(year_bytes) == DecodedJieqiDates.date_bytes_len * 24

    # Decode the bytes to `JieqiDates`.
    return { jq : bytes_to_date(self.__read_bytes_for_jieqi(year, jq)) for jq in self._actual_jieqi_order }

  def get(self, year: int, jieqi: Jieqi) -> date:
    '''
    This method is encouraged to be used over `__getitem__`, since it leverages the cache.

    Note: `year` means Gregorian/Solar year / 公历年
    '''
    assert year in self.supported_year_range()
    if year not in self._cached_datetimes:
      self._cached_datetimes[year] = self.__getitem__(year)
    return self._cached_datetimes[year][jieqi]
  
  def supported_year_range(self) -> range:
    '''Note: Gregorian/Solar year / 公历年'''
    return range(self.start_year, self.end_year + 1)


class LunarYearInfo(TypedDict):
  '''
  The information of a lunar year.
  '''
  first_solar_day: date        # The date of the first day of the lunar year (in solar calendar/gregorian calendar).
  leap: bool                   # Whether the year is leap or not.
  leap_month: Optional[int]    # If `leap` is False, this field is None. Otherwise, it is the month of the leap.
  days_counts: list[int]       # The number of days in each month. It contains 12 elements for normal years, and 13 elements for leap years.
  ganzhi: Ganzhi               # The Tiangan-Dizhi pair of the year.

class DecodedLunarYears:
  '''
  This class is used to query the information of lunar years.
  '''

  sexagenary_cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()

  def __init__(self) -> None:
    if not encoded_data_ready():
      do_encode()

    self._start_year = START_YEAR
    self._end_year = END_YEAR - 1 # hkodata.END_YEAR not included, since the data for it is incomplete.

    lunardate_encoded_path: Path = get_lunardate_encoded_data_path()
    assert lunardate_encoded_path.exists() and lunardate_encoded_path.is_file()
    assert lunardate_encoded_path.stat().st_size % 8 == 0, f'Encoded lunardate data should be a multiple of 8 bytes, but it is {lunardate_encoded_path.stat().st_size} bytes.'

    with lunardate_encoded_path.open('rb') as f:
      encoded_bytes: bytes = f.read()
    
    assert len(encoded_bytes) == 8 * (self.end_year - self.start_year + 1) # hkodata.END_YEAR not included, since the data for it is incomplete.
    self._bytes = encoded_bytes

  @property
  def start_year(self) -> int:
    '''Note: Lunar year / 阴历年'''
    return self._start_year
  
  @property
  def end_year(self) -> int:
    '''Note: Lunar year / 阴历年'''
    return self._end_year

  def __read_bytes_for_lunar_year(self, lunar_year: int) -> bytes:
    assert lunar_year in self.supported_year_range()
    return self._bytes[(lunar_year - self.start_year) * 8 : (lunar_year - self.start_year + 1) * 8]
  
  def __getitem__(self, lunar_year: int) -> LunarYearInfo:
    return self.get(lunar_year)

  def get(self, lunar_year: int) -> LunarYearInfo:
    assert lunar_year in self.supported_year_range()
    data_bytes: bytes = self.__read_bytes_for_lunar_year(lunar_year)
    assert len(data_bytes) == 8

    # Parse the bytes.
    first_solar_day: date = bytes_to_date(data_bytes[:4])
    ganzhi_index: int = bytes_to_int(data_bytes[4:5])
    ganzhi: Ganzhi = DecodedLunarYears.sexagenary_cycle[ganzhi_index]
    leap_month: int = bytes_to_int(data_bytes[5:6])
    month_info_int: int = bytes_to_int(data_bytes[6:])

    expected_months_count: int = 12 if leap_month == 0 else 13
    days_count_of_each_month: list[int] = []
    for idx in range(expected_months_count):
      if month_info_int & (1 << idx):
        days_count_of_each_month.append(30)
      else:
        days_count_of_each_month.append(29)

    return {
      'first_solar_day': first_solar_day,
      'leap': leap_month != 0,
      'leap_month': leap_month if leap_month != 0 else None,
      'days_counts': days_count_of_each_month,
      'ganzhi': ganzhi
    }

  def supported_year_range(self) -> range:
    '''Note: Lunar year / 阴历年'''
    return range(self.start_year, self.end_year + 1)
