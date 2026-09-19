# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shensha_utils.py

import random
import inspect
from collections.abc import Callable

import pytest

from bazi.defines import Tiangan, Dizhi, Ganzhi
from bazi.rules import ShenshaRules
from bazi.utils import shensha_utils


def test_predicate_argument_types() -> None:
  for name, predicate in inspect.getmembers(shensha_utils, inspect.isfunction):
    if name.startswith('_') or predicate.__module__ != shensha_utils.__name__:
      continue
    # Whole-pillar predicates have their own negative tests below.
    if predicate in (shensha_utils.kuigang, shensha_utils.tianshe):
      continue
    parameters = tuple(inspect.signature(predicate).parameters.values())
    assert len(parameters) in (2, 3), name
    key_type = parameters[0].annotation
    assert key_type in (Tiangan, Dizhi), name
    assert parameters[1].annotation is Dizhi, name
    key = Tiangan.甲 if key_type is Tiangan else Dizhi.子

    with pytest.raises(TypeError, match=f'Expected {key_type.__name__}'):
      predicate(str(key), Dizhi.子)
    with pytest.raises(TypeError, match='Expected Dizhi'):
      predicate(key, '子')
    if len(parameters) == 3:
      definition = parameters[2]
      assert definition.name == 'definition', name
      assert definition.kind is inspect.Parameter.KEYWORD_ONLY, name
      with pytest.raises(TypeError, match=f'Expected {type(definition.default).__name__}'):
        predicate(key, Dizhi.子, definition=object())


def test_taohua() -> None:
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi(k_str) : Dizhi(v_str)
    for k_strs, v_str in zip(['申子辰', '寅午戌', '亥卯未', '巳酉丑'], '酉卯子午')
    for k_str in k_strs
  }

  for dz1 in Dizhi:
    for dz2 in Dizhi:
      assert shensha_utils.taohua(dz1, dz2) == (expected_table[dz1] is dz2)
      assert shensha_utils.taohua(dz1, dz2) == (expected_table[dz1] is dz2)


def test_hongyan() -> None:
  expected_table: dict[Dizhi, list[Tiangan]] = {
    Dizhi.午 : [Tiangan.甲],
    Dizhi.申 : [Tiangan.乙, Tiangan.癸],
    Dizhi.寅 : [Tiangan.丙],
    Dizhi.未 : [Tiangan.丁],
    Dizhi.辰 : [Tiangan.戊, Tiangan.己],
    Dizhi.戌 : [Tiangan.庚],
    Dizhi.酉 : [Tiangan.辛],
    Dizhi.子 : [Tiangan.壬],
  }

  for _ in range(16):
    tg, dz = random.choice(Tiangan.as_list()), random.choice(Dizhi.as_list())
    expected_result: bool = dz in expected_table and tg in expected_table[dz]
    assert shensha_utils.hongyan(tg, dz) == expected_result
    assert shensha_utils.hongyan(tg, dz) == expected_result # Second call must answer the same (determinism across calls).


def test_hongluan() -> None:
  expected_table: dict[Dizhi, Dizhi] = {}
  for dz1, dz2 in [
    (Dizhi.子, Dizhi.卯),
    (Dizhi.丑, Dizhi.寅),
    (Dizhi.辰, Dizhi.亥),
    (Dizhi.巳, Dizhi.戌),
    (Dizhi.午, Dizhi.酉),
    (Dizhi.未, Dizhi.申),
  ]:
    expected_table[dz1] = dz2
    expected_table[dz2] = dz1

  for _ in range(16):
    dz1, dz2 = random.choices(Dizhi.as_list(), k=2)
    assert shensha_utils.hongluan(dz1, dz2) == (expected_table[dz1] is dz2)
    assert shensha_utils.hongluan(dz1, dz2) == (expected_table[dz1] is dz2) # Second call must answer the same (determinism across calls).


def test_tianxi() -> None:
  expected_table: dict[Dizhi, Dizhi] = {}
  for dz1, dz2 in [
    (Dizhi.子, Dizhi.酉),
    (Dizhi.丑, Dizhi.申),
    (Dizhi.未, Dizhi.寅),
    (Dizhi.午, Dizhi.卯),
    (Dizhi.辰, Dizhi.巳),
    (Dizhi.戌, Dizhi.亥),
  ]:
    expected_table[dz1] = dz2
    expected_table[dz2] = dz1

  for _ in range(16):
    dz1, dz2 = random.choices(Dizhi.as_list(), k=2)
    assert shensha_utils.tianxi(dz1, dz2) == (expected_table[dz1] is dz2)
    assert shensha_utils.tianxi(dz1, dz2) == (expected_table[dz1] is dz2) # Second call must answer the same (determinism across calls).


def test_yima() -> None:
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi(k_str) : Dizhi(v_str)
    for k_strs, v_str in zip(['申子辰', '寅午戌', '亥卯未', '巳酉丑'], '寅申巳亥')
    for k_str in k_strs
  }

  for dz1 in Dizhi:
    for dz2 in Dizhi:
      assert shensha_utils.yima(dz1, dz2) == (expected_table[dz1] is dz2)
      assert shensha_utils.yima(dz1, dz2) == (expected_table[dz1] is dz2)


def test_huagai() -> None:
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi(k_str) : Dizhi(v_str)
    for k_strs, v_str in {
      '寅午戌' : '戌',
      '亥卯未' : '未',
      '申子辰' : '辰',
      '巳酉丑' : '丑',
    }.items()
    for k_str in k_strs
  }

  for dz1 in Dizhi:
    for dz2 in Dizhi:
      assert shensha_utils.huagai(dz1, dz2) == (expected_table[dz1] is dz2)
      assert shensha_utils.huagai(dz1, dz2) == (expected_table[dz1] is dz2)


def test_jiangxing() -> None:
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi.申 : Dizhi.子, Dizhi.子 : Dizhi.子, Dizhi.辰 : Dizhi.子,
    Dizhi.寅 : Dizhi.午, Dizhi.午 : Dizhi.午, Dizhi.戌 : Dizhi.午,
    Dizhi.亥 : Dizhi.卯, Dizhi.卯 : Dizhi.卯, Dizhi.未 : Dizhi.卯,
    Dizhi.巳 : Dizhi.酉, Dizhi.酉 : Dizhi.酉, Dizhi.丑 : Dizhi.酉,
  }

  for dz1 in Dizhi:
    for dz2 in Dizhi:
      assert shensha_utils.jiangxing(dz1, dz2) == (expected_table[dz1] is dz2)
      assert shensha_utils.jiangxing(dz1, dz2) == (expected_table[dz1] is dz2)


def test_zaisha() -> None:
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi.申 : Dizhi.午, Dizhi.子 : Dizhi.午, Dizhi.辰 : Dizhi.午,
    Dizhi.寅 : Dizhi.子, Dizhi.午 : Dizhi.子, Dizhi.戌 : Dizhi.子,
    Dizhi.巳 : Dizhi.卯, Dizhi.酉 : Dizhi.卯, Dizhi.丑 : Dizhi.卯,
    Dizhi.亥 : Dizhi.酉, Dizhi.卯 : Dizhi.酉, Dizhi.未 : Dizhi.酉,
  }

  for key_dizhi in Dizhi:
    for other_dizhi in Dizhi:
      expected = expected_table[key_dizhi] is other_dizhi
      assert shensha_utils.zaisha(key_dizhi, other_dizhi) == expected
      assert shensha_utils.zaisha(key_dizhi, other_dizhi) == expected


def test_jiesha() -> None:
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi.申 : Dizhi.巳, Dizhi.子 : Dizhi.巳, Dizhi.辰 : Dizhi.巳,
    Dizhi.寅 : Dizhi.亥, Dizhi.午 : Dizhi.亥, Dizhi.戌 : Dizhi.亥,
    Dizhi.亥 : Dizhi.申, Dizhi.卯 : Dizhi.申, Dizhi.未 : Dizhi.申,
    Dizhi.巳 : Dizhi.寅, Dizhi.酉 : Dizhi.寅, Dizhi.丑 : Dizhi.寅,
  }

  for dz1 in Dizhi:
    for dz2 in Dizhi:
      assert shensha_utils.jiesha(dz1, dz2) == (expected_table[dz1] is dz2)
      assert shensha_utils.jiesha(dz1, dz2) == (expected_table[dz1] is dz2)


def test_wangshen() -> None:
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi.申 : Dizhi.亥, Dizhi.子 : Dizhi.亥, Dizhi.辰 : Dizhi.亥,
    Dizhi.寅 : Dizhi.巳, Dizhi.午 : Dizhi.巳, Dizhi.戌 : Dizhi.巳,
    Dizhi.亥 : Dizhi.寅, Dizhi.卯 : Dizhi.寅, Dizhi.未 : Dizhi.寅,
    Dizhi.巳 : Dizhi.申, Dizhi.酉 : Dizhi.申, Dizhi.丑 : Dizhi.申,
  }

  for dz1 in Dizhi:
    for dz2 in Dizhi:
      assert shensha_utils.wangshen(dz1, dz2) == (expected_table[dz1] is dz2)
      assert shensha_utils.wangshen(dz1, dz2) == (expected_table[dz1] is dz2)


@pytest.mark.parametrize('predicate, targets', [
  (shensha_utils.guchen, '寅巳申亥'),
  (shensha_utils.guasu,  '戌丑辰未'),
])
def test_guchen_guasu(
  predicate: Callable[[Dizhi, Dizhi], bool],
  targets: str,
) -> None:
  direction_groups = ('亥子丑', '寅卯辰', '巳午未', '申酉戌')
  expected_table: dict[Dizhi, Dizhi] = {
    Dizhi(key) : Dizhi(target)
    for keys, target in zip(direction_groups, targets)
    for key in keys
  }
  for year_dizhi in Dizhi:
    for other_dizhi in Dizhi:
      expected = expected_table[year_dizhi] is other_dizhi
      assert predicate(year_dizhi, other_dizhi) == expected
      assert predicate(year_dizhi, other_dizhi) == expected # Repeated lookup must answer the same.


@pytest.mark.parametrize('predicate, expected_table', [
  (shensha_utils.lushen, {
    Tiangan.甲 : Dizhi.寅, Tiangan.乙 : Dizhi.卯,
    Tiangan.丙 : Dizhi.巳, Tiangan.丁 : Dizhi.午,
    Tiangan.戊 : Dizhi.巳, Tiangan.己 : Dizhi.午,
    Tiangan.庚 : Dizhi.申, Tiangan.辛 : Dizhi.酉,
    Tiangan.壬 : Dizhi.亥, Tiangan.癸 : Dizhi.子,
  }),
  (shensha_utils.jinyu, {
    Tiangan.甲 : Dizhi.辰, Tiangan.乙 : Dizhi.巳,
    Tiangan.丙 : Dizhi.未, Tiangan.丁 : Dizhi.申,
    Tiangan.戊 : Dizhi.未, Tiangan.己 : Dizhi.申,
    Tiangan.庚 : Dizhi.戌, Tiangan.辛 : Dizhi.亥,
    Tiangan.壬 : Dizhi.丑, Tiangan.癸 : Dizhi.寅,
  }),
])
def test_lushen_jinyu(
  predicate: Callable[[Tiangan, Dizhi], bool],
  expected_table: dict[Tiangan, Dizhi],
) -> None:
  for tiangan in Tiangan:
    for dizhi in Dizhi:
      expected = expected_table[tiangan] is dizhi
      assert predicate(tiangan, dizhi) == expected
      assert predicate(tiangan, dizhi) == expected # Repeated lookup must answer the same.


def test_kuigang() -> None:
  cycle = Ganzhi.list_sexagenary_cycle()
  expected = {
    Ganzhi.from_str('庚辰'),
    Ganzhi.from_str('壬辰'),
    Ganzhi.from_str('戊戌'),
    Ganzhi.from_str('庚戌'),
  }
  assert len(cycle) == 60
  assert {ganzhi for ganzhi in cycle if shensha_utils.kuigang(ganzhi)} == expected
  assert all(shensha_utils.kuigang(ganzhi) == (ganzhi in expected) for ganzhi in cycle)
  assert not shensha_utils.kuigang(Ganzhi.from_str('甲辰'))


def test_kuigang_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.kuigang('庚辰') # type: ignore


def test_tianshe() -> None:
  cycle = Ganzhi.list_sexagenary_cycle()
  expected = {
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
  assert len(cycle) == 60
  assert set(expected) == set(Dizhi)
  for month_dizhi in Dizhi:
    for day_ganzhi in cycle:
      assert shensha_utils.tianshe(month_dizhi, day_ganzhi) == (
        expected[month_dizhi] == day_ganzhi
      )


def test_tianshe_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.tianshe('寅', Ganzhi.from_str('戊寅')) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.tianshe(Dizhi.寅, '戊寅') # type: ignore


def test_yangren() -> None:
  expected: dict[ShenshaRules.YangrenDef, dict[Tiangan, Dizhi | None]] = {
    ShenshaRules.YangrenDef.ZIPING : {
      Tiangan.甲 : Dizhi.卯, Tiangan.乙 : None,
      Tiangan.丙 : Dizhi.午, Tiangan.丁 : None,
      Tiangan.戊 : Dizhi.午, Tiangan.己 : None,
      Tiangan.庚 : Dizhi.酉, Tiangan.辛 : None,
      Tiangan.壬 : Dizhi.子, Tiangan.癸 : None,
    },
    ShenshaRules.YangrenDef.LUMING : {
      Tiangan.甲 : Dizhi.卯, Tiangan.乙 : Dizhi.辰,
      Tiangan.丙 : Dizhi.午, Tiangan.丁 : Dizhi.未,
      Tiangan.戊 : Dizhi.午, Tiangan.己 : Dizhi.未,
      Tiangan.庚 : Dizhi.酉, Tiangan.辛 : Dizhi.戌,
      Tiangan.壬 : Dizhi.子, Tiangan.癸 : Dizhi.丑,
    },
    ShenshaRules.YangrenDef.DIWANG : {
      Tiangan.甲 : Dizhi.卯, Tiangan.乙 : Dizhi.寅,
      Tiangan.丙 : Dizhi.午, Tiangan.丁 : Dizhi.巳,
      Tiangan.戊 : Dizhi.午, Tiangan.己 : Dizhi.巳,
      Tiangan.庚 : Dizhi.酉, Tiangan.辛 : Dizhi.申,
      Tiangan.壬 : Dizhi.子, Tiangan.癸 : Dizhi.亥,
    },
  }

  for yangren_def in ShenshaRules.YangrenDef:
    for tg in Tiangan:
      for dz in Dizhi:
        assert shensha_utils.yangren(
          tg,
          dz,
          definition=yangren_def,
        ) == (expected[yangren_def][tg] is dz)

  for tg in Tiangan:
    for dz in Dizhi:
      assert shensha_utils.yangren(tg, dz) == shensha_utils.yangren(
        tg,
        dz,
        definition=ShenshaRules.YangrenDef.ZIPING,
      )


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

  for feiren_def in ShenshaRules.YangrenDef:
    for tiangan in Tiangan:
      for dizhi in Dizhi:
        assert shensha_utils.feiren(
          tiangan,
          dizhi,
          definition=feiren_def,
        ) == (expected[feiren_def][tiangan] is dizhi)

  for tiangan in Tiangan:
    for dizhi in Dizhi:
      assert shensha_utils.feiren(tiangan, dizhi) == shensha_utils.feiren(
        tiangan,
        dizhi,
        definition=ShenshaRules.YangrenDef.ZIPING,
      )


def test_tianyi() -> None:
  expected: dict[ShenshaRules.TianyiDef, dict[Tiangan, frozenset[Dizhi]]] = {
    ShenshaRules.TianyiDef.GENG_WITH_JIA_WU : {
      Tiangan.甲 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.丙 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.戊 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.己 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.庚 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.辛 : frozenset((Dizhi.午, Dizhi.寅)),
      Tiangan.壬 : frozenset((Dizhi.卯, Dizhi.巳)),
      Tiangan.癸 : frozenset((Dizhi.卯, Dizhi.巳)),
    },
    ShenshaRules.TianyiDef.GENG_WITH_XIN : {
      Tiangan.甲 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.丙 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.亥, Dizhi.酉)),
      Tiangan.戊 : frozenset((Dizhi.丑, Dizhi.未)),
      Tiangan.己 : frozenset((Dizhi.子, Dizhi.申)),
      Tiangan.庚 : frozenset((Dizhi.午, Dizhi.寅)),
      Tiangan.辛 : frozenset((Dizhi.午, Dizhi.寅)),
      Tiangan.壬 : frozenset((Dizhi.卯, Dizhi.巳)),
      Tiangan.癸 : frozenset((Dizhi.卯, Dizhi.巳)),
    },
    ShenshaRules.TianyiDef.YANGGUI : {
      Tiangan.甲 : frozenset((Dizhi.未,)),
      Tiangan.乙 : frozenset((Dizhi.申,)),
      Tiangan.丙 : frozenset((Dizhi.酉,)),
      Tiangan.丁 : frozenset((Dizhi.亥,)),
      Tiangan.戊 : frozenset((Dizhi.丑,)),
      Tiangan.己 : frozenset((Dizhi.子,)),
      Tiangan.庚 : frozenset((Dizhi.丑,)),
      Tiangan.辛 : frozenset((Dizhi.寅,)),
      Tiangan.壬 : frozenset((Dizhi.卯,)),
      Tiangan.癸 : frozenset((Dizhi.巳,)),
    },
    ShenshaRules.TianyiDef.YINGUI : {
      Tiangan.甲 : frozenset((Dizhi.丑,)),
      Tiangan.乙 : frozenset((Dizhi.子,)),
      Tiangan.丙 : frozenset((Dizhi.亥,)),
      Tiangan.丁 : frozenset((Dizhi.酉,)),
      Tiangan.戊 : frozenset((Dizhi.未,)),
      Tiangan.己 : frozenset((Dizhi.申,)),
      Tiangan.庚 : frozenset((Dizhi.未,)),
      Tiangan.辛 : frozenset((Dizhi.午,)),
      Tiangan.壬 : frozenset((Dizhi.巳,)),
      Tiangan.癸 : frozenset((Dizhi.卯,)),
    },
  }

  for tianyi_def in ShenshaRules.TianyiDef:
    for tg in Tiangan:
      for dz in Dizhi:
        assert shensha_utils.tianyi(
          tg,
          dz,
          definition=tianyi_def,
        ) == (dz in expected[tianyi_def][tg])

  for tg in Tiangan:
    for dz in Dizhi:
      assert shensha_utils.tianyi(tg, dz) == shensha_utils.tianyi(
        tg,
        dz,
        definition=ShenshaRules.TianyiDef.GENG_WITH_JIA_WU,
      )


def test_wenchang() -> None:
  # The two readings differ in 辛 only; every other stem is written out so a table-wide
  # edit cannot hide behind the one cell everybody looks at.
  # 两读只在辛分歧；其余九干逐格写出，免得改动躲在唯一有人盯着的那一格背后。
  expected: dict[ShenshaRules.WenchangDef, dict[Tiangan, Dizhi]] = {
    ShenshaRules.WenchangDef.XIN_ZI : {
      Tiangan.甲 : Dizhi.巳,
      Tiangan.乙 : Dizhi.午,
      Tiangan.丙 : Dizhi.申,
      Tiangan.丁 : Dizhi.酉,
      Tiangan.戊 : Dizhi.申,
      Tiangan.己 : Dizhi.酉,
      Tiangan.庚 : Dizhi.亥,
      Tiangan.辛 : Dizhi.子,
      Tiangan.壬 : Dizhi.寅,
      Tiangan.癸 : Dizhi.卯,
    },
    ShenshaRules.WenchangDef.XIN_XU : {
      Tiangan.甲 : Dizhi.巳,
      Tiangan.乙 : Dizhi.午,
      Tiangan.丙 : Dizhi.申,
      Tiangan.丁 : Dizhi.酉,
      Tiangan.戊 : Dizhi.申,
      Tiangan.己 : Dizhi.酉,
      Tiangan.庚 : Dizhi.亥,
      Tiangan.辛 : Dizhi.戌,
      Tiangan.壬 : Dizhi.寅,
      Tiangan.癸 : Dizhi.卯,
    },
  }

  for wenchang_def in ShenshaRules.WenchangDef:
    for tg in Tiangan:
      for dz in Dizhi:
        assert shensha_utils.wenchang(tg, dz, definition=wenchang_def) == (
          expected[wenchang_def][tg] is dz
        )

  # The default is the 辛=子 reading.
  for tg in Tiangan:
    for dz in Dizhi:
      assert shensha_utils.wenchang(tg, dz) == shensha_utils.wenchang(
        tg,
        dz,
        definition=ShenshaRules.WenchangDef.XIN_ZI,
      )

  # 辛 is the whole of the divergence: the two readings agree on the other nine stems and
  # disagree on that one. Written as an executor so a second diverging cell cannot be
  # introduced quietly.
  # 分歧全在辛：两读在其余九干一致、在辛不一致。写成执行者，免得第二处分歧被悄悄塞进来。
  differing = {
    tg for tg in Tiangan for dz in Dizhi
    if shensha_utils.wenchang(tg, dz, definition=ShenshaRules.WenchangDef.XIN_ZI)
    != shensha_utils.wenchang(tg, dz, definition=ShenshaRules.WenchangDef.XIN_XU)
  }
  assert differing == {Tiangan.辛}


def test_wenchanggui() -> None:
  expected: dict[Tiangan, Dizhi] = {
    Tiangan.甲 : Dizhi.巳,
    Tiangan.乙 : Dizhi.亥,
    Tiangan.丙 : Dizhi.戌,
    Tiangan.丁 : Dizhi.辰,
    Tiangan.戊 : Dizhi.申,
    Tiangan.己 : Dizhi.午,
    Tiangan.庚 : Dizhi.寅,
    Tiangan.辛 : Dizhi.未,
    Tiangan.壬 : Dizhi.卯,
    Tiangan.癸 : Dizhi.丑,
  }

  for tg in Tiangan:
    for dz in Dizhi:
      assert shensha_utils.wenchanggui(tg, dz) == (expected[tg] is dz)


def test_wenchang_and_wenchanggui_are_two_stars() -> None:
  # They are separate entries because they are separate stars: the tables agree on 甲 → 巳
  # and 戊 → 申, and differ on the other eight stems. If a later change collapses them into
  # one, this fails.
  # 两者分列是因为本就是两颗星：两表在甲→巳、戊→申两格相同，其余八干皆异。
  # 将来谁把它们并成一条，这里会响。
  agreeing = {
    tg for tg in Tiangan
    if all(
      shensha_utils.wenchang(tg, dz) == shensha_utils.wenchanggui(tg, dz)
      for dz in Dizhi
    )
  }
  assert agreeing == {Tiangan.甲, Tiangan.戊}


def test_taiji() -> None:
  # Both readings written out in full. 甲乙 / 丙丁 / 戊己 / 庚辛 pair up, but they are spelled
  # per stem rather than as pairs -- a table that quietly breaks a pair would still satisfy
  # any check written in terms of the pairs.
  # 两读逐格写全。甲乙 / 丙丁 / 戊己 / 庚辛 虽然成对，但逐干写出：表里悄悄拆散一对，
  # 按「对」写的检查是发现不了的。
  storage = frozenset((Dizhi.辰, Dizhi.戌, Dizhi.丑, Dizhi.未))
  expected: dict[ShenshaRules.TaijiDef, dict[Tiangan, frozenset[Dizhi]]] = {
    ShenshaRules.TaijiDef.REN_GUI_BOTH : {
      Tiangan.甲 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.丙 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.戊 : storage,
      Tiangan.己 : storage,
      Tiangan.庚 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.辛 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.壬 : frozenset((Dizhi.巳, Dizhi.申)),
      Tiangan.癸 : frozenset((Dizhi.巳, Dizhi.申)),
    },
    ShenshaRules.TaijiDef.REN_SI_GUI_SHEN : {
      Tiangan.甲 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.乙 : frozenset((Dizhi.子, Dizhi.午)),
      Tiangan.丙 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.丁 : frozenset((Dizhi.卯, Dizhi.酉)),
      Tiangan.戊 : storage,
      Tiangan.己 : storage,
      Tiangan.庚 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.辛 : frozenset((Dizhi.寅, Dizhi.亥)),
      Tiangan.壬 : frozenset((Dizhi.巳,)),
      Tiangan.癸 : frozenset((Dizhi.申,)),
    },
  }

  for taiji_def in ShenshaRules.TaijiDef:
    for tg in Tiangan:
      for dz in Dizhi:
        assert shensha_utils.taiji(tg, dz, definition=taiji_def) == (dz in expected[taiji_def][tg])

  # The default is the reading 《五行精纪》's 「一作」 points to.
  for tg in Tiangan:
    for dz in Dizhi:
      assert shensha_utils.taiji(tg, dz) == shensha_utils.taiji(
        tg,
        dz,
        definition=ShenshaRules.TaijiDef.REN_GUI_BOTH,
      )

  # 壬癸 is the whole of the divergence, and it is one-way: the split reading drops a branch
  # from each, never adds one. 分歧全在壬癸，且是单向的：分读法各去一支，不会多出一支。
  differing = {
    tg for tg in Tiangan for dz in Dizhi
    if shensha_utils.taiji(tg, dz, definition=ShenshaRules.TaijiDef.REN_GUI_BOTH)
    != shensha_utils.taiji(tg, dz, definition=ShenshaRules.TaijiDef.REN_SI_GUI_SHEN)
  }
  assert differing == {Tiangan.壬, Tiangan.癸}
  for tg in Tiangan:
    for dz in Dizhi:
      if shensha_utils.taiji(tg, dz, definition=ShenshaRules.TaijiDef.REN_SI_GUI_SHEN):
        assert shensha_utils.taiji(tg, dz, definition=ShenshaRules.TaijiDef.REN_GUI_BOTH)


def test_guoyin() -> None:
  # Two readings, twenty cells, written out per stem. The derivation from 禄 is pinned in
  # `tests/test_rules.py`; here the literals are spelled independently so that a change to
  # the offset story and a change to the table cannot cancel each other out.
  # 两读二十格逐干写出。由禄推导那一层钉在 `test_rules.py`；此处独立写字面值，
  # 使「偏移说法」与「表」两处改动无法互相抵消。
  expected: dict[ShenshaRules.GuoyinDef, dict[Tiangan, Dizhi]] = {
    ShenshaRules.GuoyinDef.WUXING_JINGJI : {
      Tiangan.甲 : Dizhi.酉, Tiangan.乙 : Dizhi.戌, Tiangan.丙 : Dizhi.子, Tiangan.丁 : Dizhi.丑,
      Tiangan.戊 : Dizhi.子, Tiangan.己 : Dizhi.丑, Tiangan.庚 : Dizhi.卯, Tiangan.辛 : Dizhi.辰,
      Tiangan.壬 : Dizhi.午, Tiangan.癸 : Dizhi.未,
    },
    ShenshaRules.GuoyinDef.MODERN : {
      Tiangan.甲 : Dizhi.戌, Tiangan.乙 : Dizhi.亥, Tiangan.丙 : Dizhi.丑, Tiangan.丁 : Dizhi.寅,
      Tiangan.戊 : Dizhi.丑, Tiangan.己 : Dizhi.寅, Tiangan.庚 : Dizhi.辰, Tiangan.辛 : Dizhi.巳,
      Tiangan.壬 : Dizhi.未, Tiangan.癸 : Dizhi.申,
    },
  }

  for guoyin_def in ShenshaRules.GuoyinDef:
    for tg in Tiangan:
      for dz in Dizhi:
        assert shensha_utils.guoyin(tg, dz, definition=guoyin_def) == (expected[guoyin_def][tg] is dz)

  # The default is the modern table.
  for tg in Tiangan:
    for dz in Dizhi:
      assert shensha_utils.guoyin(tg, dz) == shensha_utils.guoyin(
        tg,
        dz,
        definition=ShenshaRules.GuoyinDef.MODERN,
      )

  # No stem answers the same branch under two readings, so switching the knob always moves
  # the hit rather than dropping it -- unlike 太极, where the split reading only removes a
  # branch. 无一干在两读下答同一支，故切旋钮总是「换一支」而非「少一支」——
  # 与太极不同，太极的分读法只去支。
  for tg in Tiangan:
    assert len({expected[d][tg] for d in ShenshaRules.GuoyinDef}) == len(
      ShenshaRules.GuoyinDef
    ), tg
