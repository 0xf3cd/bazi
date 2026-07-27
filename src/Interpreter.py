# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from .Defines import Shishen, Tiangan
from .Common import ShishenDescription, TianganDescription
from .Descriptions import SHISHEN_DESCRIPTIONS, TIANGAN_DESCRIPTIONS


class Interpreter:
  '''
  `Interpreter` statically looks up the curated description corpus (语料库) of
  Shishen and Tiangan. The corpus tables are frozen, and the returned descriptions
  are deep copies (see `frozendict` in `Common`), so callers may freely modify them
  without corrupting the corpus.

  `Interpreter` 以静态方法查询十神和天干的语料库。语料表是冻结的，且返回的描述是
  深拷贝（见 `Common` 中的 `frozendict`），调用方可随意修改，不会污染语料库。

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
    assert isinstance(shishen, Shishen)
    return SHISHEN_DESCRIPTIONS[shishen]

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
    assert isinstance(tg, Tiangan)
    return TIANGAN_DESCRIPTIONS[tg]
