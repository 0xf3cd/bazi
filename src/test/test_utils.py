# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_utils.py

import random
import unittest
import itertools
from typing import Union, Optional, Iterable
from datetime import date, datetime, timedelta

from src import (
  CalendarUtils, TraitTuple, HiddenTianganDict,
  Ganzhi, Tiangan, Dizhi, Wuxing, Yinyang, Shishen, ShierZhangsheng, TianganRelation, DizhiRelation,
  Rules,
)
from src.Utils import BaziUtils, TianganRelationUtils, DizhiRelationUtils


class TestBaziUtils(unittest.TestCase):
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

  def test_get_12zhangsheng(self) -> None:
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('甲子')), ShierZhangsheng.沐浴)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('甲亥')), ShierZhangsheng.长生)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('甲午')), ShierZhangsheng.死)

    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('乙亥')), ShierZhangsheng.死)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('乙丑')), ShierZhangsheng.衰)

    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('丙午')), ShierZhangsheng.帝旺)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('丙未')), ShierZhangsheng.衰)

    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('丁未')), ShierZhangsheng.冠带)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('丁戌')), ShierZhangsheng.养)

    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('戊戌')), ShierZhangsheng.墓)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('戊亥')), ShierZhangsheng.绝)

    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('己亥')), ShierZhangsheng.胎)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('庚辰')), ShierZhangsheng.养)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('辛酉')), ShierZhangsheng.临官)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('壬申')), ShierZhangsheng.长生)
    self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_str('癸卯')), ShierZhangsheng.长生)

    for dz in Dizhi:
      self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_strs('丙', str(dz))),
                       BaziUtils.get_12zhangsheng(*Ganzhi.from_strs('戊', str(dz))))
      self.assertEqual(BaziUtils.get_12zhangsheng(*Ganzhi.from_strs('丁', str(dz))),
                       BaziUtils.get_12zhangsheng(*Ganzhi.from_strs('己', str(dz))))
      
  def test_find_12zhangsheng_dizhi(self) -> None:
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('甲'), ShierZhangsheng.沐浴), Dizhi('子'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('甲'), ShierZhangsheng.长生), Dizhi('亥'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('甲'), ShierZhangsheng.死), Dizhi('午'))

    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('乙'), ShierZhangsheng.死), Dizhi('亥'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('乙'), ShierZhangsheng.衰), Dizhi('丑'))

    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('丙'), ShierZhangsheng.帝旺), Dizhi('午'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('丙'), ShierZhangsheng.衰), Dizhi('未'))

    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('丁'), ShierZhangsheng.冠带), Dizhi('未'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('丁'), ShierZhangsheng.养), Dizhi('戌'))

    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('戊'), ShierZhangsheng.墓), Dizhi('戌'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('戊'), ShierZhangsheng.绝), Dizhi('亥'))

    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('己'), ShierZhangsheng.胎), Dizhi('亥'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('庚'), ShierZhangsheng.养), Dizhi('辰'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('辛'), ShierZhangsheng.临官), Dizhi('酉'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('壬'), ShierZhangsheng.长生), Dizhi('申'))
    self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('癸'), ShierZhangsheng.长生), Dizhi('卯'))

    for place in ShierZhangsheng:
      self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('丙'), place), 
                       BaziUtils.find_12zhangsheng_dizhi(Tiangan('戊'), place))
      self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(Tiangan('丁'), place), 
                       BaziUtils.find_12zhangsheng_dizhi(Tiangan('己'), place))
      
  def test_12zhangsheng_consistency(self) -> None:
    for tg, dz in itertools.product(Tiangan, Dizhi):
      zs: ShierZhangsheng = BaziUtils.get_12zhangsheng(tg, dz)
      self.assertEqual(BaziUtils.find_12zhangsheng_dizhi(tg, zs), dz)
    for tg, zs in itertools.product(Tiangan, ShierZhangsheng):
      dz: Dizhi = BaziUtils.find_12zhangsheng_dizhi(tg, zs)
      self.assertEqual(BaziUtils.get_12zhangsheng(tg, dz), zs)

  def test_get_tiangan_lu(self) -> None:
    for tg in Tiangan:
      self.assertEqual(BaziUtils.get_tiangan_lu(tg), BaziUtils.find_12zhangsheng_dizhi(tg, ShierZhangsheng('临官')))


class TestTianganRelationUtils(unittest.TestCase):
  TgCmpType = Union[list[set[Tiangan]], Iterable[frozenset[Tiangan]]]    
  @staticmethod
  def __tg_equal(l1: TgCmpType, l2: TgCmpType) -> bool:
    _l1 = list(l1)
    _l2 = list(l2)
    if len(_l1) != len(_l2):
      return False
    for s in _l1:
      if s not in _l2:
        return False
    return True

  def test_find_tiangan_combos_basic(self) -> None:
    for relation in TianganRelation:
      empty_result: list[frozenset[Tiangan]] = TianganRelationUtils.find_tiangan_combos([], relation)
      self.assertEqual(len(empty_result), 0)

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.丙, Tiangan.辛},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.冲), 
      [
        {Tiangan.甲, Tiangan.庚},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.甲, Tiangan.丙},
        {Tiangan.甲, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.克), 
      [
        {Tiangan.庚, Tiangan.甲},
        {Tiangan.辛, Tiangan.甲},
        {Tiangan.丙, Tiangan.庚},
        {Tiangan.丙, Tiangan.辛},
        {Tiangan.丁, Tiangan.庚},
        {Tiangan.丁, Tiangan.辛},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.壬, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲), 
      []
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.丁, Tiangan.戊},
        {Tiangan.戊, Tiangan.辛},
        {Tiangan.辛, Tiangan.壬},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克), 
      [
        {Tiangan.戊, Tiangan.壬},
        {Tiangan.壬, Tiangan.丁},
        {Tiangan.丁, Tiangan.辛},
      ]
    ))

  def test_find_tiangan_combos_negative(self) -> None:
    with self.assertRaises(TypeError):
      TianganRelationUtils.find_tiangan_combos(Tiangan.辛, TianganRelation.合) # type: ignore
    with self.assertRaises(TypeError):
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Dizhi.子)) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Dizhi.子), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.find_tiangan_combos(('甲', '丙', '辛'), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, '辛'), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), '合') # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), 'HE') # type: ignore

    # Invoke the method and do bad things on the result.
    TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合).clear()
    TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲).append(frozenset({Tiangan.壬, Tiangan.丁}))
    sheng_result = TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生)
    sheng_result[0] = frozenset((Tiangan.丁,))
    sheng_result[1] = frozenset((Tiangan.壬, Tiangan.戊))

    # Make sure the method still returns the correct result.
    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.壬, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲), 
      []
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.丁, Tiangan.戊},
        {Tiangan.戊, Tiangan.辛},
        {Tiangan.辛, Tiangan.壬},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganRelationUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克), 
      [
        {Tiangan.戊, Tiangan.壬},
        {Tiangan.壬, Tiangan.丁},
        {Tiangan.丁, Tiangan.辛},
      ]
    ))

  def test_find_tiangan_combos_correctness(self) -> None:
    # Generate the expected relation combos/pairs, which are used later in this test.
    expected_he:    set[frozenset[Tiangan]] = set()
    expected_chong: set[frozenset[Tiangan]] = set()
    expected_sheng: set[frozenset[Tiangan]] = set()
    expected_ke:    set[frozenset[Tiangan]] = set()
    for combo in itertools.product(Tiangan, Tiangan):
      tg1, tg2 = combo
      if tg1 == tg2:
        continue
      trait1, trait2 = [BaziUtils.get_tiangan_traits(tg) for tg in combo]
      wx1, wx2 = trait1.wuxing, trait2.wuxing

      if abs(tg1.index - tg2.index) == 5: # Check "He" relation. 合。
        expected_he.add(frozenset(combo))
      if all(wx is not Wuxing.土 for wx in [wx1, wx2]): # Check "Chong" relation. 冲。
        if abs(tg1.index - tg2.index) == 6:
          expected_chong.add(frozenset(combo))
      if wx1.generates(wx2) or wx2.generates(wx1): # Check "Sheng" relation. 生。
        expected_sheng.add(frozenset(combo))
      if wx1.destructs(wx2) or wx2.destructs(wx1): # Check "Ke" relation. 克。
        expected_ke.add(frozenset(combo))

    def __find_relation_combos(tiangans: list[Tiangan], relation: TianganRelation) -> list[set[Tiangan]]:
      expected: set[frozenset[Tiangan]] = expected_he
      if relation is TianganRelation.冲:
        expected = expected_chong
      if relation is TianganRelation.生:
        expected = expected_sheng
      if relation is TianganRelation.克:
        expected = expected_ke

      result: list[set[Tiangan]] = []
      for combo in itertools.combinations(tiangans, 2):
        if frozenset(combo) in expected:
          result.append(set(combo))
      return result

    for _ in range(100):
      tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))

      for combo in TianganRelationUtils.find_tiangan_combos(tiangans, TianganRelation.合):
        self.assertEqual(len(combo), 2)
        tg1, tg2 = tuple(combo)
        self.assertIn(tg1.index - tg2.index, [5, -5])

      for combo in TianganRelationUtils.find_tiangan_combos(tiangans, TianganRelation.冲):
        self.assertEqual(len(combo), 2)
        trait1, trait2 = [BaziUtils.get_tiangan_traits(tg) for tg in combo]
        # No Tiangan of `Wuxing.土` is involved in the "Chong" relation.
        self.assertNotEqual(trait1.wuxing, Wuxing.土)
        self.assertNotEqual(trait2.wuxing, Wuxing.土)
        self.assertEqual(trait1.yinyang, trait2.yinyang)
        wx1, wx2 = trait1.wuxing, trait2.wuxing
        self.assertTrue(wx1.destructs(wx2) or wx2.destructs(wx1))

      for combo in TianganRelationUtils.find_tiangan_combos(tiangans, TianganRelation.生):
        self.assertEqual(len(combo), 2)
        # We don't care Tiangan's Yinyang when talking about the "Sheng" relation.
        wx1, wx2 = [BaziUtils.get_tiangan_traits(tg).wuxing for tg in combo]
        self.assertTrue(wx1.generates(wx2) or wx2.generates(wx1))

      for combo in TianganRelationUtils.find_tiangan_combos(tiangans, TianganRelation.克):
        self.assertEqual(len(combo), 2)
        # We don't care Tiangan's Yinyang when talking about the "Ke" relation.
        wx1, wx2 = [BaziUtils.get_tiangan_traits(tg).wuxing for tg in combo]
        self.assertTrue(wx1.destructs(wx2) or wx2.destructs(wx1))

    for relation in TianganRelation:
      tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
      combos1: list[frozenset[Tiangan]] = TianganRelationUtils.find_tiangan_combos(tiangans, relation)
      combos2: list[frozenset[Tiangan]] = TianganRelationUtils.find_tiangan_combos(tiangans + tiangans, relation)
      self.assertEqual(len(combos1), len(combos2))
      for combo in combos1:
        self.assertIn(combo, combos2)

      for _ in range(100):
        combos: list[frozenset[Tiangan]] = TianganRelationUtils.find_tiangan_combos(tiangans, relation)
        expected_combos: list[set[Tiangan]] = __find_relation_combos(tiangans, relation)
        self.assertEqual(len(expected_combos), len(combos))
        for combo in combos:
          self.assertIn(combo, expected_combos)

  def test_he(self) -> None:
    with self.assertRaises(AssertionError):
      TianganRelationUtils.he(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.he(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.he('甲', '己') # type: ignore

    expected: dict[frozenset[Tiangan], Wuxing] = {
      frozenset((Tiangan.甲, Tiangan.己)) : Wuxing.土,
      frozenset((Tiangan.乙, Tiangan.庚)) : Wuxing.金,
      frozenset((Tiangan.丙, Tiangan.辛)) : Wuxing.水,
      frozenset((Tiangan.丁, Tiangan.壬)) : Wuxing.木,
      frozenset((Tiangan.戊, Tiangan.癸)) : Wuxing.火,
    }

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      tg_set: set[Tiangan] = {tg1, tg2}
      if any(tg_set == s for s in expected):
        self.assertEqual(TianganRelationUtils.he(tg1, tg2), expected[frozenset(tg_set)])
        self.assertEqual(TianganRelationUtils.he(tg2, tg1), expected[frozenset(tg_set)])
      else:
        self.assertIsNone(TianganRelationUtils.he(tg1, tg2))
        self.assertIsNone(TianganRelationUtils.he(tg2, tg1))

  def test_chong(self) -> None:
    with self.assertRaises(AssertionError):
      TianganRelationUtils.chong(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.chong(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.chong('甲', '庚') # type: ignore

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      wx1, wx2 = BaziUtils.get_tiangan_traits(tg1).wuxing, BaziUtils.get_tiangan_traits(tg2).wuxing
      if all(wx is not Wuxing('土') for wx in [wx1, wx2]):
        if abs(tg1.index - tg2.index) == 6:
          self.assertTrue(TianganRelationUtils.chong(tg1, tg2))
          self.assertTrue(TianganRelationUtils.chong(tg2, tg1))
          continue
      # Else, the two Tiangans are not in CHONG relation.
      self.assertFalse(TianganRelationUtils.chong(tg1, tg2))
      self.assertFalse(TianganRelationUtils.chong(tg2, tg1))

  def test_sheng(self) -> None:
    with self.assertRaises(AssertionError):
      TianganRelationUtils.sheng(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.sheng(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.sheng('甲', '庚') # type: ignore

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      wx1, wx2 = BaziUtils.get_tiangan_traits(tg1).wuxing, BaziUtils.get_tiangan_traits(tg2).wuxing
      if wx1.generates(wx2):
        self.assertTrue(TianganRelationUtils.sheng(tg1, tg2))
        self.assertFalse(TianganRelationUtils.sheng(tg2, tg1))
      else:
        self.assertFalse(TianganRelationUtils.sheng(tg1, tg2))

  def test_ke(self) -> None:
    with self.assertRaises(AssertionError):
      TianganRelationUtils.ke(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.ke(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganRelationUtils.ke('甲', '庚') # type: ignore

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      wx1, wx2 = BaziUtils.get_tiangan_traits(tg1).wuxing, BaziUtils.get_tiangan_traits(tg2).wuxing
      if wx1.destructs(wx2):
        self.assertTrue(TianganRelationUtils.ke(tg1, tg2))
        self.assertFalse(TianganRelationUtils.ke(tg2, tg1))
      else:
        self.assertFalse(TianganRelationUtils.ke(tg1, tg2))


class TestDizhiRelationUtils(unittest.TestCase):
  def test_find_dizhi_combos_negative(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.find_dizhi_combos(Dizhi.子, DizhiRelation.生) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.find_dizhi_combos([Dizhi.子, Dizhi.午]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.find_dizhi_combos(['甲', '己'], DizhiRelation.克) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.find_dizhi_combos([Dizhi.子, Dizhi.午], '生') # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.find_dizhi_combos([Dizhi.子, Dizhi.午], TianganRelation.冲) # type: ignore

  DzCmpType = Union[list[set[Dizhi]], Iterable[frozenset[Dizhi]]]
  @staticmethod
  def __dz_equal(l1: DzCmpType, l2: DzCmpType) -> bool:
    _l1 = list(l1)
    _l2 = list(l2)
    if len(_l1) != len(_l2):
      return False
    for s in _l1:
      if s not in _l2:
        return False
    return True

  def test_find_dizhi_combos_sanhui(self) -> None:
    sanhui_combos: list[frozenset[Dizhi]] = [
      frozenset((Dizhi.from_index(2), Dizhi.from_index(3), Dizhi.from_index(4))),
      frozenset((Dizhi.from_index(5), Dizhi.from_index(6), Dizhi.from_index(7))),
      frozenset((Dizhi.from_index(8), Dizhi.from_index(9), Dizhi.from_index(10))),
      frozenset((Dizhi.from_index(11), Dizhi.from_index(0), Dizhi.from_index(1))),
    ]

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.三会),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.三会),
      [set(c) for c in sanhui_combos],
    ))
    
    for _ in range(100):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.三会)
      expected_result: list[set[Dizhi]] = [set(c) for c in sanhui_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_sanhui(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhui(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhui(Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhui(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhui((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhui({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhui([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.sanhui('亥', '子', '丑') # type: ignore

    dizhi_tuples: list[tuple[Dizhi, Dizhi, Dizhi]] = [
      (Dizhi.寅, Dizhi.卯, Dizhi.辰), # Spring / 春
      (Dizhi.巳, Dizhi.午, Dizhi.未), # Summer / 夏
      (Dizhi.申, Dizhi.酉, Dizhi.戌), # Fall   / 秋
      (Dizhi.亥, Dizhi.子, Dizhi.丑), # Winter / 冬
    ]
    expected: dict[frozenset[Dizhi], Wuxing] = { 
      frozenset(dizhis) : BaziUtils.get_dizhi_traits(dizhis[0]).wuxing for dizhis in dizhi_tuples 
    }
    
    for dizhis in itertools.product(Dizhi, repeat=3):
      fs: frozenset[Dizhi] = frozenset(dizhis)
      if fs in expected:
        for combo in itertools.permutations(dizhis):
          self.assertEqual(DizhiRelationUtils.sanhui(*combo), expected[fs])
      else:
        for combo in itertools.permutations(dizhis):
          self.assertIsNone(DizhiRelationUtils.sanhui(*dizhis))

  def test_find_dizhi_combos_liuhe(self) -> None:
    liuhe_combos: list[frozenset[Dizhi]] = [
      frozenset((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
    ]

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.六合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.六合),
      liuhe_combos,
    ))

    for _ in range(100):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.六合)
      expected_result: list[set[Dizhi]] = [set(c) for c in liuhe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_liuhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.liuhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.liuhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.liuhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.liuhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.liuhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.liuhe('亥', '子') # type: ignore

    liuhe_combos: list[frozenset[Dizhi]] = [
      frozenset((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
    ]

    for dz1, dz2 in itertools.permutations(Dizhi, 2):
      liuhe_result: Optional[Wuxing] = DizhiRelationUtils.liuhe(dz1, dz2)
      liuhe_result2: Optional[Wuxing] = DizhiRelationUtils.liuhe(dz2, dz1)
      self.assertEqual(liuhe_result, liuhe_result2)
      
      if frozenset((dz1, dz2)) in liuhe_combos:
        wx1, wx2 = BaziUtils.get_dizhi_traits(dz1).wuxing, BaziUtils.get_dizhi_traits(dz2).wuxing
        if wx1.generates(wx2):
          self.assertEqual(liuhe_result, wx2)
        elif wx2.generates(wx1):
          self.assertEqual(liuhe_result, wx1)
        else:
          self.assertTrue(wx1.destructs(wx2) or wx2.destructs(wx1))
          if {dz1, dz2} == {Dizhi.子, Dizhi.丑}:
            self.assertEqual(liuhe_result, Wuxing.土)
          elif {dz1, dz2} == {Dizhi.卯, Dizhi.戌}:
            self.assertEqual(liuhe_result, Wuxing.火)
          else:
            self.assertEqual({dz1, dz2}, {Dizhi.申, Dizhi.巳})
            self.assertEqual(liuhe_result, Wuxing.水)
      else:
        self.assertIsNone(liuhe_result)

  def test_find_dizhi_combos_anhe(self) -> None:
    anhe_combos: list[frozenset[Dizhi]] = [ # 天干五合对应的地支暗合，5组。
      frozenset((BaziUtils.get_tiangan_lu(tg1), BaziUtils.get_tiangan_lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganRelationUtils.he(tg1, tg2) is not None
    ] + [ # `NORMAL_EXTENDED` 中额外的1组。
      frozenset((Dizhi.寅, Dizhi.丑)), 
    ]

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.暗合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.暗合),
      anhe_combos,
    ))

    for _ in range(100):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.暗合)
      expected_result: list[set[Dizhi]] = [set(c) for c in anhe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_anhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.anhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.anhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.anhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.anhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.anhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.anhe('亥', '子') # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.anhe(Dizhi.子, Dizhi.辰, Rules.AnheDef.NORMAL + 100) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.anhe(Dizhi.子, Dizhi.辰, definition='Rules.AnheDef.NORMAL') # type: ignore

    normal_combos: list[frozenset[Dizhi]] = [
      frozenset((BaziUtils.get_tiangan_lu(tg1), BaziUtils.get_tiangan_lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganRelationUtils.he(tg1, tg2) is not None
    ] 
    
    normal_extended_combos: list[frozenset[Dizhi]] = normal_combos + [
      frozenset((Dizhi.寅, Dizhi.丑)), 
    ]

    mangpai_combos: list[frozenset[Dizhi]] = [
      frozenset((Dizhi.寅, Dizhi.丑)), 
      frozenset((Dizhi.午, Dizhi.亥)), 
      frozenset((Dizhi.卯, Dizhi.申)), 
    ]

    expected: dict[Rules.AnheDef, list[frozenset[Dizhi]]] = {
      Rules.AnheDef.NORMAL: normal_combos,
      Rules.AnheDef.NORMAL_EXTENDED: normal_extended_combos,
      Rules.AnheDef.MANGPAI: mangpai_combos
    }

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      for anhe_def in Rules.AnheDef:
        self.assertEqual(DizhiRelationUtils.anhe(dz1, dz2, definition=anhe_def), frozenset((dz1, dz2)) in expected[anhe_def])
        self.assertEqual(DizhiRelationUtils.anhe(dz1, dz2, definition=anhe_def), DizhiRelationUtils.anhe(dz2, dz1, definition=anhe_def))

    # Ensure the default definition is `NORMAL`.
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiRelationUtils.anhe(dz1, dz2), frozenset((dz1, dz2)) in normal_combos)
      self.assertEqual(DizhiRelationUtils.anhe(dz1, dz2), DizhiRelationUtils.anhe(dz2, dz1))

  def test_find_dizhi_combos_tonghe(self) -> None:
    tonghe_combos: set[frozenset[Dizhi]] = set()
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      hidden1, hidden2 = BaziUtils.get_hidden_tiangans(dz1), BaziUtils.get_hidden_tiangans(dz2)
      if len(hidden1) != len(hidden2):
        continue
      expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1.keys()]
      if all(tg in hidden2 for tg in expected_hidden2):
        tonghe_combos.add(frozenset((dz1, dz2)))

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.通合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.通合),
      tonghe_combos,
    ))

    for _ in range(100):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.通合)
      expected_result: list[set[Dizhi]] = [set(c) for c in tonghe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_tonghe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tonghe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tonghe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tonghe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tonghe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tonghe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.tonghe('亥', '子') # type: ignore

    tonghe_combos: set[frozenset[Dizhi]] = set()
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      hidden1, hidden2 = BaziUtils.get_hidden_tiangans(dz1), BaziUtils.get_hidden_tiangans(dz2)
      if len(hidden1) != len(hidden2):
        continue
      expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1.keys()]
      if all(tg in hidden2 for tg in expected_hidden2):
        tonghe_combos.add(frozenset((dz1, dz2)))

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiRelationUtils.tonghe(dz1, dz2), frozenset((dz1, dz2)) in tonghe_combos)
      self.assertEqual(DizhiRelationUtils.tonghe(dz1, dz2), DizhiRelationUtils.tonghe(dz2, dz1))

  def test_find_dizhi_combos_tongluhe(self) -> None:
    tongluhe_combos: list[frozenset[Dizhi]] = [ # 天干五合对应的地支禄身。
      frozenset((BaziUtils.get_tiangan_lu(tg1), BaziUtils.get_tiangan_lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganRelationUtils.he(tg1, tg2) is not None
    ]

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.通禄合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.通禄合),
      tongluhe_combos,
    ))

    for _ in range(100):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.通禄合)
      expected_result: list[set[Dizhi]] = [set(c) for c in tongluhe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_tongluhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tongluhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tongluhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tongluhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tongluhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.tongluhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.tongluhe('亥', '子') # type: ignore

    tongluhe_combos: list[frozenset[Dizhi]] = [ # 天干五合对应的地支禄身。
      frozenset((BaziUtils.get_tiangan_lu(tg1), BaziUtils.get_tiangan_lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganRelationUtils.he(tg1, tg2) is not None
    ]

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiRelationUtils.tongluhe(dz1, dz2), frozenset((dz1, dz2)) in tongluhe_combos)
      self.assertEqual(DizhiRelationUtils.tongluhe(dz1, dz2), DizhiRelationUtils.tongluhe(dz2, dz1))

  @staticmethod
  def __gen_sanhe_table() -> dict[frozenset[Dizhi], Wuxing]:
    return {
      frozenset((
        dz, 
        Dizhi.from_index((dz.index + 4) % 12), 
        Dizhi.from_index((dz.index - 4) % 12),
      )) : BaziUtils.get_dizhi_traits(dz).wuxing
      for dz in [Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉')]
    }

  def test_find_dizhi_combos_sanhe(self) -> None:
    sanhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_sanhe_table()

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.三合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.三合),
      sanhe_table.keys(),
    ))

    for _ in range(100):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.三合)
      expected_result: list[set[Dizhi]] = [set(c) for c in sanhe_table if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_sanhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhe(Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhe((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhe({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.sanhe([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.sanhe('亥', '子', '丑') # type: ignore

    sanhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_sanhe_table()
    
    for dizhis in itertools.product(Dizhi, repeat=3):
      fs: frozenset[Dizhi] = frozenset(dizhis)
      if fs in sanhe_table:
        for combo in itertools.permutations(dizhis):
          self.assertEqual(DizhiRelationUtils.sanhe(*combo), sanhe_table[fs])
      else:
        for combo in itertools.permutations(dizhis):
          self.assertIsNone(DizhiRelationUtils.sanhe(*dizhis))

  @staticmethod
  def __gen_banhe_table() -> dict[frozenset[Dizhi], Wuxing]:
    pivots: set[Dizhi] = set((Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉'))) # 四中神
    sanhe_table: dict[frozenset[Dizhi], Wuxing] = TestDizhiRelationUtils.__gen_sanhe_table()

    d: dict[frozenset[Dizhi], Wuxing] = {}
    for sanhe_dizhis, wx in sanhe_table.items():
      for dz1, dz2 in itertools.combinations(sanhe_dizhis, 2):
        if any(dz in pivots for dz in (dz1, dz2)): # 半合局需要出现中神
          d[frozenset((dz1, dz2))] = wx
    return d

  def test_find_dizhi_combos_banhe(self) -> None:
    banhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_banhe_table()

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.半合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.半合),
      banhe_table.keys()
    ))

    for _ in range(100):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.半合)
      expected_result: list[set[Dizhi]] = [set(c) for c in banhe_table if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_banhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiRelationUtils.banhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.banhe(Dizhi.子, Dizhi.辰, Dizhi.申) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.banhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.banhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiRelationUtils.banhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiRelationUtils.banhe('亥', '子') # type: ignore

    banhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_banhe_table()

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiRelationUtils.banhe(dz1, dz2), banhe_table.get(frozenset((dz1, dz2)), None))
      self.assertEqual(DizhiRelationUtils.banhe(dz1, dz2), DizhiRelationUtils.banhe(dz2, dz1))

  def test_find_dizhi_combos_xing(self) -> None:
    xing_expected: list[dict[Dizhi, int]] = [ # 辰午酉亥自刑
      {
        dz : 2,
      } for dz in [Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥]
    ] + [ # 其他相刑
      { Dizhi.子 : 1, Dizhi.卯 : 1, },
      { Dizhi.寅 : 1, Dizhi.巳 : 1, Dizhi.申 : 1, },
      { Dizhi.丑 : 1, Dizhi.未 : 1, Dizhi.戌 : 1, },
    ]

    def __find_qualified(dizhis: list[Dizhi]) -> list[set[Dizhi]]:
      ret: list[set[Dizhi]] = []
      for required in xing_expected:
        count = lambda dz : sum(dz == d for d in dizhis)
        if all(count(dz) >= required[dz] for dz in required):
          ret.append(set(required.keys())) 
      return ret

    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos([], DizhiRelation.刑),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.刑),
      [{Dizhi.子, Dizhi.卯}, {Dizhi.寅, Dizhi.巳, Dizhi.申}, {Dizhi.丑, Dizhi.未, Dizhi.戌}],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiRelationUtils.find_dizhi_combos(list(Dizhi) + [Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥], DizhiRelation.刑),
      [set(d.keys()) for d in xing_expected]
    ))

    for _ in range(100):
      dizhis: list[Dizhi] = [] 
      for _ in range(random.randint(1, 4)):
        dizhis += random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiRelationUtils.find_dizhi_combos(dizhis, DizhiRelation.刑)
      expected_result: list[set[Dizhi]] = __find_qualified(dizhis)
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_xing(self) -> None:
    # DizhiRelationUtils.xing(definition=Rules.XingDef.LOOSE)
    pass
