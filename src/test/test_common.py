# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_common.py

import unittest
from src.Common import ReadOnlyMetaClass, classproperty

class TestCommon(unittest.TestCase):
  def test_readonly_meta_class(self) -> None:
    class TestClass(metaclass=ReadOnlyMetaClass):
      A: int = 1
      B: list[int] = [2, 3]
      C: list[int] = B

    with self.assertRaises(TypeError):
      # ReadOnlyMetaClass cannot contain classmethods.
      class TestSubclass1(TestClass):
        @classmethod
        def somemethod(cls):
          return 0
        
    with self.assertRaises(TypeError):
      # ReadOnlyMetaClass cannot contain staticmethods.
      class TestSubclass2(TestClass):
        @staticmethod
        def somemethod(self):
          return 0
        
    with self.assertRaises(TypeError):
      # ReadOnlyMetaClass cannot contain methods.
      class TestSubclass3(TestClass):
        def somemethod(self):
          return 0
    
    with self.subTest('Test initialization'):
      TestClass() # Should not raise.

    with self.subTest('Attributes read'):
      self.assertEqual(TestClass.A, 1)
      self.assertEqual(TestClass.B, [2, 3])
      self.assertEqual(TestClass.C, [2, 3])
    
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

  def test_classproperty(self) -> None:
    class TestClass:
      @classproperty
      def property1(self) -> int:
        return 1
      @classproperty
      def property2() -> int: # type: ignore
        return 2
      @classproperty
      def property3(self) -> int:
        return self.property1 + self.property2
      @classproperty
      def property4(self) -> int:
        return TestClass.property1 + TestClass.property3
      @classproperty
      def property5() -> int: # type: ignore
        return TestClass.property1 + TestClass.property4
      @classproperty
      def property6(self) -> int:
        return self.property1 + TestClass.property5

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
