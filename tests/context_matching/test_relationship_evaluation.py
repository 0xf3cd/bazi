# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from datetime import datetime
from typing import Any

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextResult, RelatedEntry, evaluate_context, RelationshipProfile, TransitCoordinate
from bazi.defines import Tiangan, DizhiRelation
from bazi.defines import Dizhi as _Dizhi
from bazi.knowledge import KnowledgeBase
from bazi.school import BaziConfig, BaziSchool, PeiouXingDef
from bazi.transits import TransitKind

from matching_samples import PALACE, TOUGAN, RELATED_PALACE, RELATED_TOUGAN, rel_match, chart_from


def test_palace_verdict_matches_observations() -> None:
  # 宫刑冲: the male chart with 子午冲＋午午自刑 is SATISFIED; the 丙寅 day chart without 刑 or 冲 is NOT_SATISFIED.
  satisfied = rel_match()
  assert satisfied.criterion.status == 'SATISFIED' and satisfied.criterion.reason == 'premise_satisfied'
  assert satisfied.criterion.scope_complete is True
  assert dict(satisfied.criterion.observations) == {'day_pillar_in_chong': True, 'day_pillar_in_xing': True}
  unsatisfied = rel_match(birth='2000-01-09 12:00')
  assert unsatisfied.criterion.status == 'NOT_SATISFIED' and unsatisfied.criterion.reason == 'required_classification_absent'
  assert dict(unsatisfied.criterion.observations) == {'day_pillar_in_chong': False, 'day_pillar_in_xing': False}
  for result in (satisfied, unsatisfied):
    assert result.occurrences == () and result.entries == () and result.relationship is not None
    assert ContextResult.from_json(result.export_json()) == result


def test_tougan_verdict_matches_observations() -> None:
  # 透干: a visible 辛明干 is SATISFIED; 藏干 only record facts and never satisfy 「透」.
  visible = rel_match(TOUGAN, birth='2000-01-29 06:00')
  assert visible.criterion.status == 'SATISFIED'
  assert dict(visible.criterion.observations) == {'target_stem_visible': True, 'target_stem_hidden': True}
  hidden_only = rel_match(TOUGAN, birth='2000-01-01 12:00') # 丑 hides 辛; no 辛 in 明干.
  assert hidden_only.criterion.status == 'NOT_SATISFIED'
  assert dict(hidden_only.criterion.observations) == {'target_stem_visible': False, 'target_stem_hidden': True}
  for result in (visible, hidden_only):
    assert result.occurrences == () and result.entries == () and result.relationship is not None
    assert ContextResult.from_json(result.export_json()) == result


def test_relationship_scope_missing_data_paths() -> None:
  c = chart_from('2000-01-01 12:00', 'male') # born 2000-01-01, 干支年 1999.
  # Missing query coordinate: kinds stay explicitly non-empty; UNKNOWN/missing_transit_coordinate with transits None.
  no_coordinate = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', None, (TransitKind.LIUNIAN, TransitKind.DAYUN),
  ))
  assert no_coordinate.criterion.status == 'UNKNOWN' and no_coordinate.criterion.reason == 'missing_transit_coordinate'
  assert no_coordinate.criterion.scope_complete is False
  assert no_coordinate.relationship is not None and no_coordinate.relationship.transits is None
  # Before birth: the entry returns None → transit_unavailable.
  before_birth = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=1998), (TransitKind.LIUNIAN,),
  ))
  assert before_birth.criterion.reason == 'transit_unavailable'
  assert before_birth.relationship is not None and before_birth.relationship.transits is None
  # A DAY-precision at_moment entry is unavailable → transit_unavailable.
  day_precision = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_moment', solar_moment=datetime(2024, 4, 10, 12)), (TransitKind.LIUNIAN,),
  ))
  assert day_precision.criterion.reason == 'transit_unavailable'
  for result in (no_coordinate, before_birth, day_precision):
    assert ContextResult.from_json(result.export_json()) == result
    rendered = result.render()
    assert '请求种类=' in rendered and '未取得种类=' in rendered


def _assert_kind_record_roundtrip(result: ContextResult) -> None:
  restored = ContextResult.from_json(result.export_json())
  assert restored == result
  # The record keeps the requested kinds after round-trip.
  assert isinstance(result.profile, RelationshipProfile) and isinstance(restored.profile, RelationshipProfile)
  assert result.profile.kinds == restored.profile.kinds


def test_partial_kinds_keep_obtained_evidence() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  # No 小运 after adulthood: requesting {小运, 大运} obtains only 大运 → UNKNOWN/transit_unavailable, evidence of obtained kinds kept.
  partial = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN),
  ))
  assert partial.criterion.reason == 'transit_unavailable' and partial.criterion.scope_complete is False
  assert partial.relationship is not None
  assert partial.relationship.transits is not None
  assert tuple(partial.relationship.transits) == (TransitKind.DAYUN,)
  _assert_kind_record_roundtrip(partial)


def test_missing_kinds_return_no_transits() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  # Fully missing: only 小运 requested and none that year → empty intersection, transits None; the underlying select exception is not raised.
  all_missing = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN,),
  ))
  assert all_missing.criterion.reason == 'transit_unavailable'
  assert all_missing.relationship is not None and all_missing.relationship.transits is None
  _assert_kind_record_roundtrip(all_missing)


def test_complete_kinds_keep_fixed_order() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  # All requested kinds obtained: verdict per the criterion, obtained set in fixed order.
  complete = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN, TransitKind.DAYUN),
  ))
  assert complete.criterion.status == 'SATISFIED' and complete.criterion.scope_complete is True
  assert complete.relationship is not None
  assert complete.relationship.transits is not None
  assert tuple(kind for kind, _ in complete.relationship.transits.items) == (TransitKind.DAYUN, TransitKind.LIUNIAN)
  _assert_kind_record_roundtrip(complete)


def test_moment_microseconds_equal_but_recorded() -> None:
  c = BaziChart(Bazi.create('2000-01-01 12:00', 'male', BaziConfig.from_values(precision='hour')))
  profile_a = RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_moment', solar_moment=datetime(2024, 4, 10, 12, 30, 0, 500000)),
    (TransitKind.LIUNIAN, TransitKind.LIUYUE),
  )
  profile_b = RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_moment', solar_moment=datetime(2024, 4, 10, 12, 29, 59, 750000)),
    (TransitKind.LIUNIAN, TransitKind.LIUYUE),
  )
  left = evaluate_context(c, criterion_id=PALACE, profile=profile_a)
  right = evaluate_context(c, criterion_id=PALACE, profile=profile_b)
  assert left.criterion == right.criterion and left.relationship == right.relationship
  assert left != right # records keep the request as given, with no fake sub-second precision.
  assert isinstance(left.profile, RelationshipProfile) and isinstance(right.profile, RelationshipProfile)
  assert left.profile.coordinate is not None
  assert left.profile.coordinate.solar_moment is not None
  assert left.profile.coordinate.solar_moment.microsecond == 500000
  assert json.loads(left.export_json())['profile']['coordinate']['solar_moment'] == '2024-04-10T12:30:00.500000'
  assert ContextResult.from_json(left.export_json()) == left


def test_relationship_reference_matrix() -> None:
  # Related-entry matrix over include_reference_only × gender × structural status (three states).
  male = chart_from('2000-01-01 12:00', 'male')
  female = chart_from('2000-01-01 12:00', 'female')
  hidden: dict[str, Any] = {'include_reference_only': True}

  # False × anything: no reference section.
  off = evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal'))
  assert off.related == () and '关联参考' not in off.render()

  # True × male × SATISFIED/NOT_SATISFIED/UNKNOWN (two reasons): entry returned, recognized=True.
  for result in (
    evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal'), **hidden),
    evaluate_context(chart_from('2000-01-09 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile('natal'), **hidden),
    evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal_and_transits', None, (TransitKind.LIUNIAN,)), **hidden),
    evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile(
      'natal_and_transits', TransitCoordinate('at_year', gz_year=1998), (TransitKind.LIUNIAN,)), **hidden),
  ):
    assert [entry.claim_id for entry in result.related] == [RELATED_PALACE]
    assert all(entry.recognized for entry in result.related)
    rendered = result.render()
    assert '关联参考（该判据的条件参考，不表示事实已成立或完整前提已满足）：' + RELATED_PALACE in rendered
    assert knowledge_text(RELATED_PALACE) in rendered
    # NOT_SATISFIED/UNKNOWN use the same reference wording as SATISFIED; no 「已核结构命中」 appears.
    assert '已核结构命中' not in rendered
    assert '事实判别：' + result.criterion.status in rendered
    assert '事实判别不表示原文完整条件已满足，也不表示现实事件成立。' in rendered
    assert '前提满足只表示本范围内的原作使用条件满足' not in rendered

  # True × female: the two gated entries are never related (same-ID replacement included); structure is still evaluated; static queries stay unrestricted.
  female_result = evaluate_context(female, criterion_id=PALACE, profile=RelationshipProfile('natal'), **hidden)
  assert female_result.related == () and '关联参考' not in female_result.render()
  assert female_result.criterion.status == 'SATISFIED' # female charts are still evaluated by the structural criteria.
  knowledge = KnowledgeBase.load()
  assert knowledge.entry(RELATED_PALACE).text and knowledge.entry(RELATED_TOUGAN).text

  # True × male × entry missing from the knowledge base: no RelatedEntry is produced.
  trimmed = KnowledgeBase.from_json(knowledge.export_json(()))
  missing = evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal'), knowledge=trimmed, **hidden)
  assert missing.related == () and '关联参考' not in missing.render()


def knowledge_text(claim_id: str) -> str:
  return KnowledgeBase.load().entry(claim_id).text


@pytest.mark.parametrize('dimension', ['text', 'premise', 'limits', 'viewpoint', 'object', 'source'])
def test_female_gate_comes_before_binding(dimension: str) -> None:
  # Female charts never relate the two restricted IDs, and a same-ID custom replacement cannot bypass;
  # male replacement yields recognized=False, listing only the ID with 「绑定未识别」, without rendering the replacement text.
  knowledge = KnowledgeBase.load()
  data = json.loads(knowledge.export_json())
  entry = next(value for value in data['entries'] if value['claim_id'] == RELATED_PALACE)
  if dimension in ('text', 'premise', 'viewpoint'):
    entry[dimension] += '（编辑口径）'
  elif dimension == 'limits':
    entry['limits'] = [*entry['limits'], '编辑者另记的限度。']
  elif dimension == 'object':
    next(value for value in data['objects'] if value['object_id'] == 'concept.peiou_gong')['name'] = '同名异物'
  else:
    next(value for value in data['sources'] if value['source_id'] == 'tanyuan_qizi')['limitations'] += '不同边界。'
  custom = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))

  female = evaluate_context(chart_from('2000-01-01 12:00', 'female'), criterion_id=PALACE,
                            profile=RelationshipProfile('natal'), knowledge=custom, include_reference_only=True)
  assert female.related == () and '关联参考' not in female.render()
  assert '（编辑口径）' not in female.render()

  male = evaluate_context(chart_from('2000-01-01 12:00', 'male'), criterion_id=PALACE,
                          profile=RelationshipProfile('natal'), knowledge=custom, include_reference_only=True)
  assert [entry.claim_id for entry in male.related] == [RELATED_PALACE]
  assert male.related[0] == RelatedEntry(RELATED_PALACE, False)
  rendered = male.render()
  assert ('关联参考（该判据的条件参考，不表示事实已成立或完整前提已满足）：' + RELATED_PALACE + '；绑定未识别') in rendered
  assert '绑定未识别' in rendered
  if dimension == 'text':
    assert '（编辑口径）' not in rendered
  assert ContextResult.from_json(male.export_json()) == male
  with pytest.raises(ValueError):
    RelatedEntry('', True)
  with pytest.raises(TypeError):
    RelatedEntry(RELATED_PALACE, 1) # type: ignore[arg-type]


def test_transits_flip_palace_tougan_verdicts() -> None:
  # Male chart born 2000-01-09 12:00 (己卯丁丑丙寅甲午): the chosen 岁运 really flip the verdict.
  c = chart_from('2000-01-09 12:00', 'male')

  def verdict(criterion_id: str, year: int | None) -> ContextResult:
    profile = RelationshipProfile('natal') if year is None else RelationshipProfile(
      'natal_and_transits', TransitCoordinate('at_year', gz_year=year), (TransitKind.DAYUN, TransitKind.LIUNIAN),
    )
    return evaluate_context(c, criterion_id=criterion_id, profile=profile)

  # 宫刑冲: NOT at birth; SAT in 2016 (乙亥大运、丙申流年, 申寅刑冲); NOT again in 2021／2024.
  assert verdict(PALACE, None).criterion.status == 'NOT_SATISFIED'
  flipped = verdict(PALACE, 2016)
  assert flipped.criterion.status == 'SATISFIED' and flipped.criterion.reason == 'premise_satisfied'
  assert flipped.criterion.scope_complete is True
  assert dict(flipped.criterion.observations) == {'day_pillar_in_chong': True, 'day_pillar_in_xing': True}
  assert flipped.relationship is not None and flipped.relationship.transits is not None
  assert flipped.relationship.transits.json == {'dayun': '乙亥', 'liunian': '丙申'}
  for year in (2021, 2024):
    stayed = verdict(PALACE, year)
    assert stayed.criterion.status == 'NOT_SATISFIED' and stayed.criterion.scope_complete is True
  # 透干: NOT at birth (辛 only hidden in 丑); SAT in 2021 (甲戌大运、辛丑流年, 辛明透); NOT again in 2024.
  assert verdict(TOUGAN, None).criterion.status == 'NOT_SATISFIED'
  assert verdict(TOUGAN, 2021).criterion.status == 'SATISFIED'
  assert verdict(TOUGAN, 2024).criterion.status == 'NOT_SATISFIED'
  for result in (flipped, verdict(PALACE, 2024), verdict(TOUGAN, 2021)):
    assert ContextResult.from_json(result.export_json()) == result


def test_render_labels_categories_scopes() -> None:
  # Sections and categories asserted by value: a combo in both 宫 and 星 categories is listed with each label, not just the section headers.
  natal = rel_match(PALACE, birth='2000-01-01 12:00')
  rendered = natal.render()
  assert (
    '证据：原局内部；宫·刑：2:戊午、3:戊午；宫·冲：1:丙子、2:戊午；宫·破：0:己卯、2:戊午；'
    '宫·生：0:己卯、2:戊午；宫·克：1:丙子、2:戊午；星·刑：0:己卯、1:丙子；星·冲：1:丙子、2:戊午；'
    '星·冲：1:丙子、3:戊午；星·生：0:己卯、1:丙子；星·克：1:丙子、2:戊午；星·克：1:丙子、3:戊午'
  ) in rendered
  assert '证据：原局×岁运；无' in rendered and '证据：岁运内部；无' in rendered
  # Cross-group combos land in the 原局×岁运 section; the 2016 岁运 flips the 宫刑冲 criterion from NOT to SAT.
  transits = evaluate_context(chart_from('2000-01-09 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2016), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ))
  rendered = transits.render()
  assert (
    '证据：原局×岁运；宫·六合：2:丙寅、4:乙亥；宫·刑：2:丙寅、5:丙申；宫·冲：2:丙寅、5:丙申；'
    '宫·破：2:丙寅、4:乙亥；宫·生：2:丙寅、4:乙亥；宫·克：2:丙寅、5:丙申'
  ) in rendered
  # 明干 category: 辛 shows in the 2021 辛丑流年, so transit 明干 combos carry the 「明干」 label; pure-transit combos land in the 岁运内部 section.
  toug = evaluate_context(chart_from('2000-01-09 12:00', 'male'), criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2021), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ))
  rendered = toug.render()
  assert '明干·合：2:丙寅、5:辛丑' in rendered
  assert '明干·生：0:己卯、5:辛丑' in rendered
  assert rendered.count('明干·克：') == 4
  assert '证据：岁运内部；明干·克：4:甲戌、5:辛丑' in rendered


def test_cross_group_gong_precise_participants() -> None:
  # Male chart 戊寅己未甲申甲戌 (1998-08-05 20:00): at_year 2054 (干支年 label, 甲戌流年) queried for real.
  c = chart_from('1998-08-05 20:00', 'male')
  result = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2054), (TransitKind.LIUNIAN,),
  ), include_reference_only=True)
  assert result.criterion.status == 'SATISFIED' and result.criterion.scope_complete is True
  evidence = result.relationship
  assert evidence is not None and evidence.transits is not None
  assert evidence.transits.json == {'liunian': '甲戌'}
  # 拱会 is exactly 原局内部 {2,3} and 原局×岁运 {2,4}; index 2 is the day pillar 甲申,
  # index 4 is the 甲戌流年 chosen via the at_year entry (first item of the only requested kind; transit indexes start at 4).
  assert [sorted(o.index for o in combo) for combo in evidence.house_relations[DizhiRelation.拱会]] == [[2, 3], [2, 4]]
  participants = {
    occurrence.index: str(occurrence.ganzhi)
    for combo in evidence.house_relations[DizhiRelation.拱会]
    for occurrence in combo
  }
  assert participants == {2: '甲申', 3: '甲戌', 4: '甲戌'}
  assert ContextResult.from_json(result.export_json()) == result


def test_yinyanggan_evaluation_export_restore() -> None:
  # Male chart with 乙 day master (2000-01-08 12:00, 己卯丁丑乙丑壬午): the 阴阳干读法 targets 己 (丑、未),
  # and the non-default definition keeps its input identity across evaluation, export, and restoration.
  c = BaziChart(Bazi.create('2000-01-08 12:00', 'male', BaziConfig(school=BaziSchool(peiou_xing_def=PeiouXingDef.YINYANGGAN))))
  result = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ))
  assert result.criterion.status == 'SATISFIED' and result.criterion.reason == 'premise_satisfied'
  evidence = result.relationship
  assert evidence is not None
  assert evidence.star_target.tiangan is Tiangan.己 and evidence.star_target.dizhi == (_Dizhi.丑, _Dizhi.未)
  assert json.loads(result.input_json)['config']['school']['peiou_xing_def'] == 'YINYANGGAN'
  restored = ContextResult.from_json(result.export_json())
  assert restored == result
  assert json.loads(restored.input_json)['config']['school']['peiou_xing_def'] == 'YINYANGGAN'


def test_location_chart_evaluation_roundtrip() -> None:
  # Location chart (真太阳时) combined with a 婚恋 profile: at_year evaluation and record round-trip.
  c = BaziChart(Bazi.create(
    '2024-01-01T12:00:00+14:00', 'male',
    BaziConfig.from_values(precision='minute'), longitude=-157.4,
  ))
  result = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ))
  assert result.criterion.status == 'SATISFIED' and result.criterion.scope_complete is True
  assert 'time_basis' in result.input_json
  restored = ContextResult.from_json(result.export_json())
  assert restored == result and restored.render() == result.render()
