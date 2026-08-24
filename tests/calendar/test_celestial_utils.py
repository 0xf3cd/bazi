# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_celestial_utils.py

import pytest

from datetime import date, datetime, timedelta

from src.calendar import CalendarUtilsProtocol
from src.calendar.dates import CalendarType, CalendarDate
from src.calendar.celestial_utils import ALGO1, ALGO2
from src.defines import Jieqi

# The whitelist's single source of truth.  Bare sibling import -- see the NOTE in
# `test_celestial_tables.py` for why `from tests.calendar...` is not used.
from celestial_parity_data import ALGO2_DIVERGENT_YEARS


def solar(year: int, month: int, day: int) -> CalendarDate:
  return CalendarDate(year, month, day, CalendarType.SOLAR)


def lunar(year: int, month: int, day: int) -> CalendarDate:
  return CalendarDate(year, month, day, CalendarType.LUNAR)


def ganzhi(year: int, month: int, day: int) -> CalendarDate:
  return CalendarDate(year, month, day, CalendarType.GANZHI)


def test_conforms() -> None:
  for utils in (ALGO1, ALGO2):
    assert isinstance(utils, CalendarUtilsProtocol)


def test_the_two_algos_are_separate_objects() -> None:
  # A shared mutable switch plus `lru_cache` would let a switch return results computed
  # under the previous algorithm; separate instances make that impossible.
  assert ALGO1 is not ALGO2


def test_derived_bounds() -> None:
  # Derived from the tables, not hardcoded: the solar bounds are the anchor and the
  # other four are conversions of them.
  assert ALGO1.get_min_supported_date(CalendarType.SOLAR) == solar(1901, 2, 19)
  assert ALGO1.get_max_supported_date(CalendarType.SOLAR) == solar(2099, 12, 31)
  assert ALGO1.get_min_supported_date(CalendarType.LUNAR) == lunar(1901, 1, 1)
  assert ALGO1.get_max_supported_date(CalendarType.LUNAR) == lunar(2099, 12, 20)
  assert ALGO1.get_min_supported_date(CalendarType.GANZHI) == ganzhi(1901, 1, 16)
  assert ALGO1.get_max_supported_date(CalendarType.GANZHI) == ganzhi(2099, 11, 25)


def test_the_three_bounds_are_one_physical_day() -> None:
  # This is why per-date-type ranges would be wrong: they are the same day, spelled three
  # ways.  A conversion of either bound must stay inside the window on all three axes.
  for bound in (ALGO1.get_min_supported_date, ALGO1.get_max_supported_date):
    day: date = ALGO1.to_date(bound(CalendarType.SOLAR))
    assert ALGO1.to_date(bound(CalendarType.LUNAR)) == day
    assert ALGO1.to_date(bound(CalendarType.GANZHI)) == day


def test_get_min_supported_date_negative() -> None:
  with pytest.raises(ValueError):
    ALGO1.get_min_supported_date(42)


def test_get_max_supported_date_negative() -> None:
  with pytest.raises(ValueError):
    ALGO1.get_max_supported_date(42)


def test_solar() -> None:
  assert ALGO1.is_valid_solar_date(solar(2024, 2, 4))
  assert not ALGO1.is_valid_solar_date(lunar(2024, 2, 4)) # Wrong date type.
  assert not ALGO1.is_valid_solar_date(solar(1901, 2, 18)) # One day before min.
  assert not ALGO1.is_valid_solar_date(solar(2100, 1, 1)) # Past max.
  assert not ALGO1.is_valid_solar_date(solar(2023, 2, 29)) # Not a leap year.
  assert ALGO1.is_valid_solar_date(solar(2024, 2, 29)) # A leap year.
  assert not ALGO1.is_valid_solar_date(solar(2024, 13, 1)) # No such month.


def test_lunar() -> None:
  assert ALGO1.is_valid_lunar_date(lunar(2024, 1, 1))
  assert not ALGO1.is_valid_lunar_date(solar(2024, 1, 1)) # Wrong date type.
  assert not ALGO1.is_valid_lunar_date(lunar(1900, 12, 1)) # Before min.
  assert not ALGO1.is_valid_lunar_date(lunar(2099, 12, 21)) # Past max.
  assert not ALGO1.is_valid_lunar_date(lunar(2024, 13, 1)) # 2024 has 12 lunar months.
  assert ALGO1.is_valid_lunar_date(lunar(2023, 13, 1)) # 2023 is a leap lunar year.
  assert not ALGO1.is_valid_lunar_date(lunar(2024, 1, 0))
  assert not ALGO1.is_valid_lunar_date(lunar(2024, 1, 31))


def test_lunar_leap_month_boundary() -> None:
  # A readable sample of the slot-3 numbering convention, plus the boundary: 2023's leap
  # month is 闰二月, slot 3 in this numbering (it shifts the later months -- slot 13 is
  # 腊月, not the leap month), running 29 days from 2023-03-22 to 2023-04-19.  The data
  # itself is regression-pinned by `test_data_sections_are_frozen` (table hash) and
  # `test_algo1_matches_hko_strictly`; this test does not guard that class alone.
  assert ALGO1.is_valid_lunar_date(lunar(2023, 3, 29)) # Last day of the leap month.
  assert not ALGO1.is_valid_lunar_date(lunar(2023, 3, 30)) # One past the leap month's end.


def test_ganzhi() -> None:
  assert ALGO1.is_valid_ganzhi_date(ganzhi(2024, 1, 1))
  assert not ALGO1.is_valid_ganzhi_date(solar(2024, 1, 1)) # Wrong date type.
  assert not ALGO1.is_valid_ganzhi_date(ganzhi(1901, 1, 15)) # Before min.
  assert not ALGO1.is_valid_ganzhi_date(ganzhi(2099, 11, 26)) # Past max.
  assert not ALGO1.is_valid_ganzhi_date(ganzhi(2024, 13, 1)) # 12 ganzhi months only.
  assert not ALGO1.is_valid_ganzhi_date(ganzhi(2024, 1, 0))
  assert not ALGO1.is_valid_ganzhi_date(ganzhi(2024, 1, 33))


def test_dispatch() -> None:
  assert ALGO1.is_valid(solar(2024, 2, 4))
  assert ALGO1.is_valid(lunar(2024, 1, 1))
  assert ALGO1.is_valid(ganzhi(2024, 1, 1))
  assert not ALGO1.is_valid(solar(2100, 1, 1))


def test_ganzhi_month_lengths() -> None:
  for year in (2024, 2100):
    counts: list[int] = ALGO1.days_counts_in_ganzhi_year(year)
    assert len(counts) == 12
    # A ganzhi year runs 立春 to 立春, so the months must add up to exactly that span.
    span: int = (ALGO1.jieqi_date(year + 1, Jieqi.立春) - ALGO1.jieqi_date(year, Jieqi.立春)).days
    assert sum(counts) == span


def test_ganzhi_month_lengths_cannot_poison_the_cache() -> None:
  '''
  The lengths come from a cache, so handing back the cached list itself would let one
  caller's in-place edit corrupt every later answer.  Worse, it would not stay contained:
  `is_valid_ganzhi_date` caches verdicts computed from these lengths, so the wrong answers
  would outlive the edit and no `cache_clear` would bring them back.
  '''
  counts: list[int] = ALGO1.days_counts_in_ganzhi_year(2000)
  assert counts is not ALGO1.days_counts_in_ganzhi_year(2000)

  counts[0] = 999
  assert ALGO1.days_counts_in_ganzhi_year(2000)[0] == 30
  assert ALGO1.is_valid_ganzhi_date(ganzhi(2000, 1, 29))


def test_days_counts_in_ganzhi_year_negative() -> None:
  with pytest.raises(ValueError):
    ALGO1.days_counts_in_ganzhi_year(1900) # Before the first jieqi-table year.
  with pytest.raises(ValueError):
    ALGO1.days_counts_in_ganzhi_year(2200) # The last jieqi-table year: no 立春 of 2201 to close it.


def test_round_trips() -> None:
  # Every day of a leap lunar year and of a plain one, both ways round.
  for year in (2023, 2024):
    day: date = date(year, 1, 1)
    while day.year == year:
      d: CalendarDate = solar(day.year, day.month, day.day)
      assert ALGO1.lunar_to_solar(ALGO1.solar_to_lunar(d)) == d
      assert ALGO1.ganzhi_to_solar(ALGO1.solar_to_ganzhi(d)) == d
      assert ALGO1.ganzhi_to_lunar(ALGO1.solar_to_ganzhi(d)) == ALGO1.solar_to_lunar(d)
      assert ALGO1.lunar_to_ganzhi(ALGO1.solar_to_lunar(d)) == ALGO1.solar_to_ganzhi(d)
      day += timedelta(days=1)


def test_lunar_leap_month_round_trips() -> None:
  # Lunar-anchored: `test_round_trips` reaches the leap month only via solar dates, so
  # walk the leap month from the lunar side.  Like the boundary test above, this is a
  # readable sample of the slot-3 convention; the data-side regression belongs to
  # `test_data_sections_are_frozen` (table hash) and `test_algo1_matches_hko_strictly`.
  for d, expected in ((1, solar(2023, 3, 22)), (15, solar(2023, 4, 5)), (29, solar(2023, 4, 19))):
    leap: CalendarDate = lunar(2023, 3, d)
    assert ALGO1.lunar_to_solar(leap) == expected
    assert ALGO1.solar_to_lunar(ALGO1.lunar_to_solar(leap)) == leap


def test_dates_before_the_year_boundaries() -> None:
  # A solar date before 立春 belongs to the previous ganzhi year; before the lunar new
  # year, to the previous lunar year.  Both are the `-= 1` branches.
  assert ALGO1.solar_to_ganzhi(solar(2024, 1, 1)).year == 2023
  assert ALGO1.solar_to_lunar(solar(2024, 1, 1)).year == 2023
  assert ALGO1.solar_to_ganzhi(solar(2024, 2, 5)).year == 2024


def test_date_conversions_negative() -> None:
  with pytest.raises(ValueError):
    ALGO1.ganzhi_to_lunar(ganzhi(1, 1, 1))
  with pytest.raises(ValueError):
    ALGO1.ganzhi_to_lunar(solar(2024, 1, 1))

  with pytest.raises(ValueError):
    ALGO1.lunar_to_ganzhi(lunar(1, 1, 1))
  with pytest.raises(ValueError):
    ALGO1.lunar_to_ganzhi(solar(2024, 1, 1))

  with pytest.raises(ValueError):
    ALGO1.solar_to_lunar(solar(1, 1, 1))
  with pytest.raises(ValueError):
    ALGO1.solar_to_lunar(ganzhi(2024, 1, 1))

  with pytest.raises(ValueError):
    ALGO1.lunar_to_solar(lunar(1, 1, 1))
  with pytest.raises(ValueError):
    ALGO1.lunar_to_solar(ganzhi(2024, 1, 1))

  with pytest.raises(ValueError):
    ALGO1.solar_to_ganzhi(solar(1, 1, 1))
  with pytest.raises(ValueError):
    ALGO1.solar_to_ganzhi(ganzhi(2024, 1, 1))

  with pytest.raises(ValueError):
    ALGO1.ganzhi_to_solar(ganzhi(1, 1, 1))
  with pytest.raises(ValueError):
    ALGO1.ganzhi_to_solar(solar(2024, 1, 1))


def test_to_family() -> None:
  day: date = date(2024, 2, 4)
  assert ALGO1.to_solar(day) == solar(2024, 2, 4)
  assert ALGO1.to_date(day) == day
  assert ALGO1.to_lunar(day) == ALGO1.solar_to_lunar(solar(2024, 2, 4))
  assert ALGO1.to_ganzhi(day) == ALGO1.solar_to_ganzhi(solar(2024, 2, 4))

  # Each `to_*` is the identity on its own type, and converts from the other two.
  for d in (solar(2024, 2, 4), lunar(2023, 13, 25), ganzhi(2024, 1, 1)):
    assert ALGO1.to_solar(d).date_type == CalendarType.SOLAR
    assert ALGO1.to_lunar(d).date_type == CalendarType.LUNAR
    assert ALGO1.to_ganzhi(d).date_type == CalendarType.GANZHI
    assert ALGO1.to_date(d) == date(2024, 2, 4)


def test_to_family_negative() -> None:
  # Both checks live in the shared funnel, so every `to_*` carries the same contract.
  with pytest.raises(ValueError):
    ALGO1.to_solar(date(1901, 1, 1)) # An in-window year, yet before the first supported day.
  with pytest.raises(ValueError):
    ALGO1.to_lunar(lunar(9999, 1, 1))
  with pytest.raises(ValueError):
    ALGO1.to_ganzhi(solar(1901, 1, 1)) # Before the first supported day.
  with pytest.raises(TypeError):
    ALGO1.to_solar('2024-01-01') # Not a date or CalendarDate.
  with pytest.raises(TypeError):
    ALGO1.to_lunar('2024-01-01') # Not a date or CalendarDate.
  with pytest.raises(TypeError):
    ALGO1.to_ganzhi('2024-01-01') # Not a date or CalendarDate.


def test_real_moments_not_placeholders() -> None:
  # The whole point of this backend: HKO can only say 00:00:00.
  assert ALGO1.jieqi_moment(2024, Jieqi.立春) == datetime(2024, 2, 4, 16, 27, 6)
  assert ALGO1.jieqi_moment(2000, Jieqi.立春) == datetime(2000, 2, 4, 20, 40, 23)
  assert ALGO1.jieqi_moment(2024, Jieqi.立春).time() != datetime.min.time()


def test_date_is_the_moment_truncated() -> None:
  for year in (1901, 1979, 2024, 2100):
    for jq in Jieqi.as_list():
      assert ALGO1.jieqi_date(year, jq) == ALGO1.jieqi_moment(year, jq).date()


def test_out_of_range_year() -> None:
  with pytest.raises(ValueError):
    ALGO1.jieqi_moment(2201, Jieqi.立春)
  with pytest.raises(ValueError):
    ALGO1.jieqi_moment(1900, Jieqi.立春)
  with pytest.raises(TypeError):
    ALGO1.jieqi_moment('2024', Jieqi.立春)
  with pytest.raises(TypeError):
    ALGO1.jieqi_moment(2024, '立春')


def test_supported_jie_boundaries() -> None:
  first, last = ALGO1.supported_jie_boundaries()
  assert first == ALGO1.jieqi_moment(1901, Jieqi.小寒)
  assert last == ALGO1.jieqi_moment(2200, Jieqi.大雪)


def test_jie_range_is_enforced() -> None:
  first, last = ALGO1.supported_jie_boundaries()
  for fn in (ALGO1.prev_jie, ALGO1.next_jie):
    with pytest.raises(ValueError):
      fn(first - timedelta(seconds=1))
    with pytest.raises(ValueError):
      fn(last) # The upper bound is exclusive.
    with pytest.raises(TypeError):
      fn(date(2024, 2, 4)) # A date is not a datetime.


def test_exactly_on_a_jie_belongs_to_it() -> None:
  '''
  The `>=` convention.  #72's golden cases are all comfortably away from a boundary, so
  this hole is not covered by them -- and with real moments it is now reachable.
  '''
  moment: datetime = ALGO1.jieqi_moment(2024, Jieqi.立春)

  assert ALGO1.prev_jie(moment) == (Jieqi.立春, moment)
  assert ALGO1.next_jie(moment) == (Jieqi.惊蛰, ALGO1.jieqi_moment(2024, Jieqi.惊蛰))

  # One second earlier, the previous Jie is still 小寒 and the next one is 立春 itself.
  assert ALGO1.prev_jie(moment - timedelta(seconds=1)).jieqi == Jieqi.小寒
  assert ALGO1.next_jie(moment - timedelta(seconds=1)) == (Jieqi.立春, moment)

  # One second later, both have moved past 立春.
  assert ALGO1.prev_jie(moment + timedelta(seconds=1)) == (Jieqi.立春, moment)
  assert ALGO1.next_jie(moment + timedelta(seconds=1)).jieqi == Jieqi.惊蛰


def test_jie_across_year_boundaries() -> None:
  # Before 小寒 of its own year, the previous Jie is last year's 大雪.
  assert ALGO1.prev_jie(datetime(2024, 1, 1)) == (Jieqi.大雪, ALGO1.jieqi_moment(2023, Jieqi.大雪))
  # On or after 大雪, the next Jie is next year's 小寒.
  assert ALGO1.next_jie(datetime(2024, 12, 20)) == (Jieqi.小寒, ALGO1.jieqi_moment(2025, Jieqi.小寒))


def test_prev_and_next_bracket_every_jie() -> None:
  # Walking the whole window: `prev_jie` and `next_jie` must always be adjacent 节.
  first, last = ALGO1.supported_jie_boundaries()
  moment: datetime = first
  seen: int = 0
  while moment < last:
    assert ALGO1.prev_jie(moment).moment == moment
    nxt = ALGO1.next_jie(moment)
    assert nxt.moment > moment
    assert ALGO1.prev_jie(nxt.moment - timedelta(seconds=1)).moment == moment
    moment = nxt.moment
    seen += 1
  # 12 节 per year over 1901..2200, minus 大雪 2200 itself (the bound is exclusive).
  assert seen == len(range(1901, 2201)) * 12 - 1


def test_divergence_is_exactly_the_known_years() -> None:
  '''
  Scanned over the whole window rather than over month starts: 1915's difference is in
  the length of its *last* month, so no month start inside 1915 moves -- it surfaces as
  lunar 1916 starting a day later.
  '''
  diverging_days: list[date] = []
  diverging_years: set[int] = set()
  day: date = ALGO1.to_date(ALGO1.get_min_supported_date(CalendarType.SOLAR))
  last: date = ALGO1.to_date(ALGO1.get_max_supported_date(CalendarType.SOLAR))
  while day <= last:
    d: CalendarDate = solar(day.year, day.month, day.day)
    algo1_lunar, algo2_lunar = ALGO1.solar_to_lunar(d), ALGO2.solar_to_lunar(d)
    if algo1_lunar != algo2_lunar:
      diverging_days.append(day)
      diverging_years |= {algo1_lunar.year, algo2_lunar.year}
    day += timedelta(days=1)

  assert tuple(sorted(diverging_years)) == ALGO2_DIVERGENT_YEARS
  # Each divergence is one lunar month shifted by a day, so it spans exactly 30 days.
  assert len(diverging_days) == 150


def test_the_jieqi_surface_is_shared() -> None:
  # Only the lunar tables differ; everything jieqi-derived is identical.
  assert ALGO1.jieqi_moment(2024, Jieqi.立春) == ALGO2.jieqi_moment(2024, Jieqi.立春)
  assert ALGO1.days_counts_in_ganzhi_year(2024) == ALGO2.days_counts_in_ganzhi_year(2024)
