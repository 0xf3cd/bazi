# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''命盘与流运的纯文本展示。

basic_text、transit_text 与 chart_text 接收调用方给定的 BaziChart 并返回文本：不写文件，
不依赖终端着色库，固定输入的输出可重放。终端着色由调用方通过 TextStyle 接入，默认纯文本。'''

import itertools
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from typing import TypeVar

from .bazi_chart import BaziChart, _check_chart
from .calendar import calendar_utils_of
from .data_types import HiddenTianganDict
from .defines import Tiangan, Dizhi, Ganzhi
from .utils.bazi_utils import traits, shishen, hidden_tiangans, nayin_str, shier_zhangsheng


_T = TypeVar('_T')


@dataclass(frozen=True)
class TextStyle:
  '''
  给展示文字加样式的钩子；两个字段都不设（`None`）时原样输出，得到纯文本。

  Note:
  - 钩子的返回值原样放进文本，不做检查；版式由调用方负责。
  - 字段既不是 `None` 也不可调用时抛 `TypeError`。

  Args:
  - glyph: (Callable[[Tiangan | Dizhi], str] | None) 干支字形。收到单个天干或地支，
    返回显示文字；干支（`Ganzhi`）逐字形分别调用。
  - day_master_mark: (Callable[[str], str] | None) 日柱天干十神位置的“日主”标记。

  Examples:
  - 不设样式即纯文本：`basic_text(chart)`。
  - 脚本里用 `TextStyle(glyph=colored, day_master_mark=highlight)` 接入终端着色。
  '''
  glyph:           Callable[[Tiangan | Dizhi], str] | None = None
  day_master_mark: Callable[[str], str] | None = None

  def __post_init__(self) -> None:
    for name in ('glyph', 'day_master_mark'):
      value = getattr(self, name)
      if value is not None and not callable(value):
        raise TypeError(f'Expected callable | None, got {type(value)}')


def _batched(it: Iterable[_T], n: int) -> Generator[tuple[_T, ...], None, None]:
  '''为 Python 3.12 之前的版本提供分批迭代，替代 itertools.batched。'''
  assert n > 0
  it_list: list[_T] = list(it)
  for i in range(0, len(it_list), n):
    yield tuple(it_list[i:i + n])


def _check_style(style: object) -> TextStyle:
  if style is None:
    return TextStyle()
  if not isinstance(style, TextStyle):
    raise TypeError(f'Expected TextStyle | None, got {type(style)}')
  return style


def _check_count(name: str, count: object) -> int:
  if not isinstance(count, int):
    raise TypeError(f'Expected int, got {type(count)}')
  if count < 0:
    raise ValueError(f'Unsupported {name}: {count}')
  return count


def _glyph(style: TextStyle, s: Tiangan | Dizhi) -> str:
  return str(s) if style.glyph is None else style.glyph(s)


def _day_master_mark(style: TextStyle) -> str:
  return '日主' if style.day_master_mark is None else style.day_master_mark('日主')


def _ganzhi(style: TextStyle, ganzhi: Ganzhi) -> str:
  return _glyph(style, ganzhi.tiangan) + _glyph(style, ganzhi.dizhi)


def _traits(s: Tiangan | Dizhi) -> str:
  t = traits(s)
  return f'{t.yinyang}{t.wuxing}'


def _hidden_tiangans(style: TextStyle, d: HiddenTianganDict, day_master: Tiangan) -> str:
  def f(tg: Tiangan) -> str:
    return f'{_glyph(style, tg)} [{_traits(tg)}] <{shishen(day_master, tg).abbr}>'
  return ' '.join(f(tg) for tg in d)


def basic_text(chart: BaziChart, *, style: TextStyle | None = None) -> str:
  '''
  命盘的基本展示：日元、出生时刻、四柱及其十神、阴阳五行、藏干、纳音与十二长生。

  Note:
  - 文本以换行开头、换行结尾，可直接 `print`；地点盘另列民用、真太阳与节气表出生时刻。

  Args:
  - chart: (BaziChart) 待展示的命盘。
  - style: (TextStyle | None) 着色钩子；`None` 为纯文本。

  Return: (str) 纯文本展示。
  '''
  _check_chart(chart)
  style = _check_style(style)

  s: str = '\n'
  bazi = chart.bazi
  day_master_wx = traits(bazi.day_master).wuxing
  date_label = '生于 ' if bazi.longitude is None else '真太阳时日期：'
  s += f'日元{_glyph(style, bazi.day_master)}{day_master_wx}，{bazi.gender}，{date_label}{bazi.solar_date}\n\n'
  if bazi.longitude is None:
    s += f'出生时刻：{bazi.solar_datetime.isoformat()}\n\n'
  location_time = bazi.location_time
  if location_time is not None:
    s += f'民用出生时刻（固定出生地偏移）：{location_time.civil_time.isoformat()}；经度={location_time.longitude}\n'
    s += f'真太阳出生时刻：{location_time.apparent_time.isoformat()}\n'
    s += f'节气表出生时刻（UTC+08:00）：{bazi.reference_datetime.isoformat()}\n\n'

  pillars = list(bazi.pillars)
  shishens = list(chart.shishen)
  hidden_tiangan = list(chart.hidden_tiangan)
  nayin = list(chart.nayin)
  zhangsheng = list(chart.shier_zhangsheng)

  s += '     天干                  地支                  地支藏干\n'
  for idx, head in enumerate(['年', '月', '日', '时']):
    tg = pillars[idx].tiangan
    dz = pillars[idx].dizhi

    tg_shishen: str = str(shishens[idx].tiangan)
    if idx == 2:
      tg_shishen = _day_master_mark(style)

    tg_str: str = f'{_glyph(style, tg)} [{_traits(tg)}] <{tg_shishen}>'
    dz_str: str = f'{_glyph(style, dz)} [{_traits(dz)}] <{shishens[idx].dizhi!s}>'
    hd_str: str = _hidden_tiangans(style, hidden_tiangan[idx], bazi.day_master)

    s += f'{head}：  {tg_str}      {dz_str}     {hd_str}\n'
    s += f'  -- 纳音：{nayin[idx]}  -- 十二长生：{zhangsheng[idx]}\n'

  return s


def transit_text(
  chart: BaziChart,
  *,
  dayun_count: int = 10,
  liunian_count: int = 100,
  style: TextStyle | None = None,
) -> str:
  '''
  命盘的运限展示：出生前后的节、交运时间、大运、小运与流年。

  Note:
  - 流年可以无限延续，必须限定数量：大运取前 `dayun_count` 步，流年取自出生干支年起的
    `liunian_count` 年；小运是有限序列，全部列出。
  - 节与大运区间用节气表时刻（UTC+08:00），地点盘也不采用真太阳时。
  - 出生后没有大运起于历法支持范围内时（如 HKO 后端的 2099 年末出生），抛 `ValueError`，
    与 `chart.xiaoyun` 一致；`basic_text` 不受影响。
  - 文本以换行开头、换行结尾，可直接 `print`。

  Args:
  - chart: (BaziChart) 待展示的命盘。
  - dayun_count: (int) 列出的大运步数，不小于 0。
  - liunian_count: (int) 列出的流年数，不小于 0。
  - style: (TextStyle | None) 着色钩子；`None` 为纯文本。

  Return: (str) 纯文本展示。
  '''
  _check_chart(chart)
  dayun_count = _check_count('dayun_count', dayun_count)
  liunian_count = _check_count('liunian_count', liunian_count)
  style = _check_style(style)

  day_master: Tiangan = chart.bazi.day_master
  s: str = '\n'

  utils = calendar_utils_of(chart.bazi.config.backend)
  birth_time = chart.bazi.reference_datetime
  jie_before = utils.prev_jie(birth_time)
  jie_after = utils.next_jie(birth_time)

  if chart.bazi.longitude is not None:
    s += '节与大运区间采用节气表时刻（UTC+08:00），不采用真太阳时。\n'

  s += f'出生时刻前一节：{jie_before.jieqi} - {jie_before.moment.isoformat()}\n'
  s += f'出生时刻后一节：{jie_after.jieqi} - {jie_after.moment.isoformat()}\n'
  owning, following = chart.bazi.month_jies
  counted = following if chart.dayun_order else owning
  direction = '顺排' if chart.dayun_order else '逆排'
  s += f'大运数节依据（{direction}）：{counted.jieqi} - {counted.moment.isoformat()}\n'
  s += f'交运时间： {chart.dayun_start_moment.isoformat()}\n\n'

  s += '大运：            天干                 地支                 地支藏干\n'
  for dayun in itertools.islice(chart.dayun, dayun_count):
    tg, dz = dayun.ganzhi

    tg_str: str = f'{_glyph(style, tg)} [{_traits(tg)}] <{shishen(day_master, tg)}>'
    dz_str: str = f'{_glyph(style, dz)} [{_traits(dz)}] <{shishen(day_master, dz)}>'
    hd_str: str = _hidden_tiangans(style, hidden_tiangans(dz), day_master)

    s += f'{dayun.ganzhi_year}年标签：       {tg_str}     {dz_str}    {hd_str}\n'
    s += f'               -- 公历区间：{dayun.start_moment:%Y-%m-%d %H:%M} ～ {dayun.end_moment:%Y-%m-%d %H:%M}\n'
    s += f'               -- 纳音：{nayin_str(dayun.ganzhi)}  -- 十二长生：{shier_zhangsheng(day_master, dz)}\n\n'

  s += '小运：\n'
  for xy_batch in _batched(chart.xiaoyun, 10):
    xy_batch_str: str = '  '.join(f'{xy.xusui}岁-{_ganzhi(style, xy.ganzhi)}' for xy in xy_batch)
    s += f'{xy_batch_str}\n'

  s += '\n流年：\n'
  for ln_batch in _batched(itertools.islice(chart.liunian, liunian_count), 10):
    ln_batch_str: str = '  '.join(f'{ln.ganzhi_year}-{_ganzhi(style, ln.ganzhi)}' for ln in ln_batch)
    s += f'{ln_batch_str}\n'

  return s


def chart_text(
  chart: BaziChart,
  *,
  dayun_count: int = 10,
  liunian_count: int = 100,
  style: TextStyle | None = None,
) -> str:
  '''
  命盘的完整文本展示：`basic_text` 之后接 `transit_text`。

  Args:
  - chart: (BaziChart) 待展示的命盘。
  - dayun_count: (int) 列出的大运步数，不小于 0。
  - liunian_count: (int) 列出的流年数，不小于 0。
  - style: (TextStyle | None) 着色钩子；`None` 为纯文本。

  Return: (str) 纯文本展示。
  '''
  return basic_text(chart, style=style) + transit_text(
    chart,
    dayun_count=dayun_count,
    liunian_count=liunian_count,
    style=style,
  )
