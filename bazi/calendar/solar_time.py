# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Apparent-solar conversion using the bundled equation-of-time table.'''

from datetime import UTC, datetime, timedelta
from typing import Final

from .celestial_data.loader import EquationOfTimeTable


_EOT_TABLE: Final[EquationOfTimeTable] = EquationOfTimeTable()


def apparent_solar_datetime(civil_instant: datetime, longitude: float) -> datetime:
  '''
  Correct a fixed-offset civil clock to a naive local apparent-solar clock.

  The circular longitude-minus-offset correction selects [-12h, 12h). EOT is
  apparent minus mean, evaluated at the exact UTC instant. Midnight carry is natural.
  '''
  assert isinstance(civil_instant, datetime)
  offset = civil_instant.utcoffset()
  assert offset is not None
  assert isinstance(longitude, float)

  utc = civil_instant.astimezone(UTC)
  equation_of_time = _EOT_TABLE.seconds_at(utc)
  half_day = timedelta(hours=12)
  correction = (timedelta(hours=longitude / 15) - offset + half_day) % timedelta(days=1) - half_day
  return civil_instant.replace(tzinfo=None) + correction + timedelta(seconds=equation_of_time)
