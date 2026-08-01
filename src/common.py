# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import inspect

from dataclasses import dataclass
from datetime import datetime

from typing import (
  TypeVar, Generic, Final, NamedTuple, TypedDict, Any,
)
from collections.abc import Callable, Sequence, Iterator, Mapping
from .defines import Wuxing, Yinyang, Tiangan, Ganzhi, Jieqi


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



######################################################
#region Bazi

class TraitTuple(NamedTuple):
  '''Representing the Wuxing and Yinyang of a Tiangan or Dizhi. 某天干或地支的五行和阴阳。'''
  wuxing:  Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


class DayunTuple(NamedTuple):
  '''Representing the Dayun of a bazi chart. 八字命盘的某步大运。'''
  ganzhi_year: int
  ganzhi:      Ganzhi


class XiaoyunTuple(NamedTuple):
  '''Representing the Xiaoyun of a bazi chart. 八字命盘的某个小运。'''
  xusui:  int    # 虚岁
  ganzhi: Ganzhi


class LiunianTuple(NamedTuple):
  '''Representing a Liunian. 流年。'''
  ganzhi_year: int
  ganzhi:      Ganzhi


class JieqiTime(NamedTuple):
  '''Representing a Jieqi and its accurate time (datetime). 节气及其精确时间。'''
  jieqi:  Jieqi
  moment: datetime


class HiddenTianganDict(frozendict[Tiangan, int]):
  '''
  `HiddenTianganDict` reveals the hidden Tiangans info.
  The dict represents the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
  A `HiddenTianganDict` is simply a `frozendict` with a customized `__str__` function.

  `HiddenTianganDict` 代表了某个地支的藏干和藏干各自所占的百分比。
  '''
  def __str__(self) -> str:
    sorted_kv = sorted(self.items(), key=lambda kv : kv[1], reverse=True)
    return ','.join([f'{k}:{v}' for k, v in sorted_kv])


PillarDataType = TypeVar('PillarDataType')
@dataclass(frozen=True)
class BaziData(Generic[PillarDataType]):
  '''
  A generic class for storing Bazi data.
  A `BaziData` object stores 4 `PillarDataType` objects for year, month, day, and hour.
  '''
  year: PillarDataType
  month: PillarDataType
  day: PillarDataType
  hour: PillarDataType

  def __iter__(self) -> Iterator[PillarDataType]:
    return iter((self.year, self.month, self.day, self.hour))


TianganDataType_co = TypeVar('TianganDataType_co', covariant=True)
DizhiDataType_co = TypeVar('DizhiDataType_co', covariant=True)
@dataclass(frozen=True)
class GanzhiData(Generic[TianganDataType_co, DizhiDataType_co]):
  '''
  A helper class for storing the data of a Pillar/Ganzhi.
  Can be used with `BaziData` class.
  '''
  tiangan: TianganDataType_co
  dizhi: DizhiDataType_co

#endregion



######################################################
#region JSON

class BaziJson:
  '''
  The class that represents bazi-related charts in JSON format.
  '''

  class FourPillars(TypedDict):
    '''Not expected to be accessed directly. Used in `JsonDict`.'''
    year:  str
    month: str
    day:   str
    hour:  str

  @staticmethod
  def gen_fourpillars(data: Sequence[str]) -> 'BaziJson.FourPillars':
    assert len(data) == 4
    return { 'year': data[0], 'month': data[1], 'day': data[2], 'hour': data[3] }
  
  class Transits(TypedDict):
    '''Not expected to be accessed directly. Used in `JsonDict`.'''
    # start time of the dayun (isoformat string) / 大运的开始时间 (isoformat 格式的字符串)
    dayun_start_time: str

    # key: xusui / 虚岁
    # value: xiaoyun at this xusui age / 对应虚岁的小运
    xiaoyun: dict[str, str]

    # key: ganzhi year that current dayun starts/ 该步大运开始的干支年
    # value: dayun in str / 该步大运
    dayun: dict[str, str]

  class BaziChartJsonDict(TypedDict):
    birth_time: str
    gender: str
    precision: str
    backend: str
    pillars: 'BaziJson.FourPillars'
    nayin: 'BaziJson.FourPillars'
    shier_zhangsheng: 'BaziJson.FourPillars'
    tiangan_traits: 'BaziJson.FourPillars'
    dizhi_traits: 'BaziJson.FourPillars'
    tiangan_shishen: 'BaziJson.FourPillars'
    dizhi_shishen: 'BaziJson.FourPillars'
    hidden_tiangan: 'BaziJson.FourPillars'
    transits: 'BaziJson.Transits'

#endregion



######################################################
#region Descriptions / Interpretations

class ShishenDescription(TypedDict):
  # The general descriptions of the Shishen.
  # 这个十神的基本描述。
  general:        list[str]

  # The descriptions when the Shishen is in good status.
  # 当十神处于力量不过强，状态良好的时候（如不被冲、克，也不过旺/为命主喜用时），这个十神代表的特征。
  in_good_status: list[str]

  # The descriptions when the Shishen is in bad status.
  # 当十神过旺（如在天干和地支藏干中出现3次）或被其他元素冲克（如处于“绝”一柱/受刑、穿、克...）的时候，这个十神代表的特征。
  in_bad_status:  list[str]

  # The views of relationship and friendship represeted by the Shishen.
  # 这个十神代表的恋爱观和交友观。
  relationship:   list[str]


# The description of the Tiangan, including the meanings, interpretations, images, traits, personalities that it has.
class TianganDescription(TypedDict):
  # The general description(s) of a given Tiangan.
  general:     list[str]

  # The personalities that the given Tiangan reveals.
  personality: list[str]

#endregion
