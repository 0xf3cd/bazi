# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import fields
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
  My simple implementation of a frozen, immutable dict.

  Shallow-frozen: the mapping itself never changes, and lookups return the stored
  values as-is (no defensive copies). A holder of mutable values protects them at
  its own boundary.
  浅冻结：映射本身不可变，取值原样返回、不做防御性拷贝。持有可变值的一方在自己的
  边界自行防护。
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
  def __hash__(self) -> int:
    # Tuple semantics, computed lazily: equal contents hash equal (in sync with
    # `Mapping.__eq__`), and unhashable contents (e.g. the description corpus holds
    # lists) raise TypeError on the first hash attempt.
    # 元组语义，惰性计算：内容相等则哈希相等（与 `Mapping.__eq__` 一致），
    # 内容不可哈希（如语料表的 list 值）则首次求哈希时抛 TypeError。
    if self._hash is None:
      self._hash = hash(frozenset(self._data.items()))
    return self._hash

#endregion


######################################################
#region Runtime type gates

def check_declared_types(instance: 'DataclassInstance') -> None:
  '''
  Raise `TypeError` for the first field whose value is not of the type the field declares.
  This is the runtime half of the typing contract, for the frozen value types whose
  constructor is a public boundary: a field's gate is its own annotation, so a new field
  cannot arrive without one.
  逐字段核对运行时类型，第一个不合的抛 `TypeError`。这是「全量标注」的运行时那一半，
  给构造入口即公开边界的 frozen 值类型用：字段的闸就是它自己的注解，新增字段不会漏闸。

  Note:
  - Callers are `__post_init__`s. Value checks (ranges, membership, cross-field rules) stay
    at the call site -- this answers only "is it the declared type".
    调用者是各处 `__post_init__`；值域检查（范围、成员、跨字段规则）留在调用处，本函数只管类型。
  - Every field's annotation must be a runtime class, or a union of them -- no deferred
    annotations, no parameterized generics. A dataclass that does not satisfy that keeps its
    own hand-written gate.
    每个字段的注解在运行时必须是真类，或真类的联合——不能延迟注解，也不能是参数化泛型。
    不满足的 dataclass 自己写闸。

  Args:
  - instance: (DataclassInstance) The dataclass instance to check, normally `self`.
  '''
  for f in fields(instance):
    # `f.type` is the annotated class itself; typeshed spells the attribute as a union
    # with `str`, hence the cast.
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
