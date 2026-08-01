# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_dizhi.py

import pytest

from src.defines import (
  Tiangan, Dizhi, 地支,
)


def test_basic() -> None:
  assert 12 == len(Dizhi)
  assert '子' == Dizhi.ZI.value
  assert Dizhi('子') == Dizhi.子
  assert Dizhi.WEI != Dizhi.SHEN
  assert Dizhi.WEI.value != Dizhi.SHEN.value


def test_alias() -> None:
  assert 地支 == Dizhi
  assert 地支 is Dizhi
  assert 12 == len(地支)

  assert Dizhi.子 is Dizhi.ZI
  assert Dizhi.子 is 地支.ZI
  assert Dizhi.子 is 地支.子

  assert Dizhi.丑 is not Dizhi.午

  assert '午' == 地支.午.value
  assert '午' == Dizhi.午.value
  assert '未' == 地支.WEI.value
  assert Dizhi.午.value == Dizhi.WU.value
  assert Dizhi.午.value == 地支.WU.value

  assert '未' != 地支.SHEN.value
  assert 地支.申 != 地支.未

  for e in 地支:
    assert e.value is not None
    assert e in Dizhi

  for e in Dizhi:
    assert e.value is not None
    assert e in 地支


def test_as_list() -> None:
  assert Dizhi.as_list() == list(Dizhi)
  assert Dizhi.as_list() == \
    [Dizhi.子, Dizhi.丑, Dizhi.寅, Dizhi.卯, Dizhi.辰, Dizhi.巳, Dizhi.午, Dizhi.未, Dizhi.申, Dizhi.酉, Dizhi.戌, Dizhi.亥]


def test_from_str() -> None:
  with pytest.raises(ValueError):
    Dizhi.from_str('子子')
  with pytest.raises(ValueError):
    Dizhi.from_str('ZI')
  with pytest.raises(ValueError):
    Dizhi.from_str('Zi')
  with pytest.raises(ValueError):
    Dizhi.from_str('甲')
  with pytest.raises(TypeError):
    Dizhi.from_str(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    Dizhi.from_str(0) # type: ignore
  with pytest.raises(TypeError):
    Dizhi.from_str(Tiangan.丁) # type: ignore

  assert Dizhi.from_str('寅') == Dizhi.寅
  assert Dizhi.寅 == Dizhi.from_str('寅')
  assert Dizhi.from_str('卯') == Dizhi.from_str('卯')
  assert Dizhi.寅 != Dizhi.from_str('卯')
  assert Dizhi.from_str('卯') != Dizhi.from_str('寅')


def test_str() -> None:
  for e in Dizhi:
    assert str(e) == e.value
    assert Dizhi(str(e)) is e
  for e in Dizhi.as_list():
    assert str(e) == e.value
    assert Dizhi(str(e)) is e

  assert '子丑寅卯辰巳午未申酉戌亥' == ''.join([str(e) for e in Dizhi.as_list()])


def test_index() -> None:
  assert Dizhi.子.index == 0
  assert Dizhi.丑.index == 1
  assert Dizhi.寅.index == 2
  assert Dizhi.卯.index == 3
  assert Dizhi.辰.index == 4
  assert Dizhi.巳.index == 5
  assert Dizhi.午.index == 6
  assert Dizhi.未.index == 7
  assert Dizhi.申.index == 8
  assert Dizhi.酉.index == 9
  assert Dizhi.戌.index == 10
  assert Dizhi.亥.index == 11


def test_from_index() -> None:
  assert Dizhi.from_index(0) == Dizhi.子
  assert Dizhi.from_index(1) == Dizhi.丑
  assert Dizhi.from_index(2) == Dizhi.寅
  assert Dizhi.from_index(3) == Dizhi.卯
  assert Dizhi.from_index(4) == Dizhi.辰
  assert Dizhi.from_index(5) == Dizhi.巳
  assert Dizhi.from_index(6) == Dizhi.午
  assert Dizhi.from_index(7) == Dizhi.未
  assert Dizhi.from_index(8) == Dizhi.申
  assert Dizhi.from_index(9) == Dizhi.酉
  assert Dizhi.from_index(10) == Dizhi.戌
  assert Dizhi.from_index(11) == Dizhi.亥
  with pytest.raises(IndexError):
    Dizhi.from_index(12)
  with pytest.raises(IndexError):
    Dizhi.from_index(-13)
