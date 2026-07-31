# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shier_zhangsheng.py

import unittest

from src.defines import (
  ShierZhangsheng, 十二长生,
)


class TestShierZhangsheng(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(ShierZhangsheng, 十二长生)
    self.assertEqual(len(ShierZhangsheng), 12)
    self.assertEqual(len(ShierZhangsheng.as_list()), 12)
    self.assertEqual(list(ShierZhangsheng)[0].value, '长生')
    self.assertEqual(list(ShierZhangsheng)[-1].value, '养')

  def test_index(self) -> None:
    for zs in ShierZhangsheng:
      self.assertEqual(ShierZhangsheng.from_index(zs.index), zs)
      self.assertEqual(ShierZhangsheng.from_index(zs.index), zs)
      self.assertEqual(ShierZhangsheng.as_list()[zs.index], zs)

    with self.assertRaises(IndexError):
      ShierZhangsheng.from_index(12)
    with self.assertRaises(IndexError):
      ShierZhangsheng.from_index(-13)

  def test_str(self) -> None:
    for zs in ShierZhangsheng:
      self.assertEqual(str(zs), zs.value)
      self.assertEqual(ShierZhangsheng.from_str(str(zs)), zs)
      self.assertEqual(ShierZhangsheng(str(zs)), zs)

      self.assertEqual(''.join([str(zs) for zs in ShierZhangsheng.as_list()]),
                       '长生沐浴冠带临官帝旺衰病死墓绝胎养')
