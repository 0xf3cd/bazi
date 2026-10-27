# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from bazi.defines import Zhu, 柱, TianganLayer, 天干层次


def test_pillar_order_and_aliases() -> None:
  assert 柱 is Zhu
  assert tuple(Zhu) == (Zhu.年, Zhu.月, Zhu.日, Zhu.时)
  assert (Zhu.NIAN, Zhu.YUE, Zhu.RI, Zhu.SHI) == tuple(Zhu)
  assert tuple(map(str, Zhu)) == ('年', '月', '日', '时')
  for index, position in enumerate(Zhu):
    assert position.index == index and Zhu.from_index(index) is position
    assert Zhu.from_str(str(position)) is position


def test_layer_values_and_aliases() -> None:
  assert 天干层次 is TianganLayer
  assert tuple(TianganLayer) == (TianganLayer.明干, TianganLayer.藏干)
  assert TianganLayer.MINGGAN is TianganLayer.明干
  assert TianganLayer.CANGGAN is TianganLayer.藏干
  assert tuple(map(str, TianganLayer)) == ('明干', '藏干')
