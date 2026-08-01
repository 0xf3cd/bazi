# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Final

from .defines import Ganzhi
from .bazi_chart import BaziChart
from .transits import TransitMoment, TransitOptions, TransitDatabase, _ALL_OPTIONS


class TransitChart:
  '''
  `TransitChart` reveals the transit information (i.e. Dayun / Xiaoyun / Liunian) of a given `BaziChart`.
  `TransitChart` 基于原盘（`BaziChart`）提供大运、小运、流年等运的信息。

  Note: `TransitChart` is a facade / the unified entry for querying transits.
  The actual computations are delegated to `TransitDatabase`.
  `TransitChart` 是一个门面类，作为查询运的统一入口，实际计算委托给 `TransitDatabase`。
  '''

  def __init__(self, bazi_chart: BaziChart) -> None:
    '''
    Takes a `BaziChart` as the input.
    接受一个 `BaziChart` 作为输入。

    Args:
    - `bazi_chart`: (BaziChart) The bazi chart (原盘) to generate the transit chart from.
    '''

    assert isinstance(bazi_chart, BaziChart)
    self._bazi_chart: Final[BaziChart] = bazi_chart
    self._transit_db: Final[TransitDatabase] = TransitDatabase(self._bazi_chart)

  @property
  def bazi_chart(self) -> BaziChart:
    '''The underlying `BaziChart` (原盘). Shared, not copied -- `BaziChart` is read-only
    (its non-frozen `Bazi` is isolated inside the chart). 直接共享——`BaziChart` 只读，
    非 frozen 的 `Bazi` 已由命盘自身隔离。'''
    return self._bazi_chart

  def support(self, moment: TransitMoment, options: TransitOptions) -> bool:
    '''
    Return whether the given `moment` and `options` are supported by this `TransitChart`.
    返回当前 `TransitChart` 是否支持给定的时刻和选项。

    Args:
    - `moment`: (TransitMoment) The moment in Ganzhi calendar. 干支历法中的时刻。Only the year granularity is supported for now (目前仅支持年粒度)。
    - `options`: (TransitOptions) Specifies the transits to be picked. 用于指定是否考虑流年、小运、大运等。

    Return: (bool) Whether the given `moment` and `options` are supported by this `TransitChart`.

    Note: raises `NotImplementedError` for month/day-granularity moments until #48. / 注意：#48 落地前，月/日粒度的 moment 会抛 `NotImplementedError`。
    '''

    assert isinstance(moment, TransitMoment)
    assert isinstance(options, TransitOptions)
    # `options in TransitOptions` rejects unnamed composites on Python 3.11; check the enumerated space instead.
    assert options in _ALL_OPTIONS
    return self._transit_db.support(moment, options)

  def ganzhis(self, moment: TransitMoment, options: TransitOptions) -> tuple[Ganzhi, ...]:
    '''
    Return the Ganzhis of the selected transits for the given `moment` and `options`.
    返回所选中的小运、大运或流年等对应的干支。

    Args:
    - `moment`: (TransitMoment) The moment in Ganzhi calendar, mainly used to compute the transit pillars. 干支历法中的时刻，主要用于计算运（小运/大运/流年）的天干地支。Only the year granularity is supported for now (目前仅支持年粒度)。
    - `options`: (TransitOptions) Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (tuple[Ganzhi, ...]) The Ganzhis of the selected transits for the given `moment` and `options`.

    Note: raises `NotImplementedError` for month/day-granularity moments until #48 (via `TransitDatabase`). / 注意：#48 落地前，月/日粒度的 moment 会抛 `NotImplementedError`（经 `TransitDatabase` 冒出）。
    '''

    assert isinstance(moment, TransitMoment)
    assert isinstance(options, TransitOptions)
    # `options in TransitOptions` rejects unnamed composites on Python 3.11; check the enumerated space instead.
    assert options in _ALL_OPTIONS
    return self._transit_db.ganzhis(moment, options)


流年大运 = TransitChart
