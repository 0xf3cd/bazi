# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_tiangan.py

import unittest

from src.defines import (
  Tiangan, 天干,
)


class TestTiangan(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Tiangan), 10)
    self.assertEqual(Tiangan.JIA.value, '甲')
    self.assertEqual(Tiangan('甲').value, '甲')
    self.assertNotEqual(Tiangan.WU, Tiangan.REN)
    self.assertNotEqual(Tiangan.WU.value, Tiangan.REN.value)

  def test_alias(self) -> None:
    self.assertEqual(天干, Tiangan)
    self.assertIs(天干, Tiangan)
    self.assertEqual(len(天干), 10)

    self.assertIs(Tiangan.甲, Tiangan.JIA)
    self.assertIs(Tiangan.甲, Tiangan.甲)
    self.assertIs(天干.甲, Tiangan.甲)
    self.assertIs(天干.甲, 天干.JIA)
    self.assertIs(天干.BING, 天干.丙)

    self.assertIsNot(Tiangan.甲, Tiangan.乙)

    self.assertEqual(天干.甲.value, '甲')
    self.assertEqual(天干.JIA.value, '甲')
    self.assertEqual(天干.丁.value, Tiangan.丁.value)
    self.assertEqual(天干.甲.value, Tiangan.JIA.value)
    self.assertEqual(天干.甲.value, 天干.JIA.value)

    self.assertNotEqual(天干.癸, 天干.庚)
    self.assertNotEqual(天干.甲.value, Tiangan.丁.value)
    self.assertNotEqual(天干.WU.value, '甲')

    for e in Tiangan:
      self.assertIsNotNone(e.value)
      self.assertIn(e, 天干)

    for e in 天干:
      self.assertIsNotNone(e.value)
      self.assertIn(e, Tiangan)

  def test_as_list(self) -> None:
    self.assertListEqual(Tiangan.as_list(), list(Tiangan))
    self.assertListEqual(Tiangan.as_list(), \
      [Tiangan.甲, Tiangan.乙, Tiangan.丙, Tiangan.丁, Tiangan.戊, Tiangan.己, Tiangan.庚, Tiangan.辛, Tiangan.壬, Tiangan.癸])
  
  def test_from_str(self) -> None:
    with self.assertRaises(ValueError):
      Tiangan.from_str('甲甲')
    with self.assertRaises(ValueError):
      Tiangan.from_str('JIA')
    with self.assertRaises(ValueError):
      Tiangan.from_str('Jia')
    with self.assertRaises(ValueError):
      Tiangan.from_str('子')
    with self.assertRaises(AssertionError):
      Tiangan.from_str(Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      Tiangan.from_str(0) # type: ignore

    self.assertEqual(Tiangan.from_str('甲'), Tiangan.甲)
    self.assertEqual(Tiangan.甲, Tiangan.from_str('甲'))
    self.assertEqual(Tiangan.from_str('丁'), Tiangan.from_str('丁'))
    self.assertNotEqual(Tiangan.甲, Tiangan.from_str('丁'))
    self.assertNotEqual(Tiangan.from_str('丁'), Tiangan.from_str('甲'))
                        
  def test_str(self) -> None:
    for e in Tiangan:
      self.assertEqual(str(e), e.value)
      self.assertIs(Tiangan(str(e)), e)
    for e in Tiangan.as_list():
      self.assertEqual(str(e), e.value)
      self.assertIs(Tiangan(str(e)), e)

    self.assertEqual('甲乙丙丁戊己庚辛壬癸', ''.join([str(e) for e in Tiangan.as_list()]))

  def test_index(self) -> None:
    self.assertEqual(Tiangan.甲.index, 0)
    self.assertEqual(Tiangan.乙.index, 1)
    self.assertEqual(Tiangan.丙.index, 2)
    self.assertEqual(Tiangan.丁.index, 3)
    self.assertEqual(Tiangan.戊.index, 4)
    self.assertEqual(Tiangan.己.index, 5)
    self.assertEqual(Tiangan.庚.index, 6)
    self.assertEqual(Tiangan.辛.index, 7)
    self.assertEqual(Tiangan.壬.index, 8)
    self.assertEqual(Tiangan.癸.index, 9)

  def test_from_index(self) -> None:
    self.assertEqual(Tiangan.from_index(0), Tiangan.甲)
    self.assertEqual(Tiangan.from_index(1), Tiangan.乙)
    self.assertEqual(Tiangan.from_index(2), Tiangan.丙)
    self.assertEqual(Tiangan.from_index(3), Tiangan.丁)
    self.assertEqual(Tiangan.from_index(4), Tiangan.戊)
    self.assertEqual(Tiangan.from_index(5), Tiangan.己)
    self.assertEqual(Tiangan.from_index(6), Tiangan.庚)
    self.assertEqual(Tiangan.from_index(7), Tiangan.辛)
    self.assertEqual(Tiangan.from_index(8), Tiangan.壬)
    self.assertEqual(Tiangan.from_index(9), Tiangan.癸)
    with self.assertRaises(IndexError):
      Tiangan.from_index(10)
    with self.assertRaises(IndexError):
      Tiangan.from_index(-11)
