# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_interpreter.py

import unittest
from src import (
  BaziChart, Shishen, Tiangan,
  ShishenDescription, TianganDescription, Interpreter
)

class TestInterpreter(unittest.TestCase):
  def test_interpret_shishen(self) -> None:
    for shishen in Shishen:
      result: ShishenDescription = Interpreter.interpret_shishen(shishen)

      keys: list[str] = ['general', 'in_good_status', 'in_bad_status', 'relationship']
      for k in keys:
        self.assertIn(k, result)
        self.assertIsInstance(result[k], list)
        self.assertGreaterEqual(len(result[k]), 1)
        for d in result[k]:
          self.assertIsInstance(d, str)
          self.assertGreaterEqual(len(d), 1)

          self.assertEqual(d, d.strip(), f'"{d}" not stripped') # No space at the beginning or end.
          self.assertTrue(d[-1] == '。', f'"{d}" not ending with "。"') # End with '。'.

      self.assertEqual(result, Interpreter.interpret_shishen(shishen))

  def test_interpret_tiangan(self) -> None:
    for tg in Tiangan:
      result: TianganDescription = Interpreter.interpret_tiangan(tg)

      keys: list[str] = ['general', 'personality']
      for k in keys:
        self.assertIn(k, result)
        self.assertIsInstance(result[k], list)
        self.assertGreaterEqual(len(result[k]), 1)
        for d in result[k]:
          self.assertIsInstance(d, str)
          self.assertGreaterEqual(len(d), 1)

          self.assertEqual(d, d.strip(), f'"{d}" not stripped') # No space at the beginning or end.
          self.assertTrue(d[-1] == '。', f'"{d}" not ending with "。"') # End with '。'.

      self.assertEqual(result, Interpreter.interpret_tiangan(tg))

  def test_chart(self) -> None:
    chart: BaziChart = BaziChart.random()
    interpretation: Interpreter = Interpreter(chart)
    self.assertEqual(chart.json, interpretation.chart.json)
