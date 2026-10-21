# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError, replace

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Tiangan, Dizhi, Ganzhi
from bazi.school import Anchor, BaziConfig, BaziSchool
from bazi.transits import TransitKind, TransitSet
from bazi.analyzer.relationship import KongwangHit, KongwangResult, RelationshipAnalyzer


def _analyzer(birth: str, anchor: Anchor) -> RelationshipAnalyzer:
  return RelationshipAnalyzer(BaziChart(Bazi.create(
    birth, 'male', BaziConfig(school=BaziSchool(kongwang_anchor=anchor)),
  )))


@pytest.mark.parametrize('anchor, names, targets', [
  (Anchor.YEAR, ('year',), (('day', '壬戌'),)),
  (Anchor.DAY, ('day',), (('year', '甲子'),)),
  (Anchor.YEAR_AND_DAY, ('year', 'day'), (('day', '壬戌'), ('year', '甲子'))),
])
def test_year_day_mutual_hits_keep_each_anchor(
  anchor: Anchor, names: tuple[str, ...], targets: tuple[tuple[str, str], ...],
) -> None:
  analyzer = _analyzer('1984-03-29 12:00', anchor)
  results = analyzer.at_birth.kongwang
  assert tuple(result.anchor for result in results) == names
  assert tuple((hit.pillar, str(hit.ganzhi)) for result in results for hit in result.hits) == targets
  expected = {'year': ('甲子', frozenset({Dizhi.戌, Dizhi.亥})), 'day': ('壬戌', frozenset({Dizhi.子, Dizhi.丑}))}
  for result in results:
    assert (str(result.ganzhi), result.xunkong) == expected[result.anchor]
    assert all(hit.origin == 'natal' and hit.kind is None for hit in result.hits)
  assert analyzer.at_birth.shensha['kongwang'] == frozenset(hit.ganzhi.dizhi for result in results for hit in result.hits)


def test_repeated_target_branches_keep_positions() -> None:
  analyzer = _analyzer('1982-10-09 20:00', Anchor.DAY)
  result, = analyzer.at_birth.kongwang
  assert str(result.ganzhi) == '乙丑'
  assert result.xunkong == frozenset({Dizhi.戌, Dizhi.亥})
  assert tuple((hit.pillar, str(hit.ganzhi)) for hit in result.hits) == (
    ('year', '壬戌'), ('month', '庚戌'), ('hour', '丙戌'),
  )
  assert analyzer.at_birth.shensha['kongwang'] == frozenset({Dizhi.戌})


def test_same_anchor_values_and_no_hits_survive() -> None:
  analyzer = _analyzer('1984-03-31 12:00', Anchor.YEAR_AND_DAY)
  results = analyzer.at_birth.kongwang
  assert tuple(result.anchor for result in results) == ('year', 'day')
  assert tuple(str(result.ganzhi) for result in results) == ('甲子', '甲子')
  assert all(result.hits == () and result.xunkong == frozenset({Dizhi.戌, Dizhi.亥}) for result in results)
  assert analyzer.at_birth.shensha['kongwang'] == frozenset()
  transits = TransitSet(liunian=Ganzhi.from_str('甲子'))
  assert all(result.hits == () for result in analyzer.transits.kongwang(transits))
  assert analyzer.transits.shensha(transits)['kongwang'] == frozenset()


def test_same_anchor_values_keep_separate_hits() -> None:
  analyzer = _analyzer('1984-03-31 20:00', Anchor.YEAR_AND_DAY)
  results = analyzer.at_birth.kongwang
  assert tuple(result.anchor for result in results) == ('year', 'day')
  assert tuple(str(result.ganzhi) for result in results) == ('甲子', '甲子')
  assert tuple(tuple((hit.pillar, str(hit.ganzhi)) for hit in result.hits) for result in results) == (
    (('hour', '甲戌'),), (('hour', '甲戌'),),
  )
  assert analyzer.at_birth.shensha['kongwang'] == frozenset({Dizhi.戌})


@pytest.mark.parametrize('anchor, counts', [
  (Anchor.YEAR, (2,)), (Anchor.DAY, (1,)), (Anchor.YEAR_AND_DAY, (2, 1)),
])
def test_transit_kinds_are_not_merged(anchor: Anchor, counts: tuple[int, ...]) -> None:
  analyzer = _analyzer('1984-03-29 12:00', anchor)
  transits = TransitSet(
    dayun=Ganzhi.from_str('甲戌'), liunian=Ganzhi.from_str('甲戌'), liuyue=Ganzhi.from_str('甲子'),
  )
  results = analyzer.transits.kongwang(transits)
  assert tuple(len(result.hits) for result in results) == counts
  for result in results:
    expected = (
      ((TransitKind.DAYUN, '甲戌'), (TransitKind.LIUNIAN, '甲戌')) if result.anchor == 'year'
      else ((TransitKind.LIUYUE, '甲子'),)
    )
    assert tuple((hit.kind, str(hit.ganzhi)) for hit in result.hits) == expected
    assert all(hit.origin == 'transit' and hit.pillar is None for hit in result.hits)
  assert analyzer.transits.shensha(transits)['kongwang'] == frozenset(hit.ganzhi.dizhi for result in results for hit in result.hits)


def test_kongwang_does_not_change_other_results() -> None:
  day = _analyzer('1984-03-29 12:00', Anchor.DAY)
  both = _analyzer('1984-03-29 12:00', Anchor.YEAR_AND_DAY)
  transits = TransitSet(dayun=Ganzhi.from_str('甲戌'), liunian=Ganzhi.from_str('甲辰'))
  for left, right in ((day.at_birth.shensha, both.at_birth.shensha),
                      (day.transits.shensha(transits), both.transits.shensha(transits))):
    assert {key: value for key, value in left.items() if key != 'kongwang'} == {
      key: value for key, value in right.items() if key != 'kongwang'
    }
  assert day.at_birth.house_relations == both.at_birth.house_relations
  assert day.at_birth.star_relations == both.at_birth.star_relations
  assert day.transits.house_relations(transits) == both.transits.house_relations(transits)
  assert both.transits.shensha(transits)['kongwang'] == frozenset({Dizhi.戌}) # 辰冲 does not cancel 戌.


def test_detail_results_are_frozen_values() -> None:
  result, = _analyzer('1982-10-09 20:00', Anchor.DAY).at_birth.kongwang
  assert hash(result) == hash(replace(result))
  with pytest.raises(FrozenInstanceError):
    result.anchor = 'year' # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result.hits[0].pillar = 'hour' # type: ignore[misc]
  with pytest.raises(TypeError):
    _analyzer('1984-03-29 12:00', Anchor.DAY).transits.kongwang(object()) # type: ignore[arg-type]


@pytest.mark.parametrize('changes, error', [
  ({'ganzhi': '甲戌'}, TypeError), ({'ganzhi': Ganzhi('甲', Dizhi.戌)}, TypeError), # type: ignore[arg-type]
  ({'ganzhi': Ganzhi(Tiangan.甲, '戌')}, TypeError), # type: ignore[arg-type]
  ({'origin': 1}, TypeError), ({'pillar': 1}, TypeError), ({'kind': 'dayun'}, TypeError),
  ({'origin': 'unknown'}, ValueError), ({'pillar': None}, ValueError),
  ({'pillar': 'unknown'}, ValueError),
  ({'kind': TransitKind.DAYUN}, ValueError),
  ({'origin': 'transit'}, ValueError),
  ({'origin': 'transit', 'pillar': None}, ValueError),
])
def test_hit_coordinates_are_validated(changes: dict[str, object], error: type[Exception]) -> None:
  hit = KongwangHit('natal', 'month', None, Ganzhi.from_str('甲戌'))
  with pytest.raises(error):
    replace(hit, **changes) # type: ignore[arg-type] # Deliberately invalid public constructor fields.


@pytest.mark.parametrize('changes, error', [
  ({'anchor': 1}, TypeError), ({'anchor': 'month'}, ValueError),
  ({'ganzhi': '甲子'}, TypeError), ({'ganzhi': Ganzhi.from_str('甲丑')}, ValueError),
  ({'hits': []}, TypeError), ({'hits': (object(),)}, TypeError),
  ({'hits': (KongwangHit('natal', 'hour', None, Ganzhi.from_str('甲子')),)}, ValueError),
  ({'hits': (KongwangHit('natal', 'day', None, Ganzhi.from_str('甲戌')),)}, ValueError),
])
def test_result_anchor_and_hits_are_validated(changes: dict[str, object], error: type[Exception]) -> None:
  result = KongwangResult('day', Ganzhi.from_str('甲子'), ())
  with pytest.raises(error):
    replace(result, **changes) # type: ignore[arg-type] # Deliberately invalid public constructor fields.
