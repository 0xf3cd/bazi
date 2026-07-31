# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_dizhi.py

import unittest

from src.defines import (
  Tiangan, Dizhi, 地支,
)


class TestDizhi(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(12, len(Dizhi))
    self.assertEqual('子', Dizhi.ZI.value)
    self.assertEqual(Dizhi('子'), Dizhi.子)
    self.assertNotEqual(Dizhi.WEI, Dizhi.SHEN)
    self.assertNotEqual(Dizhi.WEI.value, Dizhi.SHEN.value)

  def test_alias(self) -> None:
    self.assertEqual(地支, Dizhi)
    self.assertIs(地支, Dizhi)
    self.assertEqual(12, len(地支))

    self.assertIs(Dizhi.子, Dizhi.ZI)
    self.assertIs(Dizhi.子, 地支.ZI)
    self.assertIs(Dizhi.子, 地支.子)
    
    self.assertIsNot(Dizhi.丑, Dizhi.午)

    self.assertEqual('午', 地支.午.value)
    self.assertEqual('午', Dizhi.午.value)
    self.assertEqual('未', 地支.WEI.value)
    self.assertEqual(Dizhi.午.value, Dizhi.WU.value)
    self.assertEqual(Dizhi.午.value, 地支.WU.value)
    
    self.assertNotEqual('未', 地支.SHEN.value)
    self.assertNotEqual(地支.申, 地支.未)

    for e in 地支:
      self.assertIsNotNone(e.value)
      self.assertIn(e, Dizhi)

    for e in Dizhi:
      self.assertIsNotNone(e.value)
      self.assertIn(e, 地支)

  def test_as_list(self) -> None:
    self.assertListEqual(Dizhi.as_list(), list(Dizhi))
    self.assertListEqual(Dizhi.as_list(), \
      [Dizhi.子, Dizhi.丑, Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.巳, Dizhi.午, Dizhi.未, Dizhi.申, Dizhi.酉, Dizhi.戌, Dizhi.亥])
  
  def test_from_str(self) -> None:
    with self.assertRaises(ValueError):
      Dizhi.from_str('子子')
    with self.assertRaises(ValueError):
      Dizhi.from_str('ZI')
    with self.assertRaises(ValueError):
      Dizhi.from_str('Zi')
    with self.assertRaises(ValueError):
      Dizhi.from_str('甲')
    with self.assertRaises(AssertionError):
      Dizhi.from_str(Dizhi.子) # type: ignore
    with self.assertRaises(AssertionError):
      Dizhi.from_str(0) # type: ignore
    with self.assertRaises(AssertionError):
      Dizhi.from_str(Tiangan.丁) # type: ignore

    self.assertEqual(Dizhi.from_str('寅'), Dizhi.寅)
    self.assertEqual(Dizhi.寅, Dizhi.from_str('寅'))
    self.assertEqual(Dizhi.from_str('卯'), Dizhi.from_str('卯'))
    self.assertNotEqual(Dizhi.寅, Dizhi.from_str('卯'))
    self.assertNotEqual(Dizhi.from_str('卯'), Dizhi.from_str('寅'))

  def test_str(self) -> None:
    for e in Dizhi:
      self.assertEqual(str(e), e.value)
      self.assertIs(Dizhi(str(e)), e)
    for e in Dizhi.as_list():
      self.assertEqual(str(e), e.value)
      self.assertIs(Dizhi(str(e)), e)

    self.assertEqual('子丑寅卯辰巳午未申酉戌亥', ''.join([str(e) for e in Dizhi.as_list()]))

  def test_index(self) -> None:
    self.assertEqual(Dizhi.子.index, 0)
    self.assertEqual(Dizhi.丑.index, 1)
    self.assertEqual(Dizhi.寅.index, 2)
    self.assertEqual(Dizhi.卯.index, 3)
    self.assertEqual(Dizhi.辰.index, 4)
    self.assertEqual(Dizhi.巳.index, 5)
    self.assertEqual(Dizhi.午.index, 6)
    self.assertEqual(Dizhi.未.index, 7)
    self.assertEqual(Dizhi.申.index, 8)
    self.assertEqual(Dizhi.酉.index, 9)
    self.assertEqual(Dizhi.戌.index, 10)
    self.assertEqual(Dizhi.亥.index, 11)

  def test_from_index(self) -> None:
    self.assertEqual(Dizhi.from_index(0), Dizhi.子)
    self.assertEqual(Dizhi.from_index(1), Dizhi.丑)
    self.assertEqual(Dizhi.from_index(2), Dizhi.寅)
    self.assertEqual(Dizhi.from_index(3), Dizhi.卯)
    self.assertEqual(Dizhi.from_index(4), Dizhi.辰)
    self.assertEqual(Dizhi.from_index(5), Dizhi.巳)
    self.assertEqual(Dizhi.from_index(6), Dizhi.午)
    self.assertEqual(Dizhi.from_index(7), Dizhi.未)
    self.assertEqual(Dizhi.from_index(8), Dizhi.申)
    self.assertEqual(Dizhi.from_index(9), Dizhi.酉)
    self.assertEqual(Dizhi.from_index(10), Dizhi.戌)
    self.assertEqual(Dizhi.from_index(11), Dizhi.亥)
    with self.assertRaises(IndexError):
      Dizhi.from_index(12)
    with self.assertRaises(IndexError):
      Dizhi.from_index(-13)
