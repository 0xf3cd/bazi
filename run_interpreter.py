#!/usr/bin/env python3

import argparse
import copy
import json
import shlex
import sys
from random import Random, SystemRandom
import re
from collections.abc import Callable, Iterable
from datetime import date, datetime, timedelta, tzinfo
from pathlib import Path
from typing import Final, get_args
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from run_demo import get_basic_info
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.bazi_chart import BaziJson
from bazi.defines import Tiangan, Shishen, Dizhi
from bazi.knowledge import Applicability, DEFAULT_SOURCE_PATH, KnowledgeBase, object_id
from bazi.context_matching import (
  ContextProfile, ObservationScope, RelationshipProfile, TransitCoordinate, TransitEntry,
  _CRITERIA, criteria, criterion, evaluate_context,
)
from bazi.school import BaziConfig
from bazi.transits import TransitKind


_DEFAULT_OUTPUT_DIR: Final[Path] = Path(__file__).parent / 'output_data'
_ANSI_ESCAPE: Final[re.Pattern[str]] = re.compile(r'\x1b\[[0-9;]*m')


def interpret(
  chart: BaziChart,
  *,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> str:
  s: str = ''
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


def _gz_month(value: str) -> Dizhi:
  try:
    return Dizhi.from_str(value)
  except (TypeError, ValueError) as error:
    raise argparse.ArgumentTypeError(str(error)) from error


def _solar_date(value: str) -> date:
  try:
    parsed = date.fromisoformat(value)
  except ValueError as error:
    raise argparse.ArgumentTypeError(str(error)) from error
  if parsed.isoformat() != value:
    raise argparse.ArgumentTypeError(f'Expected canonical ISO date: {value}')
  return parsed


def _solar_moment(value: str) -> datetime:
  try:
    parsed = datetime.fromisoformat(value)
  except ValueError as error:
    raise argparse.ArgumentTypeError(str(error)) from error
  if parsed.tzinfo is not None or parsed.isoformat() != value:
    raise argparse.ArgumentTypeError(f'Expected canonical naive moment: {value}')
  return parsed


def _transit_kinds(parser: argparse.ArgumentParser, value: str) -> tuple[TransitKind, ...]:
  '''解析逗号分隔的种类值；查重、拒未知名与空项，再按固定种类序规范化。'''
  kinds: list[TransitKind] = []
  for item in value.split(','):
    try:
      kinds.append(TransitKind(item))
    except ValueError:
      parser.error(f'Unsupported transit kind: {item}')
  if len(set(kinds)) != len(kinds):
    parser.error(f'Duplicate transit kinds: {value}')
  return tuple(kind for kind in TransitKind if kind in frozenset(kinds))


def _relationship_profile(parser: argparse.ArgumentParser, args: argparse.Namespace) -> RelationshipProfile:
  '''由 CLI 参数构造婚恋 profile；构造期拒绝互斥与缺字段组合。'''
  coordinate_flags = any((
    args.ganzhi_year is not None, args.gz_month is not None,
    args.solar_date is not None, args.solar_moment is not None,
  ))
  if args.transit_entry is None and coordinate_flags:
    parser.error('Transit coordinates require --transit-entry')
  kinds = _transit_kinds(parser, args.transit_kinds) if args.transit_kinds is not None else ()
  try:
    coordinate = None
    if args.transit_entry is not None:
      coordinate = TransitCoordinate(
        args.transit_entry,
        gz_year=args.ganzhi_year,
        gz_month=args.gz_month,
        solar_date=args.solar_date,
        solar_moment=args.solar_moment,
      )
    return RelationshipProfile(args.observation_scope, coordinate, kinds)
  except (TypeError, ValueError) as error:
    parser.error(str(error))
  raise AssertionError('Unreachable parser state') # pragma: no cover # parser.error 总是退出。


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
  if args.match_context not in _CRITERIA:
    parser.error(f'Unsupported value: {args.match_context}')
  if _CRITERIA[args.match_context].profile_kind == 'context' and any((
    args.transit_entry is not None, args.gz_month is not None, args.solar_date is not None,
    args.solar_moment is not None, args.transit_kinds is not None,
  )):
    parser.error('Context criteria cannot combine transit entry, coordinate or kind inputs')
  try:
    profile: ContextProfile | RelationshipProfile
    if _CRITERIA[args.match_context].profile_kind == 'context':
      profile = ContextProfile(args.observation_scope, args.ganzhi_year)
    else:
      profile = _relationship_profile(parser, args)
    result = evaluate_context(
      _fixed_chart(args),
      criterion_id=args.match_context,
      profile=profile,
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
      '已导出判别记录：',
    )
  return 0


def _legacy_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description='展示命盘、判别显式范围前提，或查询、校验、导出解释知识。')
  parser.add_argument('--birth-time', help='固定民用时刻；带时区输入须给经度，如 "2024-01-01T12:00:00-05:00"。')
  parser.add_argument('--gender', choices=('male', 'female'), help='与 --birth-time 一起必填。')
  parser.add_argument('--longitude', type=float, help='东经为正的角度；须用带时区固定输入及 hour/minute 精度。')
  parser.add_argument('--precision', choices=('day', 'hour', 'minute'), help='出生精度，默认 day。')
  parser.add_argument('--civil-timezone', type=_civil_timezone, help='显式出生地区 IANA 时区（Pacific/Kiritimati）或固定偏移（+14:00）；负偏移用 --civil-timezone=-05:00；须给经度。')
  parser.add_argument('--export-chart-json', type=Path, help='将固定命盘导出为可重载 JSON。')
  parser.add_argument('--seed', type=int, help='重放随机示例的种子。')
  parser.add_argument('--count', type=int, help='随机命盘数量，默认 1。')
  parser.add_argument('--include-reference-only', action='store_true', help='包含参考文字；匹配模式同时展示前提判别或条件参考。')
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
  parser.add_argument('--observation-scope', choices=get_args(ObservationScope) + ('natal_and_transits',), help='显式选择原局或原局加单流年（婚恋以外的判据），或原局加显式选定岁运（婚恋判据）。')
  parser.add_argument('--ganzhi-year', type=int, help='干支年查询坐标：婚恋以外的判据为流年，婚恋 at_year／at_month 入口为年份。')
  parser.add_argument('--transit-entry', choices=get_args(TransitEntry), help='婚恋判据的显式岁运查询入口；与坐标字段共同构成查询坐标。')
  parser.add_argument('--gz-month', type=_gz_month, help='干支月坐标（中文支名），配 at_month 入口与 --ganzhi-year。')
  parser.add_argument('--solar-date', type=_solar_date, help='东八区无时区公历日期坐标（如 2024-04-10），配 at_date 入口。')
  parser.add_argument('--solar-moment', type=_solar_moment, help='东八区无时区时刻坐标（如 2024-04-10T12:00:00，可含微秒），配 at_moment 入口；要求 HOUR／MINUTE 原盘，DAY 精度返回 UNKNOWN。')
  parser.add_argument('--transit-kinds', help='逗号分隔的岁运种类值（xiaoyun,dayun,liunian,liuyue,liuri）；重复或未知值报错，其余按固定序规范化。')
  parser.add_argument('--export-context-json', type=Path, help='导出匹配记录、证据及完整知识快照。')
  return parser


def _chart_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
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


def _legacy_dispatch(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  if args.match_context is not None:
    return _matching_main(parser, args)
  if args.observation_scope is not None or args.ganzhi_year is not None or args.export_context_json is not None or any(
    value is not None for value in (
      args.transit_entry, args.gz_month, args.solar_date, args.solar_moment, args.transit_kinds,
    )
  ):
    parser.error('Matching inputs require --match-context')
  if args.query_knowledge or args.validate_knowledge or args.export_knowledge_json is not None:
    return _knowledge_main(parser, args)
  if args.knowledge_source is not None or any(
    value is not None for value in (args.object_id, args.context_id, args.topic, args.source_id,
                                    args.viewpoint, args.applicability, args.time_scope)
  ):
    parser.error('Knowledge inputs require a knowledge mode flag')
  return _chart_main(parser, args)


_COMMANDS: Final[tuple[str, ...]] = ('chart', 'knowledge', 'match')
_PROG: Final[str] = 'python run_interpreter.py'

# `--list-values` 的取值与知识过滤选项同名；右侧是 `KnowledgeBase.filter_values` 的维度名。
_LIST_DIMENSIONS: Final[dict[str, str]] = {
  'object': 'object_id', 'context': 'context_id', 'source': 'source_id', 'topic': 'topic',
  'viewpoint': 'viewpoint', 'applicability': 'applicability', 'time-scope': 'time_scope',
}

# 判据目录里的查询坐标字段对应的命令行选项。
_COORDINATE_FLAGS: Final[dict[str, str]] = {
  'ganzhi_year': '--ganzhi-year', 'gz_year': '--ganzhi-year', 'gz_month': '--gz-month',
  'solar_date': '--solar-date', 'solar_moment': '--solar-moment',
}

_MATCH_EXAMPLE: Final[str] = (
  f'{_PROG} match <判据ID> --birth-time "2000-01-01 12:00" --gender female --observation-scope natal'
)


def _add_chart_arguments(parser: argparse.ArgumentParser) -> None:
  basic = parser.add_argument_group('出生信息（都不给则随机生成一张盘）')
  basic.add_argument('--birth-time', help='公历出生时刻，如 "2000-01-01 12:00"。')
  basic.add_argument('--gender', choices=('male', 'female'), help='给了 --birth-time 就要给。')
  more = parser.add_argument_group('更多选项（都可省略）')
  more.add_argument('--seed', type=int, help='重放随机命盘的种子；随机命盘的种子会打印在第一行。')
  more.add_argument('--count', type=int, help='随机命盘数量，默认 1。')
  more.add_argument('--precision', choices=('day', 'hour', 'minute'), help='出生精度，默认 day。')
  more.add_argument('--longitude', type=float, help='东经为正的角度，启用真太阳时；须带时区的出生时刻与 hour/minute 精度。')
  more.add_argument('--civil-timezone', type=_civil_timezone, help='出生地时区（IANA 名如 Pacific/Kiritimati，或固定偏移如 +14:00；负偏移写成 --civil-timezone=-05:00）；须给经度。')
  more.add_argument('--include-reference-only', action='store_true', help='同时显示仅供参考的知识条目。')
  more.add_argument('--show-sources', action='store_true', help='显示条目 ID、署名与来源见证。')
  more.add_argument('--output-dir', type=Path, help='把展示的命盘另存为这个目录下的文本文件。')
  more.add_argument('--export-chart-json', type=Path, help='把命盘导出为可重新载入的 JSON。')


def _add_knowledge_arguments(parser: argparse.ArgumentParser) -> None:
  common = parser.add_argument_group('查询（给任一条件就是查询；条件可以组合）')
  common.add_argument('--object', dest='object_id', help='讨论对象 ID，如 tiangan.ding。')
  common.add_argument('--topic', help='知识主题。')
  common.add_argument('--list-values', choices=tuple(_LIST_DIMENSIONS), help='列出某个条件的全部合法值。')
  common.add_argument('--all', action='store_true', help='列出全部默认可见的条目。')
  more = parser.add_argument_group('更多选项（都可省略）')
  more.add_argument('--context', dest='context_id', help='人工给定的查阅情境 ID，不表示命盘前提判别。')
  more.add_argument('--source', dest='source_id', help='来源见证 ID。')
  more.add_argument('--viewpoint', help='解释所用观点。')
  more.add_argument('--applicability', choices=get_args(Applicability), help='前提整理状态。')
  more.add_argument('--time-scope', help='查阅情境所记录的时间范围。')
  more.add_argument('--include-reference-only', action='store_true', help='同时包含仅供参考的条目。')
  more.add_argument('--knowledge-source', type=Path, help='改用你自己的知识 JSON。')
  more.add_argument('--validate-knowledge', action='store_true', help='校验完整知识源。')
  more.add_argument('--export-knowledge-json', type=Path, help='导出可重新载入的知识 JSON；有查询条件时只导出所选条目。')
  more.add_argument('--export-knowledge-base', action='store_true', help='把全部天干与十神说明各存成一个文本文件。')
  more.add_argument('--output-dir', type=Path, help='--export-knowledge-base 的目录，默认 output_data。')


def _add_match_arguments(parser: argparse.ArgumentParser) -> None:
  parser.add_argument('criterion', nargs='?', metavar='判据ID', help='不给则列出全部判据；只给 ID 则说明该判据与所需输入。')
  common = parser.add_argument_group('求值所需（给了任一求值输入就会求值）')
  common.add_argument('--birth-time', help='公历出生时刻，如 "2000-01-01 12:00"。')
  common.add_argument('--gender', choices=('male', 'female'), help='性别。')
  common.add_argument('--observation-scope', choices=get_args(ObservationScope) + ('natal_and_transits',), help='判别范围，须显式选择；各判据支持的范围见判据说明。')
  more = parser.add_argument_group('更多选项（按判据说明所需给出，其余可省略）')
  more.add_argument('--ganzhi-year', type=int, help='干支年坐标。')
  more.add_argument('--transit-entry', choices=get_args(TransitEntry), help='岁运查询入口（婚恋判据）。')
  more.add_argument('--gz-month', type=_gz_month, help='干支月坐标（中文支名），配 at_month 入口。')
  more.add_argument('--solar-date', type=_solar_date, help='东八区公历日期坐标，如 2024-04-10，配 at_date 入口。')
  more.add_argument('--solar-moment', type=_solar_moment, help='东八区时刻坐标，如 2024-04-10T12:00:00，配 at_moment 入口。')
  more.add_argument('--transit-kinds', help='逗号分隔的岁运种类（xiaoyun,dayun,liunian,liuyue,liuri）。')
  more.add_argument('--precision', choices=('day', 'hour', 'minute'), help='出生精度，默认 day。')
  more.add_argument('--longitude', type=float, help='东经为正的角度，启用真太阳时。')
  more.add_argument('--civil-timezone', type=_civil_timezone, help='出生地时区；须给经度。')
  more.add_argument('--include-reference-only', action='store_true', help='同时显示仅供参考的条目与条件参考。')
  more.add_argument('--knowledge-source', type=Path, help='改用你自己的知识 JSON。')
  more.add_argument('--export-context-json', type=Path, help='导出判别记录与知识快照。')


def _command_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    prog=_PROG,
    description='源码脚本：展示命盘、查询解释知识、判别判据前提。先选一个任务，再用「任务 --help」看它的选项。',
    epilog=(
      '示例：\n'
      f'  {_PROG} chart                                  随机命盘\n'
      f'  {_PROG} chart --birth-time "2000-01-01 12:00" --gender male\n'
      f'  {_PROG} knowledge                              知识库概览\n'
      f'  {_PROG} knowledge --object tiangan.ding\n'
      f'  {_PROG} match                                  列出全部判据\n'
      f'  {_PROG} match <判据ID>                         判据说明与所需输入\n'
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )
  tasks = parser.add_subparsers(dest='command', metavar='<任务>', required=True)
  for name, summary, usage, add in (
    ('chart', '展示命盘；不给出生信息就随机生成', '[--birth-time 时刻 --gender male|female] [选项]', _add_chart_arguments),
    ('knowledge', '查询、校验、导出解释知识，不需要命盘', '[查询条件] [选项]', _add_knowledge_arguments),
    ('match', '查看判据，或对给定命盘判别前提', '[判据ID] [选项]', _add_match_arguments),
  ):
    add(tasks.add_parser(name, help=summary, description=summary, usage=f'{_PROG} {name} {usage}'))
  return parser


def _fill_legacy_defaults(args: argparse.Namespace) -> None:
  '''补齐新子命令没有提供的旧选项，使共用的核心处理函数读到与旧路径相同的字段。'''
  for action in _legacy_parser()._actions:
    if action.dest != 'help' and not hasattr(args, action.dest):
      setattr(args, action.dest, action.default)


def _knowledge_overview(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  try:
    knowledge = KnowledgeBase.load(args.knowledge_source)
    sizes = {flag: len(knowledge.filter_values(dimension)) for flag, dimension in _LIST_DIMENSIONS.items()}
    visible = len(knowledge.query())
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  print(f'知识库：{len(knowledge.entries)} 条目（默认可见 {visible} 条；--include-reference-only 另含仅供参考的条目），'
        f'{len(knowledge.sources)} 来源见证，{len(knowledge.contexts)} 情境。')
  print('可用来筛选的条件（--list-values 条件名 查看全部合法值）：')
  for flag, size in sizes.items():
    print(f'  --{flag}：{size} 个值')
  print('示例：')
  print(f'  {_PROG} knowledge --object tiangan.ding')
  print(f'  {_PROG} knowledge --list-values topic')
  print(f'  {_PROG} knowledge --all')
  return 0


def _knowledge_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  filters = (args.object_id, args.context_id, args.topic, args.source_id, args.viewpoint, args.applicability, args.time_scope)
  query = args.all or any(value is not None for value in filters)
  if args.output_dir is not None and not args.export_knowledge_base:
    parser.error('--output-dir only applies with --export-knowledge-base')
  if not any((query, args.list_values, args.validate_knowledge, args.export_knowledge_json is not None,
              args.export_knowledge_base)):
    return _knowledge_overview(parser, args)

  if args.list_values is not None:
    try:
      for value in KnowledgeBase.load(args.knowledge_source).filter_values(_LIST_DIMENSIONS[args.list_values]):
        print(value)
    except (OSError, TypeError, ValueError) as error:
      parser.error(str(error))
  if query or args.validate_knowledge or args.export_knowledge_json is not None:
    core = copy.copy(args)
    core.query_knowledge = query
    core.output_dir = None
    core.export_knowledge_base = False
    _knowledge_main(parser, core)
  if args.export_knowledge_base:
    try:
      save_knowledge_base(
        args.output_dir if args.output_dir is not None else _DEFAULT_OUTPUT_DIR,
        include_reference_only=args.include_reference_only,
      )
    except OSError as error:
      parser.error(str(error))
  return 0


def _criteria_listing() -> int:
  for criterion_id, info in criteria().items():
    print(f'{criterion_id}  {info.definition}')
    print(f'    可选范围：{", ".join(info.scopes)}')
  print(f'用 {_PROG} match <判据ID> 查看某个判据的说明与所需输入。')
  return 0


def _criterion_description(parser: argparse.ArgumentParser, criterion_id: str) -> int:
  try:
    info = criterion(criterion_id)
  except (TypeError, ValueError) as error:
    parser.error(f'{error}（{_PROG} match 可列出全部判据）')
  print(f'{info.criterion_id}\n  {info.definition}')
  print(f'  求值需要：--birth-time、--gender、--observation-scope（可选：{", ".join(info.scopes)}）')
  for scope, inputs in info.scope_inputs.items():
    if inputs:
      needs = '、'.join(
        '--transit-kinds' if name == 'kinds' else '--transit-entry 及其坐标（见下）' if name == 'coordinate'
        else _COORDINATE_FLAGS.get(name, name) for name in inputs
      )
      print(f'  --observation-scope {scope} 还需要：{needs}')
  for entry, fields in info.transit_entries.items():
    flags = ' '.join(_COORDINATE_FLAGS[field] for field in fields)
    print(f'  --transit-entry {entry}：{flags}')
  if info.required_gender is not None:
    print(f'  性别门槛：{info.required_gender}')
  print(f'  示例：{_MATCH_EXAMPLE.replace("<判据ID>", info.criterion_id)}')
  return 0


def _match_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  if args.criterion is None and any(value is not None for value in (args.birth_time, args.gender, args.observation_scope)):
    parser.error(f'a criterion ID is required for evaluation; run {_PROG} match to list them')
  if args.criterion is None:
    return _criteria_listing()
  evaluation_inputs = (
    args.birth_time, args.gender, args.observation_scope, args.ganzhi_year, args.transit_entry, args.gz_month,
    args.solar_date, args.solar_moment, args.transit_kinds, args.longitude, args.precision, args.civil_timezone,
    args.knowledge_source, args.export_context_json,
  )
  if not (any(value is not None for value in evaluation_inputs) or args.include_reference_only):
    return _criterion_description(parser, args.criterion)
  missing = [flag for flag, value in (
    ('--birth-time', args.birth_time), ('--gender', args.gender), ('--observation-scope', args.observation_scope),
  ) if value is None]
  if missing:
    parser.error(f'missing {" and ".join(missing)}; example: {_MATCH_EXAMPLE}')
  args.match_context = args.criterion
  return _matching_main(parser, args)


def _subcommand_parsers(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
  tasks = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
  return dict(tasks.choices)


def _command_main(tokens: list[str]) -> int:
  parser = _command_parser()
  args = parser.parse_args(tokens)
  _fill_legacy_defaults(args)
  sub = _subcommand_parsers(parser)[args.command]
  if args.command == 'chart':
    return _chart_main(sub, args)
  if args.command == 'knowledge':
    return _knowledge_command(sub, args)
  return _match_command(sub, args)


def _zone_text(zone: tzinfo) -> str:
  if isinstance(zone, ZoneInfo):
    return zone.key
  offset = zone.utcoffset(None) or timedelta(0)
  seconds = int(offset.total_seconds())
  sign = '-' if seconds < 0 else '+'
  hours, rest = divmod(abs(seconds), 3600)
  minutes, secs = divmod(rest, 60)
  return f'{sign}{hours:02d}:{minutes:02d}' + (f':{secs:02d}' if secs else '')


def _option(flag: str, value: object) -> list[str]:
  if value is None or value is False:
    return []
  if value is True:
    return [flag]
  if isinstance(value, tzinfo):
    return [f'{flag}={_zone_text(value)}']
  if isinstance(value, (date, datetime)):
    return [flag, value.isoformat()]
  return [flag, str(value)]


def _replacement_commands(args: argparse.Namespace) -> list[str]:
  '''旧平铺调用对应的新命令；命盘加知识文本导出的旧组合要拆成两条。'''
  def command(*parts: list[str]) -> str:
    return ' '.join([_PROG] + [token if token.startswith('--') and '=' in token else shlex.quote(token)
                               for part in parts for token in part])

  filters = ('object_id', 'context_id', 'topic', 'source_id', 'viewpoint', 'applicability', 'time_scope')
  flag_of = {'object_id': '--object', 'context_id': '--context', 'source_id': '--source', 'time_scope': '--time-scope'}
  if args.match_context is not None:
    return [command(
      ['match', args.match_context],
      *(_option(flag, getattr(args, name)) for flag, name in (
        ('--birth-time', 'birth_time'), ('--gender', 'gender'), ('--observation-scope', 'observation_scope'),
        ('--ganzhi-year', 'ganzhi_year'), ('--transit-entry', 'transit_entry'), ('--gz-month', 'gz_month'),
        ('--solar-date', 'solar_date'), ('--solar-moment', 'solar_moment'), ('--transit-kinds', 'transit_kinds'),
        ('--precision', 'precision'), ('--longitude', 'longitude'), ('--civil-timezone', 'civil_timezone'),
        ('--include-reference-only', 'include_reference_only'), ('--knowledge-source', 'knowledge_source'),
        ('--export-context-json', 'export_context_json'),
      )),
    )]
  if args.query_knowledge or args.validate_knowledge or args.export_knowledge_json is not None:
    has_filter = any(getattr(args, name) is not None for name in filters)
    return [command(
      ['knowledge'],
      ['--all'] if args.query_knowledge and not has_filter else [],
      *(_option(flag_of.get(name, '--' + name.replace('_', '-')), getattr(args, name)) for name in filters),
      _option('--include-reference-only', args.include_reference_only),
      _option('--knowledge-source', args.knowledge_source),
      _option('--validate-knowledge', args.validate_knowledge),
      _option('--export-knowledge-json', args.export_knowledge_json),
    )]
  commands = [command(
    ['chart'],
    *(_option(flag, getattr(args, name)) for flag, name in (
      ('--birth-time', 'birth_time'), ('--gender', 'gender'), ('--seed', 'seed'), ('--count', 'count'),
      ('--precision', 'precision'), ('--longitude', 'longitude'), ('--civil-timezone', 'civil_timezone'),
      ('--include-reference-only', 'include_reference_only'), ('--show-sources', 'show_sources'),
      ('--output-dir', 'output_dir'), ('--export-chart-json', 'export_chart_json'),
    )),
  )]
  if args.export_knowledge_base:
    commands.append(command(
      ['knowledge', '--export-knowledge-base'],
      _option('--output-dir', args.output_dir),
      _option('--include-reference-only', args.include_reference_only),
    ))
  return commands


def _legacy_main(tokens: list[str]) -> int:
  parser = _legacy_parser()
  args = parser.parse_args(tokens)
  status = _legacy_dispatch(parser, args)
  # 校验失败经 parser.error 退出，到不了这里；只有成功的旧调用才给迁移提示。
  print('提示：不带任务名的旧写法将来会移除，请改用：' + ' && '.join(_replacement_commands(args)), file=sys.stderr)
  return status


def main(argv: list[str] | None = None) -> int:
  tokens = sys.argv[1:] if argv is None else list(argv)
  if (tokens and tokens[0] in _COMMANDS) or tokens in (['-h'], ['--help']):
    return _command_main(tokens)
  return _legacy_main(tokens)


if __name__ == '__main__':
  raise SystemExit(main())
