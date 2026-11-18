# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# tests/calendar/hko_data/decoder.py
#
# 解码 encoder.py 生成的数据；只读取 hko_data/data/ 中已提交的二进制文件。
# 不下载或重新编码，重建数据须运行离线工具 encoder.py。

'''读取 HKO 测试对照用的节气与阴历二进制表。

DecodedJieqiDates 与 DecodedLunarYears 只解码数据，不负责日期换算、下载或生成文件。'''

import functools

from pathlib import Path
from datetime import date
from typing import Final

from bazi.defines import Jieqi, Ganzhi
from bazi.calendar.dates import LunarYearInfo as LunarYearInfo # noqa: PLC0414 # 解码记录也供对拍测试导入。

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
    if not encoded_data_ready():
      raise RuntimeError('Encoded HKO test data files are missing. Run `PYTHONPATH=tests/calendar:. python -m hko_data.encoder` in the source checkout.')

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
    assert isinstance(year, int) and year in self.supported_year_range()

    # 提取输入年份的字节。
    year_bytes: bytes = self._bytes[(year - self.start_year) * 24 * DecodedJieqiDates.date_bytes_len : (year - self.start_year + 1) * 24 * DecodedJieqiDates.date_bytes_len]
    assert len(year_bytes) == DecodedJieqiDates.date_bytes_len * 24

    # 解码为 JieqiDates。
    return { jq : bytes_to_date(self.__read_bytes_for_jieqi(year, jq)) for jq in self._actual_jieqi_order }

  @functools.cache
  def get(self, year: int, jieqi: Jieqi) -> date:
    '''
    查询公历年 year 的指定节气日期；复用缓存，优先于直接调用 __getitem__。
    '''
    assert isinstance(jieqi, Jieqi)
    return self[year][jieqi]
  
  def supported_year_range(self) -> range:
    '''支持的公历年份范围。'''
    return range(self.start_year, self.end_year + 1)


class DecodedLunarYears:
  '''
  查询各农历年的信息。
  '''

  sexagenary_cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()

  def __init__(self) -> None:
    if not encoded_data_ready():
      raise RuntimeError('Encoded HKO test data files are missing. Run `PYTHONPATH=tests/calendar:. python -m hko_data.encoder` in the source checkout.')

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
    assert isinstance(lunar_year, int) and lunar_year in self.supported_year_range()

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

    return LunarYearInfo(
      first_solar_day=first_solar_day,
      leap=leap_month != 0,
      leap_month=leap_month if leap_month != 0 else None,
      days_counts=tuple(days_count_of_each_month),
      ganzhi=ganzhi,
    )

  @functools.cache
  def get(self, lunar_year: int) -> LunarYearInfo:
    '''
    查询农历年信息；复用缓存，优先于直接调用 __getitem__。
    记录与 days_counts 均不可变，可直接共享缓存结果。
    '''
    return self[lunar_year]

  def supported_year_range(self) -> range:
    '''支持的农历年份范围。'''
    return range(self.start_year, self.end_year + 1)
