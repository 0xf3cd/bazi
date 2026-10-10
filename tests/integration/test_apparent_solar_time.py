# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import json
import math

from datetime import UTC, date, datetime, timedelta, timezone
from fractions import Fraction
from typing import cast
from zoneinfo import ZoneInfo

import pytest

from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart, BaziJson
from bazi.calendar import CalendarBackend
from bazi.defines import Dizhi
from bazi.school import BaziConfig, BaziPrecision
from bazi.transit_chart import TransitChart


HOUR_CONFIG = BaziConfig(precision=BaziPrecision.HOUR)
MINUTE_CONFIG = BaziConfig(precision=BaziPrecision.MINUTE)


def _construct(
  direct: bool,
  birth_time: datetime,
  config: BaziConfig,
  longitude: object,
) -> Bazi:
  if direct:
    return Bazi(
      birth_time,
      BaziGender.男,
      config,
      longitude=longitude, # type: ignore[arg-type]
    )
  return Bazi.create(
    birth_time,
    'male',
    config,
    longitude=longitude, # type: ignore[arg-type]
  )


@pytest.mark.parametrize('direct', [False, True])
def test_location_input_matrix(direct: bool) -> None:
  aware = datetime(2000, 1, 1, 12, tzinfo=UTC)
  naive = aware.replace(tzinfo=None)

  with pytest.raises(ValueError, match='Timezone'):
    _construct(direct, aware, MINUTE_CONFIG, None)
  with pytest.raises(ValueError, match='timezone-aware'):
    _construct(direct, naive, MINUTE_CONFIG, 120.0)

  for value in (False, '120', 120j, object()):
    with pytest.raises(TypeError, match='real longitude'):
      _construct(direct, aware, MINUTE_CONFIG, value)
  for value in (float('-inf'), float('inf'), float('nan')):
    with pytest.raises(ValueError, match='finite'):
      _construct(direct, aware, MINUTE_CONFIG, value)
  for value in (-180.01, 180.01):
    with pytest.raises(ValueError, match=r'\[-180, 180\]'):
      _construct(direct, aware, MINUTE_CONFIG, value)

  unsupported = (
    BaziConfig(precision=BaziPrecision.DAY),
    BaziConfig(precision=BaziPrecision.MINUTE, backend=CalendarBackend.HKO),
    BaziConfig(precision=BaziPrecision.MINUTE, backend=CalendarBackend.CELESTIAL_ALGO2),
  )
  for config in unsupported:
    with pytest.raises(ValueError, match='Longitude requires'):
      _construct(direct, aware, config, 120.0)


@pytest.mark.parametrize('direct', [False, True])
@pytest.mark.parametrize('kind', ['integer', 'fraction'])
@pytest.mark.parametrize('sign', [-1, 1])
def test_overflowing_real_longitude_is_a_bounded_value_error(direct: bool, kind: str, sign: int) -> None:
  integer = sign * 10 ** 10_000
  longitude = integer if kind == 'integer' else Fraction(integer, 3)
  with pytest.raises(ValueError) as error:
    _construct(direct, datetime(2000, 1, 1, 12, tzinfo=UTC), MINUTE_CONFIG, longitude)
  assert str(error.value) == 'Unsupported longitude: expected finite degrees in [-180, 180].'


@pytest.mark.parametrize('direct', [False, True])
def test_location_validation_precedence(direct: bool) -> None:
  unsupported = BaziConfig(precision=BaziPrecision.DAY, backend=CalendarBackend.HKO)
  with pytest.raises(TypeError, match='real longitude'):
    _construct(direct, datetime(2000, 1, 1), unsupported, False)
  with pytest.raises(ValueError, match='finite'):
    _construct(direct, datetime(2000, 1, 1), unsupported, float('nan'))
  with pytest.raises(ValueError, match='timezone-aware'):
    _construct(direct, datetime(2000, 1, 1), unsupported, 0.0)
  with pytest.raises(ValueError, match='CalendarBackend.CELESTIAL'):
    _construct(direct, datetime(2000, 1, 1, tzinfo=UTC), unsupported, 0.0)


def test_create_accepts_offset_iso_but_not_latitude() -> None:
  with pytest.raises(ValueError, match='Timezone'):
    Bazi.create('2000-01-01T12:00:00+00:00', 'male', MINUTE_CONFIG)
  with pytest.raises(ValueError, match='timezone-aware'):
    Bazi.create('2000-01-01T12:00:00', 'male', MINUTE_CONFIG, longitude=30.0)

  bazi = Bazi.create(
    '2000-01-01T07:00:00-05:00',
    'male',
    MINUTE_CONFIG,
    longitude=30,
  )
  assert bazi._reference_datetime == datetime(2000, 1, 1, 20)
  assert bazi.longitude == 30.0
  with pytest.raises(TypeError, match='latitude'):
    Bazi.create( # type: ignore[call-arg]
      '2000-01-01T12:00:00+00:00',
      'male',
      MINUTE_CONFIG,
      longitude=30.0,
      latitude=10.0,
    )


def test_eot_alone_crosses_a_shichen_boundary() -> None:
  # Meeus' early-November positive EOT moves mean 00:50 to apparent 01:06. At
  # longitude zero, longitude contributes nothing: EOT alone changes 子时 to 丑时.
  bazi = Bazi.create(
    '2000-11-03T00:50:00+00:00',
    'male',
    HOUR_CONFIG,
    longitude=0.0,
  )
  assert bazi.solar_datetime == datetime(2000, 11, 3, 1, 6)
  assert bazi.hour == 1
  assert bazi.hour_pillar.dizhi is Dizhi.丑


@pytest.mark.parametrize('birth_time, longitude, absolute_after, apparent_after, pillars', [
  # 立春 2000 = 2000-02-04 20:40:23 UTC+08:00. Absolute is after it while
  # apparent time and the caller's UTC-05:00 civil label precede the unprojected UTC+08:00 label.
  ('2000-02-04T07:50:00-05:00', 0.0, True, False, ('庚辰', '戊寅')),
  # Absolute is before 立春 while +150° apparent time and the caller's UTC+14:00
  # civil label follow the unprojected UTC+08:00 label.
  ('2000-02-05T02:30:00+14:00', 150.0, False, True, ('己卯', '丁丑')),
])
def test_jie_attribution_does_not_mix_apparent_and_physical_frames(
  birth_time: str,
  longitude: float,
  absolute_after: bool,
  apparent_after: bool,
  pillars: tuple[str, str],
) -> None:
  bazi = Bazi.create(birth_time, 'male', MINUTE_CONFIG, longitude=longitude)
  jie = datetime(2000, 2, 4, 20, 40, 23)
  assert (bazi._reference_datetime > jie) is absolute_after
  assert (bazi.solar_datetime > jie) is apparent_after
  assert (str(bazi.year_pillar), str(bazi.month_pillar)) == pillars


def test_apparent_clock_drives_date_day_hour_and_both_longitude_signs() -> None:
  instant = '2000-01-01T12:00:00+00:00'
  east = Bazi.create(instant, 'male', MINUTE_CONFIG, longitude=30.0)
  west = Bazi.create(instant, 'male', MINUTE_CONFIG, longitude=-30.0)
  rollover = Bazi.create(instant, 'male', MINUTE_CONFIG, longitude=-180.0)

  assert east.solar_datetime == datetime(2000, 1, 1, 13, 56)
  assert west.solar_datetime == datetime(2000, 1, 1, 9, 56)
  assert east.hour_pillar.dizhi is Dizhi.未
  assert west.hour_pillar.dizhi is Dizhi.巳
  assert rollover.solar_datetime == datetime(1999, 12, 31, 23, 56)
  assert rollover.solar_date == date(1999, 12, 31)
  assert str(rollover.day_pillar) == '戊午'
  assert rollover.ganzhi_date == rollover._utils.to_ganzhi(date(1999, 12, 31))


def test_dayun_and_transit_lower_bounds_use_absolute_time() -> None:
  instant = datetime(2000, 1, 1, 12, tzinfo=UTC)
  east = BaziChart(Bazi.create(instant, 'male', MINUTE_CONFIG, longitude=120.0))
  west = BaziChart(Bazi.create(instant, 'male', MINUTE_CONFIG, longitude=-180.0))
  absolute = BaziChart(Bazi.create(datetime(2000, 1, 1, 20), 'male', MINUTE_CONFIG))

  assert east.dayun_start_moment == west.dayun_start_moment == absolute.dayun_start_moment
  assert [dayun.start_moment for dayun in east.dayun] == [dayun.start_moment for dayun in west.dayun]

  transits = TransitChart(west)
  assert west.bazi.solar_date == date(1999, 12, 31)
  assert transits.at_date(date(1999, 12, 31)) is None
  assert transits.at_date(date(2000, 1, 1)) is not None
  assert transits.at_moment(datetime(2000, 1, 1, 19, 59)) is None
  assert transits.at_moment(datetime(2000, 1, 1, 20, 0)) is not None


def test_same_instant_offset_identity_and_canonical_json() -> None:
  utc = Bazi.create(
    '2000-01-01T12:34:56+00:00',
    'female',
    MINUTE_CONFIG,
    longitude=116.4,
  )
  offset = Bazi.create(
    '2000-01-01T07:34:56-05:00',
    'female',
    MINUTE_CONFIG,
    longitude=116.4,
    civil_timezone=UTC,
  )
  other_longitude = Bazi.create(
    '2000-01-01T12:34:00+00:00',
    'female',
    MINUTE_CONFIG,
    longitude=116.5,
  )

  assert utc == offset
  assert hash(utc) == hash(offset)
  assert BaziChart(utc).json == BaziChart(offset).json
  assert utc != other_longitude
  assert len({utc, offset, other_longitude}) == 2


def test_dst_fold_is_an_absolute_instant_distinction() -> None:
  zone = ZoneInfo('America/New_York')
  fold0 = datetime(2024, 11, 3, 1, 30, tzinfo=zone, fold=0)
  fold1 = datetime(2024, 11, 3, 1, 30, tzinfo=zone, fold=1)
  first = Bazi.create(fold0, 'male', MINUTE_CONFIG, longitude=-74.0)
  second = Bazi.create(fold1, 'male', MINUTE_CONFIG, longitude=-74.0)
  same_first = Bazi.create(
    fold0.astimezone(timezone(timedelta(hours=9))),
    'male',
    MINUTE_CONFIG,
    longitude=-74.0,
    civil_timezone=zone,
  )

  assert first == same_first
  assert hash(first) == hash(same_first)
  assert first != second
  first_json = cast(BaziJson.LocationBaziChartJsonDict, BaziChart(first).json)
  second_json = cast(BaziJson.LocationBaziChartJsonDict, BaziChart(second).json)
  assert first_json['canonical_instant'] == '2024-11-03T05:30:00+00:00'
  assert second_json['canonical_instant'] == '2024-11-03T06:30:00+00:00'


def test_location_json_roster_roundtrip_and_tampering() -> None:
  chart = BaziChart(Bazi.create(
    '2000-01-01T07:34:00-05:00',
    'female',
    MINUTE_CONFIG,
    longitude=116.4,
  ))
  data = json.loads(json.dumps(chart.json))
  assert set(data) == BaziChart(chart.bazi).json.keys()
  assert {'time_basis', 'canonical_instant', 'longitude', 'apparent_time'} <= set(data)
  assert 'birth_time' not in data
  assert BaziChart.from_json(data).json == chart.json

  legacy = dict(BaziChart(Bazi.create('2000-01-01T12:34:00', 'female')).json)
  for mixed in (
    {**data, 'birth_time': legacy['birth_time']},
    {**legacy, 'longitude': 116.4},
    {**data, 'unknown': 'value'},
  ):
    with pytest.raises(ValueError, match='roster'):
      BaziChart.from_json(mixed)

  for key, value in (
    ('time_basis', 'mean_solar'),
    ('canonical_instant', '2000-01-01T12:35+00:00'),
    ('longitude', 116.5),
  ):
    tampered = copy.deepcopy(data)
    tampered[key] = value
    with pytest.raises(ValueError):
      BaziChart.from_json(tampered)

  non_float_longitude = copy.deepcopy(data)
  non_float_longitude['longitude'] = 116
  with pytest.raises(TypeError, match='float at longitude'):
    BaziChart.from_json(non_float_longitude)

  zero_chart = BaziChart(Bazi.create(
    '2000-01-01T12:34:00+00:00',
    'female',
    MINUTE_CONFIG,
    longitude=0.0,
  ))
  negative_zero_longitude = copy.deepcopy(cast(BaziJson.LocationBaziChartJsonDict, zero_chart.json))
  negative_zero_longitude['longitude'] = -0.0
  with pytest.raises(ValueError, match='canonical longitude'):
    BaziChart.from_json(negative_zero_longitude)

  derived = copy.deepcopy(data)
  derived['pillars']['hour'] = '甲子'
  with pytest.raises(ValueError, match='pillars.hour'):
    BaziChart.from_json(derived)


@pytest.mark.parametrize('birth_time, pillars, hour_dizhi', [
  # The birth is 戌时, before 惊蛰's apparent 亥时, despite sharing its UTC+08:00 巳时.
  ('2024-03-05T01:52:45+00:00', ('甲辰', '丙寅'), Dizhi.戌),
  # Both are apparent 丑时, though the UTC+08:00 labels straddle 15:00 at 清明.
  ('2024-04-04T06:32:16+00:00', ('甲辰', '戊辰'), Dizhi.丑),
  # 立春 also controls the year: apparent 丑时 is old, apparent 寅时 is new.
  ('2024-02-04T07:27:06+00:00', ('癸卯', '乙丑'), Dizhi.丑),
  ('2024-02-04T08:22:06+00:00', ('甲辰', '丙寅'), Dizhi.寅),
])
def test_hour_jie_ties_use_apparent_shichen(
  birth_time: str,
  pillars: tuple[str, str],
  hour_dizhi: Dizhi,
) -> None:
  bazi = Bazi.create(birth_time, 'male', HOUR_CONFIG, longitude=-74.0)
  assert (str(bazi.year_pillar), str(bazi.month_pillar)) == pillars
  assert bazi.hour_pillar.dizhi is hour_dizhi


@pytest.mark.parametrize('birth_time, pillars', [
  # Different UTC minutes, same apparent 03:17 minute as 立春.
  ('2024-02-04T08:26:59+00:00', ('甲辰', '丙寅')),
  # Same UTC minute, apparent 21:14 before 惊蛰's 21:15 minute.
  ('2024-03-05T02:22:25+00:00', ('甲辰', '丙寅')),
])
def test_minute_jie_ties_use_apparent_minutes(birth_time: str, pillars: tuple[str, str]) -> None:
  bazi = Bazi.create(birth_time, 'male', MINUTE_CONFIG, longitude=-74.0)
  assert (str(bazi.year_pillar), str(bazi.month_pillar)) == pillars


@pytest.mark.parametrize('config', [HOUR_CONFIG, MINUTE_CONFIG])
def test_seconds_are_preserved_before_apparent_conversion(config: BaziConfig) -> None:
  chart = BaziChart(Bazi.create(
    '2000-11-03T00:43:59+00:00',
    'male',
    config,
    longitude=0.0,
  ))
  floored = Bazi.create('2000-11-03T00:43:00+00:00', 'male', config, longitude=0.0)
  assert chart.bazi.solar_datetime == datetime(2000, 11, 3, 1, 0)
  assert chart.bazi.hour_pillar.dizhi is Dizhi.丑
  assert floored.hour_pillar.dizhi is Dizhi.子
  assert chart.bazi != floored
  data = cast(BaziJson.LocationBaziChartJsonDict, chart.json)
  assert data['canonical_instant'] == '2000-11-03T00:43:59+00:00'
  assert data['apparent_time'] == '2000-11-03T01:00:25.084728'
  assert BaziChart.from_json(json.loads(json.dumps(chart.json))).json == chart.json


def test_exact_instant_identity_and_microsecond_roundtrip() -> None:
  chart = BaziChart(Bazi.create(
    '2000-01-01T12:34:56.123456+00:00',
    'female',
    MINUTE_CONFIG,
    longitude=116.4,
  ))
  offset = Bazi.create(
    '2000-01-01T07:34:56.123456-05:00',
    'female',
    MINUTE_CONFIG,
    longitude=116.4,
    civil_timezone=UTC,
  )
  other_second = Bazi.create(
    '2000-01-01T12:34:57.123456+00:00',
    'female',
    MINUTE_CONFIG,
    longitude=116.4,
  )
  assert chart.bazi == offset
  assert hash(chart.bazi) == hash(offset)
  assert chart.bazi.solar_datetime == other_second.solar_datetime
  assert chart.bazi != other_second
  assert cast(BaziJson.LocationBaziChartJsonDict, chart.json)['canonical_instant'] == '2000-01-01T12:34:56.123456+00:00'
  assert BaziChart.from_json(json.loads(json.dumps(chart.json))).json == chart.json


@pytest.mark.parametrize('direct', [False, True])
def test_negative_zero_longitude_emits_canonical_roundtrippable_json(direct: bool) -> None:
  chart = BaziChart(_construct(
    direct,
    datetime(2000, 1, 1, 12, tzinfo=UTC),
    MINUTE_CONFIG,
    -0.0,
  ))
  longitude = chart.bazi.longitude
  assert longitude is not None
  assert math.copysign(1.0, longitude) == 1.0
  data = cast(BaziJson.LocationBaziChartJsonDict, chart.json)
  assert data['longitude'] == 0.0
  assert math.copysign(1.0, data['longitude']) == 1.0
  assert BaziChart.from_json(json.loads(json.dumps(chart.json))).json == chart.json
