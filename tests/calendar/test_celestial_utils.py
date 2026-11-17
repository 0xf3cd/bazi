# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date, datetime, timedelta

import pytest

from bazi.calendar import utils
from bazi.calendar.dates import CalendarType, CalendarDate
from bazi.defines import Jieqi


def solar(year: int, month: int, day: int) -> CalendarDate:
  return CalendarDate(year, month, day, CalendarType.SOLAR)


def lunar(year: int, month: int, day: int) -> CalendarDate:
  return CalendarDate(year, month, day, CalendarType.LUNAR)


def ganzhi(year: int, month: int, day: int) -> CalendarDate:
  return CalendarDate(year, month, day, CalendarType.GANZHI)


def test_derived_bounds() -> None:
  assert utils.get_min_supported_date(CalendarType.SOLAR) == solar(1901, 2, 19)
  assert utils.get_max_supported_date(CalendarType.SOLAR) == solar(2099, 12, 31)
  assert utils.get_min_supported_date(CalendarType.LUNAR) == lunar(1901, 1, 1)
  assert utils.get_max_supported_date(CalendarType.LUNAR) == lunar(2099, 12, 20)
  assert utils.get_min_supported_date(CalendarType.GANZHI) == ganzhi(1901, 1, 16)
  assert utils.get_max_supported_date(CalendarType.GANZHI) == ganzhi(2099, 11, 25)


def test_the_three_bounds_are_one_physical_day() -> None:
  for bound in (utils.get_min_supported_date, utils.get_max_supported_date):
    day = utils.to_date(bound(CalendarType.SOLAR))
    assert utils.to_date(bound(CalendarType.LUNAR)) == day
    assert utils.to_date(bound(CalendarType.GANZHI)) == day


@pytest.mark.input_contract('bazi.calendar.utils', 'get_min_supported_date get_max_supported_date')
def test_bounds_reject_wrong_type() -> None:
  for bound in (utils.get_min_supported_date, utils.get_max_supported_date):
    with pytest.raises(TypeError):
      bound(42) # type: ignore[arg-type] # Deliberately invalid input.


@pytest.mark.input_contract('bazi.calendar.utils', 'to_solar to_lunar to_ganzhi to_date')
@pytest.mark.parametrize('invalid', [
  solar(1901, 2, 18), solar(2100, 1, 1), solar(2023, 2, 29), solar(2024, 13, 1),
  solar(2024, 0, 1), solar(2024, 1, 0),
  lunar(1900, 12, 1), lunar(2099, 12, 21), lunar(2024, 13, 1), lunar(2024, 0, 1),
  lunar(2024, 1, 0), lunar(2024, 1, 31), lunar(2023, 3, 30),
  ganzhi(1901, 1, 15), ganzhi(2099, 11, 26), ganzhi(2024, 13, 1), ganzhi(2024, 0, 1),
  ganzhi(2024, 1, 0), ganzhi(2024, 1, 33),
])
def test_invalid_dates_are_rejected(invalid: CalendarDate) -> None:
  for convert in (utils.to_solar, utils.to_lunar, utils.to_ganzhi, utils.to_date):
    with pytest.raises(ValueError, match=f'is not a valid {invalid.date_type.name} date in the supported range'):
      convert(invalid)


def test_valid_leap_days() -> None:
  assert utils.to_date(solar(2024, 2, 29)) == date(2024, 2, 29)
  assert utils.to_lunar(lunar(2023, 13, 1)) == lunar(2023, 13, 1)
  assert utils.to_date(lunar(2023, 3, 29)) == date(2023, 4, 19)


def test_ganzhi_month_lengths() -> None:
  for year in (2024, 2100):
    counts = utils._days_counts_in_ganzhi_year(year)
    assert isinstance(counts, tuple)
    assert len(counts) == 12
    span = (utils.jieqi_moment(year + 1, Jieqi.立春).date()
            - utils.jieqi_moment(year, Jieqi.立春).date()).days
    assert sum(counts) == span


def test_month_lengths_require_next_lichun() -> None:
  for year in (1900, 2200):
    with pytest.raises(ValueError):
      utils._days_counts_in_ganzhi_year(year)


def test_round_trips() -> None:
  # Every day of a leap lunar year and of a plain one, both ways round.
  for year in (2023, 2024):
    day = date(year, 1, 1)
    while day.year == year:
      d = solar(day.year, day.month, day.day)
      assert utils.to_solar(utils.to_lunar(d)) == d
      assert utils.to_solar(utils.to_ganzhi(d)) == d
      assert utils.to_lunar(utils.to_ganzhi(d)) == utils.to_lunar(d)
      assert utils.to_ganzhi(utils.to_lunar(d)) == utils.to_ganzhi(d)
      day += timedelta(days=1)


def test_lunar_leap_month_round_trips() -> None:
  # 2023's 闰二月 occupies slot 3, shifting later months; slot 13 is 腊月.
  for d, expected in ((1, solar(2023, 3, 22)), (15, solar(2023, 4, 5)), (29, solar(2023, 4, 19))):
    leap = lunar(2023, 3, d)
    assert utils.to_solar(leap) == expected
    assert utils.to_lunar(utils.to_solar(leap)) == leap


def test_dates_before_the_year_boundaries() -> None:
  assert utils.to_ganzhi(solar(2024, 1, 1)).year == 2023
  assert utils.to_lunar(solar(2024, 1, 1)).year == 2023
  assert utils.to_ganzhi(solar(2024, 2, 5)).year == 2024


def test_to_family() -> None:
  day = date(2024, 2, 4)
  for d in (day, solar(2024, 2, 4), lunar(2023, 13, 25), ganzhi(2024, 1, 1)):
    assert utils.to_solar(d) == solar(2024, 2, 4)
    assert utils.to_lunar(d) == lunar(2023, 13, 25)
    assert utils.to_ganzhi(d) == ganzhi(2024, 1, 1)
    assert utils.to_date(d) == day


@pytest.mark.input_contract('bazi.calendar.utils', 'to_solar to_lunar to_ganzhi to_date')
def test_to_family_negative() -> None:
  for convert in (utils.to_solar, utils.to_lunar, utils.to_ganzhi, utils.to_date):
    with pytest.raises(ValueError):
      convert(date(1901, 1, 1))
    with pytest.raises(ValueError):
      convert(lunar(9999, 1, 1))
    with pytest.raises(TypeError):
      convert('2024-01-01') # type: ignore[arg-type] # Not a date or CalendarDate.


def test_real_moments_not_placeholders() -> None:
  assert utils.jieqi_moment(2024, Jieqi.立春) == datetime(2024, 2, 4, 16, 27, 6)
  assert utils.jieqi_moment(2000, Jieqi.立春) == datetime(2000, 2, 4, 20, 40, 23)


@pytest.mark.input_contract('bazi.calendar.utils', 'jieqi_moment')
def test_jieqi_queries_validate_before_lookup() -> None:
  class Year(int):
    pass

  result = utils.jieqi_moment(2024, Jieqi.立春)
  assert result is utils.jieqi_moment(Year(2024), Jieqi.LICHUN)
  bad: object
  for bad in (2024.0, '2024', []):
    with pytest.raises(TypeError, match='Expected int'):
      utils.jieqi_moment(bad, Jieqi.立春) # type: ignore[arg-type]
  for bad in ('立春', 0, None, []):
    with pytest.raises(TypeError, match='Expected Jieqi'):
      utils.jieqi_moment(2024, bad) # type: ignore[arg-type]
  for supported_year in (1901, 2200):
    assert utils.jieqi_moment(Year(supported_year), Jieqi.小寒) == utils.jieqi_moment(supported_year, Jieqi.小寒)
  for bad_value in (1900, 2201, True, False):
    with pytest.raises(ValueError, match='out of the supported range'):
      utils.jieqi_moment(bad_value, Jieqi.立春)


def test_supported_jie_boundaries() -> None:
  first, last = utils.supported_jie_boundaries()
  assert first == utils.jieqi_moment(1901, Jieqi.小寒)
  assert last == utils.jieqi_moment(2200, Jieqi.大雪)


@pytest.mark.input_contract('bazi.calendar.utils', 'prev_jie next_jie')
def test_jie_range_is_enforced() -> None:
  first, last = utils.supported_jie_boundaries()
  for fn in (utils.prev_jie, utils.next_jie):
    with pytest.raises(ValueError, match='first available Jie'):
      fn(first - timedelta(seconds=1))
    with pytest.raises(ValueError, match='last available Jie'):
      fn(last)
    with pytest.raises(TypeError):
      fn(date(2024, 2, 4)) # type: ignore[arg-type] # A date is not a datetime.


def test_short_window_ignores_warm_cache(request: pytest.FixtureRequest) -> None:
  outside = utils.jieqi_moment(2150, Jieqi.立春)
  for query in (utils.prev_jie, utils.next_jie):
    query(outside)
  request.getfixturevalue('short_jie_window')
  for query in (utils.prev_jie, utils.next_jie):
    with pytest.raises(ValueError, match='last available Jie'):
      query(outside)


def test_exactly_on_a_jie_belongs_to_it() -> None:
  moment = utils.jieqi_moment(2024, Jieqi.立春)
  assert utils.prev_jie(moment) == (Jieqi.立春, moment)
  assert utils.next_jie(moment) == (Jieqi.惊蛰, utils.jieqi_moment(2024, Jieqi.惊蛰))
  assert utils.prev_jie(moment - timedelta(seconds=1)).jieqi == Jieqi.小寒
  assert utils.next_jie(moment - timedelta(seconds=1)) == (Jieqi.立春, moment)
  assert utils.prev_jie(moment + timedelta(seconds=1)) == (Jieqi.立春, moment)
  assert utils.next_jie(moment + timedelta(seconds=1)).jieqi == Jieqi.惊蛰


def test_jie_across_year_boundaries() -> None:
  assert utils.prev_jie(datetime(2024, 1, 1)) == (Jieqi.大雪, utils.jieqi_moment(2023, Jieqi.大雪))
  assert utils.next_jie(datetime(2024, 12, 20)) == (Jieqi.小寒, utils.jieqi_moment(2025, Jieqi.小寒))


def test_prev_and_next_bracket_every_jie() -> None:
  first, last = utils.supported_jie_boundaries()
  moment = first
  seen = 0
  while moment < last:
    assert utils.prev_jie(moment).moment == moment
    nxt = utils.next_jie(moment)
    assert nxt.moment > moment
    assert utils.prev_jie(nxt.moment - timedelta(seconds=1)).moment == moment
    moment = nxt.moment
    seen += 1
  assert seen == len(range(1901, 2201)) * 12 - 1
