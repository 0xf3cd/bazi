# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_wuxing.py

import pytest

from itertools import product
from src.defines import (
  Wuxing, 五行,
)


def test_basic() -> None:
  assert len(Wuxing) == 5
  assert Wuxing.METAL.value == '金'
  assert Wuxing.金.value == '金'
  assert Wuxing('金') == Wuxing.金
  assert Wuxing.金 != Wuxing.木
  assert Wuxing.金.value != Wuxing.木.value


def test_alias() -> None:
  assert Wuxing.木 is Wuxing.WOOD
  assert Wuxing.火 is Wuxing.FIRE
  assert Wuxing.土 is Wuxing.EARTH
  assert Wuxing.金 is Wuxing.METAL
  assert Wuxing.水 is Wuxing.WATER
  assert Wuxing is 五行


def test_as_list() -> None:
  assert len(Wuxing.as_list()) == 5
  assert Wuxing.as_list()[0] == Wuxing.木
  assert Wuxing.as_list()[1] == Wuxing.火
  assert Wuxing.as_list()[2] == Wuxing.土
  assert Wuxing.as_list()[3] == Wuxing.金
  assert Wuxing.as_list()[4] == Wuxing.水


def test_from_str() -> None:
  assert Wuxing.from_str('木') is Wuxing.木
  assert Wuxing.from_str('火') is Wuxing.火
  assert Wuxing.from_str('土') is Wuxing.土
  assert Wuxing.from_str('金') is Wuxing.金
  assert Wuxing.from_str('水') is Wuxing.水

  with pytest.raises(AssertionError):
    Wuxing.from_str('')
  with pytest.raises(AssertionError):
    Wuxing.from_str('木木')
  with pytest.raises(ValueError):
    Wuxing.from_str('甲')
  with pytest.raises(ValueError):
    Wuxing.from_str('辰')


def test_str() -> None:
  for wx in Wuxing:
    assert str(wx) == wx.value
    assert Wuxing.from_str(str(wx)) == wx

  assert ''.join([str(wx) for wx in Wuxing]) == '木火土金水'


def test_generates_and_destructs() -> None:
  assert Wuxing.木.generates(Wuxing.火)
  assert Wuxing.火.destructs(Wuxing.金)

  wx_list: list[Wuxing] = Wuxing.as_list()
  for wx1, wx2 in product(wx_list, wx_list):
    wx1_index: int = wx_list.index(wx1)
    wx2_index: int = wx_list.index(wx2)

    if (wx1_index + 1) % 5 == wx2_index:
      assert wx1.generates(wx2)
      assert not wx2.generates(wx1)
      assert not wx1.destructs(wx2)
    else:
      assert not wx1.generates(wx2)

    if (wx1_index + 2) % 5 == wx2_index:
      assert wx1.destructs(wx2)
      assert not wx2.destructs(wx1)
      assert not wx1.generates(wx2)
    else:
      assert not wx1.destructs(wx2)
