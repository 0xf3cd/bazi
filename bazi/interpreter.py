# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from .defines import Shishen, Tiangan
from .descriptions import (
  ShishenDescription, TianganDescription, SHISHEN_DESCRIPTIONS, TIANGAN_DESCRIPTIONS,
  _complete_shishen_description, _complete_tiangan_description,
)


class Interpreter:
  '''
  `Interpreter` statically looks up Shishen and Tiangan descriptions; the returned
  entries are deep copies, safe to modify.
  `Interpreter` 以静态方法查询十神和天干描述；返回条目是深拷贝，可随意修改。

  Note:
  - Editorial reference-only claims are excluded unless `include_reference_only=True`
    is passed. / 仅在传入 `include_reference_only=True` 时返回 editorial reference-only 断言。
  - Combining the descriptions against a specific chart (i.e. producing a whole-chart
    reading) is currently done in the `run_interpreter` entry script, not in this class.
  - 针对具体命盘组合这些描述（即整盘解读）目前在 `run_interpreter` 入口脚本中完成，不在本类中。
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
    - include_reference_only: (bool) Include editorial claims that are not eligible for
      default output. / 是否包含不参与默认输出的 editorial 断言。

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
    - include_reference_only: (bool) Include editorial claims that are not eligible for
      default output. / 是否包含不参与默认输出的 editorial 断言。

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
