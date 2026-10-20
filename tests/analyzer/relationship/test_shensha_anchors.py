# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shensha_anchors.py

import pytest

from collections.abc import Callable

from bazi.defines import Tiangan, Dizhi, Ganzhi
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig, BaziSchool, Anchor
from bazi.transits import TransitSet
from bazi.analyzer.relationship import RelationshipAnalyzer, ShenshaAnalysis


def _five_anchor_school(anchor: Anchor) -> BaziSchool:
  '''The five Dizhi-anchored Shenshas (驿马、华盖、将星、劫煞、亡神) all on one anchor.
  Each carries its own knob; these tests move the five together on purpose, because their
  readings come from one source (see `_ANCHOR_CHOICES`).'''
  return BaziSchool(
    yima_anchor=anchor,
    huagai_anchor=anchor,
    jiangxing_anchor=anchor,
    jiesha_anchor=anchor,
    wangshen_anchor=anchor,
  )


@pytest.mark.parametrize('anchor, expected', [
  (Anchor.YEAR, frozenset({Dizhi.午})),
  (Anchor.YEAR_AND_DAY, frozenset({Dizhi.午, Dizhi.子})),
])
def test_zaisha_anchor_at_birth_and_transits(
  anchor: Anchor,
  expected: frozenset[Dizhi],
) -> None:
  # 子年灾煞在午，午日灾煞在子；原局与所选流运都包含两个目标。
  chart = BaziChart(Bazi.create(
    '2020-07-02 19:08',
    'female',
    BaziConfig(school=BaziSchool(zaisha_anchor=anchor)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('庚子', '壬午', '丙午', '戊戌')
  assert RelationshipAnalyzer(chart).at_birth.shensha['zaisha'] == expected

  transits = TransitSet(
    dayun=Ganzhi.from_str('甲午'),
    liunian=Ganzhi.from_str('甲子'),
  )
  assert RelationshipAnalyzer(chart).transits.shensha(transits)['zaisha'] == expected

  if anchor is Anchor.YEAR:
    default_chart = BaziChart(Bazi.create('2020-07-02 19:08', 'female'))
    assert RelationshipAnalyzer(default_chart).at_birth.shensha['zaisha'] == expected


def test_zaisha_dedup_and_empty_result() -> None:
  # 年、日支同为丑，双锚的灾煞都在卯；重复流运支也只返回一个值。
  chart = BaziChart(Bazi.create(
    '1902-01-06 12:00',
    'male',
    BaziConfig(school=BaziSchool(zaisha_anchor=Anchor.YEAR_AND_DAY)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('辛丑', '辛丑', '己丑', '庚午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['zaisha'] == set()
  assert RelationshipAnalyzer(chart).transits.shensha(TransitSet(
    dayun=Ganzhi.from_str('甲卯'),
    liunian=Ganzhi.from_str('乙卯'),
  ))['zaisha'] == {Dizhi.卯}
  assert RelationshipAnalyzer(chart).transits.shensha(
    TransitSet(liuyue=Ganzhi.from_str('甲子'))
  )['zaisha'] == set()


def test_zaisha_anchor_is_independent_of_axes() -> None:
  chart = BaziChart(Bazi.create(
    '2020-07-02 19:08',
    'female',
    BaziConfig(school=BaziSchool(
      hongyan_anchor=Anchor.YEAR,
      yima_anchor=Anchor.DAY,
      huagai_anchor=Anchor.DAY,
      jiangxing_anchor=Anchor.DAY,
      jiesha_anchor=Anchor.DAY,
      wangshen_anchor=Anchor.DAY,
    )),
  ))
  assert RelationshipAnalyzer(chart).at_birth.shensha['zaisha'] == {Dizhi.午}


@pytest.mark.parametrize('birth_time, pillars, expected', [
  # The year anchor contributes 亥; the day anchor contributes nothing.
  ('1918-11-18 11:58', ('戊午', '癸亥', '己巳', '庚午'), frozenset((Dizhi.亥,))),
  # The day anchor contributes 寅; the year anchor contributes nothing.
  ('2070-06-05 18:46', ('庚寅', '壬午', '辛丑', '丁酉'), frozenset((Dizhi.寅,))),
  # The two anchors contribute distinct branches.
  ('2023-01-17 15:42', ('壬寅', '癸丑', '乙亥', '甲申'), frozenset((Dizhi.亥, Dizhi.申))),
  # Neither anchor contributes a branch.
  ('1948-10-03 14:22', ('戊子', '辛酉', '辛酉', '乙未'), frozenset()),
])
def test_jiesha_at_birth(
  birth_time: str,
  pillars: tuple[str, str, str, str],
  expected: frozenset[Dizhi],
) -> None:
  chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == pillars
  assert RelationshipAnalyzer(chart).at_birth.shensha['jiesha'] == expected


def test_jiesha_at_transits() -> None:
  chart = BaziChart(Bazi.create('2023-01-17 15:42', BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬寅', '癸丑', '乙亥', '甲申')
  analysis = RelationshipAnalyzer(chart).transits

  year_anchor = TransitSet(dayun=Ganzhi.from_str('乙亥'))
  day_anchor = TransitSet(liunian=Ganzhi.from_str('丙申'))
  assert analysis.shensha(year_anchor)['jiesha'] == {Dizhi.亥}
  assert analysis.shensha(day_anchor)['jiesha'] == {Dizhi.申}
  assert analysis.shensha(TransitSet(
    dayun=Ganzhi.from_str('乙亥'),
    liunian=Ganzhi.from_str('丙申'),
  ))['jiesha'] == {Dizhi.亥, Dizhi.申}
  assert analysis.shensha(TransitSet(liuyue=Ganzhi.from_str('甲子')))['jiesha'] == set()


@pytest.mark.parametrize('birth_time, pillars, expected', [
  # The year anchor contributes 巳; the day anchor contributes nothing.
  ('1918-11-18 11:58', ('戊午', '癸亥', '己巳', '庚午'), frozenset((Dizhi.巳,))),
  # The day anchor contributes 寅; the year anchor contributes nothing.
  ('2023-01-17 15:42', ('壬寅', '癸丑', '乙亥', '甲申'), frozenset((Dizhi.寅,))),
  # The two anchors contribute distinct branches.
  ('1902-05-08 12:00', ('壬寅', '乙巳', '辛卯', '甲午'), frozenset((Dizhi.巳, Dizhi.寅))),
  # Neither anchor contributes a branch.
  ('1948-10-03 14:22', ('戊子', '辛酉', '辛酉', '乙未'), frozenset()),
])
def test_wangshen_at_birth(
  birth_time: str,
  pillars: tuple[str, str, str, str],
  expected: frozenset[Dizhi],
) -> None:
  chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == pillars
  assert RelationshipAnalyzer(chart).at_birth.shensha['wangshen'] == expected


def test_wangshen_at_transits() -> None:
  chart = BaziChart(Bazi.create('2023-01-17 15:42', BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬寅', '癸丑', '乙亥', '甲申')
  analysis = RelationshipAnalyzer(chart).transits

  year_anchor = TransitSet(dayun=Ganzhi.from_str('乙巳'))
  day_anchor = TransitSet(liunian=Ganzhi.from_str('丙寅'))
  assert analysis.shensha(year_anchor)['wangshen'] == {Dizhi.巳}
  assert analysis.shensha(day_anchor)['wangshen'] == {Dizhi.寅}
  assert analysis.shensha(TransitSet(
    dayun=Ganzhi.from_str('乙巳'),
    liunian=Ganzhi.from_str('丙寅'),
  ))['wangshen'] == {Dizhi.巳, Dizhi.寅}
  assert analysis.shensha(TransitSet(liuyue=Ganzhi.from_str('甲子')))['wangshen'] == set()


@pytest.mark.parametrize('birth_time, pillars, expected_guchen, expected_guasu', [
  ('2034-04-18 05:14', ('甲寅', '戊辰', '甲辰', '丁卯'), frozenset(), frozenset()),
  ('1910-12-24 15:31', ('庚戌', '戊子', '癸亥', '庚申'), frozenset((Dizhi.亥,)), frozenset()),
  ('1913-10-27 15:35', ('癸丑', '壬戌', '辛巳', '丙申'), frozenset(), frozenset((Dizhi.戌,))),
  # Raw detection reports Guchen and Guasu separately when both occur (「连属」).
  ('2032-02-10 07:45', ('壬子', '壬寅', '丙戌', '壬辰'),
   frozenset((Dizhi.寅,)), frozenset((Dizhi.戌,))),
  # The repeated 巳 target collapses to one Guchen result.
  ('2023-06-04 05:39', ('癸卯', '丁巳', '癸巳', '乙卯'), frozenset((Dizhi.巳,)), frozenset()),
])
def test_guchen_guasu_at_birth(
  birth_time: str,
  pillars: tuple[str, str, str, str],
  expected_guchen: frozenset[Dizhi],
  expected_guasu: frozenset[Dizhi],
) -> None:
  chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == pillars
  shensha = RelationshipAnalyzer(chart).at_birth.shensha
  assert shensha['guchen'] == expected_guchen
  assert shensha['guasu'] == expected_guasu


def test_guchen_guasu_at_transits() -> None:
  chart = BaziChart(Bazi.create('2032-02-10 07:45', BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬子', '壬寅', '丙戌', '壬辰')
  analysis = RelationshipAnalyzer(chart).transits

  guchen_dayun = analysis.shensha(TransitSet(dayun=Ganzhi.from_str('甲寅')))
  assert guchen_dayun['guchen'] == {Dizhi.寅}
  assert guchen_dayun['guasu'] == set()

  guasu_liunian = analysis.shensha(TransitSet(liunian=Ganzhi.from_str('丙戌')))
  assert guasu_liunian['guchen'] == set()
  assert guasu_liunian['guasu'] == {Dizhi.戌}

  combined = analysis.shensha(TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('丙戌'),
  ))
  assert combined['guchen'] == {Dizhi.寅}
  assert combined['guasu'] == {Dizhi.戌}

  duplicate_guchen = analysis.shensha(TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('丙寅'),
  ))
  assert duplicate_guchen['guchen'] == {Dizhi.寅}
  assert duplicate_guchen['guasu'] == set()

  no_hits = analysis.shensha(TransitSet(liuyue=Ganzhi.from_str('甲子')))
  assert no_hits['guchen'] == set()
  assert no_hits['guasu'] == set()


'''Getter type for one field of a Shensha analysis result.'''
ShenshaGetter = Callable[[ShenshaAnalysis], frozenset[Dizhi]]


# Each case isolates a year-anchor contribution; 亡神 also retains one day-anchor hit.
@pytest.mark.parametrize('getter, birth_time, pillars, default_expected, day_expected', [
  (lambda result: result['yima'], '1972-07-26 03:14', ('壬子', '丁未', '戊午', '甲寅'),
   frozenset((Dizhi.寅,)), frozenset()),
  (lambda result: result['huagai'], '2036-05-18 07:29', ('丙辰', '癸巳', '乙酉', '庚辰'),
   frozenset((Dizhi.辰,)), frozenset()),
  (lambda result: result['jiangxing'], '2025-09-19 14:00', ('乙巳', '乙酉', '辛卯', '乙未'),
   frozenset((Dizhi.酉,)), frozenset()),
  (lambda result: result['jiesha'], '2036-05-18 07:29', ('丙辰', '癸巳', '乙酉', '庚辰'),
   frozenset((Dizhi.巳,)), frozenset()),
  (lambda result: result['wangshen'], '2061-08-20 12:04', ('辛巳', '丙申', '庚午', '壬午'),
   frozenset((Dizhi.巳, Dizhi.申)), frozenset((Dizhi.巳,))),
])
def test_five_dizhi_anchors_at_birth(
  getter: ShenshaGetter,
  birth_time: str,
  pillars: tuple[str, str, str, str],
  default_expected: frozenset[Dizhi],
  day_expected: frozenset[Dizhi],
) -> None:
  default_chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  day_chart = BaziChart(Bazi.create(
    birth_time,
    BaziGender.MALE,
    BaziConfig(school=_five_anchor_school(Anchor.DAY)),
  ))
  assert tuple(map(str, default_chart.bazi.pillars)) == pillars

  default_shensha = RelationshipAnalyzer(default_chart).at_birth.shensha
  day_shensha = RelationshipAnalyzer(day_chart).at_birth.shensha
  assert getter(default_shensha) == default_expected
  assert getter(day_shensha) == day_expected
  assert default_shensha['taohua'] == day_shensha['taohua']


def test_five_dizhi_anchors_move_independently() -> None:
  school = BaziSchool(yima_anchor=Anchor.DAY, huagai_anchor=Anchor.YEAR_AND_DAY)
  chart = BaziChart(Bazi.create(
    '1955-07-19 09:00',
    BaziGender.MALE,
    BaziConfig(school=school),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('乙未', '癸未', '辛巳', '癸巳')

  shensha = RelationshipAnalyzer(chart).at_birth.shensha
  assert shensha['yima'] == frozenset()
  assert shensha['huagai'] == frozenset({Dizhi.未})


# Each pair supplies one year-anchor-only hit and one day-anchor hit.
@pytest.mark.parametrize('getter, year_ganzhi, day_ganzhi', [
  (lambda result: result['yima'], Ganzhi.from_str('甲申'), Ganzhi.from_str('乙巳')),
  (lambda result: result['huagai'], Ganzhi.from_str('甲戌'), Ganzhi.from_str('乙未')),
  (lambda result: result['jiangxing'], Ganzhi.from_str('甲午'), Ganzhi.from_str('乙卯')),
  (lambda result: result['jiesha'], Ganzhi.from_str('乙亥'), Ganzhi.from_str('甲申')),
  (lambda result: result['wangshen'], Ganzhi.from_str('乙巳'), Ganzhi.from_str('甲寅')),
])
def test_five_dizhi_anchors_at_transits(
  getter: ShenshaGetter,
  year_ganzhi: Ganzhi,
  day_ganzhi: Ganzhi,
) -> None:
  default_chart = BaziChart(Bazi.create('2023-01-17 15:42', BaziGender.MALE))
  day_chart = BaziChart(Bazi.create(
    '2023-01-17 15:42',
    BaziGender.MALE,
    BaziConfig(school=_five_anchor_school(Anchor.DAY)),
  ))
  assert tuple(map(str, default_chart.bazi.pillars)) == ('壬寅', '癸丑', '乙亥', '甲申')
  transits = TransitSet(dayun=year_ganzhi, liunian=day_ganzhi)

  default_shensha = RelationshipAnalyzer(default_chart).transits.shensha(transits)
  day_shensha = RelationshipAnalyzer(day_chart).transits.shensha(transits)
  assert getter(default_shensha) == {year_ganzhi.dizhi, day_ganzhi.dizhi}
  assert getter(day_shensha) == {day_ganzhi.dizhi}
  assert default_shensha['taohua'] == day_shensha['taohua']


@pytest.mark.parametrize('birth_time, pillars, yangren_index', [
  ('1950-01-11 00:00', ('己丑', '丁丑', '丙午', '戊子'), 2),
  ('1950-01-01 12:00', ('己丑', '丙子', '丙申', '甲午'), 3),
])
def test_yangren_checks_day_and_hour_branches(
  birth_time: str,
  pillars: tuple[str, str, str, str],
  yangren_index: int,
) -> None:
  chart: BaziChart = BaziChart(Bazi.create(birth_time, 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == pillars
  assert chart.bazi.four_dizhis[yangren_index] is Dizhi.午
  assert all(dz is not Dizhi.午 for i, dz in enumerate(chart.bazi.four_dizhis)
             if i != yangren_index)
  assert RelationshipAnalyzer(chart).at_birth.shensha['yangren'] == {Dizhi.午}


@pytest.mark.parametrize('birth_time, expected', [
  ('1902-02-10 12:00', frozenset({Dizhi.寅})), # 甲日，年、月两支均为寅，结果按支值去重。
  ('2020-07-02 19:08', frozenset()),          # 丙日禄在巳，原局四支不见巳。
])
def test_lushen_at_birth(birth_time: str, expected: frozenset[Dizhi]) -> None:
  chart = BaziChart(Bazi.create(birth_time, 'male'))
  assert RelationshipAnalyzer(chart).at_birth.shensha['lushen'] == expected


def test_lushen_at_transits() -> None:
  chart = BaziChart(Bazi.create('1902-02-10 12:00', 'male'))
  analysis = RelationshipAnalyzer(chart).transits
  assert chart.bazi.day_master is Tiangan.甲

  assert analysis.shensha(TransitSet(dayun=Ganzhi.from_str('甲寅')))['lushen'] == {Dizhi.寅}
  assert analysis.shensha(TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('丙寅'),
  ))['lushen'] == {Dizhi.寅}
  assert analysis.shensha(TransitSet(liuyue=Ganzhi.from_str('甲子')))['lushen'] == set()
