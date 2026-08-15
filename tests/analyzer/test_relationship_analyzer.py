# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analyzer.py

import pytest

import ast
import inspect
import random
import itertools

from src.defines import Tiangan, Dizhi, Shishen, DizhiRelation
from src.utils import shensha_utils, tiangan_utils, dizhi_utils, bazi_utils
from src.bazi import Bazi
from src.bazi_chart import BaziChart
from src.school import BaziConfig, BaziSchool, KeyStem
from src.transit_chart import TransitChart
from src.transits import TransitKind, TransitSet, TransitYear
from src.analyzer import relationship as relationship_module
from src.analyzer.relationship import RelationshipAnalyzer, TransitAnalysis, ShenshaAnalysis, _REGISTRY


@pytest.mark.slow
def test_at_birth_shensha() -> None:
  for _ in range(100):
    chart = BaziChart.random()
    analyzer = RelationshipAnalyzer(chart)

    dm: Tiangan = chart.bazi.day_master
    y, m, d, h = chart.bazi.four_dizhis

    # The 红艳 anchor stem follows the chart's school (查法锚干, issue #69) -- don't assume the day master.
    anchor: Tiangan = dm if chart.bazi.config.school.hongyan_key is KeyStem.DAY_MASTER else chart.bazi.year_pillar.tiangan

    at_birth = analyzer.at_birth

    # Taohua / 桃花
    expected_taohua: list[Dizhi] = []
    for dz1, dz2 in itertools.product([y], [m, d, h]):
      if shensha_utils.taohua(dz1, dz2):
        expected_taohua.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.taohua(dz1, dz2):
        expected_taohua.append(dz2)
    assert at_birth.shensha['taohua'] == set(expected_taohua)
    assert at_birth.shensha['taohua'] == at_birth.shensha['taohua'] # Repeated lookup must answer the same.

    # Hongyan / 红艳
    expected_hongyan: list[Dizhi] = []
    for tg, dz in itertools.product([anchor], [y, m, d, h]):
      if shensha_utils.hongyan(tg, dz):
        expected_hongyan.append(dz)
    assert at_birth.shensha['hongyan'] == set(expected_hongyan)
    assert at_birth.shensha['hongyan'] == at_birth.shensha['hongyan'] # Repeated lookup must answer the same.

    # Hongluan / 红鸾
    expected_hongluan: list[Dizhi] = []
    for dz1, dz2 in itertools.product([y], [m, d, h]):
      if shensha_utils.hongluan(dz1, dz2):
        expected_hongluan.append(dz2)
    assert at_birth.shensha['hongluan'] == set(expected_hongluan)
    assert at_birth.shensha['hongluan'] == at_birth.shensha['hongluan'] # Repeated lookup must answer the same.

    # Tianxi / 天喜
    expected_tianxi: list[Dizhi] = []
    for dz1, dz2 in itertools.product([y], [m, d, h]):
      if shensha_utils.tianxi(dz1, dz2):
        expected_tianxi.append(dz2)
    assert at_birth.shensha['tianxi'] == set(expected_tianxi)
    assert at_birth.shensha['tianxi'] == at_birth.shensha['tianxi'] # Repeated lookup must answer the same.

    # Yima / 驿马
    expected_yima: list[Dizhi] = []
    for dz1, dz2 in itertools.product([y], [m, d, h]):
      if shensha_utils.yima(dz1, dz2):
        expected_yima.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.yima(dz1, dz2):
        expected_yima.append(dz2)
    assert at_birth.shensha['yima'] == set(expected_yima)
    assert at_birth.shensha['yima'] == at_birth.shensha['yima'] # Repeated lookup must answer the same.


@pytest.mark.slow
def test_at_birth_day_master_relations() -> None:
  for _ in range(100):
    chart = BaziChart.random()
    analyzer = RelationshipAnalyzer(chart)

    dm = chart.bazi.day_master
    at_birth = analyzer.at_birth

    assert at_birth.day_master_relations == tiangan_utils.discover_mutual([
      chart.bazi.year_pillar.tiangan,
      chart.bazi.month_pillar.tiangan,
      chart.bazi.hour_pillar.tiangan
    ], [dm])
    assert at_birth.day_master_relations == at_birth.day_master_relations # Repeated lookup must answer the same.


@pytest.mark.slow
def test_at_birth_house_relations() -> None:
  for _ in range(100):
    chart = BaziChart.random()
    analyzer = RelationshipAnalyzer(chart)

    y, m, d, h = chart.bazi.four_dizhis
    at_birth = analyzer.at_birth

    # The oracle mirrors the analyzer by reading the chart's school profile (issue #69).
    school: BaziSchool = chart.bazi.config.school

    # For AtBirth analysis, the following two algorithms are equivalent.
    assert at_birth.house_relations == dizhi_utils.discover(
      [y, m, d, h], anhe_def=school.anhe_def, xing_def=school.xing_def,
    ).filter(
      lambda _, combo : d in combo
    )
    assert at_birth.house_relations == dizhi_utils.discover_mutual(
      [y, m, h], [d], anhe_def=school.anhe_def, xing_def=school.xing_def,
    )

    assert at_birth.house_relations == at_birth.house_relations # Repeated lookup must answer the same.


@pytest.mark.slow
def test_at_birth_star_relations() -> None:
  for _ in range(100):
    chart = BaziChart.random()
    analyzer = RelationshipAnalyzer(chart)

    at_birth = analyzer.at_birth
    stars = chart.relationship_stars

    for tg_combos in at_birth.star_relations.tiangan.values():
      for tg_combo in tg_combos:
        assert stars.tiangan in tg_combo
    for dz_combos in at_birth.star_relations.dizhi.values():
      for dz_combo in dz_combos:
        assert any(dz in dz_combo for dz in stars.dizhi)

    assert at_birth.star_relations.tiangan == at_birth.star_relations.tiangan # Repeated lookup must answer the same.
    assert at_birth.star_relations.dizhi == at_birth.star_relations.dizhi # Repeated lookup must answer the same.


@pytest.mark.slow
def test_filtered() -> None:
  '''Test "star_relations" only contain filtered combos.'''
  for _ in range(16):
    chart: BaziChart = BaziChart.random()
    analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)

    stars = chart.relationship_stars
    at_birth = analyzer.at_birth

    for tg_rel, tg_combos in tiangan_utils.discover(chart.bazi.four_tiangans).items():
      if tg_rel not in at_birth.star_relations.tiangan:
        assert all(stars.tiangan not in tg_combo for tg_combo in tg_combos)
      else:
        for tg_combo in tg_combos:
          assert (stars.tiangan in tg_combo) == (tg_combo in at_birth.star_relations.tiangan[tg_rel])

    for dz_rel, dz_combos in dizhi_utils.discover(
      chart.bazi.four_dizhis,
      anhe_def=chart.bazi.config.school.anhe_def, # The oracle mirrors the chart's school (issue #69).
      xing_def=chart.bazi.config.school.xing_def,
    ).items():
      if dz_rel not in at_birth.star_relations.dizhi:
        assert all(dz not in dz_combo for dz_combo in dz_combos for dz in stars.dizhi)
      else:
        for dz_combo in dz_combos:
          assert any(dz in dz_combo for dz in stars.dizhi) == (dz_combo in at_birth.star_relations.dizhi[dz_rel])


'''Operand type of `_equal`: either relation-discovery flavor.'''
DiscoveryType = tiangan_utils.TianganRelationDiscovery | dizhi_utils.DizhiRelationDiscovery
def _equal(discovery1: DiscoveryType, discovery2: DiscoveryType) -> bool:
  if type(discovery1) is not type(discovery2):
    return False
  if set(discovery1.keys()) != set(discovery2.keys()):
    return False
  for key in discovery1:
    if set(discovery1[key]) != set(discovery2[key]):  # type: ignore
      return False
  return True


def _random_year_transits(transit_chart: TransitChart, gz_year: int) -> TransitSet:
  full_transits = transit_chart.at(TransitYear(gz_year))
  available = tuple(full_transits)
  selected = random.sample(available, random.randint(1, len(available)))
  return full_transits.select(*selected)


@pytest.mark.slow
def test_transit_shensha() -> None:
  for _ in range(32):
    chart = BaziChart.random()
    transit_chart = TransitChart(chart)

    y_dz = chart.bazi.year_pillar.dizhi
    d_dz = chart.bazi.day_pillar.dizhi

    # The 红艳 anchor stem follows the chart's school (查法锚干, issue #69) -- don't assume the day master.
    anchor: Tiangan = (chart.bazi.day_master if chart.bazi.config.school.hongyan_key is KeyStem.DAY_MASTER
                       else chart.bazi.year_pillar.tiangan)

    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + random.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year)

      transit_dz = tuple(gz.dizhi for gz in transits.ganzhis)
      actual = transits_analysis.shensha(transits)

      # Taohua / 桃花
      expected = []
      for dz in transit_dz:
        if shensha_utils.taohua(y_dz, dz):
          expected.append(dz)
        if shensha_utils.taohua(d_dz, dz):
          expected.append(dz)
      assert actual['taohua'] == set(expected)

      # Hongyan / 红艳
      expected = []
      for dz in transit_dz:
        if shensha_utils.hongyan(anchor, dz):
          expected.append(dz)
      assert actual['hongyan'] == set(expected)

      # Hongluan / 红鸾
      expected = []
      for dz in transit_dz:
        if shensha_utils.hongluan(y_dz, dz):
          expected.append(dz)
      assert actual['hongluan'] == set(expected)

      # Tianxi / 天喜
      expected = []
      for dz in transit_dz:
        if shensha_utils.tianxi(y_dz, dz):
          expected.append(dz)
      assert actual['tianxi'] == set(expected)

      # Yima / 驿马
      expected = []
      for dz in transit_dz:
        if shensha_utils.yima(y_dz, dz):
          expected.append(dz)
        if shensha_utils.yima(d_dz, dz):
          expected.append(dz)
      assert actual['yima'] == set(expected)


# 红艳查法 variants (issue #69): `KeyStem` mounted on `BaziSchool.hongyan_key`; the analyzer
# re-reads the anchor stem from the chart's school profile at evaluation time. The chart below
# is the golden chart of `test_relationship_analysis.test_case1` (1984-04-01 11:08, male:
# 甲子/丁卯/乙丑/壬午) -- the day master 乙 keys on 申 (absent from the chart), while the year
# tiangan 甲 keys on 午 (the hour Dizhi), so the two 查法 answer differently on this chart.
@pytest.mark.parametrize('key_stem, expected', [
  (KeyStem.DAY_MASTER,  frozenset()),           # 日干乙 -> 申 (《三命通会》, the default): 申 not in 子卯丑午.
  (KeyStem.YEAR_MASTER, frozenset({Dizhi.午})), # 年干甲 -> 午: the hour Dizhi matches.
])
def test_hongyan_key_variant_at_birth(key_stem: KeyStem, expected: frozenset[Dizhi]) -> None:
  config: BaziConfig = BaziConfig(school=BaziSchool(hongyan_key=key_stem))
  chart: BaziChart = BaziChart(Bazi.create('1984-04-01 11:08', 'male', config))
  assert RelationshipAnalyzer(chart).at_birth.shensha['hongyan'] == expected

  # The default school is DAY_MASTER -- the long-pinned behavior carries over unchanged.
  if key_stem is KeyStem.DAY_MASTER:
    default_chart: BaziChart = BaziChart(Bazi.create('1984-04-01 11:08', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['hongyan'] == expected


@pytest.mark.parametrize('key_stem, expected', [
  (KeyStem.DAY_MASTER,  frozenset()),           # 日干乙 -> 申: not among the 1990 transit Dizhis 辰/午.
  (KeyStem.YEAR_MASTER, frozenset({Dizhi.午})), # 年干甲 -> 午: the 1990 流年 is 庚午.
])
def test_hongyan_key_variant_at_transits(key_stem: KeyStem, expected: frozenset[Dizhi]) -> None:
  '''Same chart; the selected 1990 Dayun and Liunian are 戊辰/庚午 (pinned in `test_case1`).'''
  config: BaziConfig = BaziConfig(school=BaziSchool(hongyan_key=key_stem))
  chart: BaziChart = BaziChart(Bazi.create('1984-04-01 11:08', 'male', config))
  transits: TransitAnalysis = RelationshipAnalyzer(chart).transits
  selected = TransitChart(chart).at(TransitYear(1990)).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  )
  assert transits.shensha(selected)['hongyan'] == expected


@pytest.mark.slow
def test_transit_day_master_relations() -> None:
  for _ in range(32):
    chart = BaziChart.random()
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + random.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year)

      transit_tg = tuple(gz.tiangan for gz in transits.ganzhis)
      expected = tiangan_utils.discover_mutual([chart.bazi.day_master], transit_tg)
      actual = transits_analysis.day_master_relations(transits)

      assert _equal(expected, actual)


@pytest.mark.slow
def test_transit_house_relations() -> None:
  for _ in range(32):
    chart = BaziChart.random()
    house = chart.house_of_relationship
    bazi = chart.bazi
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + random.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year)

      transit_dz = [gz.dizhi for gz in transits.ganzhis]

      actual = transits_analysis.house_relations(transits)
      for combos in actual.values():
        for combo in combos:
          assert house in combo
          assert not set(transit_dz).isdisjoint(combo)

      def __expected_filter(dz_rel: DizhiRelation, combo: dizhi_utils.DizhiCombo):
        # `house` must appear in the combo.
        if house not in combo:
          return False

        # Special handling for 自刑 cases.
        if len(combo) == 1:
          assert dz_rel is DizhiRelation.刑
          return house in transit_dz

        return not (combo - {house}).isdisjoint(transit_dz)

      expected = dizhi_utils.discover_mutual(
        bazi.four_dizhis, transit_dz,
        anhe_def=bazi.config.school.anhe_def, # The oracle mirrors the chart's school (issue #69).
        xing_def=bazi.config.school.xing_def,
      ).filter(__expected_filter)

      assert _equal(expected, actual)


@pytest.mark.slow
def test_transit_star_relations() -> None:
  for _ in range(32):
    chart = BaziChart.random()
    stars = chart.relationship_stars

    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(64):
      random_year = chart.bazi.ganzhi_year + random.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year)
      random_level = random.choice([
        TransitAnalysis.Level.TRANSITS_ONLY,
        TransitAnalysis.Level.MUTUAL,
        TransitAnalysis.Level.ALL
      ]) # mypy with Python 3.12 is problematic here on type checking... Explicitly list all enum values.

      transit_tg = tuple(gz.tiangan for gz in transits.ganzhis)
      transit_dz = tuple(gz.dizhi for gz in transits.ganzhis)

      tg_discovery = tiangan_utils.TianganRelationDiscovery({})
      dz_discovery = dizhi_utils.DizhiRelationDiscovery({})
      # The oracle mirrors the analyzer by reading the chart's school profile (issue #69).
      school: BaziSchool = chart.bazi.config.school
      if random_level in [TransitAnalysis.Level.TRANSITS_ONLY, TransitAnalysis.Level.ALL]:
        tg_discovery = tg_discovery.merge(tiangan_utils.discover(transit_tg))
        dz_discovery = dz_discovery.merge(dizhi_utils.discover(transit_dz, anhe_def=school.anhe_def, xing_def=school.xing_def))
      if random_level in [TransitAnalysis.Level.MUTUAL, TransitAnalysis.Level.ALL]:
        tg_discovery = tg_discovery.merge(tiangan_utils.discover_mutual(chart.bazi.four_tiangans, transit_tg))
        dz_discovery = dz_discovery.merge(dizhi_utils.discover_mutual(chart.bazi.four_dizhis, transit_dz, anhe_def=school.anhe_def, xing_def=school.xing_def))

      actual = transits_analysis.star_relations(transits, level=random_level)

      # Tiangan
      for tg_rel, tg_combos in actual.tiangan.items():
        assert tg_rel in tg_discovery
        for tg_combo in tg_combos:
          assert tg_combo in tg_discovery[tg_rel]

      for tg_rel, tg_combos in tg_discovery.items():
        for tg_combo in tg_combos:
          if stars.tiangan in tg_combo:
            assert tg_combo in actual.tiangan[tg_rel]

      assert _equal(actual.tiangan, tg_discovery.filter(
        lambda _, combo : stars.tiangan in combo
      ))

      # Dizhi
      for dz_rel, dz_combos in actual.dizhi.items():
        assert dz_rel in dz_discovery
        for dz_combo in dz_combos:
          assert dz_combo in dz_discovery[dz_rel]

      for dz_rel, dz_combos in dz_discovery.items():
        for dz_combo in dz_combos:
          if len(dz_combo & set(stars.dizhi)) > 0:
            assert dz_combo in actual.dizhi[dz_rel]

      assert _equal(actual.dizhi, dz_discovery.filter(
        lambda _, combo : len(combo & set(stars.dizhi)) > 0
      ))


@pytest.mark.slow
def test_zhengyin() -> None:
  for _ in range(32):
    chart = BaziChart.random()
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + random.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year)

      expected_tg: bool = False
      expected_dz: bool = False
      for gz in transits.ganzhis:
        if bazi_utils.shishen(chart.bazi.day_master, gz.tiangan) == Shishen.正印:
          expected_tg = True
        if bazi_utils.shishen(chart.bazi.day_master, gz.dizhi) == Shishen.正印:
          expected_dz = True

      actual = transits_analysis.zhengyin(transits)
      assert expected_tg == actual.tiangan
      assert expected_dz == actual.dizhi


@pytest.mark.slow
def test_star() -> None:
  for _ in range(16):
    chart = BaziChart.random()
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(64):
      random_year = chart.bazi.ganzhi_year + random.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year)

      expected_tg: bool = False
      expected_dz: bool = False
      for gz in transits.ganzhis:
        if gz.tiangan == chart.relationship_stars.tiangan:
          expected_tg = True
        if gz.dizhi in chart.relationship_stars.dizhi:
          expected_dz = True

      actual = transits_analysis.star(transits)
      assert expected_tg == actual.tiangan
      assert expected_dz == actual.dizhi


def test_transit_analysis_negative() -> None:
  chart = BaziChart.random()
  transits_analysis = RelationshipAnalyzer(chart).transits

  for analysis in (transits_analysis.shensha, transits_analysis.day_master_relations,
                    transits_analysis.house_relations, transits_analysis.star_relations,
                    transits_analysis.zhengyin, transits_analysis.star):
    with pytest.raises(TypeError):
      analysis(object()) # type: ignore

  transits = TransitChart(chart).at(TransitYear(chart.bazi.ganzhi_year)).select(TransitKind.LIUNIAN)
  with pytest.raises(TypeError):
    transits_analysis.star_relations(transits, level=0x8) # type: ignore
  # IntFlag happily constructs pseudo-members (undefined bit / empty flag); the gate rejects them by value.
  with pytest.raises(ValueError):
    transits_analysis.star_relations(transits, level=TransitAnalysis.Level(0x8))
  with pytest.raises(ValueError):
    transits_analysis.star_relations(transits, level=TransitAnalysis.Level(0))


def test_registry_matches_shensha_analysis_keys() -> None:
  '''The Shensha registry and `ShenshaAnalysis` must stay in sync / 神煞注册表和 ShenshaAnalysis 的键必须保持同步。'''
  assert set(_REGISTRY.keys()) == set(ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__)


def test_no_bare_dizhi_discovery_calls() -> None:
  # The "no bare calls" invariant declared by the `_dz_*` wrappers in relationship.py needs
  # an executor: every `dizhi_utils.search` / `discover` / `discover_mutual` call in that file
  # must sit inside one of the two wrappers -- a call anywhere else silently falls
  # back to the hardcoded defaults (issue #69).
  # 「无裸调」不变量得有执行者：relationship.py 里的三个入口调用必须都在两薄包装体内——
  # 别处的调用会静默回落到硬编码默认（issue #69）。
  wrappers = {'_dz_discover', '_dz_discover_mutual'}
  gated = {'search', 'discover', 'discover_mutual'}

  bare: list[int] = []

  class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
      self._scope: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
      self._scope.append(node.name)
      self.generic_visit(node)
      self._scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
      f = node.func
      if (isinstance(f, ast.Attribute) and f.attr in gated
          and isinstance(f.value, ast.Name) and f.value.id == 'dizhi_utils'
          and (not self._scope or self._scope[-1] not in wrappers)):
        bare.append(node.lineno)
      self.generic_visit(node)

  _Visitor().visit(ast.parse(inspect.getsource(relationship_module)))
  assert bare == []
