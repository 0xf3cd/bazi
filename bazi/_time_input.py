# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Shared location-time snapshots for chart and observation records.'''

import math

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TypedDict

from .bazi import Bazi


class _LocationTimeJson(TypedDict):
  '''Canonical location inputs and the recorded exact apparent clock.'''
  time_basis: str
  civil_time: str
  canonical_instant: str
  longitude: float
  apparent_time: str


def _location_json(bazi: Bazi) -> _LocationTimeJson:
  assert bazi.longitude is not None
  return {
    'time_basis': 'apparent_solar',
    'civil_time': bazi._canonical_civil.isoformat(),
    'canonical_instant': bazi._canonical_instant.isoformat(),
    'longitude': bazi.longitude,
    'apparent_time': bazi._clock_datetime.isoformat(),
  }


def _parse_location(data: Mapping[str, object]) -> tuple[datetime, float]:
  '''Validate each field's canonical spelling, without authenticating their relationships.

  Charts additionally reconstruct and compare; observation records do not recalculate.
  The caller validates its complete roster before calling this helper.
  '''
  moments: dict[str, datetime] = {}
  for key in ('time_basis', 'civil_time', 'canonical_instant', 'apparent_time'):
    value = data[key]
    if type(value) is not str:
      raise TypeError(f'Expected str at {key}, got {type(value)}')
    if key == 'time_basis':
      if value != 'apparent_solar':
        raise ValueError(f'Unsupported time_basis: {value}')
    else:
      moment = datetime.fromisoformat(value)
      if moment.isoformat() != value:
        raise ValueError(f'Expected canonical datetime at {key}')
      moments[key] = moment

  civil = moments['civil_time']
  if civil.utcoffset() is None:
    raise ValueError('Expected fixed-offset aware civil_time')
  instant = moments['canonical_instant']
  if instant.utcoffset() is None or instant.utcoffset() != UTC.utcoffset(instant):
    raise ValueError('Expected canonical UTC instant')
  if moments['apparent_time'].tzinfo is not None:
    raise ValueError('Expected naive apparent_time')
  longitude = data['longitude']
  if type(longitude) is not float:
    raise TypeError(f'Expected float at longitude, got {type(longitude)}')
  if (not math.isfinite(longitude) or not -180 <= longitude < 180
      or (longitude == 0 and math.copysign(1.0, longitude) < 0)):
    raise ValueError(f'Expected canonical longitude in [-180, 180), got {longitude}')
  return civil, longitude
