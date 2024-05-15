# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_tiangan_relation_utils.py

import random
import itertools
from typing import Union, Iterable

import pytest
import unittest

from src.Common import TianganCombo, TianganRelationCombos, TianganRelationDiscovery
from src.Defines import Tiangan, Dizhi, Wuxing, TianganRelation, DizhiRelation
from src.Utils import BaziUtils, TianganUtils


class TestTianganUtils(unittest.TestCase):
  TgCmpType = Union[list[set[Tiangan]], Iterable[TianganCombo]]    
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

  def test_search_basic(self) -> None:
    for relation in TianganRelation:
      empty_result: TianganRelationCombos = TianganUtils.search([], relation)
      self.assertEqual(len(empty_result), 0)

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.丙, Tiangan.辛},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.冲), 
      [
        {Tiangan.甲, Tiangan.庚},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.甲, Tiangan.丙},
        {Tiangan.甲, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.克), 
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
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.壬, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲), 
      []
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.丁, Tiangan.戊},
        {Tiangan.戊, Tiangan.辛},
        {Tiangan.辛, Tiangan.壬},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克), 
      [
        {Tiangan.戊, Tiangan.壬},
        {Tiangan.壬, Tiangan.丁},
        {Tiangan.丁, Tiangan.辛},
      ]
    ))

  def test_search_negative(self) -> None:
    with self.assertRaises(TypeError):
      TianganUtils.search(Tiangan.辛, TianganRelation.合) # type: ignore
    with self.assertRaises(TypeError):
      TianganUtils.search((Tiangan.甲, Dizhi.子)) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.search((Tiangan.甲, Dizhi.子), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.search(('甲', '丙', '辛'), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, '辛'), TianganRelation.合) # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), '合') # type: ignore
    with self.assertRaises(AssertionError):
      TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), 'HE') # type: ignore

    for dz_relation in DizhiRelation:
      with self.assertRaises(AssertionError):
        TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), dz_relation) # type: ignore

    for relation in TianganRelation:
      with self.assertRaises(AssertionError):
        TianganUtils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), str(relation)) # type: ignore

    # Invoke the method and do bad things on the result.
    # TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合).clear()
    # TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲).append(TianganCombo({Tiangan.壬, Tiangan.丁}))
    # sheng_result = TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生)
    # sheng_result[0] = TianganCombo((Tiangan.丁,))
    # sheng_result[1] = TianganCombo((Tiangan.壬, Tiangan.戊))
    #
    # No need to do bad things again since the return type `tuple` is immutable.

    # Make sure the method still returns the correct result.
    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合), 
      [
        {Tiangan.壬, Tiangan.丁},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲), 
      []
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生), 
      [
        {Tiangan.丁, Tiangan.戊},
        {Tiangan.戊, Tiangan.辛},
        {Tiangan.辛, Tiangan.壬},
      ]
    ))

    self.assertTrue(self.__tg_equal(
      TianganUtils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克), 
      [
        {Tiangan.戊, Tiangan.壬},
        {Tiangan.壬, Tiangan.丁},
        {Tiangan.丁, Tiangan.辛},
      ]
    ))

  @pytest.mark.slow
  def test_search_correctness(self) -> None:
    # Generate the expected relation combos/pairs, which are used later in this test.
    expected_he:    set[TianganCombo] = set()
    expected_chong: set[TianganCombo] = set()
    expected_sheng: set[TianganCombo] = set()
    expected_ke:    set[TianganCombo] = set()
    for combo in itertools.product(Tiangan, Tiangan):
      tg1, tg2 = combo
      if tg1 == tg2:
        continue
      trait1, trait2 = [BaziUtils.tiangan_traits(tg) for tg in combo]
      wx1, wx2 = trait1.wuxing, trait2.wuxing

      if abs(tg1.index - tg2.index) == 5: # Check "He" relation. 合。
        expected_he.add(TianganCombo(combo))
      if all(wx is not Wuxing.土 for wx in [wx1, wx2]): # Check "Chong" relation. 冲。
        if abs(tg1.index - tg2.index) == 6:
          expected_chong.add(TianganCombo(combo))
      if wx1.generates(wx2) or wx2.generates(wx1): # Check "Sheng" relation. 生。
        expected_sheng.add(TianganCombo(combo))
      if wx1.destructs(wx2) or wx2.destructs(wx1): # Check "Ke" relation. 克。
        expected_ke.add(TianganCombo(combo))

    def __find_relation_combos(tiangans: list[Tiangan], relation: TianganRelation) -> list[set[Tiangan]]:
      expected: set[TianganCombo] = expected_he
      if relation is TianganRelation.冲:
        expected = expected_chong
      if relation is TianganRelation.生:
        expected = expected_sheng
      if relation is TianganRelation.克:
        expected = expected_ke

      result: list[set[Tiangan]] = []
      for combo_tuple in itertools.combinations(tiangans, 2):
        if TianganCombo(combo_tuple) in expected:
          result.append(set(combo_tuple))
      return result

    for _ in range(512):
      tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))

      for combo_fs in TianganUtils.search(tiangans, TianganRelation.合):
        self.assertEqual(len(combo_fs), 2)
        tg1, tg2 = tuple(combo_fs)
        self.assertIn(tg1.index - tg2.index, [5, -5])

      for combo_fs in TianganUtils.search(tiangans, TianganRelation.冲):
        self.assertEqual(len(combo_fs), 2)
        trait1, trait2 = [BaziUtils.traits(tg) for tg in combo_fs]
        # No Tiangan of `Wuxing.土` is involved in the "Chong" relation.
        self.assertNotEqual(trait1.wuxing, Wuxing.土)
        self.assertNotEqual(trait2.wuxing, Wuxing.土)
        self.assertEqual(trait1.yinyang, trait2.yinyang)
        wx1, wx2 = trait1.wuxing, trait2.wuxing
        self.assertTrue(wx1.destructs(wx2) or wx2.destructs(wx1))

      for combo_fs in TianganUtils.search(tiangans, TianganRelation.生):
        self.assertEqual(len(combo_fs), 2)
        # We don't care Tiangan's Yinyang when talking about the "Sheng" relation.
        wx1, wx2 = [BaziUtils.traits(tg).wuxing for tg in combo_fs]
        self.assertTrue(wx1.generates(wx2) or wx2.generates(wx1))

      for combo_fs in TianganUtils.search(tiangans, TianganRelation.克):
        self.assertEqual(len(combo_fs), 2)
        # We don't care Tiangan's Yinyang when talking about the "Ke" relation.
        wx1, wx2 = [BaziUtils.traits(tg).wuxing for tg in combo_fs]
        self.assertTrue(wx1.destructs(wx2) or wx2.destructs(wx1))

    for relation in TianganRelation:
      tiangans = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
      combos1: TianganRelationCombos = TianganUtils.search(tiangans, relation)
      combos2: TianganRelationCombos = TianganUtils.search(tiangans + tiangans, relation)
      self.assertEqual(len(combos1), len(combos2))
      for combo_fs in combos1:
        self.assertIn(combo_fs, combos2)

      for _ in range(512):
        combos: TianganRelationCombos = TianganUtils.search(tiangans, relation)
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

    expected: dict[TianganCombo, Wuxing] = {
      TianganCombo((Tiangan.甲, Tiangan.己)) : Wuxing.土,
      TianganCombo((Tiangan.乙, Tiangan.庚)) : Wuxing.金,
      TianganCombo((Tiangan.丙, Tiangan.辛)) : Wuxing.水,
      TianganCombo((Tiangan.丁, Tiangan.壬)) : Wuxing.木,
      TianganCombo((Tiangan.戊, Tiangan.癸)) : Wuxing.火,
    }

    for tg1, tg2 in itertools.product(Tiangan, Tiangan):
      tg_set: set[Tiangan] = {tg1, tg2}
      if any(tg_set == s for s in expected):
        self.assertEqual(TianganUtils.he(tg1, tg2), expected[TianganCombo(tg_set)])
        self.assertEqual(TianganUtils.he(tg2, tg1), expected[TianganCombo(tg_set)])
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

  @pytest.mark.slow
  def test_discover(self) -> None:
    for _ in range(512):
      tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan))) + \
                                random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
      discovery: TianganRelationDiscovery = TianganUtils.discover(tiangans)

      with self.subTest('correctness'):
        for rel in TianganRelation:
          self.assertIn(rel, discovery)
          self.assertSetEqual(set(discovery[rel]), set(TianganUtils.search(tiangans, rel)))

      with self.subTest('consistency'):
        discovery2: TianganRelationDiscovery = TianganUtils.discover(tiangans)
        self.assertEqual(discovery, discovery2)

  @pytest.mark.slow
  def test_results_matched(self) -> None:
    '''Test that the results of different methods are the same.'''
    for _ in range(512):
      tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan))) + \
                                random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
      discovery: TianganRelationDiscovery = TianganUtils.discover(tiangans)

      with self.subTest('HE / 合'): # Non-directional relation
        for combo in discovery[TianganRelation.合]:
          self.assertEqual(len(combo), 2)
          self.assertTrue(TianganUtils.he(*combo))

      with self.subTest('CHONG / 冲'): # Non-directional relation
        for combo in discovery[TianganRelation.冲]:
          self.assertEqual(len(combo), 2)
          self.assertTrue(TianganUtils.chong(*combo))

      with self.subTest('SHENG / 生'): # Directional relation
        for combo in discovery[TianganRelation.生]:
          self.assertEqual(len(combo), 2)
          tg1, tg2 = combo
          r1, r2 = TianganUtils.sheng(tg1, tg2), TianganUtils.sheng(tg2, tg1)
          self.assertTrue(r1 or r2)
          self.assertFalse(r1 and r2)

      with self.subTest('KE / 克'): # Directional relation
        for combo in discovery[TianganRelation.克]:
          self.assertEqual(len(combo), 2)
          tg1, tg2 = combo
          r1, r2 = TianganUtils.ke(tg1, tg2), TianganUtils.ke(tg2, tg1)
          self.assertTrue(r1 or r2)
          self.assertFalse(r1 and r2)
