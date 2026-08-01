# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import inspect

from typing import TypeVar, Generic, Final, Any
from collections.abc import Callable, Iterator, Mapping


######################################################
#region Metaclasses and decorators

class ConstMetaClass(type):
  '''
  This meta class ensures a class is not attribute-setable, which means that
  the Class's methods and variables/properties are not settable once the class is defined.
  '''
  def __new__(cls: type['ConstMetaClass'], name: str, bases: tuple[type], attrs: dict[str, Any]) -> 'ConstMetaClass':
    return super().__new__(cls, name, bases, attrs)
  
  def __setattr__(self, name: str, value: Any) -> None:
    raise AttributeError('ConstMetaClass class attribute is read-only')

  def __delattr__(self, name: str) -> None:
    raise AttributeError('ConstMetaClass class attribute is read-only')


class Const(metaclass=ConstMetaClass):
  '''
  All subclasses of this class are not instantiable. 
  It is expected that child classes only contain class variables.

  The class variables can't be changed once the class is defined.
  However, the class variables can still be mutable.

  Example:
  ```
  class SomeClass(Const):
    A: int = 1
    B: list[int] = [2, 3]
    C: list[int] = B

  assert SomeClass.A == 1
  assert SomeClass.B == [2, 3]
  assert SomeClass.C == [2, 3]
  assert SomeClass.B is SomeClass.C

  SomeClass.A = 2  # AttributeError
  SomeClass.B = [] # AttributeError

  SomeClass.B.append(4) # OK!!
  assert SomeClass.B == [2, 3, 4]
  assert SomeClass.C == [2, 3, 4]
  ```
  '''
  def __init__(self, *args: Any, **kwargs: Any) -> None:
    raise NotImplementedError('Const cannot be instantiated')


class ImmutableMetaClass(type):
  '''
  This meta class is intended to be used as the meta data of classes that only contains 
  class variables (i.e. class properties / class-wise shared properties).

  This meta class overrides the `__setattr__` and `__getattribute__` methods:
  - `__setattr__`: Raise an `AttributeError`.
  - `__getattribute__`: Deepcopy the original value and return the copied value.
  '''

  def __new__(cls: type['ImmutableMetaClass'], name: str, bases: tuple[type], attrs: dict[str, Any]) -> 'ImmutableMetaClass':
    return super().__new__(cls, name, bases, attrs)
  
  def __setattr__(cls, name: str, value: Any) -> None:
    raise AttributeError('ImmutableMetaClass class attribute is read-only')
  
  def __delattr__(cls, name: str) -> None:
    raise AttributeError('ImmutableMetaClass class attribute is read-only')
  
  def __getattribute__(cls, name: str) -> Any:
    val = super().__getattribute__(name)
    try:
      if inspect.isfunction(val) or inspect.ismethod(val) or isinstance(val, (classmethod, staticmethod)):
        return val
      return copy.deepcopy(val)
    except TypeError:
      raise NotImplementedError('Not supported yet...')

class Immutable(metaclass=ImmutableMetaClass):
  '''
  All subclasses of this class are not instantiable. 
  It is expected that child classes only contain class variables.

  The class variables can't be changed once the class is defined.
  When accessing class variables, the deep-copies of the original values are returned - not the original values.

  Example:
  ```
  class SomeClass(Immutable):
    A: int = 1
    B: list[int] = [2, 3]
    C: list[int] = B

  assert SomeClass.A == 1
  assert SomeClass.B == [2, 3]
  assert SomeClass.C == [2, 3]
  assert SomeClass.B is not SomeClass.B # Deepcopy upon every access.

  SomeClass.A = 2  # AttributeError
  SomeClass.B = [] # AttributeError

  SomeClass.B.append(4) # OK!!
  assert SomeClass.B == [2, 3] # Not changed!
  assert SomeClass.C == [2, 3] # Not changed!
  ```
  '''
  def __init__(self, *args: Any, **kwargs: Any) -> None:
    raise NotImplementedError('Immutable cannot be instantiated')

# Decorator for class property.
ClassPropertyType = TypeVar('ClassPropertyType')
class classproperty(Generic[ClassPropertyType]):
  def __init__(self, fget: Callable[..., ClassPropertyType]) -> None:
    self._fget: Final[Callable[..., ClassPropertyType]] = fget
  def __get__(self, instance, owner) -> ClassPropertyType:
    sig = inspect.signature(self._fget)
    if len(sig.parameters) == 0:
      return self._fget()
    return self._fget(owner)
  def __set__(self, instance, value) -> None:
    raise AttributeError('Class property is read-only.')

#endregion



######################################################
#region Immutable data structures

FrozenDictKeyType = TypeVar('FrozenDictKeyType')
FrozenDictValueType = TypeVar('FrozenDictValueType')
class frozendict(Mapping[FrozenDictKeyType, FrozenDictValueType]):
  '''
  My simple implementation of a frozen, immutable dict.
  '''
  def __init__(self, data: Mapping[FrozenDictKeyType, FrozenDictValueType]) -> None:
    self._data: Final[Mapping[FrozenDictKeyType, FrozenDictValueType]] = copy.deepcopy(data)
  def __getitem__(self, key: FrozenDictKeyType) -> FrozenDictValueType:
    # Use deepcopy to avoid changing the original dict.
    # The value may not be deepcopyable though...
    return copy.deepcopy(self._data[key])
  def __iter__(self) -> Iterator[FrozenDictKeyType]:
    return iter(self._data)
  def __len__(self) -> int:
    return len(self._data)

#endregion

