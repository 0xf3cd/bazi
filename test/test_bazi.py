# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
from datetime import datetime
from bazi import Bazi, 八字

class TestBaziInit(unittest.TestCase):
  def test_basic_arguments(self) -> None:
    # Generate a random datetime.
    random_dt: datetime = datetime(
      year=random.randint(1900, 2100),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
    )

    bazi: Bazi = Bazi(*random_dt.timetuple()[:5])

    self.assertEqual(bazi.year, random_dt.year)
    self.assertEqual(bazi.month, random_dt.month)
    self.assertEqual(bazi.day, random_dt.day)
    self.assertEqual(bazi.hour, random_dt.hour)
    self.assertEqual(bazi.minute, random_dt.minute)
    self.assertEqual(bazi.datetime, random_dt)

  def test_invalid_arguments(self) -> None:
    with self.assertRaises(TypeError):
      Bazi(2000, 1, 31, 15) # type: ignore # Missing minute
    with self.assertRaises(ValueError):
      Bazi(2000, 13, 31, 15, 30) # Invalid month
    with self.assertRaises(ValueError):
      Bazi(2000, 2, 30, 15, 30) # Invalid day
    with self.assertRaises(ValueError):
      Bazi(2024, 2, 29, 24, 30) # Invalid hour
    with self.assertRaises(ValueError):
      Bazi(2024, 8, 1, 22, 60) # Invalid minute
    with self.assertRaises(ValueError):
      Bazi(2030, 2, 1, 0, -1) # Invalid minute

class TestBazi(unittest.TestCase):
  def test_chinese(self) -> None:
    self.assertIs(Bazi, 八字)

    random_dt: datetime = datetime(
      year=random.randint(1900, 2100),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
    )

    bazi: 八字 = 八字(*random_dt.timetuple()[:5])

    self.assertEqual(bazi.year, random_dt.year)
    self.assertEqual(bazi.month, random_dt.month)
    self.assertEqual(bazi.day, random_dt.day)
    self.assertEqual(bazi.hour, random_dt.hour)
    self.assertEqual(bazi.minute, random_dt.minute)
    self.assertEqual(bazi.datetime, random_dt)
