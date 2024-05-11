# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_rules.py

import re
import inspect
import unittest

from src.Rules import Rules
from src.Common import frozendict

class TestRules(unittest.TestCase):
  @staticmethod
  def list_all_rules() -> list[str]:
    # Assume that all rules' names are consist of '_' and upper letters.
    # Use `inspect` and `re` to find out the names of the rules.
    return [
      member[0] for member in inspect.getmembers(Rules)
      if re.match(r'^[A-Z_]+$', member[0])
    ]

  def test_basic(self) -> None:
    self.assertEqual(Rules.DIZHI_PO, Rules.DIZHI_PO)
    self.assertEqual(Rules.HIDDEN_TIANGANS, Rules.HIDDEN_TIANGANS)
    self.assertEqual(Rules.TIANGAN_ZHANGSHENG, Rules.TIANGAN_ZHANGSHENG)
    self.assertEqual(Rules.TIANGAN_TRAITS, Rules.TIANGAN_TRAITS)

  def test_immutable(self) -> None:
    self.assertIs(Rules.DIZHI_PO, Rules.DIZHI_PO)
    self.assertIs(Rules.HIDDEN_TIANGANS, Rules.HIDDEN_TIANGANS) 
    self.assertIs(Rules.TIANGAN_ZHANGSHENG, Rules.TIANGAN_ZHANGSHENG)
    self.assertIs(Rules.TIANGAN_TRAITS, Rules.TIANGAN_TRAITS)

  def test_cache(self) -> None:
    self.assertIs(Rules.DIZHI_PO, Rules.DIZHI_PO)
    self.assertIs(Rules.HIDDEN_TIANGANS, Rules.HIDDEN_TIANGANS) 
    self.assertIs(Rules.TIANGAN_ZHANGSHENG, Rules.TIANGAN_ZHANGSHENG)
    self.assertIs(Rules.TIANGAN_TRAITS, Rules.TIANGAN_TRAITS)
 
  def test_all_rules(self) -> None:
    # I just want `Rules` to be a immutable Class...
    # Actually maybe this is an overkill because no one is going to change `Rules`'s attributes...
    table_names: list[str] = TestRules.list_all_rules()
    self.assertGreater(len(table_names), 0)

    for attr in table_names:
      self.assertEqual(getattr(Rules, attr), getattr(Rules, attr))
      self.assertIs(getattr(Rules, attr), getattr(Rules, attr)) # Ensure cached
      with self.assertRaises(AttributeError):
        setattr(Rules, attr, '') # Error raised!

  def test_anhetable(self) -> None:
    # I just want `Rules.AnheTable` to be a immutable Class...
    # Actually maybe this is an overkill because no one is going to change `Rules.AnheTable`'s attributes...

    for member in inspect.getmembers(Rules.AnheTable):
      with self.assertRaises(AttributeError):
        setattr(Rules.AnheTable, member[0], '')

    at = Rules.AnheTable()
    for attr in ['normal', 'normal_extended', 'mangpai']:
      with self.assertRaises(AttributeError):
        setattr(at, attr, '')

    with self.assertRaises(TypeError):
      at[Rules.AnheDef.NORMAL] = '' # type: ignore
    with self.assertRaises(TypeError):
      at[Rules.AnheDef.NORMAL_EXTENDED] = '' # type: ignore
    with self.assertRaises(TypeError):
      at[Rules.AnheDef.MANGPAI] = '' # type: ignore

  def test_xingtable(self) -> None:
    # I just want `Rules.XingTable` to be a immutable Class...
    # Actually maybe this is an overkill because no one is going to change `Rules.XingTable`'s attributes...

    for member in inspect.getmembers(Rules.XingTable):
      with self.assertRaises(AttributeError):
        setattr(Rules.XingTable, member[0], '')

    xt = Rules.XingTable()
    for attr in ['strict', 'loose']:
      with self.assertRaises(AttributeError):
        setattr(xt, attr, '')
    
    with self.assertRaises(TypeError):
      xt[Rules.XingDef.STRICT] = '' # type: ignore
    with self.assertRaises(TypeError):
      xt[Rules.XingDef.LOOSE] = '' # type: ignore
