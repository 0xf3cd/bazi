# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_rules.py

import re
import inspect

import pytest

from src.defines import Tiangan, Dizhi, Wuxing, DizhiRelation, ShierZhangsheng
from src.rules import BaziRules, TianganRules, DizhiRules, ShenshaRules
from src.utils import bazi_utils


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


def test_dizhi_gong() -> None:
  assert DizhiRules.GONG_RELATIONS == (DizhiRelation.拱合, DizhiRelation.拱会)
  assert set(DizhiRules.GONG_GONGHE_SCOPE) == set(DizhiRules.GongDef)
  assert DizhiRules.GONG_GONGHE_SCOPE == {
    DizhiRules.GongDef.SAME_STEM_NARROW    : DizhiRules.GongheDef.NARROW,
    DizhiRules.GongDef.SAME_STEM_WIDE      : DizhiRules.GongheDef.WIDE,
    DizhiRules.GongDef.TRANSFORMING_NARROW : DizhiRules.GongheDef.NARROW,
    DizhiRules.GongDef.LU_NARROW           : DizhiRules.GongheDef.NARROW,
  }
  assert set(DizhiRules.DIZHI_GONGHE) == set(DizhiRules.GongheDef)
  assert len(DizhiRules.DIZHI_GONGHE[DizhiRules.GongheDef.NARROW]) == 4
  assert len(DizhiRules.DIZHI_GONGHE[DizhiRules.GongheDef.WIDE]) == 12
  assert set(DizhiRules.DIZHI_GONGHE[DizhiRules.GongheDef.NARROW]).issubset(
    DizhiRules.DIZHI_GONGHE[DizhiRules.GongheDef.WIDE]
  )
  assert len(DizhiRules.DIZHI_GONGHUI) == 4
  for table in DizhiRules.DIZHI_GONGHE.values():
    for pair, target in table.items():
      assert frozenset((*pair, target)) in DizhiRules.DIZHI_SANHE
  for pair, target in DizhiRules.DIZHI_GONGHUI.items():
    assert frozenset((*pair, target)) in DizhiRules.DIZHI_SANHUI
  assert DizhiRules.DIZHI_GONG_LU_TIANGAN == {
    Wuxing.木 : Tiangan.乙,
    Wuxing.火 : Tiangan.丁,
    Wuxing.金 : Tiangan.辛,
    Wuxing.水 : Tiangan.癸,
  }

  with pytest.raises(TypeError):
    DizhiRules.DIZHI_GONGHE[DizhiRules.GongheDef.NARROW] = {} # type: ignore


def test_sanhe_shensha_tables() -> None:
  expected_tables = (
    (ShenshaRules.TAOHUA, {
      Dizhi.申 : Dizhi.酉, Dizhi.子 : Dizhi.酉, Dizhi.辰 : Dizhi.酉,
      Dizhi.寅 : Dizhi.卯, Dizhi.午 : Dizhi.卯, Dizhi.戌 : Dizhi.卯,
      Dizhi.亥 : Dizhi.子, Dizhi.卯 : Dizhi.子, Dizhi.未 : Dizhi.子,
      Dizhi.巳 : Dizhi.午, Dizhi.酉 : Dizhi.午, Dizhi.丑 : Dizhi.午,
    }),
    (ShenshaRules.YIMA, {
      Dizhi.申 : Dizhi.寅, Dizhi.子 : Dizhi.寅, Dizhi.辰 : Dizhi.寅,
      Dizhi.寅 : Dizhi.申, Dizhi.午 : Dizhi.申, Dizhi.戌 : Dizhi.申,
      Dizhi.亥 : Dizhi.巳, Dizhi.卯 : Dizhi.巳, Dizhi.未 : Dizhi.巳,
      Dizhi.巳 : Dizhi.亥, Dizhi.酉 : Dizhi.亥, Dizhi.丑 : Dizhi.亥,
    }),
    (ShenshaRules.HUAGAI, {
      Dizhi.寅 : Dizhi.戌, Dizhi.午 : Dizhi.戌, Dizhi.戌 : Dizhi.戌,
      Dizhi.亥 : Dizhi.未, Dizhi.卯 : Dizhi.未, Dizhi.未 : Dizhi.未,
      Dizhi.申 : Dizhi.辰, Dizhi.子 : Dizhi.辰, Dizhi.辰 : Dizhi.辰,
      Dizhi.巳 : Dizhi.丑, Dizhi.酉 : Dizhi.丑, Dizhi.丑 : Dizhi.丑,
    }),
    (ShenshaRules.JIANGXING, {
      Dizhi.申 : Dizhi.子, Dizhi.子 : Dizhi.子, Dizhi.辰 : Dizhi.子,
      Dizhi.寅 : Dizhi.午, Dizhi.午 : Dizhi.午, Dizhi.戌 : Dizhi.午,
      Dizhi.亥 : Dizhi.卯, Dizhi.卯 : Dizhi.卯, Dizhi.未 : Dizhi.卯,
      Dizhi.巳 : Dizhi.酉, Dizhi.酉 : Dizhi.酉, Dizhi.丑 : Dizhi.酉,
    }),
  )

  for table, expected in expected_tables:
    assert tuple(table.items()) == tuple(expected.items())


def test_sanhe_shensha_tables_follow_shier_zhangsheng() -> None:
  group_tiangans = {
    frozenset((Dizhi.申, Dizhi.子, Dizhi.辰)) : Tiangan.壬,
    frozenset((Dizhi.寅, Dizhi.午, Dizhi.戌)) : Tiangan.丙,
    frozenset((Dizhi.亥, Dizhi.卯, Dizhi.未)) : Tiangan.甲,
    frozenset((Dizhi.巳, Dizhi.酉, Dizhi.丑)) : Tiangan.庚,
  }
  table_places = (
    (ShenshaRules.TAOHUA,   ShierZhangsheng.沐浴),
    (ShenshaRules.YIMA,     ShierZhangsheng.病),
    (ShenshaRules.HUAGAI,   ShierZhangsheng.墓),
    (ShenshaRules.JIANGXING, ShierZhangsheng.帝旺),
  )

  assert set(group_tiangans) == set(DizhiRules.DIZHI_SANHE)
  for sanhe, tiangan in group_tiangans.items():
    for table, place in table_places:
      expected = bazi_utils.from_shier_zhangsheng(tiangan, place)
      assert {table[dizhi] for dizhi in sanhe} == {expected}


def test_yangren() -> None:
  assert set(ShenshaRules.YANGREN) == set(ShenshaRules.YangrenDef)
  assert all(set(table) == set(Tiangan) for table in ShenshaRules.YANGREN.values())

  yang_tiangans = (Tiangan.甲, Tiangan.丙, Tiangan.戊, Tiangan.庚, Tiangan.壬)
  expected_yang = (Dizhi.卯, Dizhi.午, Dizhi.午, Dizhi.酉, Dizhi.子)
  for table in ShenshaRules.YANGREN.values():
    assert tuple(table[tg] for tg in yang_tiangans) == expected_yang

  yin_tiangans = (Tiangan.乙, Tiangan.丁, Tiangan.己, Tiangan.辛, Tiangan.癸)
  assert tuple(ShenshaRules.YANGREN[ShenshaRules.YangrenDef.ZIPING][tg]
               for tg in yin_tiangans) == (None, None, None, None, None)
  assert tuple(ShenshaRules.YANGREN[ShenshaRules.YangrenDef.LUMING][tg]
               for tg in yin_tiangans) == (Dizhi.辰, Dizhi.未, Dizhi.未, Dizhi.戌, Dizhi.丑)
  assert tuple(ShenshaRules.YANGREN[ShenshaRules.YangrenDef.DIWANG][tg]
               for tg in yin_tiangans) == (Dizhi.寅, Dizhi.巳, Dizhi.巳, Dizhi.申, Dizhi.亥)


def test_tianyi() -> None:
  assert set(ShenshaRules.TIANYI) == set(ShenshaRules.TianyiDef)
  assert all(set(table) == set(Tiangan) for table in ShenshaRules.TIANYI.values())

  yanggui = ShenshaRules.TIANYI[ShenshaRules.TianyiDef.YANGGUI]
  yingui = ShenshaRules.TIANYI[ShenshaRules.TianyiDef.YINGUI]
  merged = ShenshaRules.TIANYI[ShenshaRules.TianyiDef.GENG_WITH_JIA_WU]
  for tg in Tiangan:
    assert len(yanggui[tg]) == 1
    assert len(yingui[tg]) == 1
    assert merged[tg] == yanggui[tg] | yingui[tg]

  modified = ShenshaRules.TIANYI[ShenshaRules.TianyiDef.GENG_WITH_XIN]
  assert modified[Tiangan.庚] == merged[Tiangan.辛]
  assert all(modified[tg] == merged[tg] for tg in Tiangan if tg is not Tiangan.庚)


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
