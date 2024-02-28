# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
from datetime import date, datetime
from bazi import BaziGender, Bazi, 八字, CalendarDate, CalendarType, CalendarUtils


class TestBaziGender(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(BaziGender), 2)

    self.assertIs(BaziGender.YANG, BaziGender.MALE)
    self.assertIs(BaziGender.YANG, BaziGender.男)
    self.assertIs(BaziGender.YANG, BaziGender.阳)
    self.assertIs(BaziGender.YANG, BaziGender.乾)

    self.assertIs(BaziGender.YIN, BaziGender.FEMALE)
    self.assertIs(BaziGender.YIN, BaziGender.女)
    self.assertIs(BaziGender.YIN, BaziGender.阴)
    self.assertIs(BaziGender.YIN, BaziGender.坤)


class TestBazi(unittest.TestCase):
  def test_init_with_date(self) -> None:
    for _ in range(128):
      random_d: date = date(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
      )

      bazi: Bazi = Bazi(random_d, 15, BaziGender.男)

      self.assertEqual(bazi.solar_date, CalendarDate(random_d.year, random_d.month, random_d.day, CalendarType.SOLAR))
      self.assertEqual(bazi.hour, 15)
      self.assertEqual(bazi.gender, BaziGender.男)

      # Also test that `datetime` is acceptable, since `datetime` is subclass of `date`.
      random_dt: datetime = datetime(
        year=random_d.year,
        month=random_d.month,
        day=random_d.day,
        hour=23,
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )

      bazi: Bazi = Bazi(random_dt, 15, BaziGender.男)

      self.assertEqual(bazi.solar_date, CalendarDate(random_d.year, random_d.month, random_d.day, CalendarType.SOLAR))
      self.assertNotEqual(bazi.hour, random_dt.hour) # `datetime.hour` is ignored by `bazi.__init__`.
      self.assertEqual(bazi.hour, 15)
      self.assertEqual(bazi.gender, BaziGender.男)

  def test_init_with_solar_date(self) -> None:
    for _ in range(128):
      random_solar_date: CalendarDate = CalendarDate(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        date_type=CalendarType.SOLAR
      )

      bazi: Bazi = Bazi(random_solar_date, 15, BaziGender.男)

      self.assertEqual(bazi.solar_date, random_solar_date)
      self.assertEqual(bazi.hour, 15)
      self.assertEqual(bazi.gender, BaziGender.男)

  def test_init_with_ganzhi_date(self) -> None:
    for _ in range(128):
      random_ganzhi_date: CalendarDate = CalendarDate(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        date_type=CalendarType.GANZHI
      )

      bazi: Bazi = Bazi(random_ganzhi_date, 15, BaziGender.男)

      self.assertEqual(bazi.solar_date, CalendarUtils.ganzhi_to_solar(random_ganzhi_date))
      self.assertEqual(bazi.hour, 15)
      self.assertEqual(bazi.gender, BaziGender.男)

  def test_init_with_lunar_date(self) -> None:
    for _ in range(128):
      random_lunar_date: CalendarDate = CalendarDate(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12), # Not using (1, 13) here, since we don't know which years are leap years.
        day=random.randint(1, 28),
        date_type=CalendarType.LUNAR
      )

      bazi: Bazi = Bazi(random_lunar_date, 15, BaziGender.男)

      self.assertEqual(bazi.solar_date, CalendarUtils.lunar_to_solar(random_lunar_date))
      self.assertEqual(bazi.hour, 15)
      self.assertEqual(bazi.gender, BaziGender.男)

  def test_chinese(self) -> None:
    self.assertIs(Bazi, 八字)

    for _ in range(128):
      random_d: date = date(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
      )

      bazi: 八字 = 八字(random_d, 15, BaziGender.男)

      self.assertEqual(bazi.solar_date, CalendarDate(random_d.year, random_d.month, random_d.day, CalendarType.SOLAR))
      self.assertEqual(bazi.hour, 15)
      self.assertEqual(bazi.gender, BaziGender.男)

  def test_invalid_arguments(self) -> None:
    random_d: date = date(
      year=random.randint(1950, 2000),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
    )

    with self.assertRaises(TypeError):
      Bazi(random_d, 15) # type: ignore # Missing `gender`
    with self.assertRaises(TypeError):
      Bazi(random_d, BaziGender.女) # type: ignore # Missing `hour`
    with self.assertRaises(AssertionError):
      Bazi(CalendarDate(999999, 3, 30, CalendarType.SOLAR), 20, BaziGender.男) # Invalid year
    with self.assertRaises(AssertionError):
      Bazi(CalendarDate(2024, 13, 3, CalendarType.SOLAR), 20, BaziGender.男) # Invalid month
    with self.assertRaises(AssertionError):
      Bazi(CalendarDate(2024, 1, 0, CalendarType.SOLAR), 20, BaziGender.男) # Invalid day
    with self.assertRaises(AssertionError):
      Bazi(CalendarDate(2024, 1, 30, CalendarType.SOLAR), 24, BaziGender.男) # Invalid hour
    with self.assertRaises(AssertionError):
      Bazi(CalendarDate(2024, 8, 1, CalendarType.SOLAR), -1, BaziGender.男) # Yet another invalid hour
    with self.assertRaises(AssertionError):
      Bazi('2024-01-30', 13, BaziGender.男) # type: ignore # Currently doesn't take string as input
