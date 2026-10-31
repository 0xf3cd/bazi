# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import fields
from datetime import datetime, timedelta, timezone

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.calendar import CalendarBackend, CalendarType, calendar_utils_of
from bazi.calendar.solar_time import apparent_solar_datetime
from bazi.defines import Dizhi, Wuxing, WuxingState, 五行状态
from bazi.school import BaziConfig, BaziPrecision, BaziSchool, TuwangDef


ROWS = {
  Wuxing.木: '旺相死囚休', Wuxing.火: '休旺相死囚', Wuxing.土: '囚休旺相死',
  Wuxing.金: '死囚休旺相', Wuxing.水: '相死囚休旺',
}
MONTHS = (
  (2, Dizhi.寅, Wuxing.木), (3, Dizhi.卯, Wuxing.木), (4, Dizhi.辰, Wuxing.木),
  (5, Dizhi.巳, Wuxing.火), (6, Dizhi.午, Wuxing.火), (7, Dizhi.未, Wuxing.火),
  (8, Dizhi.申, Wuxing.金), (9, Dizhi.酉, Wuxing.金), (10, Dizhi.戌, Wuxing.金),
  (11, Dizhi.亥, Wuxing.水), (12, Dizhi.子, Wuxing.水), (1, Dizhi.丑, Wuxing.水),
)
SEASONAL = (Dizhi.辰, Dizhi.未, Dizhi.戌, Dizhi.丑)


def _states(chart: BaziChart) -> str:
  return ''.join(str(chart.wuxing_states[element]) for element in Wuxing)


def _truncate(moment: datetime, precision: BaziPrecision) -> datetime:
  day = moment.replace(hour=0, minute=0, second=0, microsecond=0)
  if precision is BaziPrecision.DAY:
    return day
  if precision is BaziPrecision.HOUR:
    return day + timedelta(hours=(moment.hour + 1) // 2 * 2 - 1)
  return moment.replace(second=0, microsecond=0)


@pytest.mark.parametrize('backend', list(CalendarBackend))
@pytest.mark.parametrize('definition', list(TuwangDef))
def test_twelve_months_and_all_five_states(backend: CalendarBackend, definition: TuwangDef) -> None:
  config = BaziConfig(backend=backend, school=BaziSchool(tuwang_def=definition))
  for month, dizhi, seasonal in MONTHS:
    chart = BaziChart(Bazi.create(datetime(2026, month, 15, 12), 'male', config))
    assert chart.bazi.month_commander is dizhi
    dominant = Wuxing.土 if dizhi in SEASONAL and definition is TuwangDef.WHOLE_MONTH else seasonal
    assert _states(chart) == ROWS[dominant]
    assert set(chart.wuxing_states) == set(Wuxing)
    assert set(chart.wuxing_states.values()) == set(WuxingState)
    if dizhi in SEASONAL:
      late = BaziChart(Bazi.create(datetime(2026, month, 25, 12), 'male', config))
      assert _states(late) == ROWS[Wuxing.土]


@pytest.mark.parametrize('definition', [TuwangDef.AFTER_TWELVE_DAYS, TuwangDef.BEFORE_EIGHTEEN_DAYS])
@pytest.mark.parametrize('backend,precision', [
  (backend, precision) for backend in CalendarBackend for precision in BaziPrecision
  if backend is not CalendarBackend.HKO or precision is BaziPrecision.DAY
])
@pytest.mark.parametrize('month,seasonal', [(1, Wuxing.水), (4, Wuxing.木), (7, Wuxing.火), (10, Wuxing.金)])
def test_threshold_before_equal_after(
  definition: TuwangDef, backend: CalendarBackend, precision: BaziPrecision, month: int, seasonal: Wuxing,
) -> None:
  config = BaziConfig(backend=backend, precision=precision, school=BaziSchool(tuwang_def=definition))
  sample = Bazi.create(datetime(2026, month, 15), 'male', config)
  opening, following = sample.month_jies
  boundary = opening.moment + timedelta(days=12) if definition is TuwangDef.AFTER_TWELVE_DAYS else following.moment - timedelta(days=18)
  start = _truncate(boundary, precision)
  unit = timedelta(days=1) if precision is BaziPrecision.DAY else timedelta(hours=2) if precision is BaziPrecision.HOUR else timedelta(minutes=1)
  for birth, dominant in ((start - unit, seasonal), (start, Wuxing.土), (start + unit, Wuxing.土)):
    assert _states(BaziChart(Bazi.create(birth, 'male', config))) == ROWS[dominant]


@pytest.mark.parametrize('birth,precision,expected', [
  ('2026-04-17 12:00', BaziPrecision.DAY, (True, True)),
  ('2026-04-17 12:00', BaziPrecision.HOUR, (True, False)),
  ('2026-04-17 12:00', BaziPrecision.MINUTE, (True, False)),
  ('2026-07-19 12:00', BaziPrecision.DAY, (True, False)),
  ('2024-01-17 12:00', BaziPrecision.DAY, (False, True)),
])
def test_two_anchors_have_both_window_directions(
  birth: str, precision: BaziPrecision, expected: tuple[bool, bool],
) -> None:
  actual = tuple(
    BaziChart(Bazi.create(birth, 'male', BaziConfig(precision=precision, school=BaziSchool(tuwang_def=definition))))
    .wuxing_states[Wuxing.土] is WuxingState.旺
    for definition in (TuwangDef.AFTER_TWELVE_DAYS, TuwangDef.BEFORE_EIGHTEEN_DAYS)
  )
  assert actual == expected


@pytest.mark.parametrize('precision', [BaziPrecision.HOUR, BaziPrecision.MINUTE])
@pytest.mark.parametrize('longitude', [75.0, 116.4, 135.0])
def test_location_boundary_uses_aware_utc8(precision: BaziPrecision, longitude: float) -> None:
  utc8 = timezone(timedelta(hours=8))
  for definition in (TuwangDef.AFTER_TWELVE_DAYS, TuwangDef.BEFORE_EIGHTEEN_DAYS):
    config = BaziConfig(precision=precision, school=BaziSchool(tuwang_def=definition))
    opening, following = Bazi.create('2026-04-15', 'male', config).month_jies
    boundary = opening.moment + timedelta(days=12) if definition is TuwangDef.AFTER_TWELVE_DAYS else following.moment - timedelta(days=18)
    solar_boundary = apparent_solar_datetime(boundary.replace(tzinfo=utc8), longitude)
    reached = []
    for delta in (-180, -1, 0, 1, 180):
      birth = boundary.replace(tzinfo=utc8) + timedelta(minutes=delta)
      chart = BaziChart(Bazi.create(birth, 'male', config, longitude=longitude))
      expected = _truncate(chart.bazi.solar_datetime, precision) >= _truncate(solar_boundary, precision)
      assert (chart.wuxing_states[Wuxing.土] is WuxingState.旺) == expected
      reached.append(expected)
    assert not reached[0] and reached[-1]


def test_enum_defaults_identity_and_immutability() -> None:
  assert 五行状态 is WuxingState
  assert WuxingState.from_str('旺') is WuxingState.WANG
  assert tuple(field.name for field in fields(BaziSchool))[-1] == 'tuwang_def'
  assert BaziSchool().tuwang_def is TuwangDef.WHOLE_MONTH
  charts = tuple(BaziChart(Bazi.create('2026-04-15', 'male', BaziConfig(school=BaziSchool(tuwang_def=d)))) for d in TuwangDef)
  assert len({chart.bazi for chart in charts}) == 3
  assert len({chart.bazi.pillars for chart in charts}) == 1
  chart = charts[0]
  assert chart.wuxing_states is chart.wuxing_states
  assert BaziChart(chart.bazi).wuxing_states == chart.wuxing_states
  with pytest.raises(TypeError):
    chart.wuxing_states[Wuxing.木] = WuxingState.死 # type: ignore[index]
  with pytest.raises(TypeError):
    BaziSchool(tuwang_def='whole_month') # type: ignore[arg-type]


@pytest.mark.parametrize('backend', list(CalendarBackend))
def test_supported_window_ends_and_year_rollover(backend: CalendarBackend) -> None:
  utils = calendar_utils_of(backend)
  first = utils.to_date(utils.get_min_supported_date(CalendarType.公历))
  last = utils.to_date(utils.get_max_supported_date(CalendarType.公历))
  for definition in TuwangDef:
    config = BaziConfig(backend=backend, school=BaziSchool(tuwang_def=definition))
    for birth in (first, last, datetime(2025, 12, 31), datetime(2026, 1, 1)):
      value = datetime.combine(birth, datetime.min.time())
      chart = BaziChart(Bazi.create(value, 'male', config))
      assert len(chart.wuxing_states) == 5
