# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_shensha_utils.py

import random
from collections.abc import Callable

import pytest

from src.defines import Tiangan, Dizhi
from src.rules import ShenshaRules
from src.utils import shensha_utils


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


def test_taohua_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.taohua('申', Dizhi.酉) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.taohua(Dizhi.申, '酉') # type: ignore


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


def test_hongyan_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.hongyan('癸', Dizhi.申) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.hongyan(Tiangan.癸, '申') # type: ignore


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


def test_hongluan_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.hongluan('申', Dizhi.未) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.hongluan(Dizhi.申, '未') # type: ignore


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


def test_tianxi_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.tianxi('寅', Dizhi.未) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.tianxi(Dizhi.寅, '未') # type: ignore


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


def test_yima_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.yima('申', Dizhi.寅) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.yima(Dizhi.申, '寅') # type: ignore


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


def test_huagai_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.huagai('申', Dizhi.辰) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.huagai(Dizhi.申, '辰') # type: ignore


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


def test_jiangxing_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.jiangxing('申', Dizhi.子) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.jiangxing(Dizhi.申, '子') # type: ignore


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


def test_jiesha_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.jiesha('申', Dizhi.巳) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.jiesha(Dizhi.申, '巳') # type: ignore


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


def test_wangshen_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.wangshen('申', Dizhi.亥) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.wangshen(Dizhi.申, '亥') # type: ignore


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


@pytest.mark.parametrize('predicate, target', [
  (shensha_utils.guchen, Dizhi.寅),
  (shensha_utils.guasu,  Dizhi.戌),
])
def test_guchen_guasu_negative(
  predicate: Callable[[Dizhi, Dizhi], bool],
  target: Dizhi,
) -> None:
  with pytest.raises(TypeError):
    predicate('子', target) # type: ignore
  with pytest.raises(TypeError):
    predicate(Dizhi.子, str(target)) # type: ignore


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


def test_yangren_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.yangren('甲', Dizhi.卯) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.yangren(Tiangan.甲, '卯') # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.yangren(Tiangan.甲, Dizhi.卯, definition=object()) # type: ignore


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


def test_tianyi_negative() -> None:
  with pytest.raises(TypeError):
    shensha_utils.tianyi('甲', Dizhi.丑) # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.tianyi(Tiangan.甲, '丑') # type: ignore
  with pytest.raises(TypeError):
    shensha_utils.tianyi(Tiangan.甲, Dizhi.丑, definition=object()) # type: ignore
