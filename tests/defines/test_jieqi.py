# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_jieqi.py

import pytest

from src.defines import (
  Tiangan, Jieqi, 节气,
)


def test_basic() -> None:
  assert len(Jieqi) == 24
  assert Jieqi.QINGMING.value == '清明'
  assert Jieqi('清明') == Jieqi.清明
  assert Jieqi.QINGMING != Jieqi.LICHUN
  assert Jieqi.QINGMING.value != Jieqi.LICHUN.value


def test_alias() -> None:
  assert 节气 is Jieqi
  assert len(节气) == len(Jieqi)

  for jq in Jieqi:
    assert jq.value is not None
    assert jq in 节气
    assert jq.value in (jq.value for jq in 节气)

  for jq in 节气:
    assert jq.value is not None
    assert jq in Jieqi
    assert jq.value in (jq.value for jq in Jieqi)

  assert 节气.雨水 is Jieqi.YUSHUI
  assert 节气.雨水 is 节气.YUSHUI
  assert 节气.雨水 is Jieqi.雨水

  assert 节气.惊蛰 == Jieqi.JINGZHE
  assert 节气.春分 != 节气.秋分
  assert Jieqi.春分 != Jieqi.秋分


def test_as_list() -> None:
  assert Jieqi.as_list() == list(Jieqi)
  assert Jieqi.as_list() == [
    Jieqi.立春, Jieqi.雨水, Jieqi.惊蛰, Jieqi.春分, Jieqi.清明, Jieqi.谷雨, Jieqi.立夏, Jieqi.小满, Jieqi.芒种, Jieqi.夏至, Jieqi.小暑, Jieqi.大暑,
    Jieqi.立秋, Jieqi.处暑, Jieqi.白露, Jieqi.秋分, Jieqi.寒露, Jieqi.霜降, Jieqi.立冬, Jieqi.小雪, Jieqi.大雪, Jieqi.冬至, Jieqi.小寒, Jieqi.大寒
  ]
  assert Jieqi.as_list(ganzhi_year=True) == [
    Jieqi.立春, Jieqi.雨水, Jieqi.惊蛰, Jieqi.春分, Jieqi.清明, Jieqi.谷雨, Jieqi.立夏, Jieqi.小满, Jieqi.芒种, Jieqi.夏至, Jieqi.小暑, Jieqi.大暑,
    Jieqi.立秋, Jieqi.处暑, Jieqi.白露, Jieqi.秋分, Jieqi.寒露, Jieqi.霜降, Jieqi.立冬, Jieqi.小雪, Jieqi.大雪, Jieqi.冬至, Jieqi.小寒, Jieqi.大寒
  ]
  assert Jieqi.as_list(ganzhi_year=False) == [
    Jieqi.小寒, Jieqi.大寒, Jieqi.立春, Jieqi.雨水, Jieqi.惊蛰, Jieqi.春分, Jieqi.清明, Jieqi.谷雨, Jieqi.立夏, Jieqi.小满, Jieqi.芒种, Jieqi.夏至,
    Jieqi.小暑, Jieqi.大暑, Jieqi.立秋, Jieqi.处暑, Jieqi.白露, Jieqi.秋分, Jieqi.寒露, Jieqi.霜降, Jieqi.立冬, Jieqi.小雪, Jieqi.大雪, Jieqi.冬至,
  ]


def test_from_str() -> None:
  with pytest.raises(ValueError):
    Jieqi.from_str('甲甲')
  with pytest.raises(ValueError):
    Jieqi.from_str('處暑') # Not supporting traditional Chinese.
  with pytest.raises(AssertionError):
    Jieqi.from_str('立秋 ')
  with pytest.raises(AssertionError):
    Jieqi.from_str('SHUNFEN')
  with pytest.raises(AssertionError):
    Jieqi.from_str('Xiazhi')
  with pytest.raises(AssertionError):
    Jieqi.from_str('春')
  with pytest.raises(AssertionError):
    Jieqi.from_str(Tiangan.甲) # type: ignore
  with pytest.raises(AssertionError):
    Jieqi.from_str(0) # type: ignore

  for jq in Jieqi:
    assert Jieqi.from_str(str(jq)) == jq
    assert Jieqi(str(jq)) == jq

  assert Jieqi.from_str('秋分') == Jieqi.秋分
  assert Jieqi.from_str('秋分') == Jieqi.from_str('秋分')
  assert Jieqi.from_str('秋分') != Jieqi.from_str('小寒')

  assert Jieqi.from_str('立春') is Jieqi.立春
  assert Jieqi.from_str('雨水') is Jieqi.雨水
  assert Jieqi.from_str('惊蛰') is Jieqi.惊蛰
  assert Jieqi.from_str('春分') is Jieqi.春分
  assert Jieqi.from_str('清明') is Jieqi.清明
  assert Jieqi.from_str('谷雨') is Jieqi.谷雨
  assert Jieqi.from_str('立夏') is Jieqi.立夏
  assert Jieqi.from_str('小满') is Jieqi.小满
  assert Jieqi.from_str('芒种') is Jieqi.芒种
  assert Jieqi.from_str('夏至') is Jieqi.夏至
  assert Jieqi.from_str('小暑') is Jieqi.小暑
  assert Jieqi.from_str('大暑') is Jieqi.大暑
  assert Jieqi.from_str('立秋') is Jieqi.立秋
  assert Jieqi.from_str('处暑') is Jieqi.处暑
  assert Jieqi.from_str('白露') is Jieqi.白露
  assert Jieqi.from_str('秋分') is Jieqi.秋分
  assert Jieqi.from_str('寒露') is Jieqi.寒露
  assert Jieqi.from_str('霜降') is Jieqi.霜降
  assert Jieqi.from_str('立冬') is Jieqi.立冬
  assert Jieqi.from_str('小雪') is Jieqi.小雪
  assert Jieqi.from_str('大雪') is Jieqi.大雪
  assert Jieqi.from_str('冬至') is Jieqi.冬至
  assert Jieqi.from_str('小寒') is Jieqi.小寒
  assert Jieqi.from_str('大寒') is Jieqi.大寒


def test_str() -> None:
  for jq in Jieqi:
    assert str(jq) == jq.value
    assert Jieqi.from_str(str(jq)) == jq
  for jq in Jieqi.as_list():
    assert str(jq) == jq.value
    assert Jieqi.from_str(str(jq)) == jq

  assert ''.join([str(jq) for jq in Jieqi.as_list()]) == '立春雨水惊蛰春分清明谷雨立夏小满芒种夏至小暑大暑立秋处暑白露秋分寒露霜降立冬小雪大雪冬至小寒大寒'
