#!/usr/bin/env python3
#
# bazi/hko/encoder.py
# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
#
# Download the raw data from Hong Kong Observatory (hko) and encode the downloaded hko data.

import requests
import re
from pathlib import Path
from datetime import datetime

if __name__ == '__main__':
  from common import (
    START_YEAR, END_YEAR,
    get_data_base_path, get_raw_txt_file_paths, raw_data_ready,
    get_jieqi_encoded_data_path, get_lunardate_encoded_data_path, encoded_data_ready,
    jieqi_list_in_traditional_chinese, twelve_months_in_traditional_chinese,
    date_to_bytes, int_to_bytes,
  )

  import sys
  sys.path.append(Path(__file__).parent.parent.parent.as_posix())
  from Defines import Ganzhi
else:
  from ...Defines import Ganzhi
  from .common import (
    START_YEAR, END_YEAR,
    get_data_base_path, get_raw_txt_file_paths, raw_data_ready,
    get_jieqi_encoded_data_path, get_lunardate_encoded_data_path, encoded_data_ready,
    jieqi_list_in_traditional_chinese, twelve_months_in_traditional_chinese,
    date_to_bytes, int_to_bytes,
  )


__sexagenary_cycle__: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()

def download_one_year_data(txt_path: Path, year: int) -> bool:
  url = f'https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T{year}c.txt'
  response = requests.get(url)
  if response.status_code == 200:
    response.encoding = 'big5'
    with txt_path.open('w') as f:
      f.write(response.text) # The file is encoded in utf-8, not big5.
    return True
  return False # Failed to download.

def do_download() -> None:
  if raw_data_ready():
    print('> Data already exists, and all data is complete. Do nothing.')
    return

  data_dir = get_data_base_path()
  if data_dir.exists():
    print(f'> {data_dir} exists, but the data is not complete. Redownloading...')

  print(f'> Creating {data_dir}...')
  data_dir.mkdir(parents=True, exist_ok=True)

  to_retry: dict[int, Path] = {}
  for year, txt_path in get_raw_txt_file_paths().items():
    print(f'> Collecting {year}...')
    success: bool = download_one_year_data(txt_path, year)
    if not success:
      print(f'> Failed to download {year}. Retry later.')
      to_retry[year] = txt_path

  if len(to_retry) > 0:
    print(f'> Data for {list(to_retry.keys())} failed to be downloaded. Retrying now...')
    for year in to_retry:
      success: bool = download_one_year_data(to_retry[year], year)
      if not success:
        print(f'> WARNING: Failed to download {year} in the retry attempt.')

  assert raw_data_ready(), 'Some data is missing.'

def extract_from_raw_txts() -> dict[int, list[str]]:
  '''
  Open all raw txt files and extract the lines that contain the data that we care about.
  '''
  assert raw_data_ready()

  def is_valid_line(line: str) -> bool:
    if '年' not in line:
      return False
    if '月' not in line:
      return False
    if '日' not in line:
      return False
    if '夏令時間' in line:
      return False
    return True
  
  txt_paths: dict[int, Path] = get_raw_txt_file_paths()
  ret: dict[int, list[str]] = {}
  for year, txt_path in txt_paths.items():
    assert txt_path.exists()
    assert txt_path.is_file()

    with txt_path.open('r') as f:
      ret[year] = [line for line in f if is_valid_line(line)]
      assert len(ret[year]) in [365, 366], f'Unexpected number of days in {txt_path}.'
    
  return ret

def encode_jieqi() -> None:
  print('> Encoding jieqi data...')

  extractions: dict[int, list[str]] = extract_from_raw_txts()
  sorted_years: list[int] = list(extractions.keys())
  sorted_years.sort()

  dates_to_write: list[datetime] = []
  for year in sorted_years:
    valid_lines: list[str] = extractions[year]
    jieqi_lines: list[str] = [line for line in valid_lines if len(line.split()) == 4]
    assert len(jieqi_lines) == 24
    assert jieqi_lines[0].split()[-1] == '小寒' # Starts with 小寒

    for line in jieqi_lines:
      splitted: list[str] = line.split()
      assert splitted[-1] in jieqi_list_in_traditional_chinese
      date: datetime = datetime.strptime(splitted[0], '%Y年%m月%d日')
      dates_to_write.append(date)

  with get_jieqi_encoded_data_path().open('wb') as f:
    for date in dates_to_write:
      f.write(date_to_bytes(date))

def parse_lines_in_lunar_years() -> dict[int, list[str]]:  
  extractions: dict[int, list[str]] = extract_from_raw_txts()
  sorted_years: list[int] = list(extractions.keys())
  sorted_years.sort()

  all_lines: list[str] = []
  for year in sorted_years:
    all_lines.extend(extractions[year])

  zhengyue_line_indices: list[int] = [idx for idx, line in enumerate(all_lines) if '正月' in line]
  assert len(zhengyue_line_indices) == END_YEAR - START_YEAR + 1

  ret: dict[int, list[str]] = {}
  for lunar_year in range(START_YEAR, END_YEAR): # The data for the last lunar year is incomplete, so skip the `END_YEAR`.
    line_start_idx: int = zhengyue_line_indices[lunar_year - START_YEAR]
    line_end_idx: int = zhengyue_line_indices[lunar_year - START_YEAR + 1]
    ret[lunar_year] = all_lines[line_start_idx:line_end_idx]

  return ret

def parse_ganzhis_in_lunar_years() -> dict[int, Ganzhi]:  
  raw_txt_paths: dict[int, Path] = get_raw_txt_file_paths()
  ret: dict[int, Ganzhi] = {}
  for lunar_year in range(START_YEAR, END_YEAR): # The data for the last lunar year is incomplete, so skip the `END_YEAR`.
    with raw_txt_paths[lunar_year].open('r') as f:
      first_line: str = f.readline().strip()
      ganzhi_str: str = first_line.split('(')[-1].split('-')[0].strip()
      ret[lunar_year] = Ganzhi.from_str(ganzhi_str)

  return ret

def encode_one_lunar_year_lines(lunar_year: int, lines: list[str], ganzhi: Ganzhi) -> bytes:
  # The data for each lunar year will be encoded into 8 bytes.

  # First 4 bytes are the solar-calendar date of the frist day in this lunar year.
  first_day_date: datetime = datetime.strptime(lines[0].split()[0], '%Y年%m月%d日')
  first_day_date_bytes: bytes = date_to_bytes(first_day_date)
  assert len(first_day_date_bytes) == 4

  # Then use 1 byte to save the index to the ganzhi of this lunar year.
  ganzhi_index_byte: bytes = int_to_bytes(__sexagenary_cycle__.index(ganzhi), 1)
  assert len(ganzhi_index_byte) == 1

  # Use 1 byte to save the whether the leap month exists in this lunar year.
  # If exists, save which month is the leap month (e.g. save 7 if the 7th month is leap).
  # If not, save 0.
  concatenated_lines: str = ''.join(lines)
  has_leap_month: bool = '閏' in concatenated_lines
  leap_month: int = 0
  if has_leap_month:
    re_results = re.findall(r'閏[\u4e00-\u9fff]+月', concatenated_lines)
    assert len(re_results) == 1
    leap_month = 1 + twelve_months_in_traditional_chinese.index(re_results[0][1:])

  leap_month_byte: bytes = int_to_bytes(leap_month, 1)
  assert len(leap_month_byte) == 1

  # Last, use 2 bytes to indicate how many days are there in every month.
  # The least significant 13 bits are indicating whether the 13 months are long or short. If no long month, just use least significant 12 bits.
  first_days_indices: list[int] = [idx for idx, line in enumerate(lines) if '月' in line.split()[1]]
  days_count_of_each_month: list[int] = [right - left for left, right in zip(first_days_indices, first_days_indices[1:] + [len(lines)])]
  if has_leap_month:
    assert len(first_days_indices) == 13
    assert len(days_count_of_each_month) == 13
  else:
    assert len(first_days_indices) == 12
    assert len(days_count_of_each_month) == 12
  
  month_info_int: int = 0
  for idx, days_count in enumerate(days_count_of_each_month):
    assert days_count in [29, 30]
    if days_count == 30:
      month_info_int |= 1 << idx
  month_info_bytes: bytes = int_to_bytes(month_info_int, 2)

  final_bytes: bytes = first_day_date_bytes + ganzhi_index_byte + leap_month_byte + month_info_bytes
  assert len(final_bytes) == 8
  return final_bytes

def encode_lunardate() -> None:
  print('> Encoding lunar date data...')

  lunar_year_lines: dict[int, list[str]] = parse_lines_in_lunar_years()
  lunar_year_ganzhis: dict[int, Ganzhi] = parse_ganzhis_in_lunar_years()
  with get_lunardate_encoded_data_path().open('wb') as f:
    for lunar_year, lines in lunar_year_lines.items():
      bytes_to_write: bytes = encode_one_lunar_year_lines(lunar_year, lines, lunar_year_ganzhis[lunar_year])
      f.write(bytes_to_write)

def do_encode() -> None:
  if not raw_data_ready():
    do_download()

  if encoded_data_ready():
    print('> Encoded data already exists. Do nothing.')
    return

  encode_jieqi()
  encode_lunardate()

if __name__ == '__main__':
  do_encode()
