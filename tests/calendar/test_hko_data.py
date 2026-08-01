# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_hkodata.py

import random
import shutil
import hashlib
import tempfile

import pytest

from pathlib import Path
from datetime import date, timedelta

from src.calendar import hko_data
from src.calendar.hko_data import encoder
from src.defines import Jieqi, Ganzhi


pytestmark = pytest.mark.hkodata


def test_traditional_chinese_jieqi() -> None:
  assert len(hko_data.jieqi_list_in_traditional_chinese) == 24


def test_traditional_chinese_month() -> None:
  assert len(hko_data.twelve_months_in_traditional_chinese) == 12


def test_int_bytes_conversion() -> None:
  assert hko_data.int_to_bytes(0x12345678, 4) == b'\x12\x34\x56\x78'
  assert hko_data.bytes_to_int(b'\x12\x34\x56\x78') == 0x12345678

  for _ in range(512):
    i: int = random.randint(0, 0xffffffff)
    i_bytes: bytes = hko_data.int_to_bytes(i, 4)
    assert i == hko_data.bytes_to_int(i_bytes)


def test_date_bytes_conversion() -> None:
  assert hko_data.date_to_bytes(date(2000, 1, 1)) == hko_data.date_to_bytes(date(2000, 1, 1))
  assert hko_data.date_to_bytes(date(2000, 1, 1)) != hko_data.date_to_bytes(date(2000, 1, 2))
  assert hko_data.bytes_to_date(b'\x00\x01\x01\x01') == date(1, 1, 1)
  assert hko_data.bytes_to_date(hko_data.date_to_bytes(date(2024, 2, 25))) == date(2024, 2, 25)

  dt: date = date(
    year=random.randint(1600, 2500),
    month=random.randint(1, 12),
    day=random.randint(1, 28), # Not using 29, 30, or 31 here, to avoid invalid day (e.g. 2024-2-31)
  )
  for _ in range(512):
    dt = dt + timedelta(days=random.randint(1, 3))
    dt_bytes: bytes = hko_data.date_to_bytes(dt)
    assert dt == hko_data.bytes_to_date(dt_bytes)
    assert len(dt_bytes) == 4, f'expect the length of dt_bytes to be 4, but got {len(dt_bytes)}'
    assert hko_data.bytes_to_int(dt_bytes[0:2]) == dt.year
    assert hko_data.bytes_to_int(dt_bytes[2:3]) == dt.month
    assert hko_data.bytes_to_int(dt_bytes[3:4]) == dt.day

  with pytest.raises(ValueError):
    hko_data.date_to_bytes(date(2024, 64, 1))
  with pytest.raises(ValueError):
    hko_data.date_to_bytes(date(2024, 12, 32))
  with pytest.raises(ValueError):
    hko_data.bytes_to_date(b'\x00\x01\x00\x00')
  with pytest.raises(AssertionError):
    hko_data.bytes_to_date(b'\x00\x00\x00\x00\x00\x01\x00\x00')
  with pytest.raises(AssertionError):
    hko_data.bytes_to_date(b'\x00\x00')
  with pytest.raises(AssertionError):
    hko_data.bytes_to_date(b'\x00\x00' * 10)


def test_decode_jieqi() -> None:
  decoded_jieqi: hko_data.DecodedJieqiDates = hko_data.DecodedJieqiDates()

  # In our expectation, the data between gregorian year 1901 and 2100 (edges included) is valid.
  for year in range(1901, 2100 + 1):
    assert year in decoded_jieqi.supported_year_range()

  for year in decoded_jieqi.supported_year_range():
    assert len(decoded_jieqi[year]) == 24

  assert min(decoded_jieqi.supported_year_range()) == hko_data.START_YEAR
  assert max(decoded_jieqi.supported_year_range()) == hko_data.END_YEAR

  for year in decoded_jieqi.supported_year_range():
    jieqi_dates_dict: hko_data.JieqiDates = decoded_jieqi[year]
    assert len(jieqi_dates_dict) == 24
    assert set(jieqi_dates_dict.keys()) == set(Jieqi)

  for year in decoded_jieqi.supported_year_range():
    for jieqi in Jieqi:
      assert decoded_jieqi.get(year, jieqi) == decoded_jieqi[year][jieqi]

  assert decoded_jieqi[1964][Jieqi.寒露] == date(1964, 10, 8)
  assert decoded_jieqi[1997][Jieqi.小寒] == date(1997, 1, 5)
  assert decoded_jieqi[2024][Jieqi.立春] == date(2024, 2, 4)

  assert decoded_jieqi.get(1964, Jieqi.寒露) == date(1964, 10, 8)
  assert decoded_jieqi.get(1997, Jieqi.小寒) == date(1997, 1, 5)
  assert decoded_jieqi.get(2024, Jieqi.立春) == date(2024, 2, 4)

  another_decoded_jieqi: hko_data.DecodedJieqiDates = hko_data.DecodedJieqiDates()
  assert list(decoded_jieqi.supported_year_range()) == list(another_decoded_jieqi.supported_year_range())

  for year in decoded_jieqi.supported_year_range():
    for jieqi in Jieqi:
      assert decoded_jieqi.get(year, jieqi) == another_decoded_jieqi.get(year, jieqi)


def test_decode_jieqi_getitem_negative() -> None:
  decoded_jieqi: hko_data.DecodedJieqiDates = hko_data.DecodedJieqiDates()
  with pytest.raises(AssertionError):
    decoded_jieqi[1000]
  with pytest.raises(AssertionError):
    decoded_jieqi[min(decoded_jieqi.supported_year_range()) - 1]
  with pytest.raises(AssertionError):
    decoded_jieqi[max(decoded_jieqi.supported_year_range()) + 1]
  with pytest.raises(AssertionError):
    decoded_jieqi['2024'] # type: ignore
  with pytest.raises(AssertionError):
    decoded_jieqi[Jieqi.芒种] # type: ignore
  with pytest.raises(AssertionError):
    decoded_jieqi[:] # type: ignore
  with pytest.raises(AssertionError):
    decoded_jieqi[date(2024, 1, 1)] # type: ignore

  data1 = decoded_jieqi[2024]
  data2 = decoded_jieqi[2024]
  assert data1 == data2
  assert data1 is not data2

  data2[Jieqi.惊蛰] = date(1999, 1, 1)
  data3 = decoded_jieqi[2024]
  assert data1 == data3
  assert data1 != data2
  assert data2 != data3


def test_decode_jieqi_get_negative() -> None:
  decoded_jieqi: hko_data.DecodedJieqiDates = hko_data.DecodedJieqiDates()
  with pytest.raises(TypeError):
    decoded_jieqi.get(2024)
  with pytest.raises(TypeError):
    decoded_jieqi.get(Jieqi.春分)
  with pytest.raises(AssertionError):
    decoded_jieqi.get('1000', Jieqi.寒露)
  with pytest.raises(AssertionError):
    decoded_jieqi.get(1000, Jieqi.寒露)
  with pytest.raises(AssertionError):
    decoded_jieqi.get(min(decoded_jieqi.supported_year_range()) - 1, Jieqi.寒露)
  with pytest.raises(AssertionError):
    decoded_jieqi.get(max(decoded_jieqi.supported_year_range()) + 1, Jieqi.寒露)

  assert decoded_jieqi.get(2024, Jieqi.立春) == decoded_jieqi.get(2024, Jieqi.立春)
  assert decoded_jieqi.get(2024, Jieqi.立春) is decoded_jieqi.get(2024, Jieqi.立春), 'should be the same object since it is cached'

  lichun_2024_date = decoded_jieqi.get(2024, Jieqi.立春)
  lichun_2024_date_ = decoded_jieqi.get(2024, Jieqi.立春)
  lichun_2024_date_ = date(9999, 9, 9)
  assert lichun_2024_date != lichun_2024_date_
  assert lichun_2024_date == decoded_jieqi.get(2024, Jieqi.立春)

  jieqi_dates_in_2024 = decoded_jieqi[2024]
  assert jieqi_dates_in_2024[Jieqi.立春] == lichun_2024_date

  jieqi_dates_in_2024[Jieqi.立春] = date(1996, 2, 4)
  assert jieqi_dates_in_2024[Jieqi.立春] != lichun_2024_date
  assert decoded_jieqi.get(2024, Jieqi.立春) == lichun_2024_date


def test_decode_lunar_year() -> None:
  decoded_lunardate: hko_data.DecodedLunarYears = hko_data.DecodedLunarYears()

  # In our expectation, the lunar years in [1901, 2099] (edges included) are supported.
  for year in range(1901, 2099 + 1):
    assert year in decoded_lunardate.supported_year_range()

  for year in decoded_lunardate.supported_year_range():
    info1 = decoded_lunardate[year]
    info2 = decoded_lunardate.get(year)
    assert info1 is not info2
    assert set(info1.keys()) == set(info2.keys())

    assert info1['first_solar_day'] == info2['first_solar_day']
    assert info1['leap'] == info2['leap']
    assert info1['leap_month'] == info2['leap_month']
    assert info1['days_counts'] == info2['days_counts']
    assert info1['ganzhi'] == info2['ganzhi']

    if info1['leap']:
      assert info1['leap_month'] != 0
      assert len(info1['days_counts']) == 13
    else:
      assert info1['leap_month'] is None
      assert len(info1['days_counts']) == 12

  expected_days_counts_2000: list[int] = [30, 30, 29, 29, 30, 29, 29, 30, 29, 30, 30, 29]
  assert decoded_lunardate[2000]['first_solar_day'] == date(2000, 2, 5)
  assert not decoded_lunardate[2000]['leap']
  assert decoded_lunardate[2000]['leap_month'] is None
  assert decoded_lunardate[2000]['days_counts'] == expected_days_counts_2000
  assert decoded_lunardate[2000]['ganzhi'] == Ganzhi.from_str('庚辰')

  expected_days_counts_2001: list[int] = [30, 30, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30]
  assert decoded_lunardate[2001]['first_solar_day'] == date(2001, 1, 24)
  assert decoded_lunardate[2001]['leap']
  assert decoded_lunardate[2001]['leap_month'] == 4
  assert decoded_lunardate[2001]['days_counts'] == expected_days_counts_2001
  assert decoded_lunardate[2001]['ganzhi'] == Ganzhi.from_str('辛巳')

  expected_days_counts_2024: list[int] = [29, 30, 29, 29, 30, 29, 30, 30, 29, 30, 30, 29]
  assert decoded_lunardate[2024]['first_solar_day'] == date(2024, 2, 10)
  assert not decoded_lunardate[2024]['leap']
  assert decoded_lunardate[2024]['leap_month'] is None
  assert decoded_lunardate[2024]['days_counts'] == expected_days_counts_2024
  assert decoded_lunardate[2024]['ganzhi'] == Ganzhi.from_str('甲辰')

  # 1924 is a year of "甲子" ganzhi.
  assert decoded_lunardate[1924]['ganzhi'] == Ganzhi.from_str('甲子')
  sexagenary_cycle = Ganzhi.list_sexagenary_cycle()
  for year in decoded_lunardate.supported_year_range():
    diff: int = year - 1924
    expected_ganzhi: Ganzhi = sexagenary_cycle[diff % len(sexagenary_cycle)]
    assert decoded_lunardate[year]['ganzhi'] == expected_ganzhi


def test_decode_lunar_year_get_returns_a_copy() -> None:
  '''
  `get` leverages a cache, so it must hand back a rebuilt record: mutating what a caller
  received must not corrupt later answers (issue #92).
  '''
  decoded_lunardate: hko_data.DecodedLunarYears = hko_data.DecodedLunarYears()
  info: hko_data.LunarYearInfo = decoded_lunardate.get(2000)
  assert info is not decoded_lunardate.get(2000)
  assert info['days_counts'] is not decoded_lunardate.get(2000)['days_counts']

  original_days_counts: list[int] = list(info['days_counts'])
  info['days_counts'][0] = 999
  info['leap_month'] = 7
  assert decoded_lunardate.get(2000)['days_counts'] == original_days_counts
  assert decoded_lunardate.get(2000)['leap_month'] is None


def test_decode_lunar_year_negative() -> None:
  decoded_lunardate: hko_data.DecodedLunarYears = hko_data.DecodedLunarYears()
  with pytest.raises(AssertionError):
    decoded_lunardate.get(min(decoded_lunardate.supported_year_range()) - 1)
  with pytest.raises(AssertionError):
    decoded_lunardate[min(decoded_lunardate.supported_year_range()) - 1]
  with pytest.raises(AssertionError):
    decoded_lunardate.get(max(decoded_lunardate.supported_year_range()) + 1)
  with pytest.raises(AssertionError):
    decoded_lunardate[max(decoded_lunardate.supported_year_range()) + 1]
  with pytest.raises(AssertionError):
    decoded_lunardate.get('a') # type: ignore
  with pytest.raises(AssertionError):
    decoded_lunardate.get('1984') # type: ignore
  with pytest.raises(AssertionError):
    decoded_lunardate.get(date(year=1984, month=1, day=1)) # type: ignore

  temp = decoded_lunardate[2024]
  temp['days_counts'].append(29)
  temp['ganzhi'] = Ganzhi.from_str('甲子')

  new_2024_info = decoded_lunardate[2024]
  assert new_2024_info is not temp
  assert new_2024_info['days_counts'] != temp['days_counts']
  assert new_2024_info['ganzhi'] != temp['ganzhi']

  expected_days_counts_2024: list[int] = [29, 30, 29, 29, 30, 29, 30, 30, 29, 30, 30, 29]
  assert new_2024_info['first_solar_day'] == date(2024, 2, 10)
  assert not new_2024_info['leap']
  assert new_2024_info['leap_month'] is None
  assert new_2024_info['days_counts'] == expected_days_counts_2024
  assert new_2024_info['ganzhi'] == Ganzhi.from_str('甲辰')


def test_file_existence() -> None:
  '''The data files should exist and be readable.'''
  data_path: Path = hko_data.get_data_base_path()
  assert data_path.exists() and data_path.is_dir()

  txt_paths: dict[int, Path] = hko_data.common.get_raw_txt_file_paths()
  for path in txt_paths.values():
    assert path.exists() and path.is_file()
    with open(path, 'r', encoding='utf-8') as f:
      assert f.read() != ''

  assert hko_data.common.raw_data_ready()


def test_raw_data_ready() -> None:
  assert hko_data.common.raw_data_ready()

  # Do something bad in between.

  temp_dir: Path = Path(tempfile.mkdtemp())
  data_path: Path = hko_data.common.get_data_base_path()
  assert temp_dir.exists() and temp_dir.is_dir()
  assert data_path.exists() and data_path.is_dir()

  # Copy the data folder to the temporary folder.
  shutil.copytree(data_path, temp_dir / 'data')

  try:
    shutil.move(data_path, temp_dir / 'data2')
    assert not hko_data.common.raw_data_ready()

    # Create a file called "data" (not a folder).
    with open(data_path, 'w') as f:
      f.write('I am not a folder!!!')
    assert not hko_data.common.raw_data_ready()

    # Remove the fake "data" file.
    data_path.unlink()
    assert not data_path.exists()

    # Copy the original data folder back.
    shutil.copytree(temp_dir / 'data', data_path)
    assert hko_data.common.raw_data_ready()

    all_txt_paths: dict[int, Path] = hko_data.common.get_raw_txt_file_paths()
    random.choice(list(all_txt_paths.values())).unlink()
    assert not hko_data.common.raw_data_ready()

  finally:
    # Finally restore the original data folder.
    # Also ensure the data is ready again after the above malicious operations.
    shutil.copytree(temp_dir / 'data', data_path, dirs_exist_ok=True)
    assert hko_data.common.raw_data_ready()

    shutil.rmtree(temp_dir)


@pytest.mark.slow
def test_do_encode() -> None:
  assert hko_data.common.encoded_data_ready()

  # Do something bad in between.

  temp_dir: Path = Path(tempfile.mkdtemp())
  jieqi_path: Path = hko_data.common.get_jieqi_encoded_data_path()
  lunardate_path: Path = hko_data.common.get_lunardate_encoded_data_path()
  assert temp_dir.exists() and temp_dir.is_dir()
  assert jieqi_path.exists() and jieqi_path.is_file()
  assert lunardate_path.exists() and lunardate_path.is_file()

  # Copy the data folder to the temporary folder.
  data_path: Path = hko_data.common.get_data_base_path()
  shutil.copytree(data_path, temp_dir / 'data')

  try:
    # Copy the encoded binary files to the temporary folder.
    shutil.move(jieqi_path, temp_dir / 'jieqi.bin')
    assert not hko_data.common.encoded_data_ready()
    shutil.move(lunardate_path, temp_dir / 'lunardate.bin')
    assert not hko_data.common.encoded_data_ready()

    # Ensure the encoded binary files are gone.
    assert not jieqi_path.exists()
    assert not lunardate_path.exists()

    # The decoder only reads the committed data files; it never re-encodes them.
    with pytest.raises(RuntimeError):
      hko_data.DecodedJieqiDates()
    with pytest.raises(RuntimeError):
      hko_data.DecodedLunarYears()

    # Encode them again, with the offline encoder tool.
    encoder.do_encode()
    assert hko_data.DecodedJieqiDates() is not None
    assert hko_data.common.encoded_data_ready()

    lunardate_path.unlink()
    assert not hko_data.common.encoded_data_ready()

    # Encode them again, with the offline encoder tool.
    encoder.do_encode()
    assert hko_data.DecodedLunarYears() is not None
    assert hko_data.common.encoded_data_ready()

    # Ensure the new encoded binary files are the same as the old ones.
    prev_jieqi_md5: str = hashlib.md5((temp_dir / 'jieqi.bin').read_bytes()).hexdigest()
    prev_lunardate_md5: str = hashlib.md5((temp_dir / 'lunardate.bin').read_bytes()).hexdigest()

    new_jieqi_md5: str = hashlib.md5(jieqi_path.read_bytes()).hexdigest()
    new_lunardate_md5: str = hashlib.md5(lunardate_path.read_bytes()).hexdigest()

    assert prev_jieqi_md5 == new_jieqi_md5
    assert prev_lunardate_md5 == new_lunardate_md5

  finally:
    # Finally restore the original data folder.
    # Also ensure the data is ready again after the above malicious operations.
    shutil.copytree(temp_dir / 'data', data_path, dirs_exist_ok=True)
    assert hko_data.common.raw_data_ready()

    shutil.rmtree(temp_dir)
