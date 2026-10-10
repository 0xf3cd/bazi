# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import UTC, datetime, tzinfo
from typing import Any

import pytest

from bazi.calendar.solar_time import apparent_solar_datetime


@pytest.mark.parametrize('civil,longitude,error', [
  (42, 0.0, TypeError),
  (datetime(2000, 1, 1), 0.0, ValueError),
  (datetime(2000, 1, 1, tzinfo=UTC), True, TypeError),
  (datetime(2000, 1, 1, tzinfo=UTC), '0', TypeError),
  (datetime(2000, 1, 1, tzinfo=UTC), float('nan'), ValueError),
  (datetime(2000, 1, 1, tzinfo=UTC), float('inf'), ValueError),
  (datetime(2000, 1, 1, tzinfo=UTC), -180.01, ValueError),
  (datetime(2000, 1, 1, tzinfo=UTC), 180.01, ValueError),
  (datetime(2000, 1, 1, tzinfo=UTC), 10 ** 400, ValueError),
])
def test_solar_time_public_boundary(civil: Any, longitude: Any, error: type[Exception]) -> None:
  with pytest.raises(error):
    apparent_solar_datetime(civil, longitude)


def test_solar_time_none_offset_and_real_longitude() -> None:
  class MissingOffset(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
      return None
    def dst(self, dt: datetime | None) -> None:
      return None
    def tzname(self, dt: datetime | None) -> None:
      return None
  with pytest.raises(ValueError, match='timezone-aware'):
    apparent_solar_datetime(datetime(2000, 1, 1, tzinfo=MissingOffset()), 0.0)
  instant = datetime(2000, 11, 3, 0, 50, tzinfo=UTC)
  assert apparent_solar_datetime(instant, 0) == apparent_solar_datetime(instant, 0.0)
  assert apparent_solar_datetime(instant, 0) == datetime(2000, 11, 3, 1, 6, 26, 82639)


@pytest.mark.parametrize('longitude,canonical', [(180.0, -180.0), (-0.0, 0.0)])
def test_solar_clock_meridian_and_zero_aliases(longitude: float, canonical: float) -> None:
  instant = datetime(2024, 1, 1, 12, tzinfo=UTC)
  assert apparent_solar_datetime(instant, longitude) == apparent_solar_datetime(instant, canonical)
