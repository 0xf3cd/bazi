# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shishen.py

import pytest

from src.defines import (
  Shishen, 十神,
)


def test_basic() -> None:
  assert len(Shishen) == 10
  assert len(Shishen.as_list()) == 10
  assert 十神 is Shishen
  assert Shishen('比肩').value == '比肩'
  assert Shishen('食神').value == '食神'
  assert Shishen('偏印').value != '食神'


def test_str() -> None:
  # Two characters - fullname.
  assert str(Shishen.比肩) == '比肩'
  assert str(Shishen.劫财) == '劫财'
  assert str(Shishen.食神) == '食神'
  assert str(Shishen.伤官) == '伤官'
  assert str(Shishen.正财) == '正财'
  assert str(Shishen.偏财) == '偏财'
  assert str(Shishen.正官) == '正官'
  assert str(Shishen.七杀) == '七杀'
  assert str(Shishen.正印) == '正印'
  assert str(Shishen.偏印) == '偏印'

  for s in Shishen:
    assert str(s) == s.value
    assert Shishen.from_str(str(s)) == s
    assert Shishen(str(s)) == s

  assert ''.join([str(s) for s in Shishen.as_list()]) == \
         '比肩劫财食神伤官正财偏财正官七杀正印偏印'

  # One character - abbreviation.
  assert len(Shishen.str_mapping_table()) == 10

  assert Shishen.from_str('比') is Shishen.比肩
  assert Shishen.from_str('劫') is Shishen.劫财
  assert Shishen.from_str('食') is Shishen.食神
  assert Shishen.from_str('伤') is Shishen.伤官
  assert Shishen.from_str('财') is Shishen.正财
  assert Shishen.from_str('才') is Shishen.偏财
  assert Shishen.from_str('官') is Shishen.正官
  assert Shishen.from_str('杀') is Shishen.七杀
  assert Shishen.from_str('印') is Shishen.正印
  assert Shishen.from_str('枭') is Shishen.偏印

  assert ''.join([s.abbr for s in Shishen]) == '比劫食伤财才官杀印枭'

  with pytest.raises(AssertionError):
    Shishen.from_str('甲')
  with pytest.raises(AssertionError):
    Shishen.from_str('辰')
  with pytest.raises(AssertionError):
    Shishen.from_str('')
  with pytest.raises(ValueError):
    Shishen.from_str('甲子')
  with pytest.raises(ValueError):
    Shishen.from_str('比间')
  with pytest.raises(ValueError):
    Shishen.from_str('枭神')
