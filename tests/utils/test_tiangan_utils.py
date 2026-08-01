# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_tiangan_utils.py

import random
import itertools
from collections.abc import Iterable

import pytest

from src.defines import Tiangan, Dizhi, Wuxing, TianganRelation, DizhiRelation
from src.utils import bazi_utils, tiangan_utils
from src.utils.tiangan_utils import TianganCombo, TianganRelationCombos, TianganRelationDiscovery


'''Operand type of `_tg_equal`: tiangan combos as a list of sets or an iterable of `TianganCombo`s.'''
TgCmpType = list[set[Tiangan]] | Iterable[TianganCombo]


def _tg_equal(l1: TgCmpType, l2: TgCmpType) -> bool:
  _l1 = list(l1)
  _l2 = list(l2)
  if len(_l1) != len(_l2):
    return False
  for s in _l1:
    if s not in _l2:
      return False
  return True


def test_search_basic() -> None:
  for relation in TianganRelation:
    empty_result: TianganRelationCombos = tiangan_utils.search([], relation)
    assert len(empty_result) == 0

  assert _tg_equal(
    tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.合),
    [
      {Tiangan.丙, Tiangan.辛},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.冲),
    [
      {Tiangan.甲, Tiangan.庚},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.生),
    [
      {Tiangan.甲, Tiangan.丙},
      {Tiangan.甲, Tiangan.丁},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, Tiangan.辛), TianganRelation.克),
    [
      {Tiangan.庚, Tiangan.甲},
      {Tiangan.辛, Tiangan.甲},
      {Tiangan.丙, Tiangan.庚},
      {Tiangan.丙, Tiangan.辛},
      {Tiangan.丁, Tiangan.庚},
      {Tiangan.丁, Tiangan.辛},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合),
    [
      {Tiangan.壬, Tiangan.丁},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲),
    []
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生),
    [
      {Tiangan.丁, Tiangan.戊},
      {Tiangan.戊, Tiangan.辛},
      {Tiangan.辛, Tiangan.壬},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克),
    [
      {Tiangan.戊, Tiangan.壬},
      {Tiangan.壬, Tiangan.丁},
      {Tiangan.丁, Tiangan.辛},
    ]
  )


def test_search_negative() -> None:
  with pytest.raises(TypeError):
    tiangan_utils.search(Tiangan.辛, TianganRelation.合) # type: ignore
  with pytest.raises(TypeError):
    tiangan_utils.search((Tiangan.甲, Dizhi.子)) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.search((Tiangan.甲, Dizhi.子), TianganRelation.合) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.search(('甲', '丙', '辛'), TianganRelation.合) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚, '辛'), TianganRelation.合) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), '合') # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), 'HE') # type: ignore

  for dz_relation in DizhiRelation:
    with pytest.raises(AssertionError):
      tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), dz_relation) # type: ignore

  for relation in TianganRelation:
    with pytest.raises(AssertionError):
      tiangan_utils.search((Tiangan.甲, Tiangan.丙, Tiangan.丁, Tiangan.庚), str(relation)) # type: ignore

  # No need to mutate the result: the returned tuple is immutable.

  # Make sure the method still returns the correct result.
  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.合),
    [
      {Tiangan.壬, Tiangan.丁},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.冲),
    []
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.生),
    [
      {Tiangan.丁, Tiangan.戊},
      {Tiangan.戊, Tiangan.辛},
      {Tiangan.辛, Tiangan.壬},
    ]
  )

  assert _tg_equal(
    tiangan_utils.search((Tiangan.壬, Tiangan.戊, Tiangan.丁, Tiangan.辛), TianganRelation.克),
    [
      {Tiangan.戊, Tiangan.壬},
      {Tiangan.壬, Tiangan.丁},
      {Tiangan.丁, Tiangan.辛},
    ]
  )


@pytest.mark.slow
def test_search_correctness() -> None:
  # Generate the expected relation combos/pairs, which are used later in this test.
  expected_he:    set[TianganCombo] = set()
  expected_chong: set[TianganCombo] = set()
  expected_sheng: set[TianganCombo] = set()
  expected_ke:    set[TianganCombo] = set()
  for combo in itertools.product(Tiangan, Tiangan):
    tg1, tg2 = combo
    if tg1 == tg2:
      continue
    trait1, trait2 = [bazi_utils.tiangan_traits(tg) for tg in combo]
    wx1, wx2 = trait1.wuxing, trait2.wuxing

    if abs(tg1.index - tg2.index) == 5: # Check "He" relation. 合。
      expected_he.add(TianganCombo(combo))
    if all(wx is not Wuxing.土 for wx in [wx1, wx2]) and abs(tg1.index - tg2.index) == 6: # Check "Chong" relation. 冲。
      expected_chong.add(TianganCombo(combo))
    if wx1.generates(wx2) or wx2.generates(wx1): # Check "Sheng" relation. 生。
      expected_sheng.add(TianganCombo(combo))
    if wx1.destructs(wx2) or wx2.destructs(wx1): # Check "Ke" relation. 克。
      expected_ke.add(TianganCombo(combo))

  def __find_relation_combos(tiangans: list[Tiangan], relation: TianganRelation) -> list[set[Tiangan]]:
    expected: set[TianganCombo] = expected_he
    if relation is TianganRelation.冲:
      expected = expected_chong
    if relation is TianganRelation.生:
      expected = expected_sheng
    if relation is TianganRelation.克:
      expected = expected_ke

    result: list[set[Tiangan]] = []
    for combo_tuple in itertools.combinations(tiangans, 2):
      if TianganCombo(combo_tuple) in expected:
        result.append(set(combo_tuple))
    return result

  for _ in range(512):
    tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))

    for combo_fs in tiangan_utils.search(tiangans, TianganRelation.合):
      assert len(combo_fs) == 2
      tg1, tg2 = tuple(combo_fs)
      assert tg1.index - tg2.index in [5, -5]

    for combo_fs in tiangan_utils.search(tiangans, TianganRelation.冲):
      assert len(combo_fs) == 2
      trait1, trait2 = [bazi_utils.traits(tg) for tg in combo_fs]
      # No Tiangan of `Wuxing.土` is involved in the "Chong" relation.
      assert trait1.wuxing != Wuxing.土
      assert trait2.wuxing != Wuxing.土
      assert trait1.yinyang == trait2.yinyang
      wx1, wx2 = trait1.wuxing, trait2.wuxing
      assert wx1.destructs(wx2) or wx2.destructs(wx1)

    for combo_fs in tiangan_utils.search(tiangans, TianganRelation.生):
      assert len(combo_fs) == 2
      # We don't care Tiangan's Yinyang when talking about the "Sheng" relation.
      wx1, wx2 = [bazi_utils.traits(tg).wuxing for tg in combo_fs]
      assert wx1.generates(wx2) or wx2.generates(wx1)

    for combo_fs in tiangan_utils.search(tiangans, TianganRelation.克):
      assert len(combo_fs) == 2
      # We don't care Tiangan's Yinyang when talking about the "Ke" relation.
      wx1, wx2 = [bazi_utils.traits(tg).wuxing for tg in combo_fs]
      assert wx1.destructs(wx2) or wx2.destructs(wx1)

  for relation in TianganRelation:
    tiangans = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
    combos1: TianganRelationCombos = tiangan_utils.search(tiangans, relation)
    combos2: TianganRelationCombos = tiangan_utils.search(tiangans + tiangans, relation)
    assert len(combos1) == len(combos2)
    for combo_fs in combos1:
      assert combo_fs in combos2

    for _ in range(512):
      combos: TianganRelationCombos = tiangan_utils.search(tiangans, relation)
      expected_combos: list[set[Tiangan]] = __find_relation_combos(tiangans, relation)
      assert len(expected_combos) == len(combos)
      for combo_fs in combos:
        assert combo_fs in expected_combos


def test_he() -> None:
  with pytest.raises(AssertionError):
    tiangan_utils.he(Tiangan.甲, Dizhi.子) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.he(Dizhi.子, Tiangan.甲) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.he('甲', '己') # type: ignore

  expected: dict[TianganCombo, Wuxing] = {
    TianganCombo((Tiangan.甲, Tiangan.己)) : Wuxing.土,
    TianganCombo((Tiangan.乙, Tiangan.庚)) : Wuxing.金,
    TianganCombo((Tiangan.丙, Tiangan.辛)) : Wuxing.水,
    TianganCombo((Tiangan.丁, Tiangan.壬)) : Wuxing.木,
    TianganCombo((Tiangan.戊, Tiangan.癸)) : Wuxing.火,
  }

  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    tg_set: set[Tiangan] = {tg1, tg2}
    if any(tg_set == s for s in expected):
      assert tiangan_utils.he(tg1, tg2) == expected[TianganCombo(tg_set)]
      assert tiangan_utils.he(tg2, tg1) == expected[TianganCombo(tg_set)]
    else:
      assert tiangan_utils.he(tg1, tg2) is None
      assert tiangan_utils.he(tg2, tg1) is None


def test_chong() -> None:
  with pytest.raises(AssertionError):
    tiangan_utils.chong(Tiangan.甲, Dizhi.子) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.chong(Dizhi.子, Tiangan.甲) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.chong('甲', '庚') # type: ignore

  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    wx1, wx2 = bazi_utils.traits(tg1).wuxing, bazi_utils.traits(tg2).wuxing
    if all(wx is not Wuxing('土') for wx in [wx1, wx2]) and abs(tg1.index - tg2.index) == 6:
      assert tiangan_utils.chong(tg1, tg2)
      assert tiangan_utils.chong(tg2, tg1)
      continue
    # Else, the two Tiangans are not in CHONG relation.
    assert not tiangan_utils.chong(tg1, tg2)
    assert not tiangan_utils.chong(tg2, tg1)


def test_sheng() -> None:
  with pytest.raises(AssertionError):
    tiangan_utils.sheng(Tiangan.甲, Dizhi.子) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.sheng(Dizhi.子, Tiangan.甲) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.sheng('甲', '庚') # type: ignore

  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    wx1, wx2 = bazi_utils.traits(tg1).wuxing, bazi_utils.traits(tg2).wuxing
    if wx1.generates(wx2):
      assert tiangan_utils.sheng(tg1, tg2)
      assert not tiangan_utils.sheng(tg2, tg1)
    else:
      assert not tiangan_utils.sheng(tg1, tg2)


def test_ke() -> None:
  with pytest.raises(AssertionError):
    tiangan_utils.ke(Tiangan.甲, Dizhi.子) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.ke(Dizhi.子, Tiangan.甲) # type: ignore
  with pytest.raises(AssertionError):
    tiangan_utils.ke('甲', '庚') # type: ignore

  for tg1, tg2 in itertools.product(Tiangan, Tiangan):
    wx1, wx2 = bazi_utils.traits(tg1).wuxing, bazi_utils.traits(tg2).wuxing
    if wx1.destructs(wx2):
      assert tiangan_utils.ke(tg1, tg2)
      assert not tiangan_utils.ke(tg2, tg1)
    else:
      assert not tiangan_utils.ke(tg1, tg2)


@pytest.mark.slow
def test_discover() -> None:
  for _ in range(512):
    tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan))) + \
                              random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
    discovery: TianganRelationDiscovery = tiangan_utils.discover(tiangans)

    # correctness
    for rel in TianganRelation:
      if rel in discovery:
        assert set(discovery[rel]) == set(tiangan_utils.search(tiangans, rel))
      else:
        assert len(tiangan_utils.search(tiangans, rel)) == 0

    # consistency
    discovery2: TianganRelationDiscovery = tiangan_utils.discover(tiangans)
    assert discovery == discovery2


@pytest.mark.slow
def test_discover_mutual() -> None:
  def __random_tg_lists() -> tuple[list[Tiangan], list[Tiangan]]:
    tiangans1: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
    tiangans2: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))

    if random.randint(0, 2) == 0:
      tiangans1.extend(random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan))))
    if random.randint(0, 2) == 0:
      tiangans2.extend(random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan))))

    return tiangans1, tiangans2

  for _ in range(512):
    tiangans1, tiangans2 = __random_tg_lists()
    discovery: TianganRelationDiscovery = tiangan_utils.discover_mutual(tiangans1, tiangans2)

    assert discovery == tiangan_utils.discover_mutual(tiangans1, tiangans2) # Test consistency
    assert discovery == tiangan_utils.discover_mutual(tiangans2, tiangans1) # Test symmertry/equivalence

    expected: dict[TianganRelation, list[TianganCombo]] = {
      TianganRelation.合: [],
      TianganRelation.冲: [],
      TianganRelation.生: [],
      TianganRelation.克: [],
    }

    for tg1, tg2 in itertools.product(tiangans1, tiangans2):
      combo = TianganCombo((tg1, tg2))

      if tiangan_utils.he(tg1, tg2):
        assert combo in discovery[TianganRelation.合]
        expected[TianganRelation.合].append(combo)

      if tiangan_utils.chong(tg1, tg2):
        assert combo in discovery[TianganRelation.冲]
        expected[TianganRelation.冲].append(combo)

      if tiangan_utils.sheng(tg1, tg2) or tiangan_utils.sheng(tg2, tg1):
        assert combo in discovery[TianganRelation.生]
        expected[TianganRelation.生].append(combo)

      if tiangan_utils.ke(tg1, tg2) or tiangan_utils.ke(tg2, tg1):
        assert combo in discovery[TianganRelation.克]
        expected[TianganRelation.克].append(combo)

    for rel, expected_combos in expected.items():
      if rel in discovery:
        for combo in discovery[rel]:
          assert combo in expected_combos
      else:
        assert len(expected_combos) == 0


@pytest.mark.slow
def test_results_matched() -> None:
  '''Test that the results of different methods are the same.'''
  for _ in range(512):
    tiangans: list[Tiangan] = random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan))) + \
                              random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan)))
    discovery: TianganRelationDiscovery = tiangan_utils.discover(tiangans)

    # HE / 合 -- Non-directional relation
    if TianganRelation.合 in discovery:
      for combo in discovery[TianganRelation.合]:
        assert len(combo) == 2
        assert tiangan_utils.he(*combo)

    # CHONG / 冲 -- Non-directional relation
    if TianganRelation.冲 in discovery:
      for combo in discovery[TianganRelation.冲]:
        assert len(combo) == 2
        assert tiangan_utils.chong(*combo)

    # SHENG / 生 -- Directional relation
    if TianganRelation.生 in discovery:
      for combo in discovery[TianganRelation.生]:
        assert len(combo) == 2
        tg1, tg2 = combo
        r1, r2 = tiangan_utils.sheng(tg1, tg2), tiangan_utils.sheng(tg2, tg1)
        assert r1 or r2
        assert not (r1 and r2)

    # KE / 克 -- Directional relation
    if TianganRelation.克 in discovery:
      for combo in discovery[TianganRelation.克]:
        assert len(combo) == 2
        tg1, tg2 = combo
        r1, r2 = tiangan_utils.ke(tg1, tg2), tiangan_utils.ke(tg2, tg1)
        assert r1 or r2
        assert not (r1 and r2)

    tiangans_part1: set[Tiangan] = set(random.sample(tiangans, random.randint(0, len(tiangans))))
    tiangans_part2: set[Tiangan] = set(tiangans) - tiangans_part1
    mutual_discovery: TianganRelationDiscovery = tiangan_utils.discover_mutual(list(tiangans_part1), list(tiangans_part2))

    for rel, mutual_combos in mutual_discovery.items():
      expected = discovery[rel]
      for combo in mutual_combos:
        assert combo in expected
      assert len(expected) >= len(mutual_combos)

    # discover / discover_mutual consistency
    part1_discoverty: TianganRelationDiscovery = tiangan_utils.discover(list(tiangans_part1))
    part2_discoverty: TianganRelationDiscovery = tiangan_utils.discover(list(tiangans_part2))

    for rel in TianganRelation:
      actual: set[TianganCombo] = set()
      if rel in part1_discoverty:
        actual.update(part1_discoverty[rel])
      if rel in part2_discoverty:
        actual.update(part2_discoverty[rel])
      if rel in mutual_discovery:
        actual.update(mutual_discovery[rel])

      if rel in discovery:
        assert set(discovery[rel]) == actual
      else:
        assert len(actual) == 0


def test_discovery_filter() -> None:
  for _ in range(5):
    tiangans: list[Tiangan] = random.sample(list(Tiangan), random.randint(0, len(Tiangan)))
    discovery: TianganRelationDiscovery = tiangan_utils.discover(tiangans)

    assert discovery == discovery.filter(lambda rel, combo : True)

    forbidden_tiangans: list[Tiangan] = random.sample(list(Tiangan), random.randint(0, len(Tiangan)))
    forbidden_relations: list[TianganRelation] = random.sample(list(TianganRelation), random.randint(0, len(TianganRelation)))

    def filter_func(rel: TianganRelation, combo: TianganCombo) -> bool:
      if rel in forbidden_relations:
        return False
      return not any(tg in combo for tg in forbidden_tiangans)

    filtered = discovery.filter(filter_func)

    for rel in forbidden_relations:
      assert rel not in filtered

    for rel, combos in filtered.items():
      for combo in combos:
        assert all(tg not in combo for tg in forbidden_tiangans)
        assert combo in discovery[rel]


def test_discovery_merge() -> None:
  for _ in range(3):
    tiangans1: list[Tiangan] = random.sample(list(Tiangan), random.randint(0, len(Tiangan)))
    discovery1: TianganRelationDiscovery = tiangan_utils.discover(tiangans1)

    tiangans2: list[Tiangan] = random.sample(list(Tiangan), random.randint(0, len(Tiangan)))
    discovery2: TianganRelationDiscovery = tiangan_utils.discover(tiangans2)

    merged = discovery1.merge(discovery2)

    # merge consistency
    merged_ = discovery2.merge(discovery1)
    assert set(merged) == set(merged_)
    for rel, combos in merged.items():
      assert rel in merged_
      assert set(combos) == set(merged_[rel])

    # correctness
    for rel, combos in discovery1.items():
      assert rel in merged
      for combo in combos:
        assert combo in merged[rel]

    for rel, combos in discovery2.items():
      assert rel in merged
      for combo in combos:
        assert combo in merged[rel]

    for rel, combos in merged.items():
      expected = set(discovery1.get(rel, set())) | set(discovery2.get(rel, set()))
      assert set(combos) == expected
