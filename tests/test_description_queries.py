# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError, fields, replace
from collections.abc import Callable

import pytest

from bazi.defines import Shishen, Tiangan
from bazi.descriptions import (
  DescriptionClaim, DescriptionClaims, DescriptionCondition, DescriptionOutput,
  DescriptionSource, ShishenDescription, TianganDescription,
  DescriptionSourceRecord, DescriptionLineage,
)
from bazi.interpreter import Interpreter


@pytest.mark.parametrize(('query', 'text_query', 'subjects', 'counts'), [
  (Interpreter.query_shishen, Interpreter.interpret_shishen, tuple(Shishen), (9, 219)),
  (Interpreter.query_tiangan, Interpreter.interpret_tiangan, tuple(Tiangan), (10, 72)),
])
def test_structured_queries_conserve_text_order_and_metadata(
  query: Callable[..., DescriptionClaims],
  text_query: Callable[..., ShishenDescription | TianganDescription],
  subjects: tuple[Shishen | Tiangan, ...],
  counts: tuple[int, int],
) -> None:
  for include_reference_only, expected_count in zip((False, True), counts, strict=True):
    total = 0
    ids: set[str] = set()
    for subject in subjects:
      result = query(subject, include_reference_only=include_reference_only)
      texts = text_query(subject, include_reference_only=include_reference_only)
      assert {field: [claim.text for claim in claims] for field, claims in result.items()} == texts
      for claims in result.values():
        assert isinstance(claims, tuple)
        total += len(claims)
        for claim in claims:
          assert isinstance(claim, DescriptionClaim)
          assert claim.claim_id not in ids
          ids.add(claim.claim_id)
          if not include_reference_only:
            assert claim.output is DescriptionOutput.DEFAULT
            assert not claim.conditions
          for source_id in claim.sources:
            source = Interpreter.query_source(source_id)
            assert source.work and source.locator and source.url
            assert source.supports and source.limitations
    assert total == expected_count


def test_results_are_transitively_immutable() -> None:
  result = Interpreter.query_tiangan(Tiangan.丁, include_reference_only=True)
  with pytest.raises(TypeError):
    result['general'] = () # type: ignore[index]
  claim = result['general'][0]
  with pytest.raises(FrozenInstanceError):
    claim.text = 'changed' # type: ignore[misc]
  source = Interpreter.query_source(claim.sources[0])
  with pytest.raises(FrozenInstanceError):
    source.work = 'changed' # type: ignore[misc]
  assert hash(result) == hash(Interpreter.query_tiangan(Tiangan.丁, include_reference_only=True))


def test_reference_state_and_source_boundaries_are_retained() -> None:
  claims = Interpreter.query_shishen(Shishen.比肩, include_reference_only=True)
  unverified = next(claim for claim in claims['in_good_status'] if not claim.sources)
  assert unverified.attribution == 'Legacy corpus; source unverified'
  assert unverified.output is DescriptionOutput.REFERENCE_ONLY
  assert unverified.conditions == (DescriptionCondition.CHART_CONTEXT_REQUIRED,)
  ding = Interpreter.query_tiangan(Tiangan.丁, include_reference_only=True)
  historical = next(claim for claim in ding['general'] if claim.claim_id == 'tiangan.ding.lamp_symbol')
  assert historical.output is DescriptionOutput.REFERENCE_ONLY
  assert historical.sources == (DescriptionSource.YUANHAI_ZIPING_STEM_SYMBOLS_P70,)
  witness = Interpreter.query_source(historical.sources[0])
  assert 'p. 70' in witness.locator
  assert 'personality' in witness.limitations


@pytest.mark.parametrize('bad_flag', [None, 0, 1, 'true', ()])
def test_query_flags_reject_non_bool(bad_flag: object) -> None:
  with pytest.raises(TypeError, match='Expected bool'):
    Interpreter.query_shishen(Shishen.食神, include_reference_only=bad_flag) # type: ignore[arg-type]
  with pytest.raises(TypeError, match='Expected bool'):
    Interpreter.query_tiangan(Tiangan.甲, include_reference_only=bad_flag) # type: ignore[arg-type]


def test_query_inputs_and_keyword_only_contract() -> None:
  with pytest.raises(TypeError, match='Expected Shishen'):
    Interpreter.query_shishen('食神') # type: ignore[arg-type]
  with pytest.raises(TypeError, match='Expected Tiangan'):
    Interpreter.query_tiangan('甲') # type: ignore[arg-type]
  with pytest.raises(TypeError, match='Expected DescriptionSource'):
    Interpreter.query_source('editorial') # type: ignore[arg-type]
  with pytest.raises(TypeError):
    Interpreter.query_shishen(Shishen.食神, True) # type: ignore[call-arg]
  with pytest.raises(TypeError):
    Interpreter.query_tiangan(Tiangan.甲, True) # type: ignore[call-arg]


@pytest.mark.parametrize(('field', 'value'), [
  ('claim_id', 1), ('text', None), ('attribution', False), ('output', 'default'),
  ('sources', []), ('sources', ('editorial',)),
  ('conditions', []), ('conditions', ('chart_context_required',)),
])
def test_claim_constructor_rejects_invalid_types(field: str, value: object) -> None:
  claim = Interpreter.query_tiangan(Tiangan.丁)['general'][0]
  with pytest.raises(TypeError):
    replace(claim, **{field: value}) # type: ignore[arg-type] # Deliberately invalid constructor fields.


def test_source_constructor_checks_every_declared_field() -> None:
  for source_id in DescriptionSource:
    record = Interpreter.query_source(source_id)
    assert isinstance(record, DescriptionSourceRecord)
    assert isinstance(record.lineage, DescriptionLineage)
    for field in fields(record):
      with pytest.raises(TypeError):
        replace(record, **{field.name: object()}) # type: ignore[arg-type] # Probe every declared type gate.
