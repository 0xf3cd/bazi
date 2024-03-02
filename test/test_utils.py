# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_utils.py

import unittest
from datetime import date, datetime, timedelta
from bazi import CalendarUtils, Ganzhi, Tiangan, Dizhi, Wuxing, Yinyang
from bazi.Utils import BaziUtils


class TestUtils(unittest.TestCase):
  def test_get_day_ganzhi_basic(self) -> None:
    with self.subTest('Basic'):
      d: date = date(2024, 3, 1)
      self.assertEqual(BaziUtils.get_day_ganzhi(d), BaziUtils.get_day_ganzhi(CalendarUtils.to_solar(d)))

      dt: datetime = datetime(2024, 3, 1, 15, 34, 6)
      self.assertEqual(BaziUtils.get_day_ganzhi(d), BaziUtils.get_day_ganzhi(dt)) # `BaziUtils.get_day_ganzhi` also takes `datetime` objects.

    with self.subTest('Correctness'):
      d: date = date(2024, 3, 1)
      self.assertEqual(BaziUtils.get_day_ganzhi(d), Ganzhi.from_str('甲子'))
      self.assertEqual(BaziUtils.get_day_ganzhi(d + timedelta(days=1)), Ganzhi.from_str('乙丑'))
      self.assertEqual(BaziUtils.get_day_ganzhi(d - timedelta(days=1)), Ganzhi.from_str('癸亥'))

      self.assertEqual(BaziUtils.get_day_ganzhi(date(1914, 2, 14)), Ganzhi.from_str('辛未'))
      self.assertEqual(BaziUtils.get_day_ganzhi(date(1933, 11, 1)), Ganzhi.from_str('辛未'))
      self.assertEqual(BaziUtils.get_day_ganzhi(date(1958, 6, 29)), Ganzhi.from_str('丁丑'))
      self.assertEqual(BaziUtils.get_day_ganzhi(date(1964, 1, 19)), Ganzhi.from_str('丁卯'))
      self.assertEqual(BaziUtils.get_day_ganzhi(date(1984, 5, 31)), Ganzhi.from_str('乙丑'))
      self.assertEqual(BaziUtils.get_day_ganzhi(date(1997, 1, 30)), Ganzhi.from_str('壬申'))
      self.assertEqual(BaziUtils.get_day_ganzhi(date(2003, 7, 12)), Ganzhi.from_str('丙戌'))

      for offset in range(-2000, 2000):
        d: date = date(2024, 3, 1) + timedelta(days=offset)
        self.assertEqual(BaziUtils.get_day_ganzhi(d), Ganzhi.list_sexagenary_cycle()[offset % 60])

  def test_get_day_ganzhi_advanced(self) -> None:
    for d, ganzhi in [
      (CalendarUtils.to_lunar(date(2024, 3, 1)), Ganzhi.from_str('甲子')),
      (CalendarUtils.to_ganzhi(date(2024, 3, 1)), Ganzhi.from_str('甲子')),
      (CalendarUtils.to_lunar(date(1933, 11, 1)), Ganzhi.from_str('辛未')),
      (CalendarUtils.to_ganzhi(date(1933, 11, 1)), Ganzhi.from_str('辛未')),
      (CalendarUtils.to_lunar(date(1997, 1, 30)), Ganzhi.from_str('壬申')),
      (CalendarUtils.to_ganzhi(date(1997, 1, 30)), Ganzhi.from_str('壬申')),
    ]:
      self.assertEqual(BaziUtils.get_day_ganzhi(d), ganzhi)

  def test_find_month_tiangan(self) -> None:
    self.assertEqual(BaziUtils.find_month_tiangan(Tiangan.甲, Dizhi.寅), Tiangan.丙)
    self.assertEqual(BaziUtils.find_month_tiangan(Tiangan.壬, Dizhi.子), Tiangan.壬)
    self.assertEqual(BaziUtils.find_month_tiangan(Tiangan.丁, Dizhi.丑), Tiangan.癸)
    self.assertEqual(BaziUtils.find_month_tiangan(Tiangan.戊, Dizhi.巳), Tiangan.丁)

  def test_find_hour_tiangan(self) -> None:
    self.assertEqual(BaziUtils.find_hour_tiangan(Tiangan.甲, Dizhi.寅), Tiangan.丙)
    self.assertEqual(BaziUtils.find_hour_tiangan(Tiangan.壬, Dizhi.子), Tiangan.庚)
    self.assertEqual(BaziUtils.find_hour_tiangan(Tiangan.丁, Dizhi.丑), Tiangan.辛)
    self.assertEqual(BaziUtils.find_hour_tiangan(Tiangan.戊, Dizhi.巳), Tiangan.丁)
    self.assertEqual(BaziUtils.find_hour_tiangan(Tiangan.丙, Dizhi.卯), Tiangan.辛)

  def test_tiangan_traits(self) -> None:
    for idx, tg in enumerate(Tiangan):
      expected_wuxing: Wuxing = Wuxing.as_list()[idx // 2]
      expected_yinyang: Yinyang = Yinyang.as_list()[idx % 2]
      self.assertEqual(BaziUtils.get_tiangan_traits(tg), (expected_wuxing, expected_yinyang))

  def test_dizhi_traits(self) -> None:
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('子')), (Wuxing('水'), Yinyang('阳')))
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('辰')), (Wuxing('土'), Yinyang('阳')))
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('巳')), (Wuxing('火'), Yinyang('阴')))
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('丑')), (Wuxing('土'), Yinyang('阴')))

    for idx, dz in enumerate(Dizhi):
      month_idx: int = (idx - 2) % 12
      if month_idx % 3 == 2:
        expected_wuxing: Wuxing = Wuxing.土
      elif month_idx < 3:
        expected_wuxing: Wuxing = Wuxing.木
      elif month_idx < 6:
        expected_wuxing: Wuxing = Wuxing.火
      elif month_idx < 9:
        expected_wuxing: Wuxing = Wuxing.金
      else:
        expected_wuxing: Wuxing = Wuxing.水
      
      expected_yinyang: Yinyang = Yinyang.as_list()[idx % 2]
      self.assertEqual(BaziUtils.get_dizhi_traits(dz), (expected_wuxing, expected_yinyang))

  def test_get_hidden_tiangans(self) -> None:
    for dz in Dizhi:
      percentages: dict[Tiangan, int] = BaziUtils.get_hidden_tiangans(dz)
      self.assertGreaterEqual(len(percentages), 1)
      self.assertLessEqual(len(percentages), 3)
      self.assertEqual(sum(percentages.values()), 100)
      for tg in percentages.keys():
        self.assertIn(tg, Tiangan)
