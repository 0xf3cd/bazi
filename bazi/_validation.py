# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''记录与文字输出共用的结构、JSON 及 UTF-8 校验；不是对外 API。

知识引用、判据、版本及失败后的处理指引由各记录模块决定。
'''

import json
from collections.abc import Iterator
from contextlib import contextmanager
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
  '''输出须能按 UTF-8 保存；不替换不支持的字符。'''
  try:
    text.encode('utf-8')
  except UnicodeEncodeError:
    raise ValueError('Unsupported surrogate in text; expected UTF-8') from None
  return text


def _json_dumps(value: object) -> str:
  '''记录的带缩进输出，同时检查所有字符串键和值的 UTF-8 保存能力。'''
  try:
    return _utf8(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
  except RecursionError:
    raise ValueError('JSON nesting exceeds the supported serialization depth') from None


def _json_loads(text: str) -> Any:
  '''拒绝重复键，并使用实际记录编码路径检查解析结果的保存能力。'''
  _text(text, empty=True)
  try:
    value = json.loads(text, object_pairs_hook=_pairs)
  except RecursionError:
    raise ValueError('JSON nesting exceeds the supported parsing depth') from None
  _json_dumps(value)
  return value


@contextmanager
def _record_errors(next_step: str) -> Iterator[None]:
  '''保留记录错误的类型分类与原因，附加该记录的处理指引。'''
  try:
    yield
  except json.JSONDecodeError as error:
    raise json.JSONDecodeError(f'{error.msg}. {next_step}', error.doc, error.pos) from None
  except (TypeError, ValueError) as error:
    message = f'{error}. {next_step}'.encode('utf-8', errors='backslashreplace').decode('utf-8')
    error_type = TypeError if isinstance(error, TypeError) else ValueError
    raise error_type(message) from None
