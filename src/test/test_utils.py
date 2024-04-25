# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_utils.py

import unittest
from datetime import date, datetime, timedelta
from src import (
  CalendarUtils, TraitTuple, HiddenTianganDict,
  Ganzhi, Tiangan, Dizhi, Wuxing, Yinyang, Shishen, ShierZhangsheng,
)
from src.Utils import BaziUtils


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
      self.assertEqual(BaziUtils.get_tiangan_traits(tg), TraitTuple(expected_wuxing, expected_yinyang))
      self.assertEqual(str(BaziUtils.get_tiangan_traits(tg)), str(expected_yinyang) + str(expected_wuxing))

  def test_dizhi_traits(self) -> None:
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('子')), TraitTuple(Wuxing('水'), Yinyang('阳')))
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('辰')), TraitTuple(Wuxing('土'), Yinyang('阳')))
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('巳')), TraitTuple(Wuxing('火'), Yinyang('阴')))
    self.assertEqual(BaziUtils.get_dizhi_traits(Dizhi('丑')), TraitTuple(Wuxing('土'), Yinyang('阴')))

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
      self.assertEqual(BaziUtils.get_dizhi_traits(dz), TraitTuple(expected_wuxing, expected_yinyang))

  def test_get_hidden_tiangans(self) -> None:
    for dz in Dizhi:
      percentages: HiddenTianganDict = BaziUtils.get_hidden_tiangans(dz)
      self.assertGreaterEqual(len(percentages), 1)
      self.assertLessEqual(len(percentages), 3)
      self.assertEqual(sum(percentages.values()), 100)
      for tg in percentages.keys():
        self.assertIn(tg, Tiangan)

  def test_get_shishen(self) -> None:
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Tiangan.甲), Shishen.比肩)
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Tiangan.乙), Shishen.劫财)
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Dizhi.寅), Shishen.比肩)
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Dizhi.卯), Shishen.劫财)

    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Tiangan.丙), Shishen.食神)
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Dizhi.午), Shishen.伤官)
    
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Tiangan.戊), Shishen.偏财)
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Dizhi.未), Shishen.正财)

    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Tiangan.辛), Shishen.正官)
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Dizhi.申), Shishen.七杀)

    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Tiangan.壬), Shishen.偏印)
    self.assertEqual(BaziUtils.get_shishen(Tiangan.甲, Dizhi.子), Shishen.正印)

  def test_get_nayin_str(self) -> None:
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('甲子')), '海中金')
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('乙丑')), '海中金')
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('丙寅')), '炉中火')

    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('癸卯')), '金箔金')
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('甲辰')), '覆灯火')
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('乙巳')), '覆灯火')
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('丙午')), '天河水')

    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('辛酉')), '石榴木')
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('壬戌')), '大海水')
    self.assertEqual(BaziUtils.get_nayin_str(Ganzhi.from_str('癸亥')), '大海水')

    cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
    for tg in Tiangan:
      for dz in Dizhi:
        gz: Ganzhi = Ganzhi(tg, dz)
        if gz in cycle:
          self.assertEqual(len(BaziUtils.get_nayin_str(gz)), 3)
        else:
          with self.assertRaises(AssertionError):
            BaziUtils.get_nayin_str(gz) # Ganzhis not in the sexagenary cycle don't have nayins.

  def test_shier_zhangsheng(self) -> None:
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('甲子')), ShierZhangsheng.沐浴)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('甲亥')), ShierZhangsheng.长生)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('甲午')), ShierZhangsheng.死)

    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('乙亥')), ShierZhangsheng.死)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('乙丑')), ShierZhangsheng.衰)

    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('丙午')), ShierZhangsheng.帝旺)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('丙未')), ShierZhangsheng.衰)

    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('丁未')), ShierZhangsheng.冠带)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('丁戌')), ShierZhangsheng.养)

    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('戊戌')), ShierZhangsheng.墓)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('戊亥')), ShierZhangsheng.绝)

    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('己亥')), ShierZhangsheng.胎)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('庚辰')), ShierZhangsheng.养)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('辛酉')), ShierZhangsheng.临官)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('壬申')), ShierZhangsheng.长生)
    self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_str('癸卯')), ShierZhangsheng.长生)

    for dz in Dizhi:
      self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_strs('丙', str(dz))),
                       BaziUtils.get_shier_zhangsheng(*Ganzhi.from_strs('戊', str(dz))))
      self.assertEqual(BaziUtils.get_shier_zhangsheng(*Ganzhi.from_strs('丁', str(dz))),
                       BaziUtils.get_shier_zhangsheng(*Ganzhi.from_strs('己', str(dz))))
