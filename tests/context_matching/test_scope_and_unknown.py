# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest

from bazi.context_matching import ContextProfile, ContextResult
from bazi.defines import Ganzhi
from bazi.transit_chart import TransitChart
from bazi.transits import TransitSet

from matching_samples import FEMALE, match


@pytest.mark.parametrize('day,year,reason', [
  (1, None, 'missing_transit_coordinate'), (3, None, 'missing_transit_coordinate'),
  (1, 1998, 'transit_unavailable'), (1, 0, 'transit_unavailable'), (1, -1, 'transit_unavailable'),
])
def test_incomplete_scope_beats_partial_natal(day: int, year: int | None, reason: str) -> None:
  result = match(day, profile=ContextProfile('natal_and_liunian', year))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == reason
  assert result.criterion.scope_complete is False
  assert all(o.origin == 'natal' for o in result.occurrences)
  assert result.criterion.observations['observed_coexistence'] is (day == 3)
  assert all(m.status == 'UNKNOWN' for m in result.entries)
  assert ContextResult.from_json(result.export_json()) == result


def test_unavailable_kind_unknown_errors_surface(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(TransitChart, 'at_year', lambda self, year: TransitSet(dayun=Ganzhi.from_str('甲辰')))
  result = match(profile=ContextProfile('natal_and_liunian', 2024))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == 'transit_unavailable'
  def broken(self: TransitChart, year: int) -> TransitSet:
    raise ValueError('A programming error, not unavailability')
  monkeypatch.setattr(TransitChart, 'at_year', broken)
  with pytest.raises(ValueError, match='programming error'):
    match(profile=ContextProfile('natal_and_liunian', 2024))


@pytest.mark.parametrize('criterion_id,gender,year,reason', [
  (FEMALE, 'female', None, 'missing_transit_coordinate'),
  (FEMALE, 'male', None, 'missing_transit_coordinate'),
  (FEMALE, 'female', 1998, 'transit_unavailable'),
  (FEMALE, 'male', 1998, 'transit_unavailable'),
])
def test_incomplete_scope_reason_precedence(criterion_id: str, gender: str, year: int | None, reason: str) -> None:
  result = match(gender=gender, criterion_id=criterion_id, profile=ContextProfile('natal_and_liunian', year))
  assert result.criterion.status == 'UNKNOWN'
  assert result.criterion.reason == reason and result.criterion.scope_complete is False
  assert all(entry.status == 'UNKNOWN' and entry.reason == reason for entry in result.entries)
  assert all(o.origin == 'natal' for o in result.occurrences)
  assert ContextResult.from_json(result.export_json()) == result
