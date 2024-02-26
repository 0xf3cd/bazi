# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_calendar.py

import unittest
from datetime import date, datetime
from bazi import (
  Ganzhi, CalendarType, CalendarUtils, SolarDate, LunarDate, GanzhiDate
)

class TestCalendarType(unittest.TestCase):
  def test_calendar_type(self) -> None:
    self.assertIs(CalendarType.SOLAR, CalendarType.公历)
    self.assertIs(CalendarType.LUNAR, CalendarType.农历)
    self.assertIs(CalendarType.GANZHI, CalendarType.干支历)
    self.assertEqual(len(CalendarType), 3)


class TestCalendarDates(unittest.TestCase):
  def test_solar_date(self) -> None:
    sd = SolarDate(2024, 1, 1)
    self.assertEqual(sd.year, 2024)
    self.assertEqual(sd.month, 1)
    self.assertEqual(sd.day, 1)

    self.assertEqual(date(2024, 1, 1), sd.to_date())
    self.assertEqual(sd, SolarDate.from_date(date(2024, 1, 1)))
    self.assertEqual(sd, SolarDate.from_date(sd.to_date()))
    self.assertEqual(sd, date(2024, 1, 1))
    self.assertEqual(sd, sd.to_date())
    self.assertEqual(date(2024, 1, 1), sd)
    self.assertEqual(sd, datetime(2024, 1, 1)) # Attention: datetime is a subclass of date. So `__eq__` returns True.
    self.assertEqual(sd, datetime(2024, 1, 1, 13, 56, 6)) # Attention: datetime is a subclass of date. So `__eq__` returns True.

    self.assertNotEqual(sd, SolarDate(2023, 1, 1))
    self.assertNotEqual(sd, date(2023, 1, 1))
    self.assertNotEqual(sd, (2023, 1, 1))
    self.assertNotEqual(sd, (2024, 1, 1))
    self.assertNotEqual(sd, '2024-01-01')

    with self.assertRaises(AssertionError):
      SolarDate('2024', '12', '1') # type: ignore
    with self.assertRaises(AssertionError):
      SolarDate(2024, 13, 1)
    with self.assertRaises(AssertionError):
      SolarDate(2024, 1, 32)
    with self.assertRaises(AssertionError):
      SolarDate(2024, 1, 0)
    with self.assertRaises(TypeError):
      SolarDate('2024-01-01') # type: ignore

  def test_lunar_date(self) -> None:
    ld = LunarDate(2024, 1, 1, False, Ganzhi.from_str('甲辰'))
    self.assertEqual(ld.year, 2024)
    self.assertEqual(ld.month, 1)
    self.assertEqual(ld.day, 1)
    self.assertEqual(ld.is_leap_month, False)
    self.assertEqual(ld.year_ganzhi, Ganzhi.from_str('甲辰'))
    self.assertEqual(ld, ld)
    self.assertEqual(ld, LunarDate(2024, 1, 1, False, Ganzhi.from_str('甲辰')))

    self.assertNotEqual(ld, LunarDate(2001, 1, 1, False, Ganzhi.from_str('辛巳')))
    self.assertNotEqual(ld, LunarDate(2024, 1, 1, True, Ganzhi.from_str('甲辰'))) # Fake data. First lunar month is not a leap month.
    self.assertNotEqual(ld, LunarDate(2024, 1, 1, False, Ganzhi.from_str('甲子'))) # Fake data. Ganzhi for this year is not "甲子".
    self.assertNotEqual(ld, SolarDate(2024, 1, 1))
    self.assertNotEqual(ld, datetime(2024, 1, 1))
    self.assertNotEqual(ld, '2024-01-01')

    with self.assertRaises(TypeError):
      LunarDate(2024, 1, 1, False) # type: ignore # Missing Ganzhi
    with self.assertRaises(AssertionError):
      LunarDate(2024, 1, 1, False, '甲辰') # type: ignore # Wrong Ganzhi
    with self.assertRaises(AssertionError):
      LunarDate('2024', '1', '1', False, Ganzhi.from_str('甲辰')) # type: ignore # Wrong Ganzhi
    with self.assertRaises(AssertionError):
      LunarDate(2024, 1, 31, False, Ganzhi.from_str('甲辰')) # Wrong day. A lunar month can contain 30 days at most.
    with self.assertRaises(AssertionError):
      LunarDate(2024, 1, 0, False, Ganzhi.from_str('甲辰')) # Wrong day.
    with self.assertRaises(AssertionError):
      LunarDate(2024, 0, 1, False, Ganzhi.from_str('甲辰')) # Wrong month.
    with self.assertRaises(AssertionError):
      LunarDate(2024, 13, 1, False, Ganzhi.from_str('甲辰')) # Wrong month.

  def test_ganzhi_date(self) -> None:
    # Use fake data to test `GanzhiDate`.
    sexagenary_cycle = Ganzhi.list_sexagenary_cycle()
    three_ganzhis = sexagenary_cycle[:3]

    gzd = GanzhiDate(2024, 1, 1, *three_ganzhis)
    self.assertEqual(gzd.year, 2024)
    self.assertEqual(gzd.month, 1)
    self.assertEqual(gzd.day, 1)
    self.assertEqual(gzd.year_ganzhi, three_ganzhis[0])
    self.assertEqual(gzd.month_ganzhi, three_ganzhis[1])
    self.assertEqual(gzd.day_ganzhi, three_ganzhis[2])
    self.assertEqual(gzd, gzd)
    self.assertEqual(gzd, GanzhiDate(2024, 1, 1, *three_ganzhis))

    same_gzd = GanzhiDate(2024, 1, 1, *three_ganzhis)
    self.assertEqual(gzd, same_gzd)
    
    self.assertNotEqual(gzd, GanzhiDate(2001, 1, 1, *three_ganzhis))
    self.assertNotEqual(gzd, GanzhiDate(2024, 1, 1, sexagenary_cycle[0], sexagenary_cycle[1], sexagenary_cycle[3]))
    self.assertNotEqual(gzd, GanzhiDate(2024, 1, 1, sexagenary_cycle[0], sexagenary_cycle[3], sexagenary_cycle[2]))
    self.assertNotEqual(gzd, GanzhiDate(2024, 1, 1, sexagenary_cycle[3], sexagenary_cycle[1], sexagenary_cycle[2]))
    self.assertNotEqual(gzd, date(2024, 1, 1))
    self.assertNotEqual(gzd, datetime(2024, 1, 1))
    self.assertNotEqual(gzd, '2024-01-01')

    with self.assertRaises(TypeError):
      GanzhiDate(2024, 1, 1, sexagenary_cycle[0], sexagenary_cycle[1]) # type: ignore # Missing argument
    with self.assertRaises(AssertionError):
      GanzhiDate(2024, 1, 1, '甲辰', '甲辰', '甲辰') # type: ignore # Wrong ganzhi type
    with self.assertRaises(AssertionError):
      GanzhiDate(2024, 0, 1, *three_ganzhis) # Wrong month.
    with self.assertRaises(AssertionError):
      GanzhiDate(2024, 13, 1, *three_ganzhis) # Wrong month.

class TestCalendarUtils(unittest.TestCase):
  def test_calendar_utils_init(self) -> None:
    with self.assertRaises(NotImplementedError):
      CalendarUtils() # Only expect to use static methods of the class.
