# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_dates.py

import random
import copy

import pytest

from datetime import date, timedelta
from itertools import product

from src.calendar import CalendarType, CalendarDate


def test_calendar_type() -> None:
  assert CalendarType.SOLAR is CalendarType.公历
  assert CalendarType.LUNAR is CalendarType.农历
  assert CalendarType.GANZHI is CalendarType.干支历
  assert len(CalendarType) == 3


def test_solar_date() -> None:
  sd = CalendarDate(2024, 1, 1, CalendarType.SOLAR)
  assert sd.year == 2024
  assert sd.month == 1
  assert sd.day == 1
  assert sd.date_type == CalendarType.SOLAR

  assert sd == CalendarDate(2024, 1, 1, CalendarType.SOLAR)
  assert sd == sd # noqa: PLR0124 # reflexivity is the behavior under test

  assert sd != CalendarDate(2023, 1, 1, CalendarType.SOLAR)
  assert sd != CalendarDate(2024, 2, 1, CalendarType.SOLAR)
  assert sd != CalendarDate(2024, 1, 30, CalendarType.SOLAR)
  assert sd != CalendarDate(2024, 1, 1, CalendarType.LUNAR)
  assert sd != CalendarDate(2024, 1, 1, CalendarType.GANZHI)

  assert sd != date(2024, 1, 1)
  assert sd != '2024-01-01'

  with pytest.raises(AssertionError):
    CalendarDate('2024', 1, 1, CalendarType.SOLAR) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, '1', 1, CalendarType.SOLAR) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, 1, '1', CalendarType.SOLAR) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, 1, 1, 'SOLAR') # type: ignore
  with pytest.raises(TypeError):
    CalendarDate(2024, 1, 1) # type: ignore # Missing argument.

  # Create invalid dates, no exception is expected to be raised, since `CalendarType` is just a thin wrapper.
  CalendarDate(2024, 13, 1, CalendarType.SOLAR) # Invalid month.
  CalendarDate(2024, 0, 1, CalendarType.SOLAR) # Invalid month.
  CalendarDate(2024, 1, 0, CalendarType.SOLAR) # Invalid day.
  CalendarDate(2024, 1, 32, CalendarType.SOLAR) # Invalid day.


def test_lunar_date() -> None:
  ld = CalendarDate(2024, 1, 1, CalendarType.LUNAR)
  assert ld.year == 2024
  assert ld.month == 1
  assert ld.day == 1
  assert ld.date_type == CalendarType.LUNAR

  assert ld == CalendarDate(2024, 1, 1, CalendarType.LUNAR)
  assert ld == ld # noqa: PLR0124 # reflexivity is the behavior under test

  assert ld != CalendarDate(2023, 1, 1, CalendarType.LUNAR)
  assert ld != CalendarDate(2024, 2, 1, CalendarType.LUNAR)
  assert ld != CalendarDate(2024, 1, 30, CalendarType.LUNAR)
  assert ld != CalendarDate(2024, 13, 29, CalendarType.LUNAR) # Notice that there can be 13 lunar months in a lunar year.
  assert ld != CalendarDate(2024, 1, 1, CalendarType.SOLAR)
  assert ld != CalendarDate(2024, 1, 1, CalendarType.GANZHI)

  assert ld != date(2024, 1, 1)
  assert ld != '2024-01-01'

  with pytest.raises(AssertionError):
    CalendarDate('2024', 1, 1, CalendarType.LUNAR) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, '1', 1, CalendarType.LUNAR) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, 1, '1', CalendarType.LUNAR) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, 1, 1, 'LUNAR') # type: ignore
  with pytest.raises(TypeError):
    CalendarDate(2024, 1, 1) # type: ignore # Missing argument.

  # Create invalid dates, no exception is expected to be raised, since `CalendarType` is just a thin wrapper.
  CalendarDate(2024, 14, 1, CalendarType.LUNAR) # Invalid month.
  CalendarDate(2024, 0, 1, CalendarType.LUNAR) # Invalid month.
  CalendarDate(2024, 1, 31, CalendarType.LUNAR) # Invalid day.
  CalendarDate(2024, 1, 0, CalendarType.LUNAR) # Invalid day.


def test_ganzhi_date() -> None:
  gzd = CalendarDate(2024, 1, 1, CalendarType.GANZHI)
  assert gzd.year == 2024
  assert gzd.month == 1
  assert gzd.day == 1
  assert gzd.date_type == CalendarType.GANZHI

  assert gzd == CalendarDate(2024, 1, 1, CalendarType.GANZHI)
  assert gzd == gzd # noqa: PLR0124 # reflexivity is the behavior under test

  assert gzd != CalendarDate(2023, 1, 1, CalendarType.GANZHI)
  assert gzd != CalendarDate(2024, 2, 1, CalendarType.GANZHI)
  assert gzd != CalendarDate(2024, 1, 30, CalendarType.GANZHI)
  assert gzd != CalendarDate(2024, 1, 1, CalendarType.LUNAR)
  assert gzd != CalendarDate(2024, 1, 1, CalendarType.SOLAR)

  assert gzd != date(2024, 1, 1)
  assert gzd != '2024-01-01'

  with pytest.raises(AssertionError):
    CalendarDate('2024', 1, 1, CalendarType.GANZHI) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, '1', 1, CalendarType.GANZHI) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, 1, '1', CalendarType.GANZHI) # type: ignore
  with pytest.raises(AssertionError):
    CalendarDate(2024, 1, 1, 'GANZHI') # type: ignore
  with pytest.raises(TypeError):
    CalendarDate(2024, 1, 1) # type: ignore # Missing argument.

  # Create invalid dates, no exception is expected to be raised, since `CalendarType` is just a thin wrapper.
  CalendarDate(2024, 13, 1, CalendarType.GANZHI) # Invalid month.
  CalendarDate(2024, 0, 1, CalendarType.GANZHI) # Invalid month.
  CalendarDate(2024, 1, 32, CalendarType.GANZHI) # Invalid day.
  CalendarDate(2024, 1, 0, CalendarType.GANZHI) # Invalid day.


def test_date_cmp_operators() -> None:
  # Use solar dates to test date operators.
  random_date_list: list[date] = []
  for _ in range(256):
    random_date_list.append(date(random.randint(1, 9999), random.randint(1, 12), random.randint(1, 28)))

  for date1, date2 in product(random_date_list, random_date_list):
    c_date1: CalendarDate = CalendarDate(date1.year, date1.month, date1.day, CalendarType.SOLAR)
    c_date2: CalendarDate = CalendarDate(date2.year, date2.month, date2.day, CalendarType.SOLAR)

    if date1 < date2:
      assert c_date1 < c_date2
    if date1 <= date2:
      assert c_date1 <= c_date2
    if date1 > date2:
      assert c_date1 > c_date2
    if date1 >= date2:
      assert c_date1 >= c_date2
    if date1 == date2:
      assert c_date1 == c_date2
    if date1 != date2:
      assert c_date1 != c_date2

  cur_date: date = date(
    random.randint(1, 9999),
    random.randint(1, 12),
    random.randint(1, 28)
  )
  for _ in range(512):
    next_date: date = cur_date + timedelta(days=1)
    c_date1 = CalendarDate(cur_date.year, cur_date.month, cur_date.day, CalendarType.SOLAR)
    c_date2 = CalendarDate(next_date.year, next_date.month, next_date.day, CalendarType.SOLAR)

    assert c_date1 < c_date2
    assert c_date1 <= c_date2
    assert not c_date1 > c_date2
    assert not c_date1 >= c_date2
    assert not c_date1 == c_date2 # noqa: SIM201 # `==` itself is the operator under test
    assert c_date1 != c_date2

    assert c_date1 >= c_date1 # noqa: PLR0124 # reflexivity is the behavior under test
    assert c_date1 <= c_date1 # noqa: PLR0124 # reflexivity is the behavior under test
    assert not c_date1 > c_date1 # noqa: PLR0124 # reflexivity is the behavior under test
    assert not c_date1 < c_date1 # noqa: PLR0124 # reflexivity is the behavior under test
    assert c_date1 == c_date1 # noqa: PLR0124 # reflexivity is the behavior under test
    assert not c_date1 != c_date1 # noqa: PLR0124, SIM202 # reflexivity is the behavior under test

    cur_date = next_date


def test_date_cmp_operators_negative() -> None:
  # As expected, only the dates of the same `CalendarType` can be compared.
  calendar_dates: list[CalendarDate] = [
    CalendarDate(2024, 1, 1, CalendarType.SOLAR),
    CalendarDate(2024, 1, 1, CalendarType.LUNAR),
    CalendarDate(2024, 1, 1, CalendarType.GANZHI),
  ]

  for d1, d2 in product(calendar_dates, calendar_dates):
    bool1: bool = d1 == d2
    bool2: bool = d1 != d2

    # Either bool1 or bool2 is True.
    assert bool1 or bool2
    assert not (bool1 and bool2)

    assert (d1 == d2) == (d2 == d1)
    assert (d1 != d2) == (d2 != d1)

    # Following subtests need `d1` to be of the same `CalendarType` as `d2`.
    if d1.date_type == d2.date_type:
      continue

    with pytest.raises(TypeError):
      d1 < d2 # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      d1 <= d2 # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      d1 > d2 # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      d1 >= d2 # noqa: B015 # the raising comparison is the behavior under test

  for d1, dt in zip(calendar_dates, [date(2024, 1, 1)] * 3):
    # `==`/`!=` against a foreign type follow Python's convention (False/True, both
    # directions, no raise); ordering against one still raises.
    assert not d1 == dt # noqa: SIM201 # `==` itself is the operator under test
    assert d1 != dt
    assert not dt == d1 # noqa: SIM201 # `==` itself is the operator under test
    assert dt != d1

    with pytest.raises(TypeError):
      d1 < dt # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      d1 <= dt # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      d1 > dt # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      d1 >= dt # noqa: B015 # the raising comparison is the behavior under test

    with pytest.raises(TypeError):
      dt < d1 # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      dt <= d1 # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      dt > d1 # noqa: B015 # the raising comparison is the behavior under test
    with pytest.raises(TypeError):
      dt >= d1 # noqa: B015 # the raising comparison is the behavior under test


def test_str_repr() -> None:
  random_date_list: list[CalendarDate] = []
  for _ in range(256):
    random_date_list.append(
      CalendarDate(
        random.randint(1902, 2099),
        random.randint(1, 12),
        random.randint(1, 28),
        random.choice(list(CalendarType))
      )
    )

  for d in random_date_list:
    assert str(d) == d.__str__()
    assert repr(d) == d.__repr__()
    assert str(d) == str(d) # noqa: PLR0124 # determinism across calls is the behavior under test
    assert repr(d) == repr(d) # noqa: PLR0124 # determinism across calls is the behavior under test

  for d1, d2 in product(random_date_list, random_date_list):
    if d1 == d2:
      assert str(d1) == str(d2)
      assert repr(d1) == repr(d2)
    if d1 != d2:
      assert str(d1) != str(d2)
      assert repr(d1) != repr(d2)


def test_malicious_writes() -> None:
  # Write to properties.
  d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
  with pytest.raises(AttributeError):
    d.year = 1999 # type: ignore
  with pytest.raises(AttributeError):
    d.month = 2 # type: ignore
  with pytest.raises(AttributeError):
    d.day = 10 # type: ignore
  with pytest.raises(AttributeError):
    d.date_type = CalendarType.LUNAR # type: ignore

  # Write to underlying instance variables.
  # A frozen dataclass rejects writes to any attribute -- even brand-new private names.
  d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
  with pytest.raises(AttributeError):
    d._year = 1999 # type: ignore


def test_copy() -> None:
  d = CalendarDate(2000, 1, 1, CalendarType.SOLAR)
  for method, d_copy in [('shallow', copy.copy(d)), ('deep', copy.deepcopy(d))]:
    assert d == d_copy
    assert d_copy == d
    assert d is not d_copy
    # Copies can no longer be mutated into inequality (frozen dataclass), so
    # distinctness is shown against freshly constructed different dates instead.
    assert d_copy != CalendarDate(2001, 1, 1, CalendarType.SOLAR)
    assert d_copy != CalendarDate(2000, 1, 1, CalendarType.LUNAR)
