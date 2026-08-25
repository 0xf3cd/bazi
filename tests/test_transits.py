# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transits.py

import itertools
import random
from datetime import datetime

import pytest

from src.data_types import DayunTuple
from src.defines import Ganzhi

from src.bazi import Bazi
from src.bazi_chart import BaziChart
from src.school import BaziConfig
from src.transits import (
  DayunDatabase,
  TransitDatabase,
  TransitKind,
  TransitSet,
)


def test_simple() -> None:
  chart = BaziChart(Bazi.create('2000-02-04 22:01', 'male'))
  db = DayunDatabase(chart)

  dayuns = list(itertools.islice(chart.dayun, 3))
  assert [str(dayun.ganzhi) for dayun in dayuns] == ['己卯', '庚辰', '辛巳']
  for current, following in itertools.pairwise(dayuns):
    for year in range(current.ganzhi_year, following.ganzhi_year):
      assert db[year] == current


def test_dayun_database() -> None:
  chart = BaziChart.random()
  expected: dict[int, DayunTuple] = {}
  dayuns = tuple(chart.dayun)
  for current, following in itertools.pairwise(dayuns):
    for year in range(current.ganzhi_year, following.ganzhi_year):
      expected[year] = current
  for year in range(dayuns[-1].ganzhi_year, dayuns[-1].ganzhi_year + 10):
    expected[year] = dayuns[-1]

  db = DayunDatabase(chart)
  with pytest.raises(TypeError):
    db['2000'] # type: ignore
  with pytest.raises(ValueError):
    db[dayuns[0].ganzhi_year - 1]
  with pytest.raises(ValueError):
    db[dayuns[-1].ganzhi_year + 10]

  years = list(expected.keys())
  for year in random.sample(years, 100):
    assert db[year] == expected[year]


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

    dayuns = tuple(chart.dayun)
    assert db.dayun(dayuns[0].ganzhi_year - 1) is None
    for current, following in itertools.pairwise(dayuns):
      for gz_year in range(current.ganzhi_year, following.ganzhi_year):
        assert db.dayun(gz_year) == current.ganzhi
    for gz_year in range(dayuns[-1].ganzhi_year, dayuns[-1].ganzhi_year + 10):
      assert db.dayun(gz_year) == dayuns[-1].ganzhi
    assert db.dayun(dayuns[-1].ganzhi_year + 10) is None


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

  first_dayun, second_dayun = itertools.islice(chart.dayun, 2)
  assert first_dayun == DayunTuple(
    2009,
    Ganzhi.from_str('乙丑'),
    datetime(2009, 2, 3, 23, 30),
    datetime(2019, 2, 3, 23, 30),
  )
  assert second_dayun == DayunTuple(
    2018,
    Ganzhi.from_str('甲子'),
    datetime(2019, 2, 3, 23, 30),
    datetime(2029, 2, 3, 23, 30),
  )

  db = TransitDatabase(chart)
  assert db.dayun(2008) is None
  assert db.dayun(2009) == Ganzhi.from_str('乙丑')
  assert db.xiaoyun(2009) == Ganzhi.from_str('乙亥')
  # The first-label floor does not propagate: the second Dayun boundary belongs to 2018.
  assert db.dayun(2018) == Ganzhi.from_str('甲子')
  assert db.dayun(2019) == Ganzhi.from_str('甲子')


def test_fixed_dayun_years_continue_from_the_first_label() -> None:
  fixed_chart = BaziChart(Bazi.create(
    '2009-02-03 23:30',
    'male',
    BaziConfig.from_values(precision='hour', dayun_year_rule='fixed_decade'),
  ))
  assert [dayun.ganzhi_year for dayun in itertools.islice(fixed_chart.dayun, 3)] == [2009, 2019, 2029]
  fixed_db = TransitDatabase(fixed_chart)
  assert fixed_db.dayun(2018) == Ganzhi.from_str('乙丑')
  assert fixed_db.dayun(2019) == Ganzhi.from_str('甲子')


def test_dayun_database_uses_projected_year_boundaries() -> None:
  chart = BaziChart(Bazi.create('1910-04-07 06:01', 'male'))
  db = DayunDatabase(chart)
  first, second, third = itertools.islice(chart.dayun, 3)

  assert (first.ganzhi_year, second.ganzhi_year, third.ganzhi_year) == (1919, 1930, 1939)
  assert db[1928] == first
  assert db[1929] == first
  assert db[1930] == second


def test_dayun_database_tail_uses_label_years() -> None:
  chart = BaziChart(Bazi.create('2045-10-07 05:29', 'female'))
  db = DayunDatabase(chart)
  last = tuple(chart.dayun)[-1]

  assert last.ganzhi_year == 2195
  assert last.start_moment.year == 2196
  assert last.end_moment.year == 2206
  assert db[2204] == last
  with pytest.raises(ValueError):
    db[2205]

  transit_db = TransitDatabase(chart)
  assert transit_db.dayun(2204) == last.ganzhi
  assert transit_db.dayun(2205) is None
  assert datetime(2205, 8, 1) < last.end_moment


def test_empty_dayun_database() -> None:
  chart = BaziChart(Bazi.create(
    '2099-12-20 12:00',
    'male',
    BaziConfig.from_values(backend='hko'),
  ))
  db = DayunDatabase(chart)

  with pytest.raises(ValueError, match='No Dayun starts within the supported Jie range'):
    db[2100]
