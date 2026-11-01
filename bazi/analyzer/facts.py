# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''原局与所选流运的通根、透干查询。'''

from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import assert_never

from ..bazi_chart import BaziChart, _check_chart
from ..common import check_declared_types
from ..defines import Zhu, Tiangan, Dizhi, Ganzhi
from ..transits import TransitKind, TransitSet
from ..utils.bazi_utils import hidden_tiangans, traits


class TianganMatch(Enum):
  '''明藏干按同干或同五行匹配；同五行包括同干。'''
  SAME_TIANGAN = 'same_tiangan'
  SAME_WUXING  = 'same_wuxing'


@dataclass(frozen=True)
class TianganOccurrence:
  '''某柱位或流运种类上的实际干；明藏角色由查询结果中的字段指定。

  stem 必须是该干支的明干或藏干；同干支的不同位置不合并。
  '''
  position: Zhu | TransitKind
  ganzhi:   Ganzhi
  stem:     Tiangan

  def __post_init__(self) -> None:
    check_declared_types(self)
    for value, expected in ((self.ganzhi.tiangan, Tiangan), (self.ganzhi.dizhi, Dizhi)):
      if not isinstance(value, expected):
        raise TypeError(f'Expected {expected.__name__}, got {type(value)}')
    if self.stem is not self.ganzhi.tiangan and self.stem not in hidden_tiangans(self.ganzhi.dizhi):
      raise ValueError('Stem is absent from its Ganzhi')


@dataclass(frozen=True)
class TouganHit:
  '''一处藏干与一处明干的匹配，保留两端的实际干和位置。'''
  hidden:  TianganOccurrence
  visible: TianganOccurrence

  def __post_init__(self) -> None:
    check_declared_types(self)
    if self.hidden.stem not in hidden_tiangans(self.hidden.ganzhi.dizhi):
      raise ValueError('Hidden stem is absent from its Ganzhi')
    if self.visible.stem is not self.visible.ganzhi.tiangan:
      raise ValueError('Visible stem differs from its Ganzhi')


def _positions(
  chart: BaziChart,
  target: Tiangan,
  transits: TransitSet | None,
  condition: TianganMatch,
) -> tuple[tuple[Zhu | TransitKind, Ganzhi], ...]:
  '''校验查询输入，按原局四柱、所选流运固定序列出参与位置。'''
  _check_chart(chart)
  if not isinstance(target, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(target)}')
  if not isinstance(condition, TianganMatch):
    raise TypeError(f'Expected TianganMatch, got {type(condition)}')
  if transits is not None and not isinstance(transits, TransitSet):
    raise TypeError(f'Expected TransitSet | None, got {type(transits)}')
  natal: tuple[tuple[Zhu | TransitKind, Ganzhi], ...] = tuple(zip(Zhu, chart.bazi.pillars, strict=True))
  return natal + (() if transits is None else transits.items)


def _matches(target: Tiangan, actual: Tiangan, condition: TianganMatch) -> bool:
  if condition is TianganMatch.SAME_TIANGAN:
    return target is actual
  elif condition is TianganMatch.SAME_WUXING:
    return traits(target).wuxing is traits(actual).wuxing
  else:
    assert_never(condition) # pragma: no cover # 输入已校验，穷尽守卫让新增成员触发静态检查。


def tonggen(
  chart: BaziChart,
  target: Tiangan,
  transits: TransitSet | None = None,
  *, condition: TianganMatch = TianganMatch.SAME_WUXING,
) -> tuple[TianganOccurrence, ...]:
  '''查目标天干在原局及所选流运的哪些藏干中匹配，默认同五行。

  Args:
  - chart: (BaziChart) 原局命盘。
  - target: (Tiangan) 待查天干值，可取任一天干。
  - transits: (TransitSet | None) 同时参与查询的流运；None 只查原局。
  - condition: (TianganMatch) 同干或同五行；错误参数类型抛 TypeError。

  Return: (tuple[TianganOccurrence, ...]) 按位置、藏干表顺序返回匹配的实际藏干。

  Note:
  - 同五行通根例见《子平真诠》六、论十干得时不旺失时不弱的甲逢未、丙逢戌：
    https://www.donglishuzhai.net/chapter/3719.html
  - 《滴天髓阐微》才德篇任注亦有庚在酉丑通根的例子：
    https://www.zhyw.net/a/ditiansui/2020/11/09/23706.html
  '''
  positions = _positions(chart, target, transits, condition)
  return tuple(
    TianganOccurrence(position, ganzhi, stem)
    for position, ganzhi in positions
    for stem in hidden_tiangans(ganzhi.dizhi)
    if _matches(target, stem, condition)
  )


def tougan(
  chart: BaziChart,
  target: Tiangan,
  transits: TransitSet | None = None,
  *, condition: TianganMatch,
) -> tuple[TouganHit, ...]:
  '''查指定藏干在哪些明干处匹配；必须显式选择同干或同五行。

  Args:
  - chart: (BaziChart) 原局命盘。
  - target: (Tiangan) 待查的实际藏干值；先按同干定位这个藏干本人，再按 condition 匹配明干。
  - transits: (TransitSet | None) 参与查询的流运；明、藏两端均从原局及所选流运中取。
  - condition: (TianganMatch) 匹配条件，无默认；错误参数类型抛 TypeError。

  Return: (tuple[TouganHit, ...]) 藏干位置优先、明干位置次序；保留同柱及同干支不同位置。
  无该藏干或无匹配明干时返回空元组。

  Note:
  - 辰藏癸而透壬的墓库例见徐乐吾《子平真诠评注》三、论阴阳生死的注文：
    https://tianjihq.com/zh-CN/learn/books/ziping-zhenquan-pingzhu/14
  '''
  positions = _positions(chart, target, transits, condition)
  hidden = tuple(
    TianganOccurrence(position, ganzhi, target)
    for position, ganzhi in positions
    if target in hidden_tiangans(ganzhi.dizhi)
  )
  visible = tuple(
    TianganOccurrence(position, ganzhi, ganzhi.tiangan)
    for position, ganzhi in positions
    if _matches(target, ganzhi.tiangan, condition)
  )
  return tuple(TouganHit(left, right) for left, right in product(hidden, visible))
