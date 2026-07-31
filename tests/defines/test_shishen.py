# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shishen.py

import unittest

from src.defines import (
  Shishen, 十神,
)


class TestShishen(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Shishen), 10)
    self.assertEqual(len(Shishen.as_list()), 10)
    self.assertIs(十神, Shishen)
    self.assertEqual(Shishen('比肩').value, '比肩')
    self.assertEqual(Shishen('食神').value, '食神')
    self.assertNotEqual(Shishen('偏印').value, '食神')

  def test_str(self) -> None:
    with self.subTest('Two characters - fullname'):
      self.assertEqual(str(Shishen.比肩), '比肩')
      self.assertEqual(str(Shishen.劫财), '劫财')
      self.assertEqual(str(Shishen.食神), '食神')
      self.assertEqual(str(Shishen.伤官), '伤官')
      self.assertEqual(str(Shishen.正财), '正财')
      self.assertEqual(str(Shishen.偏财), '偏财')
      self.assertEqual(str(Shishen.正官), '正官')
      self.assertEqual(str(Shishen.七杀), '七杀')
      self.assertEqual(str(Shishen.正印), '正印')
      self.assertEqual(str(Shishen.偏印), '偏印')

      for s in Shishen:
        self.assertEqual(str(s), s.value)
        self.assertEqual(Shishen.from_str(str(s)), s)
        self.assertEqual(Shishen(str(s)), s)

      self.assertEqual(''.join([str(s) for s in Shishen.as_list()]), 
                      '比肩劫财食神伤官正财偏财正官七杀正印偏印')
      
    with self.subTest('One character - abbreviation'):
      self.assertEqual(len(Shishen.str_mapping_table()), 10)

      self.assertIs(Shishen.from_str('比'), Shishen.比肩)
      self.assertIs(Shishen.from_str('劫'), Shishen.劫财)
      self.assertIs(Shishen.from_str('食'), Shishen.食神)
      self.assertIs(Shishen.from_str('伤'), Shishen.伤官)
      self.assertIs(Shishen.from_str('财'), Shishen.正财)
      self.assertIs(Shishen.from_str('才'), Shishen.偏财)
      self.assertIs(Shishen.from_str('官'), Shishen.正官)
      self.assertIs(Shishen.from_str('杀'), Shishen.七杀)
      self.assertIs(Shishen.from_str('印'), Shishen.正印)
      self.assertIs(Shishen.from_str('枭'), Shishen.偏印)

      self.assertEqual(''.join([s.abbr for s in Shishen]), '比劫食伤财才官杀印枭')

      with self.assertRaises(AssertionError):
        Shishen.from_str('甲')
      with self.assertRaises(AssertionError):
        Shishen.from_str('辰')
      with self.assertRaises(AssertionError):
        Shishen.from_str('')
      with self.assertRaises(ValueError):
        Shishen.from_str('甲子')
      with self.assertRaises(ValueError):
        Shishen.from_str('比间')
      with self.assertRaises(ValueError):
        Shishen.from_str('枭神')
