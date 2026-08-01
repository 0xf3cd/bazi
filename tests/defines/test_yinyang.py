# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_yinyang.py

import pytest

from src.defines import (
  Yinyang, 阴阳,
)


def test_basic() -> None:
  assert len(Yinyang) == 2
  assert Yinyang.阴 is Yinyang.YIN
  assert Yinyang.阳 is Yinyang.YANG

  assert Yinyang.阴.value == '阴'
  assert Yinyang.阴 != Yinyang.阳
  assert Yinyang.阴.value != Yinyang.阳.value

  assert len(Yinyang.as_list()) == 2
  assert Yinyang.as_list()[0] == Yinyang.阳
  assert Yinyang.as_list()[1] == Yinyang.阴

  assert 阴阳 is Yinyang


def test_str() -> None:
  assert str(Yinyang.阴) == '阴'
  assert str(Yinyang.阳) == '阳'
  assert Yinyang.from_str('阴') == Yinyang.阴
  assert Yinyang.from_str('阳') == Yinyang.阳
  assert Yinyang('阴') == Yinyang.阴
  assert Yinyang('阳') == Yinyang.阳

  assert ''.join([str(e) for e in Yinyang.as_list()]) == '阳阴'

  assert Yinyang.from_str('阴') == Yinyang.阴
  assert Yinyang.from_str('阳') == Yinyang.阳

  with pytest.raises(ValueError):
    Yinyang.from_str('甲')
  with pytest.raises(ValueError):
    Yinyang.from_str('辰')


def test_opposite() -> None:
  assert Yinyang.阴.opposite == Yinyang.阳
  assert Yinyang.阳.opposite == Yinyang.阴
