# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_interpreter.py

import unittest

from src.common import ShishenDescription, TianganDescription
from src.defines import Tiangan, Shishen
from src.descriptions import SHISHEN_DESCRIPTIONS, TIANGAN_DESCRIPTIONS
from src.interpreter import Interpreter

class TestInterpreter(unittest.TestCase):
  def test_interpret_shishen(self) -> None:
    for shishen in Shishen:
      result: ShishenDescription = Interpreter.interpret_shishen(shishen)

      keys: list[str] = ['general', 'in_good_status', 'in_bad_status', 'relationship']
      for k in keys:
        self.assertIn(k, result)
        self.assertIsInstance(result[k], list) # type: ignore # mypy complains.
        self.assertGreaterEqual(len(result[k]), 1) # type: ignore # mypy complains.
        for d in result[k]: # type: ignore # mypy complains.
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
        self.assertIsInstance(result[k], list) # type: ignore # mypy complains.
        self.assertGreaterEqual(len(result[k]), 1) # type: ignore # mypy complains.
        for d in result[k]: # type: ignore # mypy complains.
          self.assertIsInstance(d, str)
          self.assertGreaterEqual(len(d), 1)

          self.assertEqual(d, d.strip(), f'"{d}" not stripped') # No space at the beginning or end.
          self.assertTrue(d[-1] == '。', f'"{d}" not ending with "。"') # End with '。'.

      self.assertEqual(result, Interpreter.interpret_tiangan(tg))

  def test_corpus_is_frozen(self) -> None:
    # The corpus tables are frozen: reassigning an entry must fail, and mutating a
    # returned description must not corrupt the corpus.
    # 语料表是冻结的：覆盖条目必须报错；修改返回的描述不能污染语料库。
    with self.assertRaises(TypeError):
      SHISHEN_DESCRIPTIONS[Shishen.比肩] = SHISHEN_DESCRIPTIONS[Shishen.比肩] # type: ignore # mypy complains.
    with self.assertRaises(TypeError):
      TIANGAN_DESCRIPTIONS[Tiangan.甲] = TIANGAN_DESCRIPTIONS[Tiangan.甲] # type: ignore # mypy complains.

    mutated_shishen: ShishenDescription = Interpreter.interpret_shishen(Shishen.比肩)
    mutated_shishen['general'].append('污染内容')
    self.assertNotIn('污染内容', Interpreter.interpret_shishen(Shishen.比肩)['general'])

    mutated_tg: TianganDescription = Interpreter.interpret_tiangan(Tiangan.甲)
    mutated_tg['general'].append('污染内容')
    self.assertNotIn('污染内容', Interpreter.interpret_tiangan(Tiangan.甲)['general'])
