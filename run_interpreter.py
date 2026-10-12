#!/usr/bin/env python3

import argparse
import json
from random import Random, SystemRandom
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
from bazi.knowledge import Applicability, DEFAULT_SOURCE_PATH, KnowledgeBase, object_id
from bazi.context_matching import ContextProfile, ObservationScope, evaluate_context
from bazi.school import BaziConfig


_DEFAULT_OUTPUT_DIR: Final[Path] = Path(__file__).parent / 'output_data'
_ANSI_ESCAPE: Final[re.Pattern[str]] = re.compile(r'\x1b\[[0-9;]*m')


def interpret(
  chart: BaziChart,
  *,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> str:
  s: str = '' # 返回的展示字符串。
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
    __s += f"天干{j['pillars'][key][0]}（{j['tiangan_traits'][key]}，" # type: ignore # mypy 要求 TypedDict 使用字面键。
    __s += '日元' if key == 'day' else j['tiangan_shishen'][key] # type: ignore # mypy 要求 TypedDict 使用字面键。
    __s += f"）。地支{j['pillars'][key][1]}（{j['dizhi_traits'][key]}，{j['dizhi_shishen'][key]}）。" # type: ignore # mypy 要求 TypedDict 使用字面键。
    return __s
  
  s += '\n' + '-' * 60 + '\n'
  s += '年柱：' + __gen_pillar_str('year') + '\n'
  s += '月柱：' + __gen_pillar_str('month') + '\n'
  s += '日柱：' + __gen_pillar_str('day') + '\n'
  s += '时柱：' + __gen_pillar_str('hour') + '\n'

  day_master: Tiangan = chart.bazi.day_master
  s += '\n' + '-' * 60 + '\n'
  s += f"日主：{j['pillars']['day'][0]}，为{j['tiangan_traits']['day']}。\n\n"
  if descriptions := knowledge.render_subject(
    object_id(day_master),
    include_reference_only=include_reference_only,
    show_sources=show_sources,
  ):
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
    if descriptions := knowledge.render_subject(
      object_id(ss),
      include_reference_only=include_reference_only,
      show_sources=show_sources,
    ):
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
      f.write(knowledge.render_subject(
        object_id(tg),
        include_reference_only=include_reference_only,
        show_sources=show_sources,
      ))
      f.write('\n')

  ss_dir_path: Path = output_dir / 'knowledge_base' / 'shishen'
  if not ss_dir_path.exists():
    ss_dir_path.mkdir(parents=True)

  for ss in Shishen:
    with open(ss_dir_path / f'{ss}.txt', 'w', encoding='utf-8') as f:
      f.write(f'{ss}知识条目：\n')
      f.write(knowledge.render_subject(
        object_id(ss),
        include_reference_only=include_reference_only,
        show_sources=show_sources,
      ))
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


def _same_export_path(left: Path, right: Path) -> bool:
  return left.resolve() == right.resolve() or (
    left.exists() and right.exists() and left.samefile(right)
  )


def _export_json(
  parser: argparse.ArgumentParser,
  target: Path,
  knowledge_source: Path | None,
  export: Callable[[], str],
  label: str,
) -> None:
  sources: tuple[Path, ...] = (DEFAULT_SOURCE_PATH,)
  if knowledge_source is not None:
    sources += (knowledge_source,)
  if any(_same_export_path(target, source) for source in sources):
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
  parser = argparse.ArgumentParser(description='展示命盘、判别显式范围前提，或查询、校验、导出解释知识。')
  parser.add_argument('--birth-time', help='固定民用时刻；带时区输入须给经度，如 "2024-01-01T12:00:00-05:00"。')
  parser.add_argument('--gender', choices=('male', 'female'), help='与 --birth-time 一起必填。')
  parser.add_argument('--longitude', type=float, help='东经为正的角度；须用带时区固定输入及 hour/minute 精度。')
  parser.add_argument('--precision', choices=('day', 'hour', 'minute'), help='出生精度，默认 day。')
  parser.add_argument('--civil-timezone', type=_civil_timezone, help='显式出生地区 IANA 时区（Pacific/Kiritimati）或固定偏移（+14:00）；负偏移用 --civil-timezone=-05:00；须给经度。')
  parser.add_argument('--export-chart-json', type=Path, help='将固定命盘导出为可重载 JSON。')
  parser.add_argument('--seed', type=int, help='重放随机示例的种子。')
  parser.add_argument('--count', type=int, help='随机命盘数量，默认 1。')
  parser.add_argument('--include-reference-only', action='store_true', help='包含参考文字；匹配模式同时展示其前提判别。')
  parser.add_argument('--show-sources', action='store_true', help='展示条目 ID、署名及来源见证；知识查询与匹配始终展示。')
  parser.add_argument('--output-dir', type=Path, help='在此目录下导出已展示命盘。')
  parser.add_argument('--export-knowledge-base', action='store_true', help='导出全部天干及十神说明文字。')
  parser.add_argument('--query-knowledge', action='store_true', help='查询知识，不创建命盘。')
  parser.add_argument('--validate-knowledge', action='store_true', help='校验完整知识源。')
  parser.add_argument('--export-knowledge-json', type=Path, help='导出可重载知识 JSON；查询时只导出所选条目。')
  parser.add_argument('--knowledge-source', type=Path, help='为知识查询、校验、导出或前提匹配提供自定义 JSON 源。')
  parser.add_argument('--object', dest='object_id', help='讨论对象 ID，包含所有绑定角色。')
  parser.add_argument('--context', dest='context_id', help='人工给定的查阅情境 ID，不表示命盘前提判别。')
  parser.add_argument('--topic', help='知识主题。')
  parser.add_argument('--source', dest='source_id', help='来源见证 ID。')
  parser.add_argument('--viewpoint', help='解释所用观点。')
  parser.add_argument('--applicability', choices=get_args(Applicability), help='前提整理状态。')
  parser.add_argument('--time-scope', help='查阅情境所记录的时间范围。')
  parser.add_argument('--match-context', help='已注册判据 ID；对显式范围内的固定命盘求值。')
  parser.add_argument('--observation-scope', choices=get_args(ObservationScope), help='显式选择原局或原局加单流年，均包含全部实际藏干。')
  parser.add_argument('--ganzhi-year', type=int, help='流年的干支年查询坐标，不是公历时刻。')
  parser.add_argument('--export-context-json', type=Path, help='导出匹配记录、证据及完整知识快照。')
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

  if args.export_chart_json is not None:
    text_paths: list[Path] = []
    if args.output_dir is not None:
      text_paths.append(args.output_dir / 'interpretation_examples' / '0.txt')
    if args.export_knowledge_base:
      base = args.output_dir if args.output_dir is not None else _DEFAULT_OUTPUT_DIR
      text_paths.extend(base / 'knowledge_base' / 'tiangan' / f'{tg}.txt' for tg in Tiangan)
      text_paths.extend(base / 'knowledge_base' / 'shishen' / f'{ss}.txt' for ss in Shishen)
    if any(_same_export_path(args.export_chart_json, path) for path in text_paths):
      parser.error('--export-chart-json must not overlap generated TXT outputs')

  charts: Iterable[BaziChart]
  if args.birth_time is not None:
    try:
      charts = (_fixed_chart(args),)
    except (TypeError, ValueError) as error:
      parser.error(str(error))
  else:
    seed = SystemRandom().getrandbits(64) if args.seed is None else args.seed
    rng = Random(seed)
    charts = (BaziChart(Bazi.random(rng=rng)) for _ in range(count))

  output = None if args.output_dir is None else args.output_dir / 'interpretation_examples'
  if output is not None:
    try:
      output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
      parser.error(str(error))

  if args.birth_time is None:
    print(f'random seed: {seed}')
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
