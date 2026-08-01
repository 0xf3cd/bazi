# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_hko_data_utils.py

import random
import itertools
import pytest

from datetime import date, datetime, timedelta
from typing import Any

from src.calendar import CalendarType, CalendarDate, hko_data_utils
from src.calendar.hko_data import DecodedLunarYears, DecodedJieqiDates
from src.defines import Jieqi


@pytest.mark.slow
def test_is_valid_solar_date() -> None:
  d: date = date(1902, 1, 1)
  while d < date(2099, 1, 1):
    solar_date: CalendarDate = CalendarDate(d.year, d.month, d.day, CalendarType.SOLAR)
    assert hko_data_utils.is_valid_solar_date(solar_date)
    assert not hko_data_utils.is_valid_lunar_date(solar_date)
    assert not hko_data_utils.is_valid_ganzhi_date(solar_date)
    d = d + timedelta(days=1)

  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2024, 1, 1, CalendarType.LUNAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2024, 1, 1, CalendarType.GANZHI))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(9999, 2, 29, CalendarType.SOLAR)) # Out of supported range.
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2023, 2, 29, CalendarType.SOLAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2023, 13, 29, CalendarType.SOLAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(1900, 2, 29, CalendarType.SOLAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2024, 2, 30, CalendarType.SOLAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2024, 4, 31, CalendarType.SOLAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2023, 0, 29, CalendarType.SOLAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(2023, 1, 32, CalendarType.SOLAR))
  assert not hko_data_utils.is_valid_solar_date(CalendarDate(0, 1, 15, CalendarType.SOLAR))


@pytest.mark.slow
def test_is_valid_lunar_date() -> None:
  lunar_years_db: DecodedLunarYears = DecodedLunarYears()
  min_year: int = hko_data_utils.get_min_supported_date(CalendarType.LUNAR).year + 1
  max_year: int = hko_data_utils.get_max_supported_date(CalendarType.LUNAR).year - 1

  assert not hko_data_utils.is_valid_lunar_date(CalendarDate(0, 1, 1, CalendarType.LUNAR)) # Out or supported range.
  assert not hko_data_utils.is_valid_lunar_date(CalendarDate(9999, 1, 1, CalendarType.LUNAR)) # Out of supported range.

  for year in range(min_year, max_year + 1):
    info = lunar_years_db[year]

    for idx, count in enumerate(info['days_counts']):
      month = idx + 1

      for day in range(1, count + 1):
        lunar_date: CalendarDate = CalendarDate(year, month, day, CalendarType.LUNAR)
        assert not hko_data_utils.is_valid_solar_date(lunar_date)
        assert hko_data_utils.is_valid_lunar_date(lunar_date)
        assert not hko_data_utils.is_valid_ganzhi_date(lunar_date)

      assert not hko_data_utils.is_valid_lunar_date(CalendarDate(year, month, count + 1, CalendarType.LUNAR))

    assert not hko_data_utils.is_valid_lunar_date(CalendarDate(year, len(info['days_counts']) + 1, 1, CalendarType.LUNAR))


@pytest.mark.slow
def test_is_valid_ganzhi_date() -> None:
  def __run_test_in_ganzhi_year(year: int) -> None:
    days_counts: list[int] = hko_data_utils.days_counts_in_ganzhi_year(year)
    for idx, count in enumerate(days_counts):
      month: int = idx + 1
      for day in range(1, count + 1):
        ganzhi_date: CalendarDate = CalendarDate(year, month, day, CalendarType.GANZHI)
        assert not hko_data_utils.is_valid_solar_date(ganzhi_date)
        assert not hko_data_utils.is_valid_lunar_date(ganzhi_date)
        assert hko_data_utils.is_valid_ganzhi_date(ganzhi_date)
      assert not hko_data_utils.is_valid_ganzhi_date(CalendarDate(year, month, count + 1, CalendarType.GANZHI))
    assert not hko_data_utils.is_valid_ganzhi_date(CalendarDate(year, 0, 1, CalendarType.GANZHI))
    assert not hko_data_utils.is_valid_ganzhi_date(CalendarDate(year, len(days_counts) + 1, 1, CalendarType.GANZHI))

  min_year: int = hko_data_utils.get_min_supported_date(CalendarType.LUNAR).year + 1
  max_year: int = hko_data_utils.get_max_supported_date(CalendarType.LUNAR).year - 1
  for year in range(min_year, max_year + 1):
    __run_test_in_ganzhi_year(year)

  assert not hko_data_utils.is_valid_ganzhi_date(CalendarDate(0, 1, 1, CalendarType.GANZHI)) # Out or supported range.
  assert not hko_data_utils.is_valid_ganzhi_date(CalendarDate(9999, 1, 1, CalendarType.GANZHI)) # Out of supported range.


@pytest.mark.slow
def test_days_counts_in_ganzhi_year() -> None:
  min_year: int = hko_data_utils.get_min_supported_date(CalendarType.GANZHI).year
  max_year: int = hko_data_utils.get_max_supported_date(CalendarType.GANZHI).year

  # Test negative cases first.
  with pytest.raises(AssertionError):
    hko_data_utils.days_counts_in_ganzhi_year(-1)
  with pytest.raises(AssertionError):
    hko_data_utils.days_counts_in_ganzhi_year(min_year - 1)
  with pytest.raises(AssertionError):
    hko_data_utils.days_counts_in_ganzhi_year(max_year + 1)

  # Test edge cases.
  days_counts = hko_data_utils.days_counts_in_ganzhi_year(min_year)
  for count in days_counts:
    assert 29 <= count <= 32
  days_counts = hko_data_utils.days_counts_in_ganzhi_year(max_year)
  for count in days_counts:
    assert 29 <= count <= 32

  jieqi_dates_db: DecodedJieqiDates = DecodedJieqiDates()
  month_starting_jieqis: list[Jieqi] = [ # List the jieqis that start new months in this ganzhi year.
    Jieqi.立春, Jieqi.惊蛰, Jieqi.清明, Jieqi.立夏, Jieqi.芒种, Jieqi.小暑,
    Jieqi.立秋, Jieqi.白露, Jieqi.寒露, Jieqi.立冬, Jieqi.大雪, Jieqi.小寒,
  ]
  for year in range(min_year, max_year + 1):
    dates: list[date] = []
    # First 11 Jieqis will be in `year`, and the last Jieqi will be in `year + 1`.
    for jq in month_starting_jieqis[:-1]:
      dates.append(jieqi_dates_db.get(year, jq))
    dates.append(jieqi_dates_db.get(year + 1, month_starting_jieqis[-1]))
    dates.append(hko_data_utils.jieqi_dates_db.get(year + 1, Jieqi.立春)) # Start of the next ganzhi year.

    days_counts = hko_data_utils.days_counts_in_ganzhi_year(year)
    for idx, (start_date, next_start_date) in enumerate(itertools.pairwise(dates)):
      days_in_this_month: int = days_counts[idx]
      assert days_in_this_month == (next_start_date - start_date).days


def test_days_counts_in_ganzhi_year_cannot_poison_the_cache() -> None:
  '''
  The lengths come from a cache, so handing back the cached list itself would let one
  caller's in-place edit corrupt every later answer.  Worse, it would not stay contained:
  `is_valid_ganzhi_date` caches verdicts computed from these lengths, so a wrong answer
  cached during the poisoned window would outlive the edit (issue #92).
  '''
  counts: list[int] = hko_data_utils.days_counts_in_ganzhi_year(2000)
  assert counts is not hko_data_utils.days_counts_in_ganzhi_year(2000)

  # Poison, then FIRST-query a verdict computed from the lengths: month 1 of ganzhi
  # year 2000 has 30 days, so day 31 must stay invalid even while the edit is live.
  hko_data_utils.is_valid_ganzhi_date.cache_clear()
  assert counts[0] == 30
  counts[0] = 999
  assert hko_data_utils.days_counts_in_ganzhi_year(2000)[0] == 30
  assert not hko_data_utils.is_valid_ganzhi_date(CalendarDate(2000, 1, 31, CalendarType.GANZHI))


def test_is_valid() -> None:
  for date_type in [CalendarType.SOLAR, CalendarType.LUNAR, CalendarType.GANZHI]:
    min_date: CalendarDate = hko_data_utils.get_min_supported_date(date_type)
    max_date: CalendarDate = hko_data_utils.get_max_supported_date(date_type)

    assert hko_data_utils.is_valid(min_date)
    assert hko_data_utils.is_valid(max_date)
    assert not hko_data_utils.is_valid(CalendarDate(0, 1, 1, date_type)) # Out or supported range.
    assert not hko_data_utils.is_valid(CalendarDate(9999, 1, 1, date_type)) # Out of supported range.

  class __DuckTypeClass:
    def __init__(self, anything: Any) -> None:
      self.date_type = anything
  assert not hko_data_utils.is_valid(__DuckTypeClass(0)) # Test duck type.


def _solar_date_gen(d: CalendarDate):
  assert d.date_type == CalendarType.SOLAR
  _d: date = date(d.year, d.month, d.day)
  while True:
    yield CalendarDate(_d.year, _d.month, _d.day, CalendarType.SOLAR)
    _d = _d + timedelta(days=1)


def _lunar_date_gen(d: CalendarDate):
  assert d.date_type == CalendarType.LUNAR
  _y, _m, _d = d.year, d.month, d.day
  _lunar_year_db: DecodedLunarYears = DecodedLunarYears()
  _year_data = _lunar_year_db.get(_y)
  while True:
    yield CalendarDate(_y, _m, _d, CalendarType.LUNAR)
    _d += 1
    if _d > _year_data['days_counts'][_m - 1]:
      _d = 1
      _m += 1
      if _m > len(_year_data['days_counts']):
        _m = 1
        _y += 1
        _year_data = _lunar_year_db.get(_y)


def _ganzhi_date_gen(d: CalendarDate):
  assert d.date_type == CalendarType.GANZHI
  _y, _m, _d = d.year, d.month, d.day
  _month_lengths: list[int] = hko_data_utils.days_counts_in_ganzhi_year(_y)
  while True:
    yield CalendarDate(_y, _m, _d, CalendarType.GANZHI)
    _d += 1
    if _d > _month_lengths[_m - 1]:
      _d = 1
      _m += 1
      if _m > 12:
        _m = 1
        _y += 1
        _month_lengths = hko_data_utils.days_counts_in_ganzhi_year(_y)


@pytest.mark.slow
def test_lunar_to_solar() -> None:
  min_lunar_date: CalendarDate = hko_data_utils.get_min_supported_date(CalendarType.LUNAR)
  max_lunar_date: CalendarDate = hko_data_utils.get_max_supported_date(CalendarType.LUNAR)

  assert hko_data_utils.lunar_to_solar(min_lunar_date) == hko_data_utils.get_min_supported_date(CalendarType.SOLAR)
  assert hko_data_utils.lunar_to_solar(max_lunar_date) == hko_data_utils.get_max_supported_date(CalendarType.SOLAR)

  solar_date_gen = _solar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.SOLAR))
  lunar_date_gen = _lunar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.LUNAR))

  while True:
    solar_date = next(solar_date_gen)
    lunar_date = next(lunar_date_gen)
    assert solar_date == hko_data_utils.lunar_to_solar(lunar_date)

    if lunar_date == max_lunar_date:
      assert solar_date == hko_data_utils.get_max_supported_date(CalendarType.SOLAR)
      break


@pytest.mark.slow
def test_solar_to_lunar() -> None:
  min_solar_date: CalendarDate = hko_data_utils.get_min_supported_date(CalendarType.SOLAR)
  max_solar_date: CalendarDate = hko_data_utils.get_max_supported_date(CalendarType.SOLAR)

  assert hko_data_utils.solar_to_lunar(min_solar_date) == hko_data_utils.get_min_supported_date(CalendarType.LUNAR)
  assert hko_data_utils.solar_to_lunar(max_solar_date) == hko_data_utils.get_max_supported_date(CalendarType.LUNAR)

  solar_date_gen = _solar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.SOLAR))
  lunar_date_gen = _lunar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.LUNAR))

  while True:
    solar_date = next(solar_date_gen)
    lunar_date = next(lunar_date_gen)
    assert lunar_date == hko_data_utils.solar_to_lunar(solar_date)

    if solar_date == max_solar_date:
      assert lunar_date == hko_data_utils.get_max_supported_date(CalendarType.LUNAR)
      break


@pytest.mark.slow
def test_ganzhi_to_solar() -> None:
  min_ganzhi_date: CalendarDate = hko_data_utils.get_min_supported_date(CalendarType.GANZHI)
  max_ganzhi_date: CalendarDate = hko_data_utils.get_max_supported_date(CalendarType.GANZHI)

  assert hko_data_utils.ganzhi_to_solar(min_ganzhi_date) == hko_data_utils.get_min_supported_date(CalendarType.SOLAR)
  assert hko_data_utils.ganzhi_to_solar(max_ganzhi_date) == hko_data_utils.get_max_supported_date(CalendarType.SOLAR)

  solar_date_gen = _solar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.SOLAR))
  ganzhi_date_gen = _ganzhi_date_gen(hko_data_utils.get_min_supported_date(CalendarType.GANZHI))

  while True:
    solar_date = next(solar_date_gen)
    ganzhi_date = next(ganzhi_date_gen)
    assert solar_date == hko_data_utils.ganzhi_to_solar(ganzhi_date)

    if ganzhi_date == max_ganzhi_date:
      assert solar_date == hko_data_utils.get_max_supported_date(CalendarType.SOLAR)
      break


@pytest.mark.slow
def test_solar_to_ganzhi() -> None:
  min_solar_date: CalendarDate = hko_data_utils.get_min_supported_date(CalendarType.SOLAR)
  max_solar_date: CalendarDate = hko_data_utils.get_max_supported_date(CalendarType.SOLAR)

  assert hko_data_utils.solar_to_ganzhi(min_solar_date) == hko_data_utils.get_min_supported_date(CalendarType.GANZHI)
  assert hko_data_utils.solar_to_ganzhi(max_solar_date) == hko_data_utils.get_max_supported_date(CalendarType.GANZHI)

  solar_date_gen = _solar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.SOLAR))
  ganzhi_date_gen = _ganzhi_date_gen(hko_data_utils.get_min_supported_date(CalendarType.GANZHI))

  while True:
    solar_date = next(solar_date_gen)
    ganzhi_date = next(ganzhi_date_gen)
    assert ganzhi_date == hko_data_utils.solar_to_ganzhi(solar_date)

    if solar_date == max_solar_date:
      assert ganzhi_date == hko_data_utils.get_max_supported_date(CalendarType.GANZHI)
      break


@pytest.mark.slow
def test_lunar_to_ganzhi() -> None:
  min_lunar_date: CalendarDate = hko_data_utils.get_min_supported_date(CalendarType.LUNAR)
  max_lunar_date: CalendarDate = hko_data_utils.get_max_supported_date(CalendarType.LUNAR)

  assert hko_data_utils.lunar_to_ganzhi(min_lunar_date) == hko_data_utils.get_min_supported_date(CalendarType.GANZHI)
  assert hko_data_utils.lunar_to_ganzhi(max_lunar_date) == hko_data_utils.get_max_supported_date(CalendarType.GANZHI)

  lunar_date_gen = _lunar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.LUNAR))
  ganzhi_date_gen = _ganzhi_date_gen(hko_data_utils.get_min_supported_date(CalendarType.GANZHI))

  while True:
    lunar_date = next(lunar_date_gen)
    ganzhi_date = next(ganzhi_date_gen)
    assert ganzhi_date == hko_data_utils.lunar_to_ganzhi(lunar_date)

    if lunar_date == max_lunar_date:
      assert ganzhi_date == hko_data_utils.get_max_supported_date(CalendarType.GANZHI)
      break


@pytest.mark.slow
def test_ganzhi_to_lunar() -> None:
  min_ganzhi_date: CalendarDate = hko_data_utils.get_min_supported_date(CalendarType.GANZHI)
  max_ganzhi_date: CalendarDate = hko_data_utils.get_max_supported_date(CalendarType.GANZHI)

  assert hko_data_utils.ganzhi_to_lunar(min_ganzhi_date) == hko_data_utils.get_min_supported_date(CalendarType.LUNAR)
  assert hko_data_utils.ganzhi_to_lunar(max_ganzhi_date) == hko_data_utils.get_max_supported_date(CalendarType.LUNAR)

  ganzhi_date_gen = _ganzhi_date_gen(hko_data_utils.get_min_supported_date(CalendarType.GANZHI))
  lunar_date_gen = _lunar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.LUNAR))

  while True:
    ganzhi_date = next(ganzhi_date_gen)
    lunar_date = next(lunar_date_gen)
    assert lunar_date == hko_data_utils.ganzhi_to_lunar(ganzhi_date)

    if ganzhi_date == max_ganzhi_date:
      assert lunar_date == hko_data_utils.get_max_supported_date(CalendarType.LUNAR)
      break


@pytest.mark.slow
def test_complex_date_conversions() -> None:
  solar_date_gen = _solar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.SOLAR))
  lunar_date_gen = _lunar_date_gen(hko_data_utils.get_min_supported_date(CalendarType.LUNAR))
  ganzhi_date_gen = _ganzhi_date_gen(hko_data_utils.get_min_supported_date(CalendarType.GANZHI))

  for _ in range(4096):
    solar_date = next(solar_date_gen)
    lunar_date = next(lunar_date_gen)
    ganzhi_date = next(ganzhi_date_gen)

    # ganzhi
    _solar_date = hko_data_utils.ganzhi_to_solar(ganzhi_date)
    _lunar_date = hko_data_utils.ganzhi_to_lunar(ganzhi_date)

    assert solar_date == _solar_date
    assert lunar_date == _lunar_date
    assert ganzhi_date == hko_data_utils.solar_to_ganzhi(_solar_date)
    assert ganzhi_date == hko_data_utils.lunar_to_ganzhi(_lunar_date)

    # solar
    _lunar_date = hko_data_utils.solar_to_lunar(solar_date)
    _ganzhi_date = hko_data_utils.solar_to_ganzhi(solar_date)

    assert lunar_date == _lunar_date
    assert ganzhi_date == _ganzhi_date
    assert solar_date == hko_data_utils.lunar_to_solar(_lunar_date)
    assert solar_date == hko_data_utils.ganzhi_to_solar(_ganzhi_date)

    # lunar
    _solar_date = hko_data_utils.lunar_to_solar(lunar_date)
    _ganzhi_date = hko_data_utils.lunar_to_ganzhi(lunar_date)

    assert solar_date == _solar_date
    assert ganzhi_date == _ganzhi_date
    assert lunar_date == hko_data_utils.solar_to_lunar(_solar_date)
    assert lunar_date == hko_data_utils.ganzhi_to_lunar(_ganzhi_date)


def test_date_conversions_negative() -> None:
  with pytest.raises(AssertionError):
    hko_data_utils.ganzhi_to_lunar(CalendarDate(1, 1, 1, CalendarType.GANZHI))
  with pytest.raises(AssertionError):
    hko_data_utils.ganzhi_to_lunar(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

  with pytest.raises(AssertionError):
    hko_data_utils.lunar_to_ganzhi(CalendarDate(1, 1, 1, CalendarType.LUNAR))
  with pytest.raises(AssertionError):
    hko_data_utils.lunar_to_ganzhi(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

  with pytest.raises(AssertionError):
    hko_data_utils.solar_to_lunar(CalendarDate(1, 1, 1, CalendarType.SOLAR))
  with pytest.raises(AssertionError):
    hko_data_utils.solar_to_lunar(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

  with pytest.raises(AssertionError):
    hko_data_utils.lunar_to_solar(CalendarDate(1, 1, 1, CalendarType.LUNAR))
  with pytest.raises(AssertionError):
    hko_data_utils.lunar_to_solar(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

  with pytest.raises(AssertionError):
    hko_data_utils.solar_to_ganzhi(CalendarDate(1, 1, 1, CalendarType.SOLAR))
  with pytest.raises(AssertionError):
    hko_data_utils.solar_to_ganzhi(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

  with pytest.raises(AssertionError):
    hko_data_utils.ganzhi_to_solar(CalendarDate(1, 1, 1, CalendarType.GANZHI))
  with pytest.raises(AssertionError):
    hko_data_utils.ganzhi_to_solar(CalendarDate(2024, 1, 1, CalendarType.SOLAR))


def test_to_solar() -> None:
  # Positive cases.
  d: date = date(2023, 5, 8)
  solar_date: CalendarDate = hko_data_utils.to_solar(d)
  assert solar_date == CalendarDate(2023, 5, 8, CalendarType.SOLAR)
  assert solar_date == hko_data_utils.to_solar(d)
  assert solar_date == hko_data_utils.to_solar(solar_date)
  assert solar_date == hko_data_utils.to_solar(hko_data_utils.solar_to_lunar(solar_date))
  assert solar_date == hko_data_utils.to_solar(hko_data_utils.solar_to_ganzhi(solar_date))

  # Negative cases.
  with pytest.raises(AssertionError):
    hko_data_utils.to_solar(CalendarDate(9999, 1, 1, CalendarType.SOLAR)) # Invalid date
  with pytest.raises(AssertionError):
    hko_data_utils.to_solar('2024-01-01') # Invalid type


def test_to_lunar() -> None:
  # Positive cases.
  d: date = date(2023, 5, 8)
  lunar_date: CalendarDate = hko_data_utils.to_lunar(d)
  assert lunar_date == hko_data_utils.solar_to_lunar(CalendarDate(2023, 5, 8, CalendarType.SOLAR))
  assert lunar_date == hko_data_utils.to_lunar(d)
  assert lunar_date == hko_data_utils.to_lunar(lunar_date)
  assert lunar_date == hko_data_utils.to_lunar(hko_data_utils.lunar_to_solar(lunar_date))
  assert lunar_date == hko_data_utils.to_lunar(hko_data_utils.lunar_to_ganzhi(lunar_date))

  # Negative cases.
  with pytest.raises(AssertionError):
    hko_data_utils.to_lunar(CalendarDate(9999, 1, 1, CalendarType.LUNAR)) # Invalid date
  with pytest.raises(AssertionError):
    hko_data_utils.to_lunar('2024-01-01') # Invalid type


def test_to_ganzhi() -> None:
  # Positive cases.
  d: date = date(2023, 5, 8)
  ganzhi_date: CalendarDate = hko_data_utils.to_ganzhi(d)
  assert ganzhi_date == hko_data_utils.solar_to_ganzhi(CalendarDate(2023, 5, 8, CalendarType.SOLAR))
  assert ganzhi_date == hko_data_utils.to_ganzhi(d)
  assert ganzhi_date == hko_data_utils.to_ganzhi(ganzhi_date)
  assert ganzhi_date == hko_data_utils.to_ganzhi(hko_data_utils.ganzhi_to_solar(ganzhi_date))
  assert ganzhi_date == hko_data_utils.to_ganzhi(hko_data_utils.ganzhi_to_lunar(ganzhi_date))

  # Negative cases.
  with pytest.raises(AssertionError):
    hko_data_utils.to_ganzhi(CalendarDate(9999, 1, 1, CalendarType.GANZHI)) # Invalid date
  with pytest.raises(AssertionError):
    hko_data_utils.to_ganzhi('2024-01-01') # Invalid type


def test_to_date() -> None:
  d = date(2023, 5, 8)
  assert hko_data_utils.to_date(d) == d

  dt = datetime(2023, 5, 8, 1, 2, 3)
  assert hko_data_utils.to_date(dt) == d

  cd = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
  assert hko_data_utils.to_date(cd) == date(2000, 1, 1)

  cd = CalendarDate(1901, 1, 1, CalendarType.LUNAR)
  assert hko_data_utils.to_date(cd) == date(1901, 2, 19)

  # Negative cases.
  with pytest.raises(AssertionError):
    hko_data_utils.to_date(CalendarDate(9999, 1, 1, CalendarType.GANZHI)) # Invalid date
  with pytest.raises(AssertionError):
    hko_data_utils.to_date('2024-01-01') # Invalid type


def test_get_jieqi_date() -> None:
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_date('2024', Jieqi.大寒)
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_date(2024, '大寒')
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_date(9999, Jieqi.大寒) # Out of supported solar year range.
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_date(2101, Jieqi.小寒) # Out of supported solar year range.
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_date(0, Jieqi.大寒) # Out of supported solar year range.
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_date(1900, Jieqi.冬至) # Out of supported solar year range.

  assert hko_data_utils.jieqi_date(1901, Jieqi.小寒) == date(1901, 1, 6)
  assert hko_data_utils.jieqi_date(2100, Jieqi.冬至) == date(2100, 12, 22)

  assert hko_data_utils.jieqi_date(2024, Jieqi.大寒) == date(2024, 1, 20)
  assert hko_data_utils.jieqi_date(1997, Jieqi.小寒) == date(1997, 1, 5)
  assert hko_data_utils.jieqi_date(2000, Jieqi.立春) == date(2000, 2, 4)
  assert hko_data_utils.jieqi_date(2005, Jieqi.雨水) == date(2005, 2, 18)

  random_solar_year: int = random.randint(1901, 2100)
  dates: list[date] = []
  for jieqi in Jieqi.as_list(ganzhi_year=False):
    dates.append(hko_data_utils.jieqi_date(random_solar_year, jieqi))
  for d1, d2 in itertools.pairwise(dates):
    assert d1 < d2


def test_get_jieqi_moment() -> None:
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_moment('2024', Jieqi.大寒)
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_moment(2024, '大寒')
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_moment(9999, Jieqi.大寒) # Out of supported solar year range.
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_moment(2101, Jieqi.小寒) # Out of supported solar year range.
  with pytest.raises(AssertionError):
    hko_data_utils.jieqi_moment(0, Jieqi.大寒) # Out of supported solar year range.

  # HKO data only supported day-level precision.
  # So all returned moments are always at the beginning of the day.
  assert hko_data_utils.jieqi_moment(1901, Jieqi.小寒) == datetime(1901, 1, 6, 0, 0, 0)
  assert hko_data_utils.jieqi_moment(2100, Jieqi.冬至) == datetime(2100, 12, 22, 0, 0, 0)

  assert hko_data_utils.jieqi_moment(2024, Jieqi.大寒) == datetime(2024, 1, 20, 0, 0, 0)
  assert hko_data_utils.jieqi_moment(1997, Jieqi.小寒) == datetime(1997, 1, 5, 0, 0, 0)
  assert hko_data_utils.jieqi_moment(2000, Jieqi.立春) == datetime(2000, 2, 4, 0, 0, 0)
  assert hko_data_utils.jieqi_moment(2005, Jieqi.雨水) == datetime(2005, 2, 18, 0, 0, 0)

  random_solar_year: int = random.randint(1901, 2100)
  datetimes: list[datetime] = []
  for jieqi in Jieqi.as_list(ganzhi_year=False): # The first Jieqi in a solar year is always "小寒".
    datetimes.append(hko_data_utils.jieqi_moment(random_solar_year, jieqi))
  for d1, d2 in itertools.pairwise(datetimes):
    assert d1 < d2


def test_prev_jie() -> None:
  supported_range: tuple[datetime, datetime] = hko_data_utils.supported_jie_boundaries()

  with pytest.raises(AssertionError):
    hko_data_utils.prev_jie('2024-06-15')
  with pytest.raises(ValueError):
    hko_data_utils.prev_jie(datetime(1899, 12, 31))
  with pytest.raises(ValueError):
    hko_data_utils.prev_jie(datetime(2101, 1, 1))
  with pytest.raises(ValueError):
    hko_data_utils.prev_jie(supported_range[0] - timedelta(microseconds=1))
  with pytest.raises(ValueError):
    hko_data_utils.prev_jie(supported_range[1])

  for _ in range(500):
    random_dt: datetime = datetime(
      year=random.randint(1800, 2200),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59),
    )
    if supported_range[0] <= random_dt < supported_range[1]: # In supported range.
      assert isinstance(hko_data_utils.prev_jie(random_dt), tuple)
    else:
      with pytest.raises(ValueError):
        hko_data_utils.prev_jie(random_dt)

  assert hko_data_utils.prev_jie(hko_data_utils.jieqi_moment(2024, Jieqi.大雪)) == (
    Jieqi.大雪, hko_data_utils.jieqi_moment(2024, Jieqi.大雪)
  )

  assert hko_data_utils.prev_jie(hko_data_utils.jieqi_moment(2024, Jieqi.大雪) + timedelta(microseconds=1)) == (
    Jieqi.大雪, hko_data_utils.jieqi_moment(2024, Jieqi.大雪)
  )

  assert hko_data_utils.prev_jie(hko_data_utils.jieqi_moment(2024, Jieqi.大雪) - timedelta(microseconds=1)) == (
    Jieqi.立冬, hko_data_utils.jieqi_moment(2024, Jieqi.立冬)
  )

  assert hko_data_utils.prev_jie(hko_data_utils.jieqi_moment(2024, Jieqi.小寒)) == (
    Jieqi.小寒, hko_data_utils.jieqi_moment(2024, Jieqi.小寒)
  )

  assert hko_data_utils.prev_jie(hko_data_utils.jieqi_moment(2024, Jieqi.小寒) - timedelta(microseconds=1)) == (
    Jieqi.大雪, hko_data_utils.jieqi_moment(2023, Jieqi.大雪)
  )

  first_year: int = hko_data_utils.jieqi_dates_db.start_year
  jie_list: list[Jieqi] = Jieqi.as_list(ganzhi_year=False)[::2]
  for jie1, jie2 in itertools.pairwise(jie_list):
    assert hko_data_utils.prev_jie(hko_data_utils.jieqi_moment(first_year, jie1)) == (
      jie1, hko_data_utils.jieqi_moment(first_year, jie1)
    )
    assert hko_data_utils.prev_jie(hko_data_utils.jieqi_moment(first_year, jie2) - timedelta(microseconds=1)) == (
      jie1, hko_data_utils.jieqi_moment(first_year, jie1)
    )


def test_next_jie() -> None:
  supported_range: tuple[datetime, datetime] = hko_data_utils.supported_jie_boundaries()

  with pytest.raises(AssertionError):
    hko_data_utils.next_jie('2024-06-15')
  with pytest.raises(ValueError):
    hko_data_utils.next_jie(datetime(1899, 12, 31))
  with pytest.raises(ValueError):
    hko_data_utils.next_jie(datetime(2101, 1, 1))
  with pytest.raises(ValueError):
    hko_data_utils.next_jie(supported_range[0] - timedelta(microseconds=1))
  with pytest.raises(ValueError):
    hko_data_utils.next_jie(supported_range[1])

  for _ in range(500):
    random_dt: datetime = datetime(
      year=random.randint(1800, 2200),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59),
    )
    if supported_range[0] <= random_dt < supported_range[1]: # In supported range.
      assert isinstance(hko_data_utils.next_jie(random_dt), tuple)
    else:
      with pytest.raises(ValueError):
        hko_data_utils.next_jie(random_dt)

  assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(2024, Jieqi.小寒)) == (
    Jieqi.立春, hko_data_utils.jieqi_moment(2024, Jieqi.立春)
  )

  assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(2024, Jieqi.小寒) + timedelta(microseconds=1)) == (
    Jieqi.立春, hko_data_utils.jieqi_moment(2024, Jieqi.立春)
  )

  assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(2024, Jieqi.小寒) - timedelta(microseconds=1)) == (
    Jieqi.小寒, hko_data_utils.jieqi_moment(2024, Jieqi.小寒)
  )

  assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(2024, Jieqi.大雪)) == (
    Jieqi.小寒, hko_data_utils.jieqi_moment(2025, Jieqi.小寒)
  )

  assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(2024, Jieqi.大雪) + timedelta(microseconds=1)) == (
    Jieqi.小寒, hko_data_utils.jieqi_moment(2025, Jieqi.小寒)
  )

  assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(2024, Jieqi.大雪) - timedelta(microseconds=1)) == (
    Jieqi.大雪, hko_data_utils.jieqi_moment(2024, Jieqi.大雪)
  )

  last_year: int = hko_data_utils.jieqi_dates_db.end_year
  jie_list: list[Jieqi] = Jieqi.as_list(ganzhi_year=False)[::2]
  for jie1, jie2 in itertools.pairwise(jie_list):
    assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(last_year, jie1)) == (
      jie2, hko_data_utils.jieqi_moment(last_year, jie2)
    )
    assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(last_year, jie1) - timedelta(microseconds=1)) == (
      jie1, hko_data_utils.jieqi_moment(last_year, jie1)
    )
    assert hko_data_utils.next_jie(hko_data_utils.jieqi_moment(last_year, jie2) - timedelta(microseconds=1)) == (
      jie2, hko_data_utils.jieqi_moment(last_year, jie2)
    )
