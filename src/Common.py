# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import TypeVar, Callable, Generic, Final

PropertyType = TypeVar('PropertyType')
class classproperty(Generic[PropertyType]):
  def __init__(self, func: Callable[..., PropertyType]) -> None:
    self.fget: Final[Callable[..., PropertyType]] = func
  def __get__(self, instance, owner) -> PropertyType:
    return self.fget(owner)
