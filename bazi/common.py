# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import fields
from enum import Enum
from typing import TYPE_CHECKING, TypeVar, Final, cast, get_args
from collections.abc import Iterator, Mapping

if TYPE_CHECKING:
  from _typeshed import DataclassInstance


######################################################
#region Immutable data structures

FrozenDictKeyType = TypeVar('FrozenDictKeyType')
FrozenDictValueType = TypeVar('FrozenDictValueType')
class frozendict(Mapping[FrozenDictKeyType, FrozenDictValueType]):
  '''
  浅冻结的不可变映射：映射本身不可变，取值原样返回，不做防御性拷贝。
  持有可变值的一方须在自己的边界防止外部修改。
  '''
  def __init__(self, data: Mapping[FrozenDictKeyType, FrozenDictValueType]) -> None:
    self._data: Final[Mapping[FrozenDictKeyType, FrozenDictValueType]] = dict(data)
    self._hash: int | None = None
  def __getitem__(self, key: FrozenDictKeyType) -> FrozenDictValueType:
    return self._data[key]
  def __iter__(self) -> Iterator[FrozenDictKeyType]:
    return iter(self._data)
  def __len__(self) -> int:
    return len(self._data)
  def __repr__(self) -> str:
    return f'{type(self).__name__}({self._data!r})'
  def __hash__(self) -> int:
    # 惰性计算：内容相等则哈希相等，与 `Mapping.__eq__` 一致。
    # 内容不可哈希（如 list 值）时，首次求哈希抛 TypeError。
    if self._hash is None:
      self._hash = hash(frozenset(self._data.items()))
    return self._hash

#endregion


def _compact_dataclass_repr(instance: 'DataclassInstance') -> str:
  '''配置摘要只列出非默认字段；枚举显示限定成员名，不改变枚举自身的 repr。'''
  def display(value: object) -> str:
    if isinstance(value, Enum):
      return f'{type(value).__qualname__}.{value.name}'
    return repr(value)

  values = ', '.join(
    f'{f.name}={display(value)}'
    for f in fields(instance)
    if (value := getattr(instance, f.name)) != f.default
  )
  return f'{type(instance).__name__}({values})'


######################################################
#region Runtime type gates

def check_declared_types(instance: 'DataclassInstance') -> None:
  '''
  逐字段核对运行时类型，第一个不符合声明类型的字段抛 `TypeError`。
  用于构造函数为公开入口的 frozen 值类型；校验依据字段注解，新增字段也会被检查。

  Note:
  - 由 `__post_init__` 调用；值域检查（范围、成员、跨字段规则）留在调用处，本函数只检查类型。
  - 字段注解必须是运行时类或它们的联合，不能是延迟注解或参数化泛型。
    不满足此条件的 dataclass 须自行校验。

  Args:
  - instance: (DataclassInstance) 待检查的 dataclass 实例，通常为 `self`。
  '''
  for f in fields(instance):
    # `f.type` 实际为注解中的类；typeshed 将其声明为与 str 的联合，因此需要 cast。
    declared = cast(type, f.type)
    value = getattr(instance, f.name)
    if not isinstance(value, declared):
      members = get_args(declared)
      name = ' | '.join(
        'None' if member is type(None) else member.__name__
        for member in members
      ) if members else declared.__name__
      raise TypeError(f'Expected {name}, got {type(value)}')

#endregion
