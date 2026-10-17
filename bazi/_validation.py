# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''知识语料与前提记录共用的结构校验；仅供包内调用，不是对外 API。

这里只检查文字、元组、JSON 键及字段集合。知识引用、判据与版本规则留在各自模块。
'''

from typing import Any, TypeVar


_T = TypeVar('_T')


def _text(value: object, *, empty: bool = False) -> None:
  if not isinstance(value, str):
    raise TypeError(f'Expected str, got {type(value)}')
  if not empty and not value.strip():
    raise ValueError('Expected non-empty text')


def _choice(value: object, choices: tuple[str, ...]) -> None:
  _text(value)
  if value not in choices:
    raise ValueError(f'Unsupported value: {value}')


def _tuple(value: object, member_type: type[_T]) -> None:
  if not isinstance(value, tuple):
    raise TypeError(f'Expected tuple, got {type(value)}')
  for member in value:
    if not isinstance(member, member_type):
      raise TypeError(f'Expected {member_type.__name__}, got {type(member)}')
    if isinstance(member, str):
      _text(member)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    if key in result:
      raise ValueError(f'Duplicate JSON key: {key}')
    result[key] = value
  return result


def _mapping(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
  if not isinstance(value, dict):
    raise TypeError(f'Expected JSON object, got {type(value)}')
  if set(value) != set(keys):
    raise ValueError(f'JSON fields differ: {set(value) ^ set(keys)}')
  return value
