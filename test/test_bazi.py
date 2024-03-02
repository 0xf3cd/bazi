# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
from datetime import date, datetime
from zoneinfo import ZoneInfo
from bazi import (
  Tiangan, Dizhi, Ganzhi, Wuxing, Yinyang, BaziUtils,
  BaziGender, BaziPrecision, BaziData, Bazi, 八字,
  BaziChart, 命盘,
  TraitTuple
)


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
  
  def test_chart(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: BaziData[Ganzhi] = bazi.pillars
      self.assertEqual(pillars.year, Ganzhi.from_str(ganzhi_strs[0]))
      self.assertEqual(pillars.month, Ganzhi.from_str(ganzhi_strs[1]))
      self.assertEqual(pillars.day, Ganzhi.from_str(ganzhi_strs[2]))
      self.assertEqual(pillars.hour, Ganzhi.from_str(ganzhi_strs[3]))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])

  def test_consistency(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: BaziData[Ganzhi] = bazi.pillars

      self.assertEqual(bazi.day_master, pillars.day.tiangan)
      self.assertEqual(bazi.month_commander, pillars.month.dizhi)

      self.assertEqual(bazi.year_pillar, pillars.year)
      self.assertEqual(bazi.month_pillar, pillars.month)
      self.assertEqual(bazi.day_pillar, pillars.day)
      self.assertEqual(bazi.hour_pillar, pillars.hour)

      self.assertEqual(bazi.four_tiangans, tuple([tg for tg, _ in pillars]))
      self.assertEqual(bazi.four_dizhis, tuple([dz for _, dz in pillars]))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])


class TestBaziChart(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(BaziChart, 命盘)

  def test_malicious(self) -> None:
    with self.subTest('Modification attemp'):
      bazi: Bazi = Bazi(
        birth_time=datetime(1984, 4, 2, 4, 2),
        gender=BaziGender.男,
        precision=BaziPrecision.DAY,
      )
      chart: BaziChart = BaziChart(bazi)

      bazi._day_pillar = Ganzhi.from_str('甲子')
      self.assertEqual(chart.bazi._day_pillar, Ganzhi.from_str('丙寅'))
      self.assertEqual(bazi._day_pillar, Ganzhi.from_str('甲子'))

    with self.subTest('Invalid __init__ parameters'):
      with self.assertRaises(AssertionError):
        BaziChart('1984-04-02 04:02:00') # type: ignore
      with self.assertRaises(TypeError):
        BaziChart(datetime(1984, 4, 2, 4, 2), BaziGender.男, BaziPrecision.DAY) # type: ignore

  def test_traits(self) -> None:
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    traits: BaziData[BaziChart.PillarTraits] = chart.traits

    self.assertEqual(traits.year.tiangan, TraitTuple(Wuxing.木, Yinyang.阳))  # 甲
    self.assertEqual(traits.year.dizhi, TraitTuple(Wuxing.水, Yinyang.阳))    # 子

    self.assertEqual(traits.month.tiangan, TraitTuple(Wuxing.火, Yinyang.阴)) # 丁
    self.assertEqual(traits.month.dizhi, TraitTuple(Wuxing.木, Yinyang.阴))   # 卯

    self.assertEqual(traits.day.tiangan, TraitTuple(Wuxing.火, Yinyang.阳))   # 丙
    self.assertEqual(traits.day.dizhi, TraitTuple(Wuxing.木, Yinyang.阳))     # 寅

    self.assertEqual(traits.hour.tiangan, TraitTuple(Wuxing.金, Yinyang.阳))  # 庚
    self.assertEqual(traits.hour.dizhi, TraitTuple(Wuxing.木, Yinyang.阳))    # 寅

    for pillar, pillar_traits in zip(bazi.pillars, traits):
      self.assertEqual(BaziUtils.get_tiangan_traits(pillar.tiangan), pillar_traits.tiangan)
      self.assertEqual(BaziUtils.get_dizhi_traits(pillar.dizhi), pillar_traits.dizhi)

  def test_hidden_tiangans(self) -> None:
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    hidden_tiangans: BaziData[BaziChart.PillarHiddenTiangans] = chart.hidden_tiangans

    for hidden in hidden_tiangans:
      self.assertIsNone(hidden.tiangan) # There's no hidden tiangans in tiangan.
    
    self.assertDictEqual(hidden_tiangans.year.dizhi, {  # 子
      Tiangan.癸 : 100,
    })
    self.assertDictEqual(hidden_tiangans.month.dizhi, { # 卯
      Tiangan.乙 : 100,
    })
    self.assertDictEqual(hidden_tiangans.day.dizhi, {   # 寅
      Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10,
    })
    self.assertDictEqual(hidden_tiangans.hour.dizhi, {  # 寅
      Tiangan.甲 : 60, Tiangan.丙 : 30, Tiangan.戊 : 10,
    })
