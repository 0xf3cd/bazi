# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest

from bazi.defines import Tiangan, Dizhi, Ganzhi
from bazi.rules import ShenshaRules
from bazi.utils.shensha_utils import xunkong, kongwang


@pytest.mark.parametrize('head, absent', [
  ('甲子', '戌亥'), ('甲戌', '申酉'), ('甲申', '午未'),
  ('甲午', '辰巳'), ('甲辰', '寅卯'), ('甲寅', '子丑'),
])
def test_six_xun_tables_and_ten_branch_complement(head: str, absent: str) -> None:
  cycle = Ganzhi.list_sexagenary_cycle()
  start = cycle.index(Ganzhi.from_str(head))
  anchors = cycle[start:start + 10]
  expected = frozenset(Dizhi(dz) for dz in absent)
  assert set(Dizhi) - {gz.dizhi for gz in anchors} == expected
  for anchor in anchors:
    assert xunkong(anchor) == ShenshaRules.KONGWANG[anchor] == expected
    assert isinstance(xunkong(anchor), frozenset)
    for target in Dizhi:
      assert kongwang(anchor, target) is (target in expected)


def test_table_has_only_sixty_legal_anchors() -> None:
  assert len(ShenshaRules.KONGWANG) == 60
  assert set(ShenshaRules.KONGWANG) == set(Ganzhi.list_sexagenary_cycle())
  with pytest.raises(TypeError):
    ShenshaRules.KONGWANG[Ganzhi.from_str('甲子')] = frozenset() # type: ignore[index]
  with pytest.raises(AttributeError):
    xunkong(Ganzhi.from_str('甲子')).add(Dizhi.子) # type: ignore[attr-defined]


@pytest.mark.input_contract('bazi.utils.shensha_utils', 'xunkong kongwang')
@pytest.mark.parametrize('bad', [None, '甲子', ('甲', '子'), 1, []])
def test_outer_anchor_type_is_checked(bad: object) -> None:
  with pytest.raises(TypeError, match='Expected Ganzhi'):
    xunkong(bad) # type: ignore[arg-type]
  with pytest.raises(TypeError, match='Expected Ganzhi'):
    kongwang(bad, Dizhi.子) # type: ignore[arg-type]


@pytest.mark.input_contract('bazi.utils.shensha_utils', 'kongwang')
@pytest.mark.parametrize('bad', [None, '戌', Tiangan.甲, Ganzhi.from_str('甲戌'), []])
def test_target_type_uses_a_valid_anchor(bad: object) -> None:
  assert kongwang(Ganzhi.from_str('甲子'), Dizhi.戌)
  with pytest.raises(TypeError, match='Expected Dizhi'):
    kongwang(Ganzhi.from_str('甲子'), bad) # type: ignore[arg-type]
