# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Apparent-solar conversion using the bundled equation-of-time table.'''

import math

from datetime import UTC, datetime, timedelta
from functools import cache
from numbers import Real

from .celestial_data.loader import EquationOfTimeTable


def _canonical_longitude(longitude: float) -> float:
  '''Validate east-positive degrees and canonicalize the meridian and zero aliases.'''
  longitude_input: object = longitude
  if isinstance(longitude_input, bool) or not isinstance(longitude_input, Real):
    raise TypeError(f'Expected real longitude, got {type(longitude)}')
  try:
    value = float(longitude_input)
  except OverflowError as error:
    raise ValueError('Unsupported longitude: expected finite degrees in [-180, 180].') from error
  if not math.isfinite(value) or not -180 <= value <= 180:
    raise ValueError(f'Unsupported longitude: {value}; expected finite degrees in [-180, 180].')

  if value == 0:
    return 0.0
  # +180 and -180 identify the same meridian.
  return -180.0 if value == 180 else value


@cache
def _equation_of_time_table() -> EquationOfTimeTable:
  '''Read the immutable table on first lookup, not during import.'''
  return EquationOfTimeTable()


def apparent_solar_datetime(civil_instant: datetime, longitude: float) -> datetime:
  '''
  Correct a fixed-offset civil clock to a naive local apparent-solar clock.

  Wrap longitude-minus-offset to [-12h, 12h) to use the birth region's civil date
  basis: a UTC+14 clock near 157 degrees west is a civil day ahead of its meridian.
  The resulting clock can still cross midnight. EOT is apparent minus mean,
  evaluated at the exact UTC instant.
  '''
  if not isinstance(civil_instant, datetime):
    raise TypeError(f'Expected datetime, got {type(civil_instant)}')
  offset = civil_instant.utcoffset()
  if offset is None:
    raise ValueError('Expected a timezone-aware civil datetime.')
  longitude_value = _canonical_longitude(longitude)

  utc = civil_instant.astimezone(UTC)
  equation_of_time = _equation_of_time_table().seconds_at(utc)
  half_day = timedelta(hours=12)
  correction = (timedelta(hours=longitude_value / 15) - offset + half_day) % timedelta(days=1) - half_day
  return civil_instant.replace(tzinfo=None) + correction + timedelta(seconds=equation_of_time)
