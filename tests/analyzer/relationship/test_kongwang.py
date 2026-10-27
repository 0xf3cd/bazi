# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError, replace

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Zhu, Tiangan, Dizhi, Ganzhi
from bazi.school import Anchor, BaziConfig, BaziSchool
from bazi.transits import TransitKind, TransitSet
from bazi.analyzer.relationship import KongwangHit, KongwangResult, RelationshipAnalyzer


def _analyzer(birth: str, anchor: Anchor) -> RelationshipAnalyzer:
  return RelationshipAnalyzer(BaziChart(Bazi.create(
    birth, 'male', BaziConfig(school=BaziSchool(kongwang_anchor=anchor)),
  )))


@pytest.mark.parametrize('anchor, names, targets', [
  (Anchor.YEAR, (Zhu.年,), ((Zhu.日, '壬戌'),)),
  (Anchor.DAY, (Zhu.日,), ((Zhu.年, '甲子'),)),
  (Anchor.YEAR_AND_DAY, (Zhu.年, Zhu.日), ((Zhu.日, '壬戌'), (Zhu.年, '甲子'))),
])
def test_year_day_mutual_hits_keep_each_anchor(
  anchor: Anchor, names: tuple[Zhu, ...], targets: tuple[tuple[Zhu, str], ...],
) -> None:
  analyzer = _analyzer('1984-03-29 12:00', anchor)
  results = analyzer.at_birth.kongwang
  assert tuple(result.anchor for result in results) == names
  assert tuple((hit.position, str(hit.ganzhi)) for result in results for hit in result.hits) == targets
  expected = {Zhu.年: ('甲子', frozenset({Dizhi.戌, Dizhi.亥})), Zhu.日: ('壬戌', frozenset({Dizhi.子, Dizhi.丑}))}
  for result in results:
    assert (str(result.ganzhi), result.xunkong) == expected[result.anchor]
    assert all(isinstance(hit.position, Zhu) and hit.position != result.anchor for hit in result.hits)
  assert analyzer.at_birth.shensha['kongwang'] == frozenset(hit.ganzhi.dizhi for result in results for hit in result.hits)


def test_repeated_target_branches_keep_positions() -> None:
  analyzer = _analyzer('1982-10-09 20:00', Anchor.DAY)
  result, = analyzer.at_birth.kongwang
  assert str(result.ganzhi) == '乙丑'
  assert result.xunkong == frozenset({Dizhi.戌, Dizhi.亥})
  assert tuple((hit.position, str(hit.ganzhi)) for hit in result.hits) == (
    (Zhu.年, '壬戌'), (Zhu.月, '庚戌'), (Zhu.时, '丙戌'),
  )
  assert analyzer.at_birth.shensha['kongwang'] == frozenset({Dizhi.戌})


def test_same_anchor_values_and_no_hits_survive() -> None:
  analyzer = _analyzer('1984-03-31 12:00', Anchor.YEAR_AND_DAY)
  results = analyzer.at_birth.kongwang
  assert tuple(result.anchor for result in results) == (Zhu.年, Zhu.日)
  assert tuple(str(result.ganzhi) for result in results) == ('甲子', '甲子')
  assert all(result.hits == () and result.xunkong == frozenset({Dizhi.戌, Dizhi.亥}) for result in results)
  assert analyzer.at_birth.shensha['kongwang'] == frozenset()
  transits = TransitSet(liunian=Ganzhi.from_str('甲子'))
  assert all(result.hits == () for result in analyzer.transits.kongwang(transits))
  assert analyzer.transits.shensha(transits)['kongwang'] == frozenset()


def test_same_anchor_values_keep_separate_hits() -> None:
  analyzer = _analyzer('1984-03-31 20:00', Anchor.YEAR_AND_DAY)
  results = analyzer.at_birth.kongwang
  assert tuple(result.anchor for result in results) == (Zhu.年, Zhu.日)
  assert tuple(str(result.ganzhi) for result in results) == ('甲子', '甲子')
  assert tuple(tuple((hit.position, str(hit.ganzhi)) for hit in result.hits) for result in results) == (
    ((Zhu.时, '甲戌'),), ((Zhu.时, '甲戌'),),
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
      ((TransitKind.DAYUN, '甲戌'), (TransitKind.LIUNIAN, '甲戌')) if result.anchor is Zhu.年
      else ((TransitKind.LIUYUE, '甲子'),)
    )
    assert tuple((hit.position, str(hit.ganzhi)) for hit in result.hits) == expected
    assert all(isinstance(hit.position, TransitKind) for hit in result.hits)
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
    result.anchor = Zhu.年 # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result.hits[0].position = Zhu.时 # type: ignore[misc]
  with pytest.raises(TypeError):
    _analyzer('1984-03-29 12:00', Anchor.DAY).transits.kongwang(object()) # type: ignore[arg-type]


@pytest.mark.parametrize('changes, error', [
  ({'ganzhi': '甲戌'}, TypeError), ({'ganzhi': Ganzhi('甲', Dizhi.戌)}, TypeError), # type: ignore[arg-type]
  ({'ganzhi': Ganzhi(Tiangan.甲, '戌')}, TypeError), # type: ignore[arg-type]
  ({'position': 1}, TypeError), ({'position': 'dayun'}, TypeError),
  ({'position': 'unknown'}, TypeError), ({'position': None}, TypeError),
])
def test_hit_coordinates_are_validated(changes: dict[str, object], error: type[Exception]) -> None:
  hit = KongwangHit(Zhu.月, Ganzhi.from_str('甲戌'))
  with pytest.raises(error):
    replace(hit, **changes) # type: ignore[arg-type] # Deliberately invalid public constructor fields.


@pytest.mark.parametrize('changes, error', [
  ({'anchor': 1}, TypeError), ({'anchor': Zhu.月}, ValueError),
  ({'ganzhi': '甲子'}, TypeError), ({'ganzhi': Ganzhi.from_str('甲丑')}, ValueError),
  ({'hits': []}, TypeError), ({'hits': (object(),)}, TypeError),
  ({'hits': (KongwangHit(Zhu.时, Ganzhi.from_str('甲子')),)}, ValueError),
  ({'hits': (KongwangHit(Zhu.日, Ganzhi.from_str('甲戌')),)}, ValueError),
])
def test_result_anchor_and_hits_are_validated(changes: dict[str, object], error: type[Exception]) -> None:
  result = KongwangResult(Zhu.日, Ganzhi.from_str('甲子'), ())
  with pytest.raises(error):
    replace(result, **changes) # type: ignore[arg-type] # Deliberately invalid public constructor fields.


def test_anchor_alias_subset_is_checked() -> None:
  anchor = Ganzhi.from_str('甲子')
  results = (
    KongwangResult(Zhu.年, anchor, ()), KongwangResult(Zhu.NIAN, anchor, ()),
    KongwangResult(Zhu.日, anchor, ()), KongwangResult(Zhu.RI, anchor, ()),
  )
  assert tuple(result.anchor for result in results) == (Zhu.年, Zhu.年, Zhu.日, Zhu.日)
  with pytest.raises(ValueError):
    KongwangResult(Zhu.月, anchor, ()) # type: ignore[arg-type] # 月／时不在年日锚点静态子集中。
  with pytest.raises(ValueError):
    KongwangResult(Zhu.YUE, anchor, ()) # type: ignore[arg-type] # 拼音别名也须被静态与运行时同时拒绝。
  with pytest.raises(ValueError):
    KongwangResult(Zhu.时, anchor, ()) # type: ignore[arg-type] # 月／时不在年日锚点静态子集中。
  with pytest.raises(ValueError):
    KongwangResult(Zhu.SHI, anchor, ()) # type: ignore[arg-type] # 拼音别名也须被静态与运行时同时拒绝。
