# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import functools

from datetime import UTC, datetime, timedelta

from .celestial_data.loader import EquationOfTimeTable


@functools.cache
def _equation_of_time_table() -> EquationOfTimeTable:
  return EquationOfTimeTable()


def apparent_solar_datetime(utc_instant: datetime, longitude: float) -> datetime:
  '''
  Convert an aware absolute instant to a naive local apparent-solar clock.

  `longitude` is east-positive degrees. The equation of time is apparent minus
  mean, so both the longitude correction and the stored value are added to UTC.
  '''
  assert isinstance(utc_instant, datetime)
  assert utc_instant.tzinfo is not None and utc_instant.utcoffset() is not None
  assert isinstance(longitude, float)

  utc = utc_instant.astimezone(UTC)
  equation_of_time = _equation_of_time_table().seconds_at(utc)
  return utc.replace(tzinfo=None) + timedelta(
    hours=longitude / 15,
    seconds=equation_of_time,
  )
