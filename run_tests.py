#!/usr/bin/env python3

import os
import sys
import shutil
import psutil
import platform
import argparse
import subprocess

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Final

import pytest
import coverage
import colorama


# Get the argument from terminal.
argparser = argparse.ArgumentParser()

# Test related.
argparser.add_argument('-nt', '--no-test', action='store_true', help='If set, no test and coverage will run.')
argparser.add_argument('-s', '--slow-test', action='store_true', help='Whether or not to run slow tests.')
argparser.add_argument('-hko', '--hkodata-test', action='store_true', help='Whether or not to run hkodata tests.')
argparser.add_argument('-k', '--expression', type=str, help='Expression to filter tests.', default=None)
argparser.add_argument('-v', '--verbose', action='store_true', help='Whether or not to print verbose information during testing.')

# Coverage.
argparser.add_argument('-c', '--coverage', action='store_true', help='Whether or not to generate coverage report.')
argparser.add_argument('-cr', '--coverage-rate', type=float, help='Must-met minimum coverage rate. Default: 80.0', default=80.0)

# Linter and static type check.
argparser.add_argument('-l', '--linter', action='store_true', help='Whether or not to skip linting.')
argparser.add_argument('-mypy', '--mypy', action='store_true', help='Whether or not to run static type check.')

# Demo and interpreter.
argparser.add_argument('-d', '--demo', action='store_true', help='Whether or not to run demo code.')
argparser.add_argument('-i', '--interpreter', action='store_true', help='Whether or not to run interpreter.')

args = argparser.parse_args()

skip_test: Final[bool] = args.no_test
run_slow_test: Final[bool] = args.slow_test
run_hko_test: Final[bool] = args.hkodata_test
expression: Final[Optional[str]] = args.expression
test_verbose: Final[bool] = args.verbose

do_cov: Final[bool] = args.coverage
minimum_cov_rate: Final[float] = args.coverage_rate
do_linter: Final[bool] = args.linter
do_mypy: Final[bool] = args.mypy

do_demo: Final[bool] = args.demo
do_interpreter: Final[bool] = args.interpreter

term_width: Final[int] = shutil.get_terminal_size().columns


def print_sysinfo() -> None:
  '''Print system time and other info.'''
  mem = psutil.virtual_memory()
  this_moment: datetime = datetime.now()
  print('#' * term_width)

  print(f'-- {sys.argv}')
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


def run_proc_and_print(cmds: list[str]) -> int:
  '''This method is mainly for compatability with Windows. It creates a subprocess and runs the commands.'''
  if platform.system() == 'Windows':
    return subprocess.run(cmds).returncode
  else:
    proc: subprocess.CompletedProcess = subprocess.run(cmds, capture_output=True)
    ret: int = proc.returncode
    print(proc.stdout.decode('utf-8'))
    print(proc.stderr.decode('utf-8'))
    return ret


def run_tests() -> int:
  '''Run tests with pytest, with args from terminal.'''
  print('\n' + '#' * term_width)
  print('>> Running bazi tests...')

  pytest_args: list[str] = [
    str(Path(os.path.realpath(__file__)).parent / 'tests'),
    '-x',
  ]

  if test_verbose:
    pytest_args.append('-v')

  if expression is not None: # If `-k` is set, we don't care `-s` and `-hko`...
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
    print(colorama.Fore.RED + f'>> Tests failed with exit code {ret_code}' + colorama.Style.RESET_ALL)

  return ret_code


def run_coverage(test_f: Callable[[], int]) -> int:
  '''Run tests, and generate coverage report.'''
  print('\n' + '#' * term_width)
  print(f'>> Running {test_f} with coverage...')

  cov = coverage.Coverage(
    omit=[
      '*/__init__.py',
      '*/run_tests.py',
      '*/tests/*',
      'src/Calendar/HkoData/encoder.py', # The raw data already downloaded. No much need to fully test the encoder.
    ]
  )
  cov.start()
  ret_code: int = test_f()
  cov.stop()
  cov.html_report(directory=str(Path(__file__).parent / 'covhtml'))

  # Print the coverage report.
  print('\n' + '#' * term_width)
  print('>> Generating coverage report...')
  cov_rate: float = cov.report(show_missing=True)
  
  if cov_rate < minimum_cov_rate:
    print(colorama.Fore.RED + f'>> Coverage rate: {cov_rate}% (below {minimum_cov_rate}%)' + colorama.Style.RESET_ALL)
    ret_code |= 0x42
  else:
    print(colorama.Fore.GREEN + f'>> Coverage rate: {cov_rate}%' + colorama.Style.RESET_ALL)

  return ret_code


def run_ruff() -> int:
  '''Use `ruff` to check for style violations.'''
  print('\n' + '#' * term_width)
  print('>> Checking for style violations...')

  proc: subprocess.CompletedProcess = subprocess.run([
    'ruff', 'check', str(Path(__file__).parent)
  ], capture_output=True)
  ruff_ret: int = proc.returncode
  print('>> Checking style violations completed...')

  if ruff_ret == 0:
    print(colorama.Fore.GREEN + '>> No style violations found!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + '>> Violations detected!' + colorama.Style.RESET_ALL)
    print(proc.stdout.decode('utf-8'))
    print(proc.stderr.decode('utf-8'))

  return ruff_ret


def run_mypy() -> int:
  '''Do static type checking with `mypy`'''
  print('\n' + '#' * term_width)
  print('>> Running mypy...')
  ret: int = run_proc_and_print([
    'python3', '-m', 'mypy', str(Path(__file__).parent), 
    '--check-untyped-defs', '--warn-redundant-casts', '--warn-unused-ignores',
    '--warn-return-any', '--warn-unreachable',
  ])

  if ret == 0:
    print(colorama.Fore.GREEN + '>> mypy static type checking passed!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + '>> mypy static type checking failed!' + colorama.Style.RESET_ALL)
  return ret


def run_demo() -> int:
  '''Run demo by executing `run_demo.py`'''
  print('\n' + '#' * term_width)
  print('>> Running demo...')
  ret: int = run_proc_and_print([
    'python3', str(Path(__file__).parent / 'run_demo.py')
  ])

  if ret == 0:
    print(colorama.Fore.GREEN + '>> Demo passed!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + '>> Demo failed!' + colorama.Style.RESET_ALL)
  return ret


def run_interpreter() -> int:
  '''Run interpreter by executing `run_interpreter.py`'''
  print('\n' + '#' * term_width)
  print('>> Running interpreter...')
  ret: int = run_proc_and_print([
    'python3', str(Path(__file__).parent / 'run_interpreter.py')
  ])
  
  if ret == 0:
    print(colorama.Fore.GREEN + '>> Interpreter passed!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + '>> Interpreter failed!' + colorama.Style.RESET_ALL)
  return ret


def main() -> None:
  start_time: datetime = datetime.now()
  ret_code: int = 0

  print_sysinfo()

  if not skip_test:
    if do_cov:
      ret_code |= run_coverage(run_tests)
    else:
      ret_code |= run_tests()

  if do_demo:
    ret_code |= run_demo()

  if do_interpreter:
    ret_code |= run_interpreter()

  if do_linter:
    ret_code |= run_ruff()

  if do_mypy:
    ret_code |= run_mypy()

  print('\n' + '#' * term_width)
  end_time: datetime = datetime.now()
  print(f'-- Finished at {end_time.isoformat()}')
  print(f'-- Time elapsed: {end_time - start_time}')

  if ret_code == 0:
    print(colorama.Fore.GREEN + '>> All tasks passed!' + colorama.Style.RESET_ALL)
  else:
    print(colorama.Fore.RED + f'>> Some tasks failed! Exit with code {ret_code}' + colorama.Style.RESET_ALL)

  sys.exit(ret_code)


if __name__ == '__main__':
  main()
