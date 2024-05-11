# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_common.py

import unittest

from typing import Optional

from src.Defines import Shishen
from src.Common import (
  classproperty, frozendict, PillarData, BaziData,
  ConstMetaClass, Const, ImmutableMetaClass, Immutable,
)

class TestCommon(unittest.TestCase):

  def test_classproperty(self) -> None:
    class TestClass:
      @classproperty
      def property1(cls) -> int:
        return 1
      @classproperty
      def property2() -> int: # type: ignore
        return 2
      @classproperty
      def property3(cls) -> int:
        return cls.property1 + cls.property2
      @classproperty
      def property4(cls) -> int:
        return TestClass.property1 + TestClass.property3
      @classproperty
      def property5() -> int: # type: ignore
        return TestClass.property1 + TestClass.property4
      @classproperty
      def property6(cls) -> int:
        return cls.property1 + TestClass.property5

    self.assertEqual(TestClass.property1, 1)
    self.assertEqual(TestClass.property2, 2)
    self.assertEqual(TestClass.property3, 3)
    self.assertEqual(TestClass.property4, 4)
    self.assertEqual(TestClass.property5, 5)
    self.assertEqual(TestClass.property6, 6)

    tc: TestClass = TestClass()
    self.assertEqual(tc.property1, 1)
    self.assertEqual(tc.property2, 2)
    self.assertEqual(tc.property3, 3)
    self.assertEqual(tc.property4, 4)
    self.assertEqual(tc.property5, 5)
    self.assertEqual(tc.property6, 6)

    with self.assertRaises(AttributeError):
      tc.property1 = 1
    with self.assertRaises(AttributeError):
      tc.property2 = 1
    with self.assertRaises(AttributeError):
      tc.property3 = 1
    with self.assertRaises(AttributeError):
      tc.property4 = 1
    with self.assertRaises(AttributeError):
      tc.property5 = 1
    with self.assertRaises(AttributeError):
      tc.property6 = 1

  def test_const_meta_class(self) -> None:
    class TestClass(metaclass=ConstMetaClass):
      A: int = 1
      B: list[int] = [2, 3]
      C: list[int] = B

    self.assertEqual(TestClass.A, 1)
    self.assertEqual(TestClass.B, [2, 3])
    self.assertEqual(TestClass.C, [2, 3])

    with self.assertRaises(AttributeError):
      del TestClass.A
    with self.assertRaises(AttributeError):
      TestClass.A = 2
    with self.assertRaises(AttributeError):
      TestClass.B = []
    with self.assertRaises(AttributeError):
      TestClass.C = []

    # `Const` just means the value can't be changed. But the underlying data may still be changed.
    # E.g., if the underlying data is a list, we can still add an element to it.
    TestClass.B.append(4) # Should not raise.
    self.assertEqual(TestClass.B, [2, 3, 4])
    self.assertEqual(TestClass.C, [2, 3, 4])

  def test_const(self) -> None:
    class TestClass(Const):
      A: int = 1
      B: list[int] = [2, 3]
      C: list[int] = B
      def somemethod(self) -> int:
        return 0
    with self.assertRaises(NotImplementedError):
      TestClass()

    with self.subTest('Test value readablility'):
      self.assertEqual(TestClass.A, 1)
      self.assertEqual(TestClass.B, [2, 3])
      self.assertEqual(TestClass.C, [2, 3])

    with self.subTest('Test constants'):
      self.assertIs(TestClass.A, TestClass.A)
      self.assertIs(TestClass.B, TestClass.B)

    with self.assertRaises(AttributeError):
      TestClass.A = 2
    with self.assertRaises(AttributeError):
      TestClass.B = []
    with self.assertRaises(AttributeError):
      TestClass.C = []
    with self.assertRaises(AttributeError):
      TestClass.somemethod = lambda _self : 1 # type: ignore

    with self.subTest('Test valur mutability'):
      TestClass.B.append(4) # Should not raise.
      self.assertEqual(TestClass.B, [2, 3, 4])
      self.assertEqual(TestClass.C, [2, 3, 4])

  def test_immutable_meta_class(self) -> None:
    class TestClass(metaclass=ImmutableMetaClass):
      A: int = 1
      B: list[int] = [2, 3]
      C: list[int] = B

    with self.subTest('Test instantiation'):
      TestClass() # Should not raise.

    with self.subTest('Test classmethod'):
      class TestSubclass1(TestClass):
        @classmethod
        def somemethod(cls):
          return 0

      self.assertEqual(TestSubclass1.somemethod(), 0)
      with self.assertRaises(AttributeError):
        TestSubclass1.somemethod = lambda : 0 # type: ignore
      with self.subTest('Test instantiation'):
        TestSubclass1() # Should not raise.
        
    with self.subTest('Test staticmethod'):
      class TestSubclass2(TestClass):
        @staticmethod
        def somemethod():
          return 0

      self.assertEqual(TestSubclass2.somemethod(), 0)
      with self.assertRaises(AttributeError):
        TestSubclass2.somemethod = lambda : 0 # type: ignore
      with self.subTest('Test instantiation'):
        TestSubclass2() # Should not raise.
        
    with self.subTest('Test normal method'):
      class TestSubclass3(TestClass):
        def somemethod(self):
          return 0
        
      with self.assertRaises(AttributeError):
        TestSubclass3.somemethod = lambda self : 0 # type: ignore
      tsc = TestSubclass3()
      self.assertEqual(tsc.somemethod(), 0)
      self.assertEqual(tsc.A, 1)
      self.assertEqual(tsc.B, [2, 3])
      self.assertEqual(tsc.C, [2, 3])
    
    with self.subTest('Attributes read'):
      self.assertEqual(TestClass.A, 1)
      self.assertEqual(TestClass.B, [2, 3])
      self.assertEqual(TestClass.C, [2, 3])
    
    with self.assertRaises(AttributeError):
      del TestClass.A
    with self.assertRaises(AttributeError):
      TestClass.A = 2
    with self.assertRaises(AttributeError):
      TestClass.B = []
    with self.assertRaises(AttributeError):
      TestClass.C = []
    with self.assertRaises(AttributeError):
      TestClass.method1 = lambda: 0 # Attribute not even exiting.
    with self.assertRaises(AttributeError):
      TestClass.method2 = lambda: 0 # Attribute not even exiting.

    with self.subTest('Attribute deepcopy'):
      self.assertEqual(TestClass.B, [2, 3])
      TestClass.B.append(3) # Should not raise.
      self.assertEqual(TestClass.B, [2, 3])

      self.assertEqual(TestClass.C, [2, 3])
      TestClass.C.append(4) # Should not raise.
      self.assertEqual(TestClass.C, [2, 3])

  def test_immutable_class(self) -> None:
    class TestClass(Immutable):
      A: int = 1
      B: list[int] = [2, 3]
      C: list[int] = B
      def somemethod(self) -> int:
        return 0
      @staticmethod
      def ret_B() -> list[int]:
        return TestClass.B
      @classproperty
      def classprop(cls) -> list[int]:
        return cls.C
      
    with self.assertRaises(NotImplementedError):
      TestClass()
      
    with self.subTest('Test value reads'):
      self.assertEqual(TestClass.B, [2, 3])
      self.assertEqual(TestClass.C, [2, 3])
      self.assertEqual(TestClass.classprop, [2, 3])

    with self.subTest('Test immutable'):
      TestClass.classprop.pop()
      TestClass.C.append(100)
      self.assertEqual(TestClass.C, [2, 3])
      self.assertEqual(TestClass.classprop, [2, 3])

      self.assertIsNot(TestClass.B, TestClass.B) # Deepcopy.

    with self.assertRaises(AttributeError):
      TestClass.A = 2
    with self.assertRaises(AttributeError):
      TestClass.B = []
    with self.assertRaises(AttributeError):
      TestClass.C = []
    with self.assertRaises(AttributeError):
      TestClass.method1 = lambda: 0 # Attribute not even exiting.
    with self.assertRaises(AttributeError):
      TestClass.somemethod = lambda: 0 # type: ignore

  def test_frozendict(self) -> None:
    fd: frozendict[int, int] = frozendict({1: 2, 3: 4})
    self.assertEqual(fd[1], 2)
    self.assertEqual(fd[3], 4)
    with self.assertRaises(TypeError):
      fd[1] = 100 # type: ignore

    fd2: frozendict[int, list[int]] = frozendict({1: [2, 3]})
    self.assertEqual(fd2[1], [2, 3])
    with self.assertRaises(TypeError):
      fd2[1] = [4, 5] # type: ignore
    with self.assertRaises(KeyError):
      fd2[2]
    
    fd2[1].append(6)
    self.assertEqual(fd2[1], [2, 3])

  def test_pillardata(self) -> None:
    combo1: PillarData[str, int] = PillarData('a', 1)
    combo2: PillarData[str, int] = PillarData('a', 1)
    combo3: PillarData[str, int] = PillarData('a ', 1)
    combo4: PillarData[str, float] = PillarData('a', 1.1)
    self.assertEqual(combo1, combo2)
    self.assertNotEqual(combo1, combo3)
    self.assertNotEqual(combo1, combo4)

    self.assertEqual(combo1.tiangan, 'a')
    self.assertEqual(combo1.dizhi, 1)
    self.assertEqual(combo4.dizhi, 1.1)

    combo5: PillarData[None, Shishen] = PillarData(None, Shishen.七杀)
    self.assertEqual(combo5, PillarData(None, Shishen.七杀))
    self.assertNotEqual(combo5, PillarData(Shishen.七杀, Shishen.七杀))
    self.assertNotEqual(combo5, PillarData(None, Shishen.正官))

    self.assertNotEqual(combo5, Shishen.正官)
    self.assertNotEqual(combo5, (None, Shishen.七杀))

  def test_bazidata(self) -> None:
    bd1: BaziData[int] = BaziData(int, [1, 2, 3, 4])
    bd2: BaziData[int] = BaziData(int, [1, 2, 3, 4])
    bd3: BaziData[int] = BaziData(int, [1, 2, 3, 5])
    self.assertEqual(bd1, bd2)
    self.assertNotEqual(bd1, bd3)
    self.assertNotEqual(bd1, [1, 2, 3, 4])

    self.assertEqual(bd1.year, 1)
    self.assertEqual(bd1.month, 2)
    self.assertEqual(bd1.day, 3)
    self.assertEqual(bd1.hour, 4)
    self.assertEqual(bd3.hour, 5)

    with self.assertRaises(AssertionError):
      BaziData(PillarData[None, Shishen], [])

    bd5: BaziData[PillarData[Optional[Shishen], Shishen]] = BaziData(PillarData[Optional[Shishen], Shishen], [
      PillarData(None, Shishen.七杀),
      PillarData(Shishen.伤官, Shishen.偏印),
      PillarData(Shishen.正官, Shishen.食神),
      PillarData(Shishen.七杀, Shishen.正官),
    ])

    bd6: BaziData[PillarData[Optional[Shishen], Shishen]] = BaziData(PillarData[Optional[Shishen], Shishen], [
      PillarData(None, Shishen.七杀),
      PillarData(Shishen.伤官, Shishen.偏印),
      PillarData(Shishen.正官, Shishen.食神),
      PillarData(Shishen.七杀, Shishen.正官),
    ])

    bd7: BaziData[PillarData[Optional[Shishen], Shishen]] = BaziData(PillarData[Optional[Shishen], Shishen], [
      PillarData(Shishen.比肩, Shishen.七杀),
      PillarData(Shishen.伤官, Shishen.偏印),
      PillarData(Shishen.正官, Shishen.食神),
      PillarData(Shishen.七杀, Shishen.正官),
    ])

    bd8: BaziData[PillarData[Optional[Shishen], Shishen]] = BaziData(PillarData[Optional[Shishen], Shishen], [
      PillarData(None, Shishen.七杀),
      PillarData(Shishen.伤官, Shishen.伤官),
      PillarData(Shishen.正官, Shishen.食神),
      PillarData(Shishen.七杀, Shishen.正官),
    ])

    bd9: BaziData[PillarData[Optional[Shishen], Shishen]] = BaziData(PillarData[Optional[Shishen], Shishen], [
      PillarData(None, Shishen.七杀),
      PillarData(Shishen.伤官, Shishen.偏印),
      PillarData(None, Shishen.食神),
      PillarData(Shishen.七杀, Shishen.正官),
    ])

    bd10: BaziData[PillarData[Optional[Shishen], Shishen]] = BaziData(PillarData[Optional[Shishen], Shishen], [
      PillarData(None, Shishen.七杀),
      PillarData(Shishen.伤官, Shishen.偏印),
      PillarData(Shishen.正官, Shishen.食神),
      PillarData(Shishen.七杀, Shishen.伤官),
    ])

    self.assertEqual(bd5, bd6)
    self.assertNotEqual(bd5, bd7)
    self.assertNotEqual(bd5, bd8)
    self.assertNotEqual(bd5, bd9)
    self.assertNotEqual(bd5, bd10)
