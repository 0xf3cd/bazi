# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shier_zhangsheng.py

import pytest

from src.defines import (
  ShierZhangsheng, 十二长生,
)


def test_basic() -> None:
  assert ShierZhangsheng is 十二长生
  assert len(ShierZhangsheng) == 12
  assert len(ShierZhangsheng.as_list()) == 12
  assert next(iter(ShierZhangsheng)).value == '长生'
  assert list(ShierZhangsheng)[-1].value == '养'


def test_index() -> None:
  for zs in ShierZhangsheng:
    assert ShierZhangsheng.from_index(zs.index) == zs
    assert ShierZhangsheng.from_index(zs.index) == zs
    assert ShierZhangsheng.as_list()[zs.index] == zs

  with pytest.raises(IndexError):
    ShierZhangsheng.from_index(12)
  with pytest.raises(IndexError):
    ShierZhangsheng.from_index(-13)


def test_str() -> None:
  for zs in ShierZhangsheng:
    assert str(zs) == zs.value
    assert ShierZhangsheng.from_str(str(zs)) == zs
    assert ShierZhangsheng(str(zs)) == zs

    assert ''.join([str(zs) for zs in ShierZhangsheng.as_list()]) == '长生沐浴冠带临官帝旺衰病死墓绝胎养'
