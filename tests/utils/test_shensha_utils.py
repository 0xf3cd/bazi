# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shensha_utils.py

import unittest

import random

from src.Defines import Tiangan, Dizhi
from src.Utils import ShenshaUtils


class TestShenshaUtils(unittest.TestCase):
  def test_taohua(self) -> None:
    expected_table: dict[Dizhi, Dizhi] = {
      Dizhi(k_str) : Dizhi(v_str)
      for k_strs, v_str in zip(['申子辰', '寅午戌', '亥卯未', '巳酉丑'], '酉卯子午')
      for k_str in k_strs
    }

    for _ in range(16):
      dz1, dz2 = random.choices(Dizhi.as_list(), k=2)
      self.assertEqual(ShenshaUtils.taohua(dz1, dz2), expected_table[dz1] is dz2)
      self.assertEqual(ShenshaUtils.taohua(dz1, dz2), expected_table[dz1] is dz2, 'Result consistency')

  def test_hongyan(self) -> None:
    expected_table: dict[Dizhi, list[Tiangan]] = {
      Dizhi.午 : [Tiangan.甲],
      Dizhi.申 : [Tiangan.乙, Tiangan.癸],
      Dizhi.寅 : [Tiangan.丙],
      Dizhi.未 : [Tiangan.丁],
      Dizhi.辰 : [Tiangan.戊, Tiangan.己],
      Dizhi.戌 : [Tiangan.庚],
      Dizhi.酉 : [Tiangan.辛],
      Dizhi.子 : [Tiangan.壬],
    }

    for _ in range(16):
      tg, dz = random.choice(Tiangan.as_list()), random.choice(Dizhi.as_list())
      expected_result: bool = dz in expected_table and tg in expected_table[dz]
      self.assertEqual(ShenshaUtils.hongyan(tg, dz), expected_result)
      self.assertEqual(ShenshaUtils.hongyan(tg, dz), expected_result, 'Result consistency')

  def test_hongluan(self) -> None:
    expected_table: dict[Dizhi, Dizhi] = {}
    for dz1, dz2 in [
      (Dizhi.子, Dizhi.卯),
      (Dizhi.丑, Dizhi.寅),
      (Dizhi.辰, Dizhi.亥),
      (Dizhi.巳, Dizhi.戌),
      (Dizhi.午, Dizhi.酉),
      (Dizhi.未, Dizhi.申),
    ]:
      expected_table[dz1] = dz2
      expected_table[dz2] = dz1

    for _ in range(16):
      dz1, dz2 = random.choices(Dizhi.as_list(), k=2)
      self.assertEqual(ShenshaUtils.hongluan(dz1, dz2), expected_table[dz1] is dz2)
      self.assertEqual(ShenshaUtils.hongluan(dz1, dz2), expected_table[dz1] is dz2, 'Result consistency')

  def test_tianxi(self) -> None:
    expected_table: dict[Dizhi, Dizhi] = {}
    for dz1, dz2 in [
      (Dizhi.子, Dizhi.酉),
      (Dizhi.丑, Dizhi.申),
      (Dizhi.未, Dizhi.寅),
      (Dizhi.午, Dizhi.卯),
      (Dizhi.辰, Dizhi.巳),
      (Dizhi.戌, Dizhi.亥),
    ]:
      expected_table[dz1] = dz2
      expected_table[dz2] = dz1

    for _ in range(16):
      dz1, dz2 = random.choices(Dizhi.as_list(), k=2)
      self.assertEqual(ShenshaUtils.tianxi(dz1, dz2), expected_table[dz1] is dz2)
      self.assertEqual(ShenshaUtils.tianxi(dz1, dz2), expected_table[dz1] is dz2, 'Result consistency')

  def test_yima(self) -> None:
    expected_table: dict[Dizhi, Dizhi] = {
      Dizhi(k_str) : Dizhi(v_str)
      for k_strs, v_str in zip(['申子辰', '寅午戌', '亥卯未', '巳酉丑'], '寅申巳亥')
      for k_str in k_strs
    }

    for _ in range(16):
      dz1, dz2 = random.choices(Dizhi.as_list(), k=2)
      self.assertEqual(ShenshaUtils.yima(dz1, dz2), expected_table[dz1] is dz2)
      self.assertEqual(ShenshaUtils.yima(dz1, dz2), expected_table[dz1] is dz2, 'Result consistency')
