# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_dizhi_relation_utils.py

import copy
import random
import pytest
import unittest
import itertools

from collections import Counter
from typing import Union, Optional, Iterable, Any

from src.Defines import Tiangan, Dizhi, Wuxing, TianganRelation, DizhiRelation
from src.Rules import Rules
from src.Utils import BaziUtils, TianganUtils, DizhiUtils


@pytest.mark.errorprone
class TestDizhiUtils(unittest.TestCase):
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
      DizhiUtils.find_dizhi_combos([], DizhiRelation.三会),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.三会),
      [set(c) for c in sanhui_combos],
    ))
    
    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.三会)
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
    expected: dict[frozenset[Dizhi], Wuxing] = { 
      frozenset(dizhis) : BaziUtils.traits(dizhis[0]).wuxing for dizhis in dizhi_tuples 
    }
    
    for dizhis in itertools.product(Dizhi, repeat=3):
      fs: frozenset[Dizhi] = frozenset(dizhis)
      if fs in expected:
        for combo in itertools.permutations(dizhis):
          self.assertEqual(DizhiUtils.sanhui(*combo), expected[fs])
      else:
        for combo in itertools.permutations(dizhis):
          self.assertIsNone(DizhiUtils.sanhui(*dizhis))

  def test_find_dizhi_combos_liuhe(self) -> None:
    liuhe_combos: list[frozenset[Dizhi]] = [
      frozenset((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
    ]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.六合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.六合),
      liuhe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.六合)
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

    liuhe_combos: list[frozenset[Dizhi]] = [
      frozenset((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
    ]

    for dz1, dz2 in itertools.permutations(Dizhi, 2):
      liuhe_result: Optional[Wuxing] = DizhiUtils.liuhe(dz1, dz2)
      liuhe_result2: Optional[Wuxing] = DizhiUtils.liuhe(dz2, dz1)
      self.assertEqual(liuhe_result, liuhe_result2)
      
      if frozenset((dz1, dz2)) in liuhe_combos:
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

  def test_find_dizhi_combos_anhe(self) -> None:
    anhe_combos: list[frozenset[Dizhi]] = [ # 天干五合对应的地支暗合，5组。
      frozenset((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
    ] + [ # `NORMAL_EXTENDED` 中额外的1组。
      frozenset((Dizhi.寅, Dizhi.丑)), 
    ]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.暗合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.暗合),
      anhe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.暗合)
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
      DizhiUtils.anhe(Dizhi.子, Dizhi.辰, Rules.AnheDef.NORMAL + 100) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.anhe(Dizhi.子, Dizhi.辰, definition='Rules.AnheDef.NORMAL') # type: ignore

    normal_combos: list[frozenset[Dizhi]] = [
      frozenset((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
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
        self.assertEqual(DizhiUtils.anhe(dz1, dz2, definition=anhe_def), frozenset((dz1, dz2)) in expected[anhe_def])
        self.assertEqual(DizhiUtils.anhe(dz1, dz2, definition=anhe_def), DizhiUtils.anhe(dz2, dz1, definition=anhe_def))

    # Ensure the default definition is `NORMAL`.
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.anhe(dz1, dz2), frozenset((dz1, dz2)) in normal_combos)
      self.assertEqual(DizhiUtils.anhe(dz1, dz2), DizhiUtils.anhe(dz2, dz1))

  def test_find_dizhi_combos_tonghe(self) -> None:
    tonghe_combos: set[frozenset[Dizhi]] = set()
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      hidden1, hidden2 = BaziUtils.hidden_tiangans(dz1), BaziUtils.hidden_tiangans(dz2)
      if len(hidden1) != len(hidden2):
        continue
      expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1.keys()]
      if all(tg in hidden2 for tg in expected_hidden2):
        tonghe_combos.add(frozenset((dz1, dz2)))

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.通合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.通合),
      tonghe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.通合)
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

    tonghe_combos: set[frozenset[Dizhi]] = set()
    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      hidden1, hidden2 = BaziUtils.hidden_tiangans(dz1), BaziUtils.hidden_tiangans(dz2)
      if len(hidden1) != len(hidden2):
        continue
      expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1.keys()]
      if all(tg in hidden2 for tg in expected_hidden2):
        tonghe_combos.add(frozenset((dz1, dz2)))

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.tonghe(dz1, dz2), frozenset((dz1, dz2)) in tonghe_combos)
      self.assertEqual(DizhiUtils.tonghe(dz1, dz2), DizhiUtils.tonghe(dz2, dz1))

  def test_find_dizhi_combos_tongluhe(self) -> None:
    tongluhe_combos: list[frozenset[Dizhi]] = [ # 天干五合对应的地支禄身。
      frozenset((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
    ]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.通禄合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.通禄合),
      tongluhe_combos,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.通禄合)
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

    tongluhe_combos: list[frozenset[Dizhi]] = [ # 天干五合对应的地支禄身。
      frozenset((BaziUtils.lu(tg1), BaziUtils.lu(tg2))) 
      for tg1, tg2 in itertools.combinations(Tiangan, 2) if TianganUtils.he(tg1, tg2) is not None
    ]

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.tongluhe(dz1, dz2), frozenset((dz1, dz2)) in tongluhe_combos)
      self.assertEqual(DizhiUtils.tongluhe(dz1, dz2), DizhiUtils.tongluhe(dz2, dz1))

  @staticmethod
  def __gen_sanhe_table() -> dict[frozenset[Dizhi], Wuxing]:
    return {
      frozenset((
        dz, 
        Dizhi.from_index((dz.index + 4) % 12), 
        Dizhi.from_index((dz.index - 4) % 12),
      )) : BaziUtils.traits(dz).wuxing
      for dz in [Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉')]
    }

  def test_find_dizhi_combos_sanhe(self) -> None:
    sanhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_sanhe_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.三合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.三合),
      sanhe_table.keys(),
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.三合)
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

    sanhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_sanhe_table()
    
    for dizhis in itertools.product(Dizhi, repeat=3):
      fs: frozenset[Dizhi] = frozenset(dizhis)
      if fs in sanhe_table:
        for combo in itertools.permutations(dizhis):
          self.assertEqual(DizhiUtils.sanhe(*combo), sanhe_table[fs])
      else:
        for combo in itertools.permutations(dizhis):
          self.assertIsNone(DizhiUtils.sanhe(*dizhis))

  @staticmethod
  def __gen_banhe_table() -> dict[frozenset[Dizhi], Wuxing]:
    pivots: set[Dizhi] = set((Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉'))) # 四中神
    sanhe_table: dict[frozenset[Dizhi], Wuxing] = TestDizhiUtils.__gen_sanhe_table()

    d: dict[frozenset[Dizhi], Wuxing] = {}
    for sanhe_dizhis, wx in sanhe_table.items():
      for dz1, dz2 in itertools.combinations(sanhe_dizhis, 2):
        if any(dz in pivots for dz in (dz1, dz2)): # 半合局需要出现中神
          d[frozenset((dz1, dz2))] = wx
    return d

  def test_find_dizhi_combos_banhe(self) -> None:
    banhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_banhe_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.半合),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.半合),
      banhe_table.keys()
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.半合)
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

    banhe_table: dict[frozenset[Dizhi], Wuxing] = self.__gen_banhe_table()

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      self.assertEqual(DizhiUtils.banhe(dz1, dz2), banhe_table.get(frozenset((dz1, dz2)), None))
      self.assertEqual(DizhiUtils.banhe(dz1, dz2), DizhiUtils.banhe(dz2, dz1))

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
        if all(
          sum(dz == d for d in dizhis) >= required[dz] 
          for dz in required
        ):
          ret.append(set(required.keys())) 
      return ret

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.刑),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([Dizhi.子, Dizhi.卯], DizhiRelation.刑),
      [{Dizhi.子, Dizhi.卯}],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([Dizhi.卯, Dizhi.子], DizhiRelation.刑),
      [{Dizhi.子, Dizhi.卯}],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.刑),
      [{Dizhi.子, Dizhi.卯}, {Dizhi.寅, Dizhi.巳, Dizhi.申}, {Dizhi.丑, Dizhi.未, Dizhi.戌}],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi) + [Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥], DizhiRelation.刑),
      [set(d.keys()) for d in xing_expected]
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = [] 
      for _ in range(random.randint(1, 4)):
        dizhis += random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.刑)
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
      DizhiUtils.xing(Dizhi.子, Dizhi.辰, Rules.XingDef.LOOSE) # type: ignore
    with self.assertRaises(AssertionError):
      DizhiUtils.xing(Dizhi.子, Dizhi.辰, definition='Rules.X.NORMAL') # type: ignore

    for dz in Dizhi:
      self.assertIsNone(DizhiUtils.xing(dz))
      self.assertIsNone(DizhiUtils.xing(dz, definition=Rules.XingDef.STRICT))
      self.assertIsNone(DizhiUtils.xing(dz, definition=Rules.XingDef.LOOSE))

    for _ in range(500):
      random_dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(4, len(Dizhi)))
      with self.assertRaises(AssertionError):
        self.assertIsNone(DizhiUtils.xing(*random_dizhis))
      with self.assertRaises(AssertionError):
        self.assertIsNone(DizhiUtils.xing(*random_dizhis, definition=Rules.XingDef.STRICT))
      with self.assertRaises(AssertionError):
        self.assertIsNone(DizhiUtils.xing(*random_dizhis, definition=Rules.XingDef.LOOSE))

  def test_xing_strict(self) -> None:
    self.assertIsNone(DizhiUtils.xing())
    self.assertIsNone(DizhiUtils.xing(definition=Rules.XingDef.STRICT))
    self.assertEqual(DizhiUtils.xing(Dizhi.亥), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥), Rules.XingSubType.自刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥, Dizhi.亥), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯), Rules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.卯, Dizhi.子), Rules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯, Dizhi.亥), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申), Rules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅, Dizhi.申), Rules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳), None)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅), None)

    def __expected_strict_xing(__dizhis: tuple[Dizhi, ...]) -> Optional[Rules.XingSubType]:
      # In `XingDef.STRICT` mode, we don't care about the direction.
      __fs: frozenset[Dizhi] = frozenset(__dizhis)
      if __fs in [frozenset((Dizhi.丑, Dizhi.戌, Dizhi.未)), frozenset((Dizhi.寅, Dizhi.巳, Dizhi.申))]:
        return Rules.XingSubType.三刑
      elif __fs == frozenset((Dizhi.子, Dizhi.卯)):
        return Rules.XingSubType.子卯刑
      elif len(__fs) == 1 and len(__dizhis) == 2:
        if __dizhis[0] in (Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥):
          return Rules.XingSubType.自刑
      return None
    
    for dz in Dizhi:
      self.assertIsNone(DizhiUtils.xing(dz))
      self.assertIsNone(DizhiUtils.xing(dz, definition=Rules.XingDef.STRICT))

    for dz1, dz2 in itertools.product(Dizhi, Dizhi):
      strict_result: Optional[Rules.XingSubType] = DizhiUtils.xing(dz1, dz2)
      strict_result2: Optional[Rules.XingSubType] = DizhiUtils.xing(dz2, dz1)
      strict_result3: Optional[Rules.XingSubType] = DizhiUtils.xing(dz1, dz2, definition=Rules.XingDef.STRICT)
      self.assertEqual(strict_result, strict_result2)
      self.assertEqual(strict_result, strict_result3)
      self.assertEqual(strict_result, __expected_strict_xing((dz1, dz2)))

    for dz_tuple in itertools.product(Dizhi, Dizhi, Dizhi):
      strict_result4: Optional[Rules.XingSubType] = DizhiUtils.xing(*dz_tuple)
      for dz1, dz2, dz3 in itertools.permutations(dz_tuple, 3):
        self.assertEqual(strict_result4, DizhiUtils.xing(dz1, dz2, dz3))
        self.assertEqual(strict_result4, DizhiUtils.xing(dz1, dz2, dz3, definition=Rules.XingDef.STRICT))

  def test_xing_loose(self) -> None:
    self.assertIsNone(DizhiUtils.xing(definition=Rules.XingDef.LOOSE))
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, definition=Rules.XingDef.LOOSE), 
                     None)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥, definition=Rules.XingDef.LOOSE), 
                     Rules.XingSubType.自刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.亥, Dizhi.亥, Dizhi.亥, definition=Rules.XingDef.LOOSE), 
                     None)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯, definition=Rules.XingDef.LOOSE), 
                     Rules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.卯, Dizhi.子, definition=Rules.XingDef.LOOSE), 
                     Rules.XingSubType.子卯刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.子, Dizhi.卯, Dizhi.亥, definition=Rules.XingDef.LOOSE), 
                     None)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申, definition=Rules.XingDef.LOOSE), 
                     Rules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅, Dizhi.申, definition=Rules.XingDef.LOOSE), 
                     Rules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.寅, Dizhi.巳, definition=Rules.XingDef.LOOSE), 
                     Rules.XingSubType.三刑)
    self.assertEqual(DizhiUtils.xing(Dizhi.巳, Dizhi.寅, definition=Rules.XingDef.LOOSE), 
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
      self.assertIsNone(DizhiUtils.xing(dz, definition=Rules.XingDef.LOOSE))

    dz_tuple: tuple[Dizhi, ...]
    for dz_tuple in itertools.product(Dizhi, Dizhi):
      loose_result: Optional[Rules.XingSubType] = DizhiUtils.xing(*dz_tuple, definition=Rules.XingDef.LOOSE)
      if loose_result is Rules.XingSubType.三刑:
        self.assertIn(dz_tuple, sanxing_list)
      elif loose_result is Rules.XingSubType.子卯刑:
        self.assertIn(dz_tuple, zimaoxing_list)
      elif loose_result is Rules.XingSubType.自刑:
        self.assertIn(dz_tuple, zixing_list)
      else:
        self.assertIsNone(loose_result)
        self.assertNotIn(dz_tuple, sanxing_list)
        self.assertNotIn(dz_tuple, zimaoxing_list)
        self.assertNotIn(dz_tuple, zixing_list)

    for dz_tuple in itertools.product(Dizhi, Dizhi, Dizhi):
      loose_result2: Optional[Rules.XingSubType] = DizhiUtils.xing(*dz_tuple, definition=Rules.XingDef.LOOSE)
      if loose_result2 is None:
        self.assertNotIn(dz_tuple, sanxing_list)
        self.assertNotIn(dz_tuple, zimaoxing_list)
        self.assertNotIn(dz_tuple, zixing_list)
      else:
        self.assertEqual(loose_result2, Rules.XingSubType.三刑)
        self.assertIn(dz_tuple, sanxing_list)

  def test_find_dizhi_combos_chong(self) -> None:
    chong_table: list[set[Dizhi]] = [set(dz_tuple) for dz_tuple in zip(Dizhi.as_list()[:6], Dizhi.as_list()[6:])]

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.冲),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.冲),
      chong_table,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.冲)
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

  def test_find_dizhi_combos_po(self) -> None:
    po_table: list[set[Dizhi]] = self.__gen_po_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.破),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.破),
      po_table,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.破)
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
  def __gen_hai_table() -> set[frozenset[Dizhi]]:
    ret: set[frozenset[Dizhi]] = set()
    for dz1, dz2 in itertools.combinations(Dizhi, 2):
      if DizhiUtils.liuhe(dz1, dz2):
        dz1_chong: Dizhi = Dizhi.from_index((dz1.index + 6) % 12)
        dz2_chong: Dizhi = Dizhi.from_index((dz2.index + 6) % 12)
        ret.add(frozenset((dz1, dz2_chong)))
        ret.add(frozenset((dz1_chong, dz2)))
    return ret
  
  def test_find_dizhi_combos_hai(self) -> None:
    hai_set: set[frozenset[Dizhi]] = self.__gen_hai_table()

    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos([], DizhiRelation.害),
      [],
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi), DizhiRelation.害),
      hai_set,
    ))
    self.assertTrue(self.__dz_equal(
      DizhiUtils.find_dizhi_combos(list(Dizhi) * 2, DizhiRelation.害),
      hai_set,
    ))

    for _ in range(500):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.害)
      expected_result: list[frozenset[Dizhi]] = [c for c in hai_set if c.issubset(dizhis)]
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

    hai_set: set[frozenset[Dizhi]] = self.__gen_hai_table()

    for dz1, dz2 in itertools.product(Dizhi, repeat=2):
      self.assertEqual(DizhiUtils.hai(dz1, dz2), DizhiUtils.hai(dz2, dz1), 'HAI (害) is a bi-directional relation')
      self.assertEqual(DizhiUtils.hai(dz1, dz2), frozenset((dz1, dz2)) in hai_set)

  def test_find_dizhi_combos_sheng_ke(self) -> None:
    for _ in range(200):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      sheng_result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.生)
      ke_result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, DizhiRelation.克)

      for fs in sheng_result:
        for dz in fs:
          self.assertIn(dz, dizhis)
      for fs in ke_result:
        for dz in fs:
          self.assertIn(dz, dizhis)

      for dz1, dz2 in itertools.combinations(dizhis, 2):
        wx1, wx2 = BaziUtils.traits(dz1).wuxing, BaziUtils.traits(dz2).wuxing
        if wx1.generates(wx2) or wx2.generates(wx1):
          self.assertTrue(frozenset((dz1, dz2)) in sheng_result)
        if wx1.destructs(wx2) or wx2.destructs(wx1):
          self.assertTrue(frozenset((dz1, dz2)) in ke_result)

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

  def test_find_dizhi_combos_negative(self) -> None:
    with self.assertRaises(TypeError):
      DizhiUtils.find_dizhi_combos([Dizhi.子, Dizhi.午]) # type: ignore

    for tg_relation in TianganRelation:
      with self.assertRaises(AssertionError):
        DizhiUtils.find_dizhi_combos([Dizhi.子, Dizhi.午], tg_relation) # type: ignore

    for relation in DizhiRelation:
      with self.assertRaises(AssertionError):
        DizhiUtils.find_dizhi_combos(Dizhi.子, relation) # type: ignore
      with self.assertRaises(AssertionError):
        DizhiUtils.find_dizhi_combos(['甲', '己'], relation) # type: ignore
      with self.assertRaises(AssertionError):
        DizhiUtils.find_dizhi_combos([Dizhi.子, Dizhi.午], str(relation)) # type: ignore
      with self.assertRaises(AssertionError):
        DizhiUtils.find_dizhi_combos(set([Dizhi.子, Dizhi.午]), relation) # type: ignore

  def test_find_dizhi_combos_integration(self) -> None:
    for relation in DizhiRelation:
      for round in range(200):
        dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
        for _ in range(random.randint(0, 2)):
          dizhis += random.sample(list(Dizhi), random.randint(0, len(Dizhi)))

        dizhi_counter: Counter[Dizhi] = Counter(dizhis)
        result: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis, relation)
        for _ in range(2):
          random.shuffle(dizhis)
          copied: list[Dizhi] = copy.deepcopy(dizhis)
          self.assertTrue(self.__dz_equal(result, DizhiUtils.find_dizhi_combos(dizhis, relation)))
          self.assertListEqual(copied, dizhis) # Ensure `find_dizhi_combos` has no effect on the input `dizhis`.

        result2: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis + dizhis, relation)
        result3: list[frozenset[Dizhi]] = DizhiUtils.find_dizhi_combos(dizhis + dizhis + dizhis, relation)

        # Expectedly, `result2` and `result3` should be equal to `result1`.
        # The only exception is 自刑。
        result_patched: list[frozenset[Dizhi]] = copy.deepcopy(result)
        if relation is DizhiRelation.刑:
          for dz in (Dizhi.午, Dizhi.辰, Dizhi.酉, Dizhi.亥):
            if dizhi_counter[dz] == 1:
              fs = frozenset((dz,))
              self.assertNotIn(fs, result_patched)
              self.assertIn(fs, result2)
              self.assertIn(fs, result3)
              result_patched.append(fs) # Patch it up.

        self.assertTrue(self.__dz_equal(result_patched, result2))
        self.assertTrue(self.__dz_equal(result_patched, result3))

  @staticmethod
  def __run_all_relation_methods(dizhis: list[Dizhi]) -> list[Any]:
    '''This test basically iterates all possible permutations of `dizhis` and invokes all relation checking methods.'''
    dizhi_set: set[Dizhi] = set(dizhis)
    sorted_dizhis: list[Dizhi] = sorted(dizhi_set, key=lambda dz : dz.index)
    result: list[Any] = []

    result.append(DizhiUtils.xing(definition=Rules.XingDef.STRICT))
    result.append(DizhiUtils.xing(definition=Rules.XingDef.LOOSE))

    for dz in sorted_dizhis:
      result.append(DizhiUtils.xing(dz, definition=Rules.XingDef.STRICT))
      result.append(DizhiUtils.xing(dz, definition=Rules.XingDef.LOOSE))

    dz_tuple: tuple[Dizhi, ...]
    for dz_tuple in itertools.permutations(sorted_dizhis, 2):
      result.append(DizhiUtils.liuhe(*dz_tuple))
      result.append(DizhiUtils.anhe(*dz_tuple, definition=Rules.AnheDef.NORMAL))
      result.append(DizhiUtils.anhe(*dz_tuple, definition=Rules.AnheDef.NORMAL_EXTENDED))
      result.append(DizhiUtils.anhe(*dz_tuple, definition=Rules.AnheDef.MANGPAI))
      result.append(DizhiUtils.tonghe(*dz_tuple))
      result.append(DizhiUtils.tongluhe(*dz_tuple))
      result.append(DizhiUtils.banhe(*dz_tuple))
      result.append(DizhiUtils.xing(*dz_tuple, definition=Rules.XingDef.STRICT))
      result.append(DizhiUtils.xing(*dz_tuple, definition=Rules.XingDef.LOOSE))
      result.append(DizhiUtils.chong(*dz_tuple))
      result.append(DizhiUtils.po(*dz_tuple))
      result.append(DizhiUtils.hai(*dz_tuple))
      result.append(DizhiUtils.sheng(*dz_tuple))
      result.append(DizhiUtils.ke(*dz_tuple))

    for dz_tuple in itertools.permutations(sorted_dizhis, 3):
      result.append(DizhiUtils.sanhui(*dz_tuple)) # Mypy complains... # type: ignore
      result.append(DizhiUtils.sanhe(*dz_tuple)) # Mypy complains... # type: ignore
      result.append(DizhiUtils.xing(*dz_tuple, definition=Rules.XingDef.STRICT)) # Mypy complains... # type: ignore
      result.append(DizhiUtils.xing(*dz_tuple, definition=Rules.XingDef.LOOSE)) # Mypy complains... # type: ignore
    
    return result

  def test_consistency(self) -> None:
    '''This test mainly tests that staticmethods in `DizhiUtils` give consistent results.'''
    dizhis: list[Dizhi] = []
    for _ in range(random.randint(1, 3)):
      dizhis.extend(random.sample(list(Dizhi), random.randint(0, 5)))
    copied_dizhis: list[Dizhi] = copy.deepcopy(dizhis)

    for relation in DizhiRelation:
      relation_results: list[list[Any]] = []
      combo_results: list[list[frozenset[Dizhi]]] = []
      for _ in range(7):
        if random.randint(0, 1) == 0:
          relation_results.append(self.__run_all_relation_methods(dizhis))
        if random.randint(0, 1) == 0:
          combo_results.append(DizhiUtils.find_dizhi_combos(dizhis, relation))

      if len(relation_results) >= 2:
        for r in relation_results[1:]:
          self.assertEqual(relation_results[0], r)
      if len(combo_results) >= 2:
        for r in combo_results[1:]:
          self.assertEqual(combo_results[0], r)

    self.assertEqual(dizhis, copied_dizhis) # Ensure the order of `dizhis` was not changed.
