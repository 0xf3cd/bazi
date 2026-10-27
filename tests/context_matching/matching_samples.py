# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

# Sample charts, criterion IDs and evaluation helpers shared by the context-matching tests in this directory.
# Imported as a bare sibling module: the suite has no `__init__.py`, so pytest puts this directory on
# `sys.path`, and `from tests.<package>...` would be shadowed by a stray installed `tests` package
# (see the NOTE in `tests/calendar/test_celestial_tables.py`).

from datetime import datetime
from functools import cache
from pathlib import Path
import json
from typing import Any

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import (
  Observation, NatalObservation, ContextResult, ChartOccurrence, EntryMatch, RelatedEntry,
  PremiseMatches, ConditionReferences, evaluate_context,
)
from bazi.analyzer.relationship import RelationshipEvidence
from bazi.school import BaziConfig
from bazi.knowledge import KnowledgeBase
from bazi.transits import TransitSet


GUANSHA = 'editorial.guansha_coexistence.v1'
FEMALE = 'editorial.guansha_coexistence_female.v1'
LEGAL = ('editorial.shishen.zhengguan.legal_trouble', 'editorial.shishen.qisha.legal_trouble')
RELATIONSHIP = ('editorial.shishen.zhengguan.infidelity', 'editorial.shishen.qisha.infidelity')
DING, GENG = 'tiangan.ding_weak_and_overcontrolled', 'tiangan.geng_regulated_transit'
PIANYIN, XIAOYIN = 'shishen.pianyin_favorable_or_balanced', 'shishen.xiaoyin_duoshi'
CONDITION_CLAIMS = {
  DING: 'legacy.tiangan.ding.weak_state', GENG: 'legacy.tiangan.geng.regulated_transit',
  PIANYIN: 'legacy.shishen.SH-199', XIAOYIN: 'legacy.shishen.SH-066',
}


def chart(day: int = 3, gender: str = 'female', hour: int = 12) -> BaziChart:
  return BaziChart(Bazi.create(datetime(2000, 1, day, hour), gender, BaziConfig.from_values(backend='celestial', precision='day')))


def match(day: int = 3, gender: str = 'female', **kwargs: Any) -> ContextResult:
  options = {'criterion_id': GUANSHA, 'observation': NatalObservation(), 'include_reference_only': True, **kwargs}
  return evaluate_context(chart(day, gender), **options)


@cache
def record(criterion_id: str, observation: Observation, day: int, gender: str) -> ContextResult:
  return match(day, gender, criterion_id=criterion_id, observation=observation)


def occurrences(result: ContextResult) -> tuple[ChartOccurrence, ...]:
  assert isinstance(result.evidence, tuple)
  return result.evidence


def premise_entries(result: ContextResult) -> tuple[EntryMatch, ...]:
  assert isinstance(result.references, PremiseMatches)
  return result.references.entries


def condition_entries(result: ContextResult) -> tuple[RelatedEntry, ...]:
  assert isinstance(result.references, ConditionReferences)
  return result.references.entries


def relationship_evidence(result: ContextResult) -> RelationshipEvidence:
  assert isinstance(result.evidence, RelationshipEvidence)
  return result.evidence


def obtained_transits(result: ContextResult) -> TransitSet:
  transits = relationship_evidence(result).transits
  assert transits is not None
  return transits


class Year(int):
  pass


# #233 婚恋判据: explicit observations, missing data and three-state reference matrix.
# All cases use reproducible real birth inputs and configs; 岁运 come from real TransitChart queries by coordinate.

PALACE = 'editorial.spouse_palace_xingchong.v1'
TOUGAN = 'editorial.spouse_star_tougan.v1'
RELATED_PALACE = 'editorial.tanyuan.wife_palace_xingchong.v1'
RELATED_TOUGAN = 'editorial.tanyuan.wife_star_gantou.v1'


def rel_match(
  criterion_id: str = PALACE,
  birth: str = '2000-01-01 12:00',
  gender: str = 'male',
  **kwargs: Any,
) -> ContextResult:
  options: dict[str, Any] = {'observation': NatalObservation(), **kwargs}
  return evaluate_context(chart_from(birth, gender), criterion_id=criterion_id, **options)


def chart_from(birth: str, gender: str) -> BaziChart:
  return BaziChart(Bazi.create(birth, gender))


def load_knowledge(data: dict[str, Any], directory: Path) -> KnowledgeBase:
  source = directory / 'knowledge.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  return KnowledgeBase.load(source)
