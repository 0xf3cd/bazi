# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import random
import copy

import pytest

from itertools import product
from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Final

from src.calendar import JieqiTime
from src.defines import Tiangan, Dizhi, Ganzhi, Jieqi
from src.bazi import BaziGender, BaziPrecision, Bazi, 八字
from src.school import DayRollover, BaziSchool, BaziConfig
from src.calendar import CalendarBackend, calendar_utils_of


def test_bazi_gender_basic() -> None:
  assert len(BaziGender) == 2

  assert BaziGender.YANG is BaziGender.MALE
  assert BaziGender.YANG is BaziGender.男
  assert BaziGender.YANG is BaziGender.阳
  assert BaziGender.YANG is BaziGender.乾

  assert BaziGender.YIN is BaziGender.FEMALE
  assert BaziGender.YIN is BaziGender.女
  assert BaziGender.YIN is BaziGender.阴
  assert BaziGender.YIN is BaziGender.坤


def test_str() -> None:
  assert str(BaziGender.YANG) == 'male'
  assert str(BaziGender.YIN) == 'female'
  assert BaziGender.YANG is BaziGender('男')
  assert BaziGender.YIN is BaziGender('女')


def test_bazi_precision_basic() -> None:
  assert len(BaziPrecision) == 3

  assert str(BaziPrecision.DAY) == 'day'
  assert str(BaziPrecision.HOUR) == 'hour'
  assert str(BaziPrecision.MINUTE) == 'minute'


@pytest.mark.parametrize('backend', ('hko', 'celestial'))
@pytest.mark.parametrize('moment, year_pillar, month_dizhi', [
  # 立春 2000 is 02-04 20:40:23 (celestial); the HKO almanac publishes 02-04.  So every
  # moment of 02-04 gives 庚辰/寅 -- including 00:00, which precedes the jieqi by 20 hours.
  ('2000-02-03 12:00', '己卯', Dizhi.丑),
  ('2000-02-04 00:00', '庚辰', Dizhi.寅), # 20h40m before the jieqi, still the new pillar.
  ('2000-02-04 20:40', '庚辰', Dizhi.寅),
  ('2000-02-04 23:59', '庚辰', Dizhi.寅),
])
def test_day_precision_compares_dates_not_moments(backend: str, moment: str, year_pillar: str, month_dizhi: Dizhi) -> None:
  '''
  `DAY` compares dates, so the whole of a jieqi's day falls on the new side of it -- the tie
  at day granularity resolves to the new pillar, as `BaziPrecision` documents.

  Pinned because nothing else would notice it changing. The behaviour rests on `datetime`
  being a `date` subclass, so `to_ganzhi` accepts it and drops the time; anyone "fixing" that
  to honour the moment would silently move ~1.6% of charts, which is exactly how the question
  stayed open long enough to become issue #72. Changing the rule should mean deleting this
  test on purpose.
  '''
  bazi: Bazi = Bazi.create(moment, 'male', BaziConfig.from_values(backend=backend))
  assert str(bazi.year_pillar) == year_pillar
  assert bazi.month_commander == month_dizhi


def test_day_precision_bracketing_jies_stay_moment_level() -> None:
  '''
  The bracketing half of the DAY trade-off (`Bazi.bracketing_jies` docstring): on a jieqi's
  day the pillars compare dates -- the whole day falls on the new side -- while
  `bracketing_jies` keeps the moment-level `prev_jie` / `next_jie`, so before the jie's true
  moment the birth is still owned by the OLD jie. `BaziChart`'s dayun counting consumes
  `bracketing_jies`, so the two readings legitimately disagree -- this is the pin
  `Bazi.bracketing_jies`' docstring points at.
  '''
  # 立春 2000 = 02-04 20:40:23; midnight precedes the true moment by 20h40m...
  bazi: Bazi = Bazi.create('2000-02-04 00:00', 'male')
  # ...yet the pillars already read the new year and month (day-level attribution).
  assert str(bazi.year_pillar) == '庚辰'
  assert str(bazi.month_pillar) == '戊寅'
  # The bracketing jies stay moment-level: the old 小寒 still owns the birth.
  owning, following = bazi.bracketing_jies
  assert owning == JieqiTime(Jieqi.小寒, datetime(2000, 1, 6, 9, 0, 41))
  assert following == JieqiTime(Jieqi.立春, datetime(2000, 2, 4, 20, 40, 23))
  assert following.moment > bazi.solar_datetime


@pytest.mark.parametrize('moment, year, month, day', [
  # 1984-02-04 is the 立春 date, so the year/month pillars turn over between these rows while
  # the day pillar turns over an hour earlier, at 23:00.
  ('1984-02-03 22:30', '癸亥', '乙丑', '丁卯'),
  ('1984-02-03 23:30', '癸亥', '乙丑', '戊辰'), # Day pillar already rolled, year/month not.
  ('1984-02-04 00:30', '甲子', '丙寅', '戊辰'), # Year/month rolled, day pillar unchanged.
])
def test_the_23_oclock_rollover_moves_only_the_day_pillar(moment: str, year: str, month: str, day: str) -> None:
  '''
  晚子时换日 moves the day pillar to the next day, while the year and month pillars keep
  comparing dates -- so a 23:30 birth carries the next day's day pillar and the current
  date's year/month pillars. Both halves are 流派 variants tracked in issue #69; this pins
  which answer is today's default, so that making it configurable is a deliberate carry-over
  rather than whatever the code happened to do.
  '''
  bazi: Bazi = Bazi.create(moment, 'male')
  assert str(bazi.year_pillar) == year
  assert str(bazi.month_pillar) == month
  assert str(bazi.day_pillar) == day


# 换日点 variants (issue #69): `DayRollover` mounted on `BaziSchool.day_rollover`.
@pytest.mark.parametrize('rollover, day_pillar, hour_pillar', [
  (DayRollover.WAN_ZISHI, '己未', '甲子'), # 晚子时 (the default): rolled at 23:00; 己日 -> 甲子时.
  (DayRollover.ZIZHENG,   '戊午', '壬子'), # 子正: the civil day's pillar; 戊日 -> 壬子时.
])
def test_day_rollover_variant_at_23_oclock(rollover: DayRollover, day_pillar: str, hour_pillar: str) -> None:
  '''
  A 23:30 birth at DAY precision: WAN_ZISHI (晚子时, the default) moves the day pillar to
  the next day, ZIZHENG (子正) keeps the civil day's. The hour dizhi is 子 either way, but
  the hour tiangan follows the day tiangan via 五鼠遁 (己日 -> 甲子, 戊日 -> 壬子), so the
  full hour pillar splits with the variant too. The year and month pillars do NOT follow
  this knob -- they are `BaziPrecision`'s attribution (see `DayRollover`'s docstring).
  '''
  config: BaziConfig = BaziConfig(school=BaziSchool(day_rollover=rollover))
  bazi: Bazi = Bazi.create('2000-01-01 23:30', 'male', config)
  assert str(bazi.year_pillar) == '己卯'
  assert str(bazi.month_pillar) == '丙子'
  assert str(bazi.day_pillar) == day_pillar
  assert str(bazi.hour_pillar) == hour_pillar

  # The default school is WAN_ZISHI -- the long-pinned behavior carries over unchanged.
  if rollover is DayRollover.WAN_ZISHI:
    assert Bazi.create('2000-01-01 23:30', 'male').day_pillar == bazi.day_pillar


# Brief-v2 P2-5 golden: 换日点 variant inside a jieqi tie window (cross-midnight 子时).
@pytest.mark.parametrize('rollover, pillars', [
  (DayRollover.WAN_ZISHI, ('己丑', '丙寅', '庚辰', '丙子')), # 晚子时: day rolled; 庚日 -> 丙子时.
  (DayRollover.ZIZHENG,   ('己丑', '丙寅', '己卯', '甲子')), # 子正: civil day kept; 己日 -> 甲子时.
])
def test_day_rollover_variant_inside_a_jieqi_tie_window(rollover: DayRollover, pillars: tuple[str, str, str, str]) -> None:
  '''
  立春 2009 = 02-04 00:49:48, inside the 子时 that began at 02-03 23:00, so a HOUR birth at
  2009-02-03 23:30 ties and the year/month pillars already read the new side -- under BOTH
  variants. 换日点 only splits the day pillar (and with it the hour tiangan via 五鼠遁);
  it never moves the year/month attribution, which is `BaziPrecision`'s own rule. This pins
  that 子正 does NOT mean "the whole 子时 keeps the old year and month too".
  '''
  config: BaziConfig = BaziConfig(precision=BaziPrecision.HOUR, school=BaziSchool(day_rollover=rollover))
  bazi: Bazi = Bazi.create('2009-02-03 23:30', 'male', config)
  assert (str(bazi.year_pillar), str(bazi.month_pillar),
          str(bazi.day_pillar), str(bazi.hour_pillar)) == pillars


# HOUR / MINUTE precisions (issue #6): `birth >= jieqi` compared at the known granularity,
# ties go new. The reference rule text is the `BaziPrecision` docstring.


# The jie owning a birth month opens it: 立春 opens 寅月, and so on. Written out as data
# (not derived from enum order) so the tests share no derivation with `src.Bazi`.
JIE_MONTH_DIZHI: Final[dict[Jieqi, Dizhi]] = {
  Jieqi.立春 : Dizhi.寅,  Jieqi.惊蛰 : Dizhi.卯,  Jieqi.清明 : Dizhi.辰,
  Jieqi.立夏 : Dizhi.巳,  Jieqi.芒种 : Dizhi.午,  Jieqi.小暑 : Dizhi.未,
  Jieqi.立秋 : Dizhi.申,  Jieqi.白露 : Dizhi.酉,  Jieqi.寒露 : Dizhi.戌,
  Jieqi.立冬 : Dizhi.亥,  Jieqi.大雪 : Dizhi.子,  Jieqi.小寒 : Dizhi.丑,
}


def _truncated(dt: datetime, precision: BaziPrecision) -> datetime:
  '''
  Independent re-statement of the granularity truncation, for oracle use. HOUR scans the
  时辰 boundaries (the odd clock hours, plus the previous day's 23:00) and takes the latest
  one at or before `dt` -- deliberately NOT the shift-floor-shift formula `src.Bazi` uses,
  so the oracle and the implementation cannot share a truncation error.
  '''
  if precision is BaziPrecision.MINUTE:
    return dt.replace(second=0, microsecond=0)
  assert precision is BaziPrecision.HOUR
  boundaries: list[datetime] = [datetime.combine(dt.date() - timedelta(days=1), time(23))]
  boundaries += [datetime.combine(dt.date(), time(h)) for h in range(1, 24, 2)]
  return max(b for b in boundaries if b <= dt)


@pytest.mark.parametrize('moment, precision, year_pillar, month_dizhi', [
  ('2000-02-04 19:30', 'hour',   '庚辰', Dizhi.寅), # 戌时 [19:00, 21:00) holds the jieqi: tie -> new.
  ('2000-02-04 20:59', 'hour',   '庚辰', Dizhi.寅),
  ('2000-02-04 18:59', 'hour',   '己卯', Dizhi.丑), # 酉时: before the jieqi's 时辰 -> old.
  ('2000-02-04 20:40', 'minute', '庚辰', Dizhi.寅), # Same minute as the jieqi: tie -> new.
  ('2000-02-04 20:41', 'minute', '庚辰', Dizhi.寅),
  ('2000-02-04 20:39', 'minute', '己卯', Dizhi.丑),
  ('2000-02-05 04:00', 'hour',   '庚辰', Dizhi.寅), # Plain interior moments, both sides.
  ('2000-02-03 12:00', 'minute', '己卯', Dizhi.丑),

  ('2017-02-03 23:10', 'hour',   '丁酉', Dizhi.寅), # 子时 starts 23:00, holds 立春 23:34:03: tie.
  ('2017-02-04 00:30', 'hour',   '丁酉', Dizhi.寅), # Still the same 子时, next civil day.
  ('2017-02-03 22:30', 'hour',   '丙申', Dizhi.丑), # 亥时 -> old, on a day DAY assigns new.
  ('2017-02-03 23:10', 'minute', '丙申', Dizhi.丑), # At minute granularity 23:10 < 23:34.
  ('2017-02-03 23:34', 'minute', '丁酉', Dizhi.寅),

  ('2009-02-03 23:30', 'hour',   '己丑', Dizhi.寅), # Cross-midnight tie: 立春 02-04 00:49:48.
  ('2009-02-04 00:30', 'hour',   '己丑', Dizhi.寅), # The tie seen from the jieqi's own day.
  ('2009-02-03 22:59', 'hour',   '戊子', Dizhi.丑), # 亥时, right before the tie window opens.
  ('2009-02-04 00:49', 'minute', '己丑', Dizhi.寅),
  ('2009-02-04 00:48', 'minute', '戊子', Dizhi.丑),
  ('2009-01-10 12:00', 'minute', '戊子', Dizhi.丑), # 丑月 interior: owned by 小寒 of 2009.
])
def test_goldens_from_the_docstring(moment: str, precision: str, year_pillar: str, month_dizhi: Dizhi) -> None:
  '''
  The `BaziPrecision` docstring's worked examples, pinned:
  - 立春 2000 = 02-04 20:40:23 -- the same-day 时辰 tie (戌时) and the minute tie.
  - 立春 2017 = 02-03 23:34:03 -- the tie 时辰 (子时) starts at 23:00 of the jieqi's own day.
  - 立春 2009 = 02-04 00:49:48 -- the tie 时辰 starts on the PREVIOUS civil day, so HOUR
    attributes a 02-03 23:30 birth to the new year on a day DAY assigns to the old side.
    The granularities are three readings of one rule, not nested refinements.
  '''
  bazi: Bazi = Bazi.create(moment, 'male', BaziConfig.from_values(precision=precision))
  assert str(bazi.year_pillar) == year_pillar
  assert bazi.month_commander == month_dizhi


def test_day_and_hour_pillars_ignore_precision() -> None:
  '''Precision only moves the year/month attribution; the day/hour pillars must not move.'''
  moments: list[str] = ['2009-02-03 23:30', '2017-02-03 23:10', '2000-02-04 20:39', '1984-02-04 12:30']
  for moment in moments:
    day_bazi: Bazi = Bazi.create(moment, 'female')
    for precision in ('hour', 'minute'):
      bazi: Bazi = Bazi.create(moment, 'female', BaziConfig.from_values(precision=precision))
      assert bazi.day_pillar == day_bazi.day_pillar
      assert bazi.hour_pillar == day_bazi.hour_pillar


def test_hko_backend_rejected() -> None:
  '''HOUR / MINUTE need real jieqi moments; the HKO backend's are midnight placeholders.'''
  for precision in (BaziPrecision.HOUR, BaziPrecision.MINUTE):
    with pytest.raises(ValueError):
      Bazi(datetime(2000, 2, 4, 19, 30), BaziGender.MALE, BaziConfig(precision=precision, backend=CalendarBackend.HKO))
  assert str(Bazi.create('2000-02-04 19:30', 'male', BaziConfig.from_values(backend='hko')).year_pillar) == '庚辰'


def test_ganzhi_year_and_bracketing_jies_are_the_attribution() -> None:
  '''`ganzhi_year` / `bracketing_jies` expose exactly what the pillars were derived from.'''
  bazi: Bazi = Bazi.create('2009-02-04 00:30', 'male', BaziConfig.from_values(precision='hour'))
  assert bazi.ganzhi_year == 2009
  owning, following = bazi.bracketing_jies
  assert owning == JieqiTime(Jieqi.立春, datetime(2009, 2, 4, 0, 49, 48))
  assert following.jieqi == Jieqi.惊蛰
  # The owning jie's true moment lies AFTER the birth -- that is what a tie looks like.
  assert owning.moment > bazi.solar_datetime
  # `ganzhi_date` stays a day-level channel: on the jieqi's own day the two channels agree
  # (DAY gives the whole day to the new side), but for the cross-midnight tie birth on the
  # PREVIOUS day they legitimately disagree.
  assert bazi.ganzhi_date.year == 2009
  advance: Bazi = Bazi.create('2009-02-03 23:30', 'male', BaziConfig.from_values(precision='hour'))
  assert advance.ganzhi_year == 2009
  assert advance.ganzhi_date.year == 2008


@pytest.mark.slow
def test_attribution_matches_scan_oracle() -> None:
  '''
  Independent oracle, two derivations compared:
  - Year: compare the truncated birth against the truncated 立春 of its solar year directly.
  - Month: linearly scan all nearby Jies and take the LAST one whose truncated moment is
    <= the truncated birth (ties go new), then map it to a month via literal data.
  The scan shares none of `Bazi.__init__`'s bracketing/tie-flip shortcut, so a bug in
  either derivation shows up as a mismatch.

  Also pins the divergence-from-DAY shape: a finer granularity may disagree with DAY only
  around a jie's own day -- retreating (jieqi-day birth before the jie's truncated moment)
  or advancing (previous-day 晚子时 birth tying a 00:xx jie across midnight). Both windows
  are sampled densely by biasing half the moments to fall near a jie.
  '''
  utils = calendar_utils_of(CalendarBackend.CELESTIAL)
  rng = random.Random(6) # Deterministic sampling; seeded with the issue number.

  all_jies: list[Jieqi] = Jieqi.as_list(ganzhi_year=False)[::2]

  def __random_moment() -> datetime:
    uniform: datetime = datetime(
      rng.randint(1902, 2080), rng.randint(1, 12), rng.randint(1, 28),
      rng.randint(0, 23), rng.randint(0, 59),
    )
    if rng.random() < 0.5:
      return uniform
    # Bias near a jie so tie windows (rare under uniform sampling) are exercised densely.
    jie_moment: datetime = utils.jieqi_moment(uniform.year, rng.choice(all_jies))
    biased: datetime = jie_moment + timedelta(minutes=rng.randint(-180, 180))
    return biased.replace(second=0, microsecond=0)

  total: int = 30_000
  divergent: int = 0
  for _ in range(total):
    birth: datetime = __random_moment()
    day_bazi: Bazi = Bazi(birth, BaziGender.女)

    candidates: list[JieqiTime] = sorted(
      (JieqiTime(jie, utils.jieqi_moment(year, jie))
       for year in (birth.year - 1, birth.year) for jie in all_jies),
      key=lambda jt: jt.moment,
    )

    for precision in (BaziPrecision.HOUR, BaziPrecision.MINUTE):
      bazi: Bazi = Bazi(birth, BaziGender.女, BaziConfig(precision=precision))

      trunc_birth: datetime = _truncated(birth, precision)
      lichun: datetime = utils.jieqi_moment(birth.year, Jieqi.立春)
      expected_year: int = birth.year if trunc_birth >= _truncated(lichun, precision) else birth.year - 1
      assert bazi.ganzhi_year == expected_year

      owning: JieqiTime = max(
        (jt for jt in candidates if _truncated(jt.moment, precision) <= trunc_birth),
        key=lambda jt: jt.moment,
      )
      assert bazi.month_commander == JIE_MONTH_DIZHI[owning.jieqi]

      # Divergence-from-DAY shape: only inside a tie window around a jie's own day.
      if (bazi.year_pillar, bazi.month_commander) != (day_bazi.year_pillar, day_bazi.month_commander):
        divergent += 1
        day_owning: JieqiTime = max(
          (jt for jt in candidates if jt.moment.date() <= birth.date()),
          key=lambda jt: jt.moment,
        )
        if owning.moment > day_owning.moment:  # Advance: cross-midnight 晚子时 tie.
          assert precision is BaziPrecision.HOUR
          assert _truncated(owning.moment, precision) == trunc_birth
          assert birth.date() < owning.moment.date()
        else:                                  # Retreat: jieqi-day birth before the moment.
          assert birth.date() == day_owning.moment.date()
          assert trunc_birth < _truncated(day_owning.moment, precision)

  # The biased sampling must actually have exercised the divergence windows.
  assert divergent > 100


def test_minute_vs_moment_level_prev_jie() -> None:
  '''
  MINUTE attribution vs the moment-level `prev_jie`: the two may disagree ONLY at a
  same-minute tie (birth in the same minute as the jieqi but before its true second --
  ties go new, `prev_jie` stays old). At any other moment they must agree, and the
  sampling must actually produce ties -- without the floor assertion, an implementation
  degenerated to pure moment-level `prev_jie` would sail through green.
  '''
  utils = calendar_utils_of(CalendarBackend.CELESTIAL)
  rng = random.Random(72) # Seeded with the issue this rule closes.

  all_jies: list[Jieqi] = Jieqi.as_list(ganzhi_year=False)[::2]
  disagree: int = 0
  for _ in range(2_000):
    jie_moment: datetime = utils.jieqi_moment(rng.randint(1902, 2080), rng.choice(all_jies))
    birth: datetime = (jie_moment + timedelta(seconds=rng.randint(-90, 90))).replace(second=0, microsecond=0)

    bazi: Bazi = Bazi(birth, BaziGender.男, BaziConfig(precision=BaziPrecision.MINUTE))
    moment_owning: JieqiTime = utils.prev_jie(birth)
    attribution_owning: JieqiTime = bazi.bracketing_jies[0]

    if attribution_owning != moment_owning:
      disagree += 1
      next_j: JieqiTime = utils.next_jie(birth)
      assert attribution_owning == next_j
      assert next_j.moment.replace(second=0, microsecond=0) == birth # Same minute.
      assert birth < next_j.moment                                   # Before the true second.
    assert bazi.month_commander == JIE_MONTH_DIZHI[attribution_owning.jieqi]

  assert disagree > 0 # At seed 72 the ties number in the hundreds.


def test_init() -> None:
  for _ in range(128):
    random_dt: datetime = datetime(
      year=random.randint(1950, 2000),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59)
    )

    bazi: Bazi = Bazi(
      birth_time=random_dt,
      gender=BaziGender.男,
    )

    assert bazi.solar_date == date(random_dt.year, random_dt.month, random_dt.day)
    assert bazi.hour == random_dt.hour
    assert bazi.minute == random_dt.minute
    assert bazi.gender == BaziGender.男
    assert bazi.config.precision == BaziPrecision.DAY


def test_chinese() -> None:
  assert Bazi is 八字

  for _ in range(128):
    random_dt: datetime = datetime(
      year=random.randint(1950, 2000),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59)
    )

    bazi: 八字 = 八字(
      birth_time=random_dt,
      gender=BaziGender.男,
    )

    assert bazi.solar_date == date(random_dt.year, random_dt.month, random_dt.day)
    assert bazi.hour == random_dt.hour
    assert bazi.minute == random_dt.minute
    assert bazi.gender == BaziGender.男
    assert bazi.config.precision == BaziPrecision.DAY


def test_invalid_arguments() -> None:
  random_dt: datetime = datetime(
    year=random.randint(1950, 2000),
    month=random.randint(1, 12),
    day=random.randint(1, 28),
    hour=random.randint(0, 23),
    minute=random.randint(0, 59),
    second=random.randint(0, 59)
  )

  with pytest.raises(TypeError):
    Bazi(birth_time=random_dt, gender=BaziGender.男, config='day') # type: ignore # `__init__` only takes `BaziConfig`, not str.
  with pytest.raises(TypeError):
    Bazi(birth_time=random_dt) # type: ignore # Missing `gender`
  with pytest.raises(TypeError):
    Bazi(birth_time='2024-03-03', gender=BaziGender.男) # type: ignore # Currently doesn't take string as input
  with pytest.raises(TypeError):
    Bazi(birth_time=date(9999, 1, 1), gender=BaziGender.男) # type: ignore
  with pytest.raises(TypeError):
    Bazi(birth_time=random_dt, gender='男') # type: ignore # `__init__` only takes the enum.
  with pytest.raises(TypeError):
    Bazi(birth_time=random_dt, gender=BaziGender.男, config=BaziPrecision.DAY) # type: ignore # `__init__` only takes `BaziConfig`.
  with pytest.raises(ValueError):
    dt: datetime = datetime(
      year=9999, # Out of supported range.
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59)
    )
    Bazi(birth_time=dt, gender=BaziGender.男)
  with pytest.raises(ValueError):
    Bazi(
      birth_time=datetime(
        year=2000,
        month=1,
        day=1,
        hour=7,
        minute=0,
        second=0,
        tzinfo=ZoneInfo('Asia/Shanghai') # Doesn't support timezone.
      ),
      gender=BaziGender.男,
    )


def _create_bazi(dt: datetime) -> Bazi:
  return Bazi(
    birth_time=dt,
    gender=BaziGender.男,
  )


def test_four_dizhis_correctness() -> None:
  '''
  Test the correctness of `Bazi` on the given test cases.
  Precision is at `DAY` level.
  '''
  def __check(dt: datetime, dizhi_strs: list[str]) -> None:
    assert len(dizhi_strs) == 4

    bazi = _create_bazi(dt)
    assert bazi.four_dizhis == (
      Dizhi.from_str(dizhi_strs[0]),
      Dizhi.from_str(dizhi_strs[1]),
      Dizhi.from_str(dizhi_strs[2]),
      Dizhi.from_str(dizhi_strs[3]),
    )

  # Basic cases
  # Data was collected from the "测测" app.
  __check(datetime(2024, 2, 6, 11, 55), ['辰', '寅', '子', '午'])
  __check(datetime(1984, 4, 2, 4, 2), ['子', '卯', '寅', '寅'])

  __check(datetime(1998, 3, 17, 13, 0), ['寅', '卯', '亥', '未'])
  __check(datetime(1998, 3, 17, 13, 59), ['寅', '卯', '亥', '未'])
  __check(datetime(1998, 3, 17, 14, 0), ['寅', '卯', '亥', '未'])
  __check(datetime(1998, 3, 17, 14, 59), ['寅', '卯', '亥', '未'])
  __check(datetime(1998, 3, 17, 15, 0), ['寅', '卯', '亥', '申'])
  __check(datetime(1998, 3, 17, 23, 0), ['寅', '卯', '子', '子'])
  __check(datetime(1998, 3, 18, 0, 59), ['寅', '卯', '子', '子'])
  __check(datetime(1998, 3, 18, 1, 0), ['寅', '卯', '子', '丑'])

  # Edge cases
  __check(datetime(2000, 2, 3, 0, 0), ['卯', '丑', '卯', '子'])
  __check(datetime(2000, 2, 3, 22, 59), ['卯', '丑', '卯', '亥'])
  __check(datetime(2000, 2, 3, 23, 0), ['卯', '丑', '辰', '子'])
  __check(datetime(2000, 2, 4, 0, 0), ['辰', '寅', '辰', '子'])
  __check(datetime(2000, 2, 4, 1, 0), ['辰', '寅', '辰', '丑'])


def test_four_tiangans_correctness() -> None:
  def __check(dt: datetime, tiangan_strs: list[str]) -> None:
    assert len(tiangan_strs) == 4

    bazi = _create_bazi(dt)
    assert bazi.four_tiangans == (
      Tiangan.from_str(tiangan_strs[0]),
      Tiangan.from_str(tiangan_strs[1]),
      Tiangan.from_str(tiangan_strs[2]),
      Tiangan.from_str(tiangan_strs[3]),
    )

  __check(datetime(1984, 4, 2, 4, 2), ['甲', '丁', '丙', '庚'])
  __check(datetime(2000, 2, 4, 22, 1), ['庚', '戊', '壬', '辛'])
  __check(datetime(2001, 10, 20, 19, 0), ['辛', '戊', '丙', '戊'])


def test_ganzhi_date() -> None:
  # The oracle must follow the chart's own backend: `ganzhi_date` is the day-level label
  # through `Bazi`'s resolved calendar utils. The two backends legitimately diverge inside
  # the 1917/1927 jieqi-shift windows (pinned by the parity whitelist), so an oracle bound
  # to the wrong backend false-reds there -- the #114 CI failure was exactly that.
  bazi: Bazi = _create_bazi(datetime(1984, 4, 2, 4, 2))
  assert bazi.ganzhi_date == calendar_utils_of(bazi.config.backend).to_ganzhi(date(1984, 4, 2))

  for _ in range(10):
    bazi = Bazi.random()
    assert bazi.ganzhi_date == calendar_utils_of(bazi.config.backend).to_ganzhi(bazi.solar_date)


def test_date_time() -> None:
  bazi: Bazi = _create_bazi(datetime(1984, 4, 2, 4, 2))
  assert bazi.solar_date == date(1984, 4, 2)
  assert bazi.hour == 4
  assert bazi.minute == 2
  assert bazi.solar_datetime == datetime(1984, 4, 2, 4, 2)

  random_bazi: Bazi = Bazi.random()
  with pytest.raises(AttributeError):
    random_bazi.solar_date = date(1984, 4, 3) # type: ignore
  with pytest.raises(AttributeError):
    random_bazi.hour = 9 # type: ignore
  with pytest.raises(AttributeError):
    random_bazi.minute = 8 # type: ignore
  with pytest.raises(AttributeError):
    random_bazi.solar_datetime = datetime(1984, 4, 3, 9, 8) # type: ignore


def test_pillars() -> None:
  def __check(dt: datetime, ganzhi_strs: list[str]) -> None:
    assert len(ganzhi_strs) == 4

    bazi = _create_bazi(dt)
    pillars: list[Ganzhi] = list(bazi.pillars)
    assert pillars[0] == Ganzhi.from_str(ganzhi_strs[0])
    assert pillars[1] == Ganzhi.from_str(ganzhi_strs[1])
    assert pillars[2] == Ganzhi.from_str(ganzhi_strs[2])
    assert pillars[3] == Ganzhi.from_str(ganzhi_strs[3])

  __check(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
  __check(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
  __check(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])


def test_consistency() -> None:
  def __check(dt: datetime, ganzhi_strs: list[str]) -> None:
    assert len(ganzhi_strs) == 4

    bazi = _create_bazi(dt)
    pillars: list[Ganzhi] = list(bazi.pillars)

    assert bazi.day_master == pillars[2].tiangan
    assert bazi.month_commander == pillars[1].dizhi

    assert bazi.year_pillar == pillars[0]
    assert bazi.month_pillar == pillars[1]
    assert bazi.day_pillar == pillars[2]
    assert bazi.hour_pillar == pillars[3]

    assert bazi.four_tiangans == tuple([tg for tg, _ in pillars])
    assert bazi.four_dizhis == tuple([dz for _, dz in pillars])

  __check(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
  __check(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
  __check(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])


def test_deepcopy() -> None:
  bazi: Bazi = Bazi(
    birth_time=datetime(1984, 4, 2, 4, 2),
    gender=BaziGender.男,
  )
  bazi2: Bazi = copy.deepcopy(bazi)

  assert bazi._solar_date is not bazi2._solar_date
  assert bazi._year_pillar is not bazi2._year_pillar

  assert bazi._day_pillar is not bazi2._day_pillar
  assert bazi._day_pillar == bazi2._day_pillar

  cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
  next_day_pillar: Ganzhi = cycle[(cycle.index(bazi._day_pillar) + 1) % len(cycle)]
  bazi._day_pillar = next_day_pillar # type: ignore
  assert bazi._day_pillar != bazi2._day_pillar


def test_create() -> None:
  with pytest.raises(ValueError):
    Bazi.create('WrongDatetimeFormat', BaziGender.FEMALE)
  with pytest.raises(ValueError):
    Bazi.create(datetime.now(), 'femal')
  with pytest.raises(ValueError):
    Bazi.create(datetime.now(), BaziGender.FEMALE, BaziConfig.from_values(precision='dya'))

  with pytest.raises(TypeError):
    Bazi.create(19840402, BaziGender.FEMALE) # type: ignore
  with pytest.raises(TypeError):
    Bazi.create(datetime.now(), 1984) # type: ignore
  with pytest.raises(TypeError):
    Bazi.create(datetime.now(), BaziGender.FEMALE, BaziConfig.from_values(precision=1984)) # type: ignore
  with pytest.raises(TypeError):
    Bazi.create(datetime.now(), BaziGender.FEMALE, 'day') # type: ignore # `create` takes `BaziConfig`, not str.

  # Create a datetime and set its timezone to Asia/Shanghai.
  _dt: datetime = datetime.now()
  _dt = _dt.replace(tzinfo=ZoneInfo('Asia/Shanghai'))
  with pytest.raises(ValueError):
    Bazi.create(_dt, BaziGender.FEMALE)
  with pytest.raises(ValueError):
    Bazi.create(_dt.isoformat(), BaziGender.FEMALE)

  now: datetime = datetime.now()
  dt_options: list[str | datetime] = [now, now.isoformat()]
  male_options: list[str | BaziGender] = [BaziGender.男, BaziGender.YANG, BaziGender.阳, 'Male', '男', 'MALE']
  female_options: list[str | BaziGender] = [BaziGender.YIN, BaziGender.FEMALE, '女', 'FEMALE', 'female']
  day_precision_options: list[str | BaziPrecision] = [BaziPrecision.DAY, 'day', 'DAY', 'Day', '日', '天', 'd', 'D']

  expected_bazi: Bazi = Bazi.create(now, BaziGender.FEMALE)
  for dt, g, p in product(dt_options, female_options, day_precision_options):
    bazi = Bazi.create(dt, g, BaziConfig.from_values(precision=p))
    assert list(bazi.pillars) == list(expected_bazi.pillars)
    assert bazi.gender == expected_bazi.gender
    assert bazi.config.precision == expected_bazi.config.precision
    assert bazi.solar_date == expected_bazi.solar_date
    assert bazi.hour == expected_bazi.hour
    assert bazi.minute == expected_bazi.minute

  expected_bazi = Bazi.create(now, BaziGender.MALE)
  for dt, g, p in product(dt_options, male_options, day_precision_options):
    bazi = Bazi.create(dt, g, BaziConfig.from_values(precision=p))
    assert list(bazi.pillars) == list(expected_bazi.pillars)
    assert bazi.gender == expected_bazi.gender
    assert bazi.config.precision == expected_bazi.config.precision
    assert bazi.solar_date == expected_bazi.solar_date
    assert bazi.hour == expected_bazi.hour
    assert bazi.minute == expected_bazi.minute

  finer_precision_options: list = [BaziPrecision.HOUR, BaziPrecision.MINUTE, 'hour', 'minute', 'H', 'm', '时', '小时', '分', '分钟']
  for dt, g, p in product(dt_options, male_options + female_options, finer_precision_options):
    bazi = Bazi.create(dt, g, BaziConfig.from_values(precision=p)) # Supported since issue #6 -- on the celestial backend only.
    assert bazi.config.precision in (BaziPrecision.HOUR, BaziPrecision.MINUTE)
    with pytest.raises(ValueError):
      Bazi.create(dt, g, BaziConfig.from_values(precision=p, backend='hko')) # HKO has no real jieqi moments.


def test_supported_date_window_edges() -> None:
  '''
  The supported date window, pinned as a `Bazi`-level contract: one day outside either
  edge raises (the calendar funnel validates the converted date), the edges themselves
  construct. The window itself is the celestial backend's, pinned in its own tests.
  '''
  with pytest.raises(ValueError):
    Bazi.create(datetime(1901, 2, 18, 12), 'male')
  with pytest.raises(ValueError):
    Bazi.create(datetime(2100, 1, 1, 12), 'male')
  assert Bazi.create(datetime(1901, 2, 19, 12), 'male').solar_date == date(1901, 2, 19)
  assert Bazi.create(datetime(2099, 12, 31, 12), 'male').solar_date == date(2099, 12, 31)


def test_eq_ne() -> None:
  def __random_info() -> tuple[datetime, BaziGender]:
    return (datetime(
      year=random.randint(1950, 2000),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59)
    ), random.choice(list(BaziGender)))

  def __toggle_gender(g: BaziGender) -> BaziGender:
    return BaziGender.MALE if g is BaziGender.FEMALE else BaziGender.FEMALE

  def __inc_datetime(dt: datetime) -> datetime:
    return dt + timedelta(days=1)

  for _ in range(64):
    dt, gender = __random_info()

    bazi: Bazi = Bazi.create(dt, gender)
    assert bazi == Bazi.create(dt, gender)
    assert bazi != Bazi.create(dt, __toggle_gender(gender))
    assert bazi != Bazi.create(__inc_datetime(dt), gender)

    assert bazi != 0

    bazi_hacked: Bazi = Bazi.create(dt, gender)
    bazi_hacked._config = BaziConfig(precision=BaziPrecision.HOUR) # type: ignore # Intended for testing only.
    assert bazi != bazi_hacked


def test_hash() -> None:
  dt: datetime = datetime(2000, 2, 4, 22, 1)
  bazi: Bazi = Bazi.create(dt, BaziGender.MALE)
  same: Bazi = Bazi.create(dt, BaziGender.MALE)
  assert hash(bazi) == hash(same)
  assert len({bazi, same}) == 1 # In sync with `__eq__`: usable for set dedup.

  other: Bazi = Bazi.create(dt, BaziGender.FEMALE)
  assert len({bazi, same, other}) == 2


def test_sub_minute_truncation() -> None:
  # Two births in the same minute are the same Bazi -- `Bazi.solar_datetime` is the
  # SSOT on why sub-minute parts are dropped.
  dt: datetime = datetime(2000, 2, 4, 22, 1)
  bazi: Bazi = Bazi.create(dt, BaziGender.MALE)
  sub_minute: Bazi = Bazi.create(dt.replace(second=37, microsecond=999999),
                                 BaziGender.MALE)
  assert sub_minute.solar_datetime == dt
  assert sub_minute.hour == 22
  assert sub_minute.minute == 1
  assert bazi == sub_minute
  assert hash(bazi) == hash(sub_minute)
