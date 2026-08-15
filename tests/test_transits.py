# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transits.py

import itertools
import random
from datetime import date, datetime

import pytest

from src.data_types import DayunTuple
from src.defines import Ganzhi, Dizhi

from src.bazi import Bazi
from src.bazi_chart import BaziChart
from src.calendar import calendar_utils_of
from src.school import BaziConfig
from src.transits import (
  DayunDatabase,
  TransitDatabase,
  TransitDate,
  TransitKind,
  TransitMonth,
  TransitSet,
  TransitYear,
)


def _dayun_start_gz_year(chart: BaziChart) -> int:
  # Independent recomputation, not a mirror of `next(chart.dayun).ganzhi_year` -- the very
  # expression `TransitDatabase` consumes: the day-level label of `dayun_start_moment`
  # through the chart's own backend, floored at `Bazi.ganzhi_year`.
  return max(
    calendar_utils_of(chart.bazi.config.backend).to_ganzhi(chart.dayun_start_moment).year,
    chart.bazi.ganzhi_year,
  )


def test_simple() -> None:
  chart = BaziChart(Bazi.create('2000-02-04 22:01', 'male'))
  db = DayunDatabase(chart)

  first_dayun = next(chart.dayun)
  for year in range(first_dayun.ganzhi_year, first_dayun.ganzhi_year + 10):
    assert db[year] == DayunTuple(first_dayun.ganzhi_year, Ganzhi.from_str('己卯'))
  for year in range(first_dayun.ganzhi_year + 10, first_dayun.ganzhi_year + 20):
    assert db[year] == DayunTuple(first_dayun.ganzhi_year + 10, Ganzhi.from_str('庚辰'))
  for year in range(first_dayun.ganzhi_year + 20, first_dayun.ganzhi_year + 30):
    assert db[year] == DayunTuple(first_dayun.ganzhi_year + 20, Ganzhi.from_str('辛巳'))


def test_dayun_database() -> None:
  chart = BaziChart.random()
  expected: dict[int, DayunTuple] = {}
  for start_year, dayun_ganzhi in itertools.islice(chart.dayun, 100):
    for year in range(start_year, start_year + 10):
      expected[year] = DayunTuple(start_year, dayun_ganzhi)

  db = DayunDatabase(chart)
  with pytest.raises(TypeError):
    db['2000'] # type: ignore
  with pytest.raises(ValueError):
    db[next(chart.dayun).ganzhi_year - 1]

  years = list(expected.keys())
  for year in random.sample(years, 100):
    assert db[year] == expected[year]


def test_query_shapes() -> None:
  year = TransitYear(1990)
  month = TransitMonth(1990, Dizhi.寅)
  day = TransitDate(date(1990, 5, 20))

  assert year.gz_year == 1990
  assert month == TransitMonth(1990, Dizhi.寅)
  assert day.solar_date == date(1990, 5, 20)
  assert len({year, TransitYear(1990)}) == 1


def test_query_shapes_negative() -> None:
  with pytest.raises(TypeError):
    TransitYear('1990') # type: ignore
  with pytest.raises(TypeError):
    TransitMonth('1990', Dizhi.寅) # type: ignore
  with pytest.raises(TypeError):
    TransitMonth(1990, 3) # type: ignore
  with pytest.raises(TypeError):
    TransitDate('1990-05-20') # type: ignore
  with pytest.raises(TypeError):
    TransitDate(datetime(1990, 5, 20, 12, 0))


def test_transit_set() -> None:
  xiaoyun = Ganzhi.from_str('癸未')
  dayun = Ganzhi.from_str('戊辰')
  liunian = Ganzhi.from_str('甲辰')
  liuyue = Ganzhi.from_str('丙寅')
  liuri = Ganzhi.from_str('戊戌')
  transits = TransitSet(xiaoyun, dayun, liunian, liuyue, liuri)

  assert transits.items == (
    (TransitKind.XIAOYUN, xiaoyun),
    (TransitKind.DAYUN, dayun),
    (TransitKind.LIUNIAN, liunian),
    (TransitKind.LIUYUE, liuyue),
    (TransitKind.LIURI, liuri),
  )
  assert tuple(transits) == tuple(TransitKind)
  assert TransitKind.LIUYUE in transits
  assert object() not in transits
  assert transits.ganzhis == (xiaoyun, dayun, liunian, liuyue, liuri)
  assert transits.json == {
    'xiaoyun': '癸未',
    'dayun': '戊辰',
    'liunian': '甲辰',
    'liuyue': '丙寅',
    'liuri': '戊戌',
  }

  selected = transits.select(TransitKind.LIURI, TransitKind.DAYUN)
  assert selected == TransitSet(dayun=dayun, liuri=liuri)
  assert selected.ganzhis == (dayun, liuri)
  assert selected.json == {'dayun': '戊辰', 'liuri': '戊戌'}


def test_transit_set_negative() -> None:
  with pytest.raises(ValueError):
    TransitSet()
  with pytest.raises(TypeError):
    TransitSet(liunian='甲辰') # type: ignore

  transits = TransitSet(liunian=Ganzhi.from_str('甲辰'))
  with pytest.raises(ValueError):
    transits.select()
  with pytest.raises(TypeError):
    transits.select('liunian') # type: ignore
  with pytest.raises(ValueError):
    transits.select(TransitKind.LIUNIAN, TransitKind.LIUNIAN)
  with pytest.raises(ValueError):
    transits.select(TransitKind.LIUNIAN, TransitKind.DAYUN)


def test_transit_database() -> None:
  for _ in range(4):
    chart = BaziChart.random()
    db = TransitDatabase(chart)

    with pytest.raises(TypeError):
      db.xiaoyun('2000') # type: ignore
    with pytest.raises(TypeError):
      db.dayun('2000') # type: ignore

    expected_xiaoyun = {
      chart.bazi.ganzhi_year + age - 1: ganzhi
      for age, ganzhi in chart.xiaoyun
    }
    for gz_year, ganzhi in expected_xiaoyun.items():
      assert db.xiaoyun(gz_year) == ganzhi
    assert db.xiaoyun(min(expected_xiaoyun) - 1) is None
    assert db.xiaoyun(max(expected_xiaoyun) + 1) is None

    first_dayun_year = _dayun_start_gz_year(chart)
    assert db.dayun(first_dayun_year - 1) is None
    for expected in itertools.islice(chart.dayun, 20):
      for gz_year in range(expected.ganzhi_year, expected.ganzhi_year + 10):
        assert db.dayun(gz_year) == expected.ganzhi


def test_birth_year_is_precision_attributed() -> None:
  chart = BaziChart(Bazi.create('2009-02-03 23:30', 'female', BaziConfig.from_values(precision='hour')))
  assert chart.bazi.ganzhi_year == 2009
  db = TransitDatabase(chart)

  assert db.xiaoyun(2008) is None
  assert db.xiaoyun(2009) == chart.xiaoyun[0].ganzhi
  assert db.xiaoyun(2018) == chart.xiaoyun[-1].ganzhi
  assert db.xiaoyun(2019) is None


def test_day_precision_unchanged() -> None:
  chart = BaziChart(Bazi.create('2009-02-03 23:30', 'female'))
  assert chart.bazi.ganzhi_year == chart.bazi.ganzhi_date.year
  db = TransitDatabase(chart)
  assert db.xiaoyun(2008) == chart.xiaoyun[0].ganzhi
  assert db.xiaoyun(2007) is None


def test_dayun_year_floored_at_ganzhi_year() -> None:
  chart = BaziChart(Bazi.create('2009-02-03 23:30', 'male', BaziConfig.from_values(precision='hour')))
  assert chart.dayun_start_moment == chart.bazi.solar_datetime
  assert chart.bazi.ganzhi_date.year == 2008
  assert chart.bazi.ganzhi_year == 2009

  first_dayun = next(chart.dayun)
  assert first_dayun == DayunTuple(2009, Ganzhi.from_str('乙丑'))

  db = TransitDatabase(chart)
  assert db.dayun(2008) is None
  assert db.dayun(2009) == Ganzhi.from_str('乙丑')
  assert db.xiaoyun(2009) == Ganzhi.from_str('乙亥')
  assert db.dayun(2018) == Ganzhi.from_str('乙丑')
  assert db.dayun(2019) == Ganzhi.from_str('甲子')
