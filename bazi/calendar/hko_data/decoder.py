# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# bazi/calendar/hko_data/decoder.py
#
# 解码 encoder.py 生成的数据；只读取 hko_data/data/ 中已提交的二进制文件。
# 不下载或重新编码，重建数据须运行离线工具 encoder.py。

import functools

from pathlib import Path
from datetime import date
from typing import TypedDict, Final

from ...defines import Jieqi, Ganzhi

from .common import (
  START_YEAR, END_YEAR, date_to_bytes, bytes_to_date, bytes_to_int,
  get_jieqi_encoded_data_path, get_lunardate_encoded_data_path, encoded_data_ready,
)


'''节气到公历日期的映射。'''
JieqiDates = dict[Jieqi, date]

class DecodedJieqiDates:
  '''
  查询各公历年的节气日期。
  ''' 

  date_bytes_len: int = len(date_to_bytes(date(2000, 1, 1)))

  def __init__(self) -> None:
    # 显式抛异常，保证公开入口在 python -O 下仍会立即失败。
    if not encoded_data_ready():
      raise RuntimeError('Encoded HKO data files are missing. Reinstall bazi; in a source checkout, run `python -m bazi.calendar.hko_data.encoder` with the optional generation tools.')

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

    # 公历年首节为小寒，而 Jieqi 枚举从立春开始；HKO 数据采用公历年序。
    self._actual_jieqi_order: Final[list[Jieqi]] = Jieqi.as_list(ganzhi_year=False)

    self._jieqi_offset_mapping: Final[dict[Jieqi, int]] = { k : v for k, v in zip(self._actual_jieqi_order, range(0, 24 * DecodedJieqiDates.date_bytes_len, DecodedJieqiDates.date_bytes_len)) }
    assert len(self._jieqi_offset_mapping) == 24

  @property
  def start_year(self) -> int:
    '''支持的首公历年。'''
    return self._start_year
  
  @property
  def end_year(self) -> int:
    '''支持的末公历年。'''
    return self._end_year

  def __read_bytes_for_jieqi(self, year: int, jieqi: Jieqi) -> bytes:
    assert year in self.supported_year_range()
    offset: int = self._jieqi_offset_mapping[jieqi]
    return self._bytes[(year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len + offset : (year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len + offset + DecodedJieqiDates.date_bytes_len]

  def __getitem__(self, year: int) -> JieqiDates:
    '''查询公历年 year 的全部节气日期。'''
    if not isinstance(year, int):
      raise TypeError(f'Expected int, got {type(year)}')
    if year not in self.supported_year_range():
      raise ValueError(f'Year {year} is out of the supported range {self.supported_year_range()}')

    # 提取输入年份的字节。
    year_bytes: bytes = self._bytes[(year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len : (year - self.start_year + 1) * 24 * DecodedJieqiDates.date_bytes_len]
    assert len(year_bytes) == DecodedJieqiDates.date_bytes_len * 24

    # 解码为 JieqiDates。
    return { jq : bytes_to_date(self.__read_bytes_for_jieqi(year, jq)) for jq in self._actual_jieqi_order }

  @functools.cache
  def __cached_date(self, year: int, jieqi: Jieqi) -> date:
    return self[year][jieqi]

  def get(self, year: int, jieqi: Jieqi) -> date:
    '''
    查询公历年 year 的指定节气日期；复用缓存，优先于直接调用 __getitem__。
    '''
    if not isinstance(year, int):
      raise TypeError(f'Expected int, got {type(year)}')
    if year not in self.supported_year_range():
      raise ValueError(f'Year {year} is out of the supported range {self.supported_year_range()}')
    if not isinstance(jieqi, Jieqi):
      raise TypeError(f'Expected Jieqi, got {type(jieqi)}')
    return self.__cached_date(year, jieqi)
  
  def supported_year_range(self) -> range:
    '''支持的公历年份范围。'''
    return range(self.start_year, self.end_year + 1)


class LunarYearInfo(TypedDict):
  '''
  一年的农历信息。
  '''
  first_solar_day: date        # 农历年首日的公历日期。
  leap: bool                   # 是否有闰月。
  leap_month: int | None       # 无闰月为 None，否则为闰月月份。
  days_counts: list[int]       # 各月日数，平年十二项，闰年十三项。
  ganzhi: Ganzhi               # 此年的干支。

class DecodedLunarYears:
  '''
  查询各农历年的信息。
  '''

  sexagenary_cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()

  def __init__(self) -> None:
    # 显式抛异常，保证公开入口在 python -O 下仍会立即失败。
    if not encoded_data_ready():
      raise RuntimeError('Encoded HKO data files are missing. Reinstall bazi; in a source checkout, run `python -m bazi.calendar.hko_data.encoder` with the optional generation tools.')

    self._start_year: Final[int] = START_YEAR
    self._end_year: Final[int] = END_YEAR - 1 # END_YEAR 的数据不完整，故不包含。

    lunardate_encoded_path: Path = get_lunardate_encoded_data_path()
    assert lunardate_encoded_path.exists() and lunardate_encoded_path.is_file()
    assert lunardate_encoded_path.stat().st_size % 8 == 0, f'Encoded lunardate data should be a multiple of 8 bytes, but it is {lunardate_encoded_path.stat().st_size} bytes.'

    with lunardate_encoded_path.open('rb') as f:
      encoded_bytes: bytes = f.read()
    
    assert len(encoded_bytes) == 8 * (self.end_year - self.start_year + 1) # 不包含数据不完整的 END_YEAR。
    self._bytes: Final[bytes] = encoded_bytes

  @property
  def start_year(self) -> int:
    '''支持的首农历年。'''
    return self._start_year
  
  @property
  def end_year(self) -> int:
    '''支持的末农历年。'''
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

    # 解析农历年字节。
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
    查询农历年信息；复用缓存，优先于直接调用 __getitem__。
    每次返回新记录与独立 days_counts 列表，外部修改不影响缓存；其余值不可变，可共享。
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
    '''支持的农历年份范围。'''
    return range(self.start_year, self.end_year + 1)
