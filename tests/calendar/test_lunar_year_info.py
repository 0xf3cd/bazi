# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date
from typing import get_type_hints

from bazi.calendar.dates import LunarYearInfo
from bazi.calendar.hko_data import LunarYearInfo as HkoInfo
from bazi.calendar.hko_data.decoder import LunarYearInfo as DecoderInfo
from bazi.calendar.celestial_data.loader import LunarYearInfo as CelestialInfo
from bazi.defines import Ganzhi


def test_canonical_type_and_old_imports() -> None:
  assert LunarYearInfo is HkoInfo is DecoderInfo is CelestialInfo
  assert LunarYearInfo.__module__ == 'bazi.calendar.dates'
  assert get_type_hints(LunarYearInfo) == {
    'first_solar_day': date, 'leap': bool, 'leap_month': int | None,
    'days_counts': list[int], 'ganzhi': Ganzhi,
  }
  value = LunarYearInfo(first_solar_day=date(2000, 2, 5), leap=False, leap_month=None, days_counts=[30], ganzhi=Ganzhi.from_str('庚辰'))
  assert type(value) is dict
  value['days_counts'].append(29)
  assert value['days_counts'] == [30, 29]
