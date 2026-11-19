# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_hko_data.py

import random
import shutil

from pathlib import Path
from datetime import date, timedelta

import pytest

from bazi.defines import Jieqi, Ganzhi

import hko_data
from hko_data import encoder


pytestmark = pytest.mark.hkodata


def test_traditional_chinese_jieqi() -> None:
  assert len(hko_data.jieqi_list_in_traditional_chinese) == 24


def test_traditional_chinese_month() -> None:
  assert len(hko_data.twelve_months_in_traditional_chinese) == 12


def test_int_bytes_conversion(rng: random.Random) -> None:
  assert hko_data.int_to_bytes(0x12345678, 4) == b'\x12\x34\x56\x78'
  assert hko_data.bytes_to_int(b'\x12\x34\x56\x78') == 0x12345678

  for _ in range(512):
    i: int = rng.randint(0, 0xffffffff)
    assert i == hko_data.bytes_to_int(hko_data.int_to_bytes(i, 4))


def test_date_bytes_conversion(rng: random.Random) -> None:
  assert hko_data.bytes_to_date(b'\x00\x01\x01\x01') == date(1, 1, 1)
  assert hko_data.bytes_to_date(hko_data.date_to_bytes(date(2024, 2, 25))) == date(2024, 2, 25)

  dt: date = date(
    year=rng.randint(1600, 2500),
    month=rng.randint(1, 12),
    day=rng.randint(1, 28), # Avoid invalid dates such as February 31.
  )
  for _ in range(512):
    dt += timedelta(days=rng.randint(1, 3))
    dt_bytes: bytes = hko_data.date_to_bytes(dt)
    assert dt == hko_data.bytes_to_date(dt_bytes)
    assert len(dt_bytes) == 4
    assert hko_data.bytes_to_int(dt_bytes[0:2]) == dt.year
    assert hko_data.bytes_to_int(dt_bytes[2:3]) == dt.month
    assert hko_data.bytes_to_int(dt_bytes[3:4]) == dt.day

  with pytest.raises(ValueError):
    hko_data.bytes_to_date(b'\x00\x01\x00\x00')
  for data in (b'\x00\x00', b'\x00\x00' * 4, b'\x00\x00' * 10):
    with pytest.raises(AssertionError):
      hko_data.bytes_to_date(data)


def test_decode_jieqi() -> None:
  decoded: hko_data.DecodedJieqiDates = hko_data.DecodedJieqiDates()
  assert decoded.supported_year_range() == range(1901, 2101)
  assert decoded.start_year == hko_data.START_YEAR
  assert decoded.end_year == hko_data.END_YEAR

  for year in decoded.supported_year_range():
    dates: hko_data.JieqiDates = decoded[year]
    assert set(dates) == set(Jieqi)
    assert len(dates) == 24
    for jieqi in Jieqi:
      assert decoded.get(year, jieqi) == dates[jieqi]

  assert decoded.get(1964, Jieqi.寒露) == date(1964, 10, 8)
  assert decoded.get(1997, Jieqi.小寒) == date(1997, 1, 5)
  assert decoded.get(2024, Jieqi.立春) == date(2024, 2, 4)


def test_decode_lunar_year() -> None:
  decoded: hko_data.DecodedLunarYears = hko_data.DecodedLunarYears()
  assert decoded.supported_year_range() == range(1901, 2100)
  assert decoded.start_year == hko_data.START_YEAR
  assert decoded.end_year == hko_data.END_YEAR - 1
  cycle = Ganzhi.list_sexagenary_cycle()

  for year in decoded.supported_year_range():
    info = decoded[year]
    assert info == decoded.get(year)
    assert info.leap == (info.leap_month is not None)
    assert len(info.days_counts) == (13 if info.leap else 12)
    assert all(count in (29, 30) for count in info.days_counts)
    assert info.ganzhi == cycle[(year - 1924) % 60]
    if year < decoded.end_year:
      assert info.first_solar_day + timedelta(days=sum(info.days_counts)) == decoded[year + 1].first_solar_day


@pytest.mark.parametrize('year, first_day, leap_month, days_counts, ganzhi', [
  (2000, date(2000, 2, 5), None, (30, 30, 29, 29, 30, 29, 29, 30, 29, 30, 30, 29), '庚辰'),
  (2001, date(2001, 1, 24), 4, (30, 30, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30), '辛巳'),
  (2024, date(2024, 2, 10), None, (29, 30, 29, 29, 30, 29, 30, 30, 29, 30, 30, 29), '甲辰'),
])
def test_lunar_year_examples(
  year: int,
  first_day: date,
  leap_month: int | None,
  days_counts: tuple[int, ...],
  ganzhi: str,
) -> None:
  info = hko_data.DecodedLunarYears().get(year)
  assert info.first_solar_day == first_day
  assert info.leap == (leap_month is not None)
  assert info.leap_month == leap_month
  assert info.days_counts == days_counts
  assert info.ganzhi == Ganzhi.from_str(ganzhi)


@pytest.mark.parametrize('decoder_type', [hko_data.DecodedJieqiDates, hko_data.DecodedLunarYears])
def test_decode_outside_data_range(
  decoder_type: type[hko_data.DecodedJieqiDates] | type[hko_data.DecodedLunarYears],
) -> None:
  decoded = decoder_type()
  for year in (decoded.start_year - 1, decoded.end_year + 1):
    with pytest.raises(AssertionError):
      decoded[year]


def test_file_existence() -> None:
  data_path: Path = hko_data.get_data_base_path()
  assert data_path.is_dir()
  for path in hko_data.get_raw_txt_file_paths().values():
    assert path.is_file()
    assert path.read_text(encoding='utf-8')
  assert hko_data.raw_data_ready()
  assert hko_data.encoded_data_ready()


def test_raw_data_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  source: Path = hko_data.get_data_base_path()
  data_path: Path = tmp_path / 'data'
  monkeypatch.setattr(hko_data.common, 'get_data_base_path', lambda: data_path)
  assert not hko_data.raw_data_ready()
  data_path.write_text('I am not a folder.')
  assert not hko_data.raw_data_ready()
  data_path.unlink()

  shutil.copytree(source, data_path)
  assert hko_data.raw_data_ready()
  hko_data.get_raw_txt_file_paths()[1901].unlink()
  assert not hko_data.raw_data_ready()


@pytest.mark.slow
def test_do_encode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  # Rebuild a copy, so a failed test cannot damage the committed reference data.
  source: Path = hko_data.get_data_base_path()
  data_path: Path = tmp_path / 'data'
  shutil.copytree(source, data_path)
  monkeypatch.setattr(hko_data.common, 'get_data_base_path', lambda: data_path)
  jieqi_path = hko_data.get_jieqi_encoded_data_path()
  lunar_path = hko_data.get_lunardate_encoded_data_path()
  expected_jieqi: bytes = jieqi_path.read_bytes()
  expected_lunar: bytes = lunar_path.read_bytes()

  encoder.do_encode() # Existing files need no work.
  assert jieqi_path.read_bytes() == expected_jieqi
  assert lunar_path.read_bytes() == expected_lunar

  jieqi_path.unlink()
  assert not hko_data.encoded_data_ready()
  lunar_path.unlink()
  assert not hko_data.encoded_data_ready()
  with pytest.raises(RuntimeError, match='Encoded HKO test data files are missing'):
    hko_data.DecodedJieqiDates()
  with pytest.raises(RuntimeError, match='Encoded HKO test data files are missing'):
    hko_data.DecodedLunarYears()

  encoder.do_encode()
  assert hko_data.encoded_data_ready()
  assert hko_data.DecodedJieqiDates().get(2024, Jieqi.立春) == date(2024, 2, 4)
  assert hko_data.DecodedLunarYears().get(2024).first_solar_day == date(2024, 2, 10)
  assert jieqi_path.read_bytes() == expected_jieqi
  assert lunar_path.read_bytes() == expected_lunar

  lunar_path.unlink()
  encoder.do_encode()
  assert hko_data.encoded_data_ready()
  assert jieqi_path.read_bytes() == expected_jieqi
  assert lunar_path.read_bytes() == expected_lunar
