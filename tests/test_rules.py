# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_rules.py

import re
import inspect

import pytest

from src.rules import BaziRules, TianganRules, DizhiRules, ShenshaRules


def test_basic() -> None:
  assert BaziRules.HIDDEN_TIANGANS == BaziRules.HIDDEN_TIANGANS
  assert BaziRules.TIANGAN_ZHANGSHENG == BaziRules.TIANGAN_ZHANGSHENG
  assert BaziRules.TIANGAN_TRAITS == BaziRules.TIANGAN_TRAITS
  assert TianganRules.TIANGAN_HE == TianganRules.TIANGAN_HE
  assert DizhiRules.DIZHI_PO == DizhiRules.DIZHI_PO
  assert ShenshaRules.TAOHUA == ShenshaRules.TAOHUA


def test_cache() -> None:
  assert BaziRules.HIDDEN_TIANGANS is BaziRules.HIDDEN_TIANGANS
  assert BaziRules.TIANGAN_ZHANGSHENG is BaziRules.TIANGAN_ZHANGSHENG
  assert BaziRules.TIANGAN_TRAITS is BaziRules.TIANGAN_TRAITS
  assert TianganRules.TIANGAN_HE is TianganRules.TIANGAN_HE
  assert DizhiRules.DIZHI_PO is DizhiRules.DIZHI_PO
  assert ShenshaRules.TAOHUA is ShenshaRules.TAOHUA


def test_dizhi_anhe() -> None:
  # `DIZHI_ANHE` is a frozendict keyed by `AnheDef` - one sub-table per definition.
  assert set(DizhiRules.DIZHI_ANHE) == set(DizhiRules.AnheDef)

  for anhe_def in DizhiRules.AnheDef:
    assert DizhiRules.DIZHI_ANHE[anhe_def] == DizhiRules.DIZHI_ANHE[anhe_def]

  with pytest.raises(TypeError):
    DizhiRules.DIZHI_ANHE[DizhiRules.AnheDef.NORMAL] = '' # type: ignore
  with pytest.raises(KeyError):
    _ = DizhiRules.DIZHI_ANHE['not an AnheDef'] # type: ignore


def test_dizhi_xing() -> None:
  # `DIZHI_XING` is a frozendict keyed by `XingDef` - one sub-table per definition.
  assert set(DizhiRules.DIZHI_XING) == set(DizhiRules.XingDef)

  for xing_def in DizhiRules.XingDef:
    assert DizhiRules.DIZHI_XING[xing_def] == DizhiRules.DIZHI_XING[xing_def]

  with pytest.raises(TypeError):
    DizhiRules.DIZHI_XING[DizhiRules.XingDef.STRICT] = '' # type: ignore
  with pytest.raises(KeyError):
    _ = DizhiRules.DIZHI_XING['not a XingDef'] # type: ignore


def test_all_rules() -> None:
  # Every table on every Rule class reads stably: equal and identical across accesses.
  # (Runtime reassignment protection was deliberately retired; `Final` + mypy is the guard now.)

  def list_all_rules(rule_class: type) -> list[str]:
    # Assume that all rules' names are consist of '_' and upper letters.
    # Use `inspect` and `re` to find out the names of the rules.
    return [
      member[0] for member in inspect.getmembers(rule_class)
      if re.match(r'^[A-Z_]+$', member[0])
    ]

  for klass in [BaziRules, TianganRules, DizhiRules, ShenshaRules]:
    table_names: list[str] = list_all_rules(klass)
    assert len(table_names) > 0

    for attr in table_names:
      assert getattr(klass, attr) == getattr(klass, attr)
      assert getattr(klass, attr) is getattr(klass, attr) # Same object on every access.
