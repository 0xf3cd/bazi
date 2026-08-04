# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_school.py

import pytest

from dataclasses import FrozenInstanceError
from datetime import datetime

from src.calendar import CalendarBackend
from src.bazi import Bazi, BaziGender
from src.bazi_chart import BaziChart
from src.school import (
  BaziPrecision, DayRollover, KeyStem, BaziSchool, BaziConfig,
  DEFAULT_SCHOOL, DEFAULT_CONFIG,
)


def test_school_enums_basic() -> None:
  assert len(DayRollover) == 2
  assert DayRollover.WAN_ZISHI.value == 0 # 晚子时, the default.
  assert DayRollover.ZIZHENG.value == 1   # 子正.

  assert len(KeyStem) == 2
  assert KeyStem.DAY_MASTER.value == 0  # 日干, the 《三命通会》 reading, the default.
  assert KeyStem.YEAR_MASTER.value == 1 # 年干.


def test_school_defaults() -> None:
  assert BaziSchool().day_rollover is DayRollover.WAN_ZISHI
  assert BaziSchool().hongyan_key is KeyStem.DAY_MASTER
  assert BaziSchool() == DEFAULT_SCHOOL


def test_config_type_gates() -> None:
  # The constructor takes the strict types only; coercion lives in `from_values`.
  with pytest.raises(TypeError):
    BaziConfig(precision='day') # type: ignore
  with pytest.raises(TypeError):
    BaziConfig(backend='hko') # type: ignore
  with pytest.raises(TypeError):
    BaziConfig(school=DayRollover.ZIZHENG) # type: ignore # An enum is not a `BaziSchool`.
  with pytest.raises(TypeError):
    BaziSchool(day_rollover='wan_zishi') # type: ignore
  with pytest.raises(TypeError):
    BaziSchool(hongyan_key=0) # type: ignore


def test_config_and_school_are_frozen() -> None:
  config: BaziConfig = BaziConfig()
  with pytest.raises(FrozenInstanceError):
    config.precision = BaziPrecision.HOUR # type: ignore
  with pytest.raises(FrozenInstanceError):
    config.school = BaziSchool(day_rollover=DayRollover.ZIZHENG) # type: ignore
  with pytest.raises(FrozenInstanceError):
    DEFAULT_SCHOOL.hongyan_key = KeyStem.YEAR_MASTER # type: ignore


# The same acceptance face `Bazi.create` historically parsed: every alias below must
# resolve, case insensitively -- written out as data so the test shares no table with src.
@pytest.mark.parametrize('spelling, expected', [
  ('分', BaziPrecision.MINUTE), ('分钟', BaziPrecision.MINUTE),
  ('m', BaziPrecision.MINUTE), ('M', BaziPrecision.MINUTE),
  ('min', BaziPrecision.MINUTE), ('Min', BaziPrecision.MINUTE),
  ('minute', BaziPrecision.MINUTE), ('MINUTE', BaziPrecision.MINUTE),
  ('时', BaziPrecision.HOUR), ('小时', BaziPrecision.HOUR),
  ('h', BaziPrecision.HOUR), ('H', BaziPrecision.HOUR),
  ('hour', BaziPrecision.HOUR), ('HOUR', BaziPrecision.HOUR), ('Hour', BaziPrecision.HOUR),
  ('天', BaziPrecision.DAY), ('日', BaziPrecision.DAY),
  ('d', BaziPrecision.DAY), ('D', BaziPrecision.DAY),
  ('day', BaziPrecision.DAY), ('DAY', BaziPrecision.DAY), ('Day', BaziPrecision.DAY),
])
def test_from_values_precision_aliases(spelling: str, expected: BaziPrecision) -> None:
  assert BaziConfig.from_values(precision=spelling).precision is expected


# Both the member name and the value resolve, case insensitively (same face as
# `CalendarBackend.from_str`, which does the actual parsing).
@pytest.mark.parametrize('spelling, expected', [
  ('hko', CalendarBackend.HKO), ('HKO', CalendarBackend.HKO), ('Hko', CalendarBackend.HKO),
  ('celestial', CalendarBackend.CELESTIAL), ('CELESTIAL', CalendarBackend.CELESTIAL),
  ('Celestial', CalendarBackend.CELESTIAL),
  ('celestial-algo2', CalendarBackend.CELESTIAL_ALGO2),
  ('CELESTIAL_ALGO2', CalendarBackend.CELESTIAL_ALGO2),
  ('celestial_algo2', CalendarBackend.CELESTIAL_ALGO2),
])
def test_from_values_backend_spellings(spelling: str, expected: CalendarBackend) -> None:
  assert BaziConfig.from_values(backend=spelling).backend is expected


def test_from_values_enum_passthrough() -> None:
  config: BaziConfig = BaziConfig.from_values(precision=BaziPrecision.HOUR, backend=CalendarBackend.HKO)
  assert config.precision is BaziPrecision.HOUR
  assert config.backend is CalendarBackend.HKO


@pytest.mark.parametrize('bad', ['sec', '秒', 'hr', 'days', ''])
def test_from_values_rejects_bad_precision(bad: str) -> None:
  with pytest.raises(ValueError):
    BaziConfig.from_values(precision=bad)


def test_from_values_rejection_face() -> None:
  with pytest.raises(ValueError):
    BaziConfig.from_values(backend='lunar')
  with pytest.raises(TypeError):
    BaziConfig.from_values(precision=1984) # type: ignore
  with pytest.raises(TypeError):
    BaziConfig.from_values(backend=42) # type: ignore
  with pytest.raises(TypeError):
    BaziConfig.from_values(school='default') # type: ignore # No string spelling for school.


def test_from_values_school_passthrough() -> None:
  school: BaziSchool = BaziSchool(day_rollover=DayRollover.ZIZHENG, hongyan_key=KeyStem.YEAR_MASTER)
  config: BaziConfig = BaziConfig.from_values(school=school)
  assert config.school is school
  assert config.precision is BaziPrecision.DAY # Untouched knobs keep their defaults.
  assert config.backend is CalendarBackend.CELESTIAL


def test_defaults_are_defined_once() -> None:
  # D-7: the defaults live in the field defaults only; the constants pick them up.
  assert BaziConfig() == DEFAULT_CONFIG
  assert BaziConfig() is not DEFAULT_CONFIG
  assert BaziConfig().school is DEFAULT_SCHOOL
  assert BaziConfig.from_values() == DEFAULT_CONFIG
  assert BaziConfig.from_values().school is DEFAULT_SCHOOL
  assert DEFAULT_CONFIG.school is DEFAULT_SCHOOL


def test_bazi_default_config_is_the_shared_default() -> None:
  # Every construction path picks up `DEFAULT_CONFIG` implicitly (默认零变化).
  dt: datetime = datetime(1984, 4, 2, 4, 2)
  assert Bazi.create(dt, BaziGender.男).config is DEFAULT_CONFIG
  assert Bazi(dt, BaziGender.男).config is DEFAULT_CONFIG
  assert Bazi.random().config is DEFAULT_CONFIG
  assert Bazi.create(dt, BaziGender.男) == Bazi(dt, BaziGender.男)


def test_eq_hash_include_school() -> None:
  # Same birth, same gender, different school: not equal, different hash, no set dedup.
  dt: datetime = datetime(1984, 4, 2, 4, 2)
  default_bazi: Bazi = Bazi.create(dt, BaziGender.MALE)
  zi_bazi: Bazi = Bazi.create(dt, BaziGender.MALE,
                              BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)))

  assert default_bazi != zi_bazi
  assert hash(default_bazi) != hash(zi_bazi)
  assert len({default_bazi, zi_bazi}) == 2

  # Same school (by value, not identity): equal, same hash, set dedups.
  same_school: Bazi = Bazi.create(dt, BaziGender.MALE,
                                  BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)))
  assert zi_bazi == same_school
  assert hash(zi_bazi) == hash(same_school)
  assert len({zi_bazi, same_school}) == 1


def test_json_roundtrip_default_school() -> None:
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  j = chart.json
  assert j['school'] == { 'day_rollover': 'WAN_ZISHI', 'hongyan_key': 'DAY_MASTER' }

  rebuilt: BaziChart = BaziChart(
    Bazi.create(datetime.fromisoformat(j['birth_time']), j['gender'],
                BaziConfig.from_values(
                  precision=j['precision'],
                  backend=j['backend'],
                  school=BaziSchool(
                    day_rollover=DayRollover[j['school']['day_rollover']],
                    hongyan_key=KeyStem[j['school']['hongyan_key']],
                  ),
                ))
  )
  assert rebuilt.json == j
  assert rebuilt.bazi == chart.bazi


def test_json_roundtrip_non_default_school() -> None:
  # A non-default school must survive the JSON roundtrip losslessly (D-5): rebuilding
  # from the json alone reproduces the same chart, not a silent default-school one.
  school: BaziSchool = BaziSchool(day_rollover=DayRollover.ZIZHENG, hongyan_key=KeyStem.YEAR_MASTER)
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE,
                                           BaziConfig(school=school)))
  j = chart.json
  assert j['school'] == { 'day_rollover': 'ZIZHENG', 'hongyan_key': 'YEAR_MASTER' }

  rebuilt: BaziChart = BaziChart(
    Bazi.create(datetime.fromisoformat(j['birth_time']), j['gender'],
                BaziConfig.from_values(
                  precision=j['precision'],
                  backend=j['backend'],
                  school=BaziSchool(
                    day_rollover=DayRollover[j['school']['day_rollover']],
                    hongyan_key=KeyStem[j['school']['hongyan_key']],
                  ),
                ))
  )
  assert rebuilt.json == j
  assert rebuilt.bazi == chart.bazi
  assert rebuilt.bazi.config.school == school
