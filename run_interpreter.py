#!/usr/bin/env python3

import argparse
import random
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Final, get_args

from run_demo import get_basic_info
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.bazi_chart import BaziJson
from bazi.defines import Tiangan, Shishen
from bazi.knowledge import Applicability, KnowledgeBase


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


def _knowledge_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  if any((args.birth_time is not None, args.gender is not None, args.seed is not None, args.count is not None,
          args.output_dir, args.export_knowledge_base)):
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
    editing_sources: tuple[Path, ...] = (Path(__file__).parent / 'bazi/knowledge_data.json',)
    if args.knowledge_source is not None:
      editing_sources += (args.knowledge_source,)
    if any(
      args.export_knowledge_json.resolve() == source.resolve() or (
        args.export_knowledge_json.exists() and source.exists() and args.export_knowledge_json.samefile(source)
      )
      for source in editing_sources
    ):
      parser.error('Export must not overwrite the editing source')
    try:
      args.export_knowledge_json.parent.mkdir(parents=True, exist_ok=True)
      args.export_knowledge_json.write_text(knowledge.export_json(selection), encoding='utf-8')
    except OSError as error:
      parser.error(str(error))
    print(f'已导出知识：{args.export_knowledge_json}')
  return 0


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description='Display charts or query, validate and export interpretation knowledge.')
  parser.add_argument('--birth-time', help='Local civil time, e.g. "2000-01-01 12:00".')
  parser.add_argument('--gender', choices=('male', 'female'), help='Required with --birth-time.')
  parser.add_argument('--seed', type=int, help='Seed for reproducible random examples.')
  parser.add_argument('--count', type=int, help='Number of random charts (default: 1).')
  parser.add_argument('--include-reference-only', action='store_true', help='Include unevaluated reference text.')
  parser.add_argument('--show-sources', action='store_true', help='Show claim IDs, attribution and source witnesses.')
  parser.add_argument('--output-dir', type=Path, help='Export the displayed charts below this directory.')
  parser.add_argument('--export-knowledge-base', action='store_true', help='Export descriptions for every Tiangan and Shishen.')
  parser.add_argument('--query-knowledge', action='store_true', help='Query knowledge without creating a chart.')
  parser.add_argument('--validate-knowledge', action='store_true', help='Validate the whole knowledge source.')
  parser.add_argument('--export-knowledge-json', type=Path, help='Export reloadable knowledge JSON; with a query, export its selection.')
  parser.add_argument('--knowledge-source', type=Path, help='Use an edited JSON source in knowledge mode.')
  parser.add_argument('--object', dest='object_id', help='Discussion object ID, including any bound role.')
  parser.add_argument('--context', dest='context_id', help='Manually supplied lookup context ID, not a chart verdict.')
  parser.add_argument('--topic', help='Knowledge topic.')
  parser.add_argument('--source', dest='source_id', help='Source-witness ID.')
  parser.add_argument('--viewpoint', help='Interpretation viewpoint.')
  parser.add_argument('--applicability', choices=get_args(Applicability), help='Premise organization state.')
  parser.add_argument('--time-scope', help='Time scope recorded by a lookup context.')
  args = parser.parse_args(argv)

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
  if args.seed is not None:
    random.seed(args.seed)

  charts: Iterable[BaziChart]
  if args.birth_time is not None:
    try:
      charts = (BaziChart(Bazi.create(args.birth_time, args.gender)),)
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
