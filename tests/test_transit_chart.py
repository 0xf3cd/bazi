# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transit_chart.py

from datetime import date, datetime

import pytest

from src.bazi import Bazi
from src.bazi_chart import BaziChart
from src.defines import Ganzhi, Dizhi
from src.school import BaziConfig
from src.transit_chart import TransitChart, 流年大运
from src.transits import TransitKind, TransitSet
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


def test_query_boundaries() -> None:
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))

  assert chart.at_year(1983) is None
  assert chart.at_year(1984) is not None

  assert chart.at_month(1984, Dizhi.寅) is None
  assert chart.at_month(1984, Dizhi.卯) is not None
  assert chart.at_month(1985, Dizhi.寅) is not None

  assert chart.at_date(date(1984, 3, 31)) is None
  assert chart.at_date(date(1984, 4, 1)) is not None
  # The lower date is also pre-birth; the upper date is one day past the solar range.
  assert chart.at_date(date(1901, 2, 18)) is None
  assert chart.at_date(date(2100, 1, 1)) is None


def test_queries_use_precision_attributed_birth_boundary() -> None:
  config = BaziConfig.from_values(precision='hour')
  chart = TransitChart(BaziChart(Bazi.create('2009-02-03 23:30', 'female', config)))
  assert chart.bazi_chart.bazi.ganzhi_date.year == 2008
  assert chart.bazi_chart.bazi.ganzhi_year == 2009

  assert chart.at_year(2008) is None
  assert chart.at_year(2009) is not None
  assert chart.at_month(2008, Dizhi.丑) is None
  assert chart.at_month(2009, Dizhi.寅) is not None


def test_query_types() -> None:
  chart = TransitChart(BaziChart.random())
  with pytest.raises(TypeError):
    chart.at_year('2024') # type: ignore
  with pytest.raises(TypeError):
    chart.at_month('2024', Dizhi.寅) # type: ignore
  with pytest.raises(TypeError):
    chart.at_month(2024, '寅') # type: ignore
  with pytest.raises(TypeError):
    chart.at_date('2024-01-01') # type: ignore
  with pytest.raises(TypeError):
    chart.at_date(datetime(2024, 1, 1))


def test_year_transits() -> None:
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))

  birth_year = chart.at_year(1984)
  assert birth_year == TransitSet(
    xiaoyun=Ganzhi.from_str('癸未'),
    liunian=Ganzhi.from_str('甲子'),
  )

  first_dayun_year = chart.at_year(1985)
  assert first_dayun_year == TransitSet(
    xiaoyun=Ganzhi.from_str('甲申'),
    dayun=Ganzhi.from_str('戊辰'),
    liunian=Ganzhi.from_str('乙丑'),
  )

  later = chart.at_year(2024)
  assert later is not None
  assert TransitKind.XIAOYUN not in later
  assert later.dayun == Ganzhi.from_str('辛未')
  assert later.liunian == Ganzhi.from_str('甲辰')


def test_month_transits() -> None:
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))
  assert chart.at_month(1984, Dizhi.卯) == TransitSet(
    xiaoyun=Ganzhi.from_str('癸未'),
    liunian=Ganzhi.from_str('甲子'),
    liuyue=Ganzhi.from_str('丁卯'),
  )

  transits = chart.at_month(2024, Dizhi.寅)
  assert transits is not None
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
  transits = chart.at_date(solar_date)
  assert transits is not None

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
  transits = chart.at_date(date(2009, 2, 3))
  assert transits is not None
  assert transits.liunian == Ganzhi.from_str('戊子')
  assert transits.liuyue == Ganzhi.from_str('乙丑')
  assert transits.liuri == ganzhi_of_day(date(2009, 2, 3))


def test_date_dayun_follows_the_configured_year_labels() -> None:
  projected = TransitChart(BaziChart(Bazi.create('1910-04-07 06:01', 'male')))
  fixed = TransitChart(BaziChart(Bazi.create(
    '1910-04-07 06:01',
    'male',
    BaziConfig.from_values(dayun_year_rule='fixed_decade'),
  )))

  projected_transits = projected.at_date(date(1929, 6, 1))
  fixed_transits = fixed.at_date(date(1929, 6, 1))
  assert projected_transits is not None
  assert fixed_transits is not None
  assert projected_transits.dayun == Ganzhi.from_str('辛巳')
  assert fixed_transits.dayun == Ganzhi.from_str('壬午')
