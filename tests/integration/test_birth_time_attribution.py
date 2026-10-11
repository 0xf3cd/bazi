# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import UTC, date, datetime, time, timedelta
from fractions import Fraction
from itertools import pairwise

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.calendar import CalendarType, JieqiTime, calendar_utils_of
from bazi.defines import Dizhi, Jieqi
from bazi.school import BaziConfig
from bazi.transit_chart import TransitChart
from bazi.transits import TransitDatabase
from run_demo import get_basic_info, get_transit_info


# Literal month ownership; neither enum indices nor production coordinate conversions are an oracle.
JIE_MONTHS = (
  (Jieqi.小寒, Dizhi.丑, 12), (Jieqi.立春, Dizhi.寅, 1), (Jieqi.惊蛰, Dizhi.卯, 2),
  (Jieqi.清明, Dizhi.辰, 3), (Jieqi.立夏, Dizhi.巳, 4), (Jieqi.芒种, Dizhi.午, 5),
  (Jieqi.小暑, Dizhi.未, 6), (Jieqi.立秋, Dizhi.申, 7), (Jieqi.白露, Dizhi.酉, 8),
  (Jieqi.寒露, Dizhi.戌, 9), (Jieqi.立冬, Dizhi.亥, 10), (Jieqi.大雪, Dizhi.子, 11),
)


@pytest.mark.parametrize('backend', ('celestial', 'celestial-algo2', 'hko'))
@pytest.mark.parametrize('year', (1902, 1917, 1927, 2000, 2009, 2017, 2099))
def test_day_ownership_and_counting_match_date_scan(backend: str, year: int) -> None:
  utils = calendar_utils_of(backend)
  candidates = sorted(
    [(utils.jieqi_moment(y, jie), jie, dizhi, month)
     for y in (year - 1, year, year + 1) for jie, dizhi, month in JIE_MONTHS],
    key=lambda row: row[0],
  )
  for jie, _, _ in JIE_MONTHS:
    moment = utils.jieqi_moment(year, jie)
    midnight = datetime.combine(moment.date(), time.min)
    # Input retains seconds, while the default reference clock deliberately truncates to a minute.
    births = (midnight - timedelta(minutes=1), midnight, moment - timedelta(seconds=1),
              moment, moment + timedelta(seconds=1), midnight + timedelta(hours=23, minutes=59),
              midnight + timedelta(days=1))
    for birth in births:
      owning_index = max(i for i, row in enumerate(candidates) if row[0].date() <= birth.date())
      owning, following = candidates[owning_index:owning_index + 2]
      expected_year = birth.year - (birth.date() < utils.jieqi_date(birth.year, Jieqi.立春))
      for gender in ('male', 'female'):
        chart = BaziChart(Bazi.create(birth, gender, BaziConfig.from_values(backend=backend)))
        bazi = chart.bazi
        reference = birth.replace(second=0, microsecond=0)
        assert bazi.reference_datetime == reference
        assert bazi.ganzhi_year == expected_year
        assert (bazi.ganzhi_year_month.year, bazi.ganzhi_year_month.month) == (expected_year, owning[3])
        assert bazi.month_commander is owning[2]
        assert bazi.month_jies == (JieqiTime(owning[1], owning[0]), JieqiTime(following[1], following[0]))
        # Yang years are even (甲子 1984); select direction independently of chart.dayun_order.
        forward = (gender == 'male') == (expected_year % 2 == 0)
        gap = following[0] - reference if forward else max(timedelta(), reference - owning[0])
        gap_us = gap // timedelta(microseconds=1)
        expected_start = reference + timedelta(microseconds=round(Fraction(gap_us * 365, 3)))
        assert chart.dayun_order is forward
        assert abs(chart.dayun_start_moment - expected_start) <= timedelta(microseconds=1)
        _, last_supported = utils.supported_jie_boundaries()
        if expected_start >= last_supported:
          assert tuple(chart.dayun) == ()
          with pytest.raises(ValueError, match='No Dayun starts'):
            _ = chart.xiaoyun
          continue
        first = next(chart.dayun)
        start_year = expected_start.year - (expected_start < utils.jieqi_moment(expected_start.year, Jieqi.立春))
        expected_label = max(expected_year, start_year)
        assert first.ganzhi_year == expected_label
        assert len(chart.xiaoyun) == expected_label - expected_year + 1
        if expected_start == reference:
          transits = TransitChart(chart)
          current_month = transits.at_month(expected_year, owning[2])
          assert current_month is not None and current_month.dayun == first.ganzhi
          previous_year = expected_year - (owning[3] == 1)
          previous_branch = candidates[owning_index - 1][2]
          assert TransitDatabase(chart)._dayun_at_month(previous_year, previous_branch) is None
        # Calendar lookups still bracket the physical minute, including DAY's advance window.
        physical_index = max(i for i, row in enumerate(candidates) if row[0] <= reference)
        assert utils.prev_jie(reference) == JieqiTime(candidates[physical_index][1], candidates[physical_index][0])
        assert utils.next_jie(reference) == JieqiTime(candidates[physical_index + 1][1], candidates[physical_index + 1][0])


@pytest.mark.parametrize('backend', ('celestial', 'celestial-algo2', 'hko'))
def test_birth_and_query_endpoints_remain_distinct(backend: str) -> None:
  utils = calendar_utils_of(backend)
  first_date = utils.to_date(utils.get_min_supported_date(CalendarType.SOLAR))
  last_date = utils.to_date(utils.get_max_supported_date(CalendarType.SOLAR))
  for birth_date in (first_date, last_date):
    for gender in ('male', 'female'):
      chart = BaziChart(Bazi.create(datetime.combine(birth_date, time(12)), gender,
                                   BaziConfig.from_values(backend=backend)))
      owning, following = chart.bazi.month_jies
      assert owning.moment.date() <= birth_date < following.moment.date()
      dayuns = tuple(chart.dayun)
      first, last = utils.supported_jie_boundaries()
      assert all(first <= item.start_moment < last for item in dayuns)
      assert all(left.end_moment == right.start_moment for left, right in pairwise(dayuns))
      if dayuns:
        assert dayuns[-1].end_moment >= last
      else:
        with pytest.raises(ValueError, match='No Dayun starts'):
          _ = chart.xiaoyun
      transits = TransitChart(chart)
      assert transits.at_date(birth_date) is not None
      assert transits.at_date(birth_date - timedelta(days=1)) is None
      assert transits.at_date(last_date + timedelta(days=1)) is None
      assert transits.at_month(chart.bazi.ganzhi_year, chart.bazi.month_commander) is not None
  for outside in (first_date - timedelta(days=1), last_date + timedelta(days=1)):
    with pytest.raises(ValueError):
      Bazi.create(datetime.combine(outside, time.min), 'male', BaziConfig.from_values(backend=backend))


@pytest.mark.parametrize('birth,previous_year,previous,current,first_ganzhi', [
  ('2000-02-04 10:00', 1999, Dizhi.丑, Dizhi.寅, '丁丑'),
  ('2000-03-05 10:00', 2000, Dizhi.寅, Dizhi.卯, '戊寅'),
])
def test_day_first_month_floor_does_not_change_physical_queries(
  birth: str, previous_year: int, previous: Dizhi, current: Dizhi, first_ganzhi: str,
) -> None:
  chart = BaziChart(Bazi.create(birth, 'female'))
  database = TransitDatabase(chart)
  assert chart.dayun_start_moment == datetime.fromisoformat(birth)
  assert chart.bazi.month_jies[0].moment > chart.bazi.reference_datetime
  assert database._dayun_at_month(previous_year, previous) is None
  assert str(database._dayun_at_month(2000, current)) == first_ganzhi
  assert next(chart.dayun).ganzhi_year == 2000


def test_day_year_floor_does_not_change_physical_queries() -> None:
  chart = BaziChart(Bazi.create('2000-02-04 10:00', 'female'))
  transits = TransitChart(chart)
  database = TransitDatabase(chart)
  assert database._dayun_at_month(1999, Dizhi.丑) is None
  assert str(database._dayun_at_month(2000, Dizhi.寅)) == '丁丑'
  assert next(chart.dayun).ganzhi_year == 2000
  assert transits.at_year(1999) is None
  assert transits.at_month(1999, Dizhi.丑) is None
  current = transits.at_month(2000, Dizhi.寅)
  assert current is not None and str(current.dayun) == '丁丑'
  assert transits.at_date(date(2000, 2, 4)) is not None
  assert transits.at_moment(datetime(2000, 2, 4, 10)) is None
  precise = TransitChart(BaziChart(Bazi.create('2000-02-04 10:00', 'female',
                                             BaziConfig.from_values(precision='hour'))))
  physical = precise.at_moment(datetime(2000, 2, 4, 10))
  assert physical is not None and str(physical.liunian) == '己卯' and str(physical.liuyue) == '丁丑'


@pytest.mark.parametrize('located', [False, True])
@pytest.mark.parametrize('gender,counting', [
  ('male', '大运数节依据（顺排）：惊蛰 - 2000-03-05T14:42:39'),
  ('female', '大运数节依据（逆排）：立春 - 2000-02-04T20:40:23'),
])
def test_demo_reads_time_facts_without_serializing_chart(
  monkeypatch: pytest.MonkeyPatch, located: bool, gender: str, counting: str,
) -> None:
  def fail_json(_chart: BaziChart) -> object:
    raise AssertionError('Display must not generate a complete chart JSON')
  monkeypatch.setattr(BaziChart, 'json', property(fail_json))
  chart = BaziChart(Bazi.create(
    '2000-02-04T07:40:00-05:00' if located else '2000-02-04 10:00',
    gender,
    BaziConfig.from_values(precision='minute' if located else 'day'),
    longitude=0.0 if located else None,
  ))
  bazi = chart.bazi
  facts = bazi.location_time
  basic = get_basic_info(chart)
  if located:
    assert facts is not None
    assert facts.canonical_instant == datetime(2000, 2, 4, 12, 40, tzinfo=UTC)
    assert facts.civil_time.isoformat() == '2000-02-04T07:40:00-05:00'
    # Daily EOT nodes are -828.6s/-834.6s; at 12:40 UTC the fraction is 19/36.
    assert facts.apparent_time.isoformat() == '2000-02-04T12:26:08.233333'
    assert bazi.reference_datetime == datetime(2000, 2, 4, 20, 40)
    assert bazi.solar_datetime == datetime(2000, 2, 4, 12, 26)
    assert '民用出生时刻（固定出生地偏移）：2000-02-04T07:40:00-05:00' in basic
  else:
    assert facts is None
    assert '出生时刻：2000-02-04T10:00:00' in basic
  assert bazi.month_jies[0].jieqi is Jieqi.立春
  text = get_transit_info(chart)
  assert '出生时刻前一节：小寒' in text
  assert '出生时刻后一节：立春 - 2000-02-04T20:40:23' in text
  assert counting in text


def test_time_facts_are_readonly_and_json_is_detached() -> None:
  bazi = Bazi.create('2000-02-04T07:40:12.123456-05:00', 'male',
                     BaziConfig.from_values(precision='minute'), longitude=0.0)
  facts = bazi.location_time
  assert facts is not None
  assert facts.canonical_instant.microsecond == 123456
  assert bazi.reference_datetime == datetime(2000, 2, 4, 20, 40, 12, 123456)
  with pytest.raises(AttributeError):
    facts.longitude = 1.0 # type: ignore[misc]
  with pytest.raises(AttributeError):
    bazi.reference_datetime = datetime(2000, 1, 1) # type: ignore[misc]
  detached = facts.json
  detached['apparent_time'] = 'wrong'
  assert facts.json['apparent_time'] == facts.apparent_time.isoformat()
  assert Bazi.create('2000-02-04 10:00', 'male').location_time is None


def test_day_json_restoration_rejects_old_derived_start() -> None:
  chart = BaziChart(Bazi.create('2000-02-04 10:00', 'male'))
  data = chart.json
  assert BaziChart.from_json(data).json == data
  data['transits']['dayun_start_time'] = '2000-03-29T12:33:18.333333'
  with pytest.raises(ValueError):
    BaziChart.from_json(data)


@pytest.mark.parametrize('backend', ('celestial', 'celestial-algo2'))
@pytest.mark.parametrize('precision', ('hour', 'minute'))
def test_precise_birth_and_physical_queries_match_scans(backend: str, precision: str) -> None:
  utils = calendar_utils_of(backend)

  def truncated(moment: datetime) -> datetime:
    if precision == 'minute':
      return moment.replace(second=0, microsecond=0)
    candidates = [datetime.combine(moment.date() - timedelta(days=1), time(23))]
    candidates += [datetime.combine(moment.date(), time(h)) for h in (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23)]
    return max(value for value in candidates if value <= moment)

  for year in (2000, 2009, 2017):
    candidates = sorted(
      [(utils.jieqi_moment(y, jie), jie, dizhi)
       for y in (year - 1, year, year + 1) for jie, dizhi, _ in JIE_MONTHS],
      key=lambda row: row[0],
    )
    for jie, _, _ in JIE_MONTHS:
      moment = utils.jieqi_moment(year, jie)
      tie_start = truncated(moment)
      for birth in (tie_start - timedelta(minutes=1), tie_start, moment - timedelta(seconds=1),
                    moment, moment + timedelta(seconds=1), tie_start + timedelta(hours=2)):
        index = max(i for i, row in enumerate(candidates) if truncated(row[0]) <= truncated(birth))
        owning, following = candidates[index:index + 2]
        chart = BaziChart(Bazi.create(birth, 'female', BaziConfig.from_values(backend=backend, precision=precision)))
        assert chart.bazi.month_commander is owning[2]
        assert chart.bazi.month_jies == (JieqiTime(owning[1], owning[0]), JieqiTime(following[1], following[0]))
        physical_index = max(i for i, row in enumerate(candidates) if row[0] <= chart.bazi.reference_datetime)
        reading = TransitChart(chart).at_moment(chart.bazi.reference_datetime)
        assert reading is not None and reading.liuyue is not None
        assert reading.liuyue.dizhi is candidates[physical_index][2]
  precise = TransitChart(BaziChart(Bazi.create('2000-01-01 12:00', 'female',
                                             BaziConfig.from_values(backend=backend, precision=precision))))
  _, last = utils.supported_jie_boundaries()
  assert precise.at_moment(last - timedelta(seconds=1)) is not None
  assert precise.at_moment(last) is None


@pytest.mark.parametrize('backend,last_year', [('celestial', 2200), ('celestial-algo2', 2200), ('hko', 2100)])
def test_month_query_support_endpoint(backend: str, last_year: int) -> None:
  transits = TransitChart(BaziChart(Bazi.create('1901-02-19 12:00', 'male',
                                             BaziConfig.from_values(backend=backend))))
  assert transits.at_month(last_year, Dizhi.亥) is not None
  assert transits.at_month(last_year, Dizhi.子) is None
  assert transits.at_month(last_year - 1, Dizhi.丑) is not None
