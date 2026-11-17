# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_celestial_parity_derived.py

'''
Compare runtime conversions with dates derived directly from the HKO decoder.

Lunar dates must agree throughout the supported range. The seven frozen 节气 date
differences include two 节; moving those month starts explains exactly 61 days of
干支 date differences. No HKO runtime conversion implementation is used here.

This checks equivalence with the HKO almanac, not independent astronomical truth:
the runtime lunar table and the decoded HKO data share the same source.
'''

from datetime import date, datetime, time, timedelta
from itertools import pairwise
from typing import Final

import pytest

from bazi.calendar import utils
from bazi.calendar.dates import CalendarType, CalendarDate
from bazi.defines import Jieqi

from hko_data import DecodedJieqiDates, DecodedLunarYears
from celestial_parity_data import JIEQI_DATE_DIVERGENCES, JieqiDateDivergence


JIES: Final[tuple[Jieqi, ...]] = tuple(Jieqi.as_list()[::2])
HKO_JIEQI: Final[DecodedJieqiDates] = DecodedJieqiDates()
HKO_LUNAR: Final[DecodedLunarYears] = DecodedLunarYears()
FIRST_DAY: Final[date] = HKO_LUNAR.get(HKO_LUNAR.start_year).first_solar_day
LAST_DAY: Final[date] = date(HKO_LUNAR.end_year, 12, 31)


def solar(day: date) -> CalendarDate:
  return CalendarDate(day.year, day.month, day.day, CalendarType.SOLAR)


def jieqi_of(row: JieqiDateDivergence) -> Jieqi:
  return Jieqi.as_list()[row.jq_idx]


def flipped_jies() -> tuple[JieqiDateDivergence, ...]:
  return tuple(row for row in JIEQI_DATE_DIVERGENCES if row.is_jie)


def hko_month_starts(year: int) -> tuple[date, ...]:
  # 小寒 belongs to the following Gregorian year; the final 立春 closes month 12.
  return tuple(
    HKO_JIEQI.get(year + (jieqi is Jieqi.小寒), jieqi) for jieqi in JIES
  ) + (HKO_JIEQI.get(year + 1, Jieqi.立春),)


def celestial_month_starts(year: int) -> tuple[date, ...]:
  return tuple(
    utils.jieqi_moment(year + (jieqi is Jieqi.小寒), jieqi).date() for jieqi in JIES
  ) + (utils.jieqi_moment(year + 1, Jieqi.立春).date(),)


@pytest.fixture(scope='module')
def hko_lunar_dates() -> dict[date, CalendarDate]:
  # Expand each decoded month by counting forward from the recorded lunar new year.
  dates: dict[date, CalendarDate] = {}
  for year in HKO_LUNAR.supported_year_range():
    info = HKO_LUNAR.get(year)
    day: date = info.first_solar_day
    for month, count in enumerate(info.days_counts, start=1):
      for index in range(1, count + 1):
        if FIRST_DAY <= day <= LAST_DAY:
          assert day not in dates
          dates[day] = CalendarDate(year, month, index, CalendarType.LUNAR)
        day += timedelta(days=1)
  assert len(dates) == (LAST_DAY - FIRST_DAY).days + 1
  return dates


def affected_solar_days() -> set[date]:
  days: set[date] = set()
  for row in flipped_jies():
    index = JIES.index(jieqi_of(row))
    next_jie = JIES[(index + 1) % len(JIES)]
    year = row.year + (next_jie is Jieqi.小寒)
    end = HKO_JIEQI.get(year, next_jie)
    assert end == utils.jieqi_moment(year, next_jie).date()
    start = min(row.celestial_moment.date(), row.hko_date)
    days.update(start + timedelta(days=i) for i in range((end - start).days))
  return days


def affected_ganzhi_months() -> set[tuple[int, int]]:
  return {
    (row.year - (jieqi_of(row) is Jieqi.小寒), JIES.index(jieqi_of(row)) + 1)
    for row in flipped_jies()
  }


def test_whitelist_is_exact_through_runtime() -> None:
  measured: set[tuple[int, int, date]] = set()
  for year in HKO_JIEQI.supported_year_range():
    for jq_idx, jq in enumerate(Jieqi):
      cel = utils.jieqi_moment(year, jq).date()
      if cel != HKO_JIEQI.get(year, jq):
        measured.add((year, jq_idx, cel))
  assert measured == {
    (row.year, row.jq_idx, row.celestial_moment.date()) for row in JIEQI_DATE_DIVERGENCES
  }


def test_moments_match_the_whitelist() -> None:
  for row in JIEQI_DATE_DIVERGENCES:
    assert utils.jieqi_moment(row.year, jieqi_of(row)) == row.celestial_moment
    assert HKO_JIEQI.get(row.year, jieqi_of(row)) == row.hko_date


def test_only_two_of_them_are_jie() -> None:
  assert [(row.year, row.name) for row in flipped_jies()] == [(1917, '大雪'), (1927, '白露')]


def test_prev_next_jie_use_the_real_moment() -> None:
  # HKO records midnight placeholders. The runtime keeps the preceding 节 until the
  # real moment, including the two cases where that moment falls on the next date.
  first, last = utils.supported_jie_boundaries()
  for year in HKO_JIEQI.supported_year_range():
    for index, jieqi in enumerate(JIES):
      moment = utils.jieqi_moment(year, jieqi)
      start = datetime.combine(min(HKO_JIEQI.get(year, jieqi), moment.date()), time.min)
      previous = JIES[(index - 1) % len(JIES)]
      following = JIES[(index + 1) % len(JIES)]
      for probe in (start - timedelta(seconds=1), start + (moment - start) / 2, moment - timedelta(seconds=1)):
        if first <= probe < last:
          assert utils.prev_jie(probe).jieqi == previous, (year, jieqi, probe)
          assert utils.next_jie(probe).jieqi == jieqi, (year, jieqi, probe)
      for probe in (moment, moment + timedelta(seconds=1)):
        if first <= probe < last:
          assert utils.prev_jie(probe).jieqi == jieqi, (year, jieqi, probe)
          assert utils.next_jie(probe).jieqi == following, (year, jieqi, probe)


def test_the_derivations_preconditions_hold() -> None:
  # A moved 立春 would transfer a day between years, not just between months.
  assert Jieqi.立春 not in {jieqi_of(row) for row in flipped_jies()}
  days = affected_solar_days()
  assert FIRST_DAY <= min(days) <= max(days) <= LAST_DAY


def test_lunar_dates_agree_throughout_range(hko_lunar_dates: dict[date, CalendarDate]) -> None:
  for day, lunar in hko_lunar_dates.items():
    assert utils.to_lunar(day) == lunar, day
    assert utils.to_lunar(solar(day)) == lunar, day
    assert utils.to_solar(lunar) == solar(day), lunar
    assert utils.to_date(lunar) == day, lunar


def test_bounds(hko_lunar_dates: dict[date, CalendarDate]) -> None:
  expected = (
    (CalendarType.SOLAR, solar(FIRST_DAY), solar(LAST_DAY)),
    (CalendarType.LUNAR, hko_lunar_dates[FIRST_DAY], hko_lunar_dates[LAST_DAY]),
    (
      CalendarType.GANZHI,
      CalendarDate(1901, 1, (FIRST_DAY - HKO_JIEQI.get(1901, Jieqi.立春)).days + 1, CalendarType.GANZHI),
      CalendarDate(2099, 11, (LAST_DAY - HKO_JIEQI.get(2099, Jieqi.大雪)).days + 1, CalendarType.GANZHI),
    ),
  )
  for date_type, first, last in expected:
    assert utils.get_min_supported_date(date_type) == first
    assert utils.get_max_supported_date(date_type) == last
    assert utils.to_date(first) == FIRST_DAY
    assert utils.to_date(last) == LAST_DAY
  for day in (FIRST_DAY - timedelta(days=1), LAST_DAY + timedelta(days=1)):
    with pytest.raises(ValueError):
      utils.to_lunar(day)
    with pytest.raises(ValueError):
      utils.to_ganzhi(day)


def test_solar_disagreements_are_exactly_derived(hko_lunar_dates: dict[date, CalendarDate]) -> None:
  expected = affected_solar_days()
  measured_ganzhi: set[date] = set()
  measured_via_lunar: set[date] = set()
  checked: int = 0
  for year in HKO_LUNAR.supported_year_range():
    for month, (start, end) in enumerate(pairwise(hko_month_starts(year)), start=1):
      for index in range((end - start).days):
        day = start + timedelta(days=index)
        if not FIRST_DAY <= day <= LAST_DAY:
          continue
        hko = CalendarDate(year, month, index + 1, CalendarType.GANZHI)
        if utils.to_ganzhi(solar(day)) != hko:
          measured_ganzhi.add(day)
        if utils.to_ganzhi(hko_lunar_dates[day]) != hko:
          measured_via_lunar.add(day)
        checked += 1

  assert checked == len(hko_lunar_dates)
  assert measured_ganzhi == expected
  assert measured_via_lunar == expected
  assert len(expected) == 61 # Two moved 节 affect 30 and 31 days.


def test_days_counts_differ_on_derived_years() -> None:
  expected = {year for year, _ in affected_ganzhi_months()}
  measured: set[int] = set()
  for year in HKO_LUNAR.supported_year_range():
    hko_counts = tuple((end - start).days for start, end in pairwise(hko_month_starts(year)))
    cel_counts = tuple((end - start).days for start, end in pairwise(celestial_month_starts(year)))
    if cel_counts != hko_counts:
      measured.add(year)
    assert sum(cel_counts) == sum(hko_counts)
  assert measured == expected


def test_ganzhi_disagreements_in_derived_months(hko_lunar_dates: dict[date, CalendarDate]) -> None:
  expected_months = affected_ganzhi_months()
  measured_months: set[tuple[int, int]] = set()
  measured_validity: set[tuple[int, int, int]] = set()
  expected_validity: set[tuple[int, int, int]] = set()

  for year in HKO_LUNAR.supported_year_range():
    hko_starts = hko_month_starts(year)
    cel_starts = celestial_month_starts(year)
    for month in range(1, 13):
      hko_count = (hko_starts[month] - hko_starts[month - 1]).days
      cel_count = (cel_starts[month] - cel_starts[month - 1]).days
      if year in {y for y, _ in expected_months}:
        lo, hi = sorted((hko_count, cel_count))
        expected_validity.update((year, month, day) for day in range(lo + 1, hi + 1))
      for day in range(1, max(hko_count, cel_count) + 1):
        d = CalendarDate(year, month, day, CalendarType.GANZHI)
        hko_day = hko_starts[month - 1] + timedelta(days=day - 1)
        cel_day = cel_starts[month - 1] + timedelta(days=day - 1)
        hko_valid = day <= hko_count and FIRST_DAY <= hko_day <= LAST_DAY
        cel_valid = day <= cel_count and FIRST_DAY <= cel_day <= LAST_DAY
        if cel_valid:
          actual = utils.to_solar(d)
          assert actual == solar(cel_day)
        else:
          with pytest.raises(ValueError):
            utils.to_solar(d)
        if cel_valid != hko_valid:
          measured_validity.add((year, month, day))
        elif cel_valid and (actual != solar(hko_day) or utils.to_lunar(d) != hko_lunar_dates[hko_day]):
          measured_months.add((year, month))

  assert measured_months == expected_months
  assert measured_validity == expected_validity
