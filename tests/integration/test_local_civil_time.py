# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.calendar import CalendarDate, CalendarType
from bazi.context_matching import NatalObservation, evaluate_context
from bazi.school import BaziConfig, BaziPrecision, BaziSchool, DayRollover
from bazi import cli


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
  facts = chart.bazi.location_time
  assert facts is not None
  assert chart.bazi._clock_datetime == expected
  assert chart.bazi.solar_date == expected.date()
  assert facts.civil_time.isoformat() == civil
  assert facts.apparent_time == expected


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


def test_civil_basis_identity_meridian_aliases() -> None:
  config = BaziConfig(precision=BaziPrecision.MINUTE)
  civil = datetime.fromisoformat('2024-01-01T12:00:00+14:00')
  basis = ZoneInfo('Pacific/Kiritimati')
  original = Bazi.create(civil, 'male', config, longitude=-157.4, civil_timezone=basis)
  for zone in (UTC, timezone(timedelta(hours=-12)), ZoneInfo('America/New_York')):
    alternate = Bazi.create(civil.astimezone(zone), 'male', config, longitude=-157.4, civil_timezone=basis)
    assert alternate == original
    assert hash(alternate) == hash(original)
    assert alternate.location_time == original.location_time
  different_basis = Bazi.create(civil.astimezone(UTC), 'male', config, longitude=-157.4)
  assert different_basis != original
  assert len({original, different_basis}) == 2
  assert different_basis.solar_date == date(2023, 12, 31)
  assert original.solar_date == date(2024, 1, 1)
  for zone in (UTC, timezone(timedelta(hours=14)), timezone(timedelta(hours=-12))):
    east = Bazi.create(civil.astimezone(zone), 'male', config, longitude=180.0)
    west = Bazi.create(civil.astimezone(zone), 'male', config, longitude=-180.0)
    assert east == west and hash(east) == hash(west)
    assert east.location_time == west.location_time
    assert east.longitude == -180.0


@pytest.mark.parametrize('coordinate', ['reference', 'display'])
@pytest.mark.parametrize('precision', [BaziPrecision.HOUR, BaziPrecision.MINUTE])
def test_legacy_location_identity_partition(coordinate: str, precision: BaziPrecision) -> None:
  config = BaziConfig(precision=precision)
  location = Bazi.create('2000-01-01T12:34:00+00:00', 'female', config, longitude=0.0)
  moment = location.reference_datetime if coordinate == 'reference' else location.solar_datetime
  legacy = Bazi.create(moment, 'female', config)
  if coordinate == 'reference':
    assert legacy.reference_datetime == location.reference_datetime
  else:
    assert legacy.solar_datetime == location.solar_datetime
  assert legacy != location and location != legacy
  assert len({legacy, location}) == len({location, legacy}) == 2


def test_apparent_birth_at_lower_boundary() -> None:
  config = BaziConfig(precision=BaziPrecision.MINUTE)
  first = Bazi.create('1901-02-18T12:24:00+23:54', 'male', config, longitude=177.0)
  assert first.location_time is not None
  assert first.location_time.canonical_instant.isoformat() == '1901-02-17T12:30:00+00:00'
  assert first._clock_datetime == datetime(1901, 2, 19, 0, 3, 45, 35417)
  # Pinned source at the exact instant; the daily interpolant is an approximation.
  source_apparent = datetime(1901, 2, 19, 0, 3, 44, 914798)
  assert abs((first._clock_datetime - source_apparent).total_seconds()) < 0.16
  assert first.solar_date == date(1901, 2, 19)
  assert first._utils.to_lunar(first.solar_date) == CalendarDate(1901, 1, 1, CalendarType.LUNAR)


def test_apparent_birth_at_upper_boundary() -> None:
  config = BaziConfig(precision=BaziPrecision.MINUTE)
  last = Bazi.create('2100-01-01T12:00:00+00:00', 'male', config, longitude=-180.0)
  assert last.solar_date == date(2099, 12, 31)
  assert last._utils.to_date(last._utils.to_lunar(last.solar_date)) == date(2099, 12, 31)
  assert str(last.month_jies[1].jieqi) == '小寒'


def test_apparent_birth_rejects_outside_window() -> None:
  config = BaziConfig(precision=BaziPrecision.MINUTE)
  for civil, longitude in (
    ('1901-02-18T12:24:00+23:54', 176.0),
    ('2100-01-01T12:10:00+00:00', -180.0),
    ('2200-01-01T12:00:00+00:00', 0.0),
  ):
    with pytest.raises(ValueError):
      Bazi.create(civil, 'male', config, longitude=longitude)


@pytest.mark.parametrize('year', [1850, 2200])
def test_out_of_table_reports_birth_window(year: int) -> None:
  with pytest.raises(ValueError, match=r'apparent-solar birth date.*1901-02-19.*2099-12-31'):
    Bazi.create(datetime(year, 1, 1, 12, tzinfo=UTC), 'male',
                BaziConfig(precision=BaziPrecision.MINUTE), longitude=0.0)


@pytest.mark.parametrize('direct', [False, True])
@pytest.mark.parametrize('birth,basis', [
  pytest.param(datetime.min.replace(tzinfo=timezone(timedelta(hours=14))), None, id='utc-underflow'),
  pytest.param(datetime.max.replace(tzinfo=timezone(timedelta(hours=-12))), None, id='utc-overflow'),
  pytest.param(datetime.min.replace(tzinfo=UTC), timezone(timedelta(hours=-12)), id='civil-underflow'),
  pytest.param(datetime.max.replace(tzinfo=UTC), timezone(timedelta(hours=14)), id='civil-overflow'),
])
def test_extreme_aware_birth_reports_value_error(direct: bool, birth: datetime, basis: tzinfo | None) -> None:
  create: Any = Bazi if direct else Bazi.create
  gender = BaziGender.男 if direct else 'male'
  with pytest.raises(ValueError, match=r'apparent-solar birth date.*1901-02-19.*2099-12-31'):
    create(birth, gender, BaziConfig(precision=BaziPrecision.MINUTE), longitude=0.0, civil_timezone=basis)


def test_window_error_does_not_hide_table(monkeypatch: pytest.MonkeyPatch) -> None:
  from bazi.calendar.celestial_data.loader import EquationOfTimeTable

  def corrupt(table: EquationOfTimeTable, moment: datetime) -> float:
    raise ValueError('equation-of-time payload checksum mismatch')

  monkeypatch.setattr(EquationOfTimeTable, 'seconds_at', corrupt)
  with pytest.raises(ValueError, match='payload checksum mismatch'):
    Bazi.create('2024-01-01T12:00:00+00:00', 'male',
                BaziConfig(precision=BaziPrecision.MINUTE), longitude=0.0)


def test_next_jie_freezes_basis_across_dst(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_demo_separates_physical_jie_clocks() -> None:
  chart = BaziChart(Bazi.create('2000-02-04T07:50:00-05:00', 'male',
                               BaziConfig(precision=BaziPrecision.MINUTE), longitude=0.0))
  text = cli._get_transit_info(chart)
  assert '出生时刻前一节：立春 - 2000-02-04T20:40:23' in text
  assert '出生时刻后一节：惊蛰' in text
  assert 'UTC+08:00' in text
  for label in ('民用出生时刻', '真太阳出生时刻', '节气表出生时刻'):
    assert label in cli._get_basic_info(chart)


def test_context_keeps_exact_location_input() -> None:
  chart = BaziChart(Bazi.create('2024-01-01T12:00:00+14:00', 'female',
                               BaziConfig(precision=BaziPrecision.HOUR), longitude=-157.4))
  result = evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', observation=NatalObservation())
  assert result.bazi == chart.bazi and result.bazi.config == chart.bazi.config
  facts = result.bazi.location_time
  assert facts is not None
  assert facts.civil_time.isoformat() == '2024-01-01T12:00:00+14:00'
  assert facts.canonical_instant.isoformat() == '2023-12-31T22:00:00+00:00'
  assert facts.apparent_time.isoformat() == '2024-01-01T11:27:21.883333'
  for value in (facts.civil_time.isoformat(), facts.canonical_instant.isoformat(), facts.apparent_time.isoformat()):
    assert value in result.render()
