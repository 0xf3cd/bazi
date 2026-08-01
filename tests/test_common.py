# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_common.py

import pytest



from src.defines import Shishen, Tiangan
from src.common import frozendict
from src.data_types import GanzhiData, BaziData, HiddenTianganDict



def test_frozendict() -> None:
  fd: frozendict[int, int] = frozendict({1: 2, 3: 4})
  assert fd[1] == 2
  assert fd[3] == 4
  with pytest.raises(TypeError):
    fd[1] = 100 # type: ignore

  # The mapping itself is detached from the source dict...
  src_dict: dict[int, list[int]] = {1: [2, 3]}
  fd2: frozendict[int, list[int]] = frozendict(src_dict)
  src_dict[9] = [9]
  assert 9 not in fd2
  with pytest.raises(TypeError):
    fd2[1] = [4, 5] # type: ignore
  with pytest.raises(KeyError):
    fd2[2]

  # ...but the frozendict is shallow-frozen: values are returned as-is, not copied.
  assert fd2[1] is fd2[1]
  assert fd2[1] is src_dict[1]

def test_frozendict_hash() -> None:
  # Tuple semantics: equal contents hash equal, regardless of insertion order.
  fd1: frozendict[int, int] = frozendict({1: 2, 3: 4})
  fd2: frozendict[int, int] = frozendict({3: 4, 1: 2})
  assert fd1 == fd2
  assert hash(fd1) == hash(fd2)
  assert len({fd1, fd2}) == 1
  assert len({fd1, frozendict({1: 2})}) == 2

  # Unhashable contents surface as TypeError on the first hash attempt.
  with pytest.raises(TypeError):
    hash(frozendict({1: [2, 3]}))

  # `BaziData[HiddenTianganDict]` must stay hashable -- the hidden-tiangan chain
  # is frozendict all the way down.
  htd: HiddenTianganDict = HiddenTianganDict({Tiangan.甲: 60, Tiangan.丙: 30, Tiangan.戊: 10})
  bd: BaziData[HiddenTianganDict] = BaziData(htd, htd, htd, htd)
  assert hash(bd) == hash(BaziData(htd, htd, htd, htd))
  assert bd in {bd}

def test_pillardata() -> None:
  combo1: GanzhiData[str, int] = GanzhiData('a', 1)
  combo2: GanzhiData[str, int] = GanzhiData('a', 1)
  combo3: GanzhiData[str, int] = GanzhiData('a ', 1)
  combo4: GanzhiData[str, float] = GanzhiData('a', 1.1)
  assert combo1 == combo2
  assert combo1 != combo3
  assert combo1 != combo4

  assert combo1.tiangan == 'a'
  assert combo1.dizhi == 1
  assert combo4.dizhi == 1.1

  combo5: GanzhiData[None, Shishen] = GanzhiData(None, Shishen.七杀)
  assert combo5 == GanzhiData(None, Shishen.七杀)
  assert combo5 != GanzhiData(Shishen.七杀, Shishen.七杀)
  assert combo5 != GanzhiData(None, Shishen.正官)

  assert combo5 != Shishen.正官
  assert combo5 != (None, Shishen.七杀)

def test_bazidata() -> None:
  bd1: BaziData[int] = BaziData(1, 2, 3, 4)
  bd2: BaziData[int] = BaziData(1, 2, 3, 4)
  bd3: BaziData[int] = BaziData(1, 2, 3, 5)
  assert bd1 == bd2
  assert bd1 != bd3
  assert bd1 != [1, 2, 3, 4]

  assert bd1.year == 1
  assert bd1.month == 2
  assert bd1.day == 3
  assert bd1.hour == 4
  assert bd3.hour == 5

  with pytest.raises(TypeError):
    BaziData(1, 2, 3) # type: ignore # arity is enforced by the dataclass signature now

  bd5: BaziData[GanzhiData[Shishen | None, Shishen]] = BaziData(
    GanzhiData(None, Shishen.七杀),
    GanzhiData(Shishen.伤官, Shishen.偏印),
    GanzhiData(Shishen.正官, Shishen.食神),
    GanzhiData(Shishen.七杀, Shishen.正官),
  )

  bd6: BaziData[GanzhiData[Shishen | None, Shishen]] = BaziData(
    GanzhiData(None, Shishen.七杀),
    GanzhiData(Shishen.伤官, Shishen.偏印),
    GanzhiData(Shishen.正官, Shishen.食神),
    GanzhiData(Shishen.七杀, Shishen.正官),
  )

  bd7: BaziData[GanzhiData[Shishen | None, Shishen]] = BaziData(
    GanzhiData(Shishen.比肩, Shishen.七杀),
    GanzhiData(Shishen.伤官, Shishen.偏印),
    GanzhiData(Shishen.正官, Shishen.食神),
    GanzhiData(Shishen.七杀, Shishen.正官),
  )

  bd8: BaziData[GanzhiData[Shishen | None, Shishen]] = BaziData(
    GanzhiData(None, Shishen.七杀),
    GanzhiData(Shishen.伤官, Shishen.伤官),
    GanzhiData(Shishen.正官, Shishen.食神),
    GanzhiData(Shishen.七杀, Shishen.正官),
  )

  bd9: BaziData[GanzhiData[Shishen | None, Shishen]] = BaziData(
    GanzhiData(None, Shishen.七杀),
    GanzhiData(Shishen.伤官, Shishen.偏印),
    GanzhiData(None, Shishen.食神),
    GanzhiData(Shishen.七杀, Shishen.正官),
  )

  bd10: BaziData[GanzhiData[Shishen | None, Shishen]] = BaziData(
    GanzhiData(None, Shishen.七杀),
    GanzhiData(Shishen.伤官, Shishen.偏印),
    GanzhiData(Shishen.正官, Shishen.食神),
    GanzhiData(Shishen.七杀, Shishen.伤官),
  )

  assert bd5 == bd6
  assert bd5 != bd7
  assert bd5 != bd8
  assert bd5 != bd9
  assert bd5 != bd10
