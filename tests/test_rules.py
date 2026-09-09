# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_rules.py

import re
import inspect

import pytest

from src.defines import Tiangan, Dizhi, Ganzhi, Wuxing, DizhiRelation, ShierZhangsheng
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
    (ShenshaRules.ZAISHA, {
      Dizhi.申 : Dizhi.午, Dizhi.子 : Dizhi.午, Dizhi.辰 : Dizhi.午,
      Dizhi.寅 : Dizhi.子, Dizhi.午 : Dizhi.子, Dizhi.戌 : Dizhi.子,
      Dizhi.巳 : Dizhi.卯, Dizhi.酉 : Dizhi.卯, Dizhi.丑 : Dizhi.卯,
      Dizhi.亥 : Dizhi.酉, Dizhi.卯 : Dizhi.酉, Dizhi.未 : Dizhi.酉,
    }),
    (ShenshaRules.JIESHA, {
      Dizhi.申 : Dizhi.巳, Dizhi.子 : Dizhi.巳, Dizhi.辰 : Dizhi.巳,
      Dizhi.寅 : Dizhi.亥, Dizhi.午 : Dizhi.亥, Dizhi.戌 : Dizhi.亥,
      Dizhi.亥 : Dizhi.申, Dizhi.卯 : Dizhi.申, Dizhi.未 : Dizhi.申,
      Dizhi.巳 : Dizhi.寅, Dizhi.酉 : Dizhi.寅, Dizhi.丑 : Dizhi.寅,
    }),
    (ShenshaRules.WANGSHEN, {
      Dizhi.申 : Dizhi.亥, Dizhi.子 : Dizhi.亥, Dizhi.辰 : Dizhi.亥,
      Dizhi.寅 : Dizhi.巳, Dizhi.午 : Dizhi.巳, Dizhi.戌 : Dizhi.巳,
      Dizhi.亥 : Dizhi.寅, Dizhi.卯 : Dizhi.寅, Dizhi.未 : Dizhi.寅,
      Dizhi.巳 : Dizhi.申, Dizhi.酉 : Dizhi.申, Dizhi.丑 : Dizhi.申,
    }),
  )

  for table, expected in expected_tables:
    assert tuple(table.items()) == tuple(expected.items())


def test_zaisha_table_is_jiangxing_chong() -> None:
  assert set(ShenshaRules.ZAISHA) == set(ShenshaRules.JIANGXING) == set(Dizhi)
  for anchor in Dizhi:
    assert frozenset((
      ShenshaRules.JIANGXING[anchor],
      ShenshaRules.ZAISHA[anchor],
    )) in DizhiRules.DIZHI_CHONG


def test_sanhe_shensha_tables_follow_shier_zhangsheng() -> None:
  group_zhangsheng = {
    frozenset((Dizhi.申, Dizhi.子, Dizhi.辰)) : Dizhi.申,
    frozenset((Dizhi.寅, Dizhi.午, Dizhi.戌)) : Dizhi.寅,
    frozenset((Dizhi.亥, Dizhi.卯, Dizhi.未)) : Dizhi.亥,
    frozenset((Dizhi.巳, Dizhi.酉, Dizhi.丑)) : Dizhi.巳,
  }
  table_places = (
    (ShenshaRules.TAOHUA,    ShierZhangsheng.沐浴),
    (ShenshaRules.YIMA,      ShierZhangsheng.病),
    (ShenshaRules.HUAGAI,    ShierZhangsheng.墓),
    (ShenshaRules.JIANGXING, ShierZhangsheng.帝旺),
    (ShenshaRules.JIESHA,    ShierZhangsheng.绝),
    (ShenshaRules.WANGSHEN,  ShierZhangsheng.临官),
  )

  assert set(group_zhangsheng) == set(DizhiRules.DIZHI_SANHE)
  for sanhe, zhangsheng in group_zhangsheng.items():
    for table, place in table_places:
      expected = Dizhi.from_index((zhangsheng.index + place.index) % len(Dizhi))
      assert {table[dizhi] for dizhi in sanhe} == {expected}


def test_guchen_guasu_tables() -> None:
  assert ShenshaRules.GUCHEN == {
    Dizhi.亥 : Dizhi.寅, Dizhi.子 : Dizhi.寅, Dizhi.丑 : Dizhi.寅,
    Dizhi.寅 : Dizhi.巳, Dizhi.卯 : Dizhi.巳, Dizhi.辰 : Dizhi.巳,
    Dizhi.巳 : Dizhi.申, Dizhi.午 : Dizhi.申, Dizhi.未 : Dizhi.申,
    Dizhi.申 : Dizhi.亥, Dizhi.酉 : Dizhi.亥, Dizhi.戌 : Dizhi.亥,
  }
  assert ShenshaRules.GUASU == {
    Dizhi.亥 : Dizhi.戌, Dizhi.子 : Dizhi.戌, Dizhi.丑 : Dizhi.戌,
    Dizhi.寅 : Dizhi.丑, Dizhi.卯 : Dizhi.丑, Dizhi.辰 : Dizhi.丑,
    Dizhi.巳 : Dizhi.辰, Dizhi.午 : Dizhi.辰, Dizhi.未 : Dizhi.辰,
    Dizhi.申 : Dizhi.未, Dizhi.酉 : Dizhi.未, Dizhi.戌 : Dizhi.未,
  }

  for table in (ShenshaRules.GUCHEN, ShenshaRules.GUASU):
    # The tables have no fixed points and retain the four source direction groups.
    assert all(key is not target for key, target in table.items())
    assert {
      frozenset(key for key, value in table.items() if value is target)
      for target in table.values()
    } == set(DizhiRules.DIZHI_SANHUI)


def test_lushen_jinyu_tables() -> None:
  expected_lushen = {
    Tiangan.甲 : Dizhi.寅, Tiangan.乙 : Dizhi.卯,
    Tiangan.丙 : Dizhi.巳, Tiangan.丁 : Dizhi.午,
    Tiangan.戊 : Dizhi.巳, Tiangan.己 : Dizhi.午,
    Tiangan.庚 : Dizhi.申, Tiangan.辛 : Dizhi.酉,
    Tiangan.壬 : Dizhi.亥, Tiangan.癸 : Dizhi.子,
  }
  expected_jinyu = {
    Tiangan.甲 : Dizhi.辰, Tiangan.乙 : Dizhi.巳,
    Tiangan.丙 : Dizhi.未, Tiangan.丁 : Dizhi.申,
    Tiangan.戊 : Dizhi.未, Tiangan.己 : Dizhi.申,
    Tiangan.庚 : Dizhi.戌, Tiangan.辛 : Dizhi.亥,
    Tiangan.壬 : Dizhi.丑, Tiangan.癸 : Dizhi.寅,
  }

  assert ShenshaRules.LUSHEN is BaziRules.TIANGAN_LU
  assert ShenshaRules.LUSHEN == expected_lushen
  assert ShenshaRules.JINYU == expected_jinyu
  for tiangan in Tiangan:
    assert ShenshaRules.JINYU[tiangan] is Dizhi.from_index(
      (expected_lushen[tiangan].index + 2) % len(Dizhi)
    )


def test_kuigang_rule() -> None:
  assert ShenshaRules.KUIGANG == frozenset((
    Ganzhi.from_str('庚辰'),
    Ganzhi.from_str('壬辰'),
    Ganzhi.from_str('戊戌'),
    Ganzhi.from_str('庚戌'),
  ))


def test_tianshe_rule() -> None:
  assert ShenshaRules.TIANSHE == {
    Dizhi.寅 : Ganzhi.from_str('戊寅'),
    Dizhi.卯 : Ganzhi.from_str('戊寅'),
    Dizhi.辰 : Ganzhi.from_str('戊寅'),
    Dizhi.巳 : Ganzhi.from_str('甲午'),
    Dizhi.午 : Ganzhi.from_str('甲午'),
    Dizhi.未 : Ganzhi.from_str('甲午'),
    Dizhi.申 : Ganzhi.from_str('戊申'),
    Dizhi.酉 : Ganzhi.from_str('戊申'),
    Dizhi.戌 : Ganzhi.from_str('戊申'),
    Dizhi.亥 : Ganzhi.from_str('甲子'),
    Dizhi.子 : Ganzhi.from_str('甲子'),
    Dizhi.丑 : Ganzhi.from_str('甲子'),
  }


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


def test_feiren() -> None:
  expected: dict[ShenshaRules.YangrenDef, dict[Tiangan, Dizhi | None]] = {
    ShenshaRules.YangrenDef.ZIPING : {
      Tiangan.甲 : Dizhi.酉, Tiangan.乙 : None,
      Tiangan.丙 : Dizhi.子, Tiangan.丁 : None,
      Tiangan.戊 : Dizhi.子, Tiangan.己 : None,
      Tiangan.庚 : Dizhi.卯, Tiangan.辛 : None,
      Tiangan.壬 : Dizhi.午, Tiangan.癸 : None,
    },
    ShenshaRules.YangrenDef.LUMING : {
      Tiangan.甲 : Dizhi.酉, Tiangan.乙 : Dizhi.戌,
      Tiangan.丙 : Dizhi.子, Tiangan.丁 : Dizhi.丑,
      Tiangan.戊 : Dizhi.子, Tiangan.己 : Dizhi.丑,
      Tiangan.庚 : Dizhi.卯, Tiangan.辛 : Dizhi.辰,
      Tiangan.壬 : Dizhi.午, Tiangan.癸 : Dizhi.未,
    },
    ShenshaRules.YangrenDef.DIWANG : {
      Tiangan.甲 : Dizhi.酉, Tiangan.乙 : Dizhi.申,
      Tiangan.丙 : Dizhi.子, Tiangan.丁 : Dizhi.亥,
      Tiangan.戊 : Dizhi.子, Tiangan.己 : Dizhi.亥,
      Tiangan.庚 : Dizhi.卯, Tiangan.辛 : Dizhi.寅,
      Tiangan.壬 : Dizhi.午, Tiangan.癸 : Dizhi.巳,
    },
  }
  assert ShenshaRules.FEIREN == expected
  assert set(ShenshaRules.FEIREN) == set(ShenshaRules.YangrenDef)
  assert all(set(table) == set(Tiangan) for table in ShenshaRules.FEIREN.values())

  for definition in ShenshaRules.YangrenDef:
    for tiangan in Tiangan:
      yangren = ShenshaRules.YANGREN[definition][tiangan]
      feiren = ShenshaRules.FEIREN[definition][tiangan]
      if yangren is None:
        assert feiren is None
      else:
        assert feiren is Dizhi.from_index((yangren.index + 6) % len(Dizhi))


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


def test_wenchang() -> None:
  # Structure and the cross-reading relation. The per-cell values and the predicate's own
  # behaviour are pinned in `tests/utils/test_shensha_utils.py`; this layer asks a different
  # question -- do the tables hold together as a set of readings.
  # 结构与跨读法关系。逐格值与 predicate 行为钉在 utils 层，这一层问的是另一个问题：
  # 几张表作为一组读法是否自洽。
  assert set(ShenshaRules.WENCHANG) == set(ShenshaRules.WenchangDef)
  assert all(set(table) == set(Tiangan) for table in ShenshaRules.WENCHANG.values())

  xin_zi = ShenshaRules.WENCHANG[ShenshaRules.WenchangDef.XIN_ZI]
  xin_xu = ShenshaRules.WENCHANG[ShenshaRules.WenchangDef.XIN_XU]
  # The whole divergence is 辛 -- written as a difference set so a second diverging cell
  # cannot slip in unnoticed. 分歧全在辛：写成差集，第二处分歧混不进来。
  assert {tg for tg in Tiangan if xin_zi[tg] is not xin_xu[tg]} == {Tiangan.辛}
  assert xin_zi[Tiangan.辛] is Dizhi.子
  assert xin_xu[Tiangan.辛] is Dizhi.戌

  assert set(ShenshaRules.WENCHANGGUI) == set(Tiangan)


def test_taiji() -> None:
  assert set(ShenshaRules.TAIJI) == set(ShenshaRules.TaijiDef)
  assert all(set(table) == set(Tiangan) for table in ShenshaRules.TAIJI.values())

  both = ShenshaRules.TAIJI[ShenshaRules.TaijiDef.REN_GUI_BOTH]
  split = ShenshaRules.TAIJI[ShenshaRules.TaijiDef.REN_SI_GUI_SHEN]
  # 《五行精纪》 carries both readings in one line and they differ in 壬癸 only.
  # 《五行精纪》一句之内并存两读，分歧只在壬癸。
  assert {tg for tg in Tiangan if both[tg] != split[tg]} == {Tiangan.壬, Tiangan.癸}
  assert both[Tiangan.壬] == both[Tiangan.癸] == frozenset((Dizhi.巳, Dizhi.申))
  assert split[Tiangan.壬] == frozenset((Dizhi.巳,))
  assert split[Tiangan.癸] == frozenset((Dizhi.申,))

  # Unlike every other stem-anchored table, cardinality varies inside one reading -- 戊己 take
  # all four storage branches while the split reading gives 壬癸 one each. Pin the whole
  # distribution, not just that it is non-empty: a table that quietly loses 戌 from 戊 would
  # still look fine to a "every stem has at least one branch" check.
  # 与其余干锚表不同，同一读法内部势数不齐：戊己占四库，而分读法的壬癸各一支。
  # 钉整个分布而不只是「非空」——戊悄悄少掉一个戌，「每干至少一支」是看不出来的。
  storage = frozenset((Dizhi.辰, Dizhi.戌, Dizhi.丑, Dizhi.未))
  for table in ShenshaRules.TAIJI.values():
    assert table[Tiangan.戊] == storage
    assert table[Tiangan.己] == storage
  assert {len(v) for v in both.values()} == {2, 4}
  assert {len(v) for v in split.values()} == {1, 2, 4}


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
