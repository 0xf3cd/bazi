# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import NatalObservation, LiunianObservation, LiunianPosition, CriterionResult, evaluate_context
from bazi.common import frozendict
from bazi.defines import Zhu, TianganLayer, Shishen

from matching_samples import GUANSHA, FEMALE, LEGAL, RELATIONSHIP, chart, match
from matching_samples import occurrences


def test_literal_witnesses_and_negative_control() -> None:
  result = match()
  assert tuple(map(str, result.bazi.pillars)) == ('己卯', '丙子', '庚申', '壬午')
  # This oracle is a literal ordered inventory, not a call to the production classifier.
  expected = (
    ('年', 0, '己卯', '明干', '己', '正印'),
    ('年', 0, '己卯', '藏干', '乙', '正财'),
    ('月', 1, '丙子', '明干', '丙', '七杀'),
    ('月', 1, '丙子', '藏干', '癸', '伤官'),
    ('日', 2, '庚申', '藏干', '庚', '比肩'),
    ('日', 2, '庚申', '藏干', '壬', '食神'),
    ('日', 2, '庚申', '藏干', '戊', '偏印'),
    ('时', 3, '壬午', '明干', '壬', '食神'),
    ('时', 3, '壬午', '藏干', '丁', '正官'),
    ('时', 3, '壬午', '藏干', '己', '正印'),
  )
  assert tuple((str(o.position), o.index, str(o.ganzhi), str(o.layer), str(o.stem), str(o.shishen)) for o in occurrences(result)) == expected
  assert all(isinstance(o.position, Zhu) for o in occurrences(result))
  assert any(line.startswith('证据：natal.月；') for line in result.render().splitlines())
  assert result.criterion.status == 'SATISFIED' and result.criterion.scope_complete
  assert result.criterion.reason == 'premise_satisfied'
  assert result.reference_ids == LEGAL
  visible = {o.shishen for o in occurrences(result) if o.layer is TianganLayer.明干}
  assert not {Shishen.正官, Shishen.七杀} <= visible
  assert chart().shishen.day.tiangan is None


def test_non_main_hidden_stem_is_in_scope() -> None:
  # 辰藏乙 is secondary qi: a LIUNIAN must retain it, independently of its percentage.
  result = match(1, observation=LiunianObservation(2024))
  assert tuple((str(o.stem), str(o.shishen)) for o in occurrences(result) if isinstance(o.position, LiunianPosition) and o.layer is TianganLayer.藏干) == (
    ('戊', '比肩'), ('乙', '正官'), ('癸', '正财'),
  )
  assert result.criterion.status == 'SATISFIED'


def test_duplicate_pillars_keep_all_occurrences() -> None:
  result = match(1)
  assert tuple(map(str, result.bazi.pillars)) == ('己卯', '丙子', '戊午', '戊午')
  repeated = [(o.position, o.index, str(o.ganzhi), str(o.stem)) for o in occurrences(result) if o.layer is TianganLayer.藏干 and o.ganzhi.dizhi.name == 'WU']
  assert repeated == [(Zhu.日, 2, '戊午', '丁'), (Zhu.日, 2, '戊午', '己'), (Zhu.时, 3, '戊午', '丁'), (Zhu.时, 3, '戊午', '己')]
  assert result.criterion.status == 'NOT_SATISFIED'
  assert result.criterion.reason == 'required_classification_absent'
  assert len(occurrences(result)) == 9


def test_visible_guansha_satisfies_premise() -> None:
  result = evaluate_context(chart(5, hour=16), criterion_id=GUANSHA, observation=NatalObservation(), include_reference_only=True)
  assert tuple(map(str, result.bazi.pillars)) == ('己卯', '丙子', '壬戌', '戊申')
  assert {(o.position, str(o.stem), str(o.shishen)) for o in occurrences(result) if o.layer is TianganLayer.明干 and o.shishen in (Shishen.正官, Shishen.七杀)} == {
    (Zhu.年, '己', '正官'), (Zhu.时, '戊', '七杀'),
  }


def test_female_premise_rejects_male_chart() -> None:
  female, male = match(criterion_id=FEMALE), match(gender='male', criterion_id=FEMALE)
  assert female.criterion.status == 'SATISFIED'
  assert male.criterion.status == 'NOT_SATISFIED' and male.criterion.reason == 'female_gate_false'
  assert male.criterion.observations['observed_coexistence'] is True
  assert male.criterion.observations['female'] is False
  assert female.reference_ids == male.reference_ids == RELATIONSHIP
  assert match(gender='male').criterion.status == 'SATISFIED'


def test_liunian_kind_and_cycle_identity() -> None:
  natal = match(1)
  first = match(1, observation=LiunianObservation(2024))
  next_cycle = match(1, observation=LiunianObservation(2084))
  assert natal.criterion.status == 'NOT_SATISFIED'
  assert first.criterion.status == next_cycle.criterion.status == 'SATISFIED'
  assert first != next_cycle
  assert isinstance(first.observation, LiunianObservation) and isinstance(next_cycle.observation, LiunianObservation)
  assert first.observation.ganzhi_year == 2024 and next_cycle.observation.ganzhi_year == 2084
  for result, year in ((first, 2024), (next_cycle, 2084)):
    transit = [o for o in occurrences(result) if isinstance(o.position, LiunianPosition)]
    assert len(transit) == 4
    assert all(o.index == 4 and o.position == LiunianPosition(year) and str(o.ganzhi) == '甲辰' for o in transit)
    assert [(str(o.layer), str(o.stem), str(o.shishen)) for o in transit] == [
      ('明干', '甲', '七杀'), ('藏干', '戊', '比肩'), ('藏干', '乙', '正官'), ('藏干', '癸', '正财'),
    ]
  assert [(o.index, str(o.stem), str(o.shishen)) for o in occurrences(first)] == [(o.index, str(o.stem), str(o.shishen)) for o in occurrences(next_cycle)]


def test_liunian_label_has_no_calendar_cutoff() -> None:
  # at_year has no calendar-data upper cutoff: preserve that existing label contract.
  assert match(1, observation=LiunianObservation(10000)).criterion.scope_complete


def test_evidence_keeps_year_kind_input() -> None:
  result = match(1, observation=LiunianObservation(2024))
  assert result.observation == LiunianObservation(2024)
  assert result.bazi == chart(1).bazi
  assert len(occurrences(result)) == 13
  assert tuple((o.position, str(o.ganzhi), str(o.layer), str(o.stem), str(o.shishen)) for o in occurrences(result)[-3:]) == (
    (LiunianPosition(2024), '甲辰', '藏干', '戊', '比肩'),
    (LiunianPosition(2024), '甲辰', '藏干', '乙', '正官'),
    (LiunianPosition(2024), '甲辰', '藏干', '癸', '正财'),
  )


def test_historical_default_observations() -> None:
  # Literal criterion and occurrences from ddfe16e7c51d695167b09cc4c2f64ba46e7565c3.
  result = evaluate_context(
    BaziChart(Bazi.create('2000-01-01T12:00:00', 'male')),
    criterion_id=GUANSHA, observation=NatalObservation(),
  )
  assert result.criterion == CriterionResult(
    GUANSHA, 'required_classification_absent', frozendict({'observed_coexistence': False, 'female': False}),
  )
  assert result.criterion.definition == '选定范围内正官与七杀各至少出现一次。'
  assert result.criterion.status == 'NOT_SATISFIED' and result.criterion.scope_complete
  assert tuple((o.position, str(o.ganzhi), str(o.layer), str(o.stem), str(o.shishen)) for o in occurrences(result)) == (
    (Zhu.年, '己卯', '明干', '己', '劫财'),
    (Zhu.年, '己卯', '藏干', '乙', '正官'),
    (Zhu.月, '丙子', '明干', '丙', '偏印'),
    (Zhu.月, '丙子', '藏干', '癸', '正财'),
    (Zhu.日, '戊午', '藏干', '丁', '正印'),
    (Zhu.日, '戊午', '藏干', '己', '劫财'),
    (Zhu.时, '戊午', '明干', '戊', '比肩'),
    (Zhu.时, '戊午', '藏干', '丁', '正印'),
    (Zhu.时, '戊午', '藏干', '己', '劫财'),
  )
