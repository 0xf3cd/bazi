# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
from datetime import date, datetime
from bazi import BaziGender, BaziPrecision, Bazi, 八字


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
  def test_init(self) -> None:
    for _ in range(128):
      random_dt: datetime = datetime(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )

      bazi: Bazi = Bazi(
        birth_time=random_dt,
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )

      self.assertEqual(bazi.solar_birth_date, date(random_dt.year, random_dt.month, random_dt.day))
      self.assertEqual(bazi.hour, random_dt.hour)
      self.assertEqual(bazi.minute, random_dt.minute)
      self.assertEqual(bazi.gender, BaziGender.男)
      self.assertEqual(bazi.precision, BaziPrecision.DAY)

  def test_chinese(self) -> None:
    self.assertIs(Bazi, 八字)

    for _ in range(128):
      random_dt: datetime = datetime(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )

      bazi: 八字 = 八字(
        birth_time=random_dt,
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )

      self.assertEqual(bazi.solar_birth_date, date(random_dt.year, random_dt.month, random_dt.day))
      self.assertEqual(bazi.hour, random_dt.hour)
      self.assertEqual(bazi.minute, random_dt.minute)
      self.assertEqual(bazi.gender, BaziGender.男)
      self.assertEqual(bazi.precision, BaziPrecision.DAY)

  def test_invalid_arguments(self) -> None:
    random_dt: datetime = datetime(
      year=random.randint(1950, 2000),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59)
    )

    with self.assertRaises(AssertionError):
      Bazi(birth_time=random_dt, gender=BaziGender.男) # type: ignore # Missing `precision`
    with self.assertRaises(AssertionError):
      Bazi(birth_time=random_dt, precision=BaziPrecision.DAY) # type: ignore # Missing `gender`
    with self.assertRaises(AssertionError):
      Bazi(birth_time='2024-03-03', gender=BaziGender.男, precision=BaziPrecision.DAY) # type: ignore # Currently doesn't take string as input
    with self.assertRaises(AssertionError):
      Bazi(birth_time=date(9999, 1, 1), gender=BaziGender.男, precision=BaziPrecision.DAY) # type: ignore
    with self.assertRaises(AssertionError):
      dt: datetime = datetime(
        year=9999, # Out of supported range.
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )
      Bazi(birth_time=dt, gender=BaziGender.男, precision=BaziPrecision.DAY)
