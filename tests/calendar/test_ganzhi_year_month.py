# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from bazi.calendar.dates import GanzhiYearMonth, JieqiTime
from bazi.defines import Dizhi, Jieqi


@pytest.mark.parametrize('month,dizhi,jie,solar_year', [
  (1,  Dizhi.寅, Jieqi.立春, 2024), (2,  Dizhi.卯, Jieqi.惊蛰, 2024),
  (3,  Dizhi.辰, Jieqi.清明, 2024), (4,  Dizhi.巳, Jieqi.立夏, 2024),
  (5,  Dizhi.午, Jieqi.芒种, 2024), (6,  Dizhi.未, Jieqi.小暑, 2024),
  (7,  Dizhi.申, Jieqi.立秋, 2024), (8,  Dizhi.酉, Jieqi.白露, 2024),
  (9,  Dizhi.戌, Jieqi.寒露, 2024), (10, Dizhi.亥, Jieqi.立冬, 2024),
  (11, Dizhi.子, Jieqi.大雪, 2024), (12, Dizhi.丑, Jieqi.小寒, 2025),
])
def test_month_coordinate(month: int, dizhi: Dizhi, jie: Jieqi, solar_year: int) -> None:
  value = GanzhiYearMonth(2024, month)
  assert value.dizhi is dizhi
  assert value.opening_jie == (solar_year, jie)
  assert GanzhiYearMonth.from_dizhi(2024, dizhi) == value
  assert GanzhiYearMonth.from_jie(JieqiTime(jie, datetime(solar_year, 1, 1))) == value
  assert hash(GanzhiYearMonth.from_dizhi(2024, dizhi)) == hash(value)


def test_month_order_and_immutability() -> None:
  assert GanzhiYearMonth(2023, 12) < GanzhiYearMonth(2024, 1) < GanzhiYearMonth(2024, 12)
  value = GanzhiYearMonth(2024, 1)
  with pytest.raises(FrozenInstanceError):
    value.month = 12 # type: ignore[misc]
  assert value != (2024, 1)
  with pytest.raises(TypeError):
    _ = value < (2024, 1) # type: ignore[operator]


@pytest.mark.parametrize('year,month,error', [
  ('2024', 1, TypeError), (2024, '1', TypeError), (2024, None, TypeError),
  (2024, 0, ValueError), (2024, 13, ValueError), (2024, -1, ValueError),
])
def test_invalid_coordinate(year: object, month: object, error: type[Exception]) -> None:
  with pytest.raises(error):
    GanzhiYearMonth(year, month) # type: ignore[arg-type]


@pytest.mark.parametrize('jie,error', [
  (None, TypeError),
  (JieqiTime('立春', datetime(2024, 2, 4)), TypeError), # type: ignore[arg-type]
  (JieqiTime(Jieqi.立春, '2024-02-04'), TypeError), # type: ignore[arg-type]
  (JieqiTime(Jieqi.雨水, datetime(2024, 2, 19)), ValueError),
])
def test_invalid_opening_jie(jie: object, error: type[Exception]) -> None:
  with pytest.raises(error):
    GanzhiYearMonth.from_jie(jie) # type: ignore[arg-type]


def test_invalid_month_branch() -> None:
  with pytest.raises(TypeError):
    GanzhiYearMonth.from_dizhi(2024, '寅') # type: ignore[arg-type]
  with pytest.raises(TypeError):
    GanzhiYearMonth.from_dizhi('2024', Dizhi.寅) # type: ignore[arg-type]
