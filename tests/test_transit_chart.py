# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transit_chart.py

from datetime import date, datetime

import pytest

from src.bazi import Bazi
from src.bazi_chart import BaziChart
from src.defines import Ganzhi, Dizhi
from src.school import BaziConfig
from src.transit_chart import TransitChart, 流年大运
from src.transits import TransitDate, TransitKind, TransitMonth, TransitSet, TransitYear
from src.utils.bazi_utils import ganzhi_of_day


def test_basic() -> None:
  assert TransitChart is 流年大运

  bazi_chart = BaziChart.random()
  transits = TransitChart(bazi_chart)
  assert bazi_chart.json == transits.bazi_chart.json


def test_basic_negative() -> None:
  with pytest.raises(TypeError):
    TransitChart(BaziChart.random().bazi) # type: ignore
  with pytest.raises(TypeError):
    TransitChart(datetime(2024, 1, 1)) # type: ignore
  with pytest.raises(AttributeError):
    TransitChart(BaziChart.random()).bazi_chart = BaziChart.random() # type: ignore


def test_support_boundaries() -> None:
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))

  assert not chart.support(TransitYear(1983))
  assert chart.support(TransitYear(1984))

  assert not chart.support(TransitMonth(1984, Dizhi.寅))
  assert chart.support(TransitMonth(1984, Dizhi.卯))
  assert chart.support(TransitMonth(1985, Dizhi.寅))

  assert not chart.support(TransitDate(date(1984, 3, 31)))
  assert chart.support(TransitDate(date(1984, 4, 1)))
  # The lower date is also pre-birth; the upper date is one day past the solar range.
  assert not chart.support(TransitDate(date(1901, 2, 18)))
  assert not chart.support(TransitDate(date(2100, 1, 1)))


def test_support_uses_precision_attributed_birth_boundary() -> None:
  config = BaziConfig.from_values(precision='hour')
  chart = TransitChart(BaziChart(Bazi.create('2009-02-03 23:30', 'female', config)))
  assert chart.bazi_chart.bazi.ganzhi_date.year == 2008
  assert chart.bazi_chart.bazi.ganzhi_year == 2009

  assert not chart.support(TransitYear(2008))
  assert chart.support(TransitYear(2009))
  assert not chart.support(TransitMonth(2008, Dizhi.丑))
  assert chart.support(TransitMonth(2009, Dizhi.寅))


def test_support_negative() -> None:
  chart = TransitChart(BaziChart.random())
  with pytest.raises(TypeError):
    chart.support(2024) # type: ignore
  with pytest.raises(TypeError):
    chart.at(date(2024, 1, 1)) # type: ignore

  unsupported = TransitYear(chart.bazi_chart.bazi.ganzhi_year - 1)
  with pytest.raises(ValueError):
    chart.at(unsupported)


def test_year_transits() -> None:
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))

  birth_year = chart.at(TransitYear(1984))
  assert birth_year == TransitSet(
    xiaoyun=Ganzhi.from_str('癸未'),
    liunian=Ganzhi.from_str('甲子'),
  )

  first_dayun_year = chart.at(TransitYear(1985))
  assert first_dayun_year == TransitSet(
    xiaoyun=Ganzhi.from_str('甲申'),
    dayun=Ganzhi.from_str('戊辰'),
    liunian=Ganzhi.from_str('乙丑'),
  )

  later = chart.at(TransitYear(2024))
  assert TransitKind.XIAOYUN not in later
  assert later.dayun == Ganzhi.from_str('辛未')
  assert later.liunian == Ganzhi.from_str('甲辰')


def test_month_transits() -> None:
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))
  assert chart.at(TransitMonth(1984, Dizhi.卯)) == TransitSet(
    xiaoyun=Ganzhi.from_str('癸未'),
    liunian=Ganzhi.from_str('甲子'),
    liuyue=Ganzhi.from_str('丁卯'),
  )

  transits = chart.at(TransitMonth(2024, Dizhi.寅))
  assert transits == TransitSet(
    dayun=Ganzhi.from_str('辛未'),
    liunian=Ganzhi.from_str('甲辰'),
    liuyue=Ganzhi.from_str('丙寅'),
  )
  assert tuple(transits) == (TransitKind.DAYUN, TransitKind.LIUNIAN, TransitKind.LIUYUE)


@pytest.mark.parametrize('backend', ['hko', 'celestial', 'celestial-algo2'])
def test_date_transits(backend: str) -> None:
  config = BaziConfig.from_values(backend=backend)
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male', config)))
  solar_date = date(2024, 2, 4)
  transits = chart.at(TransitDate(solar_date))

  assert transits == TransitSet(
    dayun=Ganzhi.from_str('辛未'),
    liunian=Ganzhi.from_str('甲辰'),
    liuyue=Ganzhi.from_str('丙寅'),
    liuri=ganzhi_of_day(solar_date),
  )
  assert tuple(transits) == (
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
    TransitKind.LIUYUE,
    TransitKind.LIURI,
  )
  assert transits.json['liuri'] == str(ganzhi_of_day(solar_date))


def test_date_uses_day_level_calendar_coordinates() -> None:
  config = BaziConfig.from_values(precision='hour', backend='celestial')
  chart = TransitChart(BaziChart(Bazi.create('2009-02-03 23:30', 'female', config)))

  # The date query has no time-of-day. On the birth date it therefore uses the old,
  # day-level Ganzhi year/month even though the HOUR natal chart has crossed 立春.
  transits = chart.at(TransitDate(date(2009, 2, 3)))
  assert transits.liunian == Ganzhi.from_str('戊子')
  assert transits.liuyue == Ganzhi.from_str('乙丑')
  assert transits.liuri == ganzhi_of_day(date(2009, 2, 3))
