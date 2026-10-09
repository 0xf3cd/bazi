# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.calendar import CalendarDate, CalendarType
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context
from bazi.school import BaziConfig, BaziPrecision, BaziSchool, DayRollover
from run_demo import get_basic_info, get_transit_info


@pytest.mark.parametrize('precision', [BaziPrecision.HOUR, BaziPrecision.MINUTE])
@pytest.mark.parametrize('civil, longitude, apparent', [
  pytest.param('2024-01-01T12:00:00+14:00', -157.4, '2024-01-01T11:27:21.883333', id='Kiritimati'),
  pytest.param('2024-01-01T12:00:00+13:00', -171.75, '2024-01-01T11:29:56.691667', id='Apia'),
  pytest.param('2024-01-01T12:00:00+12:00', 179.0, '2024-01-01T11:52:55.500000', id='east-date-line'),
  pytest.param('2024-01-01T12:00:00-12:00', -179.0, '2024-01-01T12:00:27.100000', id='west-date-line'),
  pytest.param('2024-01-01T12:00:00+08:00', 116.4, '2024-01-01T11:42:26.766667', id='China'),
  pytest.param('2024-01-01T12:00:00+00:00', 0.0, '2024-01-01T11:56:41.300000', id='Greenwich'),
  pytest.param('2024-01-01T12:00:00-05:00', -74.0, '2024-01-01T12:00:35.383333', id='New-York'),
  pytest.param('2024-01-01T00:10:00+08:00', 116.4, '2023-12-31T23:52:40.834722', id='midnight-back'),
  pytest.param('2000-11-03T23:50:00+00:00', 0.0, '2000-11-04T00:06:25.603472', id='midnight-forward'),
  pytest.param('1920-01-01T12:34:56.123456+07:45:20', 116.4, '1920-01-01T12:32:07.771637', id='caller-owned-pre1929'),
])
def test_named_civil_clocks(precision: BaziPrecision, civil: str, longitude: float, apparent: str) -> None:
  chart = BaziChart(Bazi.create(civil, 'male', BaziConfig(precision=precision), longitude=longitude))
  expected = datetime.fromisoformat(apparent)
  assert chart.bazi._clock_datetime == expected
  assert chart.bazi.solar_date == expected.date()
  assert chart.bazi._canonical_civil.isoformat() == civil
  assert chart.json['apparent_time'] == expected.isoformat()
  assert BaziChart.from_json(chart.json).json == chart.json


@pytest.mark.parametrize('precision', [BaziPrecision.HOUR, BaziPrecision.MINUTE])
@pytest.mark.parametrize('rollover', list(DayRollover))
def test_midnight_carry_obeys_both_day_profiles(precision: BaziPrecision, rollover: DayRollover) -> None:
  config = BaziConfig(precision=precision, school=BaziSchool(day_rollover=rollover))
  chart = Bazi.create('2024-01-01T00:10:00+08:00', 'female', config, longitude=116.4)
  legacy = Bazi.create('2023-12-31T23:52:40', 'female', config)
  assert chart.solar_date == date(2023, 12, 31)
  assert chart.day_pillar == legacy.day_pillar
  assert chart.hour_pillar == legacy.hour_pillar
  other = Bazi.create('2024-01-01T00:10:00+08:00', 'female', replace(config, school=BaziSchool(
    day_rollover=DayRollover.ZIZHENG if rollover is DayRollover.WAN_ZISHI else DayRollover.WAN_ZISHI,
  )), longitude=116.4)
  assert chart.day_pillar != other.day_pillar


def test_civil_basis_identity_and_meridian_aliases() -> None:
  config = BaziConfig(precision=BaziPrecision.MINUTE)
  civil = datetime.fromisoformat('2024-01-01T12:00:00+14:00')
  basis = ZoneInfo('Pacific/Kiritimati')
  original = Bazi.create(civil, 'male', config, longitude=-157.4, civil_timezone=basis)
  for zone in (UTC, timezone(timedelta(hours=-12)), ZoneInfo('America/New_York')):
    alternate = Bazi.create(civil.astimezone(zone), 'male', config, longitude=-157.4, civil_timezone=basis)
    assert alternate == original
    assert hash(alternate) == hash(original)
    assert BaziChart(alternate).json == BaziChart(original).json
  different_basis = Bazi.create(civil.astimezone(UTC), 'male', config, longitude=-157.4)
  assert different_basis != original
  assert len({original, different_basis}) == 2
  assert different_basis.solar_date == date(2023, 12, 31)
  assert original.solar_date == date(2024, 1, 1)
  for zone in (UTC, timezone(timedelta(hours=14)), timezone(timedelta(hours=-12))):
    east = Bazi.create(civil.astimezone(zone), 'male', config, longitude=180.0)
    west = Bazi.create(civil.astimezone(zone), 'male', config, longitude=-180.0)
    assert east == west and hash(east) == hash(west)
    assert BaziChart(east).json == BaziChart(west).json
    assert east.longitude == -180.0


@pytest.mark.parametrize('coordinate', ['reference', 'display'])
@pytest.mark.parametrize('precision', [BaziPrecision.HOUR, BaziPrecision.MINUTE])
def test_legacy_location_identity_partition(coordinate: str, precision: BaziPrecision) -> None:
  config = BaziConfig(precision=precision)
  location = Bazi.create('2000-01-01T12:34:00+00:00', 'female', config, longitude=0.0)
  moment = location._reference_datetime if coordinate == 'reference' else location.solar_datetime
  legacy = Bazi.create(moment, 'female', config)
  if coordinate == 'reference':
    assert legacy._reference_datetime == location._reference_datetime
  else:
    assert legacy.solar_datetime == location.solar_datetime
  assert legacy != location and location != legacy
  assert len({legacy, location}) == len({location, legacy}) == 2


def test_leading_corner_and_apparent_birth_window() -> None:
  config = BaziConfig(precision=BaziPrecision.MINUTE)
  first = Bazi.create('1901-02-18T12:24:00+23:54', 'male', config, longitude=177.0)
  assert first._canonical_instant == datetime(1901, 2, 17, 12, 30, tzinfo=UTC)
  assert first._clock_datetime == datetime(1901, 2, 19, 0, 3, 45, 35417)
  # Pinned source at the exact instant; the daily interpolant is an approximation.
  source_apparent = datetime(1901, 2, 19, 0, 3, 44, 914798)
  assert abs((first._clock_datetime - source_apparent).total_seconds()) < 0.16
  assert first.solar_date == date(1901, 2, 19)
  assert first._utils.to_lunar(first.solar_date) == CalendarDate(1901, 1, 1, CalendarType.LUNAR)
  last = Bazi.create('2100-01-01T12:00:00+00:00', 'male', config, longitude=-180.0)
  assert last.solar_date == date(2099, 12, 31)
  assert last._utils.to_date(last._utils.to_lunar(last.solar_date)) == date(2099, 12, 31)
  assert str(last.bracketing_jies[1].jieqi) == '小寒'
  for civil, longitude in (
    ('1901-02-18T12:24:00+23:54', 176.0),
    ('2100-01-01T12:10:00+00:00', -180.0),
    ('2200-01-01T12:00:00+00:00', 0.0),
  ):
    with pytest.raises(ValueError):
      Bazi.create(civil, 'male', config, longitude=longitude)


def test_next_jie_uses_frozen_birth_basis_across_dst(monkeypatch: pytest.MonkeyPatch) -> None:
  from bazi.calendar import solar_time
  original = solar_time.apparent_solar_datetime
  projected: list[datetime] = []

  def capture(civil: datetime, longitude: float) -> datetime:
    projected.append(civil)
    return original(civil, longitude)

  monkeypatch.setattr(solar_time, 'apparent_solar_datetime', capture)
  birth = Bazi.create('2024-03-09T12:00:00-05:00', 'male', BaziConfig(precision=BaziPrecision.MINUTE),
                      longitude=-74.0, civil_timezone=ZoneInfo('America/New_York'))
  assert [moment.utcoffset() for moment in projected] == [timedelta(hours=-5), timedelta(hours=-5)]
  assert projected[1].date() == date(2024, 4, 4)
  assert str(birth.month_pillar) == '丁卯'


@pytest.mark.parametrize('direct', [False, True])
def test_civil_timezone_invalid_inputs(direct: bool) -> None:
  create: Any = Bazi if direct else Bazi.create
  gender = BaziGender.男 if direct else 'male'
  config = BaziConfig(precision=BaziPrecision.MINUTE)
  with pytest.raises(TypeError, match='tzinfo'):
    create(datetime(2000, 1, 1, tzinfo=UTC), gender, config, longitude=0.0, civil_timezone='+08:00')
  with pytest.raises(ValueError, match='requires longitude'):
    create(datetime(2000, 1, 1), gender, config, civil_timezone=UTC)

  class MissingOffset(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
      return None
    def dst(self, dt: datetime | None) -> None:
      return None
    def tzname(self, dt: datetime | None) -> None:
      return None
    def fromutc(self, dt: datetime) -> datetime:
      return dt

  with pytest.raises(ValueError, match='UTC offset'):
    create(datetime(2000, 1, 1, tzinfo=UTC), gender, config, longitude=0.0, civil_timezone=MissingOffset())
  with pytest.raises(ValueError, match='timezone-aware birth_time'):
    create(datetime(2000, 1, 1, tzinfo=MissingOffset()), gender, config, longitude=0.0)


def test_demo_uses_physical_jies_and_distinguishes_clocks() -> None:
  chart = BaziChart(Bazi.create('2000-02-04T07:50:00-05:00', 'male',
                               BaziConfig(precision=BaziPrecision.MINUTE), longitude=0.0))
  text = get_transit_info(chart)
  assert '出生时刻前一节：立春 - 2000-02-04T20:40:23' in text
  assert '出生时刻后一节：惊蛰' in text
  assert 'UTC+08:00' in text
  for label in ('民用出生时刻', '真太阳出生时刻', '物理出生时刻'):
    assert label in get_basic_info(chart)


def test_location_context_snapshot_is_observational() -> None:
  chart = BaziChart(Bazi.create('2024-01-01T12:00:00+14:00', 'female',
                               BaziConfig(precision=BaziPrecision.HOUR), longitude=-157.4))
  result = evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', profile=ContextProfile('natal'))
  data = json.loads(result.export_json())
  assert set(data['input']) == {'time_basis', 'civil_time', 'canonical_instant', 'longitude', 'apparent_time', 'gender', 'config', 'pillars'}
  assert data['input']['civil_time'] == '2024-01-01T12:00:00+14:00'
  assert data['input']['canonical_instant'] == '2023-12-31T22:00:00+00:00'
  assert ContextResult.from_json(result.export_json()) == result
  data['input']['apparent_time'] = '2000-01-01T12:00:00'
  data['input']['pillars'][0] = '甲子'
  restored = ContextResult.from_json(json.dumps(data))
  assert restored.criterion == result.criterion and restored.occurrences == result.occurrences
  assert json.loads(restored.input_json)['apparent_time'] == '2000-01-01T12:00:00'
  for identity in (
    {**data['input'], 'birth_time': '2024-01-01T12:00:00'},
    {key: value for key, value in data['input'].items() if key != 'civil_time'},
    {key: value for key, value in data['input'].items() if key != 'time_basis'},
  ):
    with pytest.raises(ValueError):
      ContextResult.from_json(json.dumps({**data, 'input': identity}))


@pytest.mark.parametrize('key,value,error', [
  ('civil_time', 42, TypeError),
  ('time_basis', 42, TypeError),
  ('canonical_instant', 42, TypeError),
  ('apparent_time', 42, TypeError),
  ('civil_time', 'not-a-datetime', ValueError),
  ('canonical_instant', 'not-a-datetime', ValueError),
  ('apparent_time', 'not-a-datetime', ValueError),
  ('civil_time', '2024-01-01T12:00:00', ValueError),
  ('civil_time', '2024-01-01T12:00+14:00', ValueError),
  ('canonical_instant', '2023-12-31T22:00:00+01:00', ValueError),
  ('canonical_instant', '2023-12-31T22:00:00', ValueError),
  ('apparent_time', '2024-01-01T11:27:21.883333+00:00', ValueError),
  ('longitude', 180.0, ValueError),
  ('longitude', float('nan'), ValueError),
  ('time_basis', 'mean_solar', ValueError),
])
def test_location_record_canonical_fields(key: str, value: object, error: type[Exception]) -> None:
  chart = BaziChart(Bazi.create('2024-01-01T12:00:00+14:00', 'female',
                               BaziConfig(precision=BaziPrecision.MINUTE), longitude=-157.4))
  bad: dict[str, object] = dict(chart.json)
  bad[key] = value
  with pytest.raises(error):
    BaziChart.from_json(bad)
  result = evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', profile=ContextProfile('natal'))
  data = json.loads(result.export_json())
  data['input'][key] = value
  with pytest.raises(error):
    ContextResult.from_json(json.dumps(data))
