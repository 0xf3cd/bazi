# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_tiangan.py

import pytest

from src.defines import (
  Tiangan, 天干,
)


def test_basic() -> None:
  assert len(Tiangan) == 10
  assert Tiangan.JIA.value == '甲'
  assert Tiangan('甲').value == '甲'
  assert Tiangan.WU != Tiangan.REN
  assert Tiangan.WU.value != Tiangan.REN.value


def test_alias() -> None:
  assert 天干 == Tiangan
  assert 天干 is Tiangan
  assert len(天干) == 10

  assert Tiangan.甲 is Tiangan.JIA
  assert Tiangan.甲 is Tiangan.甲
  assert 天干.甲 is Tiangan.甲
  assert 天干.甲 is 天干.JIA
  assert 天干.BING is 天干.丙

  assert Tiangan.甲 is not Tiangan.乙

  assert 天干.甲.value == '甲'
  assert 天干.JIA.value == '甲'
  assert 天干.丁.value == Tiangan.丁.value
  assert 天干.甲.value == Tiangan.JIA.value
  assert 天干.甲.value == 天干.JIA.value

  assert 天干.癸 != 天干.庚
  assert 天干.甲.value != Tiangan.丁.value
  assert 天干.WU.value != '甲'

  for e in Tiangan:
    assert e.value is not None
    assert e in 天干

  for e in 天干:
    assert e.value is not None
    assert e in Tiangan


def test_as_list() -> None:
  assert Tiangan.as_list() == list(Tiangan)
  assert Tiangan.as_list() == \
    [Tiangan.甲, Tiangan.乙, Tiangan.丙, Tiangan.丁, Tiangan.戊, Tiangan.己, Tiangan.庚, Tiangan.辛, Tiangan.壬, Tiangan.癸]


def test_from_str() -> None:
  with pytest.raises(ValueError):
    Tiangan.from_str('甲甲')
  with pytest.raises(ValueError):
    Tiangan.from_str('JIA')
  with pytest.raises(ValueError):
    Tiangan.from_str('Jia')
  with pytest.raises(ValueError):
    Tiangan.from_str('子')
  with pytest.raises(TypeError):
    Tiangan.from_str(Tiangan.甲) # type: ignore
  with pytest.raises(TypeError):
    Tiangan.from_str(0) # type: ignore

  assert Tiangan.from_str('甲') == Tiangan.甲
  assert Tiangan.甲 == Tiangan.from_str('甲')
  assert Tiangan.from_str('丁') == Tiangan.from_str('丁')
  assert Tiangan.甲 != Tiangan.from_str('丁')
  assert Tiangan.from_str('丁') != Tiangan.from_str('甲')


def test_str() -> None:
  for e in Tiangan:
    assert str(e) == e.value
    assert Tiangan(str(e)) is e
  for e in Tiangan.as_list():
    assert str(e) == e.value
    assert Tiangan(str(e)) is e

  assert '甲乙丙丁戊己庚辛壬癸' == ''.join([str(e) for e in Tiangan.as_list()])


def test_index() -> None:
  assert Tiangan.甲.index == 0
  assert Tiangan.乙.index == 1
  assert Tiangan.丙.index == 2
  assert Tiangan.丁.index == 3
  assert Tiangan.戊.index == 4
  assert Tiangan.己.index == 5
  assert Tiangan.庚.index == 6
  assert Tiangan.辛.index == 7
  assert Tiangan.壬.index == 8
  assert Tiangan.癸.index == 9


def test_from_index() -> None:
  assert Tiangan.from_index(0) == Tiangan.甲
  assert Tiangan.from_index(1) == Tiangan.乙
  assert Tiangan.from_index(2) == Tiangan.丙
  assert Tiangan.from_index(3) == Tiangan.丁
  assert Tiangan.from_index(4) == Tiangan.戊
  assert Tiangan.from_index(5) == Tiangan.己
  assert Tiangan.from_index(6) == Tiangan.庚
  assert Tiangan.from_index(7) == Tiangan.辛
  assert Tiangan.from_index(8) == Tiangan.壬
  assert Tiangan.from_index(9) == Tiangan.癸
  with pytest.raises(IndexError):
    Tiangan.from_index(10)
  with pytest.raises(IndexError):
    Tiangan.from_index(-11)
