# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_hkodata_calendar_utils.py

import pytest
import unittest

from datetime import date, datetime, timedelta
from typing import Any

from src.Calendar import CalendarType, CalendarDate, HkoDataCalendarUtils
from src.Calendar.HkoData import DecodedLunarYears, DecodedJieqiDates
from src.Defines import Jieqi

@pytest.mark.slow
class TestHkoDataCalendarUtils(unittest.TestCase):
  def test_calendar_utils_init(self) -> None:
    with self.assertRaises(NotImplementedError):
      HkoDataCalendarUtils() # Only expect to use static methods of the class.

  def test_is_valid_solar_date(self) -> None:
    d: date = date(1902, 1, 1)
    while d < date(2099, 1, 1):
      solar_date: CalendarDate = CalendarDate(d.year, d.month, d.day, CalendarType.SOLAR)
      self.assertTrue(HkoDataCalendarUtils.is_valid_solar_date(solar_date))
      self.assertFalse(HkoDataCalendarUtils.is_valid_lunar_date(solar_date))
      self.assertFalse(HkoDataCalendarUtils.is_valid_ganzhi_date(solar_date))
      d = d + timedelta(days=1)

    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2024, 1, 1, CalendarType.LUNAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2024, 1, 1, CalendarType.GANZHI)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(9999, 2, 29, CalendarType.SOLAR))) # Out of supported range.
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2023, 2, 29, CalendarType.SOLAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2023, 13, 29, CalendarType.SOLAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(1900, 2, 29, CalendarType.SOLAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2024, 2, 30, CalendarType.SOLAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2024, 4, 31, CalendarType.SOLAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2023, 0, 29, CalendarType.SOLAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(2023, 1, 32, CalendarType.SOLAR)))
    self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(CalendarDate(0, 1, 15, CalendarType.SOLAR)))

  def test_is_valid_lunar_date(self) -> None:
    lunar_years_db: DecodedLunarYears = DecodedLunarYears()
    min_year: int = HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR).year + 1
    max_year: int = HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR).year - 1

    self.assertFalse(HkoDataCalendarUtils.is_valid_lunar_date(CalendarDate(0, 1, 1, CalendarType.LUNAR))) # Out or supported range.
    self.assertFalse(HkoDataCalendarUtils.is_valid_lunar_date(CalendarDate(9999, 1, 1, CalendarType.LUNAR))) # Out of supported range.

    for year in range(min_year, max_year + 1):
      info = lunar_years_db[year]

      for idx, count in enumerate(info['days_counts']):
        month = idx + 1

        for day in range(1, count + 1):
          lunar_date: CalendarDate = CalendarDate(year, month, day, CalendarType.LUNAR)
          self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(lunar_date))
          self.assertTrue(HkoDataCalendarUtils.is_valid_lunar_date(lunar_date))
          self.assertFalse(HkoDataCalendarUtils.is_valid_ganzhi_date(lunar_date))

        self.assertFalse(HkoDataCalendarUtils.is_valid_lunar_date(CalendarDate(year, month, count + 1, CalendarType.LUNAR)))

      self.assertFalse(HkoDataCalendarUtils.is_valid_lunar_date(CalendarDate(year, len(info['days_counts']) + 1, 1, CalendarType.LUNAR)))

  def test_is_valid_ganzhi_date(self) -> None:
    def __run_test_in_ganzhi_year(year: int) -> None:
      days_counts: list[int] = HkoDataCalendarUtils.days_counts_in_ganzhi_year(year)
      for idx, count in enumerate(days_counts):
        month: int = idx + 1
        for day in range(1, count + 1):
          ganzhi_date: CalendarDate = CalendarDate(year, month, day, CalendarType.GANZHI)
          self.assertFalse(HkoDataCalendarUtils.is_valid_solar_date(ganzhi_date))
          self.assertFalse(HkoDataCalendarUtils.is_valid_lunar_date(ganzhi_date))
          self.assertTrue(HkoDataCalendarUtils.is_valid_ganzhi_date(ganzhi_date))
        self.assertFalse(HkoDataCalendarUtils.is_valid_ganzhi_date(CalendarDate(year, month, count + 1, CalendarType.GANZHI)))
      self.assertFalse(HkoDataCalendarUtils.is_valid_ganzhi_date(CalendarDate(year, 0, 1, CalendarType.GANZHI)))
      self.assertFalse(HkoDataCalendarUtils.is_valid_ganzhi_date(CalendarDate(year, len(days_counts) + 1, 1, CalendarType.GANZHI)))

    min_year: int = HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR).year + 1
    max_year: int = HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR).year - 1
    for year in range(min_year, max_year + 1):
      __run_test_in_ganzhi_year(year)

    self.assertFalse(HkoDataCalendarUtils.is_valid_ganzhi_date(CalendarDate(0, 1, 1, CalendarType.GANZHI))) # Out or supported range.
    self.assertFalse(HkoDataCalendarUtils.is_valid_ganzhi_date(CalendarDate(9999, 1, 1, CalendarType.GANZHI))) # Out of supported range.


  def test_days_counts_in_ganzhi_year(self) -> None:
    min_year: int = HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI).year
    max_year: int = HkoDataCalendarUtils.get_max_supported_date(CalendarType.GANZHI).year

    # Test negative cases first.
    with self.assertRaises(AssertionError):
      HkoDataCalendarUtils.days_counts_in_ganzhi_year(-1)
    with self.assertRaises(AssertionError):
      HkoDataCalendarUtils.days_counts_in_ganzhi_year(min_year - 1)
    with self.assertRaises(AssertionError):
      HkoDataCalendarUtils.days_counts_in_ganzhi_year(max_year + 1)

    # Test edge cases.
    days_counts = HkoDataCalendarUtils.days_counts_in_ganzhi_year(min_year)
    for count in days_counts:
      self.assertTrue(29 <= count <= 32) 
    days_counts = HkoDataCalendarUtils.days_counts_in_ganzhi_year(max_year)
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
      dates.append(HkoDataCalendarUtils.jieqi_dates_db.get(year + 1, Jieqi.立春)) # Start of the next ganzhi year.

      days_counts = HkoDataCalendarUtils.days_counts_in_ganzhi_year(year)
      for idx, (start_date, next_start_date) in enumerate(zip(dates[:-1], dates[1:])):
        days_in_this_month: int = days_counts[idx]
        self.assertEqual(days_in_this_month, (next_start_date - start_date).days)
      

  def test_is_valid(self) -> None:
    for date_type in [CalendarType.SOLAR, CalendarType.LUNAR, CalendarType.GANZHI]:
      min_date: CalendarDate = HkoDataCalendarUtils.get_min_supported_date(date_type)
      max_date: CalendarDate = HkoDataCalendarUtils.get_max_supported_date(date_type)

      self.assertTrue(HkoDataCalendarUtils.is_valid(min_date))
      self.assertTrue(HkoDataCalendarUtils.is_valid(max_date))
      self.assertFalse(HkoDataCalendarUtils.is_valid(CalendarDate(0, 1, 1, date_type))) # Out or supported range.
      self.assertFalse(HkoDataCalendarUtils.is_valid(CalendarDate(9999, 1, 1, date_type))) # Out of supported range.

    class __DuckTypeClass:
      def __init__(self, anything: Any) -> None:
        self.date_type = anything
    self.assertFalse(HkoDataCalendarUtils.is_valid(__DuckTypeClass(0))) # type: ignore # Test duck type.

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
    _month_lengths: list[int] = HkoDataCalendarUtils.days_counts_in_ganzhi_year(_y)
    while True:
      yield CalendarDate(_y, _m, _d, CalendarType.GANZHI)
      _d += 1
      if _d > _month_lengths[_m - 1]:
        _d = 1
        _m += 1
        if _m > 12:
          _m = 1
          _y += 1
          _month_lengths = HkoDataCalendarUtils.days_counts_in_ganzhi_year(_y)
          
  def test_lunar_to_solar(self) -> None:
    min_lunar_date: CalendarDate = HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR)
    max_lunar_date: CalendarDate = HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR)

    self.assertEqual(HkoDataCalendarUtils.lunar_to_solar(min_lunar_date),
                     HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    self.assertEqual(HkoDataCalendarUtils.lunar_to_solar(max_lunar_date),
                     HkoDataCalendarUtils.get_max_supported_date(CalendarType.SOLAR))

    solar_date_gen = self.__solar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    lunar_date_gen = self.__lunar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR))

    while True:
      solar_date = next(solar_date_gen)
      lunar_date = next(lunar_date_gen)
      self.assertEqual(solar_date, HkoDataCalendarUtils.lunar_to_solar(lunar_date))

      if lunar_date == max_lunar_date:
        self.assertEqual(solar_date, HkoDataCalendarUtils.get_max_supported_date(CalendarType.SOLAR))
        break

  def test_solar_to_lunar(self) -> None:
    min_solar_date: CalendarDate = HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR)
    max_solar_date: CalendarDate = HkoDataCalendarUtils.get_max_supported_date(CalendarType.SOLAR)

    self.assertEqual(HkoDataCalendarUtils.solar_to_lunar(min_solar_date),
                     HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    self.assertEqual(HkoDataCalendarUtils.solar_to_lunar(max_solar_date),
                     HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR))

    solar_date_gen = self.__solar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    lunar_date_gen = self.__lunar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR))

    while True:
      solar_date = next(solar_date_gen)
      lunar_date = next(lunar_date_gen)
      self.assertEqual(lunar_date, HkoDataCalendarUtils.solar_to_lunar(solar_date))

      if solar_date == max_solar_date:
        self.assertEqual(lunar_date, HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR))
        break

  def test_ganzhi_to_solar(self) -> None:
    min_ganzhi_date: CalendarDate = HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI)
    max_ganzhi_date: CalendarDate = HkoDataCalendarUtils.get_max_supported_date(CalendarType.GANZHI)

    self.assertEqual(HkoDataCalendarUtils.ganzhi_to_solar(min_ganzhi_date),
                     HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    self.assertEqual(HkoDataCalendarUtils.ganzhi_to_solar(max_ganzhi_date),
                     HkoDataCalendarUtils.get_max_supported_date(CalendarType.SOLAR))
    
    solar_date_gen = self.__solar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    while True:
      solar_date = next(solar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)
      self.assertEqual(solar_date, HkoDataCalendarUtils.ganzhi_to_solar(ganzhi_date))

      if ganzhi_date == max_ganzhi_date:
        self.assertEqual(solar_date, HkoDataCalendarUtils.get_max_supported_date(CalendarType.SOLAR))
        break

  def test_solar_to_ganzhi(self) -> None:
    min_solar_date: CalendarDate = HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR)
    max_solar_date: CalendarDate = HkoDataCalendarUtils.get_max_supported_date(CalendarType.SOLAR)

    self.assertEqual(HkoDataCalendarUtils.solar_to_ganzhi(min_solar_date),
                     HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI))
    self.assertEqual(HkoDataCalendarUtils.solar_to_ganzhi(max_solar_date),
                     HkoDataCalendarUtils.get_max_supported_date(CalendarType.GANZHI))

    solar_date_gen = self.__solar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    while True:
      solar_date = next(solar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)
      self.assertEqual(ganzhi_date, HkoDataCalendarUtils.solar_to_ganzhi(solar_date))

      if solar_date == max_solar_date:
        self.assertEqual(ganzhi_date, HkoDataCalendarUtils.get_max_supported_date(CalendarType.GANZHI))
        break

  def test_lunar_to_ganzhi(self) -> None:
    min_lunar_date: CalendarDate = HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR)
    max_lunar_date: CalendarDate = HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR)

    self.assertEqual(HkoDataCalendarUtils.lunar_to_ganzhi(min_lunar_date),
                     HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI))
    self.assertEqual(HkoDataCalendarUtils.lunar_to_ganzhi(max_lunar_date),
                     HkoDataCalendarUtils.get_max_supported_date(CalendarType.GANZHI))

    lunar_date_gen = self.__lunar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    while True:
      lunar_date = next(lunar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)
      self.assertEqual(ganzhi_date, HkoDataCalendarUtils.lunar_to_ganzhi(lunar_date))

      if lunar_date == max_lunar_date:
        self.assertEqual(ganzhi_date, HkoDataCalendarUtils.get_max_supported_date(CalendarType.GANZHI))
        break

  def test_ganzhi_to_lunar(self) -> None:
    min_ganzhi_date: CalendarDate = HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI)
    max_ganzhi_date: CalendarDate = HkoDataCalendarUtils.get_max_supported_date(CalendarType.GANZHI)

    self.assertEqual(HkoDataCalendarUtils.ganzhi_to_lunar(min_ganzhi_date),
                     HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    self.assertEqual(HkoDataCalendarUtils.ganzhi_to_lunar(max_ganzhi_date),
                     HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR))

    ganzhi_date_gen = self.__ganzhi_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI))
    lunar_date_gen = self.__lunar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR))

    while True:
      ganzhi_date = next(ganzhi_date_gen)
      lunar_date = next(lunar_date_gen)
      self.assertEqual(lunar_date, HkoDataCalendarUtils.ganzhi_to_lunar(ganzhi_date))

      if ganzhi_date == max_ganzhi_date:
        self.assertEqual(lunar_date, HkoDataCalendarUtils.get_max_supported_date(CalendarType.LUNAR))
        break

  def test_complex_date_conversions(self) -> None:
    solar_date_gen = self.__solar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.SOLAR))
    lunar_date_gen = self.__lunar_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.LUNAR))
    ganzhi_date_gen = self.__ganzhi_date_gen(HkoDataCalendarUtils.get_min_supported_date(CalendarType.GANZHI))

    for _ in range(4096):
      solar_date = next(solar_date_gen)
      lunar_date = next(lunar_date_gen)
      ganzhi_date = next(ganzhi_date_gen)

      with self.subTest('ganzhi'):
        _solar_date = HkoDataCalendarUtils.ganzhi_to_solar(ganzhi_date)
        _lunar_date = HkoDataCalendarUtils.ganzhi_to_lunar(ganzhi_date)

        self.assertEqual(solar_date, _solar_date)
        self.assertEqual(lunar_date, _lunar_date)
        self.assertEqual(ganzhi_date, HkoDataCalendarUtils.solar_to_ganzhi(_solar_date))
        self.assertEqual(ganzhi_date, HkoDataCalendarUtils.lunar_to_ganzhi(_lunar_date))

      with self.subTest('solar'):
        _lunar_date = HkoDataCalendarUtils.solar_to_lunar(solar_date)
        _ganzhi_date = HkoDataCalendarUtils.solar_to_ganzhi(solar_date)

        self.assertEqual(lunar_date, _lunar_date)
        self.assertEqual(ganzhi_date, _ganzhi_date)
        self.assertEqual(solar_date, HkoDataCalendarUtils.lunar_to_solar(_lunar_date))
        self.assertEqual(solar_date, HkoDataCalendarUtils.ganzhi_to_solar(_ganzhi_date))

      with self.subTest('lunar'):
        _solar_date = HkoDataCalendarUtils.lunar_to_solar(lunar_date)
        _ganzhi_date = HkoDataCalendarUtils.lunar_to_ganzhi(lunar_date)

        self.assertEqual(solar_date, _solar_date)
        self.assertEqual(ganzhi_date, _ganzhi_date)
        self.assertEqual(lunar_date, HkoDataCalendarUtils.solar_to_lunar(_solar_date))
        self.assertEqual(lunar_date, HkoDataCalendarUtils.ganzhi_to_lunar(_ganzhi_date))

  def test_date_conversions_negative(self) -> None:
    with self.subTest('ganzhi_to_lunar negative'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.ganzhi_to_lunar(CalendarDate(1, 1, 1, CalendarType.GANZHI))
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.ganzhi_to_lunar(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

    with self.subTest('lunar_to_ganzhi negative'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.lunar_to_ganzhi(CalendarDate(1, 1, 1, CalendarType.LUNAR))
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.lunar_to_ganzhi(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

    with self.subTest('solar_to_lunar negative'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.solar_to_lunar(CalendarDate(1, 1, 1, CalendarType.SOLAR))
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.solar_to_lunar(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.subTest('lunar_to_solar negative'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.lunar_to_solar(CalendarDate(1, 1, 1, CalendarType.LUNAR))
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.lunar_to_solar(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.subTest('solar_to_ganzhi negative'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.solar_to_ganzhi(CalendarDate(1, 1, 1, CalendarType.SOLAR))
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.solar_to_ganzhi(CalendarDate(2024, 1, 1, CalendarType.GANZHI))

    with self.subTest('ganzhi_to_solar negative'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.ganzhi_to_solar(CalendarDate(1, 1, 1, CalendarType.GANZHI))
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.ganzhi_to_solar(CalendarDate(2024, 1, 1, CalendarType.SOLAR))

  def test_to_solar(self) -> None:
    with self.subTest('Positive cases'):
      d: date = date(2023, 5, 8)
      solar_date: CalendarDate = HkoDataCalendarUtils.to_solar(d)
      self.assertEqual(solar_date, CalendarDate(2023, 5, 8, CalendarType.SOLAR))
      self.assertEqual(solar_date, HkoDataCalendarUtils.to_solar(d))
      self.assertEqual(solar_date, HkoDataCalendarUtils.to_solar(solar_date))
      self.assertEqual(solar_date, HkoDataCalendarUtils.to_solar(HkoDataCalendarUtils.solar_to_lunar(solar_date)))
      self.assertEqual(solar_date, HkoDataCalendarUtils.to_solar(HkoDataCalendarUtils.solar_to_ganzhi(solar_date)))
    
    with self.subTest('Negative cases'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_solar(CalendarDate(9999, 1, 1, CalendarType.SOLAR)) # Invalid date
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_solar('2024-01-01') # type: ignore # Invalid type

  def test_to_lunar(self) -> None:
    with self.subTest('Positive cases'):
      d: date = date(2023, 5, 8)
      lunar_date: CalendarDate = HkoDataCalendarUtils.to_lunar(d)
      self.assertEqual(lunar_date, HkoDataCalendarUtils.solar_to_lunar(CalendarDate(2023, 5, 8, CalendarType.SOLAR)))
      self.assertEqual(lunar_date, HkoDataCalendarUtils.to_lunar(d))
      self.assertEqual(lunar_date, HkoDataCalendarUtils.to_lunar(lunar_date))
      self.assertEqual(lunar_date, HkoDataCalendarUtils.to_lunar(HkoDataCalendarUtils.lunar_to_solar(lunar_date)))
      self.assertEqual(lunar_date, HkoDataCalendarUtils.to_lunar(HkoDataCalendarUtils.lunar_to_ganzhi(lunar_date)))
    
    with self.subTest('Negative cases'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_lunar(CalendarDate(9999, 1, 1, CalendarType.LUNAR)) # Invalid date
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_lunar('2024-01-01') # type: ignore # Invalid type

  def test_to_ganzhi(self) -> None:
    with self.subTest('Positive cases'):
      d: date = date(2023, 5, 8)
      ganzhi_date: CalendarDate = HkoDataCalendarUtils.to_ganzhi(d)
      self.assertEqual(ganzhi_date, HkoDataCalendarUtils.solar_to_ganzhi(CalendarDate(2023, 5, 8, CalendarType.SOLAR)))
      self.assertEqual(ganzhi_date, HkoDataCalendarUtils.to_ganzhi(d))
      self.assertEqual(ganzhi_date, HkoDataCalendarUtils.to_ganzhi(ganzhi_date))
      self.assertEqual(ganzhi_date, HkoDataCalendarUtils.to_ganzhi(HkoDataCalendarUtils.ganzhi_to_solar(ganzhi_date)))
      self.assertEqual(ganzhi_date, HkoDataCalendarUtils.to_ganzhi(HkoDataCalendarUtils.ganzhi_to_lunar(ganzhi_date)))
    
    with self.subTest('Negative cases'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_ganzhi(CalendarDate(9999, 1, 1, CalendarType.GANZHI)) # Invalid date
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_ganzhi('2024-01-01') # type: ignore # Invalid type

  def test_to_date(self) -> None:
    d = date(2023, 5, 8)
    self.assertEqual(HkoDataCalendarUtils.to_date(d), d)

    dt = datetime(2023, 5, 8, 1, 2, 3)
    self.assertEqual(HkoDataCalendarUtils.to_date(dt), d)

    cd = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
    self.assertEqual(HkoDataCalendarUtils.to_date(cd), date(2000, 1, 1))

    cd = CalendarDate(1901, 1, 1, CalendarType.LUNAR)
    self.assertEqual(HkoDataCalendarUtils.to_date(cd), date(1901, 2, 19))

    with self.subTest('Negative cases'):
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_date(CalendarDate(9999, 1, 1, CalendarType.GANZHI)) # Invalid date
      with self.assertRaises(AssertionError):
        HkoDataCalendarUtils.to_date('2024-01-01') # type: ignore # Invalid type
