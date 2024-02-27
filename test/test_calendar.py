# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_calendar.py

import unittest
import random
from datetime import date, timedelta
from itertools import product

from bazi.hkodata import DecodedLunarYears, DecodedJieqiDates
from bazi import (
  Jieqi, CalendarType, CalendarUtils, CalendarDate
)

class TestCalendarType(unittest.TestCase):
  def test_calendar_type(self) -> None:
    self.assertIs(CalendarType.SOLAR, CalendarType.公历)
    self.assertIs(CalendarType.LUNAR, CalendarType.农历)
    self.assertIs(CalendarType.GANZHI, CalendarType.干支历)
    self.assertEqual(len(CalendarType), 3)


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

    with self.assertRaises(TypeError):
      self.assertNotEqual(sd, CalendarDate(2024, 1, 1, CalendarType.LUNAR))
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
    
    with self.assertRaises(TypeError):
      self.assertNotEqual(ld, CalendarDate(2024, 1, 1, CalendarType.SOLAR))
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

    with self.assertRaises(TypeError):
      self.assertNotEqual(gzd, CalendarDate(2024, 1, 1, CalendarType.LUNAR))
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
    for _ in range(512):
      y1, m1, d1 = random.randint(1, 9999), random.randint(1, 12), random.randint(1, 28)
      y2, m2, d2 = random.randint(1, 9999), random.randint(1, 12), random.randint(1, 28)
      date1: date = date(y1, m1, d1)
      date2: date = date(y2, m2, d2)
      c_date1: CalendarDate = CalendarDate(y1, m1, d1, CalendarType.SOLAR)
      c_date2: CalendarDate = CalendarDate(y2, m2, d2, CalendarType.SOLAR)
      
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
      if d1.date_type == d2.date_type:
        continue
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
    # TODO: Implement me!
    pass

  def test_is_valid(self) -> None:
    # TODO: Implement me!
    pass

  def test_supported_range(self) -> None:
    # TODO: Implement me!
    pass
