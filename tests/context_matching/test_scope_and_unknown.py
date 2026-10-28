# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest
from typing import get_args

from bazi.context_matching import NatalObservation, LiunianObservation, CriterionReason, _CRITERIA
from bazi.defines import Zhu, Ganzhi
from bazi.transit_chart import TransitChart
from bazi.transits import TransitSet

from matching_samples import FEMALE, LEGAL, RELATIONSHIP, match, record
from matching_samples import occurrences


@pytest.mark.parametrize('day,year,reason', [
  (1, None, 'missing_transit_coordinate'), (3, None, 'missing_transit_coordinate'),
  (1, 1998, 'transit_unavailable'), (1, 0, 'transit_unavailable'), (1, -1, 'transit_unavailable'),
])
def test_incomplete_scope_beats_partial_natal(day: int, year: int | None, reason: str) -> None:
  result = match(day, observation=LiunianObservation(year))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == reason
  assert result.criterion.scope_complete is False
  assert all(isinstance(o.position, Zhu) for o in occurrences(result))
  assert result.criterion.observations['observed_coexistence'] is (day == 3)
  assert result.reference_ids == LEGAL
  assert result.render().count('前提判别：UNKNOWN') == 2


def test_render_distinguishes_unused_missing_year() -> None:
  for observation, scope_line in (
    (NatalObservation(), '范围：全部明藏干；natal'),
    (LiunianObservation(), '范围：全部明藏干；natal_and_liunian；干支年=未提供'),
    (LiunianObservation(2024), '范围：全部明藏干；natal_and_liunian；干支年=2024'),
  ):
    result = match(observation=observation)
    rendered = result.render()
    assert rendered.splitlines()[1] == scope_line
    natal_lines = tuple(line for line in rendered.splitlines() if line.startswith('证据：natal.'))
    assert natal_lines and all('kind=' not in line and '干支年=' not in line for line in natal_lines)
    if isinstance(observation, LiunianObservation) and observation.ganzhi_year is None:
      assert 'UNKNOWN；missing_transit_coordinate；scope_complete=False' in rendered
    if isinstance(observation, LiunianObservation) and observation.ganzhi_year == 2024:
      assert '；kind=liunian；干支年=2024' in rendered
    assert result.render() == rendered


def test_unavailable_kind_unknown_errors_surface(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(TransitChart, 'at_year', lambda self, year: TransitSet(dayun=Ganzhi.from_str('甲辰')))
  result = match(observation=LiunianObservation(2024))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == 'transit_unavailable'
  def broken(self: TransitChart, year: int) -> TransitSet:
    raise ValueError('A programming error, not unavailability')
  monkeypatch.setattr(TransitChart, 'at_year', broken)
  with pytest.raises(ValueError, match='programming error'):
    match(observation=LiunianObservation(2024))


@pytest.mark.parametrize('criterion_id,gender,year,reason', [
  (FEMALE, 'female', None, 'missing_transit_coordinate'),
  (FEMALE, 'male', None, 'missing_transit_coordinate'),
  (FEMALE, 'female', 1998, 'transit_unavailable'),
  (FEMALE, 'male', 1998, 'transit_unavailable'),
])
def test_incomplete_scope_reason_precedence(criterion_id: str, gender: str, year: int | None, reason: str) -> None:
  result = match(gender=gender, criterion_id=criterion_id, observation=LiunianObservation(year))
  assert result.criterion.status == 'UNKNOWN'
  assert result.criterion.reason == reason and result.criterion.scope_complete is False
  assert result.reference_ids == RELATIONSHIP
  assert result.render().count('前提判别：UNKNOWN') == 2
  assert all(isinstance(o.position, Zhu) for o in occurrences(result))


def test_scope_matrix_covers_legal_reasons() -> None:
  results = [
    (observation, record(criterion_id, observation, day, gender))
    for criterion_id, info in _CRITERIA.items() if info.analysis_kind == 'context'
    for observation in (NatalObservation(), LiunianObservation(2024), LiunianObservation(), LiunianObservation(1998))
    for day, gender in ((3, 'female'), (5, 'male'))
  ]
  assert all(isinstance(result.evidence, tuple) for _, result in results)
  assert {p.scope for p, r in results if r.criterion.scope_complete} == {'natal', 'natal_and_liunian'}
  assert {r.criterion.reason for _, r in results} == set(get_args(CriterionReason))
