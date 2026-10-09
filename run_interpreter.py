#!/usr/bin/env python3

import argparse
import json
import random
import re
from collections.abc import Callable, Iterable
from datetime import datetime, tzinfo
from pathlib import Path
from typing import Final, get_args
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from run_demo import get_basic_info
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.bazi_chart import BaziJson
from bazi.defines import Tiangan, Shishen
from bazi.knowledge import Applicability, KnowledgeBase
from bazi.context_matching import ContextProfile, ObservationScope, evaluate_context
from bazi.school import BaziConfig


_DEFAULT_OUTPUT_DIR: Final[Path] = Path(__file__).parent / 'output_data'
_ANSI_ESCAPE: Final[re.Pattern[str]] = re.compile(r'\x1b\[[0-9;]*m')


def _object_text(knowledge: KnowledgeBase, subject: Tiangan | Shishen, include_reference_only: bool, show_sources: bool) -> str:
  object_id = type(subject).__name__.lower() + '.' + subject.name.lower()
  return '\n\n'.join(
    '／'.join(entry.topics) + '：' + knowledge.render(entry, show_sources=show_sources)
    for entry in knowledge.query(object_id=object_id, include_reference_only=include_reference_only)
    if entry.legacy is None or entry.legacy.object_id == object_id
  )


def interpret(
  chart: BaziChart,
  *,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> str:
  s: str = '' # The string to return.
  knowledge = KnowledgeBase.load()
  j: BaziJson.BaziChartJsonDict = chart.json

  bazi: Bazi = chart.bazi
  if bazi.longitude is None:
    s += f'出生时间：{bazi.solar_date}, {bazi.hour}:{bazi.minute}\n'
  else:
    s += f'真太阳时（分钟显示）：{bazi.solar_datetime.isoformat()}\n'
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
  s += '\n' + '-' * 60 + '\n'
  s += f"日主：{j['pillars']['day'][0]}，为{j['tiangan_traits']['day']}。\n\n"
  if descriptions := _object_text(knowledge, day_master, include_reference_only, show_sources):
    s += descriptions + '\n\n'

  shishens: dict[Shishen, int] = { ss : 0 for ss in Shishen }
  for pillar_shishens in chart.shishen:
    if pillar_shishens.tiangan is not None:
      shishens[pillar_shishens.tiangan] += 1
    shishens[pillar_shishens.dizhi] += 1
  
  for ss, count in shishens.items():
    if count == 0:
      continue
    
    ratio: float = count / sum(shishens.values())
    s += '\n' + '-' * 60 + '\n'
    s += f'原局中，{ss}有{count}个，占比{ratio:.2%}。\n\n'
    if descriptions := _object_text(knowledge, ss, include_reference_only, show_sources):
      s += descriptions + '\n\n'

  return s


def save_knowledge_base(
  output_dir: Path = _DEFAULT_OUTPUT_DIR,
  *,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> None:
  knowledge = KnowledgeBase.load()
  tg_dir_path: Path = output_dir / 'knowledge_base' / 'tiangan'
  if not tg_dir_path.exists():
    tg_dir_path.mkdir(parents=True)

  for tg in Tiangan:
    with open(tg_dir_path / f'{tg}.txt', 'w', encoding='utf-8') as f:
      f.write(f'{tg}知识条目：\n')
      f.write(_object_text(knowledge, tg, include_reference_only, show_sources))
      f.write('\n')

  ss_dir_path: Path = output_dir / 'knowledge_base' / 'shishen'
  if not ss_dir_path.exists():
    ss_dir_path.mkdir(parents=True)

  for ss in Shishen:
    with open(ss_dir_path / f'{ss}.txt', 'w', encoding='utf-8') as f:
      f.write(f'{ss}知识条目：\n')
      f.write(_object_text(knowledge, ss, include_reference_only, show_sources))
      f.write('\n')


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


def _export_json(
  parser: argparse.ArgumentParser,
  target: Path,
  knowledge_source: Path | None,
  export: Callable[[], str],
  label: str,
) -> None:
  sources: tuple[Path, ...] = (Path(__file__).parent / 'bazi/knowledge_data.json',)
  if knowledge_source is not None:
    sources += (knowledge_source,)
  if any(
    target.resolve() == source.resolve() or (
      target.exists() and source.exists() and target.samefile(source)
    ) for source in sources
  ):
    parser.error('Export must not overwrite the editing source')
  try:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export(), encoding='utf-8')
  except OSError as error:
    parser.error(str(error))
  print(f'{label}{target}')


def _knowledge_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  if any((args.birth_time is not None, args.gender is not None, args.seed is not None, args.count is not None,
          args.output_dir, args.export_knowledge_base, args.longitude is not None,
          args.precision is not None, args.civil_timezone is not None, args.export_chart_json is not None)):
    parser.error('Knowledge mode cannot be combined with chart input or TXT export flags')
  filters = {
    'object_id': args.object_id, 'context_id': args.context_id, 'topic': args.topic,
    'source_id': args.source_id, 'viewpoint': args.viewpoint,
    'applicability': args.applicability, 'time_scope': args.time_scope,
  }
  if not args.query_knowledge and any(value is not None for value in filters.values()):
    parser.error('Knowledge filters require --query-knowledge')
  try:
    knowledge = KnowledgeBase.load(args.knowledge_source)
    selection = knowledge.query(**filters, include_reference_only=args.include_reference_only) if args.query_knowledge else None
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  if args.validate_knowledge:
    print(f'校验通过：{len(knowledge.entries)} 条目，{len(knowledge.sources)} 来源见证，{len(knowledge.contexts)} 情境。')
  if selection is not None:
    for entry in selection:
      print(knowledge.render(entry, manual_context=args.context_id is not None))
      print()
    if not selection:
      print('无匹配条目。')
  if args.export_knowledge_json is not None:
    _export_json(
      parser,
      args.export_knowledge_json,
      args.knowledge_source,
      lambda: knowledge.export_json(selection),
      '已导出知识：',
    )
  return 0


def _civil_timezone(value: str) -> tzinfo:
  try:
    if value.startswith(('+', '-')):
      zone = datetime.fromisoformat('2000-01-01T00:00:00' + value).tzinfo
      if zone is None:
        raise ValueError('Expected fixed UTC offset')
      return zone
    return ZoneInfo(value)
  except (ValueError, ZoneInfoNotFoundError, OSError) as error:
    raise argparse.ArgumentTypeError(str(error)) from error


def _fixed_chart(args: argparse.Namespace) -> BaziChart:
  return BaziChart(Bazi.create(
    args.birth_time,
    args.gender,
    BaziConfig.from_values(precision=args.precision or 'day'),
    longitude=args.longitude,
    civil_timezone=args.civil_timezone,
  ))


def _matching_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  if args.birth_time is None or args.gender is None or args.observation_scope is None:
    parser.error('Matching requires fixed --birth-time, --gender and explicit --observation-scope')
  if any((args.seed is not None, args.count is not None, args.output_dir is not None, args.export_knowledge_base,
          args.query_knowledge, args.validate_knowledge, args.export_knowledge_json is not None,
          args.export_chart_json is not None)) or any(
    value is not None for value in (args.object_id, args.context_id, args.topic, args.source_id,
                                    args.viewpoint, args.applicability, args.time_scope)
  ):
    parser.error('Matching cannot be combined with random input, TXT export or knowledge modes/filters')
  try:
    result = evaluate_context(
      _fixed_chart(args),
      criterion_id=args.match_context,
      profile=ContextProfile(args.observation_scope, args.ganzhi_year),
      knowledge=KnowledgeBase.load(args.knowledge_source),
      include_reference_only=args.include_reference_only,
    )
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  print(result.render())
  if args.export_context_json is not None:
    _export_json(
      parser,
      args.export_context_json,
      args.knowledge_source,
      result.export_json,
      '已导出前提判别记录：',
    )
  return 0


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description='Display charts, match scoped premises, or query, validate and export interpretation knowledge.')
  parser.add_argument('--birth-time', help='Fixed civil time; aware input requires longitude, e.g. "2024-01-01T12:00:00-05:00".')
  parser.add_argument('--gender', choices=('male', 'female'), help='Required with --birth-time.')
  parser.add_argument('--longitude', type=float, help='East-positive degrees; requires aware fixed input and hour/minute precision.')
  parser.add_argument('--precision', choices=('day', 'hour', 'minute'), help='Birth precision (default: day).')
  parser.add_argument('--civil-timezone', type=_civil_timezone, help='Explicit birth-region IANA zone (Pacific/Kiritimati) or fixed offset (+14:00); use --civil-timezone=-05:00 for negative offsets; requires longitude.')
  parser.add_argument('--export-chart-json', type=Path, help='Export the fixed chart as reloadable JSON.')
  parser.add_argument('--seed', type=int, help='Seed for reproducible random examples.')
  parser.add_argument('--count', type=int, help='Number of random charts (default: 1).')
  parser.add_argument('--include-reference-only', action='store_true', help='Include reference text; matching mode also displays its premise verdict.')
  parser.add_argument('--show-sources', action='store_true', help='Show claim IDs, attribution and source witnesses (always included in knowledge queries and matching).')
  parser.add_argument('--output-dir', type=Path, help='Export the displayed charts below this directory.')
  parser.add_argument('--export-knowledge-base', action='store_true', help='Export descriptions for every Tiangan and Shishen.')
  parser.add_argument('--query-knowledge', action='store_true', help='Query knowledge without creating a chart.')
  parser.add_argument('--validate-knowledge', action='store_true', help='Validate the whole knowledge source.')
  parser.add_argument('--export-knowledge-json', type=Path, help='Export reloadable knowledge JSON; with a query, export its selection.')
  parser.add_argument('--knowledge-source', type=Path, help='Use an edited JSON source for knowledge queries, validation, export or context matching.')
  parser.add_argument('--object', dest='object_id', help='Discussion object ID, including any bound role.')
  parser.add_argument('--context', dest='context_id', help='Manually supplied lookup context ID, not a chart verdict.')
  parser.add_argument('--topic', help='Knowledge topic.')
  parser.add_argument('--source', dest='source_id', help='Source-witness ID.')
  parser.add_argument('--viewpoint', help='Interpretation viewpoint.')
  parser.add_argument('--applicability', choices=get_args(Applicability), help='Premise organization state.')
  parser.add_argument('--time-scope', help='Time scope recorded by a lookup context.')
  parser.add_argument('--match-context', help='Registered criterion ID; evaluate an explicitly scoped fixed chart.')
  parser.add_argument('--observation-scope', choices=get_args(ObservationScope), help='Explicit natal or natal-plus-one-LIUNIAN scope; all hidden stems are included.')
  parser.add_argument('--ganzhi-year', type=int, help='Ganzhi-year query coordinate for LIUNIAN, not a Gregorian timestamp.')
  parser.add_argument('--export-context-json', type=Path, help='Export the matching record, evidence and complete knowledge snapshot.')
  args = parser.parse_args(argv)

  if args.match_context is not None:
    return _matching_main(parser, args)
  if args.observation_scope is not None or args.ganzhi_year is not None or args.export_context_json is not None:
    parser.error('Matching inputs require --match-context')
  if args.query_knowledge or args.validate_knowledge or args.export_knowledge_json is not None:
    return _knowledge_main(parser, args)
  if args.knowledge_source is not None or any(
    value is not None for value in (args.object_id, args.context_id, args.topic, args.source_id,
                                    args.viewpoint, args.applicability, args.time_scope)
  ):
    parser.error('Knowledge inputs require a knowledge mode flag')
  count = 1 if args.count is None else args.count
  if count < 1:
    parser.error('--count must be positive')
  if (args.birth_time is None) != (args.gender is None):
    parser.error('--birth-time and --gender must be supplied together')
  if args.birth_time is not None and (args.seed is not None or count != 1):
    parser.error('--seed and multiple charts require random input')
  if args.birth_time is None and any(value is not None for value in (
    args.longitude, args.precision, args.civil_timezone, args.export_chart_json,
  )):
    parser.error('Location, precision and chart JSON flags require fixed birth input')
  if args.seed is not None:
    random.seed(args.seed)

  charts: Iterable[BaziChart]
  if args.birth_time is not None:
    try:
      charts = (_fixed_chart(args),)
    except (TypeError, ValueError) as error:
      parser.error(str(error))
  else:
    charts = (BaziChart(Bazi.random()) for _ in range(count))

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
    if args.export_chart_json is not None:
      def __export_chart(chart: BaziChart = chart) -> str:
        return json.dumps(chart.json, ensure_ascii=False, indent=2) + '\n'
      _export_json(parser, args.export_chart_json, None, __export_chart, '已导出命盘：')
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
