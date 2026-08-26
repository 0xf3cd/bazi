# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_dizhi_utils.py

import copy
import random
import itertools

import pytest

from collections import Counter
from typing import Any
from collections.abc import Iterable, Callable

from src.defines import Tiangan, Dizhi, Ganzhi, Wuxing, TianganRelation, DizhiRelation
from src.rules import DizhiRules
from src.utils import bazi_utils, tiangan_utils, dizhi_utils
from src.utils.dizhi_utils import (
  DizhiCombo, DizhiRelationCombos, DizhiRelationDiscovery,
  GanzhiOccurrence, GanzhiRelationCombo, GanzhiRelationCombos, GanzhiRelationDiscovery,
)


'''Operand type of `_dz_equal`: dizhi combos as a list of sets or an iterable of `DizhiCombo`s.'''
DzCmpType = list[set[Dizhi]] | Iterable[DizhiCombo]


def _dz_equal(l1: DzCmpType, l2: DzCmpType) -> bool:
  _l1 = list(l1)
  _l2 = list(l2)
  if len(_l1) != len(_l2):
    return False
  for s in _l1:
    if s not in _l2:
      return False
  return True


def _project_ganzhi_combos(combos: GanzhiRelationCombos) -> set[DizhiCombo]:
  return {
    DizhiCombo(occurrence.ganzhi.dizhi for occurrence in combo)
    for combo in combos
  }


def test_search_sanhui() -> None:
  sanhui_combos: list[DizhiCombo] = [
    DizhiCombo((Dizhi.from_index(2), Dizhi.from_index(3), Dizhi.from_index(4))),
    DizhiCombo((Dizhi.from_index(5), Dizhi.from_index(6), Dizhi.from_index(7))),
    DizhiCombo((Dizhi.from_index(8), Dizhi.from_index(9), Dizhi.from_index(10))),
    DizhiCombo((Dizhi.from_index(11), Dizhi.from_index(0), Dizhi.from_index(1))),
  ]

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.三会),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.三会),
    [set(c) for c in sanhui_combos],
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.三会)
    expected_result: list[set[Dizhi]] = [set(c) for c in sanhui_combos if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_sanhui() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.sanhui(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhui(Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhui(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhui((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhui({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhui([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhui('亥', '子', '丑') # type: ignore

  dizhi_tuples: list[tuple[Dizhi, Dizhi, Dizhi]] = [
    (Dizhi.寅, Dizhi.卯, Dizhi.辰), # Spring / 春
    (Dizhi.巳, Dizhi.午, Dizhi.未), # Summer / 夏
    (Dizhi.申, Dizhi.酉, Dizhi.戌), # Fall   / 秋
    (Dizhi.亥, Dizhi.子, Dizhi.丑), # Winter / 冬
  ]
  expected: dict[DizhiCombo, Wuxing] = {
    DizhiCombo(dizhis) : bazi_utils.traits(dizhis[0]).wuxing for dizhis in dizhi_tuples
  }

  for dizhis in itertools.product(Dizhi, repeat=3):
    fs: DizhiCombo = DizhiCombo(dizhis)
    if fs in expected:
      for combo in itertools.permutations(dizhis):
        assert dizhi_utils.sanhui(*combo) == expected[fs]
    else:
      for combo in itertools.permutations(dizhis):
        assert dizhi_utils.sanhui(*combo) is None


def test_search_liuhe() -> None:
  liuhe_combos: list[DizhiCombo] = [
    DizhiCombo((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
  ]

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.六合),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.六合),
    liuhe_combos,
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.六合)
    expected_result: list[set[Dizhi]] = [set(c) for c in liuhe_combos if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_liuhe() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.liuhe(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.liuhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.liuhe((Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.liuhe({Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.liuhe([Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.liuhe('亥', '子') # type: ignore

  liuhe_combos: list[DizhiCombo] = [
    DizhiCombo((dz1, dz2)) for dz1, dz2 in itertools.combinations(Dizhi, 2) if (dz1.index + dz2.index) % 12 == 1
  ]

  for dz1, dz2 in itertools.permutations(Dizhi, 2):
    liuhe_result: Wuxing | None = dizhi_utils.liuhe(dz1, dz2)
    liuhe_result2: Wuxing | None = dizhi_utils.liuhe(dz2, dz1)
    assert liuhe_result == liuhe_result2

    if DizhiCombo((dz1, dz2)) in liuhe_combos:
      wx1, wx2 = bazi_utils.traits(dz1).wuxing, bazi_utils.traits(dz2).wuxing
      if wx1.generates(wx2):
        assert liuhe_result == wx2
      elif wx2.generates(wx1):
        assert liuhe_result == wx1
      else:
        assert wx1.destructs(wx2) or wx2.destructs(wx1)
        if {dz1, dz2} == {Dizhi.子, Dizhi.丑}:
          assert liuhe_result == Wuxing.土
        elif {dz1, dz2} == {Dizhi.卯, Dizhi.戌}:
          assert liuhe_result == Wuxing.火
        else:
          assert {dz1, dz2} == {Dizhi.申, Dizhi.巳}
          assert liuhe_result == Wuxing.水
    else:
      assert liuhe_result is None


def test_search_anhe() -> None:
  normal_combos: list[DizhiCombo] = [ # 天干五合对应的地支暗合，5组。
    DizhiCombo((bazi_utils.lu(tg1), bazi_utils.lu(tg2)))
    for tg1, tg2 in itertools.combinations(Tiangan, 2) if tiangan_utils.he(tg1, tg2) is not None
  ]

  expected: dict[DizhiRules.AnheDef, list[DizhiCombo]] = {
    DizhiRules.AnheDef.NORMAL: normal_combos,
    DizhiRules.AnheDef.NORMAL_EXTENDED: normal_combos + [ # `NORMAL_EXTENDED` 中额外的1组。
      DizhiCombo((Dizhi.寅, Dizhi.丑)),
    ],
    DizhiRules.AnheDef.MANGPAI: [ # 盲派三对。
      DizhiCombo((Dizhi.寅, Dizhi.丑)),
      DizhiCombo((Dizhi.午, Dizhi.亥)),
      DizhiCombo((Dizhi.卯, Dizhi.申)),
    ],
  }

  for anhe_def in DizhiRules.AnheDef:
    anhe_combos: list[DizhiCombo] = expected[anhe_def]

    assert _dz_equal(
      dizhi_utils.search([], DizhiRelation.暗合, anhe_def=anhe_def),
      [],
    )
    assert _dz_equal(
      dizhi_utils.search(list(Dizhi), DizhiRelation.暗合, anhe_def=anhe_def),
      anhe_combos,
    )

    for _ in range(200):
      dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.暗合, anhe_def=anhe_def)
      expected_result: list[set[Dizhi]] = [set(c) for c in anhe_combos if c.issubset(dizhis)]
      assert _dz_equal(result, expected_result)

  # The default stays `NORMAL_EXTENDED` (默认仍是最宽定义).
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.暗合),
    expected[DizhiRules.AnheDef.NORMAL_EXTENDED],
  )


def test_anhe() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.anhe(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.anhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.anhe((Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.anhe({Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.anhe([Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.anhe('亥', '子') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.anhe(Dizhi.子, Dizhi.辰, DizhiRules.AnheDef.NORMAL + 100) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.anhe(Dizhi.子, Dizhi.辰, definition='DizhiRules.AnheDef.NORMAL') # type: ignore

  normal_combos: list[DizhiCombo] = [
    DizhiCombo((bazi_utils.lu(tg1), bazi_utils.lu(tg2)))
    for tg1, tg2 in itertools.combinations(Tiangan, 2) if tiangan_utils.he(tg1, tg2) is not None
  ]

  normal_extended_combos: list[DizhiCombo] = normal_combos + [
    DizhiCombo((Dizhi.寅, Dizhi.丑)),
  ]

  mangpai_combos: list[DizhiCombo] = [
    DizhiCombo((Dizhi.寅, Dizhi.丑)),
    DizhiCombo((Dizhi.午, Dizhi.亥)),
    DizhiCombo((Dizhi.卯, Dizhi.申)),
  ]

  expected: dict[DizhiRules.AnheDef, list[DizhiCombo]] = {
    DizhiRules.AnheDef.NORMAL: normal_combos,
    DizhiRules.AnheDef.NORMAL_EXTENDED: normal_extended_combos,
    DizhiRules.AnheDef.MANGPAI: mangpai_combos
  }

  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    for anhe_def in DizhiRules.AnheDef:
      assert dizhi_utils.anhe(dz1, dz2, definition=anhe_def) == (DizhiCombo((dz1, dz2)) in expected[anhe_def])
      assert dizhi_utils.anhe(dz1, dz2, definition=anhe_def) == dizhi_utils.anhe(dz2, dz1, definition=anhe_def)

  # Ensure the default definition is `NORMAL_EXTENDED`.
  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    assert dizhi_utils.anhe(dz1, dz2) == (DizhiCombo((dz1, dz2)) in normal_extended_combos)
    assert dizhi_utils.anhe(dz1, dz2) == dizhi_utils.anhe(dz2, dz1)


def test_search_tonghe() -> None:
  tonghe_combos: set[DizhiCombo] = set()
  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    hidden1, hidden2 = bazi_utils.hidden_tiangans(dz1), bazi_utils.hidden_tiangans(dz2)
    if len(hidden1) != len(hidden2):
      continue
    expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1]
    if all(tg in hidden2 for tg in expected_hidden2):
      tonghe_combos.add(DizhiCombo((dz1, dz2)))

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.通合),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.通合),
    tonghe_combos,
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.通合)
    expected_result: list[set[Dizhi]] = [set(c) for c in tonghe_combos if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_tonghe() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.tonghe(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tonghe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tonghe((Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tonghe({Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tonghe([Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tonghe('亥', '子') # type: ignore

  tonghe_combos: set[DizhiCombo] = set()
  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    hidden1, hidden2 = bazi_utils.hidden_tiangans(dz1), bazi_utils.hidden_tiangans(dz2)
    if len(hidden1) != len(hidden2):
      continue
    expected_hidden2: list[Tiangan] = [Tiangan.from_index((tg.index + 5) % 10) for tg in hidden1]
    if all(tg in hidden2 for tg in expected_hidden2):
      tonghe_combos.add(DizhiCombo((dz1, dz2)))

  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    assert dizhi_utils.tonghe(dz1, dz2) == (DizhiCombo((dz1, dz2)) in tonghe_combos)
    assert dizhi_utils.tonghe(dz1, dz2) == dizhi_utils.tonghe(dz2, dz1)


def test_search_tongluhe() -> None:
  tongluhe_combos: list[DizhiCombo] = [ # 天干五合对应的地支禄身。
    DizhiCombo((bazi_utils.lu(tg1), bazi_utils.lu(tg2)))
    for tg1, tg2 in itertools.combinations(Tiangan, 2) if tiangan_utils.he(tg1, tg2) is not None
  ]

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.通禄合),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.通禄合),
    tongluhe_combos,
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.通禄合)
    expected_result: list[set[Dizhi]] = [set(c) for c in tongluhe_combos if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_tongluhe() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.tongluhe(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tongluhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tongluhe((Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tongluhe({Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tongluhe([Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.tongluhe('亥', '子') # type: ignore

  tongluhe_combos: list[DizhiCombo] = [ # 天干五合对应的地支禄身。
    DizhiCombo((bazi_utils.lu(tg1), bazi_utils.lu(tg2)))
    for tg1, tg2 in itertools.combinations(Tiangan, 2) if tiangan_utils.he(tg1, tg2) is not None
  ]

  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    assert dizhi_utils.tongluhe(dz1, dz2) == (DizhiCombo((dz1, dz2)) in tongluhe_combos)
    assert dizhi_utils.tongluhe(dz1, dz2) == dizhi_utils.tongluhe(dz2, dz1)


def _gen_sanhe_table() -> dict[DizhiCombo, Wuxing]:
  return {
    DizhiCombo((
      dz,
      Dizhi.from_index((dz.index + 4) % 12),
      Dizhi.from_index((dz.index - 4) % 12),
    )) : bazi_utils.traits(dz).wuxing
    for dz in [Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉')]
  }


def test_search_sanhe() -> None:
  sanhe_table: dict[DizhiCombo, Wuxing] = _gen_sanhe_table()

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.三合),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.三合),
    sanhe_table.keys(),
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.三合)
    expected_result: list[set[Dizhi]] = [set(c) for c in sanhe_table if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_sanhe() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.sanhe(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhe(Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhe(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhe((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhe({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhe([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sanhe('亥', '子', '丑') # type: ignore

  sanhe_table: dict[DizhiCombo, Wuxing] = _gen_sanhe_table()

  for dizhis in itertools.product(Dizhi, repeat=3):
    fs: DizhiCombo = DizhiCombo(dizhis)
    if fs in sanhe_table:
      for combo in itertools.permutations(dizhis):
        assert dizhi_utils.sanhe(*combo) == sanhe_table[fs]
    else:
      for combo in itertools.permutations(dizhis):
        assert dizhi_utils.sanhe(*combo) is None


def _gen_banhe_table() -> dict[DizhiCombo, Wuxing]:
  pivots: set[Dizhi] = {Dizhi('子'), Dizhi('午'), Dizhi('卯'), Dizhi('酉')} # 四中神
  sanhe_table: dict[DizhiCombo, Wuxing] = _gen_sanhe_table()

  d: dict[DizhiCombo, Wuxing] = {}
  for sanhe_dizhis, wx in sanhe_table.items():
    for dz1, dz2 in itertools.combinations(sanhe_dizhis, 2):
      if any(dz in pivots for dz in (dz1, dz2)): # 半合局需要出现中神
        d[DizhiCombo((dz1, dz2))] = wx
  return d


def test_search_banhe() -> None:
  banhe_table: dict[DizhiCombo, Wuxing] = _gen_banhe_table()

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.半合),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.半合),
    banhe_table.keys()
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.半合)
    expected_result: list[set[Dizhi]] = [set(c) for c in banhe_table if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_banhe() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.banhe(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.banhe(Dizhi.子, Dizhi.辰, Dizhi.申) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.banhe((Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.banhe({Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.banhe([Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.banhe('亥', '子') # type: ignore

  banhe_table: dict[DizhiCombo, Wuxing] = _gen_banhe_table()

  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    assert dizhi_utils.banhe(dz1, dz2) == banhe_table.get(DizhiCombo((dz1, dz2)), None)
    assert dizhi_utils.banhe(dz1, dz2) == dizhi_utils.banhe(dz2, dz1)


def test_gonghe() -> None:
  narrow: dict[DizhiCombo, Dizhi] = {
    DizhiCombo((Dizhi.巳, Dizhi.丑)) : Dizhi.酉,
    DizhiCombo((Dizhi.亥, Dizhi.未)) : Dizhi.卯,
    DizhiCombo((Dizhi.申, Dizhi.辰)) : Dizhi.子,
    DizhiCombo((Dizhi.寅, Dizhi.戌)) : Dizhi.午,
  }
  wide: dict[DizhiCombo, Dizhi] = {
    **narrow,
    DizhiCombo((Dizhi.巳, Dizhi.酉)) : Dizhi.丑,
    DizhiCombo((Dizhi.酉, Dizhi.丑)) : Dizhi.巳,
    DizhiCombo((Dizhi.亥, Dizhi.卯)) : Dizhi.未,
    DizhiCombo((Dizhi.卯, Dizhi.未)) : Dizhi.亥,
    DizhiCombo((Dizhi.申, Dizhi.子)) : Dizhi.辰,
    DizhiCombo((Dizhi.子, Dizhi.辰)) : Dizhi.申,
    DizhiCombo((Dizhi.寅, Dizhi.午)) : Dizhi.戌,
    DizhiCombo((Dizhi.午, Dizhi.戌)) : Dizhi.寅,
  }

  with pytest.raises(TypeError):
    dizhi_utils.gonghe('申', Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.gonghe(Dizhi.申, Dizhi.辰, definition='NARROW') # type: ignore

  for dz1, dz2 in itertools.product(Dizhi, repeat=2):
    combo = DizhiCombo((dz1, dz2))
    assert dizhi_utils.gonghe(dz1, dz2) is narrow.get(combo)
    assert dizhi_utils.gonghe(dz1, dz2, definition=DizhiRules.GongheDef.NARROW) is narrow.get(combo)
    assert dizhi_utils.gonghe(dz1, dz2, definition=DizhiRules.GongheDef.WIDE) is wide.get(combo)
    assert dizhi_utils.gonghe(dz1, dz2) is dizhi_utils.gonghe(dz2, dz1)


def test_gonghui() -> None:
  expected: dict[DizhiCombo, Dizhi] = {
    DizhiCombo((Dizhi.寅, Dizhi.辰)) : Dizhi.卯,
    DizhiCombo((Dizhi.巳, Dizhi.未)) : Dizhi.午,
    DizhiCombo((Dizhi.申, Dizhi.戌)) : Dizhi.酉,
    DizhiCombo((Dizhi.亥, Dizhi.丑)) : Dizhi.子,
  }

  with pytest.raises(TypeError):
    dizhi_utils.gonghui(Dizhi.寅, '辰') # type: ignore

  for dz1, dz2 in itertools.product(Dizhi, repeat=2):
    combo = DizhiCombo((dz1, dz2))
    assert dizhi_utils.gonghui(dz1, dz2) is expected.get(combo)
    assert dizhi_utils.gonghui(dz1, dz2) is dizhi_utils.gonghui(dz2, dz1)


def test_search_xing() -> None:
  base_expected: list[dict[Dizhi, int]] = [ # 辰午酉亥自刑
    {
      dz : 2,
    } for dz in [Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥]
  ] + [ # 其他相刑（两定义共有 / shared by both definitions）。
    { Dizhi.子 : 1, Dizhi.卯 : 1, },
    { Dizhi.寅 : 1, Dizhi.巳 : 1, Dizhi.申 : 1, },
    { Dizhi.丑 : 1, Dizhi.未 : 1, Dizhi.戌 : 1, },
  ]
  loose_only: list[dict[Dizhi, int]] = [ # LOOSE only: any two of the three suffice / 仅 LOOSE：三取二。
    { Dizhi.寅 : 1, Dizhi.巳 : 1, },
    { Dizhi.巳 : 1, Dizhi.申 : 1, },
    { Dizhi.寅 : 1, Dizhi.申 : 1, },
    { Dizhi.丑 : 1, Dizhi.未 : 1, },
    { Dizhi.未 : 1, Dizhi.戌 : 1, },
    { Dizhi.丑 : 1, Dizhi.戌 : 1, },
  ]
  expected_by_def: dict[DizhiRules.XingDef, list[dict[Dizhi, int]]] = {
    DizhiRules.XingDef.STRICT: base_expected,
    DizhiRules.XingDef.LOOSE:  base_expected + loose_only,
  }

  def __find_qualified(xing_expected: list[dict[Dizhi, int]], dizhis: list[Dizhi]) -> list[set[Dizhi]]:
    ret: list[set[Dizhi]] = []
    for required in xing_expected:
      if all(
        sum(dz == d for d in dizhis) >= required[dz]
        for dz in required
      ):
        ret.append(set(required.keys()))
    return ret

  # The fixed pins below run on the default definition (`LOOSE`).
  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.刑),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search([Dizhi.子, Dizhi.卯], DizhiRelation.刑),
    [{Dizhi.子, Dizhi.卯}],
  )
  assert _dz_equal(
    dizhi_utils.search([Dizhi.卯, Dizhi.子], DizhiRelation.刑),
    [{Dizhi.子, Dizhi.卯}],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.刑),
    [{Dizhi.子, Dizhi.卯},
     {Dizhi.寅, Dizhi.巳, Dizhi.申}, {Dizhi.寅, Dizhi.巳}, {Dizhi.巳, Dizhi.申}, {Dizhi.寅, Dizhi.申},
     {Dizhi.丑, Dizhi.未, Dizhi.戌}, {Dizhi.丑, Dizhi.未}, {Dizhi.未, Dizhi.戌}, {Dizhi.丑, Dizhi.戌}],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi) + [Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥], DizhiRelation.刑),
    [set(d.keys()) for d in expected_by_def[DizhiRules.XingDef.LOOSE]]
  )

  # Every definition gets the full-combo and random-subset treatment (每个定义都过一遍全组合与随机子集).
  for xing_def in DizhiRules.XingDef:
    xing_expected: list[dict[Dizhi, int]] = expected_by_def[xing_def]

    assert _dz_equal(
      dizhi_utils.search(list(Dizhi), DizhiRelation.刑, xing_def=xing_def),
      __find_qualified(xing_expected, list(Dizhi)),
    )

    for _ in range(200):
      dizhis: list[Dizhi] = []
      for _ in range(random.randint(1, 4)):
        dizhis += random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.刑, xing_def=xing_def)
      expected_result: list[set[Dizhi]] = __find_qualified(xing_expected, dizhis)
      assert _dz_equal(result, expected_result)


def test_search_def_type_gates() -> None:
  # Every batch entry gates both def params at runtime (每个批量入口都查两个定义参数的类型).
  with pytest.raises(TypeError):
    dizhi_utils.search([Dizhi.子], DizhiRelation.暗合, anhe_def='NORMAL_EXTENDED') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search([Dizhi.子], DizhiRelation.刑, xing_def='LOOSE') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover([Dizhi.子], anhe_def=0) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover([Dizhi.子], xing_def=DizhiRules.AnheDef.NORMAL) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual([Dizhi.子], [Dizhi.丑], anhe_def='NORMAL') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual([Dizhi.子], [Dizhi.丑], xing_def=1) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis([Ganzhi.from_str('甲子')], DizhiRelation.拱合, gong_def='NARROW') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_ganzhis([Ganzhi.from_str('甲子')], gong_def=0) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual_ganzhis(
      [Ganzhi.from_str('甲子')],
      [Ganzhi.from_str('乙丑')],
      gong_def=DizhiRules.GongheDef.NARROW, # type: ignore
    )


def test_discover_def_passthrough() -> None:
  # The def params reach `search` through both batch entries (参数经两个批量入口透传到 search)。
  # 寅午 forms ANHE under NORMAL / NORMAL_EXTENDED but not MANGPAI; 寅巳 forms XING only under LOOSE.
  # 寅午暗合 NORMAL / NORMAL_EXTENDED 皆有、MANGPAI 无；寅巳刑仅 LOOSE 成立。
  dizhis: list[Dizhi] = [Dizhi.寅, Dizhi.午, Dizhi.巳, Dizhi.子]

  default_d: DizhiRelationDiscovery = dizhi_utils.discover(dizhis)
  mangpai_d: DizhiRelationDiscovery = dizhi_utils.discover(dizhis, anhe_def=DizhiRules.AnheDef.MANGPAI)
  strict_d: DizhiRelationDiscovery = dizhi_utils.discover(dizhis, xing_def=DizhiRules.XingDef.STRICT)

  # Pin the exact combos, not just "fewer results" (钉精确集合,不钉「变少」).
  assert _dz_equal(default_d[DizhiRelation.暗合], [{Dizhi.寅, Dizhi.午}, {Dizhi.子, Dizhi.巳}])
  assert DizhiRelation.暗合 not in mangpai_d
  assert _dz_equal(default_d[DizhiRelation.刑], [{Dizhi.寅, Dizhi.巳}])
  assert DizhiRelation.刑 not in strict_d

  mutual_default: DizhiRelationDiscovery = dizhi_utils.discover_mutual([Dizhi.寅], [Dizhi.午])
  mutual_mangpai: DizhiRelationDiscovery = dizhi_utils.discover_mutual([Dizhi.寅], [Dizhi.午], anhe_def=DizhiRules.AnheDef.MANGPAI)
  assert _dz_equal(mutual_default[DizhiRelation.暗合], [{Dizhi.寅, Dizhi.午}])
  assert DizhiRelation.暗合 not in mutual_mangpai

  mutual_loose: DizhiRelationDiscovery = dizhi_utils.discover_mutual([Dizhi.寅], [Dizhi.巳])
  mutual_strict: DizhiRelationDiscovery = dizhi_utils.discover_mutual([Dizhi.寅], [Dizhi.巳], xing_def=DizhiRules.XingDef.STRICT)
  assert _dz_equal(mutual_loose[DizhiRelation.刑], [{Dizhi.寅, Dizhi.巳}])
  assert DizhiRelation.刑 not in mutual_strict


def test_xing_negative() -> None:
  with pytest.raises(ValueError):
    dizhi_utils.xing(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰)
  with pytest.raises(TypeError):
    dizhi_utils.xing((Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.xing({Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.xing([Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.xing('亥', '子') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.xing(Dizhi.子, Dizhi.辰, DizhiRules.XingDef.LOOSE) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.xing(Dizhi.子, Dizhi.辰, definition='DizhiRules.X.NORMAL') # type: ignore

  for dz in Dizhi:
    assert dizhi_utils.xing(dz) is None
    assert dizhi_utils.xing(dz, definition=DizhiRules.XingDef.STRICT) is None
    assert dizhi_utils.xing(dz, definition=DizhiRules.XingDef.LOOSE) is None

  for _ in range(500):
    random_dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(4, len(Dizhi)))
    with pytest.raises(ValueError):
      dizhi_utils.xing(*random_dizhis)
    with pytest.raises(ValueError):
      dizhi_utils.xing(*random_dizhis, definition=DizhiRules.XingDef.STRICT)
    with pytest.raises(ValueError):
      dizhi_utils.xing(*random_dizhis, definition=DizhiRules.XingDef.LOOSE)


@pytest.mark.slow
def test_xing_strict() -> None:
  assert dizhi_utils.xing() is None
  assert dizhi_utils.xing(definition=DizhiRules.XingDef.STRICT) is None
  assert dizhi_utils.xing(Dizhi.亥, definition=DizhiRules.XingDef.STRICT) is None
  assert dizhi_utils.xing(Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.STRICT) == DizhiRules.XingSubType.自刑
  assert dizhi_utils.xing(Dizhi.亥, Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.STRICT) is None
  assert dizhi_utils.xing(Dizhi.子, Dizhi.卯, definition=DizhiRules.XingDef.STRICT) == DizhiRules.XingSubType.子卯刑
  assert dizhi_utils.xing(Dizhi.卯, Dizhi.子, definition=DizhiRules.XingDef.STRICT) == DizhiRules.XingSubType.子卯刑
  assert dizhi_utils.xing(Dizhi.子, Dizhi.卯, Dizhi.亥, definition=DizhiRules.XingDef.STRICT) is None
  assert dizhi_utils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申, definition=DizhiRules.XingDef.STRICT) == DizhiRules.XingSubType.三刑
  assert dizhi_utils.xing(Dizhi.巳, Dizhi.寅, Dizhi.申, definition=DizhiRules.XingDef.STRICT) == DizhiRules.XingSubType.三刑
  assert dizhi_utils.xing(Dizhi.寅, Dizhi.巳, definition=DizhiRules.XingDef.STRICT) is None
  assert dizhi_utils.xing(Dizhi.巳, Dizhi.寅, definition=DizhiRules.XingDef.STRICT) is None

  def __expected_strict_xing(dizhis: tuple[Dizhi, ...]) -> DizhiRules.XingSubType | None:
    # In `XingDef.STRICT` mode, we don't care about the direction.
    __fs: DizhiCombo = DizhiCombo(dizhis)
    if __fs in [DizhiCombo((Dizhi.丑, Dizhi.戌, Dizhi.未)), DizhiCombo((Dizhi.寅, Dizhi.巳, Dizhi.申))]:
      return DizhiRules.XingSubType.三刑
    elif __fs == DizhiCombo((Dizhi.子, Dizhi.卯)):
      return DizhiRules.XingSubType.子卯刑
    elif len(__fs) == 1 and len(dizhis) == 2 and dizhis[0] in (Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥):
      return DizhiRules.XingSubType.自刑
    return None

  for dz in Dizhi:
    assert dizhi_utils.xing(dz, definition=DizhiRules.XingDef.STRICT) is None

  for dz1, dz2 in itertools.product(Dizhi, Dizhi):
    strict_result: DizhiRules.XingSubType | None = dizhi_utils.xing(dz1, dz2, definition=DizhiRules.XingDef.STRICT)
    strict_result2: DizhiRules.XingSubType | None = dizhi_utils.xing(dz2, dz1, definition=DizhiRules.XingDef.STRICT)
    strict_result3: DizhiRules.XingSubType | None = dizhi_utils.xing(dz1, dz2, definition=DizhiRules.XingDef.STRICT)
    assert strict_result == strict_result2
    assert strict_result == strict_result3
    assert strict_result == __expected_strict_xing((dz1, dz2))

  for dz_tuple in itertools.product(Dizhi, Dizhi, Dizhi):
    strict_result4: DizhiRules.XingSubType | None = dizhi_utils.xing(*dz_tuple, definition=DizhiRules.XingDef.STRICT)
    for dz1, dz2, dz3 in itertools.permutations(dz_tuple, 3):
      assert strict_result4 == dizhi_utils.xing(dz1, dz2, dz3, definition=DizhiRules.XingDef.STRICT)
      assert strict_result4 == dizhi_utils.xing(dz1, dz2, dz3, definition=DizhiRules.XingDef.STRICT)


def test_xing_loose() -> None:
  assert dizhi_utils.xing(definition=DizhiRules.XingDef.LOOSE) is None
  assert dizhi_utils.xing(Dizhi.亥, definition=DizhiRules.XingDef.LOOSE) is None
  assert dizhi_utils.xing(Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.LOOSE) == DizhiRules.XingSubType.自刑
  assert dizhi_utils.xing(Dizhi.亥, Dizhi.亥, Dizhi.亥, definition=DizhiRules.XingDef.LOOSE) is None
  assert dizhi_utils.xing(Dizhi.子, Dizhi.卯, definition=DizhiRules.XingDef.LOOSE) == DizhiRules.XingSubType.子卯刑
  assert dizhi_utils.xing(Dizhi.卯, Dizhi.子, definition=DizhiRules.XingDef.LOOSE) == DizhiRules.XingSubType.子卯刑
  assert dizhi_utils.xing(Dizhi.子, Dizhi.卯, Dizhi.亥, definition=DizhiRules.XingDef.LOOSE) is None
  assert dizhi_utils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申, definition=DizhiRules.XingDef.LOOSE) == DizhiRules.XingSubType.三刑
  assert dizhi_utils.xing(Dizhi.巳, Dizhi.寅, Dizhi.申, definition=DizhiRules.XingDef.LOOSE) == DizhiRules.XingSubType.三刑
  assert dizhi_utils.xing(Dizhi.寅, Dizhi.巳, definition=DizhiRules.XingDef.LOOSE) == DizhiRules.XingSubType.三刑
  assert dizhi_utils.xing(Dizhi.巳, Dizhi.寅, definition=DizhiRules.XingDef.LOOSE) is None

  sanxing_list: list[tuple[Dizhi, ...]] = [
    (Dizhi.丑, Dizhi.戌),
    (Dizhi.戌, Dizhi.未),
    (Dizhi.未, Dizhi.丑),
    (Dizhi.寅, Dizhi.巳),
    (Dizhi.巳, Dizhi.申),
    (Dizhi.申, Dizhi.寅),
    *(list(itertools.permutations((Dizhi.丑, Dizhi.戌, Dizhi.未)))),
    *(list(itertools.permutations((Dizhi.寅, Dizhi.巳, Dizhi.申)))),
  ]

  zimaoxing_list: list[tuple[Dizhi, ...]] = [
    (Dizhi.子, Dizhi.卯),
    (Dizhi.卯, Dizhi.子),
  ]

  zixing_list: list[tuple[Dizhi, ...]] = [
    (dz, dz) for dz in (Dizhi.辰, Dizhi.午, Dizhi.酉, Dizhi.亥)
  ]

  for dz in Dizhi:
    assert dizhi_utils.xing(dz, definition=DizhiRules.XingDef.LOOSE) is None

  dz_tuple: tuple[Dizhi, ...]
  for dz_tuple in itertools.product(Dizhi, Dizhi):
    loose_result: DizhiRules.XingSubType | None = dizhi_utils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE)
    if loose_result is DizhiRules.XingSubType.三刑:
      assert dz_tuple in sanxing_list
    elif loose_result is DizhiRules.XingSubType.子卯刑:
      assert dz_tuple in zimaoxing_list
    elif loose_result is DizhiRules.XingSubType.自刑:
      assert dz_tuple in zixing_list
    else:
      assert loose_result is None
      assert dz_tuple not in sanxing_list
      assert dz_tuple not in zimaoxing_list
      assert dz_tuple not in zixing_list

  for dz_tuple in itertools.product(Dizhi, Dizhi, Dizhi):
    loose_result2: DizhiRules.XingSubType | None = dizhi_utils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE)
    if loose_result2 is None:
      assert dz_tuple not in sanxing_list
      assert dz_tuple not in zimaoxing_list
      assert dz_tuple not in zixing_list
    else:
      assert loose_result2 == DizhiRules.XingSubType.三刑
      assert dz_tuple in sanxing_list


def test_search_chong() -> None:
  chong_table: list[set[Dizhi]] = [set(dz_tuple) for dz_tuple in zip(Dizhi.as_list()[:6], Dizhi.as_list()[6:])]

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.冲),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.冲),
    chong_table,
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.冲)
    expected_result: list[set[Dizhi]] = [c for c in chong_table if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_chong() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.chong(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.chong(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.chong(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.chong((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.chong({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.chong([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.chong('亥', '子') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.chong(Tiangan.甲, '子') # type: ignore

  chong_table: list[set[Dizhi]] = [set(dz_tuple) for dz_tuple in zip(Dizhi.as_list()[:6], Dizhi.as_list()[6:])]

  for dz1, dz2 in itertools.product(Dizhi, repeat=2):
    assert dizhi_utils.chong(dz1, dz2) == dizhi_utils.chong(dz2, dz1), 'CHONG (冲) is a bi-directional relation'
    assert dizhi_utils.chong(dz1, dz2) == ({dz1, dz2} in chong_table)


def _gen_po_table() -> list[set[Dizhi]]:
  return [{
    Dizhi.from_index(dz_idx), Dizhi.from_index((dz_idx - 3) % 12),
  } for dz_idx in range(0, 12, 2)]


def test_search_po() -> None:
  po_table: list[set[Dizhi]] = _gen_po_table()

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.破),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.破),
    po_table,
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.破)
    expected_result: list[set[Dizhi]] = [c for c in po_table if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_po() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.po(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.po(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.po(Dizhi.子, Dizhi.辰, Dizhi.子, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.po((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.po({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.po([Dizhi.亥, Dizhi.子, Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.po([Dizhi.亥, Dizhi.子], [Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.po('亥', '子') # type: ignore

  po_table: list[set[Dizhi]] = _gen_po_table()

  for dz1, dz2 in itertools.product(Dizhi, repeat=2):
    assert dizhi_utils.po(dz1, dz2) == dizhi_utils.po(dz2, dz1), 'PO (破) is a bi-directional relation'
    assert dizhi_utils.po(dz1, dz2) == ({dz1, dz2} in po_table)


def _gen_hai_table() -> set[DizhiCombo]:
  ret: set[DizhiCombo] = set()
  for dz1, dz2 in itertools.combinations(Dizhi, 2):
    if dizhi_utils.liuhe(dz1, dz2):
      dz1_chong: Dizhi = Dizhi.from_index((dz1.index + 6) % 12)
      dz2_chong: Dizhi = Dizhi.from_index((dz2.index + 6) % 12)
      ret.add(DizhiCombo((dz1, dz2_chong)))
      ret.add(DizhiCombo((dz1_chong, dz2)))
  return ret


def test_search_hai() -> None:
  hai_set: set[DizhiCombo] = _gen_hai_table()

  assert _dz_equal(
    dizhi_utils.search([], DizhiRelation.害),
    [],
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi), DizhiRelation.害),
    hai_set,
  )
  assert _dz_equal(
    dizhi_utils.search(list(Dizhi) * 2, DizhiRelation.害),
    hai_set,
  )

  for _ in range(500):
    dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
    result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.害)
    expected_result: list[DizhiCombo] = [c for c in hai_set if c.issubset(dizhis)]
    assert _dz_equal(result, expected_result)


def test_hai() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.hai(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.hai(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.hai((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.hai({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.hai([Dizhi.亥], [Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.hai('亥', '丑') # type: ignore

  hai_set: set[DizhiCombo] = _gen_hai_table()

  for dz1, dz2 in itertools.product(Dizhi, repeat=2):
    assert dizhi_utils.hai(dz1, dz2) == dizhi_utils.hai(dz2, dz1), 'HAI (害) is a bi-directional relation'
    assert dizhi_utils.hai(dz1, dz2) == (DizhiCombo((dz1, dz2)) in hai_set)


def test_search_sheng_ke() -> None:
  for _ in range(200):
    dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
    sheng_result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.生)
    ke_result: DizhiRelationCombos = dizhi_utils.search(dizhis, DizhiRelation.克)

    for fs in sheng_result:
      for dz in fs:
        assert dz in dizhis
    for fs in ke_result:
      for dz in fs:
        assert dz in dizhis

    for dz1, dz2 in itertools.combinations(dizhis, 2):
      wx1, wx2 = bazi_utils.traits(dz1).wuxing, bazi_utils.traits(dz2).wuxing
      if wx1.generates(wx2) or wx2.generates(wx1):
        assert DizhiCombo((dz1, dz2)) in sheng_result
      if wx1.destructs(wx2) or wx2.destructs(wx1):
        assert DizhiCombo((dz1, dz2)) in ke_result


def test_sheng() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.sheng(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sheng(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sheng((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sheng({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sheng([Dizhi.亥], [Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.sheng('亥', '丑') # type: ignore

  for dz1, dz2 in itertools.product(Dizhi, repeat=2):
    wx1, wx2 = bazi_utils.traits(dz1).wuxing, bazi_utils.traits(dz2).wuxing
    if wx1.generates(wx2):
      assert dizhi_utils.sheng(dz1, dz2)
      assert not dizhi_utils.sheng(dz2, dz1)
    else:
      assert not dizhi_utils.sheng(dz1, dz2)


def test_ke() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.ke(Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.ke(Dizhi.子, Dizhi.辰, Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.ke((Dizhi.亥, Dizhi.子, Dizhi.丑)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.ke({Dizhi.亥, Dizhi.子, Dizhi.丑}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.ke([Dizhi.亥], [Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.ke('亥', '丑') # type: ignore

  for dz1, dz2 in itertools.product(Dizhi, repeat=2):
    wx1, wx2 = bazi_utils.traits(dz1).wuxing, bazi_utils.traits(dz2).wuxing
    if wx1.destructs(wx2):
      assert dizhi_utils.ke(dz1, dz2)
      assert not dizhi_utils.ke(dz2, dz1)
    else:
      assert not dizhi_utils.ke(dz1, dz2)


def test_search_negative() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.search([Dizhi.子, Dizhi.午]) # type: ignore

  for tg_relation in TianganRelation:
    with pytest.raises(TypeError):
      dizhi_utils.search([Dizhi.子, Dizhi.午], tg_relation) # type: ignore

  for relation in DizhiRelation:
    with pytest.raises(TypeError):
      dizhi_utils.search(Dizhi.子, relation) # type: ignore
    with pytest.raises(TypeError):
      dizhi_utils.search(['甲', '己'], relation) # type: ignore
    with pytest.raises(TypeError):
      dizhi_utils.search([Dizhi.子, Dizhi.午], str(relation)) # type: ignore
    with pytest.raises(TypeError):
      dizhi_utils.search({Dizhi.子, Dizhi.午}, relation) # type: ignore

  for relation in (DizhiRelation.拱合, DizhiRelation.拱会):
    with pytest.raises(ValueError):
      dizhi_utils.search([Dizhi.申, Dizhi.辰], relation)


def test_ganzhi_occurrence() -> None:
  occurrence = GanzhiOccurrence(2, Ganzhi.from_str('庚申'))
  assert occurrence.index == 2
  assert occurrence.ganzhi == Ganzhi.from_str('庚申')
  assert occurrence == GanzhiOccurrence(2, Ganzhi.from_str('庚申'))
  assert occurrence != GanzhiOccurrence(0, Ganzhi.from_str('庚申'))
  assert hash(occurrence) == hash(GanzhiOccurrence(2, Ganzhi.from_str('庚申')))

  with pytest.raises(TypeError):
    GanzhiOccurrence('2', Ganzhi.from_str('庚申')) # type: ignore
  with pytest.raises(ValueError):
    GanzhiOccurrence(-1, Ganzhi.from_str('庚申'))
  with pytest.raises(TypeError):
    GanzhiOccurrence(2, Dizhi.申) # type: ignore


def test_search_ganzhis_occurrence_identity() -> None:
  repeated_shen = (
    Ganzhi.from_str('庚申'),
    Ganzhi.from_str('甲子'),
    Ganzhi.from_str('壬申'),
    Ganzhi.from_str('癸巳'),
  )
  result: GanzhiRelationCombos = dizhi_utils.search_ganzhis(repeated_shen, DizhiRelation.六合)
  assert set(result) == {
    GanzhiRelationCombo((GanzhiOccurrence(0, repeated_shen[0]), GanzhiOccurrence(3, repeated_shen[3]))),
    GanzhiRelationCombo((GanzhiOccurrence(2, repeated_shen[2]), GanzhiOccurrence(3, repeated_shen[3]))),
  }
  assert _project_ganzhi_combos(result) == {DizhiCombo((Dizhi.申, Dizhi.巳))}

  repeated_ganzhi = (
    Ganzhi.from_str('甲子'),
    Ganzhi.from_str('甲子'),
    Ganzhi.from_str('乙丑'),
  )
  assert set(dizhi_utils.search_ganzhis(repeated_ganzhi, DizhiRelation.六合)) == {
    GanzhiRelationCombo((GanzhiOccurrence(0, repeated_ganzhi[0]), GanzhiOccurrence(2, repeated_ganzhi[2]))),
    GanzhiRelationCombo((GanzhiOccurrence(1, repeated_ganzhi[1]), GanzhiOccurrence(2, repeated_ganzhi[2]))),
  }

  repeated_yin = (
    Ganzhi.from_str('甲寅'),
    Ganzhi.from_str('壬午'),
    Ganzhi.from_str('甲戌'),
    Ganzhi.from_str('丙寅'),
  )
  assert set(dizhi_utils.search_ganzhis(repeated_yin, DizhiRelation.三合)) == {
    GanzhiRelationCombo((
      GanzhiOccurrence(0, repeated_yin[0]),
      GanzhiOccurrence(1, repeated_yin[1]),
      GanzhiOccurrence(2, repeated_yin[2]),
    )),
    GanzhiRelationCombo((
      GanzhiOccurrence(1, repeated_yin[1]),
      GanzhiOccurrence(2, repeated_yin[2]),
      GanzhiOccurrence(3, repeated_yin[3]),
    )),
  }

  repeated_chen = (
    Ganzhi.from_str('戊辰'),
    Ganzhi.from_str('庚辰'),
    Ganzhi.from_str('壬辰'),
  )
  self_xing: GanzhiRelationCombos = dizhi_utils.search_ganzhis(repeated_chen, DizhiRelation.刑)
  assert set(self_xing) == {
    GanzhiRelationCombo((GanzhiOccurrence(i, repeated_chen[i]), GanzhiOccurrence(j, repeated_chen[j])))
    for i, j in itertools.combinations(range(3), 2)
  }
  assert _project_ganzhi_combos(self_xing) == {DizhiCombo((Dizhi.辰,))}

  for pair in (
    (Ganzhi.from_str('戊辰'), Ganzhi.from_str('庚辰')),
    (Ganzhi.from_str('庚午'), Ganzhi.from_str('壬午')),
    (Ganzhi.from_str('癸酉'), Ganzhi.from_str('乙酉')),
    (Ganzhi.from_str('乙亥'), Ganzhi.from_str('丁亥')),
  ):
    assert dizhi_utils.search_ganzhis(pair, DizhiRelation.刑) == (
      GanzhiRelationCombo((GanzhiOccurrence(0, pair[0]), GanzhiOccurrence(1, pair[1]))),
    )


def test_search_ganzhis_gong_profiles_and_scope() -> None:
  same = (Ganzhi.from_str('庚申'), Ganzhi.from_str('庚辰'))
  expected_same = (
    GanzhiRelationCombo((GanzhiOccurrence(0, same[0]), GanzhiOccurrence(1, same[1]))),
  )
  assert dizhi_utils.search_ganzhis(same, DizhiRelation.拱合) == expected_same
  assert dizhi_utils.gonghe(*(occurrence.ganzhi.dizhi for occurrence in expected_same[0])) is Dizhi.子
  assert dizhi_utils.search_ganzhis(tuple(reversed(same)), DizhiRelation.拱合) != ()

  nonadjacent = (same[0], Ganzhi.from_str('乙卯'), same[1])
  assert dizhi_utils.search_ganzhis(nonadjacent, DizhiRelation.拱合) == ()
  filled = (*same, Ganzhi.from_str('甲子'))
  assert dizhi_utils.search_ganzhis(filled, DizhiRelation.拱合) == ()
  assert dizhi_utils.search_ganzhis(
    (Ganzhi.from_str('庚申'), Ganzhi.from_str('戊辰')),
    DizhiRelation.拱合,
  ) == ()

  wide = (Ganzhi.from_str('庚申'), Ganzhi.from_str('庚子'))
  assert dizhi_utils.search_ganzhis(wide, DizhiRelation.拱合) == ()
  assert dizhi_utils.search_ganzhis(
    wide,
    DizhiRelation.拱合,
    gong_def=DizhiRules.GongDef.SAME_STEM_WIDE,
  ) == (
    GanzhiRelationCombo((GanzhiOccurrence(0, wide[0]), GanzhiOccurrence(1, wide[1]))),
  )

  transforming = (Ganzhi.from_str('壬午'), Ganzhi.from_str('庚申'), Ganzhi.from_str('戊辰'))
  assert dizhi_utils.search_ganzhis(
    transforming,
    DizhiRelation.拱合,
    gong_def=DizhiRules.GongDef.TRANSFORMING_NARROW,
  ) == (
    GanzhiRelationCombo((GanzhiOccurrence(1, transforming[1]), GanzhiOccurrence(2, transforming[2]))),
  )
  assert dizhi_utils.search_ganzhis(
    (Ganzhi.from_str('甲午'), *transforming[1:]),
    DizhiRelation.拱合,
    gong_def=DizhiRules.GongDef.TRANSFORMING_NARROW,
  ) == ()

  lu = (Ganzhi.from_str('癸亥'), Ganzhi.from_str('庚申'), Ganzhi.from_str('戊辰'))
  assert dizhi_utils.search_ganzhis(
    lu,
    DizhiRelation.拱合,
    gong_def=DizhiRules.GongDef.LU_NARROW,
  ) != ()

  gonghui = (Ganzhi.from_str('甲寅'), Ganzhi.from_str('甲辰'))
  assert dizhi_utils.search_ganzhis(gonghui, DizhiRelation.拱会) != ()
  transforming_gonghui = (Ganzhi.from_str('乙丑'), Ganzhi.from_str('甲寅'), Ganzhi.from_str('戊辰'))
  assert dizhi_utils.search_ganzhis(
    transforming_gonghui,
    DizhiRelation.拱会,
    gong_def=DizhiRules.GongDef.TRANSFORMING_NARROW,
  ) != ()
  assert dizhi_utils.search_ganzhis(
    transforming_gonghui,
    DizhiRelation.拱会,
    gong_def=DizhiRules.GongDef.LU_NARROW,
  ) == ()


def test_discover_mutual_ganzhis_scope_and_identity() -> None:
  first = (Ganzhi.from_str('庚申'), Ganzhi.from_str('丙午'))
  second = (Ganzhi.from_str('甲寅'), Ganzhi.from_str('庚辰'))
  discovery = dizhi_utils.discover_mutual_ganzhis(first, second)
  assert discovery[DizhiRelation.拱合] == (
    GanzhiRelationCombo((GanzhiOccurrence(0, first[0]), GanzhiOccurrence(3, second[1]))),
  )

  filled_second = (*second, Ganzhi.from_str('甲子'))
  assert DizhiRelation.拱合 not in dizhi_utils.discover_mutual_ganzhis(first, filled_second)
  assert dizhi_utils.discover_mutual_ganzhis((), second) == GanzhiRelationDiscovery({})

  repeated = dizhi_utils.discover_mutual_ganzhis(
    (Ganzhi.from_str('甲子'),),
    (Ganzhi.from_str('甲子'), Ganzhi.from_str('乙丑')),
  )
  assert repeated[DizhiRelation.六合] == (
    GanzhiRelationCombo((
      GanzhiOccurrence(0, Ganzhi.from_str('甲子')),
      GanzhiOccurrence(2, Ganzhi.from_str('乙丑')),
    )),
  )

  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual_ganzhis(object(), second) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual_ganzhis(first, {Ganzhi.from_str('庚辰')}) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual_ganzhis([Dizhi.申], second) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual_ganzhis(first, [Dizhi.辰]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual_ganzhis(first, second, anhe_def='NORMAL') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual_ganzhis(first, second, xing_def='LOOSE') # type: ignore


def test_search_ganzhis_projection() -> None:
  assert dizhi_utils.search_ganzhis((), DizhiRelation.六合) == ()
  assert dizhi_utils.search_ganzhis((Ganzhi.from_str('甲子'),), DizhiRelation.六合) == ()

  ganzhis = tuple(Ganzhi.list_sexagenary_cycle()[:24])
  dizhis = tuple(gz.dizhi for gz in ganzhis)

  for anhe_def, xing_def, relation in itertools.product(
    DizhiRules.AnheDef,
    DizhiRules.XingDef,
    DizhiRelation,
  ):
    if relation in (DizhiRelation.拱合, DizhiRelation.拱会):
      continue
    original = dizhi_utils.search(dizhis, relation, anhe_def=anhe_def, xing_def=xing_def)
    positioned = dizhi_utils.search_ganzhis(ganzhis, relation, anhe_def=anhe_def, xing_def=xing_def)
    assert _project_ganzhi_combos(positioned) == set(original)


def test_search_ganzhis_negative() -> None:
  relation = DizhiRelation.六合
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis(Ganzhi.from_str('甲子'), relation) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis([Ganzhi.from_str('甲子'), Dizhi.丑], relation) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis({Ganzhi.from_str('甲子'), Ganzhi.from_str('乙丑')}, relation) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis([Ganzhi.from_str('甲子')], TianganRelation.合) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis([Ganzhi.from_str('甲子')], relation, anhe_def='NORMAL') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis([Ganzhi.from_str('甲子')], relation, xing_def='LOOSE') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.search_ganzhis([Ganzhi.from_str('甲子')], relation, gong_def='SAME_STEM_NARROW') # type: ignore


def test_discover_ganzhis_projection() -> None:
  assert dizhi_utils.discover_ganzhis(()) == GanzhiRelationDiscovery({})
  assert dizhi_utils.discover_ganzhis((Ganzhi.from_str('甲子'),)) == GanzhiRelationDiscovery({})

  ganzhis = tuple(Ganzhi.list_sexagenary_cycle()[:24])
  dizhis = tuple(gz.dizhi for gz in ganzhis)

  for anhe_def, xing_def in itertools.product(DizhiRules.AnheDef, DizhiRules.XingDef):
    original = dizhi_utils.discover(dizhis, anhe_def=anhe_def, xing_def=xing_def)
    positioned = dizhi_utils.discover_ganzhis(ganzhis, anhe_def=anhe_def, xing_def=xing_def)
    assert positioned.to_dizhi_discovery() == original

  empty = GanzhiRelationDiscovery({DizhiRelation.六合: ()})
  assert empty.to_dizhi_discovery() == DizhiRelationDiscovery({})
  assert not hasattr(empty, 'merge')


def test_discover_ganzhis_negative() -> None:
  ganzhis = [Ganzhi.from_str('甲子')]
  with pytest.raises(TypeError):
    dizhi_utils.discover_ganzhis(Ganzhi.from_str('甲子')) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_ganzhis([Ganzhi.from_str('甲子'), Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_ganzhis(set(ganzhis)) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_ganzhis(ganzhis, anhe_def='NORMAL') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_ganzhis(ganzhis, xing_def='LOOSE') # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_ganzhis(ganzhis, gong_def='SAME_STEM_NARROW') # type: ignore


@pytest.mark.slow
def test_search() -> None:
  for relation in DizhiRelation:
    if relation in (DizhiRelation.拱合, DizhiRelation.拱会):
      continue
    for round in range(300):
      dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
      for _ in range(random.randint(0, 2)):
        dizhis += random.sample(list(Dizhi), random.randint(0, len(Dizhi)))

      dizhi_counter: Counter[Dizhi] = Counter(dizhis)
      result: DizhiRelationCombos = dizhi_utils.search(dizhis, relation)
      for _ in range(2):
        random.shuffle(dizhis)
        copied: list[Dizhi] = copy.deepcopy(dizhis)
        assert _dz_equal(result, dizhi_utils.search(dizhis, relation))
        assert copied == dizhis # Ensure `search` has no effect on the input `dizhis`.

      result2: DizhiRelationCombos = dizhi_utils.search(dizhis + dizhis, relation)
      result3: DizhiRelationCombos = dizhi_utils.search(dizhis + dizhis + dizhis, relation)

      # Expectedly, `result2` and `result3` should be equal to `result1`.
      # The only exception is 自刑。
      result_patched: DizhiRelationCombos = copy.deepcopy(result)
      if relation is DizhiRelation.刑:
        for dz in (Dizhi.午, Dizhi.辰, Dizhi.酉, Dizhi.亥):
          if dizhi_counter[dz] == 1:
            fs = DizhiCombo((dz,))
            assert fs not in result_patched
            assert fs in result2
            assert fs in result3
            result_patched = result_patched + (fs,) # Patch it up.

      assert _dz_equal(result_patched, result2)
      assert _dz_equal(result_patched, result3)


def _run_all_relation_methods(dizhis: list[Dizhi]) -> list[Any]:
  '''Invokes every relation method over the given dizhis (all permutations) and returns the collected results.'''
  dizhi_set: set[Dizhi] = set(dizhis)
  sorted_dizhis: list[Dizhi] = sorted(dizhi_set, key=lambda dz : dz.index)
  result: list[Any] = []

  result.append(dizhi_utils.xing(definition=DizhiRules.XingDef.STRICT))
  result.append(dizhi_utils.xing(definition=DizhiRules.XingDef.LOOSE))

  for dz in sorted_dizhis:
    result.append(dizhi_utils.xing(dz, definition=DizhiRules.XingDef.STRICT))
    result.append(dizhi_utils.xing(dz, definition=DizhiRules.XingDef.LOOSE))

  dz_tuple: tuple[Dizhi, ...]
  for dz_tuple in itertools.permutations(sorted_dizhis, 2):
    result.append(dizhi_utils.liuhe(*dz_tuple))
    result.append(dizhi_utils.anhe(*dz_tuple, definition=DizhiRules.AnheDef.NORMAL))
    result.append(dizhi_utils.anhe(*dz_tuple, definition=DizhiRules.AnheDef.NORMAL_EXTENDED))
    result.append(dizhi_utils.anhe(*dz_tuple, definition=DizhiRules.AnheDef.MANGPAI))
    result.append(dizhi_utils.tonghe(*dz_tuple))
    result.append(dizhi_utils.tongluhe(*dz_tuple))
    result.append(dizhi_utils.banhe(*dz_tuple))
    result.append(dizhi_utils.gonghe(*dz_tuple))
    result.append(dizhi_utils.gonghe(*dz_tuple, definition=DizhiRules.GongheDef.WIDE))
    result.append(dizhi_utils.gonghui(*dz_tuple))
    result.append(dizhi_utils.xing(*dz_tuple, definition=DizhiRules.XingDef.STRICT))
    result.append(dizhi_utils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE))
    result.append(dizhi_utils.chong(*dz_tuple))
    result.append(dizhi_utils.po(*dz_tuple))
    result.append(dizhi_utils.hai(*dz_tuple))
    result.append(dizhi_utils.sheng(*dz_tuple))
    result.append(dizhi_utils.ke(*dz_tuple))

  for dz_tuple in itertools.permutations(sorted_dizhis, 3):
    result.append(dizhi_utils.sanhui(*dz_tuple)) # Mypy complains... # type: ignore
    result.append(dizhi_utils.sanhe(*dz_tuple)) # Mypy complains... # type: ignore
    result.append(dizhi_utils.xing(*dz_tuple, definition=DizhiRules.XingDef.STRICT)) # Mypy complains... # type: ignore
    result.append(dizhi_utils.xing(*dz_tuple, definition=DizhiRules.XingDef.LOOSE)) # Mypy complains... # type: ignore

  return result


@pytest.mark.slow
def test_discover() -> None:
  for _ in range(512):
    dizhis: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi))) + \
                          random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    discovery: DizhiRelationDiscovery = dizhi_utils.discover(dizhis)

    # correctness
    for rel in DizhiRelation:
      if rel in (DizhiRelation.拱合, DizhiRelation.拱会):
        assert rel not in discovery
        continue
      if rel in discovery:
        assert set(discovery[rel]) == set(dizhi_utils.search(dizhis, rel))
      else:
        assert len(dizhi_utils.search(dizhis, rel)) == 0

    # consistency
    discovery2: DizhiRelationDiscovery = dizhi_utils.discover(dizhis)
    assert discovery == discovery2


def test_discover_negative() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.discover([Dizhi.子, '午']) # type: ignore


@pytest.mark.slow
def test_discover_mutual() -> None:
  def __random_dz_lists() -> tuple[list[Dizhi], list[Dizhi]]:
    dizhis1: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))
    dizhis2: list[Dizhi] = random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi)))

    if random.randint(0, 2) == 0:
      dizhis1.extend(random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi))))
    if random.randint(0, 2) == 0:
      dizhis2.extend(random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi))))

    return dizhis1, dizhis2

  for _ in range(16):
    dizhis1, dizhis2 = __random_dz_lists()
    discovery: DizhiRelationDiscovery = dizhi_utils.discover_mutual(dizhis1, dizhis2)

    assert discovery == dizhi_utils.discover_mutual(dizhis1, dizhis2) # Test consistency
    assert discovery == dizhi_utils.discover_mutual(dizhis2, dizhis1) # Test symmetry/equivalence

    expected: dict[DizhiRelation, set[DizhiCombo]] = {
      rel : set() for rel in DizhiRelation
    }

    rules: list[tuple[DizhiRelation, Callable[..., Any], int]] = [
      (DizhiRelation.三会, dizhi_utils.sanhui, 3),
      (DizhiRelation.三合, dizhi_utils.sanhe, 3),
      (DizhiRelation.刑, dizhi_utils.xing, 3),
      (DizhiRelation.六合, dizhi_utils.liuhe, 2),
      (DizhiRelation.暗合, dizhi_utils.anhe, 2),
      (DizhiRelation.通合, dizhi_utils.tonghe, 2),
      (DizhiRelation.通禄合, dizhi_utils.tongluhe, 2),
      (DizhiRelation.半合, dizhi_utils.banhe, 2),
      (DizhiRelation.刑, dizhi_utils.xing, 2),
      (DizhiRelation.冲, dizhi_utils.chong, 2),
      (DizhiRelation.破, dizhi_utils.po, 2),
      (DizhiRelation.害, dizhi_utils.hai, 2),
      (DizhiRelation.生, dizhi_utils.sheng, 2),
      (DizhiRelation.克, dizhi_utils.ke, 2),
    ]

    # Fill `expected`...
    dizhis1_set, dizhis2_set = set(dizhis1), set(dizhis2)
    for rel, f, n in rules:
      for dz_tuple in itertools.permutations(dizhis1 + dizhis2, n):
        combo = DizhiCombo(dz_tuple)
        if not f(*dz_tuple):
          continue
        if any(combo.isdisjoint(s) for s in (dizhis1_set, dizhis2_set)):
          continue

        assert combo in discovery[rel]
        expected[rel].add(combo)

    for rel, expected_combos in expected.items():
      if rel in discovery:
        for combo in discovery[rel]:
          assert combo in expected_combos
      else:
        assert len(expected_combos) == 0


def test_discover_mutual_negative() -> None:
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual([Dizhi.亥, '子'], [Dizhi.丑]) # type: ignore
  with pytest.raises(TypeError):
    dizhi_utils.discover_mutual([Dizhi.亥], [Dizhi.子, '丑']) # type: ignore


def test_edge_cases() -> None:
  '''Test `discover_mutual` on 三合、三会、三刑、自刑'''
  for combo_fs in DizhiRules.DIZHI_SANHE:
    part1 = [random.choice(list(combo_fs))]
    part2 = list(combo_fs - set(part1))

    assert DizhiRelation.三合 not in dizhi_utils.discover_mutual([], [*combo_fs])

    assert (combo_fs,) == dizhi_utils.discover_mutual(part1, part2)[DizhiRelation.三合]
    assert (dizhi_utils.discover_mutual(part1, part2) ==
            dizhi_utils.discover_mutual(part2, part1))

  for combo_fs in DizhiRules.DIZHI_SANHUI:
    part1 = [random.choice(list(combo_fs))]
    part2 = list(combo_fs - set(part1))

    assert DizhiRelation.三会 not in dizhi_utils.discover_mutual([], [*combo_fs])

    assert (combo_fs,) == dizhi_utils.discover_mutual(part1, part2)[DizhiRelation.三会]
    assert (dizhi_utils.discover_mutual(part1, part2) ==
            dizhi_utils.discover_mutual(part2, part1))

  for combo_tuple in DizhiRules.DIZHI_XING[DizhiRules.XingDef.LOOSE]:
    part1 = [random.choice(combo_tuple)]
    part2 = list(combo_tuple)
    part2.remove(part1[0])

    assert DizhiRelation.刑 not in dizhi_utils.discover_mutual([], [*combo_tuple])

    assert frozenset(combo_tuple) in dizhi_utils.discover_mutual(part1, part2)[DizhiRelation.刑]
    assert (dizhi_utils.discover_mutual(part1, part2) ==
            dizhi_utils.discover_mutual(part2, part1))

  assert (frozenset({Dizhi.午}),) == dizhi_utils.discover_mutual([Dizhi.午], [Dizhi.午])[DizhiRelation.刑]


@pytest.mark.slow
def test_consistency() -> None:
  '''Module-level functions in `dizhi_utils` must give consistent results across calls.'''

  def __split(dizhis: list[Dizhi]) -> tuple[list[Dizhi], list[Dizhi]]:
    dz_idx_list: list[int] = [idx for idx, _ in enumerate(dizhis)]
    part1_idx_list: list[int] = random.sample(dz_idx_list, random.randint(0, len(dz_idx_list)))
    part2_idx_list: list[int] = [idx for idx in dz_idx_list if idx not in part1_idx_list]
    assert len(part1_idx_list) + len(part2_idx_list) == len(dizhis)
    assert len(set(part1_idx_list + part2_idx_list)) == len(dizhis)

    part1_dizhis: list[Dizhi] = [dizhis[idx] for idx in part1_idx_list]
    part2_dizhis: list[Dizhi] = [dizhis[idx] for idx in part2_idx_list]
    assert len(part1_dizhis) + len(part2_dizhis) == len(dizhis)

    return part1_dizhis, part2_dizhis

  for attempt in range(8):
    dizhis: list[Dizhi] = []
    for _ in range(random.randint(0, 4)):
      dizhis.extend(random.sample(list(Dizhi), random.randint(0, 5)))
    copied_dizhis: list[Dizhi] = copy.deepcopy(dizhis)

    for relation in DizhiRelation:
      if relation in (DizhiRelation.拱合, DizhiRelation.拱会):
        continue
      relation_results: list[list[Any]] = []
      combo_results: list[DizhiRelationCombos] = []
      discover_results: list[DizhiRelationDiscovery] = []
      discover_mutual_results: list[DizhiRelationDiscovery] = []

      dizhis_p1, dizhis_p2 = __split(dizhis)

      for _ in range(5):
        if random.randint(0, 1) == 0:
          relation_results.append(_run_all_relation_methods(dizhis))
        if random.randint(0, 1) == 0:
          combo_results.append(dizhi_utils.search(dizhis, relation))
        if random.randint(0, 1) == 0:
          discover_results.append(dizhi_utils.discover(dizhis))
        if random.randint(0, 1) == 0:
          discover_mutual_results.append(dizhi_utils.discover_mutual(dizhis_p1, dizhis_p2))
          discover_mutual_results.append(dizhi_utils.discover_mutual(dizhis_p2, dizhis_p1))

      for rr1, rr2 in itertools.pairwise(relation_results):
        assert rr1 == rr2
      for cr1, cr2 in itertools.pairwise(combo_results):
        assert cr1 == cr2
      for dr1, dr2 in itertools.pairwise(discover_results):
        assert dr1 == dr2
      for dmr1, dmr2 in itertools.pairwise(discover_mutual_results):
        assert dmr1 == dmr2

    assert dizhis == copied_dizhis # Ensure the order of `dizhis` was not changed.


def test_discovery_filter() -> None:
  for _ in range(5):
    dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
    discovery: DizhiRelationDiscovery = dizhi_utils.discover(dizhis)

    assert discovery == discovery.filter(lambda rel, combos : True)

    forbidden_dizhis: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
    forbidden_relations: list[DizhiRelation] = random.sample(list(DizhiRelation), random.randint(0, len(DizhiRelation)))

    def filter_func(rel: DizhiRelation, combo: DizhiCombo) -> bool:
      if rel in forbidden_relations:
        return False
      return not any(dz in combo for dz in forbidden_dizhis)

    filtered = discovery.filter(filter_func)

    for rel in forbidden_relations:
      assert rel not in filtered

    for rel, combos in filtered.items():
      for combo in combos:
        assert all(dz not in combo for dz in forbidden_dizhis)
        assert combo in discovery[rel]


@pytest.mark.slow
def test_discovery_merge() -> None:
  for _ in range(5):
    dizhis1: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))
    dizhis2: list[Dizhi] = random.sample(list(Dizhi), random.randint(0, len(Dizhi)))

    discovery1 = dizhi_utils.discover(dizhis1)
    discovery2 = dizhi_utils.discover(dizhis2)

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
