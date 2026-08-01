# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_rules.py

import re
import inspect
import unittest

from src.rules import BaziRules, TianganRules, DizhiRules, ShenshaRules

class TestRules(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(BaziRules.HIDDEN_TIANGANS, BaziRules.HIDDEN_TIANGANS)
    self.assertEqual(BaziRules.TIANGAN_ZHANGSHENG, BaziRules.TIANGAN_ZHANGSHENG)
    self.assertEqual(BaziRules.TIANGAN_TRAITS, BaziRules.TIANGAN_TRAITS)
    self.assertEqual(TianganRules.TIANGAN_HE, TianganRules.TIANGAN_HE)
    self.assertEqual(DizhiRules.DIZHI_PO, DizhiRules.DIZHI_PO)
    self.assertEqual(ShenshaRules.TAOHUA, ShenshaRules.TAOHUA)

  def test_cache(self) -> None:
    self.assertIs(BaziRules.HIDDEN_TIANGANS, BaziRules.HIDDEN_TIANGANS) 
    self.assertIs(BaziRules.TIANGAN_ZHANGSHENG, BaziRules.TIANGAN_ZHANGSHENG)
    self.assertIs(BaziRules.TIANGAN_TRAITS, BaziRules.TIANGAN_TRAITS)
    self.assertIs(TianganRules.TIANGAN_HE, TianganRules.TIANGAN_HE)
    self.assertIs(DizhiRules.DIZHI_PO, DizhiRules.DIZHI_PO)
    self.assertIs(ShenshaRules.TAOHUA, ShenshaRules.TAOHUA)

  def test_dizhi_anhe(self) -> None:
    # `DIZHI_ANHE` is a frozendict keyed by `AnheDef` - one sub-table per definition.
    self.assertSetEqual(set(DizhiRules.DIZHI_ANHE), set(DizhiRules.AnheDef))

    for anhe_def in DizhiRules.AnheDef:
      self.assertEqual(DizhiRules.DIZHI_ANHE[anhe_def], DizhiRules.DIZHI_ANHE[anhe_def])

    with self.assertRaises(TypeError):
      DizhiRules.DIZHI_ANHE[DizhiRules.AnheDef.NORMAL] = '' # type: ignore
    with self.assertRaises(KeyError):
      _ = DizhiRules.DIZHI_ANHE['not an AnheDef'] # type: ignore

  def test_dizhi_xing(self) -> None:
    # `DIZHI_XING` is a frozendict keyed by `XingDef` - one sub-table per definition.
    self.assertSetEqual(set(DizhiRules.DIZHI_XING), set(DizhiRules.XingDef))

    for xing_def in DizhiRules.XingDef:
      self.assertEqual(DizhiRules.DIZHI_XING[xing_def], DizhiRules.DIZHI_XING[xing_def])

    with self.assertRaises(TypeError):
      DizhiRules.DIZHI_XING[DizhiRules.XingDef.STRICT] = '' # type: ignore
    with self.assertRaises(KeyError):
      _ = DizhiRules.DIZHI_XING['not a XingDef'] # type: ignore

  def test_all_rules(self) -> None:
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
      self.assertGreater(len(table_names), 0)

      for attr in table_names:
        self.assertEqual(getattr(klass, attr), getattr(klass, attr))
        self.assertIs(getattr(klass, attr), getattr(klass, attr)) # Same object on every access.
