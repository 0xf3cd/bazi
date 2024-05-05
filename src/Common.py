# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from typing import (
  TypeVar, Callable, Generic, Final, NamedTuple, TypedDict,
  Sequence, Iterator, Type, Mapping,
)
from .Defines import Wuxing, Yinyang, Tiangan


# Decorator for class property.
ClassPropertyType = TypeVar('ClassPropertyType')
class classproperty(Generic[ClassPropertyType]):
  def __init__(self, func: Callable[..., ClassPropertyType]) -> None:
    self._fget: Final[Callable[..., ClassPropertyType]] = func
  def __get__(self, instance, owner) -> ClassPropertyType:
    return self._fget(owner)


class TraitTuple(NamedTuple):
  '''Representing the Wuxing and Yinyang of a Tiangan or Dizhi. 某天干或地支的五行和阴阳。'''
  wuxing: Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


class HiddenTianganDict(Mapping[Tiangan, int]):
  '''
  `HiddenTianganDict` reveals the hidden Tiangans info.
  The dict represents the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
  A `HiddenTianganDict` is simply a `Mapping` with a customized `__str__` function.

  `HiddenTianganDict` 代表了某个地支的藏干和藏干各自所占的百分比。
  '''
  def __init__(self, data: Mapping[Tiangan, int]) -> None:
    self._data: Final[frozenset[tuple[Tiangan, int]]] = frozenset(data.items())

  def __iter__(self) -> Iterator[Tiangan]:
    return iter(tg for tg, _ in self._data)

  def __len__(self) -> int:
    return len(self._data)

  def __getitem__(self, key: Tiangan) -> int:
    for tg, percent in self._data:
      if tg == key:
        return percent
    raise KeyError(f'{key} not found')
  
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


TianganDataType = TypeVar('TianganDataType')
DizhiDataType = TypeVar('DizhiDataType')
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
