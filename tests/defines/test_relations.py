# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relations.py

import unittest

from src.defines import (
  TianganRelation, 天干关系, DizhiRelation, 地支关系,
)


class TestTianganRelation(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(TianganRelation, 天干关系)
    self.assertEqual(len(TianganRelation), 4) # 合、冲、生、克

  def test_str(self) -> None:
    for relation in TianganRelation:
      self.assertEqual(str(relation), relation.value)
      self.assertEqual(f'{relation}', relation.value)
      self.assertEqual(TianganRelation.from_str(str(relation)), relation)
      self.assertEqual(TianganRelation(str(relation)), relation)

    with self.assertRaises(ValueError):
      TianganRelation.from_str('甲')
    with self.assertRaises(ValueError):
      TianganRelation.from_str('和')
    with self.assertRaises(ValueError):
      TianganRelation.from_str('冲 ')

    self.assertEqual(''.join([str(relation) for relation in TianganRelation]), '合冲生克')


class TestDizhiRelation(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(DizhiRelation, 地支关系)
    self.assertEqual(len(DizhiRelation), 13) # 三会、六合、暗合、通合、通禄合、三合、半合、刑、冲、破、害、生、克

  def test_str(self) -> None:
    for relation in DizhiRelation:
      self.assertEqual(str(relation), relation.value)
      self.assertEqual(f'{relation}', relation.value)
      self.assertEqual(DizhiRelation.from_str(str(relation)), relation)
      self.assertEqual(DizhiRelation(str(relation)), relation)

    with self.assertRaises(ValueError):
      DizhiRelation.from_str('甲')
    with self.assertRaises(ValueError):
      DizhiRelation.from_str('八合')
    with self.assertRaises(ValueError):
      DizhiRelation.from_str('冲 ')

    self.assertEqual(''.join([str(relation) for relation in DizhiRelation]), '三会六合暗合通合通禄合三合半合刑冲破害生克')
