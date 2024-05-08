# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_HkoData.py

import random
import shutil
import hashlib
import unittest
import tempfile

from pathlib import Path
from datetime import date, timedelta

from src.Calendar import HkoData
from src.Defines import Jieqi, Ganzhi

class TestHkoData(unittest.TestCase):
  def test_traditional_chinese_jieqi(self) -> None:
    self.assertEqual(len(HkoData.jieqi_list_in_traditional_chinese), 24)

  def test_traditional_chinese_month(self) -> None:
    self.assertEqual(len(HkoData.twelve_months_in_traditional_chinese), 12)
  
  def test_int_bytes_conversion(self) -> None:
    self.assertEqual(HkoData.int_to_bytes(0x12345678, 4), b'\x12\x34\x56\x78')
    self.assertEqual(HkoData.bytes_to_int(b'\x12\x34\x56\x78'), 0x12345678)

    for _ in range(512):
      i: int = random.randint(0, 0xffffffff)
      i_bytes: bytes = HkoData.int_to_bytes(i, 4)
      self.assertEqual(i, HkoData.bytes_to_int(i_bytes))

  def test_date_bytes_conversion(self) -> None:
    self.assertEqual(HkoData.date_to_bytes(date(2000, 1, 1)), HkoData.date_to_bytes(date(2000, 1, 1)))
    self.assertNotEqual(HkoData.date_to_bytes(date(2000, 1, 1)), HkoData.date_to_bytes(date(2000, 1, 2)))
    self.assertEqual(HkoData.bytes_to_date(b'\x00\x01\x01\x01'), date(1, 1, 1))
    self.assertEqual(HkoData.bytes_to_date(HkoData.date_to_bytes(date(2024, 2, 25))), date(2024, 2, 25))

    dt: date = date(
      year=random.randint(1600, 2500),
      month=random.randint(1, 12),
      day=random.randint(1, 28), # Not using 29, 30, or 31 here, to avoid invalid day (e.g. 2024-2-31)
    )
    for _ in range(512):
      dt = dt + timedelta(days=random.randint(1, 3))
      dt_bytes: bytes = HkoData.date_to_bytes(dt)
      self.assertEqual(dt, HkoData.bytes_to_date(dt_bytes))
      self.assertEqual(len(dt_bytes), 4, msg=f'expect the length of dt_bytes to be 4, but got {len(dt_bytes)}')
      self.assertEqual(HkoData.bytes_to_int(dt_bytes[0:2]), dt.year)
      self.assertEqual(HkoData.bytes_to_int(dt_bytes[2:3]), dt.month)
      self.assertEqual(HkoData.bytes_to_int(dt_bytes[3:4]), dt.day)

    with self.assertRaises(ValueError):
      HkoData.date_to_bytes(date(2024, 64, 1))
    with self.assertRaises(ValueError):
      HkoData.date_to_bytes(date(2024, 12, 32))
    with self.assertRaises(ValueError):
      HkoData.bytes_to_date(b'\x00\x01\x00\x00')
    with self.assertRaises(AssertionError):
      HkoData.bytes_to_date(b'\x00\x00\x00\x00\x00\x01\x00\x00')
    with self.assertRaises(AssertionError):
      HkoData.bytes_to_date(b'\x00\x00')
    with self.assertRaises(AssertionError):
      HkoData.bytes_to_date(b'\x00\x00' * 10)

  def test_decode_jieqi(self) -> None:
    decoded_jieqi: HkoData.DecodedJieqiDates = HkoData.DecodedJieqiDates()

    # In our expectation, the data between gregorian year 1901 and 2100 (edges included) is valid.
    for year in range(1901, 2100 + 1):
      self.assertTrue(year in decoded_jieqi.supported_year_range())

    for year in decoded_jieqi.supported_year_range():
      self.assertEqual(len(decoded_jieqi[year]), 24)

    self.assertEqual(min(decoded_jieqi.supported_year_range()), HkoData.HkoYearLimits.START_YEAR)
    self.assertEqual(max(decoded_jieqi.supported_year_range()), HkoData.HkoYearLimits.END_YEAR)

    for year in decoded_jieqi.supported_year_range():
      jieqi_dates_dict: HkoData.JieqiDates = decoded_jieqi[year]
      self.assertEqual(len(jieqi_dates_dict), 24)
      self.assertEqual(set(jieqi_dates_dict.keys()), set(Jieqi))

    for year in decoded_jieqi.supported_year_range():
      for jieqi in Jieqi:
        self.assertEqual(decoded_jieqi.get(year, jieqi), decoded_jieqi[year][jieqi])
    
    self.assertEqual(decoded_jieqi[1964][Jieqi.寒露], date(1964, 10, 8))
    self.assertEqual(decoded_jieqi[1997][Jieqi.小寒], date(1997, 1, 5))
    self.assertEqual(decoded_jieqi[2024][Jieqi.立春], date(2024, 2, 4))

    self.assertEqual(decoded_jieqi.get(1964, Jieqi.寒露), date(1964, 10, 8))
    self.assertEqual(decoded_jieqi.get(1997, Jieqi.小寒), date(1997, 1, 5))
    self.assertEqual(decoded_jieqi.get(2024, Jieqi.立春), date(2024, 2, 4))

    another_decoded_jieqi: HkoData.DecodedJieqiDates = HkoData.DecodedJieqiDates()
    self.assertListEqual(list(decoded_jieqi.supported_year_range()), list(another_decoded_jieqi.supported_year_range()))

    for year in decoded_jieqi.supported_year_range():
      for jieqi in Jieqi:
        self.assertEqual(decoded_jieqi.get(year, jieqi), another_decoded_jieqi.get(year, jieqi))
    
  def test_decode_jieqi_getitem_negative(self) -> None:
    decoded_jieqi: HkoData.DecodedJieqiDates = HkoData.DecodedJieqiDates()
    with self.assertRaises(AssertionError):
      decoded_jieqi[1000]
    with self.assertRaises(AssertionError):
      decoded_jieqi[min(decoded_jieqi.supported_year_range()) - 1]
    with self.assertRaises(AssertionError):
      decoded_jieqi[max(decoded_jieqi.supported_year_range()) + 1]
    with self.assertRaises(AssertionError):
      decoded_jieqi['2024'] # type: ignore
    with self.assertRaises(AssertionError):
      decoded_jieqi[Jieqi.芒种] # type: ignore
    with self.assertRaises(AssertionError):
      decoded_jieqi[:] # type: ignore
    with self.assertRaises(AssertionError):
      decoded_jieqi[date(2024, 1, 1)] # type: ignore

    data1 = decoded_jieqi[2024]
    data2 = decoded_jieqi[2024]
    self.assertEqual(data1, data2)
    self.assertIsNot(data1, data2)

    data2[Jieqi.惊蛰] = date(1999, 1, 1)
    data3 = decoded_jieqi[2024]
    self.assertEqual(data1, data3)
    self.assertNotEqual(data1, data2)
    self.assertNotEqual(data2, data3)

  def test_decode_jieqi_get_negative(self) -> None:
    decoded_jieqi: HkoData.DecodedJieqiDates = HkoData.DecodedJieqiDates()
    with self.assertRaises(TypeError):
      decoded_jieqi.get(2024) # type: ignore
    with self.assertRaises(TypeError):
      decoded_jieqi.get(Jieqi.春分) # type: ignore
    with self.assertRaises(AssertionError):
      decoded_jieqi.get('1000', Jieqi.寒露) # type: ignore
    with self.assertRaises(AssertionError):
      decoded_jieqi.get(1000, Jieqi.寒露)
    with self.assertRaises(AssertionError):
      decoded_jieqi.get(min(decoded_jieqi.supported_year_range()) - 1, Jieqi.寒露)
    with self.assertRaises(AssertionError):
      decoded_jieqi.get(max(decoded_jieqi.supported_year_range()) + 1, Jieqi.寒露)

    self.assertEqual(decoded_jieqi.get(2024, Jieqi.立春), decoded_jieqi.get(2024, Jieqi.立春))
    self.assertIs(decoded_jieqi.get(2024, Jieqi.立春), decoded_jieqi.get(2024, Jieqi.立春), msg='should be the same object since it is cached')

    lichun_2024_date = decoded_jieqi.get(2024, Jieqi.立春)
    lichun_2024_date_ = decoded_jieqi.get(2024, Jieqi.立春)
    lichun_2024_date_ = date(9999, 9, 9)
    self.assertNotEqual(lichun_2024_date, lichun_2024_date_)
    self.assertEqual(lichun_2024_date, decoded_jieqi.get(2024, Jieqi.立春))

    jieqi_dates_in_2024 = decoded_jieqi[2024]
    self.assertEqual(jieqi_dates_in_2024[Jieqi.立春], lichun_2024_date)

    jieqi_dates_in_2024[Jieqi.立春] = date(1996, 2, 4)
    self.assertNotEqual(jieqi_dates_in_2024[Jieqi.立春], lichun_2024_date)
    self.assertEqual(decoded_jieqi.get(2024, Jieqi.立春), lichun_2024_date)

  def test_decode_lunar_year(self) -> None:
    decoded_lunardate: HkoData.DecodedLunarYears = HkoData.DecodedLunarYears()

    # In our expectation, the lunar years in [1901, 2099] (edges included) are supported.
    for year in range(1901, 2099 + 1):
      self.assertTrue(year in decoded_lunardate.supported_year_range())

    for year in decoded_lunardate.supported_year_range():
      info1 = decoded_lunardate[year]
      info2 = decoded_lunardate.get(year)
      self.assertIsNot(info1, info2)
      self.assertEqual(set(info1.keys()), set(info2.keys()))

      self.assertEqual(info1['first_solar_day'], info2['first_solar_day'])
      self.assertEqual(info1['leap'], info2['leap'])
      self.assertEqual(info1['leap_month'], info2['leap_month'])
      self.assertEqual(info1['days_counts'], info2['days_counts'])
      self.assertEqual(info1['ganzhi'], info2['ganzhi'])

      if info1['leap']:
        self.assertNotEqual(info1['leap_month'], 0)
        self.assertEqual(len(info1['days_counts']), 13)
      else:
        self.assertIsNone(info1['leap_month'])
        self.assertEqual(len(info1['days_counts']), 12)

    expected_days_counts_2000: list[int] = [30, 30, 29, 29, 30, 29, 29, 30, 29, 30, 30, 29]
    self.assertEqual(decoded_lunardate[2000]['first_solar_day'], date(2000, 2, 5))
    self.assertFalse(decoded_lunardate[2000]['leap'])
    self.assertIsNone(decoded_lunardate[2000]['leap_month'])
    self.assertListEqual(decoded_lunardate[2000]['days_counts'], expected_days_counts_2000)
    self.assertEqual(decoded_lunardate[2000]['ganzhi'], Ganzhi.from_str('庚辰'))

    expected_days_counts_2001: list[int] = [30, 30, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30]
    self.assertEqual(decoded_lunardate[2001]['first_solar_day'], date(2001, 1, 24))
    self.assertTrue(decoded_lunardate[2001]['leap'])
    self.assertEqual(decoded_lunardate[2001]['leap_month'], 4)
    self.assertListEqual(decoded_lunardate[2001]['days_counts'], expected_days_counts_2001)
    self.assertEqual(decoded_lunardate[2001]['ganzhi'], Ganzhi.from_str('辛巳'))

    expected_days_counts_2024: list[int] = [29, 30, 29, 29, 30, 29, 30, 30, 29, 30, 30, 29]
    self.assertEqual(decoded_lunardate[2024]['first_solar_day'], date(2024, 2, 10))
    self.assertFalse(decoded_lunardate[2024]['leap'])
    self.assertIsNone(decoded_lunardate[2024]['leap_month'])
    self.assertListEqual(decoded_lunardate[2024]['days_counts'], expected_days_counts_2024)
    self.assertEqual(decoded_lunardate[2024]['ganzhi'], Ganzhi.from_str('甲辰'))

    # 1924 is a year of "甲子" ganzhi.
    self.assertEqual(decoded_lunardate[1924]['ganzhi'], Ganzhi.from_str('甲子'))
    sexagenary_cycle = Ganzhi.list_sexagenary_cycle()
    for year in decoded_lunardate.supported_year_range():
      diff: int = year - 1924
      expected_ganzhi: Ganzhi = sexagenary_cycle[diff % len(sexagenary_cycle)]
      self.assertEqual(decoded_lunardate[year]['ganzhi'], expected_ganzhi)

  def test_decode_lunar_year_negative(self) -> None:
    decoded_lunardate: HkoData.DecodedLunarYears = HkoData.DecodedLunarYears()
    with self.assertRaises(AssertionError):
      decoded_lunardate.get(min(decoded_lunardate.supported_year_range()) - 1)
    with self.assertRaises(AssertionError):
      decoded_lunardate[min(decoded_lunardate.supported_year_range()) - 1]
    with self.assertRaises(AssertionError):
      decoded_lunardate.get(max(decoded_lunardate.supported_year_range()) + 1)
    with self.assertRaises(AssertionError):
      decoded_lunardate[max(decoded_lunardate.supported_year_range()) + 1]
    with self.assertRaises(AssertionError):
      decoded_lunardate.get('a') # type: ignore
    with self.assertRaises(AssertionError):
      decoded_lunardate.get('1984') # type: ignore
    with self.assertRaises(AssertionError):
      decoded_lunardate.get(date(year=1984, month=1, day=1)) # type: ignore
    
    temp = decoded_lunardate[2024]
    temp['days_counts'].append(29)
    temp['ganzhi'] = Ganzhi.from_str('甲子')

    new_2024_info = decoded_lunardate[2024]
    self.assertIsNot(new_2024_info, temp)
    self.assertNotEqual(new_2024_info['days_counts'], temp['days_counts'])
    self.assertNotEqual(new_2024_info['ganzhi'], temp['ganzhi'])

    expected_days_counts_2024: list[int] = [29, 30, 29, 29, 30, 29, 30, 30, 29, 30, 30, 29]
    self.assertEqual(new_2024_info['first_solar_day'], date(2024, 2, 10))
    self.assertFalse(new_2024_info['leap'])
    self.assertIsNone(new_2024_info['leap_month'])
    self.assertListEqual(new_2024_info['days_counts'], expected_days_counts_2024)
    self.assertEqual(new_2024_info['ganzhi'], Ganzhi.from_str('甲辰'))

  def test_file_existence(self) -> None:
    '''The data files should exist and be readable.'''
    data_path: Path = Path(__file__).parent.parent / 'data'
    self.assertTrue(data_path.exists() and data_path.is_dir())

    txt_paths: dict[int, Path] = HkoData.common.get_raw_txt_file_paths()
    for path in txt_paths.values():
      self.assertTrue(path.exists() and path.is_file())
      with open(path, 'r', encoding='utf-8') as f:
        self.assertTrue(f.read() != '')

    self.assertTrue(HkoData.common.raw_data_ready())

  def test_raw_data_ready(self) -> None:
    self.assertTrue(HkoData.common.raw_data_ready())

    # Do something bad in between.

    temp_dir: Path = Path(tempfile.mkdtemp())
    data_path: Path = HkoData.common.get_data_base_path()
    self.assertTrue(temp_dir.exists() and temp_dir.is_dir())
    self.assertTrue(data_path.exists() and data_path.is_dir())

    # Copy the data folder to the temporary folder.
    shutil.copytree(data_path, temp_dir / 'data')

    try:
      shutil.move(data_path, temp_dir / 'data2')
      self.assertFalse(HkoData.common.raw_data_ready())

      # Create a file called "data" (not a folder).
      with open(data_path, 'w') as f:
        f.write('I am not a folder!!!')
      self.assertFalse(HkoData.common.raw_data_ready())

      # Remove the fake "data" file.
      data_path.unlink()
      self.assertFalse(data_path.exists())

      # Copy the original data folder back.
      shutil.copytree(temp_dir / 'data', data_path)
      self.assertTrue(HkoData.common.raw_data_ready())

      all_txt_paths: dict[int, Path] = HkoData.common.get_raw_txt_file_paths()
      random.choice(list(all_txt_paths.values())).unlink()
      self.assertFalse(HkoData.common.raw_data_ready())

    finally:
      # Finally restore the original data folder.
      # Also ensure the data is ready again after the above malicious operations.
      shutil.copytree(temp_dir / 'data', data_path, dirs_exist_ok=True)
      self.assertTrue(HkoData.common.raw_data_ready())

      shutil.rmtree(temp_dir)

  def test_do_encode(self) -> None:
    self.assertTrue(HkoData.common.encoded_data_ready())

    # Do something bad in between.

    temp_dir: Path = Path(tempfile.mkdtemp())
    jieqi_path: Path = HkoData.common.get_jieqi_encoded_data_path()
    lunardate_path: Path = HkoData.common.get_lunardate_encoded_data_path()
    self.assertTrue(temp_dir.exists() and temp_dir.is_dir())
    self.assertTrue(jieqi_path.exists() and jieqi_path.is_file())
    self.assertTrue(lunardate_path.exists() and lunardate_path.is_file())

    # Copy the data folder to the temporary folder.
    data_path: Path = HkoData.common.get_data_base_path()
    shutil.copytree(data_path, temp_dir / 'data')

    try:
      # Copy the encoded binary files to the temporary folder.
      shutil.move(jieqi_path, temp_dir / 'jieqi.bin')
      self.assertFalse(HkoData.common.encoded_data_ready())
      shutil.move(lunardate_path, temp_dir / 'lunardate.bin')
      self.assertFalse(HkoData.common.encoded_data_ready())

      # Ensure the encoded binary files are gone.
      self.assertFalse(jieqi_path.exists())
      self.assertFalse(lunardate_path.exists())

      # Encode them again.
      self.assertIsNotNone(HkoData.DecodedJieqiDates())
      self.assertTrue(HkoData.common.encoded_data_ready())

      lunardate_path.unlink()
      self.assertFalse(HkoData.common.encoded_data_ready())

      # Encode them again.
      self.assertIsNotNone(HkoData.DecodedLunarYears())
      self.assertTrue(HkoData.common.encoded_data_ready())

      # Ensure the new encoded binary files are the same as the old ones.
      prev_jieqi_md5: str = hashlib.md5((temp_dir / 'jieqi.bin').read_bytes()).hexdigest()
      prev_lunardate_md5: str = hashlib.md5((temp_dir / 'lunardate.bin').read_bytes()).hexdigest()

      new_jieqi_md5: str = hashlib.md5(jieqi_path.read_bytes()).hexdigest()
      new_lunardate_md5: str = hashlib.md5(lunardate_path.read_bytes()).hexdigest()

      self.assertEqual(prev_jieqi_md5, new_jieqi_md5)
      self.assertEqual(prev_lunardate_md5, new_lunardate_md5)

    finally:
      # Finally restore the original data folder.
      # Also ensure the data is ready again after the above malicious operations.
      shutil.copytree(temp_dir / 'data', data_path, dirs_exist_ok=True)
      self.assertTrue(HkoData.common.raw_data_ready())

      shutil.rmtree(temp_dir)
