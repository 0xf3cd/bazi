# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_interpreter.py

import pytest

from src.descriptions import ShishenDescription, TianganDescription
from src.defines import Tiangan, Shishen
from src.descriptions import SHISHEN_DESCRIPTIONS, TIANGAN_DESCRIPTIONS
from src.interpreter import Interpreter


def test_interpret_shishen() -> None:
  for shishen in Shishen:
    result: ShishenDescription = Interpreter.interpret_shishen(shishen)

    keys: list[str] = ['general', 'in_good_status', 'in_bad_status', 'relationship']
    for k in keys:
      assert k in result
      assert isinstance(result[k], list) # type: ignore # mypy complains.
      assert len(result[k]) >= 1 # type: ignore # mypy complains.
      for d in result[k]: # type: ignore # mypy complains.
        assert isinstance(d, str)
        assert len(d) >= 1

        assert d == d.strip(), f'"{d}" not stripped' # No space at the beginning or end.
        assert d[-1] == '。', f'"{d}" not ending with "。"' # End with '。'.

    assert result == Interpreter.interpret_shishen(shishen)


def test_interpret_tiangan() -> None:
  for tg in Tiangan:
    result: TianganDescription = Interpreter.interpret_tiangan(tg)

    keys: list[str] = ['general', 'personality']
    for k in keys:
      assert k in result
      assert isinstance(result[k], list) # type: ignore # mypy complains.
      assert len(result[k]) >= 1 # type: ignore # mypy complains.
      for d in result[k]: # type: ignore # mypy complains.
        assert isinstance(d, str)
        assert len(d) >= 1

        assert d == d.strip(), f'"{d}" not stripped' # No space at the beginning or end.
        assert d[-1] == '。', f'"{d}" not ending with "。"' # End with '。'.

    assert result == Interpreter.interpret_tiangan(tg)


def test_corpus_is_frozen() -> None:
  # The corpus tables are frozen: reassigning an entry must fail, and mutating a
  # returned description must not corrupt the corpus.
  # 语料表是冻结的：覆盖条目必须报错；修改返回的描述不能污染语料库。
  with pytest.raises(TypeError):
    SHISHEN_DESCRIPTIONS[Shishen.比肩] = SHISHEN_DESCRIPTIONS[Shishen.比肩] # type: ignore # mypy complains.
  with pytest.raises(TypeError):
    TIANGAN_DESCRIPTIONS[Tiangan.甲] = TIANGAN_DESCRIPTIONS[Tiangan.甲] # type: ignore # mypy complains.

  mutated_shishen: ShishenDescription = Interpreter.interpret_shishen(Shishen.比肩)
  mutated_shishen['general'].append('污染内容')
  assert '污染内容' not in Interpreter.interpret_shishen(Shishen.比肩)['general']

  mutated_tg: TianganDescription = Interpreter.interpret_tiangan(Tiangan.甲)
  mutated_tg['general'].append('污染内容')
  assert '污染内容' not in Interpreter.interpret_tiangan(Tiangan.甲)['general']
