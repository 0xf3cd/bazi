# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_dizhi_relation_utils.py

import copy
import random
import itertools

import pytest
import unittest

from collections import Counter
from typing import Union, Optional, Iterable, Any, Callable

from src.Defines import Tiangan, Dizhi, Wuxing, TianganRelation, DizhiRelation
from src.Rules import DizhiRules
from src.Utils import BaziUtils, TianganUtils, DizhiUtils
from src.Utils.DizhiUtils import DizhiCombo, DizhiRelationCombos, DizhiRelationDiscovery


class TestDizhiUtils(unittest.TestCase):
  DzCmpType = Union[list[set[Dizhi]], Iterable[DizhiCombo]]
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

  def test_search_sanhui(self) -> None:
    sanhui_combos: list[DizhiCombo] = [
      DizhiCombo((Dizhi.from_index(2), Dizhi.from_index(3), Dizhi.from_index(4))),
      DizhiCombo((Dizhi.from_index(5), Dizhi.from_index(6), Dizhi.from_index(7))),
      DizhiCombo((Dizhi.from_index(8), Dizhi.from_index(9), Dizhi.from_index(10))),
      DizhiCombo((Dizhi.from_index(11), Dizhi.from_index(0), Dizhi.from_index(1))),
    ]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.三会),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.三会),
      [set(c) for c in sanhui_combos],
    ))
    
    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.三会)
      expected_result: list[set[Dizhi]] = [set(c) for c in sanhui_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_sanhui(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.sanhui(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhui(Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhui(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhui((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhui({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhui([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.sanhui('亥', '子', '丑') # type: ignore

    dizhi_tuples: list[tuple[Dizhi, Dizhi, Dizhi]] = [
      (Dizhi.寅, Dizhi.卯, Dizhi.辰), # Spring / 春
      (Dizhi.巳, Dizhi.午, Dizhi.未), # Summer / 夏
      (Dizhi.申, Dizhi.酉, Dizhi.戌), # Fall   / 秋
      (Dizhi.亥, Dizhi.子, Dizhi.丑), # Winter / 冬
    ]
    expected: dict[DizhiCombo, Wuxing] = { 
      DizhiCombo(dizhis) : BaziUtils.traits(dizhis[0]).wuxing for dizhis in dizhi_tuples 
    }
    
    for dizhis in itertools.product(Dizhi, repeat=3):
      fs: DizhiCombo = DizhiCombo(dizhis)
      if fs in expected:
        for combo in itertools.permutations(dizhis):
          self.assertEqual(DizhiUtils.sanhui(*combo), expected[fs])
      else:
        for combo in itertools.permutations(dizhis):
          self.assertIsNone(DizhiUtils.sanhui(*dizhis))

  def test_search_liuhe(self) -> None:
    liuhe_combos: list[DizhiCombo] = [
      DizhiCombo((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
    ]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.六合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.六合),
      liuhe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.六合)
      expected_result: list[set[Dizhi]] = [set(c) for c in liuhe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_liuhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.liuhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.liuhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.liuhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.liuhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.liuhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.liuhe('亥', '子') # type: ignore

    liuhe_combos: list[DizhiCombo] = [
      DizhiCombo((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
    ]

    for dz1, dz2 in itertools.permutations(Dizhi, 2):
      liuhe_result: Optional[Wuxing] = DizhiUtils.liuhe(dz1, dz2)
      liuhe_result2: Optional[Wuxing] = DizhiUtils.liuhe(dz2, dz1)
      self.assertEqual(liuhe_result, liuhe_result2)
      
      if DizhiCombo((dz1, dz2)) in liuhe_combos:
        wx1, wx2 = BaziUtils.traits(dz1).wuxing, BaziUtils.traits(dz2).wuxing
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

  def test_search_anhe(self) -> None:
    anhe_combos: list[DizhiCombo] = [ # 天干五合对应的地支暗合，5组。
      DizhiCombo((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
    ] + [ # `NORMAL_EXTENDED` 中额外的1组。
      DizhiCombo((Dizhi.寅, Dizhi.丑)), 
    ]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.暗合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.暗合),
      anhe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.暗合)
      expected_result: list[set[Dizhi]] = [set(c) for c in anhe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_anhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.anhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.anhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.anhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.anhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.anhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.anhe('亥', '子') # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.anhe(Dizhi.子, Dizhi.辰, DizhiRules.AnheDef.NORMAL + 100) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.anhe(Dizhi.子, Dizhi.辰, definition='DizhiRules.AnheDef.NORMAL') # type: ignore

    normal_combos: list[DizhiCombo] = [
      DizhiCombo((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
    ] 
    
    normal_extended_combos: list[DizhiCombo] = normal_combos + [
      DizhiCombo((Dizhi.寅, Dizhi.丑)), 
    ]

    mangpai_combos: list[DizhiCombo] = [
      DizhiCombo((Dizhi.寅, Dizhi.丑)), 
      DizhiCombo((Dizhi.午, Dizhi.亥)), 
      DizhiCombo((Dizhi.卯, Dizhi.申)), 
    ]

    expected: dict[DizhiRules.AnheDef, list[DizhiCombo]] = {
      DizhiRules.AnheDef.NORMAL: normal_combos,
      DizhiRules.AnheDef.NORMAL_EXTENDED: normal_extended_combos,
      DizhiRules.AnheDef.MANGPAI: mangpai_combos
    }

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      for anhe_def in DizhiRules.AnheDef:
        self.assertEqual(DizhiUtils.anhe(dz1, dz2, definition=anhe_def), DizhiCombo((dz1, dz2)) in expected[anhe_def])
        self.assertEqual(DizhiUtils.anhe(dz1, dz2, definition=anhe_def), DizhiUtils.anhe(dz2, dz1, definition=anhe_def))

    # Ensure the default definition is `NORMAL`.
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.anhe(dz1, dz2), DizhiCombo((dz1, dz2)) in normal_extended_combos)
      self.assertEqual(DizhiUtils.anhe(dz1, dz2), DizhiUtils.anhe(dz2, dz1))

  def test_search_tonghe(self) -> None:
    tonghe_combos: set[DizhiCombo] = set()
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      hidden1, hidden2 = BaziUtils.hidden_tiangans(dz1), BaziUtils.hidden_tiangans(dz2)
      if len(hidden1) != len(hidden2):
        continue
      expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1.keys()]
      if all(tg in hidden2 for tg in expected_hidden2):
        tonghe_combos.add(DizhiCombo((dz1, dz2)))

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.通合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.通合),
      tonghe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.通合)
      expected_result: list[set[Dizhi]] = [set(c) for c in tonghe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_tonghe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.tonghe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tonghe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tonghe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tonghe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tonghe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.tonghe('亥', '子') # type: ignore

    tonghe_combos: set[DizhiCombo] = set()
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      hidden1, hidden2 = BaziUtils.hidden_tiangans(dz1), BaziUtils.hidden_tiangans(dz2)
      if len(hidden1) != len(hidden2):
        continue
      expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1.keys()]
      if all(tg in hidden2 for tg in expected_hidden2):
        tonghe_combos.add(DizhiCombo((dz1, dz2)))

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.tonghe(dz1, dz2), DizhiCombo((dz1, dz2)) in tonghe_combos)
      self.assertEqual(DizhiUtils.tonghe(dz1, dz2), DizhiUtils.tonghe(dz2, dz1))

  def test_search_tongluhe(self) -> None:
    tongluhe_combos: list[DizhiCombo] = [ # 天干五合对应的地支禄身。
      DizhiCombo((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
    ]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.通禄合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.通禄合),
      tongluhe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.通禄合)
      expected_result: list[set[Dizhi]] = [set(c) for c in tongluhe_combos if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_tongluhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.tongluhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tongluhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tongluhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tongluhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.tongluhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.tongluhe('亥', '子') # type: ignore

    tongluhe_combos: list[DizhiCombo] = [ # 天干五合对应的地支禄身。
      DizhiCombo((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
    ]

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.tongluhe(dz1, dz2), DizhiCombo((dz1, dz2)) in tongluhe_combos)
      self.assertEqual(DizhiUtils.tongluhe(dz1, dz2), DizhiUtils.tongluhe(dz2, dz1))

  @staticmethod
  def __gen_sanhe_table() -> dict[DizhiCombo, Wuxing]:
    return {
      DizhiCombo((
        dz, 
        Dizhi.from_index((dz.index + 4) % 12), 
        Dizhi.from_index((dz.index - 4) % 12),
      )) : BaziUtils.traits(dz).wuxing
      for dz in [Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉')]
    }

  def test_search_sanhe(self) -> None:
    sanhe_table: dict[DizhiCombo, Wuxing] = self.__gen_sanhe_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.三合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.三合),
      sanhe_table.keys(),
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.三合)
      expected_result: list[set[Dizhi]] = [set(c) for c in sanhe_table if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_sanhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.sanhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhe(Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhe((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhe({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sanhe([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.sanhe('亥', '子', '丑') # type: ignore

    sanhe_table: dict[DizhiCombo, Wuxing] = self.__gen_sanhe_table()
    
    for dizhis in itertools.product(Dizhi, repeat=3):
      fs: DizhiCombo = DizhiCombo(dizhis)
      if fs in sanhe_table:
        for combo in itertools.permutations(dizhis):
          self.assertEqual(DizhiUtils.sanhe(*combo), sanhe_table[fs])
      else:
        for combo in itertools.permutations(dizhis):
          self.assertIsNone(DizhiUtils.sanhe(*dizhis))

  @staticmethod
  def __gen_banhe_table() -> dict[DizhiCombo, Wuxing]:
    pivots: set[Dizhi] = set((Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉'))) # 四中神
    sanhe_table: dict[DizhiCombo, Wuxing] = TestDizhiUtils.__gen_sanhe_table()

    d: dict[DizhiCombo, Wuxing] = {}
    for sanhe_dizhis, wx in sanhe_table.items():
      for dz1, dz2 in itertools.combinations(sanhe_dizhis, 2):
        if any(dz in pivots for dz in (dz1, dz2)): # 半合局需要出现中神
          d[DizhiCombo((dz1, dz2))] = wx
    return d

  def test_search_banhe(self) -> None:
    banhe_table: dict[DizhiCombo, Wuxing] = self.__gen_banhe_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.半合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.半合),
      banhe_table.keys()
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.半合)
      expected_result: list[set[Dizhi]] = [set(c) for c in banhe_table if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_banhe(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.banhe(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.banhe(Dizhi.子, Dizhi.辰, Dizhi.申) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.banhe((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.banhe({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.banhe([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.banhe('亥', '子') # type: ignore

    banhe_table: dict[DizhiCombo, Wuxing] = self.__gen_banhe_table()

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.banhe(dz1, dz2), banhe_table.get(DizhiCombo((dz1, dz2)), None))
      self.assertEqual(DizhiUtils.banhe(dz1, dz2), DizhiUtils.banhe(dz2, dz1))

  def test_search_xing(self) -> None:
    xing_expected: list[dict[Dizhi, int]] = [ # 辰午酉亥自刑
      {
        dz : 2,
      } for dz in [Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥]
    ] + [ # 其他相刑
      { Dizhi.子 : 1, Dizhi.卯 : 1, },
      { Dizhi.寅 : 1, Dizhi.巳 : 1, Dizhi.申 : 1, },
      { Dizhi.丑 : 1, Dizhi.未 : 1, Dizhi.戌 : 1, },
    ] + [ # LOOSE def.
      { Dizhi.寅 : 1, Dizhi.巳 : 1, },
      { Dizhi.巳 : 1, Dizhi.申 : 1, },
      { Dizhi.寅 : 1, Dizhi.申 : 1, },
      { Dizhi.丑 : 1, Dizhi.未 : 1, },
      { Dizhi.未 : 1, Dizhi.戌 : 1, },
      { Dizhi.丑 : 1, Dizhi.戌 : 1, },
    ]

    def __find_qualified(dizhis: list[Dizhi]) -> list[set[Dizhi]]:
      ret: list[set[Dizhi]] = []
      for required in xing_expected:
        if all(
          sum(dz == d for d in dizhis) >= required[dz] 
          for dz in required
        ):
          ret.append(set(required.keys())) 
      return ret

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.刑),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([Dizhi.子, Dizhi.卯], DizhiRelation.刑),
      [{Dizhi.子, Dizhi.卯}],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([Dizhi.卯, Dizhi.子], DizhiRelation.刑),
      [{Dizhi.子, Dizhi.卯}],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.刑),
      [{Dizhi.子, Dizhi.卯}, 
       {Dizhi.寅, Dizhi.巳, Dizhi.申}, {Dizhi.寅, Dizhi.巳}, {Dizhi.巳, Dizhi.申}, {Dizhi.寅, Dizhi.申}, 
       {Dizhi.丑, Dizhi.未, Dizhi.戌}, {Dizhi.丑, Dizhi.未}, {Dizhi.未, Dizhi.戌}, {Dizhi.丑, Dizhi.戌}],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi) + [Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥], DizhiRelation.刑),
      [set(d.keys()) for d in xing_expected]
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = [] 
      for _ in range(random.randint(1, 4)):
        dizhis += random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.刑)
      expected_result: list[set[Dizhi]] = __find_qualified(dizhis)
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_xing_negative(self) -> None:
    with self.assertRaises(AssertionError):
      DizhiUtils.xing(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰)
    with self.assertRaises(AssertionError):
      DizhiUtils.xing((Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.xing({Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.xing([Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.xing('亥', '子') # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.xing(Dizhi.子, Dizhi.辰, DizhiRules.XingDef.LOOSE) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.xing(Dizhi.子, Dizhi.辰, definition='DizhiRules.X.NORMAL') # type: ignore

    for dz in Dizhi:
      self.assertIsNone(DizhiUtils.xing(dz))
      self.assertIsNone(DizhiUtils.xing(dz, definition=DizhiRules.XingDef.STRICT))
      self.assertIsNone(DizhiUtils.xing(dz, definition=DizhiRules.XingDef.LOOSE))

    for _ in range(500):
      random_dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(4, len(Dizhi)))
      with self.assertRaises(AssertionError):
        self.assertIsNone(DizhiUtils.xing(*random_dizhis))
      with self.assertRaises(AssertionError):
        self.assertIsNone(DizhiUtils.xing(*random_dizhis, definition=DizhiRules.XingDef.STRICT))
      with self.assertRaises(AssertionError):
        self.assertIsNone(DizhiUtils.xing(*random_dizhis, definition=DizhiRules.XingDef.LOOSE))

  @pytest.mark.slow
  def test_xing_strict(self) -> None:
    self.assertIsNone(DizhiUtils.xing())
    self.assertIsNone(DizhiUtils.xing(definition=DizhiRules.XingDef.STRICT))
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, definition=DizhiRules.XingDef.STRICT), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.STRICT), DizhiRules.XingSubType.自刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.STRICT), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯, definition=DizhiRules.XingDef.STRICT), DizhiRules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.卯, Dizhi.子, definition=DizhiRules.XingDef.STRICT), DizhiRules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯, Dizhi.亥, definition=DizhiRules.XingDef.STRICT), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申, definition=DizhiRules.XingDef.STRICT), DizhiRules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅, Dizhi.申, definition=DizhiRules.XingDef.STRICT), DizhiRules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳, definition=DizhiRules.XingDef.STRICT), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅, definition=DizhiRules.XingDef.STRICT), None)

    def __expected_strict_xing(__dizhis: tuple[Dizhi, ...]) -> Optional[DizhiRules.XingSubType]:
      # In `XingDef.STRICT` mode, we don't care about the direction.
      __fs: DizhiCombo = DizhiCombo(__dizhis)
      if __fs in [DizhiCombo((Dizhi.丑, Dizhi.戌, Dizhi.未)), DizhiCombo((Dizhi.寅, Dizhi.巳, Dizhi.申))]:
        return DizhiRules.XingSubType.三刑
      elif __fs == DizhiCombo((Dizhi.子, Dizhi.卯)):
        return DizhiRules.XingSubType.子卯刑
      elif len(__fs) == 1 and len(__dizhis) == 2:
        if __dizhis[0] in (Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥):
          return DizhiRules.XingSubType.自刑
      return None
    
    for dz in Dizhi:
      self.assertIsNone(DizhiUtils.xing(dz, definition=DizhiRules.XingDef.STRICT))

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      strict_result: Optional[DizhiRules.XingSubType] = DizhiUtils.xing(dz1, dz2, definition=DizhiRules.XingDef.STRICT)
      strict_result2: Optional[DizhiRules.XingSubType] = DizhiUtils.xing(dz2, dz1, definition=DizhiRules.XingDef.STRICT)
      strict_result3: Optional[DizhiRules.XingSubType] = DizhiUtils.xing(dz1, dz2, definition=DizhiRules.XingDef.STRICT)
      self.assertEqual(strict_result, strict_result2)
      self.assertEqual(strict_result, strict_result3)
      self.assertEqual(strict_result, __expected_strict_xing((dz1, dz2)))

    for dz_tuple in itertools.product(Dizhi, Dizhi, Dizhi):
      strict_result4: Optional[DizhiRules.XingSubType] = DizhiUtils.xing(*dz_tuple, definition=DizhiRules.XingDef.STRICT)
      for dz1, dz2, dz3 in itertools.permutations(dz_tuple, 3):
        self.assertEqual(strict_result4, DizhiUtils.xing(dz1, dz2, dz3, definition=DizhiRules.XingDef.STRICT))
        self.assertEqual(strict_result4, DizhiUtils.xing(dz1, dz2, dz3, definition=DizhiRules.XingDef.STRICT))

  def test_xing_loose(self) -> None:
    self.assertIsNone(DizhiUtils.xing(definition=DizhiRules.XingDef.LOOSE))
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, definition=DizhiRules.XingDef.LOOSE), 
                     None)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.LOOSE), 
                     DizhiRules.XingSubType.自刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.LOOSE), 
                     None)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯, definition=DizhiRules.XingDef.LOOSE), 
                     DizhiRules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.卯, Dizhi.子, definition=DizhiRules.XingDef.LOOSE), 
                     DizhiRules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯, Dizhi.亥, definition=DizhiRules.XingDef.LOOSE), 
                     None)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申, definition=DizhiRules.XingDef.LOOSE), 
                     DizhiRules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅, Dizhi.申, definition=DizhiRules.XingDef.LOOSE), 
                     DizhiRules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳, definition=DizhiRules.XingDef.LOOSE), 
                     DizhiRules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅, definition=DizhiRules.XingDef.LOOSE), 
                     None)

    sanxing_list: list[tuple[Dizhi, ...]] = [
      (Dizhi.丑, Dizhi.戌),
      (Dizhi.戌, Dizhi.未),
      (Dizhi.未, Dizhi.丑),
      (Dizhi.寅, Dizhi.巳),
      (Dizhi.巳, Dizhi.申),
      (Dizhi.申, Dizhi.寅),
      *(list(itertools.permutations((Dizhi.丑, Dizhi.戌, Dizhi.未)))),
      *(list(itertools.permutations((Dizhi.寅, Dizhi.巳, Dizhi.申)))),
    ]

    zimaoxing_list: list[tuple[Dizhi, ...]] = [
      (Dizhi.子, Dizhi.卯),
      (Dizhi.卯, Dizhi.子),
    ]

    zixing_list: list[tuple[Dizhi, ...]] = [
      (dz, dz) for dz in (Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥)
    ]

    for dz in Dizhi:
      self.assertIsNone(DizhiUtils.xing(dz, definition=DizhiRules.XingDef.LOOSE))

    dz_tuple: tuple[Dizhi, ...]
    for dz_tuple in itertools.product(Dizhi, Dizhi):
      loose_result: Optional[DizhiRules.XingSubType] = DizhiUtils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE)
      if loose_result is DizhiRules.XingSubType.三刑:
        self.assertIn(dz_tuple, sanxing_list)
      elif loose_result is DizhiRules.XingSubType.子卯刑:
        self.assertIn(dz_tuple, zimaoxing_list)
      elif loose_result is DizhiRules.XingSubType.自刑:
        self.assertIn(dz_tuple, zixing_list)
      else:
        self.assertIsNone(loose_result)
        self.assertNotIn(dz_tuple, sanxing_list)
        self.assertNotIn(dz_tuple, zimaoxing_list)
        self.assertNotIn(dz_tuple, zixing_list)

    for dz_tuple in itertools.product(Dizhi, Dizhi, Dizhi):
      loose_result2: Optional[DizhiRules.XingSubType] = DizhiUtils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE)
      if loose_result2 is None:
        self.assertNotIn(dz_tuple, sanxing_list)
        self.assertNotIn(dz_tuple, zimaoxing_list)
        self.assertNotIn(dz_tuple, zixing_list)
      else:
        self.assertEqual(loose_result2, DizhiRules.XingSubType.三刑)
        self.assertIn(dz_tuple, sanxing_list)

  def test_search_chong(self) -> None:
    chong_table: list[set[Dizhi]] = [set(dz_tuple) for dz_tuple in zip(Dizhi.as_list()[:6], Dizhi.as_list()[6:])]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.冲),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.冲),
      chong_table,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.冲)
      expected_result: list[set[Dizhi]] = [c for c in chong_table if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_chong(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.chong(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.chong(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.chong(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.chong((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.chong({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.chong([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.chong('亥', '子') # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.chong(Tiangan.甲, '子') # type: ignore

    chong_table: list[set[Dizhi]] = [set(dz_tuple) for dz_tuple in zip(Dizhi.as_list()[:6], Dizhi.as_list()[6:])]

    for dz1, dz2 in itertools.product(Dizhi, repeat=2):
      self.assertEqual(DizhiUtils.chong(dz1, dz2), DizhiUtils.chong(dz2, dz1), 'CHONG (冲) is a bi-directional relation')
      self.assertEqual(DizhiUtils.chong(dz1, dz2), set((dz1, dz2)) in chong_table)

  @staticmethod
  def __gen_po_table() -> list[set[Dizhi]]:
    return [set((
      Dizhi.from_index(dz_idx), Dizhi.from_index((dz_idx - 3) % 12),
    )) for dz_idx in range(0, 12, 2)]

  def test_search_po(self) -> None:
    po_table: list[set[Dizhi]] = self.__gen_po_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.破),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.破),
      po_table,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.破)
      expected_result: list[set[Dizhi]] = [c for c in po_table if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_po(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.po(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.po(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.po(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.po((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.po({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.po([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.po([Dizhi.亥, Dizhi.子], [Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.po('亥', '子') # type: ignore

    po_table: list[set[Dizhi]] = self.__gen_po_table()

    for dz1, dz2 in itertools.product(Dizhi, repeat=2):
      self.assertEqual(DizhiUtils.po(dz1, dz2), DizhiUtils.po(dz2, dz1), 'PO (破) is a bi-directional relation')
      self.assertEqual(DizhiUtils.po(dz1, dz2), set((dz1, dz2)) in po_table)

  @staticmethod
  def __gen_hai_table() -> set[DizhiCombo]:
    ret: set[DizhiCombo] = set()
    for dz1, dz2 in itertools.combinations(Dizhi, 2):
      if DizhiUtils.liuhe(dz1, dz2):
        dz1_chong: Dizhi = Dizhi.from_index((dz1.index + 6) % 12)
        dz2_chong: Dizhi = Dizhi.from_index((dz2.index + 6) % 12)
        ret.add(DizhiCombo((dz1, dz2_chong)))
        ret.add(DizhiCombo((dz1_chong, dz2)))
    return ret
  
  def test_search_hai(self) -> None:
    hai_set: set[DizhiCombo] = self.__gen_hai_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.search([], DizhiRelation.害),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi), DizhiRelation.害),
      hai_set,
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.search(list(Dizhi) * 2, DizhiRelation.害),
      hai_set,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.害)
      expected_result: list[DizhiCombo] = [c for c in hai_set if c.issubset(dizhis)]
      self.assertTrue(self.__dz_equal(result, expected_result))

  def test_hai(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.hai(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.hai(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.hai((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.hai({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.hai([Dizhi.亥], [Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.hai('亥', '丑') # type: ignore

    hai_set: set[DizhiCombo] = self.__gen_hai_table()

    for dz1, dz2 in itertools.product(Dizhi, repeat=2):
      self.assertEqual(DizhiUtils.hai(dz1, dz2), DizhiUtils.hai(dz2, dz1), 'HAI (害) is a bi-directional relation')
      self.assertEqual(DizhiUtils.hai(dz1, dz2), DizhiCombo((dz1, dz2)) in hai_set)

  def test_search_sheng_ke(self) -> None:
    for _ in range(200):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      sheng_result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.生)
      ke_result: DizhiRelationCombos = DizhiUtils.search(dizhis, DizhiRelation.克)

      for fs in sheng_result:
        for dz in fs:
          self.assertIn(dz, dizhis)
      for fs in ke_result:
        for dz in fs:
          self.assertIn(dz, dizhis)

      for dz1, dz2 in itertools.combinations(dizhis, 2):
        wx1, wx2 = BaziUtils.traits(dz1).wuxing, BaziUtils.traits(dz2).wuxing
        if wx1.generates(wx2) or wx2.generates(wx1):
          self.assertTrue(DizhiCombo((dz1, dz2)) in sheng_result)
        if wx1.destructs(wx2) or wx2.destructs(wx1):
          self.assertTrue(DizhiCombo((dz1, dz2)) in ke_result)

  def test_sheng(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.sheng(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sheng(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sheng((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.sheng({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.sheng([Dizhi.亥], [Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.sheng('亥', '丑') # type: ignore

    for dz1, dz2 in itertools.product(Dizhi, repeat=2):
      wx1, wx2 = BaziUtils.traits(dz1).wuxing, BaziUtils.traits(dz2).wuxing
      if wx1.generates(wx2):
        self.assertTrue(DizhiUtils.sheng(dz1, dz2))
        self.assertFalse(DizhiUtils.sheng(dz2, dz1))
      else:
        self.assertFalse(DizhiUtils.sheng(dz1, dz2))

  def test_ke(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.ke(Dizhi.子) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.ke(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.ke((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
    with self.assertRaises(TypeError):
      DizhiUtils.ke({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.ke([Dizhi.亥], [Dizhi.丑]) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.ke('亥', '丑') # type: ignore

    for dz1, dz2 in itertools.product(Dizhi, repeat=2):
      wx1, wx2 = BaziUtils.traits(dz1).wuxing, BaziUtils.traits(dz2).wuxing
      if wx1.destructs(wx2):
        self.assertTrue(DizhiUtils.ke(dz1, dz2))
        self.assertFalse(DizhiUtils.ke(dz2, dz1))
      else:
        self.assertFalse(DizhiUtils.ke(dz1, dz2))

  def test_search_negative(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.search([Dizhi.子, Dizhi.午]) # type: ignore

    for tg_relation in TianganRelation:
      with self.assertRaises(AssertionError):
        DizhiUtils.search([Dizhi.子, Dizhi.午], tg_relation) # type: ignore

    for relation in DizhiRelation:
      with self.assertRaises(AssertionError):
        DizhiUtils.search(Dizhi.子, relation) # type: ignore
      with self.assertRaises(AssertionError):
        DizhiUtils.search(['甲', '己'], relation) # type: ignore
      with self.assertRaises(AssertionError):
        DizhiUtils.search([Dizhi.子, Dizhi.午], str(relation)) # type: ignore
      with self.assertRaises(AssertionError):
        DizhiUtils.search(set([Dizhi.子, Dizhi.午]), relation) # type: ignore

  @pytest.mark.slow
  def test_search(self) -> None:
    for relation in DizhiRelation:
      for round in range(300):
        dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
        for _ in range(random.randint(0, 2)):
          dizhis += random.sample(list(Dizhi), random.randint(0, len(Dizhi)))

        dizhi_counter: Counter[Dizhi] = Counter(dizhis)
        result: DizhiRelationCombos = DizhiUtils.search(dizhis, relation)
        for _ in range(2):
          random.shuffle(dizhis)
          copied: list[Dizhi] = copy.deepcopy(dizhis)
          self.assertTrue(self.__dz_equal(result, DizhiUtils.search(dizhis, relation)))
          self.assertListEqual(copied, dizhis) # Ensure `search` has no effect on the input `dizhis`.

        result2: DizhiRelationCombos = DizhiUtils.search(dizhis + dizhis, relation)
        result3: DizhiRelationCombos = DizhiUtils.search(dizhis + dizhis + dizhis, relation)

        # Expectedly, `result2` and `result3` should be equal to `result1`.
        # The only exception is 自刑。
        result_patched: DizhiRelationCombos = copy.deepcopy(result)
        if relation is DizhiRelation.刑:
          for dz in (Dizhi.午, Dizhi.辰, Dizhi.酉, Dizhi.亥):
            if dizhi_counter[dz] == 1:
              fs = DizhiCombo((dz,))
              self.assertNotIn(fs, result_patched)
              self.assertIn(fs, result2)
              self.assertIn(fs, result3)
              result_patched = result_patched + (fs,) # Patch it up.

        self.assertTrue(self.__dz_equal(result_patched, result2))
        self.assertTrue(self.__dz_equal(result_patched, result3))

  @staticmethod
  def __run_all_relation_methods(dizhis: list[Dizhi]) -> list[Any]:
    '''This test basically iterates all possible permutations of `dizhis` and invokes all relation checking methods.'''
    dizhi_set: set[Dizhi] = set(dizhis)
    sorted_dizhis: list[Dizhi] = sorted(dizhi_set, key=lambda dz : dz.index)
    result: list[Any] = []

    result.append(DizhiUtils.xing(definition=DizhiRules.XingDef.STRICT))
    result.append(DizhiUtils.xing(definition=DizhiRules.XingDef.LOOSE))

    for dz in sorted_dizhis:
      result.append(DizhiUtils.xing(dz, definition=DizhiRules.XingDef.STRICT))
      result.append(DizhiUtils.xing(dz, definition=DizhiRules.XingDef.LOOSE))

    dz_tuple: tuple[Dizhi, ...]
    for dz_tuple in itertools.permutations(sorted_dizhis, 2):
      result.append(DizhiUtils.liuhe(*dz_tuple))
      result.append(DizhiUtils.anhe(*dz_tuple, definition=DizhiRules.AnheDef.NORMAL))
      result.append(DizhiUtils.anhe(*dz_tuple, definition=DizhiRules.AnheDef.NORMAL_EXTENDED))
      result.append(DizhiUtils.anhe(*dz_tuple, definition=DizhiRules.AnheDef.MANGPAI))
      result.append(DizhiUtils.tonghe(*dz_tuple))
      result.append(DizhiUtils.tongluhe(*dz_tuple))
      result.append(DizhiUtils.banhe(*dz_tuple))
      result.append(DizhiUtils.xing(*dz_tuple, definition=DizhiRules.XingDef.STRICT))
      result.append(DizhiUtils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE))
      result.append(DizhiUtils.chong(*dz_tuple))
      result.append(DizhiUtils.po(*dz_tuple))
      result.append(DizhiUtils.hai(*dz_tuple))
      result.append(DizhiUtils.sheng(*dz_tuple))
      result.append(DizhiUtils.ke(*dz_tuple))

    for dz_tuple in itertools.permutations(sorted_dizhis, 3):
      result.append(DizhiUtils.sanhui(*dz_tuple)) # Mypy complains... # type: ignore
      result.append(DizhiUtils.sanhe(*dz_tuple)) # Mypy complains... # type: ignore
      result.append(DizhiUtils.xing(*dz_tuple, definition=DizhiRules.XingDef.STRICT)) # Mypy complains... # type: ignore
      result.append(DizhiUtils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE)) # Mypy complains... # type: ignore
    
    return result

  @pytest.mark.slow
  def test_discover(self) -> None:
    for _ in range(512):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi))) + \
                            random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      discovery: DizhiRelationDiscovery = DizhiUtils.discover(dizhis)

      with self.subTest('correctness'):
        for rel in DizhiRelation:
          if rel in discovery:
            self.assertSetEqual(set(discovery[rel]), set(DizhiUtils.search(dizhis, rel)))
          else:
            self.assertEqual(len(DizhiUtils.search(dizhis, rel)), 0)

      with self.subTest('consistency'):
        discovery2: DizhiRelationDiscovery = DizhiUtils.discover(dizhis)
        self.assertEqual(discovery, discovery2)

  @pytest.mark.slow
  def test_discover_mutual(self) -> None:
    def __random_dz_lists() -> tuple[list[Dizhi], list[Dizhi]]:
      dizhis1: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      dizhis2: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))

      if random.randint(0, 2) == 0:
        dizhis1.extend(random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi))))
      if random.randint(0, 2) == 0:
        dizhis2.extend(random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi))))

      return dizhis1, dizhis2

    for _ in range(16):
      dizhis1, dizhis2 = __random_dz_lists()
      discovery: DizhiRelationDiscovery = DizhiUtils.discover_mutual(dizhis1, dizhis2)

      self.assertEqual(discovery, DizhiUtils.discover_mutual(dizhis1, dizhis2)) # Test consistency
      self.assertEqual(discovery, DizhiUtils.discover_mutual(dizhis2, dizhis1)) # Test symmetry/equivalence

      expected: dict[DizhiRelation, set[DizhiCombo]] = {
        rel : set() for rel in DizhiRelation
      }
      
      rules: list[tuple[DizhiRelation, Callable[..., Any], int]] = [
        (DizhiRelation.三会, DizhiUtils.sanhui, 3),
        (DizhiRelation.三合, DizhiUtils.sanhe, 3),
        (DizhiRelation.刑, DizhiUtils.xing, 3),
        (DizhiRelation.六合, DizhiUtils.liuhe, 2),
        (DizhiRelation.暗合, DizhiUtils.anhe, 2),
        (DizhiRelation.通合, DizhiUtils.tonghe, 2),
        (DizhiRelation.通禄合, DizhiUtils.tongluhe, 2),
        (DizhiRelation.半合, DizhiUtils.banhe, 2),
        (DizhiRelation.刑, DizhiUtils.xing, 2),
        (DizhiRelation.冲, DizhiUtils.chong, 2),
        (DizhiRelation.破, DizhiUtils.po, 2),
        (DizhiRelation.害, DizhiUtils.hai, 2),
        (DizhiRelation.生, DizhiUtils.sheng, 2),
        (DizhiRelation.克, DizhiUtils.ke, 2),
      ]
      
      # Fill `expected`...
      dizhis1_set, dizhis2_set = set(dizhis1), set(dizhis2)
      for rel, f, n in rules:
        for dz_tuple in itertools.permutations(dizhis1 + dizhis2, n):
          combo = DizhiCombo(dz_tuple)
          if not f(*dz_tuple):
            continue
          if any(combo.isdisjoint(s) for s in (dizhis1_set, dizhis2_set)):
            continue

          self.assertIn(combo, discovery[rel])
          expected[rel].add(combo)

      for rel, expected_combos in expected.items():
        if rel in discovery:
          for combo in discovery[rel]:
            self.assertIn(combo, expected_combos)
        else:
          self.assertEqual(len(expected_combos), 0)

  def test_edge_cases(self) -> None:
    '''Test `discover_mutual` on 三合、三会、三刑、自刑'''
    for combo_fs in DizhiRules.DIZHI_SANHE.keys():
      part1 = [random.choice(list(combo_fs))]
      part2 = list(combo_fs - set(part1))

      self.assertNotIn(DizhiRelation.三合, DizhiUtils.discover_mutual([], [*combo_fs]))

      self.assertTupleEqual((combo_fs,), 
                            DizhiUtils.discover_mutual(part1, part2)[DizhiRelation.三合])
      self.assertEqual(DizhiUtils.discover_mutual(part1, part2), 
                       DizhiUtils.discover_mutual(part2, part1))

    for combo_fs in DizhiRules.DIZHI_SANHUI.keys():
      part1 = [random.choice(list(combo_fs))]
      part2 = list(combo_fs - set(part1))

      self.assertNotIn(DizhiRelation.三会, DizhiUtils.discover_mutual([], [*combo_fs]))

      self.assertTupleEqual((combo_fs,), 
                            DizhiUtils.discover_mutual(part1, part2)[DizhiRelation.三会])
      self.assertEqual(DizhiUtils.discover_mutual(part1, part2), 
                       DizhiUtils.discover_mutual(part2, part1))
    
    for combo_tuple, _ in DizhiRules.DIZHI_XING.loose.items():
      part1 = [random.choice(combo_tuple)]
      part2 = list(combo_tuple)
      part2.remove(part1[0])

      self.assertNotIn(DizhiRelation.刑, DizhiUtils.discover_mutual([], [*combo_tuple]))

      self.assertIn(frozenset(combo_tuple), 
                    DizhiUtils.discover_mutual(part1, part2)[DizhiRelation.刑])
      self.assertEqual(DizhiUtils.discover_mutual(part1, part2), 
                       DizhiUtils.discover_mutual(part2, part1))
      
    self.assertTupleEqual((frozenset({Dizhi.午}),),
                          DizhiUtils.discover_mutual([Dizhi.午], [Dizhi.午])[DizhiRelation.刑])

  @pytest.mark.slow
  def test_consistency(self) -> None:
    '''This test mainly tests that staticmethods in `DizhiUtils` give consistent results.'''

    def __split(dizhis: list[Dizhi]) -> tuple[list[Dizhi], list[Dizhi]]:
      dz_idx_list: list[int] = [idx for idx, _ in enumerate(dizhis)]
      part1_idx_list: list[int] = random.sample(dz_idx_list, random.randint(0, len(dz_idx_list)))
      part2_idx_list: list[int] = [idx for idx in dz_idx_list if idx not in part1_idx_list]
      assert len(part1_idx_list) + len(part2_idx_list) == len(dizhis)
      assert len(set(part1_idx_list + part2_idx_list)) == len(dizhis)

      part1_dizhis: list[Dizhi] = [dizhis[idx] for idx in part1_idx_list]
      part2_dizhis: list[Dizhi] = [dizhis[idx] for idx in part2_idx_list]
      assert len(part1_dizhis) + len(part2_dizhis) == len(dizhis)

      return part1_dizhis, part2_dizhis

    for attempt in range(8):
      dizhis: list[Dizhi] = []
      for _ in range(random.randint(0, 4)):
        dizhis.extend(random.sample(list(Dizhi), random.randint(0, 5)))
      copied_dizhis: list[Dizhi] = copy.deepcopy(dizhis)

      for relation in DizhiRelation:
        relation_results: list[list[Any]] = []
        combo_results: list[DizhiRelationCombos] = []
        discover_results: list[DizhiRelationDiscovery] = []
        discover_mutual_results: list[DizhiRelationDiscovery] = []

        dizhis_p1, dizhis_p2 = __split(dizhis)
       
        for _ in range(5):
          if random.randint(0, 1) == 0:
            relation_results.append(self.__run_all_relation_methods(dizhis))
          if random.randint(0, 1) == 0:
            combo_results.append(DizhiUtils.search(dizhis, relation))
          if random.randint(0, 1) == 0:
            discover_results.append(DizhiUtils.discover(dizhis))
          if random.randint(0, 1) == 0:
            discover_mutual_results.append(DizhiUtils.discover_mutual(dizhis_p1, dizhis_p2))
            discover_mutual_results.append(DizhiUtils.discover_mutual(dizhis_p2, dizhis_p1))

        for rr1, rr2 in zip(relation_results, relation_results[1:]):
          self.assertEqual(rr1, rr2)
        for cr1, cr2 in zip(combo_results, combo_results[1:]):
          self.assertEqual(cr1, cr2)
        for dr1, dr2 in zip(discover_results, discover_results[1:]):
          self.assertEqual(dr1, dr2)
        for dmr1, dmr2 in zip(discover_mutual_results, discover_mutual_results[1:]):
          self.assertEqual(dmr1, dmr2)

      self.assertEqual(dizhis, copied_dizhis) # Ensure the order of `dizhis` was not changed.

  def test_discovery_filter(self) -> None:
    for _ in range(5):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      discovery: DizhiRelationDiscovery = DizhiUtils.discover(dizhis)

      self.assertEqual(discovery, discovery.filter(lambda rel, combos : True))

      forbidden_dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      forbidden_relations: list[DizhiRelation] = random.sample(list(DizhiRelation), random.randint(0, len(DizhiRelation)))
      
      def filter_func(rel: DizhiRelation, combo: DizhiCombo) -> bool:
        if rel in forbidden_relations:
          return False
        if any(dz in combo for dz in forbidden_dizhis):
          return False
        return True
      
      filtered = discovery.filter(filter_func)

      for rel in forbidden_relations:
        self.assertNotIn(rel, filtered)

      for rel, combos in filtered.items():
        for combo in combos:
          self.assertTrue(all(dz not in combo for dz in forbidden_dizhis))
          self.assertIn(combo, discovery[rel])

  @pytest.mark.slow
  def test_discovery_merge(self) -> None:
    for _ in range(5):
      dizhis1: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      dizhis2: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      
      discovery1 = DizhiUtils.discover(dizhis1)
      discovery2 = DizhiUtils.discover(dizhis2)

      merged = discovery1.merge(discovery2)

      with self.subTest('merge consistency'):
        merged_ = discovery2.merge(discovery1)
        self.assertSetEqual(set(merged), set(merged_))
        for rel, combos in merged.items():
          self.assertIn(rel, merged_)
          self.assertSetEqual(set(combos), set(merged_[rel]))

      with self.subTest('correctness'):
        for rel, combos in discovery1.items():
          self.assertIn(rel, merged)
          for combo in combos:
            self.assertIn(combo, merged[rel])

        for rel, combos in discovery2.items():
          self.assertIn(rel, merged)
          for combo in combos:
            self.assertIn(combo, merged[rel])

        for rel, combos in merged.items():
          expected = set(discovery1.get(rel, set())) | set(discovery2.get(rel, set()))
          self.assertSetEqual(set(combos), expected)
