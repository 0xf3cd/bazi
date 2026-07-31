# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_jieqi.py

import unittest

from src.defines import (
  Tiangan, Jieqi, 节气,
)


class TestJieqi(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(Jieqi), 24)
    self.assertEqual(Jieqi.QINGMING.value, '清明')
    self.assertEqual(Jieqi('清明'), Jieqi.清明)
    self.assertNotEqual(Jieqi.QINGMING, Jieqi.LICHUN)
    self.assertNotEqual(Jieqi.QINGMING.value, Jieqi.LICHUN.value)

  def test_alias(self) -> None:
    self.assertIs(节气, Jieqi)
    self.assertEqual(len(节气), len(Jieqi))

    for jq in Jieqi:
      self.assertIsNotNone(jq.value)
      self.assertIn(jq, 节气)
      self.assertIn(jq.value, (jq.value for jq in 节气))

    for jq in 节气:
      self.assertIsNotNone(jq.value)
      self.assertIn(jq, Jieqi)
      self.assertIn(jq.value, (jq.value for jq in Jieqi))

    self.assertIs(节气.雨水, Jieqi.YUSHUI)
    self.assertIs(节气.雨水, 节气.YUSHUI)
    self.assertIs(节气.雨水, Jieqi.雨水)

    self.assertEqual(节气.惊蛰, Jieqi.JINGZHE)
    self.assertNotEqual(节气.春分, 节气.秋分)
    self.assertNotEqual(Jieqi.春分, Jieqi.秋分)

  def test_as_list(self) -> None:
    self.assertListEqual(Jieqi.as_list(), list(Jieqi))
    self.assertListEqual(Jieqi.as_list(), [
      Jieqi.立春, Jieqi.雨水, Jieqi.惊蛰, Jieqi.春分, Jieqi.清明, Jieqi.谷雨, Jieqi.立夏, Jieqi.小满, Jieqi.芒种, Jieqi.夏至, Jieqi.小暑, Jieqi.大暑, 
      Jieqi.立秋, Jieqi.处暑, Jieqi.白露, Jieqi.秋分, Jieqi.寒露, Jieqi.霜降, Jieqi.立冬, Jieqi.小雪, Jieqi.大雪, Jieqi.冬至, Jieqi.小寒, Jieqi.大寒
    ])
    self.assertListEqual(Jieqi.as_list(ganzhi_year=True), [
      Jieqi.立春, Jieqi.雨水, Jieqi.惊蛰, Jieqi.春分, Jieqi.清明, Jieqi.谷雨, Jieqi.立夏, Jieqi.小满, Jieqi.芒种, Jieqi.夏至, Jieqi.小暑, Jieqi.大暑, 
      Jieqi.立秋, Jieqi.处暑, Jieqi.白露, Jieqi.秋分, Jieqi.寒露, Jieqi.霜降, Jieqi.立冬, Jieqi.小雪, Jieqi.大雪, Jieqi.冬至, Jieqi.小寒, Jieqi.大寒
    ])
    self.assertListEqual(Jieqi.as_list(ganzhi_year=False), [
      Jieqi.小寒, Jieqi.大寒, Jieqi.立春, Jieqi.雨水, Jieqi.惊蛰, Jieqi.春分, Jieqi.清明, Jieqi.谷雨, Jieqi.立夏, Jieqi.小满, Jieqi.芒种, Jieqi.夏至,
      Jieqi.小暑, Jieqi.大暑, Jieqi.立秋, Jieqi.处暑, Jieqi.白露, Jieqi.秋分, Jieqi.寒露, Jieqi.霜降, Jieqi.立冬, Jieqi.小雪, Jieqi.大雪, Jieqi.冬至, 
    ])

  def test_from_str(self) -> None:
    with self.assertRaises(ValueError):
      Jieqi.from_str('甲甲')
    with self.assertRaises(ValueError):
      Jieqi.from_str('處暑') # Not supporting traditional Chinese.
    with self.assertRaises(AssertionError):
      Jieqi.from_str('立秋 ')
    with self.assertRaises(AssertionError):
      Jieqi.from_str('SHUNFEN')
    with self.assertRaises(AssertionError):
      Jieqi.from_str('Xiazhi')
    with self.assertRaises(AssertionError):
      Jieqi.from_str('春')
    with self.assertRaises(AssertionError):
      Jieqi.from_str(Tiangan.甲) # type: ignore
    with self.assertRaises(AssertionError):
      Jieqi.from_str(0) # type: ignore

    for jq in Jieqi:
      self.assertEqual(Jieqi.from_str(str(jq)), jq)
      self.assertEqual(Jieqi(str(jq)), jq)

    self.assertEqual(Jieqi.from_str('秋分'), Jieqi.秋分)
    self.assertEqual(Jieqi.from_str('秋分'), Jieqi.from_str('秋分'))
    self.assertNotEqual(Jieqi.from_str('秋分'), Jieqi.from_str('小寒'))

    self.assertIs(Jieqi.from_str('立春'), Jieqi.立春)
    self.assertIs(Jieqi.from_str('雨水'), Jieqi.雨水)
    self.assertIs(Jieqi.from_str('惊蛰'), Jieqi.惊蛰)
    self.assertIs(Jieqi.from_str('春分'), Jieqi.春分)
    self.assertIs(Jieqi.from_str('清明'), Jieqi.清明)
    self.assertIs(Jieqi.from_str('谷雨'), Jieqi.谷雨)
    self.assertIs(Jieqi.from_str('立夏'), Jieqi.立夏)
    self.assertIs(Jieqi.from_str('小满'), Jieqi.小满)
    self.assertIs(Jieqi.from_str('芒种'), Jieqi.芒种)
    self.assertIs(Jieqi.from_str('夏至'), Jieqi.夏至)
    self.assertIs(Jieqi.from_str('小暑'), Jieqi.小暑)
    self.assertIs(Jieqi.from_str('大暑'), Jieqi.大暑)
    self.assertIs(Jieqi.from_str('立秋'), Jieqi.立秋)
    self.assertIs(Jieqi.from_str('处暑'), Jieqi.处暑)
    self.assertIs(Jieqi.from_str('白露'), Jieqi.白露)
    self.assertIs(Jieqi.from_str('秋分'), Jieqi.秋分)
    self.assertIs(Jieqi.from_str('寒露'), Jieqi.寒露)
    self.assertIs(Jieqi.from_str('霜降'), Jieqi.霜降)
    self.assertIs(Jieqi.from_str('立冬'), Jieqi.立冬)
    self.assertIs(Jieqi.from_str('小雪'), Jieqi.小雪)
    self.assertIs(Jieqi.from_str('大雪'), Jieqi.大雪)
    self.assertIs(Jieqi.from_str('冬至'), Jieqi.冬至)
    self.assertIs(Jieqi.from_str('小寒'), Jieqi.小寒)
    self.assertIs(Jieqi.from_str('大寒'), Jieqi.大寒)

  def test_str(self) -> None:
    for jq in Jieqi:
      self.assertEqual(str(jq), jq.value)
      self.assertEqual(Jieqi.from_str(str(jq)), jq)
    for jq in Jieqi.as_list():
      self.assertEqual(str(jq), jq.value)
      self.assertEqual(Jieqi.from_str(str(jq)), jq)

    self.assertEqual(''.join([str(jq) for jq in Jieqi.as_list()]), 
                     '立春雨水惊蛰春分清明谷雨立夏小满芒种夏至小暑大暑立秋处暑白露秋分寒露霜降立冬小雪大雪冬至小寒大寒')
