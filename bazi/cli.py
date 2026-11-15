# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''安装版 bazi 命令：展示命盘与关系报告、查询知识、判别前提。'''

import argparse
import sys
from random import Random, SystemRandom
import re
from collections.abc import Mapping
from datetime import date, datetime, tzinfo
from pathlib import Path
from typing import Final, cast, get_args
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .bazi import Bazi
from .bazi_chart import BaziChart
from .chart_text import TextStyle, basic_text, transit_text
from .defines import Zhu, Tiangan, Shishen, Dizhi, Wuxing, Ganzhi
from .knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase
from .context_matching import (
  CriterionInfo, Observation, NatalObservation, LiunianObservation, TransitObservation, ScopeName,
  TransitCoordinate, YearCoordinate, MonthCoordinate, DateCoordinate, MomentCoordinate, TransitEntry,
  criteria, criterion, evaluate_context,
)
from .school import BaziConfig
from .transit_chart import TransitChart
from .transits import TransitKind
from .utils.bazi_utils import traits, shishen
from .analyzer.relationship import (
  RelationshipAnalyzer, ShenshaAnalysis, AtBirthShenshaAnalysis, SHENSHA_LABELS, WHOLE_PILLAR_SHENSHA_LABELS,
  KongwangResult,
)


_ANSI_ESCAPE: Final[re.Pattern[str]] = re.compile(r'\x1b\[[0-9;]*m')


def _colored_str(s: Tiangan | Dizhi | Ganzhi) -> str:
  color_mapping_table: dict[Wuxing, str] = {
    Wuxing.火: '\x1b[31m',
    Wuxing.木: '\x1b[32m',
    Wuxing.金: '\x1b[33m',
    Wuxing.水: '\x1b[34m',
    Wuxing.土: '\x1b[35m',
  }

  if isinstance(s, Ganzhi):
    return _colored_str(s.tiangan) + _colored_str(s.dizhi)
  else:
    return color_mapping_table[traits(s).wuxing] + str(s) + '\x1b[0m'


def _highlighted_day_master(label: str) -> str:
  return '\x1b[104m\x1b[30m' + label + '\x1b[0m'


_TERMINAL_STYLE: Final[TextStyle] = TextStyle(glyph=_colored_str, day_master_mark=_highlighted_day_master)


def _get_basic_info(chart: BaziChart) -> str:
  return basic_text(chart, style=_TERMINAL_STYLE)


def _get_transit_info(chart: BaziChart) -> str:
  return transit_text(chart, style=_TERMINAL_STYLE)


def _named_shensha(shensha: ShenshaAnalysis) -> tuple[tuple[str, frozenset[Dizhi]], ...]:
  # TypedDict 用字面键索引；展示按 SHENSHA_LABELS 注册序读取，不包含原局的两个整柱神煞。
  dizhis = cast(Mapping[str, frozenset[Dizhi]], shensha)
  return tuple((label, dizhis[name]) for name, label in SHENSHA_LABELS.items())


def _shensha_strs(shensha: ShenshaAnalysis) -> list[str]:
  return [
    f'{label}：{", ".join(map(_colored_str, sorted(dz_fs, key=lambda dz: dz.index)))}'
    for label, dz_fs in _named_shensha(shensha)
    if dz_fs
  ]


def _at_birth_shensha_strs(shensha: AtBirthShenshaAnalysis) -> list[str]:
  result = _shensha_strs(shensha)
  whole_pillars = cast(Mapping[str, Ganzhi | None], shensha)
  for name, label in WHOLE_PILLAR_SHENSHA_LABELS.items():
    if (ganzhi := whole_pillars[name]) is not None:
      result.append(f'{label}：{_colored_str(ganzhi)}')
  return result


def _no_shensha_str(shensha: AtBirthShenshaAnalysis) -> str:
  labels = tuple(label for label, _ in _named_shensha(shensha))
  return f'原局无{"、".join(labels + tuple(WHOLE_PILLAR_SHENSHA_LABELS.values()))}'


def _kongwang_strs(results: tuple[KongwangResult, ...]) -> list[str]:
  '''逐锚展示旬空二支与具体命中；没有命中时仍列二支。'''
  lines = []
  for result in results:
    absent = ''.join(map(str, sorted(result.xunkong, key=lambda dz: dz.index)))
    hit_texts: list[str] = []
    for hit in result.hits:
      position = hit.position
      label = f'{position}柱' if isinstance(position, Zhu) else position.value
      hit_texts.append(f'{label} {hit.ganzhi}')
    lines.append(f'{result.anchor}柱 {result.ganzhi} → 旬空{absent}；命中：{"、".join(hit_texts) or "无"}')
  return lines


def _relationship_text(chart: BaziChart) -> str:
  analyzer = RelationshipAnalyzer(chart)
  house = chart.house_of_relationship
  stars = chart.relationship_stars
  star_strs = [_colored_str(stars.tiangan), *map(_colored_str, stars.dizhi)]
  lines = [f'夫妻宫：{_colored_str(house)}', f'配偶星：{", ".join(star_strs)}']

  at_birth_shensha = analyzer.at_birth.shensha
  shensha_str_list = _at_birth_shensha_strs(at_birth_shensha)
  if len(shensha_str_list) == 0:
    lines.append(_no_shensha_str(at_birth_shensha))
  else:
    lines.extend(('原局神煞：', *shensha_str_list))
  lines.extend(('六甲旬空依据：', *_kongwang_strs(analyzer.at_birth.kongwang)))

  transits_analysis = analyzer.transits
  transit_chart = TransitChart(chart)
  start_gz_year = chart.bazi.ganzhi_year + 20
  lines.append(f'流年神煞（{start_gz_year} 起十年）：')
  for gz_year in range(start_gz_year, start_gz_year + 10):
    year_transits = transit_chart.at_year(gz_year)
    assert year_transits is not None # 查询年份晚于出生干支年。
    year_strs = _shensha_strs(transits_analysis.shensha(
      year_transits.select(TransitKind.LIUNIAN)
    ))
    if len(year_strs) == 0:
      lines.append(f'{gz_year}：无')
    else:
      lines.extend((f'{gz_year}：', *(f'  {s}' for s in year_strs)))
    lines.extend(f'  {s}' for s in _kongwang_strs(transits_analysis.kongwang(
      year_transits.select(TransitKind.LIUNIAN)
    )))
  return '\n'.join(lines)


def _chart_knowledge(
  chart: BaziChart,
  knowledge: KnowledgeBase,
  *,
  show_sources: bool = False,
) -> str:
  observed = (
    {pair.tiangan for pair in chart.shishen if pair.tiangan is not None} |
    {shishen(chart.bazi.day_master, tg) for hidden in chart.hidden_tiangan for tg in hidden}
  )
  subjects: tuple[Tiangan | Shishen, ...] = (
    chart.bazi.day_master,
    *(ss for ss in Shishen if ss in observed),
  )
  lines = ['相关知识（按日主、十神分组；命盘适用性未判断）：']
  seen: set[str] = set()
  for subject in subjects:
    lines.append(f'\n【{"日主" if isinstance(subject, Tiangan) else "十神"}：{subject}】')
    try:
      entries = knowledge.query(subject)
    except ValueError as error:
      lines.append(f'无法查阅：{error}')
      continue
    for entry in entries:
      if entry.claim_id not in seen:
        seen.add(entry.claim_id)
        lines.extend((knowledge.render(entry, show_sources=show_sources), ''))
    if not entries:
      lines.append('无相关条目。')
  return '\n'.join(lines)


def _reject_source_overwrite(parser: argparse.ArgumentParser, target: Path, knowledge_source: Path | None) -> None:
  for source in (DEFAULT_SOURCE_PATH, knowledge_source):
    if source is not None and source.resolve() == target.resolve():
      parser.error('Export must not overwrite the editing source')


def _knowledge_main(parser: argparse.ArgumentParser, args: argparse.Namespace, *, query: bool) -> int:
  filters = {
    'subject': args.subject if args.subject is not None else args.object_id, 'topic': args.topic,
    'source_id': args.source_id, 'viewpoint': args.viewpoint,
  }
  try:
    knowledge = KnowledgeBase.load(args.knowledge_source)
    selection = (
      knowledge.search(args.search, **filters) if args.search is not None else knowledge.query(**filters)
    ) if query else None
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  if args.validate_knowledge:
    print(f'校验通过：{len(knowledge.entries)} 条目，{len(knowledge.sources)} 来源。')
  if selection is not None:
    for entry in selection:
      print(knowledge.render(entry, show_sources=args.show_sources))
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
    BaziConfig.from_values(precision=args.precision if args.precision is not None else 'day'),
    longitude=args.longitude,
    civil_timezone=args.civil_timezone,
  ))


def _ganzhi_month(value: str) -> Dizhi:
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
  '''解析逗号分隔的种类值；查重，拒绝未知名与空项。'''
  kinds: list[TransitKind] = []
  for item in value.split(','):
    try:
      kinds.append(TransitKind(item))
    except ValueError:
      parser.error(f'Unsupported transit kind: {item}')
  if len(set(kinds)) != len(kinds):
    parser.error(f'Duplicate transit kinds: {value}')
  return tuple(kinds)


def _relationship_observation(
  parser: argparse.ArgumentParser,
  args: argparse.Namespace,
  info: CriterionInfo,
) -> NatalObservation | TransitObservation:
  '''在 CLI 边界检查坐标缺项／多余项，再构造具体婚恋观察请求。'''
  values = {
    'ganzhi_year': args.ganzhi_year, 'ganzhi_month': args.ganzhi_month,
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
      coordinate = MonthCoordinate(args.ganzhi_year, args.ganzhi_month)
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
      args.transit_entry is not None, args.ganzhi_month is not None, args.solar_date is not None,
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
    )
    knowledge = KnowledgeBase.load(args.knowledge_source) if args.knowledge else None
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  text = result.render()
  if knowledge is not None:
    for claim_id in result.reference_ids:
      entry = knowledge.entries.get(claim_id)
      text += '\n\n' + (
        f'{claim_id}：知识库未收录' if entry is None else knowledge.render(entry, show_sources=args.show_sources)
      )
  print(text)
  return 0


def _chart_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  if (args.birth_time is None) != (args.gender is None):
    parser.error('--birth-time and --gender must be supplied together')
  if args.birth_time is not None and args.seed is not None:
    parser.error('--seed requires random input')
  if args.birth_time is None and any(value is not None for value in (
    args.longitude, args.precision, args.civil_timezone,
  )):
    parser.error('Location and precision flags require fixed birth input')
  _check_reading_options(parser, args)
  try:
    if args.output is not None:
      _reject_source_overwrite(parser, args.output, args.knowledge_source)
    text = ''
    if args.birth_time is not None:
      chart = _fixed_chart(args)
    else:
      seed = SystemRandom().getrandbits(64) if args.seed is None else args.seed
      chart = BaziChart(Bazi.random(rng=Random(seed)))
      text = f'random seed: {seed}\n'
    knowledge_text = ''
    if args.knowledge:
      knowledge_text = '\n' + _chart_knowledge(
        chart,
        KnowledgeBase.load(args.knowledge_source),
        show_sources=args.show_sources,
      )
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  text += _get_basic_info(chart)
  if args.transits:
    text += '\n' + _get_transit_info(chart)
  if args.relationship:
    text += '\n' + _relationship_text(chart)
  text += knowledge_text
  if args.output is not None:
    try:
      args.output.write_text(_ANSI_ESCAPE.sub('', text) + '\n', encoding='utf-8')
    except OSError as error:
      parser.error(str(error))
  print(text)
  return 0


_PROG: Final[str] = 'bazi'

# `--list-values` 的取值与知识过滤选项同名；右侧是 `KnowledgeBase.filter_values` 的维度名。
_LIST_DIMENSIONS: Final[dict[str, str]] = {
  'object': 'object_id', 'source': 'source_id', 'topic': 'topic', 'viewpoint': 'viewpoint',
}

_LONGITUDE_HELP: Final[str] = (
  '东经为正的角度，启用真太阳时；须配带时区的 --birth-time（如 "2000-01-01T12:00:00+08:00"）与 --precision hour 或 minute。'
)

# 判据目录里的查询坐标字段对应的命令行选项。
_COORDINATE_FLAGS: Final[dict[str, str]] = {
  'ganzhi_year': '--ganzhi-year', 'ganzhi_month': '--ganzhi-month',
  'solar_date': '--solar-date', 'solar_moment': '--solar-moment',
}

_MATCH_EXAMPLE: Final[str] = (
  f'{_PROG} match <判据ID> --birth-time "2000-01-01 12:00" --gender female --observation-scope natal'
)


def _add_reading_arguments(parser: argparse._ActionsContainer) -> None:
  parser.add_argument('--knowledge', action='store_true', help='显式阅读相关知识正文。')
  parser.add_argument('--knowledge-source', type=Path, help='--knowledge 使用的自定义知识 JSON。')
  parser.add_argument('--show-sources', action='store_true', help='--knowledge 展开来源定位与引文。')


def _check_reading_options(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
  if not args.knowledge and (args.knowledge_source is not None or args.show_sources):
    parser.error('--knowledge-source and --show-sources require --knowledge')


def _add_chart_arguments(parser: argparse.ArgumentParser) -> None:
  basic = parser.add_argument_group('出生信息（都不给则随机生成一张盘）')
  basic.add_argument('--birth-time', help='公历出生时刻；默认按东八区钟填写，不换算时区。')
  basic.add_argument('--gender', choices=('男', '女', 'male', 'female'), help='与 --birth-time 成对给出。')
  more = parser.add_argument_group('更多选项（都可省略）')
  more.add_argument('--seed', type=int, help='重放随机命盘的种子；随机命盘的种子会打印在第一行。')
  more.add_argument('--precision', help='出生精度：day（日）、hour（时）、minute（分），默认 day；须配 --birth-time。')
  more.add_argument('--longitude', type=float, help=_LONGITUDE_HELP)
  more.add_argument('--civil-timezone', type=_civil_timezone, help='出生地时区（IANA 名如 Pacific/Kiritimati，或固定偏移如 +14:00；负偏移写成 --civil-timezone=-05:00）；须给经度。')
  more.add_argument('--transits', action='store_true', help='追加大运、小运和流年文本。')
  more.add_argument('--relationship', action='store_true', help='追加婚恋结构与十年流年报告。')
  _add_reading_arguments(more)
  more.add_argument('--output', type=Path, help='把本次完整输出保存为不带颜色码的 UTF-8 文本。')


def _add_knowledge_arguments(parser: argparse.ArgumentParser) -> None:
  parser.add_argument('subject', nargs='?', metavar='对象', help='中文名称或对象 ID，如 丁、文昌、tiangan.ding。')
  common = parser.add_argument_group('查询（给任一条件就是查询；条件可以组合）')
  common.add_argument('--object', dest='object_id', help='讨论对象名称或 ID；与位置参数二选一。')
  common.add_argument('--search', help='按实际文字搜索，不推断同义词。')
  common.add_argument('--topic', help='知识主题。')
  common.add_argument('--list-values', choices=tuple(_LIST_DIMENSIONS), help='列出某个条件的全部合法值；单独使用。')
  common.add_argument('--all', action='store_true', help='列出全部条目。')
  more = parser.add_argument_group('更多选项（都可省略）')
  more.add_argument('--source', dest='source_id', help='来源 ID。')
  more.add_argument('--viewpoint', help='读法。')
  more.add_argument('--knowledge-source', type=Path, help='改用你自己的知识 JSON。')
  more.add_argument('--validate-knowledge', action='store_true', help='校验完整知识源。')
  more.add_argument('--show-sources', action='store_true', help='展开来源定位与引文。')


def _add_match_arguments(parser: argparse.ArgumentParser) -> None:
  parser.add_argument('criterion', nargs='?', metavar='判据ID', help='不给则列出全部判据；只给 ID 则说明该判据与所需输入；再给任何选项就是求值。')
  common = parser.add_argument_group('求值所需')
  common.add_argument('--birth-time', help='公历出生时刻；默认按东八区钟填写，不换算时区。')
  common.add_argument('--gender', choices=('男', '女', 'male', 'female'), help='命盘性别。')
  common.add_argument('--observation-scope', choices=get_args(ScopeName), help='判别范围，须显式选择；各判据支持的范围见判据说明。')
  more = parser.add_argument_group('更多选项（按判据说明所需给出，其余可省略）')
  more.add_argument('--ganzhi-year', type=int, help='干支年坐标，写公历年份数字，如 2024。')
  more.add_argument('--transit-entry', choices=get_args(TransitEntry), help='岁运查询入口（婚恋判据）。')
  more.add_argument('--ganzhi-month', type=_ganzhi_month, help='干支月坐标（中文支名，如 午），配 at_month 入口与 --ganzhi-year。')
  more.add_argument('--solar-date', type=_solar_date, help='东八区公历日期坐标，如 2024-04-10，配 at_date 入口。')
  more.add_argument('--solar-moment', type=_solar_moment, help='东八区时刻坐标，如 2024-04-10T12:00:00，配 at_moment 入口；day 精度的命盘判别为 UNKNOWN。')
  more.add_argument('--transit-kinds', help='逗号分隔的岁运种类（xiaoyun,dayun,liunian,liuyue,liuri）。')
  more.add_argument('--precision', help='出生精度：day（日）、hour（时）、minute（分），默认 day。')
  more.add_argument('--longitude', type=float, help=_LONGITUDE_HELP)
  more.add_argument('--civil-timezone', type=_civil_timezone, help='出生地时区；须给经度。')
  _add_reading_arguments(more)


def _command_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    prog=_PROG,
    description='展示命盘、查询解释知识、判别判据前提。先选一个任务，再用「任务 --help」看它的选项。',
    epilog=(
      '示例：\n'
      f'  {_PROG} chart --birth-time "2000-01-01 12:00" --gender male\n'
      f'  {_PROG} knowledge                              知识库概览\n'
      f'  {_PROG} knowledge 丁\n'
      f'  {_PROG} match                                  列出全部判据\n'
      f'  {_PROG} match <判据ID>                         判据说明与所需输入\n'
      f'  {_PROG} chart --seed 236 --transits --relationship\n'
      '文档与版本：https://0xf3cd.github.io/bazi/\n'
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )
  tasks = parser.add_subparsers(dest='command', metavar='<任务>', required=True)
  for name, summary, usage, add in (
    ('chart', '展示命盘；不给出生信息就随机生成', '[--birth-time 时刻 --gender male|female] [选项]', _add_chart_arguments),
    ('knowledge', '查询、校验解释知识，不需要命盘', '[对象] [查询条件] [选项]', _add_knowledge_arguments),
    ('match', '查看判据，或对给定命盘判别前提', '[判据ID] [选项]', _add_match_arguments),
  ):
    add(tasks.add_parser(name, help=summary, description=summary, usage=f'{_PROG} {name} {usage}'))
  return parser


def _knowledge_overview(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  try:
    knowledge = KnowledgeBase.load(args.knowledge_source)
    sizes = {flag: len(knowledge.filter_values(dimension)) for flag, dimension in _LIST_DIMENSIONS.items()}
  except (OSError, TypeError, ValueError) as error:
    parser.error(str(error))
  print(f'知识库：{len(knowledge.entries)} 条目，{len(knowledge.objects)} 对象，{len(knowledge.sources)} 来源。')
  print('可用来筛选的条件（--list-values 条件名 查看全部合法值）：')
  for flag, size in sizes.items():
    print(f'  --{flag}：{size} 个值')
  print('示例：')
  print(f'  {_PROG} knowledge 丁')
  print(f'  {_PROG} knowledge --search 枭印')
  print(f'  {_PROG} knowledge --list-values topic')
  print(f'  {_PROG} knowledge --all')
  return 0


def _knowledge_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
  if args.subject is not None and args.object_id is not None:
    parser.error('Use either the object argument or --object')
  filters = (args.subject, args.object_id, args.topic, args.source_id, args.viewpoint, args.search)
  query = args.all or any(value is not None for value in filters)
  if args.all and any(value is not None for value in filters):
    parser.error('--all cannot be combined with query conditions')
  if args.show_sources and not query:
    parser.error('--show-sources requires a query')
  if not any((query, args.list_values, args.validate_knowledge)):
    return _knowledge_overview(parser, args)

  if args.list_values is not None:
    if query or args.validate_knowledge:
      parser.error('--list-values only lists values; use it without queries or validation')
    try:
      for value in KnowledgeBase.load(args.knowledge_source).filter_values(_LIST_DIMENSIONS[args.list_values]):
        print(value)
    except (OSError, TypeError, ValueError) as error:
      parser.error(str(error))
    return 0
  return _knowledge_main(parser, args, query=query)


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
    args.birth_time, args.gender, args.observation_scope, args.ganzhi_year, args.transit_entry, args.ganzhi_month,
    args.solar_date, args.solar_moment, args.transit_kinds, args.longitude, args.precision, args.civil_timezone,
    args.knowledge_source,
  )
  evaluating = any(value is not None for value in evaluation_inputs) or args.knowledge or args.show_sources
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
  _check_reading_options(parser, args)
  return _matching_main(parser, args)


def _subcommand_parsers(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
  tasks = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
  return dict(tasks.choices)


def _command_main(tokens: list[str]) -> int:
  parser = _command_parser()
  if not tokens:
    parser.print_help()
    return 0
  args = parser.parse_args(tokens)
  sub = _subcommand_parsers(parser)[args.command]
  if args.command == 'chart':
    return _chart_main(sub, args)
  if args.command == 'knowledge':
    return _knowledge_command(sub, args)
  return _match_command(sub, args)


def main(argv: list[str] | None = None) -> int:
  '''执行一个命令行任务；未给参数时只显示帮助。

  Args:
  - argv: (list[str] | None) 不含程序名的参数；None 表示读取 sys.argv[1:]。

  Return: (int) 成功时为 0；参数错误由 argparse 以退出码 2 结束。

  Note:
  - TypeError: argv 不是列表或包含非字符串成员。
  '''
  if argv is not None:
    if not isinstance(argv, list):
      raise TypeError(f'Expected list, got {type(argv)}')
    for token in argv:
      if not isinstance(token, str):
        raise TypeError(f'Expected str, got {type(token)}')
  tokens = sys.argv[1:] if argv is None else list(argv)
  return _command_main(tokens)
