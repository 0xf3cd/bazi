# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_ganzhi.py

import pytest
import random

from src.defines import (
  Tiangan, 天干, Dizhi, 地支, Ganzhi, 干支,
)


def test_basic() -> None:
  gz_jiazi: Ganzhi = Ganzhi(Tiangan.JIA, Dizhi.ZI)
  gz_jiazi2: Ganzhi = Ganzhi(Tiangan.甲, Dizhi.子)
  gz_bingwu: Ganzhi = Ganzhi(Tiangan.丙, Dizhi.午)

  assert gz_jiazi.tiangan == Tiangan.甲
  assert gz_jiazi.dizhi == Dizhi.子
  assert gz_jiazi2.tiangan == Tiangan.甲
  assert gz_jiazi2.dizhi == Dizhi.子
  assert gz_bingwu.tiangan == Tiangan.丙
  assert gz_bingwu.dizhi == Dizhi.午
  assert gz_jiazi == gz_jiazi2
  assert gz_jiazi != gz_bingwu
  assert gz_jiazi2 != gz_bingwu

  gz_list: list[Ganzhi] = []
  for _ in range(3):
    for tg in Tiangan:
      for dz in Dizhi:
        gz_list.append(Ganzhi(tg, dz))

  # In theory, 10 tiangans and 12 dizhis can produce 120 different Ganzhis.
  assert len(set(gz_list)) == 120


def test_alias() -> None:
  assert Ganzhi is 干支
  assert Ganzhi(Tiangan.WU, Dizhi.XU) == 干支(天干.戊, 地支.戌)
  assert Ganzhi(Tiangan.WU, Dizhi.XU) != Ganzhi(Tiangan.WU, Dizhi.MAO)


def test_from_strs() -> None:
  assert Ganzhi.from_strs('甲', '子') == Ganzhi(Tiangan.甲, Dizhi.子)
  assert Ganzhi.from_strs('戊', '午') == Ganzhi(Tiangan.戊, Dizhi.午)
  assert Ganzhi.from_strs('丙', '子') != Ganzhi(Tiangan.丙, Dizhi.寅)

  with pytest.raises(ValueError):
    Ganzhi.from_strs('假', '子')
  with pytest.raises(ValueError):
    Ganzhi.from_strs('JIA', '子')
  with pytest.raises(ValueError):
    Ganzhi.from_strs('Jia', '子')
  with pytest.raises(ValueError):
    Ganzhi.from_strs('甲', '子子')
  with pytest.raises(ValueError):
    Ganzhi.from_strs('子', '甲')
  with pytest.raises(ValueError):
    Ganzhi.from_strs('子', '子')
  with pytest.raises(ValueError):
    Ganzhi.from_strs('甲', '甲')
  with pytest.raises(AssertionError):
    Ganzhi.from_strs('甲', Dizhi.子) # type: ignore
  with pytest.raises(AssertionError):
    Ganzhi.from_strs(Tiangan.甲, '子') # type: ignore
  with pytest.raises(AssertionError):
    Ganzhi.from_strs(0, 0) # type: ignore


def test_from_str() -> None:
  assert Ganzhi.from_str('甲子') == Ganzhi(Tiangan.甲, Dizhi.子)
  assert Ganzhi.from_str('戊午') == Ganzhi(Tiangan.戊, Dizhi.午)
  assert Ganzhi.from_str('丙子') != Ganzhi(Tiangan.丙, Dizhi.寅)

  with pytest.raises(ValueError):
    Ganzhi.from_str('假子')
  with pytest.raises(AssertionError):
    Ganzhi.from_str('JIA子')
  with pytest.raises(AssertionError):
    Ganzhi.from_str('Jia子')
  with pytest.raises(AssertionError):
    Ganzhi.from_str('甲子子')
  with pytest.raises(ValueError):
    Ganzhi.from_str('子甲')
  with pytest.raises(ValueError):
    Ganzhi.from_str('子子')
  with pytest.raises(ValueError):
    Ganzhi.from_str('甲甲')
  with pytest.raises(TypeError):
    Ganzhi.from_str(0) # type: ignore


def test_str() -> None:
  for tg in Tiangan.as_list():
    for dz in Dizhi.as_list():
      # `Ganzhi` should be able to hold all 120 possible Tiangan-Dizhi pairs
      assert str(Ganzhi(tg, dz)) == f'{tg}{dz}'
      assert Ganzhi.from_str(str(Ganzhi(tg, dz))) == Ganzhi(tg, dz)


def test_list_sexagenary_cycle() -> None:
  sexagenary_cycle = Ganzhi.list_sexagenary_cycle()

  assert len(sexagenary_cycle) == 60
  assert sexagenary_cycle[0] == Ganzhi(Tiangan.甲, Dizhi.子)
  assert sexagenary_cycle[-1] == Ganzhi(Tiangan.癸, Dizhi.亥)

  tg_list = Tiangan.as_list()
  dz_list = Dizhi.as_list()
  for i, gz in enumerate(sexagenary_cycle):
    assert gz.tiangan is tg_list[i % 10]
    assert gz.dizhi is dz_list[i % 12]


def test_list_sexagenary_cycle_strs() -> None:
  sexagenary_cycle_strs = Ganzhi.list_sexagenary_cycle_strs()

  assert len(sexagenary_cycle_strs) == 60
  assert sexagenary_cycle_strs[0] == '甲子'
  assert sexagenary_cycle_strs[-1] == '癸亥'

  tg_list = Tiangan.as_list()
  dz_list = Dizhi.as_list()
  for i, gz_str in enumerate(sexagenary_cycle_strs):
    assert gz_str == f'{tg_list[i % 10]}{dz_list[i % 12]}'


def test_ganzhi_next_prev() -> None:
  # Negative.
  with pytest.raises(AssertionError):
    Ganzhi(Tiangan.甲, Dizhi.子).next('1')
  with pytest.raises(AssertionError):
    Ganzhi(Tiangan.甲, Dizhi.子).prev('1')
  with pytest.raises(AssertionError):
    Ganzhi(Tiangan.甲, Dizhi.子).next(3.5)
  with pytest.raises(AssertionError):
    Ganzhi(Tiangan.甲, Dizhi.子).prev(3.5)

  def __random_gz() -> Ganzhi:
    while True:
      tg: Tiangan = random.choice(Tiangan.as_list())
      dz: Dizhi = random.choice(Dizhi.as_list())
      if (tg.index % 2) == (dz.index % 2):
        return Ganzhi(tg, dz)

  # Correctness.
  assert Ganzhi(Tiangan.甲, Dizhi.子).next(1) == Ganzhi(Tiangan.乙, Dizhi.丑)
  assert Ganzhi(Tiangan.甲, Dizhi.子).prev(-1) == Ganzhi(Tiangan.乙, Dizhi.丑)
  assert Ganzhi(Tiangan.甲, Dizhi.子).prev(1) == Ganzhi(Tiangan.癸, Dizhi.亥)
  assert Ganzhi(Tiangan.甲, Dizhi.子).next(-1) == Ganzhi(Tiangan.癸, Dizhi.亥)

  cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
  for _ in range(16):
    random_gz1: Ganzhi = __random_gz()
    assert random_gz1 == random_gz1.next(0)
    assert random_gz1 == random_gz1.next(60)
    assert random_gz1 == random_gz1.prev(0)
    assert random_gz1 == random_gz1.prev(60)

    random_int: int = random.randint(-1000, 1000)
    assert random_gz1.next(random_int) == \
           cycle[(cycle.index(random_gz1) + random_int) % 60]
    assert random_gz1.prev(random_int) == \
           cycle[(cycle.index(random_gz1) - random_int) % 60]

  # Immutability.
  gz: Ganzhi = Ganzhi(Tiangan.甲, Dizhi.子)
  assert gz is not gz.next(0)
  assert gz is not gz.prev(0)

  # Consistency.
  for _ in range(16):
    random_gz2: Ganzhi = __random_gz()
    for __ in range(16):
      x: int = random.randint(-1000, 1000)
      assert random_gz2 == \
             random_gz2.next(x).prev(x)
      assert random_gz2 == \
             random_gz2.prev(x).next(x)
      assert random_gz2.next(x) == random_gz2.prev(-x)
      assert random_gz2.prev(x) == random_gz2.next(-x)
