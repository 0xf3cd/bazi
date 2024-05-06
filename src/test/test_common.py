# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_common.py

import random
import unittest

from src.Common import classproperty, cached_classproperty

class TestCommon(unittest.TestCase):
  def test_classproperty_decorator(self) -> None:
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

  def test_cached_classproperty_decorator(self) -> None:
    class TestClass:
      @cached_classproperty
      def property1(self) -> int:
        return 1
      @cached_classproperty
      def property2() -> int: # type: ignore
        return 2
      @cached_classproperty
      def property3(self) -> int:
        return self.property1 + self.property2
      @cached_classproperty
      def property4(self) -> int:
        return TestClass.property1 + TestClass.property3
      @cached_classproperty
      def property5() -> int: # type: ignore
        return TestClass.property1 + TestClass.property4
      @cached_classproperty
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

  def test_decorators(self) -> None:
    class TestClass:
      @cached_classproperty
      def property1(self) -> int:
        return 1
      @cached_classproperty
      def property2() -> int: # type: ignore
        return 2
      @classproperty
      def property3(self) -> int:
        return self.property1 + self.property2
      @cached_classproperty
      def property4(self) -> int:
        return TestClass.property1 + TestClass.property3
      @classproperty
      def property5() -> int: # type: ignore
        return TestClass.property1 + TestClass.property4
      @classproperty
      def property6(self) -> int:
        return self.property1 + TestClass.property5
      @cached_classproperty
      def property7(self) -> int:
        attr: dict[int, str] = {
          1: 'property1',
          2: 'property2',
          3: 'property3',
          4: 'property4',
          5: 'property5',
          6: 'property6',
        }
        rand_int: int = random.randint(1, 6)
        another_int: int = 7 - rand_int
        attr1: str = attr[rand_int]
        attr2: str = attr[another_int]
        return getattr(random.choice([self, TestClass]), attr1) + \
               getattr(random.choice([self, TestClass]), attr2)
      @classproperty
      def property8(self) -> int:
        attr: dict[int, str] = {
          1: 'property1',
          2: 'property2',
          3: 'property3',
          4: 'property4',
          5: 'property5',
          6: 'property6',
          7: 'property7',
        }
        rand_int: int = random.randint(1, 7)
        another_int: int = 8 - rand_int
        attr1: str = attr[rand_int]
        attr2: str = attr[another_int]
        return getattr(random.choice([self, TestClass]), attr1) + \
               getattr(random.choice([self, TestClass]), attr2)
      @property
      def property9(self) -> int:
        attr: dict[int, str] = {
          1: 'property1',
          2: 'property2',
          3: 'property3',
          4: 'property4',
          5: 'property5',
          6: 'property6',
          7: 'property7',
          8: 'property8',
        }
        rand_int: int = random.randint(1, 8)
        another_int: int = 9 - rand_int
        attr1: str = attr[rand_int]
        attr2: str = attr[another_int]
        return getattr(random.choice([self, TestClass]), attr1) + \
               getattr(random.choice([self, TestClass]), attr2)

    self.assertEqual(TestClass.property1, 1)
    self.assertEqual(TestClass.property2, 2)
    self.assertEqual(TestClass.property3, 3)
    self.assertEqual(TestClass.property4, 4)
    self.assertEqual(TestClass.property5, 5)
    self.assertEqual(TestClass.property6, 6)
    self.assertEqual(TestClass.property7, 7)
    self.assertEqual(TestClass.property8, 8)

    for _ in range(10):
      tc: TestClass = TestClass()
      self.assertEqual(tc.property1, 1)
      self.assertEqual(tc.property2, 2)
      self.assertEqual(tc.property3, 3)
      self.assertEqual(tc.property4, 4)
      self.assertEqual(tc.property5, 5)
      self.assertEqual(tc.property6, 6)
      self.assertEqual(tc.property7, 7)
      self.assertEqual(tc.property8, 8)
      self.assertEqual(tc.property9, 9)

  def test_cached(self) -> None:
    class TestClass:
      sm_count: int = 0
      @classproperty
      def noncached_list(self) -> list[int]:
        TestClass.sm_count += 1
        return [1, 2, 3, 4, 5]
      @cached_classproperty
      def cached_list1() -> list[int]: # type: ignore
        TestClass.sm_count += 1
        return [1, 2, 3, 4, 5]
      @cached_classproperty
      def cached_list2(self) -> list[int]:
        TestClass.sm_count += 1
        return [1, 2, 3, 4, 5]
      @cached_classproperty
      def cached_list3(self) -> list[int]:
        self.sm_count += 1
        return [1, 2, 3, 4, 5]

    self.assertEqual(TestClass.sm_count, 0)
    nc_l1 = TestClass.noncached_list
    nc_l2 = TestClass.noncached_list
    self.assertIsNot(nc_l1, nc_l2)
    self.assertEqual(TestClass.sm_count, 2)

    c_l3 = TestClass.cached_list1
    c_l4 = TestClass.cached_list1
    self.assertEqual(c_l3, c_l4)
    self.assertIs(c_l3, c_l4)
    self.assertEqual(TestClass.sm_count, 3)

    c_l3.append(6)
    self.assertEqual(TestClass.cached_list1, [1, 2, 3, 4, 5, 6])

    c_l5 = TestClass.cached_list2
    c_l6 = TestClass.cached_list2
    self.assertEqual(c_l5, c_l6)
    self.assertIs(c_l5, c_l6)
    self.assertEqual(TestClass.sm_count, 4)

    c_l5.append(6)
    self.assertEqual(TestClass.cached_list2, [1, 2, 3, 4, 5, 6])

    c_l7 = TestClass.cached_list3
    c_l8 = TestClass.cached_list3
    self.assertEqual(c_l7, c_l8)
    self.assertIs(c_l7, c_l8)
    self.assertEqual(TestClass.sm_count, 5)

    c_l7.append(6)
    self.assertEqual(TestClass.cached_list3, [1, 2, 3, 4, 5, 6])
