# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analyzer.py

import pytest

import ast
import dataclasses
import inspect
import random
import itertools
import sys
from datetime import datetime
from collections.abc import Callable, Sequence
from types import FrameType

from bazi.defines import Tiangan, Dizhi, Ganzhi, Shishen, DizhiRelation
from bazi.utils import shensha_utils, tiangan_utils, dizhi_utils, bazi_utils
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.rules import DizhiRules, ShenshaRules
from bazi.school import BaziConfig, BaziSchool, Anchor, _ANCHOR_CHOICES
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind, TransitSet
from bazi.analyzer import relationship as relationship_module
from bazi.analyzer.relationship import (
  RelationshipAnalyzer, TransitAnalysis, ShenshaAnalysis, AtBirthShenshaAnalysis, _REGISTRY,
)


_GONG_RELATIONS = (DizhiRelation.拱合, DizhiRelation.拱会)


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


def _project_gong(
  discovery: dizhi_utils.GanzhiRelationDiscovery,
  predicate: Callable[[dizhi_utils.GanzhiRelationCombo], bool],
) -> dizhi_utils.DizhiRelationDiscovery:
  return dizhi_utils.GanzhiRelationDiscovery({
    relation : tuple(combo for combo in discovery.get(relation, ()) if predicate(combo))
    for relation in _GONG_RELATIONS
  }).to_dizhi_discovery()


@pytest.mark.slow
def test_at_birth_shensha(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    analyzer = RelationshipAnalyzer(chart)

    dm: Tiangan = chart.bazi.day_master
    y, m, d, h = chart.bazi.four_dizhis
    school = chart.bazi.config.school
    # The five Dizhi-anchored Shenshas each carry their own knob -- read each one, never a shared flag.
    year_anchored = {
      'yima':      school.yima_anchor is Anchor.YEAR_AND_DAY,
      'huagai':    school.huagai_anchor is Anchor.YEAR_AND_DAY,
      'jiangxing': school.jiangxing_anchor is Anchor.YEAR_AND_DAY,
      'jiesha':    school.jiesha_anchor is Anchor.YEAR_AND_DAY,
      'wangshen':  school.wangshen_anchor is Anchor.YEAR_AND_DAY,
    }
    use_day_zaisha_anchor = school.zaisha_anchor is Anchor.YEAR_AND_DAY

    # The 红艳 anchor stem follows the chart's school (查法锚, issue #69) -- don't assume the day master.
    anchor: Tiangan = dm if school.hongyan_anchor is Anchor.DAY else chart.bazi.year_pillar.tiangan

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
    if year_anchored['yima']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.yima(dz1, dz2):
          expected_yima.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.yima(dz1, dz2):
        expected_yima.append(dz2)
    assert at_birth.shensha['yima'] == set(expected_yima)
    assert at_birth.shensha['yima'] == at_birth.shensha['yima'] # Repeated lookup must answer the same.

    # Huagai / 华盖
    expected_huagai: list[Dizhi] = []
    if year_anchored['huagai']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.huagai(dz1, dz2):
          expected_huagai.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.huagai(dz1, dz2):
        expected_huagai.append(dz2)
    assert at_birth.shensha['huagai'] == set(expected_huagai)
    assert at_birth.shensha['huagai'] == at_birth.shensha['huagai'] # Repeated lookup must answer the same.

    # Yangren / 羊刃
    expected_yangren: list[Dizhi] = []
    for dz in [y, m, d, h]:
      if shensha_utils.yangren(
        dm,
        dz,
        definition=chart.bazi.config.school.yangren_def,
      ):
        expected_yangren.append(dz)
    assert at_birth.shensha['yangren'] == set(expected_yangren)
    assert at_birth.shensha['yangren'] == at_birth.shensha['yangren'] # Repeated lookup must answer the same.

    # Feiren / 飞刃
    expected_feiren: list[Dizhi] = []
    for dz in [y, m, d, h]:
      if shensha_utils.feiren(
        dm,
        dz,
        definition=chart.bazi.config.school.feiren_def,
      ):
        expected_feiren.append(dz)
    assert at_birth.shensha['feiren'] == set(expected_feiren)
    assert at_birth.shensha['feiren'] == at_birth.shensha['feiren'] # Repeated lookup must answer the same.

    # Tianyi Guiren / 天乙贵人
    expected_tianyi: list[Dizhi] = []
    for tg, dz in itertools.product([chart.bazi.year_pillar.tiangan, dm], [y, m, d, h]):
      if shensha_utils.tianyi(
        tg,
        dz,
        definition=chart.bazi.config.school.tianyi_def,
      ):
        expected_tianyi.append(dz)
    assert at_birth.shensha['tianyi'] == set(expected_tianyi)
    assert at_birth.shensha['tianyi'] == at_birth.shensha['tianyi'] # Repeated lookup must answer the same.

    # Jiangxing / 将星
    expected_jiangxing: list[Dizhi] = []
    if year_anchored['jiangxing']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.jiangxing(dz1, dz2):
          expected_jiangxing.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.jiangxing(dz1, dz2):
        expected_jiangxing.append(dz2)
    assert at_birth.shensha['jiangxing'] == set(expected_jiangxing)
    assert at_birth.shensha['jiangxing'] == at_birth.shensha['jiangxing'] # Repeated lookup must answer the same.

    # Zaisha / 灾煞
    expected_zaisha = [dz for dz in (m, d, h) if shensha_utils.zaisha(y, dz)]
    if use_day_zaisha_anchor:
      expected_zaisha.extend(dz for dz in (y, m, h) if shensha_utils.zaisha(d, dz))
    assert at_birth.shensha['zaisha'] == set(expected_zaisha)
    assert at_birth.shensha['zaisha'] == at_birth.shensha['zaisha'] # Repeated lookup must answer the same.

    # Jiesha / 劫煞
    expected_jiesha: list[Dizhi] = []
    if year_anchored['jiesha']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.jiesha(dz1, dz2):
          expected_jiesha.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.jiesha(dz1, dz2):
        expected_jiesha.append(dz2)
    assert at_birth.shensha['jiesha'] == set(expected_jiesha)
    assert at_birth.shensha['jiesha'] == at_birth.shensha['jiesha'] # Repeated lookup must answer the same.

    # Wangshen / 亡神
    expected_wangshen: list[Dizhi] = []
    if year_anchored['wangshen']:
      for dz1, dz2 in itertools.product([y], [m, d, h]):
        if shensha_utils.wangshen(dz1, dz2):
          expected_wangshen.append(dz2)
    for dz1, dz2 in itertools.product([d], [y, m, h]):
      if shensha_utils.wangshen(dz1, dz2):
        expected_wangshen.append(dz2)
    assert at_birth.shensha['wangshen'] == set(expected_wangshen)
    assert at_birth.shensha['wangshen'] == at_birth.shensha['wangshen'] # Repeated lookup must answer the same.

    # Guchen / 孤辰
    expected_guchen = {dz for dz in (m, d, h) if shensha_utils.guchen(y, dz)}
    assert at_birth.shensha['guchen'] == expected_guchen
    assert at_birth.shensha['guchen'] == at_birth.shensha['guchen'] # Repeated lookup must answer the same.

    # Guasu / 寡宿
    expected_guasu = {dz for dz in (m, d, h) if shensha_utils.guasu(y, dz)}
    assert at_birth.shensha['guasu'] == expected_guasu
    assert at_birth.shensha['guasu'] == at_birth.shensha['guasu'] # Repeated lookup must answer the same.

    # Lushen / 禄神
    expected_lushen = {dz for dz in (y, m, d, h) if shensha_utils.lushen(dm, dz)}
    assert at_birth.shensha['lushen'] == expected_lushen
    assert at_birth.shensha['lushen'] == at_birth.shensha['lushen'] # Repeated lookup must answer the same.

    # Jinyu / 金舆
    expected_jinyu = {dz for dz in (y, m, d, h) if shensha_utils.jinyu(dm, dz)}
    assert at_birth.shensha['jinyu'] == expected_jinyu
    assert at_birth.shensha['jinyu'] == at_birth.shensha['jinyu'] # Repeated lookup must answer the same.

    # Kuigang / 魁罡
    expected_kuigang = chart.bazi.day_pillar if shensha_utils.kuigang(chart.bazi.day_pillar) else None
    assert at_birth.shensha['kuigang'] == expected_kuigang
    assert at_birth.shensha['kuigang'] == at_birth.shensha['kuigang'] # Repeated lookup must answer the same.

    # Tianshe / 天赦
    expected_tianshe = (
      chart.bazi.day_pillar
      if shensha_utils.tianshe(chart.bazi.month_commander, chart.bazi.day_pillar)
      else None
    )
    assert at_birth.shensha['tianshe'] == expected_tianshe
    assert at_birth.shensha['tianshe'] == at_birth.shensha['tianshe'] # Repeated lookup must answer the same.


@pytest.mark.parametrize('birth_time, day_pillar, expected_hit', [
  ('2000-01-23 12:00', '庚辰', True),
  ('2000-02-04 12:00', '壬辰', True),
  ('2000-02-10 12:00', '戊戌', True),
  ('2000-02-22 12:00', '庚戌', True),
  ('2000-02-16 12:00', '甲辰', False),
])
def test_kuigang_at_birth(
  birth_time: str,
  day_pillar: str,
  expected_hit: bool,
) -> None:
  chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  assert str(chart.bazi.day_pillar) == day_pillar
  assert RelationshipAnalyzer(chart).at_birth.shensha['kuigang'] == (
    chart.bazi.day_pillar if expected_hit else None
  )


@pytest.mark.parametrize('birth_time, pillars, expected_hit', [
  ('1999-03-27 12:00', ('己卯', '丁卯', '戊寅', '戊午'), True),
  ('1999-06-11 12:00', ('己卯', '庚午', '甲午', '庚午'), True),
  ('1999-08-24 12:00', ('己卯', '壬申', '戊申', '戊午'), True),
  ('1999-11-08 12:00', ('己卯', '乙亥', '甲子', '庚午'), True),
  # Each Tianshe day pillar misses outside its own season.
  ('1999-01-26 12:00', ('戊寅', '乙丑', '戊寅', '戊午'), False),
  ('1999-02-11 12:00', ('己卯', '丙寅', '甲午', '庚午'), False),
  ('1999-02-25 12:00', ('己卯', '丙寅', '戊申', '戊午'), False),
  ('1999-03-13 12:00', ('己卯', '丁卯', '甲子', '庚午'), False),
])
def test_tianshe_at_birth(
  birth_time: str,
  pillars: tuple[str, str, str, str],
  expected_hit: bool,
) -> None:
  chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == pillars
  assert RelationshipAnalyzer(chart).at_birth.shensha['tianshe'] == (
    chart.bazi.day_pillar if expected_hit else None
  )


@pytest.mark.parametrize('birth_time, pillars, expected', [
  # The year anchor contributes 午; the day anchor contributes nothing.
  ('1918-11-18 11:58', ('戊午', '癸亥', '己巳', '庚午'), frozenset((Dizhi.午,))),
  # The day anchor contributes 酉; the year anchor contributes nothing.
  ('1948-10-03 14:22', ('戊子', '辛酉', '辛酉', '乙未'), frozenset((Dizhi.酉,))),
  # The two anchors contribute distinct branches.
  ('2070-06-05 18:46', ('庚寅', '壬午', '辛丑', '丁酉'), frozenset((Dizhi.午, Dizhi.酉))),
  # The year branch is its own 将星, but the year anchor does not inspect itself.
  ('2077-05-20 10:47', ('丁酉', '乙巳', '壬戌', '乙巳'), frozenset()),
  # The day branch is its own 将星, but the day anchor does not inspect itself.
  ('1967-12-08 01:58', ('丁未', '壬子', '丙午', '己丑'), frozenset()),
])
def test_jiangxing_at_birth(
  birth_time: str,
  pillars: tuple[str, str, str, str],
  expected: frozenset[Dizhi],
) -> None:
  chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == pillars
  assert RelationshipAnalyzer(chart).at_birth.shensha['jiangxing'] == expected


def test_jiangxing_at_transits() -> None:
  chart = BaziChart(Bazi.create('2070-06-05 18:46', BaziGender.MALE))
  assert tuple(map(str, chart.bazi.pillars)) == ('庚寅', '壬午', '辛丑', '丁酉')
  analysis = RelationshipAnalyzer(chart).transits

  year_anchor = TransitSet(dayun=Ganzhi.from_str('甲午'))
  day_anchor = TransitSet(liunian=Ganzhi.from_str('乙酉'))
  assert analysis.shensha(year_anchor)['jiangxing'] == {Dizhi.午}
  assert analysis.shensha(day_anchor)['jiangxing'] == {Dizhi.酉}
  assert analysis.shensha(TransitSet(
    dayun=Ganzhi.from_str('甲午'),
    liunian=Ganzhi.from_str('乙酉'),
  ))['jiangxing'] == {Dizhi.午, Dizhi.酉}
  assert analysis.shensha(TransitSet(liuyue=Ganzhi.from_str('乙亥')))['jiangxing'] == set()


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


def test_zaisha_deduplicates_repeated_target_and_empty_result() -> None:
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


def test_zaisha_anchor_is_independent_from_other_shensha_axes() -> None:
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
def test_yangren_at_birth_checks_day_and_hour_branches(
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


@pytest.mark.slow
def test_at_birth_day_master_relations(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
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
def test_at_birth_house_relations(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    analyzer = RelationshipAnalyzer(chart)

    y, m, d, h = chart.bazi.four_dizhis
    at_birth = analyzer.at_birth

    # The oracle mirrors the analyzer by reading the chart's school profile (issue #69).
    school: BaziSchool = chart.bazi.config.school

    # For AtBirth analysis, the following two algorithms are equivalent.
    existing = dizhi_utils.discover(
      [y, m, d, h], definitions=school.relation_definitions,
    ).filter(
      lambda _, combo : d in combo
    )
    gong = _project_gong(
      dizhi_utils.discover_ganzhis(chart.bazi.pillars, definitions=school.relation_definitions),
      lambda combo : any(occurrence.index == 2 for occurrence in combo),
    )
    assert _equal(at_birth.house_relations, existing.merge(gong))

    existing_mutual = dizhi_utils.discover_mutual(
      [y, m, h], [d], definitions=school.relation_definitions,
    )
    actual_without_gong = dizhi_utils.DizhiRelationDiscovery({
      relation : combos
      for relation, combos in at_birth.house_relations.items()
      if relation not in _GONG_RELATIONS
    })
    assert actual_without_gong == existing_mutual

    assert at_birth.house_relations == at_birth.house_relations # Repeated lookup must answer the same.


@pytest.mark.slow
def test_at_birth_star_relations(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
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


def test_at_birth_gong_relations_use_concrete_participants() -> None:
  positive = BaziChart(Bazi.create(datetime(1980, 1, 12, 20), BaziGender.MALE))
  assert dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.戌)) in (
    RelationshipAnalyzer(positive).at_birth.house_relations[DizhiRelation.拱会]
  )

  # The day branch repeats the year branch, but only the year/month occurrences form 拱会.
  # A value-only house filter would incorrectly retain it for the day pillar.
  repeated_house = BaziChart(Bazi.create(datetime(1912, 1, 12, 2), BaziGender.MALE))
  assert repeated_house.bazi.year_pillar.dizhi is repeated_house.bazi.day_pillar.dizhi
  assert DizhiRelation.拱会 not in RelationshipAnalyzer(repeated_house).at_birth.house_relations

  wide_birth_time = datetime(1980, 1, 6, 12)
  default_wide = BaziChart(Bazi.create(wide_birth_time, BaziGender.MALE))
  assert DizhiRelation.拱合 not in RelationshipAnalyzer(default_wide).at_birth.house_relations
  wide = BaziChart(Bazi.create(
    wide_birth_time,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  assert dizhi_utils.DizhiCombo((Dizhi.寅, Dizhi.午)) in (
    RelationshipAnalyzer(wide).at_birth.house_relations[DizhiRelation.拱合]
  )


def test_at_birth_gong_relations_reach_stars_and_read_school() -> None:
  birth_time = datetime(1980, 1, 21, 2)
  default_chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  combo = dizhi_utils.DizhiCombo((Dizhi.巳, Dizhi.丑))
  assert combo in RelationshipAnalyzer(default_chart).at_birth.star_relations.dizhi[DizhiRelation.拱合]

  lu_chart = BaziChart(Bazi.create(
    birth_time,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.LU_NARROW)),
  ))
  assert DizhiRelation.拱合 not in RelationshipAnalyzer(lu_chart).at_birth.star_relations.dizhi


@pytest.mark.slow
def test_filtered(rng: random.Random) -> None:
  '''Test "star_relations" only contain filtered combos.'''
  for _ in range(16):
    chart: BaziChart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
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
      definitions=chart.bazi.config.school.relation_definitions, # The oracle mirrors the chart's school (issue #69).
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


def _at_year(transit_chart: TransitChart, gz_year: int) -> TransitSet:
  transits = transit_chart.at_year(gz_year)
  assert transits is not None
  return transits


def _random_year_transits(transit_chart: TransitChart, gz_year: int, rng: random.Random) -> TransitSet:
  full_transits = _at_year(transit_chart, gz_year)
  available = tuple(full_transits)
  selected = rng.sample(available, rng.randint(1, len(available)))
  return full_transits.select(*selected)


@pytest.mark.slow
def test_transit_shensha(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)

    y_dz = chart.bazi.year_pillar.dizhi
    d_dz = chart.bazi.day_pillar.dizhi
    school = chart.bazi.config.school
    # The five Dizhi-anchored Shenshas each carry their own knob -- read each one, never a shared flag.
    year_anchored = {
      'yima':      school.yima_anchor is Anchor.YEAR_AND_DAY,
      'huagai':    school.huagai_anchor is Anchor.YEAR_AND_DAY,
      'jiangxing': school.jiangxing_anchor is Anchor.YEAR_AND_DAY,
      'jiesha':    school.jiesha_anchor is Anchor.YEAR_AND_DAY,
      'wangshen':  school.wangshen_anchor is Anchor.YEAR_AND_DAY,
    }
    use_day_zaisha_anchor = school.zaisha_anchor is Anchor.YEAR_AND_DAY

    # The 红艳 anchor stem follows the chart's school (查法锚, issue #69) -- don't assume the day master.
    anchor: Tiangan = (chart.bazi.day_master if school.hongyan_anchor is Anchor.DAY
                       else chart.bazi.year_pillar.tiangan)

    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year, rng)

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
        if year_anchored['yima'] and shensha_utils.yima(y_dz, dz):
          expected.append(dz)
        if shensha_utils.yima(d_dz, dz):
          expected.append(dz)
      assert actual['yima'] == set(expected)

      # Huagai / 华盖
      expected = []
      for dz in transit_dz:
        if year_anchored['huagai'] and shensha_utils.huagai(y_dz, dz):
          expected.append(dz)
        if shensha_utils.huagai(d_dz, dz):
          expected.append(dz)
      assert actual['huagai'] == set(expected)

      # Yangren / 羊刃
      expected = []
      for dz in transit_dz:
        if shensha_utils.yangren(
          chart.bazi.day_master,
          dz,
          definition=chart.bazi.config.school.yangren_def,
        ):
          expected.append(dz)
      assert actual['yangren'] == set(expected)

      # Feiren / 飞刃
      expected = []
      for dz in transit_dz:
        if shensha_utils.feiren(
          chart.bazi.day_master,
          dz,
          definition=chart.bazi.config.school.feiren_def,
        ):
          expected.append(dz)
      assert actual['feiren'] == set(expected)

      # Tianyi Guiren / 天乙贵人
      expected = []
      for tg, dz in itertools.product(
        [chart.bazi.year_pillar.tiangan, chart.bazi.day_master],
        transit_dz,
      ):
        if shensha_utils.tianyi(
          tg,
          dz,
          definition=chart.bazi.config.school.tianyi_def,
        ):
          expected.append(dz)
      assert actual['tianyi'] == set(expected)

      # Jiangxing / 将星
      expected = []
      for dz in transit_dz:
        if year_anchored['jiangxing'] and shensha_utils.jiangxing(y_dz, dz):
          expected.append(dz)
        if shensha_utils.jiangxing(d_dz, dz):
          expected.append(dz)
      assert actual['jiangxing'] == set(expected)

      # Zaisha / 灾煞
      expected = []
      for dz in transit_dz:
        if shensha_utils.zaisha(y_dz, dz):
          expected.append(dz)
        if use_day_zaisha_anchor and shensha_utils.zaisha(d_dz, dz):
          expected.append(dz)
      assert actual['zaisha'] == set(expected)

      # Jiesha / 劫煞
      expected = []
      for dz in transit_dz:
        if year_anchored['jiesha'] and shensha_utils.jiesha(y_dz, dz):
          expected.append(dz)
        if shensha_utils.jiesha(d_dz, dz):
          expected.append(dz)
      assert actual['jiesha'] == set(expected)

      # Wangshen / 亡神
      expected = []
      for dz in transit_dz:
        if year_anchored['wangshen'] and shensha_utils.wangshen(y_dz, dz):
          expected.append(dz)
        if shensha_utils.wangshen(d_dz, dz):
          expected.append(dz)
      assert actual['wangshen'] == set(expected)

      # Guchen / 孤辰
      expected = [dz for dz in transit_dz if shensha_utils.guchen(y_dz, dz)]
      assert actual['guchen'] == set(expected)

      # Guasu / 寡宿
      expected = [dz for dz in transit_dz if shensha_utils.guasu(y_dz, dz)]
      assert actual['guasu'] == set(expected)

      # Lushen / 禄神
      expected = [dz for dz in transit_dz if shensha_utils.lushen(chart.bazi.day_master, dz)]
      assert actual['lushen'] == set(expected)

      # Jinyu / 金舆
      expected = [dz for dz in transit_dz if shensha_utils.jinyu(chart.bazi.day_master, dz)]
      assert actual['jinyu'] == set(expected)


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
  selected = _at_year(TransitChart(chart), 1990).select(
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


def test_yangren_checks_every_selected_transit_branch() -> None:
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


def test_yangren_and_feiren_definitions_are_independent() -> None:
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


def test_feiren_deduplicates_repeated_target_and_empty_result() -> None:
  chart = BaziChart(Bazi.create('1902-09-08 18:00', 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('壬寅', '己酉', '甲午', '癸酉')
  analysis = RelationshipAnalyzer(chart)
  assert analysis.at_birth.shensha['feiren'] == {Dizhi.酉}
  assert analysis.transits.shensha(TransitSet(
    dayun=Ganzhi.from_str('癸酉'),
    liunian=Ganzhi.from_str('乙酉'),
  ))['feiren'] == {Dizhi.酉}
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


def test_jinyu_deduplicates_shared_target_and_empty_result() -> None:
  # 丙年、戊日的金舆均在未；两锚命中同一支时只返回一个位置值。
  chart = BaziChart(Bazi.create(
    '1906-07-13 12:00',
    'male',
    BaziConfig(school=BaziSchool(jinyu_anchor=Anchor.YEAR_AND_DAY)),
  ))
  assert tuple(map(str, chart.bazi.pillars)) == ('丙午', '乙未', '戊午', '戊午')
  assert RelationshipAnalyzer(chart).at_birth.shensha['jinyu'] == {Dizhi.未}
  assert RelationshipAnalyzer(chart).transits.shensha(
    TransitSet(liunian=Ganzhi.from_str('乙未'))
  )['jinyu'] == {Dizhi.未}
  assert RelationshipAnalyzer(chart).transits.shensha(
    TransitSet(liunian=Ganzhi.from_str('甲子'))
  )['jinyu'] == set()


@pytest.mark.slow
def test_transit_day_master_relations(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year, rng)

      transit_tg = tuple(gz.tiangan for gz in transits.ganzhis)
      expected = tiangan_utils.discover_mutual([chart.bazi.day_master], transit_tg)
      actual = transits_analysis.day_master_relations(transits)

      assert _equal(expected, actual)


@pytest.mark.slow
def test_transit_house_relations(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    house = chart.house_of_relationship
    bazi = chart.bazi
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year, rng)

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
        definitions=bazi.config.school.relation_definitions, # The oracle mirrors the chart's school (issue #69).
      ).filter(__expected_filter)

      gong = _project_gong(
        dizhi_utils.discover_mutual_ganzhis(
          bazi.pillars,
          transits.ganzhis,
          definitions=bazi.config.school.relation_definitions,
        ),
        lambda combo : any(occurrence.index == 2 for occurrence in combo),
      )
      expected = expected.merge(gong)

      assert _equal(expected, actual)


def test_transit_gong_relations_use_mutual_scope_and_fill() -> None:
  chart = BaziChart(Bazi.create(datetime(1980, 1, 12, 20), BaziGender.MALE))
  analysis = RelationshipAnalyzer(chart).transits
  combo = dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.辰))

  transits = TransitSet(liunian=Ganzhi.from_str('甲辰'))
  assert combo in analysis.house_relations(transits)[DizhiRelation.拱合]

  filled = TransitSet(
    dayun=Ganzhi.from_str('甲辰'),
    liunian=Ganzhi.from_str('甲子'),
  )
  assert combo not in analysis.house_relations(filled).get(DizhiRelation.拱合, ())

  wide_only = TransitSet(liunian=Ganzhi.from_str('甲子'))
  assert DizhiRelation.拱合 not in analysis.house_relations(wide_only)
  wide_chart = BaziChart(Bazi.create(
    datetime(1980, 1, 12, 20),
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  assert dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.子)) in (
    RelationshipAnalyzer(wide_chart).transits.house_relations(wide_only)[DizhiRelation.拱合]
  )

  gonghui = TransitSet(liunian=Ganzhi.from_str('甲戌'))
  assert dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.戌)) in (
    analysis.house_relations(gonghui)[DizhiRelation.拱会]
  )


def test_transit_gong_relations_reach_stars() -> None:
  chart = BaziChart(Bazi.create(datetime(1980, 1, 21, 2), BaziGender.MALE))
  analysis = RelationshipAnalyzer(chart).transits
  transits = TransitSet(liunian=Ganzhi.from_str('癸丑'))
  combo = dizhi_utils.DizhiCombo((Dizhi.巳, Dizhi.丑))

  mutual = analysis.star_relations(transits, level=TransitAnalysis.Level.MUTUAL)
  assert combo in mutual.dizhi[DizhiRelation.拱合]
  assert DizhiRelation.拱合 not in analysis.star_relations(
    transits,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi

  star_birth_time = datetime(1984, 2, 17)
  star_chart = BaziChart(Bazi.create(star_birth_time, BaziGender.MALE))
  star_analysis = RelationshipAnalyzer(star_chart).transits
  wide_transits = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('甲午'),
  )
  assert DizhiRelation.拱合 not in star_analysis.star_relations(
    wide_transits,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi

  wide_star_chart = BaziChart(Bazi.create(
    star_birth_time,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  wide_star_relations = RelationshipAnalyzer(wide_star_chart).transits.star_relations(
    wide_transits,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  )
  assert dizhi_utils.DizhiCombo((Dizhi.寅, Dizhi.午)) in (
    wide_star_relations.dizhi[DizhiRelation.拱合]
  )

  full = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('甲午'),
    liuyue=Ganzhi.from_str('甲辰'),
  )
  narrow = full.select(TransitKind.DAYUN, TransitKind.LIUYUE)
  assert DizhiRelation.拱会 not in star_analysis.star_relations(
    full,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi
  assert dizhi_utils.DizhiCombo((Dizhi.寅, Dizhi.辰)) in star_analysis.star_relations(
    narrow,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi[DizhiRelation.拱会]


@pytest.mark.slow
def test_transit_star_relations(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    stars = chart.relationship_stars

    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(64):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year, rng)
      random_level = rng.choice([
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
        dz_discovery = dz_discovery.merge(dizhi_utils.discover(transit_dz, definitions=school.relation_definitions))
        dz_discovery = dz_discovery.merge(_project_gong(
          dizhi_utils.discover_ganzhis(transits.ganzhis, definitions=school.relation_definitions),
          lambda _: True,
        ))
      if random_level in [TransitAnalysis.Level.MUTUAL, TransitAnalysis.Level.ALL]:
        tg_discovery = tg_discovery.merge(tiangan_utils.discover_mutual(chart.bazi.four_tiangans, transit_tg))
        dz_discovery = dz_discovery.merge(dizhi_utils.discover_mutual(chart.bazi.four_dizhis, transit_dz, definitions=school.relation_definitions))
        dz_discovery = dz_discovery.merge(_project_gong(
          dizhi_utils.discover_mutual_ganzhis(
            chart.bazi.pillars,
            transits.ganzhis,
            definitions=school.relation_definitions,
          ),
          lambda _: True,
        ))

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
def test_zhengyin(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year, rng)

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
def test_star(rng: random.Random) -> None:
  for _ in range(16):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(64):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = _random_year_transits(transit_chart, random_year, rng)

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


def test_transit_analysis_negative(rng: random.Random) -> None:
  chart = BaziChart.random(rng=rng)
  transits_analysis = RelationshipAnalyzer(chart).transits

  for analysis in (transits_analysis.shensha, transits_analysis.day_master_relations,
                   transits_analysis.house_relations, transits_analysis.star_relations,
                   transits_analysis.zhengyin, transits_analysis.star):
    with pytest.raises(TypeError):
      analysis(object()) # type: ignore

  transits = _at_year(TransitChart(chart), chart.bazi.ganzhi_year).select(TransitKind.LIUNIAN)
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


def test_analyses_are_built_from_the_registry() -> None:
  # Both analyses build their dicts by iterating the registry behind a `cast`, so mypy no
  # longer checks the key set -- this is the executor. A registry entry that never lands in
  # the result, or a declared key with no entry, fails here (issue #172).
  # 两处分析都在 `cast` 之后按注册表推导，键集不再由 mypy 检查——这条测试就是执行者。
  chart: BaziChart = BaziChart(Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE))
  analyzer = RelationshipAnalyzer(chart)

  at_birth_keys = AtBirthShenshaAnalysis.__required_keys__ | AtBirthShenshaAnalysis.__optional_keys__
  assert set(analyzer.at_birth.shensha) == set(at_birth_keys)

  transits = _at_year(TransitChart(chart), chart.bazi.ganzhi_year).select(TransitKind.LIUNIAN)
  common_keys = ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__
  assert set(analyzer.transits.shensha(transits)) == set(common_keys)


def test_at_birth_shensha_analysis_has_only_whole_pillar_extras() -> None:
  common_keys = ShenshaAnalysis.__required_keys__ | ShenshaAnalysis.__optional_keys__
  at_birth_keys = AtBirthShenshaAnalysis.__required_keys__ | AtBirthShenshaAnalysis.__optional_keys__
  assert at_birth_keys == common_keys | {'kuigang', 'tianshe'}
  assert {'kuigang', 'tianshe'}.isdisjoint(_REGISTRY)


def test_at_birth_anchors_preserve_kind_and_pillar_scope() -> None:
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


def test_at_birth_anchor_resolver_reads_the_chart_school() -> None:
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


def test_at_birth_repeated_branch_values_are_all_inspected() -> None:
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


def test_transit_anchors_reuse_the_keys_without_pillar_exclusion() -> None:
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


def test_registry_definitions_are_the_declared_fields() -> None:
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
def test_wenchang_definition_at_birth_and_transits(
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

# ----------------------------------------------------------------------------------

from dataclasses import replace
from typing import Any

from bazi.analyzer.relationship import (
  RelationshipEvidence, StarAppearance, StemRelationDiscovery, _discover_stem_occurrences, spouse_evidence,
)
from bazi.defines import TianganRelation
from bazi.school import PeiouXingDef


def _at(combo: frozenset) -> set[int]:
  return {occurrence.index for occurrence in combo}


def test_stem_occurrences_expand_value_combos_per_position() -> None:
  left = [Ganzhi.from_str(value) for value in ('甲子', '己丑', '丙寅', '己卯')]
  right = [Ganzhi.from_str(value) for value in ('甲子', '丙寅', '己丑', '己卯')]
  left_discovery = _discover_stem_occurrences(left)
  right_discovery = _discover_stem_occurrences(right)
  assert [_at(combo) for combo in left_discovery[TianganRelation.合]] == [{0, 1}, {0, 3}]
  assert [_at(combo) for combo in right_discovery[TianganRelation.合]] == [{0, 2}, {0, 3}]
  assert tiangan_utils.discover([gz.tiangan for gz in left]) == tiangan_utils.discover([gz.tiangan for gz in right])
  assert left_discovery != right_discovery
  # The day master's visible stem (position 0 here) may appear as a real participant; combos carry no direction.
  for discovery in (left_discovery, right_discovery):
    assert all(0 in _at(combo) for combo in discovery[TianganRelation.合])

  # Hidden stems never enter Tiangan combos: 子 hides 癸, 辰 hides 戊, else 癸 at 子 and visible 戊 at 辰 would 合.
  hidden_carrier = [Ganzhi.from_str('甲子'), Ganzhi.from_str('戊辰')]
  assert TianganRelation.合 not in _discover_stem_occurrences(hidden_carrier)


def test_evidence_transit_internal_relations_use_shifted_indexes() -> None:
  # A 丙 day-master male chart (2000-01-09T12:00, 己卯丁丑丙寅甲午): target stem 辛, target branch 酉.
  chart = BaziChart(Bazi.create(datetime(2000, 1, 9, 12), 'male'))
  transits = TransitSet(
    xiaoyun=Ganzhi.from_str('丙戌'),
    dayun=Ganzhi.from_str('甲申'),
    liunian=Ganzhi.from_str('丁酉'),
  )
  evidence = spouse_evidence(chart, transits)
  assert isinstance(evidence, RelationshipEvidence)
  assert evidence.star_target.tiangan is Tiangan.辛
  assert evidence.star_target.dizhi == (Dizhi.酉,)
  assert evidence.transits is transits

  # Transit-internal 三会 申酉戌: indexes 4, 5, 6.
  assert [_at(combo) for combo in evidence.star_relations[DizhiRelation.三会]] == [{4, 5, 6}]
  # It has no day pillar, so no house evidence; it has 酉 (the spouse-star branch), so it enters star evidence.
  assert DizhiRelation.三会 not in evidence.house_relations
  # Every house-evidence combo contains the day pillar as a specific occurrence (index 2).
  for combos in evidence.house_relations.values():
    assert all(2 in _at(combo) for combo in combos)
  # Every stem-evidence combo contains the target stem; this chart has no visible 辛, so the key is empty.
  assert evidence.stem_relations == StemRelationDiscovery({})

  # One liunian forms no internal relation and cannot verify numbering; internal relations need two or more transits (above).
  single = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('甲辰')))
  assert single.transits is not None and single.transits.json == {'liunian': '甲辰'}
  for discovery in (single.house_relations, single.star_relations):
    for combos in discovery.values():
      for combo in combos:
        # A single-liunian combo cannot have all indexes >= 4; cross-group combos (like 1, 4) may exist.
        assert not all(index >= 4 for index in _at(combo))


def test_evidence_gong_scopes_are_not_suppressed_by_either_side() -> None:
  # Natal 甲申、甲戌 拱 酉 with the transit bringing 酉: the natal-internal 拱会 (2,3) stays, not suppressed by the fill-in.
  natal_gong = BaziChart(Bazi.create(datetime(1998, 8, 5, 20), 'male'))
  assert tuple(map(str, natal_gong.bazi.pillars)) == ('戊寅', '己未', '甲申', '甲戌')
  filled = spouse_evidence(natal_gong, TransitSet(liunian=Ganzhi.from_str('己酉')))
  assert [_at(combo) for combo in filled.house_relations[DizhiRelation.拱会]] == [{2, 3}]

  # Mirror: transit-internal 甲申、甲戌 拱 酉 while the natal has 酉, so transit-internal 拱会 (4,5) stays.
  # 癸 day-master female: target stem 戊, target branches 辰戌; 戌 is a real branch participant, so the 拱会 enters star evidence.
  transit_gong = BaziChart(Bazi.create(datetime(1969, 9, 25, 6), 'female'))
  assert tuple(map(str, transit_gong.bazi.pillars)) == ('己酉', '癸酉', '癸卯', '乙卯')
  mirrored = spouse_evidence(transit_gong, TransitSet(
    dayun=Ganzhi.from_str('甲申'),
    liunian=Ganzhi.from_str('甲戌'),
  ))
  assert mirrored.star_target.tiangan is Tiangan.戊
  assert [_at(combo) for combo in mirrored.star_relations[DizhiRelation.拱会]] == [{4, 5}]


def test_evidence_reads_school_definitions_in_all_calls() -> None:
  # 刑 follows xing_def: on the same real chart (庚辰辛巳丙寅甲午), LOOSE forms a 刑 between day pillar (寅) and 巳,
  # STRICT does not. 拱 follows gong_def: 戊寅己未甲申甲戌 has natal-internal 拱会 under both SAME_STEM levels,
  # none under TRANSFORMING_NARROW (no metal stem) or LU_NARROW (禄 level has no 拱会); all four evaluations pass this chart's definitions.
  for xing_def, expected in (
    (DizhiRules.XingDef.LOOSE, [{1, 2}]),
    (DizhiRules.XingDef.STRICT, []),
  ):
    chart = BaziChart(Bazi.create(
      datetime(2000, 5, 8, 12), 'male',
      BaziConfig(school=BaziSchool(xing_def=xing_def)),
    ))
    assert tuple(map(str, chart.bazi.pillars)) == ('庚辰', '辛巳', '丙寅', '甲午')
    evidence = spouse_evidence(chart, None)
    assert [{o.index for o in combo} for combo in evidence.house_relations.get(DizhiRelation.刑, ())] == expected

  # 冲 and 自刑 ignore xing_def: on 己卯丙子戊午戊午 the 子午 冲 and 午午 自刑 give the same result under both levels.
  for xing_def in DizhiRules.XingDef:
    chart = BaziChart(Bazi.create(
      datetime(2000, 1, 1, 12), 'male',
      BaziConfig(school=BaziSchool(xing_def=xing_def)),
    ))
    evidence = spouse_evidence(chart, None)
    assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.冲]] == [{1, 2}]
    assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.刑]] == [{2, 3}]

  for gong_def, expected in (
    (DizhiRules.GongDef.SAME_STEM_NARROW, [{2, 3}]),
    (DizhiRules.GongDef.SAME_STEM_WIDE, [{2, 3}]),
    (DizhiRules.GongDef.TRANSFORMING_NARROW, []),
    (DizhiRules.GongDef.LU_NARROW, []),
  ):
    chart = BaziChart(Bazi.create(
      datetime(1998, 8, 5, 20), 'male',
      BaziConfig(school=BaziSchool(gong_def=gong_def)),
    ))
    evidence = spouse_evidence(chart, None)
    assert [_at(combo) for combo in evidence.house_relations.get(DizhiRelation.拱会, ())] == expected


def test_evidence_cross_group_gong_precise_participants() -> None:
  # Male chart 戊寅己未甲申甲戌: the chosen liunian 甲戌 (explicit TransitSet, the function's declared input) 拱 酉
  # with the day pillar; the cross-group 拱会 is exactly {2,4}: index 2 is day pillar 甲申, index 4 is the chosen
  # liunian (transits start at 4); natal-internal 拱会 {2,3} stays, not suppressed by the liunian filling the 拱.
  chart = BaziChart(Bazi.create(datetime(1998, 8, 5, 20), 'male'))
  evidence = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('甲戌')))
  assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.拱会]] == [{2, 3}, {2, 4}]
  participants = {
    occurrence.index: str(occurrence.ganzhi)
    for combo in evidence.house_relations[DizhiRelation.拱会]
    for occurrence in combo
  }
  assert participants == {2: '甲申', 3: '甲戌', 4: '甲戌'}


def test_evidence_school_definitions_flow_through_all_segments_with_transits(monkeypatch: pytest.MonkeyPatch) -> None:
  # Male chart 戊寅己未甲申甲戌 (gong_def=SAME_STEM_WIDE): transits are queried for real by coordinate (at_year
  # 2054, 甲戌 liunian), never hand-picked ganzhi. Spies wrap the real discovery tools, recording the definitions
  # (non-拱 full sequence, natal 拱, cross-group 拱, transit-internal 拱); each must be this chart's definitions.
  chart = BaziChart(Bazi.create(
    datetime(1998, 8, 5, 20), 'male',
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  queried = TransitChart(chart).at_year(2054)
  assert queried is not None and queried.liunian is not None
  transits = queried.select(TransitKind.LIUNIAN)
  definitions = chart.bazi.config.school.relation_definitions

  seen: list[tuple[str, int, bool]] = []
  original_discover = dizhi_utils.discover_ganzhis
  original_mutual = dizhi_utils.discover_mutual_ganzhis

  def __spied_discover(ganzhis: Sequence[Ganzhi], **kwargs: Any) -> dizhi_utils.GanzhiRelationDiscovery:
    # relation_definitions builds a new object each time, so the spy compares by value.
    seen.append(('discover_ganzhis', len(ganzhis), kwargs['definitions'] == definitions))
    return original_discover(ganzhis, **kwargs)

  def __spied_mutual(
    left: Sequence[Ganzhi], right: Sequence[Ganzhi], **kwargs: Any,
  ) -> dizhi_utils.GanzhiRelationDiscovery:
    seen.append(('discover_mutual_ganzhis', len(left) + len(right), kwargs['definitions'] == definitions))
    return original_mutual(left, right, **kwargs)

  monkeypatch.setattr(dizhi_utils, 'discover_ganzhis', __spied_discover)
  monkeypatch.setattr(dizhi_utils, 'discover_mutual_ganzhis', __spied_mutual)
  evidence = spouse_evidence(chart, transits)
  assert seen == [
    ('discover_ganzhis', 5, True),
    ('discover_ganzhis', 4, True),
    ('discover_mutual_ganzhis', 5, True),
    ('discover_ganzhis', 1, True),
  ]
  # Non-default gong_def changes transit-inclusive evaluation: cross-group 拱 {2,4} exists here; TRANSFORMING_NARROW on the same chart and liunian has none.
  assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.拱会]] == [{2, 3}, {2, 4}]
  narrow = BaziChart(Bazi.create(
    datetime(1998, 8, 5, 20), 'male',
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.TRANSFORMING_NARROW)),
  ))
  narrow_queried = TransitChart(narrow).at_year(2054)
  assert narrow_queried is not None and narrow_queried.liunian is not None
  narrow_evidence = spouse_evidence(narrow, narrow_queried.select(TransitKind.LIUNIAN))
  assert DizhiRelation.拱会 not in narrow_evidence.house_relations


def test_evidence_star_target_follows_peiou_xing_def() -> None:
  # 乙 day-master male (2000-01-08T12:00, 己卯丁丑乙丑壬午): the default reading takes 戊 (辰戌), 阴阳干 takes 己 (丑未).
  default = BaziChart(Bazi.create(datetime(2000, 1, 8, 12), 'male'))
  yinyang = BaziChart(Bazi.create(
    datetime(2000, 1, 8, 12), 'male',
    BaziConfig(school=BaziSchool(peiou_xing_def=PeiouXingDef.YINYANGGAN)),
  ))
  assert tuple(map(str, default.bazi.pillars)) == ('己卯', '丁丑', '乙丑', '壬午')
  assert default.relationship_stars.tiangan is Tiangan.戊
  assert yinyang.relationship_stars.tiangan is Tiangan.己
  default_evidence = spouse_evidence(default, None)
  yinyang_evidence = spouse_evidence(yinyang, None)
  # Default reading: the natal has no 辰戌, so star evidence is empty; 阴阳干 reading: 丑 (both occurrences) joins as a target branch.
  assert default_evidence.star_relations == dizhi_utils.GanzhiRelationDiscovery({})
  assert {o.index for combo in yinyang_evidence.star_relations[DizhiRelation.害] for o in combo} == {1, 2, 3}


def test_evidence_appearances_keep_layers_and_positions() -> None:
  # 丙 day-master male (2000-01-29T06:00, 己卯丁丑丙戌辛卯): target 辛 is 藏干 in month branch 丑 and day branch
  # 戌, 明干 in the hour stem; both layers coexist per position; the day pillar's visible slot never shows the target (never the day master).
  chart = BaziChart(Bazi.create(datetime(2000, 1, 29, 6), 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('己卯', '丁丑', '丙戌', '辛卯')
  evidence = spouse_evidence(chart, None)
  assert [(a.origin, a.pillar, a.kind, str(a.ganzhi), a.layer, a.stem) for a in evidence.appearances] == [
    ('natal', 'month', None, '丁丑', 'hidden', Tiangan.辛),
    ('natal', 'day', None, '丙戌', 'hidden', Tiangan.辛),
    ('natal', 'hour', None, '辛卯', 'visible', Tiangan.辛),
  ]
  with_transits = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('辛亥')))
  assert [(a.origin, a.kind, str(a.ganzhi), a.layer) for a in with_transits.appearances if a.origin == 'transit'] == [
    ('transit', TransitKind.LIUNIAN, '辛亥', 'visible'),
  ]
  # Chosen liunian 辛酉: 酉 hides 辛, so visible and hidden layers coexist at one position, one appearance each, kind preserved.
  xinyou = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('辛酉')))
  assert [(a.origin, a.kind, str(a.ganzhi), a.layer) for a in xinyou.appearances if a.origin == 'transit'] == [
    ('transit', TransitKind.LIUNIAN, '辛酉', 'visible'),
    ('transit', TransitKind.LIUNIAN, '辛酉', 'hidden'),
  ]
  # Construction checks follow the ChartOccurrence style: visible stem must equal the pillar stem, hidden stem must live in its branch, exclusive coordinates rejected.
  appearance = evidence.appearances[2]
  assert appearance is not None
  value_changes: tuple[dict[str, Any], ...] = (
    {'origin': 'other'}, {'layer': 'other'}, {'layer': 'hidden'}, {'pillar': 'liunian'},
    {'kind': TransitKind.LIUNIAN}, {'stem': Tiangan.庚},
  )
  for change in value_changes:
    with pytest.raises(ValueError):
      replace(appearance, **change)
  type_changes: tuple[dict[str, Any], ...] = (
    {'ganzhi': '辛卯'}, {'stem': '辛'}, {'kind': 'liunian'},
    {'origin': 1}, {'layer': 1}, {'pillar': 1},
  )
  for change in type_changes:
    with pytest.raises(TypeError):
      replace(appearance, **change)
  # RelationshipEvidence's construction-time type gate; scope-style cross-field constraints belong to ContextResult.
  for change in (
    {'star_target': '辛'}, {'appearances': (object(),)}, {'house_relations': {}},
    {'stem_relations': {}}, {'transits': TransitChart},
  ):
    with pytest.raises(TypeError):
      replace(evidence, **change)
  assert spouse_evidence(chart, None).transits is None
  with pytest.raises(TypeError):
    spouse_evidence(chart.bazi, None) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    spouse_evidence(chart, '甲辰') # type: ignore[arg-type]
  assert StarAppearance('transit', None, TransitKind.LIUNIAN, Ganzhi.from_str('辛亥'), 'visible', Tiangan.辛)
  with pytest.raises(ValueError):
    StarAppearance('transit', 'hour', TransitKind.LIUNIAN, Ganzhi.from_str('辛亥'), 'visible', Tiangan.辛)


def test_evidence_day_pillar_is_a_specific_occurrence() -> None:
  # 己卯丙子戊午戊午: day branch 午 冲 month branch 子 (1,2); the hour branch equals the day branch in value, but
  # the 子午 combo (1,3) lacks the day pillar as a specific occurrence, so it does not enter house evidence.
  chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('己卯', '丙子', '戊午', '戊午')
  evidence = spouse_evidence(chart, None)
  assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.冲]] == [{1, 2}]
  for combos in evidence.house_relations.values():
    assert all(2 in _at(combo) for combo in combos)
    assert all(_at(combo) != {1, 3} for combo in combos)


@pytest.mark.slow
def test_non_gong_full_sequence_equals_three_segment_union() -> None:
  # Non-拱 relations on the full sequence equal, combo by combo, 「原局内部 ∪ 跨组 ∪ 岁运内部(+4)」; this is a seeded
  # randomized property test (seed hardcoded here), not exhaustive; 拱 is deliberately not unioned segment-wise (fill-in semantics).
  from random import Random
  from bazi.rules import DizhiRelationDefinitions
  from bazi.utils.dizhi_utils import GanzhiOccurrence, GanzhiRelationDiscovery
  rng = Random(20261015)
  non_gong = tuple(rel for rel in DizhiRelation if rel not in DizhiRules.GONG_RELATIONS)
  cycle = tuple(Ganzhi.from_str(f'{tg}{dz}') for tg in Tiangan for dz in Dizhi)

  def __shifted(discovery: GanzhiRelationDiscovery, offset: int) -> dict[DizhiRelation, set[frozenset[GanzhiOccurrence]]]:
    return {
      relation: {
        frozenset(GanzhiOccurrence(occurrence.index + offset, occurrence.ganzhi) for occurrence in combo)
        for combo in combos
      }
      for relation, combos in discovery.items()
    }

  for _ in range(40):
    natal = tuple(rng.choice(cycle) for _ in range(4))
    transits = tuple(rng.choice(cycle) for _ in range(rng.randrange(0, 5)))
    definitions = DizhiRelationDefinitions(
      anhe_def=rng.choice(tuple(DizhiRules.AnheDef)),
      xing_def=rng.choice(tuple(DizhiRules.XingDef)),
      gong_def=rng.choice(tuple(DizhiRules.GongDef)),
    )
    combined = dizhi_utils.discover_ganzhis(natal + transits, definitions=definitions, relations=non_gong)
    segments = (
      dizhi_utils.discover_ganzhis(natal, definitions=definitions, relations=non_gong),
      dizhi_utils.discover_mutual_ganzhis(natal, transits, definitions=definitions, relations=non_gong),
      dizhi_utils.discover_ganzhis(transits, definitions=definitions, relations=non_gong),
    )
    union: dict[DizhiRelation, set[frozenset[GanzhiOccurrence]]] = {}
    for index, segment in enumerate(segments):
      for relation, combos in __shifted(segment, 0 if index < 2 else 4).items():
        union.setdefault(relation, set()).update(combos)
    for relation in non_gong:
      expected = {frozenset(combo) for combo in union.get(relation, ())}
      actual = {frozenset(combo) for combo in combined.get(relation, ())}
      assert expected == actual, (relation, natal, transits)
