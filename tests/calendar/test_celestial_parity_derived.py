# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_celestial_parity_derived.py

'''
Parity between the HKO and celestial backends, layer (c): the ganzhi-derived methods.

The contract is deliberately not "100% identical, with known exceptions allowed" -- that
is unfalsifiable, and it is also false.  Instead:

  (a) the lunar surface is strictly identical (celestial's algo1 *is* the HKO almanac);
  (b) `jieqi_date` disagrees on exactly the frozen whitelist below -- celestial knows the
      real moment, HKO only the official date, so a moment near midnight can land on the
      other side of it;
  (c) every ganzhi-derived method's expected disagreement is *computed* from that
      whitelist here.  No hand-written exemptions: if a table changes, the derivation
      moves with it and an unattributed difference turns the suite red.

What this proves is *equivalence, not truth*.  Both backends descend from the HKO
almanac, so they agree by construction wherever the almanac made a call (the 2033 problem
being the famous one).  The truth side is covered upstream, by celestial-calendar's own
HKO x DE441 dual-axis golden tests (0.525 min agreement over 2022-2028).
'''

import unittest

from datetime import date, timedelta

from src.Calendar import HkoDataCalendarUtils as HKO
from src.Calendar.CalendarDefines import CalendarType, CalendarDate
from src.Calendar.CelestialCalendarUtils import ALGO1 as CEL
from src.Defines import Jieqi


# The frozen whitelist: (solar year, jieqi, celestial date, HKO date).
#
# Measured over the whole 1901-2100 x 24 table: 7 disagreements out of 4800, every one of
# them a moment within ~12 minutes of midnight.  Times are the stored (truncated) ones.
#
# Five of the seven cluster in 1901-1928, but they do not point the same way (1912/1913
# fall on the earlier date while 1917/1927/1928 fall on the later one), so this is not a
# constant offset -- issue #69's Beijing local mean time would not explain it either.  It
# is old-epoch / delta-T noise, which is why each row is attributed individually rather
# than exempted by a formula.
#
# NOTE (integration): Lane G's `celestial_parity_data.py` is meant to be the single source
# of this list, together with layer (b).  Until it lands, this copy anchors layer (c); the
# two must agree, and a disagreement is itself a finding.
JIEQI_DATE_WHITELIST: list[tuple[int, Jieqi, date, date]] = [
  (1912, Jieqi.小雪, date(1912, 11, 22), date(1912, 11, 23)), # 23:48:13, 气
  (1913, Jieqi.秋分, date(1913, 9, 23), date(1913, 9, 24)),   # 23:52:48, 气
  (1917, Jieqi.大雪, date(1917, 12, 8), date(1917, 12, 7)),   # 00:01:05, 节 -- propagates
  (1927, Jieqi.白露, date(1927, 9, 9), date(1927, 9, 8)),     # 00:05:30, 节 -- propagates
  (1928, Jieqi.夏至, date(1928, 6, 22), date(1928, 6, 21)),   # 00:06:27, 气
  (1979, Jieqi.大寒, date(1979, 1, 20), date(1979, 1, 21)),   # 23:59:56, 气 -- 4s from midnight
  (2084, Jieqi.春分, date(2084, 3, 20), date(2084, 3, 19)),   # 00:00:30, 气
]

JIES: list[Jieqi] = Jieqi.as_list()[::2] # The 12 节: only these start ganzhi months.


def solar(day: date) -> CalendarDate:
  return CalendarDate(day.year, day.month, day.day, CalendarType.SOLAR)


def flipped_jies() -> list[tuple[int, Jieqi, date, date]]:
  '''The whitelist rows that are 节. Only these can move a ganzhi month boundary.'''
  return [row for row in JIEQI_DATE_WHITELIST if row[1] in JIES]


def affected_solar_days() -> set[date]:
  '''
  Derived, not listed: a moved 节 shifts the start of its ganzhi month, so every day from
  the earlier of the two candidate dates up to (but excluding) the next 节 gets a different
  ganzhi month or day index.
  '''
  days: set[date] = set()
  for year, jieqi, cel, hko in flipped_jies():
    end: date = CEL.next_jie(CEL.jieqi_moment(year, jieqi)).moment.date()
    day: date = min(cel, hko)
    while day < end:
      days.add(day)
      day += timedelta(days=1)
  return days


def affected_ganzhi_months() -> set[tuple[int, int]]:
  '''The (ganzhi year, ganzhi month) pairs that a moved 节 starts.'''
  months: set[tuple[int, int]] = set()
  for year, jieqi, _, _ in flipped_jies():
    # 立春 starts ganzhi month 1; 小寒, the twelfth 节, starts month 12 of the *previous*
    # ganzhi year, since it falls in January.
    index: int = JIES.index(jieqi)
    months.add((year - 1 if jieqi is Jieqi.小寒 else year, index + 1))
  return months


class TestJieqiDateWhitelist(unittest.TestCase):
  def test_whitelist_is_exact_over_the_table(self) -> None:
    '''The anchor for layer (c): the difference set is exactly these rows, no more.'''
    measured: list[tuple[int, Jieqi, date, date]] = []
    for year in range(1901, 2101):
      for jq in Jieqi.as_list():
        cel, hko = CEL.jieqi_date(year, jq), HKO.jieqi_date(year, jq)
        if cel != hko:
          measured.append((year, jq, cel, hko))
    self.assertEqual(measured, JIEQI_DATE_WHITELIST)

  def test_only_two_of_them_are_jie(self) -> None:
    # Only 节 start ganzhi months, so only these two can propagate into ganzhi methods.
    self.assertEqual([(y, jq.value) for y, jq, _, _ in flipped_jies()],
                     [(1917, '大雪'), (1927, '白露')])


class TestLunarSurfaceIsIdentical(unittest.TestCase):
  '''Layer (a): celestial's algo1 is the same HKO almanac data, so this is strict.'''

  def test_no_disagreement_anywhere(self) -> None:
    day: date = HKO.to_date(HKO.get_min_supported_date(CalendarType.SOLAR))
    last: date = HKO.to_date(HKO.get_max_supported_date(CalendarType.SOLAR))
    while day <= last:
      d: CalendarDate = solar(day)
      self.assertEqual(CEL.solar_to_lunar(d), HKO.solar_to_lunar(d), day)
      day += timedelta(days=1)

  def test_lunar_dates_round_trip_identically(self) -> None:
    for year in range(1901, 2100):
      for month in range(1, 14):
        d: CalendarDate = CalendarDate(year, month, 1, CalendarType.LUNAR)
        self.assertEqual(CEL.is_valid_lunar_date(d), HKO.is_valid_lunar_date(d))
        if CEL.is_valid_lunar_date(d):
          self.assertEqual(CEL.lunar_to_solar(d), HKO.lunar_to_solar(d))


class TestSupportedRangeIsIdentical(unittest.TestCase):
  def test_bounds(self) -> None:
    # celestial derives these from its tables, HKO hardcodes them; they must still agree,
    # because the two backends cover the same physical window.
    for date_type in CalendarType:
      self.assertEqual(CEL.get_min_supported_date(date_type), HKO.get_min_supported_date(date_type))
      self.assertEqual(CEL.get_max_supported_date(date_type), HKO.get_max_supported_date(date_type))


class TestGanzhiDerivedMethods(unittest.TestCase):
  '''Layer (c): every expectation below is computed from the whitelist.'''

  def test_solar_side_disagreements_are_exactly_derived(self) -> None:
    expected: set[date] = affected_solar_days()
    measured_ganzhi: set[date] = set()
    measured_via_lunar: set[date] = set()

    day: date = HKO.to_date(HKO.get_min_supported_date(CalendarType.SOLAR))
    last: date = HKO.to_date(HKO.get_max_supported_date(CalendarType.SOLAR))
    while day <= last:
      d: CalendarDate = solar(day)
      if CEL.solar_to_ganzhi(d) != HKO.solar_to_ganzhi(d):
        measured_ganzhi.add(day)
      if CEL.lunar_to_ganzhi(CEL.solar_to_lunar(d)) != HKO.lunar_to_ganzhi(HKO.solar_to_lunar(d)):
        measured_via_lunar.add(day)
      day += timedelta(days=1)

    self.assertEqual(measured_ganzhi, expected)
    self.assertEqual(measured_via_lunar, expected)
    # Two moved 节, each shifting one ganzhi month: 30 and 31 days.
    self.assertEqual(len(expected), 61)

  def test_days_counts_disagrees_on_exactly_the_derived_years(self) -> None:
    expected: set[int] = {year for year, _ in affected_ganzhi_months()}
    measured: set[int] = {year for year in range(1901, 2100)
                          if CEL.days_counts_in_ganzhi_year(year) != HKO.days_counts_in_ganzhi_year(year)}
    self.assertEqual(measured, expected)
    # A moved 节 makes one month longer and its neighbour shorter, so the year still adds up.
    for year in expected:
      self.assertEqual(sum(CEL.days_counts_in_ganzhi_year(year)),
                       sum(HKO.days_counts_in_ganzhi_year(year)))

  def test_ganzhi_side_disagreements_stay_in_the_derived_months(self) -> None:
    expected_months: set[tuple[int, int]] = affected_ganzhi_months()
    measured_months: set[tuple[int, int]] = set()
    measured_validity: set[tuple[int, int, int]] = set()

    for year in range(1901, 2100):
      cel_counts: list[int] = CEL.days_counts_in_ganzhi_year(year)
      hko_counts: list[int] = HKO.days_counts_in_ganzhi_year(year)
      for month in range(1, 13):
        for day in range(1, max(cel_counts[month - 1], hko_counts[month - 1]) + 1):
          d: CalendarDate = CalendarDate(year, month, day, CalendarType.GANZHI)
          cel_valid, hko_valid = CEL.is_valid_ganzhi_date(d), HKO.is_valid_ganzhi_date(d)
          if cel_valid != hko_valid:
            measured_validity.add((year, month, day))
            continue
          if not cel_valid:
            continue
          if (CEL.ganzhi_to_solar(d) != HKO.ganzhi_to_solar(d)
              or CEL.ganzhi_to_lunar(d) != HKO.ganzhi_to_lunar(d)):
            measured_months.add((year, month))

    self.assertEqual(measured_months, expected_months)
    # Validity can only differ where the month lengths do: the days in between the two.
    expected_validity: set[tuple[int, int, int]] = set()
    for year, _ in expected_months:
      cel_counts = CEL.days_counts_in_ganzhi_year(year)
      hko_counts = HKO.days_counts_in_ganzhi_year(year)
      for month in range(1, 13):
        lo, hi = sorted((cel_counts[month - 1], hko_counts[month - 1]))
        expected_validity |= {(year, month, day) for day in range(lo + 1, hi + 1)}
    self.assertEqual(measured_validity, expected_validity)
