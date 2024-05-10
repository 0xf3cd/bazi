# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_calendar_defines.py

import pytest
import unittest
import random
import copy

from datetime import date, timedelta
from itertools import product

from src.Calendar import CalendarType, CalendarDate


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
      c_date1 = CalendarDate(cur_date.year, cur_date.month, cur_date.day, CalendarType.SOLAR)
      c_date2 = CalendarDate(next_date.year, next_date.month, next_date.day, CalendarType.SOLAR)

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

      self.assertRaises(TypeError, lambda : d1 < d2)
      self.assertRaises(TypeError, lambda : d1 <= d2)
      self.assertRaises(TypeError, lambda : d1 > d2)
      self.assertRaises(TypeError, lambda : d1 >= d2)

    for d1, dt in zip(calendar_dates, [date(2024, 1, 1)] * 3):
      self.assertRaises(TypeError, lambda : d1 == dt)
      self.assertRaises(TypeError, lambda : d1 != dt)
      self.assertRaises(TypeError, lambda : d1 < dt)
      self.assertRaises(TypeError, lambda : d1 <= dt)
      self.assertRaises(TypeError, lambda : d1 > dt)
      self.assertRaises(TypeError, lambda : d1 >= dt)

      self.assertRaises(TypeError, lambda : dt == d1)
      self.assertRaises(TypeError, lambda : dt != d1)
      self.assertRaises(TypeError, lambda : dt < d1)
      self.assertRaises(TypeError, lambda : dt <= d1)
      self.assertRaises(TypeError, lambda : dt > d1)
      self.assertRaises(TypeError, lambda : dt >= d1)

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
      d._year = 1999 # type: ignore
      d._month = 2 # type: ignore
      d._day = 10 # type: ignore
      d._date_type = CalendarType.LUNAR # type: ignore
      self.assertEqual(d, CalendarDate(1999, 2, 10, CalendarType.LUNAR))
    
  def test_copy(self) -> None:
    with self.subTest('Test shallow copy'):
      d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
      d_copy = copy.copy(d)
      self.assertEqual(d, d_copy)
      self.assertIsNot(d, d_copy)

      d_copy._year += 1 # type: ignore
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)

      d_copy._year -= 1 # type: ignore
      self.assertEqual(d, d_copy)
      self.assertEqual(d_copy, d)

      d_copy._date_type = CalendarType.LUNAR # type: ignore
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)

    with self.subTest('Test deep copy'):
      d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
      d_copy = copy.deepcopy(d)
      self.assertEqual(d, d_copy)
      self.assertIsNot(d, d_copy)

      d_copy._year += 1 # type: ignore
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)

      d_copy._year -= 1 # type: ignore
      self.assertEqual(d, d_copy)
      self.assertEqual(d_copy, d)

      d_copy._date_type = CalendarType.LUNAR # type: ignore
      self.assertNotEqual(d, d_copy)
      self.assertNotEqual(d_copy, d)
