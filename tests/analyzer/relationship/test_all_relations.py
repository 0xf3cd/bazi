# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError
from random import Random
from typing import Any

import pytest

from bazi.analyzer.relationship import RelationshipAnalyzer, RelationParticipant, RelationPositionDiscovery
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Zhu, Tiangan, Dizhi, Ganzhi, DizhiRelation
from bazi.rules import DizhiRules
from bazi.school import BaziConfig, BaziSchool
from bazi.transits import TransitKind, TransitSet
from bazi.utils.dizhi_utils import discover_mutual_ganzhis


@pytest.mark.parametrize('anhe', list(DizhiRules.AnheDef))
@pytest.mark.parametrize('xing', list(DizhiRules.XingDef))
@pytest.mark.parametrize('gong', list(DizhiRules.GongDef))
def test_position_mapping_matches_low_level(
  anhe: DizhiRules.AnheDef,
  xing: DizhiRules.XingDef,
  gong: DizhiRules.GongDef,
) -> None:
  rng = Random(20261031)
  config = BaziConfig(school=BaziSchool(anhe_def=anhe, xing_def=xing, gong_def=gong))
  cycle = Ganzhi.list_sexagenary_cycle()
  for _ in range(30):
    chart = BaziChart(Bazi.random(config, rng=rng))
    transits = TransitSet(**{kind.value: rng.choice(cycle) for kind in reversed(tuple(TransitKind))})
    analysis = RelationshipAnalyzer(chart).transits
    old = analysis.house_relations(transits)
    low = discover_mutual_ganzhis(
      chart.bazi.pillars, transits.ganzhis, definitions=config.school.relation_definitions,
    )
    identities = (*Zhu, *(kind for kind, _ in transits.items))
    expected = {
      relation: tuple(frozenset(
        RelationParticipant(identities[item.index], item.ganzhi) for item in combo
      ) for combo in combos)
      for relation, combos in low.items()
    }
    actual = analysis.all_relations(transits)
    assert isinstance(actual, RelationPositionDiscovery)
    assert tuple(actual) == tuple(low)
    assert actual == expected
    assert analysis.house_relations(transits) == old
    for combos in actual.values():
      for combo in combos:
        assert any(isinstance(item.position, Zhu) for item in combo)
        assert any(isinstance(item.position, TransitKind) for item in combo)
        assert all(item.ganzhi == dict((*zip(Zhu, chart.bazi.pillars, strict=True), *transits.items))[item.position]
                   for item in combo)


def test_repeated_ganzhis_keep_each_position(monkeypatch: pytest.MonkeyPatch) -> None:
  chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
  natal = tuple(map(Ganzhi.from_str, ('甲子', '甲子', '庚午', '辛酉')))
  monkeypatch.setattr(Bazi, 'pillars', property(lambda _: natal))
  transits = TransitSet(dayun=Ganzhi.from_str('甲子'), liunian=Ganzhi.from_str('甲子'), liuri=Ganzhi.from_str('庚午'))
  actual = RelationshipAnalyzer(chart).transits.all_relations(transits)
  assert set(actual[DizhiRelation.冲]) == {
    frozenset((RelationParticipant(Zhu.日, natal[2]), RelationParticipant(TransitKind.DAYUN, transits.ganzhis[0]))),
    frozenset((RelationParticipant(Zhu.日, natal[2]), RelationParticipant(TransitKind.LIUNIAN, transits.ganzhis[1]))),
    frozenset((RelationParticipant(Zhu.年, natal[0]), RelationParticipant(TransitKind.LIURI, transits.ganzhis[2]))),
    frozenset((RelationParticipant(Zhu.月, natal[1]), RelationParticipant(TransitKind.LIURI, transits.ganzhis[2]))),
  }
  with pytest.raises(TypeError):
    actual[DizhiRelation.冲] = () # type: ignore[index]
  first = next(iter(actual[DizhiRelation.冲][0]))
  with pytest.raises(FrozenInstanceError):
    first.position = Zhu.年 # type: ignore[misc]


def test_all_relations_input_and_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
  chart = BaziChart(Bazi.random())
  monkeypatch.setattr(Bazi, 'pillars', property(lambda _: (Ganzhi.from_str('甲子'),) * 4))
  analysis = RelationshipAnalyzer(chart).transits
  with pytest.raises(TypeError):
    analysis.all_relations(2026) # type: ignore[arg-type]
  assert analysis.all_relations(TransitSet(liunian=Ganzhi.from_str('甲子'))) == {}


@pytest.mark.parametrize('position,ganzhi', [
  ('年', Ganzhi.from_str('甲子')), (Zhu.年, '甲子'),
  (Zhu.年, Ganzhi('甲', Dizhi.子)), (Zhu.年, Ganzhi(Tiangan.甲, '子')), # type: ignore[arg-type]
])
def test_participant_type_gates(position: Any, ganzhi: Any) -> None:
  with pytest.raises(TypeError):
    RelationParticipant(position, ganzhi)
