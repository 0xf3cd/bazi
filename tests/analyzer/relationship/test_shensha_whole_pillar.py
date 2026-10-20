# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shensha_whole_pillar.py

import pytest

from bazi.defines import Dizhi, Ganzhi
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.transits import TransitSet
from bazi.analyzer.relationship import RelationshipAnalyzer


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
