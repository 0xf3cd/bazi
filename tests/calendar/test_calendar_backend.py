# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_calendar_backend.py

import copy
import types
import unittest

from datetime import datetime

from src.Calendar import (
  CalendarBackend, CalendarUtilsProtocol, HkoDataCalendarUtils, calendar_utils_of,
)
from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.BaziChart import BaziChart


class TestCalendarBackend(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(len(CalendarBackend), 1)
    self.assertEqual(str(CalendarBackend.HKO), 'hko')

  def test_from_str(self) -> None:
    for s in ['hko', 'HKO', 'Hko']:
      self.assertIs(CalendarBackend.from_str(s), CalendarBackend.HKO)

    with self.assertRaises(ValueError):
      CalendarBackend.from_str('lunar') # Not a supported backend.

    with self.assertRaises(AssertionError):
      CalendarBackend.from_str(42) # type: ignore[arg-type]

  def test_calendar_utils_of(self) -> None:
    utils = calendar_utils_of(CalendarBackend.HKO)
    self.assertIs(utils, HkoDataCalendarUtils)
    self.assertIsInstance(utils, CalendarUtilsProtocol)

    # Strings are also accepted and resolved the same way.
    self.assertIs(calendar_utils_of('hko'), HkoDataCalendarUtils)

    with self.assertRaises(ValueError):
      calendar_utils_of('lunar')

    with self.assertRaises(AssertionError):
      calendar_utils_of(42) # type: ignore[arg-type]


class TestBaziBackend(unittest.TestCase):
  def test_default_backend(self) -> None:
    bazi: Bazi = Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY)
    self.assertIs(bazi.backend, CalendarBackend.HKO)

  def test_create_with_backend(self) -> None:
    bazi_default: Bazi = Bazi.create('1984-04-02 04:02', 'male', 'day')
    bazi_enum: Bazi = Bazi.create('1984-04-02 04:02', 'male', 'day', backend=CalendarBackend.HKO)
    bazi_str: Bazi = Bazi.create('1984-04-02 04:02', 'male', 'day', backend='hko')

    self.assertIs(bazi_default.backend, CalendarBackend.HKO)
    self.assertEqual(bazi_default, bazi_enum)
    self.assertEqual(bazi_default, bazi_str)

    with self.assertRaises(ValueError):
      Bazi.create('1984-04-02 04:02', 'male', 'day', backend='lunar')

    with self.assertRaises(AssertionError):
      Bazi.create('1984-04-02 04:02', 'male', 'day', backend=42) # type: ignore[arg-type]

  def test_consistent_with_hko_utils(self) -> None:
    # The backend-resolved utils should produce results identical to direct HKO calls.
    bazi: Bazi = Bazi(datetime(2000, 2, 4, 20, 35), BaziGender.FEMALE, BaziPrecision.DAY,
                      backend=CalendarBackend.HKO)
    self.assertEqual(bazi.solar_date, HkoDataCalendarUtils.to_date(datetime(2000, 2, 4)))
    self.assertEqual(bazi.ganzhi_date, HkoDataCalendarUtils.to_ganzhi(bazi.solar_date))

  def test_init_rejects_str_backend(self) -> None:
    # `__init__` only takes the enum; strings go through `Bazi.create` (same
    # contract split as `gender` / `precision`).
    with self.assertRaises(AssertionError):
      Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY,
           backend='hko') # type: ignore[arg-type]

  def test_random_uses_default_backend(self) -> None:
    self.assertIs(Bazi.random().backend, CalendarBackend.HKO)

  def test_json_contains_backend(self) -> None:
    chart: BaziChart = BaziChart(Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY))
    self.assertEqual(chart.json['backend'], 'hko')

  def test_deepcopy(self) -> None:
    bazi: Bazi = Bazi(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY)
    chart: BaziChart = BaziChart(bazi) # `BaziChart` deepcopies the bazi internally.

    # Trigger the utils-resolving paths before copying.
    _ = bazi.solar_date, bazi.ganzhi_date
    _ = chart.dayun_start_moment

    # Only the `CalendarBackend` enum may be stored on the instances (deepcopy-safe).
    # `_utils` must stay a plain property: no module reference may ever land in
    # the instance dicts, since modules are not deepcopyable.
    for obj in (bazi, chart):
      for value in vars(obj).values():
        self.assertNotIsInstance(value, types.ModuleType)

    bazi2: Bazi = copy.deepcopy(bazi)
    self.assertEqual(bazi, bazi2)
    self.assertIs(bazi2.backend, CalendarBackend.HKO)
    # The copy still resolves the calendar utils on demand.
    self.assertEqual(bazi2.ganzhi_date, bazi.ganzhi_date)

    chart2: BaziChart = copy.deepcopy(chart)
    self.assertIs(chart2.bazi.backend, CalendarBackend.HKO)
    self.assertEqual(chart2.dayun_start_moment, chart.dayun_start_moment)
