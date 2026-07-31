# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_yinyang.py

import unittest

from src.defines import (
  Yinyang, 阴阳,
)


class TestYinyang(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Yinyang), 2)
    self.assertIs(Yinyang.阴, Yinyang.YIN)
    self.assertIs(Yinyang.阳, Yinyang.YANG)

    self.assertEqual(Yinyang.阴.value, '阴')
    self.assertNotEqual(Yinyang.阴, Yinyang.阳)
    self.assertNotEqual(Yinyang.阴.value, Yinyang.阳.value)

    self.assertEqual(len(Yinyang.as_list()), 2)
    self.assertEqual(Yinyang.as_list()[0], Yinyang.阳)
    self.assertEqual(Yinyang.as_list()[1], Yinyang.阴)

    self.assertIs(阴阳, Yinyang)

  def test_str(self) -> None:
    self.assertEqual(str(Yinyang.阴), '阴')
    self.assertEqual(str(Yinyang.阳), '阳')
    self.assertEqual(Yinyang.from_str('阴'), Yinyang.阴)
    self.assertEqual(Yinyang.from_str('阳'), Yinyang.阳)
    self.assertEqual(Yinyang('阴'), Yinyang.阴)
    self.assertEqual(Yinyang('阳'), Yinyang.阳)

    self.assertEqual(''.join([str(e) for e in Yinyang.as_list()]), '阳阴')

    self.assertEqual(Yinyang.from_str('阴'), Yinyang.阴)
    self.assertEqual(Yinyang.from_str('阳'), Yinyang.阳)

    with self.assertRaises(ValueError):
      Yinyang.from_str('甲')
    with self.assertRaises(ValueError):
      Yinyang.from_str('辰')

  def test_opposite(self) -> None:
    self.assertEqual(Yinyang.阴.opposite, Yinyang.阳)
    self.assertEqual(Yinyang.阳.opposite, Yinyang.阴)
