# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_analysis_registry.py

import pytest

import ast
import dataclasses
import inspect
import itertools
import sys
from datetime import datetime
from collections.abc import Callable
from types import FrameType

from bazi.defines import Tiangan, Dizhi, Ganzhi
from bazi.utils import dizhi_utils
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig, BaziSchool, Anchor, _ANCHOR_CHOICES
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind, TransitSet
from bazi.analyzer import relationship as relationship_module
from bazi.analyzer.relationship import (
  RelationshipAnalyzer, TransitAnalysis, ShenshaAnalysis, AtBirthShenshaAnalysis, _REGISTRY,
)

from relationship_samples import at_year


def test_registry_matches_shensha_analysis_keys() -> None:
  '''The Shensha registry and `ShenshaAnalysis` must stay in sync / 神煞注册表和 ShenshaAnalysis 的键必须保持同步。'''
  assert set(_REGISTRY.keys()) == set(ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__)


def test_analyses_are_built_from_the_registry() -> None:
  # Both analyses build their dicts by iterating the registry behind a `cast`, so mypy no
  # longer checks the key set -- this is the executor. A registry entry that never lands in
  # the result, or a declared key with no entry, fails here (issue #172).
  # 两处分析都在 `cast` 之后按注册表推导，键集不再由 mypy 检查——这条测试就是执行者。
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  analyzer = RelationshipAnalyzer(chart)

  at_birth_keys = AtBirthShenshaAnalysis.__required_keys__ | AtBirthShenshaAnalysis.__optional_keys__
  assert set(analyzer.at_birth.shensha) == set(at_birth_keys)

  transits = at_year(TransitChart(chart), chart.bazi.ganzhi_year).select(TransitKind.LIUNIAN)
  common_keys = ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__
  assert set(analyzer.transits.shensha(transits)) == set(common_keys)


def test_at_birth_extras_are_whole_pillar_only() -> None:
  common_keys = ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__
  at_birth_keys = AtBirthShenshaAnalysis.__required_keys__ | AtBirthShenshaAnalysis.__optional_keys__
  assert at_birth_keys == common_keys | {'kuigang', 'tianshe'}
  assert {'kuigang', 'tianshe'}.isdisjoint(_REGISTRY)


def test_at_birth_anchors_keep_kind_and_scope() -> None:
  '''Pin every (kind, anchor) pair's key x inspected-pillar calls, repeated branch values
  included. This is the executor for the one at-birth rule: a Tiangan key inspects all four
  branches, a Dizhi key skips its own pillar, and a two-pillar anchor runs once per pillar.
  一条原局规则的执行者：干锚查四支，支锚跳过自身柱，两柱锚按柱各跑一遍。'''
  YD, MD, DD, HD = Dizhi.子, Dizhi.午, Dizhi.午, Dizhi.戌
  YT, DT = Tiangan.庚, Tiangan.丙
  all_dizhis = (YD, MD, DD, HD)
  year_dizhi_calls = ((YD, MD), (YD, DD), (YD, HD))
  day_dizhi_calls = ((DD, YD), (DD, MD), (DD, HD))
  year_tiangan_calls = tuple((YT, dizhi) for dizhi in all_dizhis)
  day_tiangan_calls = tuple((DT, dizhi) for dizhi in all_dizhis)

  DIZHI = relationship_module._AnchorKind.DIZHI
  TIANGAN = relationship_module._AnchorKind.TIANGAN
  cases: tuple[tuple[relationship_module._AnchorKind, Anchor, tuple[tuple[Tiangan | Dizhi, Dizhi], ...]], ...] = (
    (DIZHI, Anchor.YEAR, year_dizhi_calls),
    (DIZHI, Anchor.DAY, day_dizhi_calls),
    (DIZHI, Anchor.YEAR_AND_DAY, (*year_dizhi_calls, *day_dizhi_calls)),
    (TIANGAN, Anchor.YEAR, year_tiangan_calls),
    (TIANGAN, Anchor.DAY, day_tiangan_calls),
    (TIANGAN, Anchor.YEAR_AND_DAY, (*year_tiangan_calls, *day_tiangan_calls)),
  )
  assert {(kind, anchor) for kind, anchor, _ in cases} == set(itertools.product(
    relationship_module._AnchorKind,
    Anchor,
  ))

  chart = BaziChart(Bazi.create('2020-07-02 19:08', 'female'))
  assert tuple(map(str, chart.bazi.pillars)) == ('庚子', '壬午', '丙午', '戊戌')

  for kind, anchor, expected_calls in cases:
    calls: list[tuple[Tiangan | Dizhi, Dizhi]] = []

    def record(key: Tiangan | Dizhi, dizhi: Dizhi) -> bool:
      calls.append((key, dizhi))
      return False

    spec = relationship_module._ShenshaSpec(record, kind, anchor, 'probe')
    assert relationship_module._eval_at_birth(spec, chart.bazi) == frozenset()
    assert tuple(calls) == expected_calls, (kind, anchor)


def test_at_birth_resolver_reads_chart_school() -> None:
  # A spec whose anchor is a resolver takes the knob from the chart, not from the spec --
  # the same rule then applies. 锚是解析函数时，取值来自盘上的旋钮，规则不变。
  YD, MD, DD, HD = Dizhi.子, Dizhi.午, Dizhi.午, Dizhi.戌
  expected = {
    Anchor.YEAR: ((YD, MD), (YD, DD), (YD, HD)),
    Anchor.YEAR_AND_DAY: ((YD, MD), (YD, DD), (YD, HD), (DD, YD), (DD, MD), (DD, HD)),
  }

  for anchor, expected_calls in expected.items():
    chart = BaziChart(Bazi.create(
      '2020-07-02 19:08',
      'female',
      BaziConfig(school=BaziSchool(zaisha_anchor=anchor)),
    ))
    calls: list[tuple[Tiangan | Dizhi, Dizhi]] = []

    def record(key: Tiangan | Dizhi, dizhi: Dizhi) -> bool:
      calls.append((key, dizhi))
      return False

    spec = relationship_module._ShenshaSpec(
      record,
      relationship_module._AnchorKind.DIZHI,
      lambda school: school.zaisha_anchor,
      'probe',
    )
    assert relationship_module._eval_at_birth(spec, chart.bazi) == frozenset()
    assert tuple(calls) == expected_calls, anchor


def test_at_birth_inspects_repeated_branches() -> None:
  # Every branch equals 丑 but the hour: a Dizhi anchor still skips only its OWN pillar,
  # so equal values never collapse the call list. 支值全同也只跳自身柱，不按值去重。
  chart = BaziChart(Bazi.create('1902-01-06 12:00', 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('辛丑', '辛丑', '己丑', '庚午')
  calls: list[tuple[Tiangan | Dizhi, Dizhi]] = []

  def record(key: Tiangan | Dizhi, dizhi: Dizhi) -> bool:
    calls.append((key, dizhi))
    return False

  spec = relationship_module._ShenshaSpec(
    record, relationship_module._AnchorKind.DIZHI, Anchor.YEAR_AND_DAY, 'probe')
  assert relationship_module._eval_at_birth(spec, chart.bazi) == frozenset()
  assert tuple(calls) == (
    (Dizhi.丑, Dizhi.丑), (Dizhi.丑, Dizhi.丑), (Dizhi.丑, Dizhi.午),
    (Dizhi.丑, Dizhi.丑), (Dizhi.丑, Dizhi.丑), (Dizhi.丑, Dizhi.午),
  )


def test_transit_anchors_reuse_keys_no_exclusion() -> None:
  # Transits share the at-birth key path, but no transit branch is the anchor's own pillar,
  # so every key inspects every transit branch -- including one equal to a natal branch.
  # 流运与原局共用取 key 路径；流运支不可能是锚柱自身，故每个 key 查全部流运支。
  chart = BaziChart(Bazi.create('2020-07-02 19:08', 'female'))
  assert tuple(map(str, chart.bazi.pillars)) == ('庚子', '壬午', '丙午', '戊戌')
  transit_dizhis = (Dizhi.卯, Dizhi.子)
  DIZHI = relationship_module._AnchorKind.DIZHI
  TIANGAN = relationship_module._AnchorKind.TIANGAN
  cases: tuple[tuple[relationship_module._AnchorKind, Anchor, tuple[Tiangan | Dizhi, ...]], ...] = (
    (DIZHI, Anchor.YEAR, (Dizhi.子,)),
    (DIZHI, Anchor.DAY, (Dizhi.午,)),
    (DIZHI, Anchor.YEAR_AND_DAY, (Dizhi.子, Dizhi.午)),
    (TIANGAN, Anchor.YEAR, (Tiangan.庚,)),
    (TIANGAN, Anchor.DAY, (Tiangan.丙,)),
    (TIANGAN, Anchor.YEAR_AND_DAY, (Tiangan.庚, Tiangan.丙)),
  )
  assert {(kind, anchor) for kind, anchor, _ in cases} == set(itertools.product(
    relationship_module._AnchorKind,
    Anchor,
  ))

  for kind, anchor, keys in cases:
    calls: list[tuple[Tiangan | Dizhi, Dizhi]] = []

    def record(key: Tiangan | Dizhi, dizhi: Dizhi) -> bool:
      calls.append((key, dizhi))
      return False

    spec = relationship_module._ShenshaSpec(record, kind, anchor, 'probe')
    assert relationship_module._eval_transits(spec, chart.bazi, transit_dizhis) == frozenset()
    assert tuple(calls) == tuple(
      (key, dizhi) for key in keys for dizhi in transit_dizhis
    ), (kind, anchor)


def test_every_anchor_member_is_wired_to_pillars() -> None:
  # Mechanical binding: the five deleted enums each carried an "unwired member" guard; one
  # table replaces them all, so one gate has to execute that invariant. A new `Anchor` member
  # with no entry would otherwise surface as a bare `KeyError` at lookup time.
  # 机械绑定：被删的五个枚举各带一条「成员未接线」守卫，合并成一张表后要有一道闸执行这条
  # 不变量——新成员漏登记的话，只会在查法时抛裸 `KeyError`。
  pillars = relationship_module._ANCHOR_PILLARS
  assert set(pillars) == set(Anchor)
  for anchor, indices in pillars.items():
    assert indices, anchor
    assert all(0 <= i < 4 for i in indices), anchor          # Four pillars, 年月日时.
    assert list(indices) == sorted(set(indices)), anchor     # Ascending and distinct: the
                                                             # call order follows pillar order.


def test_registry_anchors_are_the_declared_table() -> None:
  # The full roster of (kind, anchor) per Shensha, written out as data. A silently
  # re-anchored Shensha fails here, and so does one that quietly stops (or starts)
  # reading a school knob.
  # 每个神煞的（key 类型，锚）全表按数据钉死：偷偷换锚、或偷偷改成/不再读流派旋钮都会响。
  DIZHI = relationship_module._AnchorKind.DIZHI
  TIANGAN = relationship_module._AnchorKind.TIANGAN
  fixed = {
    name: (spec.kind, spec.anchor)
    for name, spec in _REGISTRY.items() if isinstance(spec.anchor, Anchor)
  }
  assert fixed == {
    'taohua':   (DIZHI, Anchor.YEAR_AND_DAY),
    'hongluan': (DIZHI, Anchor.YEAR),
    'tianxi':   (DIZHI, Anchor.YEAR),
    'guchen':   (DIZHI, Anchor.YEAR),
    'guasu':    (DIZHI, Anchor.YEAR),
    'yangren':  (TIANGAN, Anchor.DAY),
    'feiren':   (TIANGAN, Anchor.DAY),
    'lushen':   (TIANGAN, Anchor.DAY),
    'wenchanggui': (TIANGAN, Anchor.YEAR),
  }

  # The rest read one school knob each. Vary exactly that field and require the resolver to
  # follow it -- reading a neighbour's knob leaves the default behind and fails here.
  # 其余各读一个旋钮：每次只改那一个字段，读错邻居的旋钮就会拿回默认值而在这里响。
  knobs = {
    'hongyan':   (TIANGAN, 'hongyan_anchor'),
    'tianyi':    (TIANGAN, 'tianyi_anchor'),
    'jinyu':     (TIANGAN, 'jinyu_anchor'),
    'zaisha':    (DIZHI, 'zaisha_anchor'),
    'yima':      (DIZHI, 'yima_anchor'),
    'huagai':    (DIZHI, 'huagai_anchor'),
    'jiangxing': (DIZHI, 'jiangxing_anchor'),
    'jiesha':    (DIZHI, 'jiesha_anchor'),
    'wangshen':  (DIZHI, 'wangshen_anchor'),
    'wenchang':  (TIANGAN, 'wenchang_anchor'),
    'taiji':     (TIANGAN, 'taiji_anchor'),
    'guoyin':    (TIANGAN, 'guoyin_anchor'),
  }
  assert set(knobs) | set(fixed) == set(_REGISTRY)
  for name, (kind, field) in knobs.items():
    spec = _REGISTRY[name]
    assert spec.kind is kind, name
    assert not isinstance(spec.anchor, Anchor), name
    for anchor in _ANCHOR_CHOICES[field]:
      school = BaziSchool(**{field: anchor}) # type: ignore # Field name is data here.
      assert spec.anchor(school) is anchor, (name, anchor)


def test_registry_definitions_are_declared_fields() -> None:
  knobs = {
    'yangren': 'yangren_def',
    'feiren': 'feiren_def',
    'tianyi': 'tianyi_def',
    'wenchang': 'wenchang_def',
    'taiji': 'taiji_def',
    'guoyin': 'guoyin_def',
  }
  assert set(knobs) == {name for name, spec in _REGISTRY.items() if spec.definition is not None}
  default = BaziSchool()
  for name, field in knobs.items():
    resolver = _REGISTRY[name].definition
    assert resolver is not None
    # Vary only the named field: 羊刃 and 飞刃 share an enum and default, not a knob.
    for definition in type(getattr(default, field)):
      school = dataclasses.replace(default, **{field: definition})
      assert resolver(school) is definition, (name, definition)


@pytest.mark.parametrize('scope, plain_queries, gong_queries', [
  ('birth_house', 13, 2), ('birth_star', 13, 2), ('transit_house', 13, 2),
  ('star_transits', 13, 2), ('star_mutual', 13, 2), ('star_all', 26, 4),
])
def test_gong_supplement_skips_non_gong(scope: str, plain_queries: int, gong_queries: int) -> None:
  analyzer = RelationshipAnalyzer(BaziChart(Bazi.create('1980-01-12 20:00', 'male')))
  transits = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('甲午'),
    liuyue=Ganzhi.from_str('甲辰'),
  )
  queries: dict[str, Callable[[], object]] = {
    'birth_house': lambda: analyzer.at_birth.house_relations,
    'birth_star': lambda: analyzer.at_birth.star_relations,
    'transit_house': lambda: analyzer.transits.house_relations(transits),
    'star_transits': lambda: analyzer.transits.star_relations(transits, level=TransitAnalysis.Level.TRANSITS_ONLY),
    'star_mutual': lambda: analyzer.transits.star_relations(transits, level=TransitAnalysis.Level.MUTUAL),
    'star_all': lambda: analyzer.transits.star_relations(transits),
  }
  counts = {'plain': 0, 'supplement': 0, 'gong': 0}

  def profile(frame: FrameType, event: str, arg: object) -> None:
    if event != 'call' or frame.f_code.co_filename != dizhi_utils.__file__:
      return
    if frame.f_code.co_name == '_search_gong':
      counts['gong'] += 1
    elif frame.f_code.co_name == 'search':
      parent = frame.f_back
      while parent is not None:
        if parent.f_code.co_name in ('discover_ganzhis', 'discover_mutual_ganzhis'):
          counts['supplement'] += 1
          return
        parent = parent.f_back
      counts['plain'] += 1

  previous = sys.getprofile()
  sys.setprofile(profile)
  try:
    queries[scope]()
  finally:
    sys.setprofile(previous)
  assert counts == {'plain': plain_queries, 'supplement': 0, 'gong': gong_queries}


def test_dizhi_queries_use_chart_definitions() -> None:
  # Every query must explicitly receive definitions read from this chart's school (issue #69).
  gated = {
    'search', 'discover', 'discover_mutual',
    'search_ganzhis', 'discover_ganzhis', 'discover_mutual_ganzhis',
  }

  tree = ast.parse(inspect.getsource(relationship_module))
  queries = 0
  for function in (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)):
    bindings = {
      target.id
      for node in ast.walk(function) if isinstance(node, ast.Assign)
      if ast.unparse(node.value) in (
        'bazi.config.school.relation_definitions',
        'self._chart.bazi.config.school.relation_definitions',
      )
      for target in node.targets if isinstance(target, ast.Name)
    }
    for node in ast.walk(function):
      if not isinstance(node, ast.Call):
        continue
      f = node.func
      if not (isinstance(f, ast.Attribute) and f.attr in gated
              and isinstance(f.value, ast.Name) and f.value.id == 'dizhi_utils'):
        continue
      definitions = next((kw.value for kw in node.keywords if kw.arg == 'definitions'), None)
      assert isinstance(definitions, ast.Name) and definitions.id in bindings, node.lineno
      queries += 1
  assert queries > 0
