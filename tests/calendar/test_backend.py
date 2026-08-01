# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_backend.py

import copy
import types

import pytest

from datetime import datetime

from src.calendar import (
  CalendarBackend, CalendarUtilsProtocol, hko_data_utils, calendar_utils_of,
)
from src.calendar.celestial_utils import ALGO1, ALGO2
from src.bazi import Bazi, BaziGender, BaziPrecision
from src.bazi_chart import BaziChart


def test_basic() -> None:
  assert len(CalendarBackend) == 3
  assert str(CalendarBackend.HKO) == 'hko'
  assert str(CalendarBackend.CELESTIAL) == 'celestial'
  assert str(CalendarBackend.CELESTIAL_ALGO2) == 'celestial-algo2'


def test_from_str() -> None:
  for s in ['hko', 'HKO', 'Hko']:
    assert CalendarBackend.from_str(s) is CalendarBackend.HKO
  for s in ['celestial', 'CELESTIAL', 'Celestial']:
    assert CalendarBackend.from_str(s) is CalendarBackend.CELESTIAL
  # Both the member name and the value resolve, and they differ in spelling here.
  for s in ['celestial-algo2', 'CELESTIAL_ALGO2', 'celestial_algo2']:
    assert CalendarBackend.from_str(s) is CalendarBackend.CELESTIAL_ALGO2

  with pytest.raises(ValueError):
    CalendarBackend.from_str('lunar') # Not a supported backend.

  with pytest.raises(TypeError):
    CalendarBackend.from_str(42) # type: ignore[arg-type]


def test_calendar_utils_of() -> None:
  utils = calendar_utils_of(CalendarBackend.HKO)
  assert utils is hko_data_utils
  assert isinstance(utils, CalendarUtilsProtocol)

  assert calendar_utils_of(CalendarBackend.CELESTIAL) is ALGO1
  assert calendar_utils_of(CalendarBackend.CELESTIAL_ALGO2) is ALGO2

  # Strings are also accepted and resolved the same way.
  assert calendar_utils_of('hko') is hko_data_utils
  assert calendar_utils_of('celestial') is ALGO1

  for backend in CalendarBackend:
    assert isinstance(calendar_utils_of(backend), CalendarUtilsProtocol)

  with pytest.raises(ValueError):
    calendar_utils_of('lunar')

  with pytest.raises(TypeError):
    calendar_utils_of(42) # type: ignore[arg-type]


def test_create_with_backend() -> None:
  bazi_enum: Bazi = Bazi.create('1984-04-02 04:02', 'male', 'day', backend=CalendarBackend.HKO)
  bazi_str: Bazi = Bazi.create('1984-04-02 04:02', 'male', 'day', backend='hko')

  assert bazi_enum == bazi_str # enum and string spellings resolve the same way

  with pytest.raises(ValueError):
    Bazi.create('1984-04-02 04:02', 'male', 'day', backend='lunar')

  with pytest.raises(TypeError):
    Bazi.create('1984-04-02 04:02', 'male', 'day', backend=42) # type: ignore[arg-type]


def test_consistent_with_hko_utils() -> None:
  # The backend-resolved utils should produce results identical to direct HKO calls.
  bazi: Bazi = Bazi(datetime(2000, 2, 4, 20, 35), BaziGender.FEMALE, BaziPrecision.DAY,
                    backend=CalendarBackend.HKO)
  assert bazi.solar_date == hko_data_utils.to_date(datetime(2000, 2, 4))
  assert bazi.ganzhi_date == hko_data_utils.to_ganzhi(bazi.solar_date)


def test_init_rejects_str_backend() -> None:
  # `__init__` only takes the enum; strings go through `Bazi.create` (same
  # contract split as `gender` / `precision`).
  with pytest.raises(TypeError):
    Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY,
         backend='hko') # type: ignore[arg-type]


def test_default_backend_is_celestial() -> None:
  '''
  #93 flipped the default from HKO to CELESTIAL.  The switch is two quiet keyword
  defaults, so pin every construction path that can pick it up implicitly.
  '''
  assert Bazi(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY).backend is CalendarBackend.CELESTIAL
  assert Bazi.create('2000-02-04 22:01', 'male', 'day').backend is CalendarBackend.CELESTIAL
  assert Bazi.random().backend is CalendarBackend.CELESTIAL


def test_json_contains_backend() -> None:
  chart: BaziChart = BaziChart(Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY))
  assert chart.json['backend'] == 'celestial' # the default
  hko_chart: BaziChart = BaziChart(Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY,
                                        backend=CalendarBackend.HKO))
  assert hko_chart.json['backend'] == 'hko'


def test_celestial_backend_end_to_end() -> None:
  '''
  F1's claim is that the backend is *in place*, so the whole path gets exercised here --
  `Bazi.create` from a string, the bare `datetime` that `__init__` hands to the utils, and
  the json round-trip -- not just the utils in isolation.  Without this, refactoring
  `to_solar`'s `isinstance(d, date)` into `type(d) is date` would break every celestial
  chart while the calendar unit tests stayed green.
  '''
  for spelling, backend in (('celestial', CalendarBackend.CELESTIAL),
                            ('celestial-algo2', CalendarBackend.CELESTIAL_ALGO2)):
    bazi: Bazi = Bazi.create('1984-04-02 04:02', 'male', 'day', backend=spelling)
    assert bazi.backend is backend
    assert bazi == Bazi.create('1984-04-02 04:02', 'male', 'day', backend=backend)
    # The bare-`datetime` call shape, which is what `Bazi.__init__` actually uses.
    assert bazi.solar_date == calendar_utils_of(backend).to_date(datetime(1984, 4, 2))
    assert BaziChart(bazi).json['backend'] == spelling


def test_celestial_differs_from_hko_exactly_where_the_whitelist_says() -> None:
  '''
  celestial puts 1917 大雪 at 12-08 00:01:05; the HKO almanac dates it 12-07.  So on 12-07
  the two backends genuinely build different charts.  This is the one place F1's opt-in
  path is *meant* to disagree, and `(1917, 10, 30)` is one of the four ganzhi dates the
  layer-c derivation predicts from that whitelist row -- so this pins the propagation
  end to end, not just inside the calendar layer.
  '''
  hko: Bazi = Bazi.create('1917-12-07 12:00', 'male', 'day', backend='hko')
  cel: Bazi = Bazi.create('1917-12-07 12:00', 'male', 'day', backend='celestial')

  assert str(hko.month_pillar) == '壬子'
  assert str(cel.month_pillar) == '辛亥'
  assert (hko.ganzhi_date.month, hko.ganzhi_date.day) == (11, 1)
  assert (cel.ganzhi_date.month, cel.ganzhi_date.day) == (10, 30)
  # The moved 节 shifts the month, nothing else: year and day pillars still agree.
  assert hko.year_pillar == cel.year_pillar
  assert hko.day_pillar == cel.day_pillar


def test_deepcopy() -> None:
  # Every backend, not only HKO.  The celestial ones resolve to *instances*, so a leak
  # into an instance dict would deepcopy silently -- cloning both tables -- where the HKO
  # module would have raised.  Hence the guard names the resolved objects themselves
  # rather than just excluding `ModuleType`.
  forbidden: tuple[object, ...] = tuple(calendar_utils_of(b) for b in CalendarBackend)

  for backend in CalendarBackend:
    bazi: Bazi = Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY,
                      backend=backend)
    chart: BaziChart = BaziChart(bazi) # `BaziChart` deepcopies the bazi internally.

    # Trigger the utils-resolving paths before copying.
    _ = bazi.solar_date, bazi.ganzhi_date
    _ = chart.dayun_start_moment

    # Only the `CalendarBackend` enum may be stored on the instances (deepcopy-safe).
    # `_utils` must stay a plain property: no resolved utils object may ever land in
    # the instance dicts.
    for obj in (bazi, chart):
      for value in vars(obj).values():
        assert not isinstance(value, types.ModuleType)
        for utils in forbidden:
          assert value is not utils

    bazi2: Bazi = copy.deepcopy(bazi)
    assert bazi == bazi2
    assert bazi2.backend is backend
    # The copy still resolves the calendar utils on demand.
    assert bazi2.ganzhi_date == bazi.ganzhi_date

    chart2: BaziChart = copy.deepcopy(chart)
    assert chart2.bazi.backend is backend
    assert chart2.dayun_start_moment == chart.dayun_start_moment
