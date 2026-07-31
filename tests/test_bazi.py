# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_bazi.py

import unittest
import random
import copy

import pytest

from itertools import product
from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Union

from src.Common import JieqiTime
from src.Defines import Tiangan, Dizhi, Ganzhi, Jieqi
from src.Bazi import BaziGender, BaziPrecision, Bazi, 八字
from src.Calendar import HkoDataCalendarUtils, CalendarBackend, calendar_utils_of

class TestBaziGender(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(BaziGender), 2)

    self.assertIs(BaziGender.YANG, BaziGender.MALE)
    self.assertIs(BaziGender.YANG, BaziGender.男)
    self.assertIs(BaziGender.YANG, BaziGender.阳)
    self.assertIs(BaziGender.YANG, BaziGender.乾)

    self.assertIs(BaziGender.YIN, BaziGender.FEMALE)
    self.assertIs(BaziGender.YIN, BaziGender.女)
    self.assertIs(BaziGender.YIN, BaziGender.阴)
    self.assertIs(BaziGender.YIN, BaziGender.坤)

  def test_str(self) -> None:
    self.assertEqual(str(BaziGender.YANG), 'male')
    self.assertEqual(str(BaziGender.YIN), 'female')
    self.assertIs(BaziGender.YANG, BaziGender('男'))
    self.assertIs(BaziGender.YIN, BaziGender('女'))


class TestBaziPrecision(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(BaziPrecision), 3)

    self.assertEqual(str(BaziPrecision.DAY), 'day')
    self.assertEqual(str(BaziPrecision.HOUR), 'hour')
    self.assertEqual(str(BaziPrecision.MINUTE), 'minute')

  def test_day_precision_compares_dates_not_moments(self) -> None:
    '''
    `DAY` compares dates, so the whole of a jieqi's day falls on the new side of it -- the tie
    at day granularity resolves to the new pillar, as `BaziPrecision` documents.

    Pinned because nothing else would notice it changing. The behaviour rests on `datetime`
    being a `date` subclass, so `to_ganzhi` accepts it and drops the time; anyone "fixing" that
    to honour the moment would silently move ~1.6% of charts, which is exactly how the question
    stayed open long enough to become issue #72. Changing the rule should mean deleting this
    test on purpose.
    '''
    # 立春 2000 is 02-04 20:40:23 (celestial); the HKO almanac publishes 02-04.  So every
    # moment of 02-04 gives 庚辰/寅 -- including 00:00, which precedes the jieqi by 20 hours.
    expected: list[tuple[str, str, Dizhi]] = [
      ('2000-02-03 12:00', '己卯', Dizhi.丑),
      ('2000-02-04 00:00', '庚辰', Dizhi.寅), # 20h40m before the jieqi, still the new pillar.
      ('2000-02-04 20:40', '庚辰', Dizhi.寅),
      ('2000-02-04 23:59', '庚辰', Dizhi.寅),
    ]
    for backend in ('hko', 'celestial'):
      for moment, year_pillar, month_dizhi in expected:
        with self.subTest(backend=backend, moment=moment):
          bazi: Bazi = Bazi.create(moment, 'male', 'day', backend=backend)
          self.assertEqual(str(bazi.year_pillar), year_pillar)
          self.assertEqual(bazi.month_commander, month_dizhi)

  def test_the_23_oclock_rollover_moves_only_the_day_pillar(self) -> None:
    '''
    晚子时换日 moves the day pillar to the next day, while the year and month pillars keep
    comparing dates -- so a 23:30 birth carries the next day's day pillar and the current
    date's year/month pillars. Both halves are 流派 variants tracked in issue #69; this pins
    which answer is today's default, so that making it configurable is a deliberate carry-over
    rather than whatever the code happened to do.
    '''
    # 1984-02-04 is the 立春 date, so the year/month pillars turn over between these rows while
    # the day pillar turns over an hour earlier, at 23:00.
    expected: list[tuple[str, str, str, str]] = [
      ('1984-02-03 22:30', '癸亥', '乙丑', '丁卯'),
      ('1984-02-03 23:30', '癸亥', '乙丑', '戊辰'), # Day pillar already rolled, year/month not.
      ('1984-02-04 00:30', '甲子', '丙寅', '戊辰'), # Year/month rolled, day pillar unchanged.
    ]
    for moment, year, month, day in expected:
      with self.subTest(moment=moment):
        bazi: Bazi = Bazi.create(moment, 'male', 'day')
        self.assertEqual(str(bazi.year_pillar), year)
        self.assertEqual(str(bazi.month_pillar), month)
        self.assertEqual(str(bazi.day_pillar), day)


class TestBaziHourMinutePrecisions(unittest.TestCase):
  '''
  HOUR / MINUTE precisions (issue #6): `birth >= jieqi` compared at the known granularity,
  ties go new. The reference rule text is the `BaziPrecision` docstring.
  '''

  # The jie owning a birth month opens it: 立春 opens 寅月, and so on. Written out as data
  # (not derived from enum order) so the tests share no derivation with `src.Bazi`.
  JIE_MONTH_DIZHI: dict[Jieqi, Dizhi] = {
    Jieqi.立春 : Dizhi.寅,  Jieqi.惊蛰 : Dizhi.卯,  Jieqi.清明 : Dizhi.辰,
    Jieqi.立夏 : Dizhi.巳,  Jieqi.芒种 : Dizhi.午,  Jieqi.小暑 : Dizhi.未,
    Jieqi.立秋 : Dizhi.申,  Jieqi.白露 : Dizhi.酉,  Jieqi.寒露 : Dizhi.戌,
    Jieqi.立冬 : Dizhi.亥,  Jieqi.大雪 : Dizhi.子,  Jieqi.小寒 : Dizhi.丑,
  }

  @staticmethod
  def __truncated(dt: datetime, precision: BaziPrecision) -> datetime:
    '''Independent re-statement of the granularity truncation, for oracle use.'''
    if precision is BaziPrecision.MINUTE:
      return dt.replace(second=0, microsecond=0)
    assert precision is BaziPrecision.HOUR
    shifted: datetime = dt + timedelta(hours=1)
    return datetime.combine(shifted.date(), time(shifted.hour - (shifted.hour % 2))) - timedelta(hours=1)

  def test_goldens_from_the_docstring(self) -> None:
    '''
    The `BaziPrecision` docstring's worked examples, pinned:
    - 立春 2000 = 02-04 20:40:23 -- the same-day 时辰 tie (戌时) and the minute tie.
    - 立春 2017 = 02-03 23:34:03 -- the tie 时辰 (子时) starts at 23:00 of the jieqi's own day.
    - 立春 2009 = 02-04 00:49:48 -- the tie 时辰 starts on the PREVIOUS civil day, so HOUR
      attributes a 02-03 23:30 birth to the new year on a day DAY assigns to the old side.
      The granularities are three readings of one rule, not nested refinements.
    '''
    expected: list[tuple[str, str, str, Dizhi]] = [
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
    ]
    for moment, precision, year_pillar, month_dizhi in expected:
      with self.subTest(moment=moment, precision=precision):
        bazi: Bazi = Bazi.create(moment, 'male', precision)
        self.assertEqual(str(bazi.year_pillar), year_pillar)
        self.assertEqual(bazi.month_commander, month_dizhi)

  def test_day_and_hour_pillars_ignore_precision(self) -> None:
    '''Precision only moves the year/month attribution; the day/hour pillars must not move.'''
    moments: list[str] = ['2009-02-03 23:30', '2017-02-03 23:10', '2000-02-04 20:39', '1984-02-04 12:30']
    for moment in moments:
      day_bazi: Bazi = Bazi.create(moment, 'female', 'day')
      for precision in ('hour', 'minute'):
        with self.subTest(moment=moment, precision=precision):
          bazi: Bazi = Bazi.create(moment, 'female', precision)
          self.assertEqual(bazi.day_pillar, day_bazi.day_pillar)
          self.assertEqual(bazi.hour_pillar, day_bazi.hour_pillar)

  def test_hko_backend_rejected(self) -> None:
    '''HOUR / MINUTE need real jieqi moments; the HKO backend's are midnight placeholders.'''
    for precision in (BaziPrecision.HOUR, BaziPrecision.MINUTE):
      with self.subTest(precision=precision):
        with self.assertRaises(ValueError):
          Bazi(datetime(2000, 2, 4, 19, 30), BaziGender.MALE, precision, CalendarBackend.HKO)
    self.assertEqual(str(Bazi.create('2000-02-04 19:30', 'male', 'day', backend='hko').year_pillar), '庚辰')

  def test_ganzhi_year_and_bracketing_jies_are_the_attribution(self) -> None:
    '''`ganzhi_year` / `bracketing_jies` expose exactly what the pillars were derived from.'''
    bazi: Bazi = Bazi.create('2009-02-04 00:30', 'male', 'hour')
    self.assertEqual(bazi.ganzhi_year, 2009)
    owning, following = bazi.bracketing_jies
    self.assertEqual(owning, JieqiTime(Jieqi.立春, datetime(2009, 2, 4, 0, 49, 48)))
    self.assertEqual(following.jieqi, Jieqi.惊蛰)
    # The owning jie's true moment lies AFTER the birth -- that is what a tie looks like.
    self.assertGreater(owning.moment, bazi.solar_datetime)
    # `ganzhi_date` stays a day-level channel: on the jieqi's own day the two channels agree
    # (DAY gives the whole day to the new side), but for the cross-midnight tie birth on the
    # PREVIOUS day they legitimately disagree.
    self.assertEqual(bazi.ganzhi_date.year, 2009)
    advance: Bazi = Bazi.create('2009-02-03 23:30', 'male', 'hour')
    self.assertEqual(advance.ganzhi_year, 2009)
    self.assertEqual(advance.ganzhi_date.year, 2008)

  @pytest.mark.slow
  def test_attribution_matches_scan_oracle(self) -> None:
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
      day_bazi: Bazi = Bazi(birth, BaziGender.女, BaziPrecision.DAY)

      candidates: list[JieqiTime] = sorted(
        (JieqiTime(jie, utils.jieqi_moment(year, jie))
         for year in (birth.year - 1, birth.year) for jie in all_jies),
        key=lambda jt: jt.moment,
      )

      for precision in (BaziPrecision.HOUR, BaziPrecision.MINUTE):
        with self.subTest(birth=birth, precision=precision):
          bazi: Bazi = Bazi(birth, BaziGender.女, precision)

          trunc_birth: datetime = self.__truncated(birth, precision)
          lichun: datetime = utils.jieqi_moment(birth.year, Jieqi.立春)
          expected_year: int = birth.year if trunc_birth >= self.__truncated(lichun, precision) else birth.year - 1
          self.assertEqual(bazi.ganzhi_year, expected_year)

          owning: JieqiTime = max(
            (jt for jt in candidates if self.__truncated(jt.moment, precision) <= trunc_birth),
            key=lambda jt: jt.moment,
          )
          self.assertEqual(bazi.month_commander, self.JIE_MONTH_DIZHI[owning.jieqi])

          # Divergence-from-DAY shape: only inside a tie window around a jie's own day.
          if (bazi.year_pillar, bazi.month_commander) != (day_bazi.year_pillar, day_bazi.month_commander):
            divergent += 1
            day_owning: JieqiTime = max(
              (jt for jt in candidates if jt.moment.date() <= birth.date()),
              key=lambda jt: jt.moment,
            )
            if owning.moment > day_owning.moment:  # Advance: cross-midnight 晚子时 tie.
              self.assertIs(precision, BaziPrecision.HOUR)
              self.assertEqual(self.__truncated(owning.moment, precision), trunc_birth)
              self.assertLess(birth.date(), owning.moment.date())
            else:                                  # Retreat: jieqi-day birth before the moment.
              self.assertEqual(birth.date(), day_owning.moment.date())
              self.assertLess(trunc_birth, self.__truncated(day_owning.moment, precision))

    # The biased sampling must actually have exercised the divergence windows.
    self.assertGreater(divergent, 100)

  @pytest.mark.slow
  def test_minute_vs_moment_level_prev_jie(self) -> None:
    '''
    MINUTE attribution vs the moment-level `prev_jie`: the two may disagree ONLY at a
    same-minute tie (birth in the same minute as the jieqi but before its true second --
    ties go new, `prev_jie` stays old). At any other moment they must agree.
    '''
    utils = calendar_utils_of(CalendarBackend.CELESTIAL)
    rng = random.Random(72) # Seeded with the issue this rule closes.

    all_jies: list[Jieqi] = Jieqi.as_list(ganzhi_year=False)[::2]
    for _ in range(2_000):
      jie_moment: datetime = utils.jieqi_moment(rng.randint(1902, 2080), rng.choice(all_jies))
      birth: datetime = (jie_moment + timedelta(seconds=rng.randint(-90, 90))).replace(second=0, microsecond=0)

      bazi: Bazi = Bazi(birth, BaziGender.男, BaziPrecision.MINUTE)
      moment_owning: JieqiTime = utils.prev_jie(birth)
      attribution_owning: JieqiTime = bazi.bracketing_jies[0]

      with self.subTest(birth=birth):
        if attribution_owning != moment_owning:
          next_j: JieqiTime = utils.next_jie(birth)
          self.assertEqual(attribution_owning, next_j)
          self.assertEqual(next_j.moment.replace(second=0, microsecond=0), birth) # Same minute.
          self.assertLess(birth, next_j.moment)                                   # Before the true second.
        self.assertEqual(bazi.month_commander, self.JIE_MONTH_DIZHI[attribution_owning.jieqi])


class TestBazi(unittest.TestCase):
  def test_init(self) -> None:
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
        precision=BaziPrecision.DAY,
      )

      self.assertEqual(bazi.solar_date, date(random_dt.year, random_dt.month, random_dt.day))
      self.assertEqual(bazi.hour, random_dt.hour)
      self.assertEqual(bazi.minute, random_dt.minute)
      self.assertEqual(bazi.gender, BaziGender.男)
      self.assertEqual(bazi.precision, BaziPrecision.DAY)

  def test_chinese(self) -> None:
    self.assertIs(Bazi, 八字)

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
        precision=BaziPrecision.DAY,
      )

      self.assertEqual(bazi.solar_date, date(random_dt.year, random_dt.month, random_dt.day))
      self.assertEqual(bazi.hour, random_dt.hour)
      self.assertEqual(bazi.minute, random_dt.minute)
      self.assertEqual(bazi.gender, BaziGender.男)
      self.assertEqual(bazi.precision, BaziPrecision.DAY)

  def test_invalid_arguments(self) -> None:
    random_dt: datetime = datetime(
      year=random.randint(1950, 2000),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
      second=random.randint(0, 59)
    )

    with self.assertRaises(TypeError):
      Bazi(birth_time=random_dt, gender=BaziGender.男) # type: ignore # Missing `precision`
    with self.assertRaises(TypeError):
      Bazi(birth_time=random_dt, precision=BaziPrecision.DAY) # type: ignore # Missing `gender`
    with self.assertRaises(AssertionError):
      Bazi(birth_time='2024-03-03', gender=BaziGender.男, precision=BaziPrecision.DAY) # type: ignore # Currently doesn't take string as input
    with self.assertRaises(AssertionError):
      Bazi(birth_time=date(9999, 1, 1), gender=BaziGender.男, precision=BaziPrecision.DAY) # type: ignore
    with self.assertRaises(AssertionError):
      dt: datetime = datetime(
        year=9999, # Out of supported range.
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      )
      Bazi(birth_time=dt, gender=BaziGender.男, precision=BaziPrecision.DAY)
    with self.assertRaises(AssertionError):
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
        precision=BaziPrecision.DAY,
      )

  @staticmethod
  def __create_bazi(dt: datetime) -> Bazi:
    return Bazi(
      birth_time=dt,
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )

  def test_four_dizhis_correctness(self) -> None:
    '''
    Test the correctness of `Bazi` on the given test cases.
    Precision is at `DAY` level.
    '''
    def __subtest(dt: datetime, dizhi_strs: list[str]) -> None:
      assert len(dizhi_strs) == 4

      bazi = self.__create_bazi(dt)
      self.assertEqual(bazi.four_dizhis, (
        Dizhi.from_str(dizhi_strs[0]),
        Dizhi.from_str(dizhi_strs[1]),
        Dizhi.from_str(dizhi_strs[2]),
        Dizhi.from_str(dizhi_strs[3]),
      ))

    with self.subTest('Basic cases'):
      # Data was collected from "测测" app on my iPhone 15 Pro Max.
      __subtest(datetime(2024, 2, 6, 11, 55), ['辰', '寅', '子', '午'])
      __subtest(datetime(1984, 4, 2, 4, 2), ['子', '卯', '寅', '寅'])

      __subtest(datetime(1998, 3, 17, 13, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 13, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 15, 0), ['寅', '卯', '亥', '申'])
      __subtest(datetime(1998, 3, 17, 23, 0), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 0, 59), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 1, 0), ['寅', '卯', '子', '丑'])

    with self.subTest('Edge cases'):
      __subtest(datetime(1998, 3, 17, 13, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 13, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 0), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 14, 59), ['寅', '卯', '亥', '未'])
      __subtest(datetime(1998, 3, 17, 15, 0), ['寅', '卯', '亥', '申'])
      __subtest(datetime(1998, 3, 17, 23, 0), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 0, 59), ['寅', '卯', '子', '子'])
      __subtest(datetime(1998, 3, 18, 1, 0), ['寅', '卯', '子', '丑'])

      __subtest(datetime(2000, 2, 3, 0, 0), ['卯', '丑', '卯', '子'])
      __subtest(datetime(2000, 2, 3, 22, 59), ['卯', '丑', '卯', '亥'])
      __subtest(datetime(2000, 2, 3, 23, 0), ['卯', '丑', '辰', '子'])
      __subtest(datetime(2000, 2, 4, 0, 0), ['辰', '寅', '辰', '子'])
      __subtest(datetime(2000, 2, 4, 1, 0), ['辰', '寅', '辰', '丑'])

  def test_four_tiangans_correctness(self) -> None:
    def __subtest(dt: datetime, tiangan_strs: list[str]) -> None:
      assert len(tiangan_strs) == 4

      bazi = self.__create_bazi(dt)
      self.assertEqual(bazi.four_tiangans, (
        Tiangan.from_str(tiangan_strs[0]),
        Tiangan.from_str(tiangan_strs[1]),
        Tiangan.from_str(tiangan_strs[2]),
        Tiangan.from_str(tiangan_strs[3]),
      ))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲', '丁', '丙', '庚'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚', '戊', '壬', '辛'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛', '戊', '丙', '戊'])

  def test_ganzhi_date(self) -> None:
    bazi: Bazi = self.__create_bazi(datetime(1984, 4, 2, 4, 2))
    self.assertEqual(bazi.ganzhi_date, HkoDataCalendarUtils.to_ganzhi(date(1984, 4, 2)))
    
    for _ in range(10):
      bazi = Bazi.random()
      self.assertEqual(bazi.ganzhi_date, HkoDataCalendarUtils.to_ganzhi(bazi.solar_date))

  def test_date_time(self) -> None:
    bazi: Bazi = self.__create_bazi(datetime(1984, 4, 2, 4, 2))
    self.assertEqual(bazi.solar_date, date(1984, 4, 2))
    self.assertEqual(bazi.hour, 4)
    self.assertEqual(bazi.minute, 2)
    self.assertEqual(bazi.solar_datetime, datetime(1984, 4, 2, 4, 2))

    random_bazi: Bazi = Bazi.random()
    with self.assertRaises(AttributeError):
      random_bazi.solar_date = date(1984, 4, 3) # type: ignore
    with self.assertRaises(AttributeError):
      random_bazi.hour = 9 # type: ignore
    with self.assertRaises(AttributeError):
      random_bazi.minute = 8 # type: ignore
    with self.assertRaises(AttributeError):
      random_bazi.solar_datetime = datetime(1984, 4, 3, 9, 8) # type: ignore
  
  def test_pillars(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: list[Ganzhi] = list(bazi.pillars)
      self.assertEqual(pillars[0], Ganzhi.from_str(ganzhi_strs[0]), 'Year Pillar')
      self.assertEqual(pillars[1], Ganzhi.from_str(ganzhi_strs[1]), 'Month Pillar')
      self.assertEqual(pillars[2], Ganzhi.from_str(ganzhi_strs[2]), 'Day Pillar')
      self.assertEqual(pillars[3], Ganzhi.from_str(ganzhi_strs[3]), 'Hour Pillar')

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])

  def test_consistency(self) -> None:
    def __subtest(dt: datetime, ganzhi_strs: list[str]) -> None:
      assert len(ganzhi_strs) == 4

      bazi = self.__create_bazi(dt)
      pillars: list[Ganzhi] = list(bazi.pillars)

      self.assertEqual(bazi.day_master, pillars[2].tiangan)
      self.assertEqual(bazi.month_commander, pillars[1].dizhi)

      self.assertEqual(bazi.year_pillar, pillars[0])
      self.assertEqual(bazi.month_pillar, pillars[1])
      self.assertEqual(bazi.day_pillar, pillars[2])
      self.assertEqual(bazi.hour_pillar, pillars[3])

      self.assertEqual(bazi.four_tiangans, tuple([tg for tg, _ in pillars]))
      self.assertEqual(bazi.four_dizhis, tuple([dz for _, dz in pillars]))

    __subtest(datetime(1984, 4, 2, 4, 2), ['甲子', '丁卯', '丙寅', '庚寅'])
    __subtest(datetime(2000, 2, 4, 22, 1), ['庚辰', '戊寅', '壬辰', '辛亥'])
    __subtest(datetime(2001, 10, 20, 19, 0), ['辛巳', '戊戌', '丙辰', '戊戌'])

  def test_deepcopy(self) -> None:
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 2, 4, 2),
      gender=BaziGender.男,
      precision=BaziPrecision.DAY,
    )
    bazi2: Bazi = copy.deepcopy(bazi)

    self.assertIsNot(bazi._solar_date, bazi2._solar_date)
    self.assertIsNot(bazi._year_pillar, bazi2._year_pillar)

    self.assertIsNot(bazi._day_pillar, bazi2._day_pillar)
    self.assertEqual(bazi._day_pillar, bazi2._day_pillar)

    cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
    next_day_pillar: Ganzhi = cycle[(cycle.index(bazi._day_pillar) + 1) % len(cycle)]
    bazi._day_pillar = next_day_pillar # type: ignore
    self.assertNotEqual(bazi._day_pillar, bazi2._day_pillar)

  def test_create(self) -> None:
    with self.assertRaises(ValueError):
      Bazi.create('WrongDatetimeFormat', BaziGender.FEMALE, BaziPrecision.DAY)
    with self.assertRaises(ValueError):
      Bazi.create(datetime.now(), 'femal', BaziPrecision.DAY)
    with self.assertRaises(ValueError):
      Bazi.create(datetime.now(), BaziGender.FEMALE, 'dya')

    # Create a datetime and set its timezone to Asia/Shanghai.
    _dt: datetime = datetime.now()
    _dt = _dt.replace(tzinfo=ZoneInfo('Asia/Shanghai'))
    with self.assertRaises(AssertionError):
      Bazi.create(_dt, BaziGender.FEMALE, BaziPrecision.DAY)
    with self.assertRaises(AssertionError):
      Bazi.create(_dt.isoformat(), BaziGender.FEMALE, BaziPrecision.DAY)

    now: datetime = datetime.now()
    dt_options: list[Union[str, datetime]] = [now, now.isoformat()]
    male_options: list[Union[str, BaziGender]] = [BaziGender.男, BaziGender.YANG, BaziGender.阳, 'Male', '男', 'MALE']
    female_options: list[Union[str, BaziGender]] = [BaziGender.YIN, BaziGender.FEMALE, '女', 'FEMALE', 'female']
    day_precision_options: list[Union[str, BaziPrecision]] = [BaziPrecision.DAY, 'day', 'DAY', 'Day', '日', '天', 'd', 'D']

    expected_bazi: Bazi = Bazi.create(now, BaziGender.FEMALE, BaziPrecision.DAY)
    for dt, g, p in product(dt_options, female_options, day_precision_options):
      bazi = Bazi.create(dt, g, p)
      self.assertListEqual(list(bazi.pillars), list(expected_bazi.pillars))
      self.assertEqual(bazi.gender, expected_bazi.gender)
      self.assertEqual(bazi.precision, expected_bazi.precision)
      self.assertEqual(bazi.solar_date, expected_bazi.solar_date)
      self.assertEqual(bazi.hour, expected_bazi.hour)
      self.assertEqual(bazi.minute, expected_bazi.minute)
    
    expected_bazi = Bazi.create(now, BaziGender.MALE, BaziPrecision.DAY)
    for dt, g, p in product(dt_options, male_options, day_precision_options):
      bazi = Bazi.create(dt, g, p)
      self.assertListEqual(list(bazi.pillars), list(expected_bazi.pillars))
      self.assertEqual(bazi.gender, expected_bazi.gender)
      self.assertEqual(bazi.precision, expected_bazi.precision)
      self.assertEqual(bazi.solar_date, expected_bazi.solar_date)
      self.assertEqual(bazi.hour, expected_bazi.hour)
      self.assertEqual(bazi.minute, expected_bazi.minute)

    finer_precision_options: list = [BaziPrecision.HOUR, BaziPrecision.MINUTE, 'hour', 'minute', 'H', 'm', '时', '小时', '分', '分钟']
    for dt, g, p in product(dt_options, male_options + female_options, finer_precision_options):
      bazi = Bazi.create(dt, g, p) # Supported since issue #6 -- on the celestial backend only.
      self.assertIn(bazi.precision, (BaziPrecision.HOUR, BaziPrecision.MINUTE))
      with self.assertRaises(ValueError):
        Bazi.create(dt, g, p, backend='hko') # HKO has no real jieqi moments.

  def test_eq_ne(self) -> None:
    def __random_info() -> tuple[datetime, BaziGender, BaziPrecision]:
      return (datetime(
        year=random.randint(1950, 2000),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
      ), random.choice(list(BaziGender)), BaziPrecision.DAY)
    
    def __toggle_gender(g: BaziGender) -> BaziGender:
      return BaziGender.MALE if g is BaziGender.FEMALE else BaziGender.FEMALE
    
    def __inc_datetime(dt: datetime) -> datetime:
      return dt + timedelta(days=1)

    for _ in range(64):
      dt, gender, precision = __random_info()

      bazi: Bazi = Bazi.create(dt, gender, precision)
      self.assertEqual(bazi, Bazi.create(dt, gender, precision))
      self.assertNotEqual(bazi, Bazi.create(dt, __toggle_gender(gender), precision))
      self.assertNotEqual(bazi, Bazi.create(__inc_datetime(dt), gender, precision))

      self.assertNotEqual(bazi, 0)

      bazi_hacked: Bazi = Bazi.create(dt, gender, precision)
      bazi_hacked._precision = BaziPrecision.HOUR # type: ignore # Intended for testing only.
      self.assertNotEqual(bazi, bazi_hacked)
