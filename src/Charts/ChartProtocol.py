# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import runtime_checkable, Protocol, Mapping
from ..Bazi import Bazi

@runtime_checkable
class ChartProtocol(Protocol):
  '''The protocol that all Chart classes conform to.'''
  def __init__(self, bazi: Bazi) -> None: ...
  @property
  def bazi(self) -> Bazi: ...
  @property
  def json(self) -> Mapping: ...
