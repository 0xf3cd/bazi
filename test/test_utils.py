# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_utils.py

import unittest
from datetime import date, datetime, timedelta
from bazi import get_day_ganzhi, CalendarUtils, Ganzhi

class TestUtils(unittest.TestCase):
  def test_get_day_ganzhi_basic(self) -> None:
    with self.subTest('Basic'):
      d: date = date(2024, 3, 1)
      self.assertEqual(get_day_ganzhi(d), get_day_ganzhi(CalendarUtils.to_solar(d)))

      dt: datetime = datetime(2024, 3, 1, 15, 34, 6)
      self.assertEqual(get_day_ganzhi(d), get_day_ganzhi(dt)) # `get_day_ganzhi` also takes `datetime` objects.

    with self.subTest('Correctness'):
      d: date = date(2024, 3, 1)
      self.assertEqual(get_day_ganzhi(d), Ganzhi.from_str('甲子'))
      self.assertEqual(get_day_ganzhi(d + timedelta(days=1)), Ganzhi.from_str('乙丑'))
      self.assertEqual(get_day_ganzhi(d - timedelta(days=1)), Ganzhi.from_str('癸亥'))

      self.assertEqual(get_day_ganzhi(date(1914, 2, 14)), Ganzhi.from_str('辛未'))
      self.assertEqual(get_day_ganzhi(date(1933, 11, 1)), Ganzhi.from_str('辛未'))
      self.assertEqual(get_day_ganzhi(date(1958, 6, 29)), Ganzhi.from_str('丁丑'))
      self.assertEqual(get_day_ganzhi(date(1964, 1, 19)), Ganzhi.from_str('丁卯'))
      self.assertEqual(get_day_ganzhi(date(1984, 5, 31)), Ganzhi.from_str('乙丑'))
      self.assertEqual(get_day_ganzhi(date(1997, 1, 30)), Ganzhi.from_str('壬申'))
      self.assertEqual(get_day_ganzhi(date(2003, 7, 12)), Ganzhi.from_str('丙戌'))

      for offset in range(-2000, 2000):
        d: date = date(2024, 3, 1) + timedelta(days=offset)
        self.assertEqual(get_day_ganzhi(d), Ganzhi.list_sexagenary_cycle()[offset % 60])

  def test_get_day_ganzhi_advanced(self) -> None:
    for d, ganzhi in [
      (CalendarUtils.to_lunar(date(2024, 3, 1)), Ganzhi.from_str('甲子')),
      (CalendarUtils.to_ganzhi(date(2024, 3, 1)), Ganzhi.from_str('甲子')),
      (CalendarUtils.to_lunar(date(1933, 11, 1)), Ganzhi.from_str('辛未')),
      (CalendarUtils.to_ganzhi(date(1933, 11, 1)), Ganzhi.from_str('辛未')),
      (CalendarUtils.to_lunar(date(1997, 1, 30)), Ganzhi.from_str('壬申')),
      (CalendarUtils.to_ganzhi(date(1997, 1, 30)), Ganzhi.from_str('壬申')),
    ]:
      self.assertEqual(get_day_ganzhi(d), ganzhi)
