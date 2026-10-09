# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Apparent-solar conversion using the bundled equation-of-time table.'''

import math

from datetime import UTC, datetime, timedelta
from numbers import Real
from typing import Final

from .celestial_data.loader import EquationOfTimeTable


_EOT_TABLE: Final[EquationOfTimeTable] = EquationOfTimeTable()


def apparent_solar_datetime(civil_instant: datetime, longitude: float) -> datetime:
  '''
  Correct a fixed-offset civil clock to a naive local apparent-solar clock.

  The circular longitude-minus-offset correction selects [-12h, 12h). EOT is
  apparent minus mean, evaluated at the exact UTC instant. Midnight carry is natural.
  '''
  if not isinstance(civil_instant, datetime):
    raise TypeError(f'Expected datetime, got {type(civil_instant)}')
  offset = civil_instant.utcoffset()
  if offset is None:
    raise ValueError('Expected a timezone-aware civil datetime.')
  longitude_input: object = longitude
  if isinstance(longitude_input, bool) or not isinstance(longitude_input, Real):
    raise TypeError(f'Expected real longitude, got {type(longitude)}')
  try:
    longitude_value = float(longitude_input)
  except OverflowError as error:
    raise ValueError('Expected finite longitude in [-180, 180].') from error
  if not math.isfinite(longitude_value) or not -180 <= longitude_value <= 180:
    raise ValueError('Expected finite longitude in [-180, 180].')

  utc = civil_instant.astimezone(UTC)
  equation_of_time = _EOT_TABLE.seconds_at(utc)
  half_day = timedelta(hours=12)
  correction = (timedelta(hours=longitude_value / 15) - offset + half_day) % timedelta(days=1) - half_day
  return civil_instant.replace(tzinfo=None) + correction + timedelta(seconds=equation_of_time)
