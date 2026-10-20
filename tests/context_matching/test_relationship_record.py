# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import replace
from typing import Any

import pytest

from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context, RelationshipProfile, TransitCoordinate
from bazi.transits import TransitKind

from datetime import date as _date_module  # The construction-time matrix needs the native date type.

from bazi.defines import Dizhi as _Dizhi

from matching_samples import chart, match, PALACE, TOUGAN, RELATED_TOUGAN, rel_match, chart_from


def test_record_roundtrip_and_rejections() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  result = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_month', gz_year=2024, gz_month=_Dizhi.辰), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ), include_reference_only=True)
  data = json.loads(result.export_json())
  assert data['record_version'] == 4
  assert data['profile'] == {
    'scope': 'natal_and_transits',
    'coordinate': {'entry': 'at_month', 'gz_year': 2024, 'gz_month': '辰', 'solar_date': None, 'solar_moment': None},
    'kinds': ['dayun', 'liunian'],
  }
  assert data['occurrences'] == [] and data['entries'] == []
  assert data['related'] == [{'claim_id': RELATED_TOUGAN, 'recognized': True}]
  assert data['relationship']['star_target'] == {'tiangan': '癸', 'dizhi': ['子']}
  assert data['relationship']['transits'] == {'dayun': '甲戌', 'liunian': '甲辰'}
  assert ContextResult.from_json(result.export_json()) == result
  assert ContextResult.from_json(result.export_json()).render() == result.render()
  rendered = result.render()
  assert '范围：natal_and_transits；坐标=at_month；干支年=2024；干支月=辰；' in rendered
  assert '请求种类=[dayun,liunian]；取得种类=[dayun,liunian]；未取得种类=[]' in rendered

  # Direct evaluation of at_date and at_moment coordinates: date queries really work; the DAY-precision moment entry is unavailable.
  at_date = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_date', solar_date=_date_module(2024, 4, 10)),
    (TransitKind.LIUNIAN, TransitKind.LIUYUE, TransitKind.LIURI),
  ))
  assert at_date.criterion.scope_complete is True
  assert at_date.relationship is not None and at_date.relationship.transits is not None
  assert json.loads(at_date.export_json())['profile']['coordinate']['solar_date'] == '2024-04-10'
  assert ContextResult.from_json(at_date.export_json()) == at_date
  assert '坐标=at_date；公历日=2024-04-10' in at_date.render()

  # Non-canonical spellings rejected case by case: compact dates, space-separated moments, microsecond
  # abbreviations, offsets, branch-name readback, unordered kinds, non-negative indexes, bool indexes and bool years.
  def __mutate(section: str, key: Any, value: Any) -> str:
    mutated = json.loads(json.dumps(data))
    if section == 'profile.coordinate':
      mutated['profile']['coordinate'][key] = value
    elif section == 'profile':
      mutated['profile'][key] = value
    elif section == 'relationship':
      mutated['relationship'][key] = value
    return json.dumps(mutated)

  for section, key, value in (
    ('profile.coordinate', 'solar_date', '20240410'),
    ('profile.coordinate', 'solar_moment', '2024-04-10 12:00:00'),
    ('profile.coordinate', 'gz_year', True),
    ('profile', 'kinds', ['liunian', 'dayun']),
    ('profile', 'kinds', ['dayun', 'dayun', 'liunian']),
    ('profile', 'kinds', ['dayun', 'bogus']),
  ):
    with pytest.raises((TypeError, ValueError)):
      ContextResult.from_json(__mutate(section, key, value))

  # at_year records have mutually exclusive entry fields: injecting an at_month month into an at_year record must be rejected by the coordinate construction.
  year_result = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ), include_reference_only=True)
  year_data = json.loads(year_result.export_json())
  year_data['profile']['coordinate']['gz_month'] = '辰'
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(year_data))

  # Evidence combo indexes: bool and negative values rejected (combo members are {index, ganzhi} records).
  evidence = json.loads(json.dumps(data))
  star_relations = evidence['relationship']['star_relations']
  first_key = next(iter(star_relations))
  star_relations[first_key][0][0]['index'] = True
  with pytest.raises(TypeError):
    ContextResult.from_json(json.dumps(evidence))
  star_relations[first_key][0][0]['index'] = -1
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(evidence))


def test_record_version_before_keys_old_school() -> None:
  # Real v2 shape: a 官杀 record with the old key set (no relationship/related); the version check runs
  # before the key-set check, so the rejection is about the version, not key differences. Not a current record with a hand-edited version number.
  context_record = json.loads(match().export_json())
  v2_text = json.dumps({
    key: value for key, value in context_record.items() if key not in ('relationship', 'related')
  } | {'record_version': 2}, ensure_ascii=False)
  with pytest.raises(ValueError, match='Unsupported record version'):
    ContextResult.from_json(v2_text)

  # Current record version plus an old school (missing peiou_xing_def): a different trigger path from the case above.
  legacy_school = json.loads(match().export_json())
  config_block: dict[str, Any] = legacy_school['input']['config']
  config_block['school'] = {
    key: value for key, value in config_block['school'].items() if key != 'peiou_xing_def'
  }
  with pytest.raises(ValueError, match='Missing school field: peiou_xing_def'):
    ContextResult.from_json(json.dumps(legacy_school))

  # Third entry point: an old chart JSON missing that field hits the same message via BaziChart.from_json.
  chart_json: dict[str, Any] = dict(chart().json)
  chart_json['school'] = {
    key: value for key, value in chart_json['school'].items() if key != 'peiou_xing_def'
  }
  with pytest.raises(ValueError, match='Missing school field: peiou_xing_def'):
    BaziChart.from_json(chart_json)


def test_record_structural_constraints() -> None:
  result = rel_match(TOUGAN, birth='2000-01-29 06:00', include_reference_only=True)
  # RelationshipEvidence type gates and mutually exclusive combos are rejected, as is a criterion/profile kind mismatch.
  with pytest.raises(TypeError):
    replace(result, relationship=object()) # type: ignore[arg-type]
  with pytest.raises(ValueError, match='profile'):
    replace(result, profile=ContextProfile('natal'))
  with pytest.raises(ValueError):
    replace(result, occurrences=result_with_occurrences())
  guansha = match()
  with pytest.raises(ValueError, match='Context profile cannot carry relationship evidence'):
    replace(guansha, relationship=result.relationship)
  with pytest.raises(ValueError, match='Premise criterion cannot carry condition references'):
    replace(guansha, related=result.related)
  # A natal-scope record carrying obtained 岁运 must be rejected.
  carrying = json.loads(result.export_json())
  carrying['relationship']['transits'] = {'liunian': '甲辰'}
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(carrying))
  # Obtained kinds beyond the requested set / indexes beyond the query sequence / scope_complete without all requested kinds.
  transiting = evaluate_context(chart_from('2000-01-01 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ))
  exceeded = json.loads(transiting.export_json())
  exceeded['profile']['kinds'] = ['dayun']
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(exceeded))
  indexed = json.loads(result.export_json())
  indexed['relationship']['house_relations'] = {'冲': [[{'index': 9, 'ganzhi': '甲子'}]]}
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(indexed))
  # natal scope with scope_complete=True is legal; flipping it to True when kinds are missing under natal_and_transits must be rejected.
  partial_record = evaluate_context(chart_from('2000-01-01 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN),
  ))
  incomplete = json.loads(partial_record.export_json())
  assert incomplete['criterion']['scope_complete'] is False
  incomplete['criterion']['scope_complete'] = True
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(incomplete))
  # related referencing a missing knowledge entry is rejected.
  missing_related = json.loads(result.export_json())
  missing_related['related'] = [{'claim_id': 'unknown.claim', 'recognized': True}]
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(missing_related))


def test_zero_obtained_complete_scope_rejected() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  # Zero obtained: a no-coordinate record forged to scope_complete=True/SATISFIED must be rejected (via both direct construction and from_json).
  no_coordinate = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile('natal_and_transits', None, (TransitKind.LIUNIAN,)))
  assert no_coordinate.relationship is not None and no_coordinate.relationship.transits is None
  forged = replace(
    no_coordinate.criterion,
    status='SATISFIED', reason='premise_satisfied', scope_complete=True,
  )
  with pytest.raises(ValueError, match='Complete scope'):
    replace(no_coordinate, criterion=forged)
  record = json.loads(no_coordinate.export_json())
  record['criterion'].update(status='SATISFIED', reason='premise_satisfied', scope_complete=True)
  with pytest.raises(ValueError, match='Complete scope'):
    ContextResult.from_json(json.dumps(record))
  # Partially obtained: requesting {小运, 大运} obtains only 大运; scope_complete=True is likewise rejected.
  partial = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN),
  ))
  incomplete = json.loads(partial.export_json())
  incomplete['criterion'].update(status='SATISFIED', reason='premise_satisfied', scope_complete=True)
  with pytest.raises(ValueError, match='Complete scope'):
    ContextResult.from_json(json.dumps(incomplete))
  # Obtained 岁运 but coordinate removed: complete scope must be rejected.
  complete = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ))
  assert complete.criterion.scope_complete is True
  no_coord_record = json.loads(complete.export_json())
  no_coord_record['profile']['coordinate'] = None
  with pytest.raises(ValueError, match='Complete scope'):
    ContextResult.from_json(json.dumps(no_coord_record))
  # Normal missing-data UNKNOWN records (scope_complete=False) still round-trip legally.
  for result in (no_coordinate, partial):
    assert result.criterion.scope_complete is False
    assert ContextResult.from_json(result.export_json()) == result


def test_combo_order_rejections_absorptions() -> None:
  result = rel_match(PALACE, birth='2000-01-01 12:00')
  data = json.loads(result.export_json())
  star_chong = data['relationship']['star_relations']['冲']
  assert len(star_chong) == 2
  # Combo outer order reversed: disagrees with the exported ascending index tuples; rejected.
  reversed_record = json.loads(json.dumps(data))
  reversed_record['relationship']['star_relations']['冲'] = list(reversed(star_chong))
  with pytest.raises(ValueError, match='canonical order'):
    ContextResult.from_json(json.dumps(reversed_record))
  # Shuffled combo members and relation keys are absorbed by the immutable sets/maps; round-trip stays equal.
  shuffled = json.loads(json.dumps(data))
  shuffled['relationship']['star_relations']['冲'] = [list(reversed(combo)) for combo in star_chong]
  shuffled['relationship']['star_relations'] = dict(
    reversed(list(shuffled['relationship']['star_relations'].items()))
  )
  assert ContextResult.from_json(json.dumps(shuffled)) == result
  assert ContextResult.from_json(json.dumps(data)) == result
  # appearances keep prior behavior: a record with swapped appearance items still round-trips equal by itself.
  swapping = rel_match(TOUGAN, birth='2000-01-29 06:00')
  swapped = json.loads(swapping.export_json())
  swapped['relationship']['appearances'] = list(reversed(swapped['relationship']['appearances']))
  restored = ContextResult.from_json(json.dumps(swapped))
  assert restored != swapping # different appearance order is a different record.
  assert ContextResult.from_json(restored.export_json()) == restored


def result_with_occurrences() -> tuple[Any, ...]:
  occurrence = match().occurrences[0]
  return (occurrence,)
