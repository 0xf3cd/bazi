# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import inspect

from typing import (
  TypeVar, Callable, Generic, Final, NamedTuple, TypedDict,
  Sequence, Iterator, Type, Mapping, Any, Protocol, runtime_checkable,
)
from .Defines import Wuxing, Yinyang, Tiangan


class DeepcopyImmutableMetaClass(type):
  '''
  This meta class is intended to be used as the meta data of classes that only contains 
  class variables (i.e. class properties / class-wise shared properties).

  This meta class overrides the `__setattr__` and `__getattribute__` methods:
  - `__setattr__`: Raise an `AttributeError`.
  - `__getattribute__`: Deepcopy the original value and return the copied value.
  '''
  def __new__(cls: Type, name: str, bases: tuple[Type], attrs: dict[str, Any]) -> Type:
    # Make sure the new class doesn't contain classmethods.
    for k, v in attrs.items():
      if isinstance(v, (classmethod, staticmethod)):
        raise TypeError(f'{name} cannot contain classmethods or staticmethods.')
      if inspect.isfunction(v) or inspect.ismethod(v):
        raise TypeError(f'{name} cannot contain functions.')

    def overridden_setattr(*args, **kwargs):
      raise AttributeError(f'{name} is read-only')
    cls.__setattr__ = overridden_setattr
    
    def overridden_getattribute(*args, **kwargs):
      assert len(args) >= 2
      return copy.deepcopy(attrs[args[1]])
    cls.__getattribute__ = overridden_getattribute

    return type.__new__(cls, name, bases, attrs)


class ImmutableMetaClass(type):
  '''
  This meta class ensures a class is not attribute-setable, which means that
  the Class's methods and variables/properties are not settable once the class is created.
  '''
  def __new__(cls: Type, name: str, bases: tuple[Type], attrs: dict[str, Any]) -> Type:
    def overridden_setattr(*args, **kwargs):
      raise AttributeError(f'Class {name} is read-only')
    cls.__setattr__ = overridden_setattr
    return type.__new__(cls, name, bases, attrs)


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


class TraitTuple(NamedTuple):
  '''Representing the Wuxing and Yinyang of a Tiangan or Dizhi. 某天干或地支的五行和阴阳。'''
  wuxing: Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


class HiddenTianganDict(frozendict[Tiangan, int]):
  '''
  `HiddenTianganDict` reveals the hidden Tiangans info.
  The dict represents the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
  A `HiddenTianganDict` is simply a `frozetndict` with a customized `__str__` function.

  `HiddenTianganDict` 代表了某个地支的藏干和藏干各自所占的百分比。
  '''
  def __str__(self) -> str:
    sorted_kv = sorted(self.items(), key=lambda kv : kv[1], reverse=True)
    return ','.join([f'{k}:{v}' for k, v in sorted_kv])


PillarDataType = TypeVar('PillarDataType')
class BaziData(Generic[PillarDataType]):
  '''
  A generic class for storing Bazi data.
  A `BaziData` object stores 4 `PillarDataType` objects for year, month, day, and hour.
  '''
  def __init__(self, generic_type: Type[PillarDataType], data: Sequence[PillarDataType]) -> None:
    self._type: Final[Type[PillarDataType]] = generic_type
    
    assert len(data) == 4
    self._year: Final[PillarDataType] = copy.deepcopy(data[0])
    self._month: Final[PillarDataType] = copy.deepcopy(data[1])
    self._day: Final[PillarDataType] = copy.deepcopy(data[2])
    self._hour: Final[PillarDataType] = copy.deepcopy(data[3])

  @property
  def year(self) -> PillarDataType:
    return copy.deepcopy(self._year)

  @property
  def month(self) -> PillarDataType:
    return copy.deepcopy(self._month)

  @property
  def day(self) -> PillarDataType:
    return copy.deepcopy(self._day)

  @property
  def hour(self) -> PillarDataType:
    return copy.deepcopy(self._hour)
  
  def __iter__(self) -> Iterator[PillarDataType]:
    return iter((self._year, self._month, self._day, self._hour))
  
  def __eq__(self, other: object) -> bool:
    if not isinstance(other, BaziData):
      return False
    if self.year != other.year:
      return False
    if self.month != other.month:
      return False
    if self.day != other.day:
      return False
    if self.hour != other.hour:
      return False
    return True
  
  def __ne__(self, other: object) -> bool:
    return not self.__eq__(other)


TianganDataType = TypeVar('TianganDataType', covariant=True)
DizhiDataType = TypeVar('DizhiDataType', covariant=True)

@runtime_checkable
class PillarDataProtocol(Protocol[TianganDataType, DizhiDataType]):
  '''
  The protocol that all PillarData classes conform to.
  '''
  @property
  def tiangan(self) -> TianganDataType: ...
  @property
  def dizhi(self) -> DizhiDataType: ...
  def __eq__(self, other: object) -> bool: ...
  def __ne__(self, other: object) -> bool: ...


class PillarData(Generic[TianganDataType, DizhiDataType]):
  '''
  A helper class for storing the data of a Pillar.
  Can be used with `BaziData` class.
  '''
  def __init__(self, tg: TianganDataType, dz: DizhiDataType) -> None:
    self._tg: Final[TianganDataType] = copy.deepcopy(tg)
    self._dz: Final[DizhiDataType] = copy.deepcopy(dz)

  @property
  def tiangan(self) -> TianganDataType:
    return copy.deepcopy(self._tg)
  
  @property
  def dizhi(self) -> DizhiDataType:
    return copy.deepcopy(self._dz)
  
  def __eq__(self, other: object) -> bool:
    if not isinstance(other, PillarData):
      return False
    if self.tiangan != other.tiangan:
      return False
    if self.dizhi != other.dizhi:
      return False
    return True
  
  def __ne__(self, other: object) -> bool:
    return not self.__eq__(other)


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

  class BaziChartJsonDict(TypedDict):
    birth_time: str
    gender: str
    precision: str
    pillars: 'BaziJson.FourPillars'
    nayins: 'BaziJson.FourPillars'
    shier_zhangshengs: 'BaziJson.FourPillars'
    tiangan_traits: 'BaziJson.FourPillars'
    dizhi_traits: 'BaziJson.FourPillars'
    tiangan_shishens: 'BaziJson.FourPillars'
    dizhi_shishens: 'BaziJson.FourPillars'
    hidden_tiangans: 'BaziJson.FourPillars'


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
