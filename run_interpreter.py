#!/usr/bin/env python3

import argparse
import sys
from random import Random, SystemRandom
import re
from collections.abc import Iterable
from datetime import date, datetime, tzinfo
from pathlib import Path
from typing import Final, get_args
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from run_demo import get_basic_info
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Zhu, Tiangan, Shishen, Dizhi
from bazi.knowledge import Applicability, DEFAULT_SOURCE_PATH, KnowledgeBase, object_id
from bazi.context_matching import (
  CriterionInfo, Observation, NatalObservation, LiunianObservation, TransitObservation, ScopeName,
  TransitCoordinate, YearCoordinate, MonthCoordinate, DateCoordinate, MomentCoordinate, TransitEntry,
  criteria, criterion, evaluate_context,
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

  bazi: Bazi = chart.bazi
  if bazi.longitude is None:
    s += f'出生时间：{bazi.solar_date}, {bazi.hour}:{bazi.minute}\n'
  else:
    s += f'真太阳时（分钟显示）：{bazi.solar_datetime.isoformat()}\n'
  s += f'性别：{bazi.gender}\n'

  s += '\n' + '-' * 60 + '\n'
  for label, pillar, trait, classification in zip(Zhu, bazi.pillars, chart.traits, chart.shishen, strict=True):
    stem_label = '日元' if classification.tiangan is None else str(classification.tiangan)
    s += f'{label}柱：天干{pillar.tiangan}（{trait.tiangan}，{stem_label}）。地支{pillar.dizhi}（{trait.dizhi}，{classification.dizhi}）。\n'

  day_master: Tiangan = bazi.day_master
  s += '\n' + '-' * 60 + '\n'
  s += f'日主：{day_master}，为{chart.traits.day.tiangan}。\n\n'
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


def _knowledge_text_paths(base: Path) -> list[Path]:
  return [
    *(base / 'knowledge_base' / 'tiangan' / f'{tg}.txt' for tg in Tiangan),
    *(base / 'knowledge_base' / 'shishen' / f'{ss}.txt' for ss in Shishen),
  ]


def save_knowledge_base(
  output_dir: Path = _DEFAULT_OUTPUT_DIR,
  *,
  knowledge: KnowledgeBase,
  include_reference_only: bool = False,
  show_sources: bool = False,
) -> None:
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


def _reject_source_overwrite(parser: argparse.ArgumentParser, targets: list[Path], knowledge_source: Path | None) -> None:
  for source in (DEFAULT_SOURCE_PATH, knowledge_source):
    if source is not None and any(_same_export_path(source, path) for path in targets):
      parser.error('Export must not overwrite the editing source')


def _knowledge_main(parser: argparse.ArgumentParser, args: argparse.Namespace, *, query: bool) -> int:
  filters = {
    'object_id': args.object_id, 'context_id': args.context_id, 'topic': args.topic,
    'source_id': args.source_id, 'viewpoint': args.viewpoint,
    'applicability': args.applicability, 'time_scope': args.time_scope,
  }
  try:
    knowledge = KnowledgeBase.load(args.knowledge_source)
    selection = knowledge.query(**filters, include_reference_only=args.include_reference_only) if query else None
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


def _relationship_observation(
  parser: argparse.ArgumentParser,
  args: argparse.Namespace,
  info: CriterionInfo,
) -> NatalObservation | TransitObservation:
  '''在 CLI 边界检查坐标缺项／多余项，再构造具体婚恋观察请求。'''
  values = {
    'ganzhi_year': args.ganzhi_year, 'ganzhi_month': args.gz_month,
    'solar_date': args.solar_date, 'solar_moment': args.solar_moment,
  }
  if args.transit_entry is None and any(value is not None for value in values.values()):
    parser.error('Transit coordinates require --transit-entry')
  kinds = _transit_kinds(parser, args.transit_kinds) if args.transit_kinds is not None else ()
  coordinate: TransitCoordinate | None = None
  if args.transit_entry is not None:
    required = info.transit_entries[args.transit_entry]
    for name in required:
      if values[name] is None:
        parser.error(f'Missing coordinate field for {args.transit_entry}: {name}')
    for name, value in values.items():
      if name not in required and value is not None:
        parser.error(f'Unexpected coordinate field for {args.transit_entry}: {name}')
    if args.transit_entry == 'at_year':
      coordinate = YearCoordinate(args.ganzhi_year)
    elif args.transit_entry == 'at_month':
      coordinate = MonthCoordinate(args.ganzhi_year, args.gz_month)
    elif args.transit_entry == 'at_date':
      coordinate = DateCoordinate(args.solar_date)
    else:
      coordinate = MomentCoordinate(args.solar_moment)
  if args.observation_scope == 'natal':
    if coordinate is not None or kinds:
      parser.error('Natal scope cannot include transit inputs')
    return NatalObservation()
  return TransitObservation(kinds, coordinate)


def _matching_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  try:
    info = criterion(args.criterion)
    if info.analysis_kind == 'context' and any((
      args.transit_entry is not None, args.gz_month is not None, args.solar_date is not None,
      args.solar_moment is not None, args.transit_kinds is not None,
    )):
      parser.error('Context criteria cannot combine transit entry, coordinate or kind inputs')
    if args.observation_scope not in info.scopes:
      parser.error(f'Unsupported value: {args.observation_scope}')
    observation: Observation
    if info.analysis_kind == 'context':
      if args.observation_scope == 'natal':
        if args.ganzhi_year is not None:
          parser.error('Natal scope cannot include a transit coordinate')
        observation = NatalObservation()
      else:
        observation = LiunianObservation(args.ganzhi_year)
    else:
      observation = _relationship_observation(parser, args, info)
    result = evaluate_context(
      _fixed_chart(args),
      criterion_id=args.criterion,
      observation=observation,
      knowledge=KnowledgeBase.load(args.knowledge_source),
      include_reference_only=args.include_reference_only,
    )
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  print(result.render())
  return 0


def _chart_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  count = 1 if args.count is None else args.count
  if count < 1:
    parser.error('--count must be positive')
  if (args.birth_time is None) != (args.gender is None):
    parser.error('--birth-time and --gender must be supplied together')
  if args.birth_time is not None and (args.seed is not None or count != 1):
    parser.error('--seed and multiple charts require random input')
  if args.birth_time is None and any(value is not None for value in (
    args.longitude, args.precision, args.civil_timezone,
  )):
    parser.error('Location and precision flags require fixed birth input')
  text_targets: list[Path] = []
  if args.output_dir is not None and (args.output_dir / 'interpretation_examples').is_dir():
    text_targets.extend((args.output_dir / 'interpretation_examples').glob('*.txt'))
  _reject_source_overwrite(parser, text_targets, None)

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
    if output is not None:
      try:
        _write_chart(text, output, i)
      except OSError as error:
        parser.error(str(error))

  return 0


_COMMANDS: Final[tuple[str, ...]] = ('chart', 'knowledge', 'match')
_PROG: Final[str] = 'python run_interpreter.py'

# `--list-values` 的取值与知识过滤选项同名；右侧是 `KnowledgeBase.filter_values` 的维度名。
_LIST_DIMENSIONS: Final[dict[str, str]] = {
  'object': 'object_id', 'context': 'context_id', 'source': 'source_id', 'topic': 'topic',
  'viewpoint': 'viewpoint', 'applicability': 'applicability', 'time-scope': 'time_scope',
}

_LONGITUDE_HELP: Final[str] = (
  '东经为正的角度，启用真太阳时；须配带时区的 --birth-time（如 "2000-01-01T12:00:00+08:00"）与 --precision hour 或 minute。'
)

# 判据目录里的查询坐标字段对应的命令行选项。
_COORDINATE_FLAGS: Final[dict[str, str]] = {
  'ganzhi_year': '--ganzhi-year', 'ganzhi_month': '--gz-month',
  'solar_date': '--solar-date', 'solar_moment': '--solar-moment',
}

_MATCH_EXAMPLE: Final[str] = (
  f'{_PROG} match <判据ID> --birth-time "2000-01-01 12:00" --gender female --observation-scope natal'
)


def _add_chart_arguments(parser: argparse.ArgumentParser) -> None:
  basic = parser.add_argument_group('出生信息（都不给则随机生成一张盘）')
  basic.add_argument('--birth-time', help='公历出生时刻，如 "2000-01-01 12:00"。')
  basic.add_argument('--gender', choices=('male', 'female'), help='male（男）或 female（女）；与 --birth-time 成对给出。')
  more = parser.add_argument_group('更多选项（都可省略）')
  more.add_argument('--seed', type=int, help='重放随机命盘的种子；随机命盘的种子会打印在第一行。')
  more.add_argument('--count', type=int, help='随机命盘数量，默认 1。')
  more.add_argument('--precision', choices=('day', 'hour', 'minute'), help='出生精度，默认 day；须配 --birth-time。')
  more.add_argument('--longitude', type=float, help=_LONGITUDE_HELP)
  more.add_argument('--civil-timezone', type=_civil_timezone, help='出生地时区（IANA 名如 Pacific/Kiritimati，或固定偏移如 +14:00；负偏移写成 --civil-timezone=-05:00）；须给经度。')
  more.add_argument('--include-reference-only', action='store_true', help='同时显示仅供参考的知识条目。')
  more.add_argument('--show-sources', action='store_true', help='显示条目 ID、署名与来源见证。')
  more.add_argument('--output-dir', type=Path, help='把展示的命盘另存为这个目录下的文本文件。')


def _add_knowledge_arguments(parser: argparse.ArgumentParser) -> None:
  common = parser.add_argument_group('查询（给任一条件就是查询；条件可以组合）')
  common.add_argument('--object', dest='object_id', help='讨论对象 ID，如 tiangan.ding。')
  common.add_argument('--topic', help='知识主题。')
  common.add_argument('--list-values', choices=tuple(_LIST_DIMENSIONS), help='列出某个条件的全部合法值；单独使用。')
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
  more.add_argument('--export-knowledge-base', action='store_true', help='把全部天干与十神说明各存成一个文本文件。')
  more.add_argument('--output-dir', type=Path, help='--export-knowledge-base 的目录，默认 output_data。')
  more.add_argument('--show-sources', action='store_true', help='--export-knowledge-base 的文本附带条目 ID、署名与来源见证。')


def _add_match_arguments(parser: argparse.ArgumentParser) -> None:
  parser.add_argument('criterion', nargs='?', metavar='判据ID', help='不给则列出全部判据；只给 ID 则说明该判据与所需输入；再给任何选项就是求值。')
  common = parser.add_argument_group('求值所需')
  common.add_argument('--birth-time', help='公历出生时刻，如 "2000-01-01 12:00"。')
  common.add_argument('--gender', choices=('male', 'female'), help='male（男）或 female（女）。')
  common.add_argument('--observation-scope', choices=get_args(ScopeName), help='判别范围，须显式选择；各判据支持的范围见判据说明。')
  more = parser.add_argument_group('更多选项（按判据说明所需给出，其余可省略）')
  more.add_argument('--ganzhi-year', type=int, help='干支年坐标，写公历年份数字，如 2024。')
  more.add_argument('--transit-entry', choices=get_args(TransitEntry), help='岁运查询入口（婚恋判据）。')
  more.add_argument('--gz-month', type=_gz_month, help='干支月坐标（中文支名，如 午），配 at_month 入口与 --ganzhi-year。')
  more.add_argument('--solar-date', type=_solar_date, help='东八区公历日期坐标，如 2024-04-10，配 at_date 入口。')
  more.add_argument('--solar-moment', type=_solar_moment, help='东八区时刻坐标，如 2024-04-10T12:00:00，配 at_moment 入口；day 精度的命盘判别为 UNKNOWN。')
  more.add_argument('--transit-kinds', help='逗号分隔的岁运种类（xiaoyun,dayun,liunian,liuyue,liuri）。')
  more.add_argument('--precision', choices=('day', 'hour', 'minute'), help='出生精度，默认 day。')
  more.add_argument('--longitude', type=float, help=_LONGITUDE_HELP)
  more.add_argument('--civil-timezone', type=_civil_timezone, help='出生地时区；须给经度。')
  more.add_argument('--include-reference-only', action='store_true', help='同时显示仅供参考的条目与条件参考。')
  more.add_argument('--knowledge-source', type=Path, help='改用你自己的知识 JSON。')


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
  if args.all and any(value is not None for value in filters):
    parser.error('--all cannot be combined with query conditions')
  for flag, given in (('--output-dir', args.output_dir is not None), ('--show-sources', args.show_sources)):
    if given and not args.export_knowledge_base:
      parser.error(f'{flag} only applies with --export-knowledge-base')
  if not any((query, args.list_values, args.validate_knowledge, args.export_knowledge_base)):
    return _knowledge_overview(parser, args)

  if args.list_values is not None:
    if query or args.validate_knowledge or args.export_knowledge_base:
      parser.error('--list-values only lists values; use it without queries, validation or exports')
    try:
      for value in KnowledgeBase.load(args.knowledge_source).filter_values(_LIST_DIMENSIONS[args.list_values]):
        print(value)
    except (OSError, TypeError, ValueError) as error:
      parser.error(str(error))
  base = args.output_dir if args.output_dir is not None else _DEFAULT_OUTPUT_DIR
  if args.export_knowledge_base:
    text_paths = _knowledge_text_paths(base)
    _reject_source_overwrite(parser, text_paths, args.knowledge_source)
  if query or args.validate_knowledge:
    _knowledge_main(parser, args, query=query)
  if args.export_knowledge_base:
    try:
      knowledge = KnowledgeBase.load(args.knowledge_source)
    except (OSError, TypeError, ValueError) as error:
      parser.error(str(error))
    try:
      save_knowledge_base(
        base,
        include_reference_only=args.include_reference_only,
        show_sources=args.show_sources,
        knowledge=knowledge,
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
      needs = (
        '--transit-entry 及其坐标（见下）、--transit-kinds' if inputs == ('coordinate', 'kinds')
        else '、'.join(_COORDINATE_FLAGS[name] for name in inputs)
      )
      print(f'  --observation-scope {scope} 还需要：{needs}')
  for entry, fields in info.transit_entries.items():
    flags = ' '.join(_COORDINATE_FLAGS[field] for field in fields)
    print(f'  --transit-entry {entry}：{flags}')
  if info.required_gender is not None:
    print(f'  性别门槛：{info.required_gender.value}（--gender {info.required_gender}）')
  print(f'  示例：{_MATCH_EXAMPLE.replace("<判据ID>", info.criterion_id)}')
  return 0


def _match_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  evaluation_inputs = (
    args.birth_time, args.gender, args.observation_scope, args.ganzhi_year, args.transit_entry, args.gz_month,
    args.solar_date, args.solar_moment, args.transit_kinds, args.longitude, args.precision, args.civil_timezone,
    args.knowledge_source,
  )
  evaluating = any(value is not None for value in evaluation_inputs) or args.include_reference_only
  if args.criterion is None:
    if evaluating:
      parser.error(f'a criterion ID is required for evaluation; run {_PROG} match to list them')
    return _criteria_listing()
  if not evaluating:
    return _criterion_description(parser, args.criterion)
  missing = [flag for flag, value in (
    ('--birth-time', args.birth_time), ('--gender', args.gender), ('--observation-scope', args.observation_scope),
  ) if value is None]
  if missing:
    parser.error(f'missing {" and ".join(missing)}; example: {_MATCH_EXAMPLE}')
  return _matching_main(parser, args)


def _subcommand_parsers(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
  tasks = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
  return dict(tasks.choices)


def _command_main(tokens: list[str]) -> int:
  parser = _command_parser()
  if not tokens:
    parser.print_help()
    return 0
  if tokens[0].startswith('-') and tokens not in (['-h'], ['--help']):
    parser.error(
      f'不带任务名的旧写法已在 v2.3.0 移除。请改用 {_PROG} chart [选项]、'
      f'{_PROG} knowledge [查询条件或选项]、{_PROG} match <判据ID> [选项]；'
      f'用 {_PROG} --help 查看示例。'
    )
  args = parser.parse_args(tokens)
  sub = _subcommand_parsers(parser)[args.command]
  if args.command == 'chart':
    return _chart_main(sub, args)
  if args.command == 'knowledge':
    return _knowledge_command(sub, args)
  return _match_command(sub, args)


def main(argv: list[str] | None = None) -> int:
  tokens = sys.argv[1:] if argv is None else list(argv)
  return _command_main(tokens)


if __name__ == '__main__':
  raise SystemExit(main())
