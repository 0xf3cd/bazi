# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shensha_definitions.py

import pytest

from bazi.defines import Tiangan, Dizhi, Ganzhi
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.rules import ShenshaRules
from bazi.school import BaziConfig, BaziSchool, Anchor, _ANCHOR_CHOICES
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind, TransitSet
from bazi.analyzer.relationship import RelationshipAnalyzer, TransitAnalysis

from relationship_samples import at_year


# 红艳查法 variants (issue #69): `Anchor` mounted on `BaziSchool.hongyan_anchor`; the analyzer
# re-reads the anchor stem from the chart's school profile at evaluation time. The chart below
# is the golden chart of `test_relationship_analysis.test_case1` (1984-04-01 11:08, male:
# 甲子/丁卯/乙丑/壬午) -- the day master 乙 keys on 申 (absent from the chart), while the year
# tiangan 甲 keys on 午 (the hour Dizhi), so the two 查法 answer differently on this chart.
@pytest.mark.parametrize('anchor, expected', [
  (Anchor.DAY,  frozenset()),           # 日干乙 -> 申 (the default): 申 not in 子卯丑午.
  (Anchor.YEAR, frozenset({Dizhi.午})), # 年干甲 -> 午: the hour Dizhi matches.
])
def test_hongyan_anchor_variant_at_birth(anchor: Anchor, expected: frozenset[Dizhi]) -> None:
  config: BaziConfig = BaziConfig(school=BaziSchool(hongyan_anchor=anchor))
  chart: BaziChart = BaziChart(Bazi.create('1984-04-01 11:08', 'male', config))
  assert RelationshipAnalyzer(chart).at_birth.shensha['hongyan'] == expected

  # The default school uses Anchor.DAY -- the long-pinned behavior carries over unchanged.
  if anchor is Anchor.DAY:
    default_chart: BaziChart = BaziChart(Bazi.create('1984-04-01 11:08', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['hongyan'] == expected


@pytest.mark.parametrize('anchor, expected', [
  (Anchor.DAY,  frozenset()),           # 日干乙 -> 申: not among the 1990 transit Dizhis 辰/午.
  (Anchor.YEAR, frozenset({Dizhi.午})), # 年干甲 -> 午: the 1990 流年 is 庚午.
])
def test_hongyan_anchor_variant_at_transits(anchor: Anchor, expected: frozenset[Dizhi]) -> None:
  '''Same chart; the selected 1990 Dayun and Liunian are 戊辰/庚午 (pinned in `test_case1`).'''
  config: BaziConfig = BaziConfig(school=BaziSchool(hongyan_anchor=anchor))
  chart: BaziChart = BaziChart(Bazi.create('1984-04-01 11:08', 'male', config))
  transits: TransitAnalysis = RelationshipAnalyzer(chart).transits
  selected = at_year(TransitChart(chart), 1990).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  )
  assert transits.shensha(selected)['hongyan'] == expected


@pytest.mark.parametrize('yangren_def, transit_ganzhi, expected', [
  (ShenshaRules.YangrenDef.ZIPING, Ganzhi.from_str('壬戌'), frozenset()),
  (ShenshaRules.YangrenDef.LUMING, Ganzhi.from_str('壬戌'), frozenset({Dizhi.戌})),
  (ShenshaRules.YangrenDef.DIWANG, Ganzhi.from_str('庚申'), frozenset({Dizhi.申})),
])
def test_yangren_definition_at_birth_and_transits(
  yangren_def: ShenshaRules.YangrenDef,
  transit_ganzhi: Ganzhi,
  expected: frozenset[Dizhi],
) -> None:
  # This chart is 辛日 and 庚年. Anchor.YEAR deliberately differs, proving 羊刃 keeps
  # its fixed day-master anchor instead of inheriting 红艳's configurable anchor.
  school: BaziSchool = BaziSchool(
    hongyan_anchor=Anchor.YEAR,
    yangren_def=yangren_def,
  )
  chart: BaziChart = BaziChart(Bazi.create(
    '1980-10-15 12:00',
    'male',
    BaziConfig(school=school),
  ))
  assert chart.bazi.day_master is Tiangan.辛
  assert RelationshipAnalyzer(chart).at_birth.shensha['yangren'] == expected
  transits: TransitSet = TransitSet(liunian=transit_ganzhi)
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['yangren'] == expected

  if yangren_def is ShenshaRules.YangrenDef.ZIPING:
    default_chart: BaziChart = BaziChart(Bazi.create('1980-10-15 12:00', 'male'))
    assert RelationshipAnalyzer(default_chart).transits.shensha(transits)['yangren'] == expected


def test_yangren_checks_every_transit_branch() -> None:
  school: BaziSchool = BaziSchool(yangren_def=ShenshaRules.YangrenDef.DIWANG)
  chart: BaziChart = BaziChart(Bazi.create(
    '1980-10-15 12:00',
    'male',
    BaziConfig(school=school),
  ))
  transits: TransitSet = TransitSet(
    dayun=Ganzhi.from_str('庚申'),
    liunian=Ganzhi.from_str('壬戌'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['yangren'] == {Dizhi.申}


@pytest.mark.parametrize('feiren_def, expected', [
  (ShenshaRules.YangrenDef.ZIPING, frozenset()),
  (ShenshaRules.YangrenDef.LUMING, frozenset({Dizhi.戌})),
  (ShenshaRules.YangrenDef.DIWANG, frozenset({Dizhi.申})),
])
def test_feiren_definition_at_birth_and_transits(
  feiren_def: ShenshaRules.YangrenDef,
  expected: frozenset[Dizhi],
) -> None:
  chart: BaziChart = BaziChart(Bazi.create(
    '1908-10-17 12:00',
    'male',
    BaziConfig(school=BaziSchool(feiren_def=feiren_def)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('戊申', '壬戌', '乙巳', '壬午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['feiren'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('甲戌'),
    liunian=Ganzhi.from_str('庚申'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['feiren'] == expected

  if feiren_def is ShenshaRules.YangrenDef.ZIPING:
    default_chart = BaziChart(Bazi.create('1908-10-17 12:00', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['feiren'] == expected


def test_yangren_feiren_definitions_independent() -> None:
  chart = BaziChart(Bazi.create(
    '1908-10-17 12:00',
    'male',
    BaziConfig(school=BaziSchool(
      yangren_def=ShenshaRules.YangrenDef.DIWANG,
      feiren_def=ShenshaRules.YangrenDef.LUMING,
    )),
  ))
  transits = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('甲戌'),
  )
  shensha = RelationshipAnalyzer(chart).transits.shensha(transits)
  assert shensha['yangren'] == {Dizhi.寅}
  assert shensha['feiren'] == {Dizhi.戌}


@pytest.fixture
def repeated_feiren_analysis() -> RelationshipAnalyzer:
  chart = BaziChart(Bazi.create('1902-09-08 18:00', 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬寅', '己酉', '甲午', '癸酉')
  analysis = RelationshipAnalyzer(chart)
  return analysis


def test_feiren_deduplicates_transit_branches(repeated_feiren_analysis: RelationshipAnalyzer) -> None:
  analysis = repeated_feiren_analysis
  assert analysis.at_birth.shensha['feiren'] == {Dizhi.酉}
  assert analysis.transits.shensha(TransitSet(
    dayun=Ganzhi.from_str('癸酉'),
    liunian=Ganzhi.from_str('乙酉'),
  ))['feiren'] == {Dizhi.酉}


def test_feiren_returns_empty_without_hits(repeated_feiren_analysis: RelationshipAnalyzer) -> None:
  analysis = repeated_feiren_analysis
  assert analysis.transits.shensha(
    TransitSet(liunian=Ganzhi.from_str('甲子'))
  )['feiren'] == set()


@pytest.mark.parametrize('anchor, expected', [
  (Anchor.DAY, frozenset({Dizhi.子})),
  (Anchor.YEAR, frozenset({Dizhi.丑})),
  (Anchor.YEAR_AND_DAY, frozenset({Dizhi.子, Dizhi.丑})),
])
def test_tianyi_anchor_at_birth_and_transits(
  anchor: Anchor,
  expected: frozenset[Dizhi],
) -> None:
  # 甲年、乙日, with 子 and 丑 both present: each anchor has one distinct Tianyi branch.
  chart: BaziChart = BaziChart(Bazi.create(
    '1984-04-01 11:08',
    'male',
    BaziConfig(school=BaziSchool(tianyi_anchor=anchor)),
  ))
  assert chart.bazi.year_pillar.tiangan is Tiangan.甲
  assert chart.bazi.day_master is Tiangan.乙
  assert RelationshipAnalyzer(chart).at_birth.shensha['tianyi'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('甲子'),
    liunian=Ganzhi.from_str('乙丑'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['tianyi'] == expected

  if anchor is Anchor.YEAR_AND_DAY:
    default_chart: BaziChart = BaziChart(Bazi.create('1984-04-01 11:08', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['tianyi'] == expected


@pytest.mark.parametrize('tianyi_def, at_birth_expected, transits_expected', [
  (ShenshaRules.TianyiDef.GENG_WITH_JIA_WU, frozenset({Dizhi.丑, Dizhi.子}), frozenset({Dizhi.丑, Dizhi.未})),
  (ShenshaRules.TianyiDef.GENG_WITH_XIN, frozenset({Dizhi.午, Dizhi.寅, Dizhi.子}), frozenset({Dizhi.午, Dizhi.寅})),
  (ShenshaRules.TianyiDef.YANGGUI, frozenset({Dizhi.丑}), frozenset({Dizhi.丑})),
  (ShenshaRules.TianyiDef.YINGUI, frozenset({Dizhi.子}), frozenset({Dizhi.未})),
])
def test_tianyi_definition_at_birth_and_transits(
  tianyi_def: ShenshaRules.TianyiDef,
  at_birth_expected: frozenset[Dizhi],
  transits_expected: frozenset[Dizhi],
) -> None:
  chart: BaziChart = BaziChart(Bazi.create(
    '1985-03-02 11:08',
    'male',
    BaziConfig(school=BaziSchool(
      tianyi_anchor=Anchor.YEAR_AND_DAY,
      tianyi_def=tianyi_def,
    )),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('乙丑', '戊寅', '庚子', '壬午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['tianyi'] == at_birth_expected
  transits = TransitSet(
    xiaoyun=Ganzhi.from_str('乙丑'),
    dayun=Ganzhi.from_str('癸未'),
    liunian=Ganzhi.from_str('庚午'),
    liuyue=Ganzhi.from_str('丙寅'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['tianyi'] == transits_expected


@pytest.mark.parametrize('anchor, expected', [
  (Anchor.DAY, frozenset({Dizhi.寅})),
  (Anchor.YEAR_AND_DAY, frozenset({Dizhi.丑, Dizhi.寅})),
])
def test_jinyu_anchor_at_birth_and_transits(
  anchor: Anchor,
  expected: frozenset[Dizhi],
) -> None:
  # 壬年、癸日，金舆分别在丑、寅；两支都在原局与所选流运中。
  chart = BaziChart(Bazi.create(
    '1902-03-31 12:00',
    'male',
    BaziConfig(school=BaziSchool(jinyu_anchor=anchor)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬寅', '癸卯', '癸丑', '戊午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['jinyu'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('乙丑'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['jinyu'] == expected

  if anchor is Anchor.DAY:
    default_chart = BaziChart(Bazi.create('1902-03-31 12:00', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['jinyu'] == expected


def test_jinyu_year_anchor_can_be_the_only_hit() -> None:
  # 庚年金舆在戌，丙日金舆在未；原局只见戌。
  default_chart = BaziChart(Bazi.create('2020-07-02 19:08', 'female'))
  year_and_day_chart = BaziChart(Bazi.create(
    '2020-07-02 19:08',
    'female',
    BaziConfig(school=BaziSchool(jinyu_anchor=Anchor.YEAR_AND_DAY)),
  ))
  assert tuple(map(str, default_chart.bazi.pillars)) == ('庚子', '壬午', '丙午', '戊戌')

  default_analysis = RelationshipAnalyzer(default_chart)
  year_and_day_analysis = RelationshipAnalyzer(year_and_day_chart)
  assert default_analysis.at_birth.shensha['jinyu'] == set()
  assert year_and_day_analysis.at_birth.shensha['jinyu'] == {Dizhi.戌}

  transit = TransitSet(liunian=Ganzhi.from_str('甲戌'))
  assert default_analysis.transits.shensha(transit)['jinyu'] == set()
  assert year_and_day_analysis.transits.shensha(transit)['jinyu'] == {Dizhi.戌}


@pytest.fixture
def repeated_jinyu_chart() -> BaziChart:
  # 丙年、戊日的金舆均在未；两锚命中同一支时只返回一个位置值。
  chart = BaziChart(Bazi.create(
    '1906-07-13 12:00',
    'male',
    BaziConfig(school=BaziSchool(jinyu_anchor=Anchor.YEAR_AND_DAY)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('丙午', '乙未', '戊午', '戊午')
  return chart


def test_jinyu_deduplicates_anchor_hits(repeated_jinyu_chart: BaziChart) -> None:
  chart = repeated_jinyu_chart
  assert RelationshipAnalyzer(chart).at_birth.shensha['jinyu'] == {Dizhi.未}
  assert RelationshipAnalyzer(chart).transits.shensha(
    TransitSet(liunian=Ganzhi.from_str('乙未'))
  )['jinyu'] == {Dizhi.未}


def test_jinyu_returns_empty_without_hits(repeated_jinyu_chart: BaziChart) -> None:
  chart = repeated_jinyu_chart
  assert RelationshipAnalyzer(chart).transits.shensha(
    TransitSet(liunian=Ganzhi.from_str('甲子'))
  )['jinyu'] == set()


@pytest.mark.parametrize('anchor, expected', [
  (Anchor.DAY, frozenset({Dizhi.卯})),
  (Anchor.YEAR_AND_DAY, frozenset({Dizhi.寅, Dizhi.卯})),
])
def test_wenchang_anchor_at_birth_and_transits(
  anchor: Anchor,
  expected: frozenset[Dizhi],
) -> None:
  # 壬年、癸日，文昌分别在寅、卯；两支都在原局与所选流运中。
  chart = BaziChart(Bazi.create(
    '1902-03-31 12:00',
    'male',
    BaziConfig(school=BaziSchool(wenchang_anchor=anchor)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬寅', '癸卯', '癸丑', '戊午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['wenchang'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('乙卯'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['wenchang'] == expected

  if anchor is Anchor.YEAR_AND_DAY:
    default_chart = BaziChart(Bazi.create('1902-03-31 12:00', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['wenchang'] == expected


@pytest.mark.parametrize('wenchang_def, expected', [
  (ShenshaRules.WenchangDef.XIN_ZI, frozenset({Dizhi.子})),
  (ShenshaRules.WenchangDef.XIN_XU, frozenset({Dizhi.戌})),
])
def test_wenchang_definition_at_birth_transits(
  wenchang_def: ShenshaRules.WenchangDef,
  expected: frozenset[Dizhi],
) -> None:
  # 辛日：两读的分歧就在这一个干上。原局同时有子与戌，所以切定义会把结果从一支换成另一支，
  # 而不是从「有」变成「无」——后者与「旋钮没接上」不可区分。
  # 年干壬的文昌在寅，本盘与所选流运都没有寅，故年干那一半不参与。
  chart = BaziChart(Bazi.create(
    '1982-12-14 12:00',
    'male',
    BaziConfig(school=BaziSchool(wenchang_def=wenchang_def)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬戌', '壬子', '辛未', '甲午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['wenchang'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('甲子'),
    liunian=Ganzhi.from_str('丙戌'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['wenchang'] == expected


def test_wenchanggui_keys_on_the_year_stem_only() -> None:
  # 文昌贵固定以年干为锚，不读任何旋钮：切别的神煞的锚旋钮不影响它，而年干换了就换答案。
  # 壬年文昌贵在卯，癸日若也参与则会带出丑——本盘有丑，所以「日干没参与」是可证伪的。
  chart = BaziChart(Bazi.create('1902-03-31 12:00', 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬寅', '癸卯', '癸丑', '戊午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['wenchanggui'] == {Dizhi.卯}

  # 把每个锚旋钮都拨到另一端，文昌贵纹丝不动。
  for field, anchor in ((f, a) for f, allowed in _ANCHOR_CHOICES.items() for a in allowed):
    other = BaziChart(Bazi.create(
      '1902-03-31 12:00',
      'male',
      BaziConfig(school=BaziSchool(**{field: anchor})), # type: ignore # Field name is data here.
    ))
    assert RelationshipAnalyzer(other).at_birth.shensha['wenchanggui'] == {Dizhi.卯}, (field, anchor)


@pytest.mark.parametrize('anchor, expected', [
  (Anchor.YEAR, frozenset({Dizhi.未, Dizhi.戌})),
  (Anchor.YEAR_AND_DAY, frozenset({Dizhi.未, Dizhi.戌, Dizhi.子, Dizhi.午})),
])
def test_taiji_anchor_at_birth_and_transits(
  anchor: Anchor,
  expected: frozenset[Dizhi],
) -> None:
  # 己年、甲日：己的太极是四库（盘中见未、戌），甲的太极是子午（盘中见子、午）。
  # 两锚各带来一组不同的支，所以切锚是「多一组」而不是「有变无」。
  chart = BaziChart(Bazi.create(
    '1980-01-02 12:00',
    'male',
    BaziConfig(school=BaziSchool(taiji_anchor=anchor)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('己未', '丙子', '甲戌', '庚午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['taiji'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('己未'),
    liunian=Ganzhi.from_str('甲子'),
  )
  transit_expected = expected & {Dizhi.未, Dizhi.子}
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['taiji'] == transit_expected

  if anchor is Anchor.YEAR_AND_DAY:
    default_chart = BaziChart(Bazi.create('1980-01-02 12:00', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['taiji'] == expected


@pytest.mark.parametrize('taiji_def, expected', [
  (ShenshaRules.TaijiDef.REN_GUI_BOTH, frozenset({Dizhi.巳, Dizhi.申})),
  (ShenshaRules.TaijiDef.REN_SI_GUI_SHEN, frozenset({Dizhi.申})),
])
def test_taiji_definition_at_birth_and_transits(
  taiji_def: ShenshaRules.TaijiDef,
  expected: frozenset[Dizhi],
) -> None:
  # 癸日：两读的分歧就在壬癸。原局同时有巳与申，所以切定义是巳这一支进出，而不是整体清空
  # ——后者与「旋钮没接上」不可区分。两读本身是单向的（分读法只去支不添支），
  # 所以做不出「换一支」的对照，这里退而求其次钉「少一支」。
  # 年干庚的太极在寅亥，本盘与所选流运都没有，故年干那一半不参与。
  chart = BaziChart(Bazi.create(
    '1980-03-21 12:00',
    'male',
    BaziConfig(school=BaziSchool(taiji_def=taiji_def)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('庚申', '己卯', '癸巳', '戊午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['taiji'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('丁巳'),
    liunian=Ganzhi.from_str('甲申'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['taiji'] == expected


@pytest.mark.parametrize('anchor, expected', [
  (Anchor.YEAR, frozenset({Dizhi.寅})),
  (Anchor.YEAR_AND_DAY, frozenset({Dizhi.寅, Dizhi.丑})),
])
def test_guoyin_anchor_at_birth_and_transits(
  anchor: Anchor,
  expected: frozenset[Dizhi],
) -> None:
  # 己年、戊日：现代读法下己的国印在寅、戊的在丑，两支都在原局。切锚是「多一支」。
  chart = BaziChart(Bazi.create(
    '1980-01-06 12:00',
    'male',
    BaziConfig(school=BaziSchool(guoyin_anchor=anchor)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('己未', '丁丑', '戊寅', '戊午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['guoyin'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('丙寅'),
    liunian=Ganzhi.from_str('丁丑'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['guoyin'] == expected

  if anchor is Anchor.YEAR_AND_DAY:
    default_chart = BaziChart(Bazi.create('1980-01-06 12:00', 'male'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['guoyin'] == expected


@pytest.mark.parametrize('guoyin_def, expected', [
  (ShenshaRules.GuoyinDef.WUXING_JINGJI, frozenset({Dizhi.未})),
  (ShenshaRules.GuoyinDef.MODERN, frozenset({Dizhi.申})),
])
def test_guoyin_definition_at_birth_and_transits(
  guoyin_def: ShenshaRules.GuoyinDef,
  expected: frozenset[Dizhi],
) -> None:
  # 癸日：两读分别指向未与申，而原局同时有这两支。切定义时命中在两支之间移动，
  # 两侧都是非空且互不相同——旋钮接反、没接上或被忽略，三种情形都区分得出来。
  # 年干己的国印在丑（《五行精纪》）或寅（现代），本盘与所选流运都没有，故年干那一半不参与。
  chart = BaziChart(Bazi.create(
    '1979-09-03 12:00',
    'male',
    BaziConfig(school=BaziSchool(guoyin_def=guoyin_def)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('己未', '壬申', '癸酉', '戊午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['guoyin'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('辛未'),
    liunian=Ganzhi.from_str('庚申'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['guoyin'] == expected
