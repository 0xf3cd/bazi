# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_tiangan_relation_utils.py

import random
import pytest
import unittest
import itertools
from typing import Union, Iterable

from src.Defines import Tiangan, Dizhi, Wuxing, TianganRelation, DizhiRelation
from src.Utils import BaziUtils, TianganUtils


@pytest.mark.errorprone
class TestTianganUtils(unittest.TestCase):
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
      empty_result: list[frozenset[Tiangan]] = TianganUtils.find_tiangan_combos([], relation)
      self.assertEqual(len(empty_result), 0)

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.丙, Tiangan.辛},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.冲), 
      [
        {Tiangan.甲, Tiangan.庚},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.甲, Tiangan.丙},
        {Tiangan.甲, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.克), 
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
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.壬, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲), 
      []
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.丁, Tiangan.戊},
        {Tiangan.戊, Tiangan.辛},
        {Tiangan.辛, Tiangan.壬},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克), 
      [
        {Tiangan.戊, Tiangan.壬},
        {Tiangan.壬, Tiangan.丁},
        {Tiangan.丁, Tiangan.辛},
      ]
    ))

  def test_find_tiangan_combos_negative(self) -> None:
    with self.assertRaises(TypeError):
      TianganUtils.find_tiangan_combos(Tiangan.辛, TianganRelation.合) # type: ignore
    with self.assertRaises(TypeError):
      TianganUtils.find_tiangan_combos((Tiangan.甲, Dizhi.子)) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.find_tiangan_combos((Tiangan.甲, Dizhi.子), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.find_tiangan_combos(('甲', '丙', '辛'), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, '辛'), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), '合') # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), 'HE') # type: ignore

    for dz_relation in DizhiRelation:
      with self.assertRaises(AssertionError):
        TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), dz_relation) # type: ignore

    for relation in TianganRelation:
      with self.assertRaises(AssertionError):
        TianganUtils.find_tiangan_combos((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), str(relation)) # type: ignore

    # Invoke the method and do bad things on the result.
    TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合).clear()
    TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲).append(frozenset({Tiangan.壬, Tiangan.丁}))
    sheng_result = TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生)
    sheng_result[0] = frozenset((Tiangan.丁,))
    sheng_result[1] = frozenset((Tiangan.壬, Tiangan.戊))

    # Make sure the method still returns the correct result.
    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.壬, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲), 
      []
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.丁, Tiangan.戊},
        {Tiangan.戊, Tiangan.辛},
        {Tiangan.辛, Tiangan.壬},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.find_tiangan_combos((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克), 
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
      trait1, trait2 = [BaziUtils.tiangan_traits(tg) for tg in combo]
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
      for combo_tuple in itertools.combinations(tiangans, 2):
        if frozenset(combo_tuple) in expected:
          result.append(set(combo_tuple))
      return result

    for _ in range(500):
      tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))

      for combo_fs in TianganUtils.find_tiangan_combos(tiangans, TianganRelation.合):
        self.assertEqual(len(combo_fs), 2)
        tg1, tg2 = tuple(combo_fs)
        self.assertIn(tg1.index - tg2.index, [5, -5])

      for combo_fs in TianganUtils.find_tiangan_combos(tiangans, TianganRelation.冲):
        self.assertEqual(len(combo_fs), 2)
        trait1, trait2 = [BaziUtils.traits(tg) for tg in combo_fs]
        # No Tiangan of `Wuxing.土` is involved in the "Chong" relation.
        self.assertNotEqual(trait1.wuxing, Wuxing.土)
        self.assertNotEqual(trait2.wuxing, Wuxing.土)
        self.assertEqual(trait1.yinyang, trait2.yinyang)
        wx1, wx2 = trait1.wuxing, trait2.wuxing
        self.assertTrue(wx1.destructs(wx2) or wx2.destructs(wx1))

      for combo_fs in TianganUtils.find_tiangan_combos(tiangans, TianganRelation.生):
        self.assertEqual(len(combo_fs), 2)
        # We don't care Tiangan's Yinyang when talking about the "Sheng" relation.
        wx1, wx2 = [BaziUtils.traits(tg).wuxing for tg in combo_fs]
        self.assertTrue(wx1.generates(wx2) or wx2.generates(wx1))

      for combo_fs in TianganUtils.find_tiangan_combos(tiangans, TianganRelation.克):
        self.assertEqual(len(combo_fs), 2)
        # We don't care Tiangan's Yinyang when talking about the "Ke" relation.
        wx1, wx2 = [BaziUtils.traits(tg).wuxing for tg in combo_fs]
        self.assertTrue(wx1.destructs(wx2) or wx2.destructs(wx1))

    for relation in TianganRelation:
      tiangans = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
      combos1: list[frozenset[Tiangan]] = TianganUtils.find_tiangan_combos(tiangans, relation)
      combos2: list[frozenset[Tiangan]] = TianganUtils.find_tiangan_combos(tiangans + tiangans, relation)
      self.assertEqual(len(combos1), len(combos2))
      for combo_fs in combos1:
        self.assertIn(combo_fs, combos2)

      for _ in range(500):
        combos: list[frozenset[Tiangan]] = TianganUtils.find_tiangan_combos(tiangans, relation)
        expected_combos: list[set[Tiangan]] = __find_relation_combos(tiangans, relation)
        self.assertEqual(len(expected_combos), len(combos))
        for combo_fs in combos:
          self.assertIn(combo_fs, expected_combos)

  def test_he(self) -> None:
    with self.assertRaises(AssertionError):
      TianganUtils.he(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.he(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.he('甲', '己') # type: ignore

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
        self.assertEqual(TianganUtils.he(tg1, tg2), expected[frozenset(tg_set)])
        self.assertEqual(TianganUtils.he(tg2, tg1), expected[frozenset(tg_set)])
      else:
        self.assertIsNone(TianganUtils.he(tg1, tg2))
        self.assertIsNone(TianganUtils.he(tg2, tg1))

  def test_chong(self) -> None:
    with self.assertRaises(AssertionError):
      TianganUtils.chong(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.chong(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.chong('甲', '庚') # type: ignore

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      wx1, wx2 = BaziUtils.traits(tg1).wuxing, BaziUtils.traits(tg2).wuxing
      if all(wx is not Wuxing('土') for wx in [wx1, wx2]):
        if abs(tg1.index - tg2.index) == 6:
          self.assertTrue(TianganUtils.chong(tg1, tg2))
          self.assertTrue(TianganUtils.chong(tg2, tg1))
          continue
      # Else, the two Tiangans are not in CHONG relation.
      self.assertFalse(TianganUtils.chong(tg1, tg2))
      self.assertFalse(TianganUtils.chong(tg2, tg1))

  def test_sheng(self) -> None:
    with self.assertRaises(AssertionError):
      TianganUtils.sheng(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.sheng(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.sheng('甲', '庚') # type: ignore

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      wx1, wx2 = BaziUtils.traits(tg1).wuxing, BaziUtils.traits(tg2).wuxing
      if wx1.generates(wx2):
        self.assertTrue(TianganUtils.sheng(tg1, tg2))
        self.assertFalse(TianganUtils.sheng(tg2, tg1))
      else:
        self.assertFalse(TianganUtils.sheng(tg1, tg2))

  def test_ke(self) -> None:
    with self.assertRaises(AssertionError):
      TianganUtils.ke(Tiangan.甲, Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.ke(Dizhi.子, Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.ke('甲', '庚') # type: ignore

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      wx1, wx2 = BaziUtils.traits(tg1).wuxing, BaziUtils.traits(tg2).wuxing
      if wx1.destructs(wx2):
        self.assertTrue(TianganUtils.ke(tg1, tg2))
        self.assertFalse(TianganUtils.ke(tg2, tg1))
      else:
        self.assertFalse(TianganUtils.ke(tg1, tg2))
