#!/usr/bin/env python3

import os
import sys
import io
import random
import shutil
import psutil
import tempfile
import platform
import argparse
import subprocess
import unicodedata
from importlib.util import find_spec

import operator
import functools
import itertools

from pathlib import Path, PurePath
from datetime import datetime
from typing import Final, Any
from collections.abc import Callable, Generator, Iterator

import emoji
import pytest
import coverage
import colorama


# 使用 UTF-8 输出，支持 cp1252 等 Windows 控制台显示 emoji；非标准 stdout 写入器保持原样。
if isinstance(sys.stdout, io.TextIOWrapper):
  sys.stdout.reconfigure(encoding='utf-8')

# region: Arg Parsing

# 解析命令行参数。
argparser = argparse.ArgumentParser()

argparser.add_argument('-a', '--all', action='store_true', 
                       help='运行全部测试、覆盖率、lint、类型检查、python -O 公开输入契约冒烟、文档构建检查及发行包和安装命令检查。')

# 测试选择。
argparser.add_argument('-nt', '--no-test', action='store_true', help='跳过测试与覆盖率。')
argparser.add_argument('-s', '--slow-test', action='store_true', help='包含 slow 测试。')
argparser.add_argument('-hko', '--hkodata-test', action='store_true', help='包含 hkodata 测试。')
argparser.add_argument('-k', '--expression', type=str, help='筛选 pytest 测试的表达式。', default=None)
argparser.add_argument('-v', '--verbose', action='store_true', help='显示测试详细输出。')

# 覆盖率。
argparser.add_argument('-c', '--coverage', action='store_true', help='生成覆盖率报告。')
argparser.add_argument('-cr', '--coverage-rate', type=float, help='必须达到的最低覆盖率，默认 %(default)s。', default=100.0)

# lint 与类型检查。
argparser.add_argument('-r', '-ruff', '--ruff', action='store_true', help='运行 ruff check。')
argparser.add_argument('-m', '-mypy', '--mypy', action='store_true', help='运行静态类型检查。')

# python -O 公开输入契约冒烟。
argparser.add_argument('-osmoke', '--o-smoke', action='store_true',
                       help='用 python -O 运行公开输入契约冒烟脚本 tests/o_smoke.py。')

argparser.add_argument('-docs', '--docs', action='store_true', help='在仓外临时目录严格构建文档并执行示例与对账检查。')
argparser.add_argument('--runtime-only', action='store_true', help='只检查运行时与非文档工具，不收集文档工具测试或构建文档；可用于 Python 3.11／3.12。')
argparser.add_argument('-pkg', '--package', action='store_true', help='构建并检查隔离的 wheel 与 sdist 安装。')
argparser.add_argument('--package-output-dir', type=Path, help='与 -pkg 或 -a 一起使用，在此仓外目录保留验证后的工件对。')
argparser.add_argument('--environment-report', type=Path, help='与工件保全一起使用，在此仓外新文件记录实际构建与验证环境。')
argparser.add_argument('--outer-installer-report', type=Path, help='导出环境时提供 release 步骤的三次外层 pip 版本观察。')

# 保留 -docs，但拒绝已退役的 -d 被当成它的缩写。
if '-d' in sys.argv[1:]:
  argparser.error('unrecognized arguments: -d')
args = argparser.parse_args()
if args.runtime_only and args.docs:
  argparser.error('--runtime-only cannot be combined with --docs')
if ((args.environment_report is None) != (args.outer_installer_report is None)
    or (args.environment_report is not None and (args.package_output_dir is None or not (args.package or args.all)))):
  argparser.error('Environment export requires -pkg or -a, --package-output-dir, --environment-report and --outer-installer-report')

all_the_way: Final[bool] = args.all

skip_test: Final[bool] = args.no_test and not all_the_way
run_slow_test: Final[bool] = args.slow_test or all_the_way
run_hko_test: Final[bool] = args.hkodata_test or all_the_way
expression: Final[str | None] = args.expression if not all_the_way else None # --all/-a 优先于 --expression/-k。
verbose: Final[bool] = args.verbose

do_cov: Final[bool] = args.coverage or all_the_way
minimum_cov_rate: Final[float] = args.coverage_rate
do_ruff: Final[bool] = args.ruff or all_the_way
do_mypy: Final[bool] = args.mypy or all_the_way

do_osmoke: Final[bool] = args.o_smoke or all_the_way
runtime_only: Final[bool] = args.runtime_only
do_docs: Final[bool] = (args.docs or all_the_way) and not runtime_only
do_package: Final[bool] = args.package or all_the_way

ROOT: Final[Path] = Path(__file__).resolve().parent
DOC_TOOL_PATHS: Final[tuple[Path, ...]] = (
  Path('docs'), Path('tests/docs'), Path('run_docs.py'), Path('run_doc_checks.py'),
)
DOC_MODULES: Final[tuple[str, ...]] = ('sphinx', 'myst_parser', 'docutils', 'markdown_it')


def is_doc_tool(path: PurePath) -> bool:
  '''按相对路径识别文档工具，不将其他包内同名目录当作文档源。'''
  return any(path.parts[:len(unit.parts)] == unit.parts for unit in DOC_TOOL_PATHS)


def mypy_targets(root: Path, only_runtime: bool) -> tuple[Path, ...]:
  '''完整检查保留整树发现；运行时检查显式排除文档工具及其测试。'''
  if not only_runtime:
    return (root,)
  files = (*root.glob('*.py'), *(root / 'tests').rglob('*.py'))
  return (root / 'bazi', *(path for path in sorted(files) if not is_doc_tool(path.relative_to(root))))


def check_doc_environment() -> None:
  '''完整文档任务在启动任何子任务之前核对构建环境。'''
  if sys.version_info >= (3, 13):
    missing = tuple(name for name in DOC_MODULES if find_spec(name) is None)
    if missing:
      argparser.error(f'Missing documentation dependencies: {", ".join(missing)}; install docs/requirements.txt or select --runtime-only')
  else:
    argparser.error('Documentation checks require Python 3.13 or later; create a Python 3.13+ environment with docs/requirements.txt, or select --runtime-only')

term_width: Final[int] = shutil.get_terminal_size().columns
_emoji_rng: Final[random.Random] = random.Random()


# region: Formats and Prints

animal1: Final[str] = '🦑🦀🦞🦐🦪'
animal2: Final[str] = '🐃🐍🐊🦇🦕🦅🦖🦥🦦🐫🐅🦔'
food: Final[str] = '🍋🥭🥒🍉🥝🥑🍆🌽🍑🫐🍍🍇🥬🫚🫛🥩🥓🌮🍱🍢'
astrology: Final[str] = '🌙🔮✨💫⭐🌟🌔🌓🌗🌘🌎🌏🪐🛰️🛸👾👽🗿'
weirdo: Final[str] = '🧊📸🧯🔒🪑🌈💖💞💕💗💓🪩🔥🔦📟💣💥👬🔗🖇️⛓️🫗💅'
desert_and_tree: Final[str] = '🌵🏜️🌲🏕️🌴🏝️'

def random_emoji() -> str:
  while True:
    c: str = _emoji_rng.choice(f'{animal1}{animal2}{food}{astrology}{weirdo}{desert_and_tree}')
    if emoji.is_emoji(c):
      return c

def emoji_pair_generator() -> Generator[str, None, None]:
  def random_ep(s: str) -> str:
    filtered: str = ''.join(filter(emoji.is_emoji, s))
    return ''.join(_emoji_rng.sample(filtered, k=2))
  
  emoji_pairs: list[str] = [
    '💖💅', '🌙✨', '🌵🏜️', '🔗🌐', '💡🧠',
    '📝🕵️', '🪐🛰️', '🌲🏕️', '🗻🌋', '🎃🕯️',
    *[random_ep(animal1) for _ in range(1)],
    *[random_ep(animal2) for _ in range(2)],
    *[random_ep(food) for _ in range(2)],
    *[random_ep(astrology) for _ in range(4)],
    *[random_ep(weirdo) for _ in range(4)],
    *[random_ep(desert_and_tree) for _ in range(2)],
  ]

  emoji_pairs = list(set(emoji_pairs))
  _emoji_rng.shuffle(emoji_pairs)
  for ep in itertools.cycle(emoji_pairs):
    if str_width(ep) != 4:
      continue
    yield ep

emoji_pair: Final = emoji_pair_generator()


def str_width(s: str):
  def __c_width(c: str) -> int:
    if unicodedata.east_asian_width(c) in 'WF':
      return 2
    return 1
  return sum(__c_width(c) for c in s)


def devider() -> str:
  if term_width < 15:
    return '=' * term_width

  ep: str = next(emoji_pair)
  ending_str: str = '=' * (term_width - str_width(ep) - 4)
  return f'== {ep} {ending_str}'


def green_print(s: str) -> None:
  print(colorama.Fore.GREEN + colorama.Style.BRIGHT + s + colorama.Style.RESET_ALL)


def red_print(s: str) -> None:
  print(colorama.Fore.RED + colorama.Style.BRIGHT + s + colorama.Style.RESET_ALL)


def bold_print(s: str) -> None:
  print(colorama.Back.LIGHTBLACK_EX + colorama.Fore.LIGHTWHITE_EX + colorama.Style.BRIGHT + s.ljust(term_width) + colorama.Style.RESET_ALL)


# region: Sub-tasks

def print_args() -> None:
  '''打印命令行参数。'''
  print(devider())
  bold_print('>> Terminal args:')

  def colored(x: Any) -> str:
    if isinstance(x, bool):
      if x:
        return colorama.Fore.LIGHTGREEN_EX + colorama.Style.BRIGHT + str(x) + colorama.Style.RESET_ALL
      return colorama.Fore.LIGHTYELLOW_EX + colorama.Style.DIM + str(x) + colorama.Style.RESET_ALL
    return str(x)

  print(f'-- {sys.argv}')
  print(f'-- all_the_way:      {colored(all_the_way)}')
  print(f'-- skip_test:        {colored(skip_test)}')
  print(f'-- run_slow_test:    {colored(run_slow_test)}')
  print(f'-- run_hko_test:     {colored(run_hko_test)}')
  print(f'-- expression:       {colored(expression)}')
  print(f'-- verbose:          {colored(verbose)}')

  print(f'-- do_cov:           {colored(do_cov)}')
  print(f'-- minimum_cov_rate: {colored(str(minimum_cov_rate) + "%")}')

  print(f'-- do_ruff:          {colored(do_ruff)}')
  print(f'-- do_mypy:          {colored(do_mypy)}')

  print(f'-- do_osmoke:        {colored(do_osmoke)}')
  print(f'-- do_docs:          {colored(do_docs)}')
  print(f'-- runtime_only:     {colored(runtime_only)}')
  print(f'-- do_package:       {colored(do_package)}')


def print_sysinfo() -> None:
  '''打印系统时间及其他环境信息。'''
  mem = psutil.virtual_memory()
  this_moment: datetime = datetime.now()

  print('\n' + devider())
  bold_print('>> Sys info:')

  print(f'-- system time: {this_moment.astimezone()} ({this_moment.astimezone().tzinfo})')
  print(f'-- python executable: {sys.executable}')
  print(f'-- python version: {sys.version}')
  print(f'-- default encoding: {sys.getdefaultencoding()}')

  print(f'-- pid: {os.getpid()}')
  print(f'-- cwd: {os.getcwd()}')
  print(f'-- node: {platform.node()}')

  print(f'-- system: {platform.system()}')
  print(f'-- platform: {platform.platform()}')
  print(f'-- release: {platform.release()}')
  print(f'-- version: {platform.version()}')
  print(f'-- machine: {platform.machine()}')
  print(f'-- processor: {platform.processor()}')
  print(f'-- architecture: {platform.architecture()}')
  print(f'-- cpu cores: {os.cpu_count()}')

  print(f'-- memory size: {mem.total // 1024 // 1024} MB')
  print(f'-- usable memory size: {mem.available // 1024 // 1024} MB')
  print(f'-- disk usage: {psutil.disk_usage("/").percent}%')

def run_proc_and_print(cmds: list[str], print_details: bool = False) -> int:
  '''创建子进程运行命令，主要用于兼容 Windows。'''
  if platform.system() == 'Windows':
    return subprocess.run(cmds, check=False).returncode
  else:
    proc: subprocess.CompletedProcess = subprocess.run(cmds, capture_output=True, check=False)
    ret: int = proc.returncode

    if print_details:
      print(proc.stdout.decode('utf-8'))
    if (err_info := proc.stderr.decode('utf-8')).strip() != '' or print_details:
      print(err_info)

    return ret


def run_tests() -> int:
  '''按命令行参数运行 pytest。'''
  print('\n' + devider())
  bold_print('>> Running bazi tests...')

  pytest_args: list[str] = [
    str(Path(os.path.realpath(__file__)).parent / 'tests'),
    '-x',
    '--showlocals',
  ]
  if runtime_only:
    pytest_args.extend(
      f'--ignore={ROOT / unit}' for unit in DOC_TOOL_PATHS
      if unit.parts[:1] == ('tests',)
    )

  if verbose:
    pytest_args.append('-v')

  if expression is not None: # 给定 -k 时，不使用 -s 与 -hko 选择标记。
    pytest_args.extend(['-k', expression])
  else:
    marks: list[str] = []
    if not run_slow_test:
      marks.append('not slow')
    if not run_hko_test:
      marks.append('not hkodata')
    if len(marks) > 0:
      pytest_args.extend(['-m', ' and '.join(marks)])

  ret_code: int = pytest.main(pytest_args)
  if ret_code != 0:
    print(colorama.Fore.RED + f'>> {next(emoji_pair)} Tests failed with exit code {ret_code}' + colorama.Style.RESET_ALL)

  return ret_code


def run_coverage(test_f: Callable[[], int]) -> int:
  '''执行测试并统计整个运行时 `bazi` 包，未导入模块也计入覆盖率。'''
  print('\n' + devider())
  bold_print(f'>> Running {test_f} with coverage...')

  cov = coverage.Coverage(
    source=[str(Path(__file__).parent / 'bazi')],
    omit=[
      str(Path(__file__).parent / 'bazi/calendar/hko_data/encoder.py'), # 离线生成工具。
      str(Path(__file__).parent / 'bazi/calendar/celestial_data/generator.py'), # 离线生成工具。
    ]
  )
  cov.start()
  ret_code: int = test_f()
  cov.stop()
  cov.html_report(directory=str(Path(__file__).parent / 'covhtml'))

  # 打印覆盖率报告。
  print('\n' + devider())
  print('>> Generating coverage report...')
  cov_rate: float = cov.report(show_missing=True)
  
  if cov_rate < minimum_cov_rate:
    print(colorama.Fore.RED + f'>> {next(emoji_pair)} Coverage rate: {cov_rate}% (below {minimum_cov_rate}%)' + colorama.Style.RESET_ALL)
    ret_code |= 0x42
  else:
    print(colorama.Fore.GREEN + f'>> {next(emoji_pair)} Coverage rate: {cov_rate}%' + colorama.Style.RESET_ALL)

  return ret_code


def run_ruff() -> int:
  '''用 ruff check 检查 lint 规则。'''
  print('\n' + devider())
  bold_print('>> Checking for style violations...')

  ruff_ret: int = run_proc_and_print([
    sys.executable, '-m', 'ruff', 'check', str(Path(__file__).parent)
  ], print_details=True)

  print('>> Checking style violations completed...')

  if ruff_ret == 0:
    green_print(f'>> {next(emoji_pair)} No style violations found!')
  else:
    red_print(f'>> {next(emoji_pair)} Violations detected!')

  return ruff_ret


def run_mypy() -> int:
  '''用 mypy 检查静态类型。'''
  print('\n' + devider())
  bold_print('>> Running mypy...')

  ret: int = run_proc_and_print([
    sys.executable, '-m', 'mypy', *(str(path) for path in mypy_targets(ROOT, runtime_only)),
    '--check-untyped-defs', '--warn-redundant-casts', '--warn-unused-ignores',
    '--warn-return-any', '--warn-unreachable',
  ], print_details=True)

  if ret == 0:
    green_print(f'>> {next(emoji_pair)} mypy static type checking passed!')
  else:
    red_print(f'>> {next(emoji_pair)} mypy static type checking failed!')
  return ret


def run_o_smoke() -> int:
  '''用 python -O 运行 tests/o_smoke.py 的公开输入契约检查。'''
  print('\n' + devider())
  bold_print('>> Running o_smoke (`python -O` contract smoke)...')

  ret: int = run_proc_and_print([
    sys.executable, '-O', str(Path(__file__).parent / 'tests' / 'o_smoke.py')
  ], print_details=True)

  if ret == 0:
    green_print(f'>> {next(emoji_pair)} o_smoke passed!')
  else:
    red_print(f'>> {next(emoji_pair)} o_smoke failed!')
  return ret


def run_docs() -> int:
  '''在仓外临时目录构建并检查文档，不部署。'''
  with tempfile.TemporaryDirectory(prefix='bazi-docs-check-') as output:
    return run_proc_and_print([
      sys.executable, '-B', str(Path(__file__).parent / 'run_docs.py'), '--output-dir', output,
    ], print_details=True)


def run_package_checks() -> int:
  '''在仓外构建并验证安装工件。'''
  return run_proc_and_print([
    sys.executable, str(Path(__file__).parent / 'run_package_checks.py'),
    *(['--output-dir', str(args.package_output_dir)] if args.package_output_dir is not None else []),
    *(['--environment-report', str(args.environment_report)] if args.environment_report is not None else []),
    *(['--outer-installer-report', str(args.outer_installer_report)] if args.outer_installer_report is not None else []),
  ], print_details=True)


class SubTaskStatuses:
  def __init__(self) -> None:
    self._retcodes: Final[dict[str, int]] = {}
    self._times: Final[dict[str, float]] = {}

  def set(self, name: str, retcode: int, time: float) -> None:
    self._retcodes[name] = retcode
    self._times[name] = time

  def keys(self) -> list[str]:
    assert set(self._retcodes.keys()) == set(self._times.keys())
    return list(self._retcodes.keys())

  def __iter__(self) -> Iterator[str]:
    return iter(self.keys())
  
  @property
  def max_key_len(self) -> int:
    return max(map(len, self.keys()))
  
  def retcode(self, name: str) -> int:
    return self._retcodes[name]
  
  def time(self, name: str) -> float:
    return self._times[name]

def run_subtasks() -> SubTaskStatuses:
  s: Final[SubTaskStatuses] = SubTaskStatuses()
  def run_subtask(name: str, f: Callable[[], int]) -> None:
    subtask_start_time: datetime = datetime.now()
    s.set(name, f(), (datetime.now() - subtask_start_time).total_seconds())

  if not skip_test:
    if do_cov:
      run_subtask('coverage with tests', lambda: run_coverage(run_tests))
    else:
      run_subtask('tests', run_tests)

  if do_osmoke:
    run_subtask('o_smoke', run_o_smoke)

  if do_ruff:
    run_subtask('ruff', run_ruff)

  if do_mypy:
    run_subtask('mypy', run_mypy)

  if do_docs:
    run_subtask('docs', run_docs)

  if do_package:
    run_subtask('package', run_package_checks)

  return s


# region: Main

def main() -> None:
  if do_docs:
    check_doc_environment()
  start_time: datetime = datetime.now()

  print_args()
  print_sysinfo()
  statuses: SubTaskStatuses = run_subtasks()

  end_time: datetime = datetime.now()

  print('\n' + devider())
  print(f'-- Started at {start_time.isoformat()}')
  print(f'-- Finished at {end_time.isoformat()}')
  print(f'-- Time elapsed: {end_time - start_time}')

  print('-- Sub-tasks status:')
  for name in statuses:
    ok: bool = (0 == statuses.retcode(name))
    elapsed: float = statuses.time(name)
    name_color: str = colorama.Fore.GREEN if ok else colorama.Fore.YELLOW
    name = name_color + name.ljust(statuses.max_key_len + 1) + colorama.Style.RESET_ALL
    time_str: str = f'{elapsed:.5f}'[:7]
    print(f'   -- {name}: {"✅" if ok else "❎"} | finished in {time_str} seconds {random_emoji()}')

  retcodes: map[int] = map(statuses.retcode, statuses.keys())
  # 可能没有子任务（如只给 -nt），此时视为成功。
  resolved_retcode: int = functools.reduce(operator.or_, retcodes, 0)
  if resolved_retcode == 0:
    green_print('>> All tasks passed! ' + 
                ''.join(_emoji_rng.sample('🌙✨💫⭐🌟💖💞💕💗💓🌈👾🪐', 3)))
  else:
    red_print(f'>> Some tasks failed! Exit with code {resolved_retcode} ' + 
              ''.join(_emoji_rng.sample('🧯💣💥💅👽🗿🔥', 3)))

  sys.exit(resolved_retcode)


if __name__ == '__main__':
  main()
