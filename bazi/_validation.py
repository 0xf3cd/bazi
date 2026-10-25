# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''知识编辑源、领域值与文字输出共用的结构及 UTF-8 校验；不是对外 API。'''

import json
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
    _utf8(key)
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


def _utf8(text: str) -> str:
  '''文字须能按 UTF-8 编码；不替换不支持的字符。'''
  try:
    text.encode('utf-8')
  except UnicodeEncodeError:
    raise ValueError('Unsupported surrogate in text; expected UTF-8') from None
  return text


def _json_loads(text: str) -> Any:
  '''拒绝重复键和孤立代理项；键由解析 hook 检查，值使用显式栈遍历，避免深层值检查触发递归。'''
  _text(text, empty=True)
  try:
    value = json.loads(text, object_pairs_hook=_pairs)
  except RecursionError:
    raise ValueError('JSON nesting exceeds the supported parsing depth') from None
  pending = [value]
  while pending:
    current = pending.pop()
    if isinstance(current, str):
      _utf8(current)
    elif isinstance(current, list):
      pending.extend(current)
    elif isinstance(current, dict):
      pending.extend(current.values())
  return value
