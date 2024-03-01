# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
from datetime import date, datetime
from zoneinfo import ZoneInfo
from bazi import BaziGender, BaziPrecision, Bazi, 八字, Dizhi


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
    with self.assertRaises(AssertionError):
      Bazi(
        birth_time=datetime(
          year=2000,
          month=1,
          day=1,
          hour=7,
          minute=0,
          second=0,
          tzinfo=ZoneInfo('Asia/Shanghai') # Doesn't support timezone.
        ),
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )

  def test_correctness(self) -> None:
    '''
    Test the correctness of `Bazi` on the given test cases.
    Precision is at `DAY` level.
    '''
    def __create_bazi(dt: datetime) -> Bazi:
      return Bazi(
        birth_time=dt,
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )
    
    def __subtest(dt: datetime, dizhi_strs: list[str]) -> None:
      assert len(dizhi_strs) == 4

      bazi = __create_bazi(dt)
      self.assertEqual(bazi.four_dizhis, (
        Dizhi.from_str(dizhi_strs[0]),
        Dizhi.from_str(dizhi_strs[1]),
        Dizhi.from_str(dizhi_strs[2]),
        Dizhi.from_str(dizhi_strs[3]),
      ))

    with self.subTest('Basic cases'):
      # Data was collected from "测测" app on my iPhone 15 Pro Max.
      __subtest(datetime(2024, 2, 6, 11, 55), ['辰', '寅', '子', '午'])
      __subtest(datetime(1984, 4, 2, 4, 2), ['子', '卯', '寅', '寅'])

      __subtest(datetime(1998, 3, 17, 13, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 13, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 15, 0), ['寅', '卯', '亥', '申'])
      __subtest(datetime(1998, 3, 17, 23, 0), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 0, 59), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 1, 0), ['寅', '卯', '子', '丑'])

    with self.subTest('Edge cases'):
      __subtest(datetime(1998, 3, 17, 13, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 13, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 15, 0), ['寅', '卯', '亥', '申'])
      __subtest(datetime(1998, 3, 17, 23, 0), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 0, 59), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 1, 0), ['寅', '卯', '子', '丑'])

      __subtest(datetime(2000, 2, 3, 0, 0), ['卯', '丑', '卯', '子'])
      __subtest(datetime(2000, 2, 3, 22, 59), ['卯', '丑', '卯', '亥'])
      __subtest(datetime(2000, 2, 3, 23, 0), ['卯', '丑', '辰', '子'])
      __subtest(datetime(2000, 2, 4, 0, 0), ['辰', '寅', '辰', '子'])
      __subtest(datetime(2000, 2, 4, 1, 0), ['辰', '寅', '辰', '丑'])
