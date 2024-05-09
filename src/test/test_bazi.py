# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
import copy

from itertools import product
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Union

from src.Defines import Tiangan, Dizhi, Ganzhi
from src.Bazi import BaziGender, BaziPrecision, Bazi, 八字


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

  def test_str(self) -> None:
    self.assertEqual(str(BaziGender.YANG), 'male')
    self.assertEqual(str(BaziGender.YIN), 'female')
    self.assertIs(BaziGender.YANG, BaziGender('男'))
    self.assertIs(BaziGender.YIN, BaziGender('女'))


class TestBaziPrecision(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(BaziPrecision), 3)

    self.assertEqual(str(BaziPrecision.DAY), 'day')
    self.assertEqual(str(BaziPrecision.HOUR), 'hour')
    self.assertEqual(str(BaziPrecision.MINUTE), 'minute')


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

      self.assertEqual(bazi.solar_date, date(random_dt.year, random_dt.month, random_dt.day))
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

      self.assertEqual(bazi.solar_date, date(random_dt.year, random_dt.month, random_dt.day))
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

    with self.assertRaises(TypeError):
      Bazi(birth_time=random_dt, gender=BaziGender.男) # type: ignore # Missing `precision`
    with self.assertRaises(TypeError):
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

  @staticmethod
  def __create_bazi(dt: datetime) -> Bazi:
    return Bazi(
      birth_time=dt,
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )

  def test_four_dizhis_correctness(self) -> None:
    '''
    Test the correctness of `Bazi` on the given test cases.
    Precision is at `DAY` level.
    '''
    def __subtest(dt: datetime, dizhi_strs: list[str]) -> None:
      assert len(dizhi_strs) == 4

      bazi = self.__create_bazi(dt)
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

  def test_four_tiangans_correctness(self) -> None:
    def __subtest(dt: datetime, tiangan_strs: list[str]) -> None:
      assert len(tiangan_strs) == 4

      bazi = self.__create_bazi(dt)
      self.assertEqual(bazi.four_tiangans, (
        Tiangan.from_str(tiangan_strs[0]),
        Tiangan.from_str(tiangan_strs[1]),
        Tiangan.from_str(tiangan_strs[2]),
        Tiangan.from_str(tiangan_strs[3]),
      ))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲', '丁', '丙', '庚'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚', '戊', '壬', '辛'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛', '戊', '丙', '戊'])

  def test_date_time(self) -> None:
    bazi: Bazi = self.__create_bazi(datetime(1984, 4, 2, 4, 2))
    self.assertEqual(bazi.solar_date, date(1984, 4, 2))
    self.assertEqual(bazi.hour, 4)
    self.assertEqual(bazi.minute, 2)
    self.assertEqual(bazi.solar_datetime, datetime(1984, 4, 2, 4, 2))

    random_bazi: Bazi = Bazi.random()
    with self.assertRaises(AttributeError):
      random_bazi.solar_date = date(1984, 4, 3) # type: ignore
    with self.assertRaises(AttributeError):
      random_bazi.hour = 9 # type: ignore
    with self.assertRaises(AttributeError):
      random_bazi.minute = 8 # type: ignore
    with self.assertRaises(AttributeError):
      random_bazi.solar_datetime = datetime(1984, 4, 3, 9, 8) # type: ignore
  
  def test_chart(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: list[Ganzhi] = list(bazi.pillars)
      self.assertEqual(pillars[0], Ganzhi.from_str(ganzhi_strs[0]), 'Year Pillar')
      self.assertEqual(pillars[1], Ganzhi.from_str(ganzhi_strs[1]), 'Month Pillar')
      self.assertEqual(pillars[2], Ganzhi.from_str(ganzhi_strs[2]), 'Day Pillar')
      self.assertEqual(pillars[3], Ganzhi.from_str(ganzhi_strs[3]), 'Hour Pillar')

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])

  def test_consistency(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: list[Ganzhi] = list(bazi.pillars)

      self.assertEqual(bazi.day_master, pillars[2].tiangan)
      self.assertEqual(bazi.month_commander, pillars[1].dizhi)

      self.assertEqual(bazi.year_pillar, pillars[0])
      self.assertEqual(bazi.month_pillar, pillars[1])
      self.assertEqual(bazi.day_pillar, pillars[2])
      self.assertEqual(bazi.hour_pillar, pillars[3])

      self.assertEqual(bazi.four_tiangans, tuple([tg for tg, _ in pillars]))
      self.assertEqual(bazi.four_dizhis, tuple([dz for _, dz in pillars]))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])

  def test_deepcopy(self) -> None:
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    bazi2: Bazi = copy.deepcopy(bazi)

    self.assertIsNot(bazi._solar_date, bazi2._solar_date)
    self.assertIsNot(bazi._year_pillar, bazi2._year_pillar)

    self.assertIsNot(bazi._day_pillar, bazi2._day_pillar)
    self.assertEqual(bazi._day_pillar, bazi2._day_pillar)

    cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
    next_day_pillar: Ganzhi = cycle[(cycle.index(bazi._day_pillar) + 1) % len(cycle)]
    bazi._day_pillar = next_day_pillar # type: ignore
    self.assertNotEqual(bazi._day_pillar, bazi2._day_pillar)

  def test_create(self) -> None:
    with self.assertRaises(ValueError):
      Bazi.create('WrongDatetimeFormat', BaziGender.FEMALE, BaziPrecision.DAY)
    with self.assertRaises(ValueError):
      Bazi.create(datetime.now(), 'femal', BaziPrecision.DAY)
    with self.assertRaises(ValueError):
      Bazi.create(datetime.now(), BaziGender.FEMALE, 'dya')

    # Create a datetime and set its timezone to Asia/Shanghai.
    _dt: datetime = datetime.now()
    _dt = _dt.replace(tzinfo=ZoneInfo('Asia/Shanghai'))
    with self.assertRaises(AssertionError):
      Bazi.create(_dt, BaziGender.FEMALE, BaziPrecision.DAY)
    with self.assertRaises(AssertionError):
      Bazi.create(_dt.isoformat(), BaziGender.FEMALE, BaziPrecision.DAY)

    now: datetime = datetime.now()
    dt_options: list[Union[str, datetime]] = [now, now.isoformat()]
    male_options: list[Union[str, BaziGender]] = [BaziGender.男, BaziGender.YANG, BaziGender.阳, 'Male', '男', 'MALE']
    female_options: list[Union[str, BaziGender]] = [BaziGender.YIN, BaziGender.FEMALE, '女', 'FEMALE', 'female']
    day_precision_options: list[Union[str, BaziPrecision]] = [BaziPrecision.DAY, 'day', 'DAY', 'Day', '日', '天', 'd', 'D']

    expected_bazi: Bazi = Bazi.create(now, BaziGender.FEMALE, BaziPrecision.DAY)
    for dt, g, p in product(dt_options, female_options, day_precision_options):
      bazi = Bazi.create(dt, g, p)
      self.assertListEqual(list(bazi.pillars), list(expected_bazi.pillars))
      self.assertEqual(bazi.gender, expected_bazi.gender)
      self.assertEqual(bazi.precision, expected_bazi.precision)
      self.assertEqual(bazi.solar_date, expected_bazi.solar_date)
      self.assertEqual(bazi.hour, expected_bazi.hour)
      self.assertEqual(bazi.minute, expected_bazi.minute)
    
    expected_bazi = Bazi.create(now, BaziGender.MALE, BaziPrecision.DAY)
    for dt, g, p in product(dt_options, male_options, day_precision_options):
      bazi = Bazi.create(dt, g, p)
      self.assertListEqual(list(bazi.pillars), list(expected_bazi.pillars))
      self.assertEqual(bazi.gender, expected_bazi.gender)
      self.assertEqual(bazi.precision, expected_bazi.precision)
      self.assertEqual(bazi.solar_date, expected_bazi.solar_date)
      self.assertEqual(bazi.hour, expected_bazi.hour)
      self.assertEqual(bazi.minute, expected_bazi.minute)

    unsupported_precision_options: list = [BaziPrecision.HOUR, BaziPrecision.MINUTE, 'hour', 'minute', 'H', 'm', '时', '小时', '分', '分钟']
    for dt, g, p in product(dt_options, male_options + female_options, unsupported_precision_options):
      with self.assertRaises(AssertionError):
        Bazi.create(dt, g, p) # Other level precision is not supported at the moment

  def test_eq_ne(self) -> None:
    def __random_info() -> tuple[datetime, BaziGender, BaziPrecision]:
      return (datetime(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      ), random.choice(list(BaziGender)), BaziPrecision.DAY)
    
    def __toggle_gender(g: BaziGender) -> BaziGender:
      return BaziGender.MALE if g is BaziGender.FEMALE else BaziGender.FEMALE
    
    def __inc_datetime(dt: datetime) -> datetime:
      return dt + timedelta(days=1)

    for _ in range(64):
      dt, gender, precision = __random_info()

      bazi: Bazi = Bazi.create(dt, gender, precision)
      self.assertEqual(bazi, Bazi.create(dt, gender, precision))
      self.assertNotEqual(bazi, Bazi.create(dt, __toggle_gender(gender), precision))
      self.assertNotEqual(bazi, Bazi.create(__inc_datetime(dt), gender, precision))
