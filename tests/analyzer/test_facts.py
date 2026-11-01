# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError, replace
from itertools import product
from typing import Any

import pytest

from bazi.analyzer.facts import TianganMatch, TianganOccurrence, TouganHit, tonggen, tougan
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Zhu, Tiangan, Dizhi, Ganzhi
from bazi.transits import TransitKind, TransitSet


HIDDEN = dict(zip(Dizhi, (
  '癸', '己癸辛', '甲丙戊', '乙', '戊乙癸', '丙戊庚',
  '丁己', '己丁乙', '庚壬戊', '辛', '戊辛丁', '壬甲',
), strict=True))
ELEMENT = {stem: index for index, stems in enumerate(('甲乙', '丙丁', '戊己', '庚辛', '壬癸')) for stem in stems}


def test_all_hidden_matches_preserve_actual_stems() -> None:
  chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
  for dizhi, target, condition in product(Dizhi, Tiangan, TianganMatch):
    transits = TransitSet(liunian=Ganzhi(Tiangan.甲, dizhi))
    positions: tuple[tuple[Zhu | TransitKind, Ganzhi], ...] = (*zip(Zhu, chart.bazi.pillars, strict=True), *transits.items)
    def matches(stem: str) -> bool:
      return (
        str(target) == stem if condition is TianganMatch.SAME_TIANGAN
        else ELEMENT[str(target)] == ELEMENT[stem]
      )
    expected_roots = tuple(
      TianganOccurrence(position, ganzhi, Tiangan.from_str(stem))
      for position, ganzhi in positions for stem in HIDDEN[ganzhi.dizhi] if matches(stem)
    )
    assert tonggen(chart, target, transits, condition=condition) == expected_roots
    expected_pairs = tuple(
      TouganHit(
        TianganOccurrence(left, hidden, target),
        TianganOccurrence(right, visible, visible.tiangan),
      )
      for left, hidden in positions if str(target) in HIDDEN[hidden.dizhi]
      for right, visible in positions if matches(str(visible.tiangan))
    )
    assert tougan(chart, target, transits, condition=condition) == expected_pairs


def test_defaults_duplicates_and_transit_kinds() -> None:
  chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
  ganzhi = Ganzhi.from_str('甲辰')
  transits = TransitSet(**{kind.value: ganzhi for kind in TransitKind})
  roots = tonggen(chart, Tiangan.甲, transits)
  assert roots == tonggen(chart, Tiangan.甲, transits, condition=TianganMatch.SAME_WUXING)
  assert tuple(hit.position for hit in roots) == tuple(TransitKind)
  assert all(hit.stem is Tiangan.乙 for hit in roots)
  assert len(set(roots)) == 5
  assert tonggen(chart, Tiangan.甲, transits, condition=TianganMatch.SAME_TIANGAN) == ()
  pairs = tougan(chart, Tiangan.乙, transits, condition=TianganMatch.SAME_WUXING)
  assert {pair.hidden.position for pair in pairs} == set(TransitKind)
  assert any(pair.hidden.position == pair.visible.position for pair in pairs)
  assert any(isinstance(pair.visible.position, Zhu) for pair in pairs)
  assert any(isinstance(pair.visible.position, TransitKind) for pair in pairs)
  assert tougan(chart, Tiangan.甲, transits, condition=TianganMatch.SAME_WUXING) == ()


def test_natal_only_and_canggui_touren() -> None:
  chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
  assert tonggen(chart, Tiangan.甲) == ()
  assert tougan(chart, Tiangan.癸, condition=TianganMatch.SAME_WUXING) == ()
  transits = TransitSet(liuyue=Ganzhi.from_str('甲辰'))
  pairs = tougan(chart, Tiangan.癸, transits, condition=TianganMatch.SAME_WUXING)
  assert pairs == (TouganHit(
    TianganOccurrence(TransitKind.LIUYUE, Ganzhi.from_str('甲辰'), Tiangan.癸),
    TianganOccurrence(Zhu.日, chart.bazi.day_pillar, Tiangan.壬),
  ),)
  assert tougan(chart, Tiangan.癸, transits, condition=TianganMatch.SAME_TIANGAN) == ()
  assert tougan(chart, Tiangan.庚, condition=TianganMatch.SAME_TIANGAN)


@pytest.mark.parametrize('target,ganzhi', [(Tiangan.乙, '甲午'), (Tiangan.丁, '乙酉')])
@pytest.mark.parametrize('condition', list(TianganMatch))
def test_yin_changsheng_is_not_a_hidden_root(
  target: Tiangan, ganzhi: str, condition: TianganMatch,
) -> None:
  chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
  roots = tonggen(chart, target, TransitSet(liunian=Ganzhi.from_str(ganzhi)), condition=condition)
  assert all(root.position is not TransitKind.LIUNIAN for root in roots)


@pytest.mark.parametrize('query', [tonggen, tougan])
@pytest.mark.parametrize('field,value', [
  ('chart', object()), ('target', '甲'), ('condition', 'same_wuxing'), ('condition', None),
  ('condition', Zhu.年), ('transits', ()),
])
def test_query_type_gates(query: Any, field: str, value: object) -> None:
  args: dict[str, Any] = {
    'chart': BaziChart.random(), 'target': Tiangan.甲, 'condition': TianganMatch.SAME_WUXING, 'transits': None,
  }
  args[field] = value
  with pytest.raises(TypeError):
    query(**args)


def test_tougan_requires_an_explicit_condition() -> None:
  with pytest.raises(TypeError):
    tougan(BaziChart.random(), Tiangan.甲) # type: ignore[call-arg]


@pytest.mark.parametrize('position,ganzhi,stem,error', [
  ('年', Ganzhi.from_str('甲辰'), Tiangan.甲, TypeError),
  (Zhu.年, '甲辰', Tiangan.甲, TypeError),
  (Zhu.年, Ganzhi.from_str('甲辰'), '甲', TypeError),
  (Zhu.年, Ganzhi('甲', Dizhi.辰), Tiangan.甲, TypeError), # type: ignore[arg-type]
  (Zhu.年, Ganzhi(Tiangan.甲, '辰'), Tiangan.甲, TypeError), # type: ignore[arg-type]
  (Zhu.年, Ganzhi.from_str('甲辰'), Tiangan.丙, ValueError),
])
def test_occurrence_checks_actual_stem(position: Any, ganzhi: Any, stem: Any, error: type[Exception]) -> None:
  with pytest.raises(error):
    TianganOccurrence(position, ganzhi, stem)


def test_tougan_roles_and_immutability() -> None:
  visible = TianganOccurrence(Zhu.日, Ganzhi.from_str('甲辰'), Tiangan.甲)
  hidden = replace(visible, stem=Tiangan.乙)
  valid = TouganHit(hidden, visible)
  for left, right, error in ((visible, visible, ValueError), (hidden, hidden, ValueError),
                             (None, visible, TypeError), (hidden, None, TypeError)):
    with pytest.raises(error):
      TouganHit(left, right) # type: ignore[arg-type]
  with pytest.raises(FrozenInstanceError):
    visible.stem = Tiangan.乙 # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    valid.visible = hidden # type: ignore[misc]
  assert hash(valid) == hash(TouganHit(hidden, visible))
