# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import UTC, datetime, timedelta, timezone, tzinfo
from typing import Any

import pytest

from bazi.calendar.solar_time import apparent_solar_datetime
from bazi.calendar.celestial_data.loader import EquationOfTimeTable


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


@pytest.mark.parametrize('moment', [
  datetime.min.replace(tzinfo=timezone(timedelta(hours=14))),
  datetime.max.replace(tzinfo=timezone(timedelta(hours=-12))),
])
@pytest.mark.parametrize('table_reader', [False, True])
def test_extreme_aware_conversion_is_a_value_error(moment: datetime, table_reader: bool) -> None:
  with pytest.raises(ValueError, match='Unsupported UTC instant'):
    if table_reader:
      EquationOfTimeTable().seconds_at(moment)
    else:
      apparent_solar_datetime(moment, 0.0)
