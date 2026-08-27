# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relations.py

import pytest

from src.defines import (
  TianganRelation, 天干关系, DizhiRelation, 地支关系,
)


def test_tiangan_relation_basic() -> None:
  assert TianganRelation is 天干关系
  assert len(TianganRelation) == 4 # 合、冲、生、克


def test_tiangan_relation_str() -> None:
  for relation in TianganRelation:
    assert str(relation) == relation.value
    assert f'{relation}' == relation.value
    assert TianganRelation.from_str(str(relation)) == relation
    assert TianganRelation(str(relation)) == relation

  with pytest.raises(ValueError):
    TianganRelation.from_str('甲')
  with pytest.raises(ValueError):
    TianganRelation.from_str('和')
  with pytest.raises(ValueError):
    TianganRelation.from_str('冲 ')

  assert ''.join([str(relation) for relation in TianganRelation]) == '合冲生克'


def test_dizhi_relation_basic() -> None:
  assert DizhiRelation is 地支关系
  assert len(DizhiRelation) == 15 # 三会、拱会、六合、暗合、通合、通禄合、三合、半合、拱合、刑、冲、破、害、生、克


def test_dizhi_relation_str() -> None:
  for relation in DizhiRelation:
    assert str(relation) == relation.value
    assert f'{relation}' == relation.value
    assert DizhiRelation.from_str(str(relation)) == relation
    assert DizhiRelation(str(relation)) == relation

  with pytest.raises(ValueError):
    DizhiRelation.from_str('甲')
  with pytest.raises(ValueError):
    DizhiRelation.from_str('八合')
  with pytest.raises(ValueError):
    DizhiRelation.from_str('冲 ')

  assert ''.join([str(relation) for relation in DizhiRelation]) == '三会拱会六合暗合通合通禄合三合半合拱合刑冲破害生克'
