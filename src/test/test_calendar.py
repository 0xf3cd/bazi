# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_calendar.py

import pytest
import unittest
import random
import copy
from datetime import date, timedelta
from itertools import product
from typing import Any

from src.hkodata import DecodedLunarYears, DecodedJieqiDates
from src.Calendar import CalendarType, CalendarDate, CalendarUtils
from src.Defines import Jieqi


@pytest.mark.slow
class TestCalendarType(unittest.TestCase):
  def test_calendar_type(self) -> None:
    self.assertIs(CalendarType.SOLAR, CalendarType.公历)
    self.assertIs(CalendarType.LUNAR, CalendarType.农历)
    self.assertIs(CalendarType.GANZHI, CalendarType.干支历)
    self.assertEqual(len(CalendarType), 3)


@pytest.mark.slow
class TestCalendarDate(unittest.TestCase):
  def test_solar_date(self) -> None:
    sd = CalendarDate(2024, 1, 1, CalendarType.SOLAR)
    self.assertEqual(sd.year, 2024)
    self.assertEqual(sd.month, 1)
    self.assertEqual(sd.day, 1)
    self.assertEqual(sd.date_type, CalendarType.SOLAR)

    self.assertEqual(sd, CalendarDate(2024, 1, 1, CalendarType.SOLAR))
    self.assertEqual(sd, sd)

    self.assertNotEqual(sd, CalendarDate(2023, 1, 1, CalendarType.SOLAR))
    self.assertNotEqual(sd, CalendarDate(2024, 2, 1, CalendarType.SOLAR))
    self.assertNotEqual(sd, CalendarDate(2024, 1, 30, CalendarType.SOLAR))
    self.assertNotEqual(sd, CalendarDate(2024, 1, 1, CalendarType.LUNAR))
    self.assertNotEqual(sd, CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.assertRaises(TypeError):
      self.assertNotEqual(sd, date(2024, 1, 1))
    with self.assertRaises(TypeError):
      self.assertNotEqual(sd, '2024-01-01')

    with self.assertRaises(AssertionError):
      CalendarDate('2024', 1, 1, CalendarType.SOLAR) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, '1', 1, CalendarType.SOLAR) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, 1, '1', CalendarType.SOLAR) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, 1, 1, 'SOLAR') # type: ignore
    with self.assertRaises(TypeError):
      CalendarDate(2024, 1, 1) # type: ignore # Missing argument.

    # Create invalid dates, no exception is expected to be raised, since `CalendarType` is just a thin wrapper.
    CalendarDate(2024, 13, 1, CalendarType.SOLAR) # Invalid month.
    CalendarDate(2024, 0, 1, CalendarType.SOLAR) # Invalid month.
    CalendarDate(2024, 1, 0, CalendarType.SOLAR) # Invalid day.
    CalendarDate(2024, 1, 32, CalendarType.SOLAR) # Invalid day.

  def test_lunar_date(self) -> None:
    ld = CalendarDate(2024, 1, 1, CalendarType.LUNAR)
    self.assertEqual(ld.year, 2024)
    self.assertEqual(ld.month, 1)
    self.assertEqual(ld.day, 1)
    self.assertEqual(ld.date_type, CalendarType.LUNAR)

    self.assertEqual(ld, CalendarDate(2024, 1, 1, CalendarType.LUNAR))
    self.assertEqual(ld, ld)

    self.assertNotEqual(ld, CalendarDate(2023, 1, 1, CalendarType.LUNAR))
    self.assertNotEqual(ld, CalendarDate(2024, 2, 1, CalendarType.LUNAR))
    self.assertNotEqual(ld, CalendarDate(2024, 1, 30, CalendarType.LUNAR))
    self.assertNotEqual(ld, CalendarDate(2024, 13, 29, CalendarType.LUNAR)) # Notice that there can be 13 lunar months in a lunar year.
    self.assertNotEqual(ld, CalendarDate(2024, 1, 1, CalendarType.SOLAR))
    self.assertNotEqual(ld, CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.assertRaises(TypeError):
      self.assertNotEqual(ld, date(2024, 1, 1))
    with self.assertRaises(TypeError):
      self.assertNotEqual(ld, '2024-01-01')

    with self.assertRaises(AssertionError):
      CalendarDate('2024', 1, 1, CalendarType.LUNAR) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, '1', 1, CalendarType.LUNAR) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, 1, '1', CalendarType.LUNAR) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, 1, 1, 'LUNAR') # type: ignore
    with self.assertRaises(TypeError):
      CalendarDate(2024, 1, 1) # type: ignore # Missing argument.

    # Create invalid dates, no exception is expected to be raised, since `CalendarType` is just a thin wrapper.
    CalendarDate(2024, 14, 1, CalendarType.LUNAR) # Invalid month.
    CalendarDate(2024, 0, 1, CalendarType.LUNAR) # Invalid month.
    CalendarDate(2024, 1, 31, CalendarType.LUNAR) # Invalid day.
    CalendarDate(2024, 1, 0, CalendarType.LUNAR) # Invalid day.

  def test_ganzhi_date(self) -> None:
    gzd = CalendarDate(2024, 1, 1, CalendarType.GANZHI)
    self.assertEqual(gzd.year, 2024)
    self.assertEqual(gzd.month, 1)
    self.assertEqual(gzd.day, 1)
    self.assertEqual(gzd.date_type, CalendarType.GANZHI)

    self.assertEqual(gzd, CalendarDate(2024, 1, 1, CalendarType.GANZHI))
    self.assertEqual(gzd, gzd)

    self.assertNotEqual(gzd, CalendarDate(2023, 1, 1, CalendarType.GANZHI))
    self.assertNotEqual(gzd, CalendarDate(2024, 2, 1, CalendarType.GANZHI))
    self.assertNotEqual(gzd, CalendarDate(2024, 1, 30, CalendarType.GANZHI))
    self.assertNotEqual(gzd, CalendarDate(2024, 1, 1, CalendarType.LUNAR))
    self.assertNotEqual(gzd, CalendarDate(2024, 1, 1, CalendarType.SOLAR))

    with self.assertRaises(TypeError):
      self.assertNotEqual(gzd, date(2024, 1, 1))
    with self.assertRaises(TypeError):
      self.assertNotEqual(gzd, '2024-01-01')

    with self.assertRaises(AssertionError):
      CalendarDate('2024', 1, 1, CalendarType.GANZHI) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, '1', 1, CalendarType.GANZHI) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, 1, '1', CalendarType.GANZHI) # type: ignore
    with self.assertRaises(AssertionError):
      CalendarDate(2024, 1, 1, 'GANZHI') # type: ignore
    with self.assertRaises(TypeError):
      CalendarDate(2024, 1, 1) # type: ignore # Missing argument.

    # Create invalid dates, no exception is expected to be raised, since `CalendarType` is just a thin wrapper.
    CalendarDate(2024, 13, 1, CalendarType.GANZHI) # Invalid month.
    CalendarDate(2024, 0, 1, CalendarType.GANZHI) # Invalid month.
    CalendarDate(2024, 1, 32, CalendarType.GANZHI) # Invalid day.
    CalendarDate(2024, 1, 0, CalendarType.GANZHI) # Invalid day.

  def test_date_cmp_operators(self) -> None:
    # Use solar dates to test date operators.
    random_date_list: list[date] = []
    for _ in range(256):
      random_date_list.append(date(random.randint(1, 9999), random.randint(1, 12), random.randint(1, 28)))

    for date1, date2 in product(random_date_list, random_date_list):
      c_date1: CalendarDate = CalendarDate(date1.year, date1.month, date1.day, CalendarType.SOLAR)
      c_date2: CalendarDate = CalendarDate(date2.year, date2.month, date2.day, CalendarType.SOLAR)
      
      if date1 < date2:
        self.assertTrue(c_date1 < c_date2)
      if date1 <= date2:
        self.assertTrue(c_date1 <= c_date2)
      if date1 > date2:
        self.assertTrue(c_date1 > c_date2)
      if date1 >= date2:
        self.assertTrue(c_date1 >= c_date2)
      if date1 == date2:
        self.assertTrue(c_date1 == c_date2)
      if date1 != date2:
        self.assertTrue(c_date1 != c_date2)

    cur_date: date = date(
      random.randint(1, 9999),
      random.randint(1, 12),
      random.randint(1, 28)
    )
    for _ in range(512):
      next_date: date = cur_date + timedelta(days=1)
      c_date1: CalendarDate = CalendarDate(cur_date.year, cur_date.month, cur_date.day, CalendarType.SOLAR)
      c_date2: CalendarDate = CalendarDate(next_date.year, next_date.month, next_date.day, CalendarType.SOLAR)

      self.assertTrue(c_date1 < c_date2)
      self.assertTrue(c_date1 <= c_date2)
      self.assertFalse(c_date1 > c_date2)
      self.assertFalse(c_date1 >= c_date2)
      self.assertFalse(c_date1 == c_date2)
      self.assertTrue(c_date1 != c_date2)

      self.assertTrue(c_date1 >= c_date1)
      self.assertTrue(c_date1 <= c_date1)
      self.assertFalse(c_date1 > c_date1)
      self.assertFalse(c_date1 < c_date1)
      self.assertTrue(c_date1 == c_date1)
      self.assertFalse(c_date1 != c_date1)

      cur_date = next_date

  def test_date_cmp_operators_negative(self) -> None:
    # As expected, only the dates of the same `CalendarType` can be compared.
    calendar_dates: list[CalendarDate] = [
      CalendarDate(2024, 1, 1, CalendarType.SOLAR),
      CalendarDate(2024, 1, 1, CalendarType.LUNAR),
      CalendarDate(2024, 1, 1, CalendarType.GANZHI),
    ]

    for d1, d2 in product(calendar_dates, calendar_dates):
      bool1: bool = d1 == d2
      bool2: bool = d1 != d2
      
      # Either bool1 or bool2 is True.
      self.assertTrue(bool1 or bool2)
      self.assertFalse(bool1 and bool2)

      self.assertEqual(d1 == d2, d2 == d1)
      self.assertEqual(d1 != d2, d2 != d1)

      # Following subtests need `d1` to be of the same `CalendarType` as `d2`.
      if d1.date_type == d2.date_type:
        continue
      with self.assertRaises(TypeError):
        d1 < d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 <= d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 > d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 >= d2 # type: ignore

    for d1, d2 in zip(calendar_dates, [date(2024, 1, 1)] * 3):
      with self.assertRaises(TypeError):
        d1 == d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 != d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 < d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 <= d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 > d2 # type: ignore
      with self.assertRaises(TypeError):
        d1 >= d2 # type: ignore
      with self.assertRaises(TypeError):
        d2 == d1 # type: ignore
      with self.assertRaises(TypeError):
        d2 != d1 # type: ignore
      with self.assertRaises(TypeError):
        d2 < d1 # type: ignore
      with self.assertRaises(TypeError):
        d2 <= d1 # type: ignore
      with self.assertRaises(TypeError):
        d2 > d1 # type: ignore
      with self.assertRaises(TypeError):
        d2 >= d1 # type: ignore

  def test_str_repr(self) -> None:
    random_date_list: list[CalendarDate] = []
    for _ in range(256):
      random_date_list.append(
        CalendarDate(
          random.randint(1902, 2099),
          random.randint(1, 12),
          random.randint(1, 28),
          random.choice(list(CalendarType))
        )
      )

    for d in random_date_list:
      self.assertEqual(str(d), d.__str__())
      self.assertEqual(repr(d), d.__repr__())
      self.assertEqual(str(d), str(d))
      self.assertEqual(repr(d), repr(d))
    
    for d1, d2 in product(random_date_list, random_date_list):
      if d1 == d2:
        self.assertEqual(str(d1), str(d2))
        self.assertEqual(repr(d1), repr(d2))
      if d1 != d2:
        self.assertNotEqual(str(d1), str(d2))
        self.assertNotEqual(repr(d1), repr(d2))    

  def test_malicious_writes(self) -> None:
    with self.subTest('Write to properties'):
      d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
      with self.assertRaises(AttributeError):
        d.year = 1999 # type: ignore
      with self.assertRaises(AttributeError):
        d.month = 2 # type: ignore
      with self.assertRaises(AttributeError):
        d.day = 10 # type: ignore
      with self.assertRaises(AttributeError):
        d.date_type = CalendarType.LUNAR # type: ignore

    with self.subTest('Write to underlying instance variables'):
      # Not really expect users to really write to the underlying instance variables though.
      d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
      d._year = 1999
      d._month = 2
      d._day = 10
      d._date_type = CalendarType.LUNAR
      self.assertEqual(d, CalendarDate(1999, 2, 10, CalendarType.LUNAR))
    
  def test_copy(self) -> None:
    with self.subTest('Test shallow copy'):
      d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
      d_copy = copy.copy(d)
      self.assertEqual(d, d_copy)
      self.assertIsNot(d, d_copy)

      d_copy._year += 1
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)

      d_copy._year -= 1
      self.assertEqual(d, d_copy)
      self.assertEqual(d_copy, d)

      d_copy._date_type = CalendarType.LUNAR
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)

    with self.subTest('Test deep copy'):
      d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
      d_copy = copy.deepcopy(d)
      self.assertEqual(d, d_copy)
      self.assertIsNot(d, d_copy)

      d_copy._year += 1
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)

      d_copy._year -= 1
      self.assertEqual(d, d_copy)
      self.assertEqual(d_copy, d)

      d_copy._date_type = CalendarType.LUNAR
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)

  def test_to_date(self) -> None:
    d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
    self.assertEqual(d.to_date(), date(2000, 1, 1))

    d = CalendarDate(1901, 1, 1, CalendarType.LUNAR)
    self.assertEqual(d.to_date(), date(1901, 2, 19))


@pytest.mark.slow
class TestCalendarUtils(unittest.TestCase):
  def test_calendar_utils_init(self) -> None:
    with self.assertRaises(NotImplementedError):
      CalendarUtils() # Only expect to use static methods of the class.

  def test_is_valid_solar_date(self) -> None:
    d: date = date(1902, 1, 1)
    while d < date(2099, 1, 1):
      solar_date: CalendarDate = CalendarDate(d.year, d.month, d.day, CalendarType.SOLAR)
      self.assertTrue(CalendarUtils.is_valid_solar_date(solar_date))
      self.assertFalse(CalendarUtils.is_valid_lunar_date(solar_date))
      self.assertFalse(CalendarUtils.is_valid_ganzhi_date(solar_date))
      d = d + timedelta(days=1)

    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2024, 1, 1, CalendarType.LUNAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2024, 1, 1, CalendarType.GANZHI)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(9999, 2, 29, CalendarType.SOLAR))) # Out of supported range.
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2023, 2, 29, CalendarType.SOLAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2023, 13, 29, CalendarType.SOLAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(1900, 2, 29, CalendarType.SOLAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2024, 2, 30, CalendarType.SOLAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2024, 4, 31, CalendarType.SOLAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2023, 0, 29, CalendarType.SOLAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(2023, 1, 32, CalendarType.SOLAR)))
    self.assertFalse(CalendarUtils.is_valid_solar_date(CalendarDate(0, 1, 15, CalendarType.SOLAR)))

  def test_is_valid_lunar_date(self) -> None:
    lunar_years_db: DecodedLunarYears = DecodedLunarYears()
    min_year: int = CalendarUtils.get_min_supported_date(CalendarType.LUNAR).year + 1
    max_year: int = CalendarUtils.get_max_supported_date(CalendarType.LUNAR).year - 1

    self.assertFalse(CalendarUtils.is_valid_lunar_date(CalendarDate(0, 1, 1, CalendarType.LUNAR))) # Out or supported range.
    self.assertFalse(CalendarUtils.is_valid_lunar_date(CalendarDate(9999, 1, 1, CalendarType.LUNAR))) # Out of supported range.

    for year in range(min_year, max_year + 1):
      info = lunar_years_db[year]

      for idx, count in enumerate(info['days_counts']):
        month = idx + 1

        for day in range(1, count + 1):
          lunar_date: CalendarDate = CalendarDate(year, month, day, CalendarType.LUNAR)
          self.assertFalse(CalendarUtils.is_valid_solar_date(lunar_date))
          self.assertTrue(CalendarUtils.is_valid_lunar_date(lunar_date))
          self.assertFalse(CalendarUtils.is_valid_ganzhi_date(lunar_date))

        self.assertFalse(CalendarUtils.is_valid_lunar_date(CalendarDate(year, month, count + 1, CalendarType.LUNAR)))

      self.assertFalse(CalendarUtils.is_valid_lunar_date(CalendarDate(year, len(info['days_counts']) + 1, 1, CalendarType.LUNAR)))

  def test_is_valid_ganzhi_date(self) -> None:
    def __run_test_in_ganzhi_year(year: int) -> None:
      days_counts: list[int] = CalendarUtils.days_counts_in_ganzhi_year(year)
      for idx, count in enumerate(days_counts):
        month: int = idx + 1
        for day in range(1, count + 1):
          ganzhi_date: CalendarDate = CalendarDate(year, month, day, CalendarType.GANZHI)
          self.assertFalse(CalendarUtils.is_valid_solar_date(ganzhi_date))
          self.assertFalse(CalendarUtils.is_valid_lunar_date(ganzhi_date))
          self.assertTrue(CalendarUtils.is_valid_ganzhi_date(ganzhi_date))
        self.assertFalse(CalendarUtils.is_valid_ganzhi_date(CalendarDate(year, month, count + 1, CalendarType.GANZHI)))
      self.assertFalse(CalendarUtils.is_valid_ganzhi_date(CalendarDate(year, 0, 1, CalendarType.GANZHI)))
      self.assertFalse(CalendarUtils.is_valid_ganzhi_date(CalendarDate(year, len(days_counts) + 1, 1, CalendarType.GANZHI)))

    min_year: int = CalendarUtils.get_min_supported_date(CalendarType.LUNAR).year + 1
    max_year: int = CalendarUtils.get_max_supported_date(CalendarType.LUNAR).year - 1
    for year in range(min_year, max_year + 1):
      __run_test_in_ganzhi_year(year)

    self.assertFalse(CalendarUtils.is_valid_ganzhi_date(CalendarDate(0, 1, 1, CalendarType.GANZHI))) # Out or supported range.
    self.assertFalse(CalendarUtils.is_valid_ganzhi_date(CalendarDate(9999, 1, 1, CalendarType.GANZHI))) # Out of supported range.


  def test_days_counts_in_ganzhi_year(self) -> None:
    min_year: int = CalendarUtils.get_min_supported_date(CalendarType.GANZHI).year
    max_year: int = CalendarUtils.get_max_supported_date(CalendarType.GANZHI).year

    # Test negative cases first.
    with self.assertRaises(AssertionError):
      CalendarUtils.days_counts_in_ganzhi_year(-1)
    with self.assertRaises(AssertionError):
      CalendarUtils.days_counts_in_ganzhi_year(min_year - 1)
    with self.assertRaises(AssertionError):
      CalendarUtils.days_counts_in_ganzhi_year(max_year + 1)

    # Test edge cases.
    days_counts = CalendarUtils.days_counts_in_ganzhi_year(min_year)
    for count in days_counts:
      self.assertTrue(29 <= count <= 32) 
    days_counts = CalendarUtils.days_counts_in_ganzhi_year(max_year)
    for count in days_counts:
      self.assertTrue(29 <= count <= 32) 

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
      dates.append(CalendarUtils.jieqi_dates_db.get(year + 1, Jieqi.立春)) # Start of the next ganzhi year.

      days_counts: list[int] = CalendarUtils.days_counts_in_ganzhi_year(year)
      for idx, (start_date, next_start_date) in enumerate(zip(dates[:-1], dates[1:])):
        days_in_this_month: int = days_counts[idx]
        self.assertEqual(days_in_this_month, (next_start_date - start_date).days)
      

  def test_is_valid(self) -> None:
    for date_type in [CalendarType.SOLAR, CalendarType.LUNAR, CalendarType.GANZHI]:
      min_date: CalendarDate = CalendarUtils.get_min_supported_date(date_type)
      max_date: CalendarDate = CalendarUtils.get_max_supported_date(date_type)

      self.assertTrue(CalendarUtils.is_valid(min_date))
      self.assertTrue(CalendarUtils.is_valid(max_date))
      self.assertFalse(CalendarUtils.is_valid(CalendarDate(0, 1, 1, date_type))) # Out or supported range.
      self.assertFalse(CalendarUtils.is_valid(CalendarDate(9999, 1, 1, date_type))) # Out of supported range.

    class __DuckTypeClass:
      def __init__(self, anything: Any) -> None:
        self.date_type = anything
    self.assertFalse(CalendarUtils.is_valid(__DuckTypeClass(0))) # type: ignore # Test duck type.

  @staticmethod
  def __solar_date_gen(d: CalendarDate):
    assert d.date_type == CalendarType.SOLAR
    _d: date = date(d.year, d.month, d.day)
    while True:
      yield CalendarDate(_d.year, _d.month, _d.day, CalendarType.SOLAR)
      _d = _d + timedelta(days=1)

  @staticmethod
  def __lunar_date_gen(d: CalendarDate):
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

  @staticmethod
  def __ganzhi_date_gen(d: CalendarDate):
    assert d.date_type == CalendarType.GANZHI
    _y, _m, _d = d.year, d.month, d.day
    _month_lengths: list[int] = CalendarUtils.days_counts_in_ganzhi_year(_y)
    while True:
      yield CalendarDate(_y, _m, _d, CalendarType.GANZHI)
      _d += 1
      if _d > _month_lengths[_m - 1]:
        _d = 1
        _m += 1
        if _m > 12:
          _m = 1
          _y += 1
          _month_lengths = CalendarUtils.days_counts_in_ganzhi_year(_y)
          
  def test_lunar_to_solar(self) -> None:
    min_lunar_date: CalendarDate = CalendarUtils.get_min_supported_date(CalendarType.LUNAR)
    max_lunar_date: CalendarDate = CalendarUtils.get_max_supported_date(CalendarType.LUNAR)

    self.assertEqual(CalendarUtils.lunar_to_solar(min_lunar_date),
                     CalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    self.assertEqual(CalendarUtils.lunar_to_solar(max_lunar_date),
                     CalendarUtils.get_max_supported_date(CalendarType.SOLAR))

    solar_date_gen = self.__solar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    lunar_date_gen = self.__lunar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.LUNAR))

    while True:
      solar_date = next(solar_date_gen)
      lunar_date = next(lunar_date_gen)
      self.assertEqual(solar_date, CalendarUtils.lunar_to_solar(lunar_date))

      if lunar_date == max_lunar_date:
        self.assertEqual(solar_date, CalendarUtils.get_max_supported_date(CalendarType.SOLAR))
        break

  def test_solar_to_lunar(self) -> None:
    min_solar_date: CalendarDate = CalendarUtils.get_min_supported_date(CalendarType.SOLAR)
    max_solar_date: CalendarDate = CalendarUtils.get_max_supported_date(CalendarType.SOLAR)

    self.assertEqual(CalendarUtils.solar_to_lunar(min_solar_date),
                     CalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    self.assertEqual(CalendarUtils.solar_to_lunar(max_solar_date),
                     CalendarUtils.get_max_supported_date(CalendarType.LUNAR))

    solar_date_gen = self.__solar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    lunar_date_gen = self.__lunar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.LUNAR))

    while True:
      solar_date = next(solar_date_gen)
      lunar_date = next(lunar_date_gen)
      self.assertEqual(lunar_date, CalendarUtils.solar_to_lunar(solar_date))

      if solar_date == max_solar_date:
        self.assertEqual(lunar_date, CalendarUtils.get_max_supported_date(CalendarType.LUNAR))
        break

  def test_ganzhi_to_solar(self) -> None:
    min_ganzhi_date: CalendarDate = CalendarUtils.get_min_supported_date(CalendarType.GANZHI)
    max_ganzhi_date: CalendarDate = CalendarUtils.get_max_supported_date(CalendarType.GANZHI)

    self.assertEqual(CalendarUtils.ganzhi_to_solar(min_ganzhi_date),
                     CalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    self.assertEqual(CalendarUtils.ganzhi_to_solar(max_ganzhi_date),
                     CalendarUtils.get_max_supported_date(CalendarType.SOLAR))
    
    solar_date_gen = self.__solar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(CalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    while True:
      solar_date = next(solar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)
      self.assertEqual(solar_date, CalendarUtils.ganzhi_to_solar(ganzhi_date))

      if ganzhi_date == max_ganzhi_date:
        self.assertEqual(solar_date, CalendarUtils.get_max_supported_date(CalendarType.SOLAR))
        break

  def test_solar_to_ganzhi(self) -> None:
    min_solar_date: CalendarDate = CalendarUtils.get_min_supported_date(CalendarType.SOLAR)
    max_solar_date: CalendarDate = CalendarUtils.get_max_supported_date(CalendarType.SOLAR)

    self.assertEqual(CalendarUtils.solar_to_ganzhi(min_solar_date),
                     CalendarUtils.get_min_supported_date(CalendarType.GANZHI))
    self.assertEqual(CalendarUtils.solar_to_ganzhi(max_solar_date),
                     CalendarUtils.get_max_supported_date(CalendarType.GANZHI))

    solar_date_gen = self.__solar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(CalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    while True:
      solar_date = next(solar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)
      self.assertEqual(ganzhi_date, CalendarUtils.solar_to_ganzhi(solar_date))

      if solar_date == max_solar_date:
        self.assertEqual(ganzhi_date, CalendarUtils.get_max_supported_date(CalendarType.GANZHI))
        break

  def test_lunar_to_ganzhi(self) -> None:
    min_lunar_date: CalendarDate = CalendarUtils.get_min_supported_date(CalendarType.LUNAR)
    max_lunar_date: CalendarDate = CalendarUtils.get_max_supported_date(CalendarType.LUNAR)

    self.assertEqual(CalendarUtils.lunar_to_ganzhi(min_lunar_date),
                     CalendarUtils.get_min_supported_date(CalendarType.GANZHI))
    self.assertEqual(CalendarUtils.lunar_to_ganzhi(max_lunar_date),
                     CalendarUtils.get_max_supported_date(CalendarType.GANZHI))

    lunar_date_gen = self.__lunar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(CalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    while True:
      lunar_date = next(lunar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)
      self.assertEqual(ganzhi_date, CalendarUtils.lunar_to_ganzhi(lunar_date))

      if lunar_date == max_lunar_date:
        self.assertEqual(ganzhi_date, CalendarUtils.get_max_supported_date(CalendarType.GANZHI))
        break

  def test_ganzhi_to_lunar(self) -> None:
    min_ganzhi_date: CalendarDate = CalendarUtils.get_min_supported_date(CalendarType.GANZHI)
    max_ganzhi_date: CalendarDate = CalendarUtils.get_max_supported_date(CalendarType.GANZHI)

    self.assertEqual(CalendarUtils.ganzhi_to_lunar(min_ganzhi_date),
                     CalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    self.assertEqual(CalendarUtils.ganzhi_to_lunar(max_ganzhi_date),
                     CalendarUtils.get_max_supported_date(CalendarType.LUNAR))

    ganzhi_date_gen = self.__ganzhi_date_gen(CalendarUtils.get_min_supported_date(CalendarType.GANZHI))
    lunar_date_gen = self.__lunar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.LUNAR))

    while True:
      ganzhi_date = next(ganzhi_date_gen)
      lunar_date = next(lunar_date_gen)
      self.assertEqual(lunar_date, CalendarUtils.ganzhi_to_lunar(ganzhi_date))

      if ganzhi_date == max_ganzhi_date:
        self.assertEqual(lunar_date, CalendarUtils.get_max_supported_date(CalendarType.LUNAR))
        break

  def test_complex_date_conversions(self) -> None:
    solar_date_gen = self.__solar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    lunar_date_gen = self.__lunar_date_gen(CalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(CalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    for _ in range(4096):
      solar_date = next(solar_date_gen)
      lunar_date = next(lunar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)

      with self.subTest('ganzhi'):
        _solar_date = CalendarUtils.ganzhi_to_solar(ganzhi_date)
        _lunar_date = CalendarUtils.ganzhi_to_lunar(ganzhi_date)

        self.assertEqual(solar_date, _solar_date)
        self.assertEqual(lunar_date, _lunar_date)
        self.assertEqual(ganzhi_date, CalendarUtils.solar_to_ganzhi(_solar_date))
        self.assertEqual(ganzhi_date, CalendarUtils.lunar_to_ganzhi(_lunar_date))

      with self.subTest('solar'):
        _lunar_date = CalendarUtils.solar_to_lunar(solar_date)
        _ganzhi_date = CalendarUtils.solar_to_ganzhi(solar_date)

        self.assertEqual(lunar_date, _lunar_date)
        self.assertEqual(ganzhi_date, _ganzhi_date)
        self.assertEqual(solar_date, CalendarUtils.lunar_to_solar(_lunar_date))
        self.assertEqual(solar_date, CalendarUtils.ganzhi_to_solar(_ganzhi_date))

      with self.subTest('lunar'):
        _solar_date = CalendarUtils.lunar_to_solar(lunar_date)
        _ganzhi_date = CalendarUtils.lunar_to_ganzhi(lunar_date)

        self.assertEqual(solar_date, _solar_date)
        self.assertEqual(ganzhi_date, _ganzhi_date)
        self.assertEqual(lunar_date, CalendarUtils.solar_to_lunar(_solar_date))
        self.assertEqual(lunar_date, CalendarUtils.ganzhi_to_lunar(_ganzhi_date))

  def test_date_conversions_negative(self) -> None:
    with self.subTest('ganzhi_to_lunar negative'):
      with self.assertRaises(AssertionError):
        CalendarUtils.ganzhi_to_lunar(CalendarDate(1, 1, 1, CalendarType.GANZHI))
      with self.assertRaises(AssertionError):
        CalendarUtils.ganzhi_to_lunar(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

    with self.subTest('lunar_to_ganzhi negative'):
      with self.assertRaises(AssertionError):
        CalendarUtils.lunar_to_ganzhi(CalendarDate(1, 1, 1, CalendarType.LUNAR))
      with self.assertRaises(AssertionError):
        CalendarUtils.lunar_to_ganzhi(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

    with self.subTest('solar_to_lunar negative'):
      with self.assertRaises(AssertionError):
        CalendarUtils.solar_to_lunar(CalendarDate(1, 1, 1, CalendarType.SOLAR))
      with self.assertRaises(AssertionError):
        CalendarUtils.solar_to_lunar(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.subTest('lunar_to_solar negative'):
      with self.assertRaises(AssertionError):
        CalendarUtils.lunar_to_solar(CalendarDate(1, 1, 1, CalendarType.LUNAR))
      with self.assertRaises(AssertionError):
        CalendarUtils.lunar_to_solar(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.subTest('solar_to_ganzhi negative'):
      with self.assertRaises(AssertionError):
        CalendarUtils.solar_to_ganzhi(CalendarDate(1, 1, 1, CalendarType.SOLAR))
      with self.assertRaises(AssertionError):
        CalendarUtils.solar_to_ganzhi(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.subTest('ganzhi_to_solar negative'):
      with self.assertRaises(AssertionError):
        CalendarUtils.ganzhi_to_solar(CalendarDate(1, 1, 1, CalendarType.GANZHI))
      with self.assertRaises(AssertionError):
        CalendarUtils.ganzhi_to_solar(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

  def test_to_solar(self) -> None:
    with self.subTest('Positive cases'):
      d: date = date(2023, 5, 8)
      solar_date: CalendarDate = CalendarUtils.to_solar(d)
      self.assertEqual(solar_date, CalendarDate(2023, 5, 8, CalendarType.SOLAR))
      self.assertEqual(solar_date, CalendarUtils.to_solar(d))
      self.assertEqual(solar_date, CalendarUtils.to_solar(solar_date))
      self.assertEqual(solar_date, CalendarUtils.to_solar(CalendarUtils.solar_to_lunar(solar_date)))
      self.assertEqual(solar_date, CalendarUtils.to_solar(CalendarUtils.solar_to_ganzhi(solar_date)))
    
    with self.subTest('Negative cases'):
      with self.assertRaises(AssertionError):
        CalendarUtils.to_solar(CalendarDate(9999, 1, 1, CalendarType.SOLAR)) # Invalid date
      with self.assertRaises(AssertionError):
        CalendarUtils.to_solar('2024-01-01') # type: ignore # Invalid type

  def test_to_lunar(self) -> None:
    with self.subTest('Positive cases'):
      d: date = date(2023, 5, 8)
      lunar_date: CalendarDate = CalendarUtils.to_lunar(d)
      self.assertEqual(lunar_date, CalendarUtils.solar_to_lunar(CalendarDate(2023, 5, 8, CalendarType.SOLAR)))
      self.assertEqual(lunar_date, CalendarUtils.to_lunar(d))
      self.assertEqual(lunar_date, CalendarUtils.to_lunar(lunar_date))
      self.assertEqual(lunar_date, CalendarUtils.to_lunar(CalendarUtils.lunar_to_solar(lunar_date)))
      self.assertEqual(lunar_date, CalendarUtils.to_lunar(CalendarUtils.lunar_to_ganzhi(lunar_date)))
    
    with self.subTest('Negative cases'):
      with self.assertRaises(AssertionError):
        CalendarUtils.to_lunar(CalendarDate(9999, 1, 1, CalendarType.LUNAR)) # Invalid date
      with self.assertRaises(AssertionError):
        CalendarUtils.to_lunar('2024-01-01') # type: ignore # Invalid type

  def test_to_ganzhi(self) -> None:
    with self.subTest('Positive cases'):
      d: date = date(2023, 5, 8)
      ganzhi_date: CalendarDate = CalendarUtils.to_ganzhi(d)
      self.assertEqual(ganzhi_date, CalendarUtils.solar_to_ganzhi(CalendarDate(2023, 5, 8, CalendarType.SOLAR)))
      self.assertEqual(ganzhi_date, CalendarUtils.to_ganzhi(d))
      self.assertEqual(ganzhi_date, CalendarUtils.to_ganzhi(ganzhi_date))
      self.assertEqual(ganzhi_date, CalendarUtils.to_ganzhi(CalendarUtils.ganzhi_to_solar(ganzhi_date)))
      self.assertEqual(ganzhi_date, CalendarUtils.to_ganzhi(CalendarUtils.ganzhi_to_lunar(ganzhi_date)))
    
    with self.subTest('Negative cases'):
      with self.assertRaises(AssertionError):
        CalendarUtils.to_ganzhi(CalendarDate(9999, 1, 1, CalendarType.GANZHI)) # Invalid date
      with self.assertRaises(AssertionError):
        CalendarUtils.to_ganzhi('2024-01-01') # type: ignore # Invalid type
