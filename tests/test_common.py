# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_common.py

import unittest



from src.defines import Shishen, Tiangan
from src.common import frozendict
from src.data_types import GanzhiData, BaziData, HiddenTianganDict



class TestCommon(unittest.TestCase):

  def test_frozendict(self) -> None:
    fd: frozendict[int, int] = frozendict({1: 2, 3: 4})
    self.assertEqual(fd[1], 2)
    self.assertEqual(fd[3], 4)
    with self.assertRaises(TypeError):
      fd[1] = 100 # type: ignore

    # The mapping itself is detached from the source dict...
    src_dict: dict[int, list[int]] = {1: [2, 3]}
    fd2: frozendict[int, list[int]] = frozendict(src_dict)
    src_dict[9] = [9]
    self.assertNotIn(9, fd2)
    with self.assertRaises(TypeError):
      fd2[1] = [4, 5] # type: ignore
    with self.assertRaises(KeyError):
      fd2[2]

    # ...but the frozendict is shallow-frozen: values are returned as-is, not copied.
    self.assertIs(fd2[1], fd2[1])
    self.assertIs(fd2[1], src_dict[1])

  def test_frozendict_hash(self) -> None:
    # Tuple semantics: equal contents hash equal, regardless of insertion order.
    fd1: frozendict[int, int] = frozendict({1: 2, 3: 4})
    fd2: frozendict[int, int] = frozendict({3: 4, 1: 2})
    self.assertEqual(fd1, fd2)
    self.assertEqual(hash(fd1), hash(fd2))
    self.assertEqual(len({fd1, fd2}), 1)
    self.assertEqual(len({fd1, frozendict({1: 2})}), 2)

    # Unhashable contents surface as TypeError on the first hash attempt.
    with self.assertRaises(TypeError):
      hash(frozendict({1: [2, 3]}))

    # The chain #63.4 cares about: `BaziData[HiddenTianganDict]` is hashable.
    htd: HiddenTianganDict = HiddenTianganDict({Tiangan.甲: 60, Tiangan.丙: 30, Tiangan.戊: 10})
    bd: BaziData[HiddenTianganDict] = BaziData(htd, htd, htd, htd)
    self.assertEqual(hash(bd), hash(BaziData(htd, htd, htd, htd)))
    self.assertIn(bd, {bd})

  def test_pillardata(self) -> None:
    combo1: GanzhiData[str, int] = GanzhiData('a', 1)
    combo2: GanzhiData[str, int] = GanzhiData('a', 1)
    combo3: GanzhiData[str, int] = GanzhiData('a ', 1)
    combo4: GanzhiData[str, float] = GanzhiData('a', 1.1)
    self.assertEqual(combo1, combo2)
    self.assertNotEqual(combo1, combo3)
    self.assertNotEqual(combo1, combo4)

    self.assertEqual(combo1.tiangan, 'a')
    self.assertEqual(combo1.dizhi, 1)
    self.assertEqual(combo4.dizhi, 1.1)

    combo5: GanzhiData[None, Shishen] = GanzhiData(None, Shishen.七杀)
    self.assertEqual(combo5, GanzhiData(None, Shishen.七杀))
    self.assertNotEqual(combo5, GanzhiData(Shishen.七杀, Shishen.七杀))
    self.assertNotEqual(combo5, GanzhiData(None, Shishen.正官))

    self.assertNotEqual(combo5, Shishen.正官)
    self.assertNotEqual(combo5, (None, Shishen.七杀))

  def test_bazidata(self) -> None:
    bd1: BaziData[int] = BaziData(1, 2, 3, 4)
    bd2: BaziData[int] = BaziData(1, 2, 3, 4)
    bd3: BaziData[int] = BaziData(1, 2, 3, 5)
    self.assertEqual(bd1, bd2)
    self.assertNotEqual(bd1, bd3)
    self.assertNotEqual(bd1, [1, 2, 3, 4])

    self.assertEqual(bd1.year, 1)
    self.assertEqual(bd1.month, 2)
    self.assertEqual(bd1.day, 3)
    self.assertEqual(bd1.hour, 4)
    self.assertEqual(bd3.hour, 5)

    with self.assertRaises(TypeError):
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

    self.assertEqual(bd5, bd6)
    self.assertNotEqual(bd5, bd7)
    self.assertNotEqual(bd5, bd8)
    self.assertNotEqual(bd5, bd9)
    self.assertNotEqual(bd5, bd10)
