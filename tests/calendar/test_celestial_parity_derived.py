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

from datetime import date, datetime, time, timedelta

from src.Calendar import HkoDataCalendarUtils as HKO
from src.Calendar.CalendarDefines import CalendarType, CalendarDate
from src.Calendar.CelestialCalendarUtils import ALGO1 as CEL
from src.Calendar.CelestialData.Loader import JIEQI_BY_INDEX
from src.Defines import Jieqi

# The whitelist's single source of truth, shared with parity layers a/b.  Imported as a
# bare sibling module: the test suite has no `__init__.py`, so pytest puts this directory
# on `sys.path` -- and `from tests.calendar...` would be shadowed at runtime by a stray
# regular `tests` package in site-packages.
from celestial_parity_data import JIEQI_DATE_DIVERGENCES, JieqiDateDivergence


JIES: list[Jieqi] = Jieqi.as_list()[::2] # The 12 节: only these start ganzhi months.


def solar(day: date) -> CalendarDate:
  return CalendarDate(day.year, day.month, day.day, CalendarType.SOLAR)


def jieqi_of(row: JieqiDateDivergence) -> Jieqi:
  return JIEQI_BY_INDEX[row.jq_idx]


def flipped_jies() -> list[JieqiDateDivergence]:
  '''The whitelist rows that are 节. Only these can move a ganzhi month boundary.'''
  return [row for row in JIEQI_DATE_DIVERGENCES if row.is_jie]


def affected_solar_days() -> set[date]:
  '''
  Derived, not listed: a moved 节 shifts the start of its ganzhi month, so every day from
  the earlier of the two candidate dates up to (but excluding) the next 节 gets a different
  ganzhi month or day index.
  '''
  days: set[date] = set()
  for row in flipped_jies():
    end: date = CEL.next_jie(CEL.jieqi_moment(row.year, jieqi_of(row))).moment.date()
    day: date = min(row.celestial_moment.date(), row.hko_date)
    while day < end:
      days.add(day)
      day += timedelta(days=1)
  return days


def affected_ganzhi_months() -> set[tuple[int, int]]:
  '''The (ganzhi year, ganzhi month) pairs that a moved 节 starts.'''
  months: set[tuple[int, int]] = set()
  for row in flipped_jies():
    # 立春 starts ganzhi month 1; 小寒, the twelfth 节, starts month 12 of the *previous*
    # ganzhi year, since it falls in January.
    jieqi: Jieqi = jieqi_of(row)
    months.add((row.year - 1 if jieqi is Jieqi.小寒 else row.year, JIES.index(jieqi) + 1))
  return months


class TestJieqiDateWhitelist(unittest.TestCase):
  def test_whitelist_is_exact_through_the_backend(self) -> None:
    '''
    The anchor for layer (c).  Layer (b) checks the same whitelist against the raw table
    with its own minimal parser; this one goes through `Loader` + `CelestialCalendarUtils`,
    so the two together also prove that the consumer path reproduces the table faithfully.
    '''
    measured: list[tuple[int, int, date]] = []
    for year in range(1901, 2101):
      for jq_idx, jq in enumerate(JIEQI_BY_INDEX):
        cel, hko = CEL.jieqi_date(year, jq), HKO.jieqi_date(year, jq)
        if cel != hko:
          measured.append((year, jq_idx, cel))
    # Sorted: the signal is the key set, not the scan order (layer (b) compares as a set too).
    self.assertEqual(
      sorted(measured),
      sorted((row.year, row.jq_idx, row.celestial_moment.date()) for row in JIEQI_DATE_DIVERGENCES),
    )

  def test_moments_match_the_whitelist(self) -> None:
    # Not just the dates: the stored moments themselves, so a re-baked table with a
    # different rounding policy cannot pass by accident.
    for row in JIEQI_DATE_DIVERGENCES:
      self.assertEqual(CEL.jieqi_moment(row.year, jieqi_of(row)), row.celestial_moment)
      self.assertEqual(HKO.jieqi_date(row.year, jieqi_of(row)), row.hko_date)

  def test_only_two_of_them_are_jie(self) -> None:
    # Only 节 start ganzhi months, so only these two can propagate into ganzhi methods.
    self.assertEqual([(row.year, row.name) for row in flipped_jies()],
                     [(1917, '大雪'), (1927, '白露')])

  def test_prev_next_jie_diverge_only_inside_the_moment_window(self) -> None:
    '''
    `prev_jie`/`next_jie` escape layer (c) by design (see the protocol's carve-out): inside
    the window between the two backends' ideas of when a jie starts, they legitimately name
    different jie -- and `dayun_start_moment` rides on it.  Both backends answer over the 12
    节 only, so this pins the shape of that escape for every 节: the window is
    [min(hko_date, true date) midnight, true moment); inside it the backends are exactly one
    节 apart, outside it they agree.  A day-level regression that *narrows* a window turns
    red here; a widening one moves the probes along with it and is caught by the whitelist
    tests above instead.
    '''
    cel_first, cel_last = CEL.supported_jie_boundaries()
    hko_first, hko_last = HKO.supported_jie_boundaries()
    cycle: list[Jieqi] = JIES
    for year in range(1901, 2101):
      for jq_idx, jq in enumerate(cycle):
        moment: datetime = CEL.jieqi_moment(year, jq)
        window_start: datetime = datetime.combine(
          min(HKO.jieqi_date(year, jq), moment.date()),
          time.min,
        )
        prev_jq: Jieqi = cycle[(jq_idx - 1) % len(cycle)]
        next_jq: Jieqi = cycle[(jq_idx + 1) % len(cycle)]

        inside: datetime = window_start + (moment - window_start) / 2
        if inside >= cel_first: # else both queries fall off the table edge (小寒 1901)
          self.assertEqual(CEL.prev_jie(inside).jieqi, prev_jq, (year, jq))
          self.assertEqual(CEL.next_jie(inside).jieqi, jq, (year, jq))
        if inside < hko_last: # else both queries fall off the table edge (大雪 2100)
          self.assertEqual(HKO.prev_jie(inside).jieqi, jq, (year, jq))
          self.assertEqual(HKO.next_jie(inside).jieqi, next_jq, (year, jq))

        before: datetime = window_start - timedelta(seconds=1)
        if before >= cel_first and before >= hko_first:
          self.assertEqual(CEL.prev_jie(before).jieqi, HKO.prev_jie(before).jieqi, (year, jq))
          self.assertEqual(CEL.next_jie(before).jieqi, HKO.next_jie(before).jieqi, (year, jq))
        after: datetime = moment + timedelta(seconds=1)
        if after < cel_last and after < hko_last:
          self.assertEqual(CEL.prev_jie(after).jieqi, HKO.prev_jie(after).jieqi, (year, jq))
          self.assertEqual(CEL.next_jie(after).jieqi, HKO.next_jie(after).jieqi, (year, jq))

  def test_the_derivations_preconditions_hold(self) -> None:
    '''
    `affected_ganzhi_months` models a flipped 节 as moving the start of exactly one ganzhi
    month.  That holds for every 节 except 立春, which is also the *end* of the previous
    ganzhi year's twelfth month: a flipped 立春 would perturb `(Y - 1, 12)` too, and would
    falsify the "yearly totals unchanged" check below, since the day gained and the day lost
    would land in different ganzhi years.

    No shipped table flips 立春, so rather than carry untested branches for a configuration
    that does not exist, the assumption is asserted here: if a re-baked table ever flips one,
    this fails first and names what to generalise.  Layer (c) stays *sound* either way --
    every test there compares a measured set against the derived one, so an unmodelled
    divergence still turns the suite red.  What this guard protects is the diagnosis.
    '''
    self.assertNotIn(
      Jieqi.立春, {jieqi_of(row) for row in flipped_jies()},
      'a flipped 立春 also moves (Y - 1, 12): generalise `affected_ganzhi_months` and the '
      'yearly-total assertion before deleting this guard')

    # The same reasoning at the window edge: the derived days are checked against a scan
    # bounded by the supported solar range, so a flip in the final month would push the
    # derived set past where that scan can see it.
    last: date = HKO.to_date(HKO.get_max_supported_date(CalendarType.SOLAR))
    self.assertLessEqual(max(affected_solar_days()), last)


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
