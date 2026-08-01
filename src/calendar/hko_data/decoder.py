# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# bazi/src/calendar/hko_data/decoder.py
#
# Decode the encoded data produced by encoder.py.
# The decoder only reads the committed binary data files under `hko_data/data/`;
# it never downloads or re-encodes anything (use encoder.py as an offline tool for that).

import functools

from pathlib import Path
from datetime import date
from typing import TypedDict, Final

from ...defines import Jieqi, Ganzhi

from .common import (
  START_YEAR, END_YEAR, date_to_bytes, bytes_to_date, bytes_to_int,
  get_jieqi_encoded_data_path, get_lunardate_encoded_data_path, encoded_data_ready,
)


'''Jieqi -> Solar-calendar Date'''
JieqiDates = dict[Jieqi, date]

class DecodedJieqiDates:
  '''
  This class is used to query the solar-calendar date (Gregorian Calendar) of each Jieqi in each solar-calendar year.
  ''' 

  date_bytes_len: int = len(date_to_bytes(date(2000, 1, 1)))

  def __init__(self) -> None:
    # Explicit raise (not assert): this is the public fail-fast contract for library
    # consumers, and it must survive `python -O`.
    if not encoded_data_ready():
      raise RuntimeError('Encoded HKO data files are missing. Run `python -m src.calendar.hko_data.encoder` from the repo root to regenerate them.')

    self._start_year: Final[int] = START_YEAR
    self._end_year: Final[int] = END_YEAR

    jieqi_encoded_path: Path = get_jieqi_encoded_data_path()
    assert jieqi_encoded_path.exists() and jieqi_encoded_path.is_file()
    assert jieqi_encoded_path.stat().st_size % DecodedJieqiDates.date_bytes_len == 0, f'Encoded jieqi data should be a multiple of {DecodedJieqiDates.date_bytes_len} bytes, but it is {jieqi_encoded_path.stat().st_size} bytes.'
    assert jieqi_encoded_path.stat().st_size % (DecodedJieqiDates.date_bytes_len * 24) == 0, f'There are 24 jieqis in each year, so encoded jieqi data should be a multiple of 24 * {DecodedJieqiDates.date_bytes_len} bytes, but it is {jieqi_encoded_path.stat().st_size} bytes.'

    with jieqi_encoded_path.open('rb') as f:
      encoded_bytes: bytes = f.read()
    
    assert len(encoded_bytes) == 24 * (self._end_year - self._start_year + 1) * DecodedJieqiDates.date_bytes_len
    self._bytes: Final[bytes] = encoded_bytes

    # In Georgian calendar, the first Jieqi is "小寒".
    # But in `Jieqi`'s order, the first Jieqi is "立春".
    self._actual_jieqi_order: Final[list[Jieqi]] = Jieqi.as_list(ganzhi_year=False) # This is the real order in HKO data.

    self._jieqi_offset_mapping: Final[dict[Jieqi, int]] = { k : v for k, v in zip(self._actual_jieqi_order, range(0, 24 * DecodedJieqiDates.date_bytes_len, DecodedJieqiDates.date_bytes_len)) }
    assert len(self._jieqi_offset_mapping) == 24

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
    if not isinstance(year, int):
      raise TypeError(f'Expected int, got {type(year)}')
    if year not in self.supported_year_range():
      raise ValueError(f'Year {year} is out of the supported range {self.supported_year_range()}')

    # Extract the bytes for the input `year`.
    year_bytes: bytes = self._bytes[(year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len : (year - self.start_year + 1) * 24 * DecodedJieqiDates.date_bytes_len]
    assert len(year_bytes) == DecodedJieqiDates.date_bytes_len * 24

    # Decode the bytes to `JieqiDates`.
    return { jq : bytes_to_date(self.__read_bytes_for_jieqi(year, jq)) for jq in self._actual_jieqi_order }

  @functools.cache
  def get(self, year: int, jieqi: Jieqi) -> date:
    '''
    This method is encouraged to be used over `__getitem__`, since it leverages the cache.

    Note: `year` means Gregorian/Solar year / 公历年
    '''
    if not isinstance(year, int):
      raise TypeError(f'Expected int, got {type(year)}')
    if year not in self.supported_year_range():
      raise ValueError(f'Year {year} is out of the supported range {self.supported_year_range()}')
    return self[year][jieqi]
  
  def supported_year_range(self) -> range:
    '''Note: Gregorian/Solar year / 公历年'''
    return range(self.start_year, self.end_year + 1)


class LunarYearInfo(TypedDict):
  '''
  The information of a lunar year.
  '''
  first_solar_day: date        # The date of the first day of the lunar year (in solar calendar/gregorian calendar).
  leap: bool                   # Whether the year is leap or not.
  leap_month: int | None       # If `leap` is False, this field is None. Otherwise, it is the month of the leap.
  days_counts: list[int]       # The number of days in each month. It contains 12 elements for normal years, and 13 elements for leap years.
  ganzhi: Ganzhi               # The Tiangan-Dizhi pair of the year.

class DecodedLunarYears:
  '''
  This class is used to query the information of lunar years.
  '''

  sexagenary_cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()

  def __init__(self) -> None:
    # Explicit raise (not assert): this is the public fail-fast contract for library
    # consumers, and it must survive `python -O`.
    if not encoded_data_ready():
      raise RuntimeError('Encoded HKO data files are missing. Run `python -m src.calendar.hko_data.encoder` from the repo root to regenerate them.')

    self._start_year: Final[int] = START_YEAR
    self._end_year: Final[int] = END_YEAR - 1 # END_YEAR not included, since the data for it is incomplete.

    lunardate_encoded_path: Path = get_lunardate_encoded_data_path()
    assert lunardate_encoded_path.exists() and lunardate_encoded_path.is_file()
    assert lunardate_encoded_path.stat().st_size % 8 == 0, f'Encoded lunardate data should be a multiple of 8 bytes, but it is {lunardate_encoded_path.stat().st_size} bytes.'

    with lunardate_encoded_path.open('rb') as f:
      encoded_bytes: bytes = f.read()
    
    assert len(encoded_bytes) == 8 * (self.end_year - self.start_year + 1) # END_YEAR not included, since the data for it is incomplete.
    self._bytes: Final[bytes] = encoded_bytes

  @property
  def start_year(self) -> int:
    '''Note: Lunar year / 阴历年'''
    return self._start_year
  
  @property
  def end_year(self) -> int:
    '''Note: Lunar year / 阴历年'''
    return self._end_year

  @functools.cache
  def __read_bytes_for_lunar_year(self, lunar_year: int) -> bytes:
    assert lunar_year in self.supported_year_range()
    return self._bytes[(lunar_year - self.start_year) * 8 : (lunar_year - self.start_year + 1) * 8]
  
  def __getitem__(self, lunar_year: int) -> LunarYearInfo:
    if not isinstance(lunar_year, int):
      raise TypeError(f'Expected int, got {type(lunar_year)}')
    if lunar_year not in self.supported_year_range():
      raise ValueError(f'Year {lunar_year} is out of the supported range {self.supported_year_range()}')

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

  @functools.cache
  def __cached_info(self, lunar_year: int) -> LunarYearInfo:
    return self.__getitem__(lunar_year)

  def get(self, lunar_year: int) -> LunarYearInfo:
    '''
    This method is encouraged to be used over `__getitem__`, since it leverages the cache.
    The returned record is rebuilt per call (with a fresh `days_counts` list), so mutating
    it cannot poison the cache. The other values are immutable and safe to share.
    '''
    if not isinstance(lunar_year, int):
      raise TypeError(f'Expected int, got {type(lunar_year)}')
    if lunar_year not in self.supported_year_range():
      raise ValueError(f'Year {lunar_year} is out of the supported range {self.supported_year_range()}')
    info: LunarYearInfo = self.__cached_info(lunar_year)
    return LunarYearInfo(
      first_solar_day=info['first_solar_day'],
      leap=info['leap'],
      leap_month=info['leap_month'],
      days_counts=list(info['days_counts']),
      ganzhi=info['ganzhi'],
    )

  def supported_year_range(self) -> range:
    '''Note: Lunar year / 阴历年'''
    return range(self.start_year, self.end_year + 1)
