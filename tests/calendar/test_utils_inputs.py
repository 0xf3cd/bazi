# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date, datetime, timedelta, timezone, UTC
from typing import Any

import pytest

from bazi.calendar import CalendarDate, CalendarType, utils
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


@pytest.mark.input_contract('bazi.calendar.utils', 'get_min_supported_date to_solar prev_jie')
@pytest.mark.parametrize(('name', 'parameter', 'good', 'expected_type'), [
  ('get_min_supported_date', 'date_type', CalendarType.SOLAR, 'CalendarType'),
  ('to_solar', 'd', CalendarDate(2024, 3, 1, CalendarType.SOLAR), 'date or CalendarDate'),
  ('prev_jie', 'dt', datetime(2024, 3, 1), 'datetime'),
])
def test_types_before_cache(
  name: str, parameter: str, good: object, expected_type: str,
) -> None:
  # One representative for enum, date-conversion and datetime caches.
  for value in vars(utils).values():
    if hasattr(value, 'cache_clear'):
      value.cache_clear()
  method = getattr(utils, name)
  bad = EqualKey(good)
  assert bad == good and good == bad and hash(bad) == hash(good)
  invalid: object
  for warm in (False, True):
    if warm:
      method(good)
    for invalid in (bad, [], HashTrap()):
      with pytest.raises(TypeError, match=f'Expected {expected_type}'):
        method(**{parameter: invalid})


@pytest.mark.input_contract('bazi.calendar.utils', 'to_date')
def test_nested_cache_boundary() -> None:
  good = date(2024, 3, 1)
  utils.to_lunar(good)
  with pytest.raises(TypeError, match='Expected date or CalendarDate'):
    utils.to_date(EqualKey(good)) # type: ignore[arg-type]


@pytest.mark.parametrize('name', ['to_solar', 'to_lunar', 'to_ganzhi', 'to_date'])
def test_civil_projection_precedes_cache(name: str) -> None:
  a = datetime(2024, 3, 1, 0, 30, tzinfo=UTC)
  b = datetime(2024, 2, 29, 19, 30, tzinfo=timezone(timedelta(hours=-5)))
  assert a == b and hash(a) == hash(b) and a.date() != b.date()
  method = getattr(utils, name)
  for dt in (a, b, a):
    assert utils.to_date(method(dt)) == dt.date()


def test_date_boundary_valid_values() -> None:
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
    for kind in CalendarType:
      value = DateValue(Int(2024), True, True, kind)
      assert project(value) == project(DateValue(2024, 1, 1, kind))

  for jie in (utils.prev_jie, utils.next_jie):
    assert jie(Datetime(2024, 1, 1)) == jie(datetime(2024, 1, 1))


@pytest.mark.input_contract('bazi.calendar.utils', 'jieqi_moment')
def test_year_and_jieqi_types_before_lookup() -> None:
  utils.jieqi_moment(2024, Jieqi.立春)
  bad: Any
  for bad in (EqualKey(2024), HashTrap()):
    with pytest.raises(TypeError, match='Expected int'):
      utils.jieqi_moment(bad, Jieqi.立春)
  for bad in (EqualKey(Jieqi.立春), HashTrap()):
    with pytest.raises(TypeError, match='Expected Jieqi'):
      utils.jieqi_moment(2024, bad)
