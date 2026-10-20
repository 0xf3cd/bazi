# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_analysis_repr.py

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.analyzer import relationship as relationship_module
from bazi.analyzer.relationship import RelationshipAnalyzer, TransitAnalysis


_ANALYSIS_TYPES = (RelationshipAnalyzer, relationship_module.AtBirthAnalysis, TransitAnalysis)


@pytest.mark.parametrize('analysis', _ANALYSIS_TYPES)
def test_repr_wraps_the_chart_summary(analysis: type) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  assert repr(analysis(chart)) == f'{analysis.__name__}({chart!r})'


@pytest.mark.parametrize('analysis', _ANALYSIS_TYPES)
@pytest.mark.parametrize('bad, hint', [
  (Bazi.create('2000-01-01 12:00', 'male'), r'wrap it with BaziChart\(bazi\)'),
  (None, r'build one with BaziChart\(Bazi.create\(birth_time, gender\)\)'),
])
def test_construction_rejects_non_charts_early(analysis: type, bad: object, hint: str) -> None:
  with pytest.raises(TypeError, match=f'^Expected BaziChart, got <class .*>; {hint}$'):
    analysis(bad)


def test_repr_does_not_build_the_analyses(monkeypatch: pytest.MonkeyPatch) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  analyzer = RelationshipAnalyzer(chart)
  monkeypatch.setattr(RelationshipAnalyzer, 'at_birth', property(lambda self: pytest.fail('built')))
  monkeypatch.setattr(RelationshipAnalyzer, 'transits', property(lambda self: pytest.fail('built')))
  assert repr(analyzer).startswith('RelationshipAnalyzer(BaziChart(')


def test_spouse_evidence_hints_on_wrong_chart() -> None:
  with pytest.raises(TypeError, match=r'^Expected BaziChart, got .*; wrap it with BaziChart\(bazi\)$'):
    relationship_module.spouse_evidence(Bazi.create('2000-01-01 12:00', 'male'), None) # type: ignore
