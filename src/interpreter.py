# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy

from .defines import Shishen, Tiangan
from .descriptions import (
  ShishenDescription, TianganDescription, SHISHEN_DESCRIPTIONS, TIANGAN_DESCRIPTIONS,
)


class Interpreter:
  '''
  `Interpreter` statically looks up the curated description corpus (语料库) of
  Shishen and Tiangan; the returned entries are deep copies, safe to modify.
  `Interpreter` 以静态方法查询十神和天干的语料库；返回条目是深拷贝，可随意修改。

  Note:
  - Combining the descriptions against a specific chart (i.e. producing a whole-chart
    reading) is currently done in the `run_interpreter` entry script, not in this class.
  - 针对具体命盘组合这些描述（即整盘解读）目前在 `run_interpreter` 入口脚本中完成，不在本类中。
  '''

  @staticmethod
  def interpret_shishen(shishen: Shishen) -> ShishenDescription:
    '''
    Look up the description of the given Shishen.
    查询给定十神的描述。

    Args:
    - shishen: (Shishen) The Shishen to look up. / 要查询的十神。

    Returns:
    - (ShishenDescription) A deep copy of the corpus entry. / 语料库对应条目的深拷贝。
    '''
    if not isinstance(shishen, Shishen):
      raise TypeError(f'Expected Shishen, got {type(shishen)}')
    return copy.deepcopy(SHISHEN_DESCRIPTIONS[shishen])

  @staticmethod
  def interpret_tiangan(tg: Tiangan) -> TianganDescription:
    '''
    Look up the description of the given Tiangan.
    查询给定天干的描述。

    Args:
    - tg: (Tiangan) The Tiangan to look up. / 要查询的天干。

    Returns:
    - (TianganDescription) A deep copy of the corpus entry. / 语料库对应条目的深拷贝。
    '''
    if not isinstance(tg, Tiangan):
      raise TypeError(f'Expected Tiangan, got {type(tg)}')
    return copy.deepcopy(TIANGAN_DESCRIPTIONS[tg])
