# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_ganzhi.py

import unittest
import random

from src.defines import (
  Tiangan, 天干, Dizhi, 地支, Ganzhi, 干支,
)


class TestGanzhi(unittest.TestCase):
  def test_basic(self) -> None:
    gz_jiazi: Ganzhi = Ganzhi(Tiangan.JIA, Dizhi.ZI)
    gz_jiazi2: Ganzhi = Ganzhi(Tiangan.甲, Dizhi.子)
    gz_bingwu: Ganzhi = Ganzhi(Tiangan.丙, Dizhi.午)

    self.assertEqual(gz_jiazi.tiangan, Tiangan.甲)
    self.assertEqual(gz_jiazi.dizhi, Dizhi.子)
    self.assertEqual(gz_jiazi2.tiangan, Tiangan.甲)
    self.assertEqual(gz_jiazi2.dizhi, Dizhi.子)
    self.assertEqual(gz_bingwu.tiangan, Tiangan.丙)
    self.assertEqual(gz_bingwu.dizhi, Dizhi.午)
    self.assertEqual(gz_jiazi, gz_jiazi2)
    self.assertNotEqual(gz_jiazi, gz_bingwu)
    self.assertNotEqual(gz_jiazi2, gz_bingwu)

    gz_list: list[Ganzhi] = []
    for _ in range(3):
      for tg in Tiangan:
        for dz in Dizhi:
          gz_list.append(Ganzhi(tg, dz))
          
    # In theory, 10 tiangans and 12 dizhis can produce 120 different Ganzhis.
    self.assertEqual(len(set(gz_list)), 120)

  def test_alias(self) -> None:
    self.assertIs(Ganzhi, 干支)
    self.assertEqual(Ganzhi(Tiangan.WU, Dizhi.XU), 干支(天干.戊, 地支.戌))  
    self.assertNotEqual(Ganzhi(Tiangan.WU, Dizhi.XU), Ganzhi(Tiangan.WU, Dizhi.MAO))

  def test_from_strs(self) -> None:
    self.assertEqual(Ganzhi.from_strs('甲', '子'), Ganzhi(Tiangan.甲, Dizhi.子))
    self.assertEqual(Ganzhi.from_strs('戊', '午'), Ganzhi(Tiangan.戊, Dizhi.午))
    self.assertNotEqual(Ganzhi.from_strs('丙', '子'), Ganzhi(Tiangan.丙, Dizhi.寅))

    with self.assertRaises(ValueError):
      Ganzhi.from_strs('假', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('JIA', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('Jia', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('甲', '子子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('子', '甲')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('子', '子')
    with self.assertRaises(ValueError):
      Ganzhi.from_strs('甲', '甲')
    with self.assertRaises(AssertionError):
      Ganzhi.from_strs('甲', Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      Ganzhi.from_strs(Tiangan.甲, '子') # type: ignore
    with self.assertRaises(AssertionError):
      Ganzhi.from_strs(0, 0) # type: ignore

  def test_from_str(self) -> None:
    self.assertEqual(Ganzhi.from_str('甲子'), Ganzhi(Tiangan.甲, Dizhi.子))
    self.assertEqual(Ganzhi.from_str('戊午'), Ganzhi(Tiangan.戊, Dizhi.午))
    self.assertNotEqual(Ganzhi.from_str('丙子'), Ganzhi(Tiangan.丙, Dizhi.寅))

    with self.assertRaises(ValueError):
      Ganzhi.from_str('假子')
    with self.assertRaises(AssertionError):
      Ganzhi.from_str('JIA子')
    with self.assertRaises(AssertionError):
      Ganzhi.from_str('Jia子')
    with self.assertRaises(AssertionError):
      Ganzhi.from_str('甲子子')
    with self.assertRaises(ValueError):
      Ganzhi.from_str('子甲')
    with self.assertRaises(ValueError):
      Ganzhi.from_str('子子')
    with self.assertRaises(ValueError):
      Ganzhi.from_str('甲甲')
    with self.assertRaises(TypeError):
      Ganzhi.from_str(0) # type: ignore

  def test_str(self) -> None:
    for tg in Tiangan.as_list():
      for dz in Dizhi.as_list():
        # `Ganzhi` should be able to hold all 120 possible Tiangan-Dizhi pairs
        self.assertEqual(str(Ganzhi(tg, dz)), f'{tg}{dz}')
        self.assertEqual(Ganzhi.from_str(str(Ganzhi(tg, dz))), Ganzhi(tg, dz))

  def test_list_sexagenary_cycle(self) -> None:
    sexagenary_cycle = Ganzhi.list_sexagenary_cycle()

    self.assertEqual(len(sexagenary_cycle), 60)
    self.assertEqual(sexagenary_cycle[0], Ganzhi(Tiangan.甲, Dizhi.子))
    self.assertEqual(sexagenary_cycle[-1], Ganzhi(Tiangan.癸, Dizhi.亥))

    tg_list = Tiangan.as_list()
    dz_list = Dizhi.as_list()
    for i, gz in enumerate(sexagenary_cycle):
      self.assertIs(gz.tiangan, tg_list[i % 10])
      self.assertIs(gz.dizhi, dz_list[i % 12])

  def test_list_sexagenary_cycle_strs(self) -> None:
    sexagenary_cycle_strs = Ganzhi.list_sexagenary_cycle_strs()

    self.assertEqual(len(sexagenary_cycle_strs), 60)
    self.assertEqual(sexagenary_cycle_strs[0], '甲子')
    self.assertEqual(sexagenary_cycle_strs[-1], '癸亥')

    tg_list = Tiangan.as_list()
    dz_list = Dizhi.as_list()
    for i, gz_str in enumerate(sexagenary_cycle_strs):
      self.assertEqual(gz_str, f'{tg_list[i % 10]}{dz_list[i % 12]}')

  def test_ganzhi_next_prev(self) -> None:
    with self.subTest('negative'):
      with self.assertRaises(AssertionError):
        Ganzhi(Tiangan.甲, Dizhi.子).next('1')
      with self.assertRaises(AssertionError):
        Ganzhi(Tiangan.甲, Dizhi.子).prev('1')
      with self.assertRaises(AssertionError):
        Ganzhi(Tiangan.甲, Dizhi.子).next(3.5)
      with self.assertRaises(AssertionError):
        Ganzhi(Tiangan.甲, Dizhi.子).prev(3.5)

    def __random_gz() -> Ganzhi:
      while True:
        tg: Tiangan = random.choice(Tiangan.as_list())
        dz: Dizhi = random.choice(Dizhi.as_list())
        if (tg.index % 2) == (dz.index % 2):
          return Ganzhi(tg, dz)

    with self.subTest('correctness'):
      self.assertEqual(Ganzhi(Tiangan.甲, Dizhi.子).next(1), Ganzhi(Tiangan.乙, Dizhi.丑))
      self.assertEqual(Ganzhi(Tiangan.甲, Dizhi.子).prev(-1), Ganzhi(Tiangan.乙, Dizhi.丑))
      self.assertEqual(Ganzhi(Tiangan.甲, Dizhi.子).prev(1), Ganzhi(Tiangan.癸, Dizhi.亥))
      self.assertEqual(Ganzhi(Tiangan.甲, Dizhi.子).next(-1), Ganzhi(Tiangan.癸, Dizhi.亥))

      cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
      for _ in range(16):
        random_gz1: Ganzhi = __random_gz()
        self.assertEqual(random_gz1, random_gz1.next(0))
        self.assertEqual(random_gz1, random_gz1.next(60))
        self.assertEqual(random_gz1, random_gz1.prev(0))
        self.assertEqual(random_gz1, random_gz1.prev(60))

        random_int: int = random.randint(-1000, 1000)
        self.assertEqual(random_gz1.next(random_int), 
                         cycle[(cycle.index(random_gz1) + random_int) % 60])
        self.assertEqual(random_gz1.prev(random_int),
                         cycle[(cycle.index(random_gz1) - random_int) % 60])

    with self.subTest('immutability'):
      gz: Ganzhi = Ganzhi(Tiangan.甲, Dizhi.子)
      self.assertIsNot(gz, gz.next(0))
      self.assertIsNot(gz, gz.prev(0))

    with self.subTest('consistency'):
      for _ in range(16):
        random_gz2: Ganzhi = __random_gz()
        for __ in range(16):
          x: int = random.randint(-1000, 1000)
          self.assertEqual(random_gz2,
                           random_gz2.next(x).prev(x))
          self.assertEqual(random_gz2,
                           random_gz2.prev(x).next(x))
          self.assertEqual(random_gz2.next(x), random_gz2.prev(-x))
          self.assertEqual(random_gz2.prev(x), random_gz2.next(-x))
