#!/usr/bin/env python3

import argparse
import random
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Final

from run_demo import get_basic_info
from bazi.common import frozendict
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.descriptions import (
  DescriptionClaim, DescriptionClaims, DescriptionOutput,
)
from bazi.bazi_chart import BaziJson
from bazi.defines import Tiangan, Shishen
from bazi.interpreter import Interpreter


_DEFAULT_OUTPUT_DIR: Final[Path] = Path(__file__).parent / 'output_data'
_ANSI_ESCAPE: Final[re.Pattern[str]] = re.compile(r'\x1b\[[0-9;]*m')


def _claim_text(claim: DescriptionClaim, show_sources: bool) -> str:
  assert isinstance(claim, DescriptionClaim)
  assert isinstance(show_sources, bool)
  notes: list[str] = []
  if claim.output is DescriptionOutput.REFERENCE_ONLY:
    notes.append('仅供参考')
  if claim.conditions:
    notes.append('适用条件需整盘判断，尚未判断')
  if not claim.sources:
    notes.append('来源尚未核实')

  s = claim.text
  if notes:
    s += '【' + '；'.join(notes) + '】'

  if show_sources:
    s += f'\n条目：{claim.claim_id}；署名：{claim.attribution}\n'
    for source_id in claim.sources:
      source = Interpreter.query_source(source_id)
      s += f'来源：{source.work}；{source.attribution}；{source.edition}；{source.locator}\n'
      s += f'{source.url}\n支持范围：{source.supports}\n局限：{source.limitations}\n'
  return s


def _claim_fields(claims: DescriptionClaims, show_sources: bool) -> frozendict[str, tuple[str, ...]]:
  assert isinstance(claims, frozendict)
  assert isinstance(show_sources, bool)
  return frozendict({
    field: tuple(_claim_text(claim, show_sources) for claim in items)
    for field, items in claims.items()
  })


def interpret(
  chart: BaziChart,
  *,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> str:
  s: str = '' # The string to return.
  j: BaziJson.BaziChartJsonDict = chart.json

  bazi: Bazi = chart.bazi
  s += f'出生时间：{bazi.solar_date}, {bazi.hour}:{bazi.minute}\n'
  s += f'性别：{bazi.gender}\n'

  def __gen_pillar_str(key: str) -> str:
    assert key in ['year', 'month', 'day', 'hour']
    __s: str = ''
    __s += f"天干{j['pillars'][key][0]}（{j['tiangan_traits'][key]}，" # type: ignore # mypy complains.
    __s += '日元' if key == 'day' else j['tiangan_shishen'][key] # type: ignore # mypy complains.
    __s += f"）。地支{j['pillars'][key][1]}（{j['dizhi_traits'][key]}，{j['dizhi_shishen'][key]}）。" # type: ignore # mypy complains.
    return __s
  
  s += '\n' + '-' * 60 + '\n'
  s += '年柱：' + __gen_pillar_str('year') + '\n'
  s += '月柱：' + __gen_pillar_str('month') + '\n'
  s += '日柱：' + __gen_pillar_str('day') + '\n'
  s += '时柱：' + __gen_pillar_str('hour') + '\n'

  day_master: Tiangan = chart.bazi.day_master
  day_master_desc: frozendict[str, tuple[str, ...]] = _claim_fields(
    Interpreter.query_tiangan(day_master, include_reference_only=include_reference_only),
    show_sources,
  )

  s += '\n' + '-' * 60 + '\n'
  s += f"日主：{j['pillars']['day'][0]}，为{j['tiangan_traits']['day']}。\n\n"
  if day_master_desc['general']:
    s += '解读：' + '\n'.join(day_master_desc['general']) + '\n\n'
  if day_master_desc['personality']:
    s += '日主的个性：' + '\n'.join(day_master_desc['personality']) + '\n\n'

  shishens: dict[Shishen, int] = { ss : 0 for ss in Shishen }
  for pillar_shishens in chart.shishen:
    if pillar_shishens.tiangan is not None:
      shishens[pillar_shishens.tiangan] += 1
    shishens[pillar_shishens.dizhi] += 1
  
  for ss, count in shishens.items():
    if count == 0:
      continue
    
    ratio: float = count / sum(shishens.values())
    desc: frozendict[str, tuple[str, ...]] = _claim_fields(
      Interpreter.query_shishen(ss, include_reference_only=include_reference_only),
      show_sources,
    )

    s += '\n' + '-' * 60 + '\n'
    s += f'原局中，{ss}有{count}个，占比{ratio:.2%}。\n\n'
    if desc['general']:
      s += '解读：' + '\n'.join(desc['general']) + '\n\n'
    if desc['in_good_status']:
      s += f'{ss}代表的特点：' + '\n'.join(desc['in_good_status']) + '\n\n'
    if desc['in_bad_status']:
      s += f'当{ss}状态不好时，可能会有以下特点：' + '\n'.join(desc['in_bad_status']) + '\n\n'
    if desc['relationship']:
      s += f'{ss}的恋爱/交友观：' + '\n'.join(desc['relationship']) + '\n\n'

  return s


def save_knowledge_base(
  output_dir: Path = _DEFAULT_OUTPUT_DIR,
  *,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> None:
  tg_dir_path: Path = output_dir / 'knowledge_base' / 'tiangan'
  if not tg_dir_path.exists():
    tg_dir_path.mkdir(parents=True)

  for tg in Tiangan:
    tg_desc = _claim_fields(
      Interpreter.query_tiangan(tg, include_reference_only=include_reference_only),
      show_sources,
    )
    with open(tg_dir_path / f'{tg}.txt', 'w', encoding='utf-8') as f:
      f.write('天干基本解读：\n')
      f.write('\n'.join(tg_desc['general']))
      f.write('\n\n')

      f.write('天干代表的个性：\n')
      f.write('\n'.join(tg_desc['personality']))
      f.write('\n\n')

  ss_dir_path: Path = output_dir / 'knowledge_base' / 'shishen'
  if not ss_dir_path.exists():
    ss_dir_path.mkdir(parents=True)

  for ss in Shishen:
    ss_desc = _claim_fields(
      Interpreter.query_shishen(ss, include_reference_only=include_reference_only),
      show_sources,
    )
    with open(ss_dir_path / f'{ss}.txt', 'w', encoding='utf-8') as f:
      f.write(f'{ss}基本解读：\n')
      f.write('\n'.join(ss_desc['general']))
      f.write('\n\n')

      f.write(f'{ss}能量状态佳时所代表的特点：\n')
      f.write('\n'.join(ss_desc['in_good_status']))
      f.write('\n\n')

      f.write(f'{ss}能量状态不佳时所代表的特点：\n')
      f.write('\n'.join(ss_desc['in_bad_status']))
      f.write('\n\n')

      f.write(f'{ss}的恋爱/交友观：\n')
      f.write('\n'.join(ss_desc['relationship']))
      f.write('\n\n')


def _chart_text(
  chart: BaziChart,
  *,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> str:
  return get_basic_info(chart) + '\n' + '=' * 60 + '\n' + interpret(
    chart,
    include_reference_only=include_reference_only,
    show_sources=show_sources,
  )


def _write_chart(text: str, output: Path, index: int) -> None:
  assert isinstance(text, str)
  assert isinstance(output, Path)
  assert isinstance(index, int)
  (output / f'{index}.txt').write_text(_ANSI_ESCAPE.sub('', text), encoding='utf-8')


def save_chart_examples(count: int = 50) -> None:
  output = _DEFAULT_OUTPUT_DIR / 'interpretation_examples'
  output.mkdir(parents=True, exist_ok=True)
  for i in range(count):
    _write_chart(_chart_text(BaziChart(Bazi.random())), output, i)


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description='Display a chart and its static descriptions.')
  parser.add_argument('--birth-time', help='Local civil time, e.g. "2000-01-01 12:00".')
  parser.add_argument('--gender', choices=('male', 'female'), help='Required with --birth-time.')
  parser.add_argument('--seed', type=int, help='Seed for reproducible random examples.')
  parser.add_argument('--count', type=int, default=1, help='Number of random charts (default: 1).')
  parser.add_argument('--include-reference-only', action='store_true', help='Include unevaluated reference text.')
  parser.add_argument('--show-sources', action='store_true', help='Show claim IDs, attribution and source witnesses.')
  parser.add_argument('--output-dir', type=Path, help='Export the displayed charts below this directory.')
  parser.add_argument('--export-knowledge-base', action='store_true', help='Export descriptions for every Tiangan and Shishen.')
  args = parser.parse_args(argv)

  if args.count < 1:
    parser.error('--count must be positive')
  if (args.birth_time is None) != (args.gender is None):
    parser.error('--birth-time and --gender must be supplied together')
  if args.birth_time is not None and (args.seed is not None or args.count != 1):
    parser.error('--seed and multiple charts require random input')
  if args.seed is not None:
    random.seed(args.seed)

  charts: Iterable[BaziChart]
  if args.birth_time is not None:
    try:
      charts = (BaziChart(Bazi.create(args.birth_time, args.gender)),)
    except (TypeError, ValueError) as error:
      parser.error(str(error))
  else:
    charts = (BaziChart(Bazi.random()) for _ in range(args.count))

  output = None if args.output_dir is None else args.output_dir / 'interpretation_examples'
  if output is not None:
    try:
      output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
      parser.error(str(error))

  for i, chart in enumerate(charts):
    text = _chart_text(
      chart,
      include_reference_only=args.include_reference_only,
      show_sources=args.show_sources,
    )
    print(text)
    if output is not None:
      try:
        _write_chart(text, output, i)
      except OSError as error:
        parser.error(str(error))

  if args.export_knowledge_base:
    try:
      save_knowledge_base(
        args.output_dir if args.output_dir is not None else _DEFAULT_OUTPUT_DIR,
        include_reference_only=args.include_reference_only,
        show_sources=args.show_sources,
      )
    except OSError as error:
      parser.error(str(error))

  return 0


if __name__ == '__main__':
  raise SystemExit(main())
