# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# tests/calendar/celestial_parity_data.py
#
# The frozen whitelist of known divergences between the committed CelestialData tables
# (`src/Calendar/CelestialData/data/`) and HkoData -- the single source of truth
# (唯一真源). `test_celestial_tables.py` (parity layers a/b) verifies the tables against
# HkoData with exactly this whitelist, and layer c (`test_celestial_parity_derived.py`) derives its expectations
# from these entries mechanically. No formulaic exemption: every entry carries its own
# attribution, and the entry count itself is asserted.

from datetime import date, datetime
from typing import Final, NamedTuple


class JieqiDateDivergence(NamedTuple):
  '''
  One whitelisted divergence: celestial's UTC+08:00 moment (truncated to whole seconds,
  as stored in `jieqi_moments.txt`) falls on a different civil date than the HKO
  almanac's published date for the same (year, jieqi).

  All entries are midnight-adjacent date flips: |celestial date - HKO date| == 1 day.
  '''
  year:             int
  jq_idx:           int  # bazi `list(Jieqi)` index (0 = 立春 .. 23 = 大寒).
  name:             str  # Redundant with `jq_idx`, same as the table itself.
  celestial_moment: datetime # UTC+08:00, truncated to whole seconds.
  hko_date:         date
  attribution:      str

  @property
  def is_jie(self) -> bool:
    '''Even `jq_idx` = 节 (month boundary, propagates into ganzhi-calendar methods); odd = 气.'''
    return self.jq_idx % 2 == 0


# Exactly 7 divergences in the whole 1901..2100 window (4800 rows).
# The 1912..1928 cluster is pre-1972 UT1-proxy / early-epoch ΔT model noise; the two
# directions do not share one sign (1912/1913 flip one way, 1917/1927/1928 the other), so no
# single constant correction explains the whole set -- per-entry attribution only. The two 节
# among them do have a candidate mechanism of their own; see their attributions.
JIEQI_DATE_DIVERGENCES: Final[tuple[JieqiDateDivergence, ...]] = (
  JieqiDateDivergence(
    year=1912, jq_idx=19, name='小雪',
    celestial_moment=datetime(1912, 11, 22, 23, 48, 13),
    hko_date=date(1912, 11, 23),
    attribution=(
      '气. 11m47s before midnight, celestial one day earlier than HKO. '
      'Pre-1972 UT1 is a proxy (celestial Phase C convention); early-epoch ΔT '
      'model noise tips the moment across the date line.'
    ),
  ),
  JieqiDateDivergence(
    year=1913, jq_idx=15, name='秋分',
    celestial_moment=datetime(1913, 9, 23, 23, 52, 48),
    hko_date=date(1913, 9, 24),
    attribution=(
      '气. 7m12s before midnight, celestial one day earlier than HKO. '
      'Same class as 1912 小雪: pre-1972 UT1 proxy / early-epoch ΔT noise.'
    ),
  ),
  JieqiDateDivergence(
    year=1917, jq_idx=20, name='大雪',
    celestial_moment=datetime(1917, 12, 8, 0, 1, 5),
    hko_date=date(1917, 12, 7),
    attribution=(
      '节 (month boundary -- propagates into ganzhi-calendar methods). 65s after midnight, '
      'celestial one day LATER than HKO. Candidate mechanism (issue #69 appendix): China '
      'adopted the 120°E standard time in 1929; before that the almanac was computed in '
      'Beijing local mean time, UTC+7:45:40, which is 14m20s earlier -- enough to move a '
      'moment this close to midnight onto the previous date, which is what HKO publishes. '
      'Hypothesis not closed: of the 5 pre-1929 节 inside that 14m20s window, HKO matches '
      'local mean time on only this one and 1927 白露, and 120°E on the other three, so its '
      'own convention is inconsistent. Sign differs from 1912/1913, so this is not a single '
      'offset applied throughout.'
    ),
  ),
  JieqiDateDivergence(
    year=1927, jq_idx=14, name='白露',
    celestial_moment=datetime(1927, 9, 9, 0, 5, 30),
    hko_date=date(1927, 9, 8),
    attribution=(
      '节 (month boundary -- propagates into ganzhi-calendar methods). 5m30s after midnight, '
      'celestial one day later than HKO. Same candidate mechanism as 1917 大雪: pre-1929 '
      'Beijing local mean time (UTC+7:45:40) would place it on 09-08, which is HKO\'s date. '
      'The two 节 in this whitelist are exactly the two the mechanism accounts for.'
    ),
  ),
  JieqiDateDivergence(
    year=1928, jq_idx=9, name='夏至',
    celestial_moment=datetime(1928, 6, 22, 0, 6, 27),
    hko_date=date(1928, 6, 21),
    attribution=(
      '气. 6m27s after midnight, celestial one day later than HKO. '
      'Same early-epoch ΔT noise class.'
    ),
  ),
  JieqiDateDivergence(
    year=1979, jq_idx=23, name='大寒',
    celestial_moment=datetime(1979, 1, 20, 23, 59, 56),
    hko_date=date(1979, 1, 21),
    attribution=(
      '气. 4s before midnight -- the closest call in the window (SCHEMA.md '
      'timescale_caveat). Post-1972 UT1-UTC is bounded by 0.9s and truncation '
      'costs at most 1s; sub-second timescale noise decides this date.'
    ),
  ),
  JieqiDateDivergence(
    year=2084, jq_idx=3, name='春分',
    celestial_moment=datetime(2084, 3, 20, 0, 0, 30),
    hko_date=date(2084, 3, 19),
    attribution=(
      '气. 30s after midnight, celestial one day later than HKO. '
      'Future-epoch ΔT projection uncertainty.'
    ),
  ),
)

# The lunar years where algo2 disagrees with HKO (and therefore with algo1, which
# matches HKO 199/199) on `first_solar_date` / `leap_month` / `days_counts`.
# Matches celestial `src/test/lunar/diff_test.cpp`; independently reproduced against HkoData.
ALGO2_DIVERGENT_YEARS: Final[tuple[int, ...]] = (1914, 1915, 1916, 1920, 2057, 2097)
