#!/usr/bin/env python3
#
# bazi/hko/common.py
# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
#
# Define variables and functions used in other .py files in hkodata directory.

from pathlib import Path
from datetime import date

from ...Common import ImmutableMetaClass

class HkoYearLimits(metaclass=ImmutableMetaClass):
  START_YEAR: int = 1901
  END_YEAR: int = 2100

def get_data_base_path() -> Path:
  return Path(__file__).parent / 'data'

def get_raw_txt_file_paths() -> dict[int, Path]:
  data_dir = get_data_base_path()
  data_txt_file_paths: dict[int, Path] = {}
  for year in range(HkoYearLimits.START_YEAR, HkoYearLimits.END_YEAR + 1):
    data_txt_file_paths[year] = data_dir / f'{year}.txt'
  return data_txt_file_paths

def raw_data_ready() -> bool:
  data_dir = get_data_base_path()
  if not data_dir.exists():
    return False
  if not data_dir.is_dir():
    return False
  for txt_path in get_raw_txt_file_paths().values():
    if not txt_path.exists() or not txt_path.is_file():
      return False
  return True

def get_jieqi_encoded_data_path() -> Path:
  return get_data_base_path() / 'jieqi_encoded.bin'

def get_lunardate_encoded_data_path() -> Path:
  return get_data_base_path() / 'lunardate_encoded.bin'

def encoded_data_ready() -> bool:
  jieqi_path = get_jieqi_encoded_data_path()
  lunardate_path = get_lunardate_encoded_data_path()
  return jieqi_path.exists() and lunardate_path.exists() and \
         jieqi_path.is_file() and lunardate_path.is_file()

jieqi_list_in_traditional_chinese: list[str] = list('''
立春 雨水 驚蟄 春分 清明 穀雨
立夏 小滿 芒種 夏至 小暑 大暑
立秋 處暑 白露 秋分 寒露 霜降
立冬 小雪 大雪 冬至 小寒 大寒
'''.strip().split())

twelve_months_in_traditional_chinese: list[str] = list('''
一月 二月 三月 四月 五月 六月
七月 八月 九月 十月 十一月 十二月
'''.strip().split())

def int_to_bytes(n: int, length: int) -> bytes:
  return n.to_bytes(length, 'big')

def bytes_to_int(b: bytes) -> int:
  return int.from_bytes(b, 'big')

def date_to_bytes(dt: date) -> bytes:
  y: int = dt.year
  m: int = dt.month
  d: int = dt.day
  result: bytes = int_to_bytes(y, 2) + int_to_bytes(m, 1) + int_to_bytes(d, 1)
  assert len(result) == 4 # Aligned to 4 bytes.
  return result

def bytes_to_date(b: bytes) -> date:
  assert len(b) == 4
  y: int = bytes_to_int(b[0:2])
  m: int = bytes_to_int(b[2:3])
  d: int = bytes_to_int(b[3:4])
  return date(y, m, d)
