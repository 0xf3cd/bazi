# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_celestial_utils.py

import unittest

from datetime import date, datetime, timedelta

from src.calendar import CalendarUtilsProtocol
from src.calendar.calendar_defines import CalendarType, CalendarDate
from src.calendar.celestial_calendar_utils import ALGO1, ALGO2
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


class TestProtocolConformance(unittest.TestCase):
  def test_conforms(self) -> None:
    for utils in (ALGO1, ALGO2):
      self.assertIsInstance(utils, CalendarUtilsProtocol)

  def test_the_two_algos_are_separate_objects(self) -> None:
    # A shared mutable switch plus `lru_cache` would let a switch return results computed
    # under the previous algorithm; separate instances make that impossible.
    self.assertIsNot(ALGO1, ALGO2)


class TestSupportedRange(unittest.TestCase):
  def test_derived_bounds(self) -> None:
    # Derived from the tables, not hardcoded: the solar bounds are the anchor and the
    # other four are conversions of them.
    self.assertEqual(ALGO1.get_min_supported_date(CalendarType.SOLAR), solar(1901, 2, 19))
    self.assertEqual(ALGO1.get_max_supported_date(CalendarType.SOLAR), solar(2099, 12, 31))
    self.assertEqual(ALGO1.get_min_supported_date(CalendarType.LUNAR), lunar(1901, 1, 1))
    self.assertEqual(ALGO1.get_max_supported_date(CalendarType.LUNAR), lunar(2099, 12, 20))
    self.assertEqual(ALGO1.get_min_supported_date(CalendarType.GANZHI), ganzhi(1901, 1, 16))
    self.assertEqual(ALGO1.get_max_supported_date(CalendarType.GANZHI), ganzhi(2099, 11, 25))

  def test_the_three_bounds_are_one_physical_day(self) -> None:
    # This is why per-date-type ranges would be wrong: they are the same day, spelled three
    # ways.  A conversion of either bound must stay inside the window on all three axes.
    for bound in (ALGO1.get_min_supported_date, ALGO1.get_max_supported_date):
      day: date = ALGO1.to_date(bound(CalendarType.SOLAR))
      self.assertEqual(ALGO1.to_date(bound(CalendarType.LUNAR)), day)
      self.assertEqual(ALGO1.to_date(bound(CalendarType.GANZHI)), day)


class TestValidity(unittest.TestCase):
  def test_solar(self) -> None:
    self.assertTrue(ALGO1.is_valid_solar_date(solar(2024, 2, 4)))
    self.assertFalse(ALGO1.is_valid_solar_date(lunar(2024, 2, 4))) # Wrong date type.
    self.assertFalse(ALGO1.is_valid_solar_date(solar(1901, 2, 18))) # One day before min.
    self.assertFalse(ALGO1.is_valid_solar_date(solar(2100, 1, 1))) # Past max.
    self.assertFalse(ALGO1.is_valid_solar_date(solar(2023, 2, 29))) # Not a leap year.
    self.assertTrue(ALGO1.is_valid_solar_date(solar(2024, 2, 29))) # A leap year.
    self.assertFalse(ALGO1.is_valid_solar_date(solar(2024, 13, 1))) # No such month.

  def test_lunar(self) -> None:
    self.assertTrue(ALGO1.is_valid_lunar_date(lunar(2024, 1, 1)))
    self.assertFalse(ALGO1.is_valid_lunar_date(solar(2024, 1, 1))) # Wrong date type.
    self.assertFalse(ALGO1.is_valid_lunar_date(lunar(1900, 12, 1))) # Before min.
    self.assertFalse(ALGO1.is_valid_lunar_date(lunar(2099, 12, 21))) # Past max.
    self.assertFalse(ALGO1.is_valid_lunar_date(lunar(2024, 13, 1))) # 2024 has 12 lunar months.
    self.assertTrue(ALGO1.is_valid_lunar_date(lunar(2023, 13, 1))) # 2023 is a leap lunar year.
    self.assertFalse(ALGO1.is_valid_lunar_date(lunar(2024, 1, 0)))
    self.assertFalse(ALGO1.is_valid_lunar_date(lunar(2024, 1, 31)))

  def test_ganzhi(self) -> None:
    self.assertTrue(ALGO1.is_valid_ganzhi_date(ganzhi(2024, 1, 1)))
    self.assertFalse(ALGO1.is_valid_ganzhi_date(solar(2024, 1, 1))) # Wrong date type.
    self.assertFalse(ALGO1.is_valid_ganzhi_date(ganzhi(1901, 1, 15))) # Before min.
    self.assertFalse(ALGO1.is_valid_ganzhi_date(ganzhi(2099, 11, 26))) # Past max.
    self.assertFalse(ALGO1.is_valid_ganzhi_date(ganzhi(2024, 13, 1))) # 12 ganzhi months only.
    self.assertFalse(ALGO1.is_valid_ganzhi_date(ganzhi(2024, 1, 0)))
    self.assertFalse(ALGO1.is_valid_ganzhi_date(ganzhi(2024, 1, 33)))

  def test_dispatch(self) -> None:
    self.assertTrue(ALGO1.is_valid(solar(2024, 2, 4)))
    self.assertTrue(ALGO1.is_valid(lunar(2024, 1, 1)))
    self.assertTrue(ALGO1.is_valid(ganzhi(2024, 1, 1)))
    self.assertFalse(ALGO1.is_valid(solar(2100, 1, 1)))


class TestConversions(unittest.TestCase):
  def test_ganzhi_month_lengths(self) -> None:
    counts: list[int] = ALGO1.days_counts_in_ganzhi_year(2024)
    self.assertEqual(len(counts), 12)
    # A ganzhi year runs 立春 to 立春, so the months must add up to exactly that span.
    span: int = (ALGO1.jieqi_date(2025, Jieqi.立春) - ALGO1.jieqi_date(2024, Jieqi.立春)).days
    self.assertEqual(sum(counts), span)

  def test_ganzhi_month_lengths_cannot_poison_the_cache(self) -> None:
    '''
    The lengths come from a cache, so handing back the cached list itself would let one
    caller's in-place edit corrupt every later answer.  Worse, it would not stay contained:
    `is_valid_ganzhi_date` caches verdicts computed from these lengths, so the wrong answers
    would outlive the edit and no `cache_clear` would bring them back.
    '''
    counts: list[int] = ALGO1.days_counts_in_ganzhi_year(2000)
    self.assertIsNot(counts, ALGO1.days_counts_in_ganzhi_year(2000))

    counts[0] = 999
    self.assertEqual(ALGO1.days_counts_in_ganzhi_year(2000)[0], 30)
    self.assertTrue(ALGO1.is_valid_ganzhi_date(ganzhi(2000, 1, 29)))

  def test_round_trips(self) -> None:
    # Every day of a leap lunar year and of a plain one, both ways round.
    for year in (2023, 2024):
      day: date = date(year, 1, 1)
      while day.year == year:
        d: CalendarDate = solar(day.year, day.month, day.day)
        self.assertEqual(ALGO1.lunar_to_solar(ALGO1.solar_to_lunar(d)), d)
        self.assertEqual(ALGO1.ganzhi_to_solar(ALGO1.solar_to_ganzhi(d)), d)
        self.assertEqual(ALGO1.ganzhi_to_lunar(ALGO1.solar_to_ganzhi(d)), ALGO1.solar_to_lunar(d))
        self.assertEqual(ALGO1.lunar_to_ganzhi(ALGO1.solar_to_lunar(d)), ALGO1.solar_to_ganzhi(d))
        day += timedelta(days=1)

  def test_dates_before_the_year_boundaries(self) -> None:
    # A solar date before 立春 belongs to the previous ganzhi year; before the lunar new
    # year, to the previous lunar year.  Both are the `-= 1` branches.
    self.assertEqual(ALGO1.solar_to_ganzhi(solar(2024, 1, 1)).year, 2023)
    self.assertEqual(ALGO1.solar_to_lunar(solar(2024, 1, 1)).year, 2023)
    self.assertEqual(ALGO1.solar_to_ganzhi(solar(2024, 2, 5)).year, 2024)

  def test_to_family(self) -> None:
    day: date = date(2024, 2, 4)
    self.assertEqual(ALGO1.to_solar(day), solar(2024, 2, 4))
    self.assertEqual(ALGO1.to_date(day), day)
    self.assertEqual(ALGO1.to_lunar(day), ALGO1.solar_to_lunar(solar(2024, 2, 4)))
    self.assertEqual(ALGO1.to_ganzhi(day), ALGO1.solar_to_ganzhi(solar(2024, 2, 4)))

    # Each `to_*` is the identity on its own type, and converts from the other two.
    for d in (solar(2024, 2, 4), lunar(2023, 13, 25), ganzhi(2024, 1, 1)):
      self.assertEqual(ALGO1.to_solar(d).date_type, CalendarType.SOLAR)
      self.assertEqual(ALGO1.to_lunar(d).date_type, CalendarType.LUNAR)
      self.assertEqual(ALGO1.to_ganzhi(d).date_type, CalendarType.GANZHI)
      self.assertEqual(ALGO1.to_date(d), date(2024, 2, 4))

  def test_to_family_returns_copies(self) -> None:
    # The identity paths must not hand the caller its own object back.  Two calls with the
    # same argument *do* share one object (the cache holds it), which is harmless because
    # `CalendarDate` exposes only getters over `Final` fields -- and it matches HKO.
    d: CalendarDate = solar(2024, 2, 4)
    self.assertIsNot(ALGO1.to_solar(d), d)
    self.assertIsNot(ALGO1.to_lunar(ALGO1.to_lunar(d)), ALGO1.to_lunar(d))


class TestJieqi(unittest.TestCase):
  def test_real_moments_not_placeholders(self) -> None:
    # The whole point of this backend: HKO can only say 00:00:00.
    self.assertEqual(ALGO1.jieqi_moment(2024, Jieqi.立春), datetime(2024, 2, 4, 16, 27, 6))
    self.assertEqual(ALGO1.jieqi_moment(2000, Jieqi.立春), datetime(2000, 2, 4, 20, 40, 23))
    self.assertNotEqual(ALGO1.jieqi_moment(2024, Jieqi.立春).time(), datetime.min.time())

  def test_date_is_the_moment_truncated(self) -> None:
    for year in (1901, 1979, 2024, 2100):
      for jq in Jieqi.as_list():
        self.assertEqual(ALGO1.jieqi_date(year, jq), ALGO1.jieqi_moment(year, jq).date())

  def test_out_of_range_year(self) -> None:
    with self.assertRaises(AssertionError):
      ALGO1.jieqi_moment(2101, Jieqi.立春)
    with self.assertRaises(AssertionError):
      ALGO1.jieqi_moment(1900, Jieqi.立春)
    with self.assertRaises(AssertionError):
      ALGO1.jieqi_moment('2024', Jieqi.立春)
    with self.assertRaises(AssertionError):
      ALGO1.jieqi_moment(2024, '立春')

  def test_supported_jie_boundaries(self) -> None:
    first, last = ALGO1.supported_jie_boundaries()
    self.assertEqual(first, ALGO1.jieqi_moment(1901, Jieqi.小寒))
    self.assertEqual(last, ALGO1.jieqi_moment(2100, Jieqi.大雪))

  def test_jie_range_is_enforced(self) -> None:
    first, last = ALGO1.supported_jie_boundaries()
    for fn in (ALGO1.prev_jie, ALGO1.next_jie):
      with self.assertRaises(ValueError):
        fn(first - timedelta(seconds=1))
      with self.assertRaises(ValueError):
        fn(last) # The upper bound is exclusive.
      with self.assertRaises(AssertionError):
        fn(date(2024, 2, 4)) # A date is not a datetime.

  def test_exactly_on_a_jie_belongs_to_it(self) -> None:
    '''
    The `>=` convention.  #72's golden cases are all comfortably away from a boundary, so
    this hole is not covered by them -- and with real moments it is now reachable.
    '''
    moment: datetime = ALGO1.jieqi_moment(2024, Jieqi.立春)

    self.assertEqual(ALGO1.prev_jie(moment), (Jieqi.立春, moment))
    self.assertEqual(ALGO1.next_jie(moment), (Jieqi.惊蛰, ALGO1.jieqi_moment(2024, Jieqi.惊蛰)))

    # One second earlier, the previous Jie is still 小寒 and the next one is 立春 itself.
    self.assertEqual(ALGO1.prev_jie(moment - timedelta(seconds=1)).jieqi, Jieqi.小寒)
    self.assertEqual(ALGO1.next_jie(moment - timedelta(seconds=1)), (Jieqi.立春, moment))

    # One second later, both have moved past 立春.
    self.assertEqual(ALGO1.prev_jie(moment + timedelta(seconds=1)), (Jieqi.立春, moment))
    self.assertEqual(ALGO1.next_jie(moment + timedelta(seconds=1)).jieqi, Jieqi.惊蛰)

  def test_jie_across_year_boundaries(self) -> None:
    # Before 小寒 of its own year, the previous Jie is last year's 大雪.
    self.assertEqual(ALGO1.prev_jie(datetime(2024, 1, 1)),
                     (Jieqi.大雪, ALGO1.jieqi_moment(2023, Jieqi.大雪)))
    # On or after 大雪, the next Jie is next year's 小寒.
    self.assertEqual(ALGO1.next_jie(datetime(2024, 12, 20)),
                     (Jieqi.小寒, ALGO1.jieqi_moment(2025, Jieqi.小寒)))

  def test_prev_and_next_bracket_every_jie(self) -> None:
    # Walking the whole window: `prev_jie` and `next_jie` must always be adjacent 节.
    first, last = ALGO1.supported_jie_boundaries()
    moment: datetime = first
    seen: int = 0
    while moment < last:
      self.assertEqual(ALGO1.prev_jie(moment).moment, moment)
      nxt = ALGO1.next_jie(moment)
      self.assertGreater(nxt.moment, moment)
      self.assertEqual(ALGO1.prev_jie(nxt.moment - timedelta(seconds=1)).moment, moment)
      moment = nxt.moment
      seen += 1
    # 12 节 per year over 1901..2100, minus 大雪 2100 itself (the bound is exclusive).
    self.assertEqual(seen, len(range(1901, 2101)) * 12 - 1)


class TestDualLunarAlgorithms(unittest.TestCase):
  def test_divergence_is_exactly_the_known_years(self) -> None:
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

    self.assertEqual(tuple(sorted(diverging_years)), ALGO2_DIVERGENT_YEARS)
    # Each divergence is one lunar month shifted by a day, so it spans exactly 30 days.
    self.assertEqual(len(diverging_days), 150)

  def test_the_jieqi_surface_is_shared(self) -> None:
    # Only the lunar tables differ; everything jieqi-derived is identical.
    self.assertEqual(ALGO1.jieqi_moment(2024, Jieqi.立春), ALGO2.jieqi_moment(2024, Jieqi.立春))
    self.assertEqual(ALGO1.days_counts_in_ganzhi_year(2024), ALGO2.days_counts_in_ganzhi_year(2024))
