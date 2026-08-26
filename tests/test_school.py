# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_school.py

import dataclasses
import inspect
from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from src.calendar import CalendarBackend
from src.bazi import Bazi, BaziGender
from src.bazi_chart import BaziChart
from src.rules import DizhiRules
from src.utils import dizhi_utils
from src.school import (
  BaziPrecision, DayunYearRule, DayRollover, KeyStem, BaziSchool, BaziConfig,
  DEFAULT_SCHOOL, DEFAULT_CONFIG,
)


def test_bazi_precision_basic() -> None:
  assert len(BaziPrecision) == 3

  assert str(BaziPrecision.DAY) == 'day'
  assert str(BaziPrecision.HOUR) == 'hour'
  assert str(BaziPrecision.MINUTE) == 'minute'


def test_dayun_year_rule_basic() -> None:
  assert len(DayunYearRule) == 2
  assert str(DayunYearRule.JIE_PROJECTED) == 'jie_projected'
  assert str(DayunYearRule.FIXED_DECADE) == 'fixed_decade'


def test_school_enums_basic() -> None:
  assert len(DayRollover) == 2
  assert DayRollover.WAN_ZISHI.value == 0 # 晚子时, the default.
  assert DayRollover.ZIZHENG.value == 1   # 子正.

  assert len(KeyStem) == 2
  assert KeyStem.DAY_MASTER.value == 0  # 日干, the 《三命通会》 reading, the default.
  assert KeyStem.YEAR_MASTER.value == 1 # 年干.

  assert len(DizhiRules.GongheDef) == 2
  assert len(DizhiRules.GongDef) == 4


def test_school_defaults() -> None:
  assert BaziSchool().day_rollover is DayRollover.WAN_ZISHI
  assert BaziSchool().hongyan_key is KeyStem.DAY_MASTER
  assert BaziSchool().anhe_def is DizhiRules.AnheDef.NORMAL_EXTENDED
  assert BaziSchool().xing_def is DizhiRules.XingDef.LOOSE
  assert BaziSchool().gong_def is DizhiRules.GongDef.SAME_STEM_NARROW
  assert BaziSchool() == DEFAULT_SCHOOL


def test_config_type_gates() -> None:
  # The constructor takes the strict types only; coercion lives in `from_values`.
  with pytest.raises(TypeError):
    BaziConfig(precision='day') # type: ignore
  with pytest.raises(TypeError):
    BaziConfig(backend='hko') # type: ignore
  with pytest.raises(TypeError):
    BaziConfig(dayun_year_rule='fixed_decade') # type: ignore
  with pytest.raises(TypeError):
    BaziConfig(school=DayRollover.ZIZHENG) # type: ignore # An enum is not a `BaziSchool`.


def test_every_school_field_has_a_type_gate() -> None:
  # Mechanical binding: every `BaziSchool` field must reject a wrong type at construction --
  # adding a knob without a gate fails here, no per-field test needed (issue #69).
  # 机械绑定：每个字段都要有构造期类型闸，加字段不加闸会在这里响。
  for f in dataclasses.fields(BaziSchool):
    with pytest.raises(TypeError):
      BaziSchool(**{f.name: object()}) # type: ignore


def test_every_school_field_reaches_json() -> None:
  # Mechanical binding: every `BaziSchool` field must land in JSON under its own name --
  # adding a knob without serializing it fails here (issue #69).
  # 机械绑定：每个字段都要以同名键进 JSON，加字段不序列化会在这里响。
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  assert {f.name for f in dataclasses.fields(BaziSchool)} == set(chart.json['school'])


def test_config_and_school_are_frozen() -> None:
  config: BaziConfig = BaziConfig()
  with pytest.raises(FrozenInstanceError):
    config.precision = BaziPrecision.HOUR # type: ignore
  with pytest.raises(FrozenInstanceError):
    config.school = BaziSchool(day_rollover=DayRollover.ZIZHENG) # type: ignore
  with pytest.raises(FrozenInstanceError):
    DEFAULT_SCHOOL.hongyan_key = KeyStem.YEAR_MASTER # type: ignore


# Every alias below must resolve, case insensitively -- written out as data so the test
# shares no table with src.
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


@pytest.mark.parametrize('spelling, expected', [
  ('jie_projected', DayunYearRule.JIE_PROJECTED),
  ('JIE_PROJECTED', DayunYearRule.JIE_PROJECTED),
  ('Jie_Projected', DayunYearRule.JIE_PROJECTED),
  ('fixed_decade', DayunYearRule.FIXED_DECADE),
  ('FIXED_DECADE', DayunYearRule.FIXED_DECADE),
  ('Fixed_Decade', DayunYearRule.FIXED_DECADE),
])
def test_from_values_dayun_year_rule_spellings(spelling: str, expected: DayunYearRule) -> None:
  assert DayunYearRule.from_str(spelling) is expected
  assert BaziConfig.from_values(dayun_year_rule=spelling).dayun_year_rule is expected


def test_from_values_enum_passthrough() -> None:
  config: BaziConfig = BaziConfig.from_values(
    precision=BaziPrecision.HOUR,
    backend=CalendarBackend.HKO,
    dayun_year_rule=DayunYearRule.FIXED_DECADE,
  )
  assert config.precision is BaziPrecision.HOUR
  assert config.backend is CalendarBackend.HKO
  assert config.dayun_year_rule is DayunYearRule.FIXED_DECADE


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
  with pytest.raises(ValueError):
    BaziConfig.from_values(dayun_year_rule='rolling_decade')
  with pytest.raises(TypeError):
    BaziConfig.from_values(dayun_year_rule=10) # type: ignore
  with pytest.raises(TypeError):
    DayunYearRule.from_str(10) # type: ignore
  with pytest.raises(TypeError):
    BaziConfig.from_values(school='default') # type: ignore # No string spelling for school.


def test_from_values_school_passthrough() -> None:
  school: BaziSchool = BaziSchool(day_rollover=DayRollover.ZIZHENG, hongyan_key=KeyStem.YEAR_MASTER)
  config: BaziConfig = BaziConfig.from_values(school=school)
  assert config.school is school
  assert config.precision is BaziPrecision.DAY # Untouched knobs keep their defaults.
  assert config.backend is CalendarBackend.CELESTIAL
  assert config.dayun_year_rule is DayunYearRule.JIE_PROJECTED


def test_defaults_are_defined_once() -> None:
  # The defaults live in the field defaults only; the constants pick them up.
  assert BaziConfig() == DEFAULT_CONFIG
  assert BaziConfig() is not DEFAULT_CONFIG
  assert BaziConfig().school is DEFAULT_SCHOOL
  assert BaziConfig().dayun_year_rule is DayunYearRule.JIE_PROJECTED
  assert BaziConfig.from_values() == DEFAULT_CONFIG
  assert BaziConfig.from_values().school is DEFAULT_SCHOOL
  assert BaziConfig.from_values().dayun_year_rule is DayunYearRule.JIE_PROJECTED
  assert DEFAULT_CONFIG.school is DEFAULT_SCHOOL


def test_school_defaults_match_utils_signature_defaults() -> None:
  # The majority reading is spelled twice by design -- the school field defaults (chart
  # level) and the utils signature defaults (per-query override, same shape as
  # `anhe` / `xing`). Pin the two spellings identical so they can't drift apart;
  # do NOT "fix" this by making utils import school (issue #69).
  # 「多数派口径」刻意两写——school 字段默认（盘级）与 utils 签名默认（单次覆盖，同
  # `anhe` / `xing` 先例）；钉住两处等价防漂移，但别让 utils 反过来 import school（issue #69）。
  for fn in (dizhi_utils.search, dizhi_utils.discover, dizhi_utils.discover_mutual):
    params = inspect.signature(fn).parameters
    assert BaziSchool().anhe_def is params['anhe_def'].default
    assert BaziSchool().xing_def is params['xing_def'].default
  for positioned_fn in (dizhi_utils.search_ganzhis, dizhi_utils.discover_ganzhis,
                        dizhi_utils.discover_mutual_ganzhis):
    params = inspect.signature(positioned_fn).parameters
    assert BaziSchool().anhe_def is params['anhe_def'].default
    assert BaziSchool().xing_def is params['xing_def'].default
    assert BaziSchool().gong_def is params['gong_def'].default


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
  zi_bazi: Bazi = Bazi.create(
    dt,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)),
  )

  assert default_bazi != zi_bazi
  assert hash(default_bazi) != hash(zi_bazi)
  assert len({default_bazi, zi_bazi}) == 2

  # Same school (by value, not identity): equal, same hash, set dedups.
  same_school: Bazi = Bazi.create(
    dt,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)),
  )
  assert zi_bazi == same_school
  assert hash(zi_bazi) == hash(same_school)
  assert len({zi_bazi, same_school}) == 1

  # The evaluation-time knobs distinguish charts the same way (评估期旋钮同样区分两盘).
  for variant_school in (
    BaziSchool(hongyan_key=KeyStem.YEAR_MASTER),
    BaziSchool(anhe_def=DizhiRules.AnheDef.MANGPAI),
    BaziSchool(xing_def=DizhiRules.XingDef.STRICT),
    BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE),
  ):
    variant_bazi: Bazi = Bazi.create(dt, BaziGender.MALE, BaziConfig(school=variant_school))
    assert default_bazi != variant_bazi
    assert hash(default_bazi) != hash(variant_bazi)
    assert len({default_bazi, variant_bazi}) == 2


def test_eq_hash_include_dayun_year_rule() -> None:
  dt: datetime = datetime(1910, 4, 7, 6, 1)
  projected: Bazi = Bazi.create(dt, BaziGender.MALE)
  fixed: Bazi = Bazi.create(
    dt,
    BaziGender.MALE,
    BaziConfig(dayun_year_rule=DayunYearRule.FIXED_DECADE),
  )

  assert projected != fixed
  assert hash(projected) != hash(fixed)
  assert len({projected, fixed}) == 2


def test_json_roundtrip_default_school() -> None:
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  j = chart.json
  assert j['school'] == {
    'day_rollover': 'WAN_ZISHI', 'hongyan_key': 'DAY_MASTER',
    'anhe_def': 'NORMAL_EXTENDED', 'xing_def': 'LOOSE', 'gong_def': 'SAME_STEM_NARROW',
  }

  rebuilt: BaziChart = BaziChart(
    Bazi.create(datetime.fromisoformat(j['birth_time']), j['gender'],
                BaziConfig.from_values(
                  precision=j['precision'],
                  backend=j['backend'],
                  dayun_year_rule=j['dayun_year_rule'],
                  school=BaziSchool(
                    day_rollover=DayRollover[j['school']['day_rollover']],
                    hongyan_key=KeyStem[j['school']['hongyan_key']],
                    anhe_def=DizhiRules.AnheDef[j['school']['anhe_def']],
                    xing_def=DizhiRules.XingDef[j['school']['xing_def']],
                    gong_def=DizhiRules.GongDef[j['school']['gong_def']],
                  ),
                ))
  )
  assert rebuilt.json == j
  assert rebuilt.bazi == chart.bazi


def test_json_roundtrip_non_default_school() -> None:
  # A non-default school must survive the JSON roundtrip losslessly: rebuilding
  # from the json alone reproduces the same chart, not a silent default-school one.
  # All five knobs flipped, so each field proves it roundtrips (issue #69).
  # 五个旋钮全部取非默认值——每个字段各自证明它能往返。
  school: BaziSchool = BaziSchool(
    day_rollover=DayRollover.ZIZHENG,
    hongyan_key=KeyStem.YEAR_MASTER,
    anhe_def=DizhiRules.AnheDef.MANGPAI,
    xing_def=DizhiRules.XingDef.STRICT,
    gong_def=DizhiRules.GongDef.LU_NARROW,
  )
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE,
                                           BaziConfig(school=school)))
  j = chart.json
  assert j['school'] == {
    'day_rollover': 'ZIZHENG', 'hongyan_key': 'YEAR_MASTER',
    'anhe_def': 'MANGPAI', 'xing_def': 'STRICT', 'gong_def': 'LU_NARROW',
  }

  rebuilt: BaziChart = BaziChart(
    Bazi.create(datetime.fromisoformat(j['birth_time']), j['gender'],
                BaziConfig.from_values(
                  precision=j['precision'],
                  backend=j['backend'],
                  dayun_year_rule=j['dayun_year_rule'],
                  school=BaziSchool(
                    day_rollover=DayRollover[j['school']['day_rollover']],
                    hongyan_key=KeyStem[j['school']['hongyan_key']],
                    anhe_def=DizhiRules.AnheDef[j['school']['anhe_def']],
                    xing_def=DizhiRules.XingDef[j['school']['xing_def']],
                    gong_def=DizhiRules.GongDef[j['school']['gong_def']],
                  ),
                ))
  )
  assert rebuilt.json == j
  assert rebuilt.bazi == chart.bazi
  assert rebuilt.bazi.config.school == school
