# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_utils.py

import unittest

import random

from src.Defines import Dizhi
from src.Utils import RelationshipUtils


class TestRelationshipUtils(unittest.TestCase):
  def test_taohua(self) -> None:
    expected_table: dict[Dizhi, Dizhi] = {
      Dizhi.申 : Dizhi.酉, Dizhi.子 : Dizhi.酉, Dizhi.辰 : Dizhi.酉,
      Dizhi.寅 : Dizhi.卯, Dizhi.午 : Dizhi.卯, Dizhi.戌 : Dizhi.卯,
      Dizhi.亥 : Dizhi.子, Dizhi.卯 : Dizhi.子, Dizhi.未 : Dizhi.子,
      Dizhi.巳 : Dizhi.午, Dizhi.酉 : Dizhi.午, Dizhi.丑 : Dizhi.午,
    }

    for _ in range(100):
      dz1, dz2 = random.choices(Dizhi.as_list(), k=2)
      self.assertEqual(RelationshipUtils.taohua(dz1, dz2), expected_table[dz1] is dz2)
