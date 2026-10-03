# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Apparent-solar conversion using the bundled equation-of-time table.'''

from datetime import UTC, datetime, timedelta
from typing import Final

from .celestial_data.loader import EquationOfTimeTable


_EOT_TABLE: Final[EquationOfTimeTable] = EquationOfTimeTable()


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
  equation_of_time = _EOT_TABLE.seconds_at(utc)
  return utc.replace(tzinfo=None) + timedelta(
    hours=longitude / 15,
    seconds=equation_of_time,
  )
