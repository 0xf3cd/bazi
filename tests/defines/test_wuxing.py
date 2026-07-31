# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_wuxing.py

import unittest

from itertools import product
from src.defines import (
  Wuxing, 五行,
)


class TestWuxing(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Wuxing), 5)
    self.assertEqual(Wuxing.METAL.value, '金')
    self.assertEqual(Wuxing.金.value, '金')
    self.assertEqual(Wuxing('金'), Wuxing.金)
    self.assertNotEqual(Wuxing.金, Wuxing.木)
    self.assertNotEqual(Wuxing.金.value, Wuxing.木.value)

  def test_alias(self) -> None:
    self.assertIs(Wuxing.木, Wuxing.WOOD)
    self.assertIs(Wuxing.火, Wuxing.FIRE)
    self.assertIs(Wuxing.土, Wuxing.EARTH)
    self.assertIs(Wuxing.金, Wuxing.METAL)
    self.assertIs(Wuxing.水, Wuxing.WATER)
    self.assertIs(Wuxing, 五行)

  def test_as_list(self) -> None:
    self.assertEqual(len(Wuxing.as_list()), 5)
    self.assertEqual(Wuxing.as_list()[0], Wuxing.木)
    self.assertEqual(Wuxing.as_list()[1], Wuxing.火)
    self.assertEqual(Wuxing.as_list()[2], Wuxing.土)
    self.assertEqual(Wuxing.as_list()[3], Wuxing.金)
    self.assertEqual(Wuxing.as_list()[4], Wuxing.水)

  def test_from_str(self) -> None:
    self.assertIs(Wuxing.from_str('木'), Wuxing.木)
    self.assertIs(Wuxing.from_str('火'), Wuxing.火)
    self.assertIs(Wuxing.from_str('土'), Wuxing.土)
    self.assertIs(Wuxing.from_str('金'), Wuxing.金)
    self.assertIs(Wuxing.from_str('水'), Wuxing.水)

    with self.assertRaises(AssertionError):
      Wuxing.from_str('')
    with self.assertRaises(AssertionError):
      Wuxing.from_str('木木')
    with self.assertRaises(ValueError):
      Wuxing.from_str('甲')
    with self.assertRaises(ValueError):
      Wuxing.from_str('辰')

  def test_str(self) -> None:
    for wx in Wuxing:
      self.assertEqual(str(wx), wx.value)
      self.assertEqual(Wuxing.from_str(str(wx)), wx)

    self.assertEqual(''.join([str(wx) for wx in Wuxing]), '木火土金水')

  def test_generates_and_destructs(self) -> None:
    self.assertTrue(Wuxing.木.generates(Wuxing.火))
    self.assertTrue(Wuxing.火.destructs(Wuxing.金))

    wx_list: list[Wuxing] = Wuxing.as_list()
    for wx1, wx2 in product(wx_list, wx_list):
      wx1_index: int = wx_list.index(wx1)
      wx2_index: int = wx_list.index(wx2)
      
      if (wx1_index + 1) % 5 == wx2_index:
        self.assertTrue(wx1.generates(wx2))
        self.assertFalse(wx2.generates(wx1))
        self.assertFalse(wx1.destructs(wx2))
      else:
        self.assertFalse(wx1.generates(wx2))

      if (wx1_index + 2) % 5 == wx2_index:
        self.assertTrue(wx1.destructs(wx2))
        self.assertFalse(wx2.destructs(wx1))
        self.assertFalse(wx1.generates(wx2))
      else:
        self.assertFalse(wx1.destructs(wx2))
