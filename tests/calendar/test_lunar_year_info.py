# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from bazi.calendar.dates import LunarYearInfo
from bazi.calendar.celestial_data.loader import LunarYearTable
from bazi.defines import Ganzhi

from hko_data import DecodedLunarYears


@pytest.mark.parametrize('info', [
  LunarYearTable().get(2000),
  DecodedLunarYears().get(2000),
], ids=['runtime-table', 'hko-reference'])
def test_decoded_records_are_immutable(info: LunarYearInfo) -> None:
  assert info == LunarYearInfo(
    first_solar_day=date(2000, 2, 5),
    leap=False,
    leap_month=None,
    days_counts=(30, 30, 29, 29, 30, 29, 29, 30, 29, 30, 30, 29),
    ganzhi=Ganzhi.from_str('庚辰'),
  )
  with pytest.raises(FrozenInstanceError):
    info.leap_month = 7 # type: ignore[misc] # Deliberately attempt to mutate a frozen field.
  with pytest.raises(TypeError):
    info.days_counts[0] = 29 # type: ignore[index] # Nested month lengths must also be immutable.
