# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_backend.py

import copy
import types

import pytest

from datetime import date, datetime, timedelta, timezone, UTC
from typing import Any

from bazi.calendar import (
  CalendarBackend, CalendarDate, CalendarType, CalendarUtilsProtocol, hko_data_utils, calendar_utils_of,
)
from bazi.calendar.celestial_utils import ALGO1, ALGO2
from bazi.bazi import Bazi, BaziGender
from bazi.school import BaziConfig
from bazi.bazi_chart import BaziChart
from bazi.defines import Jieqi


class EqualKey:
  def __init__(self, value: object) -> None:
    self.value = value

  def __eq__(self, other: object) -> bool:
    return self.value == other

  def __hash__(self) -> int:
    return hash(self.value)


class HashTrap:
  def __hash__(self) -> int:
    raise AssertionError('Wrong-type input reached hashing')


@pytest.fixture(params=list(CalendarBackend))
def utils(request: pytest.FixtureRequest) -> CalendarUtilsProtocol:
  backend = calendar_utils_of(request.param)
  # Each case starts cold, including nested caches and both celestial receivers.
  owner = backend if isinstance(backend, types.ModuleType) else type(backend)
  for value in vars(owner).values():
    if hasattr(value, 'cache_clear'):
      value.cache_clear()
  return backend


@pytest.mark.parametrize(('name', 'parameter', 'good', 'expected_type'), [
  ('get_min_supported_date', 'date_type', CalendarType.SOLAR, 'CalendarType'),
  ('get_max_supported_date', 'date_type', CalendarType.SOLAR, 'CalendarType'),
  ('is_valid_solar_date', 'd', CalendarDate(2024, 3, 1, CalendarType.SOLAR), 'CalendarDate'),
  ('is_valid_lunar_date', 'd', CalendarDate(2024, 1, 21, CalendarType.LUNAR), 'CalendarDate'),
  ('is_valid_ganzhi_date', 'd', CalendarDate(2024, 1, 27, CalendarType.GANZHI), 'CalendarDate'),
  ('is_valid', 'd', CalendarDate(2024, 3, 1, CalendarType.SOLAR), 'CalendarDate'),
  ('lunar_to_solar', 'lunar_date', CalendarDate(2024, 1, 21, CalendarType.LUNAR), 'CalendarDate'),
  ('solar_to_lunar', 'solar_date', CalendarDate(2024, 3, 1, CalendarType.SOLAR), 'CalendarDate'),
  ('ganzhi_to_solar', 'ganzhi_date', CalendarDate(2024, 1, 27, CalendarType.GANZHI), 'CalendarDate'),
  ('solar_to_ganzhi', 'solar_date', CalendarDate(2024, 3, 1, CalendarType.SOLAR), 'CalendarDate'),
  ('lunar_to_ganzhi', 'lunar_date', CalendarDate(2024, 1, 21, CalendarType.LUNAR), 'CalendarDate'),
  ('ganzhi_to_lunar', 'ganzhi_date', CalendarDate(2024, 1, 27, CalendarType.GANZHI), 'CalendarDate'),
  ('to_solar', 'd', datetime(2024, 3, 1), 'date or CalendarDate'),
  ('to_lunar', 'd', datetime(2024, 3, 1), 'date or CalendarDate'),
  ('to_ganzhi', 'd', datetime(2024, 3, 1), 'date or CalendarDate'),
  ('to_date', 'd', datetime(2024, 3, 1), 'date or CalendarDate'),
  ('prev_jie', 'dt', datetime(2024, 3, 1), 'datetime'),
  ('next_jie', 'dt', datetime(2024, 3, 1), 'datetime'),
])
@pytest.mark.parametrize('keyword', [False, True], ids=['positional', 'keyword'])
@pytest.mark.parametrize('warm', [False, True], ids=['cold', 'warm'])
def test_date_types_before_cache(
  utils: CalendarUtilsProtocol, name: str, parameter: str, good: object,
  expected_type: str, keyword: bool, warm: bool,
) -> None:
  method = getattr(utils, name)
  bad = EqualKey(good)
  assert bad == good and good == bad and hash(bad) == hash(good)
  if warm:
    if keyword:
      method(**{parameter: good})
    else:
      method(good)
  invalid: object
  for invalid in (bad, [], HashTrap()):
    with pytest.raises(TypeError, match=f'Expected {expected_type}'):
      if keyword:
        method(**{parameter: invalid})
      else:
        method(invalid)
  for attribute in ('cache_clear', 'cache_info', 'cache_parameters', '__wrapped__'):
    assert not hasattr(method, attribute)


@pytest.mark.parametrize('name', ['to_solar', 'to_lunar', 'to_ganzhi', 'to_date'])
def test_to_date_nested_cache_boundary(utils: CalendarUtilsProtocol, name: str) -> None:
  good = date(2024, 3, 1)
  # Warm the shared adapter through another public method, not the method under test.
  if name == 'to_date':
    utils.to_lunar(good)
  else:
    utils.to_date(good)
  with pytest.raises(TypeError, match='Expected date or CalendarDate'):
    getattr(utils, name)(EqualKey(good))


@pytest.mark.parametrize('name', ['to_solar', 'to_lunar', 'to_ganzhi', 'to_date'])
@pytest.mark.parametrize('reverse', [False, True])
def test_to_date_civil_projection(utils: CalendarUtilsProtocol, name: str, reverse: bool) -> None:
  a = datetime(2024, 3, 1, 0, 30, tzinfo=UTC)
  b = datetime(2024, 2, 29, 19, 30, tzinfo=timezone(timedelta(hours=-5)))
  assert a == b and hash(a) == hash(b) and a.date() != b.date()
  method = getattr(utils, name)
  for dt in ((b, a) if reverse else (a, b)):
    assert utils.to_date(method(dt)) == dt.date()


def test_date_boundary_valid_values(utils: CalendarUtilsProtocol) -> None:
  class Date(date):
    pass

  class Datetime(datetime):
    pass

  class UnhashableDate(date):
    __hash__ = None # type: ignore[assignment] # Accepted through civil-date projection.

  class UnhashableDatetime(datetime):
    __hash__ = None # type: ignore[assignment] # Accepted through civil-date projection.

  class DateValue(CalendarDate):
    pass

  class Int(int):
    pass

  for project in (utils.to_solar, utils.to_lunar, utils.to_ganzhi, utils.to_date):
    expected = project(date(2024, 1, 1))
    for d in (
      Date(2024, 1, 1), Datetime(2024, 1, 1, 12),
      UnhashableDate(2024, 1, 1), UnhashableDatetime(2024, 1, 1, 12),
    ):
      assert project(d) == expected
    with pytest.raises(ValueError):
      project(CalendarDate(2024, 2, 30, CalendarType.SOLAR))

  for kind in CalendarType:
    value = DateValue(Int(2024), True, True, kind)
    plain = CalendarDate(2024, 1, 1, kind)
    assert utils.is_valid(value)
    assert getattr(utils, f'is_valid_{kind.name.lower()}_date')(value)
    for project in (utils.to_solar, utils.to_lunar, utils.to_ganzhi, utils.to_date):
      assert project(value) == project(DateValue(2024, 1, 1, kind))
    for target in CalendarType:
      if kind != target:
        convert = getattr(utils, f'{kind.name.lower()}_to_{target.name.lower()}')
        assert convert(value) == convert(plain)
        with pytest.raises(ValueError):
          convert(CalendarDate(2024, 0, 1, kind))
    assert not utils.is_valid(CalendarDate(2024, 0, 1, kind))
    assert utils.is_valid(utils.get_min_supported_date(kind))
    assert utils.is_valid(utils.get_max_supported_date(kind))

  for jie in (utils.prev_jie, utils.next_jie):
    assert jie(Datetime(2024, 1, 1)) == jie(datetime(2024, 1, 1))
    first, last = utils.supported_jie_boundaries()
    jie(first)
    for outside in (first - timedelta(seconds=1), last):
      with pytest.raises(ValueError):
        jie(outside)


def test_year_cache_boundaries_unchanged(utils: CalendarUtilsProtocol) -> None:
  class Year(int):
    pass

  year = Year(2024)
  calls: list[tuple[Any, tuple[object, ...]]] = [
    (utils.days_counts_in_ganzhi_year, (year,)),
    (utils.jieqi_date, (year, Jieqi.立春)),
    (utils.jieqi_moment, (year, Jieqi.立春)),
  ]
  for method, args in calls:
    method(*args)
    with pytest.raises(TypeError, match='Expected int'):
      method(EqualKey(year), *args[1:])
    with pytest.raises(ValueError):
      method(True, *args[1:])


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
  bazi_enum: Bazi = Bazi.create('1984-04-02 04:02', 'male', BaziConfig(backend=CalendarBackend.HKO))
  bazi_str: Bazi = Bazi.create('1984-04-02 04:02', 'male', BaziConfig.from_values(backend='hko'))

  assert bazi_enum == bazi_str # enum and string spellings resolve the same way

  with pytest.raises(ValueError):
    Bazi.create('1984-04-02 04:02', 'male', BaziConfig.from_values(backend='lunar'))

  with pytest.raises(TypeError):
    Bazi.create('1984-04-02 04:02', 'male', BaziConfig.from_values(backend=42)) # type: ignore[arg-type]


def test_consistent_with_hko_utils() -> None:
  # The backend-resolved utils should produce results identical to direct HKO calls.
  bazi: Bazi = Bazi(datetime(2000, 2, 4, 20, 35), BaziGender.FEMALE,
                    BaziConfig(backend=CalendarBackend.HKO))
  assert bazi.solar_date == hko_data_utils.to_date(datetime(2000, 2, 4))
  assert bazi.ganzhi_date == hko_data_utils.to_ganzhi(bazi.solar_date)


def test_init_rejects_str_config() -> None:
  # `__init__` only takes `BaziConfig`; strings go through `BaziConfig.from_values`
  # (same contract split as `gender`, whose strings go through `Bazi.create`).
  with pytest.raises(TypeError):
    Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, 'hko') # type: ignore[arg-type]


def test_default_backend_is_celestial() -> None:
  '''
  #93 flipped the default from HKO to CELESTIAL.  The default now lives in
  `DEFAULT_CONFIG`, so pin every construction path that can pick it up implicitly.
  '''
  assert Bazi(datetime(2000, 2, 4, 22, 1), BaziGender.MALE).config.backend is CalendarBackend.CELESTIAL
  assert Bazi.create('2000-02-04 22:01', 'male').config.backend is CalendarBackend.CELESTIAL
  assert Bazi.random().config.backend is CalendarBackend.CELESTIAL


def test_json_contains_backend() -> None:
  chart: BaziChart = BaziChart(Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  assert chart.json['backend'] == 'celestial' # the default
  hko_chart: BaziChart = BaziChart(Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE,
                                        BaziConfig(backend=CalendarBackend.HKO)))
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
    bazi: Bazi = Bazi.create('1984-04-02 04:02', 'male', BaziConfig.from_values(backend=spelling))
    assert bazi.config.backend is backend
    assert bazi == Bazi.create('1984-04-02 04:02', 'male', BaziConfig(backend=backend))
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
  hko: Bazi = Bazi.create('1917-12-07 12:00', 'male', BaziConfig.from_values(backend='hko'))
  cel: Bazi = Bazi.create('1917-12-07 12:00', 'male', BaziConfig.from_values(backend='celestial'))

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
    bazi: Bazi = Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziConfig(backend=backend))
    chart: BaziChart = BaziChart(bazi) # `BaziChart` deepcopies the bazi internally.

    # Trigger the utils-resolving paths before copying.
    _ = bazi.solar_date, bazi.ganzhi_date
    _ = chart.dayun_start_moment

    # Only the config (frozen, holding the `CalendarBackend` enum) may be stored on the
    # instances (deepcopy-safe). `_utils` must stay a plain property: no resolved utils
    # object may ever land in the instance dicts.
    for obj in (bazi, chart):
      for value in vars(obj).values():
        assert not isinstance(value, types.ModuleType)
        for utils in forbidden:
          assert value is not utils

    bazi2: Bazi = copy.deepcopy(bazi)
    assert bazi == bazi2
    assert bazi2.config.backend is backend
    # The copy still resolves the calendar utils on demand.
    assert bazi2.ganzhi_date == bazi.ganzhi_date

    chart2: BaziChart = copy.deepcopy(chart)
    assert chart2.bazi.config.backend is backend
    assert chart2.dayun_start_moment == chart.dayun_start_moment
