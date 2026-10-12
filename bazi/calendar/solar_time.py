# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''使用随库均时差表换算真太阳时。'''

import math

from datetime import datetime, timedelta
from functools import cache
from numbers import Real

from .celestial_data.loader import EquationOfTimeTable, _utc_instant


def _canonical_longitude(longitude: float) -> float:
  '''校验东经为正的角度，并规范同一子午线及正负零的别名。'''
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
  # +180 与 -180 为同一子午线。
  return -180.0 if value == 180 else value


@cache
def _equation_of_time_table() -> EquationOfTimeTable:
  '''首次查询时读取不可变表，导入时不读取。'''
  return EquationOfTimeTable()


def apparent_solar_datetime(civil_instant: datetime, longitude: float) -> datetime:
  '''
  把固定偏移的民用钟换算为无时区的当地真太阳钟。

  经度与时区偏移之差回绕到 [-12h, 12h)，保留出生地区的民用日期基准；
  例如西经约 157 度的 UTC+14 民用钟比该子午线提前一日。
  换算仍可跨午夜；EOT 为真太阳时减平太阳时，在精确 UTC 瞬间求值。
  '''
  if not isinstance(civil_instant, datetime):
    raise TypeError(f'Expected datetime, got {type(civil_instant)}')
  offset = civil_instant.utcoffset()
  if offset is None:
    raise ValueError('Expected a timezone-aware civil datetime.')
  longitude_value = _canonical_longitude(longitude)

  utc = _utc_instant(civil_instant)
  equation_of_time = _equation_of_time_table().seconds_at(utc)
  half_day = timedelta(hours=12)
  correction = (timedelta(hours=longitude_value / 15) - offset + half_day) % timedelta(days=1) - half_day
  return civil_instant.replace(tzinfo=None) + correction + timedelta(seconds=equation_of_time)
