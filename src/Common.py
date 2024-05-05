# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import TypeVar, Callable, Generic, Final, NamedTuple, TypedDict
from .Defines import Wuxing, Yinyang, Tiangan

PropertyType = TypeVar('PropertyType')
class classproperty(Generic[PropertyType]):
  def __init__(self, func: Callable[..., PropertyType]) -> None:
    self.fget: Final[Callable[..., PropertyType]] = func
  def __get__(self, instance, owner) -> PropertyType:
    return self.fget(owner)


class TraitTuple(NamedTuple):
  '''Representing the Wuxing and Yinyang of a Tiangan or Dizhi. 某天干或地支的五行和阴阳。'''
  wuxing: Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


# The dict represents the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
# 代表地支中的藏干和它们所占的百分比。
HiddenTianganDict = dict[Tiangan, int]


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
