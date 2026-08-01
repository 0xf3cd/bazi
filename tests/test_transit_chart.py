# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transit_chart.py

import pytest

from datetime import datetime

from src.bazi import Bazi, BaziGender, BaziPrecision
from src.bazi_chart import BaziChart
from src.defines import Dizhi
from src.transits import TransitMoment, TransitOptions, TransitDatabase
from src.transit_chart import TransitChart, 流年大运


def test_basic() -> None:
  assert TransitChart is 流年大运

  for _ in range(4):
    bazi_chart: BaziChart = BaziChart.random()
    transits: TransitChart = TransitChart(bazi_chart)
    assert bazi_chart.json == transits.bazi_chart.json


def test_basic_negative() -> None:
  with pytest.raises(AssertionError):
    TransitChart(BaziChart.random().bazi) # type: ignore
  with pytest.raises(AssertionError):
    TransitChart(datetime(2024, 1, 1)) # type: ignore

  with pytest.raises(AttributeError):
    TransitChart(BaziChart.random()).bazi_chart = BaziChart.random() # type: ignore


def test_delegation() -> None:
  bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
  transits: TransitChart = TransitChart(BaziChart(bazi))
  db: TransitDatabase = TransitDatabase(transits.bazi_chart)

  first_dayun_gz_year: int = next(transits.bazi_chart.dayun).ganzhi_year

  for gz_year in (first_dayun_gz_year, first_dayun_gz_year + 7, first_dayun_gz_year + 25):
    for option in TransitOptions:
      assert transits.support(TransitMoment(gz_year), option) == db.support(TransitMoment(gz_year), option)
      if transits.support(TransitMoment(gz_year), option):
        assert transits.ganzhis(TransitMoment(gz_year), option) == db.ganzhis(TransitMoment(gz_year), option)


def test_delegation_negative() -> None:
  bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
  transits: TransitChart = TransitChart(BaziChart(bazi))

  with pytest.raises(AssertionError):
    transits.support('1999', TransitOptions.XIAOYUN) # type: ignore
  with pytest.raises(AssertionError):
    transits.support(1999, TransitOptions.XIAOYUN) # type: ignore # int no longer accepted; `TransitMoment` required.
  with pytest.raises(AssertionError):
    transits.ganzhis(TransitMoment(1999), 'XIAOYUN') # type: ignore
  # Month/day-granularity moments are rejected until #48 / #48 落地前，月/日粒度的 moment 显式拒绝。
  with pytest.raises(NotImplementedError):
    transits.support(TransitMoment(2000, gz_month=Dizhi.寅), TransitOptions.LIUNIAN)

  first_dayun_gz_year: int = next(transits.bazi_chart.dayun).ganzhi_year
  assert not transits.support(TransitMoment(first_dayun_gz_year - 1), TransitOptions.DAYUN)
  with pytest.raises(ValueError):
    transits.ganzhis(TransitMoment(first_dayun_gz_year - 1), TransitOptions.DAYUN)
