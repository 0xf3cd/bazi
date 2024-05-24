# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_rules.py

import re
import inspect
import unittest

from src.Rules import BaziRules, TianganRules, DizhiRules

class TestRules(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertEqual(BaziRules.HIDDEN_TIANGANS, BaziRules.HIDDEN_TIANGANS)
    self.assertEqual(BaziRules.TIANGAN_ZHANGSHENG, BaziRules.TIANGAN_ZHANGSHENG)
    self.assertEqual(BaziRules.TIANGAN_TRAITS, BaziRules.TIANGAN_TRAITS)
    self.assertEqual(TianganRules.TIANGAN_HE, TianganRules.TIANGAN_HE)
    self.assertEqual(DizhiRules.DIZHI_PO, DizhiRules.DIZHI_PO)

  def test_cache(self) -> None:
    self.assertIs(BaziRules.HIDDEN_TIANGANS, BaziRules.HIDDEN_TIANGANS) 
    self.assertIs(BaziRules.TIANGAN_ZHANGSHENG, BaziRules.TIANGAN_ZHANGSHENG)
    self.assertIs(BaziRules.TIANGAN_TRAITS, BaziRules.TIANGAN_TRAITS)
    self.assertIs(TianganRules.TIANGAN_HE, TianganRules.TIANGAN_HE)
    self.assertIs(DizhiRules.DIZHI_PO, DizhiRules.DIZHI_PO)

  def test_anhetable(self) -> None:
    # I just want `DizhiRules.AnheTable` to be a immutable Class...
    # Actually maybe this is an overkill because no one is going to change `DizhiRules.AnheTable`'s attributes...

    for member in inspect.getmembers(DizhiRules.AnheTable):
      with self.assertRaises(AttributeError):
        setattr(DizhiRules.AnheTable, member[0], '')

    at = DizhiRules.AnheTable()
    for attr in ['normal', 'normal_extended', 'mangpai']:
      with self.assertRaises(AttributeError):
        setattr(at, attr, '')

    with self.assertRaises(TypeError):
      at[DizhiRules.AnheDef.NORMAL] = '' # type: ignore
    with self.assertRaises(TypeError):
      at[DizhiRules.AnheDef.NORMAL_EXTENDED] = '' # type: ignore
    with self.assertRaises(TypeError):
      at[DizhiRules.AnheDef.MANGPAI] = '' # type: ignore

  def test_xingtable(self) -> None:
    # I just want `DizhiRules.XingTable` to be a immutable Class...
    # Actually maybe this is an overkill because no one is going to change `DizhiRules.XingTable`'s attributes...

    for member in inspect.getmembers(DizhiRules.XingTable):
      with self.assertRaises(AttributeError):
        setattr(DizhiRules.XingTable, member[0], '')

    xt = DizhiRules.XingTable()
    for attr in ['strict', 'loose']:
      with self.assertRaises(AttributeError):
        setattr(xt, attr, '')
    
    with self.assertRaises(TypeError):
      xt[DizhiRules.XingDef.STRICT] = '' # type: ignore
    with self.assertRaises(TypeError):
      xt[DizhiRules.XingDef.LOOSE] = '' # type: ignore

  def test_all_rules(self) -> None:
    # I just want Rule classes to be immutable...
    # Actually maybe this is an overkill because no one is going to change their attributes...

    def list_all_rules(rule_class: type) -> list[str]:
      # Assume that all rules' names are consist of '_' and upper letters.
      # Use `inspect` and `re` to find out the names of the rules.
      return [
        member[0] for member in inspect.getmembers(rule_class)
        if re.match(r'^[A-Z_]+$', member[0])
      ]
    
    for klass in [BaziRules, TianganRules, DizhiRules]:
      table_names: list[str] = list_all_rules(klass)
      self.assertGreater(len(table_names), 0)

      for attr in table_names:
        self.assertEqual(getattr(klass, attr), getattr(klass, attr))
        self.assertIs(getattr(klass, attr), getattr(klass, attr)) # Ensure cached
        with self.assertRaises(AttributeError):
          setattr(klass, attr, '') # Error raised!
