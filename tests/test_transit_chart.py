# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transit_chart.py

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.bazi import Bazi
from src.bazi_chart import BaziChart
from src.defines import Ganzhi, Dizhi
from src.calendar import calendar_utils_of
from src.school import BaziConfig, BaziSchool, DayRollover
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
  with pytest.raises(TypeError):
    chart.at_moment(date(2024, 1, 1)) # type: ignore
  with pytest.raises(ValueError):
    chart.at_moment(datetime(2024, 1, 1, tzinfo=ZoneInfo('Asia/Shanghai')))


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


def test_physical_dayun_boundaries_at_three_granularities() -> None:
  chart = TransitChart(BaziChart(Bazi.create(
    '1984-04-01 11:08',
    'male',
    BaziConfig.from_values(precision='minute'),
  )))
  first = Ganzhi.from_str('戊辰')
  second = Ganzhi.from_str('己巳')

  month_cases = (
    (1985, Dizhi.辰, None),
    (1985, Dizhi.巳, first),
    (1985, Dizhi.午, first),
    (1995, Dizhi.辰, first),
    (1995, Dizhi.巳, second),
    (1995, Dizhi.午, second),
  )
  for gz_year, gz_month, expected in month_cases:
    transits = chart.at_month(gz_year, gz_month)
    assert transits is not None
    assert transits.dayun == expected

  date_cases = (
    (date(1985, 5, 27), None),
    (date(1985, 5, 28), first),
    (date(1985, 5, 29), first),
    (date(1995, 5, 27), first),
    (date(1995, 5, 28), second),
    (date(1995, 5, 29), second),
  )
  for solar_date, expected in date_cases:
    transits = chart.at_date(solar_date)
    assert transits is not None
    assert transits.dayun == expected

  before_first = chart.at_moment(datetime(1985, 5, 28, 10, 33, 54))
  assert before_first is not None
  assert before_first.xiaoyun == Ganzhi.from_str('甲申')
  assert before_first.dayun is None

  moment_cases = (
    (datetime(1985, 5, 28, 10, 33, 55), first),
    (datetime(1985, 5, 28, 10, 33, 56), first),
    (datetime(1995, 5, 28, 10, 33, 54), first),
    (datetime(1995, 5, 28, 10, 33, 55), second),
    (datetime(1995, 5, 28, 10, 33, 56), second),
  )
  for solar_moment, expected in moment_cases:
    transits = chart.at_moment(solar_moment)
    assert transits is not None
    assert transits.dayun == expected


def test_dayun_moment_boundaries_truncate_to_seconds() -> None:
  chart = TransitChart(BaziChart(Bazi.create(
    '1910-04-07 06:01',
    'male',
    BaziConfig.from_values(precision='minute'),
  )))
  first = Ganzhi.from_str('辛巳')
  second = Ganzhi.from_str('壬午')

  cases = (
    (datetime(1930, 2, 4, 23, 21, 40, 999999), first),
    (datetime(1930, 2, 4, 23, 21, 41), second),
    (datetime(1930, 2, 4, 23, 21, 41, 999999), second),
  )
  for solar_moment, expected in cases:
    transits = chart.at_moment(solar_moment)
    assert transits is not None
    assert transits.dayun == expected

  birth = datetime(1910, 4, 7, 6, 1)
  assert chart.at_moment(birth - timedelta(microseconds=1)) is None
  assert chart.at_moment(birth + timedelta(microseconds=999999)) is not None


def test_month_projection_uses_the_boundary_owning_jie() -> None:
  chart = TransitChart(BaziChart(Bazi.create(
    '1977-06-12 14:10',
    'female',
    BaziConfig.from_values(precision='minute'),
  )))
  first = Ganzhi.from_str('丁未')

  before = chart.at_month(1985, Dizhi.申)
  boundary = chart.at_month(1985, Dizhi.酉)
  same_day = chart.at_moment(datetime(1985, 10, 8, 12, 0))
  assert before is not None
  assert boundary is not None
  assert same_day is not None
  assert before.dayun is None
  assert boundary.dayun == first
  assert same_day.dayun == first
  assert same_day.liuyue == Ganzhi.from_str('乙酉')


def test_month_projection_floors_the_first_dayun_at_birth() -> None:
  chart = TransitChart(BaziChart(Bazi.create(
    '2009-02-03 23:30',
    'male',
    BaziConfig.from_values(precision='hour'),
  )))

  assert chart.at_month(2008, Dizhi.丑) is None
  birth_month = chart.at_month(2009, Dizhi.寅)
  assert birth_month is not None
  assert birth_month.dayun == Ganzhi.from_str('乙丑')


def test_physical_dayun_queries_ignore_the_year_label_rule() -> None:
  projected = TransitChart(BaziChart(Bazi.create(
    '1910-04-07 06:01',
    'male',
    BaziConfig.from_values(precision='minute'),
  )))
  fixed = TransitChart(BaziChart(Bazi.create(
    '1910-04-07 06:01',
    'male',
    BaziConfig.from_values(precision='minute', dayun_year_rule='fixed_decade'),
  )))

  projected_year = projected.at_year(1929)
  fixed_year = fixed.at_year(1929)
  projected_month = projected.at_month(1929, Dizhi.巳)
  fixed_month = fixed.at_month(1929, Dizhi.巳)
  projected_transits = projected.at_date(date(1929, 6, 1))
  fixed_transits = fixed.at_date(date(1929, 6, 1))
  projected_moment = projected.at_moment(datetime(1929, 6, 1, 12, 0))
  fixed_moment = fixed.at_moment(datetime(1929, 6, 1, 12, 0))
  assert projected_year is not None
  assert fixed_year is not None
  assert projected_month is not None
  assert fixed_month is not None
  assert projected_transits is not None
  assert fixed_transits is not None
  assert projected_moment is not None
  assert fixed_moment is not None
  assert projected_year.dayun == Ganzhi.from_str('辛巳')
  assert fixed_year.dayun == Ganzhi.from_str('壬午')
  assert projected_month.dayun == Ganzhi.from_str('辛巳')
  assert fixed_month.dayun == Ganzhi.from_str('辛巳')
  assert projected_transits.dayun == Ganzhi.from_str('辛巳')
  assert fixed_transits.dayun == Ganzhi.from_str('辛巳')
  assert projected_moment.dayun == Ganzhi.from_str('辛巳')
  assert fixed_moment.dayun == Ganzhi.from_str('辛巳')


def test_leap_dayun_boundaries_are_recomputed_from_the_first() -> None:
  chart = TransitChart(BaziChart(Bazi.create('2010-04-18 07:59', 'male')))
  first = Ganzhi.from_str('辛巳')
  second = Ganzhi.from_str('壬午')
  cases = (
    (date(2016, 2, 28), None),
    (date(2016, 2, 29), first),
    (date(2016, 3, 1), first),
    (date(2026, 2, 27), first),
    (date(2026, 2, 28), second),
    (date(2026, 3, 1), second),
  )
  for solar_date, expected in cases:
    transits = chart.at_date(solar_date)
    assert transits is not None
    assert transits.dayun == expected


def test_moment_uses_jieqi_seconds() -> None:
  chart = TransitChart(BaziChart(Bazi.create(
    '1984-04-01 11:08',
    'male',
    BaziConfig.from_values(precision='minute'),
  )))

  before = chart.at_moment(datetime(1985, 6, 6, 1, 59, 55))
  boundary = chart.at_moment(datetime(1985, 6, 6, 1, 59, 56))
  day_reading = chart.at_date(date(1985, 6, 6))
  assert before is not None
  assert boundary is not None
  assert day_reading is not None
  assert before.liuyue == Ganzhi.from_str('辛巳')
  assert boundary.liuyue == Ganzhi.from_str('壬午')
  assert day_reading.liuyue == Ganzhi.from_str('壬午')


@pytest.mark.parametrize(('day_rollover', 'expected'), [
  (DayRollover.WAN_ZISHI, (
    Ganzhi.from_str('丁卯'), Ganzhi.from_str('戊辰'),
    Ganzhi.from_str('戊辰'), Ganzhi.from_str('戊辰'),
  )),
  (DayRollover.ZIZHENG, (
    Ganzhi.from_str('丁卯'), Ganzhi.from_str('丁卯'),
    Ganzhi.from_str('丁卯'), Ganzhi.from_str('戊辰'),
  )),
])
def test_moment_day_rollover(
  day_rollover: DayRollover,
  expected: tuple[Ganzhi, ...],
) -> None:
  config = BaziConfig.from_values(
    precision='minute',
    school=BaziSchool(day_rollover=day_rollover),
  )
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male', config)))
  moments = (
    datetime(1985, 5, 28, 22, 59),
    datetime(1985, 5, 28, 23, 0),
    datetime(1985, 5, 28, 23, 59),
    datetime(1985, 5, 29, 0, 0),
  )

  actual: list[Ganzhi] = []
  for moment in moments:
    transits = chart.at_moment(moment)
    assert transits is not None
    assert transits.liuri is not None
    actual.append(transits.liuri)
  assert tuple(actual) == expected


@pytest.mark.parametrize(('backend', 'precision'), [
  ('celestial', 'hour'),
  ('celestial', 'minute'),
  ('celestial-algo2', 'minute'),
])
def test_moment_supported_variants(backend: str, precision: str) -> None:
  config = BaziConfig.from_values(backend=backend, precision=precision)
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male', config)))
  assert chart.at_moment(datetime(2024, 6, 1, 12, 0)) is not None


def test_moment_requires_a_precise_chart() -> None:
  day_chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))
  hko_chart = TransitChart(BaziChart(Bazi.create(
    '1984-04-01 11:08',
    'male',
    BaziConfig.from_values(backend='hko'),
  )))

  assert day_chart.at_moment(datetime(2024, 6, 1, 12, 0)) is None
  assert hko_chart.at_moment(datetime(2024, 6, 1, 12, 0)) is None


@pytest.mark.parametrize(('day_rollover', 'expected_liuri'), [
  (DayRollover.WAN_ZISHI, Ganzhi.from_str('庚辰')),
  (DayRollover.ZIZHENG, Ganzhi.from_str('己卯')),
])
def test_moment_at_cross_midnight_clamped_birth(
  day_rollover: DayRollover,
  expected_liuri: Ganzhi,
) -> None:
  config = BaziConfig.from_values(
    precision='hour',
    school=BaziSchool(day_rollover=day_rollover),
  )
  chart = TransitChart(BaziChart(Bazi.create('2009-02-03 23:30', 'male', config)))
  transits = chart.at_moment(datetime(2009, 2, 3, 23, 30))
  assert transits is not None
  assert transits == TransitSet(
    dayun=Ganzhi.from_str('乙丑'),
    liunian=Ganzhi.from_str('戊子'),
    liuyue=Ganzhi.from_str('乙丑'),
    liuri=expected_liuri,
  )


def test_physical_and_year_label_tail_views_diverge() -> None:
  chart = TransitChart(BaziChart(Bazi.create('2045-10-07 05:29', 'female')))
  year_transits = chart.at_year(2195)
  month_transits = chart.at_month(2195, Dizhi.亥)
  assert year_transits is not None
  assert month_transits is not None
  assert year_transits.dayun == Ganzhi.from_str('辛丑')
  assert month_transits.dayun == Ganzhi.from_str('庚子')

  late = TransitChart(BaziChart(Bazi.create(
    '2099-12-10 10:00',
    'male',
    BaziConfig.from_values(precision='minute'),
  )))
  late_year = late.at_year(2200)
  late_month = late.at_month(2200, Dizhi.亥)
  late_moment = late.at_moment(datetime(2200, 6, 1))
  assert late_year is not None
  assert late_month is not None
  assert late_moment is not None
  assert late_year.dayun is None
  assert late_month.dayun == Ganzhi.from_str('丙寅')
  assert late_moment.dayun == Ganzhi.from_str('丙寅')


def test_calendar_query_windows() -> None:
  chart = TransitChart(BaziChart(Bazi.create('1984-04-01 11:08', 'male')))
  precise = TransitChart(BaziChart(Bazi.create(
    '1984-04-01 11:08',
    'male',
    BaziConfig.from_values(precision='minute'),
  )))
  hko = TransitChart(BaziChart(Bazi.create(
    '1984-04-01 11:08',
    'male',
    BaziConfig.from_values(backend='hko'),
  )))

  assert chart.at_date(date(2099, 12, 31)) is not None
  assert chart.at_date(date(2100, 1, 1)) is None
  _, last = calendar_utils_of('celestial').supported_jie_boundaries()
  assert precise.at_moment(last - timedelta(seconds=1)) is not None
  assert precise.at_moment(last) is None
  assert chart.at_month(2200, Dizhi.亥) is not None
  assert chart.at_month(2200, Dizhi.子) is None
  assert hko.at_month(2100, Dizhi.亥) is not None
  assert hko.at_month(2100, Dizhi.子) is None


def test_empty_dayun_timeline_keeps_calendar_transits() -> None:
  chart = TransitChart(BaziChart(Bazi.create(
    '2099-12-20 12:00',
    'male',
    BaziConfig.from_values(backend='hko'),
  )))
  bazi = chart.bazi_chart.bazi
  year_transits = chart.at_year(bazi.ganzhi_year)
  month_transits = chart.at_month(bazi.ganzhi_year, bazi.month_commander)
  date_transits = chart.at_date(bazi.solar_date)
  assert year_transits is not None
  assert month_transits is not None
  assert date_transits is not None

  for transits in (year_transits, month_transits, date_transits):
    assert TransitKind.XIAOYUN not in transits
    assert TransitKind.DAYUN not in transits
    assert TransitKind.LIUNIAN in transits
  assert TransitKind.LIUYUE in month_transits
  assert TransitKind.LIUYUE in date_transits
  assert TransitKind.LIURI in date_transits
  assert chart.at_moment(bazi.solar_datetime) is None
