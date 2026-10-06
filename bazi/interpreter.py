# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from .defines import Shishen, Tiangan
from .descriptions import (
  ShishenDescription, TianganDescription, SHISHEN_DESCRIPTIONS, TIANGAN_DESCRIPTIONS,
  _complete_shishen_description, _complete_tiangan_description,
  DescriptionClaims, DescriptionSource, DescriptionSourceRecord,
  _shishen_claims, _tiangan_claims, _source_record,
)


class Interpreter:
  '''
  `Interpreter` provides the legacy Shishen and Tiangan projections of the knowledge corpus.
  Text-returning methods provide deep copies; structured queries return immutable claims.
  `Interpreter` 提供知识语料的旧十神和天干投影。文字查询返回深拷贝；结构化查询返回不可变条目。

  Note:
  - Claims that are not eligible for default output are excluded unless
    `include_reference_only=True` is passed. / 仅在传入 `include_reference_only=True`
    时返回不参与默认输出的断言。
  - `bazi.knowledge` exposes roles, topics, premises and contexts; these legacy queries
    retain their field shapes.
  - `bazi.knowledge` 提供角色、主题、前提及情境；旧查询保留字段形状。
  - Structured queries expose immutable claims and source witnesses.
  - 结构化查询返回不可变条目和来源见证。
  '''

  @staticmethod
  def interpret_shishen(
    shishen: Shishen,
    *,
    include_reference_only: bool = False,
  ) -> ShishenDescription:
    '''
    Look up the description of the given Shishen.
    查询给定十神的描述。

    Args:
    - shishen: (Shishen) The Shishen to look up. / 要查询的十神。
    - include_reference_only: (bool) Include claims that are not eligible for default
      output. / 是否包含不参与默认输出的断言。

    Returns:
    - (ShishenDescription) A deep copy of the description entry. / 描述条目的深拷贝。
    '''
    if not isinstance(shishen, Shishen):
      raise TypeError(f'Expected Shishen, got {type(shishen)}')
    if not isinstance(include_reference_only, bool):
      raise TypeError(f'Expected bool, got {type(include_reference_only)}')
    description: ShishenDescription = (
      _complete_shishen_description(shishen)
      if include_reference_only
      else SHISHEN_DESCRIPTIONS[shishen]
    )
    return copy.deepcopy(description)

  @staticmethod
  def interpret_tiangan(
    tg: Tiangan,
    *,
    include_reference_only: bool = False,
  ) -> TianganDescription:
    '''
    Look up the description of the given Tiangan.
    查询给定天干的描述。

    Args:
    - tg: (Tiangan) The Tiangan to look up. / 要查询的天干。
    - include_reference_only: (bool) Include claims that are not eligible for default
      output. / 是否包含不参与默认输出的断言。

    Returns:
    - (TianganDescription) A deep copy of the description entry. / 描述条目的深拷贝。
    '''
    if not isinstance(tg, Tiangan):
      raise TypeError(f'Expected Tiangan, got {type(tg)}')
    if not isinstance(include_reference_only, bool):
      raise TypeError(f'Expected bool, got {type(include_reference_only)}')
    description: TianganDescription = (
      _complete_tiangan_description(tg)
      if include_reference_only
      else TIANGAN_DESCRIPTIONS[tg]
    )
    return copy.deepcopy(description)

  @staticmethod
  def query_shishen(
    shishen: Shishen,
    *,
    include_reference_only: bool = False,
  ) -> DescriptionClaims:
    '''
    Query immutable Shishen claims grouped by description field.
    按描述字段查询不可变十神条目。

    Note:
    - Reference selection includes conditional claims without evaluating conditions.
    - 参考查询包含带条件的条目，不判断条件是否成立。

    Args:
    - shishen: (Shishen) The Shishen to query. / 要查询的十神。
    - include_reference_only: (bool) Include reference claims. / 是否包含参考条目。

    Returns:
    - (DescriptionClaims) Immutable fields and claims. / 不可变字段映射与条目。
    '''
    if not isinstance(shishen, Shishen):
      raise TypeError(f'Expected Shishen, got {type(shishen)}')
    if not isinstance(include_reference_only, bool):
      raise TypeError(f'Expected bool, got {type(include_reference_only)}')
    return _shishen_claims(shishen, include_reference_only)

  @staticmethod
  def query_tiangan(
    tg: Tiangan,
    *,
    include_reference_only: bool = False,
  ) -> DescriptionClaims:
    '''
    Query immutable Tiangan claims grouped by description field.
    按描述字段查询不可变天干条目。

    Note:
    - Reference selection includes conditional claims without evaluating conditions.
    - 参考查询包含带条件的条目，不判断条件是否成立。

    Args:
    - tg: (Tiangan) The Tiangan to query. / 要查询的天干。
    - include_reference_only: (bool) Include reference claims. / 是否包含参考条目。

    Returns:
    - (DescriptionClaims) Immutable fields and claims. / 不可变字段映射与条目。
    '''
    if not isinstance(tg, Tiangan):
      raise TypeError(f'Expected Tiangan, got {type(tg)}')
    if not isinstance(include_reference_only, bool):
      raise TypeError(f'Expected bool, got {type(include_reference_only)}')
    return _tiangan_claims(tg, include_reference_only)

  @staticmethod
  def query_source(source: DescriptionSource) -> DescriptionSourceRecord:
    '''
    Resolve a source witness, including its evidentiary boundaries.
    查询来源见证及其支持范围和局限。

    Args:
    - source: (DescriptionSource) The source identifier. / 来源标识。

    Returns:
    - (DescriptionSourceRecord) The immutable source record. / 不可变来源记录。
    '''
    if not isinstance(source, DescriptionSource):
      raise TypeError(f'Expected DescriptionSource, got {type(source)}')
    return _source_record(source)
