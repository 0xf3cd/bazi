# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_school.py

import dataclasses
import inspect
from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from src.calendar import CalendarBackend
from src.bazi import Bazi, BaziGender
from src.bazi_chart import BaziChart, BaziJson
from src.rules import DizhiRules, ShenshaRules
from src.utils import dizhi_utils, shensha_utils
from src.school import (
  BaziPrecision, DayunYearRule, DayRollover, Anchor, BaziSchool, BaziConfig,
  DEFAULT_SCHOOL, DEFAULT_CONFIG, _ANCHOR_CHOICES,
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

  assert len(Anchor) == 3
  assert Anchor.YEAR.value == 0         # 年柱.
  assert Anchor.DAY.value == 1          # 日柱.
  assert Anchor.YEAR_AND_DAY.value == 2 # 年、日两柱各自为锚.

  assert len(DizhiRules.GongheDef) == 2
  assert len(DizhiRules.GongDef) == 4
  assert len(ShenshaRules.YangrenDef) == 3
  assert not hasattr(ShenshaRules, 'FeirenDef')
  assert len(ShenshaRules.TianyiDef) == 4


def test_school_defaults() -> None:
  assert BaziSchool().day_rollover is DayRollover.WAN_ZISHI
  assert BaziSchool().hongyan_anchor is Anchor.DAY
  assert BaziSchool().yangren_def is ShenshaRules.YangrenDef.ZIPING
  assert BaziSchool().tianyi_anchor is Anchor.YEAR_AND_DAY
  assert BaziSchool().tianyi_def is ShenshaRules.TianyiDef.GENG_WITH_JIA_WU
  assert BaziSchool().yima_anchor is Anchor.YEAR_AND_DAY
  assert BaziSchool().huagai_anchor is Anchor.YEAR_AND_DAY
  assert BaziSchool().jiangxing_anchor is Anchor.YEAR_AND_DAY
  assert BaziSchool().jiesha_anchor is Anchor.YEAR_AND_DAY
  assert BaziSchool().wangshen_anchor is Anchor.YEAR_AND_DAY
  assert BaziSchool().jinyu_anchor is Anchor.DAY
  assert BaziSchool().feiren_def is ShenshaRules.YangrenDef.ZIPING
  assert BaziSchool().zaisha_anchor is Anchor.YEAR
  assert BaziSchool().anhe_def is DizhiRules.AnheDef.NORMAL_EXTENDED
  assert BaziSchool().xing_def is DizhiRules.XingDef.LOOSE
  assert BaziSchool().gong_def is DizhiRules.GongDef.SAME_STEM_NARROW
  assert BaziSchool() == DEFAULT_SCHOOL


def test_school_positional_arguments_remain_stable() -> None:
  school: BaziSchool = BaziSchool(
    DayRollover.ZIZHENG,
    Anchor.YEAR,
    DizhiRules.AnheDef.MANGPAI,
    DizhiRules.XingDef.STRICT,
    DizhiRules.GongDef.LU_NARROW,
    ShenshaRules.YangrenDef.DIWANG,
    Anchor.YEAR,
    ShenshaRules.TianyiDef.YINGUI,
    Anchor.DAY,
    Anchor.DAY,
    Anchor.DAY,
    Anchor.DAY,
    Anchor.DAY,
    Anchor.YEAR_AND_DAY,
    ShenshaRules.YangrenDef.LUMING,
    Anchor.YEAR_AND_DAY,
  )
  assert school == BaziSchool(
    day_rollover=DayRollover.ZIZHENG,
    hongyan_anchor=Anchor.YEAR,
    anhe_def=DizhiRules.AnheDef.MANGPAI,
    xing_def=DizhiRules.XingDef.STRICT,
    gong_def=DizhiRules.GongDef.LU_NARROW,
    yangren_def=ShenshaRules.YangrenDef.DIWANG,
    tianyi_anchor=Anchor.YEAR,
    tianyi_def=ShenshaRules.TianyiDef.YINGUI,
    yima_anchor=Anchor.DAY,
    huagai_anchor=Anchor.DAY,
    jiangxing_anchor=Anchor.DAY,
    jiesha_anchor=Anchor.DAY,
    wangshen_anchor=Anchor.DAY,
    jinyu_anchor=Anchor.YEAR_AND_DAY,
    feiren_def=ShenshaRules.YangrenDef.LUMING,
    zaisha_anchor=Anchor.YEAR_AND_DAY,
  )


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


def test_every_config_field_has_a_type_gate() -> None:
  # Mechanical binding, the same one `BaziSchool` has: adding a knob without a gate fails here.
  # 机械绑定，与 `BaziSchool` 同款：加字段不加闸会在这里响。
  for f in dataclasses.fields(BaziConfig):
    with pytest.raises(TypeError):
      BaziConfig(**{f.name: object()}) # type: ignore


def test_every_school_field_has_a_type_gate() -> None:
  # Mechanical binding: every `BaziSchool` field must reject a wrong type at construction --
  # adding a knob without a gate fails here, no per-field test needed (issue #69).
  # 机械绑定：每个字段都要有构造期类型闸，加字段不加闸会在这里响。
  for f in dataclasses.fields(BaziSchool):
    with pytest.raises(TypeError):
      BaziSchool(**{f.name: object()}) # type: ignore


def test_anchor_choices_bind_to_every_anchor_field() -> None:
  # Mechanical binding: the supported-values table and the `Anchor`-typed fields are one
  # set. A new anchor knob with no entry -- or an entry naming no field -- fails here, which
  # is what keeps each anchor's provenance status explicit.
  # 机械绑定：支持值表与 `Anchor` 类型字段是同一个集合；加旋钮不登记（或登记了不存在
  # 的字段）都会在这里响——每个锚的出处状态必须显式记录。
  anchor_fields = {f.name for f in dataclasses.fields(BaziSchool) if f.type is Anchor}
  assert anchor_fields == set(_ANCHOR_CHOICES)
  assert len(anchor_fields) == 9
  # Every subset is non-empty and every member of it is a real `Anchor`.
  for name, allowed in _ANCHOR_CHOICES.items():
    assert allowed, name
    assert all(isinstance(a, Anchor) for a in allowed), name


def test_anchor_choices_are_the_only_accepted_values() -> None:
  # Both directions: a supported value constructs, one outside the table raises. Without
  # the second half a table that allowed everything would still pass.
  # 两个方向都测：支持值能构造，表外值要抛；只测前者的话，一张放行一切的表也会全绿。
  for name, allowed in _ANCHOR_CHOICES.items():
    for anchor in Anchor:
      if anchor in allowed:
        assert getattr(BaziSchool(**{name: anchor}), name) is anchor # type: ignore # Field name is data here.
      else:
        with pytest.raises(ValueError):
          BaziSchool(**{name: anchor}) # type: ignore # Field name is data here.


def test_anchor_choices_match_the_supported_readings() -> None:
  # The subsets are supported knowledge, not defaults -- pin them as data so a silent widening
  # (or a lost reading) shows up as a failed assertion, not as a new legal school.
  # 支持集不是默认值，按数据钉死：悄悄放宽或丢掉一个读法都会在这里响。
  assert _ANCHOR_CHOICES['hongyan_anchor'] == frozenset({Anchor.DAY, Anchor.YEAR})
  assert _ANCHOR_CHOICES['tianyi_anchor'] == frozenset({Anchor.DAY, Anchor.YEAR, Anchor.YEAR_AND_DAY})
  assert _ANCHOR_CHOICES['jinyu_anchor'] == frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY})
  assert _ANCHOR_CHOICES['zaisha_anchor'] == frozenset({Anchor.YEAR, Anchor.YEAR_AND_DAY})
  for name in ('yima_anchor', 'huagai_anchor', 'jiangxing_anchor', 'jiesha_anchor', 'wangshen_anchor'):
    assert _ANCHOR_CHOICES[name] == frozenset({Anchor.DAY, Anchor.YEAR_AND_DAY}), name


def test_mingli_tanyuan_is_the_book_profile() -> None:
  # The preset writes out the readings in 袁树珊's two editions: the five 支锚 Shenshas
  # and 天乙 on the day pillar, 金舆 already there by default. Knobs those sources do not
  # speak to keep the default profile's values.
  # 预设写出两版所载读法：五项支锚神煞与天乙取日柱，金舆本就是默认；两版未言及的旋钮保持
  # 默认档案的取值。
  preset: BaziSchool = BaziSchool.mingli_tanyuan()
  book_anchors = ('yima_anchor', 'huagai_anchor', 'jiangxing_anchor', 'jiesha_anchor',
                  'wangshen_anchor', 'tianyi_anchor', 'jinyu_anchor')
  for name in book_anchors:
    assert getattr(preset, name) is Anchor.DAY, name
  # Everything else is the default profile untouched -- 红艳 in particular, which those sources
  # have no reading for. Written as one `replace` so a knob quietly joining the preset fails
  # here rather than riding along under a default value.
  # 其余一律是默认档案原样——尤其红艳，两版没有它的读法。写成一次 `replace`，多塞一个旋钮
  # 会在这里响，而不是搭着默认值混过去。
  assert preset == dataclasses.replace(
    DEFAULT_SCHOOL,
    yima_anchor=Anchor.DAY,
    huagai_anchor=Anchor.DAY,
    jiangxing_anchor=Anchor.DAY,
    jiesha_anchor=Anchor.DAY,
    wangshen_anchor=Anchor.DAY,
    tianyi_anchor=Anchor.DAY,
    jinyu_anchor=Anchor.DAY,
  )
  assert preset.hongyan_anchor is DEFAULT_SCHOOL.hongyan_anchor
  assert preset != DEFAULT_SCHOOL
  assert BaziSchool.mingli_tanyuan() == preset


def test_every_school_field_reaches_json() -> None:
  # Mechanical binding: every `BaziSchool` field must land in JSON under its own name --
  # adding a knob without serializing it fails here (issue #69).
  # 机械绑定：每个字段都要以同名键进 JSON，加字段不序列化会在这里响。
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  declared: list[str] = [f.name for f in dataclasses.fields(BaziSchool)]
  assert list(chart.json['school']) == declared
  # The declared contract must track the fields too -- keys, order, and value type. Both the
  # serialization and `BaziSchool.from_json` derive from `fields()` behind a `cast`, so nothing
  # static binds either of them to `BaziJson.School` any more (issue #172).
  # 声明的契约也要跟着字段走：键、顺序、值类型。序列化与 `from_json` 都经 `cast` 推导，
  # 静态检查不再把任何一侧钉在 `BaziJson.School` 上。
  assert list(BaziJson.School.__annotations__) == declared
  assert set(BaziJson.School.__annotations__.values()) == {str}


def test_config_and_school_are_frozen() -> None:
  config: BaziConfig = BaziConfig()
  with pytest.raises(FrozenInstanceError):
    config.precision = BaziPrecision.HOUR # type: ignore
  with pytest.raises(FrozenInstanceError):
    config.school = BaziSchool(day_rollover=DayRollover.ZIZHENG) # type: ignore
  with pytest.raises(FrozenInstanceError):
    DEFAULT_SCHOOL.hongyan_anchor = Anchor.YEAR # type: ignore


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
  school: BaziSchool = BaziSchool(day_rollover=DayRollover.ZIZHENG, hongyan_anchor=Anchor.YEAR)
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
  # The default reading is spelled twice by design -- the school field defaults (chart
  # level) and the utils signature defaults (per-query override, same shape as
  # `anhe` / `xing`). Pin the two spellings identical so they can't drift apart;
  # do NOT "fix" this by making utils import school (issue #69).
  # 「默认口径」刻意两写——school 字段默认（盘级）与 utils 签名默认（单次覆盖，同
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
  assert BaziSchool().yangren_def is inspect.signature(shensha_utils.yangren).parameters['definition'].default
  assert BaziSchool().tianyi_def is inspect.signature(shensha_utils.tianyi).parameters['definition'].default
  assert BaziSchool().feiren_def is inspect.signature(shensha_utils.feiren).parameters['definition'].default


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
    BaziSchool(hongyan_anchor=Anchor.YEAR),
    BaziSchool(yangren_def=ShenshaRules.YangrenDef.DIWANG),
    BaziSchool(tianyi_anchor=Anchor.DAY),
    BaziSchool(tianyi_def=ShenshaRules.TianyiDef.YINGUI),
    BaziSchool(yima_anchor=Anchor.DAY),
    BaziSchool(huagai_anchor=Anchor.DAY),
    BaziSchool(jiangxing_anchor=Anchor.DAY),
    BaziSchool(jiesha_anchor=Anchor.DAY),
    BaziSchool(wangshen_anchor=Anchor.DAY),
    BaziSchool(jinyu_anchor=Anchor.YEAR_AND_DAY),
    BaziSchool(feiren_def=ShenshaRules.YangrenDef.DIWANG),
    BaziSchool(zaisha_anchor=Anchor.YEAR_AND_DAY),
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
    'day_rollover': 'WAN_ZISHI', 'hongyan_anchor': 'DAY',
    'yangren_def': 'ZIPING',
    'anhe_def': 'NORMAL_EXTENDED', 'xing_def': 'LOOSE', 'gong_def': 'SAME_STEM_NARROW',
    'tianyi_anchor': 'YEAR_AND_DAY', 'tianyi_def': 'GENG_WITH_JIA_WU',
    'yima_anchor': 'YEAR_AND_DAY', 'huagai_anchor': 'YEAR_AND_DAY',
    'jiangxing_anchor': 'YEAR_AND_DAY', 'jiesha_anchor': 'YEAR_AND_DAY',
    'wangshen_anchor': 'YEAR_AND_DAY',
    'jinyu_anchor': 'DAY',
    'feiren_def': 'ZIPING',
    'zaisha_anchor': 'YEAR',
  }

  rebuilt: BaziChart = BaziChart(
    Bazi.create(datetime.fromisoformat(j['birth_time']), j['gender'],
                BaziConfig.from_values(
                  precision=j['precision'],
                  backend=j['backend'],
                  dayun_year_rule=j['dayun_year_rule'],
                  school=BaziSchool.from_json(j['school']),
                ))
  )
  assert rebuilt.json == j
  assert rebuilt.bazi == chart.bazi


def test_json_roundtrip_non_default_school() -> None:
  # A non-default school must survive the JSON roundtrip losslessly: rebuilding
  # from the json alone reproduces the same chart, not a silent default-school one.
  # Every field takes a non-default value, so each one proves it roundtrips (issue #69).
  # 每个字段都取非默认值，逐项证明能往返。
  school: BaziSchool = BaziSchool(
    day_rollover=DayRollover.ZIZHENG,
    hongyan_anchor=Anchor.YEAR,
    yangren_def=ShenshaRules.YangrenDef.DIWANG,
    anhe_def=DizhiRules.AnheDef.MANGPAI,
    xing_def=DizhiRules.XingDef.STRICT,
    gong_def=DizhiRules.GongDef.LU_NARROW,
    tianyi_anchor=Anchor.YEAR,
    tianyi_def=ShenshaRules.TianyiDef.YINGUI,
    yima_anchor=Anchor.DAY,
    huagai_anchor=Anchor.DAY,
    jiangxing_anchor=Anchor.DAY,
    jiesha_anchor=Anchor.DAY,
    wangshen_anchor=Anchor.DAY,
    jinyu_anchor=Anchor.YEAR_AND_DAY,
    feiren_def=ShenshaRules.YangrenDef.LUMING,
    zaisha_anchor=Anchor.YEAR_AND_DAY,
  )
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE,
                                           BaziConfig(school=school)))
  j = chart.json
  assert j['school'] == {
    'day_rollover': 'ZIZHENG', 'hongyan_anchor': 'YEAR',
    'yangren_def': 'DIWANG',
    'anhe_def': 'MANGPAI', 'xing_def': 'STRICT', 'gong_def': 'LU_NARROW',
    'tianyi_anchor': 'YEAR', 'tianyi_def': 'YINGUI',
    'yima_anchor': 'DAY', 'huagai_anchor': 'DAY',
    'jiangxing_anchor': 'DAY', 'jiesha_anchor': 'DAY',
    'wangshen_anchor': 'DAY',
    'jinyu_anchor': 'YEAR_AND_DAY',
    'feiren_def': 'LUMING',
    'zaisha_anchor': 'YEAR_AND_DAY',
  }

  rebuilt: BaziChart = BaziChart(
    Bazi.create(datetime.fromisoformat(j['birth_time']), j['gender'],
                BaziConfig.from_values(
                  precision=j['precision'],
                  backend=j['backend'],
                  dayun_year_rule=j['dayun_year_rule'],
                  school=BaziSchool.from_json(j['school']),
                ))
  )
  assert rebuilt.json == j
  assert rebuilt.bazi == chart.bazi
  assert rebuilt.bazi.config.school == school


def test_from_json_ignores_keys_that_name_no_field() -> None:
  # The reader takes the fields it declares; a key naming none of them is not an error.
  # The roundtrip itself is pinned by `test_json_roundtrip_default_school` and
  # `test_json_roundtrip_non_default_school`, which both rebuild through `from_json`.
  # 读法只取自己声明的字段，不对应字段的键不算错；往返本身由两条 roundtrip 测试钉住。
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  serialized: dict[str, object] = dict(chart.json['school'])
  serialized['not_a_school_field'] = 'WHATEVER'
  assert BaziSchool.from_json(serialized) == chart.bazi.config.school


def test_from_json_takes_the_profile_whole() -> None:
  # Mechanical binding: dropping any one field, or spelling any one member wrong, is
  # rejected -- a partial profile never silently falls back to defaults (issue #172).
  # 机械绑定：少任何一个字段、写错任何一个成员名都要被拒，残缺档案不许静默取默认。
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  serialized: dict[str, object] = dict(chart.json['school'])

  for f in dataclasses.fields(BaziSchool):
    with pytest.raises(ValueError):
      BaziSchool.from_json({k: v for k, v in serialized.items() if k != f.name})
    with pytest.raises(ValueError):
      BaziSchool.from_json({**serialized, f.name: 'NOT_A_MEMBER'})
    with pytest.raises(TypeError):
      BaziSchool.from_json({**serialized, f.name: 0})


class _DuckMapping:
  '''Looks up like a mapping without being one / 长得像映射但不是 `Mapping`。'''
  def __contains__(self, key: object) -> bool:
    return True
  def __getitem__(self, key: str) -> str:
    return 'WAN_ZISHI'


def test_from_json_rejects_a_non_mapping() -> None:
  # A duck-typed lookalike, not a list: with the gate gone a list still raises `TypeError`
  # from its own indexing, so that input cannot tell the gate apart from its absence.
  # 用鸭子冒牌货而非 list：删掉闸之后 list 照样因下标类型抛 `TypeError`，分不出闸在不在。
  with pytest.raises(TypeError):
    BaziSchool.from_json(_DuckMapping()) # type: ignore
